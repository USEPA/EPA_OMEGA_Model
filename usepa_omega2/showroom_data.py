"""
showroom_data.py
==========


"""

from usepa_omega2 import *


class ShowroomDatum(SQABase):
    # --- database table properties ---
    __tablename__ = 'showroom_data'
    market_class_ID = Column('market_class_id', String, primary_key=True)

    annual_VMT = Column('annual_vmt', Numeric)
    payback_years = Column(Float)
    price_amortization_period = Column(Float)
    discount_rate = Column(Float)
    share_weight = Column(Float)

    def __repr__(self):
        return "<OMEGA2 %s object at 0x%x>" % (type(self).__name__,  id(self))

    def init_database(filename, session, verbose=False):
        print('\nInitializing database from %s...' % filename)

        input_template_name = 'showroom_data'
        input_template_version = 0.0002
        input_template_columns = {'market_class_id', 'annual_vmt', 'payback_years', 'price_amortization_period',
                                  'share_weight', 'discount_rate'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(ShowroomDatum(
                        market_class_ID=df.loc[i, 'market_class_id'],
                        annual_VMT=df.loc[i, 'annual_vmt'],
                        payback_years=df.loc[i, 'payback_years'],
                        price_amortization_period=df.loc[i, 'price_amortization_period'],
                        discount_rate=df.loc[i, 'share_weight'],
                        share_weight=df.loc[i, 'discount_rate'],
                    ))
                session.add_all(obj_list)
                session.flush()

        return template_errors


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + ShowroomDatum.init_database(o2_options.showroom_data_file, session, verbose=o2_options.verbose)

    if not init_fail:
        dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)
