"""


----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class DemandedSharesGCAM(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'demanded_shares_gcam'
    index = Column('index', Integer, primary_key=True)

    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))
    annual_VMT = Column('annual_vmt', Numeric)
    calendar_year = Column(Float)
    payback_years = Column(Float)
    price_amortization_period = Column(Float)
    discount_rate = Column(Float)
    share_weight = Column(Float)
    demanded_share = Column(Numeric)
    consumer_generalized_cost_dollars = Column(Float)
    o_m_costs = Column(Float)
    average_occupancy = Column(Float)
    logit_exponent_mu = Column(Float)

    @staticmethod
    def get_gcam_params(calendar_year, market_class_id):
        """

        Args:
            calendar_year:
            market_class_id:

        Returns: GCAM parameters for the given calendar year and market class

        """

        start_years = cache[market_class_id]['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        key = '%s_%s' % (calendar_year, market_class_id)
        if not key in cache:
            cache[key] = o2.session.query(DemandedSharesGCAM). \
                filter(DemandedSharesGCAM.calendar_year == calendar_year). \
                filter(DemandedSharesGCAM.market_class_ID == market_class_id).one()

        return cache[key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'demanded_shares_gcam'
        input_template_version = 0.12
        input_template_columns = {'market_class_id', 'start_year', 'annual_vmt', 'payback_years',
                                  'price_amortization_period', 'share_weight', 'discount_rate',
                                  'o_m_costs', 'average_occupancy', 'logit_exponent_mu'
                                  }

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
                    obj_list.append(DemandedSharesGCAM(
                        market_class_ID=df.loc[i, 'market_class_id'],
                        calendar_year=df.loc[i, 'start_year'],
                        annual_VMT=df.loc[i, 'annual_vmt'],
                        payback_years=df.loc[i, 'payback_years'],
                        price_amortization_period=df.loc[i, 'price_amortization_period'],
                        discount_rate=df.loc[i, 'discount_rate'],
                        share_weight=df.loc[i, 'share_weight'],
                        o_m_costs=df.loc[i, 'o_m_costs'],
                        average_occupancy=df.loc[i, 'average_occupancy'],
                        logit_exponent_mu=df.loc[i, 'logit_exponent_mu'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

                for mc in df['market_class_id'].unique():
                    cache[mc] = {'start_year': np.array(df['start_year'].loc[df['market_class_id'] == mc])}

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        from consumer.market_classes import MarketClass  # needed for market class ID

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)

        init_fail += DemandedSharesGCAM.init_database_from_file(o2.options.demanded_shares_file,
                                                                           verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)