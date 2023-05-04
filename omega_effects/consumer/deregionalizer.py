"""

**OMEGA effects code de-regionalizer module.**

Used with 'zev' and 'nonzev' market classes.

----

**CODE**

"""


def remove_region_entries(df, attribute, attribute_values_to_remove, string_for_removal, *args):
    """

    Args:
        df (DataFrame): DataFrame containing region specific values to be removed.
        attribute (str): the attribute to act on (e.g., 'market_class_id', 'body_style').
        attribute_values_to_remove (str): the string to search on to remove entries (e.g., 'r1nonzev', 'r2zev').
        string_for_removal (str): the string to replace while keeping entries (e.g., 'r1nonzev', 'r2zev').
        args (str or strs): the attribute values to be deregionalized.

    Returns:
        A new DataFrame with region specific data removed.

    """
    df_return = df.copy()

    for arg in args:
        for suffix in ['BEV', 'ICE']:
            df_return = df_return.loc[df_return[attribute] != f'{arg}_{attribute_values_to_remove}.{suffix}']

    df_return[attribute].replace({f'_{string_for_removal}': ''}, regex=True, inplace=True)

    return df_return


def deregionalize_entries(df, attribute, *args):
    """

    Args:
        df (DataFrame): DataFrame containing region specific values to be deregionalized.
        attribute (str): the attribute to act on (e.g., 'market_class_id', 'body_style').
        args (str or strs): the strings to remove from entries.

    Returns:
        A new DataFrame with region specific data removed.

    """
    df_return = df.copy()

    for arg in args:
        df_return[attribute].replace({f'_{arg}': ''}, regex=True, inplace=True)

    return df_return


def clean_body_styles(df):
    """

    Args:
        df (DataFrame): DataFrame containing body_style entries to be made consistent.

    Returns:
        DataFrame with body_styles consistent with effects inputs.

    """
    body_style_dict = {'sedan_wagon': 'sedan',
                       'cuv_suv_van': 'cuv_suv',
                       }
    for style in body_style_dict:
        df['body_style'].replace({style: body_style_dict[style]}, inplace=True)

    return df
