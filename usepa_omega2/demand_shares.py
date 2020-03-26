import pandas as pd
import numpy as np
from pathlib import Path


PATH_PROJECT = Path.cwd()
PATH_INPUTS = PATH_PROJECT.joinpath('inputs')

# this dict would be an input rather than hardcoded here but the point is to show that these coefficients_pmt could change year-over-year, if desired
coefficients_pmt = {'a': .1, 'b1': 1, 'b2': .8, 'b3': 1, 'b4': 1.1, 'b5': .5}
coefficients_shared_private = {'a': .1, 'b1': .8, 'b2': 1, 'b3': 1.1, 'b4': 1, 'b5': 1}
coefficients_bev_vs_ice = {'a': .1, 'b1': 1, 'b2': 1, 'b3': 0.8, 'b4': .1, 'b5': 1}


class DemandShares:
    """
    Calculate the light-duty PMT demand; the share of hauling vs non-hauling; the share of private vs shared; the share of ICE vs BEV

    :param: coefficients_pmt: a dictionary of constants and beta coefficients_pmt by calendar year
    :param pmt_metrics_dict:  a dictionary of input parameters providing calendar year-by-calendar year cost/mile for non-light-duty forms of mobility,
    average income, population, the value of individual's time
    :param: calendar_year: the calendar year for which demand is requested
    """

    def __init__(self, coefficients, economic_parameters_dict, calendar_year):
        self.coefficients = coefficients
        self.calendar_year = calendar_year
        self.economic_parameters_dict = economic_parameters_dict

    def pmt_lightduty(self, cost_per_mile_lightduty):
        """

        :param cost_per_mile_lightduty: a single value of fleetwide light-duty cost/mile for the prior year
        :return: a dictionary having a key=calendar_year and a value=demanded mile of travel for the given year
        """
        pmt = dict()
        exponent = self.coefficients['a'] \
                   + self.coefficients['b1'] * np.log(cost_per_mile_lightduty) \
                   + self.coefficients['b2'] * np.log(self.economic_parameters_dict[self.calendar_year]['OutsideOptionCost']) \
                   + self.coefficients['b3'] * np.log(self.economic_parameters_dict[self.calendar_year]['Income']) \
                   + self.coefficients['b4'] * np.log(self.economic_parameters_dict[self.calendar_year]['Population']) \
                   + self.coefficients['b5'] * np.log(self.economic_parameters_dict[self.calendar_year]['TimeCost'])
        pmt[self.calendar_year] = np.exp(exponent)
        return pmt

    def shared_vs_private(self, cost_per_mile_shared, cost_per_mile_private, cost_per_mile_sharedtime, cost_per_mile_privatetime):
        """

        :param cost_per_mile_shared:
        :param cost_per_mile_private:
        :return:
        """
        proportion_shared = dict()
        exponent = self.coefficients['a'] \
                   + self.coefficients['b1'] * np.log(cost_per_mile_shared) \
                   + self.coefficients['b2'] * np.log(cost_per_mile_private) \
                   + self.coefficients['b3'] * np.log(cost_per_mile_sharedtime) \
                   + self.coefficients['b4'] * np.log(cost_per_mile_privatetime) \
                   + self.coefficients['b5'] * np.log(self.economic_parameters_dict[self.calendar_year]['Income'])
        proportion_shared[self.calendar_year] = np.exp(exponent) / (1 + np.exp(exponent))
        return proportion_shared

    def bev_vs_ice(self, cost_per_mile_ice, cost_per_mile_bev):
        proportion_bev = dict()
        exponent = self.coefficients['a'] \
                   + self.coefficients['b1'] * np.log(self.economic_parameters_dict[self.calendar_year]['EVInconvenienceCost']) \
                   + self.coefficients['b2'] * np.log(cost_per_mile_ice) \
                   + self.coefficients['b3'] * np.log(cost_per_mile_bev) \
                   + self.coefficients['b4'] * np.log(self.calendar_year - 2000) \
                   + self.coefficients['b5'] * np.log(self.economic_parameters_dict[self.calendar_year]['Income'])
        proportion_bev[self.calendar_year] = np.exp(exponent) / (1 + np.exp(exponent))
        return proportion_bev


class CalcDemandShareMetrics:
    def __init__(self, calendar_year):
        self.calendar_year = calendar_year

    def calc_cost_per_mile_lightduty(self, fuel_prices_dict, gallons_per_mile, kWh_per_mile):
        # cost per mile LD ($/mile) = EnergyConsumptionRate (gal/mi or kWh/mi) * EnergyPrice ($/gal or $/kWh)
        cost_per_mile_lightduty = gallons_per_mile * fuel_prices_dict[self.calendar_year]['gasoline_retail'] \
                                  + kWh_per_mile * fuel_prices_dict[self.calendar_year]['electricity_residential']
        return cost_per_mile_lightduty

    def calc_cost_per_mile_shared(self, economic_parameters_dict, cost_per_mile_lightduty, cost_of_vehicle, divisor):
        # cost per mile of shared ($/mile) = [SharedLaborCost($/hr) / AverageTripSpeed(miles/hour)
        #                                    * (1+SharedDeadheadFraction)]
        #                                    + [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                                    + [EnergyConsumptionRate (gal/mi or kWh/mi)
        #                                    * EnergyPrice ($/gal or $/kWh)]
        cost_per_mile_shared = (economic_parameters_dict[self.calendar_year]['SharedLaborCost'] / economic_parameters_dict[self.calendar_year]['AverageTripSpeed'] \
                               * (1 + economic_parameters_dict[self.calendar_year]['SharedDeadheadFraction'])) \
                               + (cost_of_vehicle / divisor) \
                               + cost_per_mile_lightduty
        return cost_per_mile_shared

    def calc_cost_per_mile_private(self, cost_per_mile_lightduty, cost_of_vehicle, divisor):
        # cost per mile of private = [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                            + [EnergyConsumptionRate (gal/mi or kWh/mi)
        #                            * EnergyPrice ($/gal or $/kWh)]
        cost_per_mile_private = (cost_of_vehicle / divisor) + cost_per_mile_lightduty
        return cost_per_mile_private

    def calc_cost_per_mile_ice(self, fuel_prices_dict, gallons_per_mile, cost_of_vehicle, divisor):
        # cost per mile of ICE ($/mile) = [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                                 + [EnergyConsumptionRate (gal/mile) * EnergyPrice ($/gal)]
        cost_per_mile_ice = (cost_of_vehicle / divisor) \
                            + gallons_per_mile * fuel_prices_dict[self.calendar_year]['gasoline_retail']
        return cost_per_mile_ice

    def calc_cost_per_mile_bev(self, fuel_prices_dict, kWh_per_mile, cost_of_vehicle, divisor):
        # cost per mile of EV ($/mile) =  [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                                 + [EnergyConsumptionRate (kWh/mi) * EnergyPrice ($/kWh)]
        cost_per_mile_bev = (cost_of_vehicle / divisor) \
                            + kWh_per_mile * fuel_prices_dict[self.calendar_year]['electricity_residential']
        return cost_per_mile_bev

    def calc_timecost_private(self, economic_parameters_dict):
        # time cost of private ($/mile) = [PrivateOverheadTime(minutes / mile) * 1 / 60 * TimeCost($ / hr)]
        cost_per_mile_privatetime = economic_parameters_dict[self.calendar_year]['PrivateOverheadTime'] \
                                    * (1 / 60) \
                                    * economic_parameters_dict[self.calendar_year]['TimeCost']
        return cost_per_mile_privatetime

    def calc_timecost_shared(self, economic_parameters_dict):
        # time cost of shared ($/mile) = SharedWaitTime (minutes/trip) * 1/60 * TimeCost ($/hr) * 1 / AverageTripLength (mile/trip)
        cost_per_mile_sharedtime = economic_parameters_dict[self.calendar_year]['SharedWaitTime'] \
                                   * (1 / 60) \
                                   * economic_parameters_dict[self.calendar_year]['TimeCost'] \
                                   * (1 / economic_parameters_dict[self.calendar_year]['AverageTripLength'])
        return cost_per_mile_sharedtime


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

    :param list_of_metrics: A list of fuel price metrics to gather.
    """

    def __init__(self, list_of_metrics):
        self.list_of_metrics = list_of_metrics

    def get_petrol_prices(self, aeo_case):
        """

        :param aeo_case: This should be set via an input file.
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

    def get_electricity_prices(self, aeo_case):
        """

        :param aeo_case: This should be set via an input file.
        :return: A fuel_prices DataFrame.
        """
        fuel_prices_file = PATH_INPUTS.joinpath('Electricity_Supply_Disposition_Prices_and_Emissions_' + aeo_case + '.csv')
        fuel_prices_full = pd.read_csv(fuel_prices_file, skiprows=4)
        fuel_prices_full = fuel_prices_full[fuel_prices_full.columns[:-1]]
        fuel_prices_full.drop(labels=['full name', 'api key', 'units'], axis=1, inplace=True)
        fuel_prices = fuel_prices_full.dropna(axis=0, how='any')
        fuel_prices = fuel_prices.loc[fuel_prices['Unnamed: 0'].str.contains('electricity', case=False)]
        fuel_prices.rename(columns={'Unnamed: 0': ''}, inplace=True)
        fuel_prices.set_index(keys=[''], inplace=True)
        fuel_prices = fuel_prices.transpose()
        fuel_prices.insert(0, 'calendar_year', fuel_prices.index)
        fuel_prices['calendar_year'] = pd.to_numeric(fuel_prices['calendar_year'])
        fuel_prices.set_index('calendar_year', drop=True, inplace=True)
        fuel_prices = fuel_prices[self.list_of_metrics]
        return fuel_prices


def main():
    # read fuel prices file and create dictionary (unless it's already been done)
    try:
        fuel_prices
    except:
        fuel_prices_petrol = GetFuelPrices(['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax']).get_petrol_prices('Reference')
        fuel_prices_electricity = GetFuelPrices('electricity_residential').get_electricity_prices('Reference')
    fuel_prices = pd.concat([fuel_prices_petrol, fuel_prices_electricity], axis=1)
    fuel_prices = DealWithParameters(fuel_prices).adjust_units('electricity_residential', .01)
    fuel_prices_dict = fuel_prices.to_dict('index')

    economic_parameters = pd.read_excel(PATH_INPUTS.joinpath('OMEGA2ToyModel_EconomicParameters_20200324.xlsx'), index_col=0, skiprows=1)
    economic_parameters = DealWithParameters(economic_parameters).adjust_units(['Income', 'NumberofHouseholds'], 1000)
    economic_parameters = DealWithParameters(economic_parameters).adjust_units('Population', 1000000)
    economic_parameters_dict = economic_parameters.to_dict('index')

    # calculated needed cost per mile metrics for given calendar year
    pmt_dict = dict()
    shared_vs_private_dict = dict()
    bev_vs_ice_dict = dict()
    for calendar_year in fuel_prices_dict.keys(): #economic_parameters_dict.keys(): this would be better but current fuel prices inputs don't go back to 1980
        cost_per_mile_lightduty = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_lightduty(fuel_prices_dict, (1/35), 0.35)
        cost_per_mile_shared = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_shared(economic_parameters_dict, cost_per_mile_lightduty, 35000, 50000)
        cost_per_mile_private = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_private(cost_per_mile_lightduty, 35000, 50000)
        cost_per_mile_ice = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_ice(fuel_prices_dict, (1/35), 35000, 50000)
        cost_per_mile_bev = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_bev(fuel_prices_dict, 0.35, 45000, 50000)
        cost_per_mile_privatetime = CalcDemandShareMetrics(calendar_year).calc_timecost_private(economic_parameters_dict)
        cost_per_mile_sharedtime = CalcDemandShareMetrics(calendar_year).calc_timecost_shared(economic_parameters_dict)

        pmt_dict.update(DemandShares(coefficients_pmt, economic_parameters_dict, calendar_year).pmt_lightduty(cost_per_mile_lightduty))
        shared_vs_private_dict.update(DemandShares(coefficients_shared_private, economic_parameters_dict, calendar_year)
                                      .shared_vs_private(cost_per_mile_shared, cost_per_mile_private, cost_per_mile_sharedtime, cost_per_mile_privatetime))
        bev_vs_ice_dict.update(DemandShares(coefficients_bev_vs_ice, economic_parameters_dict, calendar_year).bev_vs_ice(cost_per_mile_ice, cost_per_mile_bev))

    # the following is only to create DataFrames for write/save
    pmt_df = pd.DataFrame([item for item in pmt_dict.values()], [item for item in pmt_dict.keys()])
    pmt_df.rename(columns={0: 'PMT_Demand'}, inplace=True)
    pmt_df.insert(0, 'Calendar_Year', pmt_df.index)
    pmt_df.reset_index(drop=True, inplace=True)

    shared_vs_private_df = pd.DataFrame([item for item in shared_vs_private_dict.values()], [item for item in shared_vs_private_dict.keys()])
    shared_vs_private_df.rename(columns={0: 'Proportion_Shared'}, inplace=True)
    shared_vs_private_df.insert(0, 'Calendar_Year', shared_vs_private_df.index)
    shared_vs_private_df.reset_index(drop=True, inplace=True)

    bev_vs_ice_df = pd.DataFrame([item for item in bev_vs_ice_dict.values()], [item for item in bev_vs_ice_dict.keys()])
    bev_vs_ice_df.rename(columns={0: 'Proportion_BEV'}, inplace=True)
    bev_vs_ice_df.insert(0, 'Calendar_Year', bev_vs_ice_df.index)
    bev_vs_ice_df.reset_index(drop=True, inplace=True)

    pmt_df.to_csv(PATH_PROJECT.joinpath('outputs/pmt_demand.csv'), index=False)
    shared_vs_private_df.to_csv(PATH_PROJECT.joinpath('outputs/proportion_shared.csv'), index=False)
    bev_vs_ice_df.to_csv(PATH_PROJECT.joinpath('outputs/proportion_bev.csv'), index=False)


if __name__ == '__main__':
    main()
