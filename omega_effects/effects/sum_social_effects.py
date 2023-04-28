"""

**OMEGA effects social effects module.**

----

**CODE**

"""

import pandas as pd


def calc_social_effects(costs_df, benefits_df, ghg_scope, calc_health_effects=False):
    """

    Args:
        costs_df (DataFrame): the annual, present and equivalent annualized values.
        benefits_df (DataFrame): the annual, present and equivalent annualized values.
        ghg_scope (str): which GHG benefits to use in net benefits, i.e., 'global', 'domestic'
        calc_health_effects (bool): pass True to use $/ton values to calculate health effects. If cost_factors_criteria.csv contains benefit per ton values, calc_health_effects will be True; blank values will result in the default False.

    Returns:
        A summary effects DataFrame with additional columns summing costs and benefits.

    """
    dfc = costs_df.copy()
    dfc.set_index(pd.Series(zip(
        dfc['session_policy'],
        dfc['calendar_year'],
        dfc['series'],
        dfc['discount_rate'],
        dfc['reg_class_id'],
        dfc['in_use_fuel_id'],
    )), inplace=True)

    dfb = benefits_df.copy()
    dfb.set_index(pd.Series(zip(
        dfb['session_policy'],
        dfb['calendar_year'],
        dfb['series'],
        dfb['discount_rate'],
        dfb['reg_class_id'],
        dfb['in_use_fuel_id'],
    )), inplace=True)

    net_benefit_cost_attributes = [
        'fuel_pretax_cost_dollars',
        'vehicle_cost_dollars',
        'congestion_cost_dollars',
        'noise_cost_dollars',
        'maintenance_cost_dollars',
        'repair_cost_dollars',
        'refueling_cost_dollars',
    ]
    non_net_benefit_cost_attributes = [
        'fuel_retail_cost_dollars',
        'fuel_taxes_cost_dollars',
        'battery_credit_dollars',
        'purchase_credit_dollars',
    ]
    non_emission_bens = [
        'energy_security_benefit_dollars',
        'drive_value_benefit_dollars',
    ]
    # the if-else below is focused on benefits; costs are subtracted from benefits near the end to get net benefits
    if calc_health_effects:
        sum_dict = {
            1: {'name': f'ghg5_{ghg_scope}_cap3_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_5.0_benefit_dollars',
                    'cap_Wu_3.0_benefit_dollars'
                ]},
            2: {'name': f'ghg3_{ghg_scope}_cap3_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_3.0_benefit_dollars',
                    'cap_Wu_3.0_benefit_dollars'
                ]},
            3: {'name': f'ghg25_{ghg_scope}_cap3_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_2.5_benefit_dollars',
                    'cap_Wu_3.0_benefit_dollars'
                ]},
            4: {'name': f'ghg395_{ghg_scope}_cap3_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_3.95_benefit_dollars',
                    'cap_Wu_3.0_benefit_dollars'
                ]},
            5: {'name': f'ghg5_{ghg_scope}_cap7_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_5.0_benefit_dollars',
                    'cap_Wu_7.0_benefit_dollars'
                ]},
            6: {'name': f'ghg3_{ghg_scope}_cap7_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_3.0_benefit_dollars',
                    'cap_Wu_7.0_benefit_dollars'
                ]},
            7: {'name': f'ghg25_{ghg_scope}_cap7_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_2.5_benefit_dollars',
                    'cap_Wu_7.0_benefit_dollars'
                ]},
            8: {'name': f'ghg395_{ghg_scope}_cap7_Wu_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_3.95_benefit_dollars',
                    'cap_Wu_7.0_benefit_dollars'
                ]},
            9: {'name': f'ghg5_{ghg_scope}_cap3_Pope_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_5.0_benefit_dollars',
                    'cap_Pope_3.0_benefit_dollars'
                ]},
            10: {'name': f'ghg3_{ghg_scope}_cap3_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_3.0_benefit_dollars',
                     'cap_Pope_3.0_benefit_dollars'
                 ]},
            11: {'name': f'ghg25_{ghg_scope}_cap3_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_2.5_benefit_dollars',
                     'cap_Pope_3.0_benefit_dollars'
                 ]},
            12: {'name': f'ghg395_{ghg_scope}_cap3_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_3.95_benefit_dollars',
                     'cap_Pope_3.0_benefit_dollars'
                 ]},
            13: {'name': f'ghg5_{ghg_scope}_cap7_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_5.0_benefit_dollars',
                     'cap_Pope_7.0_benefit_dollars'
                 ]},
            14: {'name': f'ghg3_{ghg_scope}_cap7_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_3.0_benefit_dollars',
                     'cap_Pope_7.0_benefit_dollars'
                 ]},
            15: {'name': f'ghg25_{ghg_scope}_cap7_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_2.5_benefit_dollars',
                     'cap_Pope_7.0_benefit_dollars'
                 ]},
            16: {'name': f'ghg395_{ghg_scope}_cap7_Pope_net_benefit_dollars',
                 'attributes': [
                     *non_emission_bens,
                     f'ghg_{ghg_scope}_3.95_benefit_dollars',
                     'cap_Pope_7.0_benefit_dollars'
                 ]},
        }
    else:
        sum_dict = {
            1: {'name': f'ghg5_{ghg_scope}_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_5.0_benefit_dollars'
                ]},
            2: {'name': f'ghg3_{ghg_scope}_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_3.0_benefit_dollars'
                ]},
            3: {'name': f'ghg25_{ghg_scope}_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_2.5_benefit_dollars'
                ]},
            4: {'name': f'ghg395_{ghg_scope}_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_3.95_benefit_dollars'
                ]},
        }

    costs_dict = dfc.to_dict(orient='index')
    delta_costs_dict = dict()
    for k, v in costs_dict.items():
        session_policy, calendar_year, series, discount_rate, reg_class_id, in_use_fuel_id = k
        if session_policy != 'no_action':
            no_action_key = ('no_action', calendar_year, series, discount_rate, reg_class_id, in_use_fuel_id)
            costs_na = costs_dict[no_action_key]
            costs_a = costs_dict[k]

            delta_costs_dict[k] = dict()
            costs = 0
            for arg in non_net_benefit_cost_attributes:
                delta_costs_dict[k][arg] = costs_a[arg] - costs_na[arg]
            for arg in net_benefit_cost_attributes:
                delta_costs_dict[k][arg] = costs_a[arg] - costs_na[arg]
                costs += costs_a[arg] - costs_na[arg]
            delta_costs_dict[k]['sum_of_cost_dollars'] = costs

    delta_costs_df = pd.DataFrame.from_dict(delta_costs_dict, orient='index').reset_index(drop=True)
    dfb.reset_index(drop=True, inplace=True)
    summary_effects_df = pd.concat([dfb, delta_costs_df], axis=1)

    # sum benefits per the if-else dictionaries above and then subtract costs to get net benefits
    for sum_num in sum_dict:
        new_col = sum_dict[sum_num]['name']
        summary_effects_df.insert(
            len(summary_effects_df.columns),
            new_col,
            summary_effects_df[[item for item in sum_dict[sum_num]['attributes']]].sum(axis=1)
        )
        summary_effects_df[new_col] = summary_effects_df[new_col] - summary_effects_df['sum_of_cost_dollars']

    return summary_effects_df
