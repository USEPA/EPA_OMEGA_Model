"""

**Loads parameters and provides calculations for an "alternative" (non-attribute-based) GHG standard.**

This is just a simple standard with two regulatory classes, a year-based vehicle CO2e g/mi target and lifetime
VMT for each.

Primarily used for testing.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents a simple set of GHG standards (CO2e g/mi) by regulatory class and model year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,policy.targets_alternative,input_template_version:,0.11

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,start_year,ghg_target_co2e_grams_per_mile,lifetime_vmt
        car,2020,210,195264
        truck,2020,280,225865

Data Column Name and Description

:reg_class_id:
    Regulatory class name, e.g. 'car', 'truck'

:start_year:
    The start year of the standards, applies until the next available start year

:ghg_target_co2e_grams_per_mile:
    Vehicle GHG target (CO2e g/mi)

:lifetime_vmt:
    Lifetime Vehicle Miles Travelled for computing CO2e Mg

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


if __name__ == '__main__':
    import importlib

    omega_globals.options = OMEGASessionSettings()

    init_fail = []

    module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
    omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
    init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
        omega_globals.options.policy_reg_classes_file)


class VehicleTargets(OMEGABase, VehicleTargetsBase):
    """
    **Implements a simple non-attribute-based GHG standard.**

    """

    _data = dict()  # private dict, GHG target parameters by reg class ID and start year

    @staticmethod
    def calc_target_co2e_gpmi(vehicle):
        """
        Calculate vehicle target CO2e g/mi.

        Args:
            vehicle (Vehicle): the vehicle to get the target for

        Returns:

            Vehicle target CO2e in g/mi.

        """
        start_years = VehicleTargets._data[vehicle.reg_class_id]['start_year']
        if len(start_years[start_years <= vehicle.model_year]) > 0:
            model_year = max(start_years[start_years <= vehicle.model_year])

            return VehicleTargets._data[vehicle.reg_class_id, model_year]['ghg_target_co2e_grams_per_mile']
        else:
            raise Exception('Missing GHG CO2e g/mi target parameters for %s, %d or prior'
                            % (vehicle.reg_class_id, vehicle.model_year))

    @staticmethod
    def calc_cert_lifetime_vmt(reg_class_id, model_year):
        """
        Get lifetime VMT as a function of regulatory class and model year.

        Args:
            reg_class_id (str): e.g. 'car','truck'
            model_year (numeric): model year

        Returns:

            Lifetime VMT for the regulatory class and model year.

        """
        start_years = VehicleTargets._data[reg_class_id]['start_year']
        if len(start_years[start_years <= model_year]) > 0:
            model_year = max(start_years[start_years <= model_year])

            return VehicleTargets._data[reg_class_id, model_year]['lifetime_vmt']
        else:
            raise Exception('Missing GHG target lifetime VMT parameters for %s, %d or prior'
                            % (reg_class_id, model_year))

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

        from policy.incentives import Incentives

        start_years = VehicleTargets._data[vehicle.reg_class_id]['start_year']
        if len(start_years[start_years <= vehicle.model_year]) > 0:
            vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

            vehicle.lifetime_VMT = VehicleTargets.calc_cert_lifetime_vmt(vehicle.reg_class_id, vehicle_model_year)

            co2_gpmi = VehicleTargets.calc_target_co2e_gpmi(vehicle)

            if sales_variants is not None:
                if not (type(sales_variants) is pd.Series) or (type(sales_variants) is np.ndarray):
                    sales = np.array(sales_variants)
                else:
                    sales = sales_variants
            else:
                sales = vehicle.initial_registered_count

            return co2_gpmi * vehicle.lifetime_VMT * sales * Incentives.get_production_multiplier(vehicle) / 1e6
        else:
            raise Exception('Missing GHG target parameters for %s, %d or prior'
                            % (vehicle.reg_class_id, vehicle.model_year))

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

        from policy.incentives import Incentives

        start_years = VehicleTargets._data[vehicle.reg_class_id]['start_year']
        if len(start_years[start_years <= vehicle.model_year]) > 0:
            vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

            vehicle.lifetime_VMT = VehicleTargets.calc_cert_lifetime_vmt(vehicle.reg_class_id, vehicle_model_year)

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

            return co2_gpmi * vehicle.lifetime_VMT * sales * Incentives.get_production_multiplier(vehicle) / 1e6
        else:
            raise Exception('Missing GHG target parameters for %s, %d or prior'
                            % (vehicle.reg_class_id, vehicle.model_year))

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
        VehicleTargets._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.11
        input_template_columns = {'start_year', 'reg_class_id', 'ghg_target_co2e_grams_per_mile', 'lifetime_vmt'}

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
            VehicleTargets._data = df.set_index(['reg_class_id', 'start_year']).sort_index().to_dict(
                orient='index')

            for rc in df['reg_class_id'].unique():
                VehicleTargets._data[rc] = {
                    'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':
    try:

        __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        omega_globals.options.policy_targets_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + \
                                                    '../test_inputs/ghg_standards-alternative.csv'
        omega_log.init_logfile()

        # 

        from policy.incentives import Incentives
        init_fail += Incentives.init_from_file(omega_globals.options.production_multipliers_file,
                                               verbose=omega_globals.options.verbose)

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
                initial_registered_count = None
                cert_co2e_grams_per_mile = 150

                def get_initial_registered_count(self):
                    """
                    Get initial registered count

                    Returns:
                        Initial registered count
                    """
                    return self.initial_registered_count

            car_vehicle = VehicleDummy()
            car_vehicle.model_year = 2021
            car_vehicle.reg_class_id = 'car'
            car_vehicle.initial_registered_count = 1
            car_vehicle.fueling_class = 'BEV'

            truck_vehicle = VehicleDummy()
            truck_vehicle.model_year = 2021
            truck_vehicle.reg_class_id = 'truck'
            truck_vehicle.initial_registered_count = 1
            truck_vehicle.fueling_class = 'ICE'

            car_target_co2e_gpmi = omega_globals.options.VehicleTargets.calc_target_co2e_gpmi(car_vehicle)
            car_target_co2e_Mg = omega_globals.options.VehicleTargets.calc_target_co2e_Mg(car_vehicle)
            car_certs_co2e_Mg = omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(car_vehicle)
            car_certs_sales_co2e_Mg = omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(car_vehicle,
                                                                                             sales_variants=[1, 2, 3,
                                                                                                             4])

            truck_target_co2e_gpmi = omega_globals.options.VehicleTargets.calc_target_co2e_gpmi(truck_vehicle)
            truck_target_co2e_Mg = omega_globals.options.VehicleTargets.calc_target_co2e_Mg(truck_vehicle)
            truck_certs_co2e_Mg = omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(truck_vehicle)
            truck_certs_sales_co2e_Mg = omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(truck_vehicle,
                                                                                               sales_variants=[1, 2, 3,
                                                                                                               4])
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
