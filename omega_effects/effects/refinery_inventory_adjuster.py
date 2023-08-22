from omega_effects.effects.physical_effects import get_inputs_for_effects


def calc_adjusments(batch_settings, session_settings, no_action_dict, action_dict):

    fuel_reduction_leading_to_reduced_domestic_refining \
        = get_inputs_for_effects(batch_settings, 'fuel_reduction_leading_to_reduced_domestic_refining')

    args = [arg for arg in action_dict.values()[0] if 'refinery_ustons' in arg or 'refinery_metrictons' in arg]

    for k, v in action_dict.items():

        action_gallons = v['fuel_consumption_gallons']

        if action_gallons > 0:

            name = v['name']
            calendar_year = v['calendar_year']

            no_action = \
                [v for v in no_action_dict.values() if v['name'] == name and v['calendar_year'] == calendar_year][0]
            no_action_gallons = no_action['fuel_consumption_gallons']

            gallons_reduced = no_action_gallons - action_gallons

            for arg in args:

                no_action_arg = no_action[arg]
                action_arg_unadj = v[arg]
                rate = action_arg_unadj / action_gallons
                rate_name = [name for name in session_settings.emission_rates_refinery.rate_names if ]
                rate = session_settings.emission_rates_refinery.deets[(calendar_year, rate_name)]
                action_arg_adj = no_action_arg - gallons_reduced * fuel_reduction_leading_to_reduced_domestic_refining

