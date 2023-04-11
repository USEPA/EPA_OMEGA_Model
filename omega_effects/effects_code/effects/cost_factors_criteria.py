"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/uston benefits estimates associated with reductions in criteria air pollutants. The data should
be left blank to avoid calculating health effects (criteria air pollution effects) using $/uston values.

File Type
    comma-separated values (CSV)

Sample Header
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
        The structure for all cost factors is pollutant_study_discount-rate_units, where study refers to the low or
        high valuation and units are in US dollars per US ton.

----

**CODE**

"""
import pandas as pd

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class CostFactorsCriteria:
    """
    Loads and provides access to criteria emissions cost factors by calendar year.

    """
    def __init__(self):
        self._data = dict()  # private dict, cost factors criteria by calendar year
        self._cache = dict()
        self.calc_health_effects = True

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
        input_template_name = 'cost_factors_criteria'
        input_template_version = 0.4
        input_template_columns = {
            'calendar_year',
            'dollar_basis',
            'source_id',
            'pm25_Wu_3.0_USD_per_uston',
            'sox_Wu_3.0_USD_per_uston',
            'nox_Wu_3.0_USD_per_uston',
            'pm25_Wu_7.0_USD_per_uston',
            'sox_Wu_7.0_USD_per_uston',
            'nox_Wu_7.0_USD_per_uston',
            'pm25_Pope_3.0_USD_per_uston',
            'sox_Pope_3.0_USD_per_uston',
            'nox_Pope_3.0_USD_per_uston',
            'pm25_Pope_7.0_USD_per_uston',
            'sox_Pope_7.0_USD_per_uston',
            'nox_Pope_7.0_USD_per_uston',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        if not sum(df['calendar_year']) == 0:

            df = df.loc[df['dollar_basis'] != 0, :]

            cols_to_convert = [col for col in df.columns if 'USD_per_uston' in col]

            df = batch_settings.cpi_deflators.adjust_dollars(batch_settings, df, effects_log, *cols_to_convert)

            key = pd.Series(zip(
                df['calendar_year'],
                df['source_id'],
            ))

            self._data = df.set_index(key).to_dict(orient='index')

        else:
            self.calc_health_effects = False

    def get_cost_factors(self, calendar_year, source_id, cost_factors):
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

        if cache_key not in self._cache:

            calendar_years \
                = [v['calendar_year'] for k, v in self._data.items() if v['source_id'] == source_id]

            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for cf in cost_factors:
                factors.append(self._data[year, source_id][cf])

            if len(cost_factors) == 1:
                self._cache[cache_key] = factors[0]
            else:
                self._cache[cache_key] = factors

        return self._cache[cache_key]
