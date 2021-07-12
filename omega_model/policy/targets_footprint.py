"""

**Loads parameters and provides calculations for an attribute-based (vehicle footprint) GHG standard.**

This is based on the current standards, with two regulatory classes with lifetime VMT and
parameter-based target calculations that define a "footprint curve" based on four coefficients
("A" through "D") and min and max footprint limits.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The header uses a dynamic format.

The data represents a set of GHG standards (vehicle target CO2 g/mi) by regulatory class and model year as a function
of vehicle footprint in square feet.

File Type
    comma-separated values (CSV)

Template Header
    input_template_name:, ``[module_name]``, input_template_version:, ``[template_version]``

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
    Lifetime Vehicle Miles Travelled for computing CO2 Mg

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

cache = dict()


class Targets(OMEGABase, SQABase, TargetsBase):
    """
    Implement vehicle footprint-based GHG targets (CO2 g/mi)

    """
    # --- database table properties ---
    __tablename__ = 'targets_footprint'
    index = Column(Integer, primary_key=True)  #: database index
    model_year = Column(Numeric)  #: model year (or start year of the applied parameters)
    reg_class_ID = Column('reg_class_id', Enum(*omega_globals.options.RegulatoryClasses.reg_classes,
                                               validate_strings=True))  #: reg class name, e.g. 'car','truck'
    footprint_min_sqft = Column('footprint_min_sqft', Float)  #: minimum footprint (square feet) of curve
    footprint_max_sqft = Column('footprint_max_sqft', Float)  #: maximum footprint (square feet) of curve
    coeff_a = Column('coeff_a', Float)  #: footprint curve A coefficient
    coeff_b = Column('coeff_b', Float)  #: footprint curve B coefficient
    coeff_c = Column('coeff_c', Float)  #: footprint curve C coefficient
    coeff_d = Column('coeff_d', Float)  #: footprint curve D coefficient
    lifetime_VMT = Column('lifetime_vmt', Float)  #: regulatory lifetime VMT (in miles) of the given reg class

    @staticmethod
    def calc_target_co2_gpmi(vehicle):
        """
        Calculate vehicle target CO2 g/mi.

        Args:
            vehicle (Vehicle): the vehicle to get the target for

        Returns:

            Vehicle target CO2 in g/mi.

        """
        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        cache_key = '%s_%s_coefficients' % (vehicle_model_year, vehicle.reg_class_ID)
        if cache_key not in cache:
            cache[cache_key] = omega_globals.session.query(Targets). \
                filter(Targets.reg_class_ID == vehicle.reg_class_ID). \
                filter(Targets.model_year == vehicle_model_year).one()
        coefficients = cache[cache_key]

        if vehicle.footprint_ft2 <= coefficients.footprint_min_sqft:
            target_co2_gpmi = coefficients.coeff_a
        elif vehicle.footprint_ft2 > coefficients.footprint_max_sqft:
            target_co2_gpmi = coefficients.coeff_b
        else:
            target_co2_gpmi = vehicle.footprint_ft2 * coefficients.coeff_c + coefficients.coeff_d

        return target_co2_gpmi

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
        start_years = cache[reg_class_id]['start_year']
        model_year = max(start_years[start_years <= model_year])

        cache_key = '%s_%s_lifetime_vmt' % (model_year, reg_class_id)
        if cache_key not in cache:
            cache[cache_key] = omega_globals.session.query(Targets.lifetime_VMT). \
                filter(Targets.reg_class_ID == reg_class_id). \
                filter(Targets.model_year == model_year).scalar()
        return cache[cache_key]

    @staticmethod
    def calc_target_co2_Mg(vehicle, sales_variants=None):
        """
        Calculate vehicle target CO2 Mg as a function of the vehicle, the standards and optional sales options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Target CO2 Mg value(s) for the given vehicle and/or sales variants.

        """
        import numpy as np
        from policy.incentives import Incentives

        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        lifetime_VMT = Targets.calc_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle_model_year)

        co2_gpmi = Targets.calc_target_co2_gpmi(vehicle)

        if sales_variants is not None:
            if not (type(sales_variants) == pd.Series) or (type(sales_variants) == np.ndarray):
                sales = np.array(sales_variants)
            else:
                sales = sales_variants
        else:
            sales = vehicle.initial_registered_count

        return co2_gpmi * lifetime_VMT * sales * Incentives.get_production_multiplier(vehicle) / 1e6

    @staticmethod
    def calc_cert_co2_Mg(vehicle, co2_gpmi_variants=None, sales_variants=[1]):
        """
        Calculate vehicle cert CO2 Mg as a function of the vehicle, the standards, CO2 g/mi options and optional sales
        options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Cert CO2 Mg value(s) for the given vehicle, CO2 g/mi variants and/or sales variants.

        """
        import numpy as np
        from policy.incentives import Incentives

        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        lifetime_VMT = Targets.calc_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle_model_year)

        if co2_gpmi_variants is not None:
            if not (type(sales_variants) == pd.Series) or (type(sales_variants) == np.ndarray):
                sales = np.array(sales_variants)
            else:
                sales = sales_variants

            if not (type(co2_gpmi_variants) == pd.Series) or (type(co2_gpmi_variants) == np.ndarray):
                co2_gpmi = np.array(co2_gpmi_variants)
            else:
                co2_gpmi = co2_gpmi_variants
        else:
            sales = vehicle.initial_registered_count
            co2_gpmi = vehicle.cert_co2_grams_per_mile

        return co2_gpmi * lifetime_VMT * sales * Incentives.get_production_multiplier(vehicle) / 1e6

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
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.11
        input_template_columns = {'start_year', 'reg_class_id', 'fp_min', 'fp_max', 'a_coeff', 'b_coeff', 'c_coeff',
                                  'd_coeff', 'lifetime_vmt'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(Targets(
                        model_year=df.loc[i, 'start_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        footprint_min_sqft=df.loc[i, 'fp_min'],
                        footprint_max_sqft=df.loc[i, 'fp_max'],
                        coeff_a=df.loc[i, 'a_coeff'],
                        coeff_b=df.loc[i, 'b_coeff'],
                        coeff_c=df.loc[i, 'c_coeff'],
                        coeff_d=df.loc[i, 'd_coeff'],
                        lifetime_VMT=df.loc[i, 'lifetime_vmt'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                for rc in df['reg_class_id'].unique():
                    cache[rc] = {'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':
    try:

        __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        # omega_globals.options.policy_targets_input_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'demo_inputs/ghg_standards-footprint.csv'
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += Targets.init_from_file(omega_globals.options.policy_targets_file,
                                            verbose=omega_globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            omega_globals.options.PolicyTargets = Targets


            class dummyVehicle:
                model_year = None
                reg_class_ID = None
                footprint_ft2 = None
                initial_registered_count = None

                def get_initial_registered_count(self):
                    return self.initial_registered_count


            car_vehicle = dummyVehicle()
            car_vehicle.model_year = 2021
            car_vehicle.reg_class_ID = reg_classes.car
            car_vehicle.footprint_ft2 = 41
            car_vehicle.initial_registered_count = 1

            truck_vehicle = dummyVehicle()
            truck_vehicle.model_year = 2021
            truck_vehicle.reg_class_ID = reg_classes.truck
            truck_vehicle.footprint_ft2 = 41
            truck_vehicle.initial_registered_count = 1

            car_target_co2_gpmi = omega_globals.options.PolicyTargets.calc_target_co2_gpmi(car_vehicle)
            car_target_co2_Mg = omega_globals.options.PolicyTargets.calc_target_co2_Mg(car_vehicle)
            car_certs_co2_Mg = omega_globals.options.PolicyTargets.calc_cert_co2_Mg(car_vehicle,
                                                                                    co2_gpmi_variants=[0, 50, 100, 150])
            car_certs_sales_co2_Mg = omega_globals.options.PolicyTargets.calc_cert_co2_Mg(car_vehicle,
                                                                                          co2_gpmi_variants=[0, 50, 100, 150],
                                                                                          sales_variants=[1, 2, 3, 4])

            truck_target_co2_gpmi = omega_globals.options.PolicyTargets.calc_target_co2_gpmi(truck_vehicle)
            truck_target_co2_Mg = omega_globals.options.PolicyTargets.calc_target_co2_Mg(truck_vehicle)
            truck_certs_co2_Mg = omega_globals.options.PolicyTargets.calc_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150])
            truck_certs_sales_co2_Mg = omega_globals.options.PolicyTargets.calc_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150],
                                                                                            sales_variants=[1, 2, 3, 4])
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)