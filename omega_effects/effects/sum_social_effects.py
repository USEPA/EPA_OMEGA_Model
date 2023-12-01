"""

**OMEGA effects social effects module.**

----

**CODE**

"""
import pandas as pd


def calc_delta(dict_na, dict_a, arg):
    """
    Calculate the delta between sessions for a given attribute.

    Args:
        dict_na (dict): the no_action dictionary of data.
        dict_a (dict): the action dictionary of data.
        arg (str): the attribute for which the delta is sought.

    Returns:
        The delta between no_action and action sessions for the given attribute.

    """
    if dict_na:
        if dict_a:
            return dict_a[arg] - dict_na[arg]
        else:
            return - dict_na[arg]
    elif dict_a:
        return dict_a[arg]
    else:
        return 0


def calc_social_effects(batch_settings, costs_df, benefits_df, ghg_scope, calc_health_effects=False):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        costs_df (DataFrame): the annual, present and equivalent annualized values.
        benefits_df (DataFrame): the annual, present and equivalent annualized values.
        ghg_scope (str): which GHG benefits to use in net benefits, i.e., 'global', 'domestic'
        calc_health_effects (bool): pass True to use $/ton values to calculate health effects. If cost_factors_criteria.csv
        contains benefit per ton values, calc_health_effects will be True; blank values will result in the default False.

    Returns:
        A summary effects DataFrame with additional columns summing costs and benefits.

    """
    policies = costs_df['session_policy'].unique()
    action_policies = [policy for policy in policies if 'no_action' not in policy]

    dfc = costs_df.copy()
    dfc.set_index(pd.Series(zip(
        dfc['session_policy'],
        dfc['calendar_year'],
        dfc['series'],
        dfc['discount_rate'],
        dfc['reg_class_id'],
        dfc['in_use_fuel_id'],
        dfc['fueling_class'],
    )), inplace=True)

    dfb = benefits_df.copy()
    dfb.set_index(pd.Series(zip(
        dfb['session_policy'],
        dfb['calendar_year'],
        dfb['series'],
        dfb['discount_rate'],
        dfb['reg_class_id'],
        dfb['in_use_fuel_id'],
        dfb['fueling_class'],
    )), inplace=True)

    net_benefit_cost_attributes = [
        'fuel_pretax_cost_dollars',
        'vehicle_cost_dollars',
        'insurance_cost_dollars',
        'congestion_cost_dollars',
        'noise_cost_dollars',
        'maintenance_cost_dollars',
        'repair_cost_dollars',
        # 'refueling_cost_dollars',
    ]
    non_net_benefit_cost_attributes = [
        'fuel_retail_cost_dollars',
        'fuel_taxes_cost_dollars',
        'sales_taxes_cost_dollars',
        'battery_credit_dollars',
        'purchase_credit_dollars',
    ]
    non_emission_bens = [
        'energy_security_benefit_dollars',
        'drive_value_benefit_dollars',
        'refueling_benefit_dollars',
    ]
    sum_dict = {}
    # the if-else below is focused on benefits; costs are subtracted from benefits near the end to get net benefits
    if calc_health_effects:
        sum_num = 1
        for study in ['Wu', 'Pope']:
            for rate in [0.03, 0.07]:
                for scghg_rate in batch_settings.scghg_cost_factors.scghg_rates_as_strings:
                    sum_dict[sum_num] = {
                        'name': f'ghg{scghg_rate}_{ghg_scope}_cap{rate}_{study}_net_benefit_dollars',
                        'attributes': [
                            *non_emission_bens,
                            f'ghg_{ghg_scope}_{scghg_rate}_benefit_dollars',
                            f'cap_{study}_{rate}_benefit_dollars'
                        ]
                    }
                    sum_num += 1
    else:
        sum_num = 1
        for scghg_rate in batch_settings.scghg_cost_factors.scghg_rates_as_strings:
            sum_dict[sum_num] = {
                'name': f'ghg{scghg_rate}_{ghg_scope}_net_benefit_dollars',
                'attributes': [
                    *non_emission_bens,
                    f'ghg_{ghg_scope}_{scghg_rate}_benefit_dollars',
                ]
            }
            sum_num += 1

    costs_dict = dfc.to_dict(orient='index')

    no_action_keys = [k for k in costs_dict if costs_dict[k]['session_policy'] == 'no_action']
    action_keys = {}
    stranded_no_action_keys = {}
    for action in action_policies:
        action_keys[action] = [k for k in costs_dict if k not in no_action_keys]
        stranded_no_action_keys[action] = [
            k for k in no_action_keys if (action, k[1], k[2], k[3], k[4], k[5], k[6]) not in action_keys[action]
        ]
        # stranded_no_action_keys[action] = [k for k in no_action_keys if k not in action_keys[action]]

    delta_costs_dict = {}
    for action in action_policies:
        for key_a in action_keys[action]:
            policy, calendar_year, series, discount_rate, reg_class_id, in_use_fuel_id, fueling_class = key_a
            key_na = ('no_action', calendar_year, series, discount_rate, reg_class_id, in_use_fuel_id, fueling_class)

            costs_a = costs_dict[key_a]
            if key_na in costs_dict:
                costs_na = costs_dict[key_na]
            else:
                costs_na = None

            delta_costs_dict[key_a] = {}
            costs = 0
            for arg in non_net_benefit_cost_attributes:
                delta_costs_dict[key_a][arg] = calc_delta(costs_na, costs_a, arg)
            for arg in net_benefit_cost_attributes:
                delta_costs_dict[key_a][arg] = calc_delta(costs_na, costs_a, arg)
                costs += calc_delta(costs_na, costs_a, arg)
            delta_costs_dict[key_a]['sum_of_cost_dollars'] = costs

    for action in action_policies:
        for key_na in stranded_no_action_keys[action]:
            policy, calendar_year, series, discount_rate, reg_class_id, in_use_fuel_id, fueling_class = key_na
            key_a = (action, calendar_year, series, discount_rate, reg_class_id, in_use_fuel_id, fueling_class)
            costs_na = costs_dict[key_na]
            costs_a = None
            costs = 0
            for arg in non_net_benefit_cost_attributes:
                delta_costs_dict[key_a][arg] = calc_delta(costs_na, costs_a, arg)
            for arg in net_benefit_cost_attributes:
                delta_costs_dict[key_a][arg] = calc_delta(costs_na, costs_a, arg)
                costs += calc_delta(costs_na, costs_a, arg)
            delta_costs_dict[key_a]['sum_of_cost_dollars'] = costs

    delta_costs_df = pd.DataFrame.from_dict(delta_costs_dict, orient='index').reset_index(drop=False).rename(
        columns={'level_0': 'session_policy',
                 'level_1': 'calendar_year',
                 'level_2': 'series',
                 'level_3': 'discount_rate',
                 'level_4': 'reg_class_id',
                 'level_5': 'in_use_fuel_id',
                 'level_6': 'fueling_class',
                 })
    delta_costs_df.sort_values(by=[
        'session_policy', 'calendar_year', 'reg_class_id', 'in_use_fuel_id', 'fueling_class', 'series', 'discount_rate'
    ], inplace=True)

    # now resort the benefits DataFrame to be consistent with delta_costs_df to facilitate merge
    dfb.sort_values(by=[
        'session_policy', 'calendar_year', 'reg_class_id', 'in_use_fuel_id', 'fueling_class', 'series', 'discount_rate'
    ], inplace=True)
    dfb.reset_index(drop=True, inplace=True)
    summary_effects_df = dfb.merge(
        delta_costs_df,
        on=['session_policy', 'calendar_year', 'reg_class_id', 'in_use_fuel_id',
            'fueling_class', 'series', 'discount_rate'],
        how='left'
    )

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
