"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/metric ton benefits estimates (i.e., Social Cost of GHG) associated with reductions in GHG pollutants.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors_scc,input_template_version:,0.2

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
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

    :co2_global_5.0_USD_per_metricton:
        The structure for all cost factors is pollutant_scope_discount-rate_units, where scope is global or domestic and units are in US dollars per metric ton.


----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class CostFactorsSCC(OMEGABase):
    """
    Loads and provides access to social cost of carbon cost factors by calendar year.

    """

    _data = dict()  # private dict, cost factors social cost of carbon by calendar year

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
        calendar_years = CostFactorsSCC._data.keys()
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        factors = []
        for cf in cost_factors:
            factors.append(CostFactorsSCC._data[year][cf])

        if len(cost_factors) == 1:
            return factors[0]
        else:
            return factors

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
        CostFactorsSCC._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'cost_factors_scc'
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

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            cols_to_convert = [col for col in df.columns if 'USD_per_metricton' in col]

            df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            if not template_errors:
                CostFactorsSCC._data = df.set_index('calendar_year').to_dict(orient='index')

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

        init_fail += CostFactorsSCC.init_from_file(omega_globals.options.scc_cost_factors_file,
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
