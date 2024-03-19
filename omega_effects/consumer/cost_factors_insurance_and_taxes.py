"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,cost_factors_insurance_and_taxes,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        powertrain_type,body_style,item,value,dollar_basis,notes,
        all,all,averge_state_taxes,0.0502,
        all,sedan,average_insurance_cost,(vehicle_value * 0.009 + 220) * 1.19,2019
        all,cuv_suv,average_insurance_cost,(vehicle_value * 0.005 + 240) * 1.19,2019,
        ICE,all,average_depreciation_rate,0.149,
        HEV,all,average_depreciation_rate,0.149,


Data Column Name and Description

    :powertrain_type:
        E.g., BEV, ICE, HEV, PHEV

    :body_style:
        E.g., sedan, cuv_suv, pickup

    :item:
        The attribute name.

    :value:
        The attribute value associated with the paired attribute name.

    :dollar_basis:
        The dollar basis, if applicable, for the paired attribute value.

    :notes:
        User supplied notes ignored in code.

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class InsuranceAndTaxes:
    """
    Loads and provides access to insurance and tax cost factors by calendar year.

    """
    def __init__(self):
        self._data = {}

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
        input_template_name = 'cost_factors_insurance_and_taxes'
        input_template_version = 0.2
        input_template_columns = {
            'powertrain_type',
            'body_style',
            'item',
            'value',
            'dollar_basis',
            }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        cost_keys = pd.Series(zip(
            df['powertrain_type'],
            df['body_style'],
            df['item'],
        ))
        df.insert(0, 'cost_key', cost_keys)

        for cost_key in cost_keys:
            self._data[cost_key] = {}
            powertrain_type, body_style, item = cost_key
            cost_info = df[
                (df['powertrain_type'] == powertrain_type) & (df['body_style'] == body_style) & (df['item'] == item)
            ].iloc[0]

            self._data[cost_key] = {
                'value': {},
                'dollar_adjustment': 1,
            }
            if cost_info['dollar_basis'] > 0:
                adj_factor = batch_settings.ip_deflators.dollar_adjustment_factor(
                    batch_settings, cost_info['dollar_basis'], effects_log)
                self._data[cost_key]['dollar_adjustment'] = adj_factor

            self._data[cost_key]['value'] = compile(str(cost_info['value']), '<string>', 'eval')

    def get_attribute_value(self, powertrain_type, body_style, *attribute_names):
        """

        Get cost factors

        Args:
            powertrain_type (str): e.g., 'BEV', 'ICE', 'HEV', 'PHEV'
            body_style (str): e.g., 'sedan', 'cuv_suv', 'pickup'
            attribute_names (str): the attribute name(s) for which a value is sought

        Returns:
            Cost factor or list of cost factors

        """
        locals_dict = locals()
        values_list = []
        for attribute_name in attribute_names:
            adj_factor = self._data[(powertrain_type, body_style, attribute_name)]['dollar_adjustment']
            value = eval(self._data[(powertrain_type, body_style, attribute_name)]['value'], {}, locals_dict)
            values_list.append(value)

        if len(values_list) == 1:
            return values_list[0]

        return values_list

    def get_tax_rate(self, attribute_name):
        """

        Args:
            attribute_name (str): the attribute name for which a value is sought

        Returns:
            The tax rate value for the passed attribute_name

        """
        rate = eval(self._data[('all', 'all', attribute_name)]['value'], {}, {})

        return rate

    def calc_insurance_cost(self, avg_purchase_price, powertrain_type, body_style, age):
        """

        Args:
            avg_purchase_price (float): the average purchase price of the vehicle
            powertrain_type (str): e.g., 'BEV', 'ICE', 'HEV', 'PHEV'
            body_style (str): e.g., 'sedan', 'cuv_suv', 'pickup'
            age (int): the age of the vehicle

        Returns:
            The cost of insurance taking into consideration depreciation of the vehicle's value

        """
        locals_dict = locals()

        depreciation_rate = eval(
            self._data[(powertrain_type, 'all', 'average_depreciation_rate')]['value'], {}, locals_dict
        )
        vehicle_value = avg_purchase_price / (1 + depreciation_rate) ** age
        locals_dict.update({'vehicle_value': vehicle_value})
        adj_factor = self._data[('all', body_style, 'average_insurance_cost')]['dollar_adjustment']

        cost = eval(self._data[('all', body_style, 'average_insurance_cost')]['value'], {}, locals_dict) * adj_factor

        return cost
