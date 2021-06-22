"""

**Routines to validate input file formats and/or values.**

Used during the initialization process.

----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *

import pandas as pd


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
            '*** Wrong input template version, got "%f", was expecting "%f" ***' % (template_version, input_template_version))
    elif verbose:
        omega_log.logwrite('Template version OK')

    if error_list:
        error_list.insert(0, '\n*** Detected errors in %s ***' % filename)
        omega_log.logwrite(error_list)
    elif verbose:
        omega_log.logwrite('')

    return error_list


def validate_template_columns(filename, input_template_columns, columns, verbose=False):
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
