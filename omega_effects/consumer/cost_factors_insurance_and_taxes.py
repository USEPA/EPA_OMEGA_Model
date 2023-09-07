"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,cost_factors_insurance_and_taxes,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,value,notes,
        averge_state_taxes,0.0502,
        average_depreciation_rate,0.149,
        average_insurance_rate,0.0186,
        totaled_vehicle_adjustment,0.8,


Data Column Name and Description

    :item:
        The data item or attribute name.

    :value:
        The attribute value associated with the paired attribute name.

    :notes:
        User supplied notes ignored in code.

----

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class InsuranceAndTaxes:
    """
    Loads and provides access to insurance and tax cost factors by calendar year.

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
        input_template_name = 'cost_factors_insurance_and_taxes'
        input_template_version = 0.1
        input_template_columns = {
            'item',
            'value',
            }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index('item').to_dict(orient='index')

    def get_attribute_value(self, *attribute_names):
        """

        Get cost factors

        Args:
            attribute_names (str): the attribute name(s) for which a value is sought

        Returns:
            Cost factor or list of cost factors

        """
        values_list = []
        for attribute_name in attribute_names:
            values_list.append(self._data[attribute_name]['value'])

        if len(values_list) == 1:
            return values_list[0]

        return values_list

    def calc_insurance_cost(self, avg_purchase_price, age):
        """

        Args:
            avg_purchase_price (float): the average purchase price of the vehicle
            age (int): the age of the vehicle

        Returns:
            The cost of insurance taking into consideration depreciation of the vehicle's value

        """
        depreciation_rate, insurance_rate, totaled_adjustment = self.get_attribute_value(
            'average_depreciation_rate', 'average_insurance_rate', 'totaled_vehicle_adjustment'
        )
        cost = avg_purchase_price * insurance_rate * totaled_adjustment / (1 + depreciation_rate) ** age

        return cost
