import pandas as pd


def calc_social_costs(costs_df):
    """

    Args:
        costs_df: DataFrame; the annual values, present values and annualized values dataframe.

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
        'driving_cost_dollars',
    ]
    ghg5_criteria3_cost_attributes = [
        'ghg_global_5.0_cost_dollars',
        'criteria_3.0_cost_dollars',
    ]
    ghg3_criteria3_cost_attributes = [
        'ghg_global_3.0_cost_dollars',
        'criteria_3.0_cost_dollars',
    ]
    ghg25_criteria3_cost_attributes = [
        'ghg_global_2.5_cost_dollars',
        'criteria_3.0_cost_dollars',
    ]
    ghg395_criteria3_cost_attributes = [
        'ghg_global_3.95_cost_dollars',
        'criteria_3.0_cost_dollars',
    ]
    ghg5_criteria7_cost_attributes = [
        'ghg_global_5.0_cost_dollars',
        'criteria_7.0_cost_dollars',
    ]
    ghg3_criteria7_cost_attributes = [
        'ghg_global_3.0_cost_dollars',
        'criteria_7.0_cost_dollars',
    ]
    ghg25_criteria7_cost_attributes = [
        'ghg_global_2.5_cost_dollars',
        'criteria_7.0_cost_dollars',
    ]
    ghg395_criteria7_cost_attributes = [
        'ghg_global_3.95_cost_dollars',
        'criteria_7.0_cost_dollars',
    ]

    non_pollution_costs = df[[item for item in non_pollution_cost_attributes]].sum(axis=1)

    ghg5_criteria3_cost_dollars \
        = pd.Series(df[[item for item in ghg5_criteria3_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg5_criteria3')
    ghg3_criteria3_cost_dollars \
        = pd.Series(df[[item for item in ghg3_criteria3_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg3_criteria3')
    ghg25_criteria3_cost_dollars \
        = pd.Series(df[[item for item in ghg25_criteria3_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg25_criteria3')
    ghg395_criteria3_cost_dollars \
        = pd.Series(df[[item for item in ghg395_criteria3_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg395_criteria3')

    ghg5_criteria7_cost_dollars \
        = pd.Series(df[[item for item in ghg5_criteria7_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg5_criteria7')
    ghg3_criteria7_cost_dollars \
        = pd.Series(df[[item for item in ghg3_criteria7_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg3_criteria7')
    ghg25_criteria7_cost_dollars \
        = pd.Series(df[[item for item in ghg25_criteria7_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg25_criteria7')
    ghg395_criteria7_cost_dollars \
        = pd.Series(df[[item for item in ghg395_criteria7_cost_attributes]].sum(axis=1) + non_pollution_costs,
                    name='social_cost_dollars_ghg395_criteria7')

    df = pd.concat([
        df,
        ghg5_criteria3_cost_dollars,
        ghg3_criteria3_cost_dollars,
        ghg25_criteria3_cost_dollars,
        ghg395_criteria3_cost_dollars,
        ghg5_criteria7_cost_dollars,
        ghg3_criteria7_cost_dollars,
        ghg25_criteria7_cost_dollars,
        ghg395_criteria7_cost_dollars,
    ], axis=1, ignore_index=False
    )

    return df
