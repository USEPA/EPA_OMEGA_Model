"""

**OMEGA effects controller.**

----

**CODE**

"""
import shutil

from time import time
from datetime import datetime

from omega_effects.set_paths import SetPaths

from omega_effects.batch_settings import BatchSettings
from omega_effects.general.effects_log import EffectsLog
from omega_effects.general.general_functions import copy_files
from omega_effects.omega_effects_main import main
from omega_effects.lmdv_join.join_controller import join_controller


def effects_controller():
    """

    Effects control - calls the main function in omega_effects_main for LD then MD and, if requested, calls
    join_controller to join LD and MD effects into LMDV effects.

    """
    start_time = time()
    start_time_readable = datetime.now().strftime('%Y%m%d_%H%M%S')

    batch_settings = BatchSettings()
    batch_settings_file = batch_settings.path_of_effects_batch_settings_csv()
    batch_settings.init_from_file(batch_settings_file)
    batch_settings.get_run_id('lmdv')
    batch_settings.start_time_readable = start_time_readable

    set_paths = SetPaths()
    set_paths.create_output_paths(
        batch_settings.path_outputs, start_time_readable, batch_settings.run_id
    )
    set_paths.copy_code_to_destination()

    effects_log = EffectsLog()
    effects_log.init_logfile(set_paths.path_of_run_folder)
    effects_log.logwrite(f'\n{batch_settings.runtime_info}\n')
    effects_log.logwrite(f'EPA OMEGA Model Effects started\n', stamp=True)

    batch_settings.get_runtime_options('lmdv', effects_log)
    batch_settings.get_lmdv_batch_settings('lmdv')
    batch_settings.init_batch_classes(effects_log)
    shutil.copy2(batch_settings_file, set_paths.path_of_run_folder)

    if batch_settings.save_input_files:
        copy_files(batch_settings.inputs_filelist, set_paths.path_of_run_folder / 'batch_inputs')

    for fleet in batch_settings.fleets:

        main(set_paths, batch_settings, fleet, effects_log)

    if batch_settings.sessions_to_run == 'lmdv':

        batch_settings.get_join_settings()
        join_controller(set_paths, batch_settings, effects_log)

    elapsed_runtime = round(time() - start_time, 2)
    elapsed_runtime_minutes = round(elapsed_runtime / 60, 2)
    effects_log.logwrite('Complete', stamp=True)
    effects_log.logwrite(f'Runtime = {elapsed_runtime} seconds ({elapsed_runtime_minutes} minutes)')

    effects_log.logwrite(f'Output files have been saved to {set_paths.path_of_run_folder}', stamp=True)


if __name__ == '__main__':
    effects_controller()
