"""
GHG_standards_flat.py
=====================


"""

print('importing %s' % __file__)

from usepa_omega2 import *

input_template_name = 'ghg_standards-flat'

cache = dict()


class GHGStandardFlat(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards_flat'
    index = Column(Integer, primary_key=True)
    model_year = Column(Numeric)
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    GHG_target_co2_grams_per_mile = Column('ghg_target_co2_grams_per_mile', Float)
    lifetime_VMT = Column('lifetime_vmt', Float)

    @staticmethod
    def get_vehicle_reg_class(vehicle):
        """
        Return vehicle reg class based on vehicle characteristics
        Args:
            vehicle: vehicle object

        Returns: vehicle reg class based on vehicle characteristics

        """
        reg_class_ID = vehicle.reg_class_ID
        return reg_class_ID

    @staticmethod
    def calc_target_co2_gpmi(vehicle):
        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        cache_key = '%s_%s_target_co2_gpmi' % (vehicle.model_year, vehicle.reg_class_ID)
        if cache_key not in cache:
            cache[cache_key] = o2.session.query(GHGStandardFlat.GHG_target_co2_grams_per_mile). \
                filter(GHGStandardFlat.reg_class_ID == vehicle.reg_class_ID). \
                filter(GHGStandardFlat.model_year == vehicle_model_year).scalar()
        return cache[cache_key]

    @staticmethod
    def calc_cert_lifetime_vmt(reg_class_id, model_year):
        start_years = cache[reg_class_id]['start_year']
        model_year = max(start_years[start_years <= model_year])

        cache_key = '%s_%s_lifetime_vmt' % (model_year, reg_class_id)
        if cache_key not in cache:
            cache[cache_key] = o2.session.query(GHGStandardFlat.lifetime_VMT). \
                filter(GHGStandardFlat.reg_class_ID == reg_class_id). \
                filter(GHGStandardFlat.model_year == model_year).scalar()
        return cache[cache_key]

    @staticmethod
    def calc_target_co2_Mg(vehicle, sales_variants=None):
        import numpy as np
        from GHG_standards_incentives import GHGStandardIncentives

        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        lifetime_VMT = GHGStandardFlat.calc_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle_model_year)

        co2_gpmi = GHGStandardFlat.calc_target_co2_gpmi(vehicle)

        if sales_variants is not None:
            if not (type(sales_variants) == pd.Series) or (type(sales_variants) == np.ndarray):
                sales = np.array(sales_variants)
            else:
                sales = sales_variants
        else:
            sales = vehicle.initial_registered_count

        return co2_gpmi * lifetime_VMT * sales * GHGStandardIncentives.get_production_multiplier(vehicle) / 1e6

    @staticmethod
    def calc_cert_co2_Mg(vehicle, co2_gpmi_variants=None, sales_variants=[1]):
        import numpy as np
        from GHG_standards_incentives import GHGStandardIncentives

        start_years = cache[vehicle.reg_class_ID]['start_year']
        vehicle_model_year = max(start_years[start_years <= vehicle.model_year])

        lifetime_VMT = GHGStandardFlat.calc_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle_model_year)

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

        return co2_gpmi * lifetime_VMT * sales * GHGStandardIncentives.get_production_multiplier(vehicle) / 1e6

    @staticmethod
    def init_database_from_file(filename, verbose=False):

        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.1
        input_template_columns = {'start_year', 'reg_class_id', 'ghg_target_co2_grams_per_mile', 'lifetime_vmt'}

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
                    obj_list.append(GHGStandardFlat(
                        model_year=df.loc[i, 'start_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        GHG_target_co2_grams_per_mile=df.loc[i, 'ghg_target_co2_grams_per_mile'],
                        lifetime_VMT=df.loc[i, 'lifetime_vmt'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

                for rc in df['reg_class_id'].unique():
                    cache[rc] = {'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        o2.options.ghg_standards_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'test_inputs/ghg_standards-flat.csv'
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail += GHGStandardFlat.init_database_from_file(o2.options.ghg_standards_file,
                                                                        verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            o2.options.GHG_standard = GHGStandardFlat

            class dummyVehicle:
                model_year = None
                reg_class_ID = None
                initial_registered_count = None

                def get_initial_registered_count(self):
                    return self.initial_registered_count


            car_vehicle = dummyVehicle()
            car_vehicle.model_year = 2021
            car_vehicle.reg_class_ID = reg_classes.car
            car_vehicle.initial_registered_count = 1

            truck_vehicle = dummyVehicle()
            truck_vehicle.model_year = 2021
            truck_vehicle.reg_class_ID = reg_classes.truck
            truck_vehicle.initial_registered_count = 1

            car_target_co2_gpmi = o2.options.GHG_standard.calc_target_co2_gpmi(car_vehicle)
            car_target_co2_Mg = o2.options.GHG_standard.calc_target_co2_Mg(car_vehicle)
            car_certs_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(car_vehicle,
                                                                             co2_gpmi_variants=[0, 50, 100, 150])
            car_certs_sales_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(car_vehicle,
                                                                                   co2_gpmi_variants=[0, 50, 100, 150],
                                                                                   sales_variants=[1, 2, 3, 4])

            truck_target_co2_gpmi = o2.options.GHG_standard.calc_target_co2_gpmi(truck_vehicle)
            truck_target_co2_Mg = o2.options.GHG_standard.calc_target_co2_Mg(truck_vehicle)
            truck_certs_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150])
            truck_certs_sales_co2_Mg = o2.options.GHG_standard.calc_cert_co2_Mg(truck_vehicle, [0, 50, 100, 150],
                                                                                     sales_variants=[1, 2, 3, 4])
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
