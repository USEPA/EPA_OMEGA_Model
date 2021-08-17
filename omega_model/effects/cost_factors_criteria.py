"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/uston benefits estimates associated with reductions in criteria air pollutants.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors-criteria,input_template_version:,0.3

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,pm25_tailpipe_3.0_USD_per_uston,pm25_upstream_3.0_USD_per_uston,nox_tailpipe_3.0_USD_per_uston,nox_upstream_3.0_USD_per_uston,so2_tailpipe_3.0_USD_per_uston,so2_upstream_3.0_USD_per_uston,pm25_tailpipe_7.0_USD_per_uston,pm25_upstream_7.0_USD_per_uston,nox_tailpipe_7.0_USD_per_uston,nox_upstream_7.0_USD_per_uston,so2_tailpipe_7.0_USD_per_uston,so2_upstream_7.0_USD_per_uston
        2020,2018,602362.7901,380000,6394.459424,8100,153440.3911,81000,543698.0811,350000,5770.584738,7300,138496.0826,74000
        2025,2018,662886.8303,420000,6919.989335,8800,168685.8807,90000,598246.6516,380000,6243.868985,7900,152236.6921,80000

Data Column Name and Description
    :calendar_year:
        The calendar year for which specific cost factors are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        cpi_price_deflators input file.

    :pm25_tailpipe_3.0_USD_per_uston:
        The structure for all cost factors is pollutant_source_discount-rate_units, where source is tailpipe or upstream and units are in US dollars per US ton.


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
    pm25_tailpipe_3 = Column('pm25_tailpipe_3.0_USD_per_uston', Float)
    pm25_upstream_3 = Column('pm25_upstream_3.0_USD_per_uston', Float)
    nox_tailpipe_3 = Column('nox_tailpipe_3.0_USD_per_uston', Float)
    nox_upstream_3 = Column('nox_upstream_3.0_USD_per_uston', Float)
    so2_tailpipe_3 = Column('so2_tailpipe_3.0_USD_per_uston', Float)
    so2_upstream_3 = Column('so2_upstream_3.0_USD_per_uston', Float)
    pm25_tailpipe_7 = Column('pm25_tailpipe_7.0_USD_per_uston', Float)
    pm25_upstream_7 = Column('pm25_upstream_7.0_USD_per_uston', Float)
    nox_tailpipe_7 = Column('nox_tailpipe_7.0_USD_per_uston', Float)
    nox_upstream_7 = Column('nox_upstream_7.0_USD_per_uston', Float)
    so2_tailpipe_7 = Column('so2_tailpipe_7.0_USD_per_uston', Float)
    so2_upstream_7 = Column('so2_upstream_7.0_USD_per_uston', Float)

    @staticmethod
    def get_cost_factors(calendar_year, cost_factors):
        """

        Args:
            calendar_year: calendar year to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns: cost factor or list of cost factors

        """
        calendar_years = pd.Series(sql_unpack_result(omega_globals.session.query(CostFactorsCriteria.calendar_year).all())).unique()
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        cache_key = '%s_%s' % (year, cost_factors)

        if cache_key not in cache:
            if type(cost_factors) is not list:
                cost_factors = [cost_factors]
            attrs = CostFactorsCriteria.get_class_attributes(cost_factors)

            result = omega_globals.session.query(*attrs).filter(CostFactorsCriteria.calendar_year == year).all()[0]

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
        input_template_version = 0.3
        cost_factors_input_template_columns = {'calendar_year', 'dollar_basis',
                                               'pm25_tailpipe_3.0_USD_per_uston',
                                               'pm25_upstream_3.0_USD_per_uston',
                                               'nox_tailpipe_3.0_USD_per_uston',
                                               'nox_upstream_3.0_USD_per_uston',
                                               'so2_tailpipe_3.0_USD_per_uston',
                                               'so2_upstream_3.0_USD_per_uston',
                                               'pm25_tailpipe_7.0_USD_per_uston',
                                               'pm25_upstream_7.0_USD_per_uston',
                                               'nox_tailpipe_7.0_USD_per_uston',
                                               'nox_upstream_7.0_USD_per_uston',
                                               'so2_tailpipe_7.0_USD_per_uston',
                                               'so2_upstream_7.0_USD_per_uston'}

        template_errors = validate_template_version_info(criteria_cost_factors_file, input_template_name,
                                                         input_template_version, verbose=verbose)

        input_template_name = 'context_cpi_price_deflators'
        input_template_version = 0.2
        deflators_input_template_columns = {'price_deflator'}

        template_errors += validate_template_version_info(cpi_deflators_file, input_template_name,
                                                          input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(criteria_cost_factors_file, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(criteria_cost_factors_file, cost_factors_input_template_columns,
                                                        df.columns, verbose=verbose)

            cols_to_convert = [col for col in df.columns if 'USD_per_uston' in col]

            deflators = pd.read_csv(cpi_deflators_file, skiprows=1, index_col=0)

            template_errors += validate_template_columns(cpi_deflators_file, deflators_input_template_columns,
                                                         deflators.columns, verbose=verbose)
            deflators = deflators.to_dict('index')

            if not template_errors:
                df = gen_fxns.adjust_dollars(df, deflators, omega_globals.options.analysis_dollar_basis, *cols_to_convert)

                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(CostFactorsCriteria(
                        calendar_year=df.loc[i, 'calendar_year'],
                        dollar_basis=df.loc[i, 'dollar_basis'],
                        pm25_tailpipe_3=df.loc[i, 'pm25_tailpipe_3.0_USD_per_uston'],
                        pm25_upstream_3=df.loc[i, 'pm25_upstream_3.0_USD_per_uston'],
                        nox_tailpipe_3=df.loc[i, 'nox_tailpipe_3.0_USD_per_uston'],
                        nox_upstream_3=df.loc[i, 'nox_upstream_3.0_USD_per_uston'],
                        so2_tailpipe_3=df.loc[i, 'so2_tailpipe_3.0_USD_per_uston'],
                        so2_upstream_3=df.loc[i, 'so2_upstream_3.0_USD_per_uston'],
                        pm25_tailpipe_7=df.loc[i, 'pm25_tailpipe_7.0_USD_per_uston'],
                        pm25_upstream_7=df.loc[i, 'pm25_upstream_7.0_USD_per_uston'],
                        nox_tailpipe_7=df.loc[i, 'nox_tailpipe_7.0_USD_per_uston'],
                        nox_upstream_7=df.loc[i, 'nox_upstream_7.0_USD_per_uston'],
                        so2_tailpipe_7=df.loc[i, 'so2_tailpipe_7.0_USD_per_uston'],
                        so2_upstream_7=df.loc[i, 'so2_upstream_7.0_USD_per_uston'],
                        ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []

        init_fail += CostFactorsCriteria.init_database_from_file(omega_globals.options.criteria_cost_factors_file,
                                                                 omega_globals.options.cpi_deflators_file,
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
