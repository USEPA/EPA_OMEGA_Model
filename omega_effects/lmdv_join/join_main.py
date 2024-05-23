"""

**OMEGA effects join main.**

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.file_id_and_save import add_id_to_csv


def join_results(set_paths, batch_settings, file_id_string, effects_log):
    """

    Args:
        set_paths: An instance of the SetPaths class.
        batch_settings: An instance of the BatchSettings class.
        file_id_string (str): The search string in the filename needed.
        effects_log: An instance of the EffectsLog class.

    Returns:
        Nothing, but it joins LD effects with MD effects and saves the resultant LMDV effects.

    """
    effects_log.logwrite(f'\nJoining {file_id_string} files')

    ld_file = batch_settings.find_file(set_paths.path_of_run_folder, file_id_string, effects_log, 'ld')
    df_ld = read_input_file(ld_file, effects_log, skiprows=1)

    md_file = batch_settings.find_file(set_paths.path_of_run_folder, file_id_string, effects_log, 'md')
    df_md = read_input_file(md_file, effects_log, skiprows=1)

    # join no_action sessions
    no_action_ld = df_ld.loc[df_ld['session_policy'] == 'no_action', :]
    no_action_md = df_md.loc[df_md['session_policy'] == 'no_action', :]

    df_join = pd.concat([no_action_ld, no_action_md], axis=0, ignore_index=True)

    # join action sessions
    joins = batch_settings.joins_max
    for join in range(1, joins):

        ld_session_policy = batch_settings.join_dict['ld', join]['session_policy']
        md_session_policy = batch_settings.join_dict['md', join]['session_policy']

        ld_session_name = batch_settings.join_dict['ld', join]['session_name']
        md_session_name = batch_settings.join_dict['md', join]['session_name']

        action_ld = df_ld.loc[df_ld['session_name'] == ld_session_name, :]
        action_md = df_md.loc[df_md['session_name'] == md_session_name, :]

        # ensure that session policy entries are consistent with the join settings
        action_ld.loc[action_ld['session_name'] == ld_session_name, 'session_policy'] = ld_session_policy
        action_md.loc[action_md['session_name'] == md_session_name, 'session_policy'] = md_session_policy

        df_join = pd.concat([df_join, action_ld, action_md], axis=0, ignore_index=True)

    if file_id_string == 'safety_effects_by_body_style_summary':
        df_join = calc_annual_avg_safety_effects_by_body_style(df_join)

    df_join.to_csv(
        set_paths.path_of_run_folder / f'{batch_settings.start_time_readable}_{file_id_string}_lmdv.csv', index=False)
    output_file_id_info = [f'{set_paths.path_of_run_folder}']
    add_id_to_csv(
        set_paths.path_of_run_folder / f'{batch_settings.start_time_readable}_{file_id_string}_lmdv.csv',
        output_file_id_info
    )


def calc_annual_avg_safety_effects_by_body_style(input_df):
    """

    Args:
        input_df: DataFrame of safety effects by vehicle.

    Returns:
        A DataFrame of safety effects by calendar year and body style.

    """
    attributes = [col for col in input_df.columns
                  if ('vmt' in col or 'vmt_' in col)
                  and '_vmt' not in col]
    attribute_keys_for_weighting = ['lbs']
    attributes_to_weight = []
    for attribute in attribute_keys_for_weighting:
        for col in input_df:
            if attribute in col:
                attributes_to_weight.append(col)

    # weight appropriate columns by registered_count to work toward weighted averages
    temp_df = pd.DataFrame()
    wtd_attributes = []
    for attribute in attributes_to_weight:
        wtd_attributes.append(f'wtd_avg_{attribute}')
        s = pd.Series(input_df['registered_count'] * input_df[attribute], name=f'wtd_avg_{attribute}')
        temp_df = pd.concat([temp_df, s], axis=1)

    cols = ['session_policy', 'calendar_year', 'body_style',
            'registered_count', 'base_fatalities', 'session_fatalities'
            ]
    for attribute in attributes:
        cols.append(attribute)
    df = input_df[cols]
    df = pd.concat([df, temp_df], axis=1)

    # groupby calendar year, body style
    groupby_cols = ['session_policy', 'calendar_year', 'body_style']
    return_df = df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    for attribute in wtd_attributes:
        return_df[attribute] = return_df[attribute] / return_df['registered_count']

    return return_df
