"""
GHG_standards_flat.py
=====================


"""

import o2  # import global variables
from usepa_omega2 import *


class GHGStandardFlat(SQABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards_flat'
    index = Column(Integer, primary_key=True)
    model_year = Column(Numeric)
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    GHG_target_CO2_grams_per_mile = Column('ghg_target_co2_grams_per_mile', Float)
    lifetime_VMT = Column('lifetime_vmt', Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__, id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    # noinspection PyMethodParameters
    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'ghg_standards-flat'
        input_template_version = 0.0002
        input_template_columns = {'model_year', 'reg_class_id', 'ghg_target_co2_grams_per_mile', 'lifetime_vmt'}

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
                        model_year=df.loc[i, 'model_year'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        GHG_target_CO2_grams_per_mile=df.loc[i, 'ghg_target_co2_grams_per_mile'],
                        lifetime_VMT=df.loc[i, 'lifetime_vmt'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors

    @staticmethod
    def calculate_target_co2_gpmi(vehicle):
        return o2.session.query(GHGStandardFlat.GHG_target_CO2_grams_per_mile). \
            filter(GHGStandardFlat.reg_class_ID == vehicle.reg_class_ID). \
            filter(GHGStandardFlat.model_year == vehicle.model_year).scalar()

    @staticmethod
    def calculate_cert_lifetime_vmt(reg_class_id, model_year):
        return o2.session.query(GHGStandardFlat.lifetime_VMT). \
            filter(GHGStandardFlat.reg_class_ID == reg_class_id). \
            filter(GHGStandardFlat.model_year == model_year).scalar()

    @staticmethod
    def calculate_target_co2_Mg(vehicle, sales_variants=None):
        import numpy as np

        lifetime_VMT = GHGStandardFlat.calculate_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle.model_year)

        co2_gpmi = GHGStandardFlat.calculate_target_co2_gpmi(vehicle)

        if sales_variants:
            sales = np.array(sales_variants)
        else:
            sales = vehicle.get_initial_registered_count()

        return co2_gpmi * lifetime_VMT * sales / 1e6

    @staticmethod
    def calculate_cert_co2_Mg(vehicle, co2_gpmi_variants=None, sales_variants=[1]):
        import numpy as np

        lifetime_VMT = GHGStandardFlat.calculate_cert_lifetime_vmt(vehicle.reg_class_ID, vehicle.model_year)

        if co2_gpmi_variants:
            sales = np.array(sales_variants)
            co2_gpmi = np.array(co2_gpmi_variants)
        else:
            sales = vehicle.get_initial_registered_count()
            co2_gpmi = vehicle.cert_CO2_grams_per_mile

        return co2_gpmi * lifetime_VMT * sales / 1e6


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    o2.options.ghg_standards_file = 'input_templates\\ghg_standards-flat.csv'
    init_omega_db()
    omega_log.init_logfile()

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2.options.ghg_standards_file,
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
