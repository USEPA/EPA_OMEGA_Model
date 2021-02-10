"""
cost_factors_scc.py
===================


"""

import pandas as pd
import o2  # import global variables
from usepa_omega2 import *
import usepa_omega2.effects.general_functions as gen_fxns

cache = dict()

class CostFactorsSCC(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_scc'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column('calendar_year', Numeric)
    dollar_basis = Column('dollar_basis', Numeric)
    co2_domestic_cost_factor_25 = Column('co2_interimdomestic_2.5_USD_per_metricton', Float)
    co2_domestic_cost_factor_30 = Column('co2_interimdomestic_3.0_USD_per_metricton', Float)
    co2_domestic_cost_factor_70 = Column('co2_interimdomestic_7.0_USD_per_metricton', Float)
    ch4_domestic_cost_factor_25 = Column('ch4_interimdomestic_2.5_USD_per_metricton', Float)
    ch4_domestic_cost_factor_30 = Column('ch4_interimdomestic_3.0_USD_per_metricton', Float)
    ch4_domestic_cost_factor_70 = Column('ch4_interimdomestic_7.0_USD_per_metricton', Float)
    n2o_domestic_cost_factor_25 = Column('n2o_interimdomestic_2.5_USD_per_metricton', Float)
    n2o_domestic_cost_factor_30 = Column('n2o_interimdomestic_3.0_USD_per_metricton', Float)
    n2o_domestic_cost_factor_70 = Column('n2o_interimdomestic_7.0_USD_per_metricton', Float)
    co2_global_cost_factor_25 = Column('co2_global_2.5_USD_per_metricton', Float)
    co2_global_cost_factor_30 = Column('co2_global_3.0_USD_per_metricton', Float)
    co2_global_cost_factor_70 = Column('co2_global_7.0_USD_per_metricton', Float)
    ch4_global_cost_factor_25 = Column('ch4_global_2.5_USD_per_metricton', Float)
    ch4_global_cost_factor_30 = Column('ch4_global_3.0_USD_per_metricton', Float)
    ch4_global_cost_factor_70 = Column('ch4_global_7.0_USD_per_metricton', Float)
    n2o_global_cost_factor_25 = Column('n2o_global_2.5_USD_per_metricton', Float)
    n2o_global_cost_factor_30 = Column('n2o_global_3.0_USD_per_metricton', Float)
    n2o_global_cost_factor_70 = Column('n2o_global_7.0_USD_per_metricton', Float)

    @staticmethod
    def get_cost_factors(calendar_year, cost_factors):
        """

        Args:
            calendar_year: calendar year to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns: cost factor or list of cost factors

        """
        cache_key = '%s_%s' % (calendar_year, cost_factors)

        if cache_key not in cache:
            if type(cost_factors) is not list:
                cost_factors = [cost_factors]
            attrs = CostFactorsSCC.get_class_attributes(cost_factors)

            result = o2.session.query(*attrs).filter(CostFactorsSCC.calendar_year == calendar_year).all()[0]

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

        input_template_name = 'context_cost_factors-scc'
        input_template_version = 0.2
        input_template_columns = {'calendar_year', 
                                  'dollar_basis', 
                                  'co2_interimdomestic_2.5_USD_per_metricton', 
                                  'co2_interimdomestic_3.0_USD_per_metricton',
                                  'co2_interimdomestic_7.0_USD_per_metricton',
                                  'ch4_interimdomestic_2.5_USD_per_metricton',
                                  'ch4_interimdomestic_3.0_USD_per_metricton',
                                  'ch4_interimdomestic_7.0_USD_per_metricton',
                                  'n2o_interimdomestic_2.5_USD_per_metricton',
                                  'n2o_interimdomestic_3.0_USD_per_metricton',
                                  'n2o_interimdomestic_7.0_USD_per_metricton',
                                  'co2_global_2.5_USD_per_metricton',
                                  'co2_global_3.0_USD_per_metricton',
                                  'co2_global_7.0_USD_per_metricton',
                                  'ch4_global_2.5_USD_per_metricton',
                                  'ch4_global_3.0_USD_per_metricton',
                                  'ch4_global_7.0_USD_per_metricton',
                                  'n2o_global_2.5_USD_per_metricton',
                                  'n2o_global_3.0_USD_per_metricton',
                                  'n2o_global_7.0_USD_per_metricton',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            deflators = pd.read_csv(o2.options.ip_deflators_file, skiprows=1, index_col=0)
            df = gen_fxns.adjust_dollars(df, deflators, 'co2_interimdomestic_2.5_USD_per_metricton', 
                                                        'co2_interimdomestic_3.0_USD_per_metricton',
                                                        'co2_interimdomestic_7.0_USD_per_metricton',
                                                        'ch4_interimdomestic_2.5_USD_per_metricton',
                                                        'ch4_interimdomestic_3.0_USD_per_metricton',
                                                        'ch4_interimdomestic_7.0_USD_per_metricton',
                                                        'n2o_interimdomestic_2.5_USD_per_metricton',
                                                        'n2o_interimdomestic_3.0_USD_per_metricton',
                                                        'n2o_interimdomestic_7.0_USD_per_metricton',
                                                        'co2_global_2.5_USD_per_metricton',
                                                        'co2_global_3.0_USD_per_metricton',
                                                        'co2_global_7.0_USD_per_metricton',
                                                        'ch4_global_2.5_USD_per_metricton',
                                                        'ch4_global_3.0_USD_per_metricton',
                                                        'ch4_global_7.0_USD_per_metricton',
                                                        'n2o_global_2.5_USD_per_metricton',
                                                        'n2o_global_3.0_USD_per_metricton',
                                                        'n2o_global_7.0_USD_per_metricton',
                                         )

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsSCC(
                        calendar_year = df.loc[i, 'calendar_year'],
                        dollar_basis = df.loc[i, 'dollar_basis'],
                        co2_domestic_cost_factor_25 = df.loc[i, 'co2_interimdomestic_2.5_USD_per_metricton'],
                        co2_domestic_cost_factor_30 = df.loc[i, 'co2_interimdomestic_3.0_USD_per_metricton'],
                        co2_domestic_cost_factor_70 = df.loc[i, 'co2_interimdomestic_7.0_USD_per_metricton'],
                        ch4_domestic_cost_factor_25 = df.loc[i, 'ch4_interimdomestic_2.5_USD_per_metricton'],
                        ch4_domestic_cost_factor_30 = df.loc[i, 'ch4_interimdomestic_3.0_USD_per_metricton'],
                        ch4_domestic_cost_factor_70 = df.loc[i, 'ch4_interimdomestic_7.0_USD_per_metricton'],
                        n2o_domestic_cost_factor_25 = df.loc[i, 'n2o_interimdomestic_2.5_USD_per_metricton'],
                        n2o_domestic_cost_factor_30 = df.loc[i, 'n2o_interimdomestic_3.0_USD_per_metricton'],
                        n2o_domestic_cost_factor_70 = df.loc[i, 'n2o_interimdomestic_7.0_USD_per_metricton'],
                        co2_global_cost_factor_25 = df.loc[i, 'co2_global_2.5_USD_per_metricton'],
                        co2_global_cost_factor_30 = df.loc[i, 'co2_global_3.0_USD_per_metricton'],
                        co2_global_cost_factor_70 = df.loc[i, 'co2_global_7.0_USD_per_metricton'],
                        ch4_global_cost_factor_25 = df.loc[i, 'ch4_global_2.5_USD_per_metricton'],
                        ch4_global_cost_factor_30 = df.loc[i, 'ch4_global_3.0_USD_per_metricton'],
                        ch4_global_cost_factor_70 = df.loc[i, 'ch4_global_7.0_USD_per_metricton'],
                        n2o_global_cost_factor_25 = df.loc[i, 'n2o_global_2.5_USD_per_metricton'],
                        n2o_global_cost_factor_30 = df.loc[i, 'n2o_global_3.0_USD_per_metricton'],
                        n2o_global_cost_factor_70 = df.loc[i, 'n2o_global_7.0_USD_per_metricton'],
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
