"""
GHG_standards_footprint.py
==========================


"""

from usepa_omega2 import *


class GHGStandardFootprint(SQABase):
    # --- database table properties ---
    __tablename__ = 'ghg_standards'
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

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def __str__(self):
        s = ''  # '"<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    # noinspection PyMethodParameters
    def init_database_from_file(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        input_template_name = 'ghg_standards-footprint'
        input_template_version = 0.0003
        input_template_columns = {'model_year', 'reg_class_id', 'fp_min', 'fp_max', 'a_coeff', 'b_coeff', 'c_coeff',
                                  'd_coeff', 'lifetime_vmt'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

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
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2_options.ghg_standards_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)