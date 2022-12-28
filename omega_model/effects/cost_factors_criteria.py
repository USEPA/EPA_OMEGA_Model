"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/uston benefits estimates associated with reductions in criteria air pollutants. The data should
be left blank to avoid calculating health effects (criteria air pollution effects) using $/uston values.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors_criteria,input_template_version:,0.4

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,source_id,pm25_low_3.0_USD_per_uston,sox_low_3.0_USD_per_uston,nox_low_3.0_USD_per_uston,pm25_low_7.0_USD_per_uston,sox_low_7.0_USD_per_uston,nox_low_7.0_USD_per_uston,pm25_high_3.0_USD_per_uston,sox_high_3.0_USD_per_uston,nox_high_3.0_USD_per_uston,pm25_high_7.0_USD_per_uston,sox_high_7.0_USD_per_uston,nox_high_7.0_USD_per_uston
        2025,2020,car pump gasoline,709156.4844,127863.083,7233.620573,636535.1272,114771.2217,6494.477664,1515307.974,273678.4484,15369.82202,1362598.818,246100.5307,13822.37696
        2030,2020,car pump gasoline,813628.2611,146570.4771,8157.897937,730502.0075,131597.8376,7325.874024,1681059.868,303337.4514,16764.7674,1511757.523,272790.6288,15077.6831
        2035,2020,car pump gasoline,938850.3917,169075.4785,9195.259845,843175.5181,151847.912,8259.336809,1890653.219,340989.946,18455.67509,1700420.74,306683.2824,16599.76534

Data Column Name and Description
    :calendar_year:
        The calendar year for which specific cost factors are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        cpi_price_deflators input file.

    :source_id:
        The source of the pollutant, whether it be a gasoline car or an EGU or refinery.

    :pm25_low_3.0_USD_per_uston:
        The structure for all cost factors is pollutant_study_discount-rate_units, where study refers to the low or high valuation and units are in US dollars per US ton.

----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class CostFactorsCriteria(OMEGABase):
    """
    Loads and provides access to criteria emissions cost factors by calendar year.

    """
    _data = dict()  # private dict, cost factors criteria by calendar year

    _cache = dict()

    calc_health_effects = True

    @staticmethod
    def get_cost_factors(calendar_year, source_id, cost_factors):
        """

        Get cost factors by calendar year

        Args:
            calendar_year (int): calendar year to get cost factors for
            source_id: (str): the pollutant source, e.g., 'car pump gasoline', 'egu', 'refinery'
            cost_factors (str, [strs]): name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        cache_key = (calendar_year, source_id, cost_factors)

        if cache_key not in CostFactorsCriteria._cache:

            calendar_years \
                = [v['calendar_year'] for k, v in CostFactorsCriteria._data.items() if v['source_id'] == source_id]
            # calendar_years = CostFactorsCriteria._data.keys()
            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for cf in cost_factors:
                factors.append(CostFactorsCriteria._data[year, source_id][cf])
                # factors.append(CostFactorsCriteria._data[year][cf])

            if len(cost_factors) == 1:
                CostFactorsCriteria._cache[cache_key] = factors[0]
            else:
                CostFactorsCriteria._cache[cache_key] = factors

        return CostFactorsCriteria._cache[cache_key]

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        CostFactorsCriteria._data.clear()

        CostFactorsCriteria._cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename} ...')

        input_template_name = 'cost_factors_criteria'
        input_template_version = 0.4
        cost_factors_input_template_columns = {
            'calendar_year',
            'dollar_basis',
            'source_id',
            'pm25_low_3.0_USD_per_uston',
            'sox_low_3.0_USD_per_uston',
            'nox_low_3.0_USD_per_uston',
            'pm25_low_7.0_USD_per_uston',
            'sox_low_7.0_USD_per_uston',
            'nox_low_7.0_USD_per_uston',
            'pm25_high_3.0_USD_per_uston',
            'sox_high_3.0_USD_per_uston',
            'nox_high_3.0_USD_per_uston',
            'pm25_high_7.0_USD_per_uston',
            'sox_high_7.0_USD_per_uston',
            'nox_high_7.0_USD_per_uston',
        }

        template_errors = validate_template_version_info(filename, input_template_name,
                                                         input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, cost_factors_input_template_columns,
                                                             df.columns, verbose=verbose)

            if not sum(df['calendar_year']) == 0:

                df = df.loc[df['dollar_basis'] != 0, :]

                cols_to_convert = [col for col in df.columns if 'USD_per_uston' in col]

                if not template_errors:
                    df = gen_fxns.adjust_dollars(df, 'cpi_price_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

                    key = pd.Series(zip(df['calendar_year'], df['source_id']))

                    CostFactorsCriteria._data = df.set_index(key).to_dict(orient='index')

            else:
                CostFactorsCriteria.calc_health_effects = False

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        from effects.cpi_price_deflators import CPIPriceDeflators
        init_fail += CPIPriceDeflators.init_from_file(omega_globals.options.cpi_deflators_file,
                                                      verbose=omega_globals.options.verbose)

        init_fail += CostFactorsCriteria.init_from_file(omega_globals.options.criteria_cost_factors_file,
                                                        verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
