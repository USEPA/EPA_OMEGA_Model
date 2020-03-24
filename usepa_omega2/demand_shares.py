import pandas as pd
import numpy as np
from pathlib import Path


PATH_PROJECT = Path.cwd()
PATH_INPUTS = PATH_PROJECT.joinpath('inputs')

# this dict would be an input rather than hardcoded here but the point is to show that these coefficients_pmt could change year-over-year, if desired
coefficients_pmt = {'a': .1, 'b1': 1, 'b2': .8, 'b3': 1, 'b4': 1.1, 'b5': .5}
coefficients_shared_private = {'a': .1, 'b1': .8, 'b2': 1, 'b3': 1.1, 'b4': 1, 'b5': 1}


class DemandShares:
    """
    Calculate the light-duty PMT demand; the share of hauling vs non-hauling; the share of private vs shared; the share of ICE vs BEV

    :param: coefficients_pmt: a dictionary of constants and beta coefficients_pmt by calendar year
    :param pmt_metrics_dict:  a dictionary of input parameters providing calendar year-by-calendar year cost/mile for non-light-duty forms of mobility,
    average income, population, the value of individual's time
    :param: calendar_year: the calendar year for which demand is requested
    """

    def __init__(self, coefficients, pmt_metrics_dict, calendar_year):
        self.coefficients = coefficients
        self.calendar_year = calendar_year
        self.pmt_metrics_dict = pmt_metrics_dict

    def pmt_lightduty(self, cost_per_mile_lightduty):
        """

        :param cost_per_mile_lightduty: a single value of fleetwide light-duty cost/mile for the prior year
        :return: a dictionary having a key=calendar_year and a value=demanded mile of travel for the given year
        """
        pmt = dict()
        pmt[self.calendar_year] = np.exp(self.coefficients['a']
                                         + self.coefficients['b1'] * np.log(cost_per_mile_lightduty)
                                         + self.coefficients['b2'] * np.log(self.pmt_metrics_dict[self.calendar_year]['cost_per_mile_other'])
                                         + self.coefficients['b3'] * np.log(self.pmt_metrics_dict[self.calendar_year]['avg_income'])
                                         + self.coefficients['b4'] * np.log(self.pmt_metrics_dict[self.calendar_year]['population'])
                                         + self.coefficients['b5'] * np.log(self.pmt_metrics_dict[self.calendar_year]['cost_of_time']))
        return pmt

    def shared_vs_private(self, cost_per_mile_shared, cost_per_mile_private):
        """

        :param cost_per_mile_shared:
        :param cost_per_mile_private:
        :return:
        """
        proportion_shared = dict()
        exponent = self.coefficients['a'] \
                   + self.coefficients['b1'] * np.log(cost_per_mile_shared) \
                   + self.coefficients['b2'] * np.log(cost_per_mile_private) \
                   + self.coefficients['b3'] * np.log(self.pmt_metrics_dict[self.calendar_year]['cost_of_time_shared']) \
                   + self.coefficients['b4'] * np.log(self.pmt_metrics_dict[self.calendar_year]['cost_of_time_private']) \
                   + self.coefficients['b5'] * np.log(self.pmt_metrics_dict[self.calendar_year]['avg_income'])
        proportion_shared[self.calendar_year] = np.exp(exponent) / (1 + np.exp(exponent))
        return proportion_shared


if __name__ == '__main__':
    data = pd.read_excel(PATH_INPUTS.joinpath('PMT_Parameters.xlsx'), index_col=0)
    pmt_parameters_dict = data.to_dict('index')

    # calculate demand for personal miles traveled
    pmt_dict = dict()
    for calendar_year in pmt_parameters_dict.keys():
        pmt_dict.update(DemandShares(coefficients_pmt, pmt_parameters_dict, calendar_year).pmt_lightduty(.12))
    pmt_df = pd.DataFrame([item for item in pmt_dict.values()], [item for item in pmt_dict.keys()])
    pmt_df.rename(columns={0: 'PMT_Demand'}, inplace=True)
    pmt_df.insert(0, 'Calendar_Year', pmt_df.index)
    pmt_df.reset_index(drop=True, inplace=True)
    pmt_df.to_csv(PATH_PROJECT.joinpath('outputs/pmt_demand.csv'), index=False)

    # calculate proportion of shared vs private miles traveled
    shared_vs_private_dict = dict()
    for calendar_year in pmt_parameters_dict.keys():
        shared_vs_private_dict.update(DemandShares(coefficients_shared_private, pmt_parameters_dict, calendar_year).shared_vs_private(.5, .12))
    shared_vs_private_df = pd.DataFrame([item for item in shared_vs_private_dict.values()], [item for item in shared_vs_private_dict.keys()])
    shared_vs_private_df.rename(columns={0: 'Proportion_Shared'}, inplace=True)
    shared_vs_private_df.insert(0, 'Calendar_Year', shared_vs_private_df.index)
    shared_vs_private_df.reset_index(drop=True, inplace=True)
    shared_vs_private_df.to_csv(PATH_PROJECT.joinpath('outputs/proportion_shared.csv'), index=False)
