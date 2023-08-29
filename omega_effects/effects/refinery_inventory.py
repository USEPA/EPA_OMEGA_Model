from omega_effects.effects.physical_effects import get_inputs_for_effects


def get_refinery_emission_rate(session_settings, calendar_year):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
        calendar_year (int): The calendar year for which a refinery emission factors are needed.

    Returns:
        A list of refinery emission rates as specified in the emission_rates list for the given calendar year.

    """
    emission_rates = (
        'voc_grams_per_gallon',
        'nox_grams_per_gallon',
        'pm25_grams_per_gallon',
        'sox_grams_per_gallon',
    )

    return session_settings.emission_rates_refinery.get_emission_rate(session_settings, calendar_year, emission_rates)


def calc_refinery_inventory(batch_settings, session_settings, no_action_dict, action_dict=None):
    """

    Args:
        batch_settings: an instance of the BatchSettings class
        session_settings: an instance of the SessionSettings class
        no_action (dict): the no_action physical effects
        action_dict (dict): the action physical effects, if the current session is an action session

    Returns:
        The passed physical effects dictionary with refinery inventories included

    Note:
        For action sessions, both the action and no_action physical effects are needed so that the fuel reductions
        can be calculated; reduced fuel may or may not result in less refining depending on the
        general_inputs_for_effects input setting "fuel_reduction_leading_to_reduced_domestic_refining"

    """
    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, \
        diesel_energy_density_ratio, fuel_reduction_leading_to_reduced_domestic_refining = \
        get_inputs_for_effects(batch_settings)

    co_ref_rate = co2_ref_rate = ch4_ref_rate = n2o_ref_rate = pure_share = 0

    if action_dict is None:
        
        for na in no_action_dict.values():

            gallons = na['fuel_consumption_gallons']
            calendar_year = na['calendar_year']

            if gallons > 0:
                fuel_dict = eval(na['in_use_fuel_id'])
                fuel = [item for item in fuel_dict.keys()][0]
                if 'gasoline' in fuel:
                    pure_share = e0_share
                else:
                    pure_share = 1
            
                voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate \
                    = get_refinery_emission_rate(session_settings, calendar_year)
                ref_factor = pure_share

                na['voc_refinery_ustons'] = gallons * voc_ref_rate * ref_factor / grams_per_us_ton
                na['co_refinery_ustons'] = gallons * co_ref_rate * ref_factor / grams_per_us_ton
                na['nox_refinery_ustons'] = gallons * nox_ref_rate * ref_factor / grams_per_us_ton
                na['pm25_refinery_ustons'] = gallons * pm25_ref_rate * ref_factor / grams_per_us_ton
                na['sox_refinery_ustons'] = gallons * sox_ref_rate * ref_factor / grams_per_us_ton

                na['co2_refinery_metrictons'] = gallons * co2_ref_rate * ref_factor / grams_per_metric_ton
                na['ch4_refinery_metrictons'] = gallons * ch4_ref_rate * ref_factor / grams_per_metric_ton
                na['n2o_refinery_metrictons'] = gallons * n2o_ref_rate * ref_factor / grams_per_metric_ton

        return no_action_dict

    else:

        for k, na in no_action_dict.items():

            na_gallons, name, veh_id, base_veh_id, calendar_year, age \
                = (na['fuel_consumption_gallons'], na['name'], na['vehicle_id'], na['base_year_vehicle_id'],
                   na['calendar_year'], na['age'])

            # if na_gallons != 0:
            fuel_dict = eval(na['in_use_fuel_id'])
            fuel = [item for item in fuel_dict.keys()][0]
            if 'gasoline' in fuel:
                pure_share = e0_share
            else:
                pure_share = 1

            voc_ref_rate, nox_ref_rate, pm25_ref_rate, sox_ref_rate \
                = get_refinery_emission_rate(session_settings, calendar_year)
            a_gallons = 0
            a = None
            if na_gallons != 0:
                if k in action_dict:
                    a = action_dict[k]
                    a_gallons = a['fuel_consumption_gallons']
                elif name and base_veh_id and calendar_year and age in action_dict.values():
                    a = [v for v in action_dict.values()
                         if v['name'] == name
                         and v['base_year_vehicle_id'] == base_veh_id
                         and v['calendar_year'] == calendar_year
                         and v['age'] == age][0]
                    a_gallons = a['fuel_consumption_gallons']
                else:
                    pass

                gallons_reduced = na_gallons - a_gallons
                ref_factor = fuel_reduction_leading_to_reduced_domestic_refining * pure_share

                if a:
                    a['session_policy'] = session_settings.session_policy
                    a['reg_class_id'] = na['reg_class_id']
                    a['in_use_fuel_id'] = na['in_use_fuel_id']
                    a['fueling_class'] = na['fueling_class']
                    a['voc_refinery_ustons'] \
                        = na['voc_refinery_ustons'] - gallons_reduced * voc_ref_rate * ref_factor / grams_per_us_ton
                    a['co_refinery_ustons'] \
                        = na['co_refinery_ustons'] - gallons_reduced * co_ref_rate * ref_factor / grams_per_us_ton
                    a['nox_refinery_ustons'] \
                        = na['nox_refinery_ustons'] - gallons_reduced * nox_ref_rate * ref_factor / grams_per_us_ton
                    a['pm25_refinery_ustons'] \
                        = na['pm25_refinery_ustons'] - gallons_reduced * pm25_ref_rate * ref_factor / grams_per_us_ton
                    a['sox_refinery_ustons'] \
                        = na['sox_refinery_ustons'] - gallons_reduced * sox_ref_rate * ref_factor / grams_per_us_ton

                    a['co2_refinery_metrictons'] \
                        = na['co2_refinery_metrictons'] - gallons_reduced * co2_ref_rate * ref_factor / grams_per_metric_ton
                    a['ch4_refinery_metrictons'] \
                        = na['ch4_refinery_metrictons'] - gallons_reduced * ch4_ref_rate * ref_factor / grams_per_metric_ton
                    a['n2o_refinery_metrictons'] \
                        = na['n2o_refinery_metrictons'] - gallons_reduced * n2o_ref_rate * ref_factor / grams_per_metric_ton

        return action_dict
