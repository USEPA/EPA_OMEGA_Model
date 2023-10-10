"""

**Routines to load and access electricity prices from the analysis context**

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent electricity charging costs per kWh and the share of charging at the given rate(s).

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,base_rate_dollars_per_kwh,marginal_public_level2_dollars_per_kwh,marginal_public_level3_dollars_per_kwh,share_base_rate,share_public_level2,share_public_level3
        2027,2022,0.1,0.05,0.08,0.6,0.3,0.1
        2030,2022,0.11,0.05,0.08,0.57,0.31,0.12
        2035,2022,0.12,0.05,0.08,0.54,0.32,0.14
        2040,2022,0.13,0.05,0.08,0.51,0.33,0.16
        2045,2022,0.14,0.05,0.08,0.48,0.34,0.18
        2050,2022,0.15,0.05,0.08,0.45,0.35,0.2

Data Column Name and Description
    :calendar_year:
        The calendar year for which the indicated price is valid.

    :dollar_basis:
        The dollar value of the associated price; prices are converted to analysis dollars in code.

    :base_rate_dollars_per_kwh:
        The base rate cost per kWh for all charging.

    :marginal_public_level2_dollars_per_kwh:
        The marginal cost per kWh for level 2 charging; this is added to the base rate.

    :marginal_public_level3_dollars_per_kwh:
        The marginal cost per kWh for level 2 charging; this is added to the base rate.

    :share_base_rate:
        The share of charging at the base rate.

    :share_public_level2:
        The share of charging at the public level 2 rate.

    :share_public_level3:
        The share of charging at the public level 3 rate.

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_column_names


class ElectricityPrices:
    """
    **Loads and provides access to fuel prices from the analysis context**

    """
    def __init__(self):
        self._data = {}
        self.year_max = None
        self.year_min = None

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
        input_template_columns = {
            'calendar_year',
            'dollar_basis',
            'base_rate_dollars_per_kwh',
            'marginal_public_level2_dollars_per_kwh',
            'marginal_public_level3_dollars_per_kwh',
            'share_base_rate',
            'share_public_level2_rate',
            'share_public_level3_rate',
        }
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        dollar_basis = df['dollar_basis'].mean()
        cols_to_convert = [col for col in df.columns if 'dollars_per_kwh' in col]

        deflators = batch_settings.ip_deflators._data

        adjustment_factor = deflators[batch_settings.analysis_dollar_basis]['price_deflator'] \
                            / deflators[dollar_basis]['price_deflator']

        for col in cols_to_convert:
            df[col] = df[col] * adjustment_factor

        df['dollar_basis'] = batch_settings.analysis_dollar_basis

        df.insert(
            len(df.columns),
            'retail_dollars_per_unit',
            df['base_rate_dollars_per_kwh'] * df['share_base_rate']
            + (df['base_rate_dollars_per_kwh'] + df['marginal_public_level2_dollars_per_kwh']) *
            df['share_public_level2_rate']
            + (df['base_rate_dollars_per_kwh'] + df['marginal_public_level3_dollars_per_kwh']) *
            df['share_public_level3_rate']
        )
        args = [col for col in df.columns if 'calendar_year' not in col and 'dollar_basis' not in col]

        self._data = df.set_index('calendar_year').sort_index().to_dict(orient='index')

        df = self.interpolate_values(df, args)
        self._data = df.sort_index().to_dict(orient='index')

    def interpolate_values(self, df, args):
        """

        Parameters:
            df (DataFrame): the input data to be interpolated.
            args (list): the arguments to interpolate.

        Returns:
             The passed DataFrame with interpolated values to fill in missing data.

        """
        years = df['calendar_year'].unique()
        self.year_max = df['calendar_year'].max()
        self.year_min = df['calendar_year'].min()

        for idx, year in enumerate(years):
            if year < self.year_max:
                year1, year2 = year, years[idx + 1]
                dollar_basis = int(self._data[year]['dollar_basis'])

                for yr in range(year1 + 1, year2):
                    self._data.update({yr: {'dollar_basis': dollar_basis}})

                    for arg in args:
                        arg_value1 = self._data[year1][arg]
                        arg_value2 = self._data[year2][arg]

                        m = (arg_value2 - arg_value1) / (year2 - year1)

                        arg_value = m * (yr - year1) + arg_value1
                        self._data[yr][arg] = arg_value

        df = pd.DataFrame(self._data).transpose().sort_index()

        return df

    def get_fuel_price(self, calendar_year, *price_types):
        """
        Get fuel price data in calendar_year

        Args:
            calendar_year (numeric): calendar year for which to get fuel prices.
            price_types (str): the price types sought (e.g., retail, pretax)

        Returns:
            Fuel price or list of fuel prices if multiple attributes were requested

        """
        prices = []
        if calendar_year not in self._data:
            calendar_year = max(self.year_min, min(calendar_year, self.year_max))

        for price_type in price_types:
            prices.append(self._data[calendar_year][price_type])

        if len(prices) == 1:
            return prices[0]
        else:
            return prices
