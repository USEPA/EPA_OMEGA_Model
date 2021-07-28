"""

Some general functions for use in the effects calculations.

----

**CODE**

"""
import pandas as pd
from math import log10, floor


def adjust_dollars(df, deflators, *args):
    """

    Args:
        df: The DataFrame of values to be converted to a consistent dollar basis.
        deflators: A DataFrame of price deflators.
        args: The attributes to be converted to a consistent dollar basis.

    Returns:
        The passed DataFrame with args expressed in a consistent dollar basis.

    """
    basis_years = df['dollar_basis'].unique()
    df_return = df.copy()
    for basis_year in basis_years:
        for arg in args:
            adj_factor = deflators.at[basis_year, 'adjustment_factor']
            df_return.loc[df_return['dollar_basis'] == basis_year, arg] = df_return[arg] * adj_factor
    df_return['dollar_basis'] = deflators.index[deflators['adjustment_factor'] == 1][0]
    return df_return


def round_sig(df, divisor=1, sig=0, *args):
    """

    A function to round values to a certain number of significant digits.

    Args:
        df: The DataFrame containing data to be rounded.
        args: Attributes to be rounded.
        sig: The number of significant digits.
        divisor: The divisor to apply first prior to rounding (i.e., for values in Millions, pass 1000000).

    Returns:
        The passed DataFrame with args expressed in divisor units and rounded to sig significant digits.

    """
    for arg in args:
        try:
            df[arg] = df[arg].apply(lambda x: round(x/divisor, sig-int(floor(log10(abs(x/divisor))))-1))
        except:
            df[arg].replace(to_replace=0, value=1, inplace=True)
            df[arg] = df[arg].apply(lambda x: round(x / divisor, sig - int(floor(log10(abs(x / divisor)))) - 1))
    return df


def save_dict_to_csv(dict_to_save, save_path, row_header=None, *args):
    """

    Args:
        dict_to_save: A dictionary having a tuple of args as keys.\n
        save_path: The path for saving the passed CSV.\n
        row_header: A list of the column names to use a the row header for the preferred structure of the output file.
        args: The arguments contained in the tuple key - these will be pulled out and named according to the passed arguments.

    Returns:
        A CSV file with individual key elements split out into columns with args as names.

    """
    print('Saving dictionary to CSV.')
    df = pd.DataFrame(dict_to_save).transpose()
    df.reset_index(inplace=True)
    for idx, arg in enumerate(args):
        if arg in df.columns:
            df.drop(columns=f'level_{idx}', inplace=True)
        else:
            df.rename(columns={f'level_{idx}': arg}, inplace=True)
    # if row_header and 'yearID' not in df.columns.tolist():
    #     df.insert(0, 'yearID', df[['modelYearID', 'ageID']].sum(axis=1))
    cols = [col for col in df.columns if col not in row_header]
    df = pd.DataFrame(df, columns=row_header + cols)
    df.to_csv(f'{save_path}.csv', index=False)
    return