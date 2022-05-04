"""

Functions to get vehicle data based on vehicle ID, vehicle emission factors for the given vehicle model year and reg-class, refinery and power section emission factors for the given calendar year,
and then to calculate from them the pollutant inventories, including fuel consumed, for each year in the analysis.



----

**CODE**

"""
import pandas as pd

from omega_model import *


def get_vehicle_emission_rate(model_year, reg_class_id, fuel, ind_var_name, ind_var_value, *rate_names):
    """

    Args:
        model_year: The model year of the specific vehicle.
        reg_class_id: The regulatory class ID of the vehicle.
        fuel: The fuel ID (i.e., pump_gasoline, pump_diesel)
        ind_var_dict: An independent variable dictionary of the form {'age': 10} or {'odometer': 75000}
        rate_name: The emission rate to get.

    Returns:
        A list of emission factors as specified in the emission_factors list for the given model-year vehicle in a given calendar year.

    """
    from effects.emission_rates_vehicles import EmissionRatesVehicles

    rate_name_list = [rate_name for rate_name in rate_names]

    rates = EmissionRatesVehicles.get_emission_rate(model_year, reg_class_id, fuel, ind_var_name,
                                                    ind_var_value, *rate_name_list)

    return rates


def get_powersector_ef(calendar_year):
    """

    Args:
        calendar_year: The calendar year for which power sector emission factors are needed.

    Returns:
        A list of power sector emission factors as specified in the emission_factors list for the given calendar year.

    """
    from effects.emission_factors_powersector import EmissionFactorsPowersector

    emission_factors = ('voc_grams_per_kwh',
                        'co_grams_per_kwh',
                        'nox_grams_per_kwh',
                        'pm25_grams_per_kwh',
                        'sox_grams_per_kwh',
                        'benzene_grams_per_kwh',
                        'butadiene13_grams_per_kwh',
                        'formaldehyde_grams_per_kwh',
                        'acetaldehyde_grams_per_kwh',
                        'acrolein_grams_per_kwh',
                        'co2_grams_per_kwh',
                        'ch4_grams_per_kwh',
                        'n2o_grams_per_kwh',
                        )

    return EmissionFactorsPowersector.get_emission_factors(calendar_year, emission_factors)


def get_refinery_ef(calendar_year, fuel):
    """

    Args:
        calendar_year: The calendar year for which a refinery emission factors are needed.
        fuel: The fuel ID for which refinery emission factors are needed (i.e., pump_gasoline, pump_diesel).

    Returns:
        A list of refinery emission factors as specified in the emission_factors list for the given calendar year and liquid fuel.

    """
    from effects.emission_factors_refinery import EmissionFactorsRefinery

    emission_factors = ('voc_grams_per_gallon',
                        'co_grams_per_gallon',
                        'nox_grams_per_gallon',
                        'pm25_grams_per_gallon',
                        'sox_grams_per_gallon',
                        'benzene_grams_per_gallon',
                        'butadiene13_grams_per_gallon',
                        'formaldehyde_grams_per_gallon',
                        'acetaldehyde_grams_per_gallon',
                        'acrolein_grams_per_gallon',
                        'co2_grams_per_gallon',
                        'ch4_grams_per_gallon',
                        'n2o_grams_per_gallon',
                        )

    return EmissionFactorsRefinery.get_emission_factors(calendar_year, fuel, emission_factors)


def get_energysecurity_cf(calendar_year):
    """
    Get energy security cost factors

    Args:
        calendar_year: The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    cost_factors = ('oil_import_reduction_as_percent_of_total_oil_demand_reduction',
                    )

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_inputs_for_effects(*args):

    """
    Get general inputs needed for effects calculations.

    Args:
        args: The attributes for which attribute values are needed.

    Returns:
        A list of necessary input values; use index=[0] if passing a single attribute.

    """
    from effects.general_inputs_for_effects import GeneralInputsForEffects

    values = list()
    for arg in args:
        values.append(GeneralInputsForEffects.get_value(arg))

    return values


def calc_physical_effects(calendar_years):
    """

    Args:
        calendar_years: The years for which emission inventories and fuel consumptions will be calculated.

    Returns:
        A dictionary key, value pair where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
        vehicle attributes (e.g., model_year, reg_class_id, in_use_fuel_id, etc.) and inventory attributes (e.g., co2 tons, fuel consumed, etc.) and their attribute values.

    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal
    from context.onroad_fuels import OnroadFuel
    from common.omega_eval import Eval

    input_attributes_list = ['grams_per_us_ton', 'grams_per_metric_ton', 'gal_per_bbl',
                             'e0_in_retail_gasoline', 'e0_energy_density_ratio',
                             'gallons_of_gasoline_us_annual', 'bbl_oil_us_annual', 'kwh_us_annual', 'year_for_compares']

    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, \
    gallons_of_gasoline_us_annual, bbl_oil_us_annual, kwh_us_annual, year_for_compares = get_inputs_for_effects(*input_attributes_list)

    year_for_compares = int(year_for_compares)

    physical_effects_dict = dict()
    vehicle_info_dict = dict()
    for calendar_year in calendar_years:
        vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

        # UPDATE physical effects data
        calendar_year_effects_dict = dict()
        for vad in vads:

            attribute_list = ['manufacturer_id', 'name', 'model_year', 'base_year_reg_class_id', 'reg_class_id',
                              'in_use_fuel_id', 'fueling_class', 'powertrain_type',
                              'target_co2e_grams_per_mile', 'onroad_direct_co2e_grams_per_mile',
                              'onroad_direct_kwh_per_mile']

            # need vehicle info once for each vehicle, not every calendar year for each vehicle
            if vad['vehicle_id'] not in vehicle_info_dict:
                vehicle_info_dict[vad['vehicle_id']] = VehicleFinal.get_vehicle_attributes(vad['vehicle_id'], attribute_list)

            mfr_id, name, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, fueling_class, \
            powertrain_type, target_co2e_grams_per_mile, onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile \
                = vehicle_info_dict[vad['vehicle_id']]

            # need vehicle effects for each vehicle and for each calendar year since they change year-over-year
            vehicle_effects_dict = dict()
            flag = None
            if target_co2e_grams_per_mile is not None:

                liquid_fuel = None
                electric_fuel = None

                vmt_liquid_fuel = vmt_electricity \
                    = onroad_gallons_per_mile = fuel_consumption_gallons = fuel_consumption_kWh = 0

                voc_tailpipe_ustons = co_tailpipe_ustons = nox_tailpipe_ustons = pm25_tailpipe_ustons \
                    = so2_tailpipe_ustons = benzene_tailpipe_ustons = butadiene13_tailpipe_ustons \
                    = formaldehyde_tailpipe_ustons = acetaldehyde_tailpipe_ustons = acrolein_tailpipe_ustons = 0

                pm25_brakewear_ustons = pm25_tirewear_ustons = 0
                pm25_brakewear_l = pm25_brakewear_e = pm25_tirewear_l = pm25_tirewear_e = 0
                
                ch4_tailpipe_metrictons = n2o_tailpipe_metrictons = co2_tailpipe_metrictons = 0

                voc_ps = co_ps = nox_ps = pm25_ps = sox_ps = benzene_ps = butadiene13_ps = formaldehyde_ps \
                    = acetaldehyde_ps = acrolein_ps = co2_ps = ch4_ps = n2o_ps \
                    = voc_ref = co_ref = nox_ref = pm25_ref = sox_ref = benzene_ref = butadiene13_ref = formaldehyde_ref \
                    = acetaldehyde_ref = acrolein_ref = co2_ref = ch4_ref = n2o_ref \
                    = 0

                veh_rates_by = 'age'  # for now; set as an input if we want to; value can be 'age' or 'odometer'
                ind_var_value = pd.to_numeric(vad['age'])
                if veh_rates_by == 'odometer':
                    ind_var_value = pd.to_numeric(vad['odometer'])

                fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})
                for fuel, fuel_share in fuel_dict.items():
                    refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
                    transmission_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'transmission_efficiency')
                    co2_emissions_grams_per_unit = OnroadFuel.get_fuel_attribute(calendar_year, fuel, 'direct_co2e_grams_per_unit') / refuel_efficiency

                    # calc fuel consumption and get emission factors
                    if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                        electric_fuel = fuel
                        vmt_electricity = vad['vmt'] * fuel_share
                        fuel_consumption_kWh += vmt_electricity * onroad_direct_kwh_per_mile / transmission_efficiency

                        # vehicle emission rates:
                        rate_names = ['pm25_brakewear_grams_per_mile', 'pm25_tirewear_grams_per_mile']
                        pm25_brakewear_e, pm25_tirewear_e \
                            = get_vehicle_emission_rate(model_year, base_year_reg_class_id, fuel, veh_rates_by, ind_var_value, *rate_names)

                        # upstream EGU emission factors for electric fuel operation
                        voc_ps, co_ps, nox_ps, pm25_ps, sox_ps, benzene_ps, butadiene13_ps, formaldehyde_ps, acetaldehyde_ps, acrolein_ps, co2_ps, ch4_ps, n2o_ps \
                            = get_powersector_ef(calendar_year)

                    elif fuel != 'US electricity' and onroad_direct_co2e_grams_per_mile:
                        liquid_fuel = fuel
                        vmt_liquid_fuel = vad['vmt'] * fuel_share
                        onroad_gallons_per_mile += onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                        fuel_consumption_gallons = vad['vmt'] * onroad_gallons_per_mile / transmission_efficiency

                        # vehicle emission rates
                        rate_names = ['pm25_brakewear_grams_per_mile', 'pm25_tirewear_grams_per_mile']
                        pm25_brakewear_l, pm25_tirewear_l \
                            = get_vehicle_emission_rate(model_year, base_year_reg_class_id, fuel, veh_rates_by,
                                                        ind_var_value, *rate_names)

                        rate_names = [
                            'voc_grams_per_mile', 'co_grams_per_mile', 'nox_grams_per_mile',
                            'pm25_exhaust_grams_per_mile', 'so2_grams_per_gallon', 'benzene_grams_per_mile',
                            'butadiene13_grams_per_mile', 'formaldehyde_grams_per_mile', 'acetaldehyde_grams_per_mile',
                            'acrolein_grams_per_mile', 'ch4_grams_per_mile', 'n2o_grams_per_mile']

                        voc, co, nox, pm25_exhaust, so2, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o \
                            = get_vehicle_emission_rate(model_year, base_year_reg_class_id, fuel, veh_rates_by,
                                                        ind_var_value, *rate_names)

                        # upstream refinery emission factors for liquid fuel operation
                        voc_ref, co_ref, nox_ref, pm25_ref, sox_ref, benzene_ref, butadiene13_ref, formaldehyde_ref, \
                        acetaldehyde_ref, acrolein_ref, co2_ref, ch4_ref, n2o_ref \
                            = get_refinery_ef(calendar_year, liquid_fuel)

                        # calc tailpipe emissions for liquid fuel operation
                        factor = vmt_liquid_fuel / grams_per_us_ton
                        voc_tailpipe_ustons += voc * factor
                        co_tailpipe_ustons += co * factor
                        nox_tailpipe_ustons += nox * factor
                        pm25_tailpipe_ustons += pm25_exhaust * factor
                        benzene_tailpipe_ustons += benzene * factor
                        butadiene13_tailpipe_ustons += butadiene13 * factor
                        formaldehyde_tailpipe_ustons += formaldehyde * factor
                        acetaldehyde_tailpipe_ustons += acetaldehyde * factor
                        acrolein_tailpipe_ustons += acrolein * factor

                        so2_tailpipe_ustons += so2 * fuel_consumption_gallons / grams_per_us_ton

                        factor = vmt_liquid_fuel / grams_per_metric_ton
                        ch4_tailpipe_metrictons += ch4 * factor
                        n2o_tailpipe_metrictons += n2o * factor
                        co2_tailpipe_metrictons += onroad_direct_co2e_grams_per_mile * factor

                # other vehicle emissions
                pm25_brakewear_ustons += (vmt_liquid_fuel * pm25_brakewear_l + vmt_electricity * pm25_brakewear_e) \
                                         / grams_per_us_ton
                pm25_tirewear_ustons += (vmt_liquid_fuel * pm25_tirewear_l + vmt_electricity * pm25_tirewear_e) \
                                        / grams_per_us_ton

                # calc upstream emissions for both liquid and electric fuel operation
                kwhs, gallons = fuel_consumption_kWh, fuel_consumption_gallons
                voc_upstream_ustons = (kwhs * voc_ps + gallons * voc_ref) / grams_per_us_ton
                co_upstream_ustons = (kwhs * co_ps + gallons * co_ref) / grams_per_us_ton
                nox_upstream_ustons = (kwhs * nox_ps + gallons * nox_ref) / grams_per_us_ton
                pm25_upstream_ustons = (kwhs * pm25_ps + gallons * pm25_ref) / grams_per_us_ton
                so2_upstream_ustons = (kwhs * sox_ps + gallons * sox_ref) / grams_per_us_ton
                benzene_upstream_ustons = (kwhs * benzene_ps + gallons * benzene_ref) / grams_per_us_ton
                butadiene13_upstream_ustons = (kwhs * butadiene13_ps + gallons * butadiene13_ref) / grams_per_us_ton
                formaldehyde_upstream_ustons = (kwhs * formaldehyde_ps + gallons * formaldehyde_ref) / grams_per_us_ton
                acetaldehyde_upstream_ustons = (kwhs * acetaldehyde_ps + gallons * acetaldehyde_ref) / grams_per_us_ton
                acrolein_upstream_ustons = (kwhs * acrolein_ps + gallons * acrolein_ref) / grams_per_us_ton

                co2_upstream_metrictons = (kwhs * co2_ps + gallons * co2_ref) / grams_per_metric_ton
                ch4_upstream_metrictons = (kwhs * ch4_ps + gallons * ch4_ref) / grams_per_metric_ton
                n2o_upstream_metrictons = (kwhs * n2o_ps + gallons * n2o_ref) / grams_per_metric_ton

                # sum tailpipe and upstream into totals
                voc_total_ustons = voc_tailpipe_ustons + voc_upstream_ustons
                co_total_ustons = co_tailpipe_ustons + co_upstream_ustons
                nox_total_ustons = nox_tailpipe_ustons + nox_upstream_ustons
                pm25_total_ustons = pm25_tailpipe_ustons + pm25_upstream_ustons
                so2_total_ustons = so2_tailpipe_ustons + so2_upstream_ustons
                benzene_total_ustons = benzene_tailpipe_ustons + benzene_upstream_ustons
                butadiene13_total_ustons = butadiene13_tailpipe_ustons + butadiene13_upstream_ustons
                formaldehyde_total_ustons = formaldehyde_tailpipe_ustons + formaldehyde_upstream_ustons
                acetaldehyde_total_ustons = acetaldehyde_tailpipe_ustons + acetaldehyde_upstream_ustons
                acrolein_total_ustons = acrolein_tailpipe_ustons + acrolein_upstream_ustons
                co2_total_metrictons = co2_tailpipe_metrictons + co2_upstream_metrictons
                ch4_total_metrictons = ch4_tailpipe_metrictons + ch4_upstream_metrictons
                n2o_total_metrictons = n2o_tailpipe_metrictons + n2o_upstream_metrictons

                # calc energy security related attributes and comparisons to year_for_compares
                oil_bbl = fuel_consumption_gallons * e0_share * e0_energy_density_ratio / gal_per_bbl
                imported_oil_bbl = oil_bbl * get_energysecurity_cf(calendar_year)
                imported_oil_bbl_per_day = imported_oil_bbl / 365
                share_of_us_annual_gasoline = fuel_consumption_gallons / gallons_of_gasoline_us_annual
                share_of_us_annual_oil = oil_bbl / bbl_oil_us_annual

                # calc kwh and comparisons to year_for_compares
                share_of_us_annual_kwh = fuel_consumption_kWh / kwh_us_annual

                if vmt_liquid_fuel > 0 or vmt_electricity > 0:
                    flag = 1

                vehicle_effects_dict.update({'session_name': omega_globals.options.session_name,
                                             'vehicle_id': int(vad['vehicle_id']),
                                             'manufacturer_id': mfr_id,
                                             'name': name,
                                             'calendar_year': int(calendar_year),
                                             'model_year': calendar_year - vad['age'],
                                             'age': int(vad['age']),
                                             'base_year_reg_class_id': base_year_reg_class_id,
                                             'reg_class_id': reg_class_id,
                                             'in_use_fuel_id': in_use_fuel_id,
                                             'fueling_class': fueling_class,
                                             'powertrain_type': powertrain_type,
                                             'registered_count': vad['registered_count'],
                                             'annual_vmt': vad['annual_vmt'],
                                             'odometer': vad['odometer'],
                                             'vmt': vad['vmt'],
                                             'vmt_liquid_fuel': vmt_liquid_fuel,
                                             'vmt_electricity': vmt_electricity,
                                             'onroad_direct_co2e_grams_per_mile': onroad_direct_co2e_grams_per_mile,
                                             'onroad_direct_kwh_per_mile': onroad_direct_kwh_per_mile,
                                             'onroad_gallons_per_mile': onroad_gallons_per_mile,
                                             'fuel_consumption_gallons': fuel_consumption_gallons,
                                             'fuel_consumption_kWh': fuel_consumption_kWh,

                                             f'share_of_{year_for_compares}_US_gasoline': share_of_us_annual_gasoline,
                                             f'share_of_{year_for_compares}_US_kWh': share_of_us_annual_kwh,
                                             'barrels_of_oil': oil_bbl,
                                             f'share_of_{year_for_compares}_US_oil': share_of_us_annual_oil,
                                             'barrels_of_imported_oil': imported_oil_bbl,
                                             'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,

                                             'voc_tailpipe_ustons': voc_tailpipe_ustons,
                                             'co_tailpipe_ustons': co_tailpipe_ustons,
                                             'nox_tailpipe_ustons': nox_tailpipe_ustons,
                                             'pm25_tailpipe_ustons': pm25_tailpipe_ustons,
                                             'pm25_brakewear_ustons': pm25_brakewear_ustons,
                                             'pm25_tirewear_ustons': pm25_tirewear_ustons,
                                             'so2_tailpipe_ustons': so2_tailpipe_ustons,
                                             'benzene_tailpipe_ustons': benzene_tailpipe_ustons,
                                             'butadiene13_tailpipe_ustons': butadiene13_tailpipe_ustons,
                                             'formaldehyde_tailpipe_ustons': formaldehyde_tailpipe_ustons,
                                             'acetaldehyde_tailpipe_ustons': acetaldehyde_tailpipe_ustons,
                                             'acrolein_tailpipe_ustons': acrolein_tailpipe_ustons,

                                             'ch4_tailpipe_metrictons': ch4_tailpipe_metrictons,
                                             'n2o_tailpipe_metrictons': n2o_tailpipe_metrictons,
                                             'co2_tailpipe_metrictons': co2_tailpipe_metrictons,

                                             'voc_upstream_ustons': voc_upstream_ustons,
                                             'co_upstream_ustons': co_upstream_ustons,
                                             'nox_upstream_ustons': nox_upstream_ustons,
                                             'pm25_upstream_ustons': pm25_upstream_ustons,
                                             'so2_upstream_ustons': so2_upstream_ustons,
                                             'benzene_upstream_ustons': benzene_upstream_ustons,
                                             'butadiene13_upstream_ustons': butadiene13_upstream_ustons,
                                             'formaldehyde_upstream_ustons': formaldehyde_upstream_ustons,
                                             'acetaldehyde_upstream_ustons': acetaldehyde_upstream_ustons,
                                             'acrolein_upstream_ustons': acrolein_upstream_ustons,

                                             'co2_upstream_metrictons': co2_upstream_metrictons,
                                             'ch4_upstream_metrictons': ch4_upstream_metrictons,
                                             'n2o_upstream_metrictons': n2o_upstream_metrictons,

                                             'voc_total_ustons': voc_total_ustons,
                                             'co_total_ustons': co_total_ustons,
                                             'nox_total_ustons': nox_total_ustons,
                                             'pm25_total_ustons': pm25_total_ustons,
                                             'so2_total_ustons': so2_total_ustons,
                                             'benzene_total_ustons': benzene_total_ustons,
                                             'butadiene13_total_ustons': butadiene13_total_ustons,
                                             'formaldehyde_total_ustons': formaldehyde_total_ustons,
                                             'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
                                             'acrolein_total_ustons': acrolein_total_ustons,
                                             'co2_total_metrictons': co2_total_metrictons,
                                             'ch4_total_metrictons': ch4_total_metrictons,
                                             'n2o_total_metrictons': n2o_total_metrictons,
                                             }
                                            )
            if flag:
                key = (int(vad['vehicle_id']), int(calendar_year), int(vad['age']))
                calendar_year_effects_dict[key] = vehicle_effects_dict
        physical_effects_dict.update(calendar_year_effects_dict)
    return physical_effects_dict


def calc_annual_physical_effects(input_df):
    """

    Args:
        input_df: DataFrame of physical effects by vehicle.

    Returns:
        A DataFrame of physical effects by calendar year.

    """
    input_attributes_list = ['grams_per_metric_ton']
    grams_per_metric_ton = get_inputs_for_effects(*input_attributes_list)

    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['count', 'consumption', 'barrels', 'tons']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if col.__contains__(additional_attribute):
                attributes.append(col)

    # groupby calendar year, regclass and fueling class
    groupby_cols = ['session_name', 'calendar_year', 'reg_class_id', 'fueling_class']
    return_df = input_df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(return_df.columns.get_loc('fuel_consumption_kWh') + 1,
                     'onroad_gallons_per_mile',
                     return_df['fuel_consumption_gallons'] / return_df['vmt_liquid_fuel'])

    return_df.insert(return_df.columns.get_loc('fuel_consumption_kWh') + 1,
                     'onroad_direct_kwh_per_mile',
                     return_df['fuel_consumption_kWh'] / return_df['vmt_electricity'])

    return_df.insert(return_df.columns.get_loc('fuel_consumption_kWh') + 1,
                     'onroad_direct_co2e_grams_per_mile',
                     return_df['co2_tailpipe_metrictons'] * grams_per_metric_ton / return_df['vmt_liquid_fuel'])

    attributes += ['onroad_gallons_per_mile',
                   'onroad_direct_kwh_per_mile',
                   'onroad_direct_co2e_grams_per_mile']

    # groupby calendar year and regclass
    groupby_cols = ['session_name', 'calendar_year', 'reg_class_id']
    yr_rc_df = input_df[[*groupby_cols, *attributes]]
    yr_rc_df = yr_rc_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    yr_rc_df.insert(yr_rc_df.columns.get_loc('reg_class_id') + 1, 'fueling_class', 'ALL')

    # groupby calendar year and fueling class
    groupby_cols = ['session_name', 'calendar_year', 'fueling_class']
    yr_fc_df = input_df[[*groupby_cols, *attributes]]
    yr_fc_df = yr_fc_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    yr_fc_df.insert(yr_fc_df.columns.get_loc('fueling_class') - 1, 'reg_class_id', 'ALL')

    # groupby calendar year
    groupby_cols = ['session_name', 'calendar_year']
    yr_df = input_df[[*groupby_cols, *attributes]]
    yr_df = yr_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()
    yr_df.insert(yr_df.columns.get_loc('calendar_year') + 1, 'fueling_class', 'ALL')
    yr_df.insert(yr_df.columns.get_loc('calendar_year') + 1, 'reg_class_id', 'ALL')

    for df in [yr_rc_df, yr_fc_df, yr_df]:
        df['onroad_gallons_per_mile'] = df['fuel_consumption_gallons'] / df['vmt']
        df['onroad_direct_kwh_per_mile'] = df['fuel_consumption_kWh'] / df['vmt']
        df['onroad_direct_co2e_grams_per_mile'] = df['co2_tailpipe_metrictons'] * grams_per_metric_ton / df['vmt']

    return_df = pd.concat([return_df, yr_rc_df, yr_fc_df, yr_df], axis=0, ignore_index=True)

    # calc additional attributes
    input_attributes_list = ['gallons_of_gasoline_us_annual', 'bbl_oil_us_annual', 'kwh_us_annual', 'year_for_compares']

    gallons_of_gasoline_us_annual, bbl_oil_us_annual, kwh_us_annual, year_for_compares = get_inputs_for_effects(*input_attributes_list)
    year_for_compares = int(year_for_compares)

    share_of_us_annual_gasoline = return_df['fuel_consumption_gallons'] / gallons_of_gasoline_us_annual
    share_of_us_annual_oil = return_df['barrels_of_oil'] / bbl_oil_us_annual
    share_of_us_annual_kwh = return_df['fuel_consumption_kWh'] / kwh_us_annual

    return_df.insert(return_df.columns.get_loc('fuel_consumption_kWh') + 1, f'share_of_{year_for_compares}_US_kWh', share_of_us_annual_kwh)
    return_df.insert(return_df.columns.get_loc('fuel_consumption_kWh') + 1, f'share_of_{year_for_compares}_US_gasoline', share_of_us_annual_gasoline)
    return_df.insert(return_df.columns.get_loc('barrels_of_oil') + 1, f'share_of_{year_for_compares}_US_oil', share_of_us_annual_oil)

    return return_df
