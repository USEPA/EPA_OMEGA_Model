"""
showroom_annual_data.py
=======================


"""

from usepa_omega2 import *


class ShowroomData(SQABase):
    # --- database table properties ---
    __tablename__ = 'showroom_annual_data'
    market_class_ID = Column('market_class_id', Integer, primary_key=True)

    annual_VMT = Column('annual_vmt', Numeric)
    calendar_year = Column(Float)
    demanded_sales_count = Column(Numeric)

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
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    # dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)
