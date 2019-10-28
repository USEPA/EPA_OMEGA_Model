"""
manufacturer.py
===============


"""

import pandas as pd
import copy

from credits import *
from vehicle import *
# from copy import copy, deepcopy

class Manufacturer:
    def __init__(self, name):
        self.name = str(name)
        self.credit = CreditBank()

        self.production = Vehicle()  # so pyreverse can tell what kind of dict
        self.production = dict()     # vehicle production by year

        self.emissions_target_net_co2_Mg = dict()           # emissions target by year
        self.emissions_achieved_tailpipe_co2_Mg = dict()    # emissions achieved by year
        self.emissions_credits_tailpipe_co2_Mg = dict()     # credits tailpipe by year
        self.emissions_credits_running_tailpipe_co2_Mg = dict()     # total credits tailpipe by year
        self.tech_production_cost_delta_dollars = dict()    # tech production cost delta from initial (compliance tech cost)
        self.tech_production_running_cost_delta_dollars = dict()    # tech production running cost delta from initial (total compliance tech cost)
        self.sales = dict() # vehicle sales by year
        self.tech_production_cost_dollars_per_vehicle = dict()  # average tech production cost per vehicle

    def __str__(self):
        s = '\n<manufacturer.Manufacturer object at %#x>\n' % id(self)
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def __deepcopy__(self, memodict={}):
        cls = self.__class__
        result = cls.__new__(cls)
        memodict[id(self)] = result
        result.__init__(self.name)
        result.credit = copy.deepcopy(self.credit)
        result.emissions_credits_running_tailpipe_co2_Mg = copy.deepcopy(self.emissions_credits_running_tailpipe_co2_Mg)
        result.tech_production_running_cost_delta_dollars = copy.deepcopy(self.tech_production_running_cost_delta_dollars)
        return result

    def calc_manufacturer_emissions_costs_sales(self, calendar_year, init=False):
        mfr_emissions_target_net_co2_Mg = 0.0
        mfr_emissions_achieved_tailpipe_co2_Mg = 0.0
        mfr_tech_production_cost_delta_dollars = 0.0
        mfr_sales = 0

        for v in self.production[calendar_year]:
            mfr_emissions_target_net_co2_Mg = mfr_emissions_target_net_co2_Mg + v.emissions_target_net_co2_Mg
            mfr_emissions_achieved_tailpipe_co2_Mg = mfr_emissions_achieved_tailpipe_co2_Mg + v.emissions_achieved_tailpipe_co2_Mg
            mfr_tech_production_cost_delta_dollars = mfr_tech_production_cost_delta_dollars + v.tech_package_cost_production_delta_dollars
            mfr_sales = mfr_sales + v.sales

        self.emissions_target_net_co2_Mg[calendar_year] = mfr_emissions_target_net_co2_Mg
        self.emissions_achieved_tailpipe_co2_Mg[calendar_year] = mfr_emissions_achieved_tailpipe_co2_Mg
        self.emissions_credits_tailpipe_co2_Mg[calendar_year] = mfr_emissions_target_net_co2_Mg - mfr_emissions_achieved_tailpipe_co2_Mg
        self.tech_production_cost_delta_dollars[calendar_year] =  mfr_tech_production_cost_delta_dollars
        self.sales[calendar_year] = mfr_sales
        self.tech_production_cost_dollars_per_vehicle[calendar_year] = self.tech_production_cost_delta_dollars[calendar_year] / self.sales[calendar_year]

        # calculate cumulative costs and credits
        if (calendar_year - 1) in self.tech_production_running_cost_delta_dollars:
            self.tech_production_running_cost_delta_dollars[calendar_year] = self.tech_production_running_cost_delta_dollars[calendar_year - 1] + self.tech_production_cost_delta_dollars[calendar_year]
            self.emissions_credits_running_tailpipe_co2_Mg[calendar_year] = self.emissions_credits_running_tailpipe_co2_Mg[calendar_year - 1] + self.emissions_credits_tailpipe_co2_Mg[calendar_year]
        else:
            self.tech_production_running_cost_delta_dollars[calendar_year] = self.tech_production_cost_delta_dollars[calendar_year]
            self.emissions_credits_running_tailpipe_co2_Mg[calendar_year] = self.emissions_credits_tailpipe_co2_Mg[calendar_year]


    def update_vehicle_emissions_targets(self, calendar_year):
        for v in self.production[calendar_year]:
            v.update_vehicle_emissions_targets(calendar_year)

    def start_production(self, calendar_year):
        # copy prior year's vehicles
        self.production[calendar_year] = copy.deepcopy(self.production[calendar_year - 1])
        # update vehicle emissions targets
        self.update_vehicle_emissions_targets(calendar_year)
        # recalculate manufacturer emissions
        self.calc_manufacturer_emissions_costs_sales(calendar_year)

    def init_fleet(self, calendar_year, initial_fleet_filename):
        """

        :return:
        """
        self.production[calendar_year] = []
        initial_fleet_df = pd.read_csv(initial_fleet_filename)

        vehicles_df = initial_fleet_df.loc[initial_fleet_df['Manufacturer'] == self.name]
        for index, row in vehicles_df.iterrows():
            v = Vehicle()
            self.production[calendar_year].append(v)
            v.init_vehicle_from_dataframe(row)
        self.calc_manufacturer_emissions_costs_sales(calendar_year)


if __name__ == '__main__':
    print('manufacturer.py')
