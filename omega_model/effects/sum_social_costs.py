import pandas as pd


def calc_social_costs(costs_df, calc_health_effects=False):
    """

    Args:
        costs_df: DataFrame; the annual values, present values and annualized values dataframe.
        calc_health_effects: boolean; pass True to use $/ton values to calculate health effects.

    Returns:
        The passed dataframe with additional columns summing the non-pollution related and pollution related cost
        effects.

    """
    df = costs_df.copy()

    non_pollution_cost_attributes = [
        'vehicle_cost_dollars',
        'fuel_pretax_cost_dollars',
        'energy_security_cost_dollars',
        'congestion_cost_dollars',
        'noise_cost_dollars',
        'maintenance_cost_dollars',
        'repair_cost_dollars',
        'refueling_cost_dollars',
        'value_of_rebound_vmt_cost_dollars',
    ]
    if calc_health_effects:
        sum_dict = {
            1: {'name': 'social_cost_dollars_ghg5_criteria3_low',
                'attributes': ['ghg_global_5.0_cost_dollars', 'criteria_low_3.0_cost_dollars']},
            2: {'name': 'social_cost_dollars_ghg3_criteria3_low',
                'attributes': ['ghg_global_3.0_cost_dollars', 'criteria_low_3.0_cost_dollars']},
            3: {'name': 'social_cost_dollars_ghg25_criteria3_low',
                'attributes': ['ghg_global_2.5_cost_dollars', 'criteria_low_3.0_cost_dollars']},
            4: {'name': 'social_cost_dollars_ghg395_criteria3_low',
                'attributes': ['ghg_global_3.95_cost_dollars', 'criteria_low_3.0_cost_dollars']},
            5: {'name': 'social_cost_dollars_ghg5_criteria7_low',
                'attributes': ['ghg_global_5.0_cost_dollars', 'criteria_low_7.0_cost_dollars']},
            6: {'name': 'social_cost_dollars_ghg3_criteria7_low',
                'attributes': ['ghg_global_3.0_cost_dollars', 'criteria_low_7.0_cost_dollars']},
            7: {'name': 'social_cost_dollars_ghg25_criteria7_low',
                'attributes': ['ghg_global_2.5_cost_dollars', 'criteria_low_7.0_cost_dollars']},
            8: {'name': 'social_cost_dollars_ghg395_criteria7_low',
                'attributes': ['ghg_global_3.95_cost_dollars', 'criteria_low_7.0_cost_dollars']},
            9: {'name': 'social_cost_dollars_ghg5_criteria3_high',
                'attributes': ['ghg_global_5.0_cost_dollars', 'criteria_high_3.0_cost_dollars']},
            10: {'name': 'social_cost_dollars_ghg3_criteria3_high',
                 'attributes': ['ghg_global_3.0_cost_dollars', 'criteria_high_3.0_cost_dollars']},
            11: {'name': 'social_cost_dollars_ghg25_criteria3_high',
                 'attributes': ['ghg_global_2.5_cost_dollars', 'criteria_high_3.0_cost_dollars']},
            12: {'name': 'social_cost_dollars_ghg395_criteria3_high',
                 'attributes': ['ghg_global_3.95_cost_dollars', 'criteria_high_3.0_cost_dollars']},
            13: {'name': 'social_cost_dollars_ghg5_criteria7_high',
                 'attributes': ['ghg_global_5.0_cost_dollars', 'criteria_high_7.0_cost_dollars']},
            14: {'name': 'social_cost_dollars_ghg3_criteria7_high',
                 'attributes': ['ghg_global_3.0_cost_dollars', 'criteria_high_7.0_cost_dollars']},
            15: {'name': 'social_cost_dollars_ghg25_criteria7_high',
                 'attributes': ['ghg_global_2.5_cost_dollars', 'criteria_high_7.0_cost_dollars']},
            16: {'name': 'social_cost_dollars_ghg395_criteria7_high',
                 'attributes': ['ghg_global_3.95_cost_dollars', 'criteria_high_7.0_cost_dollars']},
        }
    else:
        sum_dict = {
            1: {'name': 'social_cost_dollars_ghg5',
                'attributes': ['ghg_global_5.0_cost_dollars']},
            2: {'name': 'social_cost_dollars_ghg3',
                'attributes': ['ghg_global_3.0_cost_dollars']},
            3: {'name': 'social_cost_dollars_ghg25',
                'attributes': ['ghg_global_2.5_cost_dollars']},
            4: {'name': 'social_cost_dollars_ghg395',
                'attributes': ['ghg_global_3.95_cost_dollars']},
        }

    non_pollution_costs = df[[item for item in non_pollution_cost_attributes]].sum(axis=1)

    series_dict = dict()

    for sum_num in sum_dict:
        series_dict[sum_num] \
            = pd.Series(df[[item for item in sum_dict[sum_num]['attributes']]].sum(axis=1) + non_pollution_costs,
                        name=sum_dict[sum_num]['name'])

    for k, v in series_dict.items():
        df = pd.concat([df, v], axis=1, ignore_index=False)

    return df
