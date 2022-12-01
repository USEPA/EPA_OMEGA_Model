from omega_model import *

from omega_model.effects.discounting import discount_values


def calc_annualized_value(present_value, rate, periods, annualized_offset):
    """

    Args:
        present_value: Numeric, the undiscounted value.
        rate: The discount rate to use.
        periods: Integer; the number of periods (years) over which to annualize the present_value.
        annualized_offset: A factor to address "start-of-year" or "end-of-year" cost accrual.

    Returns:
        The annualized value of "present_value" at "rate" and including years through calendar_year.

    """
    annlzd_value = present_value * rate * (1 + rate) ** periods \
                   / ((1 + rate) ** (periods + annualized_offset) - 1)

    return annlzd_value


def calc_annual_values(input_df, args):
    """

    Args:
        input_df: A DataFrame containing calendar year, model year, age undiscounted and discounted values to be summed
        for annual values in each calendar year.
        args: A list of monetized attributes (strings) to be summed.

    Returns:
        A DataFrame of annual values based on the input_df.

    """
    calendar_years = [yr for yr in input_df['calendar_year'].unique()]
    discount_rates = [rate for rate in input_df['discount_rate'].unique()]
    session_names = [name for name in input_df['session_name'].unique()]

    annual_values = pd.DataFrame()
    for session_name in session_names:
        for discount_rate in discount_rates:
            for calendar_year in calendar_years:
                periods = 1
                annual_value = pd.DataFrame(input_df.loc[(input_df['calendar_year'] == calendar_year)
                                                         & (input_df['discount_rate'] == discount_rate), args]
                                            .sum()
                                            ).transpose()
                annual_value.insert(0, 'periods', periods)
                annual_value.insert(0, 'series', 'AnnualValue')
                annual_value.insert(0, 'discount_rate', discount_rate)
                annual_value.insert(0, 'calendar_year', calendar_year)
                annual_value.insert(0, 'session_name', session_name)
                annual_values = pd.concat([annual_values, annual_value], axis=0, ignore_index=True)

    annual_values.set_index(pd.Series(
        zip(annual_values['calendar_year'], annual_values['discount_rate'], annual_values['series'])),
        inplace=True)

    return annual_values.to_dict('index')


def calc_present_values(input_df, args):
    """

    Args:
        input_df: A DataFrame containing annual discounted values to be summed for present values in each calendar year.
        args: A list of monetized attributes (strings) to be summed.

    Returns:
        A DataFrame of present values based on the discounted annual values in input_df.

    """
    discount_to_year = omega_globals.options.discount_values_to_year
    cost_accrual = omega_globals.options.cost_accrual
    if cost_accrual == 'beginning-of-year':
        discount_offset = 0
    elif cost_accrual == 'end-of-year':
        discount_offset = 1

    calendar_years = [yr for yr in input_df['calendar_year'].unique()]
    discount_rates = [rate for rate in input_df['discount_rate'].unique() if rate != 0]
    session_names = [name for name in input_df['session_name'].unique()]

    present_values = pd.DataFrame()
    for session_name in session_names:
        for discount_rate in discount_rates:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    present_value = pd.DataFrame(input_df.loc[(input_df['calendar_year'] == calendar_year)
                                                              & (input_df['discount_rate'] == discount_rate)
                                                              & (input_df['series'] == 'AnnualValue'), args]
                                                 )
                else:
                    present_value = pd.DataFrame(input_df.loc[((input_df['calendar_year'] >= discount_to_year)
                                                              & (input_df['calendar_year'] <= calendar_year))
                                                              & (input_df['discount_rate'] == discount_rate)
                                                              & (input_df['series'] == 'AnnualValue'), args]
                                                 .sum()
                                                 ).transpose()
                present_value.insert(0, 'periods', periods)
                present_value.insert(0, 'series', 'PresentValue')
                present_value.insert(0, 'discount_rate', discount_rate)
                present_value.insert(0, 'calendar_year', calendar_year)
                present_value.insert(0, 'session_name', session_name)
                present_values = pd.concat([present_values, present_value], axis=0, ignore_index=True)

    present_values.set_index(pd.Series(
        zip(present_values['calendar_year'], present_values['discount_rate'], present_values['series'])),
        inplace=True)

    return present_values.to_dict('index')


def calc_present_and_annualized_values(dict_of_values, calendar_years):
    """

    Parameters:
        dict_of_values: Dictionary; provides the values to be summed and annualized.
        calendar_years: List of calendar years starting with analysis_initial_year and ending with analysis_final_year

    Returns:
        A dictionary of annual, present and annualized values based on the dict_of_values.

    Note:
        Values that occur prior to the "Discount Values to Year" input setting will not be discounted and their present and
        annualized values will equal the annual value.

    """
    discount_to_year = omega_globals.options.discount_values_to_year
    cost_accrual = omega_globals.options.cost_accrual
    discount_offset = 1
    annualized_offset = 0
    if cost_accrual == 'beginning-of-year':
        discount_offset = 0
        annualized_offset = 1
    # elif cost_accrual == 'end-of-year':
    #     discount_offset = 1
    #     annualized_offset = 0

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

    # convert to pandas DataFrame for faster sum
    # calcs_df = pd.DataFrame(dict_of_values).transpose()
    calcs_df = pd.DataFrame.from_dict(dict_of_values, orient='index')

    calcs_df.reset_index(drop=True, inplace=True)
    annual_values_dict = calc_annual_values(calcs_df, all_costs)

    # omega_log.logwrite('\nDiscounting costs')
    annual_values_dict = discount_values(annual_values_dict)

    # first create a dictionary to house data
    calcs_dict = dict()

    # now do a cumulative sum year-over-year for each cost arg in calcs_dict - these will be present values (note removal of rate=0)
    # annual_values_df = pd.DataFrame(annual_values_dict).transpose()
    annual_values_df = pd.DataFrame.from_dict(annual_values_dict, orient='index')
    annual_values_df.reset_index(drop=True, inplace=True)
    present_values_dict = calc_present_values(annual_values_df, all_costs)

    calcs_dict.update(annual_values_dict)
    calcs_dict.update(present_values_dict)

    # first create an annualized_values_dict in which to store results
    series = 'AnnualizedValue'
    annualized_values_dict = dict()
    for social_discrate in social_discrates:
        for calendar_year in calendar_years:
            annualized_values_dict.update({
                (calendar_year, social_discrate, series): {'session_name': omega_globals.options.session_name,
                                                           'calendar_year': calendar_year,
                                                           'discount_rate': social_discrate,
                                                           'series': series,
                                                           'periods': 1,
                                                           }
            }
            )

    for social_discrate in social_discrates:
        for arg in non_emission_costs:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, social_discrate, periods, annualized_offset)

                annualized_values_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value
                annualized_values_dict[(calendar_year, social_discrate, series)]['periods'] = periods

        emission_discrate = 0.025
        for arg in emission_costs_dr25:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                annualized_values_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

        emission_discrate = 0.03
        for arg in emission_costs_dr3:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                annualized_values_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

        emission_discrate = 0.05
        for arg in emission_costs_dr5:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                annualized_values_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

        emission_discrate = 0.07
        for arg in emission_costs_dr7:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                annualized_values_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

    calcs_dict.update(annualized_values_dict)

    return calcs_dict
