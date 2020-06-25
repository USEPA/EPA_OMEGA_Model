"""
input_validation.py
===================

Routines to validate input file formats and/or values


"""

import pandas as pd


def validate_template_version_info(filename, input_template_name, input_template_version, verbose=False):

    # read first row of input file as list of values
    version_data = pd.read_csv(filename, header=-1, nrows=1).values.tolist()[0]

    error_list = []
    # check template name
    if 'input_template_name:' not in version_data:
        error_list.append("Can't find input template name in %s" % filename)

    name_index = version_data.index('input_template_name:')
    template_name = version_data[name_index + 1]
    if not template_name == input_template_name:
        error_list.append(
            'Wrong input template name, got "%s", was expecting "%s"' % (template_name, input_template_name))
    elif verbose:
        print('Template name OK')

    # check template version
    if 'input_template_version:' not in version_data:
        error_list.append("Can't find input template version in %s" % filename)

    version_index = version_data.index('input_template_version:')
    template_version = version_data[version_index + 1]
    if not template_version == input_template_version:
        error_list.append(
            'Wrong input template version, got "%f", was expecting "%f"' % (template_version, input_template_version))
    elif verbose:
        print('Template version OK')

    if error_list:
        error_list.insert(0, '\nDetected errors in %s:' % filename)
        if verbose:
            for e in error_list:
                print(e)

    return error_list


def validate_template_columns(filename, input_template_columns, columns, verbose=False):

    error_list = []
    columns_set = set(columns)

    if input_template_columns.intersection(columns_set) == input_template_columns:
        if verbose:
            print('Input columns OK')
    else:
        for c in input_template_columns.difference(columns_set):
            error_list.append('Missing column "%s" in input template' % c)

    if error_list:
        error_list.insert(0, '\nDetected errors in %s:' % filename)
        if verbose:
            for e in error_list:
                print(e)

    return error_list
