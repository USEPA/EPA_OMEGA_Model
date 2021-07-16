"""

**Routines to load, access and apply off-cycle credit values**

Off-cycle credits represent GHG benefits of technologies that have no or limited on-cycle benefits.

For example, LED headlights have a real-world ("off-cycle") benefit but are not represented during certification
testing (tests are performed with headlights off).

As another example, engine Stop-Start has an on-cycle benefit but the vehicle idle duration during testing may
under-represent vehicle idle duration in real-world driving so there may be some additional benefit available.


----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class OffCycleCredits(OMEGABase):
    """
    **Loads, stores and applies off-cycle credits to vehicle cost clouds**

    """

    _values = dict()

    offcycle_credit_names = []  #: List of cycle names, populated during init, used to track credits across composition/decomposition and into the database, also used to check simulated vehicles for necessary columns

    @staticmethod
    def calc_off_cycle_credits(vehicle):
        """
        Calculate vehicle off-cycle credits for the vehicle's cost cloud

        Args:
            vehicle (class Vehicle): the vehicle to apply off-cycle credits to

        Returns:
            vehicle.cost_cloud with off-cycle credits calculated

        """
        start_years = OffCycleCredits._values['start_year']
        calendar_year = max(start_years[start_years <= vehicle.model_year])

        df = OffCycleCredits._values['data']
        offcycle_credits = df.loc[df['start_year'] == calendar_year]

        # TODO: off cycle groups can be used to apply credit limits by credit group
        offcycle_groups = df['credit_group'].unique()
        group_totals = dict()
        for ocg in offcycle_groups:
            group_totals[ocg] = 0

        vehicle.cost_cloud['cert_direct_offcycle_co2e_grams_per_mile'] = 0
        vehicle.cost_cloud['cert_direct_offcycle_kwh_per_mile'] = 0
        vehicle.cost_cloud['cert_indirect_offcycle_co2e_grams_per_mile'] = 0

        for cc in OffCycleCredits._values['credit_columns']:
            attribute, value = cc.split(':')
            if vehicle.__getattribute__(attribute) == value:
                for i in offcycle_credits.itertuples():
                    credit_value = df[cc].loc[i.Index]
                    vehicle.cost_cloud[i.credit_destination] += credit_value * vehicle.cost_cloud[i.credit_name]

        return vehicle.cost_cloud

    @classmethod
    def init_from_file(cls, filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename: name of input file
            verbose: enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'offcycle_credits'
        input_template_version = 0.1
        input_template_columns = {'start_year', 'credit_name', 'credit_group', 'credit_destination'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                OffCycleCredits._values['start_year'] = np.array(df['start_year'])
                OffCycleCredits._values['data'] = df

                cls.offcycle_credit_names = df['credit_name'].unique().tolist()

                OffCycleCredits._values['credit_columns'] = [c for c in df.columns if (':' in c)]

                for cc in OffCycleCredits._values['credit_columns']:
                    reg_class_id = cc.split(':')[1]
                    if not reg_class_id in omega_globals.options.RegulatoryClasses.reg_classes:
                        template_errors.append('*** Invalid Reg Class ID "%s" in %s ***' % (reg_class_id, filename))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib
        from context.cost_clouds import CostCloud

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.cost_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += OffCycleCredits.init_from_file(omega_globals.options.offcycle_credits_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            OffCycleCredits._values['data'].to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'required_zev_shares.csv', index=False)

            class dummyVehicle:
                model_year = 2020
                reg_class_id = 'car'
                cost_curve_class = 'ice_MPW_LRL'
                cost_cloud = CostCloud.get_cloud(model_year, cost_curve_class)

            vehicle = dummyVehicle()

            OffCycleCredits.calc_off_cycle_credits(vehicle)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
