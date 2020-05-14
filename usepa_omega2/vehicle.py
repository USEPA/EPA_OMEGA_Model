"""
vehicle.py
==========


"""

import numpy as np
from standards import *

# CO2 (g/mi) = exemplar_co2_factor[ALPHA_class]/PT_eff_norm, PT_eff_norm = powertrain efficiency [0..1]
exemplar_co2_factor = {
    'LPW_LRL': 48.79,
    'LPW_HRL': 61.05,
    'MPW_LRL': 50.18,
    'MPW_HRL': 68.00,
    'HPW': 64.44,
    'Truck': 86.26,
}

current_VIN_number = -1


def get_powertrain_efficiency_norm_from_co2_gpmi(veh, achieved_tailpipe_co2_gpmi):
    if achieved_tailpipe_co2_gpmi > 0:
        return exemplar_co2_factor[veh.ALPHA_class] / achieved_tailpipe_co2_gpmi
    else:
        return 1


def get_co2_gpmi_from_powertrain_efficiency_norm(veh, powertrain_efficiency_norm):
    if powertrain_efficiency_norm >= 0.9999:
        return 0
    else:
        return exemplar_co2_factor[veh.ALPHA_class] / max(powertrain_efficiency_norm, 0.01)


def get_next_VIN():
    global current_VIN_number
    current_VIN_number = current_VIN_number + 1
    return current_VIN_number


class Vehicle:
    def __init__(self):
        self.VIN = 0
        self.manufacturer = ''
        self.nameplate = ''
        self.regulatory_class = ''
        self.footprint_ft2 = 0.0
        self.sales = 0  # count in age 0
        self.lifetime_vehicle_miles_travelled = 0

        self.emissions_target_net_co2_gpmi = 0.0
        self.emissions_achieved_tailpipe_co2_gpmi = 0.0

        self.emissions_target_net_co2_Mg = 0.0
        self.emissions_achieved_tailpipe_co2_Mg = 0.0

        self.powertrain_efficiency_norm = 0
        self.powertrain_target_efficiency_norm = 0

        self.tech_package_cost_initial_dollars = 0
        self.tech_package_cost_dollars = 0
        self.tech_package_cost_delta_dollars = 0

        self.tech_package_cost_production_initial_dollars = 0
        self.tech_package_cost_production_dollars = 0
        self.tech_package_cost_production_delta_dollars = 0

        # NEW PROPERTIES
        # power, weight and roadload determine map to ALPHA_class:
        self.roadload = []
        self.test_weight = []
        self.engine_power_kW = 0
        self.ALPHA_class = ''
        self.count = 0  # how many are left

    def __repr__(self):
        s = '\n<vehicle.Vehicle object at %#x>' % id(self)
        for k in ['VIN', 'nameplate', 'powertrain_efficiency_norm']:
            s = s + ', '
            s = s + k + ' = ' + str(self.__dict__[k])
        return s

    def __str__(self):
        s = '\n<vehicle.Vehicle object at %#x>\n' % id(self)
        for k in self.__dict__:
            s = s + k + ' = ' + str(self.__dict__[k]) + '\n'
        return s

    def calc_vehicle_emissions_Mg(self):
        """

        :return:
        """
        self.emissions_target_net_co2_Mg = self.emissions_target_net_co2_gpmi * \
                                           self.lifetime_vehicle_miles_travelled * self.sales / 1e6
        self.emissions_achieved_tailpipe_co2_Mg = self.emissions_achieved_tailpipe_co2_gpmi * \
                                                  self.lifetime_vehicle_miles_travelled * self.sales / 1e6

    def update_vehicle_emissions_targets(self, calendar_year):
        if calendar_year < 2025:
            # eventually this should come from the standards module (based on footprint, calendar year, etc)
            # fixed 5% y/y reduction for now...
            self.emissions_target_net_co2_gpmi = self.emissions_target_net_co2_gpmi * 0.95
        # update powertrain target efficiency
        self.update_powertrain_target_efficiency_norm(self.emissions_target_net_co2_gpmi)
        # update vehicle emissions
        self.calc_vehicle_emissions_Mg()

    def update_powertrain_efficiency_costs_emissions(self, new_powertrain_efficiency_norm=None, calendar_year=None, ):
        """

        :param new_powertrain_efficiency_norm:
        :return:
        """
        if new_powertrain_efficiency_norm is not None:
            self.powertrain_efficiency_norm = new_powertrain_efficiency_norm
            # update emissions g/mi:
            self.emissions_achieved_tailpipe_co2_gpmi = get_co2_gpmi_from_powertrain_efficiency_norm(self, self.powertrain_efficiency_norm)

        # update tech package costs
        self.tech_package_cost_dollars = self.powertrain_efficiency_norm * 10000

        # poor man's "learning" cost reduction!
        if calendar_year:
            self.tech_package_cost_dollars = self.tech_package_cost_dollars * 0.97**(calendar_year-2019)

        self.tech_package_cost_dollars = round(self.tech_package_cost_dollars)  # you got penny??

        self.tech_package_cost_delta_dollars = self.tech_package_cost_dollars - self.tech_package_cost_initial_dollars


        # update tech production costs
        self.tech_package_cost_production_dollars = self.tech_package_cost_dollars * self.sales
        self.tech_package_cost_production_delta_dollars = self.tech_package_cost_production_dollars - \
                                                          self.tech_package_cost_production_initial_dollars

        # update vehicle emissions
        self.calc_vehicle_emissions_Mg()

    def update_powertrain_target_efficiency_norm(self, emissions_target_net_co2_gpmi):
        self.powertrain_target_efficiency_norm = get_powertrain_efficiency_norm_from_co2_gpmi(self, emissions_target_net_co2_gpmi)

    def init_vehicle_from_dataframe(self, df):
        # populate values from dataframe
        self.manufacturer = df['Manufacturer']
        self.nameplate = df['Nameplate']
        self.ALPHA_class = df['ALPHA Class']
        self.regulatory_class = df['Regulatory Class']
        self.footprint_ft2 = df['Footprint (ft^2)']

        self.emissions_target_net_co2_gpmi = df['Emissions Target Net CO2 (g/mi)']
        self.emissions_achieved_tailpipe_co2_gpmi = df['Emissions Achieved Tailpipe CO2 (g/mi)']

        self.powertrain_efficiency_norm = get_powertrain_efficiency_norm_from_co2_gpmi(self, self.emissions_achieved_tailpipe_co2_gpmi)
        self.update_powertrain_target_efficiency_norm(self.emissions_target_net_co2_gpmi)

        self.sales = df['Sales']

        # populate derived values
        self.lifetime_vehicle_miles_travelled = lifetime_vmt_miles[self.regulatory_class]

        self.tech_package_cost_initial_dollars = round(self.powertrain_efficiency_norm * 10000)
        self.tech_package_cost_production_initial_dollars = self.tech_package_cost_initial_dollars * self.sales

        self.update_powertrain_efficiency_costs_emissions()

        self.VIN = get_next_VIN()
