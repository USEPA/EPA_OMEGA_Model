"""
omega_functions.py
==================

Functions that may be used throughout OMEGA

"""


def unique(vector):
    """
    Find unique values in a list of values, in order of appearance

    :param vector: list of values
    :return: unique values, in order of appearance
    """

    import numpy as np

    indexes = np.unique(vector, return_index=True)[1]
    return [vector[index] for index in sorted(indexes)]


def cartesian_prod(left_df, right_df, drop=False):
    """
    Calculate cartesian product of the dataframe rows

    :param left_df: 'left' dataframe
    :param right_df: 'right' dataframe
    :param drop: if True, drop join-column '_' from dataframes
    :return: cartesian product of the dataframe rows
    """
    import pandas as pd
    import numpy as np

    if left_df.empty:
        return right_df
    else:
        if '_' not in left_df:
            left_df['_'] = np.nan

        if '_' not in right_df:
            right_df['_'] = np.nan

        if drop:
            leftXright = pd.merge(left_df, right_df, on='_').drop('_', axis=1)
            left_df.drop('_', axis=1, inplace=True)
            right_df.drop('_', axis=1, inplace=True, errors='ignore')
        else:
            leftXright = pd.merge(left_df, right_df, on='_')

    return leftXright


if __name__ == '__main__':
    pass  # for now