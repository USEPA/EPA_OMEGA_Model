"""
showroom_data.py
==========


"""

from usepa_omega2 import *


class ShowroomData(SQABase):
    # --- database table properties ---
    __tablename__ = 'showroom_data'
    market_class_ID = Column('market_class_id', Integer, primary_key=True)

    annual_VMT = Column('annual_vmt', Numeric)
    payback_years = Column(Float)
    price_amortization_period = Column(Float)
    discount_rate = Column(Float)
    share_weight = Column(Float)

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
