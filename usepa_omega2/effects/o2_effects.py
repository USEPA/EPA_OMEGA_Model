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


vehicle_criteria_factors = ['voc', 'co', 'nox', 'pm25', 'sox', 'benzene', 'butadiene13', 'formaldehyde', 'acetaldehyde', 'acrolein']
vehicle_ghg_factors = ['ch4', 'n2o']
vehicle_factors = vehicle_criteria_factors + vehicle_ghg_factors

powersector_factors = ['voc', 'co', 'nox', 'pm25', 'sox', 'benzene', 'butadiene13', 'formaldehyde', 'acetaldehyde', 'acrolein',
                       'ch4', 'n2o', 'co2']
refinery_factors = powersector_factors + ['naphthalene']


# def df_from_db_table(table_name):
#     return pd.read_sql_table(table_name, con=o2.engine)


def run_effects_calcs(vf_df, vad_df, vef_df, ref_df, pef_df):
    inventories = calc_vehicle_co2_gallons(vf_df, vad_df)
    inventories = calc_vehicle_inventory(inventories, vf_df, vef_df, *vehicle_factors)
    inventories = calc_refinery_inventory(inventories, ref_df, *refinery_factors)
    inventories = calc_powersector_inventory(inventories, pef_df, *powersector_factors)
    return inventories
