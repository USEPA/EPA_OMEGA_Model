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


class DealWithParameters:
    def __init__(self, parameters_df):
        self.parameters_df = parameters_df

    def adjust_units(self, list_of_metrics, multiplier):
        temp_df = self.parameters_df.copy()
        temp_df[list_of_metrics] = temp_df[list_of_metrics] * multiplier
        return temp_df


class GetFuelPrices:
    """
    The GetFuelPrices class grabs the appropriate fuel prices from the aeo folder, cleans up some naming and creates a fuel_prices DataFrame for use in operating costs.

    :param _path_project: Well, this is the path of the project and the parent of the aeo directory.
    """

    def __init__(self, list_of_metrics):
        self.list_of_metrics = list_of_metrics

    def get_fuel_prices(self, aeo_case):
        """

        :param _aeo_case: From the BCA inputs sheet - the AEO fuel case to use (a CSV of fuel prices must exist in the aeo directory).
        :param _metrics: A list of fuel prices to gather (i.e., gasoline, diesel, retail, pre-tax, etc.)
        :return: A fuel_prices DataFrame.
        """
        fuel_prices_file = PATH_INPUTS.joinpath('Components_of_Selected_Petroleum_Product_Prices_' + aeo_case + '.csv')
        fuel_prices_full = pd.read_csv(fuel_prices_file, skiprows=4)
        fuel_prices_full = fuel_prices_full[fuel_prices_full.columns[:-1]]
        fuel_prices_full.drop(labels=['full name', 'api key', 'units'], axis=1, inplace=True)
        fuel_prices = fuel_prices_full.dropna(axis=0, how='any')
        diesel = fuel_prices.loc[fuel_prices['Unnamed: 0'].str.contains('diesel', case=False)]
        gasoline = fuel_prices.loc[fuel_prices['Unnamed: 0'].str.contains('gasoline', case=False)]
        fuel_prices = gasoline.append(diesel)
        fuel_prices.rename(columns={'Unnamed: 0': ''}, inplace=True)
        fuel_prices.set_index(keys=[''], inplace=True)
        fuel_prices = fuel_prices.transpose()
        fuel_prices.insert(0, 'calendar_year', fuel_prices.index)
        fuel_prices['calendar_year'] = pd.to_numeric(fuel_prices['calendar_year'])
        fuel_prices.set_index('calendar_year', drop=True, inplace=True)
        for fuel in ['gasoline', 'diesel']:
            fuel_prices.insert(len(fuel_prices.columns), fuel + '_pretax', fuel_prices[fuel + '_distribution'] + fuel_prices[fuel + '_wholesale'])
        # fuel_prices = fuel_prices[['calendar_year'] + self.list_of_metrics]
        fuel_prices = fuel_prices[self.list_of_metrics]
        return fuel_prices


def main():
    fuel_prices = GetFuelPrices(['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax']).get_fuel_prices('Reference')
    fuel_prices_dict = fuel_prices.to_dict('index')

    data = pd.read_excel(PATH_INPUTS.joinpath('OMEGA2ToyModel_EconomicParameters_20200324.xlsx'), index_col=0, skiprows=1)
    data = DealWithParameters(data).adjust_units(['Income', 'NumberofHouseholds'], 1000)
    data = DealWithParameters(data).adjust_units('Population', 1000000)

    data.insert(len(data.columns), 'cost_per_mile_lightduty', )

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


if __name__ == '__main__':
    main()
