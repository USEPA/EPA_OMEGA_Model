"""

**OMEGA effects general functions module.**

----

**CODE**

"""

import pandas as pd
import os
import sys
import time
import shutil


def copy_files(file_list, folder_name):
    """

    Args:
        file_list (list): List of file Path objects to copy into a new location.
        folder_name: Path object for the folder into which to copy files.

    Returns:
        Nothing, but copies files in file_list into folder_name.

    """
    folder_name.mkdir(exist_ok=False)

    for file in file_list:
        shutil.copy2(file, folder_name)


def get_file_datetime(filepath):
    """

    Parameters:
        filepath: Object; the path to the file as a pathlib object.

    Returns:
        A datetime (date stamp) for the file at the passed path.

    """
    file_datetime = time.ctime(os.path.getmtime(filepath))

    return file_datetime


def read_input_file(path, effects_log, usecols=None, index_col=None, skiprows=None, skip_blank_lines=True,
                    reset_index=False):
    """

    Parameters:
        path: Path to the specified file.\n
        effects_log: object; an object of the EffectsLog class.
        usecols: List; the columns to use in the returned DataFrame.\n
        index_col: int; the column to use as the index column of the returned DataFrame.\n
        skiprows: int; the number of rows to skip when reading the file.\n
        skip_blank_lines: bool; True will skip blank lines.
        reset_index: Boolean; True resets index, False does not.

    Returns:
        A DataFrame of the desired data from the passed input file.

    """
    if path.is_file():
        file_datetime = get_file_datetime(path)
        effects_log.logwrite(message=f'File {path}...found. Version {file_datetime}.')
        if reset_index:
            return pd.read_csv(path,
                               usecols=usecols,
                               index_col=index_col,
                               skiprows=skiprows,
                               skip_blank_lines=skip_blank_lines,
                               on_bad_lines='skip',
                               ).dropna().reset_index(drop=True)
        else:
            return pd.read_csv(path,
                               usecols=usecols,
                               index_col=index_col,
                               skiprows=skiprows,
                               skip_blank_lines=skip_blank_lines,
                               on_bad_lines='skip',
                               )
    else:
        effects_log.logwrite(message=f'File {path}......  *** NOT FOUND ***. '
                                     f'\nSet the input folder path in the batch_settings.csv.')
        sys.exit()


def save_dict(settings, dict_to_save, save_path, row_header=None, stamp=None, index=False):
    """

    Parameters:
        settings: object; an object of the SetInputs class.
        dict_to_save: Dictionary; the dictionary to be saved to CSV.\n
        save_path: Path object; the path for saving the passed dict_to_save.\n
        row_header: List; the column names to use as the row header for the preferred structure of the output file.\n
        stamp: str; an identifier for inclusion in the filename, e.g., datetime stamp.\n
        index: Boolean; True includes the index; False excludes the index.

    Returns:
        Saves the passed dictionary to a CSV file.

    """
    settings.tool_log.logwrite(message=f'Saving dictionary to {save_path}_{stamp}.csv')
    df = pd.DataFrame(dict_to_save).transpose()
    if row_header:
        cols = [col for col in df.columns if col not in row_header]
        df = pd.DataFrame(df, columns=row_header + cols)

    df.to_csv(f'{save_path}_{stamp}.csv', index=index)

    return


def save_dict_return_df(dict_to_save, save_path, row_header=None, stamp=None, index=False):
    """

    Parameters:
        dict_to_save: Dictionary; the dictionary to be saved to CSV.\n
        save_path: Path object; the path for saving the passed dict_to_save.\n
        row_header: List; the column names to use as the row header for the preferred structure of the output file.\n
        stamp: str; an identifier for inclusion in the filename, e.g., datetime stamp.\n
        index: Boolean; True includes the index; False excludes the index.

    Returns:
        Saves the passed dictionary to a CSV file and returns a DataFrame based on the passed dictionary.

    """
    print('Saving dictionary to CSV.')
    df = pd.DataFrame(dict_to_save).transpose()
    if row_header:
        cols = [col for col in df.columns if col not in row_header]
        df = pd.DataFrame(df, columns=row_header + cols)

    df.to_csv(f'{save_path}_{stamp}.csv', index=index)

    return df


def calc_rebound_effect(fuel_cpm_old, fuel_cpm_new, rebound_rate):
    """

    Args:
        fuel_cpm_old (numeric): fuel cost per mile prior to a change, whether driven by fuel consumption or fuel price.
        fuel_cpm_new (numeric): fuel cost per mile after a change, whether driven by fuel consumption or fuel price.
        rebound_rate (numeric): this should be a negative value if fewer miles are driven upon higher costs per mile.

    Returns:
        The rebound effect.

    """
    return rebound_rate * (fuel_cpm_new - fuel_cpm_old) / fuel_cpm_old
