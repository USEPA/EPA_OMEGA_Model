"""

Function to calculate fuel costs per mile in the reference session against which rebound effects can be calculated for
subsequent sessions.

----

**CODE**

"""


def calc_fuel_cost_per_mile(batch_settings, session_settings):
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

            vehicle_fuel_cpm_dict = {}

            # need vehicle info once for each vehicle_id, not every calendar year for each vehicle_id
            vehicle_id = int(v['vehicle_id'])
            age = int(v['age'])

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

            base_year_vehicle_id, name, model_year, base_year_reg_class_id, reg_class_id, context_size_class, \
                in_use_fuel_id, market_class_id, fueling_class, base_year_powertrain_type, body_style, \
                onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile \
                    = vehicle_info_dict[vehicle_id]

            key = (int(base_year_vehicle_id), base_year_powertrain_type, int(model_year), int(age))
            if key not in calendar_year_fuel_cpm_dict:

                onroad_gallons_per_mile = onroad_miles_per_gallon = fuel_cost_per_mile = 0
                retail_price_per_kwh = retail_price_per_gallon = None

                # calc fuel cost per mile
                if onroad_direct_kwh_per_mile:
                    fuel = 'US electricity'
                    retail_price_per_kwh = \
                        batch_settings.context_fuel_prices.get_fuel_prices(
                            batch_settings, calendar_year, 'retail_dollars_per_unit', fuel
                        )
                    refuel_efficiency_e = \
                        batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                    fuel_cost_per_mile += onroad_direct_kwh_per_mile * retail_price_per_kwh / refuel_efficiency_e

                if onroad_direct_co2e_grams_per_mile:
                    fuel_dict = eval(in_use_fuel_id)
                    fuel = [fuel for fuel in fuel_dict.keys()][0]
                    retail_price_per_gallon = \
                        batch_settings.context_fuel_prices.get_fuel_prices(
                            batch_settings, calendar_year, 'retail_dollars_per_unit', fuel
                        )
                    refuel_efficiency_l = \
                        batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                    co2_emissions_grams_per_unit = \
                        batch_settings.onroad_fuels.get_fuel_attribute(
                            calendar_year, fuel, 'direct_co2e_grams_per_unit'
                        ) / refuel_efficiency_l
                    onroad_gallons_per_mile += onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                    onroad_miles_per_gallon = 1 / onroad_gallons_per_mile
                    fuel_cost_per_mile += onroad_gallons_per_mile * retail_price_per_gallon

                vehicle_fuel_cpm_dict.update({
                    'session_policy': session_settings.session_policy,
                    'session_name': session_settings.session_name,
                    'base_year_vehicle_id': int(base_year_vehicle_id),
                    'calendar_year': int(calendar_year),
                    'model_year': int(model_year),
                    'age': int(age),
                    'base_year_reg_class_id': base_year_reg_class_id,
                    'reg_class_id': reg_class_id,
                    'context_size_class': context_size_class,
                    'in_use_fuel_id': in_use_fuel_id,
                    'market_class_id': market_class_id,
                    'fueling_class': fueling_class,
                    'base_year_powertrain_type': base_year_powertrain_type,
                    'body_style': body_style,
                    'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
                    'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                    'evse_kwh_per_mile': onroad_direct_kwh_per_mile / refuel_efficiency_e,
                    'onroad_gallons_per_mile': onroad_gallons_per_mile,
                    'onroad_miles_per_gallon': onroad_miles_per_gallon,
                    'retail_price_per_gallon': retail_price_per_gallon,
                    'retail_price_per_kwh': retail_price_per_kwh,
                    'fuel_cost_per_mile': fuel_cost_per_mile,
                })

                calendar_year_fuel_cpm_dict[key] = vehicle_fuel_cpm_dict

        context_fuel_cpm_dict.update(calendar_year_fuel_cpm_dict)

    return context_fuel_cpm_dict
