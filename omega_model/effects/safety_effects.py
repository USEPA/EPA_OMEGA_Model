"""

Functions to get vehicle data based on vehicle ID, safety values based on body style and fatality rates based on
calendar year and vehicle age, and to calculate fatalities.

----

**CODE**

"""
import pandas as pd

from omega_model import *


def get_safety_values(body_style):
    """

    Args:
        body_style (str): the OMEGA body style (e.g., sedan, cuv_suv, pickup)

    Returns:
        The curb weight threshold and percentage changes in fatality rates for weight changes above and below
        that threshold.

    """
    from effects.safety_values import SafetyValues

    return SafetyValues.get_safety_values(body_style)


def get_fatality_rate(model_year, age):
    """

    Args:
        model_year (int): the model year for which a fatality rate is needed.

    Returns:
        The average fatality rate for vehicles of a specific model year and age.

    """
    from effects.fatality_rates import FatalityRates

    return FatalityRates.get_fatality_rate(model_year, age)


def calc_lbs_changed(base_weight, final_weight):
    """

    Args:
        base_weight: (numeric); base curb weight in pounds
        final_weight: (numeric); final curb weight in pounds

    Returns:
        The change in curb weight - positive denotes a weight increase, negative a weight decrease.

    """
    return final_weight - base_weight


def calc_lbs_changed_below_threshold(threshold, base_weight, final_weight):
    """

    Args:
        threshold: (numeric); the curb weight threshold, in pounds, above and below which safety values change
        base_weight: (numeric); base curb weight in pounds
        final_weight: (numeric); final curb weight in pounds

    Returns:
        The portion of the weight change that occurs below the threshold - positive denotes a weight increase,
        negative a weight decrease.

    """
    if threshold < base_weight and threshold < final_weight:
        lbs_changed = 0

    elif base_weight < threshold and final_weight < threshold:
        lbs_changed = final_weight - base_weight

    elif base_weight < threshold < final_weight:
        lbs_changed = threshold - base_weight

    elif final_weight < threshold < base_weight:
        lbs_changed = final_weight - threshold

    else:
        lbs_changed = 10000  # this flags a logic error

    return lbs_changed


def calc_lbs_changed_above_threshold(threshold, base_weight, final_weight):
    """

    Args:
        threshold: (numeric); the curb weight threshold, in pounds, above and below which safety values change
        base_weight: (numeric); base curb weight in pounds
        final_weight: (numeric); final curb weight in pounds

    Returns:
        The portion of the weight change that occurs above the threshold - positive denotes a weight increase,
        negative a weight decrease.

    """
    if base_weight < threshold and final_weight < threshold:
        lbs_changed = 0

    elif threshold <= base_weight and threshold <= final_weight:
        lbs_changed = final_weight - base_weight

    elif base_weight <= threshold <= final_weight:
        lbs_changed = final_weight - threshold

    elif final_weight <= threshold <= base_weight:
        lbs_changed = threshold - base_weight

    else:
        lbs_changed = 10000  # this flags a logic error

    return lbs_changed


def calc_safety_effects(calendar_years, vmt_adjustments, context_fuel_cpm_dict):
    """

    Args:
        calendar_years: The years for which safety effects will be calculated.
        vmt_adjustments: object; an object of the AdjustmentsVMT class.
        context_fuel_cpm_dict: dictionary; the session 0 fuel costs per mile by vehicle_id and age.

    Returns:
        A dictionary of various safety effects, including fatalities.

    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal
    from context.fuel_prices import FuelPrice
    from context.onroad_fuels import OnroadFuel
    from context.new_vehicle_market import NewVehicleMarket
    from effects.general_functions import calc_rebound_effect
    from common.omega_eval import Eval

    vehicle_attribute_list = [
        'base_year_vehicle_id',
        'manufacturer_id',
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
        'base_year_curbweight_lbs',
        'curbweight_lbs',
        'onroad_direct_co2e_grams_per_mile',
        'onroad_direct_kwh_per_mile',
    ]

    rebound_rate_ice = omega_globals.options.vmt_rebound_rate_ice
    rebound_rate_bev = omega_globals.options.vmt_rebound_rate_bev

    safety_effects_dict = dict()
    vehicle_info_dict = dict()

    for calendar_year in calendar_years:
        vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

        calendar_year_vmt_adj = vmt_adjustments.dict[calendar_year]

        calendar_year_safety_dict = dict()
        for vad in vads:
            if vad['registered_count'] >= 1:

                vehicle_safety_dict = dict()

                # need vehicle info once for each vehicle, not every calendar year for each vehicle
                vehicle_id = int(vad['vehicle_id'])

                if vehicle_id not in vehicle_info_dict:
                    vehicle_info_dict[vehicle_id] \
                        = VehicleFinal.get_vehicle_attributes(vehicle_id, vehicle_attribute_list)

                base_year_vehicle_id, mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, size_class, \
                in_use_fuel_id, market_class_id, fueling_class, base_year_powertrain_type, body_style, \
                base_year_curbweight_lbs, curbweight_lbs, \
                onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile \
                    = vehicle_info_dict[vehicle_id]

                # exclude any vehicle_ids that are considered legacy fleet
                if model_year >= calendar_years[0]:
                    age = int(vad['age'])
                    threshold_lbs, change_per_100lbs_below, change_per_100lbs_above = get_safety_values(body_style)
                    fatality_rate_base = get_fatality_rate(model_year, age)

                    onroad_kwh_per_mile = onroad_gallons_per_mile = fuel_cpm = 0

                    rebound_rate = rebound_effect = 0
                    fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})
                    fuel_flag = 0
                    for fuel, fuel_share in fuel_dict.items():

                        retail_price = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel)

                        # calc fuel cost per mile
                        if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                            onroad_kwh_per_mile += onroad_direct_kwh_per_mile
                            fuel_cpm += onroad_kwh_per_mile * retail_price
                            rebound_rate = rebound_rate_bev
                            fuel_flag += 1

                        elif fuel != 'US electricity' and onroad_direct_co2e_grams_per_mile:
                            refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                            co2_emissions_grams_per_unit \
                                = OnroadFuel.get_fuel_attribute(calendar_year, fuel,
                                                                'direct_co2e_grams_per_unit') / refuel_efficiency
                            onroad_gallons_per_mile += onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                            fuel_cpm += onroad_gallons_per_mile * retail_price
                            rebound_rate = rebound_rate_ice
                            fuel_flag += 1

                    # get context fuel cost per mile
                    context_fuel_cpm_dict_key = (int(base_year_vehicle_id), base_year_powertrain_type, int(model_year), age)
                    context_fuel_cpm = context_fuel_cpm_dict[context_fuel_cpm_dict_key]['fuel_cost_per_mile']

                    if fuel_flag == 2:
                        rebound_rate = rebound_rate_ice
                    if context_fuel_cpm > 0:
                        rebound_effect = calc_rebound_effect(context_fuel_cpm, fuel_cpm, rebound_rate)
                    else:
                        rebound_effect = 0

                    vmt_adjusted = vad['vmt'] * calendar_year_vmt_adj
                    vmt_rebound = vmt_adjusted * rebound_effect

                    vmt_adjusted = vmt_adjusted + vmt_rebound
                    annual_vmt_adjusted = vmt_adjusted / vad['registered_count']
                    annual_vmt_rebound = vmt_rebound / vad['registered_count']

                    # if vad['registered_count'] > 0:
                    #     annual_vmt_adjusted = vmt_adjusted / vad['registered_count']
                    #     annual_vmt_rebound = vmt_rebound / vad['registered_count']
                    # else:
                    #     annual_vmt_adjusted = 0
                    #     annual_vmt_rebound = 0

                    if age == 0:
                        odometer_adjusted = annual_vmt_adjusted
                    else:
                        odometer_last_year = safety_effects_dict[(vehicle_id, calendar_year - 1, age - 1)]['odometer']
                        odometer_adjusted = odometer_last_year + annual_vmt_adjusted

                    lbs_changed = calc_lbs_changed(base_year_curbweight_lbs, curbweight_lbs)

                    lbs_changed_below_threshold \
                        = calc_lbs_changed_below_threshold(threshold_lbs, base_year_curbweight_lbs, curbweight_lbs)

                    lbs_changed_above_threshold \
                        = calc_lbs_changed_above_threshold(threshold_lbs, base_year_curbweight_lbs, curbweight_lbs)

                    check = abs(lbs_changed_below_threshold) + abs(lbs_changed_above_threshold) - abs(lbs_changed)

                    rate_change_below = change_per_100lbs_below * (-lbs_changed_below_threshold) / 100
                    rate_change_above = change_per_100lbs_above * (-lbs_changed_above_threshold) / 100

                    fatality_rate_session = fatality_rate_base * (1 + rate_change_below) * (1 + rate_change_above)

                    fatalities_base = fatality_rate_base * vmt_adjusted / 1000000000

                    fatalities_session = fatality_rate_session * vmt_adjusted / 1000000000

                    vehicle_safety_dict.update({
                        'session_name': omega_globals.options.session_name,
                        'vehicle_id': vehicle_id,
                        'base_year_vehicle_id': int(base_year_vehicle_id),
                        'manufacturer_id': mfr_id,
                        'name': name,
                        'calendar_year': calendar_year,
                        'model_year': int(model_year),
                        'age': age,
                        'base_year_reg_class_id': base_year_reg_class_id,
                        'reg_class_id': reg_class_id,
                        'context_size_class': size_class,
                        'in_use_fuel_id': in_use_fuel_id,
                        'market_class_id': market_class_id,
                        'fueling_class': fueling_class,
                        'base_year_powertrain_type': base_year_powertrain_type,
                        'registered_count': vad['registered_count'],
                        'context_vmt_adjustment': calendar_year_vmt_adj,
                        'annual_vmt': annual_vmt_adjusted,
                        'odometer': odometer_adjusted,
                        'vmt': vmt_adjusted,
                        'annual_vmt_rebound': annual_vmt_rebound,
                        'vmt_rebound': vmt_rebound,
                        'body_style': body_style,
                        'change_per_100lbs_below': change_per_100lbs_below,
                        'change_per_100lbs_above': change_per_100lbs_above,
                        'threshold_lbs': threshold_lbs,
                        'base_year_curbweight_lbs': base_year_curbweight_lbs,
                        'curbweight_lbs': curbweight_lbs,
                        'lbs_changed': lbs_changed,
                        'lbs_changed_below_threshold': lbs_changed_below_threshold,
                        'lbs_changed_above_threshold': lbs_changed_above_threshold,
                        'check_for_0': check,
                        'base_fatality_rate': fatality_rate_base,
                        'fatality_rate_change_below_threshold': rate_change_below,
                        'fatality_rate_change_above_threshold': rate_change_above,
                        'session_fatality_rate': fatality_rate_session,
                        'base_fatalities': fatalities_base,
                        'session_fatalities': fatalities_session,
                    }
                    )

                    key = (vehicle_id, calendar_year, age)
                    calendar_year_safety_dict[key] = vehicle_safety_dict

        safety_effects_dict.update(calendar_year_safety_dict)

    return safety_effects_dict


def calc_legacy_fleet_safety_effects(calendar_years, vmt_adjustments):
    """

    Args:
        calendar_years: The years for which safety effects will be calculated.
        vmt_adjustments: object; an object of the AdjustmentsVMT class

    Returns:
        A dictionary of various safety effects, including fatalities.

    Note:
        There is no rebound VMT calculated for the legacy fleet.

    """
    from effects.legacy_fleet import LegacyFleet

    # mfr_id = name = 'legacy_fleet'
    mfr_id = 'legacy_fleet'

    legacy_fleet_safety_effects_dict = dict()
    for key, nested_dict in LegacyFleet._legacy_fleet.items():

        vehicle_id, calendar_year, age = key

        model_year = nested_dict['model_year']
        market_class_id = nested_dict['market_class_id']
        reg_class_id = nested_dict['reg_class_id']
        fuel_id = nested_dict['in_use_fuel_id']
        registered_count = nested_dict['registered_count']
        age = nested_dict['age']
        body_style = nested_dict['body_style']

        name = set_legacy_fleet_name(market_class_id)

        calendar_year_vmt_adj = vmt_adjustments.get_vmt_adjustment(calendar_year)
        vmt_adjusted = nested_dict['vmt'] * calendar_year_vmt_adj
        annual_vmt_adjusted = vmt_adjusted / registered_count
        if nested_dict['calendar_year'] == calendar_years[0]:
            annual_vmt = nested_dict['annual_vmt']
            odometer = nested_dict['odometer']
            odometer_adjusted = odometer - annual_vmt + annual_vmt_adjusted
        else:
            odometer_last_year \
                = legacy_fleet_safety_effects_dict[(vehicle_id, calendar_year - 1, age - 1)]['odometer']
            odometer_adjusted = odometer_last_year + annual_vmt_adjusted

        fueling_class = base_year_powertrain_type = 'ICE'
        if 'BEV' in market_class_id:
            fueling_class = base_year_powertrain_type = 'BEV'

        threshold_lbs, change_per_100lbs_below, change_per_100lbs_above = get_safety_values(body_style)

        vehicle_safety_dict = dict()

        fatality_rate_base = get_fatality_rate(model_year, age)

        fatalities_base = fatality_rate_base * vmt_adjusted / 1000000000

        vehicle_safety_dict.update({
            'session_name': omega_globals.options.session_name,
            'vehicle_id': vehicle_id,
            'base_year_vehicle_id': vehicle_id,
            'manufacturer_id': mfr_id,
            'name': name,
            'calendar_year': int(calendar_year),
            'model_year': int(model_year),
            'age': int(age),
            'base_year_reg_class_id': reg_class_id,
            'reg_class_id': reg_class_id,
            'context_size_class': 'not applicable',
            'in_use_fuel_id': fuel_id,
            'market_class_id': market_class_id,
            'fueling_class': fueling_class,
            'base_year_powertrain_type': base_year_powertrain_type,
            'registered_count': registered_count,
            'context_vmt_adjustment': calendar_year_vmt_adj,
            'annual_vmt': annual_vmt_adjusted,
            'odometer': odometer_adjusted,
            'vmt': vmt_adjusted,
            'annual_vmt_rebound': 0,
            'vmt_rebound': 0,
            'body_style': body_style,
            'change_per_100lbs_below': 0,
            'change_per_100lbs_above': 0,
            'threshold_lbs': threshold_lbs,
            'base_year_curbweight_lbs': nested_dict['curbweight_lbs'],
            'curbweight_lbs': nested_dict['curbweight_lbs'],
            'lbs_changed': 0,
            'lbs_changed_below_threshold': 0,
            'lbs_changed_above_threshold': 0,
            'check_for_0': 0,
            'base_fatality_rate': fatality_rate_base,
            'fatality_rate_change_below_threshold': 0,
            'fatality_rate_change_above_threshold': 0,
            'session_fatality_rate': fatality_rate_base,
            'base_fatalities': fatalities_base,
            'session_fatalities': fatalities_base,
        }
        )

        key = (vehicle_id, calendar_year, age)

        legacy_fleet_safety_effects_dict[key] = vehicle_safety_dict

    return legacy_fleet_safety_effects_dict


def set_legacy_fleet_name(market_class_id):
    """

    Args:
        market_class_id: the legacy fleet market class id

    Returns:
        A name for the vehicle primarily for use in cost_effects, repair cost calculations which looks for 'car' or 'Pickup' in the
        name attribute

    """
    if 'sedan' in market_class_id:
        _name = 'car'
    elif 'pickup' in market_class_id:
        _name = 'Pickup'
    else:
        _name = 'cuv_suv'

    return _name
