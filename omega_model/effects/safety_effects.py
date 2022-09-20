"""

Functions to get vehicle data based on vehicle ID, safety values based on body style and fatality rates based on
calendar year of vehicle age.



----

**CODE**

"""
import pandas as pd

from omega_model import *


def get_safety_values(body_style):
    """
    Get safety values by body style.

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

    Get fatality rate for the given age of vehicle in the given model year.

    Args:
        model_year (int): the model year for which a fatality rate is needed.

    Returns:
        The curb weight threshold and percentage changes in fatality rates for weight changes above and below
        that threshold.

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


def calc_safety_effects(calendar_years):
    """

    Args:
        calendar_years: The years for which safety effects will be calculated.

    Returns:
        A dictionary of various safety effects, including fatalities.

    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal

    vehicle_attribute_list = [
        'manufacturer_id',
        'name',
        'model_year',
        'base_year_reg_class_id',
        'reg_class_id',
        'in_use_fuel_id',
        'fueling_class',
        'base_year_powertrain_type',
        'body_style',
        'base_year_curbweight_lbs',
        'curbweight_lbs',
    ]

    safety_effects_dict = dict()
    vehicle_info_dict = dict()
    for calendar_year in calendar_years:
        vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

        calendar_year_safety_dict = dict()
        for vad in vads:

            vehicle_safety_dict = dict()

            # need vehicle info once for each vehicle, not every calendar year for each vehicle
            if vad['vehicle_id'] not in vehicle_info_dict:
                vehicle_info_dict[vad['vehicle_id']] \
                    = VehicleFinal.get_vehicle_attributes(vad['vehicle_id'], vehicle_attribute_list)

            mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, fueling_class, \
            base_year_powertrain_type, body_style, base_year_curbweight_lbs, curbweight_lbs \
                = vehicle_info_dict[vad['vehicle_id']]

            age = int(vad['age'])
            threshold_lbs, change_per_100lbs_below, change_per_100lbs_above = get_safety_values(body_style)
            fatality_rate_base = get_fatality_rate(model_year, age)

            lbs_changed = calc_lbs_changed(base_year_curbweight_lbs, curbweight_lbs)

            lbs_changed_below_threshold \
                = calc_lbs_changed_below_threshold(threshold_lbs, base_year_curbweight_lbs, curbweight_lbs)

            lbs_changed_above_threshold \
                = calc_lbs_changed_above_threshold(threshold_lbs, base_year_curbweight_lbs, curbweight_lbs)

            check = abs(lbs_changed_below_threshold) + abs(lbs_changed_above_threshold) - abs(lbs_changed)

            rate_change_below = change_per_100lbs_below * (-lbs_changed_below_threshold) / 100
            rate_change_above = change_per_100lbs_above * (-lbs_changed_above_threshold) / 100

            fatality_rate_session = fatality_rate_base * (1 + rate_change_below) * (1 + rate_change_above)

            fatalities_base = fatality_rate_base * vad['vmt'] / 1000000000

            fatalities_session = fatality_rate_session * vad['vmt'] / 1000000000

            vehicle_safety_dict.update({
                'session_name': omega_globals.options.session_name,
                'vehicle_id': int(vad['vehicle_id']),
                'manufacturer_id': mfr_id,
                'name': name,
                'calendar_year': int(calendar_year),
                'model_year': int(model_year),
                'age': int(vad['age']),
                'base_year_reg_class_id': base_year_reg_class_id,
                'reg_class_id': reg_class_id,
                'in_use_fuel_id': in_use_fuel_id,
                'fueling_class': fueling_class,
                'base_year_powertrain_type': base_year_powertrain_type,
                'registered_count': vad['registered_count'],
                'annual_vmt': vad['annual_vmt'],
                'odometer': vad['odometer'],
                'vmt': vad['vmt'],
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

            key = (int(vad['vehicle_id']), int(calendar_year), int(vad['age']))
            calendar_year_safety_dict[key] = vehicle_safety_dict

        safety_effects_dict.update(calendar_year_safety_dict)

    return safety_effects_dict
