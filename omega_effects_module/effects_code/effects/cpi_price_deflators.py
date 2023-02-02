"""

**Routines to load CPI price deflators.**

Used to convert monetary general to a consistent dollar basis, e.g., in the ``cost_factors_criteria`` module.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the price deflator by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_cpi_price_deflators,input_template_version:,0.22

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,price_deflator
        2010,218.056
        2011,224.939

Data Column Name and Description

:calendar_year:
    Calendar year of the price deflator

:price_deflator:
    CPI price deflator

**CODE**

"""
import pandas as pd
import sys

from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class CPIPriceDeflators:
    """
    **Loads and provides access to CPI price deflators by calendar year.**

    """
    def __init__(self):
        self._data = dict()  # private dict, CPI price deflators by calendar year

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            batch_settings: an instance of the BatchSettings class.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log)

        input_template_name = 'context_cpi_price_deflators'
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
        Get the CPI price deflator for the given calendar year.

        Args:
            calendar_year (int): the calendar year to get the function for

        Returns:
            The CPI price deflator for the given calendar year.

        """
        calendar_years = pd.Series(self._data.keys())
        # calendar_years = np.array([*CPIPriceDeflators._data]) # np.array(list(CPIPriceDeflators._data.keys()))
        if len(calendar_years[calendar_years <= calendar_year]) > 0:
            year = max(calendar_years[calendar_years <= calendar_year])

            return self._data[year]['price_deflator']
        else:
            effects_log.logwrite(f'Missing CPI price deflator for {calendar_year} or prior')
            sys.exit()
            # raise Exception(f'Missing CPI price deflator for {calendar_year} or prior')
