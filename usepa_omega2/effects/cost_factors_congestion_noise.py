"""
cost_factors_congestion_noise.py
================================


"""

import pandas as pd

import o2  # import global variables
from usepa_omega2 import *
import usepa_omega2.effects.general_functions as gen_fxns

cache = dict()


class CostFactorsCongestionNoise(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_congestion_noise'
    index = Column('index', Integer, primary_key=True)
    reg_class_ID = Column(String)
    dollar_basis = Column(Numeric)
    congestion_cost_dollars_per_mile = Column(Float)
    noise_cost_dollars_per_mile = Column(Float)

    @staticmethod
    def get_cost_factors(reg_class_id, cost_factors):
        """

        Args:
            reg_class_id: reg class to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns: cost factor or list of cost factors

        """
        cache_key = '%s_%s' % (reg_class_id, cost_factors)

        if cache_key not in cache:
            if type(cost_factors) is not list:
                cost_factors = [cost_factors]
            attrs = CostFactorsCongestionNoise.get_class_attributes(cost_factors)

            result = o2.session.query(*attrs).filter(CostFactorsCongestionNoise.reg_class_ID == reg_class_id).all()[0]

            if len(cost_factors) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cost_factors-congestion-noise'
        input_template_version = 0.1
        input_template_columns = {'reg_class_id',
                                  'dollar_basis',
                                  'congestion_cost_dollars_per_mile',
                                  'noise_cost_dollars_per_mile',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            deflators = pd.read_csv(o2.options.ip_deflators_file, skiprows=1, index_col=0)
            df = gen_fxns.adjust_dollars(df, deflators, 'congestion_cost_dollars_per_mile', 'noise_cost_dollars_per_mile')

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsCongestionNoise(
                        reg_class_ID = df.loc[i, 'reg_class_id'],
                        dollar_basis = df.loc[i, 'dollar_basis'],
                        congestion_cost_dollars_per_mile = df.loc[i, 'congestion_cost_dollars_per_mile'],
                        noise_cost_dollars_per_mile = df.loc[i, 'noise_cost_dollars_per_mile'],
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

        init_fail = init_fail + CostFactorsCongestionNoise.init_database_from_file(o2.options.congestion_noise_cost_factors_file,
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
