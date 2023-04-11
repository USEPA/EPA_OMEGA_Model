"""

**Routines to load Implicit Price (IP) deflators.**

Used to convert monetary general to a consistent dollar basis, e.g., in the ``cost_factors_congestion_noise`` module.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the price deflator by calendar year.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,context_implicit_price_deflators,input_template_version:,0.22

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,price_deflator
        2001,79.783
        2002,81.026

Data Column Name and Description

:calendar_year:
    Calendar year of the price deflator

:price_deflator:
    Implicit price deflator

**CODE**

"""
import pandas as pd
import sys

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class ImplicitPriceDeflators:
    """
    **Loads and provides access to implicit price deflators by calendar year.**

    """
    def __init__(self):
        self._data = dict()  # private dict, implicit price deflators by calendar year
        self._cache = dict()

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log)

        input_template_name = 'context_implicit_price_deflators'
        input_template_version = 0.22
        input_template_columns = {
            'calendar_year',
            'price_deflator',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index('calendar_year').to_dict(orient='index')

    def get_price_deflator(self, calendar_year, effects_log):
        """
        Get the implicit price deflator for the given calendar year.

        Args:
            calendar_year (int): the calendar year to get the function for
            effects_log: an instance of the EffectsLog class.

        Returns:
            The implicit price deflator for the given calendar year.

        """
        cache_key = calendar_year

        if cache_key not in self._cache:

            calendar_years = pd.Series(self._data.keys())

            if len(calendar_years[calendar_years <= calendar_year]) > 0:
                year = max(calendar_years[calendar_years <= calendar_year])

                self._cache[cache_key] = self._data[year]['price_deflator']

            else:
                effects_log.logwrite(f'Missing implicit price deflator for {calendar_year} or prior')
                sys.exit()

        return self._cache[cache_key]

    def adjust_dollars(self, batch_settings, df, effects_log, *args):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            df (DataFrame): values to be converted to a consistent dollar basis.
            effects_log: an instance of the EffectsLog class.
            args (str or strs): The attributes to be converted to a consistent dollar basis.

        Returns:
            The passed DataFrame with args expressed in a consistent dollar basis.

        """
        analysis_dollar_basis = batch_settings.analysis_dollar_basis

        basis_years = pd.Series(df.loc[df['dollar_basis'] > 0, 'dollar_basis']).unique()
        adj_factor_numerator = self.get_price_deflator(analysis_dollar_basis, effects_log)
        df_return = df.copy()
        for basis_year in basis_years:
            adj_factor = adj_factor_numerator / self.get_price_deflator(basis_year, effects_log)
            for arg in args:
                df_return.loc[df_return['dollar_basis'] == basis_year, arg] = df_return[arg] * adj_factor
                df_return.loc[df_return['dollar_basis'] == basis_year, 'dollar_basis'] = analysis_dollar_basis

        return df_return

    def dollar_adjustment_factor(self, batch_settings, dollar_basis_input, effects_log):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            dollar_basis_input (int): the dollar basis of the cost to be adjusted.
            effects_log: an instance of the EffectsLog class.

        Returns:
            The multiplicative factor that can be applied to a cost in dollar_basis_input to express that value in analysis_dollar_basis.

        """
        analysis_dollar_basis = batch_settings.analysis_dollar_basis

        adj_factor_numerator = self.get_price_deflator(analysis_dollar_basis, effects_log)
        adj_factor_denominator = self.get_price_deflator(dollar_basis_input, effects_log)

        return adj_factor_numerator / adj_factor_denominator
