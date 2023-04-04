"""

**Routines to validate input file formats and/or values.**

Used during the initialization process.

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
import hashlib

import pandas as pd


def get_template_columns(filename):
    """

    Args:
        filename (str): name of the file from which to get the input columns

    Returns:

    """
    df = pd.read_csv(filename, skiprows=1, nrows=1)
    return df.columns


def get_template_name(filename):
    """
    Get input file template name.  Can be used to identify the type of input file during simulation initialization
    when more than one type of input file may be provided (e.g. various GHG standards).

    Args:
        filename (str): name of the file from which to get the input template name

    Returns:
        The input file template name

    """
    # read first row of input file as list of values
    version_data = pd.read_csv(filename, header=None, nrows=1).values.tolist()[0]
    if 'input_template_name:' not in version_data:
        template_name = None
    else:
        name_index = version_data.index('input_template_name:')
        template_name = version_data[name_index + 1]

    return template_name


def validate_template_version_info(filename, input_template_name, input_template_version, verbose=False):
    """
    Reads the template version infor from an input file and validates the template name and version number.

    Args:
        filename (str): name of the input file to validate
        input_template_name (str): target template name
        input_template_version (numeric): target template version
        verbose (bool): enable additional console and logfile output if True

    Returns:
        List of template errors, else empty list on success

    """
    # read first row of input file as list of values
    version_data = pd.read_csv(filename, header=None, nrows=1).values.tolist()[0]

    df = pd.read_csv(filename, skiprows=1)

    cols = [col for col in df if 'Unnamed' not in col]

    df = df[cols]

    df_hash = hashlib.sha1(pd.util.hash_pandas_object(df).values).hexdigest()

    omega_globals.options.inputfile_metadata.append([file_io.get_filepath(filename), file_io.get_basename(filename),
                                                     df_hash] + version_data)

    if verbose:
        omega_log.logwrite('Validating Template Version [%s]' % filename)

    error_list = []
    # check template name
    if 'input_template_name:' not in version_data:
        error_list.append("*** Can't find input template name in %s ***" % filename)

    template_name = get_template_name(filename)

    if not template_name == input_template_name:
        error_list.append(
            '*** Wrong input template name, got "%s", was expecting "%s" ***' % (template_name, input_template_name))
    elif verbose:
        omega_log.logwrite('Template name OK')

    # check template version
    if 'input_template_version:' not in version_data:
        error_list.append("*** Can't find input template version in %s ***" % filename)

    version_index = version_data.index('input_template_version:')
    template_version = version_data[version_index + 1]
    if not template_version == input_template_version:
        error_list.append(
            '*** Wrong input template version, got "%f", was expecting "%f" ***' %
            (template_version, input_template_version))
    elif verbose:
        omega_log.logwrite('Template version OK')

    if error_list:
        error_list.insert(0, '\n*** Detected errors in %s ***' % filename)
        omega_log.logwrite(error_list)
    elif verbose:
        omega_log.logwrite('')

    return error_list


def validate_template_column_names(filename, input_template_columns, columns, verbose=False):
    """
    Validate input columns against target template columns.

    Args:
        filename (str): name of the input file to validate
        input_template_columns ([strs]): list of target template column names
        columns ([strs]): list of column names to validate
        verbose: enable additional console and logfile output if True

    Returns:
        List of column name errors, else empty list on success

    """
    error_list = []
    columns_set = set(columns)

    if verbose:
        omega_log.logwrite('Validating Columns [%s]' % filename)

    if input_template_columns.intersection(columns_set) == input_template_columns:
        if verbose:
            omega_log.logwrite('Input columns OK')
    else:
        for c in input_template_columns.difference(columns_set):
            error_list.append('*** Missing column "%s" in input template ***' % c)

    if error_list:
        error_list.insert(0, '\n*** Detected errors in %s ***' % filename)
        omega_log.logwrite(error_list)
    elif verbose:
        omega_log.logwrite('')

    return error_list


def _validate_dataframe_column(df, column_name, allowed_values, header_lines=2):
    """
    Validate a dataframe column against allowed values

    Args:
        df (DataFrame): pandas dataframe containing data to validate
        column_name (str): name of the dataframe column
        allowed_values (iterable): a list / set of allowed values
        header_lines (int): number of header lines in the input file,
            offset used to calculate the row number of the error

    Returns:
        Empty list on success or list of errors on failure

    """
    error_list = []

    valid = np.array([v in allowed_values for v in df[column_name].values])

    # if any values are bad, report back which ones/which rows
    if not all(valid):
        bad_indices = np.where(~valid)[0]
        for i in bad_indices:
            error_list += ['unexpected value "%s" found in column "%s" at row %d, expected value in %s' %
                           (df[column_name].iloc[i], column_name, i + header_lines + 1, allowed_values)]

    return error_list


def validate_dataframe_columns(df, validation_dict, error_source=None, header_lines=2):
    """
    Validate dataframe column(s) against allowed values

    Args:
        df (DataFrame): pandas dataframe containing data to validate
        validation_dict (dict): dict of one or more column name / allowed value pairs
        error_source (str): typically the name of the file containing the error
        header_lines (int): header_lines (int): number of header lines in the input file,
            offset used to calculate the row number of the error

    Returns:
        Empty list on success or list of errors on failure

    """
    error_list = []

    for column_name, allowed_values in validation_dict.items():
        error_list += _validate_dataframe_column(df, column_name, allowed_values, header_lines)

    if error_list and error_source:
        error_list.insert(0, '\n*** Detected errors in %s ***' % error_source)

    return error_list
