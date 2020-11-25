"""
emission_factors_power_sector.py
================================


"""

import o2  # import global variables
from usepa_omega2 import *


class EmissionFactorsPowersector(SQABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_powersector'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    voc_grams_per_kWh = Column('voc_grams_per_kWh', Float)
    co_grams_per_kWh = Column('co_grams_per_kWh', Float)
    nox_grams_per_kWh = Column('nox_grams_per_kWh', Float)
    pm25_grams_per_kWh = Column('pm25_grams_per_kWh', Float)
    sox_grams_per_kWh = Column('sox_grams_per_kWh', Float)
    benzene_grams_per_kWh = Column('benzene_grams_per_kWh', Float)
    butadiene13_grams_per_kWh = Column('butadiene13_grams_per_kWh', Float)
    formaldehyde_grams_per_kWh = Column('formaldehyde_grams_per_kWh', Float)
    acetaldehyde_grams_per_kWh = Column('acetaldehyde_grams_per_kWh', Float)
    acrolein_grams_per_kWh = Column('acrolein_grams_per_kWh', Float)
    ch4_grams_per_kWh = Column('ch4_grams_per_kWh', Float)
    n2o_grams_per_kWh = Column('n2o_grams_per_kWh', Float)
    co2_grams_per_kWh = Column('co2_grams_per_kWh', Float)

    def __repr__(self):
        return f"<OMEGA2 {type(self).__name__} object at 0x{id(self)}>"

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_emission_factors-powersector'
        input_template_version = 0.1
        input_template_columns = {'calendar_year',
                                  'voc_grams_per_kWh', 'co_grams_per_kWh', 'nox_grams_per_kWh', 'pm25_grams_per_kWh', 'sox_grams_per_kWh',
                                  'benzene_grams_per_kWh', 'butadiene13_grams_per_kWh', 'formaldehyde_grams_per_kWh',
                                  'acetaldehyde_grams_per_kWh', 'acrolein_grams_per_kWh',
                                  'ch4_grams_per_kWh', 'n2o_grams_per_kWh', 'co2_grams_per_kWh'}

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
                        voc_grams_per_kWh=df.loc[i, 'voc_grams_per_kWh'],
                        co_grams_per_kWh=df.loc[i, 'co_grams_per_kWh'],
                        nox_grams_per_kWh=df.loc[i, 'nox_grams_per_kWh'],
                        pm25_grams_per_kWh=df.loc[i, 'pm25_grams_per_kWh'],
                        sox_grams_per_kWh=df.loc[i, 'sox_grams_per_kWh'],
                        benzene_grams_per_kWh=df.loc[i, 'benzene_grams_per_kWh'],
                        butadiene13_grams_per_kWh=df.loc[i, 'butadiene13_grams_per_kWh'],
                        formaldehyde_grams_per_kWh=df.loc[i, 'formaldehyde_grams_per_kWh'],
                        acetaldehyde_grams_per_kWh=df.loc[i, 'acetaldehyde_grams_per_kWh'],
                        acrolein_grams_per_kWh=df.loc[i, 'acrolein_grams_per_kWh'],
                        ch4_grams_per_kWh=df.loc[i, 'ch4_grams_per_kWh'],
                        n2o_grams_per_kWh=df.loc[i, 'n2o_grams_per_kWh'],
                        co2_grams_per_kWh=df.loc[i, 'co2_grams_per_kWh'],
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

        from usepa_omega2.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        # init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
        #                                                             verbose=o2.options.verbose)

        init_fail = init_fail + EmissionFactorsPowersector.init_database_from_file(o2.options.emission_factors_powersector_file,
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
