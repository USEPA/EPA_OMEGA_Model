"""

**OMEGA effects input validation module.**

----

**CODE**

"""
import sys


def validate_template_version_info(df, input_template_name, input_template_version, effects_log=None):
    """

    Args:
        df: the DataFrame to validate.
        input_template_name: the input template name.
        input_template_version: the input template version.
        effects_log: an instance of the EffectsLog class.

    Returns:
        Checks input template header for necessary data.

    """
    for item in [input_template_name, input_template_version]:
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
