"""

**Routines to load and provide access to GCAM consumer response parameters.**

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

cache = dict()


class DemandedSharesGCAM(SQABase, OMEGABase):
    """
    Loads and provides access to GCAM consumer response parameters.

    """
    # --- database table properties ---
    __tablename__ = 'demanded_shares_gcam'
    index = Column(Integer, primary_key=True)  #: database table index

    market_class_ID = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))  #: market class ID
    annual_VMT = Column('annual_vmt', Float)  #: annual vehicle miles travelled
    calendar_year = Column(Numeric)  #: the calendar year of the parameters
    payback_years = Column(Numeric)  #: payback period, in years
    price_amortization_period = Column(Numeric)  #: price amorization period, in years
    discount_rate = Column(Float)  #: discount rate [0..1], e.g. 0.1
    share_weight = Column(Float)  #: share weight [0..1]
    o_m_costs = Column(Float)  #: operating and maintenance costs, in dollars
    average_occupancy = Column(Float)  #: average vehicle occupancy, number of people
    logit_exponent_mu = Column(Float)  #: log exponent, mu

    @staticmethod
    def get_gcam_params(calendar_year, market_class_id):
        """
        Get GCAM parameters for the given calendar year and market class.

        Args:
            calendar_year (int): the year to get parameters for
            market_class_id (str): market class id, e.g. 'non_hauling.BEV'

        Returns:
            GCAM parameters for the given calendar year and market class

        """
        start_years = cache[market_class_id]['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        key = '%s_%s' % (calendar_year, market_class_id)
        if not key in cache:
            cache[key] = omega_globals.session.query(DemandedSharesGCAM). \
                filter(DemandedSharesGCAM.calendar_year == calendar_year). \
                filter(DemandedSharesGCAM.market_class_ID == market_class_id).one()

        return cache[key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
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
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                for mc in df['market_class_id'].unique():
                    cache[mc] = {'start_year': np.array(df['start_year'].loc[df['market_class_id'] == mc])}

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from consumer.market_classes import MarketClass  # needed for market class ID

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)

        init_fail += DemandedSharesGCAM.init_database_from_file(omega_globals.options.demanded_shares_file,
                                                                verbose=omega_globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)