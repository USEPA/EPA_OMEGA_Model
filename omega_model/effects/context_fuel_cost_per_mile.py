"""

Function to calculate fuel costs per mile in the reference session against which rebound effects can be calculated for
subsequent sessions.

----

**CODE**

"""
from omega_model import *


def calc_fuel_cost_per_mile(calendar_years):
    """

    Args:
        calendar_years: The calendar years included in the analysis.

    Returns:
        A dictionary of fuel costs per mile by vehicle_id and age.

    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal
    from context.fuel_prices import FuelPrice
    from context.onroad_fuels import OnroadFuel
    from common.omega_eval import Eval

    vehicle_attribute_list = [
        'base_year_vehicle_id',
        'name',
        'model_year',
        'base_year_reg_class_id',
        'reg_class_id',
        'context_size_class',
        'in_use_fuel_id',
        'market_class_id',
        'fueling_class',
        'base_year_powertrain_type',
        'body_style',
        'onroad_direct_co2e_grams_per_mile',
        'onroad_direct_kwh_per_mile',
    ]
    # let cpm refer to cost_per_mile
    context_fuel_cpm_dict = dict()
    vehicle_info_dict = dict()
    for calendar_year in calendar_years:

        vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

        calendar_year_fuel_cpm_dict = dict()
        for vad in vads:

            vehicle_fuel_cpm_dict = dict()

            # need vehicle info once for each vehicle_id, not every calendar year for each vehicle_id
            vehicle_id = int(vad['vehicle_id'])
            age = int(vad['age'])

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = VehicleFinal.get_vehicle_attributes(vehicle_id, vehicle_attribute_list)

            base_year_vehicle_id, name, model_year, base_year_reg_class_id, reg_class_id, size_class, in_use_fuel_id, \
            market_class_id, fueling_class, base_year_powertrain_type, body_style, \
            onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile \
                = vehicle_info_dict[vehicle_id]

            if model_year >= calendar_years[0]:

                onroad_kwh_per_mile = onroad_gallons_per_mile = onroad_miles_per_gallon = fuel_cpm = 0
                retail_price_e = retail_price_l = None

                fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})

                for fuel, fuel_share in fuel_dict.items():

                    # calc fuel cost per mile
                    if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                        retail_price_e = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel)
                        onroad_kwh_per_mile += onroad_direct_kwh_per_mile
                        fuel_cpm += onroad_kwh_per_mile * retail_price_e

                    elif fuel != 'US electricity' and onroad_direct_co2e_grams_per_mile:
                        retail_price_l = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel)
                        refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                        co2_emissions_grams_per_unit \
                            = OnroadFuel.get_fuel_attribute(calendar_year, fuel,
                                                            'direct_co2e_grams_per_unit') / refuel_efficiency
                        onroad_gallons_per_mile += onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                        onroad_miles_per_gallon = 1 / onroad_gallons_per_mile
                        fuel_cpm += onroad_gallons_per_mile * retail_price_l

                key = (int(base_year_vehicle_id), base_year_powertrain_type, int(model_year), int(age))
                if key in calendar_year_fuel_cpm_dict:
                    pass
                else:
                    vehicle_fuel_cpm_dict.update({
                        'session_name': omega_globals.options.session_name,
                        'key': key,
                        'base_year_vehicle_id': int(base_year_vehicle_id),
                        'calendar_year': int(calendar_year),
                        'model_year': int(model_year),
                        'age': int(age),
                        'base_year_reg_class_id': base_year_reg_class_id,
                        'reg_class_id': reg_class_id,
                        'context_size_class': size_class,
                        'in_use_fuel_id': in_use_fuel_id,
                        'market_class_id': market_class_id,
                        'fueling_class': fueling_class,
                        'base_year_powertrain_type': base_year_powertrain_type,
                        'body_style': body_style,
                        'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
                        'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                        'onroad_gallons_per_mile': onroad_gallons_per_mile,
                        'onroad_miles_per_gallon': onroad_miles_per_gallon,
                        'retail_price_per_gallon': retail_price_l,
                        'retail_price_per_kwh': retail_price_e,
                        'fuel_cost_per_mile': fuel_cpm,
                    })

                    calendar_year_fuel_cpm_dict[key] = vehicle_fuel_cpm_dict

        context_fuel_cpm_dict.update(calendar_year_fuel_cpm_dict)

    return context_fuel_cpm_dict
