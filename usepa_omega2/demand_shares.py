import pandas as pd
import numpy as np
from pathlib import Path
# from usepa_omega2.fuel_prices import GetFuelPrices
from usepa_omega2.fleet_metrics import FleetMetrics


PATH_PROJECT = Path.cwd()
PATH_INPUTS = PATH_PROJECT.joinpath('inputs')

# this dict would be an input rather than hardcoded here but the point is to show that these coefficients_pmt could change year-over-year, if desired
coefficients_pmt = {'a': .1, 'b1': 1, 'b2': .8, 'b3': 1, 'b4': 1.1, 'b5': .5}
coefficients_shared_vs_private = {'a': .1, 'b1': .1, 'b2': -2, 'b3': .1, 'b4': -.05, 'b5': -.00001}
coefficients_bev_vs_ice = {'a': .1, 'b1': -1, 'b2': -2, 'b3': .1, 'b4': -.2, 'b5': .0001}
tco_divisor = 50000 # units are miles


class DemandShares:
    """
    Calculate the light-duty PMT demand; the share of hauling vs non-hauling; the share of private vs shared; the share of ICE vs BEV

    :param: coefficients_pmt: a dictionary of constants and beta coefficients_pmt by calendar year
    :param pmt_metrics_dict:  a dictionary of input parameters providing calendar year-by-calendar year cost/mile for non-light-duty forms of mobility,
    average income, population, the value of individual's time
    :param: calendar_year: the calendar year for which demand is requested
    """
# TODO should the income metric used in this class be personal income or mean household income?
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
                   + self.coefficients['b1'] * cost_per_mile_shared \
                   + self.coefficients['b2'] * cost_per_mile_private \
                   + self.coefficients['b3'] * cost_per_mile_sharedtime \
                   + self.coefficients['b4'] * cost_per_mile_privatetime \
                   + self.coefficients['b5'] * self.economic_parameters_dict[self.calendar_year]['Income']
        proportion_shared[self.calendar_year] = np.exp(exponent) / (1 + np.exp(exponent))
        return proportion_shared

    def bev_vs_ice(self, cost_per_mile_ice, cost_per_mile_bev):
        proportion_bev = dict()
        exponent = self.coefficients['a'] \
                   + self.coefficients['b1'] * self.economic_parameters_dict[self.calendar_year]['EVInconvenienceCost'] \
                   + self.coefficients['b2'] * cost_per_mile_ice \
                   + self.coefficients['b3'] * cost_per_mile_bev \
                   + self.coefficients['b4'] * (self.calendar_year - 2000) \
                   + self.coefficients['b5'] * self.economic_parameters_dict[self.calendar_year]['Income']
        proportion_bev[self.calendar_year] = np.exp(exponent) / (1 + np.exp(exponent))
        return proportion_bev


class CalcDemandShareMetrics:
    def __init__(self, calendar_year):
        self.calendar_year = calendar_year

    def calc_cost_per_mile_lightduty(self, economic_parameters_dict, energy_consump_rates, vmts):
        # cost per mile LD ($/mile) = EnergyConsumptionRate (gal/mi or kWh/mi) * EnergyPrice ($/gal or $/kWh)
        cpm_numerator = 0
        cpm_denominator = 0
        for hauling_class in ['Hauling', 'NonHauling']:
            for ownership_class in ['Private', 'Shared']:
                for fuel_class in ['Petroleum']:
                    cpm_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                     * vmts[(fuel_class, hauling_class, ownership_class)] \
                                     * economic_parameters_dict[self.calendar_year]['GasolinePrice']
                for fuel_class in ['Electricity']:
                    cpm_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                     * vmts[(fuel_class, hauling_class, ownership_class)] \
                                     * economic_parameters_dict[self.calendar_year]['ElectricityPrice']
                for fuel_class in ['Petroleum', 'Electricity']:
                    cpm_denominator += vmts[(fuel_class, hauling_class, ownership_class)]
        cpm = cpm_numerator / cpm_denominator
        return cpm

    def calc_cost_per_mile_shared(self, economic_parameters_dict, energy_consump_rates, vmts, prices, volumes, divisor):
        # cost per mile of shared ($/mile) = [SharedLaborCost($/hr) / AverageTripSpeed(miles/hour)
        #                                    * (1+SharedDeadheadFraction)]
        #                                    + [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                                    + [EnergyConsumptionRate (gal/mi or kWh/mi)
        #                                    * EnergyPrice ($/gal or $/kWh)]
        cpm_price_numerator = 0
        cpm_price_denominator = 0
        cpm_fuel_numerator = 0
        cpm_fuel_denominator = 0
        for hauling_class in ['Hauling', 'NonHauling']:
            for ownership_class in ['Shared']:
                for fuel_class in ['Petroleum', 'Electricity']:
                    cpm_price_numerator += prices[(fuel_class, hauling_class, ownership_class)] * volumes[(fuel_class, hauling_class, ownership_class)] / divisor
                    cpm_price_denominator += volumes[(fuel_class, hauling_class, ownership_class)]
                for fuel_class in ['Petroleum']:
                    cpm_fuel_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                          * vmts[(fuel_class, hauling_class, ownership_class)] \
                                          * economic_parameters_dict[self.calendar_year]['GasolinePrice']
                for fuel_class in ['Electricity']:
                    cpm_fuel_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                          * vmts[(fuel_class, hauling_class, ownership_class)] \
                                          * economic_parameters_dict[self.calendar_year]['ElectricityPrice']
                for fuel_class in ['Petroleum', 'Electricity']:
                    cpm_fuel_denominator += vmts[(fuel_class, hauling_class, ownership_class)]
        cpm = (economic_parameters_dict[self.calendar_year]['SharedLaborCost'] / economic_parameters_dict[self.calendar_year]['AverageTripSpeed']
               * (1 + economic_parameters_dict[self.calendar_year]['SharedDeadheadFraction'])) \
              + cpm_price_numerator / cpm_price_denominator \
              + cpm_fuel_numerator / cpm_fuel_denominator
        return cpm

    def calc_cost_per_mile_private(self, economic_parameters_dict, energy_consump_rates, vmts, prices, volumes, divisor):
        # cost per mile of private = [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                            + [EnergyConsumptionRate (gal/mi or kWh/mi)
        #                            * EnergyPrice ($/gal or $/kWh)]
        cpm_price_numerator = 0
        cpm_price_denominator = 0
        cpm_fuel_numerator = 0
        cpm_fuel_denominator = 0
        for hauling_class in ['Hauling', 'NonHauling']:
            for ownership_class in ['Private']:
                for fuel_class in ['Petroleum', 'Electricity']:
                    cpm_price_numerator += prices[(fuel_class, hauling_class, ownership_class)] * volumes[(fuel_class, hauling_class, ownership_class)] / divisor
                    cpm_price_denominator += volumes[(fuel_class, hauling_class, ownership_class)]
                for fuel_class in ['Petroleum']:
                    cpm_fuel_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                          * vmts[(fuel_class, hauling_class, ownership_class)] \
                                          * economic_parameters_dict[self.calendar_year]['GasolinePrice']
                for fuel_class in ['Electricity']:
                    cpm_fuel_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                          * vmts[(fuel_class, hauling_class, ownership_class)] \
                                          * economic_parameters_dict[self.calendar_year]['ElectricityPrice']
                for fuel_class in ['Petroleum', 'Electricity']:
                    cpm_fuel_denominator += vmts[(fuel_class, hauling_class, ownership_class)]
        cpm = cpm_price_numerator / cpm_price_denominator \
              + cpm_fuel_numerator / cpm_fuel_denominator
        return cpm

    def calc_cost_per_mile_fuel_class(self, economic_parameters_dict, energy_consump_rates, vmts, prices, volumes, fuel_class_value, divisor):
        # cost per mile of ICE ($/mile) = [VehicleCost ($'s, from ProducerModule or IniitalFleet file) / 50,000 (miles)]
        #                                 + [EnergyConsumptionRate (gal/mile) * EnergyPrice ($/gal)]
        cpm_price_numerator = 0
        cpm_price_denominator = 0
        cpm_fuel_numerator = 0
        cpm_fuel_denominator = 0
        if fuel_class_value == 'Petroleum':
            fuel_price_value = 'GasolinePrice'
        else:
            fuel_price_value = 'ElectricityPrice'
        for hauling_class in ['Hauling', 'NonHauling']:
            for ownership_class in ['Shared', 'Private']:
                for fuel_class in [fuel_class_value]:
                    cpm_price_numerator += prices[(fuel_class, hauling_class, ownership_class)] * volumes[(fuel_class, hauling_class, ownership_class)] / divisor
                    cpm_price_denominator += volumes[(fuel_class, hauling_class, ownership_class)]
                    cpm_fuel_numerator += energy_consump_rates[(fuel_class, hauling_class, ownership_class)] \
                                          * vmts[(fuel_class, hauling_class, ownership_class)] \
                                          * economic_parameters_dict[self.calendar_year][fuel_price_value]
                    cpm_fuel_denominator += vmts[(fuel_class, hauling_class, ownership_class)]
        cpm = cpm_price_numerator / cpm_price_denominator \
              + cpm_fuel_numerator / cpm_fuel_denominator
        return cpm

    def calc_timecost_private(self, economic_parameters_dict):
        # time cost of private ($/mile) = [PrivateOverheadTime(minutes / mile) * 1 / 60 * TimeCost($ / hr)]
        cpm = economic_parameters_dict[self.calendar_year]['PrivateOverheadTime'] \
              * (1 / 60) \
              * economic_parameters_dict[self.calendar_year]['TimeCost']
        return cpm

    def calc_timecost_shared(self, economic_parameters_dict):
        # time cost of shared ($/mile) = SharedWaitTime (minutes/trip) * 1/60 * TimeCost ($/hr) * 1 / AverageTripLength (mile/trip)
        cpm = economic_parameters_dict[self.calendar_year]['SharedWaitTime'] \
              * (1 / 60) \
              * economic_parameters_dict[self.calendar_year]['TimeCost'] \
              * (1 / economic_parameters_dict[self.calendar_year]['AverageTripLength'])
        return cpm


class DealWithParameters:
    def __init__(self, parameters_df):
        self.parameters_df = parameters_df

    def adjust_units(self, list_of_metrics, multiplier):
        temp_df = self.parameters_df.copy()
        temp_df[list_of_metrics] = temp_df[list_of_metrics] * multiplier
        return temp_df


def main():
    # read fuel prices file and create dictionary (unless it's already been done and unless fuel prices are in the economic parameters file)
    # try:
    #     fuel_prices
    # except:
    #     fuel_prices_petrol = GetFuelPrices(['gasoline_retail', 'gasoline_pretax', 'diesel_retail', 'diesel_pretax'], PATH_INPUTS).get_petrol_prices('Reference')
    #     fuel_prices_electricity = GetFuelPrices('electricity_residential', PATH_INPUTS).get_electricity_prices('Reference')
    # fuel_prices = pd.concat([fuel_prices_petrol, fuel_prices_electricity], axis=1)
    # fuel_prices = DealWithParameters(fuel_prices).adjust_units('electricity_residential', .01)
    # fuel_prices_dict = fuel_prices.to_dict('index')

    # read and adjust some elements of the economic parameters file
    economic_parameters = pd.read_excel(PATH_INPUTS.joinpath('OMEGA2ToyModel_EconomicParameters.xlsx'), index_col=0, skiprows=1)
    economic_parameters = DealWithParameters(economic_parameters).adjust_units(['Income', 'NumberOfHouseholds'], 1000)
    economic_parameters = DealWithParameters(economic_parameters).adjust_units('Population', 1000000)
    economic_parameters_dict = economic_parameters.to_dict('index')

    # read initial fleet file & create a dictionary of DataFrames of subfleets
    fleet_initial = pd.read_excel(PATH_INPUTS.joinpath('OMEGA2ToyModel_InitialFleet.xlsx'))
    fleet_initial.insert(0, 'FC_HC_OC', pd.Series(zip(fleet_initial['FuelClass'], fleet_initial['HaulingClass'], fleet_initial['OwnershipClass'])))
    fleets = dict()
    for fuel_class in ['Petroleum', 'Electricity']:
        for hauling_class in ['Hauling', 'NonHauling']:
            for ownership_class in ['Private', 'Shared']:
                fleets[(fuel_class, hauling_class, ownership_class)] = fleet_initial.loc[(fleet_initial['FC_HC_OC'] == (fuel_class, hauling_class, ownership_class))
                                                                                         & (fleet_initial['Volume'] > 0), :]
                fleets[(fuel_class, hauling_class, ownership_class)].reset_index(drop=True, inplace=True)

    # calculate needed metrics for each of the subfleets
    energy_consump_rates = dict()
    vmts = dict()
    volumes = dict()
    prices = dict()
    for fuel_class in ['Petroleum', 'Electricity']:
        for hauling_class in ['Hauling', 'NonHauling']:
            for ownership_class in ['Private', 'Shared']:
                fleet = FleetMetrics(fleets[(fuel_class, hauling_class, ownership_class)])
                energy_consump_rates[(fuel_class, hauling_class, ownership_class)] = fleet.fleet_metric_weighted('FC', 'VehicleMilesTraveled')
                vmts[(fuel_class, hauling_class, ownership_class)] = fleet.fleet_metric_sum('VehicleMilesTraveled')
                volumes[(fuel_class, hauling_class, ownership_class)] = fleet.fleet_metric_sum('Volume')
                prices[(fuel_class, hauling_class, ownership_class)] = fleet.fleet_metric_weighted('TransactionPrice', 'Volume')

    # calculate needed cost per mile metrics for every calendar year
    pmt_dict = dict()
    shared_vs_private_dict = dict()
    bev_vs_ice_dict = dict()
    for calendar_year in range(fleet_initial['CalendarYear'].max() + 1, list(economic_parameters_dict.keys())[-1] + 1):
        # note: cpm refers to 'cost per mile'
        cpm_lightduty = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_lightduty(economic_parameters_dict,
                                                                                           energy_consump_rates,
                                                                                           vmts)
        cpm_shared = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_shared(economic_parameters_dict,
                                                                                     energy_consump_rates,
                                                                                     vmts,
                                                                                     prices,
                                                                                     volumes,
                                                                                     tco_divisor)
        cpm_private = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_private(economic_parameters_dict,
                                                                                       energy_consump_rates,
                                                                                       vmts,
                                                                                       prices,
                                                                                       volumes,
                                                                                       tco_divisor)
        cpm_ice = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_fuel_class(economic_parameters_dict,
                                                                                      energy_consump_rates,
                                                                                      vmts,
                                                                                      prices,
                                                                                      volumes,
                                                                                      'Petroleum',
                                                                                      tco_divisor)
        cpm_bev = CalcDemandShareMetrics(calendar_year).calc_cost_per_mile_fuel_class(economic_parameters_dict,
                                                                                      energy_consump_rates,
                                                                                      vmts,
                                                                                      prices,
                                                                                      volumes,
                                                                                      'Electricity',
                                                                                      tco_divisor)
        cpm_privatetime = CalcDemandShareMetrics(calendar_year).calc_timecost_private(economic_parameters_dict)
        cpm_sharedtime = CalcDemandShareMetrics(calendar_year).calc_timecost_shared(economic_parameters_dict)

        pmt_dict.update(DemandShares(coefficients_pmt, economic_parameters_dict, calendar_year).pmt_lightduty(cpm_lightduty))
        shared_vs_private_dict.update(DemandShares(coefficients_shared_vs_private, economic_parameters_dict, calendar_year)
                                      .shared_vs_private(cpm_shared, cpm_private, cpm_sharedtime, cpm_privatetime))
        bev_vs_ice_dict.update(DemandShares(coefficients_bev_vs_ice, economic_parameters_dict, calendar_year).bev_vs_ice(cpm_ice, cpm_bev))

    # the following is only to create a DataFrame for write/save
    demand_shares_df = pd.DataFrame()
    demand_shares_df.insert(0, 'Calendar_Year', [item for item in pmt_dict.keys()])
    demand_shares_df.set_index('Calendar_Year', inplace=True)
    pmt_df = pd.DataFrame([item for item in pmt_dict.values()], [item for item in pmt_dict.keys()])
    pmt_df.rename(columns={0: 'PMT_Demand'}, inplace=True)

    shared_vs_private_df = pd.DataFrame([item for item in shared_vs_private_dict.values()], [item for item in shared_vs_private_dict.keys()])
    shared_vs_private_df.rename(columns={0: 'Proportion_Shared'}, inplace=True)

    bev_vs_ice_df = pd.DataFrame([item for item in bev_vs_ice_dict.values()], [item for item in bev_vs_ice_dict.keys()])
    bev_vs_ice_df.rename(columns={0: 'Proportion_BEV'}, inplace=True)

    demand_shares_df = demand_shares_df.join(pmt_df).join(shared_vs_private_df).join(bev_vs_ice_df)
    demand_shares_df.to_csv(PATH_PROJECT.joinpath('outputs/demand_shares.csv'))


if __name__ == '__main__':
    main()
