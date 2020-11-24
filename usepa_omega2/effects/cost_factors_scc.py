"""
cost_factors_scc.py
===================


"""

import pandas as pd
import o2  # import global variables
from usepa_omega2 import *
import usepa_omega2.effects.general_functions as gen_fxns


class CostFactorsSCC(SQABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_scc'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    discount_rate = Column('discount_rate', Numeric)
    pollutant = Column('pollutant', String)
    dollar_basis = Column('dollar_basis', Numeric)
    scc_interim_domestic = Column('scc_interim_domestic', Numeric)
    scc_global = Column('scc_global', Numeric)

    def __repr__(self):
        return f"<OMEGA2 {type(self).__name__} object at 0x{id(self)}>"

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cost_factors-scc'
        input_template_version = 0.1
        input_template_columns = {'calendar_year', 'discount_rate', 'pollutant', 'dollar_basis', 'scc_interim_domestic', 'scc_global'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            deflators = pd.read_csv(o2.options.ip_deflators_file, skiprows=1, index_col=0)
            df = gen_fxns.adjust_dollars(df, deflators, 'scc_interim_domestic', 'scc_global')

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsSCC(
                        calendar_year=df.loc[i, 'calendar_year'],
                        discount_rate=df.loc[i, 'discount_rate'],
                        pollutant=df.loc[i, 'pollutant'],
                        dollar_basis=df.loc[i, 'dollar_basis'],
                        scc_interim_domestic=df.loc[i, 'scc_interim_domestic'],
                        scc_global=df.loc[i, 'scc_global'],
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

        SQABase.metadata.create_all(o2.engine)

        init_fail = []

        init_fail = init_fail + CostFactorsSCC.init_database_from_file(o2.options.scc_cost_factors_file,
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
