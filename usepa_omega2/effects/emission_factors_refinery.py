"""
emission_factors_refinery.py
============================


"""

import o2  # import global variables
from usepa_omega2 import *


class EmissionFactorsRefinery(SQABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_refinery'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    voc_grams_per_gallon = Column('voc_grams_per_gallon', Numeric)
    co_grams_per_gallon = Column('co_grams_per_gallon', Numeric)
    nox_grams_per_gallon = Column('nox_grams_per_gallon', Numeric)
    pm25_grams_per_gallon = Column('pm25_grams_per_gallon', Numeric)
    sox_grams_per_gallon = Column('sox_grams_per_gallon', Numeric)
    benzene_grams_per_gallon = Column('benzene_grams_per_gallon', Numeric)
    butadiene_grams_per_gallon = Column('13butadiene_grams_per_gallon', Numeric)
    formaldehyde_grams_per_gallon = Column('formaldehyde_grams_per_gallon', Numeric)
    acetaldehyde_grams_per_gallon = Column('acetaldehyde_grams_per_gallon', Numeric)
    acrolein_grams_per_gallon = Column('acrolein_grams_per_gallon', Numeric)
    naphthalene_grams_per_gallon = Column('naphthalene_grams_per_gallon', Numeric)
    ch4_grams_per_gallon = Column('ch4_grams_per_gallon', Numeric)
    n2o_grams_per_gallon = Column('n2o_grams_per_gallon', Numeric)

    def __repr__(self):
        return f"<OMEGA2 {type(self).__name__} object at 0x{id(self)}>"

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'emission_factors-refinery'
        input_template_version = 0.1
        input_template_columns = {'calendar_year',
                                  'voc_grams_per_gallon', 'co_grams_per_gallon', 'nox_grams_per_gallon', 'pm25_grams_per_gallon', 'sox_grams_per_gallon',
                                  'benzene_grams_per_gallon', '13butadiene_grams_per_gallon', 'formaldehyde_grams_per_gallon',
                                  'acetaldehyde_grams_per_gallon', 'acrolein_grams_per_gallon', 'naphthalene_grams_per_gallon',
                                  'ch4_grams_per_gallon', 'n2o_grams_per_gallon'}

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
                    obj_list.append(EmissionFactorsRefinery(
                        calendar_year=df.loc[i, 'calendar_year'],
                        voc_grams_per_gallon=df.loc[i, 'voc_grams_per_gallon'],
                        co_grams_per_gallon=df.loc[i, 'co_grams_per_gallon'],
                        nox_grams_per_gallon=df.loc[i, 'nox_grams_per_gallon'],
                        pm25_grams_per_gallon=df.loc[i, 'pm25_grams_per_gallon'],
                        sox_grams_per_gallon=df.loc[i, 'sox_grams_per_gallon'],
                        benzene_grams_per_gallon=df.loc[i, 'benzene_grams_per_gallon'],
                        butadiene_grams_per_gallon=df.loc[i, '13butadiene_grams_per_gallon'],
                        formaldehyde_grams_per_gallon=df.loc[i, 'formaldehyde_grams_per_gallon'],
                        acetaldehyde_grams_per_gallon=df.loc[i, 'acetaldehyde_grams_per_gallon'],
                        acrolein_grams_per_gallon=df.loc[i, 'acrolein_grams_per_gallon'],
                        naphthalene_grams_per_gallon=df.loc[i, 'naphthalene_grams_per_gallon'],
                        ch4_grams_per_gallon=df.loc[i, 'ch4_grams_per_gallon'],
                        n2o_grams_per_gallon=df.loc[i, 'n2o_grams_per_gallon'],
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

        init_fail = init_fail + EmissionFactorsRefinery.init_database_from_file(o2.options.emission_factors_refinery_file,
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
