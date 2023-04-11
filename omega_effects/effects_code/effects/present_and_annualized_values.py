"""

**OMEGA effects present and annualized values module.**

----

**CODE**

"""

import pandas as pd

from omega_effects.effects_code.effects.discounting import discount_values


class PVandEAV:
    """
    PV and EAV class definition.

    """
    def __init__(self):
        self.calendar_years = None
        self.discount_to_year = None
        self.cost_accrual = None

        self.session_names = list()
        self.reg_class_ids = list()
        self.in_use_fuel_ids = list()

        self.discount_offset = None
        self.annualized_offset = None

        self.social_discrates = [0.03, 0.07]
        self.emission_dr25 = '2.5'
        self.emission_dr3 = '3.'
        self.emission_dr5 = '5.0'
        self.emission_dr7 = '7.0'

        self.all_monetized_args = list()
        self.monetized_args_dr25 = list()
        self.monetized_args_dr3 = list()
        self.monetized_args_dr5 = list()
        self.monetized_args_dr7 = list()
        self.monetized_non_emission_args = list()
        self.id_args = list()

    @staticmethod
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

    @staticmethod
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

    def calc_present_values(self, batch_settings, df, args):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            df: A DataFrame containing annual discounted values to be summed for present values in each calendar year.
            args: A list of monetized attributes (strings) to be summed.

        Returns:
            A DataFrame of present values based on the discounted annual values in input_df.

        """
        present_values = pd.DataFrame()
        for session_name in self.session_names:
            session_policy = batch_settings.return_session_policy(session_name)

            for discount_rate in self.social_discrates:
                for calendar_year in self.calendar_years:
                    for rc_id in self.reg_class_ids:
                        for fuel_id in self.in_use_fuel_ids:
                            fueling_class = self.set_fueling_class(fuel_id)

                            periods = calendar_year - self.discount_to_year + self.discount_offset
                            if periods < 1:
                                present_value = pd.DataFrame(df.loc[(df['session_name'] == session_name)
                                                                    & (df['calendar_year'] == calendar_year)
                                                                    & (df['reg_class_id'] == rc_id)
                                                                    & (df['in_use_fuel_id'] == fuel_id)
                                                                    & (df['discount_rate'] == discount_rate)
                                                                    & (df['series'] == 'AnnualValue'), args]
                                                             )
                            else:
                                present_value = pd.DataFrame(df.loc[(df['session_name'] == session_name)
                                                                    & ((df['calendar_year'] >= self.discount_to_year)
                                                                    & (df['calendar_year'] <= calendar_year))
                                                                    & (df['reg_class_id'] == rc_id)
                                                                    & (df['in_use_fuel_id'] == fuel_id)
                                                                    & (df['discount_rate'] == discount_rate)
                                                                    & (df['series'] == 'AnnualValue'), args]
                                                             .sum()).transpose()
                            present_value.insert(0, 'discount_rate', discount_rate)
                            present_value.insert(0, 'periods', periods)
                            present_value.insert(0, 'series', 'PresentValue')
                            present_value.insert(0, 'fueling_class', fueling_class)
                            present_value.insert(0, 'in_use_fuel_id', fuel_id)
                            present_value.insert(0, 'reg_class_id', rc_id)
                            present_value.insert(0, 'calendar_year', calendar_year)
                            present_value.insert(0, 'session_name', session_name)
                            present_value.insert(0, 'session_policy', session_policy)
                            present_values = pd.concat([present_values, present_value], axis=0, ignore_index=True)

        present_values.set_index(pd.Series(zip(
            present_values['session_policy'],
            present_values['session_name'],
            present_values['calendar_year'],
            present_values['series'],
            present_values['discount_rate'],
            present_values['reg_class_id'],
            present_values['in_use_fuel_id'],
        )), inplace=True)

        return present_values.to_dict('index')

    def calc_present_and_annualized_values(self, batch_settings, df):
        """

        Parameters:
            batch_settings: an instance of the BatchSettings class.
            df (DataFrame): a DataFrame of monetized values needing PV and EAV calcs.

        Returns:
            A dictionary of annual, present and annualized values based on the df.

        Note:
            Values that occur prior to the "Discount Values to Year" input setting will not be discounted and their
            present and annualized values will equal the annual value.

        """
        self.calendar_years = batch_settings.calendar_years
        self.discount_to_year = batch_settings.discount_values_to_year
        self.cost_accrual = batch_settings.cost_accrual

        self.session_names = [name for name in df['session_name'].unique()]
        self.reg_class_ids = [rc_id for rc_id in df['reg_class_id'].unique()]
        self.in_use_fuel_ids = [fuel_id for fuel_id in df['in_use_fuel_id'].unique()]

        df.set_index(pd.Series(zip(
            df['session_policy'],
            df['session_name'],
            df['calendar_year'],
            df['series'],
            df['discount_rate'],
            df['reg_class_id'],
            df['in_use_fuel_id'],
        )), inplace=True)

        dict_of_values = df.to_dict('index')

        self.discount_offset = 1
        self.annualized_offset = 0
        if self.cost_accrual == 'beginning-of-year':
            self.discount_offset = 0
            self.annualized_offset = 1

        # establish and distinguish attributes
        nested_dict = [n_dict for key, n_dict in dict_of_values.items()][0]
        self.all_monetized_args = tuple([k for k, v in nested_dict.items() if '_dollars' in k and 'avg' not in k])
        self.monetized_args_dr25 = [arg for arg in self.all_monetized_args if f'_{self.emission_dr25}' in arg]
        self.monetized_args_dr3 = [arg for arg in self.all_monetized_args if f'_{self.emission_dr3}' in arg]
        self.monetized_args_dr5 = [arg for arg in self.all_monetized_args if f'_{self.emission_dr5}' in arg]
        self.monetized_args_dr7 = [arg for arg in self.all_monetized_args if f'_{self.emission_dr7}' in arg]
        self.monetized_non_emission_args = [arg for arg in self.all_monetized_args
                                       if arg not in self.monetized_args_dr25
                                       and arg not in self.monetized_args_dr3
                                       and arg not in self.monetized_args_dr5
                                       and arg not in self.monetized_args_dr7]
        self.id_args = [k for k, v in nested_dict.items() if '_dollars' not in k]

        annual_values_dict = discount_values(batch_settings, dict_of_values)

        # calc present values, which are cumulative sums of the discounted annual values
        annual_values_df = pd.DataFrame.from_dict(annual_values_dict, orient='index')
        annual_values_df.reset_index(drop=True, inplace=True)
        present_values_dict = self.calc_present_values(batch_settings, annual_values_df, self.all_monetized_args)

        # create a dictionary to house data
        calcs_dict = dict()
        calcs_dict.update(annual_values_dict)
        calcs_dict.update(present_values_dict)

        series = 'AnnualizedValue'
        annualized_values_dict = dict()
        for session_name in self.session_names:
            session_policy = batch_settings.return_session_policy(session_name)

            # create an annualized_values_dict with the following keys in which to store results
            for social_discrate in self.social_discrates:
                for calendar_year in self.calendar_years:
                    for rc_id in self.reg_class_ids:
                        for fuel_id in self.in_use_fuel_ids:
                            annualized_values_dict.update({
                                (session_policy, session_name, calendar_year, series, social_discrate, rc_id, fuel_id):
                                    {
                                    'session_policy': session_policy,
                                    'session_name': session_name,
                                    'calendar_year': calendar_year,
                                    'series': series,
                                    'discount_rate': social_discrate,
                                    'reg_class_id': rc_id,
                                    'in_use_fuel_id': fuel_id,
                                    }
                            }
                            )

            # populate keys with values
            for social_discrate in self.social_discrates:

                for arg in self.monetized_non_emission_args:
                    for calendar_year in self.calendar_years:
                        for rc_id in self.reg_class_ids:
                            for fuel_id in self.in_use_fuel_ids:
                                fueling_class = self.set_fueling_class(fuel_id)

                                periods = calendar_year - self.discount_to_year + self.discount_offset
                                if periods < 1:
                                    key = \
                                        (session_policy, session_name, calendar_year, 'AnnualValue',
                                         social_discrate, rc_id, fuel_id)
                                    arg_annualized_value = calcs_dict[key][arg]
                                else:
                                    key = (session_policy, session_name, calendar_year, 'PresentValue',
                                           social_discrate, rc_id, fuel_id)
                                    arg_present_value = calcs_dict[key][arg]
                                    arg_annualized_value = \
                                        self.calc_annualized_value(arg_present_value,
                                                                   social_discrate, periods, self.annualized_offset)

                                key = (session_policy, session_name, calendar_year, series,
                                       social_discrate, rc_id, fuel_id)
                                annualized_values_dict[key][arg] = arg_annualized_value
                                annualized_values_dict[key]['periods'] = periods
                                annualized_values_dict[key]['fueling_class'] = fueling_class

                emission_discrate = 0.025
                for arg in self.monetized_args_dr25:
                    for calendar_year in self.calendar_years:
                        for rc_id in self.reg_class_ids:
                            for fuel_id in self.in_use_fuel_ids:
                                periods = calendar_year - self.discount_to_year + self.discount_offset
                                if periods < 1:
                                    key = \
                                        (session_policy, session_name, calendar_year, 'AnnualValue', social_discrate,
                                         rc_id, fuel_id)
                                    arg_annualized_value = calcs_dict[key][arg]
                                else:
                                    key = (
                                        session_policy, session_name, calendar_year, 'PresentValue',
                                        social_discrate, rc_id,
                                        fuel_id)
                                    arg_present_value = calcs_dict[key][arg]
                                    arg_annualized_value = \
                                        self.calc_annualized_value(arg_present_value, emission_discrate, periods,
                                                                   self.annualized_offset)

                                key = (
                                    session_policy, session_name, calendar_year, series,
                                    social_discrate, rc_id, fuel_id)
                                annualized_values_dict[key][arg] = arg_annualized_value

                emission_discrate = 0.03
                for arg in self.monetized_args_dr3:
                    for calendar_year in self.calendar_years:
                        for rc_id in self.reg_class_ids:
                            for fuel_id in self.in_use_fuel_ids:
                                periods = calendar_year - self.discount_to_year + self.discount_offset
                                if periods < 1:
                                    key = \
                                        (session_policy, session_name, calendar_year, 'AnnualValue', social_discrate,
                                         rc_id, fuel_id)
                                    arg_annualized_value = calcs_dict[key][arg]
                                else:
                                    key = (
                                        session_policy, session_name, calendar_year, 'PresentValue', social_discrate,
                                        rc_id,
                                        fuel_id)
                                    arg_present_value = calcs_dict[key][arg]
                                    arg_annualized_value = \
                                        self.calc_annualized_value(arg_present_value, emission_discrate, periods,
                                                                   self.annualized_offset)

                                key = (
                                    session_policy, session_name, calendar_year, series, social_discrate, rc_id,
                                    fuel_id)
                                annualized_values_dict[key][arg] = arg_annualized_value

                emission_discrate = 0.05
                for arg in self.monetized_args_dr5:
                    for calendar_year in self.calendar_years:
                        for rc_id in self.reg_class_ids:
                            for fuel_id in self.in_use_fuel_ids:
                                periods = calendar_year - self.discount_to_year + self.discount_offset
                                if periods < 1:
                                    key = \
                                        (session_policy, session_name, calendar_year, 'AnnualValue', social_discrate,
                                         rc_id, fuel_id)
                                    arg_annualized_value = calcs_dict[key][arg]
                                else:
                                    key = (
                                        session_policy, session_name, calendar_year, 'PresentValue', social_discrate,
                                        rc_id,
                                        fuel_id)
                                    arg_present_value = calcs_dict[key][arg]
                                    arg_annualized_value = \
                                        self.calc_annualized_value(arg_present_value, emission_discrate, periods,
                                                                   self.annualized_offset)

                                key = (
                                    session_policy, session_name, calendar_year, series, social_discrate, rc_id,
                                    fuel_id)
                                annualized_values_dict[key][arg] = arg_annualized_value

                emission_discrate = 0.07
                for arg in self.monetized_args_dr7:
                    for calendar_year in self.calendar_years:
                        for rc_id in self.reg_class_ids:
                            for fuel_id in self.in_use_fuel_ids:
                                periods = calendar_year - self.discount_to_year + self.discount_offset
                                if periods < 1:
                                    key = \
                                        (session_policy, session_name, calendar_year, 'AnnualValue', social_discrate,
                                         rc_id, fuel_id)
                                    arg_annualized_value = calcs_dict[key][arg]
                                else:
                                    key = (
                                        session_policy, session_name, calendar_year, 'PresentValue', social_discrate,
                                        rc_id,
                                        fuel_id)
                                    arg_present_value = calcs_dict[key][arg]
                                    arg_annualized_value = \
                                        self.calc_annualized_value(arg_present_value, emission_discrate, periods,
                                                                   self.annualized_offset)

                                key = (
                                    session_policy, session_name, calendar_year, series, social_discrate, rc_id,
                                    fuel_id)
                                annualized_values_dict[key][arg] = arg_annualized_value

        calcs_dict.update(annualized_values_dict)

        return calcs_dict
