"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent fatality rates (fatalities per billion miles) for the fleet.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,fatality_rates,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        model_year,calendar_year,age,average_fatality_rate,
        1996,1996,0,8.487042,
        1996,1997,1,8.364596,
        1996,1998,2,8.342017,

Data Column Name and Description
    :model_year:
        The model year of a given vehicle

    :calendar_year:
        The calendar year

    :age:
        The vehicle age

    :average_fatality_rate:
        The fatality rate in fatalities per billions miles travelled where "average" denotes the average effectiveness
        of passenger safety technology on vehicles.

----

**CODE**

"""
import pandas as pd

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class FatalityRates:
    """
    Loads and provides access to fatality rates by calendar year and vehicle age.

    """
    def __init__(self):
        self._data = dict()  # private dict
        self.model_year_max = None

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

        input_template_name = 'fatality_rates'
        input_template_version = 0.1
        input_template_columns = {
            'model_year',
            'age',
            'average_fatality_rate',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        df.fillna(0, inplace=True)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self.model_year_max = max(df['model_year'])

        key = pd.Series(zip(
            df['model_year'],
            df['age']
        ))
        df.insert(0, 'key', key)
        self._data = df.set_index(key).to_dict(orient='index')

    def get_fatality_rate(self, model_year, age):
        """

        Args:
            model_year (int): the model year for which a fatality rate is needed.
            age (age): vehicle age in years

        Returns:
            The average fatality rate for vehicles of a specific model year and age.

        """
        year = model_year
        if model_year > self.model_year_max:
            year = self.model_year_max

        return self._data[year, age]['average_fatality_rate']
