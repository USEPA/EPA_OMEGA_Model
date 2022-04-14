"""

**Routines to load Refueling Cost Inputs.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in refueling cost calculations.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,refueling_cost,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        Several of the entries for BEVs are curves according to the equation (Ax^2 +Bx + C), where the capital letters are the entries in the worksheet and x is generally range.

        item,x_squared_factor,x_factor,constant,dollar_basis
        miles_to_mid_trip_charge_car,0.18,-64.4,7840
        miles_to_mid_trip_charge_suv,0.125,-45.5,5900
        miles_to_mid_trip_charge_truck,0.135,-49.9,6290

Data Column Name and Description

:item:
    The refueling cost curve attribute name.

:x_squared_factor:
    The attribute value.

:x_factor:
    The attribute value.

:constant:
    The attribute value.

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
from effects.general_functions import dollar_adjustment_factor


class RefuelingCost(OMEGABase):
    """
    **Loads and provides access to refueling cost input values for refueling cost calculations.**

    """
    _data = dict()  # private dict of general input attributes and values

    @staticmethod
    def calc_bev_refueling_cost_per_mile(type, range):
        """

        Args:
            type (string): The type of vehicle, e.g., 'car', 'suv', 'truck'.
            range (integer): The range (miles) of the BEV on a full charge.

        Returns:
            The refueling cost per mile for the given veh_type.

        """
        locals_dict = locals()

        if range <= 200:
            charge_rate = eval(RefuelingCost._data['under_200', 'miles_per_hour_charge_rate']['value'], {}, locals_dict)
        else:
            charge_rate = eval(RefuelingCost._data['over_201', 'miles_per_hour_charge_rate']['value'], {}, locals_dict)

        charge_frequency = eval(RefuelingCost._data[type, 'miles_to_mid_trip_charge']['value'], {}, locals_dict)
        share_charged = eval(RefuelingCost._data[type, 'share_of_miles_charged_mid_trip']['value'], {}, locals_dict)

        travel_value = eval(RefuelingCost._data[type, 'dollars_per_hour_travel_time']['value'], {}, locals_dict)
        adj_factor = RefuelingCost._data[type, 'dollars_per_hour_travel_time']['dollar_adjustment']
        travel_value = travel_value * adj_factor

        fixed_time = eval(RefuelingCost._data[type, 'fixed_refueling_minutes']['value'], {}, locals_dict)

        refueling_cost_per_mile = ((fixed_time / 60) / charge_frequency + (share_charged / charge_rate)) * travel_value

        return refueling_cost_per_mile

    @staticmethod
    def calc_liquid_refueling_cost_per_gallon(type):
        """

        Args:
            type (string): The type of vehicle, e.g., 'car', 'suv', 'truck'.

        Returns:
            The refueling cost per mile for the given veh_type.


        """
        locals_dict = locals()

        refuel_rate = eval(RefuelingCost._data['all', 'gallons_per_minute_refuel_rate']['value'], {}, locals_dict)
        refuel_share = eval(RefuelingCost._data[type, 'tank_gallons_share_refueled']['value'], {}, locals_dict)
        tank_gallons = eval(RefuelingCost._data[type, 'tank_gallons']['value'], {}, locals_dict)

        travel_value = eval(RefuelingCost._data[type, 'dollars_per_hour_travel_time']['value'], {}, locals_dict)
        adj_factor = RefuelingCost._data[type, 'dollars_per_hour_travel_time']['dollar_adjustment']
        travel_value = travel_value * adj_factor

        fixed_time = eval(RefuelingCost._data[type, 'fixed_refueling_minutes']['value'], {}, locals_dict)

        scaler = eval(RefuelingCost._data['all', 'liquid_refueling_share_included']['value'], {}, locals_dict)

        refueling_cost_per_gallon = (1 / (tank_gallons * refuel_share)) \
                                    * ((fixed_time + (tank_gallons * refuel_share) / refuel_rate) / 60) \
                                    * travel_value \
                                    * scaler

        return refueling_cost_per_gallon

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        RefuelingCost._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'refueling_cost'
        input_template_version = 0.2
        input_template_columns = {'type',
                                  'item',
                                  'value',
                                  'dollar_basis',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:

                cost_keys = zip(df['type'], df['item'])

                for cost_key in cost_keys:

                    RefuelingCost._data[cost_key] = dict()
                    type, item = cost_key

                    cost_info = df[(df['type'] == type) & (df['item'] == item)].iloc[0]

                    RefuelingCost._data[cost_key] = {'value': dict(),
                                                     'dollar_adjustment': 1}

                    if cost_info['dollar_basis'] > 0:
                        adj_factor = dollar_adjustment_factor('ip_deflators', int(cost_info['dollar_basis']))
                        RefuelingCost._data[cost_key]['dollar_adjustment'] = adj_factor

                    RefuelingCost._data[cost_key]['value'] = compile(cost_info['value'], '<string>', 'eval')

        return template_errors
