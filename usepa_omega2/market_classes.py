"""
market_classes.py
==========


"""

from usepa_omega2 import *


class MarketClass(SQABase):
    # --- database table properties ---
    __tablename__ = 'market_classes'
    market_class_ID = Column('market_class_id', Integer, primary_key=True)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    ownership_class = Column(Enum(*ownership_classes, validate_strings=True))

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    # def init_database(filename, session, verbose=False):
    #     print('\nInitializing database from %s...' % filename)
    #
    #     template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)
    #
    #     if not template_errors:
    #         # read in the data portion of the input file
    #         df = pd.read_csv(filename, skiprows=1)
    #
    #         template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)
    #
    #         if not template_errors:
    #             pass
    #
    #     return template_errors


if __name__ == '__main__':
    print(fileio.get_filenameext(__file__))

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)
