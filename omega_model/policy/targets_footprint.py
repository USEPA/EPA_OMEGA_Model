"""

**Loads parameters and provides calculations for an attribute-based (vehicle footprint) GHG standard.**

This is based on the current standards, with two regulatory classes with lifetime VMT and
parameter-based target calculations that define a "footprint curve" based on four coefficients
("A" through "D") and min and max footprint limits.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents a set of GHG standards (vehicle target CO2e g/mi) by regulatory class and model year as a function
of vehicle footprint in square feet.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,policy.targets_footprint,input_template_version:,0.11

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,start_year,fp_min,fp_max,a_coeff,b_coeff,c_coeff,d_coeff,lifetime_vmt
        car,2020,41,56,166,226,4.01,1.9,195264
        truck,2020,41,68.3,212,337,4.57,24.6,225865

Data Column Name and Description

:reg_class_id:
    Regulatory class name, e.g. 'car', 'truck'

:start_year:
    The start year of the standard coefficients, applies until the next available start year

:fp_min:
    Minimum footprint limit of the curve (square feet)

:fp_max:
    Maximum footprint limit of the curve (square feet)

:a_coeff:
    Footprint curve "A" coefficient

:b_coeff:
    Footprint curve "B" coefficient

:c_coeff:
    Footprint curve "C" coefficient

:d_coeff:
    Footprint curve "D" coefficient

:lifetime_vmt:
    Lifetime Vehicle Miles Travelled for computing CO2e Mg

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
from policy.incentives import Incentives


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
    **Implements vehicle footprint-based GHG targets (CO2e g/mi).**

    """

    _data = dict()  # private dict, footprint-based GHG target parameters by reg class ID and start year

    @staticmethod
    def calc_target_co2e_gpmi(vehicle):
        """
        Calculate vehicle target CO2e g/mi.

        Args:
            vehicle (Vehicle): the vehicle to get the target for

        Returns:

            Vehicle target CO2e in g/mi.

        """
        cache_key = (vehicle.model_year, vehicle.reg_class_id, vehicle.footprint_ft2)

        if cache_key not in VehicleTargets._data:

            start_years = VehicleTargets._data[vehicle.reg_class_id]['start_year']

            if len(start_years[start_years <= vehicle.model_year]) > 0:
                model_year = max(start_years[start_years <= vehicle.model_year])

                coefficients = VehicleTargets._data[vehicle.reg_class_id, model_year]

                if vehicle.footprint_ft2 <= coefficients['fp_min']:
                    target_co2e_gpmi = coefficients['a_coeff']
                elif vehicle.footprint_ft2 > coefficients['fp_max']:
                    target_co2e_gpmi = coefficients['b_coeff']
                else:
                    target_co2e_gpmi = vehicle.footprint_ft2 * coefficients['c_coeff'] + coefficients['d_coeff']

                VehicleTargets._data[cache_key] = target_co2e_gpmi
                # return target_co2e_gpmi
            else:
                raise Exception('Missing GHG CO2e g/mi target parameters for %s, %d or prior'
                                % (vehicle.reg_class_id, vehicle.model_year))

        return VehicleTargets._data[cache_key]

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
        cache_key = (reg_class_id, model_year, 'lifetime_vmt')

        if cache_key not in VehicleTargets._data:
            start_years = VehicleTargets._data[reg_class_id]['start_year']

            if len(start_years[start_years <= model_year]) > 0:
                year = max(start_years[start_years <= model_year])

                VehicleTargets._data[cache_key] = VehicleTargets._data[reg_class_id, year]['lifetime_vmt']
            else:
                raise Exception('Missing GHG target lifetime VMT parameters for %s, %d or prior'
                                % (reg_class_id, model_year))

        return VehicleTargets._data[cache_key]

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
        input_template_columns = {'start_year', 'reg_class_id', 'fp_min', 'fp_max', 'a_coeff', 'b_coeff', 'c_coeff',
                                  'd_coeff', 'lifetime_vmt'}

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
            VehicleTargets._data = df.set_index(['reg_class_id', 'start_year']).sort_index().to_dict(orient='index')

            for rc in df['reg_class_id'].unique():
                VehicleTargets._data[rc] = {'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':
    try:

        __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

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
                footprint_ft2 = None
                initial_registered_count = None

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
            car_vehicle.footprint_ft2 = 41
            car_vehicle.initial_registered_count = 1
            car_vehicle.fueling_class = 'BEV'

            truck_vehicle = VehicleDummy()
            truck_vehicle.model_year = 2021
            truck_vehicle.reg_class_id = 'truck'
            truck_vehicle.footprint_ft2 = 41
            truck_vehicle.initial_registered_count = 1
            truck_vehicle.fueling_class = 'ICE'

            car_target_co2e_gpmi = omega_globals.options.VehicleTargets.calc_target_co2e_gpmi(car_vehicle)

            car_target_co2e_Mg = omega_globals.options.VehicleTargets.calc_target_co2e_Mg(car_vehicle)

            car_certs_co2e_Mg = \
                omega_globals.options.VehicleTargets.calc_cert_co2e_Mg(car_vehicle,
                                                                       co2_gpmi_variants=[0, 50, 100, 150])
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
