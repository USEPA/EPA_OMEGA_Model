"""

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent the social costs per ton associated with emissions of GHGs.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,cost_factors_scghg,input_template_version:,0.4

Sample Data Columns
    .. csv-table::
        :widths: auto

        gas,calendar_year,dollar_basis,scope,0.025,0.02,0.015
        co2,2020,2020,global,117,193,337
        co2,2021,2020,global,119,197,341
        co2,2022,2020,global,122,200,346
        co2,2023,2020,global,125,204,351
        co2,2024,2020,global,128,208,356

Data Column Name and Description
    :gas:
        The pollutant, e.g., co2, ch4 or n2o.

    :calendar_year:
        The calendar year, an integer.

    :dollar_basis:
        The dollar basis of the dollars_per_metricton values; values are converted to analysis dollars in-code.

    :scope:
        The scope of the valuations, e.g., global or domestic.

    :remaining column headers:
        These headers should indicate the discount rate(s) used in generating the valuations.

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class CostFactorsSCGHG:
    """
    Loads and provides access to social cost of carbon cost factors by calendar year.

    """

    def __init__(self):
        self._dict = {}
        self.factors_in_analysis_dollars = pd.DataFrame()
        self.scghg_rates_as_strings = []
        self.scghg_rates = []
        self.gases = []
        self.scopes = []

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
        input_template_name = 'cost_factors_scghg'
        input_template_version = 0.4
        input_template_columns = [
            'calendar_year',
            'dollar_basis',
            'scope',
            'rate',
        ]

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self.gases = [col for col in df.columns if col not in input_template_columns]
        self.scghg_rates_as_strings = df['rate'].astype('string').unique()
        for item in self.scghg_rates_as_strings:
            if len(item) > 5:
                n = pd.to_numeric(item[:-3])
            else:
                n = pd.to_numeric(item)
            self.scghg_rates.append(n)
        self.scghg_rates = list(set(self.scghg_rates))
        self.scopes = df['scope'].unique()

        df = batch_settings.ip_deflators.adjust_dollars(batch_settings, df, effects_log, *self.gases)

        self.factors_in_analysis_dollars = df.copy()

        df.drop(columns='dollar_basis', inplace=True)
        key = zip(
            df['calendar_year'],
            df['scope'],
            df['rate'].astype('string')
        )
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

    def get_factors(self, calendar_year):
        """

        Parameters:
            calendar_year (int): the calendar year for which emission cost factors are needed.

        Returns:
            A dictionary of dollar per ton cost factors for the passed year_id.

        """
        factor_dict = {}
        for scope in self.scopes:
            for gas in self.gases:
                for rate in self.scghg_rates_as_strings:
                    factor_dict.update({(gas, scope, rate): self._dict[(calendar_year, scope, rate)][gas]})

        return factor_dict
