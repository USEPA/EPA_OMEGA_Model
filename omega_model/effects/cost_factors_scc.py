"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/metric ton benefits estimates (i.e., Social Cost of GHG) associated with reductions in GHG pollutants.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors-scc,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,co2_global_5.0_USD_per_metricton,co2_global_3.0_USD_per_metricton,co2_global_2.5_USD_per_metricton,co2_global_3.95_USD_per_metricton,ch4_global_5.0_USD_per_metricton,ch4_global_3.0_USD_per_metricton,ch4_global_2.5_USD_per_metricton,ch4_global_3.95_USD_per_metricton,n2o_global_5.0_USD_per_metricton,n2o_global_3.0_USD_per_metricton,n2o_global_2.5_USD_per_metricton,n2o_global_3.95_USD_per_metricton
        2020,2018,14.0514,49.5852,74.181,147.1651,646.1792,1441.555,1895.9669,3791.8882,5610.0501,17865.8998,26335.6921,46841.7517
        2021,2018,14.5258,50.6221,75.4487,150.5725,672.6103,1487.1167,1949.7824,3916.5329,5806.1046,18290.1717,26876.1028,48014.0752

Data Column Name and Description
    :calendar_year:
        The calendar year for which specific cost factors are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in code to the dollar basis to be used in the analysis.

    :co2_global_5.0_USD_per_metricton:
        The structure for all cost factors is pollutant_scope_discount-rate_units, where scope is global or domestic and units are in US dollars per metric ton.


----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns

cache = dict()


class CostFactorsSCC(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_factors_scc'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column(Numeric)
    dollar_basis = Column(Numeric)
    co2_global_5 = Column('co2_global_5.0_USD_per_metricton', Float)
    co2_global_3 = Column('co2_global_3.0_USD_per_metricton', Float)
    co2_global_25 = Column('co2_global_2.5_USD_per_metricton', Float)
    co2_global_395 = Column('co2_global_3.95_USD_per_metricton', Float)
    ch4_global_5 = Column('ch4_global_5.0_USD_per_metricton', Float)
    ch4_global_3 = Column('ch4_global_3.0_USD_per_metricton', Float)
    ch4_global_25 = Column('ch4_global_2.5_USD_per_metricton', Float)
    ch4_global_395 = Column('ch4_global_3.95_USD_per_metricton', Float)
    n2o_global_5 = Column('n2o_global_5.0_USD_per_metricton', Float)
    n2o_global_3 = Column('n2o_global_3.0_USD_per_metricton', Float)
    n2o_global_25 = Column('n2o_global_2.5_USD_per_metricton', Float)
    n2o_global_395 = Column('n2o_global_3.95_USD_per_metricton', Float)

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

            result = omega_globals.session.query(*attrs).filter(CostFactorsSCC.calendar_year == calendar_year).all()[0]

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
                                  'co2_global_5.0_USD_per_metricton',
                                  'co2_global_3.0_USD_per_metricton',
                                  'co2_global_2.5_USD_per_metricton',
                                  'co2_global_3.95_USD_per_metricton',
                                  'ch4_global_5.0_USD_per_metricton',
                                  'ch4_global_3.0_USD_per_metricton',
                                  'ch4_global_2.5_USD_per_metricton',
                                  'ch4_global_3.95_USD_per_metricton',
                                  'n2o_global_5.0_USD_per_metricton',
                                  'n2o_global_3.0_USD_per_metricton',
                                  'n2o_global_2.5_USD_per_metricton',
                                  'n2o_global_3.95_USD_per_metricton',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            deflators = pd.read_csv(omega_globals.options.ip_deflators_file, skiprows=1, index_col=0)
            df = gen_fxns.adjust_dollars(df, deflators, 
                                         'co2_global_5.0_USD_per_metricton',
                                         'co2_global_3.0_USD_per_metricton',
                                         'co2_global_2.5_USD_per_metricton',
                                         'co2_global_3.95_USD_per_metricton',
                                         'ch4_global_5.0_USD_per_metricton',
                                         'ch4_global_3.0_USD_per_metricton',
                                         'ch4_global_2.5_USD_per_metricton',
                                         'ch4_global_3.95_USD_per_metricton',
                                         'n2o_global_5.0_USD_per_metricton',
                                         'n2o_global_3.0_USD_per_metricton',
                                         'n2o_global_2.5_USD_per_metricton',
                                         'n2o_global_3.95_USD_per_metricton',
                                         )

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsSCC(
                        calendar_year = df.loc[i, 'calendar_year'],
                        dollar_basis = df.loc[i, 'dollar_basis'],
                        co2_global_5 = df.loc[i, 'co2_global_5.0_USD_per_metricton'],
                        co2_global_3 = df.loc[i, 'co2_global_3.0_USD_per_metricton'],
                        co2_global_25 = df.loc[i, 'co2_global_2.5_USD_per_metricton'],
                        co2_global_395 = df.loc[i, 'co2_global_3.95_USD_per_metricton'],
                        ch4_global_5 = df.loc[i, 'ch4_global_5.0_USD_per_metricton'],
                        ch4_global_3 = df.loc[i, 'ch4_global_3.0_USD_per_metricton'],
                        ch4_global_25 = df.loc[i, 'ch4_global_2.5_USD_per_metricton'],
                        ch4_global_395 = df.loc[i, 'ch4_global_3.95_USD_per_metricton'],
                        n2o_global_5 = df.loc[i, 'n2o_global_5.0_USD_per_metricton'],
                        n2o_global_3 = df.loc[i, 'n2o_global_3.0_USD_per_metricton'],
                        n2o_global_25 = df.loc[i, 'n2o_global_2.5_USD_per_metricton'],
                        n2o_global_395 = df.loc[i, 'n2o_global_3.95_USD_per_metricton'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []

        init_fail += CostFactorsSCC.init_database_from_file(omega_globals.options.scc_cost_factors_file,
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
