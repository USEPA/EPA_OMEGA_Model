from omega_model import *


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


def calc_present_values(input_df, args):

    groupby_cols = [col for col in input_df.columns if col not in args and 'periods' not in col and 'calendar_year' not in col]
    temp_df = input_df.loc[input_df['discount_rate'] != 0, :]
    present_values_df = temp_df.groupby(by=groupby_cols).cumsum()
    present_values_df['series'] = 'PresentValue'
    return_df = pd.concat([input_df, present_values_df], ignore_index=True)
    return return_df


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
    if cost_accrual == 'beginning-of-year':
        discount_offset = 0
        annualized_offset = 1
    elif cost_accrual == 'end-of-year':
        discount_offset = 1
        annualized_offset = 0

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

    # first create a dictionary to house data
    calcs_dict = dict()

    # first undiscounted annual values
    social_discrate = 0
    series = 'AnnualValue'
    for calendar_year in calendar_years:
        calcs_dict.update({(calendar_year, social_discrate, series): {'session_name': omega_globals.options.session_name,
                                                                      'calendar_year': calendar_year,
                                                                      'discount_rate': social_discrate,
                                                                      'series': series,
                                                                      'periods': 1,
                                                                      }
                           }
                          )

    # then for discounted values
    for series in ['AnnualValue']: #, 'PresentValue', 'AnnualizedValue']:
        for social_discrate in social_discrates:
            for calendar_year in calendar_years:
                calcs_dict.update({(calendar_year, social_discrate, series): {'session_name': omega_globals.options.session_name,
                                                                              'calendar_year': calendar_year,
                                                                              'discount_rate': social_discrate,
                                                                              'series': series,
                                                                              'periods': 1,
                                                                              }
                                   }
                                  )

    # now fill in calcs_dict; first sum by year for each cost arg in dict_of_values
    series = 'AnnualValue'
    for social_discrate in [0, *social_discrates]:
        for calendar_year in calendar_years:
            for arg in all_costs:
                arg_annual_value = sum(v[arg] for k, v in dict_of_values.items()
                                       if v['calendar_year'] == calendar_year
                                       and v['discount_rate'] == social_discrate)
                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_annual_value

    calcs_df = pd.DataFrame(calcs_dict).transpose()
    new_df = calc_present_values(calcs_df, all_costs)

    # now do a cumulative sum year-over-year for each cost arg in calcs_dict - these will be present values (note removal of rate=0)
    series = 'PresentValue'
    for social_discrate in social_discrates:
        for arg in all_costs:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = sum(v[arg] for k, v in calcs_dict.items()
                                            if discount_to_year <= v['calendar_year'] <= calendar_year
                                            and v['discount_rate'] == social_discrate
                                            and v['series'] == 'AnnualValue')
                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_present_value
                calcs_dict[(calendar_year, social_discrate, series)]['periods'] = periods

    # now annualize those present values
    series = 'AnnualizedValue'
    for social_discrate in social_discrates:
        for arg in non_emission_costs:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, social_discrate, periods, annualized_offset)

                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value
                calcs_dict[(calendar_year, social_discrate, series)]['periods'] = periods

        emission_discrate = 0.025
        for arg in emission_costs_dr25:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

        emission_discrate = 0.03
        for arg in emission_costs_dr3:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

        emission_discrate = 0.05
        for arg in emission_costs_dr5:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

        emission_discrate = 0.07
        for arg in emission_costs_dr7:
            for calendar_year in calendar_years:
                periods = calendar_year - discount_to_year + discount_offset
                if periods < 1:
                    arg_annualized_value = calcs_dict[(calendar_year, social_discrate, 'AnnualValue')][arg]
                else:
                    arg_present_value = calcs_dict[(calendar_year, social_discrate, 'PresentValue')][arg]
                    arg_annualized_value = calc_annualized_value(arg_present_value, emission_discrate, periods, annualized_offset)

                calcs_dict[(calendar_year, social_discrate, series)][arg] = arg_annualized_value

    return calcs_dict
