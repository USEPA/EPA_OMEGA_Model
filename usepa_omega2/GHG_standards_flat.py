"""
GHG_standards_flat.py
=====================


"""

from usepa_omega2 import *


class GHGStandardFlat(SQABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards'
    index = Column(Integer, primary_key=True)
    model_year = Column(Numeric)
    reg_class_ID = Column('reg_class_id', Enum(*reg_classes, validate_strings=True))
    GHG_target_CO2_grams_per_mile = Column('ghg_target_co2_grams_per_mile', Float)
    lifetime_VMT = Column('lifetime_vmt', Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    # noinspection PyMethodParameters
    @staticmethod
    def init_database_from_file(filename, session, verbose=False):
        omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'ghg_standards-flat'
        input_template_version = 0.0002
        input_template_columns = {'model_year', 'reg_class_id', 'ghg_target_co2_grams_per_mile', 'lifetime_vmt'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

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
                session.add_all(obj_list)
                session.flush()

        return template_errors

    @staticmethod
    def calculate_target_co2_gpmi(vehicle):
        return session.query(GHGStandardFlat.GHG_target_CO2_grams_per_mile). \
            filter(GHGStandardFlat.reg_class_ID == vehicle.reg_class_ID). \
            filter(GHGStandardFlat.model_year == vehicle.model_year).scalar()

    @staticmethod
    def calculate_target_co2_Mg(vehicle):
        return session.query(GHGStandardFlat.lifetime_VMT). \
            filter(GHGStandardFlat.reg_class_ID == vehicle.reg_class_ID). \
            filter(GHGStandardFlat.model_year == vehicle.model_year).scalar() * \
            GHGStandardFlat.calculate_target_co2_gpmi(vehicle) / 1e6


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2_options.ghg_standards_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

        o2_options.GHG_standard = GHGStandardFlat

        class dummyVehicle():
            model_year = None
            reg_class_ID = None

        car_vehicle = dummyVehicle()
        car_vehicle.model_year = 2021
        car_vehicle.reg_class_ID = RegClass.car

        truck_vehicle = dummyVehicle()
        truck_vehicle.model_year = 2021
        truck_vehicle.reg_class_ID = RegClass.truck

        car_target_co2_gpmi = o2_options.GHG_standard.calculate_target_co2_gpmi(car_vehicle)
        truck_target_co2_gpmi = o2_options.GHG_standard.calculate_target_co2_gpmi(truck_vehicle)
