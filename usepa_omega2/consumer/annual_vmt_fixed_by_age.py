"""
annual_vmt_fixed_by_age.py
=============================


"""

from usepa_omega2 import *


class AnnualVMTFixedByAge(SQABase):
    # --- database table properties ---
    __tablename__ = 'annual_vmt_fixed_by_age'
    index = Column('index', Integer, primary_key=True)

    age = Column('age', Numeric)
    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    reregistered_proportion = Column('annual_vmt', Float)

    def __repr__(self):
        return f"<OMEGA2 {type(self).__name__} object at 0x{id(self)}>"

    @staticmethod
    def init_database_from_file(filename, session, verbose=False):
        omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'annual_vmt_fixed_by_age'
        input_template_version = 0.0001
        input_template_columns = {'age', 'market_class_id', 'annual_vmt'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(AnnualVMTFixedByAge(
                        age=df.loc[i, 'age'],
                        market_class_ID=df.loc[i, 'market_class_id'],
                        reregistered_proportion=df.loc[i, 'annual_vmt'],
                    ))
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from usepa_omega2.market_classes import MarketClass  # needed for market class ID

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + MarketClass.init_database_from_file(o2_options.market_classes_file, session, verbose=o2_options.verbose)

    init_fail = init_fail + AnnualVMTFixedByAge.init_database_from_file(o2_options.annual_vmt_fixed_by_age_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)
