"""

Functions to get vehicle data based on vehicle ID, vehicle emission rates for the given vehicle model year and
reg-class, refinery and electricity generating unit emission rates for the given calendar year, and then to
calculate from them the pollutant inventories, including fuel consumed, for each year in the analysis.


----

**CODE**

"""
import pandas as pd


def get_vehicle_emission_rate(session_settings, model_year, sourcetype_name, reg_class_id, fuel, ind_var_value):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        model_year: The model year of the specific vehicle.
        sourcetype_name: The MOVES sourcetype name (e.g., 'passenger car', 'passenger truck', 'light commercial truck')
        reg_class_id: The regulatory class ID of the vehicle.
        fuel: The fuel ID (i.e., pump gasoline, pump diesel)
        ind_var_value: The independent variable value, e.g., age or odometer

    Returns:
        A list of emission rates for the given model year vehicle in a given calendar year.

    """
    if 'gasoline' in fuel:
        rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile',
            'pm25_exhaust_grams_per_mile',
            'nmog_exhaust_grams_per_mile',
            'nmog_evap_permeation_grams_per_gallon',
            'nmog_evap_fuel_vapor_venting_grams_per_gallon',
            'nmog_evap_fuel_leaks_grams_per_gallon',
            'nmog_refueling_displacement_grams_per_gallon',
            'nmog_refueling_spillage_grams_per_gallon',
            'co_exhaust_grams_per_mile',
            'nox_exhaust_grams_per_mile',
            'sox_exhaust_grams_per_gallon',
            'ch4_exhaust_grams_per_mile',
            'n2o_exhaust_grams_per_mile',
            'acetaldehyde_exhaust_grams_per_mile',
            'acrolein_exhaust_grams_per_mile',
            'benzene_exhaust_grams_per_mile',
            'benzene_evap_permeation_grams_per_gallon',
            'benzene_evap_fuel_vapor_venting_grams_per_gallon',
            'benzene_evap_fuel_leaks_grams_per_gallon',
            'benzene_refueling_displacement_grams_per_gallon',
            'benzene_refueling_spillage_grams_per_gallon',
            'ethylbenzene_exhaust_grams_per_mile',
            'ethylbenzene_evap_fuel_vapor_venting_grams_per_gallon',
            'ethylbenzene_evap_fuel_leaks_grams_per_gallon',
            'ethylbenzene_evap_permeation_grams_per_gallon',
            'ethylbenzene_refueling_displacement_grams_per_gallon',
            'ethylbenzene_refueling_spillage_grams_per_gallon',
            'formaldehyde_exhaust_grams_per_mile',
            'naphthalene_exhaust_grams_per_mile',
            '13_butadiene_exhaust_grams_per_mile',
            '15pah_exhaust_grams_per_mile',
        ]
    elif 'diesel' in fuel:
        rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile',
            'pm25_exhaust_grams_per_mile',
            'nmog_exhaust_grams_per_mile',
            'nmog_refueling_spillage_grams_per_gallon',
            'co_exhaust_grams_per_mile',
            'nox_exhaust_grams_per_mile',
            'sox_exhaust_grams_per_gallon',
            'ch4_exhaust_grams_per_mile',
            'n2o_exhaust_grams_per_mile',
            'acetaldehyde_exhaust_grams_per_mile',
            'acrolein_exhaust_grams_per_mile',
            'benzene_exhaust_grams_per_mile',
            'benzene_refueling_spillage_grams_per_gallon',
            'ethylbenzene_exhaust_grams_per_mile',
            'ethylbenzene_refueling_spillage_grams_per_gallon',
            'formaldehyde_exhaust_grams_per_mile',
            'naphthalene_exhaust_grams_per_mile',
            'naphthalene_refueling_spillage_grams_per_gallon',
            '13_butadiene_exhaust_grams_per_mile',
            '15pah_exhaust_grams_per_mile',
        ]
    elif 'electric' in fuel:
        rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile'
        ]
    else:
        rate_names = []

    rates = session_settings.emission_rates_vehicles.get_emission_rate(model_year, sourcetype_name, reg_class_id, fuel,
                                                                       ind_var_value, *rate_names)

    return rates


def get_egu_emission_rate(session_settings, calendar_year, kwh_consumption, kwh_generation):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        calendar_year: The calendar year for which egu emission rates are needed.
        kwh_consumption: The energy consumed by the fleet measured at the wall or charger outlet
        kwh_generation: The energy generated to satisfy the kwh_consumption value (not used)

    Returns:
        A list of EGU emission rates for the given calendar year.

    """
    kwh_session = kwh_consumption

    rate_names = (
        'voc_grams_per_kwh',
        'co_grams_per_kwh',
        'nox_grams_per_kwh',
        'pm25_grams_per_kwh',
        'sox_grams_per_kwh',
        'co2_grams_per_kwh',
        'ch4_grams_per_kwh',
        'n2o_grams_per_kwh',
        'hcl_grams_per_kwh',
        'hg_grams_per_kwh',
    )

    return session_settings.emission_rates_egu.get_emission_rate(calendar_year, kwh_session, rate_names)


def get_refinery_emission_rate(session_settings, calendar_year):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        calendar_year: The calendar year for which a refinery emission factors are needed.

    Returns:
        A list of refinery emission rates as specified in the emission_rates list for the given calendar year.

    """
    emission_rates = (
        'voc_grams_per_gallon',
        'nox_grams_per_gallon',
        'pm25_grams_per_gallon',
        'sox_grams_per_gallon',
    )

    return session_settings.emission_rates_refinery.get_emission_rate(calendar_year, emission_rates)


def get_refinery_ef(session_settings, calendar_year, fuel):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        calendar_year: The calendar year for which a refinery emission factors are needed.
        fuel: The fuel ID for which refinery emission factors are needed (i.e., pump_gasoline, pump_diesel).

    Returns:
        A list of refinery emission factors as specified in the emission_factors list for the given calendar year
        and liquid fuel.

    """
    emission_factors = (
        'voc_grams_per_gallon',
        'co_grams_per_gallon',
        'nox_grams_per_gallon',
        'pm25_grams_per_gallon',
        'sox_grams_per_gallon',
        # 'benzene_grams_per_gallon',
        # 'butadiene13_grams_per_gallon',
        # 'formaldehyde_grams_per_gallon',
        # 'acetaldehyde_grams_per_gallon',
        # 'acrolein_grams_per_gallon',
        'co2_grams_per_gallon',
        'ch4_grams_per_gallon',
        'n2o_grams_per_gallon',
    )

    return session_settings.emission_factors_refinery.get_emission_factors(calendar_year, fuel, emission_factors)


def get_energysecurity_cf(batch_settings, calendar_year):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year: The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    Note:
        In the physical_effects module, oil impacts are calculated, not cost impacts; therefore the "cost factor"
        returned is the oil import reduction as a percentage of oil demand reduction.

    """
    cost_factors = ('oil_import_reduction_as_percent_of_total_oil_demand_reduction',
                    )

    return batch_settings.energy_security_cost_factors.get_cost_factors(calendar_year, cost_factors)


def get_inputs_for_effects(batch_settings, arg=None):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        arg: The attribute for which an attribute value is needed.

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
            'fuel_reduction_leading_to_reduced_domestic_refining',
            # 'gallons_of_gasoline_us_annual',
            # 'bbl_oil_us_annual',
            # 'kwh_us_annual',
            # 'year_for_compares',
        ]
        values = list()
        for arg in args:
            values.append(batch_settings.general_inputs_for_effects.get_value(arg))

        return values


def calc_physical_effects(batch_settings, session_settings, safety_effects_dict):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        safety_effects_dict: The dictionary generated via the safety_effects module.

    Returns:
        A dictionary of physical effects where keys are a (vehicle_id, calendar_year, age) tuple and values are a
        dictionary of attribute_name and attribute_value pairs of physical effects.

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
    ]

    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, \
        diesel_energy_density_ratio, fuel_reduction_leading_to_reduced_domestic_refining \
        = get_inputs_for_effects(batch_settings)
    # gallons_of_gasoline_us_annual, bbl_oil_us_annual, kwh_us_annual, year_for_compares = \
    #  get_inputs_for_effects(*input_attributes_list)
    # year_for_compares = int(year_for_compares)

    physical_effects_dict = dict()
    vehicle_info_dict = dict()
    calendar_years = batch_settings.calendar_years
    for calendar_year in calendar_years:

        vads = session_settings.vehicle_annual_data.get_adjusted_vehicle_annual_data_by_calendar_year(calendar_year)

        # UPDATE physical effects data
        calendar_year_effects_dict = dict()

        # first a loop to determine kwh demand for this calendar year
        fuel_consumption_kWh_annual = fuel_generation_kWh_annual = 0
        for vad in vads:
            # if vad['registered_count'] >= 1:

            # need vehicle info once for each vehicle, not every calendar year for each vehicle
            vehicle_id = int(vad['vehicle_id'])
            age = int(vad['age'])

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

            base_year_vehicle_id, mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, \
                market_class_id, fueling_class, base_year_powertrain_type, footprint, workfactor, \
                target_co2e_grams_per_mile, onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile, \
                body_style, battery_kwh \
                        = vehicle_info_dict[vehicle_id]

            fuel_dict = eval(in_use_fuel_id)
            for fuel, fuel_share in fuel_dict.items():
                if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                    # refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                    transmission_efficiency \
                        = batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')

                    safety_effects_key = (vehicle_id, calendar_year, age)
                    vmt = safety_effects_dict[safety_effects_key]['vmt']
                    vmt_electricity = vmt * fuel_share
                    fuel_consumption_kWh_annual += vmt_electricity * onroad_direct_kwh_per_mile
                    fuel_generation_kWh_annual = fuel_consumption_kWh_annual / transmission_efficiency

        # upstream EGU emission rates for this calendar year to apply to electric fuel operation
        voc_egu_rate, co_egu_rate, nox_egu_rate, pm25_egu_rate, sox_egu_rate, \
            co2_egu_rate, ch4_egu_rate, n2o_egu_rate, hcl_egu_rate, hg_egu_rate \
            = get_egu_emission_rate(session_settings, calendar_year, fuel_consumption_kWh_annual,
                                    fuel_generation_kWh_annual)

        for vad in vads:
            # if vad['registered_count'] >= 1 and (vad['calendar_year'] - vad['age']) >= calendar_years[0]:

            vehicle_id = int(vad['vehicle_id'])
            age = int(vad['age'])

            base_year_vehicle_id, mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, \
                market_class_id, fueling_class, base_year_powertrain_type, footprint, workfactor, \
                target_co2e_grams_per_mile, onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile, body_style, \
                battery_kwh \
                    = vehicle_info_dict[vehicle_id]

            # for physical effects, we want battery kwh implemented on new vehicles (age=0)
            if age == 0:
                battery_kwh = battery_kwh * vad['registered_count']
            else:
                battery_kwh = 0

            if model_year >= calendar_years[0]:

                # get vmt and session fatalities from safety_effects_dict
                safety_effects_key = (vehicle_id, calendar_year, age)
                safety = safety_effects_dict[safety_effects_key]
                session_fatalities, vmt, annual_vmt, odometer, calendar_year_vmt_adj, vmt_rebound, annual_vmt_rebound, \
                    size_class \
                    = safety['session_fatalities'], \
                    safety['vmt'], \
                    safety['annual_vmt'], \
                    safety['odometer'], \
                    safety['context_vmt_adjustment'], \
                    safety['vmt_rebound'], \
                    safety['annual_vmt_rebound'], \
                    safety['context_size_class']

                if base_year_reg_class_id == 'car':
                    sourcetype_name = 'passenger car'
                elif base_year_reg_class_id == 'truck':
                    sourcetype_name = 'passenger truck'
                elif base_year_reg_class_id == 'mediumduty' and 'cuv' in body_style:
                    sourcetype_name = 'passenger truck'
                elif base_year_reg_class_id == 'mediumduty' and 'pickup' in body_style:
                    sourcetype_name = 'light commercial truck'
                else:
                    print('Improper sourcetype_name for vehicle emission rates.')

                # need vehicle effects for each vehicle and for each calendar year since they change year-over-year
                vehicle_effects_dict = dict()
                flag = None
                if target_co2e_grams_per_mile is not None:

                    liquid_fuel = None
                    electric_fuel = None

                    vmt_liquid_fuel = vmt_electricity \
                        = onroad_gallons_per_mile = fuel_consumption_gallons = onroad_miles_per_gallon \
                        = fuel_generation_kWh = fuel_consumption_kWh = 0

                    nmog_exh_ustons = nmog_evap_ustons = nmog_veh_ustons = 0
                    co_exh_ustons = co_veh_ustons = 0
                    nox_exh_ustons = nox_veh_ustons = 0
                    sox_exh_ustons = sox_veh_ustons = 0
                    pm25_exh_ustons = pm25_brakewear_ustons = pm25_tirewear_ustons = pm25_veh_ustons = 0
                    acetaldehyde_exh_ustons = acetaldehyde_veh_ustons = 0
                    acrolein_exh_ustons = acrolein_veh_ustons = 0
                    benzene_exh_ustons = benzene_evap_ustons = benzene_veh_ustons = 0
                    ethylbenzene_exh_ustons = ethylbenzene_evap_ustons = ethylbenzene_veh_ustons = 0
                    naphthalene_exh_ustons = naphthalene_evap_ustons = naphthalene_veh_ustons = 0
                    formaldehyde_exh_ustons = formaldehyde_veh_ustons = 0
                    butadiene13_exh_ustons = butadiene13_veh_ustons = 0
                    pah15_exh_ustons = pah15_veh_ustons = 0
                    co2_exh_metrictons = co2_veh_metrictons = 0
                    ch4_exh_metrictons = ch4_veh_metrictons = 0
                    n2o_exh_metrictons = n2o_veh_metrictons = 0

                    co2_upstream_metrictons = ch4_upstream_metrictons = n2o_upstream_metrictons = 0
                    voc_upstream_ustons = co_upstream_ustons = nox_upstream_ustons = pm25_upstream_ustons = 0
                    sox_upstream_ustons = hcl_upstream_ustons = hg_upstream_ustons = 0

                    pm25_brakewear_rate_l = pm25_brakewear_rate_e = pm25_tirewear_rate_l = pm25_tirewear_rate_e = 0
                    pm25_exh_rate = co_exh_rate = nox_exh_rate = sox_exh_rate = ch4_exh_rate = n2o_exh_rate = 0
                    nmog_exh_rate = nmog_permeation_rate = nmog_venting_rate = 0
                    nmog_leaks_rate = nmog_refuel_disp_rate = nmog_refuel_spill_rate = 0
                    acetaldehyde_exh_rate = acrolein_exh_rate = 0
                    benzene_exh_rate = benzene_permeation_rate = benzene_venting_rate = 0
                    benzene_leaks_rate = benzene_refuel_disp_rate = benzene_refuel_spill_rate = 0
                    ethylbenzene_exh_rate = ethylbenzene_permeation_rate = ethylbenzene_venting_rate = 0
                    ethylbenzene_leaks_rate = ethylbenzene_refuel_disp_rate = ethylbenzene_refuel_spill_rate = 0
                    formaldehyde_exh_rate = naphthalene_exh_rate = naphthalene_refuel_spill_rate = 0
                    butadiene13_exh_rate = pah15_exh_rate = 0

                    voc_ref_rate = co_ref_rate = nox_ref_rate = pm25_ref_rate = sox_ref_rate = 0
                    co2_ref_rate = ch4_ref_rate = n2o_ref_rate = 0
                    # benzene_ref = butadiene13_ref = formaldehyde_ref = acetaldehyde_ref = acrolein_ref = 0

                    pure_share = energy_density_ratio = 0

                    veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
                    ind_var_value = pd.to_numeric(vad['age'])
                    if veh_rates_by == 'odometer':
                        ind_var_value = pd.to_numeric(vad['odometer'])

                    fuel_dict = eval(in_use_fuel_id)
                    for fuel, fuel_share in fuel_dict.items():
                        refuel_efficiency \
                            = batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel,
                                                                             'refuel_efficiency')
                        transmission_efficiency \
                            = batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel,
                                                                             'transmission_efficiency')
                        co2_emissions_grams_per_unit \
                            = batch_settings.onroad_fuels.get_fuel_attribute(
                                calendar_year, fuel, 'direct_co2e_grams_per_unit') / refuel_efficiency

                        # calc fuel consumption and get emission rates
                        if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                            electric_fuel = fuel
                            vmt_electricity = vmt * fuel_share
                            fuel_consumption_kWh += vmt_electricity * onroad_direct_kwh_per_mile
                            fuel_generation_kWh = fuel_consumption_kWh / transmission_efficiency

                            # vehicle emission rates; PHEVs use the ICE vehicle rates
                            if fueling_class == 'BEV':
                                pm25_brakewear_rate_e, pm25_tirewear_rate_e \
                                    = get_vehicle_emission_rate(
                                        session_settings, model_year, sourcetype_name, base_year_reg_class_id,
                                        fuel, ind_var_value)

                        elif fuel != 'US electricity' and onroad_direct_co2e_grams_per_mile:
                            liquid_fuel = fuel
                            vmt_liquid_fuel = vmt * fuel_share
                            onroad_gallons_per_mile += onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                            fuel_consumption_gallons = \
                                vmt_liquid_fuel * onroad_gallons_per_mile / transmission_efficiency
                            onroad_miles_per_gallon = 1 / onroad_gallons_per_mile

                            if fuel == 'pump gasoline':
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
                                    butadiene13_exh_rate, pah15_exh_rate \
                                    = get_vehicle_emission_rate(
                                        session_settings, model_year, sourcetype_name, base_year_reg_class_id, fuel,
                                        ind_var_value)

                                energy_density_ratio, pure_share = e0_energy_density_ratio, e0_share

                            elif fuel == 'pump diesel':
                                pm25_brakewear_rate_l, pm25_tirewear_rate_l, pm25_exh_rate, \
                                    nmog_exh_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                                    sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, \
                                    acrolein_exh_rate, benzene_exh_rate, benzene_refuel_spill_rate, \
                                    ethylbenzene_exh_rate, ethylbenzene_refuel_spill_rate, \
                                    formaldehyde_exh_rate, naphthalene_exh_rate, naphthalene_refuel_spill_rate, \
                                    butadiene13_exh_rate, pah15_exh_rate \
                                    = get_vehicle_emission_rate(
                                        session_settings, model_year, sourcetype_name, base_year_reg_class_id, fuel,
                                        ind_var_value)

                                energy_density_ratio, pure_share = diesel_energy_density_ratio, 1
                            else:
                                pass  # add additional liquid fuels (E85) if necessary

                            # upstream refinery emission factors for liquid fuel operation
                            if session_settings.emission_factors_refinery:
                                voc_ref_rate, co_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, \
                                    co2_ref_rate, ch4_ref_rate, n2o_ref_rate \
                                        = get_refinery_ef(session_settings, calendar_year, liquid_fuel)
                            else:
                                voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate = \
                                    get_refinery_emission_rate(session_settings, calendar_year)

                            # calc exhaust and evaporative emissions for liquid fuel operation
                            factor = vmt_liquid_fuel / grams_per_us_ton
                            pm25_exh_ustons += pm25_exh_rate * factor
                            nmog_exh_ustons += nmog_exh_rate * factor
                            co_exh_ustons += co_exh_rate * factor
                            nox_exh_ustons += nox_exh_rate * factor
                            acetaldehyde_exh_ustons += acetaldehyde_exh_rate * factor
                            acrolein_exh_ustons += acrolein_exh_rate * factor
                            benzene_exh_ustons += benzene_exh_rate * factor
                            ethylbenzene_exh_ustons += ethylbenzene_exh_rate * factor
                            formaldehyde_exh_ustons += formaldehyde_exh_rate * factor
                            naphthalene_exh_ustons += naphthalene_exh_rate * factor
                            butadiene13_exh_ustons += butadiene13_exh_rate * factor
                            pah15_exh_ustons += pah15_exh_rate * factor

                            factor = fuel_consumption_gallons / grams_per_us_ton
                            sox_exh_ustons += sox_exh_rate * factor
                            nmog_evap_ustons += sum([nmog_permeation_rate,
                                                     nmog_venting_rate,
                                                     nmog_leaks_rate,
                                                     nmog_refuel_disp_rate,
                                                     nmog_refuel_spill_rate]) * factor
                            benzene_evap_ustons += sum([benzene_permeation_rate,
                                                        benzene_venting_rate,
                                                        benzene_leaks_rate,
                                                        benzene_refuel_disp_rate,
                                                        benzene_refuel_spill_rate]) * factor
                            ethylbenzene_evap_ustons += sum([ethylbenzene_permeation_rate,
                                                             ethylbenzene_venting_rate,
                                                             ethylbenzene_leaks_rate,
                                                             ethylbenzene_refuel_disp_rate,
                                                             ethylbenzene_refuel_spill_rate]) * factor
                            naphthalene_evap_ustons += naphthalene_refuel_spill_rate * factor

                            factor = vmt_liquid_fuel / grams_per_metric_ton
                            ch4_veh_metrictons += ch4_exh_rate * factor
                            n2o_veh_metrictons += n2o_exh_rate * factor
                            co2_veh_metrictons += onroad_direct_co2e_grams_per_mile * factor

                            # calc vehicle inventories as exhaust plus evap (where applicable)
                            nmog_veh_ustons = nmog_exh_ustons + nmog_evap_ustons
                            co_veh_ustons = co_exh_ustons
                            nox_veh_ustons = nox_exh_ustons
                            sox_veh_ustons = sox_exh_ustons
                            acetaldehyde_veh_ustons = acetaldehyde_exh_ustons
                            acrolein_veh_ustons = acrolein_exh_ustons
                            benzene_veh_ustons = benzene_exh_ustons + benzene_evap_ustons
                            ethylbenzene_veh_ustons = ethylbenzene_exh_ustons + ethylbenzene_evap_ustons
                            formaldehyde_veh_ustons = formaldehyde_exh_ustons
                            naphthalene_veh_ustons = naphthalene_exh_ustons + naphthalene_evap_ustons
                            butadiene13_veh_ustons = butadiene13_exh_ustons
                            pah15_veh_ustons = pah15_exh_ustons

                    # calc vehicle pm25 emissions
                    pm25_brakewear_ustons += \
                        (vmt_liquid_fuel * pm25_brakewear_rate_l + vmt_electricity * pm25_brakewear_rate_e) \
                        / grams_per_us_ton
                    pm25_tirewear_ustons += \
                        (vmt_liquid_fuel * pm25_tirewear_rate_l + vmt_electricity * pm25_tirewear_rate_e) \
                        / grams_per_us_ton

                    pm25_veh_ustons = pm25_exh_ustons + pm25_brakewear_ustons + pm25_tirewear_ustons

                    # calc upstream emissions for both liquid and electric fuel operation
                    kwhs, gallons = fuel_generation_kWh, fuel_consumption_gallons
                    ref_factor = fuel_reduction_leading_to_reduced_domestic_refining
                    voc_upstream_ustons = \
                        (kwhs * voc_egu_rate + gallons * voc_ref_rate * ref_factor) / grams_per_us_ton
                    co_upstream_ustons = \
                        (kwhs * co_egu_rate + gallons * co_ref_rate * ref_factor) / grams_per_us_ton
                    nox_upstream_ustons = \
                        (kwhs * nox_egu_rate + gallons * nox_ref_rate * ref_factor) / grams_per_us_ton
                    pm25_upstream_ustons = \
                        (kwhs * pm25_egu_rate + gallons * pm25_ref_rate * ref_factor) / grams_per_us_ton
                    sox_upstream_ustons = \
                        (kwhs * sox_egu_rate + gallons * sox_ref_rate * ref_factor) / grams_per_us_ton
                    hcl_upstream_ustons = (kwhs * hcl_egu_rate) / grams_per_us_ton
                    hg_upstream_ustons = (kwhs * hg_egu_rate) / grams_per_us_ton
                    # benzene_upstream_ustons = (kwhs * benzene_ps + gallons * benzene_ref) / grams_per_us_ton
                    # butadiene13_upstream_ustons = (kwhs * butadiene13_ps + gallons * butadiene13_ref) / grams_per_us_ton
                    # formaldehyde_upstream_ustons = (kwhs * formaldehyde_ps + gallons * formaldehyde_ref) / grams_per_us_ton
                    # acetaldehyde_upstream_ustons = (kwhs * acetaldehyde_ps + gallons * acetaldehyde_ref) / grams_per_us_ton
                    # acrolein_upstream_ustons = (kwhs * acrolein_ps + gallons * acrolein_ref) / grams_per_us_ton

                    co2_upstream_metrictons = \
                        (kwhs * co2_egu_rate + gallons * co2_ref_rate * ref_factor) / grams_per_metric_ton
                    ch4_upstream_metrictons = \
                        (kwhs * ch4_egu_rate + gallons * ch4_ref_rate * ref_factor) / grams_per_metric_ton
                    n2o_upstream_metrictons = \
                        (kwhs * n2o_egu_rate + gallons * n2o_ref_rate * ref_factor) / grams_per_metric_ton

                    # sum vehicle and upstream into totals
                    voc_total_ustons = voc_upstream_ustons  # + voc_tailpipe_ustons
                    nmog_total_ustons = nmog_veh_ustons  # + nmog_upstream_ustons
                    co_total_ustons = co_veh_ustons + co_upstream_ustons
                    nox_total_ustons = nox_veh_ustons + nox_upstream_ustons
                    pm25_total_ustons = pm25_veh_ustons + pm25_upstream_ustons
                    sox_total_ustons = sox_veh_ustons + sox_upstream_ustons
                    acetaldehyde_total_ustons = acetaldehyde_veh_ustons  # + acetaldehyde_upstream_ustons
                    acrolein_total_ustons = acrolein_veh_ustons  # + acrolein_upstream_ustons
                    benzene_total_ustons = benzene_veh_ustons  # + benzene_upstream_ustons
                    ethylbenzene_total_ustons = ethylbenzene_veh_ustons  # + ethylbenzene_upstream_ustons
                    formaldehyde_total_ustons = formaldehyde_veh_ustons  # + formaldehyde_upstream_ustons
                    naphthalene_total_ustons = naphthalene_veh_ustons  # + naphlathene_upstream_ustons
                    butadiene13_total_ustons = butadiene13_veh_ustons  # + butadiene13_upstream_ustons
                    pah15_total_ustons = pah15_veh_ustons  # + pah15_upstream_ustons
                    co2_total_metrictons = co2_veh_metrictons + co2_upstream_metrictons
                    ch4_total_metrictons = ch4_veh_metrictons + ch4_upstream_metrictons
                    n2o_total_metrictons = n2o_veh_metrictons + n2o_upstream_metrictons

                    # calc energy security related attributes and comparisons to year_for_compares
                    oil_bbl = fuel_consumption_gallons * pure_share * energy_density_ratio / gal_per_bbl
                    imported_oil_bbl = oil_bbl * get_energysecurity_cf(batch_settings, calendar_year)
                    imported_oil_bbl_per_day = imported_oil_bbl / 365
                    # share_of_us_annual_gasoline = fuel_consumption_gallons / gallons_of_gasoline_us_annual
                    # share_of_us_annual_oil = oil_bbl / bbl_oil_us_annual

                    # calc kwh and comparisons to year_for_compares
                    # share_of_us_annual_kwh = fuel_generation_kWh / kwh_us_annual

                    if vmt_liquid_fuel > 0 or vmt_electricity > 0:
                        flag = 1

                    vehicle_effects_dict.update({
                        'session_policy': session_settings.session_policy,
                        'session_name': session_settings.session_name,
                        'vehicle_id': vehicle_id,
                        'base_year_vehicle_id': int(base_year_vehicle_id),
                        'manufacturer_id': mfr_id,
                        'name': name,
                        'calendar_year': int(calendar_year),
                        'model_year': calendar_year - age,
                        'age': age,
                        'base_year_reg_class_id': base_year_reg_class_id,
                        'reg_class_id': reg_class_id,
                        'context_size_class': size_class,
                        'in_use_fuel_id': in_use_fuel_id,
                        'market_class_id': market_class_id,
                        'fueling_class': fueling_class,
                        'base_year_powertrain_type': base_year_powertrain_type,
                        'body_style': body_style,
                        'footprint_ft2': footprint,
                        'workfactor': workfactor,
                        'registered_count': vad['registered_count'],
                        'context_vmt_adjustment': calendar_year_vmt_adj,
                        'annual_vmt': annual_vmt,
                        'odometer': odometer,
                        'vmt': vmt,
                        'annual_vmt_rebound': annual_vmt_rebound,
                        'vmt_rebound': vmt_rebound,
                        'vmt_liquid_fuel': vmt_liquid_fuel,
                        'vmt_electricity': vmt_electricity,
                        'battery_kwh': battery_kwh,
                        'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
                        'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                        'onroad_gallons_per_mile': onroad_gallons_per_mile,
                        'onroad_miles_per_gallon': onroad_miles_per_gallon,
                        'fuel_consumption_gallons': fuel_consumption_gallons,
                        'fuel_consumption_kWh': fuel_consumption_kWh,
                        'fuel_generation_kWh': fuel_generation_kWh,

                        # f'share_of_{year_for_compares}_US_gasoline': share_of_us_annual_gasoline,
                        # f'share_of_{year_for_compares}_US_kWh': share_of_us_annual_kwh,
                        'barrels_of_oil': oil_bbl,
                        # f'share_of_{year_for_compares}_US_oil': share_of_us_annual_oil,
                        'barrels_of_imported_oil': imported_oil_bbl,
                        'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,

                        'session_fatalities': session_fatalities,

                        'nmog_exhaust_ustons': nmog_exh_ustons,
                        'nmog_evaporative_ustons': nmog_evap_ustons,
                        'nmog_vehicle_ustons': nmog_veh_ustons,
                        'co_vehicle_ustons': co_veh_ustons,
                        'nox_vehicle_ustons': nox_veh_ustons,
                        'pm25_exhaust_ustons': pm25_exh_ustons,
                        'pm25_brakewear_ustons': pm25_brakewear_ustons,
                        'pm25_tirewear_ustons': pm25_tirewear_ustons,
                        'pm25_vehicle_ustons': pm25_veh_ustons,
                        'sox_vehicle_ustons': sox_veh_ustons,
                        'acetaldehyde_vehicle_ustons': acetaldehyde_veh_ustons,
                        'acrolein_vehicle_ustons': acrolein_veh_ustons,
                        'benzene_exhaust_ustons': benzene_exh_ustons,
                        'benzene_evaporative_ustons': benzene_evap_ustons,
                        'benzene_vehicle_ustons': benzene_veh_ustons,
                        'ethylbenzene_exhaust_ustons': ethylbenzene_exh_ustons,
                        'ethylbenzene_evaporative_ustons': ethylbenzene_evap_ustons,
                        'ethylbenzene_vehicle_ustons': ethylbenzene_veh_ustons,
                        'formaldehyde_vehicle_ustons': formaldehyde_veh_ustons,
                        'naphthalene_exhaust_ustons': naphthalene_exh_ustons,
                        'naphthalene_evaporative_ustons': naphthalene_evap_ustons,
                        'naphthalene_vehicle_ustons': naphthalene_veh_ustons,
                        '13_butadiene_vehicle_ustons': butadiene13_veh_ustons,
                        '15pah_vehicle_ustons': pah15_veh_ustons,

                        'ch4_vehicle_metrictons': ch4_veh_metrictons,
                        'n2o_vehicle_metrictons': n2o_veh_metrictons,
                        'co2_vehicle_metrictons': co2_veh_metrictons,

                        'voc_upstream_ustons': voc_upstream_ustons,
                        'co_upstream_ustons': co_upstream_ustons,
                        'nox_upstream_ustons': nox_upstream_ustons,
                        'pm25_upstream_ustons': pm25_upstream_ustons,
                        'sox_upstream_ustons': sox_upstream_ustons,
                        'hcl_upstream_ustons': hcl_upstream_ustons,
                        'hg_upstream_ustons': hg_upstream_ustons,

                        'ch4_upstream_metrictons': ch4_upstream_metrictons,
                        'n2o_upstream_metrictons': n2o_upstream_metrictons,
                        'co2_upstream_metrictons': co2_upstream_metrictons,

                        'nmog_and_voc_total_ustons': nmog_total_ustons + voc_total_ustons,
                        'co_total_ustons': co_total_ustons,
                        'nox_total_ustons': nox_total_ustons,
                        'pm25_total_ustons': pm25_total_ustons,
                        'sox_total_ustons': sox_total_ustons,
                        'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
                        'acrolein_total_ustons': acrolein_total_ustons,
                        'benzene_total_ustons': benzene_total_ustons,
                        'ethylbenzene_total_ustons': ethylbenzene_total_ustons,
                        'formaldehyde_total_ustons': formaldehyde_total_ustons,
                        'naphthalene_total_ustons': naphthalene_total_ustons,
                        '13_butadiene_total_ustons': butadiene13_total_ustons,
                        '15pah_total_ustons': pah15_total_ustons,
                        'co2_total_metrictons': co2_total_metrictons,
                        'ch4_total_metrictons': ch4_total_metrictons,
                        'n2o_total_metrictons': n2o_total_metrictons,
                    }
                    )
                if flag:
                    key = (vehicle_id, calendar_year, age)
                    calendar_year_effects_dict[key] = vehicle_effects_dict

        physical_effects_dict.update(calendar_year_effects_dict)

    return physical_effects_dict


def calc_annual_physical_effects(batch_settings, input_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        input_df: DataFrame of physical effects by vehicle.

    Returns:
        A DataFrame of physical effects by calendar year.

    """
    grams_per_metric_ton = get_inputs_for_effects(batch_settings, arg='grams_per_metric_ton')
    calendar_years = batch_settings.calendar_years

    d = dict()
    num = 0
    for calendar_year in calendar_years:
        d[num] = {
            'calendar_year': calendar_year,
            'transmission_efficiency': batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, 'US electricity',
                                                                                      'transmission_efficiency')
        }
        num += 1

    # elec_trans_efficiency = pd.DataFrame(d).transpose()
    elec_trans_efficiency = pd.DataFrame.from_dict(d, orient='index')

    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['count', 'consumption', 'generation', 'barrels', 'tons', 'fatalit', 'battery_kwh']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # groupby calendar year, regclass and fuel
    groupby_cols = ['session_policy', 'session_name', 'calendar_year', 'reg_class_id', 'in_use_fuel_id']
    return_df = input_df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    return_df = return_df.merge(elec_trans_efficiency, on='calendar_year', how='left')

    return_df.insert(return_df.columns.get_loc('in_use_fuel_id') + 1,
                     'fueling_class',
                     '')
    return_df.loc[return_df['in_use_fuel_id'] == "{'US electricity':1.0}", 'fueling_class'] = 'BEV'
    return_df.loc[return_df['in_use_fuel_id'] != "{'US electricity':1.0}", 'fueling_class'] = 'ICE'

    return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1,
                     'onroad_gallons_per_mile',
                     return_df['fuel_consumption_gallons'] / return_df['vmt_liquid_fuel'])

    return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1,
                     'onroad_direct_kwh_per_mile',
                     return_df['fuel_consumption_kWh'] * return_df['transmission_efficiency'] /
                     return_df['vmt_electricity'])

    return_df.insert(return_df.columns.get_loc('fuel_generation_kWh') + 1,
                     'onroad_direct_co2e_grams_per_mile',
                     return_df['co2_vehicle_metrictons'] * grams_per_metric_ton / return_df['vmt_liquid_fuel'])

    attributes += ['onroad_gallons_per_mile',
                   'onroad_direct_kwh_per_mile',
                   'onroad_direct_co2e_grams_per_mile']

    return_df.drop(columns='transmission_efficiency', inplace=True)

    return return_df


def calc_legacy_fleet_physical_effects(batch_settings, session_settings, legacy_fleet_safety_effects_dict):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        legacy_fleet_safety_effects_dict: The legacy_fleet dictionary generated via the safety_effects module.

    Returns:
        A dictionary of legacy fleet physical effects where keys are a (vehicle_id, calendar_year, age)
        tuple and values are a dictionary of attribute_name and attribute_value pairs of physical effects.

    Note:
        This function must not be called until AFTER calc_physical_effects so that the EGU rates will have been
        generated using the energy consumption there. This means that legacy fleet electricity consumption is not
        included when calculating the EGU rates used in the analysis. The legacy fleet electricity consumption is
        small and gets smaller with each future year making this a minor, if not acceptably negligible, impact.

    """
    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, \
        diesel_energy_density_ratio, fuel_reduction_leading_to_reduced_domestic_refining \
        = get_inputs_for_effects(batch_settings)

    physical_effects_dict = dict()
    for key, nested_dict in batch_settings.legacy_fleet.adjusted_legacy_fleet.items():

        vehicle_effects_dict = dict()

        vehicle_id, calendar_year, age = key

        # get vmt and session fatalities from safety_effects_dict
        safety_effects_key = (vehicle_id, calendar_year, age)
        safety = legacy_fleet_safety_effects_dict[safety_effects_key]
        session_fatalities, vmt, annual_vmt, odometer, calendar_year_vmt_adj, vmt_rebound, annual_vmt_rebound, \
            size_class, body_style \
            = safety['session_fatalities'], \
            safety['vmt'], \
            safety['annual_vmt'], \
            safety['odometer'], \
            safety['context_vmt_adjustment'], \
            safety['vmt_rebound'], \
            safety['annual_vmt_rebound'], \
            safety['context_size_class'], \
            safety['body_style']

        model_year = calendar_year - age
        reg_class_id = nested_dict['reg_class_id']
        market_class_id = nested_dict['market_class_id']
        in_use_fuel_id = nested_dict['in_use_fuel_id']
        miles_per_gallon = nested_dict['miles_per_gallon']
        kwh_per_mile = nested_dict['kwh_per_mile']
        onroad_miles_per_gallon = miles_per_gallon * 0.8
        try:
            onroad_co2_grams_per_mile = 8887 / onroad_miles_per_gallon
            onroad_gallons_per_mile = 1 / onroad_miles_per_gallon
        except ZeroDivisionError:
            onroad_co2_grams_per_mile = 0
            onroad_gallons_per_mile = 0

        onroad_kwh_per_mile = kwh_per_mile / 0.7

        safety_dict_key = (vehicle_id, calendar_year, age)

        nmog_exh_ustons = nmog_evap_ustons = nmog_veh_ustons = 0
        co_exh_ustons = co_veh_ustons = 0
        nox_exh_ustons = nox_veh_ustons = 0
        sox_exh_ustons = sox_veh_ustons = 0
        pm25_exh_ustons = pm25_brakewear_ustons = pm25_tirewear_ustons = pm25_veh_ustons = 0
        acetaldehyde_exh_ustons = acetaldehyde_veh_ustons = 0
        acrolein_exh_ustons = acrolein_veh_ustons = 0
        benzene_exh_ustons = benzene_evap_ustons = benzene_veh_ustons = 0
        ethylbenzene_exh_ustons = ethylbenzene_evap_ustons = ethylbenzene_veh_ustons = 0
        naphthalene_exh_ustons = naphthalene_evap_ustons = naphthalene_veh_ustons = 0
        formaldehyde_exh_ustons = formaldehyde_veh_ustons = 0
        butadiene13_exh_ustons = butadiene13_veh_ustons = 0
        pah15_exh_ustons = pah15_veh_ustons = 0
        co2_exh_metrictons = co2_veh_metrictons = 0
        ch4_exh_metrictons = ch4_veh_metrictons = 0
        n2o_exh_metrictons = n2o_veh_metrictons = 0

        co2_upstream_metrictons = ch4_upstream_metrictons = n2o_upstream_metrictons = 0
        voc_upstream_ustons = co_upstream_ustons = nox_upstream_ustons = pm25_upstream_ustons = 0
        sox_upstream_ustons = hcl_upstream_ustons = hg_upstream_ustons = 0

        pm25_brakewear_rate = pm25_tirewear_rate = 0
        pm25_exh_rate = co_exh_rate = nox_exh_rate = sox_exh_rate = ch4_exh_rate = n2o_exh_rate = 0
        nmog_exh_rate = nmog_permeation_rate = nmog_venting_rate = 0
        nmog_leaks_rate = nmog_refuel_disp_rate = nmog_refuel_spill_rate = 0
        acetaldehyde_exh_rate = acrolein_exh_rate = 0
        benzene_exh_rate = benzene_permeation_rate = benzene_venting_rate = 0
        benzene_leaks_rate = benzene_refuel_disp_rate = benzene_refuel_spill_rate = 0
        ethylbenzene_exh_rate = ethylbenzene_permeation_rate = ethylbenzene_venting_rate = 0
        ethylbenzene_leaks_rate = ethylbenzene_refuel_disp_rate = ethylbenzene_refuel_spill_rate = 0
        formaldehyde_exh_rate = naphthalene_exh_rate = naphthalene_refuel_spill_rate = 0
        butadiene13_exh_rate = pah15_exh_rate = 0

        voc_ref_rate = co_ref_rate = nox_ref_rate = pm25_ref_rate = sox_ref_rate = 0
        co2_ref_rate = ch4_ref_rate = n2o_ref_rate = 0

        voc_egu_rate = co_egu_rate = nox_egu_rate = pm25_egu_rate = sox_egu_rate = hcl_egu_rate = hg_egu_rate = 0
        co2_egu_rate = ch4_egu_rate = n2o_egu_rate = 0

        vmt_electricity = vmt_liquid_fuel = transmission_efficiency = 0

        if reg_class_id == 'car':
            sourcetype_name = 'passenger car'
        elif reg_class_id == 'truck':
            sourcetype_name = 'passenger truck'
        elif reg_class_id == 'mediumduty' and 'cuv' in body_style:
            sourcetype_name = 'passenger truck'
        elif reg_class_id == 'mediumduty' and 'pickup' in body_style:
            sourcetype_name = 'light commercial truck'
        else:
            print('Improper sourcetype_name for vehicle emission rates.')

        veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
        ind_var_value = pd.to_numeric(age)
        if veh_rates_by == 'odometer':
            ind_var_value = pd.to_numeric(odometer)

        fuel_dict = eval(in_use_fuel_id)
        for fuel, fuel_share in fuel_dict.items():

            if 'electric' in fuel:
                vmt_electricity = vmt
                pm25_brakewear_rate, pm25_tirewear_rate \
                    = get_vehicle_emission_rate(session_settings, model_year, sourcetype_name, reg_class_id, fuel,
                                                ind_var_value)

                # the energy consumption and generation values do not matter here, so set to 0
                voc_egu_rate, co_egu_rate, nox_egu_rate, pm25_egu_rate, sox_egu_rate, co2_egu_rate, ch4_egu_rate, \
                    n2o_egu_rate, hcl_egu_rate, hg_egu_rate \
                    = get_egu_emission_rate(session_settings, calendar_year, 0, 0)

            elif 'gasoline' in fuel:
                vmt_liquid_fuel = vmt
                pm25_brakewear_rate, pm25_tirewear_rate, pm25_exh_rate, \
                    nmog_exh_rate, nmog_permeation_rate, nmog_venting_rate, nmog_leaks_rate, \
                    nmog_refuel_disp_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                    sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, acrolein_exh_rate, \
                    benzene_exh_rate, benzene_permeation_rate, benzene_venting_rate, benzene_leaks_rate, \
                    benzene_refuel_disp_rate, benzene_refuel_spill_rate, \
                    ethylbenzene_exh_rate, ethylbenzene_permeation_rate, ethylbenzene_venting_rate, \
                    ethylbenzene_leaks_rate, ethylbenzene_refuel_disp_rate, ethylbenzene_refuel_spill_rate, \
                    formaldehyde_exh_rate, naphthalene_exh_rate, \
                    butadiene13_exh_rate, pah15_exh_rate \
                        = get_vehicle_emission_rate(session_settings, model_year, sourcetype_name, reg_class_id, fuel,
                                                    ind_var_value)

                # voc_ref_rate, co_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co2_ref_rate, ch4_ref_rate, n2o_ref_rate \
                #     = get_refinery_ef(session_settings, calendar_year, fuel)

                energy_density_ratio, pure_share = e0_energy_density_ratio, e0_share

            elif 'diesel' in fuel:
                vmt_liquid_fuel = vmt
                pm25_brakewear_rate, pm25_tirewear_rate, pm25_exh_rate, \
                    nmog_exh_rate, nmog_refuel_spill_rate, co_exh_rate, nox_exh_rate, \
                    sox_exh_rate, ch4_exh_rate, n2o_exh_rate, acetaldehyde_exh_rate, acrolein_exh_rate, \
                    benzene_exh_rate, benzene_refuel_spill_rate, \
                    ethylbenzene_exh_rate, ethylbenzene_refuel_spill_rate, \
                    formaldehyde_exh_rate, naphthalene_exh_rate, naphthalene_refuel_spill_rate, \
                    butadiene13_exh_rate, pah15_exh_rate \
                        = get_vehicle_emission_rate(session_settings, model_year, sourcetype_name, reg_class_id, fuel,
                                                    ind_var_value)

                # voc_ref_rate, co_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co2_ref_rate, ch4_ref_rate, n2o_ref_rate \
                #     = get_refinery_ef(session_settings, calendar_year, fuel)

                energy_density_ratio, pure_share = diesel_energy_density_ratio, 1

            if session_settings.emission_factors_refinery:
                voc_ref_rate, co_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, \
                    co2_ref_rate, ch4_ref_rate, n2o_ref_rate \
                    = get_refinery_ef(session_settings, calendar_year, fuel)
            else:
                voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate = \
                    get_refinery_emission_rate(session_settings, calendar_year)

            transmission_efficiency \
                = batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')

        fuel_consumption_kWh = vmt * onroad_kwh_per_mile
        fuel_generation_kWh = fuel_consumption_kWh / transmission_efficiency
        fuel_consumption_gallons = vmt * onroad_gallons_per_mile

        # calc exhaust and evaporative emissions for liquid fuel operation
        factor = vmt_liquid_fuel / grams_per_us_ton
        pm25_exh_ustons += pm25_exh_rate * factor
        nmog_exh_ustons += nmog_exh_rate * factor
        co_exh_ustons += co_exh_rate * factor
        nox_exh_ustons += nox_exh_rate * factor
        acetaldehyde_exh_ustons += acetaldehyde_exh_rate * factor
        acrolein_exh_ustons += acrolein_exh_rate * factor
        benzene_exh_ustons += benzene_exh_rate * factor
        ethylbenzene_exh_ustons += ethylbenzene_exh_rate * factor
        formaldehyde_exh_ustons += formaldehyde_exh_rate * factor
        naphthalene_exh_ustons += naphthalene_exh_rate * factor
        butadiene13_exh_ustons += butadiene13_exh_rate * factor
        pah15_exh_ustons += pah15_exh_rate * factor

        factor = fuel_consumption_gallons / grams_per_us_ton
        sox_exh_ustons += sox_exh_rate * factor
        nmog_evap_ustons += sum([nmog_permeation_rate,
                                 nmog_venting_rate,
                                 nmog_leaks_rate,
                                 nmog_refuel_disp_rate,
                                 nmog_refuel_spill_rate]) * factor
        benzene_evap_ustons += sum([benzene_permeation_rate,
                                    benzene_venting_rate,
                                    benzene_leaks_rate,
                                    benzene_refuel_disp_rate,
                                    benzene_refuel_spill_rate]) * factor
        ethylbenzene_evap_ustons += sum([ethylbenzene_permeation_rate,
                                         ethylbenzene_venting_rate,
                                         ethylbenzene_leaks_rate,
                                         ethylbenzene_refuel_disp_rate,
                                         ethylbenzene_refuel_spill_rate]) * factor
        naphthalene_evap_ustons += naphthalene_refuel_spill_rate * factor

        factor = vmt_liquid_fuel / grams_per_metric_ton
        ch4_veh_metrictons += ch4_exh_rate * factor
        n2o_veh_metrictons += n2o_exh_rate * factor
        co2_veh_metrictons += onroad_co2_grams_per_mile * factor

        # calc vehicle inventories as exhaust plus evap (where applicable)
        nmog_veh_ustons = nmog_exh_ustons + nmog_evap_ustons
        co_veh_ustons = co_exh_ustons
        nox_veh_ustons = nox_exh_ustons
        sox_veh_ustons = sox_exh_ustons
        acetaldehyde_veh_ustons = acetaldehyde_exh_ustons
        acrolein_veh_ustons = acrolein_exh_ustons
        benzene_veh_ustons = benzene_exh_ustons + benzene_evap_ustons
        ethylbenzene_veh_ustons = ethylbenzene_exh_ustons + ethylbenzene_evap_ustons
        formaldehyde_veh_ustons = formaldehyde_exh_ustons
        naphthalene_veh_ustons = naphthalene_exh_ustons + naphthalene_evap_ustons
        butadiene13_veh_ustons = butadiene13_exh_ustons
        pah15_veh_ustons = pah15_exh_ustons

        # other vehicle emissions
        pm25_brakewear_ustons += vmt * pm25_brakewear_rate / grams_per_us_ton
        pm25_tirewear_ustons += vmt * pm25_tirewear_rate / grams_per_us_ton

        pm25_veh_ustons = pm25_exh_ustons + pm25_brakewear_ustons + pm25_tirewear_ustons

        # calc upstream emissions for both liquid and electric fuel operation
        kwhs, gallons = fuel_generation_kWh, fuel_consumption_gallons
        ref_factor = fuel_reduction_leading_to_reduced_domestic_refining
        voc_upstream_ustons = (kwhs * voc_egu_rate + gallons * voc_ref_rate * ref_factor) / grams_per_us_ton
        co_upstream_ustons = (kwhs * co_egu_rate + gallons * co_ref_rate * ref_factor) / grams_per_us_ton
        nox_upstream_ustons = (kwhs * nox_egu_rate + gallons * nox_ref_rate * ref_factor) / grams_per_us_ton
        pm25_upstream_ustons = (kwhs * pm25_egu_rate + gallons * pm25_ref_rate * ref_factor) / grams_per_us_ton
        sox_upstream_ustons = (kwhs * sox_egu_rate + gallons * sox_ref_rate * ref_factor) / grams_per_us_ton
        # benzene_upstream_ustons = (kwhs * benzene_ps + gallons * benzene_ref) / grams_per_us_ton
        # butadiene13_upstream_ustons = (kwhs * butadiene13_ps + gallons * butadiene13_ref) / grams_per_us_ton
        # formaldehyde_upstream_ustons = (kwhs * formaldehyde_ps + gallons * formaldehyde_ref) / grams_per_us_ton
        # acetaldehyde_upstream_ustons = (kwhs * acetaldehyde_ps + gallons * acetaldehyde_ref) / grams_per_us_ton
        # acrolein_upstream_ustons = (kwhs * acrolein_ps + gallons * acrolein_ref) / grams_per_us_ton

        co2_upstream_metrictons = (kwhs * co2_egu_rate + gallons * co2_ref_rate * ref_factor) / grams_per_metric_ton
        ch4_upstream_metrictons = (kwhs * ch4_egu_rate + gallons * ch4_ref_rate * ref_factor) / grams_per_metric_ton
        n2o_upstream_metrictons = (kwhs * n2o_egu_rate + gallons * n2o_ref_rate * ref_factor) / grams_per_metric_ton

        # sum vehicle and upstream into totals
        voc_total_ustons = voc_upstream_ustons  # + voc_tailpipe_ustons
        nmog_total_ustons = nmog_veh_ustons  # + nmog_upstream_ustons
        co_total_ustons = co_veh_ustons + co_upstream_ustons
        nox_total_ustons = nox_veh_ustons + nox_upstream_ustons
        pm25_total_ustons = pm25_veh_ustons + pm25_upstream_ustons
        sox_total_ustons = sox_veh_ustons + sox_upstream_ustons
        acetaldehyde_total_ustons = acetaldehyde_veh_ustons  # + acetaldehyde_upstream_ustons
        acrolein_total_ustons = acrolein_veh_ustons  # + acrolein_upstream_ustons
        benzene_total_ustons = benzene_veh_ustons  # + benzene_upstream_ustons
        ethylbenzene_total_ustons = ethylbenzene_veh_ustons  # + ethylbenzene_upstream_ustons
        formaldehyde_total_ustons = formaldehyde_veh_ustons  # + formaldehyde_upstream_ustons
        naphthalene_total_ustons = naphthalene_veh_ustons  # + naphlathene_upstream_ustons
        butadiene13_total_ustons = butadiene13_veh_ustons  # + butadiene13_upstream_ustons
        pah15_total_ustons = pah15_veh_ustons  # + pah15_upstream_ustons
        co2_total_metrictons = co2_veh_metrictons + co2_upstream_metrictons
        ch4_total_metrictons = ch4_veh_metrictons + ch4_upstream_metrictons
        n2o_total_metrictons = n2o_veh_metrictons + n2o_upstream_metrictons

        # calc energy security related attributes and comparisons to year_for_compares
        oil_bbl = fuel_consumption_gallons * pure_share * energy_density_ratio / gal_per_bbl
        imported_oil_bbl = oil_bbl * get_energysecurity_cf(batch_settings, calendar_year)
        imported_oil_bbl_per_day = imported_oil_bbl / 365
        # share_of_us_annual_gasoline = fuel_consumption_gallons / gallons_of_gasoline_us_annual
        # share_of_us_annual_oil = oil_bbl / bbl_oil_us_annual

        # calc kwh and comparisons to year_for_compares
        # share_of_us_annual_kwh = fuel_generation_kWh / kwh_us_annual

        vehicle_effects_dict.update({
            'session_policy': session_settings.session_policy,
            'session_name': session_settings.session_name,
            'vehicle_id': vehicle_id,
            'base_year_vehicle_id': vehicle_id,
            'manufacturer_id': legacy_fleet_safety_effects_dict[safety_dict_key]['manufacturer_id'],
            'name': legacy_fleet_safety_effects_dict[safety_dict_key]['name'],
            'calendar_year': calendar_year,
            'model_year': model_year,
            'age': age,
            'base_year_reg_class_id': reg_class_id,
            'reg_class_id': reg_class_id,
            'context_size_class': size_class,
            'in_use_fuel_id': in_use_fuel_id,
            'market_class_id': market_class_id,
            'fueling_class': legacy_fleet_safety_effects_dict[safety_dict_key]['fueling_class'],
            'base_year_powertrain_type': legacy_fleet_safety_effects_dict[safety_dict_key]['base_year_powertrain_type'],
            'body_style': legacy_fleet_safety_effects_dict[safety_dict_key]['body_style'],
            'footprint_ft2': 0,
            'workfactor': 0,
            'registered_count': legacy_fleet_safety_effects_dict[safety_dict_key]['registered_count'],
            'context_vmt_adjustment': calendar_year_vmt_adj,
            'annual_vmt': annual_vmt,
            'odometer': odometer,
            'vmt': vmt,
            'annual_vmt_rebound': annual_vmt_rebound,
            'vmt_rebound': vmt_rebound,
            'vmt_liquid_fuel': vmt_liquid_fuel,
            'vmt_electricity': vmt_electricity,
            'battery_kwh': 0,  # only care about this for age==0 vehicles which there are none in the legacy fleet
            'onroad_direct_co2e_grams_per_mile': onroad_co2_grams_per_mile,
            'onroad_direct_kwh_per_mile': onroad_kwh_per_mile,
            'onroad_gallons_per_mile': onroad_gallons_per_mile,
            'onroad_miles_per_gallon': onroad_miles_per_gallon,
            'fuel_consumption_gallons': fuel_consumption_gallons,
            'fuel_consumption_kWh': fuel_consumption_kWh,
            'fuel_generation_kWh': fuel_generation_kWh,

            # f'share_of_{year_for_compares}_US_gasoline': share_of_us_annual_gasoline,
            # f'share_of_{year_for_compares}_US_kWh': share_of_us_annual_kwh,
            'barrels_of_oil': oil_bbl,
            # f'share_of_{year_for_compares}_US_oil': share_of_us_annual_oil,
            'barrels_of_imported_oil': imported_oil_bbl,
            'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,

            'session_fatalities': session_fatalities,

            'nmog_exhaust_ustons': nmog_exh_ustons,
            'nmog_evaporative_ustons': nmog_evap_ustons,
            'nmog_vehicle_ustons': nmog_veh_ustons,
            'co_vehicle_ustons': co_veh_ustons,
            'nox_vehicle_ustons': nox_veh_ustons,
            'pm25_exhaust_ustons': pm25_exh_ustons,
            'pm25_brakewear_ustons': pm25_brakewear_ustons,
            'pm25_tirewear_ustons': pm25_tirewear_ustons,
            'pm25_vehicle_ustons': pm25_veh_ustons,
            'sox_vehicle_ustons': sox_veh_ustons,
            'acetaldehyde_vehicle_ustons': acetaldehyde_veh_ustons,
            'acrolein_vehicle_ustons': acrolein_veh_ustons,
            'benzene_exhaust_ustons': benzene_exh_ustons,
            'benzene_evaporative_ustons': benzene_evap_ustons,
            'benzene_vehicle_ustons': benzene_veh_ustons,
            'ethylbenzene_exhaust_ustons': ethylbenzene_exh_ustons,
            'ethylbenzene_evaporative_ustons': ethylbenzene_evap_ustons,
            'ethylbenzene_vehicle_ustons': ethylbenzene_veh_ustons,
            'formaldehyde_vehicle_ustons': formaldehyde_veh_ustons,
            'naphthalene_exhaust_ustons': naphthalene_exh_ustons,
            'naphthalene_evaporative_ustons': naphthalene_evap_ustons,
            'naphthalene_vehicle_ustons': naphthalene_veh_ustons,
            '13_butadiene_vehicle_ustons': butadiene13_veh_ustons,
            '15pah_vehicle_ustons': pah15_veh_ustons,

            'ch4_vehicle_metrictons': ch4_veh_metrictons,
            'n2o_vehicle_metrictons': n2o_veh_metrictons,
            'co2_vehicle_metrictons': co2_veh_metrictons,

            'voc_upstream_ustons': voc_upstream_ustons,
            'co_upstream_ustons': co_upstream_ustons,
            'nox_upstream_ustons': nox_upstream_ustons,
            'pm25_upstream_ustons': pm25_upstream_ustons,
            'sox_upstream_ustons': sox_upstream_ustons,
            'hcl_upstream_ustons': hcl_upstream_ustons,
            'hg_upstream_ustons': hg_upstream_ustons,

            'ch4_upstream_metrictons': ch4_upstream_metrictons,
            'n2o_upstream_metrictons': n2o_upstream_metrictons,
            'co2_upstream_metrictons': co2_upstream_metrictons,

            'nmog_and_voc_total_ustons': nmog_total_ustons + voc_total_ustons,
            'co_total_ustons': co_total_ustons,
            'nox_total_ustons': nox_total_ustons,
            'pm25_total_ustons': pm25_total_ustons,
            'sox_total_ustons': sox_total_ustons,
            'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
            'acrolein_total_ustons': acrolein_total_ustons,
            'benzene_total_ustons': benzene_total_ustons,
            'ethylbenzene_total_ustons': ethylbenzene_total_ustons,
            'formaldehyde_total_ustons': formaldehyde_total_ustons,
            'naphthalene_total_ustons': naphthalene_total_ustons,
            '13_butadiene_total_ustons': butadiene13_total_ustons,
            '15pah_total_ustons': pah15_total_ustons,
            'co2_total_metrictons': co2_total_metrictons,
            'ch4_total_metrictons': ch4_total_metrictons,
            'n2o_total_metrictons': n2o_total_metrictons,
        }
        )
        key = (vehicle_id, calendar_year, age)
        physical_effects_dict[key] = vehicle_effects_dict

    return physical_effects_dict


def calc_period_consumer_physical_view(batch_settings, input_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        input_df: DataFrame of physical effects by vehicle in each analysis year.

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
    periods = batch_settings.general_inputs_for_effects.get_value('years_in_consumer_view')

    # if periods = 8, then max_age should be 7 since year 1 is age=0
    max_age = periods - 1
    df = input_df.loc[(input_df['manufacturer_id'] != 'legacy_fleet') & (input_df['age'] <= max_age), :]

    # now create a sales column for use in some of the 'per vehicle' calcs below
    df.insert(df.columns.get_loc('registered_count'), 'sales', df['registered_count'])
    df.loc[df['age'] != 0, 'sales'] = 0

    # groupby model year, body_style and fuel,
    groupby_cols = ['session_policy', 'session_name', 'model_year', 'body_style', 'in_use_fuel_id']
    attributes.append('sales')
    return_df = df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(
        return_df.columns.get_loc('in_use_fuel_id') + 1,
        'fueling_class',
        '')

    return_df.loc[return_df['in_use_fuel_id'] == "{'US electricity':1.0}", 'fueling_class'] = 'BEV'
    return_df.loc[return_df['in_use_fuel_id'] != "{'US electricity':1.0}", 'fueling_class'] = 'ICE'

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
