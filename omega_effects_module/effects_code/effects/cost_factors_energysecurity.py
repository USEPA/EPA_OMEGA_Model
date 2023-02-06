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

from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names
from omega_effects_module.effects_code.general.general_functions import adjust_dollars


class CostFactorsEnergySecurity:
    """
    Loads and provides access to energy security cost factors by calendar year.

    """
    def __init__(self):
        self._data = dict()
        self._cache = dict()

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
        input_template_name = 'cost_factors_energysecurity'
        input_template_version = 0.3
        input_template_columns = {
            'calendar_year',
            'dollar_basis',
            'dollars_per_bbl',
            'oil_import_reduction_as_percent_of_total_oil_demand_reduction',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[df['dollar_basis'] != 0, :]

        df = adjust_dollars(batch_settings, df, 'ip_deflators', effects_log, 'dollars_per_bbl')

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
        cache_key = (calendar_year, cost_factors)

        if cache_key not in self._cache:

            calendar_years = self._data.keys()
            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for cf in cost_factors:
                factors.append(self._data[year][cf])

            if len(cost_factors) == 1:
                self._cache[cache_key] = factors[0]
            else:
                self._cache[cache_key] = factors

        return self._cache[cache_key]
