"""

general_functions.py
====================
"""

import pandas as pd
from math import log10, floor
from usepa_omega2 import *


def adjust_dollars(df, deflators, *args):
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

    :param df: The DataFrame containing data to be rounded.
    :param args: The metrics to be rounded.
    :param divisor: The divisor to use should results be desired in units other than those passed (set divisor=1 to maintain units).
    :param sig: The number of significant digits.
    :return: The passed DataFrame with args rounded to 'sig' digits and expressed in 'divisor' units.
    """
    for arg in args:
        try:
            df[arg] = df[arg].apply(lambda x: round(x/divisor, sig-int(floor(log10(abs(x/divisor))))-1))
        except:
            df[arg].replace(to_replace=0, value=1, inplace=True)
            df[arg] = df[arg].apply(lambda x: round(x / divisor, sig - int(floor(log10(abs(x / divisor)))) - 1))
    return df
