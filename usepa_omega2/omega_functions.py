"""
omega_functions.py
==================

Functions that may be used throughout OMEGA

"""


partition_dict = dict()
def partition(columns, max_values=[1.0], increment=0.01, min_level=0.01, verbose=False):
    """

    :param columns: number of columns or list of column names
    :param max_values: list of max values for groups of columns
    :param increment: increment from 0 to max_values
    :param min_level: minimum output value (max output value will be max_value - min_level)
    :param verbose: if True then print result
    :return: pandas Dataframe of result, rows of which add up to sum(max_values)
    """
    import sys
    import pandas as pd
    import numpy as np

    if type(columns) is list:
        num_columns = len(columns)
    else:
        num_columns = columns
        columns = [i for i in range(num_columns)]

    partition_name = '%s_%s_%s_%s' % (columns, max_values, increment, min_level)

    if not partition_name in partition_dict:
        dfs = []
        for mv in max_values:
            members = []
            for i in range(num_columns):
                members.append(pd.DataFrame(np.arange(0, mv + increment, increment), columns=[columns[i]]))

            x = pd.DataFrame()
            for m in members:
                x = cartesian_prod(x, m)
                x = x[mv - x.sum(axis=1, numeric_only=True) >= -sys.float_info.epsilon].copy()  # sum <= mv

            x = x[abs(x.sum(axis=1) - mv) <= sys.float_info.epsilon]
            x[x == 0] = min_level
            x[x == mv] = mv - min_level
            dfs.append(x)

        ans = pd.DataFrame()
        for df in dfs:
            ans = cartesian_prod(ans, df)

        if verbose:
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(ans)

        ans = ans.loc[abs(ans.sum(axis=1, numeric_only=True) - sum(max_values)) <= sys.float_info.epsilon]
        ans = ans.drop('_', axis=1)

        partition_dict[partition_name] = ans

    return partition_dict[partition_name]


def unique(vector):
    """
    Find unique values in a list of values, in order of appearance

    :param vector: list of values
    :return: unique values, in order of appearance
    """

    import numpy as np

    indexes = np.unique(vector, return_index=True)[1]
    return [vector[index] for index in sorted(indexes)]


def weighted_value(objects, weight_attribute, attribute):
    """

    :param objects: list-like of objects
    :param weight_attribute: name of object attribute to weight by (e.g. 'sales')
    :param attribute: name of attribute to calculate weighted value from (e.g. 'footprint_ft2')
    :return: weighted value
    """
    weighted_sum = 0
    total = 0
    for o in objects:
        weight = o.__getattribute__(weight_attribute)
        total = total + weight
        weighted_sum = weighted_sum + o.__getattribute__(attribute) * weight

    return weighted_sum / total


def unweighted_value(obj, weighted_value, objects, weight_attribute, attribute):
    """

    :param objects:
    :param weight:
    :param attribute:
    :param obj:
    :param weighted_value:
    :return:
    """
    total = 0
    weighted_sum = 0
    for o in objects:
        weight = o.__getattribute__(weight_attribute)
        total = total + weight
        if o is not obj:
            weighted_sum = weighted_sum + o.__getattribute__(attribute) * weight

    return (weighted_value * total - weighted_sum) / obj.__getattribute__(weight_attribute)


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
            left_df = left_df.drop('_', axis=1)
            right_df = right_df.drop('_', axis=1, errors='ignore')
        else:
            leftXright = pd.merge(left_df, right_df, on='_')

    return leftXright


if __name__ == '__main__':
    pass  # for now