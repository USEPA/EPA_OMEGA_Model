"""

Functions to get vehicle data based on vehicle ID, safety values based on body style and fatality rates based on
calendar year and vehicle age, and to calculate fatalities.

----

**CODE**

"""
import pandas as pd


def get_safety_values(session_settings, body_style):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        body_style (str): the OMEGA body style (e.g., sedan, cuv_suv, pickup)

    Returns:
        The curb weight threshold and percentage changes in fatality rates for weight changes above and below
        that threshold.

    """
    return session_settings.safety_values.get_safety_values(body_style)


def get_fatality_rate(batch_settings, model_year, age):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        model_year (int): the model year for which a fatality rate is needed.
        age (int): vehicle age in years

    Returns:
        The average fatality rate for vehicles of a specific model year and age.

    """
    return batch_settings.fatality_rates.get_fatality_rate(model_year, age)


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


def calc_safety_effects(batch_settings, session_settings):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.

    Returns:
        A dictionary of various safety effects, including fatalities.

    """
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
        'footprint_ft2',
        'workfactor',
        'body_style',
        'base_year_curbweight_lbs',
        'curbweight_lbs',
        ]

    safety_effects_dict = {}
    vehicle_info_dict = {}
    calendar_years = batch_settings.calendar_years
    for calendar_year in calendar_years:

        adjusted_vads = \
            session_settings.vehicle_annual_data.get_adjusted_vehicle_annual_data_by_calendar_year(calendar_year)

        # limit to adjusted_vads having model_year >= analysis_initial_year since only those might have new fuel
        # consumption
        adjusted_vads = \
            [v for v in adjusted_vads if (v['calendar_year'] - v['age']) >= batch_settings.analysis_initial_year]

        calendar_year_safety_dict = {}
        for v in adjusted_vads:

            vehicle_safety_dict = {}

            # need vehicle info once for each vehicle, not every calendar year for each vehicle
            if v['vehicle_id'] not in vehicle_info_dict:
                vehicle_info_dict[v['vehicle_id']] \
                    = session_settings.vehicles.get_vehicle_attributes(v['vehicle_id'], *vehicle_attribute_list)

            base_year_vehicle_id, manufacturer_id, name, model_year, base_year_reg_class_id, reg_class_id, size_class, \
                in_use_fuel_id, market_class_id, fueling_class, base_year_powertrain_type, footprint, workfactor, \
                body_style, base_year_curbweight_lbs, curbweight_lbs = \
                vehicle_info_dict[v['vehicle_id']]

            threshold_lbs, change_per_100lbs_below, change_per_100lbs_above \
                = get_safety_values(batch_settings, body_style)
            fatality_rate_base = get_fatality_rate(batch_settings, model_year, v['age'])

            lbs_changed = calc_lbs_changed(base_year_curbweight_lbs, curbweight_lbs)

            lbs_changed_below_threshold \
                = calc_lbs_changed_below_threshold(threshold_lbs, base_year_curbweight_lbs, curbweight_lbs)

            lbs_changed_above_threshold \
                = calc_lbs_changed_above_threshold(threshold_lbs, base_year_curbweight_lbs, curbweight_lbs)

            check = abs(lbs_changed_below_threshold) + abs(lbs_changed_above_threshold) - abs(lbs_changed)

            rate_change_below = change_per_100lbs_below * (-lbs_changed_below_threshold) / 100
            rate_change_above = change_per_100lbs_above * (-lbs_changed_above_threshold) / 100

            fatality_rate_session = fatality_rate_base * (1 + rate_change_below) * (1 + rate_change_above)

            fatalities_base = fatality_rate_base * v['vmt'] / 1000000000

            fatalities_session = fatality_rate_session * v['vmt'] / 1000000000

            vehicle_safety_dict.update({
                'session_policy': session_settings.session_policy,
                'session_name': session_settings.session_name,
                'vehicle_id': v['vehicle_id'],
                'base_year_vehicle_id': base_year_vehicle_id,
                'manufacturer_id': manufacturer_id,
                'name': name,
                'calendar_year': calendar_year,
                'model_year': int(model_year),
                'age': int(v['age']),
                'base_year_reg_class_id': base_year_reg_class_id,
                'reg_class_id': reg_class_id,
                'context_size_class': size_class,
                'in_use_fuel_id': in_use_fuel_id,
                'market_class_id': market_class_id,
                'fueling_class': fueling_class,
                'base_year_powertrain_type': base_year_powertrain_type,
                'registered_count': v['registered_count'],
                'context_vmt_adjustment': v['context_vmt_adjustment'],
                'annual_vmt': v['annual_vmt'],
                'odometer': v['odometer'],
                'vmt': v['vmt'],
                'annual_vmt_rebound': v['annual_vmt_rebound'],
                'vmt_rebound': v['vmt_rebound'],
                'body_style': body_style,
                'footprint_ft2': footprint,
                'workfactor': workfactor,
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
            })
            calendar_year_safety_dict[v['vehicle_id'], int(calendar_year)] = vehicle_safety_dict

        safety_effects_dict.update(calendar_year_safety_dict)

    return safety_effects_dict


def calc_legacy_fleet_safety_effects(batch_settings, session_settings):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.

    Returns:
        A dictionary of various legacy fleet safety effects, including fatalities.

    Note:
        There is no rebound VMT calculated for the legacy fleet.

    """
    manufacturer_id = 'legacy_fleet'

    legacy_fleet_safety_effects_dict = {}
    for v in batch_settings.legacy_fleet.adjusted_legacy_fleet.values():

        model_year = v['calendar_year'] - v['age']
        reg_class_id = v['reg_class_id']
        in_use_fuel_id = v['in_use_fuel_id']
        registered_count = v['registered_count']

        fueling_class = base_year_powertrain_type = 'ICE'
        if 'BEV' in v['market_class_id']:
            fueling_class = base_year_powertrain_type = 'BEV'
        elif 'PHEV' in v['market_class_id']:
            fueling_class = base_year_powertrain_type = 'PHEV'

        name = batch_settings.legacy_fleet.set_legacy_fleet_name(v['vehicle_id'], v['market_class_id'], fueling_class)

        threshold_lbs, change_per_100lbs_below, change_per_100lbs_above = \
            get_safety_values(batch_settings, v['body_style'])

        vehicle_safety_dict = {}

        fatality_rate_base = get_fatality_rate(batch_settings, model_year, v['age'])

        fatalities_base = fatality_rate_base * v['vmt'] / 1000000000

        vehicle_safety_dict.update({
            'session_policy': session_settings.session_policy,
            'session_name': session_settings.session_name,
            'vehicle_id': v['vehicle_id'],
            'base_year_vehicle_id': v['vehicle_number'],
            'manufacturer_id': manufacturer_id,
            'name': name,
            'calendar_year': int(v['calendar_year']),
            'model_year': int(model_year),
            'age': int(v['age']),
            'base_year_reg_class_id': reg_class_id,
            'reg_class_id': reg_class_id,
            'context_size_class': 'not applicable',
            'in_use_fuel_id': in_use_fuel_id,
            'market_class_id': v['market_class_id'],
            'fueling_class': fueling_class,
            'base_year_powertrain_type': base_year_powertrain_type,
            'registered_count': registered_count,
            'context_vmt_adjustment': v['context_vmt_adjustment'],
            'annual_vmt': v['annual_vmt'],
            'odometer': v['odometer'],
            'vmt': v['vmt'],
            'annual_vmt_rebound': 0,
            'vmt_rebound': 0,
            'body_style': v['body_style'],
            'footprint_ft2': 0,
            'workfactor': 0,
            'change_per_100lbs_below': change_per_100lbs_below,
            'change_per_100lbs_above': change_per_100lbs_above,
            'threshold_lbs': threshold_lbs,
            'base_year_curbweight_lbs': v['curbweight_lbs'],
            'curbweight_lbs': v['curbweight_lbs'],
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
        key = (v['vehicle_id'], int(v['calendar_year']))
        legacy_fleet_safety_effects_dict[key] = vehicle_safety_dict

    return legacy_fleet_safety_effects_dict


def calc_annual_avg_safety_effects(input_df):
    """

    Args:
        input_df: DataFrame of physical effects by vehicle.

    Returns:
        A DataFrame of physical effects by calendar year, regclass, fueling class, etc.

    """
    attributes = [col for col in input_df.columns
                  if ('vmt' in col or 'vmt_' in col)
                  and '_vmt' not in col]
    attribute_keys_for_weighting = ['lbs']
    attributes_to_weight = []
    for attribute in attribute_keys_for_weighting:
        for col in input_df:
            if attribute in col:
                attributes_to_weight.append(col)

    # weight appropriate columns by registered_count to work toward weighted averages
    temp_df = pd.DataFrame()
    wtd_attributes = []
    for attribute in attributes_to_weight:
        wtd_attributes.append(f'wtd_avg_{attribute}')
        s = pd.Series(input_df['registered_count'] * input_df[attribute], name=f'wtd_avg_{attribute}')
        temp_df = pd.concat([temp_df, s], axis=1)

    mediumduty = None
    if 'medium' in [item for item in input_df['reg_class_id']]:  # TODO is this what is needed?
        mediumduty = 1

    cols = ['session_policy', 'session_name', 'calendar_year', 'reg_class_id', 'body_style', 'in_use_fuel_id', 'fueling_class',
            'registered_count', 'base_fatalities', 'session_fatalities'
            ]
    for attribute in attributes:
        cols.append(attribute)
    df = input_df[cols]
    df = pd.concat([df, temp_df], axis=1)

    # groupby calendar year, regclass, body style and fuel
    if mediumduty:
        groupby_cols = ['session_policy', 'session_name', 'calendar_year', 'reg_class_id', 'body_style', 'in_use_fuel_id']
    else:
        groupby_cols = ['session_policy', 'session_name', 'calendar_year', 'reg_class_id', 'body_style', 'fueling_class']

    return_df = df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    for attribute in wtd_attributes:
        return_df[attribute] = return_df[attribute] / return_df['registered_count']

    return return_df


def calc_annual_avg_safety_effects_by_body_style(input_df):
    """

    Args:
        input_df: DataFrame of physical effects by vehicle.

    Returns:
        A DataFrame of physical effects by calendar year and body style.

    """
    attributes = [col for col in input_df.columns
                  if ('vmt' in col or 'vmt_' in col)
                  and '_vmt' not in col]
    attribute_keys_for_weighting = ['lbs']
    attributes_to_weight = []
    for attribute in attribute_keys_for_weighting:
        for col in input_df:
            if attribute in col:
                attributes_to_weight.append(col)

    # weight appropriate columns by registered_count to work toward weighted averages
    temp_df = pd.DataFrame()
    wtd_attributes = []
    for attribute in attributes_to_weight:
        wtd_attributes.append(f'wtd_avg_{attribute}')
        s = pd.Series(input_df['registered_count'] * input_df[attribute], name=f'wtd_avg_{attribute}')
        temp_df = pd.concat([temp_df, s], axis=1)

    cols = ['session_policy', 'session_name', 'calendar_year', 'body_style',
            'registered_count', 'base_fatalities', 'session_fatalities'
            ]
    for attribute in attributes:
        cols.append(attribute)
    df = input_df[cols]
    df = pd.concat([df, temp_df], axis=1)

    # groupby calendar year, body style
    groupby_cols = ['session_policy', 'session_name', 'calendar_year', 'body_style']
    return_df = df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    for attribute in wtd_attributes:
        return_df[attribute] = return_df[attribute] / return_df['registered_count']

    return return_df
