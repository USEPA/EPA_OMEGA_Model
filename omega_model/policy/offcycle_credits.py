"""

**Routines to load, access and apply off-cycle credit values**

Off-cycle credits represent GHG benefits of technologies that have no or limited on-cycle benefits.

For example, LED headlights have a real-world ("off-cycle") benefit but are not represented during certification
testing (tests are performed with headlights off).

As another example, engine Stop-Start has an on-cycle benefit but the vehicle idle duration during testing may
under-represent vehicle idle duration in real-world driving so there may be some additional benefit available.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format. The data header uses a dynamic column notation, as detailed below.

The data represents offcycle credit values (grams CO2e/mile) credit group and regulatory class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,policy.offcycle_credits,input_template_version:,0.11

The data header consists of ``start_year``, ``credit_name``, ``credit_group``, ``credit_destination`` columns
followed by zero or more reg class columns, as needed.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        start_year, credit_name, credit_group, credit_destination, ``reg_class_id:{reg_class_id}``, ...

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,credit_name,credit_group,credit_destination,reg_class_id:car,reg_class_id:truck
        2020,start_stop,menu,cert_direct_offcycle_co2e_grams_per_mile,2.5,4.4
        2020,high_eff_alternator,menu,cert_direct_offcycle_co2e_grams_per_mile,2.7,2.7
        2020,ac_leakage,ac,cert_indirect_offcycle_co2e_grams_per_mile,13.8,17.2
        2020,ac_efficiency,ac,cert_direct_offcycle_co2e_grams_per_mile,5,7.2

Data Column Name and Description

:start_year:
    Start year of production constraint, constraint applies until the next available start year

:credit_name:
    Name of the offcycle credit

:credit_group:
    Group name of the offcycle credit, in case of limits within a group of credits (work in progress)

:credit_destination:
    Name of the vehicle CO2e attribute to apply the credit to, e.g. ``cert_direct_offcycle_co2e_grams_per_mile``,
    ``cert_indirect_offcycle_co2e_grams_per_mile``

**Optional Columns**

:``reg_class_id:{reg_class_id}``:
    The value of the credits.  Credits are specified as positive numbers and are subtracted from the cert results
    to determine a compliance result

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class OffCycleCredits(OMEGABase, OffCycleCreditsBase):
    """
    **Loads, stores and applies off-cycle credits to vehicle cost clouds**

    """

    _data = dict()  # private dict, off cycle credit data
    _offcycle_credit_groups = []  #: list of credit groups, populated during init
    _offcycle_credit_value_columns = []  #: list of columns that contain credit values, of the format ``vehicle_attribute:attribute_value``

    offcycle_credit_names = []  #: list of credit names, populated during init, used to track credits across composition/decomposition, also used to check simulated vehicles for necessary columns

    @staticmethod
    def calc_off_cycle_credits(calendar_year, vehicle, cost_cloud):
        """
        Calculate vehicle off-cycle credits for the vehicle's cost cloud

        Args:
            calendar_year (int): the year to calculate credits for, usually the vehicle model year
            vehicle (Vehicle): the vehicle to apply off-cycle credits to
            cost_cloud (DataFrame): destination data set for off-cycle credits

        Returns:
            cost_cloud with off-cycle credits calculated

        """
        # TODO: off cycle groups can be used to apply credit limits by credit group
        group_totals = dict()
        for ocg in OffCycleCredits._offcycle_credit_groups:
            group_totals[ocg] = 0

        cost_cloud['cert_direct_offcycle_co2e_grams_per_mile'] = 0
        cost_cloud['cert_direct_offcycle_kwh_per_mile'] = 0
        cost_cloud['cert_indirect_offcycle_co2e_grams_per_mile'] = 0

        for credit_column in OffCycleCredits._offcycle_credit_value_columns:
            attribute, value = credit_column.split(':')
            if vehicle.__getattribute__(attribute) == value:
                for offcycle_credit in OffCycleCredits.offcycle_credit_names:
                    cache_key = (credit_column, attribute, calendar_year, offcycle_credit)
                    if cache_key not in OffCycleCredits._data:
                        start_years = np.array(OffCycleCredits._data['start_year'][offcycle_credit])
                        if len(start_years[start_years <= calendar_year]) > 0:
                            year = max(start_years[start_years <= calendar_year])

                            credit_value = OffCycleCredits._data[offcycle_credit, year][credit_column]
                            credit_destination = \
                                OffCycleCredits._data[offcycle_credit, year]['credit_destination']

                            OffCycleCredits._data[cache_key] = (credit_destination, credit_value)
                        else:
                            OffCycleCredits._data[cache_key] = (None, 0)

                    (credit_destination, credit_value) = OffCycleCredits._data[cache_key]

                    if offcycle_credit in cost_cloud and credit_destination is not None:
                        cost_cloud[credit_destination] += credit_value * cost_cloud[offcycle_credit]

        return cost_cloud

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename: name of input file
            verbose: enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        OffCycleCredits._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.11
        input_template_columns = {'start_year', 'credit_name', 'credit_group', 'credit_destination'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'credit_name': ['start_stop', 'high_eff_alternator', 'ac_leakage', 'ac_efficiency',
                                               'other_oc_menu_tech'],
                               'credit_group': ['menu', 'ac'],
                               'credit_destination': ['cert_direct_offcycle_co2e_grams_per_mile',
                                                      'cert_indirect_offcycle_co2e_grams_per_mile'],
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            OffCycleCredits._offcycle_credit_value_columns = [c for c in df.columns if (':' in c)]

            # for cc in OffCycleCredits._offcycle_credit_value_columns:
            #     reg_class_id = cc.split(':')[1]
            #     if reg_class_id not in omega_globals.options.RegulatoryClasses.reg_classes:
            #         template_errors.append('*** Invalid Reg Class ID "%s" in %s ***' % (reg_class_id, filename))

        if not template_errors:
            OffCycleCredits.offcycle_credit_names = list(df['credit_name'].unique())
            OffCycleCredits._offcycle_credit_groups = list(df['credit_group'].unique())
            # convert dataframe to dict keyed by credit name and start year
            OffCycleCredits._data = df.set_index(['credit_name', 'start_year']).to_dict(orient='index')
            # add 'start_year' key which returns start years by credit name
            OffCycleCredits._data.update(
                df[['credit_name', 'start_year']].set_index('credit_name').to_dict(orient='series'))

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from omega_model.omega import get_module
        from policy.drive_cycles import DriveCycles

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        import importlib
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        module_name = get_template_name(omega_globals.options.ice_vehicle_simulation_results_file)
        omega_globals.options.CostCloud = get_module(module_name).CostCloud

        # init drive cycles PRIOR to CostCloud since CostCloud needs the drive cycle names for validation
        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.CostCloud.\
            init_cost_clouds_from_files(omega_globals.options.ice_vehicle_simulation_results_file,
                                        omega_globals.options.bev_vehicle_simulation_results_file,
                                        omega_globals.options.phev_vehicle_simulation_results_file,
                                        verbose=omega_globals.options.verbose)

        init_fail += OffCycleCredits.init_from_file(omega_globals.options.offcycle_credits_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            # class VehicleDummy:
            #     model_year = 2020
            #     reg_class_id = 'car'
            #     cost_curve_class = 'ice_MPW_LRL'
            #     cost_cloud = omega_globals.options.CostCloud.get_cloud(self)
            #
            # vehicle = VehicleDummy()
            #
            # OffCycleCredits.calc_off_cycle_credits(vehicle.model_year, vehicle, vehicle.cost_cloud)
            pass

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
