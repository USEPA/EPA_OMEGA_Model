"""
emission_factors_power_sector.py
================================


"""

from usepa_omega2 import *

cache = dict()


class EmissionFactorsPowersector(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_powersector'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    voc_grams_per_kwh = Column('voc_grams_per_kwh', Float)
    co_grams_per_kwh = Column('co_grams_per_kwh', Float)
    nox_grams_per_kwh = Column('nox_grams_per_kwh', Float)
    pm25_grams_per_kwh = Column('pm25_grams_per_kwh', Float)
    sox_grams_per_kwh = Column('sox_grams_per_kwh', Float)
    benzene_grams_per_kwh = Column('benzene_grams_per_kwh', Float)
    butadiene13_grams_per_kwh = Column('butadiene13_grams_per_kwh', Float)
    formaldehyde_grams_per_kwh = Column('formaldehyde_grams_per_kwh', Float)
    acetaldehyde_grams_per_kwh = Column('acetaldehyde_grams_per_kwh', Float)
    acrolein_grams_per_kwh = Column('acrolein_grams_per_kwh', Float)
    ch4_grams_per_kwh = Column('ch4_grams_per_kwh', Float)
    n2o_grams_per_kwh = Column('n2o_grams_per_kwh', Float)
    co2_grams_per_kwh = Column('co2_grams_per_kwh', Float)

    @staticmethod
    def get_emission_factors(calendar_year, emission_factors):
        """

        Args:
            calendar_year: calendar year to get emission factors for
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """
        cache_key = '%s_%s' % (calendar_year, emission_factors)

        if cache_key not in cache:
            if type(emission_factors) is not list:
                cost_factors = [emission_factors]
            attrs = EmissionFactorsPowersector.get_class_attributes(emission_factors)

            result = o2.session.query(*attrs).filter(EmissionFactorsPowersector.calendar_year == calendar_year).all()[0]

            if len(emission_factors) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]


    @staticmethod
    def init_database_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_emission_factors-powersector'
        input_template_version = 0.1
        input_template_columns = {'calendar_year',
                                  'voc_grams_per_kwh', 'co_grams_per_kwh', 'nox_grams_per_kwh', 'pm25_grams_per_kwh', 'sox_grams_per_kwh',
                                  'benzene_grams_per_kwh', 'butadiene13_grams_per_kwh', 'formaldehyde_grams_per_kwh',
                                  'acetaldehyde_grams_per_kwh', 'acrolein_grams_per_kwh',
                                  'ch4_grams_per_kwh', 'n2o_grams_per_kwh', 'co2_grams_per_kwh'}

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
                    obj_list.append(EmissionFactorsPowersector(
                        calendar_year=df.loc[i, 'calendar_year'],
                        voc_grams_per_kwh=df.loc[i, 'voc_grams_per_kwh'],
                        co_grams_per_kwh=df.loc[i, 'co_grams_per_kwh'],
                        nox_grams_per_kwh=df.loc[i, 'nox_grams_per_kwh'],
                        pm25_grams_per_kwh=df.loc[i, 'pm25_grams_per_kwh'],
                        sox_grams_per_kwh=df.loc[i, 'sox_grams_per_kwh'],
                        benzene_grams_per_kwh=df.loc[i, 'benzene_grams_per_kwh'],
                        butadiene13_grams_per_kwh=df.loc[i, 'butadiene13_grams_per_kwh'],
                        formaldehyde_grams_per_kwh=df.loc[i, 'formaldehyde_grams_per_kwh'],
                        acetaldehyde_grams_per_kwh=df.loc[i, 'acetaldehyde_grams_per_kwh'],
                        acrolein_grams_per_kwh=df.loc[i, 'acrolein_grams_per_kwh'],
                        ch4_grams_per_kwh=df.loc[i, 'ch4_grams_per_kwh'],
                        n2o_grams_per_kwh=df.loc[i, 'n2o_grams_per_kwh'],
                        co2_grams_per_kwh=df.loc[i, 'co2_grams_per_kwh'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        from consumer.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        # init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file,
        #                                                             verbose=o2.options.verbose)

        init_fail += EmissionFactorsPowersector.init_database_from_file(o2.options.emission_factors_powersector_file,
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
