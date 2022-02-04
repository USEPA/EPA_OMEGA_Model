"""

Some general functions for use in the effects calculations.

----

**CODE**

"""
import pandas as pd
from math import log10, floor


def adjust_dollars(df, deflators, dollar_basis_year, *args):
    """

    Args:
        df (DataFrame): values to be converted to a consistent dollar basis.
        deflators (str): 'cpi_price_deflators' or 'ip_deflators' for consumer price index or implicit price deflators
        dollar_basis_year (int): the desired dollar basis for the return DataFrame.
        args: The attributes to be converted to a consistent dollar basis.

    Returns:
        The passed DataFrame with args expressed in a consistent dollar basis.

    """
    if deflators == 'cpi_price_deflators':
        from effects.cpi_price_deflators import CPIPriceDeflators
        deflators = CPIPriceDeflators
    else:
        from effects.ip_deflators import ImplictPriceDeflators
        deflators = ImplictPriceDeflators

    basis_years = pd.Series(df.loc[df['dollar_basis'] > 0, 'dollar_basis']).unique()
    adj_factor_numerator = deflators.get_price_deflator(dollar_basis_year)
    df_return = df.copy()
    for basis_year in basis_years:
        adj_factor = adj_factor_numerator / deflators.get_price_deflator(basis_year)
        for arg in args:
            df_return.loc[df_return['dollar_basis'] == basis_year, arg] = df_return[arg] * adj_factor
    df_return['dollar_basis'] = dollar_basis_year
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


def save_dict_to_csv(dict_to_save, save_path, index):
    """

    Args:
        dict_to_save: A dictionary to be converted to a DataFrame and saved to a CSV.
        save_path: The path for saving the passed dict_to_save.
        index: Boolean specifies whether to include/exclude index from CSV.

    Returns:
        A DataFrame based on the passed dict_to_save.

    """
    print(f'Saving {save_path}')
    df = pd.DataFrame(dict_to_save).transpose()
    df.to_csv(f'{save_path}', index=index)

    return df
