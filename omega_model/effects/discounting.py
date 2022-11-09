from omega_model import *


def calc_discounted_value(value, rate, calendar_year, discount_to_year, discount_offset):
    """

    Args:
        value: Numeric, the undiscounted value.
        rate: The discount rate to use.
        calendar_year: The year for which "value" applies which determines how many years of discounting to include.
        discount_to_year: The year to which values are to be discounted.
        discount_offset: A factor to address "start-of-year" or "end-of-year" cost accrual.

    Returns:
        The discounted value of "value" at "rate" and in "discount_to_year".

    """
    # no discounting of values that occur prior to "discount_to_year"; exponent controls for that
    exponent = max(0, (calendar_year - discount_to_year + discount_offset))
    disc_value = value / (1 + rate) ** exponent

    return disc_value


def discount_values(dict_of_values):
    """The discount function determines metrics appropriate for discounting (those contained in dict_of_values) and does the discounting
    calculation to a given year and point within that year.

    Parameters:
        dict_of_values: A dictionary of values to be discounted with keys consisting of vehicle_id, calendar_year, age and discount rate.\n

    Returns:
        The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at their internally consistent discount rate.

    Note:
        Important input settings for discounting of monetized values are the "Discount Values to Year" and "Cost Accrual" settings.
        The year to which to discount monetized values is set by the "Discount Values to Year" entry of the input settings.
        The "Cost Accrual" input setting should be set to 'beginning-of-year' or 'end-of-year', where beginning-of-year represents costs
        accruing at time t=0 within the year, and end-of-year represents costs accruing at the end of the year.

        Values that occur prior to the "Discount Values to Year" input setting will not be discounted.

    """
    discount_to_year = omega_globals.options.discount_values_to_year
    cost_accrual = omega_globals.options.cost_accrual
    if cost_accrual == 'beginning-of-year':
        discount_offset = 0
    elif cost_accrual == 'end-of-year':
        discount_offset = 1

    social_discrates = [0.03, 0.07]
    emission_dr25 = '_2.5'
    emission_dr3 = '_3.'
    emission_dr5 = '_5.0'
    emission_dr7 = '_7.0'

    # establish and distinguish attributes
    nested_dict = [n_dict for key, n_dict in dict_of_values.items()][0]
    all_costs = [k for k, v in nested_dict.items() if 'cost' in k]
    emission_costs_dr25 = [arg for arg in all_costs if f'{emission_dr25}' in arg]
    emission_costs_dr3 = [arg for arg in all_costs if f'{emission_dr3}' in arg]
    emission_costs_dr5 = [arg for arg in all_costs if f'{emission_dr5}' in arg]
    emission_costs_dr7 = [arg for arg in all_costs if f'{emission_dr7}' in arg]
    non_emission_costs = [arg for arg in all_costs
                          if arg not in emission_costs_dr25
                          and arg not in emission_costs_dr3
                          and arg not in emission_costs_dr5
                          and arg not in emission_costs_dr7]
    id_args = [k for k, v in nested_dict.items() if 'cost' not in k]

    update_dict = dict()
    for key in dict_of_values.keys():

        vehicle_id = age = series = None

        if len(key) == 3:
            calendar_year, discount_rate, series = key
        else:
            vehicle_id, calendar_year, age, discount_rate = key

        for social_discrate in social_discrates:
            rate_dict = dict()
            for arg in id_args:
                if arg == 'discount_rate':
                    arg_value = social_discrate
                else:
                    arg_value = dict_of_values[key][arg]
                rate_dict.update({arg: arg_value})

            for arg in non_emission_costs:
                arg_value = dict_of_values[key][arg]
                discounted_value = calc_discounted_value(arg_value, social_discrate, calendar_year, discount_to_year, discount_offset)
                rate_dict.update({arg: discounted_value})

            emission_discrate = 0.05
            for arg in emission_costs_dr5:
                arg_value = dict_of_values[key][arg]
                discounted_value = calc_discounted_value(arg_value, emission_discrate, calendar_year, discount_to_year, discount_offset)
                rate_dict.update({arg: discounted_value})

            emission_discrate = 0.03
            for arg in emission_costs_dr3:
                arg_value = dict_of_values[key][arg]
                discounted_value = calc_discounted_value(arg_value, emission_discrate, calendar_year, discount_to_year, discount_offset)
                rate_dict.update({arg: discounted_value})

            emission_discrate = 0.025
            for arg in emission_costs_dr25:
                arg_value = dict_of_values[key][arg]
                discounted_value = calc_discounted_value(arg_value, emission_discrate, calendar_year, discount_to_year, discount_offset)
                rate_dict.update({arg: discounted_value})

            emission_discrate = 0.07
            for arg in emission_costs_dr7:
                arg_value = dict_of_values[key][arg]
                discounted_value = calc_discounted_value(arg_value, emission_discrate, calendar_year, discount_to_year, discount_offset)
                rate_dict.update({arg: discounted_value})

            if len(key) == 3:
                update_dict[(calendar_year, social_discrate, series)] = rate_dict
            else:
                update_dict[(vehicle_id, calendar_year, age, social_discrate)] = rate_dict

    dict_of_values.update(update_dict)
    return dict_of_values
