"""

**Routines to load, validate, and provide access to vehicle mass scaling equation data**

Mass scaling equations are defined by a mass term, a condition expression and equation to be evaluated.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents vehicle mass scaling equations as a function of user-definable vehicle attributes
or other conditions

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,mass_scaling,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        mass_term,condition,equation,
        null_structure_mass_lbs,vehicle.body_style == 'sedan' and vehicle.unibody_structure==1,18.5 * vehicle.footprint_ft2 + 180,
        structure_mass_lbs,vehicle.structure_material == 'steel',1 * null_structure_mass,
        battery_mass_lbs,vehicle.powertrain_type == 'BEV',(2.2 * battery_kwh) / (0.0000000847 * battery_kwh ** 3 + 0.0000249011 * battery_kwh ** 2 + 0.0023686408 * battery_kwh + 0.1245668155),
        powertrain_mass_lbs,vehicle.powertrain_type == 'ICE' and vehicle.drive_system==2,0.6 * vehicle.eng_rated_hp + 200,

Data Column Name and Description

:mass_term:
    Name of the mass term

:condition:
    A boolean condition, which when ``True`` causes the evaluation of the following equation

:equation:
    The numeric equation which calculates the mass term

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class MassScaling(OMEGABase):
    """
    **Load and provides routines to access mass scaling terms and equations.**

    """

    _data = dict()  # private dict, drive cycle descriptions

    structure_materials = []

    # drive_cycle_names = []  #: list of available drive cycles (may not all be used, depends on the simulated vehicles data)

    @staticmethod
    def calc_mass_terms(vehicle, structure_material, eng_rated_hp, battery_kwh, footprint_ft2):
        """
        Calculate struture mass, battery mass and powertrain mass for the given vehicle

        Args:
            vehicle (Vehicle): the vehicle to calculate mass terms for
            structure_material (str): e.g. 'steel'
            eng_rated_hp (float): engine rated horsepower
            battery_kwh (float): battery pack size in kWh
            footprint_ft2 (float): vehicle footpring in square feet

        Returns:
            tuple of structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, delta_glider_non_structure_mass_lbs, \
               and usable_battery_capacity_norm for the given vehicle

        """
        from math import e

        null_structure_mass_lbs = 0
        structure_mass_lbs = 0
        battery_mass_lbs = 0
        powertrain_mass_lbs = 0
        delta_glider_non_structure_mass_lbs = 0
        usable_battery_capacity_norm = 0

        delta_footprint = footprint_ft2 - vehicle.base_year_footprint_ft2

        locals_dict = locals()
        for condition_equation in MassScaling._data['null_structure_mass_lbs']['condition_equation']:
            null_structure_mass_lbs += Eval.eval(condition_equation, {'np': np}, locals_dict)

        locals_dict = locals()
        for condition_equation in MassScaling._data['structure_mass_lbs']['condition_equation']:
            structure_mass_lbs += Eval.eval(condition_equation, {'np': np}, locals_dict)

        # locals_dict = locals()
        nmc_share_dict_bev = omega_globals.options.nmc_share_BEV
        nmc_share_dict_phev = omega_globals.options.nmc_share_PHEV

        if type(vehicle) is pd.DataFrame:
            nmc_model_year = vehicle.model_year.iloc[0]
        else:
            nmc_model_year = vehicle.model_year

        if nmc_model_year in nmc_share_dict_bev:
            nmc_share_bev = nmc_share_dict_bev[nmc_model_year]
        else:
            nmc_share_bev = nmc_share_dict_bev[max(nmc_share_dict_bev.keys())]

        if nmc_model_year in nmc_share_dict_phev:
            nmc_share_phev = nmc_share_dict_phev[nmc_model_year]
        else:
            nmc_share_phev = nmc_share_dict_phev[max(nmc_share_dict_phev.keys())]

        for condition_equation_nmc in MassScaling._data['battery_mass_nmc_lbs']['condition_equation']:
            # BEV batteries, NMC share
            battery_mass_lbs += (Eval.eval(condition_equation_nmc, {'np': np}, locals_dict) * nmc_share_bev *
                                 (vehicle.powertrain_type == 'BEV'))
            # PHEV batteries, NMC share
            battery_mass_lbs += (Eval.eval(condition_equation_nmc, {'np': np}, locals_dict) * nmc_share_phev *
                                 (vehicle.powertrain_type == 'PHEV'))

        for condition_equation_lfp in MassScaling._data['battery_mass_lfp_lbs']['condition_equation']:
            # BEV batteries, LFP share
            battery_mass_lbs += (Eval.eval(condition_equation_lfp, {'np': np}, locals_dict) * (1 - nmc_share_bev) *
                                 (vehicle.powertrain_type == 'BEV'))
            # PHEV batteries, LFP share
            battery_mass_lbs += (Eval.eval(condition_equation_lfp, {'np': np}, locals_dict) * (1 - nmc_share_phev) *
                                 (vehicle.powertrain_type == 'PHEV'))
            # HEV batteries, all assumed to be LFP
            battery_mass_lbs += (Eval.eval(condition_equation_lfp, {'np': np}, locals_dict) *
                                 (vehicle.powertrain_type == 'HEV'))

        # locals_dict = locals()
        for condition_equation in MassScaling._data['powertrain_mass_lbs']['condition_equation']:
            powertrain_mass_lbs += Eval.eval(condition_equation, {'np': np}, locals_dict)

        # locals_dict = locals()
        for condition_equation in MassScaling._data['delta_glider_non_structure_mass_lbs']['condition_equation']:
            delta_glider_non_structure_mass_lbs += Eval.eval(condition_equation, {'np': np}, locals_dict)

        # locals_dict = locals()
        for condition_equation in MassScaling._data['usable_battery_capacity_norm']['condition_equation']:
            usable_battery_capacity_norm += Eval.eval(condition_equation, {'np': np}, locals_dict)

        usable_battery_capacity_norm += (usable_battery_capacity_norm == 0)  # zeros -> 1.0s by default

        return structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, delta_glider_non_structure_mass_lbs, \
               usable_battery_capacity_norm

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        MassScaling._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'mass_scaling'
        input_template_version = 0.1
        input_template_columns = {'mass_term', 'condition', 'equation'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'mass_term': ['structure_materials', 'null_structure_mass_lbs', 'structure_mass_lbs',
                                             'battery_mass_nmc_lbs', 'battery_mass_lfp_lbs', 'powertrain_mass_lbs',
                                             'delta_glider_non_structure_mass_lbs', 'usable_battery_capacity_norm'],
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')

            df['condition_equation'] = '(' + df['condition'] + ') * (' + df['equation'] + ')'
            df['condition_equation'] = df['condition_equation']\
                .apply(lambda x: str.replace(x, 'max(', 'np.maximum(').replace('min(', 'np.minimum('))

            for term in ['null_structure_mass_lbs', 'structure_mass_lbs',
                         'battery_mass_nmc_lbs', 'battery_mass_lfp_lbs', 'powertrain_mass_lbs', 'delta_glider_non_structure_mass_lbs',
                         'usable_battery_capacity_norm']:
                MassScaling._data[term] = df[df['mass_term'] == term].set_index('mass_term').to_dict(orient='list')

            MassScaling.structure_materials = Eval.eval(df[df['mass_term'] == 'structure_materials']['equation'][0])

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += MassScaling.init_from_file(omega_globals.options.mass_scaling_file,
                                                verbose=omega_globals.options.verbose)

        if not init_fail:
            class Vehicle(OMEGABase):
                """
                    Dummy Vehicle class

                """
                model_year = 2024
                body_style = 'sedan'
                base_year_footprint_ft2 = 20
                footprint_ft2 = 22
                height_in = 65
                ground_clearance_in = 6
                structure_material = 'aluminum'
                eng_rated_hp = 200
                drive_system = 2
                unibody_structure = 1
                powertrain_type = 'ICE'
                battery_kwh = 60

            veh = Vehicle()

            structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, delta_glider_non_structure_mass_lbs, \
                usable_battery_capacity_norm = \
                MassScaling.calc_mass_terms(veh, veh.structure_material, veh.eng_rated_hp,
                                            veh.battery_kwh, veh.footprint_ft2)
            print(structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, delta_glider_non_structure_mass_lbs)

            veh.base_year_powertrain_type = 'BEV'
            structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, delta_glider_non_structure_mass_lbs, \
                usable_battery_capacity_norm = \
                MassScaling.calc_mass_terms(veh, veh.structure_material, veh.eng_rated_hp,
                                            veh.battery_kwh, veh.footprint_ft2)
            print(structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, delta_glider_non_structure_mass_lbs)
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
