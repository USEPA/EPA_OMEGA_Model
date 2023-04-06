"""

**Routines to load Refueling Cost Inputs.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in refueling cost calculations.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,refueling_cost,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        type,item,value,dollar_basis
        car,miles_to_mid_trip_charge,7840 + -64.4 * range + 0.18 * range ** 2,
        truck,miles_to_mid_trip_charge,6290 + -49.9 * range + 0.135 * range ** 2,
        suv,share_of_miles_charged_mid_trip,0.241 + -0.001 * range + 0.000001 * range ** 2,
        truck,fixed_refueling_minutes,3.5,

Data Column Name and Description

:type:
    The vehicle type, e.g. 'car', 'suv', etc

:item:
    The refueling cost curve attribute name

:value:
    Scalar value or expression to be evaluated for cost

:dollar_basis:
    The dollar basis year for the cost value, e.g. ``2020``

**CODE**

"""
from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class RefuelingCost:
    """
    **Loads and provides access to refueling cost input values for refueling cost calculations.**

    """
    def __init__(self):
        self._data = dict()

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
        input_template_name = 'refueling_cost'
        input_template_version = 0.2
        input_template_columns = {
            'type',
            'item',
            'value',
            'dollar_basis',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        cost_keys = zip(
            df['type'],
            df['item'],
        )

        for cost_key in cost_keys:

            self._data[cost_key] = dict()
            vehicle_type, item = cost_key

            cost_info = df[(df['type'] == vehicle_type) & (df['item'] == item)].iloc[0]

            self._data[cost_key] = {
                'value': dict(),
                'dollar_adjustment': 1,
            }

            if cost_info['dollar_basis'] > 0:
                adj_factor = \
                    batch_settings.ip_deflators.dollar_adjustment_factor(
                        batch_settings, int(cost_info['dollar_basis']), effects_log)
                self._data[cost_key]['dollar_adjustment'] = adj_factor

            self._data[cost_key]['value'] = compile(cost_info['value'], '<string>', 'eval')

    def calc_bev_refueling_cost_per_mile(self, vehicle_type, bev_range):
        """

        Args:
            vehicle_type (str): The type of vehicle, e.g., 'car', 'suv', 'truck'.
            bev_range (int): The range (miles) of the BEV on a full charge.

        Returns:
            The refueling cost per mile for the given veh_type.

        """
        locals_dict = locals()
        locals_dict['range'] = bev_range
        if bev_range <= 200:
            charge_rate = eval(self._data['under_200', 'miles_per_hour_charge_rate']['value'], {}, locals_dict)
        else:
            charge_rate = eval(self._data['over_201', 'miles_per_hour_charge_rate']['value'], {}, locals_dict)

        charge_frequency = eval(self._data[vehicle_type, 'miles_to_mid_trip_charge']['value'], {}, locals_dict)
        share_charged = eval(self._data[vehicle_type, 'share_of_miles_charged_mid_trip']['value'], {}, locals_dict)

        travel_value = eval(self._data[vehicle_type, 'dollars_per_hour_travel_time']['value'], {}, locals_dict)
        adj_factor = self._data[vehicle_type, 'dollars_per_hour_travel_time']['dollar_adjustment']
        travel_value = travel_value * adj_factor

        fixed_time = eval(self._data[vehicle_type, 'fixed_refueling_minutes']['value'], {}, locals_dict)

        refueling_cost_per_mile = ((fixed_time / 60) / charge_frequency + (share_charged / charge_rate)) * travel_value

        return refueling_cost_per_mile

    def calc_liquid_refueling_cost_per_gallon(self, vehicle_type):
        """

        Args:
            vehicle_type (str): The type of vehicle, e.g., 'car', 'suv', 'truck'.

        Returns:
            The refueling cost per mile for the given veh_type.

        """
        locals_dict = locals()

        refuel_rate = eval(self._data['all', 'gallons_per_minute_refuel_rate']['value'], {}, locals_dict)
        refuel_share = eval(self._data[vehicle_type, 'tank_gallons_share_refueled']['value'], {}, locals_dict)
        tank_gallons = eval(self._data[vehicle_type, 'tank_gallons']['value'], {}, locals_dict)

        travel_value = eval(self._data[vehicle_type, 'dollars_per_hour_travel_time']['value'], {}, locals_dict)
        adj_factor = self._data[vehicle_type, 'dollars_per_hour_travel_time']['dollar_adjustment']
        travel_value = travel_value * adj_factor

        fixed_time = eval(self._data[vehicle_type, 'fixed_refueling_minutes']['value'], {}, locals_dict)

        scaler = eval(self._data['all', 'liquid_refueling_share_included']['value'], {}, locals_dict)

        refueling_cost_per_gallon = (1 / (tank_gallons * refuel_share)) \
                                    * ((fixed_time + (tank_gallons * refuel_share) / refuel_rate) / 60) \
                                    * travel_value \
                                    * scaler

        return refueling_cost_per_gallon
