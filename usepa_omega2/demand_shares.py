import numpy as np

# this dict would be an input rather than hardcoded here but the point is to show that these coefficients could change year-over-year, if desired
coefficients = {'a': .1, 'b1': 1, 'b2': .8, 'b3': 1, 'b4': 1.1, 'b5': .5}
pmt_metrics_dict = {2018: {'cost_per_mile_other': .1, 'avg_income': 50000, 'population': 300000000, 'cost_of_time': 30},
                    2019: {'cost_per_mile_other': .11, 'avg_income': 51000, 'population': 301000000, 'cost_of_time': 31},
                    2020: {'cost_per_mile_other': .12, 'avg_income': 52000, 'population': 302000000, 'cost_of_time': 32}}


class DemandShares:
    """
    Calculate the light-duty PMT demand; the share of hauling vs non-hauling; the share of private vs shared; the share of ICE vs BEV

    :param: coefficients: a dictionary of constants and beta coefficients by calendar year
    :param: calendar_year: the calendar year for which demand is requested
    """

    def __init__(self, coefficients, calendar_year):
        self.coefficients = coefficients
        self.calendar_year = calendar_year

    def pmt_lightduty(self, cost_per_mile_lightduty, pmt_metrics_dict):
        """

        :param cost_per_mile_lightduty: a single value of fleetwide light-duty cost/mile for the prior year
        :param pmt_metrics_dict:  a dictionary of input parameters providing calendar year-by-calendar year cost/mile for non-light-duty forms of mobility,
        average income, population, the value of individual's time
        :return: a dictionary having a key=calendar_year and a value=demanded mile of travel for the given year
        """
        pmt = dict()
        pmt[self.calendar_year] = np.exp(self.coefficients['a']
                                         + self.coefficients['b1'] * np.log(cost_per_mile_lightduty)
                                         + self.coefficients['b2'] * np.log(pmt_metrics_dict[self.calendar_year]['cost_per_mile_other'])
                                         + self.coefficients['b3'] * np.log(pmt_metrics_dict[self.calendar_year]['avg_income'])
                                         + self.coefficients['b4'] * np.log(pmt_metrics_dict[self.calendar_year]['population'])
                                         + self.coefficients['b5'] * np.log(pmt_metrics_dict[self.calendar_year]['cost_of_time']))
        return pmt


pmt_dict = dict()
for calendar_year in [2018, 2019, 2020]:
    pmt_dict.update(DemandShares(coefficients, calendar_year).pmt_lightduty(.12, pmt_metrics_dict))
