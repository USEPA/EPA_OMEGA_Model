"""

Vehicle re-registration, fixed by age.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents the re-registered proportion of vehicles by model year, age and market class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,consumer.reregistration_fixed_by_age,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_model_year,age,market_class_id,reregistered_proportion
        1970,0,non_hauling.BEV,1
        1970,1,non_hauling.BEV,0.987841531
        1970,2,non_hauling.BEV,0.976587217
        1970,0,hauling.ICE,1
        1970,1,hauling.ICE,0.977597055
        1970,2,hauling.ICE,0.962974697

Data Column Name and Description

:start_model_year:
    The start vehicle model year of the re-registration data, values apply until next available start year

:age:
    Vehicle age, in years

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:reregistered_proportion:
    The fraction of vehicles re-registered, [0..1]

----

**CODE**


"""
from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names
from omega_effects.effects_code.consumer import deregionalizer


class Reregistration:
    """
    **Load and provide access to vehicle re-registration data by model year, market class ID and age.**

    """
    def __init__(self):
        self._data = dict()

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

        input_template_name = 'consumer.reregistration_fixed_by_age'
        input_template_version = 0.2
        input_template_columns = {
            'start_model_year',
            'age',
            'market_class_id',
            'reregistered_proportion',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = deregionalizer.remove_region_entries(df, 'market_class_id', 'r2zev', 'r1nonzev',
                                                  'sedan_wagon', 'cuv_suv_van', 'pickup')

        # convert dataframe to dict keyed by market class ID, age, and start year
        self._data = df.set_index(['market_class_id', 'age', 'start_model_year']).sort_index().to_dict(orient='index')

        # add 'start_year' key which returns start years by market class ID
        self._data.update(
            df[['market_class_id', 'age', 'start_model_year']].set_index('market_class_id').to_dict(orient='series'))

    def get_reregistered_proportion(self, model_year, market_class_id, age):
        """
        Get vehicle re-registered proportion [0..1] by market class and age.

        Args:
            model_year (int): the model year of the re-registration data
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            Re-registered proportion [0..1]

        """
        cache_key = (model_year, market_class_id, age)

        if cache_key not in self._data:
            start_years = self._data['start_model_year'][market_class_id].values

            max_age = int(max(self._data['age'][market_class_id].values))

            if age > max_age:
                self._data[cache_key] = 0
            elif len(start_years[start_years <= model_year]) > 0:
                year = max(start_years[start_years <= model_year])
                self._data[cache_key] = self._data[market_class_id, age, year]['reregistered_proportion']
            else:
                raise Exception('Missing registration fixed by age parameters for %s, %d or prior' %
                                (market_class_id, model_year))

        return self._data[cache_key]
