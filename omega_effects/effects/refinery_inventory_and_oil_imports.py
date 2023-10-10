from omega_effects.effects.physical_effects import get_inputs_for_effects


def get_refinery_data(session_settings, calendar_year):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        calendar_year (int): The calendar year for which a refinery emission factors are needed.

    Returns:
        A list of refinery emission rates as specified in the emission_rates list for the given calendar year.

    """
    args = (
        'voc_grams_per_gallon',
        'nox_grams_per_gallon',
        'pm25_grams_per_gallon',
        'sox_grams_per_gallon',
        'co_grams_per_gallon',
        'co2_grams_per_gallon',
        'n2o_grams_per_gallon',
        'fuel_reduction_leading_to_reduced_domestic_refining',
    )

    return session_settings.refinery_data.get_data(calendar_year, args)


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


def calc_refinery_inventory_and_oil_imports(batch_settings, session_settings, no_action_dict, action_dict=None):
    """

    Args:
        batch_settings: an instance of the BatchSettings class
        session_settings: an instance of the SessionSettings class
        no_action_dict (dict): the no_action physical effects
        action_dict (dict): the action physical effects, if the current session is an action session

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

    if action_dict is None:
        
        for na in no_action_dict.values():

            calendar_year = na['calendar_year']

            if na[gallons_arg] > 0:

                (voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co_ref_rate, co2_ref_rate, n2o_ref_rate,
                 fuel_reduction_leading_to_reduced_domestic_refining
                 ) = get_refinery_data(session_settings, calendar_year)

                na_gallons = na[gallons_arg]
                # na['domestic_refined_gallons'] = gallons_refined
                na['voc_refinery_ustons'] = na_gallons * voc_ref_rate / grams_per_us_ton
                na['co_refinery_ustons'] = na_gallons * co_ref_rate / grams_per_us_ton
                na['nox_refinery_ustons'] = na_gallons * nox_ref_rate / grams_per_us_ton
                na['pm25_refinery_ustons'] = na_gallons * pm25_ref_rate / grams_per_us_ton
                na['sox_refinery_ustons'] = na_gallons * sox_ref_rate / grams_per_us_ton

                na['co2_refinery_metrictons'] = na_gallons * co2_ref_rate / grams_per_metric_ton
                # na['ch4_refinery_metrictons'] = na_gallons * ch4_ref_rate / grams_per_metric_ton
                na['n2o_refinery_metrictons'] = na_gallons * n2o_ref_rate / grams_per_metric_ton

        return no_action_dict

    else:

        for k, na in no_action_dict.items():

            na_gallons, na_oil_bbls, name, veh_id, base_veh_id, calendar_year, age = (
                na[gallons_arg], na['barrels_of_oil'],
                na['name'], na['vehicle_id'], na['base_year_vehicle_id'], na['calendar_year'], na['age']
            )
            (voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate, co_ref_rate, co2_ref_rate, n2o_ref_rate,
             fuel_reduction_leading_to_reduced_domestic_refining
             ) = get_refinery_data(session_settings, calendar_year)

            refinery_factor = fuel_reduction_leading_to_reduced_domestic_refining
            energy_security_import_factor = get_energysecurity_cf(batch_settings, calendar_year)

            a_gallons = oil_imports_change = 0
            a = None
            if na_gallons != 0:
                if k in action_dict:
                    a = action_dict[k]
                    gallons_reduced = na_gallons - a[gallons_arg]
                    a_gallons = na_gallons - gallons_reduced * refinery_factor
                    oil_imports_change = (a['barrels_of_oil'] - na_oil_bbls) * energy_security_import_factor
                elif name and base_veh_id and calendar_year and age in action_dict.values():
                    a = [v for v in action_dict.values()
                         if v['name'] == name
                         and v['base_year_vehicle_id'] == base_veh_id
                         and v['calendar_year'] == calendar_year
                         and v['age'] == age][0]
                    gallons_reduced = na_gallons - a[gallons_arg]
                    a_gallons = na_gallons - gallons_reduced * refinery_factor
                    oil_imports_change = (a['barrels_of_oil'] - na_oil_bbls) * energy_security_import_factor
                else:
                    pass

                oil_imports_change_per_day = oil_imports_change / 365

                if a:
                    a['session_policy'] = session_settings.session_policy
                    a['reg_class_id'] = na['reg_class_id']
                    a['in_use_fuel_id'] = na['in_use_fuel_id']
                    a['fueling_class'] = na['fueling_class']
                    # a['domestic_refined_gallons'] = a_gallons_refined
                    a['voc_refinery_ustons'] = a_gallons * voc_ref_rate / grams_per_us_ton
                    a['co_refinery_ustons'] = a_gallons * co_ref_rate / grams_per_us_ton
                    a['nox_refinery_ustons'] = a_gallons * nox_ref_rate / grams_per_us_ton
                    a['pm25_refinery_ustons'] = a_gallons * pm25_ref_rate / grams_per_us_ton
                    a['sox_refinery_ustons'] = a_gallons * sox_ref_rate / grams_per_us_ton

                    a['co2_refinery_metrictons'] = a_gallons * co2_ref_rate / grams_per_metric_ton
                    # a['ch4_refinery_metrictons'] = a_gallons * ch4_ref_rate / grams_per_metric_ton
                    a['n2o_refinery_metrictons'] = a_gallons * n2o_ref_rate / grams_per_metric_ton

                    a['change_in_barrels_of_oil_imports'] = oil_imports_change
                    a['change_in_barrels_of_oil_imports_per_day'] = oil_imports_change_per_day

        return action_dict
