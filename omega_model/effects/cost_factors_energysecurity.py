"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/gallon cost estimates associated with energy security.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors_energysecurity,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,dollars_per_bbl,oil_import_reduction_as_percent_of_total_oil_demand_reduction
        2020,2020,3.21703991758471,0.91

Data Column Name and Description
    :calendar_year:
        The calendar year for which $/barrel values are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

    :dollars_per_bbl:
        The cost (in US dollars) per barrel of oil associated with energy security.

    :oil_import_reduction_as_percent_of_total_oil_demand_reduction:
        The reduction in imported oil as a percent of the total oil demand reduction.

----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class CostFactorsEnergySecurity(OMEGABase):
    """
    Loads and provides access to energy security cost factors by calendar year.

    """
    _data = dict()

    _cache = dict()

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

        if cache_key not in CostFactorsEnergySecurity._cache:

            calendar_years = CostFactorsEnergySecurity._data.keys()
            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for cf in cost_factors:
                factors.append(CostFactorsEnergySecurity._data[year][cf])

            if len(cost_factors) == 1:
                CostFactorsEnergySecurity._cache[cache_key] = factors[0]
            else:
                CostFactorsEnergySecurity._cache[cache_key] = factors

        return CostFactorsEnergySecurity._cache[cache_key]

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
        CostFactorsEnergySecurity._data.clear()
        CostFactorsEnergySecurity._cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'cost_factors_energysecurity'
        input_template_version = 0.3
        input_template_columns = {'calendar_year',
                                  'dollar_basis',
                                  'dollars_per_bbl',
                                  'oil_import_reduction_as_percent_of_total_oil_demand_reduction',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis,
                                             'dollars_per_bbl')

                CostFactorsEnergySecurity._data = df.set_index('calendar_year').to_dict(orient='index')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        from effects.ip_deflators import ImplictPriceDeflators
        init_fail += ImplictPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += CostFactorsEnergySecurity.init_from_file(omega_globals.options.energysecurity_cost_factors_file,
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
