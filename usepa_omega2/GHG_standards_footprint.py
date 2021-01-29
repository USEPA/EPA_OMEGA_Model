"""
GHG_standards_footprint.py
==========================


"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *

input_template_name = 'ghg_standards-footprint'

class GHGStandardFootprint(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards_footprint'
    index = Column(Integer, primary_key=True)
    model_year = Column(Numeric)
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    footprint_min_sqft = Column('footprint_min_sqft', Float)
    footprint_max_sqft = Column('footprint_max_sqft', Float)
    coeff_a = Column('coeff_a', Float)
    coeff_b = Column('coeff_b', Float)
    coeff_c = Column('coeff_c', Float)
    coeff_d = Column('coeff_d', Float)
    lifetime_VMT = Column('lifetime_vmt', Float)

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.0003
        input_template_columns = {'model_year', 'reg_class_id', 'fp_min', 'fp_max', 'a_coeff', 'b_coeff', 'c_coeff',
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
                    obj_list.append(GHGStandardFootprint(
                        model_year=df.loc[i, 'model_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        footprint_min_sqft=df.loc[i, 'fp_min'],
                        footprint_max_sqft=df.loc[i, 'fp_max'],
                        coeff_a=df.loc[i, 'a_coeff'],
                        coeff_b=df.loc[i, 'b_coeff'],
                        coeff_c=df.loc[i, 'c_coeff'],
                        coeff_d=df.loc[i, 'd_coeff'],
                        lifetime_VMT=df.loc[i, 'lifetime_vmt'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors

    @staticmethod
    def calculate_target_co2_gpmi(vehicle):
        coefficients = o2.session.query(GHGStandardFootprint). \
            filter(GHGStandardFootprint.reg_class_ID == vehicle.reg_class_ID). \
            filter(GHGStandardFootprint.model_year == vehicle.model_year).one()

        if vehicle.footprint_ft2 <= coefficients.footprint_min_sqft:
            target_co2_gpmi = coefficients.coeff_a
        elif vehicle.footprint_ft2 > coefficients.footprint_max_sqft:
            target_co2_gpmi = coefficients.coeff_b
        else:
            target_co2_gpmi = vehicle.footprint_ft2 * coefficients.coeff_c + coefficients.coeff_d

        return target_co2_gpmi

    @staticmethod
    def calculate_cert_lifetime_vmt(reg_class_id, model_year):
        return o2.session.query(GHGStandardFootprint.lifetime_VMT). \
            filter(GHGStandardFootprint.reg_class_ID == reg_class_id). \
            filter(GHGStandardFootprint.model_year == model_year).scalar()

    @staticmethod
    def calculate_target_co2_Mg(vehicle, sales_variants=None):
        import numpy as np

        lifetime_VMT = GHGStandardFootprint.calculate_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle.model_year)

        co2_gpmi = GHGStandardFootprint.calculate_target_co2_gpmi(vehicle)

        if sales_variants is not None:
            if not (type(sales_variants) == pd.Series) or (type(sales_variants) == np.ndarray):
                sales = np.array(sales_variants)
            else:
                sales = sales_variants
        else:
            sales = vehicle.initial_registered_count

        return co2_gpmi * lifetime_VMT * sales / 1e6

    @staticmethod
    def calculate_cert_co2_Mg(vehicle, co2_gpmi_variants=None, sales_variants=[1]):
        import numpy as np

        lifetime_VMT = GHGStandardFootprint.calculate_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle.model_year)

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
            co2_gpmi = vehicle.cert_CO2_grams_per_mile

        return co2_gpmi * lifetime_VMT * sales / 1e6


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        o2.options.ghg_standards_file = 'test_inputs/ghg_standards-footprint.csv'
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            o2.options.GHG_standard = GHGStandardFootprint


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

            car_target_co2_gpmi = o2.options.GHG_standard.calculate_target_co2_gpmi(car_vehicle)
            car_target_co2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(car_vehicle)
            car_certs_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(car_vehicle,
                                                                             co2_gpmi_variants=[0, 50, 100, 150])
            car_certs_sales_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(car_vehicle,
                                                                                   co2_gpmi_variants=[0, 50, 100, 150],
                                                                                   sales_variants=[1, 2, 3, 4])

            truck_target_co2_gpmi = o2.options.GHG_standard.calculate_target_co2_gpmi(truck_vehicle)
            truck_target_co2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(truck_vehicle)
            truck_certs_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150])
            truck_certs_sales_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150],
                                                                                     sales_variants=[1, 2, 3, 4])
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)