"""

Functions to get vehicle data based on vehicle ID, vehicle emission rates for the given vehicle model year and
reg-class, refinery and electricity generating unit emission rates for the given calendar year, and then to
calculate from them the pollutant inventories, including fuel consumed, for each year in the analysis.


----

**CODE**

"""
import pandas as pd
from omega_effects.effects.vehicle_inventory import VehiclePhysicalData, calc_vehicle_inventory


def get_inputs_for_effects(batch_settings, arg=None):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        arg (str): The attribute for which an attribute value is needed.

    Returns:
        A list of necessary input values for use in calculating effects; use index=[0] if passing a single attribute.

    """
    if arg:
        return batch_settings.general_inputs_for_effects.get_value(arg)
    else:
        args = [
            'grams_per_us_ton',
            'grams_per_metric_ton',
            'gal_per_bbl',
            'e0_in_retail_gasoline',
            'e0_energy_density_ratio',
            'diesel_energy_density_ratio',
        ]
        values = []
        for arg in args:
            values.append(batch_settings.general_inputs_for_effects.get_value(arg))

        return values


def calc_physical_effects(batch_settings, session_settings, analysis_fleet_safety):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        analysis_fleet_safety: the analysis fleet safety effects.

    Returns:
        A dictionary of physical effects for the analysis fleet.

    Notes:
        battery_kwh from the vehicle.csv file represents kwh/veh, not kwh/veh * registered_count; as such, that
        attribute_name is changed to battery_kwh_per_veh in the effects calculations meaning that battery_kwh
        becomes the attribute_name that represents kwh/veh * registered_count

    """
    vehicle_attribute_list = [
        'base_year_vehicle_id',
        'manufacturer_id',
        'name',
        'model_year',
        'base_year_reg_class_id',
        'reg_class_id',
        'in_use_fuel_id',
        'market_class_id',
        'fueling_class',
        'base_year_powertrain_type',
        'footprint_ft2',
        'workfactor',
        'target_co2e_grams_per_mile',
        'onroad_direct_co2e_grams_per_mile',
        'onroad_direct_kwh_per_mile',
        'body_style',
        'battery_kwh',
        'curbweight_lbs',
        'gvwr_lbs',
        'onroad_engine_on_distance_frac',
    ]

    (grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, diesel_energy_density_ratio,
    ) = get_inputs_for_effects(batch_settings)

    sourcetype_name = None

    physical_effects_dict = {}
    vehicle_info_dict = {}
    calendar_years = batch_settings.calendar_years
    for calendar_year in calendar_years:

        calendar_year_effects_dict = {}

        adjusted_vads = \
            session_settings.vehicle_annual_data.get_adjusted_vehicle_annual_data_by_calendar_year(calendar_year)

        # this loops thru vehicles this calendar year to calc physical effects for this calendar year
        for v in adjusted_vads:

            vehicle_data = VehiclePhysicalData()

            if v['vehicle_id'] not in vehicle_info_dict:
                vehicle_info_dict[v['vehicle_id']] \
                    = session_settings.vehicles.get_vehicle_attributes(v['vehicle_id'], *vehicle_attribute_list)

            base_year_vehicle_id, manufacturer_id, name, model_year, base_year_reg_class_id, reg_class_id, \
                in_use_fuel_id, market_class_id, fueling_class, base_year_powertrain_type, footprint_ft2, workfactor, \
                target_co2e_grams_per_mile, onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile, body_style, \
                battery_kwh_per_veh, curbweight_lbs, gvwr_lbs, onroad_engine_on_distance_frac = \
                vehicle_info_dict[v['vehicle_id']]

            if target_co2e_grams_per_mile is not None:
                fuel_dict = eval(in_use_fuel_id)
                fuel = [item for item in fuel_dict.keys()][0]

                # for physical effects, we want battery kwh implemented on new vehicles (age=0)
                if v['age'] == 0:
                    battery_kwh = battery_kwh_per_veh * v['registered_count']
                else:
                    battery_kwh = 0

                # establish VMT shares
                vmt_liquid_fuel = 0
                onroad_engine_on_distance_frac = min(onroad_engine_on_distance_frac, 1)
                if fueling_class != 'BEV':
                    vmt_liquid_fuel = v['vmt'] * onroad_engine_on_distance_frac

                vehicle_data.update_value({
                    'session_policy': session_settings.session_policy,
                    'session_name': session_settings.session_name,
                    'grams_per_us_ton': grams_per_us_ton,
                    'grams_per_metric_ton': grams_per_metric_ton,
                    'gal_per_bbl': gal_per_bbl,
                    'e0_share': e0_share,
                    'e0_energy_density_ratio': e0_energy_density_ratio,
                    'diesel_energy_density_ratio': diesel_energy_density_ratio,
                    'vehicle_id': v['vehicle_id'],
                    'base_year_vehicle_id': base_year_vehicle_id,
                    'calendar_year': calendar_year,
                    'model_year': model_year,
                    'age': int(v['age']),
                    'name': name,
                    'registered_count': v['registered_count'],
                    'base_year_reg_class_id': base_year_reg_class_id,
                    'reg_class_id': reg_class_id,
                    'manufacturer_id': manufacturer_id,
                    'in_use_fuel_id': in_use_fuel_id,
                    'market_class_id': market_class_id,
                    'fueling_class': fueling_class,
                    'base_year_powertrain_type': base_year_powertrain_type,
                    'body_style': body_style,
                    'footprint_ft2': footprint_ft2,
                    'workfactor': workfactor,
                    'battery_kwh_per_veh': battery_kwh_per_veh,
                    'battery_kwh': battery_kwh,
                    'curbweight_lbs': curbweight_lbs,
                    'gvwr_lbs': gvwr_lbs,
                    'vmt': v['vmt'],
                    'vmt_liquid_fuel': vmt_liquid_fuel,
                    'annual_vmt': v['annual_vmt'],
                    'odometer': v['odometer'],
                    'context_vmt_adjustment': v['context_vmt_adjustment'],
                    'vmt_rebound': v['vmt_rebound'],
                    'annual_vmt_rebound': v['annual_vmt_rebound'],
                })

                # get safety effects for this vehicle
                vse = analysis_fleet_safety[(v['vehicle_id'], calendar_year)]

                vehicle_data.update_value({
                    'session_fatalities': vse['session_fatalities'],
                    'context_size_class': vse['context_size_class'],
                })

                if base_year_reg_class_id == 'car':
                    sourcetype_name = 'passenger car'
                elif base_year_reg_class_id == 'truck':
                    sourcetype_name = 'passenger truck'
                elif base_year_reg_class_id == 'mediumduty' and 'cuv' in body_style:
                    sourcetype_name = 'passenger truck'  # TODO is this right?
                elif base_year_reg_class_id == 'mediumduty' and 'pickup' in body_style:
                    sourcetype_name = 'light commercial truck'  # TODO is this right?
                else:
                    print('Improper sourcetype_name for vehicle emission rates.')

                veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
                ind_var_value = v['age']
                if veh_rates_by == 'odometer':
                    ind_var_value = v['odometer']

                # calc fuel consumption and update emission rates
                if onroad_direct_kwh_per_mile:
                    refuel_efficiency = \
                        batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, 'US electricity',
                                                                       'refuel_efficiency')
                    fuel_consumption_kwh = v['vmt'] * onroad_direct_kwh_per_mile / refuel_efficiency
                    transmission_efficiency = \
                        batch_settings.onroad_fuels.get_fuel_attribute(
                            calendar_year, 'US electricity', 'transmission_efficiency'
                        )
                    fuel_generation_kwh = fuel_consumption_kwh / transmission_efficiency

                    vehicle_data.update_value({
                        'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                        'evse_kwh_per_mile': onroad_direct_kwh_per_mile / refuel_efficiency,
                        'fuel_consumption_kwh': fuel_consumption_kwh,
                        'fuel_generation_kwh': fuel_generation_kwh,
                    })

                    if fueling_class == 'BEV':
                        pm25_brakewear_rate_e, pm25_tirewear_rate_e = \
                            session_settings.emission_rates_vehicles.get_emission_rate(
                                session_settings, model_year, sourcetype_name, reg_class_id, fuel, ind_var_value
                            )
                        vehicle_data.update_value({
                            'pm25_brakewear_rate_e': pm25_brakewear_rate_e,
                            'pm25_tirewear_rate_e': pm25_tirewear_rate_e,
                        })

                if onroad_direct_co2e_grams_per_mile:
                    co2_emissions_grams_per_unit = \
                        batch_settings.onroad_fuels.get_fuel_attribute(
                            calendar_year, fuel, 'direct_co2e_grams_per_unit'
                        )
                    onroad_gallons_per_mile = onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                    fuel_consumption_gallons = v['vmt'] * onroad_gallons_per_mile
                    onroad_miles_per_gallon = 1 / onroad_gallons_per_mile

                    vehicle_data.update_value({
                        'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
                        'onroad_gallons_per_mile': onroad_gallons_per_mile,
                        'fuel_consumption_gallons': fuel_consumption_gallons,
                        'onroad_miles_per_gallon': onroad_miles_per_gallon,
                    })

                    if 'gasoline' in fuel:
                        pm25_brakewear_rate_l, pm25_tirewear_rate_l, pm25_exh_rate, \
                            nmog_exh_rate, nmog_permeation_rate, nmog_venting_rate, nmog_leaks_rate, \
                            nmog_refuel_disp_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                            sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, \
                            acrolein_exh_rate, benzene_exh_rate, benzene_permeation_rate, \
                            benzene_venting_rate, benzene_leaks_rate, benzene_refuel_disp_rate, \
                            benzene_refuel_spill_rate, ethylbenzene_exh_rate, ethylbenzene_permeation_rate, \
                            ethylbenzene_venting_rate, ethylbenzene_leaks_rate, \
                            ethylbenzene_refuel_disp_rate, ethylbenzene_refuel_spill_rate, \
                            formaldehyde_exh_rate, naphthalene_exh_rate, \
                            butadiene13_exh_rate, pah15_exh_rate = \
                            session_settings.emission_rates_vehicles.get_emission_rate(
                                session_settings, model_year, sourcetype_name, reg_class_id, fuel, ind_var_value
                            )
                        energy_density_ratio, pure_share = e0_energy_density_ratio, e0_share

                        vehicle_data.update_value({
                            'pm25_brakewear_rate_l': pm25_brakewear_rate_l,
                            'pm25_tirewear_rate_l': pm25_tirewear_rate_l,
                            'pm25_exh_rate': pm25_exh_rate,

                            'nmog_exh_rate': nmog_exh_rate,
                            'nmog_permeation_rate': nmog_permeation_rate,
                            'nmog_venting_rate': nmog_venting_rate,
                            'nmog_leaks_rate': nmog_leaks_rate,
                            'nmog_refuel_disp_rate': nmog_refuel_disp_rate,
                            'nmog_refuel_spill_rate': nmog_refuel_spill_rate,

                            'co_exh_rate': co_exh_rate,
                            'nox_exh_rate': nox_exh_rate,
                            'sox_exh_rate': sox_exh_rate,
                            'ch4_exh_rate': ch4_exh_rate,
                            'n2o_exh_rate': n2o_exh_rate,

                            'acetaldehyde_exh_rate': acetaldehyde_exh_rate,
                            'acrolein_exh_rate': acrolein_exh_rate,

                            'benzene_exh_rate': benzene_exh_rate,
                            'benzene_permeation_rate': benzene_permeation_rate,
                            'benzene_venting_rate': benzene_venting_rate,
                            'benzene_leaks_rate': benzene_leaks_rate,
                            'benzene_refuel_disp_rate': benzene_refuel_disp_rate,
                            'benzene_refuel_spill_rate': benzene_refuel_spill_rate,

                            'ethylbenzene_exh_rate': ethylbenzene_exh_rate,
                            'ethylbenzene_permeation_rate': ethylbenzene_permeation_rate,
                            'ethylbenzene_venting_rate': ethylbenzene_venting_rate,
                            'ethylbenzene_leaks_rate': ethylbenzene_leaks_rate,
                            'ethylbenzene_refuel_disp_rate': ethylbenzene_refuel_disp_rate,
                            'ethylbenzene_refuel_spill_rate': ethylbenzene_refuel_spill_rate,

                            'formaldehyde_exh_rate': formaldehyde_exh_rate,
                            'naphthalene_exh_rate': naphthalene_exh_rate,
                            'butadiene13_exh_rate': butadiene13_exh_rate,
                            'pah15_exh_rate': pah15_exh_rate,

                            'energy_density_ratio': energy_density_ratio,
                            'pure_share': pure_share,
                        })

                    elif 'diesel' in fuel:
                        pm25_brakewear_rate_l, pm25_tirewear_rate_l, pm25_exh_rate, \
                            nmog_exh_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                            sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, \
                            acrolein_exh_rate, benzene_exh_rate, benzene_refuel_spill_rate, \
                            ethylbenzene_exh_rate, ethylbenzene_refuel_spill_rate, \
                            formaldehyde_exh_rate, naphthalene_exh_rate, naphthalene_refuel_spill_rate, \
                            butadiene13_exh_rate, pah15_exh_rate = \
                            session_settings.emission_rates_vehicles.get_emission_rate(
                                session_settings, model_year, sourcetype_name, reg_class_id, fuel, ind_var_value
                            )
                        energy_density_ratio, pure_share = diesel_energy_density_ratio, 1

                        vehicle_data.update_value({
                            'pm25_brakewear_rate_l': pm25_brakewear_rate_l,
                            'pm25_tirewear_rate_l': pm25_tirewear_rate_l,
                            'pm25_exh_rate': pm25_exh_rate,

                            'nmog_exh_rate': nmog_exh_rate,
                            'nmog_refuel_spill_rate': nmog_refuel_spill_rate,

                            'co_exh_rate': co_exh_rate,
                            'nox_exh_rate': nox_exh_rate,
                            'sox_exh_rate': sox_exh_rate,
                            'ch4_exh_rate': ch4_exh_rate,
                            'n2o_exh_rate': n2o_exh_rate,

                            'acetaldehyde_exh_rate': acetaldehyde_exh_rate,
                            'acrolein_exh_rate': acrolein_exh_rate,

                            'benzene_exh_rate': benzene_exh_rate,
                            'benzene_refuel_spill_rate': benzene_refuel_spill_rate,

                            'ethylbenzene_exh_rate': ethylbenzene_exh_rate,
                            'ethylbenzene_refuel_spill_rate': ethylbenzene_refuel_spill_rate,

                            'formaldehyde_exh_rate': formaldehyde_exh_rate,
                            'naphthalene_exh_rate': naphthalene_exh_rate,
                            'naphthalene_refuel_spill_rate': naphthalene_refuel_spill_rate,
                            'butadiene13_exh_rate': butadiene13_exh_rate,
                            'pah15_exh_rate': pah15_exh_rate,

                            'energy_density_ratio': energy_density_ratio,
                            'pure_share': pure_share,
                        })
                    else:
                        pass  # add additional liquid fuels (E85) if necessary

                key = (int(v['vehicle_id']), int(v['calendar_year']))
                calendar_year_effects_dict[key] = calc_vehicle_inventory(vehicle_data)

        physical_effects_dict.update(calendar_year_effects_dict)

    return physical_effects_dict


def calc_legacy_fleet_physical_effects(batch_settings, session_settings, legacy_fleet_safety):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        legacy_fleet_safety (dict): the legacy fleet safety effects.

    Returns:
        A dictionary of legacy fleet physical effects.

    Note:
        This function must not be called until AFTER calc_physical_effects so that the EGU rates will have been
        generated using the energy consumption there. This means that legacy fleet electricity consumption is not
        included when calculating the EGU rates used in the analysis. The legacy fleet electricity consumption is
        small and gets smaller with each future year making this a minor, if not acceptably negligible, impact.

    """
    (grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, diesel_energy_density_ratio,
    ) = get_inputs_for_effects(batch_settings)

    sourcetype_name = None

    physical_effects = {}
    for v in batch_settings.legacy_fleet.adjusted_legacy_fleet.values():

        vehicle_data = VehiclePhysicalData()

        model_year = v['calendar_year'] - v['age']

        # establish VMT shares
        vmt_liquid_fuel = v['vmt']
        if 'electricity' in v['in_use_fuel_id']:
            vmt_liquid_fuel = 0

        vehicle_data.update_value({
            'session_policy': session_settings.session_policy,
            'session_name': session_settings.session_name,
            'grams_per_us_ton': grams_per_us_ton,
            'grams_per_metric_ton': grams_per_metric_ton,
            'gal_per_bbl': gal_per_bbl,
            'e0_share': e0_share,
            'e0_energy_density_ratio': e0_energy_density_ratio,
            'diesel_energy_density_ratio': diesel_energy_density_ratio,
            'vehicle_id': v['vehicle_id'],
            'base_year_vehicle_id': v['vehicle_id'],
            'calendar_year': v['calendar_year'],
            'model_year': model_year,
            'age': v['age'],
            'vmt': v['vmt'],
            'vmt_liquid_fuel': vmt_liquid_fuel,
            'annual_vmt': v['annual_vmt'],
            'odometer': v['odometer'],
            'context_vmt_adjustment': v['context_vmt_adjustment'],
            'body_style': v['body_style'],
            'registered_count': v['registered_count'],
            'reg_class_id': v['reg_class_id'],
            'base_year_reg_class_id': v['reg_class_id'],
            'market_class_id': v['market_class_id'],
            'in_use_fuel_id': v['in_use_fuel_id'],
            'miles_per_gallon': v['miles_per_gallon'],
            'kwh_per_mile': v['kwh_per_mile'],
        })

        onroad_miles_per_gallon = v['miles_per_gallon'] * 0.8
        try:
            onroad_direct_co2e_grams_per_mile = 8887 / onroad_miles_per_gallon
            onroad_gallons_per_mile = 1 / onroad_miles_per_gallon
        except ZeroDivisionError:
            onroad_direct_co2e_grams_per_mile = 0
            onroad_gallons_per_mile = 0
        onroad_direct_kwh_per_mile = v['kwh_per_mile'] / 0.7
        vehicle_data.update_value({
            'onroad_miles_per_gallon': onroad_miles_per_gallon,
            'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
            'onroad_gallons_per_mile': onroad_gallons_per_mile,
            'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
        })

        # get appropriate vehicle safety effects object
        vse = legacy_fleet_safety[(v['vehicle_id'], v['calendar_year'])]
        vehicle_data.update_value({
            'session_fatalities': vse['session_fatalities'],
            'vmt_rebound': vse['vmt_rebound'],
            'annual_vmt_rebound': vse['annual_vmt_rebound'],
            'context_size_class': vse['context_size_class'],
            'manufacturer_id': vse['manufacturer_id'],
            'name': vse['name'],
            'fueling_class': vse['fueling_class'],
            'base_year_powertrain_type': vse['base_year_powertrain_type'],
        })

        if v['reg_class_id'] == 'car':
            sourcetype_name = 'passenger car'
        elif v['reg_class_id'] == 'truck':
            sourcetype_name = 'passenger truck'
        elif v['reg_class_id'] == 'mediumduty' and 'cuv' in v['body_style']:
            sourcetype_name = 'passenger truck'  # TODO is this right?
        elif v['reg_class_id'] == 'mediumduty' and 'pickup' in v['body_style']:
            sourcetype_name = 'light commercial truck'  # TODO is this right?
        else:
            print('Improper sourcetype_name for vehicle emission rates.')

        veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
        ind_var_value = pd.to_numeric(v['age'])
        if veh_rates_by == 'odometer':
            ind_var_value = pd.to_numeric(v['odometer'])

        fuel_dict = eval(v['in_use_fuel_id'])
        fuel = [item for item in fuel_dict.keys()][0]
        if onroad_direct_kwh_per_mile:
            refuel_efficiency = \
                batch_settings.onroad_fuels.get_fuel_attribute(v['calendar_year'], 'US electricity',
                                                               'refuel_efficiency')
            fuel_consumption_kwh = v['vmt'] * onroad_direct_kwh_per_mile / refuel_efficiency
            transmission_efficiency = \
                batch_settings.onroad_fuels.get_fuel_attribute(
                    v['calendar_year'], 'US electricity', 'transmission_efficiency'
                )
            fuel_generation_kwh = fuel_consumption_kwh / transmission_efficiency

            vehicle_data.update_value({
                'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                'evse_kwh_per_mile': onroad_direct_kwh_per_mile / refuel_efficiency,
                'fuel_consumption_kwh': fuel_consumption_kwh,
                'fuel_generation_kwh': fuel_generation_kwh,
            })

            if vse['fueling_class'] == 'BEV':
                pm25_brakewear_rate_e, pm25_tirewear_rate_e = \
                    session_settings.emission_rates_vehicles.get_emission_rate(
                        session_settings, model_year, sourcetype_name, v['reg_class_id'], fuel, ind_var_value
                    )
                vehicle_data.update_value({
                    'pm25_brakewear_rate_e': pm25_brakewear_rate_e,
                    'pm25_tirewear_rate_e': pm25_tirewear_rate_e,
                })

        if onroad_direct_co2e_grams_per_mile:
            fuel_consumption_gallons = v['vmt'] * onroad_gallons_per_mile
            onroad_miles_per_gallon = 1 / onroad_gallons_per_mile

            vehicle_data.update_value({
                'fuel_consumption_gallons': fuel_consumption_gallons,
                'onroad_miles_per_gallon': onroad_miles_per_gallon,
            })

            if 'gasoline' in fuel:
                pm25_brakewear_rate_l, pm25_tirewear_rate_l, pm25_exh_rate, \
                    nmog_exh_rate, nmog_permeation_rate, nmog_venting_rate, nmog_leaks_rate, \
                    nmog_refuel_disp_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                    sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, acrolein_exh_rate, \
                    benzene_exh_rate, benzene_permeation_rate, benzene_venting_rate, benzene_leaks_rate, \
                    benzene_refuel_disp_rate, benzene_refuel_spill_rate, \
                    ethylbenzene_exh_rate, ethylbenzene_permeation_rate, ethylbenzene_venting_rate, \
                    ethylbenzene_leaks_rate, ethylbenzene_refuel_disp_rate, ethylbenzene_refuel_spill_rate, \
                    formaldehyde_exh_rate, naphthalene_exh_rate, \
                    butadiene13_exh_rate, pah15_exh_rate = \
                    session_settings.emission_rates_vehicles.get_emission_rate(
                        session_settings, model_year, sourcetype_name, v['reg_class_id'], fuel, ind_var_value
                    )

                energy_density_ratio, pure_share = e0_energy_density_ratio, e0_share

                vehicle_data.update_value({
                    'pm25_brakewear_rate_l': pm25_brakewear_rate_l,
                    'pm25_tirewear_rate_l': pm25_tirewear_rate_l,
                    'pm25_exh_rate': pm25_exh_rate,

                    'nmog_exh_rate': nmog_exh_rate,
                    'nmog_permeation_rate': nmog_permeation_rate,
                    'nmog_venting_rate': nmog_venting_rate,
                    'nmog_leaks_rate': nmog_leaks_rate,
                    'nmog_refuel_disp_rate': nmog_refuel_disp_rate,
                    'nmog_refuel_spill_rate': nmog_refuel_spill_rate,

                    'co_exh_rate': co_exh_rate,
                    'nox_exh_rate': nox_exh_rate,
                    'sox_exh_rate': sox_exh_rate,
                    'ch4_exh_rate': ch4_exh_rate,
                    'n2o_exh_rate': n2o_exh_rate,

                    'acetaldehyde_exh_rate': acetaldehyde_exh_rate,
                    'acrolein_exh_rate': acrolein_exh_rate,

                    'benzene_exh_rate': benzene_exh_rate,
                    'benzene_permeation_rate': benzene_permeation_rate,
                    'benzene_venting_rate': benzene_venting_rate,
                    'benzene_leaks_rate': benzene_leaks_rate,
                    'benzene_refuel_disp_rate': benzene_refuel_disp_rate,
                    'benzene_refuel_spill_rate': benzene_refuel_spill_rate,

                    'ethylbenzene_exh_rate': ethylbenzene_exh_rate,
                    'ethylbenzene_permeation_rate': ethylbenzene_permeation_rate,
                    'ethylbenzene_venting_rate': ethylbenzene_venting_rate,
                    'ethylbenzene_leaks_rate': ethylbenzene_leaks_rate,
                    'ethylbenzene_refuel_disp_rate': ethylbenzene_refuel_disp_rate,
                    'ethylbenzene_refuel_spill_rate': ethylbenzene_refuel_spill_rate,

                    'formaldehyde_exh_rate': formaldehyde_exh_rate,
                    'naphthalene_exh_rate': naphthalene_exh_rate,
                    'butadiene13_exh_rate': butadiene13_exh_rate,
                    'pah15_exh_rate': pah15_exh_rate,

                    'energy_density_ratio': energy_density_ratio,
                    'pure_share': pure_share,
                })
            elif 'diesel' in fuel:
                pm25_brakewear_rate_l, pm25_tirewear_rate_l, pm25_exh_rate, \
                    nmog_exh_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                    sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, acrolein_exh_rate, \
                    benzene_exh_rate, benzene_refuel_spill_rate, \
                    ethylbenzene_exh_rate, ethylbenzene_refuel_spill_rate, \
                    formaldehyde_exh_rate, naphthalene_exh_rate, naphthalene_refuel_spill_rate, \
                    butadiene13_exh_rate, pah15_exh_rate = session_settings.emission_rates_vehicles.get_emission_rate(
                    session_settings, model_year, sourcetype_name, v['reg_class_id'], fuel, ind_var_value
                )

                energy_density_ratio, pure_share = diesel_energy_density_ratio, 1

                vehicle_data.update_value({
                    'pm25_brakewear_rate_l': pm25_brakewear_rate_l,
                    'pm25_tirewear_rate_l': pm25_tirewear_rate_l,
                    'pm25_exh_rate': pm25_exh_rate,

                    'nmog_exh_rate': nmog_exh_rate,
                    'nmog_refuel_spill_rate': nmog_refuel_spill_rate,

                    'co_exh_rate': co_exh_rate,
                    'nox_exh_rate': nox_exh_rate,
                    'sox_exh_rate': sox_exh_rate,
                    'ch4_exh_rate': ch4_exh_rate,
                    'n2o_exh_rate': n2o_exh_rate,

                    'acetaldehyde_exh_rate': acetaldehyde_exh_rate,
                    'acrolein_exh_rate': acrolein_exh_rate,

                    'benzene_exh_rate': benzene_exh_rate,
                    'benzene_refuel_spill_rate': benzene_refuel_spill_rate,

                    'ethylbenzene_exh_rate': ethylbenzene_exh_rate,
                    'ethylbenzene_refuel_spill_rate': ethylbenzene_refuel_spill_rate,

                    'formaldehyde_exh_rate': formaldehyde_exh_rate,
                    'naphthalene_exh_rate': naphthalene_exh_rate,
                    'naphthalene_refuel_spill_rate': naphthalene_refuel_spill_rate,
                    'butadiene13_exh_rate': butadiene13_exh_rate,
                    'pah15_exh_rate': pah15_exh_rate,

                    'energy_density_ratio': energy_density_ratio,
                    'pure_share': pure_share,
                })

        key = (int(v['vehicle_id']), int(v['calendar_year']))
        physical_effects[key] = calc_vehicle_inventory(vehicle_data)

    return physical_effects


def calc_annual_physical_effects(batch_settings, input_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        input_df: DataFrame of physical effects by vehicle.

    Returns:
        A DataFrame of physical effects by calendar year.

    Notes:
        battery_kwh here is kwh/veh * registered_count (not kwh/veh)

    """
    grams_per_metric_ton = get_inputs_for_effects(batch_settings, arg='grams_per_metric_ton')

    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = [
        'count', 'consumption', 'refined', 'generation', 'barrels', 'tons', 'fatalit', 'battery_kwh'
    ]
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # note that the groupby_cols must include fuel_id to calculate benefits since vehicle emission rates differ by fuel
    groupby_cols = [
        'session_policy', 'session_name', 'calendar_year', 'reg_class_id', 'in_use_fuel_id', 'fueling_class'
    ]
    return_df = input_df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(return_df.columns.get_loc('fuel_generation_kwh') + 1,
                     'onroad_gallons_per_mile',
                     return_df['fuel_consumption_gallons'] / return_df['vmt'])

    return_df.insert(return_df.columns.get_loc('fuel_generation_kwh') + 1,
                     'evse_kwh_per_mile',
                     return_df['fuel_consumption_kwh'] / return_df['vmt'])

    cyears = pd.DataFrame(return_df['calendar_year'])
    cyears.insert(0, 'refuel_efficiency', 0)
    for cyear in cyears['calendar_year'].unique():
        refuel_efficiency = \
            batch_settings.onroad_fuels.get_fuel_attribute(cyear, 'US electricity', 'refuel_efficiency')
        cyears.loc[cyears['calendar_year'] == cyear, 'refuel_efficiency'] = refuel_efficiency

    return_df.insert(return_df.columns.get_loc('fuel_generation_kwh') + 1,
                     'onroad_direct_kwh_per_mile',
                     return_df['fuel_consumption_kwh'] * cyears['refuel_efficiency'] / return_df['vmt'])

    return_df.insert(return_df.columns.get_loc('fuel_generation_kwh') + 1,
                     'onroad_direct_co2e_grams_per_mile',
                     return_df['co2_vehicle_metrictons'] * grams_per_metric_ton / return_df['vmt'])

    return_df['battery_kwh_per_veh'] = return_df['battery_kwh'] / return_df['registered_count']

    return return_df


def calc_period_consumer_physical_view(input_df, periods):
    """

    Args:
        input_df: DataFrame of physical effects by vehicle in each analysis year.
        periods (int): the number of periods (years) to include in the consumer view, set via the
        general_inputs_for_effects_file.

    Returns:
        A DataFrame of physical effects by model year of available lifetime, body style and fuel type.

    """
    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col)
                  and '_vmt' not in col
                  and '_per' not in col]
    additional_attributes = ['count', 'consumption_gallons', 'consumption_kWh', 'barrels', '_total_']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # eliminate legacy_fleet and ages not desired for consumer view
    # if periods = 8, then max_age should be 7 since year 1 is age=0
    max_age = periods - 1
    df = input_df.loc[(input_df['manufacturer_id'] != 'legacy_fleet') & (input_df['age'] <= max_age), :]

    # now create a sales column for use in some of the 'per vehicle' calcs below
    df.insert(df.columns.get_loc('registered_count'), 'sales', df['registered_count'])
    df.loc[df['age'] != 0, 'sales'] = 0

    # groupby model year, body_style and fuel
    if 'medium' in [item for item in input_df['reg_class_id']]:
        groupby_cols = ['session_policy', 'session_name', 'model_year', 'body_style', 'in_use_fuel_id']
    else:
        groupby_cols = ['session_policy', 'session_name', 'model_year', 'body_style', 'fueling_class']

    attributes.append('sales')
    return_df = df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(return_df.columns.get_loc('model_year') + 1, 'periods', 0)
    return_df.insert(return_df.columns.get_loc('model_year') + 1, 'series', 'PeriodValue')

    # calc periods
    model_years = df['model_year'].unique()
    for model_year in model_years:
        max_age = max(df.loc[df['model_year'] == model_year, 'age'])
        return_df.loc[return_df['model_year'] == model_year, 'periods'] = max_age + 1

    # now calc total values per vehicle over the period and average annual values per vehicle over the period
    for attribute in attributes:
        if attribute in ['sales', 'registered_count']:
            pass
        else:
            s = pd.Series((return_df[attribute] / return_df['registered_count']) * return_df['periods'],
                          name=f'{attribute}_per_period')
            return_df = pd.concat([return_df, s], axis=1)

            s = pd.Series(return_df[attribute] / return_df['registered_count'], name=f'{attribute}_per_year_in_period')
            return_df = pd.concat([return_df, s], axis=1)

    # and values per mile
    for attribute in attributes:
        s = pd.Series(return_df[attribute] / return_df['vmt'], name=f'{attribute}_per_mile_in_period')
        return_df = pd.concat([return_df, s], axis=1)

    return return_df
