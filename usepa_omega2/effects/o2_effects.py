"""

o2_effects.py
"""
from itertools import product

import o2
from usepa_omega2 import *
# from vehicles import VehicleFinal
# from vehicle_annual_data import VehicleAnnualData
# from effects.inventory import VehicleInventory
# from effects.emission_factors_vehicles import EmissionFactorsVehicles
from effects.inventory import calc_vehicle_co2_gallons, calc_vehicle_inventory, calc_refinery_inventory, calc_powersector_inventory


vehicle_criteria_factors = ['voc', 'co', 'nox', 'pm25', 'sox', 'benzene', 'butadiene', 'formaldehyde', 'acetaldehyde', 'acrolein']
vehicle_ghg_factors = ['ch4', 'n2o']
vehicle_factors = vehicle_criteria_factors + vehicle_ghg_factors

powersector_factors = ['voc', 'co', 'nox', 'pm25', 'sox', 'benzene', 'butadiene', 'formaldehyde', 'acetaldehyde', 'acrolein',
                    'ch4', 'n2o', 'co2']
refinery_factors = powersector_factors + ['naphthalene']


def run_effects_calcs():
    calc_vehicle_co2_gallons()
    calc_vehicle_inventory(*vehicle_factors)
    calc_refinery_inventory(*refinery_factors)
    calc_powersector_inventory(*powersector_factors)
