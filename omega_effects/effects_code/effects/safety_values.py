"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent safety values associated with mass reduction in the fleet.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,safety_values,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        body_style,nhtsa_safety_class,threshold_lbs,change_per_100_lbs_below_threshold,change_per_100_lbs_at_or_above_threshold
        sedan,PC,3201,0.012,0.0042
        pickup,LT/SUV,5014,0.0031,-0.0061
        cuv_suv,CUV/Minivan,3872,-0.0025,-0.0025

Data Column Name and Description
    :body_style:
        The OMEGA body_style (e.g., sedan, pickup, cuv_suv)

    :nhtsa_safety_class:
        The NHTSA safety class (e.g., PC, LT/SUV, CUV/Minivan)

    :threshold_lbs:
        The curb weight, in pounds, above and below which safety values may change.

    :change_per_100_lbs_below_threshold:
        A percentage change in the fatality rate associated with reductions in curb weight below the associated curb
        weight threshold; a positive value denotes an increase in fatality rate associated with a reduced curb weight
        while a negative value denotes a decrease in fatality rate associated with a reduced curb weight; increased
        curb weights would have the opposite effect on fatality rate.

    :change_per_100_lbs_at_or_above_threshold:
        A percentage change in the fatality rate associated with reductions in curb weight above the associated curb
        weight threshold; a positive value denotes an increase in fatality rate associated with a reduced curb weight
        while a negative value denotes a decrease in fatality rate associated with a reduced curb weight; increased
        curb weights would have the opposite effect on fatality rate.

----

**CODE**

"""
import pandas as pd

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class SafetyValues:
    """
    Loads and provides access to safety values by body style.

    """
    def __init__(self):
        self._data = dict()  # private dict

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

        input_template_name = 'safety_values'
        input_template_version = 0.1
        input_template_columns = {
            'body_style',
            'nhtsa_safety_class',
            'threshold_lbs',
            'change_per_100_lbs_below_threshold',
            'change_per_100_lbs_at_or_above_threshold',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        df.fillna(0, inplace=True)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index('body_style').to_dict(orient='index')

    def get_safety_values(self, body_style):
        """

        Get safety values by body style.

        Args:
            body_style (str): the OMEGA body style (e.g., sedan, cuv_suv, pickup)

        Returns:
            The curb weight threshold and percentage changes in fatality rates for weight changes above and below
            that threshold.

        """
        threshold = self._data[body_style]['threshold_lbs']
        change_below = self._data[body_style]['change_per_100_lbs_below_threshold']
        change_above = self._data[body_style]['change_per_100_lbs_at_or_above_threshold']

        return threshold, change_below, change_above
