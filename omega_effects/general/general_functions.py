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


def read_input_file(path, effects_log=None, usecols=None, index_col=None, skiprows=None, skip_blank_lines=True,
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
        if effects_log:
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
        if effects_log:
            effects_log.logwrite(message=f'File {path}......  *** NOT FOUND ***. '
                                         f'\nSet the input folder path in the batch_settings.csv.')
        sys.exit()


def read_input_file_template_info(path, effects_log=None):
    """

    Parameters:
        path: Path to the specified file.\n
        effects_log: object; an object of the EffectsLog class.

    Returns:
        A DataFrame of the desired data from the passed input file.

    """
    if path.is_file():
        file_datetime = get_file_datetime(path)
        if effects_log:
            effects_log.logwrite(message=f'File {path}...found. Version {file_datetime}.')

        return pd.read_csv(path, header=None, nrows=1).values.tolist()[0]

    else:
        if effects_log:
            effects_log.logwrite(message=f'File {path}......  *** NOT FOUND ***. ')
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


def calc_fuel_cost_per_mile(
        batch_settings, session_settings, calendar_year,
        onroad_direct_kwh_per_mile, onroad_direct_co2e_grams_per_mile, in_use_fuel_id
):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        calendar_year(int): the calendar year needed for fuel prices.
        onroad_direct_kwh_per_mile (float): the onroad electricity consumption.
        onroad_direct_co2e_grams_per_mile (float): the onroad co2 grams per mile.
        in_use_fuel_id (str): a dict-like string providing fuel id information.

    Returns:
        The fuel cost per mile in the given year for the given vehicle.

    """
    fuel_cost_per_mile = 0
    if onroad_direct_kwh_per_mile:
        fuel = 'US electricity'
        retail_price_per_kwh = session_settings.electricity_prices.get_fuel_price(
            calendar_year, 'retail_dollars_per_unit'
        )
        refuel_efficiency_e = \
            batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
        fuel_cost_per_mile = onroad_direct_kwh_per_mile * retail_price_per_kwh / refuel_efficiency_e

    if onroad_direct_co2e_grams_per_mile:
        fuel_dict = eval(in_use_fuel_id)
        fuel = [fuel for fuel in fuel_dict.keys()][0]
        retail_price_per_gallon = \
            batch_settings.context_fuel_prices.get_fuel_price(
                calendar_year, fuel, 'retail_dollars_per_unit'
            )
        refuel_efficiency_l = \
            batch_settings.onroad_fuels.get_fuel_attribute(calendar_year, fuel, 'refuel_efficiency')
        co2_emissions_grams_per_unit = \
            batch_settings.onroad_fuels.get_fuel_attribute(
                calendar_year, fuel, 'direct_co2e_grams_per_unit'
            ) / refuel_efficiency_l
        onroad_gallons_per_mile = onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
        fuel_cost_per_mile += onroad_gallons_per_mile * retail_price_per_gallon

    return fuel_cost_per_mile
