"""
cost_factors_criteria.py
========================


"""

import pandas as pd

import o2  # import global variables
from usepa_omega2 import *
import usepa_omega2.effects.general_functions as gen_fxns


class CostFactorsCriteria(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_criteria'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    dollar_basis = Column('dollar_basis', Numeric)
    pm25_low_mortality_30 = Column('pm25_low-mortality_3.0_USD_per_uston', Float)
    pm25_high_mortality_30 = Column('pm25_high-mortality_3.0_USD_per_uston', Float)
    nox_low_mortality_30 = Column('nox_low-mortality_3.0_USD_per_uston', Float)
    nox_high_mortality_30 = Column('nox_high-mortality_3.0_USD_per_uston', Float)
    sox_low_mortality_30 = Column('sox_low-mortality_3.0_USD_per_uston', Float)
    sox_high_mortality_30 = Column('sox_high-mortality_3.0_USD_per_uston', Float)
    pm25_low_mortality_70 = Column('pm25_low-mortality_7.0_USD_per_uston', Float)
    pm25_high_mortality_70 = Column('pm25_high-mortality_7.0_USD_per_uston', Float)
    nox_low_mortality_70 = Column('nox_low-mortality_7.0_USD_per_uston', Float)
    nox_high_mortality_70 = Column('nox_high-mortality_7.0_USD_per_uston', Float)
    sox_low_mortality_70 = Column('sox_low-mortality_7.0_USD_per_uston', Float)
    sox_high_mortality_70 = Column('sox_high-mortality_7.0_USD_per_uston', Float)

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cost_factors-criteria'
        input_template_version = 0.2
        input_template_columns = {'calendar_year', 'dollar_basis',
                                  'pm25_low-mortality_3.0_USD_per_uston', 'pm25_high-mortality_3.0_USD_per_uston',
                                  'nox_low-mortality_3.0_USD_per_uston', 'nox_high-mortality_3.0_USD_per_uston',
                                  'sox_low-mortality_3.0_USD_per_uston', 'sox_high-mortality_3.0_USD_per_uston',
                                  'pm25_low-mortality_7.0_USD_per_uston', 'pm25_high-mortality_7.0_USD_per_uston',
                                  'nox_low-mortality_7.0_USD_per_uston', 'nox_high-mortality_7.0_USD_per_uston',
                                  'sox_low-mortality_7.0_USD_per_uston', 'sox_high-mortality_7.0_USD_per_uston'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            deflators = pd.read_csv(o2.options.cpi_deflators_file, skiprows=1, index_col=0)
            df = gen_fxns.adjust_dollars(df, deflators, 
                                         'pm25_low-mortality_3.0_USD_per_uston', 'pm25_high-mortality_3.0_USD_per_uston',
                                         'nox_low-mortality_3.0_USD_per_uston', 'nox_high-mortality_3.0_USD_per_uston',
                                         'sox_low-mortality_3.0_USD_per_uston', 'sox_high-mortality_3.0_USD_per_uston',
                                         'pm25_low-mortality_7.0_USD_per_uston', 'pm25_high-mortality_7.0_USD_per_uston',
                                         'nox_low-mortality_7.0_USD_per_uston', 'nox_high-mortality_7.0_USD_per_uston',
                                         'sox_low-mortality_7.0_USD_per_uston', 'sox_high-mortality_7.0_USD_per_uston',
                                         )

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsCriteria(
                        calendar_year=df.loc[i, 'calendar_year'],
                        dollar_basis=df.loc[i, 'dollar_basis'],
                        pm25_low_mortality_30=df.loc[i, 'pm25_low-mortality_3.0_USD_per_uston'],
                        pm25_high_mortality_30=df.loc[i, 'pm25_high-mortality_3.0_USD_per_uston'],
                        nox_low_mortality_30=df.loc[i, 'nox_low-mortality_3.0_USD_per_uston'],
                        nox_high_mortality_30=df.loc[i, 'nox_high-mortality_3.0_USD_per_uston'],
                        sox_low_mortality_30=df.loc[i, 'sox_low-mortality_3.0_USD_per_uston'],
                        sox_high_mortality_30=df.loc[i, 'sox_high-mortality_3.0_USD_per_uston'],
                        pm25_low_mortality_70=df.loc[i, 'pm25_low-mortality_7.0_USD_per_uston'],
                        pm25_high_mortality_70=df.loc[i, 'pm25_high-mortality_7.0_USD_per_uston'],
                        nox_low_mortality_70=df.loc[i, 'nox_low-mortality_7.0_USD_per_uston'],
                        nox_high_mortality_70=df.loc[i, 'nox_high-mortality_7.0_USD_per_uston'],
                        sox_low_mortality_70=df.loc[i, 'sox_low-mortality_7.0_USD_per_uston'],
                        sox_high_mortality_70=df.loc[i, 'sox_high-mortality_7.0_USD_per_uston'],
                        ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        from usepa_omega2 import *
        import o2
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []

        init_fail = init_fail + CostFactorsCriteria.init_database_from_file(o2.options.criteria_cost_factors_file,
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