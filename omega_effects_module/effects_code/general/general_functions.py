import pandas as pd
from pathlib import PurePath
import os
import sys
import time
from datetime import datetime


def inputs_filenames(input_files_pathlist):
    """

    Parameters:
        input_files_pathlist: List; those input files that are specified in the input_files file contained in the
        general folder.

    Returns:
        A list of input file full paths - these will be copied directly to the output folder so that general and outputs
        end up bundled together in the output folder associated with the given run.

    """
    _filename_list = [PurePath(path).name for path in input_files_pathlist]

    return _filename_list


def get_file_datetime_df(list_of_files):
    """

    Parameters:
        list_of_files: List; the files for which datetimes are required.

    Returns:
        A DataFrame of input files (full path) and corresponding datetimes (date stamps) for those files.

    """
    file_datetime_df = pd.DataFrame()
    file_datetime_df.insert(0, 'Item', [path_to_file for path_to_file in list_of_files])
    file_datetime_df.insert(1, 'Results', [time.ctime(os.path.getmtime(path_to_file)) for path_to_file in list_of_files])

    return file_datetime_df


def get_file_datetime(filepath):
    """

    Parameters:
        filepath: Object; the path to the file as a pathlib object.

    Returns:
        A datetime (date stamp) for the file at the passed path.

    """
    file_datetime = time.ctime(os.path.getmtime(filepath))

    return file_datetime


def read_input_file(path, effects_log, usecols=None, index_col=None, skiprows=None, skip_blank_lines=True, reset_index=False):
    """

    Parameters:
        path: Path to the specified file.\n
        effects_log: object; an object of the EffectsLog class.
        logfile_name: Path object; the tool logfile name.
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


def adjust_dollars(batch_settings, df, deflators, effects_log, *args):
    """

    Args:
        df (DataFrame): values to be converted to a consistent dollar basis.
        deflators (str): 'cpi_price_deflators' or 'ip_deflators' for consumer price index or implicit price deflators
        args: The attributes to be converted to a consistent dollar basis.

    Returns:
        The passed DataFrame with args expressed in a consistent dollar basis.

    """
    analysis_dollar_basis = batch_settings.analysis_dollar_basis
    if deflators == 'cpi_price_deflators':
        deflators = batch_settings.cpi_deflators
    else:
        deflators = batch_settings.ip_deflators

    basis_years = pd.Series(df.loc[df['dollar_basis'] > 0, 'dollar_basis']).unique()
    # basis_years = np.unique(np.array(df.loc[df['dollar_basis'] > 0, 'dollar_basis']))
    adj_factor_numerator = deflators.get_price_deflator(analysis_dollar_basis, effects_log)
    df_return = df.copy()
    for basis_year in basis_years:
        adj_factor = adj_factor_numerator / deflators.get_price_deflator(basis_year, effects_log)
        for arg in args:
            df_return.loc[df_return['dollar_basis'] == basis_year, arg] = df_return[arg] * adj_factor
            df_return.loc[df_return['dollar_basis'] == basis_year, 'dollar_basis'] = analysis_dollar_basis

    return df_return


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
