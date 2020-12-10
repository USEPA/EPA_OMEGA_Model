"""

o2_effects.py
=============
"""


import o2
from usepa_omega2 import *
from effects.inventory import calc_inventory
from effects.emission_costs import calc_carbon_emission_costs, calc_criteria_emission_costs


def run_effects_calcs():
    from vehicle_annual_data import VehicleAnnualData

    calendar_years = sql_unpack_result(o2.session.query(VehicleAnnualData.calendar_year).all())
    calendar_years = pd.Series(calendar_years).unique()

    for calendar_year in calendar_years:
        print(f'Calculating inventories for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating inventories for {int(calendar_year)}')
        calc_inventory(calendar_year)

    for calendar_year in calendar_years:
        print(f'Calculating social costs of carbon emissions for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating social costs of carbon emissions for {int(calendar_year)}')
        calc_carbon_emission_costs(calendar_year)

    for calendar_year in calendar_years:
        print(f'Calculating social costs of criteria emissions for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating social costs of criteria emissions for {int(calendar_year)}')
        calc_criteria_emission_costs(calendar_year)
