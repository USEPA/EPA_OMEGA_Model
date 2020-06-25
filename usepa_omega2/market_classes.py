"""
market_classes.py
=================


"""

from usepa_omega2 import *


class MarketClass(SQABase):
    # --- database table properties ---
    __tablename__ = 'market_classes'
    market_class_ID = Column('market_class_id', String, primary_key=True)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    ownership_class = Column(Enum(*ownership_classes, validate_strings=True))

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def init_database(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        input_template_name = 'market_classes'
        input_template_version = 0.0002
        input_template_columns = {'market_class_id', 'hauling_class', 'fueling_class', 'ownership_class'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(MarketClass(
                        market_class_ID = df.loc[i, 'market_class_id'],
                        fueling_class=df.loc[i, 'fueling_class'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        ownership_class=df.loc[i, 'ownership_class'],
                    ))
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + MarketClass.init_database(o2_options.market_classes_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)
