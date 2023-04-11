"""

**Routines to powertrain cost.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,powertrain_cost,input_template_version:,0.1,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        powertrain_type,item,value,quantity,dollar_basis,notes
        ALL,dollars_per_cylinder,((-28.814) * CYL + 726.27) * CYL * MARKUP_ICE,,2019,
        ALL,dollars_per_liter,((400) * LITERS) * MARKUP_ICE,,2019,
        ALL,gdi,((43.237) * CYL + 97.35) * MARKUP_ICE,,2019,
        BEV,battery_offset,{"dollars_per_kwh": {2023: -9, 2024: -18, 2025: -27, 2026: -36, 2027: -45, 2028: -45, 2029: -45, 2030: -33.75, 2031: -22.50, 2032: -11.25, 2033: -0}},,,

Data Column Name and Description

    :powertrain_type:
        Vehicle powertrain type, e.g. 'ICE', 'PHEV', etc

    :item:
        The name of the powertrain component associated with the cost value

    :value:
        The component cost value or equation to be evaulated

    :quantity:
        Component quantity per vehicle, if applicable

    :dollar_basis:
        The dollar basis year for the cost value, e.g. ``2020``

    :notes:
        Optional notes related to the data row

----

**CODE**

"""
from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class PowertrainCost:
    """
    **Loads and provides access to maintenance cost input values for effects calculations.**

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
        input_template_name = 'powertrain_cost'
        input_template_version = 0.1
        input_template_columns = {
            'powertrain_type',
            'item',
            'value',
            'quantity',
            'dollar_basis',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df['value'] = df['value'] \
            .apply(lambda x: str.replace(x, 'max(', 'np.maximum(').replace('min(', 'np.minimum('))

        cost_keys = zip(
            df['powertrain_type'],
            df['item'],
        )

        for cost_key in cost_keys:

            self._data[cost_key] = dict()
            powertrain_type, item = cost_key

            cost_info = df[(df['powertrain_type'] == powertrain_type) & (df['item'] == item)].iloc[0]

            self._data[cost_key] = {'value': dict(),
                                    'quantity': 0,
                                    'dollar_adjustment': 1}

            self._data[cost_key]['value'] = compile(str(cost_info['value']), '<string>', 'eval')

    def get_battery_tax_offset(self, year, battery_kwh):
        """
        Get battery tax offset.

        Args:
            year (int): year for which battery tax credit is needed.
            battery_kwh (float): battery pack capacity in kWh

        Returns:
            The battery tax offset (dollars per kWh credit) for the given year.

        """
        battery_offset = 0
        battery_offset_dict = eval(self._data['BEV', 'battery_offset']['value'])
        battery_offset_min_year = min(battery_offset_dict['dollars_per_kwh'].keys())
        battery_offset_max_year = max(battery_offset_dict['dollars_per_kwh'].keys())
        if battery_offset_min_year <= year <= battery_offset_max_year:
            battery_offset = battery_offset_dict['dollars_per_kwh'][year] * battery_kwh

        return battery_offset
