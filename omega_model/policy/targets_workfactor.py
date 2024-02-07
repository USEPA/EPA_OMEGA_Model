"""

**Loads parameters and provides calculations for an attribute-based (vehicle work factor) GHG standard.**

This is based on the current work factor based standards, with two liquid fuel types and with lifetime VMT and
parameter-based target calculations based on work factor with work factor defined in the work_factor_definition file.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represent a set of GHG standards (vehicle target CO2e g/mi) by fuel type and model year as a function
of work factor.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,policy.targets_workfactor,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,start_year,cert_fuel_id,useful_life_miles,co2_gram_per_mile
        mediumduty,2020,{'gasoline':1.0},120000,0.0440 * workfactor + 339
        mediumduty,2021,{'gasoline':1.0},120000,0.0429 * workfactor + 331
        mediumduty,2022,{'gasoline':1.0},120000,0.0418 * workfactor + 322

Data Column Name and Description

:reg_class_id:
    Regulatory class name, e.g. 'mediumduty'

:start_year:
    The start year of the standard, applies until the next available start year

:cert_fuel_id:
    Minimum footprint limit of the curve (square feet)

:useful_life_miles:
    The regulatory useful life during which the standard applies and used for computing CO2e Mg

:co2_gram_per_mile:
    The co2 gram per mile standard.

----

**CODE**

"""
import pandas as pd

print('importing %s' % __file__)

from omega_model import *
from policy.workfactor_definition import WorkFactor


class VehicleTargets(OMEGABase, VehicleTargetsBase):
    """
    **Implements vehicle workfactor-based GHG targets (CO2e g/mi).**

    """
    _cache = dict()  # the input file target equations
    start_years = dict()
    _data = dict()  # private dict, workfactor-based GHG target by cert_fuel_id and start year

    @staticmethod
    def calc_target_co2e_gpmi(vehicle):
        """
        Calculate vehicle target CO2e g/mi.

        Args:
            vehicle (Vehicle): the vehicle to get the target for

        Returns:
            Vehicle target CO2e in g/mi.

        """
        start_years = VehicleTargets.start_years[vehicle.cert_fuel_id]

        if len([yr for yr in start_years if yr <= vehicle.model_year]) > 0:

            workfactor = 0
            if vehicle.reg_class_id == 'mediumduty':
                model_year, curbweight_lbs, gvwr_lbs, gcwr_lbs, drive_system \
                    = vehicle.model_year, vehicle.curbweight_lbs, vehicle.gvwr_lbs, vehicle.gcwr_lbs, \
                    vehicle.drive_system
                workfactor = WorkFactor.calc_workfactor(model_year, curbweight_lbs, gvwr_lbs, gcwr_lbs, drive_system)

            vehicle.workfactor = workfactor
            year = max([yr for yr in start_years if yr <= vehicle.model_year])
            target = \
                eval(VehicleTargets._cache[(vehicle.reg_class_id, year, vehicle.cert_fuel_id)]['co2_gram_per_mile'],
                     locals())

        else:
            raise Exception(f'Missing GHG CO2e g/mi target parameters for {vehicle.reg_class_id}, '
                            f'{vehicle.model_year}, {vehicle.cert_fuel_id} or prior')

        return target

    @staticmethod
    def calc_cert_useful_life_vmt(reg_class_id, model_year, cert_fuel_id):
        """
        Calculate the certification useful life vehicle miles travelled.

        Args:
            reg_class_id (str): e.g. 'car', 'truck'
            model_year (int): the model year to get useful life VMT for
            cert_fuel_id (str): certification fuel id, e.g. 'gasoline'

        Returns:
            The certification useful life vehicle miles travelled.

        """
        cache_key = (reg_class_id, model_year, cert_fuel_id)

        locals_dict = locals()

        start_years = VehicleTargets.start_years[cert_fuel_id]

        if len([yr for yr in start_years if yr <= model_year]) > 0:

            year = max([yr for yr in start_years if yr <= model_year])

            useful_life = VehicleTargets._cache[(reg_class_id, year, cert_fuel_id)]['useful_life_miles']
        else:
            raise Exception(f'Missing GHG CO2e g/mi target parameters for {reg_class_id}, '
                            f'{model_year}, {cert_fuel_id} or prior')

        return useful_life

    @staticmethod
    def calc_target_co2e_Mg(vehicle, sales_variants=None):
        """
        Calculate vehicle target CO2e Mg as a function of the vehicle, the standards and optional sales options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Target CO2e Mg value(s) for the given vehicle and/or sales variants.

        """
        start_years = VehicleTargets.start_years[vehicle.cert_fuel_id]

        if len([yr for yr in start_years if yr <= vehicle.model_year]) > 0:
            model_year = max([yr for yr in start_years if yr <= vehicle.model_year])

            vehicle.lifetime_VMT \
                = VehicleTargets.calc_cert_useful_life_vmt(vehicle.reg_class_id, model_year, vehicle.cert_fuel_id)

            co2_gpmi = VehicleTargets.calc_target_co2e_gpmi(vehicle)

            if sales_variants is not None:
                if not (type(sales_variants) is pd.Series) or (type(sales_variants) is np.ndarray):
                    sales = np.array(sales_variants)
                else:
                    sales = sales_variants
            else:
                sales = vehicle.initial_registered_count

            # return co2_gpmi * vehicle.lifetime_VMT * sales * Incentives.get_production_multiplier(vehicle) / 1e6
            return co2_gpmi * vehicle.lifetime_VMT * sales / pow(10, 6)

        else:
            raise Exception(f'Missing GHG CO2e g/mi target parameters for {vehicle.reg_class_id}, '
                            f'{vehicle.model_year}, {vehicle.cert_fuel_id} or prior')

    @staticmethod
    def calc_cert_co2e_Mg(vehicle, co2_gpmi_variants=None, sales_variants=1):
        """
        Calculate vehicle cert CO2e Mg as a function of the vehicle, the standards, CO2e g/mi options and optional sales
        options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            co2_gpmi_variants (numeric list-like): optional co2 g/mi variants
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Cert CO2e Mg value(s) for the given vehicle, CO2e g/mi variants and/or sales variants.

        """
        start_years = VehicleTargets.start_years[vehicle.cert_fuel_id]

        if len([yr for yr in start_years if yr <= vehicle.model_year]) > 0:
            model_year = max([yr for yr in start_years if yr <= vehicle.model_year])

            vehicle.lifetime_VMT \
                = VehicleTargets.calc_cert_useful_life_vmt(vehicle.reg_class_id, model_year, vehicle.cert_fuel_id)

            if co2_gpmi_variants is not None:
                if not (type(sales_variants) is pd.Series) or (type(sales_variants) is np.ndarray):
                    sales = np.array(sales_variants)
                else:
                    sales = sales_variants

                if not (type(co2_gpmi_variants) is pd.Series) or (type(co2_gpmi_variants) is np.ndarray):
                    co2_gpmi = np.array(co2_gpmi_variants)
                else:
                    co2_gpmi = co2_gpmi_variants
            else:
                sales = vehicle.initial_registered_count
                co2_gpmi = vehicle.cert_co2e_grams_per_mile

            # return co2_gpmi * vehicle.lifetime_VMT * sales * Incentives.get_production_multiplier(vehicle) / 1e6
            return co2_gpmi * vehicle.lifetime_VMT * sales / pow(10, 6)
        else:
            raise Exception(f'Missing GHG CO2e g/mi target parameters for {vehicle.reg_class_id}, '
                            f'{vehicle.model_year}, {vehicle.cert_fuel_id} or prior')

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
        VehicleTargets._cache.clear()
        VehicleTargets.start_years.clear()
        VehicleTargets._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {
            'reg_class_id',
            'start_year',
            'cert_fuel_id',
            'useful_life_miles',
            'co2_gram_per_mile',
        }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            # validate columns
            validation_dict = {'reg_class_id': omega_globals.options.RegulatoryClasses.reg_classes}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            cache_keys = zip(
                df['reg_class_id'],
                df['start_year'],
                df['cert_fuel_id'],
            )
            for cache_key in cache_keys:
                VehicleTargets._cache[cache_key] = dict()

                reg_class_id, start_year, cert_fuel_id = cache_key

                target_info = df[(df['reg_class_id'] == reg_class_id)
                                 & (df['start_year'] == start_year)
                                 & (df['cert_fuel_id'] == cert_fuel_id)].iloc[0]

                useful_life = target_info['useful_life_miles']

                VehicleTargets._cache[cache_key] = {
                    'co2_gram_per_mile': dict(),
                    'useful_life_miles': useful_life,
                }
                VehicleTargets._cache[cache_key]['co2_gram_per_mile'] \
                    = compile(str(target_info['co2_gram_per_mile']), '<string>', 'eval')

            for fuel in df['cert_fuel_id'].unique():
                VehicleTargets.start_years[fuel] = [yr for yr in df.loc[df['cert_fuel_id'] == fuel, 'start_year']]

        return template_errors


if __name__ == '__main__':
    try:

        __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        from policy.incentives import Incentives
        init_fail += Incentives.init_from_file(omega_globals.options.production_multipliers_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += WorkFactor.init_from_file(omega_globals.options.workfactor_definition_file,
                                               verbose=omega_globals.options.verbose)

        omega_globals.options.policy_targets_file = \
            omega_globals.options.omega_model_path + '/test_inputs/ghg_standards_workfactor_hdp2.csv'

        init_fail += VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                   verbose=omega_globals.options.verbose)

        if not init_fail:

            omega_globals.options.VehicleTargets = VehicleTargets

            class VehicleDummy:
                """
                Dummy Vehicle class.

                """
                model_year = None
                reg_class_id = None
                footprint_ft2 = None
                initial_registered_count = None
                cert_fuel_id = 'gasoline'
                curbweight_lbs = 5000
                gvwr_lbs = 7500
                gcwr_lbs = 1000
                drive_system = 'AWD'

                def get_initial_registered_count(self):
                    """
                    Get initial registered count

                    Returns:
                        Initial registered count
                    """
                    return self.initial_registered_count

            car_vehicle = VehicleDummy()
            car_vehicle.model_year = 2021
            car_vehicle.reg_class_id = 'mediumduty'
            car_vehicle.footprint_ft2 = 41
            car_vehicle.initial_registered_count = 1
            car_vehicle.fueling_class = 'BEV'

            truck_vehicle = VehicleDummy()
            truck_vehicle.model_year = 2021
            truck_vehicle.reg_class_id = 'mediumduty'
            truck_vehicle.footprint_ft2 = 41
            truck_vehicle.initial_registered_count = 1
            truck_vehicle.fueling_class = 'ICE'

            car_target_co2e_gpmi = omega_globals.options.VehicleTargets.calc_target_co2e_gpmi(car_vehicle)

            car_target_co2e_Mg = omega_globals.options.VehicleTargets.calc_target_co2e_Mg(car_vehicle)

            car_certs_co2e_Mg = \
                omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(car_vehicle, co2_gpmi_variants=[0, 50, 100, 150])

            car_certs_sales_co2e_Mg = \
                omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(car_vehicle,
                                                                       co2_gpmi_variants=[0, 50, 100, 150],
                                                                       sales_variants=[1, 2, 3, 4])

            truck_target_co2e_gpmi = omega_globals.options.VehicleTargets.calc_target_co2e_gpmi(truck_vehicle)

            truck_target_co2e_Mg = omega_globals.options.VehicleTargets.calc_target_co2e_Mg(truck_vehicle)

            truck_certs_co2e_Mg = \
                omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(truck_vehicle, [0, 50, 100, 150])

            truck_certs_sales_co2e_Mg = \
                omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(truck_vehicle, [0, 50, 100, 150],
                                                                       sales_variants=[1, 2, 3, 4])
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
