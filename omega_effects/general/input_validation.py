"""

**OMEGA effects input validation module.**

----

**CODE**

"""
import sys

from omega_effects.general.general_functions import read_input_file_template_info


def validate_template_version_info(df, input_template_version, input_template_name=None, effects_log=None):
    """

    Args:
        df: the DataFrame to validate.
        input_template_version: the input template version.
        input_template_name: the input template name.
        effects_log: an instance of the EffectsLog class.

    Returns:
        Checks input template header for necessary data.

    """
    items = [input_template_version]
    if input_template_name:
        items.append(input_template_name)
    for item in items:
        if not str(item) in df.columns:
            if effects_log:
                effects_log.logwrite(f'{item} is not a valid template name or version number.')
            sys.exit()

    if effects_log:
        effects_log.logwrite('Template version info is valid.')


def validate_template_column_names(filepath, df, column_names, effects_log=None):
    """
    Args:
        filepath: the Path object to the file.
        df: the DataFrame to validate.
        column_names (list or set): the column names that are necessary.
        effects_log: an instance of the EffectsLog class.

    Returns:
        Checks input tamplate for necessary data columns.

    """
    for column_name in column_names:
        if column_name in df.columns:
            pass
        else:
            if effects_log:
                effects_log.logwrite(f'Missing required {column_name} in {filepath}')
                sys.exit()


def get_module_name(filepath, effects_log):
    """
    Get input file template name.  Can be used to identify the type of input file during simulation initialization
    when more than one type of input file may be provided (e.g. various GHG standards).

    Args:
        filepath: the Path object to the file.
        effects_log: an instance of the EffectsLog class.

    Returns:
        The module name portion of the input file template name

    """
    # read first row of input file as list of values
    template_info = read_input_file_template_info(filepath, effects_log)
    module_name = None
    if 'input_template_name:' not in template_info:
        effects_log.logwrite(f'Missing required template name in {filepath}')

    else:
        name_index = template_info.index('input_template_name:')
        template_name = template_info[name_index + 1]
        module_name = f'omega_effects.{template_name}'

    return module_name
