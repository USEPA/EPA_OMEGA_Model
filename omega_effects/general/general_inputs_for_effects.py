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
    :gal_per_bbl:
        The number of gallons in a barrel of crude oil.

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

    :years_in_consumer_view_1:
        The number of years of a vehicle's lifetime to include in the model year lifetime, or consumer view, calculations.

    :years_in_consumer_view_2:
        An additional number of years of a vehicle's lifetime to include in the model year lifetime, or consumer view, calculations.

    :include_powertrain_type_in_consumer_cost_view:
        If 0 then powertrain_type (i.e., ICE/HEV/PHEV/BEV) is not included in the model year lifetime, or consumer view, sales
        weighting; if 1 then powertrain_type is included.

    :social_discount_rates:
        The discount rates to be used for discounting of costs and non-GHG pollutant benefits; the rate(s) should be entered
        in square brackets, separated by commas and entered as decimal values, i.e., 3% and 7% should be entered as
        [0.03, 0.07] .

    :gwp_ch4:
        The CO2 equivalent global warming potential for CH4. This is used for physical effects only as OMEGA does not apply
        a Social Cost of CO2e value.

    :gwp_n2o:
        The CO2 equivalent global warming potential for N2O. This is used for physical effects only as OMEGA does not apply
        a Social Cost of CO2e value.

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

        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index('item').to_dict(orient='index')

    def get_value(self, *attributes):
        """
        Get the attribute value for the given attribute.

        Args:
            attributes (str): the attribute(s) for which value(s) are sought.

        Returns:
            The value of the given attribute.

        """
        # note that eval is used here since list-like entry for social discount rates causes all entries to be objects
        attribute_values = []
        for attribute in attributes:
            attribute_values.append(eval(self._data[attribute]['value']))
        if len(attribute_values) == 1:
            return attribute_values[0]

        return attribute_values
