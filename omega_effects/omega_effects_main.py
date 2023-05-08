"""

**OMEGA effects main.**

----

**CODE**

"""
import sys
import shutil
import pandas as pd

from time import time
from datetime import datetime

from omega_effects.set_paths import SetPaths

from omega_effects.batch_settings import BatchSettings
from omega_effects.session_settings import SessionSettings

from omega_effects.general.effects_log import EffectsLog
from omega_effects.general.general_functions import copy_files
from omega_effects.general.file_id_and_save import add_id_to_csv, save_file

from omega_effects.effects.vmt_adjustments import AdjustmentsVMT
from omega_effects.effects.context_fuel_cost_per_mile import calc_fuel_cost_per_mile
from omega_effects.effects.safety_effects import calc_safety_effects, calc_legacy_fleet_safety_effects, calc_annual_avg_safety_effects
from omega_effects.effects.physical_effects import calc_physical_effects, calc_legacy_fleet_physical_effects, \
    calc_annual_physical_effects, calc_period_consumer_physical_view
from omega_effects.effects.cost_effects import calc_cost_effects, calc_annual_cost_effects, calc_period_consumer_view

from omega_effects.effects.discounting import Discounting
from omega_effects.effects.benefits import calc_benefits
from omega_effects.effects.sum_social_effects import calc_social_effects


def main():
    """

    Main effects code.

    """
    set_paths = SetPaths()
    batch_settings_file = set_paths.path_of_batch_settings_csv()

    start_time = time()
    start_time_readable = datetime.now().strftime('%Y%m%d_%H%M%S')

    batch_settings = BatchSettings()
    batch_settings.init_from_file(batch_settings_file)
    batch_settings.get_batch_folder_and_name()
    batch_settings.get_run_id()

    path_of_run_folder, path_of_code_folder = \
        set_paths.create_output_paths(
            batch_settings.path_outputs, batch_settings.batch_name, start_time_readable, batch_settings.run_id
        )

    effects_log = EffectsLog()
    effects_log.init_logfile(path_of_run_folder)
    effects_log.logwrite(f'EPA OMEGA Model Effects Module started at {start_time_readable}\n')

    batch_settings.get_runtime_options(effects_log)
    batch_settings.get_batch_settings(effects_log)
    batch_settings.init_batch_classes(effects_log)

    shutil.copy2(batch_settings_file, path_of_run_folder)
    set_paths.copy_code_to_destination(path_of_code_folder)

    if batch_settings.save_input_files:
        copy_files(batch_settings.inputs_filelist, path_of_run_folder / 'batch_inputs')

    # build legacy fleet which is used for the entire batch ____________________________________________________________
    effects_log.logwrite('\nBuilding legacy fleet for the batch')
    try:
        batch_settings.legacy_fleet.build_legacy_fleet_for_analysis(batch_settings)
    except Exception as e:
        effects_log.logwrite(f'{e}')
        sys.exit()

    # context fuel cost per mile and vmt adjustments ___________________________________________________________________
    session_settings = SessionSettings()
    session_settings.get_context_session_settings(batch_settings, effects_log)
    if batch_settings.save_input_files:
        copy_files(session_settings.inputs_filelist, path_of_run_folder / 'context_inputs')

    effects_log.logwrite('\nCalculating context vmt adjustments and context fuel cost per mile')
    vmt_adjustments_context = AdjustmentsVMT()
    vmt_adjustments_context.calc_vmt_adjustments(batch_settings, session_settings)

    context_fuel_cpm_dict = calc_fuel_cost_per_mile(batch_settings, session_settings)
    if batch_settings.save_context_fuel_cost_per_mile_file:
        effects_log.logwrite(f'Saving context fuel cost per mile file')
        context_fuel_cpm_df = pd.DataFrame.from_dict(context_fuel_cpm_dict, orient='index').reset_index(drop=True)
        save_file(session_settings, context_fuel_cpm_df, path_of_run_folder, 'context_fuel_cost_per_mile',
                  effects_log, extension=batch_settings.file_format)

    # loop thru sessions to calc safety effects, physical effects, cost effects for each _______________________________
    annual_safety_effects_df = pd.DataFrame()
    annual_physical_effects_df = pd.DataFrame()
    annual_cost_effects_df = pd.DataFrame()
    my_lifetime_physical_effects_df = pd.DataFrame()
    my_lifetime_cost_effects_df = pd.DataFrame()

    effects_log.logwrite(f'\nStarting work on sessions')
    for session_num in batch_settings.session_dict:

        session_settings = SessionSettings()
        session_settings.get_session_settings(batch_settings, session_num, effects_log)
        session_name = session_settings.session_name
        if batch_settings.save_input_files:
            copy_files(session_settings.inputs_filelist, path_of_run_folder / f'{session_name}_inputs')

        # vmt adjustments to vehicle annual data _______________________________________________________________________
        effects_log.logwrite(f'\nCalculating vmt adjustments for session {session_name}')
        vmt_adjustments_session = AdjustmentsVMT()
        vmt_adjustments_session.calc_vmt_adjustments(batch_settings, session_settings)

        effects_log.logwrite(f'\nAdjusting analysis fleet VMT for {session_name}')
        session_settings.vehicle_annual_data.adjust_vad(batch_settings, session_settings,
                                                        vmt_adjustments_session, context_fuel_cpm_dict)

        effects_log.logwrite(f'\nAdjusting legacy fleet VMT and stock for {session_name}')
        batch_settings.legacy_fleet.adjust_legacy_fleet_stock_and_vmt(batch_settings, vmt_adjustments_session)

        # safety effects _______________________________________________________________________________________________
        effects_log.logwrite(f'\nCalculating legacy fleet safety effects for {session_name}')
        legacy_fleet_safety_effects_dict = calc_legacy_fleet_safety_effects(batch_settings, session_settings)

        effects_log.logwrite(f'Calculating analysis fleet safety effects for {session_name}')
        analysis_fleet_safety_effects_dict = calc_safety_effects(batch_settings, session_settings)

        session_safety_effects_dict = {**analysis_fleet_safety_effects_dict, **legacy_fleet_safety_effects_dict}

        session_safety_effects_df = \
            pd.DataFrame.from_dict(session_safety_effects_dict, orient='index').reset_index(drop=True)

        if batch_settings.save_vehicle_safety_effects_files:
            effects_log.logwrite(f'Saving safety effects file for {session_name}')
            save_file(session_settings, session_safety_effects_df, path_of_run_folder, 'safety_effects',
                      effects_log, extension=batch_settings.file_format)

        effects_log.logwrite(f'\nCalculating annual safety effects for {session_name}')
        session_annual_safety_effects_df = calc_annual_avg_safety_effects(session_safety_effects_df)

        # create an annual_safety_effects_df
        annual_safety_effects_df \
            = pd.concat([annual_safety_effects_df, session_annual_safety_effects_df], axis=0, ignore_index=True)
        annual_safety_effects_df.reset_index(inplace=True, drop=True)

        # physical effects _____________________________________________________________________________________________
        effects_log.logwrite(f'\nCalculating analysis fleet physical effects for {session_name}')
        analysis_fleet_physical_effects_dict \
            = calc_physical_effects(batch_settings, session_settings, analysis_fleet_safety_effects_dict)

        effects_log.logwrite(f'Calculating legacy fleet physical effects for {session_name}')
        legacy_fleet_physical_effects_dict \
            = calc_legacy_fleet_physical_effects(batch_settings, session_settings, legacy_fleet_safety_effects_dict)

        session_physical_effects_dict = {**analysis_fleet_physical_effects_dict, **legacy_fleet_physical_effects_dict}

        session_physical_effects_df = \
            pd.DataFrame.from_dict(session_physical_effects_dict, orient='index').reset_index(drop=True)

        if batch_settings.save_vehicle_physical_effects_files:
            effects_log.logwrite(f'Saving physical effects file for {session_name}')
            save_file(session_settings, session_physical_effects_df, path_of_run_folder, 'physical_effects', effects_log,
                      extension=batch_settings.file_format)

        effects_log.logwrite(f'\nCalculating annual physical effects for {session_name}')
        session_annual_physical_effects_df = calc_annual_physical_effects(batch_settings, session_physical_effects_df)

        effects_log.logwrite(f'\nCalculating model year period_duration physical effects for {session_name}')
        session_my_period_physical_effects_df = \
            calc_period_consumer_physical_view(batch_settings, session_physical_effects_df)

        # for use in benefits calcs, create an annual_physical_effects_df
        annual_physical_effects_df \
            = pd.concat([annual_physical_effects_df, session_annual_physical_effects_df], axis=0, ignore_index=True)
        annual_physical_effects_df.reset_index(inplace=True, drop=True)

        # for use in consumer calcs, create a my_lifetime_physical_effects_df of lifetime physical effects
        my_lifetime_physical_effects_df = \
            pd.concat([my_lifetime_physical_effects_df, session_my_period_physical_effects_df],
                      axis=0, ignore_index=True)
        my_lifetime_physical_effects_df.reset_index(inplace=True, drop=True)

        # cost effects _________________________________________________________________________________________________
        effects_log.logwrite(f'\nCalculating cost effects for {session_name}')
        session_cost_effects_dict = {}
        session_cost_effects_dict.update(
            calc_cost_effects(batch_settings, session_settings, session_physical_effects_dict, context_fuel_cpm_dict))

        session_cost_effects_df = pd.DataFrame.from_dict(session_cost_effects_dict, orient='index').reset_index(drop=True)

        if batch_settings.save_vehicle_cost_effects_files:
            effects_log.logwrite(f'Saving cost effects file for {session_name}')
            save_file(session_settings, session_cost_effects_df, path_of_run_folder, 'cost_effects', effects_log,
                      extension=batch_settings.file_format)

        effects_log.logwrite(f'\nCalculating annual costs effects for {session_name}')
        session_annual_cost_effects_df = calc_annual_cost_effects(session_cost_effects_df)

        effects_log.logwrite(f'\nCalculating model year period_duration cost effects for {session_name}')
        session_my_period_cost_effects_df = calc_period_consumer_view(batch_settings, session_cost_effects_df)

        # for use in benefits calcs, create an annual_cost_effects_df of undiscounted annual costs
        annual_cost_effects_df \
            = pd.concat([annual_cost_effects_df, session_annual_cost_effects_df], axis=0, ignore_index=True)
        annual_cost_effects_df.reset_index(inplace=True, drop=True)

        # for use in consumer calcs, create a my_lifetime_cost_effects_df of lifetime costs
        my_lifetime_cost_effects_df = pd.concat([my_lifetime_cost_effects_df, session_my_period_cost_effects_df],
                                                axis=0, ignore_index=True)
        my_lifetime_cost_effects_df.reset_index(inplace=True, drop=True)

    # discount annual costs ____________________________________________________________________________________________
    effects_log.logwrite('\nCalculating discounted annual costs, PVs and EAVs for the batch')
    discounted_costs = Discounting()
    discounted_costs.discount_annual_values(batch_settings, annual_cost_effects_df)
    discounted_costs.calc_present_values(batch_settings)
    discounted_costs.calc_annualized_values(batch_settings)
    discounted_costs_dict = \
        {**discounted_costs.annual_values_dict, **discounted_costs.pv_dict, **discounted_costs.eav_dict}

    discounted_costs_df = pd.DataFrame.from_dict(discounted_costs_dict, orient='index')

    # calculate annual benefits and annual physical effects deltas _____________________________________________________
    effects_log.logwrite(f'\nCalculating annual benefits for the batch')
    benefits_dict, delta_physical_effects_dict = \
        calc_benefits(batch_settings, annual_physical_effects_df, annual_cost_effects_df,
                      calc_health_effects=batch_settings.criteria_cost_factors.calc_health_effects)

    annual_benefits_df = pd.DataFrame.from_dict(benefits_dict, orient='index')
    annual_benefits_df.reset_index(inplace=True, drop=True)

    annual_physical_effects_deltas_df = pd.DataFrame.from_dict(delta_physical_effects_dict, orient='index')
    annual_physical_effects_deltas_df.reset_index(inplace=True, drop=True)

    # discount annual benefits _________________________________________________________________________________________
    effects_log.logwrite('\nCalculating discounted annual benefits, PVs and EAVs for the batch')
    discounted_benefits = Discounting()
    discounted_benefits.discount_annual_values(batch_settings, annual_benefits_df)
    discounted_benefits.calc_present_values(batch_settings)
    discounted_benefits.calc_annualized_values(batch_settings)
    discounted_benefits_dict = \
        {**discounted_benefits.annual_values_dict, **discounted_benefits.pv_dict, **discounted_benefits.eav_dict}

    discounted_benefits_df = pd.DataFrame.from_dict(discounted_benefits_dict, orient='index')

    # summarize costs, benefits and net benefits _______________________________________________________________________
    effects_log.logwrite('\nSummarizing social effects and calculating net benefits')
    social_effects_global_df = social_effects_domestic_df = None

    if batch_settings.net_benefit_ghg_scope in ['global', 'both']:
        social_effects_global_df = \
            calc_social_effects(discounted_costs_df, discounted_benefits_df, 'global',
                                calc_health_effects=batch_settings.criteria_cost_factors.calc_health_effects)

    if batch_settings.net_benefit_ghg_scope in ['domestic', 'both']:
        social_effects_domestic_df = \
            calc_social_effects(discounted_costs_df, discounted_benefits_df, 'domestic',
                                calc_health_effects=batch_settings.criteria_cost_factors.calc_health_effects)

    # sort DataFrames that contain discounting _________________________________________________________________________
    arg_sort_list = [
        'session_policy',
        'session_name',
        'series',
        'discount_rate',
        'calendar_year',
        'reg_class_id',
        'in_use_fuel_id'
    ]
    discounted_costs_df = discounted_costs_df.sort_values(by=arg_sort_list)
    discounted_benefits_df = discounted_benefits_df.sort_values(by=arg_sort_list)
    if social_effects_global_df is not None:
        social_effects_global_df = social_effects_global_df.sort_values(by=arg_sort_list)
    if social_effects_domestic_df is not None:
        social_effects_domestic_df = social_effects_domestic_df.sort_values(by=arg_sort_list)

    arg_sort_list = [
        'session_policy',
        'session_name',
        'discount_rate',
        'model_year',
        'body_style',
        'in_use_fuel_id'
    ]
    my_lifetime_cost_effects_df = my_lifetime_cost_effects_df.sort_values(by=arg_sort_list)

    # save files to CSV ________________________________________________________________________________________________
    annual_safety_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_safety_effects_summary.csv',
                                    index=False)
    annual_physical_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_physical_effects_annual.csv',
                                      index=False)
    annual_physical_effects_deltas_df.to_csv(
        path_of_run_folder / f'{start_time_readable}_physical_effects_annual_action_minus_no_action.csv',
        index=False)
    discounted_costs_df.to_csv(path_of_run_folder / f'{start_time_readable}_cost_effects_annual.csv', index=False)
    discounted_benefits_df.to_csv(path_of_run_folder / f'{start_time_readable}_benefits_annual.csv', index=False)
    if social_effects_global_df is not None:
        social_effects_global_df.to_csv(
            path_of_run_folder / f'{start_time_readable}_social_effects_global_ghg_annual.csv', index=False)
    if social_effects_domestic_df is not None:
        social_effects_domestic_df.to_csv(
            path_of_run_folder / f'{start_time_readable}_social_effects_domestic_ghg_annual.csv', index=False)
    my_lifetime_physical_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_MY_period_physical_effects.csv',
                                           index=False)
    my_lifetime_cost_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_MY_period_costs.csv', index=False)

    # add identifying info to CSV files ________________________________________________________________________________
    output_file_id_info = \
        [f'Batch Name: {batch_settings.batch_name}', f'Effects Run: {start_time_readable}_{batch_settings.run_id}']

    add_id_to_csv(path_of_run_folder / f'{start_time_readable}_safety_effects_summary.csv', output_file_id_info)
    add_id_to_csv(path_of_run_folder / f'{start_time_readable}_physical_effects_annual.csv', output_file_id_info)
    add_id_to_csv(
        path_of_run_folder / f'{start_time_readable}_physical_effects_annual_action_minus_no_action.csv',
        output_file_id_info)
    add_id_to_csv(path_of_run_folder / f'{start_time_readable}_cost_effects_annual.csv', output_file_id_info)
    add_id_to_csv(path_of_run_folder / f'{start_time_readable}_benefits_annual.csv', output_file_id_info)
    if batch_settings.net_benefit_ghg_scope in ['global', 'both']:
        add_id_to_csv(path_of_run_folder / f'{start_time_readable}_social_effects_global_ghg_annual.csv',
                      output_file_id_info)
    if batch_settings.net_benefit_ghg_scope in ['domestic', 'both']:
        add_id_to_csv(path_of_run_folder / f'{start_time_readable}_social_effects_domestic_ghg_annual.csv',
                      output_file_id_info)
    add_id_to_csv(path_of_run_folder / f'{start_time_readable}_MY_period_physical_effects.csv', output_file_id_info)
    add_id_to_csv(path_of_run_folder / f'{start_time_readable}_MY_period_costs.csv', output_file_id_info)

    elapsed_runtime = round(time() - start_time, 2)
    elapsed_runtime_minutes = round(elapsed_runtime / 60, 2)
    effects_log.logwrite('\nComplete')
    effects_log.logwrite(f'Runtime = {elapsed_runtime} seconds ({elapsed_runtime_minutes} minutes)')

    effects_log.logwrite(
        message=f'\n{datetime.now().strftime("%Y%m%d_%H%M%S")}: Output files have been saved to {path_of_run_folder}')


if __name__ == '__main__':
    main()
