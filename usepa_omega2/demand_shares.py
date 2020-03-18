import pandas as pd
import numpy as np

# this dict would be an input rather than hardcoded here but the point is to show that these coefficients could change year-over-year, if desired
coefficients = {2021: {'a': 1, 'b1': 1, 'b2': 2, 'b3': 3, 'b4': 4, 'b5': 5},
                2022: {'a': 1, 'b1': 1.1, 'b2': .9, 'b3': .8, 'b4': .7, 'b5': .6}}


class DemandShares:
    """
    Calculate the light-duty PMT demand; the share of hauling vs non-hauling; the share of private vs shared; the share of ICE vs BEV

    :param: coefficients: a dictionary of constants and beta coefficients by calendar year
    """
    def __init__(self, coefficients):
        self.coefficients = coefficients

    def pmt_lightduty(self, calendar_years, cost_per_mile_lightduty, cost_per_mile_other, avg_income, population, cost_of_time):
        pmt = dict()
        for calendar_year in calendar_years:
            pmt[calendar_year] = np.exp((self.coefficients[calendar_year]['a'])
                                        + self.coefficients[calendar_year]['b1'] * np.log(cost_per_mile_lightduty)
                                        + self.coefficients[calendar_year]['b2'] * np.log(cost_per_mile_other)
                                        + self.coefficients[calendar_year]['b3'] * np.log(avg_income)
                                        + self.coefficients[calendar_year]['b4'] * np.log(population)
                                        + self.coefficients[calendar_year]['b5'] * np.log(cost_of_time))
        return pmt
