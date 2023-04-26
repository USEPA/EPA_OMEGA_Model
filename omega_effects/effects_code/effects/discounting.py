"""

**OMEGA effects discounting module.**

----

**CODE**

"""
import pandas as pd


class Discounting:

    def __init__(self):

        self.social_discrates = [0.03, 0.07]

        self.annual_values_dict = {}
        self.pv_dict = {}
        self.eav_dict = {}

        self.all_monetized_args = []
        self.monetized_non_emission_args = []
        self.rate_list_dict = {}

    def discount_annual_values(self, batch_settings, annual_values_df):
        """
        The discount function determines attributes appropriate for discounting and does the discounting calculation to
        a given year and point within that year.

        Parameters:
            batch_settings: an instance of the omega effects batch settings class.
            annual_values_df: A DataFrame of values to be discounted.

        Returns:
            A dictionary providing discounted annual values where monetized values are discounted at their internally
            consistent discount rate.

        Note:
            Important input settings for discounting of monetized values are the "Discount Values to Year" and
            "Cost Accrual" settings. The year to which to discount monetized values is set by the "Discount Values to
            Year" entry of the omega effects batch input file. The "Cost Accrual" input setting should be set to
            'start-of-year' or 'end-of-year', where start-of-year represents costs accruing at time t=0 within the
            year, and end-of-year represents costs accruing at the end of the year.

            Values that occur prior to the "Discount Values to Year" input setting will not be discounted.

        """
        dict_of_values = annual_values_df.to_dict(orient='index')
        discount_to_year = batch_settings.discount_values_to_year
        cost_accrual = batch_settings.cost_accrual

        emission_dr25 = '2.5'
        emission_dr3 = '3.'
        emission_dr5 = '5.0'
        emission_dr7 = '7.0'

        # establish and distinguish attributes
        nested_dict = [n_dict for n_dict in dict_of_values.values()][0]
        self.all_monetized_args = [k for k, v in nested_dict.items() if '_dollars' in k and 'avg' not in k]
        monetized_args_dr25 = [arg for arg in self.all_monetized_args if f'_{emission_dr25}' in arg]
        monetized_args_dr3 = [arg for arg in self.all_monetized_args if f'_{emission_dr3}' in arg]
        monetized_args_dr5 = [arg for arg in self.all_monetized_args if f'_{emission_dr5}' in arg]
        monetized_args_dr7 = [arg for arg in self.all_monetized_args if f'_{emission_dr7}' in arg]
        self.monetized_non_emission_args = [arg for arg in self.all_monetized_args
                                       if arg not in monetized_args_dr25
                                       and arg not in monetized_args_dr3
                                       and arg not in monetized_args_dr5
                                       and arg not in monetized_args_dr7]
        id_args = [k for k, v in nested_dict.items() if '_dollars' not in k]

        self.rate_list_dict = {
            0.025: monetized_args_dr25,
            0.03: monetized_args_dr3,
            0.05: monetized_args_dr5,
            0.07: monetized_args_dr7,
        }

        update_dict = {}
        for v in dict_of_values.values():

            session_policy, calendar_year, reg_class_id, fuel_id = \
                v['session_policy'], v['calendar_year'], v['reg_class_id'], v['in_use_fuel_id']
            series = 'AnnualValue'

            for social_discrate in self.social_discrates:
                rate_dict = {}
                for arg in id_args:
                    if arg == 'discount_rate':
                        arg_value = social_discrate
                    else:
                        arg_value = v[arg]
                    rate_dict.update({arg: arg_value})

                for arg in self.monetized_non_emission_args:
                    arg_value = v[arg]
                    discounted_value = \
                        discount_value(arg_value, social_discrate, calendar_year, discount_to_year, cost_accrual)
                    rate_dict.update({arg: discounted_value})

                for emission_discrate, arg_list in self.rate_list_dict.items():
                    for arg in arg_list:
                        arg_value = v[arg]
                        discounted_value = \
                            discount_value(arg_value, emission_discrate, calendar_year, discount_to_year, cost_accrual)
                        rate_dict.update({arg: discounted_value})

                update_dict[(session_policy, calendar_year, reg_class_id, fuel_id, social_discrate, series)] = rate_dict

        dict_of_values.update(update_dict)

        self.annual_values_dict = dict_of_values.copy()

    def calc_present_values(self, batch_settings):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.

        Returns:
            A dictionary of present values based on the discounted annual values in dict_of_values.

        """
        discount_to_year = batch_settings.discount_values_to_year

        for v in self.annual_values_dict.values():

            session_policy, calendar_year, reg_class_id, fuel_id, discount_rate = \
                v['session_policy'], v['calendar_year'], v['reg_class_id'], v['in_use_fuel_id'], v['discount_rate']

            if discount_rate != 0:

                if calendar_year <= discount_to_year:
                    pv_dict_key = (session_policy, calendar_year, reg_class_id, fuel_id, discount_rate, 'PresentValue')
                    self.pv_dict.update({pv_dict_key: v.copy()})

                else:
                    pv_dict_key = (session_policy, calendar_year, reg_class_id, fuel_id, discount_rate, 'PresentValue')
                    self.pv_dict.update({pv_dict_key: v.copy()})
                    for arg in self.all_monetized_args:
                        arg_value = self.pv_dict[
                            (session_policy, calendar_year - 1, reg_class_id, fuel_id, discount_rate, 'PresentValue')
                        ][arg]
                        arg_value += v[arg]
                        self.pv_dict[pv_dict_key].update({arg: arg_value})

                self.pv_dict[pv_dict_key]['series'] = 'PresentValue'

    def calc_annualized_values(self, batch_settings):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.

        Returns:
            A dictionary of equivalent annualized values based on the present values in dict_of_values.

        """
        discount_to_year = batch_settings.discount_values_to_year
        cost_accrual = batch_settings.cost_accrual
        offset_list = ['start-of-year', 'end-of-year']
        offset = offset_list.index(cost_accrual)

        for v in self.pv_dict.values():

            session_policy, calendar_year, reg_class_id, fuel_id, discount_rate = \
                v['session_policy'], v['calendar_year'], v['reg_class_id'], v['in_use_fuel_id'], v['discount_rate']

            eav_dict_key = (session_policy, calendar_year, reg_class_id, fuel_id, discount_rate, 'AnnualizedValue')
            self.eav_dict[eav_dict_key] = v.copy()
            self.eav_dict[eav_dict_key]['series'] = 'AnnualizedValue'

            periods = calendar_year - discount_to_year + offset

            if periods >= 1:

                for arg in self.monetized_non_emission_args:
                    present_value = v[arg]
                    annualized_value = annualize_value(present_value, discount_rate, periods, cost_accrual)
                    self.eav_dict[eav_dict_key][arg] = annualized_value

                for emission_discrate, arg_list in self.rate_list_dict.items():
                    for arg in arg_list:
                        present_value = v[arg]
                        annualized_value = annualize_value(present_value, emission_discrate, periods, cost_accrual)
                        self.eav_dict[eav_dict_key][arg] = annualized_value


def discount_model_year_values(model_year_df):
    """
    The discount function determines attributes appropriate for discounting and does the discounting calculation to
    the first year of any given model year.

    Parameters:
        model_year_df: A DataFrame of values to be discounted.

    Returns:
        A DataFrame providing discounted model year values where monetized values are discounted to the first year
        of the model year.

    """
    dict_of_values = model_year_df.to_dict(orient='index')
    cost_accrual = 'end-of-year'  # hard coded here for model year discounting

    # establish and distinguish attributes
    nested_dict = [v for v in dict_of_values.values()][0]
    my_monetized_args = [k for k, v in nested_dict.items() if '_dollars' in k and 'avg' not in k]
    non_discounted_args = [arg for arg in my_monetized_args
                           if 'vehicle' in arg
                           or 'purchase' in arg
                           or 'battery' in arg]
    discounted_args = [arg for arg in my_monetized_args if arg not in non_discounted_args]
    id_args = [k for k, v in nested_dict.items() if '_dollars' not in k]

    discounted_my_dict = {}
    for v in dict_of_values.values():

        vehicle_id, calendar_year, model_year = v['vehicle_id'], v['calendar_year'], v['model_year']

        for social_discrate in Discounting().social_discrates:
            rate_dict = {}
            for arg in id_args:
                if arg == 'discount_rate':
                    arg_value = social_discrate
                else:
                    arg_value = v[arg]
                rate_dict.update({arg: arg_value})

            for arg in non_discounted_args:
                arg_value = v[arg]
                rate_dict.update({arg: arg_value})

            for arg in discounted_args:
                arg_value = v[arg]
                discounted_value = \
                    discount_value(arg_value, social_discrate, calendar_year, model_year, cost_accrual)
                rate_dict.update({arg: discounted_value})

            discounted_my_dict[(vehicle_id, calendar_year, social_discrate)] = rate_dict

    return pd.DataFrame.from_dict(discounted_my_dict, orient='index')


def discount_value(arg_value, rate, year, discount_to, cost_accrual):
    """

    Parameters:
        arg_value (float): the value to be discounted.
        rate (float): the discount rate to use.
        year (int): the calendar year associated with arg_value.
        discount_to (int): the calendar year to which to discount the value.
        cost_accrual (str): set via the general_inputs file to indicate whether costs occur at the start or end of
        the year.

    Returns:
        A single value representing arg_value discounted to year discount_to at rate.

    """
    # no discounting of values that occur prior to "discount_to_year"; exponent controls for that
    if 'start' in cost_accrual:
        exponent = max(0, year - discount_to)
    else:
        exponent = max(0, year - discount_to + 1)

    return arg_value / (1 + rate) ** exponent


def annualize_value(present_value, rate, periods, cost_accrual):
    """

    Parameters:
        present_value (float): the present value to be annualized.
        rate (float): the discount rate to use.
        periods (int): the number of periods over which to annualize present_value.
        cost_accrual (str): set via the general_inputs file to indicate whether costs occur at the start or end of
        the year.

    Returns:
        A single annualized value of present_value discounted at rate over periods number of year_ids.

    """
    if 'start' in cost_accrual:
        return present_value * rate * (1 + rate) ** periods \
               / ((1 + rate) ** (periods + 1) - 1)
    else:
        return present_value * rate * (1 + rate) ** periods \
               / ((1 + rate) ** periods - 1)


def set_fueling_class(fuel_id):
    """
    Set fueling class based on the provided fuel id.

    Args:
        fuel_id (str): e.g. 'electricity'

    Returns:
        ``'BEV'`` or ``'ICE'`` depending on the fuel id.

    """
    if 'electricity' in fuel_id:
        return 'BEV'
    else:
        return 'ICE'
