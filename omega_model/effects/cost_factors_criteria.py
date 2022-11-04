"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/uston benefits estimates associated with reductions in criteria air pollutants.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors_criteria,input_template_version:,0.3

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

.. todo: document context_cpi_price_deflators file format

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
    def get_cost_factors(calendar_year, cost_factors):
        """

        Get cost factors by calendar year

        Args:
            calendar_year (int): calendar year to get cost factors for
            cost_factors (str, [strs]): name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        cache_key = (calendar_year, cost_factors)

        if cache_key not in CostFactorsCriteria._cache:

            calendar_years = CostFactorsCriteria._data.keys()
            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for cf in cost_factors:
                factors.append(CostFactorsCriteria._data[year][cf])

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
        input_template_version = 0.31
        cost_factors_input_template_columns = {
            'calendar_year',
            'dollar_basis',
            'pm25_tailpipe_3.0_USD_per_uston',
            'pm25_upstream_3.0_USD_per_uston',
            'nox_tailpipe_3.0_USD_per_uston',
            'nox_upstream_3.0_USD_per_uston',
            'sox_tailpipe_3.0_USD_per_uston',
            'sox_upstream_3.0_USD_per_uston',
            'pm25_tailpipe_7.0_USD_per_uston',
            'pm25_upstream_7.0_USD_per_uston',
            'nox_tailpipe_7.0_USD_per_uston',
            'nox_upstream_7.0_USD_per_uston',
            'sox_tailpipe_7.0_USD_per_uston',
            'sox_upstream_7.0_USD_per_uston'
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

                    CostFactorsCriteria._data = df.set_index('calendar_year').to_dict(orient='index')

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
