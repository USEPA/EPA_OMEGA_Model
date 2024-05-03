"""

**Routines to load and access electricity consumption from the analysis context**

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent electricity consumption in kWh.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,context_id,case_id,electricity_consumpton_kwh,bev_electricity_consumption_kwh,ld_share,md_share
        2023,AEO2023,Reference case,12868439625,9479421747,1,0
        2024,AEO2023,Reference case,17154010551,12974465416,1,0
        2025,AEO2023,Reference case,22203382767,17043780188,1,0
        2026,AEO2023,Reference case,28250632767,21965204572,1,0

Data Column Name and Description
    :calendar_year:
        The calendar year of the fuel costs

    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', 'IPM', etc.

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', for AEO; 'action' or
        'no_action' for IPM

    :electricity_consumpton_kwh:
        The context electricity consumption.

    :bev_electricity_consumption_kwh:
        The context BEV electricity consumption.

    :ld_share:
        The share of electricity consumption attributable to light-duty.

    :md_share:
        The share of electricity consumption attributable to medium-duty.

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_column_names


class ContextElectricityConsumption:
    """
    **Loads and provides access to analysis context electricity consumption**

    """
    def __init__(self):
        self._data = {}
        self.df = pd.DataFrame()
        self.year_min = None
        self.year_max = None

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
            'context_id',
            'case_id',
            'bev_electricity_consumption_kwh',
            'ld_share',
            'md_share',
        }
        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[(df['context_id'] == batch_settings.context_name_liquid_fuel)
                    & (df['case_id'] == batch_settings.context_case_liquid_fuel), :]

        key = df['calendar_year']

        self.year_min = df['calendar_year'].min()
        self.year_max = df['calendar_year'].max()

        self._data = df.set_index(key).sort_index().to_dict(orient='index')

    def get_attribute_value(self, calendar_year, fleet=None):
        """

        Args:
            calendar_year (int): the calendar year of data to be returned
            fleet (str): e.g., 'ld' or 'md'

        Returns:
            The bev_electricity_consumption_kwh for the passed calendar year; if 'fleet' is passed, the fleet share is
            also returned.

        """
        return_list = [self._data[calendar_year]['bev_electricity_consumption_kwh']]

        if fleet:
            return_list.append(self._data[calendar_year][f'{fleet}_share'])

        if len(return_list) == 1:
            return return_list[0]
        else:
            return return_list
