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

from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names
from omega_effects_module.effects_code.general.general_functions import adjust_dollars


class CostFactorsSCC:
    """
    Loads and provides access to social cost of carbon cost factors by calendar year.

    """
    def __init__(self):
        self._data = dict()  # private dict, cost factors social cost of carbon by calendar year

    def init_from_file(self, filepath, batch_settings, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            batch_settings: an instance of the BatchSettings class.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_name = 'cost_factors_scc'
        input_template_version = 0.2
        input_template_columns = {
            'calendar_year',
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

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[df['dollar_basis'] != 0, :]

        cols_to_convert = [col for col in df.columns if 'USD_per_metricton' in col]

        df = adjust_dollars(batch_settings, df, 'ip_deflators', effects_log, *cols_to_convert)

        self._data = df.set_index('calendar_year').to_dict(orient='index')

    def get_cost_factors(self, calendar_year, cost_factors):
        """

        Get cost factors by calendar year

        Args:
            calendar_year (int): calendar year to get cost factors for
            cost_factors (str, [strs]): name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        calendar_years = self._data.keys()
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        factors = []
        for cf in cost_factors:
            factors.append(self._data[year][cf])

        if len(cost_factors) == 1:
            return factors[0]
        else:
            return factors
