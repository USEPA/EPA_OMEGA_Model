"""

**Various functions that may be used throughout OMEGA.**


----

**CODE**

"""

import sys
import pandas as pd
from pandas.api.types import is_numeric_dtype
import numpy as np
import common.omega_globals as omega_globals
from collections.abc import Mapping, Container
from sys import getsizeof

# np.seterr(all='raise')  # for troubleshooting runtime warnings


def get_ip_address():
    """
    Attempt to get "local" IP address(es)

    Example:

    ::

        >>> socket.gethostbyname_ex(socket.gethostname())
        ('mac-mini.local', [], ['127.0.0.1', '192.168.1.20'])

    Returns: list of local IP address(es)

    """
    import socket

    my_ip = []

    retries = 0
    ip_found = False
    while not ip_found and retries < 10:
        try:
            my_ip = socket.gethostbyname_ex(socket.gethostname())[2]
            ip_found = True
        except:
            retries += 1

    if not my_ip.count('127.0.0.1'):
        my_ip.append('127.0.0.1')  # Add support for local loopback interface

    return my_ip


def dataframe_to_numeric(df):
    """
    Convert dataframe columns to numeric (i.e. non-object dtypes) if possible.

    Args:
        df (DataFrame): the dataframe to convert to numeric

    Returns:
        df with numeric columns where possible

    """
    for c in df.columns:
        df[c] = pd.to_numeric(df[c], errors='ignore')

    return df


def series_to_numeric(ser):
    """
    Convert series entries to numeric (i.e. non-object dtypes) if possible.

    Args:
        ser (Series): the series to convert to numeric

    Returns:
        ser with numeric columns where possible

    """
    ser_out = pd.Series(dtype='float64')
    for c in ser.keys():
        ser_out[c] = pd.to_numeric(ser[c], errors='ignore')

    return ser_out


def sales_weight_average_dataframe(df):
    """
        Numeric columns are sales-weighted-averaged except for 'model_year' and columns containing
        'sales', which is the weighting factor.  Non-numeric columns have unique values joined by ':'

    Args:
        df (DataFrame): the dataframe to sales-weight

    Returns:
        DataFrame with sales-weighted-average for numeric columns

    """
    numeric_columns = [c for c in df.columns if is_numeric_dtype(df[c])]
    non_numeric_columns = [c for c in df.columns if not is_numeric_dtype(df[c])]

    avg_df = pd.Series(dtype='float64')

    for c in numeric_columns:
        if 'sales' not in c and c != 'model_year':
            avg_df[c] = np.nansum(df[c].values * df['sales'].values) / np.sum(df['sales'].values)
        elif 'sales' in c:
            avg_df[c] = df[c].sum()

    for c in non_numeric_columns:
        avg_df[c] = ':'.join(df[c].unique())

    return avg_df


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

            # from calc_cost_curve() in vehicles.py
            plot_frontier(self.cost_cloud, '', cost_curve, 'cert_co2e_grams_per_mile', 'new_vehicle_mfr_cost_dollars')

    """
    import common.omega_globals as omega_globals

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
    plt.savefig(omega_globals.options.output_folder + '%s versus %s %s.png' % (y_key, x_key, cost_curve_name))


def calc_frontier(cloud, x_key, y_key, allow_upslope=False, invert_x_axis=True):
    """
    Calculate the frontier of a cloud.

    Args:
        cloud (DataFrame): a set of points to find the frontier of
        x_key (str): name of the column holding x-axis data
        y_key (str): name of the column holding y-axis data
        allow_upslope (bool): allow U-shaped frontier if ``True``
        invert_x_axis (bool): invert x-axis if ``True``

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
    cloud_non_numeric_columns = omega_globals.options.CostCloud.cloud_non_numeric_columns

    # drop non-numeric columns so dtypes don't become "object"
    cloud = cloud.drop(columns=cloud_non_numeric_columns, errors='ignore')

    if max(cloud[y_key].values) == min(cloud[y_key].values) or \
            max(cloud[x_key].values) == min(cloud[x_key].values):
        cloud = cloud.drop_duplicates([x_key, y_key])

        if max(cloud[x_key].values) == min(cloud[x_key].values):
            cloud = cloud.loc[[cloud[y_key].idxmin()]]
        elif max(cloud[y_key].values) == min(cloud[y_key].values):
            cloud = cloud.loc[[cloud[x_key].idxmax()]]

    if len(cloud) > 1:
        frontier_pts = []

        if invert_x_axis:
            x_sign = -1
        else:
            x_sign = 1

        # normalize data (helps with up-slope frontier)
        cloud['y_norm'] = ((cloud[y_key].values - min(cloud[y_key].values)) /
                          (max(cloud[y_key].values) - min(cloud[y_key].values)))
        cloud['x_norm'] = x_sign * ((cloud[x_key].values - min(cloud[x_key].values)) /
                          (max(cloud[x_key].values) - min(cloud[x_key].values)))

        x_key = 'x_norm'
        y_key = 'y_norm'

        # find frontier starting point, lowest x-value, and add to frontier
        idxmin = cloud[x_key].idxmin()
        frontier_pts.append(cloud.loc[idxmin])
        min_frontier_factor = 0

        if min(cloud[x_key].values) != max(cloud[x_key].values):
            while pd.notna(idxmin) and (min_frontier_factor <= 0 or allow_upslope) \
                    and not np.isinf(min_frontier_factor) and not cloud.empty:

                prior_x = frontier_pts[-1][x_key]
                prior_y = frontier_pts[-1][y_key]

                # calculate frontier factor (more negative is more better) = slope of each point relative
                # to prior frontier point if frontier_social_affinity_factor = 1.0, else a "weighted" slope
                cloud = cull_cloud(cloud, prior_x, x_key)

                if not cloud.empty:
                    calc_frontier_factor_down(cloud, prior_x, prior_y, x_key, y_key)
                    min_frontier_factor = min(cloud['frontier_factor'].values)

                    if min_frontier_factor > 0 and allow_upslope:
                        calc_frontier_factor_up(cloud, prior_x, prior_y, x_key, y_key)
                        min_frontier_factor = min(cloud['frontier_factor'].values)

                if not cloud.empty:
                    idxmin = get_idxmin(cloud, min_frontier_factor, x_key)

                    if pd.notna(idxmin) and (allow_upslope or min_frontier_factor <= 0):
                        frontier_pts.append(cloud.loc[idxmin])

        if invert_x_axis:
            frontier_pts.reverse()

        frontier_df = pd.concat(frontier_pts, axis=1).transpose()
    else:
        frontier_df = cloud

    # CU

    return frontier_df  # was frontier_df.copy()


def get_idxmin(cloud, min_frontier_factor, x_key):
    """
    Return the index of the minimum value of the ``cloud`` ``frontier_factor``.

    Args:
        cloud (DataFrame): a set of points to find the frontier of
        min_frontier_factor (float): the minimum value of the frontier_factor
        x_key (str): ``cloud`` column name

    Returns:
        The index of the minimum value of the ``cloud`` ``frontier_factor``.

    """
    if not np.isinf(min_frontier_factor):
        if len(cloud[cloud['frontier_factor'].values == min_frontier_factor]) > 1:
            # if multiple points with the same slope, take the one with the highest x-value
            # CU
            idxmin = cloud.index[np.argmax(cloud[cloud['frontier_factor'].values == min_frontier_factor][x_key].values)]
        else:
            # CU
            idxmin = cloud.index[np.argmin(cloud['frontier_factor'])]
    else:
        # CU
        idxmin = cloud.index[np.argmax(cloud['frontier_factor'].values)]

    return idxmin


def calc_frontier_factor_up(cloud, prior_x, prior_y, x_key, y_key):
    """
    Calculate the frontier factor for an up-sloping cloud of points.

    Args:
        cloud (DataFrame): a set of points to find the frontier of
        prior_x (float): x-axis value of prior frontier point
        prior_y (float): y-axis value of prior frontier point
        x_key (str): name of the column holding x-axis data
        y_key (str): name of the column holding y-axis data

    Returns:
        Nothing, calculates ``frontier_factor`` column of ``cloud``.

    """
    # frontier factor is different for up-slope (swap x & y and invert "y")
    cloud['frontier_factor'] = (prior_x - cloud[x_key].values) / (cloud[y_key].values - prior_y) \
                               ** omega_globals.options.cost_curve_frontier_affinity_factor


def calc_frontier_factor_down(cloud, prior_x, prior_y, x_key, y_key):
    """
    Calculate the frontier factor for an down-sloping cloud of points.

    Args:
        cloud (DataFrame): a set of points to find the frontier of
        prior_x (float): x-axis value of prior frontier point
        prior_y (float): y-axis value of prior frontier point
        x_key (str): name of the column holding x-axis data
        y_key (str): name of the column holding y-axis data

    Returns:
        Nothing, calculates ``frontier_factor`` column of ``cloud``.

    """
    cloud['frontier_factor'] = (cloud[y_key].values - prior_y) / (cloud[x_key].values - prior_x) \
                               ** omega_globals.options.cost_curve_frontier_affinity_factor


def cull_cloud(cloud, prior_x, x_key):
    """
    Remove points from a dataframe where the given column (``x_key``) is above a certain value (``prior_x``).

    Args:
        cloud (dataframe): the dataframe to cull
        prior_x (float): the threshold value
        x_key (str): cloud column name

    Returns:
        ``cloud`` with culled points removed

    """
    cloud = cloud.loc[cloud[x_key].values > prior_x]  # .copy()
    return cloud


def sum_dict(dict_in, include=None, exclude=None):
    """
    Add up all terms in a dict given the ``include`` and ``exclude`` constraints.

    Args:
        dict_in (numeric dict_like): the object with elements to sum
        include (str): include term in sum if ``include`` in dict key
        exclude (str): exclude term from some if ``exclude`` in dict key

    Returns:
        Sum of terms in ``dict_in`` given the include and exclude constraints.

    """
    keys = sorted(dict_in.keys())
    if include is not None:
        keys = [k for k in keys if include in k]
    if exclude is not None:
        keys = [k for k in keys if exclude not in k]

    return sum([dict_in[k] for k in keys])


def print_keys(dict_in, include=None, exclude=None, values=True):
    """
    Print some or all keys (and optionally values) in a dict-like object

    Args:
        dict_in (dict-like): the object with keys to print
        include (str): a substring that must be present, if provided
        exclude (str): a substring that must not be present, if provided
        values (bool): print values if ``True``

    """
    keys = sorted(dict_in.keys())
    if include is not None:
        keys = [k for k in keys if include in k]
    if exclude is not None:
        keys = [k for k in keys if exclude not in k]

    max_key_len = max([len(k) for k in keys])

    for k in keys:
        if values:
            format_str = '%' + '%d' % max_key_len + 's: %s'
            print(format_str % (k, dict_in[k]))
        else:
            print(k)

    return keys


def print_dict(dict_in, num_tabs=0, to_string=False):
    """
    Attempt to printy-print a dictionary to the Python console.

    Args:
        dict_in (dict): dictionary to print
        num_tabs (int): optional argument, used to indent subsequent layers of the dictionary
        to_string (Bool): if True then result will be returned as a printable string, instead of printed to the console

    Returns:
        print_dict string if to_string==True

    """
    s = ''

    if num_tabs == 0:
        s += '\n'
        if type(dict_in) is pd.Series:
            dict_in = dict_in.to_dict()

    if type(dict_in) is list or type(dict_in) is not dict:
        s += '\t' * num_tabs + str(dict_in) + '\n'
    else:
        try:
            keys = sorted(dict_in.keys())
        except:
            keys = dict_in.keys()

        for k in keys:
            if type(dict_in[k]) is list:
                if dict_in[k]:
                    s += '\t' * num_tabs + str(k) + ':' + str(dict_in[k]) + '\n'
                else:
                    s += '\t' * num_tabs + str(k) + '\n'
            else:
                s += '\t' * num_tabs + str(k) + '\n'
                s += print_dict(dict_in[k], num_tabs + 1, to_string=True)

    if num_tabs == 0:
        s += '\n'

    if not to_string:
        print(s[:-1])

    if to_string:
        return s


def print_list(list_in):
    """
    Print the given list, one line per item

    Args:
        list_in (list): the list to print

    """
    for i in list_in:
        print(i)
    print()


def linspace(min_val, max_val, num_values):
    """
    Create a list of num_values evenly spaced values between min and max.  Based on ``Matlab`` linspace command.

    Args:
        min_val (numeric): the minimum value
        max_val (numeric): the maximum value
        num_values (int): the total number of values to return

    Returns:
        A list of evenly spaced values between min and max

    """
    ans = np.arange(min_val, max_val + (max_val - min_val) / (num_values - 1), (max_val - min_val) / (num_values - 1))
    return ans[0:num_values]


partition_dict = dict()


def partition(column_names, num_levels=5, min_constraints=None, max_constraints=None, verbose=False):
    """
    Generate a dataframe with columns from ``column_names``, whose rows sum to 1.0 across the columns, following the
    given constraints

    Args:
        column_names (list | int): list of column names or number of columns
        num_levels (int): number of values in the column with the lowest span (min value minus max value)
        min_constraints (int | dict): a scalar value or dict of minimum value constraints with column names as keys
        max_constraints (int | dict): a scalar value or dict of maximum value constraints with column names as keys
        verbose (bool): if ``True`` then the resulting partition will be printed

    Returns:
        A dataframe of the resulting partition

    Example:

        ::

            p = partition_x(['BEV','ICE','PHEV'],
                min_constraints={'BEV':0.1},
                max_constraints={'BEV':0.2, 'PHEV':0.25},
                num_levels=5, verbose=True)


    """
    cache_key = '%s_%s_%s_%s' % (column_names, num_levels, min_constraints, max_constraints)

    if cache_key not in partition_dict:

        if type(column_names) is int:
            column_names = [i for i in range(column_names)]

        min_level_dict = dict()
        if min_constraints is None:
            min_constraints = dict()

        if type(min_constraints) is float or type(min_constraints) is int:
            min_val = min_constraints
            min_constraints = dict()
            for c in column_names:
                min_constraints[c] = min_val

        max_level_dict = dict()
        if max_constraints is None:
            max_constraints = dict()

        if type(max_constraints) is float or type(max_constraints) is int:
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
            other_columns = sorted(list(set(column_names).difference({c})))
            max_level_dict[c] = max(0, min(max_level_dict[c], 1 - np.sum([min_level_dict[c] for c in other_columns])))

        # determine minimum allowed values
        for c in column_names:
            other_columns = sorted(list(set(column_names).difference({c})))
            min_level_dict[c] = min(1, max(min_level_dict[c], 1 - np.sum([max_level_dict[c] for c in other_columns])))

        # calculate span of values (max-min)
        span_dict = dict()
        for c in column_names:
            span_dict[c] = max_level_dict[c] - min_level_dict[c]

        # create list of column names sorted by span, smallest to biggest
        column_names_sorted_by_span = sorted(span_dict, key=span_dict.__getitem__)

        # generate a range of shares for the first n-1 columns
        scalars_only = True
        members = dict()
        for c in column_names_sorted_by_span[:-1]:
            if max_level_dict[c] > min_level_dict[c]:
                members[c] = linspace(min_level_dict[c], max_level_dict[c], num_levels)
                scalars_only = False
            else:
                members[c] = min_level_dict[c]

        if scalars_only:
            members = pd.DataFrame.from_dict([members])
        else:
            members = pd.DataFrame.from_dict(members)

        # generate cartesian product of first n-1 columns
        x = pd.DataFrame()
        for m in members:
            x = cartesian_prod(x, pd.DataFrame(members[m]))

        # calculate values for the last column, honoring it's upper and lower limits
        last = column_names_sorted_by_span[-1]
        x[last] = np.maximum(0, np.maximum(min_level_dict[last],
                                           np.minimum(max_level_dict[last], 1.0 - x.sum(axis=1, skipna=True))))

        # drop duplicate rows:  # RV
        x = x.drop_duplicates()

        # remove rows that don't add up to 1 and get rid of join column ('_')
        maybe_x = x.loc[abs(x.sum(axis=1, numeric_only=True) - 1) <= sys.float_info.epsilon]

        if not maybe_x.empty:
            x = maybe_x

        if '_' in x:
            x = x.drop('_', axis=1)

        if verbose:
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(x)

        partition_dict[cache_key] = x

    return partition_dict[cache_key]


def unique(vector):
    """
    Return unique values in a list of values, in order of appearance.

    Args:
        vector ([numeric]): list of values

    Returns:
        List of unique values, in order of appearance

    """
    indexes = np.unique(vector, return_index=True)[1]
    return [vector[index] for index in sorted(indexes)]


def distribute_by_attribute(obj_list, value, weight_by, distribute_to):
    """
    Used to take a value and distribute it to source values by a weight factor.  Used to assign composite attributes
    to source objects, e.g. composite vehicle sales to source vehicle sales, etc.  The weight factor is normalized
    by the sum of the object weights.  For example, if there were two objects, one with a 0.2 weight and one with a 0.1
    weight, the first object would get 2/3 of the value and the second would get 1/3 of the value.

    Args:
        obj_list ([objs]): list of objects to distribute to
        value (numeric): the value to to distribute
        weight_by (str): the name of the object attribute to use as a weight factor
        distribute_to (str): the name of the object attribute to distribute to

    """
    attribute_total = 0
    for o in obj_list:
        attribute_total += o.__getattribute__(weight_by)

    for o in obj_list:
        o.__setattr__(distribute_to, value * o.__getattribute__(weight_by) / attribute_total)


def weighted_value(objects, weight_attribute, attribute, attribute_args=None):
    """
    Calculate a weighted value from values taken from a set of objects.  The contribution of each object is normalized
    by the sum of the object weight attribute values.

    Args:
        objects ([objs]): list of source objects
        weight_attribute (str): the name of the object attribute to weight by (e.g. 'sales')
        attribute (str): the name of the attribute to calculate the weighted value of, e.g. vehicle CO2e g/mi, etc
        attribute_args: arguments to the attribute, if the attribute is a method or function, e.g. calendar_year

    Returns:
        The weighted value

    """
    weighted_sum = 0
    total = 0
    equal_weight = all([o.__getattribute__(weight_attribute) == 0 for o in objects])
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


# CU unweighted_value()


def cartesian_prod(left_df, right_df):
    """
    Calculate cartesian product of the dataframe rows.

    Args:
        left_df (DataFrame): 'left' dataframe
        right_df (DataFrame): 'right' dataframe

    Returns:
        Cartesian product of the dataframe rows (the combination of every row in the left dataframe with every row in
        the right dataframe).

    """
    if left_df.empty:
        return right_df
    else:
        return pd.merge(left_df, right_df, how='cross')


def generate_constrained_nearby_shares(columns, combo, half_range_frac, num_steps, min_constraints, max_constraints,
                                       verbose=False):
    """
    Generate a partition of share values in the neighborhood of an initial set of share values.

    See Also:

        ``compliance_strategy.create_compliance_options()``

    Args:
        columns ([strs]): list of values that represent shares in combo
        combo (Series): Series that contains the initial set of share values
        half_range_frac (float): search "radius" [0..1], half the search range
        num_steps (int): number of values to divide the search range into
        min_constraints (dict): minimum partition constraints [0..1], by column name
        max_constraints (dict): maximum partition constraints [0..1], by column name
        verbose (bool): if ``True`` then partition dataframe is printed to the console

    Returns:
        DataFrame of partion values.

    Example:

        ::

            >>>columns
            ['producer_share_frac_non_hauling.BEV', 'producer_share_frac_non_hauling.ICE']

            >>>combos
                  veh_non_hauling.BEV.car_co2e_gpmi  ...  slope
            1510                          15.91862  ...      0
            2135                          15.91862  ...      0
            [2 rows x 79 columns]

            >>>half_range_frac
            0.33

            >>>num_steps
            5

            >>>min_constraints
            {'producer_share_frac_non_hauling.BEV': 0.001, 'producer_share_frac_non_hauling.ICE': 0}

            >>>max_constraints
            {'producer_share_frac_non_hauling.BEV': 1, 'producer_share_frac_non_hauling.ICE': 1}

            Returns:
               producer_share_frac_non_hauling.BEV  producer_share_frac_non_hauling.ICE
            0                               0.0010                               0.9990
            1                               0.0835                               0.9165
            2                               0.1660                               0.8340
            3                               0.2485                               0.7515
            4                               0.3310                               0.6690
            5                               0.0010                               0.9990

    Note:
        In the example above, there appear to be repeated rows, however the values are unique in floating-point terms,
        e.g. 0.00100000000000000002 versus 0.00100000000000000089

    """
    dfs = []

    machine_resolution = omega_globals.share_precision

    # reorder columns such that last column is an ALT since it equals one minus the sum of the prior columns and we
    # don't want to blow the constraints on the NO_ALTs
    alt_columns = [c for c in columns if 'ALT' in c.split('.')]
    no_alt_columns = [c for c in columns if 'NO_ALT' in c.split('.')]

    columns = no_alt_columns + alt_columns

    if all([min_constraints[c] == max_constraints[c] or
            max_constraints[c] - min_constraints[c] <= np.power(10.0, -machine_resolution/2) for c in columns]):
        dfx = pd.DataFrame()
        for c in columns[:-1]:
            dfx[c] = np.atleast_1d(max_constraints[c])
        dfx.loc[:, columns[-1]] = np.maximum(0.0, 1.0 - dfx.sum(axis=1)[0])
        if verbose:
            print('%.20f' % dfx.sum(axis=1)[0])
    else:
        for i in range(0, len(columns) - 1):
            shares = np.array([])

            k = columns[i]
            val = combo[k]
            min_val = ASTM_round(np.maximum(min_constraints[k], val - half_range_frac), machine_resolution)
            max_val = ASTM_round(np.minimum(max_constraints[k], val + half_range_frac), machine_resolution)
            if min_val == max_val:
                shares = np.append(shares, ASTM_round(val, machine_resolution))
            else:
                if omega_globals.options.producer_compliance_search_multipoint:
                    # create new share spread and include previous value
                    shares = np.append(np.append(shares, np.linspace(min_val, max_val, num_steps)),
                                       ASTM_round(val, machine_resolution))
                else:
                    shares = np.append(shares, np.linspace(min_val, max_val, num_steps))

            dfs.append(pd.DataFrame({k: np.unique(shares)}))

        dfx = pd.DataFrame()
        for df in dfs:
            dfx = cartesian_prod(dfx, df)

        dfx = dfx[dfx.sum(axis=1).values <= 1]
        dfx.loc[:, columns[-1]] = np.maximum(0.0, 1 - dfx.sum(axis=1).values)

        if dfx.empty:
            raise Exception('empty partition!! :(')

    dfx = dfx.drop_duplicates()

    if verbose:
        print(dfx)

    return dfx


def ASTM_round(var, precision=0):
    """
    Rounds numbers as defined in ISO / IEC / IEEE 60559

    Args:
        var (float, Series): number to be rounded, scalar or pandas Series
        precision (int): number of decimal places in result

    Returns:
        var rounded using ASTM method with precision decimal places in result

    """

    if type(var) is list:
        var = np.array(var)

    scaled_var = var * (10 ** precision)

    z = np.remainder(scaled_var, 2)

    if type(z) is pd.core.series.Series or type(z) is np.ndarray:
        if type(z) is np.ndarray:
            z = pd.Series(z)
        z.loc[z != 0.5] = 0
    else:
        if abs(z) != 0.5:
            z = 0

    rounded_number = np.round(scaled_var - z) / (10**precision)

    return rounded_number


def calc_roadload_hp(A_LBSF, B_LBSF, C_LBSF, MPH):
    """
    Calculate roadload horsepower from ABC coefficients and vehicle speed (MPH)

    Args:
        A_LBSF (float): "A" coefficient, lbs
        B_LBSF (float): "B" coefficient, lbs/mph
        C_LBSF (float): "C" coefficient, lbs/mph^2
        MPH (float(s)): scalar float, numpy array or Series of vehicle speed(s), mph

    Returns:
        Roadload horsepower at the given vehicle speed

    """
    KW2HP = 1 / 0.746
    N2LBF = 0.224808943
    KMH2MPH = .621371
    MPH2MPS = 1 / KMH2MPH * 1000.0 / 3600.0
    MPS2MPH = 1 / MPH2MPS

    A_N = A_LBSF / N2LBF
    B_N = B_LBSF / (N2LBF / MPS2MPH)
    C_N = C_LBSF / (N2LBF / MPS2MPH / MPS2MPH)
    MPS = MPH / MPS2MPH

    roadload_force_N = A_N + B_N * MPS + C_N * MPS**2
    roadload_power_kW = roadload_force_N * MPS / 1000

    # roadload_force_lbs = roadload_force_N * N2LBF
    roadload_power_hp = roadload_power_kW * KW2HP

    return roadload_power_hp


def send_text(dest, message, email, password):
    """

    SMS Gateways for each Carrier
    AT&T: [number]@txt.att.net
    Sprint: [number]@messaging.sprintpcs.com or [number]@pm.sprint.com
    T-Mobile: [number]@tmomail.net
    Verizon: [number]@vtext.com
    Boost Mobile: [number]@myboostmobile.com
    Cricket: [number]@sms.mycricket.com
    Metro PCS: [number]@mymetropcs.com
    Tracfone: [number]@mmst5.tracfone.com
    U.S. Cellular: [number]@email.uscc.net
    Virgin Mobile: [number]@vmobl.com

    Args:
        dest (str): e.g. '8005552323@myboostmobile.com'
        message (str): the message to send
        email (str): the email address of the email server to use, e.g. 'my_email@gmail.com'
        password (str): the password for the email account, recommend setting up an app-specific password

    """
    import time
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    sms_gateway = dest

    pas = password

    # The server we use to send emails in our case it will be gmail but every email provider has a different smtp
    # and port is also provided by the email provider.
    smtp = "smtp.gmail.com"
    port = 587
    # This will start our email server
    server = smtplib.SMTP(smtp, port)
    # Starting the server
    server.starttls()
    # Now we need to login
    server.login(email, pas)

    # Now we use the MIME module to structure our message.
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = sms_gateway

    # Make sure you add a new line in the subject
    timestamp_str = time.strftime('%m/%d/%Y %H:%M:%S')
    msg['Subject'] = "%s" % timestamp_str + "\n"

    # Make sure you also add new lines to your body
    if not message.endswith('\n'):
        message = message + '\n'

    # and then attach that body furthermore you can also send html content.
    msg.attach(MIMEText(message, 'plain'))
    sms = msg.as_string()
    server.sendmail(email, sms_gateway, sms)

    # lastly quit the server
    server.quit()


def deep_getsizeof(o, ids=None):
    """
    Find the memory footprint of a Python object in bytes

    This is a recursive function that drills down a Python object graph
    like a dictionary holding nested dictionaries with lists of lists
    and tuples and sets.

    The sys.getsizeof function does a shallow size of only. It counts each
    object inside a container as pointer only regardless of how big it
    really is.

    Args:
        o (obj): the object
        ids (set): used to hold object id(s)

    Returns:
        The memory footprint of the object in bytes

    """
    if ids is None:
        ids = set()

    d = deep_getsizeof
    if id(o) in ids:
        return 0
    r = getsizeof(o)
    ids.add(id(o))
    if isinstance(o, str) or isinstance(0, str):
        return r
    if isinstance(o, Mapping):
        return r + sum(d(k, ids) + d(v, ids) for k, v in o.iteritems())
    if isinstance(o, Container):
        return r + sum(d(x, ids) for x in o)

    return r


if __name__ == '__main__':
    try:
        # partition test
        part = partition(['a', 'b'], verbose=True)

        # nearby shares test
        share_combo = pd.DataFrame({'a': [0.5], 'b': [0.2], 'c': [0.3]})
        column_names = ['a', 'b', 'c']

        dfx2 = partition(['BEV', 'ICE', 'NO_ALT_BEV', 'NO_ALT_ICE'],
                         min_constraints={'NO_ALT_BEV': 0.01},
                         max_constraints={'NO_ALT_BEV': 0.01}, verbose=True)

    except:
        import os
        import traceback
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
