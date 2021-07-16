import pandas as pd


def discount_values(dict_of_values):
    """The discount function determines metrics appropriate for discounting (those contained in dict_of_values) and does the discounting
    calculation to a given year and point within that year.

    Parameters:
        dict_of_values: A dictionary of values to be discounted with keys consisting of vehicle_id, calendar_year, age and discount rate.\n

    Returns:
        The passed dictionary with new key, value pairs where keys stipulate the discount rate and monetized values are discounted at that rate.

    Note:
        The costs_start entry of the BCA_General_Inputs file should be set to 'start-year' or 'end-year', where start-year represents costs
        starting at time t=0 (i.e., first year costs are undiscounted), and end-year represents costs starting at time t=1 (i.e., first year
        costs are discounted).

    """
    discount_to_year = 2021
    costs_start = 'end-year'
    social_discrates = [0.03, 0.07]
    emission_dr25 = 25
    emission_dr3 = 3
    emission_dr5 = 5
    emission_dr7 = 7

    update_dict = dict()
    for key in dict_of_values.keys():

        vehicle_id, calendar_year, age, discount_rate = key

        args = [k for k, v in dict_of_values[key].items()]
        emission_costs_dr25 = [arg for arg in args if 'cost' in arg and f'{str(emission_dr25)}' in arg]
        emission_costs_dr3 = [arg for arg in args if 'cost' in arg and f'{str(emission_dr3)}' in arg]
        emission_costs_dr5 = [arg for arg in args if 'cost' in arg and f'{str(emission_dr5)}' in arg]
        emission_costs_dr7 = [arg for arg in args if 'cost' in arg and f'{str(emission_dr7)}' in arg]
        non_emission_costs = [arg for arg in args if 'cost' in arg
                              and f'{str(emission_dr25)}' not in arg
                              and f'{str(emission_dr3)}' not in arg
                              and f'{str(emission_dr5)}' not in arg
                              and f'{str(emission_dr7)}' not in arg]
        id_args = [arg for arg in args if 'ID' in arg or 'model_year' in arg]

        if costs_start == 'start-year': discount_offset = 0
        elif costs_start == 'end-year': discount_offset = 1

        for social_discrate in social_discrates:
            rate_dict = dict()
            for arg in non_emission_costs:
                arg_value = dict_of_values[key][arg] / ((1 + social_discrate) ** (calendar_year - discount_to_year + discount_offset))
                rate_dict.update({arg: arg_value})

            emission_discrate = 0.05
            for arg in emission_costs_dr5:
                arg_value = dict_of_values[key][arg] / ((1 + emission_discrate) ** (calendar_year - discount_to_year + discount_offset))
                rate_dict.update({arg: arg_value})

            emission_discrate = 0.03
            for arg in emission_costs_dr3:
                arg_value = dict_of_values[key][arg] / ((1 + emission_discrate) ** (calendar_year - discount_to_year + discount_offset))
                rate_dict.update({arg: arg_value})

            emission_discrate = 0.025
            for arg in emission_costs_dr25:
                arg_value = dict_of_values[key][arg] / ((1 + emission_discrate) ** (calendar_year - discount_to_year + discount_offset))
                rate_dict.update({arg: arg_value})

            emission_discrate = 0.07
            for arg in emission_costs_dr7:
                arg_value = dict_of_values[key][arg] / ((1 + emission_discrate) ** (calendar_year - discount_to_year + discount_offset))
                rate_dict.update({arg: arg_value})

            for arg in id_args:
                arg_value = dict_of_values[key][arg]
                rate_dict.update({arg: arg_value})

            update_dict[(vehicle_id, calendar_year, age, social_discrate)] = rate_dict

    dict_of_values.update(update_dict)
    return dict_of_values


def annualize_values(settings, input_df):
    """This function determines the annual value that equates to a present value if that annual value were discounted at a given discount rate.
    See EPA Economic Guidelines (updated May 2014), Section 6.1.2, Equations 3 & 4.

    Parameters:
        settings: The SetInputs class.\n
        input_df: A DataFrame of annual values containing optionID, yearID, DiscountRate and Cost arguments.

    Returns:
        A DataFrame of the passed Cost arguments annualized by optionID in each of the passed yearIDs and at each discount rate.

    Note:
        This function makes use of a cumulative sum of annual discounted values. As such, the cumulative sums represent a present value
        through the given calendar year. The Offset is included to reflect costs beginning at the start of the year (Offset=1)
        or the end of the year (Offset=0).\n
        The equation used here is shown below.

        AC = PV * DR * (1+DR)^(period) / [(1+DR)^(period+Offset) - 1]

        where,\n
        AC = Annualized Cost\n
        PV = Present Value (here, the cumulative summary of discounted annual values)\n
        DR = Discount Rate\n
        CY = Calendar Year (yearID)\n
        period = the current CY minus the year to which to discount values + a discount_offset value where discount_offset equals the costs_start input value\n
        Offset = 1 for costs at the start of the year, 0 for cost at the end of the year

    """
    cap_dr1 = settings.criteria_discount_rate_1
    cap_dr2 = settings.criteria_discount_rate_2

    if settings.costs_start == 'start-year':
        discount_offset = 0
        annualized_offset = 1
    elif settings.costs_start == 'end-year': 
        discount_offset = 1
        annualized_offset = 0
    discount_to_year = settings.discount_to_yearID
    cost_args = [arg for arg in input_df.columns if 'Cost' in arg and 'PresentValue' not in arg]
    non_emission_cost_args = [arg for arg in input_df.columns if 'Cost' in arg and '_0.0' not in arg and 'PresentValue' not in arg]
    emission_costs_cap_dr1 = [arg for arg in input_df.columns if 'Cost' in arg and f'{str(cap_dr1)}' in arg and 'PresentValue' not in arg]
    emission_costs_cap_dr2 = [arg for arg in input_df.columns if 'Cost' in arg and f'{str(cap_dr2)}' in arg and 'PresentValue' not in arg]
    input_df.insert(input_df.columns.get_loc('DiscountRate') + 1, 'periods', input_df['yearID'] - discount_to_year + discount_offset)
    for cost_arg in non_emission_cost_args:
        input_df.insert(len(input_df.columns),
                        f'{cost_arg}_Annualized',
                        input_df[f'{cost_arg}_PresentValue']
                        * input_df['DiscountRate']
                        * (1 + input_df['DiscountRate']) ** (input_df['yearID'] - discount_to_year + discount_offset)
                        / ((1 + input_df['DiscountRate']) ** (input_df['periods'] + annualized_offset) - 1))
    for cost_arg in emission_costs_cap_dr1:
        input_df.insert(len(input_df.columns),
                        f'{cost_arg}_Annualized',
                        input_df[f'{cost_arg}_PresentValue']
                        * cap_dr1
                        * (1 + cap_dr1) ** (input_df['yearID'] - discount_to_year + discount_offset)
                        / ((1 + cap_dr1) ** (input_df['periods'] + annualized_offset) - 1))
    for cost_arg in emission_costs_cap_dr2:
        input_df.insert(len(input_df.columns),
                        f'{cost_arg}_Annualized',
                        input_df[f'{cost_arg}_PresentValue']
                        * cap_dr2
                        * (1 + cap_dr2) ** (input_df['yearID'] - discount_to_year + discount_offset)
                        / ((1 + cap_dr2) ** (input_df['periods'] + annualized_offset) - 1))

    return input_df


# if __name__ == '__main__':
#     import pandas as pd
#     from bca_tool_code.tool_setup import SetInputs as settings
#     from bca_tool_code.tool_postproc import create_annual_summary_df
#
#     # test discount_values and annualize_values functions
#     vehicle = (0)
#     alt = 0
#     dr = 0.03
#     my = 2027
#     cost = 100
#     growth = 0.5
#     settings.social_discount_rate_1, settings.social_discount_rate_2 = dr, dr
#
#     data_df = pd.DataFrame({'vehicle': [(vehicle, alt, my, 0, dr), (vehicle, alt, my, 1, dr), (vehicle, alt, my, 2, dr),
#                                         (vehicle, alt, my, 3, dr), (vehicle, alt, my, 4, dr), (vehicle, alt, my, 5, dr),
#                                         (vehicle, alt, my, 6, dr), (vehicle, alt, my, 7, dr), (vehicle, alt, my, 8, dr),
#                                         (vehicle, alt, my, 9, dr), (vehicle, alt, my, 10, dr)],
#                             'Cost': [cost*(1+growth)**0, cost*(1+growth)**1, cost*(1+growth)**2, cost*(1+growth)**3,
#                                      cost*(1+growth)**4, cost*(1+growth)**5, cost*(1+growth)**6, cost*(1+growth)**7,
#                                      cost*(1+growth)**8, cost*(1+growth)**9, cost*(1+growth)**10]})
#
#     data_df.set_index('vehicle', inplace=True)
#
#     settings.costs_start = 'start-year'
#     print('\n\nData\n', data_df)
#     data_dict = data_df.to_dict('index')
#     discounted_dict = discount_values(settings, data_dict)
#     discounted_df = pd.DataFrame(discounted_dict).transpose()
#     discounted_df.reset_index(drop=False, inplace=True)
#     discounted_df.rename(columns={'level_0': 'vehicle',
#                                   'level_1': 'optionID',
#                                   'level_2': 'modelYearID',
#                                   'level_3': 'ageID',
#                                   'level_4': 'DiscountRate'}, inplace=True)
#     discounted_df.insert(0, 'OptionName', 'TestOption')
#     discounted_df.insert(0, 'yearID', discounted_df[['modelYearID', 'ageID']].sum(axis=1))
#     discounted_df = create_annual_summary_df(discounted_df)
#     discounted_df = annualize_values(settings, discounted_df)
#     print(f'\n\n\nCosts start = {settings.costs_start}\n',
#           discounted_df[['yearID', 'periods', 'Cost', 'Cost_PresentValue', 'Cost_Annualized']])
#
#     settings.costs_start = 'end-year'
#     print('\n\nData\n', data_df)
#     data_dict = data_df.to_dict('index')
#     discounted_dict = discount_values(settings, data_dict)
#     discounted_df = pd.DataFrame(discounted_dict).transpose()
#     discounted_df.reset_index(drop=False, inplace=True)
#     discounted_df.rename(columns={'level_0': 'vehicle',
#                                   'level_1': 'optionID',
#                                   'level_2': 'modelYearID',
#                                   'level_3': 'ageID',
#                                   'level_4': 'DiscountRate'}, inplace=True)
#     discounted_df.insert(0, 'OptionName', 'TestOption')
#     discounted_df.insert(0, 'yearID', discounted_df[['modelYearID', 'ageID']].sum(axis=1))
#     discounted_df = create_annual_summary_df(discounted_df)
#     discounted_df = annualize_values(settings, discounted_df)
#     print(f'\n\n\nCosts start = {settings.costs_start}\n',
#           discounted_df[['yearID', 'periods', 'Cost', 'Cost_PresentValue', 'Cost_Annualized']])
