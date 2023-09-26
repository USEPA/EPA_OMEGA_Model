"""

**Routines to load General Inputs for Effects.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various general for use in effects calculations.

File Type
    comma-separated values (CSV)

Sample Header
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

Data Row Name and Description:
    :kwh_us_annual:
        This attribute is not used in code.

    :gal_per_bbl:
        The number of gallons in a barrel of crude oil.

    :gallons_of_gasoline_us_annual:
        This attribute is not used in code.

    :bbl_oil_us_annual:
        This attribute is not used in code.

    :year_for_compares:
        This attribute is not used in code.

    :e0_in_retail_gasoline:
        The amount of petroleum-based gasoline in a gallon of retail gasoline where 'e' refers to ethanol.

    :e0_energy_density_ratio:
        The ratio of petroleum-based gasoline (e0) to crude oil energy density in British Thermal Units (BTU) per gallon.

    :diesel_energy_density_ratio:
        The ratio of diesel fuel to crude oil energy density in British Thermal Units (BTU) per gallon.

    :grams_per_us_ton:
        The number of grams in a US or short ton.

    :grams_per_metric_ton:
        The number of grams in a metric ton.

    :share_of_fuel_refined_domestically:
        The share of petroleum fuel refined domestically.

    :fuel_reduction_leading_to_reduced_domestic_refining:
        The share of reduced petroleum fuel consumption leading to reduced domestic refining of crude oil; if 0 then domestic
        refining is assumed to be unaffected by reduced petroleum fuel demand; if 1 then all reduced petroleum demand
        reduces domestic refining an equal amount.

    :years_in_consumer_view:
        The number of years of a vehicle's lifetime to include in the model year lifetime, or consumer view, calculations.

    :include_powertrain_type_in_consumer_cost_view:
        If 0 then powertrain_type (i.e., ICE/HEV/PHEV/BEV) is not included in the model year lifetime, or consumer view, sales
        weighting; if 1 then powertrain_type is included.

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class GeneralInputsForEffects:
    """
    **Loads and provides access to general input values for effects calculations.**

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
