"""

**Routines to load General Inputs for Effects.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various general for use in effects calculations.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,general_inputs_for_effects,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,value,notes
        gal_per_bbl,42,gallons per barrel of oil
        imported_oil_share,0.91,estimated oil import reduction as percent of total oil demand reduction
        grams_per_uston,907185,

Data Column Name and Description

:item:
    The attribute name.

:value:
    The attribute value

:notes:
    Descriptive information regarding the attribute name and/or value.

**CODE**

"""
from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class GeneralInputsForEffects:
    """
    **Loads and provides access to general input values for effects calculations.**

    """
    def __init__(self):
        self._data = dict()  # private dict of general input attributes and values

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        df = read_input_file(filepath, effects_log)

        input_template_name = 'general_inputs_for_effects'
        input_template_version = 0.1
        input_template_columns = {
            'item',
            'value',
            'notes',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index('item').to_dict(orient='index')

    def get_value(self, attribute):
        """
        Get the attribute value for the given attribute.

        Args:
            attribute (str): the attribute(s) for which value(s) are sought.

        Returns:
            The value of the given attribute.

        """
        attribute_value = self._data[attribute]['value']

        return attribute_value
