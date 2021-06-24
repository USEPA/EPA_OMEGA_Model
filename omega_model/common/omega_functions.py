"""

Functions that may be used throughout OMEGA


----

**CODE**

"""


def plot_frontier(cost_cloud, cost_curve_name, frontier_df, x_key, y_key):
    """
    Plot a cloud and its frontier.  Saves plot to ``o2.options.output_folder``.

    Args:
        cost_cloud (DataFrame): set of points to plot
        cost_curve_name (str): name of  plot
        frontier_df (DataFrame): set of points on the frontier
        x_key (str): column name of x-value
        y_key (str): columns name of y-value

    Example:

        ::

            # from create_frontier_df() in vehicles.py
            CostCloud.plot_frontier(self.cost_cloud, '', cost_curve, 'cert_co2_grams_per_mile', 'new_vehicle_mfr_cost_dollars')

    """
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(cost_cloud[x_key], cost_cloud[y_key],
             '.')
    plt.title('Cost versus %s %s' % (x_key, cost_curve_name))
    plt.xlabel('%s' % x_key)
    plt.ylabel('%s' % y_key)
    plt.plot(frontier_df[x_key], frontier_df[y_key],
             'r-')
    plt.grid()
    plt.savefig(globals.options.output_folder + '%s versus %s %s.png' % (y_key, x_key, cost_curve_name))


def calc_frontier(cloud, x_key, y_key, allow_upslope=False):
    """
    Calculate the frontier of a cloud.

    Args:
        cloud (DataFrame): a set of points to find the frontier of
        x_key (str): name of the column holding x-axis data
        y_key (str): name of the column holding y-axis data
        allow_upslope (bool): allow U-shaped frontier

    Returns:
        DataFrame containing the frontier points

    .. figure:: _static/code_figures/cost_cloud_ice_Truck_allow_upslope_frontier_affinity_factor_0.75.png
        :scale: 75 %
        :align: center

        Cost cloud and frontier, ``o2.options.cost_curve_frontier_affinity_factor=0.75`` ``allow_upslope=True``
        These are the default settings

    .. figure:: _static/code_figures/cost_cloud_ice_Truck_allow_upslope_frontier_affinity_factor_10.png
        :scale: 75 %
        :align: center

        Cost cloud and frontier, ``o2.options.cost_curve_frontier_affinity_factor=10`` ``allow_upslope=True``
        Higher affinity factor follows cloud points more closely

    .. figure:: _static/code_figures/cost_cloud_ice_Truck_no_upslope_frontier_affinity_factor_0.75.png
        :scale: 75 %
        :align: center

        Cost cloud and frontier, ``o2.options.cost_curve_frontier_affinity_factor=0.75`` ``allow_upslope=False``
        Default affinity factor, no up-slope

    """

    import numpy as np
    import pandas as pd
    import common.omega_globals as omega_globals
    from context.cost_clouds import cloud_non_numeric_columns

    if len(cloud) > 1:
        frontier_pts = []

        # drop non-numeric columns so dtypes don't become "object"
        cloud = cloud.drop(columns=cloud_non_numeric_columns, errors='ignore')

        # normalize data (helps with up-slope frontier)
        cloud['y_norm'] = (cloud[y_key] - cloud[y_key].min()) / (cloud[y_key].max() - cloud[y_key].min())
        cloud['x_norm'] = (cloud[x_key] - cloud[x_key].min()) / (cloud[x_key].max() - cloud[x_key].min())

        x_key = 'x_norm'
        y_key = 'y_norm'

        # find frontier starting point, lowest x-value, and add to frontier
        idxmin = cloud[x_key].idxmin()
        frontier_pts.append(cloud.loc[idxmin])
        min_frontier_factor = 0

        if cloud[x_key].min() != cloud[x_key].max():
            while pd.notna(idxmin) and (min_frontier_factor <= 0 or allow_upslope) \
                    and not np.isinf(min_frontier_factor) and not cloud.empty:
                # calculate frontier factor (more negative is more better) = slope of each point relative
                # to prior frontier point if frontier_social_affinity_factor = 1.0, else a "weighted" slope
                cloud = cloud.loc[cloud[x_key] > frontier_pts[-1][x_key]].copy()
                cloud['frontier_factor'] = (cloud[y_key] - frontier_pts[-1][y_key]) / \
                                           (cloud[x_key] - frontier_pts[-1][x_key]) \
                                           ** omega_globals.options.cost_curve_frontier_affinity_factor
                # find next frontier point (lowest slope), if there is one, and add to frontier list
                min_frontier_factor = cloud['frontier_factor'].min()

                if min_frontier_factor > 0 and allow_upslope:
                    # frontier factor is different for up-slope (swap x & y and invert "y")
                    cloud['frontier_factor'] = (frontier_pts[-1][x_key] - cloud[x_key]) / \
                                               (cloud[y_key] - frontier_pts[-1][y_key]) \
                                               ** omega_globals.options.cost_curve_frontier_affinity_factor
                    min_frontier_factor = cloud['frontier_factor'].min()

                if not cloud.empty:
                    if not np.isinf(min_frontier_factor):
                        if len(cloud[cloud['frontier_factor'] == min_frontier_factor]) > 1:
                            # if multiple points with the same slope, take the one with the highest x-value
                            idxmin = cloud[cloud['frontier_factor'] == min_frontier_factor][x_key].idxmax()
                        else:
                            idxmin = cloud['frontier_factor'].idxmin()
                    else:
                        idxmin = cloud['frontier_factor'].idxmax()

                    if pd.notna(idxmin) and (allow_upslope or min_frontier_factor <= 0):
                        frontier_pts.append(cloud.loc[idxmin])

        frontier_df = pd.concat(frontier_pts, axis=1)
        frontier_df = frontier_df.transpose()
        frontier_df['frontier_factor'] = 0
    else:
        frontier_df = cloud
        frontier_df['frontier_factor'] = 0

    return frontier_df.copy()


def print_dict(dict_in, num_tabs=0):
    """
    pretty-print a dict...
    :param dict_in:
    :param num_tabs:
    :return:
    """
    if num_tabs == 0:
        print()

    if type(dict_in) is list or type(dict_in) is not dict:
        print('\t' * num_tabs + str(dict_in))
    else:
        for k in dict_in.keys():
            if type(dict_in[k]) == list:
                if dict_in[k]:
                    print('\t' * num_tabs + k + ':' + str(dict_in[k]))
                else:
                    print('\t' * num_tabs + k)
            else:
                print('\t' * num_tabs + k)
                print_dict(dict_in[k], num_tabs + 1)

    if num_tabs == 0:
        print()


def linspace(min, max, num_values):
    import numpy as np
    ans = np.arange(min, max + (max-min) / (num_values-1), (max-min) / (num_values-1))
    return ans[0:num_values]


partition_dict = dict()
def partition(column_names, num_levels=5, min_constraints=None, max_constraints=None, verbose=False):
    """
    Generate a dataframe with columns from ``column_names``, whose rows sum to 1.0 across the columns, following the
    given constraints

    Args:
        column_names: list of column names
        num_levels: number of values in the column with the lowest span (min value minus max value)
        min_constraints: a scalar value or dict of minimum value constraints with column names as keys
        max_constraints: a scalar value or dict of maximum value constraints with column names as keys
        verbose: if True then the resulting partition will be printed

    Returns:
        A dataframe of the resulting partition

    Example:

        ::

        p = partition_x(['BEV','ICE','PHEV'], min_constraints={'BEV':0.1}, max_constraints={'BEV':0.2, 'PHEV':0.25}, num_levels=5, verbose=True)


    """
    import sys
    import pandas as pd
    import numpy as np

    cache_key = '%s_%s_%s_%s' % (column_names, num_levels, min_constraints, max_constraints)

    if cache_key not in partition_dict:

        if type(column_names) is list:
            num_columns = len(column_names)
        else:
            num_columns = column_names
            column_names = [i for i in range(num_columns)]

        min_level_dict = dict()
        if min_constraints is None:
            min_constraints=dict()

        if type(min_constraints) is float or type(min_constraints) is int:
            min_val = min_constraints
            min_constraints = dict()
            for c in column_names:
                min_constraints[c] = min_val

        max_level_dict = dict()
        if max_constraints is None:
            max_constraints=dict()

        if type(max_constraints) is float or type(max_constraints) is int:
            max_val = max_constraints
            max_constraints = dict()
            for c in column_names:
                max_level_dict[c] = max_constraints

        # initialize min and max level dicts with nominal values
        for c in column_names:
            if c in min_constraints:
                min_level_dict[c] = min_constraints[c]
            else:
                min_level_dict[c] = 0
            if c in max_constraints:
                max_level_dict[c] = max_constraints[c]
            else:
                max_level_dict[c] = 1

        # determine maximum allowed values
        for c in column_names:
            other_columns = set(column_names).difference({c})
            max_level_dict[c] = min(max_level_dict[c], 1 - np.sum([min_level_dict[c] for c in other_columns]))

        # determine minimum allowed values
        for c in column_names:
            other_columns = set(column_names).difference({c})
            min_level_dict[c] = max(min_level_dict[c], 1 - np.sum([max_level_dict[c] for c in other_columns]))

        # calculate span of values (max-min)
        span_dict = dict()
        for c in column_names:
            span_dict[c] = max_level_dict[c] - min_level_dict[c]

        # create list of column names sorted by span, smallest to biggest
        column_names_sorted_by_span = sorted(span_dict, key=span_dict.__getitem__)

        # generate a range of shares for the first n-1 columns
        members = pd.DataFrame()
        for c in column_names_sorted_by_span[:-1]:
            if max_level_dict[c] > min_level_dict[c]:
                members[c] = linspace(min_level_dict[c], max_level_dict[c], num_levels)
            else:
                members[c] = [min_level_dict[c]]

        # generate cartesian product of first n-1 columns
        x = pd.DataFrame()
        for m in members:
            x = cartesian_prod(x, pd.DataFrame(members[m]))

        # calculate values for the last column, honoring it's upper and lower limits
        last = column_names_sorted_by_span[-1]
        x[last] = np.maximum(0, np.maximum(min_level_dict[last], np.minimum(max_level_dict[last], 1 - x.sum(axis=1, skipna=True))))

        # remove rows that don't add up to 1 and get rid of join column ('_')
        x = x.loc[abs(x.sum(axis=1, numeric_only=True) - 1) <= sys.float_info.epsilon]
        if '_' in x:
            x = x.drop('_', axis=1)

        if verbose:
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(x)

        partition_dict[cache_key] = x

    return partition_dict[cache_key]


def unique(vector):
    """
    Find unique values in a list of values, in order of appearance

    :param vector: list of values
    :return: unique values, in order of appearance
    """

    import numpy as np

    indexes = np.unique(vector, return_index=True)[1]
    return [vector[index] for index in sorted(indexes)]


def distribute_by_attribute(obj_list, value, weight_by, distribute_to):
    """

    Args:
        obj_list:
        value:
        weight_by:
        distribute_to:

    Returns:

    """
    attribute_total = 0
    for o in obj_list:
        attribute_total += o.__getattribute__(weight_by)

    for o in obj_list:
        o.__setattr__(distribute_to, value * o.__getattribute__(weight_by) / attribute_total)


def weighted_value(objects, weight_attribute, attribute, attribute_args=None):
    """

    :param objects: list-like of objects
    :param weight_attribute: name of object attribute to weight by (e.g. 'sales')
    :param attribute: name of attribute to calculate weighted value from (e.g. 'footprint_ft2')
    :param attribute_args: arguments to attribute if it's a method (e.g. calendar year)
    :return: weighted value
    """
    weighted_sum = 0
    total = 0
    equal_weight = all([o.__getattribute__(weight_attribute)==0 for o in objects])
    for o in objects:
        if equal_weight:
            weight = 1
        else:
            weight = o.__getattribute__(weight_attribute)
        total += weight
        if callable(o.__getattribute__(attribute)):
            weighted_sum = weighted_sum + o.__getattribute__(attribute)(attribute_args) * weight
        else:
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


def generate_nearby_shares(columns, combos, half_range_frac, num_steps, min_level=0.001, verbose=False):
    """
    Generate a partition of share values in the neighborhood of an initial set of share values
    :param columns: list-like, list of values that represent shares in combo
    :param combos: dict-like, typically a Series or Dataframe that contains the initial set of share values
    :param half_range_frac: search "radius" [0..1], half the search range
    :param num_steps: number of values to divide the search range into
    :param min_level: specifies minimum share value (max will be 1-min_value), e.g. 0.001
    :param verbose: if True then partition dataframe is printed to the console
    :return: partition dataframe, with columns as specified, values near the initial values from combo
    """
    import numpy as np
    import pandas as pd

    dfs = []

    for i in range(0, len(columns) - 1):
        shares = np.array([])
        for idx, combo in combos.iterrows():
            k = columns[i]
            val = combo[k]
            min_val = np.maximum(0, val - half_range_frac)
            max_val = np.minimum(1.0, val + half_range_frac)
            shares = np.append(np.append(shares, np.minimum(1-min_level, np.maximum(min_level,
                            np.linspace(min_val, max_val, num_steps)))), val) # create new share spread and include previous value
        dfs.append(pd.DataFrame({k: unique(shares)}))

    dfx = pd.DataFrame()
    for df in dfs:
        dfx = cartesian_prod(dfx, df)

    dfx = dfx[dfx.sum(axis=1) <= 1]
    dfx[columns[-1]] = 1 - dfx.sum(axis=1)

    if verbose:
        print(dfx)

    return dfx


def generate_constrained_nearby_shares(columns, combos, half_range_frac, num_steps, min_constraints, max_constraints,
                                       verbose=False):
    """
    Generate a partition of share values in the neighborhood of an initial set of share values
    :param columns: list-like, list of values that represent shares in combo
    :param combos: dict-like, typically a Series or Dataframe that contains the initial set of share values
    :param half_range_frac: search "radius" [0..1], half the search range
    :param num_steps: number of values to divide the search range into
    :param min_level: specifies minimum share value (max will be 1-min_value), e.g. 0.001
    :param verbose: if True then partition dataframe is printed to the console
    :return: partition dataframe, with columns as specified, values near the initial values from combo
    """
    import numpy as np
    import pandas as pd

    dfs = []

    for i in range(0, len(columns) - 1):
        shares = np.array([])
        for idx, combo in combos.iterrows():
            k = columns[i]
            val = combo[k]
            min_val = np.maximum(min_constraints[k], val - half_range_frac)
            max_val = np.minimum(max_constraints[k], val + half_range_frac)
            shares = np.append(np.append(shares, np.linspace(min_val, max_val, num_steps)), val) # create new share spread and include previous value
        dfs.append(pd.DataFrame({k: unique(shares)}))

    dfx = pd.DataFrame()
    for df in dfs:
        dfx = cartesian_prod(dfx, df)

    dfx = dfx[dfx.sum(axis=1) <= 1]
    dfx[columns[-1]] = 1 - dfx.sum(axis=1)

    if verbose:
        print(dfx)

    return dfx


def ASTM_round(var, precision=0):
    """
    Rounds numbers as defined in ISO / IEC / IEEE 60559

    Args:
        var: number to be rounded, scalar or pandas Series
        precision: number of decimal places in result

    Returns:
        var rounded using ASTM method with precision decimal places in result

    """
    import numpy as np

    scaled_var = var * (10 ** precision)

    z = np.remainder(scaled_var, 2)

    if type(z) == pd.core.series.Series:
        z.loc[z != 0.5] = 0
    else:
        if abs(z) != 0.5:
            z = 0

    rounded_number = np.round(scaled_var - z) / (10**precision)

    return rounded_number


def CityFUF(miles):
    """

    Args:
        miles: distance travelled in "city" driving, scalar or pandas Series

    Returns:
        City utility factor from SAEJ2841 SEP2010, Table 5 (55/45 city/highway split)

    """
    import numpy as np

    miles_norm = miles/399

    return ASTM_round(1-np.exp(-(
                        1.486e+01 * miles_norm +
                        2.965e+00 * miles_norm ** 2 +
                        -8.405e+01 * miles_norm ** 3 +
                        1.537e+02 * miles_norm ** 4 +
                        -4.359e+01 * miles_norm ** 5 +
                        -9.694e+01 * miles_norm ** 6 +
                        1.447e+01 * miles_norm ** 7 +
                        9.170e+01 * miles_norm ** 8 +
                        -4.636e+01 * miles_norm ** 9
    )), 3)


def HighwayFUF(miles):
    """

    Args:
        miles: distance travelled in "highway" driving, scalar or pandas Series

    Returns:
        Highway utility factor from SAEJ2841 SEP2010, Table 5 (55/45 city/highway split)

    """
    import math
    import numpy as np

    miles_norm = miles/399

    return ASTM_round(1-np.exp(-(
                        4.8e+00 * miles_norm +
                        1.3e+01 * miles_norm ** 2 +
                        -6.5e+01* miles_norm ** 3 +
                        1.2e+02 * miles_norm ** 4 +
                        -1.0e+02 * miles_norm ** 5 +
                        3.1e+01 * miles_norm ** 6
    )), 3)


if __name__ == '__main__':
    import pandas as pd

    # partition test
    part = partition(['a', 'b'], increment=0.1, min_level=0.01)

    # nearby shares test
    share_combo = pd.Series({'a': 0.5, 'b': 0.2, 'c': 0.3})
    column_names = ['a', 'b', 'c']
    dfx = generate_nearby_shares(column_names, share_combo, half_range_frac=0.02, num_steps=5, min_level=0.001, verbose=True)