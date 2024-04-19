"""

**OMEGA cost summary for use in employment analysis.**

----

**CODE**

"""
import pandas as pd

from omega_effects.general.file_id_and_save import add_id_to_csv


class EmploymentAnalysisCosts:
    """

    Cost summation for use in employment analysis - called by join_controller if requested in the runtime options of the
    effects batch file. So this runs only if both LD and MD effects have been run.

    """
    def __init__(self):

        self.attribute_dict = {
            'ICE_XEV_common': {'glider_non_structure_cost', 'structure_cost', 'driveline_cost'},
            'ICE_unique': {'engine_cost'},
            'XEV_unique': {'battery_cost', 'emachine_cost', 'electrified_driveline_cost'},
        }
        self.fueling_classes = ['BEV', 'ICE', 'PHEV']

    def employment_analysis_costs_for_batch(self, set_paths, batch_settings, file_id_string, effects_log):
        """

        Args:
            set_paths: An instance of the SetPaths class.
            batch_settings: An instance of the BatchSettings class.
            file_id_string (str): The search string in the filename needed.
            effects_log: An instance of the EffectsLog class.

        Returns:
            Nothing, but it summarizes costs and saves an output file for use in the employment analysis.

        """
        effects_log.logwrite('\nRunning employment analysis costs')
        effects_folder = set_paths.path_of_run_folder

        join_df = pd.DataFrame()

        for fleet, nested_dict in batch_settings.batch_sessions.items():

            for idx, n_dict in nested_dict.items():

                session_name, session_policy = n_dict['session_name'], n_dict['session_policy']
                filename_just_used = df = df1 = None

                session_folder = effects_folder / f'{session_name}_inputs_{fleet}'
                files_in_session_folder = [file for file in session_folder.iterdir() if file.is_file()]
                for file in files_in_session_folder:
                    if f'{session_name}_{file_id_string}' in file.name:

                        if file.name != filename_just_used:
                            effects_log.logwrite(f'\nGetting {file_id_string} file from {session_folder}')
                            df = pd.read_csv(file)
                        else:
                            effects_log.logwrite(f'\nReusing {file_id_string} file from {session_folder}')

                        df1 = df.loc[:, ['vehicle_id', '_initial_registered_count', 'model_year', 'fueling_class']]

                        for k, v in self.attribute_dict.items():
                            for attribute in v:
                                df1 = pd.concat([df1, df[attribute]], axis=1)

                        df1.insert(0, 'session_policy', session_policy)

                        join_df = pd.concat([join_df, df1], axis=0)

                        filename_just_used = file.name

        effects_log.logwrite('\nSales weighting results')
        for key, nested_list in self.attribute_dict.items():

            join_df.insert(len(join_df.columns), key, 0)

            for attribute in nested_list:
                join_df[key] = join_df[[key, attribute]].sum(axis=1)

        groupby_cols = ['session_policy', 'model_year', 'fueling_class']
        cols = ['_initial_registered_count']

        for col in self.attribute_dict:
            cols.append(col)

        for col in self.attribute_dict:
            join_df[col] = join_df[col] * join_df['_initial_registered_count']

        join_df = join_df[[*groupby_cols, *cols]]
        summary_df = join_df.fillna(0)
        summary_df = summary_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

        for col in self.attribute_dict:
            summary_df[col] = summary_df[col] / summary_df['_initial_registered_count']

        file_name = 'employment_analysis_costs'
        summary_df.to_csv(
            set_paths.path_of_run_folder / f'{batch_settings.start_time_readable}_{file_name}_lmdv.csv', index=False)
        output_file_id_info = [f'{set_paths.path_of_run_folder}']
        add_id_to_csv(
            set_paths.path_of_run_folder / f'{batch_settings.start_time_readable}_{file_name}_lmdv.csv',
            output_file_id_info
        )
