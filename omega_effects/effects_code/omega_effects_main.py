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

import omega_effects.effects_code
from omega_effects.effects_code.set_paths import SetPaths

from omega_effects.effects_code.batch_settings import BatchSettings
from omega_effects.effects_code.session_settings import SessionSettings

from omega_effects.effects_code.general.effects_log import EffectsLog
from omega_effects.effects_code.general.runtime_options import RuntimeOptions
from omega_effects.effects_code.general.general_functions import copy_files
from omega_effects.effects_code.general.file_id_and_save import add_id_to_csv, save_file

from omega_effects.effects_code.effects.vmt_adjustments import AdjustmentsVMT
from omega_effects.effects_code.effects.context_fuel_cost_per_mile import calc_fuel_cost_per_mile
from omega_effects.effects_code.effects.safety_effects import calc_safety_effects, calc_legacy_fleet_safety_effects, \
    calc_annual_avg_safety_effects
from omega_effects.effects_code.effects.physical_effects import calc_physical_effects, \
    calc_legacy_fleet_physical_effects, calc_annual_physical_effects, calc_period_consumer_physical_view
from omega_effects.effects_code.effects.cost_effects import calc_cost_effects, calc_annual_cost_effects, \
    calc_period_consumer_view
from omega_effects.effects_code.effects.present_and_annualized_values import PVandEAV
from omega_effects.effects_code.effects.benefits import calc_benefits
from omega_effects.effects_code.effects.sum_social_effects import calc_social_effects


def main():
    """

    Main effects code.

    """
    set_paths = SetPaths()
    run_id = set_paths.run_id()

    effects_log = EffectsLog()
    effects_log.init_logfile(set_paths.path_module)
    start_time = time()
    start_time_readable = datetime.now().strftime('%Y%m%d_%H%M%S')

    version = omega_effects.effects_code.__version__

    effects_log.logwrite(f'\nEPA OMEGA Model Effects Module version {version} started at {start_time_readable}\n')

    runtime_options = RuntimeOptions()
    runtime_options.init_from_file(set_paths.path_module / 'runtime_options.csv', effects_log)

    batch_settings = BatchSettings()
    batch_settings.init_from_file(runtime_options.batch_settings_file, effects_log)

    path_of_run_folder, path_of_code_folder = \
        set_paths.create_output_paths(runtime_options, batch_settings, start_time_readable, run_id)

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
    if runtime_options.save_input_files:
        copy_files(session_settings.inputs_filelist, path_of_run_folder / 'context_inputs')

    effects_log.logwrite('\nCalculating context vmt adjustments and context fuel cost per mile')
    vmt_adjustments_context = AdjustmentsVMT()
    vmt_adjustments_context.calc_vmt_adjustments(batch_settings, session_settings)

    context_fuel_cpm_dict = calc_fuel_cost_per_mile(batch_settings, session_settings)
    if runtime_options.save_context_fuel_cost_per_mile_file:
        effects_log.logwrite(f'Saving context fuel cost per mile file')
        context_fuel_cpm_df = pd.DataFrame.from_dict(context_fuel_cpm_dict, orient='index').reset_index(drop=True)
        save_file(session_settings, context_fuel_cpm_df, path_of_run_folder, 'context_fuel_cost_per_mile',
                  effects_log, extension=runtime_options.file_format)

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
        if runtime_options.save_input_files:
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

        if runtime_options.save_vehicle_safety_effects_files:
            effects_log.logwrite(f'Saving safety effects file for {session_name}')
            save_file(session_settings, session_safety_effects_df, path_of_run_folder, 'safety_effects',
                      effects_log, extension=runtime_options.file_format)

        effects_log.logwrite(f'\nCalculating safety effects summary for {session_name}')
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

        if runtime_options.save_vehicle_physical_effects_files:
            effects_log.logwrite(f'Saving physical effects file for {session_name}')
            save_file(session_settings, session_physical_effects_df, path_of_run_folder, 'physical_effects', effects_log,
                      extension=runtime_options.file_format)

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
        session_cost_effects_dict = dict()
        session_cost_effects_dict.update(
            calc_cost_effects(batch_settings, session_settings, session_physical_effects_dict, context_fuel_cpm_dict))

        session_cost_effects_df = pd.DataFrame.from_dict(session_cost_effects_dict, orient='index').reset_index(drop=True)

        if runtime_options.save_vehicle_cost_effects_files:
            effects_log.logwrite(f'Saving cost effects file for {session_name}')
            save_file(session_settings, session_cost_effects_df, path_of_run_folder, 'cost_effects', effects_log,
                      extension=runtime_options.file_format)

        effects_log.logwrite(f'\nCalculating annual costs effects for {session_name}')
        session_annual_cost_effects_df = calc_annual_cost_effects(session_cost_effects_df)

        effects_log.logwrite(f'\nCalculating model year period_duration cost effects for {session_name}')
        session_my_period_cost_effects_df = calc_period_consumer_view(batch_settings, session_cost_effects_df)

        # for use in benefits calcs, create an annual_cost_effects_df of undiscounted annual costs
        annual_cost_effects_df \
            = pd.concat([annual_cost_effects_df, session_annual_cost_effects_df], axis=0, ignore_index=True)
        annual_cost_effects_df.reset_index(inplace=True, drop=True)

        # for use in consumer calcs, create a my_lifetime_cost_effects_df of undiscounted lifetime costs
        my_lifetime_cost_effects_df = pd.concat([my_lifetime_cost_effects_df, session_my_period_cost_effects_df],
                                                axis=0, ignore_index=True)
        my_lifetime_cost_effects_df.reset_index(inplace=True, drop=True)

    effects_log.logwrite('\nCalculating present and annualized costs for the batch')
    pv_and_eav_costs_dict = PVandEAV().calc_present_and_annualized_values(batch_settings, annual_cost_effects_df)
    pv_and_eav_costs_df = pd.DataFrame.from_dict(pv_and_eav_costs_dict, orient='index')

    # benefits _________________________________________________________________________________________________________
    effects_log.logwrite(f'\nCalculating benefits for the batch')
    benefits_dict, delta_physical_effects_dict = \
        calc_benefits(batch_settings, annual_physical_effects_df, annual_cost_effects_df,
                      calc_health_effects=batch_settings.criteria_cost_factors.calc_health_effects)

    annual_benefits_df = pd.DataFrame.from_dict(benefits_dict, orient='index')
    annual_benefits_df.reset_index(inplace=True, drop=True)

    effects_log.logwrite('\nCalculating present and annualized benefits for the batch')
    pv_and_eav_benefits_dict = PVandEAV().calc_present_and_annualized_values(batch_settings, annual_benefits_df)
    pv_and_eav_benefits_df = pd.DataFrame.from_dict(pv_and_eav_benefits_dict, orient='index')

    # summarize costs, benefits and net benefits _______________________________________________________________________
    effects_log.logwrite('\nSummarizing social effects and calculating net benefits')
    social_effects_global_df = social_effects_domestic_df = None

    if batch_settings.net_benefit_ghg_scope in ['global', 'both']:
        social_effects_global_df = \
            calc_social_effects(pv_and_eav_costs_df, pv_and_eav_benefits_df, 'global',
                                calc_health_effects=batch_settings.criteria_cost_factors.calc_health_effects)

    if batch_settings.net_benefit_ghg_scope in ['domestic', 'both']:
        social_effects_domestic_df = \
            calc_social_effects(pv_and_eav_costs_df, pv_and_eav_benefits_df, 'domestic',
                                calc_health_effects=batch_settings.criteria_cost_factors.calc_health_effects)

    annual_physical_effects_deltas_df = pd.DataFrame.from_dict(delta_physical_effects_dict, orient='index')
    annual_physical_effects_deltas_df.reset_index(inplace=True, drop=True)

    # save files to CSV ________________________________________________________________________________________________
    annual_safety_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_safety_effects_summary.csv',
                                    index=False)
    annual_physical_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_physical_effects_annual.csv',
                                      index=False)
    annual_physical_effects_deltas_df.to_csv(
        path_of_run_folder / f'{start_time_readable}_physical_effects_annual_action_minus_no_action.csv',
        index=False)
    pv_and_eav_costs_df.to_csv(path_of_run_folder / f'{start_time_readable}_cost_effects_annual.csv', index=False)
    pv_and_eav_benefits_df.to_csv(path_of_run_folder / f'{start_time_readable}_benefits_annual.csv', index=False)
    if batch_settings.net_benefit_ghg_scope in ['global', 'both']:
        social_effects_global_df.to_csv(
            path_of_run_folder / f'{start_time_readable}_social_effects_global_ghg_annual.csv', index=False)
    if batch_settings.net_benefit_ghg_scope in ['domestic', 'both']:
        social_effects_domestic_df.to_csv(
            path_of_run_folder / f'{start_time_readable}_social_effects_domestic_ghg_annual.csv', index=False)
    my_lifetime_physical_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_MY_period_physical_effects.csv',
                                           index=False)
    my_lifetime_cost_effects_df.to_csv(path_of_run_folder / f'{start_time_readable}_MY_period_costs.csv', index=False)

    # add identifying info to CSV files ________________________________________________________________________________
    output_file_id_info = [f'Batch Name: {batch_settings.batch_name}', f'Effects Run: {start_time_readable}_{run_id}']

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

    shutil.copy2(runtime_options.batch_settings_file, path_of_run_folder / f'{runtime_options.batch_settings_file_name}')
    set_paths.copy_code_to_destination(path_of_code_folder)

    if runtime_options.save_input_files:
        copy_files(batch_settings.inputs_filelist, path_of_run_folder / 'batch_inputs')

    elapsed_runtime = round(time() - start_time, 2)
    elapsed_runtime_minutes = round(elapsed_runtime / 60, 2)
    effects_log.logwrite('\nComplete')
    effects_log.logwrite(f'Runtime = {elapsed_runtime} seconds ({elapsed_runtime_minutes} minutes)')

    effects_log.logwrite(
        message=f'\n{datetime.now().strftime("%Y%m%d_%H%M%S")}: Output files have been saved to {path_of_run_folder}')
    shutil.copy2(effects_log.logfile_name, path_of_run_folder / effects_log.file_name)
    shutil.copy2(set_paths.path_module / 'runtime_options.csv', path_of_run_folder / 'runtime_options.csv')


if __name__ == '__main__':
    main()
