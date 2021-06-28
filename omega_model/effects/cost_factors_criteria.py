"""


----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


cache = dict()

class CostFactorsCriteria(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_criteria'
    index = Column(Integer, primary_key=True)

    calendar_year = Column(Numeric)
    dollar_basis = Column(Numeric)
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
            attrs = CostFactorsCriteria.get_class_attributes(cost_factors)

            result = omega_globals.session.query(*attrs).filter(CostFactorsCriteria.calendar_year == calendar_year).all()[0]

            if len(cost_factors) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(criteria_cost_factors_file, cpi_deflators_file, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {criteria_cost_factors_file} and {cpi_deflators_file}...')

        input_template_name = 'context_cost_factors-criteria'
        input_template_version = 0.2
        cost_factors_input_template_columns = {'calendar_year', 'dollar_basis',
                                               'pm25_low-mortality_3.0_USD_per_uston',
                                               'pm25_high-mortality_3.0_USD_per_uston',
                                               'nox_low-mortality_3.0_USD_per_uston',
                                               'nox_high-mortality_3.0_USD_per_uston',
                                               'sox_low-mortality_3.0_USD_per_uston',
                                               'sox_high-mortality_3.0_USD_per_uston',
                                               'pm25_low-mortality_7.0_USD_per_uston',
                                               'pm25_high-mortality_7.0_USD_per_uston',
                                               'nox_low-mortality_7.0_USD_per_uston',
                                               'nox_high-mortality_7.0_USD_per_uston',
                                               'sox_low-mortality_7.0_USD_per_uston',
                                               'sox_high-mortality_7.0_USD_per_uston'}

        template_errors = validate_template_version_info(criteria_cost_factors_file, input_template_name,
                                                         input_template_version, verbose=verbose)

        input_template_name = 'context_cpi_price_deflators'
        input_template_version = 0.1
        deflators_input_template_columns = {'price_deflator', 'adjustment_factor'}

        template_errors += validate_template_version_info(cpi_deflators_file, input_template_name,
                                                          input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(criteria_cost_factors_file, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(criteria_cost_factors_file, cost_factors_input_template_columns,
                                                        df.columns, verbose=verbose)

            deflators = pd.read_csv(cpi_deflators_file, skiprows=1, index_col=0)

            template_errors += validate_template_columns(cpi_deflators_file, deflators_input_template_columns,
                                                        deflators.columns, verbose=verbose)
            if not template_errors:
                df = gen_fxns.adjust_dollars(df, deflators,
                                             'pm25_low-mortality_3.0_USD_per_uston',
                                             'pm25_high-mortality_3.0_USD_per_uston',
                                             'nox_low-mortality_3.0_USD_per_uston',
                                             'nox_high-mortality_3.0_USD_per_uston',
                                             'sox_low-mortality_3.0_USD_per_uston',
                                             'sox_high-mortality_3.0_USD_per_uston',
                                             'pm25_low-mortality_7.0_USD_per_uston',
                                             'pm25_high-mortality_7.0_USD_per_uston',
                                             'nox_low-mortality_7.0_USD_per_uston',
                                             'nox_high-mortality_7.0_USD_per_uston',
                                             'sox_low-mortality_7.0_USD_per_uston',
                                             'sox_high-mortality_7.0_USD_per_uston',
                                             )

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
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        from omega_model import *
        from common import omega_globals

        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []

        init_fail += CostFactorsCriteria.init_database_from_file(omega_globals.options.criteria_cost_factors_file,
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
