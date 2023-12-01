"""

Function to calculate fuel costs per mile in the reference session against which rebound effects can be calculated for
subsequent sessions.

----

**CODE**

"""
from omega_effects.general.general_functions import calc_fuel_cost_per_mile


def calc_context_fuel_cost_per_mile(batch_settings, session_settings):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.

    Returns:
        A dictionary of fuel costs per mile by vehicle_id and age.

    """
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
        '_initial_registered_count',
    ]
    # let cpm refer to cost_per_mile
    context_fuel_cpm_dict = {}
    vehicle_info_dict = {}
    refuel_efficiency_e = 1

    calendar_years = batch_settings.calendar_years

    for calendar_year in calendar_years:

        vads = session_settings.vehicle_annual_data.get_vehicle_annual_data_by_calendar_year(calendar_year)

        # limit to vads having model_year >= analysis_initial_year since only those might have new fuel consumption
        vads = [v for v in vads if (v['calendar_year'] - v['age']) >= batch_settings.analysis_initial_year]

        calendar_year_fuel_cpm_dict = {}
        for v in vads:

            # need vehicle info once for each vehicle_id, not every calendar year for each vehicle_id
            vehicle_id = int(v['vehicle_id'])
            age = int(v['age'])

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

            base_year_vehicle_id, name, model_year, base_year_reg_class_id, reg_class_id, context_size_class, \
                in_use_fuel_id, market_class_id, fueling_class, base_year_powertrain_type, body_style, \
                onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile, registered_count \
                    = vehicle_info_dict[vehicle_id]

            cost_per_mile_group = 'nonBEV'
            if fueling_class == 'BEV':
                cost_per_mile_group = 'BEV'

            key = (cost_per_mile_group, context_size_class, int(model_year), int(age))
            if key not in calendar_year_fuel_cpm_dict:

                fuel_cost_per_mile = calc_fuel_cost_per_mile(
                    batch_settings, calendar_year, onroad_direct_kwh_per_mile, onroad_direct_co2e_grams_per_mile,
                    in_use_fuel_id
                )
                weighted_fuel_cost_per_mile = registered_count * fuel_cost_per_mile

                calendar_year_fuel_cpm_dict[key] = {
                    'session_policy': session_settings.session_policy,
                    'session_name': session_settings.session_name,
                    'calendar_year': int(calendar_year),
                    'model_year': int(model_year),
                    'age': int(age),
                    'cost_per_mile_group': cost_per_mile_group,
                    'context_size_class': context_size_class,
                    'registered_count': registered_count,
                    'fuel_cost_per_mile': weighted_fuel_cost_per_mile,
                }
            else:
                fuel_cost_per_mile = calc_fuel_cost_per_mile(
                    batch_settings, calendar_year, onroad_direct_kwh_per_mile, onroad_direct_co2e_grams_per_mile,
                    in_use_fuel_id
                )
                weighted_fuel_cost_per_mile = calendar_year_fuel_cpm_dict[key]['fuel_cost_per_mile']
                weighted_fuel_cost_per_mile += registered_count * fuel_cost_per_mile
                prior_registered_count = calendar_year_fuel_cpm_dict[key]['registered_count']
                registered_count += prior_registered_count

                calendar_year_fuel_cpm_dict[key] = {
                    'session_policy': session_settings.session_policy,
                    'session_name': session_settings.session_name,
                    'calendar_year': int(calendar_year),
                    'model_year': int(model_year),
                    'age': int(age),
                    'cost_per_mile_group': cost_per_mile_group,
                    'context_size_class': context_size_class,
                    'registered_count': registered_count,
                    'fuel_cost_per_mile': weighted_fuel_cost_per_mile,
                }
        for key in calendar_year_fuel_cpm_dict:
            fuel_cost_per_mile = calendar_year_fuel_cpm_dict[key]['fuel_cost_per_mile']
            registered_count = calendar_year_fuel_cpm_dict[key]['registered_count']
            if registered_count != 0:
                fuel_cost_per_mile = fuel_cost_per_mile / registered_count
            calendar_year_fuel_cpm_dict[key]['fuel_cost_per_mile'] = fuel_cost_per_mile
        context_fuel_cpm_dict.update(calendar_year_fuel_cpm_dict)

    return context_fuel_cpm_dict
