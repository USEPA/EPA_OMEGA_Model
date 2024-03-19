"""

**Routines to powertrain cost.**

This omega_effects module reads the powertrain cost file used in the compliance run for the given session for the sole
purpose of determinining the battery offset. The SessionSettings class searches for the applicable powertrain cost
file for the given session so the user need not worry about the powertrain cost file for effects calculations.

----

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class PowertrainCost:
    """
    **Loads and provides access to the battery_offsets set via the applicable powertrain_cost input file.**

    """
    def __init__(self):
        self._data = dict()

    def init_from_file(self, batch_settings, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            batch_settings: an instance of the BatchSettings class.
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_version = 0.1
        input_template_columns = {
            'powertrain_type',
            'item',
            'value',
        }
        identifier = 'item'
        if batch_settings.powertrain_costs_fev:
            input_template_version = 0.21
            input_template_columns = {
                'powertrain_type',
                'system',
                'value',
            }
            identifier = 'system'

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_version, input_template_name=None, effects_log=effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df['value'] = df['value'] \
            .apply(lambda x: str.replace(x, 'max(', 'np.maximum(').replace('min(', 'np.minimum('))

        df = df.loc[df[identifier] == 'battery_offset', :]
        powertrain_types = df['powertrain_type']

        for powertrain_type in powertrain_types:
            self._data[powertrain_type] = {}
            cost_info = df[df['powertrain_type'] == powertrain_type].iloc[0]

            self._data[powertrain_type] = {
                'value': {}
            }

            self._data[powertrain_type]['value'] = compile(str(cost_info['value']), '<string>', 'eval')

    def get_battery_tax_offset(self, year, battery_kwh, powertrain_type):
        """
        Get battery tax offset.

        Args:
            year (int): year for which battery tax credit is needed.
            battery_kwh (float): battery pack capacity in kWh
            powertrain_type (str): 'BEV' or 'PHEV'

        Returns:
            The battery tax offset (dollars per kWh credit) for the given year.

        """
        battery_offset = 0
        battery_offset_dict = eval(self._data[powertrain_type]['value'])
        battery_offset_min_year = min(battery_offset_dict['dollars_per_kwh'])
        battery_offset_max_year = max(battery_offset_dict['dollars_per_kwh'])
        if battery_offset_min_year <= year <= battery_offset_max_year:
            battery_offset = battery_offset_dict['dollars_per_kwh'][year] * battery_kwh

        return battery_offset
