"""

Refinery Inventory and Oil Imports

----

**CODE**

"""
import pandas as pd

from omega_effects.effects.physical_effects import get_inputs_for_effects


def get_refinery_data(batch_settings, calendar_year, reg_class_id, fuel):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year (int): The calendar year for which a refinery emission factors are needed.
        reg_class_id (str): The reg class for which to get context scaler data, i.e., 'car', 'truck', 'mediumduty'
        fuel (str): e.g., 'gasoline' or 'diesel'

    Returns:
        A list of refinery emission rates as specified in the emission_rates list for the given calendar year.

    """
    args = [
        f'{fuel}_voc_grams_per_gallon',
        f'{fuel}_nox_grams_per_gallon',
        f'{fuel}_pm25_grams_per_gallon',
        f'{fuel}_sox_grams_per_gallon',
        f'{fuel}_co_grams_per_gallon',
        f'{fuel}_co2_grams_per_gallon',
        f'{fuel}_ch4_grams_per_gallon',
        f'{fuel}_n2o_grams_per_gallon',
        'fuel_reduction_leading_to_reduced_domestic_refining',
        f'domestic_refined_{fuel}_million_barrels_per_day',
        f'context_scaler_lmdv_{reg_class_id}_{fuel}',
        f'context_scaler_lmdv_{fuel}',
    ]
    refinery_data = batch_settings.refinery_data.get_data(calendar_year, reg_class_id, fuel, *args)

    return refinery_data


def get_energysecurity_cf(batch_settings, calendar_year):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year (int): The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    Note:
        In the physical_effects module, oil impacts are calculated, not cost impacts; therefore the "cost factor"
        returned here is the oil import reduction as a percentage of oil demand reduction.

    """
    cost_factors = ('oil_import_reduction_as_percent_of_total_oil_demand_reduction',
                    )
    return batch_settings.energy_security_cost_factors.get_cost_factors(calendar_year, cost_factors)


def calc_inventory(context_gallons, session_gallons, rate, impact_on_refining, delta_calc=True, conversion=1):
    """

    Args:
        context_gallons (float): the domestic refining associated with the refinery data
        session_gallons (float): the session liquid fuel consumption
        rate (float): the emission rate for the given pollutant
        impact_on_refining (float): the impact of reduced demand on domestic refining
        delta_calc (bool): True for delta from no_action; False for missing entry in no_action
        conversion (int): the conversion from grams to US tons or metric tons

    Returns:
        An inventory value for the given pollutant.

    """
    if delta_calc:
        return rate * (context_gallons - (context_gallons - session_gallons) * impact_on_refining) / conversion
    else:
        return rate * session_gallons / conversion


def calc_refinery_inventory_and_oil_imports(batch_settings, annual_physical_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class
        annual_physical_df (DataFrame): a DataFrame of annual physical effects

    Returns:
        The passed physical effects dictionary with refinery inventories and oil import effects included

    Note:
        For action sessions, both the action and no_action physical effects are needed so that the fuel reductions
        can be calculated; reduced fuel may or may not result in less refining and oil imports depending on the
        refinery data setting for the "fuel_reduction_leading_to_reduced_domestic_refining" attribute and the energy
        security cost factor setting for the "oil_import_reduction_as_percent_of_total_oil_demand_reduction" attribute.
        Note that there are no oil import effects in the no-action session since the effects apply only to changes in
        fuel demand.

    """
    (grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio,
     diesel_energy_density_ratio,
     ) = get_inputs_for_effects(batch_settings)

    gallons_arg = 'fuel_consumption_gallons'
    if 'petroleum' in batch_settings.refinery_data.rate_basis:
        gallons_arg = 'petroleum_consumption_gallons'

    session_policies = annual_physical_df['session_policy'].unique()
    in_use_fuel_ids = annual_physical_df['in_use_fuel_id'].unique()
    reg_class_ids = annual_physical_df['reg_class_id'].unique()

    keys = pd.Series(zip(
        annual_physical_df['session_policy'],
        annual_physical_df['calendar_year'],
        annual_physical_df['reg_class_id'],
        annual_physical_df['in_use_fuel_id'],
        annual_physical_df['fueling_class'],
    ))
    df = annual_physical_df.set_index(keys)
    sessions_dict = df.to_dict('index')

    # first a loop to calc the fuel consumption by year for each liquid fuel
    fuel_consumption_dict = {}
    for session_policy in session_policies:
        for calendar_year in batch_settings.calendar_years:
            for reg_class_id in reg_class_ids:
                for in_use_fuel_id in in_use_fuel_ids:
                    if 'gasoline' in in_use_fuel_id:
                        fuel = 'gasoline'
                    elif 'diesel' in in_use_fuel_id:
                        fuel = 'diesel'
                    else:
                        fuel = None

                    if fuel is not None:
                        fuel_consumption = 0
                        fuel_consumption = sum([
                            v[gallons_arg] for v in sessions_dict.values() if
                            v['session_policy'] == session_policy and
                            v['calendar_year'] == calendar_year and
                            v['reg_class_id'] == reg_class_id and
                            v['in_use_fuel_id'] == in_use_fuel_id
                        ])
                        fuel_consumption_dict[session_policy, calendar_year, reg_class_id, fuel] = fuel_consumption

    # now determine the share of fuel consumption that's pure ICE vs PHEV
    ice_phev_share_dict = {}
    for session_policy in session_policies:
        for calendar_year in batch_settings.calendar_years:
            for reg_class_id in reg_class_ids:
                for in_use_fuel_id in in_use_fuel_ids:
                    for fueling_class in ['ICE', 'PHEV']:
                        if 'gasoline' in in_use_fuel_id:
                            fuel = 'gasoline'
                        elif 'diesel' in in_use_fuel_id:
                            fuel = 'diesel'
                        else:
                            fuel = None

                        if fuel is not None:
                            fuel_consumption = 0
                            fuel_consumption = sum([
                                v[gallons_arg] for v in sessions_dict.values() if
                                v['session_policy'] == session_policy and
                                v['calendar_year'] == calendar_year and
                                v['reg_class_id'] == reg_class_id and
                                v['in_use_fuel_id'] == in_use_fuel_id and
                                v['fueling_class'] == fueling_class
                            ])
                            share = 0
                            if fuel_consumption_dict[session_policy, calendar_year, reg_class_id, fuel] != 0:
                                share = fuel_consumption / fuel_consumption_dict[
                                    session_policy, calendar_year, reg_class_id, fuel
                                ]
                            ice_phev_share_dict[
                                session_policy, calendar_year, reg_class_id, fuel, fueling_class
                            ] = share

    # now calc inventory impacts by year for each liquid fuel
    for k, v in sessions_dict.items():
        session_policy, calendar_year, reg_class_id, in_use_fuel_id, fueling_class = (
            v['session_policy'], v['calendar_year'], v['reg_class_id'], v['in_use_fuel_id'], v['fueling_class']
        )
        na_key = ('no_action', calendar_year, reg_class_id, in_use_fuel_id, fueling_class)
        if 'gasoline' in in_use_fuel_id:
            fuel = 'gasoline'
        elif 'diesel' in in_use_fuel_id:
            fuel = 'diesel'
        else:
            fuel = None

        voc_refinery_ustons = co_refinery_ustons = nox_refinery_ustons = pm25_refinery_ustons = sox_refinery_ustons = 0
        co2_refinery_metrictons = ch4_refinery_metrictons = n2o_refinery_metrictons = ice_phev_share = 0
        context_gallons = session_gallons = oil_imports_change = oil_imports_change_per_day = 0

        if fuel is not None:
            (voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co_ref_rate,
             co2_ref_rate, ch4_ref_rate, n2o_ref_rate,
             factor, context_million_barrels_per_day, context_scaler_rc_fuel, context_scaler_fuel) = (
                get_refinery_data(batch_settings, calendar_year, reg_class_id, fuel)
            )
            context_gallons = (context_million_barrels_per_day * pow(10, 6) * gal_per_bbl * 365 *
                               context_scaler_rc_fuel * context_scaler_fuel)
            session_gallons = fuel_consumption_dict[session_policy, calendar_year, reg_class_id, fuel]
            ice_phev_share = ice_phev_share_dict[session_policy, calendar_year, reg_class_id, fuel, fueling_class]

            delta_calc = True
            voc_refinery_ustons = calc_inventory(
                context_gallons, session_gallons, voc_ref_rate, factor, delta_calc, grams_per_us_ton
            ) * ice_phev_share
            co_refinery_ustons = calc_inventory(
                context_gallons, session_gallons, co_ref_rate, factor, delta_calc, grams_per_us_ton
            ) * ice_phev_share
            nox_refinery_ustons = calc_inventory(
                context_gallons, session_gallons, nox_ref_rate, factor, delta_calc, grams_per_us_ton
            ) * ice_phev_share
            pm25_refinery_ustons = calc_inventory(
                context_gallons, session_gallons, pm25_ref_rate, factor, delta_calc, grams_per_us_ton
            ) * ice_phev_share
            sox_refinery_ustons = calc_inventory(
                context_gallons, session_gallons, sox_ref_rate, factor, delta_calc, grams_per_us_ton
            ) * ice_phev_share
            co2_refinery_metrictons = calc_inventory(
                context_gallons, session_gallons, co2_ref_rate, factor, delta_calc, grams_per_metric_ton
            ) * ice_phev_share
            ch4_refinery_metrictons = calc_inventory(
                context_gallons, session_gallons, ch4_ref_rate, factor, delta_calc, grams_per_metric_ton
            ) * ice_phev_share
            n2o_refinery_metrictons = calc_inventory(
                context_gallons, session_gallons, n2o_ref_rate, factor, delta_calc, grams_per_metric_ton
            ) * ice_phev_share

            energy_security_import_factor = get_energysecurity_cf(batch_settings, calendar_year)
            if na_key in sessions_dict:
                oil_imports_change = (
                        (v['barrels_of_oil'] - sessions_dict[na_key][
                            'barrels_of_oil']) * energy_security_import_factor
                )
            else:
                oil_imports_change = v['barrels_of_oil']
            oil_imports_change_per_day = oil_imports_change / 365

        update_dict = {
            'context_gallons': context_gallons,
            'session_gallons': session_gallons,
            'inventory_share': ice_phev_share,
            'voc_refinery_ustons': voc_refinery_ustons,
            'co_refinery_ustons': co_refinery_ustons,
            'nox_refinery_ustons': nox_refinery_ustons,
            'pm25_refinery_ustons': pm25_refinery_ustons,
            'sox_refinery_ustons': sox_refinery_ustons,
            'co2_refinery_metrictons': co2_refinery_metrictons,
            'ch4_refinery_metrictons': ch4_refinery_metrictons,
            'n2o_refinery_metrictons': n2o_refinery_metrictons,
            'change_in_barrels_of_oil_imports': oil_imports_change,
            'change_in_barrels_of_oil_imports_per_day': oil_imports_change_per_day,
        }
        for attribute_name, attribute_value in update_dict.items():
            sessions_dict[k][attribute_name] = attribute_value

    df = pd.DataFrame(sessions_dict).transpose()
    df.reset_index(drop=True, inplace=True)

    return df
