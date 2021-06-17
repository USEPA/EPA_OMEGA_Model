"""


----

**CODE**

"""

from usepa_omega2 import *
from effects.inventory import calc_inventory
from effects.social_costs import calc_carbon_emission_costs, calc_criteria_emission_costs, calc_non_emission_costs


def run_effects_calcs():
    from vehicle_annual_data import VehicleAnnualData

    calendar_years = VehicleAnnualData.get_calendar_years()
    calendar_years = pd.Series(calendar_years).unique()

    for calendar_year in calendar_years:
        print(f'Calculating inventories for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating inventories for {int(calendar_year)}')
        calc_inventory(calendar_year)

    for calendar_year in calendar_years:
        print(f'Calculating non-emission-related social costs for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating non-emission-related social costs for {int(calendar_year)}')
        calc_non_emission_costs(calendar_year)

    for calendar_year in calendar_years:
        print(f'Calculating social costs of carbon emissions for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating social costs of carbon emissions for {int(calendar_year)}')
        calc_carbon_emission_costs(calendar_year)

    if o2.options.calc_criteria_emission_costs:
        for calendar_year in calendar_years:
            print(f'Calculating social costs of criteria emissions for {int(calendar_year)}')
            omega_log.logwrite(f'Calculating social costs of criteria emissions for {int(calendar_year)}')
            calc_criteria_emission_costs(calendar_year)
