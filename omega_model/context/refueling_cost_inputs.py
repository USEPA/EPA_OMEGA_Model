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

       input_template_name:,refueling_inputs,input_template_version:,0.1

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
import omega_model.effects.general_functions as gen_fxns


class RefuelingCostInputs(OMEGABase):
    """
    **Loads and provides access to refueling cost input values for refueling cost calculations.**

    """
    _data = dict()  # private dict of general input attributes and values

    @staticmethod
    def calc_bev_refueling_cost_per_mile(veh_type, range):
        """

        Args:
            veh_type (string): The type of vehicle, e.g., 'car', 'suv', 'truck'.
            range (integer): The range (miles) of the BEV on a full charge.

        Returns:
            The refueling cost per mile for the given veh_type.

        """
        miles_to_charge_x2_factor = RefuelingCostInputs._data[f'miles_to_mid_trip_charge_{veh_type}']['x_squared_factor']
        miles_to_charge_x_factor = RefuelingCostInputs._data[f'miles_to_mid_trip_charge_{veh_type}']['x_factor']
        miles_to_charge_constant = RefuelingCostInputs._data[f'miles_to_mid_trip_charge_{veh_type}']['constant']

        share_of_miles_x2_factor = RefuelingCostInputs._data[f'share_of_miles_charged_mid_trip_{veh_type}']['x_squared_factor']
        share_of_miles_x_factor = RefuelingCostInputs._data[f'share_of_miles_charged_mid_trip_{veh_type}']['x_factor']
        share_of_miles_constant = RefuelingCostInputs._data[f'share_of_miles_charged_mid_trip_{veh_type}']['constant']

        if range <= 200:
            charge_rate = RefuelingCostInputs._data[f'miles_per_hour_charge_rate_under_201']['constant']
        else:
            charge_rate = RefuelingCostInputs._data[f'miles_per_hour_charge_rate_over_201']['constant']

        travel_value = RefuelingCostInputs._data[f'dollars_per_hour_travel_time_{veh_type}']['constant']
        fixed_time = RefuelingCostInputs._data[f'fixed_refueling_minutes_{veh_type}']['constant']

        charge_frequency = miles_to_charge_x2_factor * range ** 2 + miles_to_charge_x_factor * range + miles_to_charge_constant
        share_charged = share_of_miles_x2_factor * range ** 2 + share_of_miles_x_factor * range + share_of_miles_constant

        refueling_cost_per_mile = ((fixed_time / 60) / charge_frequency + (share_charged / charge_rate)) * travel_value

        return refueling_cost_per_mile

    @staticmethod
    def calc_liquid_refueling_cost_per_gallon(veh_type):
        """

        Args:
            veh_type (string): The type of vehicle, e.g., 'car', 'suv', 'truck'.

        Returns:
            The refueling cost per mile for the given veh_type.


        """
        refuel_rate = RefuelingCostInputs._data['gallons_per_minute_refuel_rate']['constant']
        refuel_share = RefuelingCostInputs._data[f'tank_gallons_share_refueled_{veh_type}']['constant']
        tank_gallons = RefuelingCostInputs._data[f'tank_gallons_{veh_type}']['constant']

        travel_value = RefuelingCostInputs._data[f'dollars_per_hour_travel_time_{veh_type}']['constant']
        fixed_time = RefuelingCostInputs._data[f'fixed_refueling_minutes_{veh_type}']['constant']
        scaler = RefuelingCostInputs._data['liquid_refueling_share_included']['constant']

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
        RefuelingCostInputs._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'refueling_cost_inputs'
        input_template_version = 0.1
        input_template_columns = {'item',
                                  'x_squared_factor',
                                  'x_factor',
                                  'constant',
                                  'dollar_basis',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            cols_to_convert = [col for col in df.columns if 'constant' in col]

            df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            if not template_errors:
                RefuelingCostInputs._data = df.set_index('item').to_dict(orient='index')

        return template_errors
