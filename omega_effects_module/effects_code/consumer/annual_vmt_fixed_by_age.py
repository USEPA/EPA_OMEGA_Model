"""

**Routines to load and provide access to annual vehicle miles travelled (VMT) by market class and age.**

The data represents a fixed VMT schedule by age.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents the re-registered proportion of vehicles by calendar year, age and market class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,0.2

Sample Header
    .. csv-table::

        input_template_name:,consumer.annual_vmt_fixed_by_age,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,age,market_class_id,annual_vmt
        2019,0,non_hauling.BEV,14699.55515
        2019,1,non_hauling.BEV,14251.70373
        2019,2,non_hauling.BEV,14025.35397
        2019,0,hauling.ICE,15973.88982
        2019,1,hauling.ICE,15404.1216
        2019,2,hauling.ICE,14840.93011

:start_year:
    Start year of annual VMT data, values apply until the next available start year

:age:
    Vehicle age, in years

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:annual_vmt:
    Vehicle miles travelled per year at the given age for the given market class ID

----

**CODE**

"""
import numpy as np

from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class OnroadVMT:
    """
    **Loads and provides access to annual Vehicle Miles Travelled by calendar year, market class, and age.**

    """
    def __init__(self):

        self._data = dict()  # private dict, on-road VMT by market class ID and age
        self.cumulative_vmt = dict()

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

        input_template_name = 'consumer.annual_vmt_fixed_by_age'
        input_template_version = 0.2
        input_template_columns = {
            'start_year',
            'age',
            'market_class_id',
            'annual_vmt',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        # convert dataframe to dict keyed by market class ID, age, and start year
        self._data = df.set_index(['market_class_id', 'age', 'start_year']).sort_index().to_dict(orient='index')
        # add 'start_year' key which returns start years by market class ID
        self._data.update(df[['market_class_id', 'age', 'start_year']].set_index('market_class_id').to_dict(orient='dict'))

    def get_vmt(self, calendar_year, market_class_id, age):
        """
        Get vehicle miles travelled by calendar year, market class and age.

        Args:
            calendar_year (int): calendar year of the VMT data
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            (float) Annual vehicle miles travelled.

        """
        cache_key = (calendar_year, market_class_id, age)

        if cache_key not in self._data:
            start_years = np.array(self._data['start_year'][market_class_id])

            if len(start_years[start_years <= calendar_year]) > 0:
                year = max(start_years[start_years <= calendar_year])
                self._data[cache_key] = self._data[market_class_id, age, year]['annual_vmt']
            else:
                raise Exception('Missing onroad VMT fixed by age parameters for %s, %d or prior' %
                                (market_class_id, calendar_year))

        return self._data[cache_key]

    def get_cumulative_vmt(self, market_class_id, age):

        if (market_class_id, age) in self.cumulative_vmt:
            return self.cumulative_vmt[market_class_id, age]
        else:
            cumulative_vmt = sum([v['annual_vmt'] for k, v in self._data.items()
                                  if k[0] == market_class_id
                                  and k[1] <= age]
                                 )
            self.cumulative_vmt[market_class_id, age] = cumulative_vmt

            return cumulative_vmt
