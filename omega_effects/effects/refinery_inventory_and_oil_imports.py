"""

Refinery Inventory and Oil Imports

----

**CODE**

"""
import pandas as pd

from omega_effects.effects.physical_effects import get_inputs_for_effects


def get_refinery_data(session_settings, calendar_year, reg_class_id, fuel):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
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
        f'context_scaler_{reg_class_id}_{fuel}'
    ]
    refinery_data = session_settings.refinery_data.get_data(calendar_year, fuel, *args)

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
        inventory = rate * (context_gallons - (context_gallons - session_gallons) * impact_on_refining) / conversion
        internal_rate = inventory * conversion / session_gallons

        return inventory, internal_rate

    else:
        return rate * session_gallons / conversion, rate


def calc_refinery_inventory_and_oil_imports(batch_settings, session_settings, annual_physical_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class
        session_settings: an instance of the SessionSettings class
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
    if 'petroleum' in session_settings.refinery_data.rate_basis:
        gallons_arg = 'petroleum_consumption_gallons'

    keys = pd.Series(zip(
        annual_physical_df['session_policy'],
        annual_physical_df['calendar_year'],
        annual_physical_df['reg_class_id'],
        annual_physical_df['in_use_fuel_id'],
        annual_physical_df['fueling_class'],
    ))
    df = annual_physical_df.set_index(keys)
    sessions_dict = df.to_dict('index')

    internal_rates = {}

    for k, v in sessions_dict.items():
        session_policy, calendar_year, fuel_dict = v['session_policy'], v['calendar_year'], eval(v['in_use_fuel_id'])
        fuel = [item for item in fuel_dict.keys()][0]  # fuel here will be something like 'pump gasoline'
        if 'gasoline' in fuel:
            fuel = 'gasoline'
        elif 'diesel' in fuel:
            fuel = 'diesel'
        else:
            fuel = None

        na_key = ('no_action', calendar_year, v['reg_class_id'], v['in_use_fuel_id'], v['fueling_class'])

        voc_refinery_ustons = co_refinery_ustons = nox_refinery_ustons = pm25_refinery_ustons = sox_refinery_ustons = 0
        co2_refinery_metrictons = ch4_refinery_metrictons = n2o_refinery_metrictons = 0
        oil_imports_change = oil_imports_change_per_day = 0

        energy_security_import_factor = get_energysecurity_cf(batch_settings, calendar_year)

        if fuel is not None:

            delta_calc = True
            if na_key not in sessions_dict:
                delta_calc = False

            if v['fueling_class'] != 'PHEV':
                (voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co_ref_rate,
                 co2_ref_rate, ch4_ref_rate, n2o_ref_rate,
                 factor, context_million_barrels_per_day, context_scaler) = get_refinery_data(
                    session_settings, calendar_year, v['reg_class_id'], fuel
                )
                context_gallons = context_million_barrels_per_day * pow(10, 6) * gal_per_bbl * 365 * context_scaler
                session_gallons = v[gallons_arg]

                voc_refinery_ustons, voc_internal_rate = calc_inventory(
                    context_gallons, session_gallons, voc_ref_rate, factor, delta_calc, grams_per_us_ton
                )
                co_refinery_ustons, co_internal_rate = calc_inventory(
                    context_gallons, session_gallons, co_ref_rate, factor, delta_calc, grams_per_us_ton
                )
                nox_refinery_ustons, nox_internal_rate = calc_inventory(
                    context_gallons, session_gallons, nox_ref_rate, factor, delta_calc, grams_per_us_ton
                )
                pm25_refinery_ustons, pm25_internal_rate = calc_inventory(
                    context_gallons, session_gallons, pm25_ref_rate, factor, delta_calc, grams_per_us_ton
                )
                sox_refinery_ustons, sox_internal_rate = calc_inventory(
                    context_gallons, session_gallons, sox_ref_rate, factor, delta_calc, grams_per_us_ton
                )
                co2_refinery_metrictons, co2_internal_rate = calc_inventory(
                    context_gallons, session_gallons, co2_ref_rate, factor, delta_calc, grams_per_metric_ton
                )
                ch4_refinery_metrictons, ch4_internal_rate = calc_inventory(
                    context_gallons, session_gallons, ch4_ref_rate, factor, delta_calc, grams_per_metric_ton
                )
                n2o_refinery_metrictons, n2o_internal_rate = calc_inventory(
                    context_gallons, session_gallons, n2o_ref_rate, factor, delta_calc, grams_per_metric_ton
                )
                if na_key in sessions_dict:
                    oil_imports_change = (
                            (v['barrels_of_oil'] - sessions_dict[na_key][
                                'barrels_of_oil']) * energy_security_import_factor
                    )
                else:
                    oil_imports_change = v['barrels_of_oil']
                oil_imports_change_per_day = oil_imports_change / 365

                internal_rates[(calendar_year, fuel)] = [
                    voc_internal_rate, co_internal_rate, nox_internal_rate, pm25_internal_rate, sox_internal_rate,
                    co2_internal_rate, ch4_internal_rate, n2o_internal_rate, factor
                ]
            else:
                voc_internal_rate, co_internal_rate, nox_internal_rate, pm25_internal_rate, sox_internal_rate, \
                    co2_internal_rate, ch4_internal_rate, n2o_internal_rate, factor = internal_rates[(
                    calendar_year, fuel
                )]
                session_gallons = v[gallons_arg]
                delta_calc = False
                context_gallons = 0

                voc_refinery_ustons, voc_internal_rate = calc_inventory(
                    context_gallons, session_gallons, voc_internal_rate, factor, delta_calc, grams_per_us_ton
                )
                co_refinery_ustons, co_internal_rate = calc_inventory(
                    context_gallons, session_gallons, co_internal_rate, factor, delta_calc, grams_per_us_ton
                )
                nox_refinery_ustons, nox_internal_rate = calc_inventory(
                    context_gallons, session_gallons, nox_internal_rate, factor, delta_calc, grams_per_us_ton
                )
                pm25_refinery_ustons, pm25_internal_rate = calc_inventory(
                    context_gallons, session_gallons, pm25_internal_rate, factor, delta_calc, grams_per_us_ton
                )
                sox_refinery_ustons, sox_internal_rate = calc_inventory(
                    context_gallons, session_gallons, sox_internal_rate, factor, delta_calc, grams_per_us_ton
                )
                co2_refinery_metrictons, co2_internal_rate = calc_inventory(
                    context_gallons, session_gallons, co2_internal_rate, factor, delta_calc, grams_per_metric_ton
                )
                ch4_refinery_metrictons, ch4_internal_rate = calc_inventory(
                    context_gallons, session_gallons, ch4_internal_rate, factor, delta_calc, grams_per_metric_ton
                )
                n2o_refinery_metrictons, n2o_internal_rate = calc_inventory(
                    context_gallons, session_gallons, n2o_internal_rate, factor, delta_calc, grams_per_metric_ton
                )
                if na_key in sessions_dict:
                    oil_imports_change = (
                            (v['barrels_of_oil'] - sessions_dict[na_key][
                                'barrels_of_oil']) * energy_security_import_factor
                    )
                else:
                    oil_imports_change = v['barrels_of_oil']
                oil_imports_change_per_day = oil_imports_change / 365

        update_dict = {
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
