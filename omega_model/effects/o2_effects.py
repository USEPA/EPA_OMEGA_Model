"""

The o2_effects module first calls the inventory module to calculate emission inventories from tailpipe sources (vehicles) and from upstream sources (both refineries and electricity generating units).
The module also calculates fuel consumption, both liquid and electric. The module then calls the "cost_effects_non_emissions" module, the "cost_effects_scc" module and the "cost_effects_criteria"
module (if requested) to calculate the "costs" associated with each.

Each of the cost elements, and each parameter within each, is calculated for every vehicle in the vehicles.csv input file and for each year of its life. The results are then written to the
vehicle_annual_data table and included in the vehicle_annual_data.csv output file.


----

**CODE**

"""

from omega_model import *
from inventory import calc_inventory
from social_costs import calc_carbon_emission_costs, calc_criteria_emission_costs, calc_non_emission_costs


def run_effects_calcs():
    from omega_model.producer.vehicle_annual_data import VehicleAnnualData

    calendar_years = VehicleAnnualData.get_calendar_years()
    calendar_years = pd.Series(calendar_years).unique()

    for calendar_year in calendar_years:
        print(f'Calculating inventories for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating inventories for {int(calendar_year)}')
        calc_inventory(calendar_year)

    for calendar_year in calendar_years:
        print(f'Calculating non-emission-related costs for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating non-emission-related costs for {int(calendar_year)}')
        calc_non_emission_costs(calendar_year)

    for calendar_year in calendar_years:
        print(f'Calculating costs of carbon emissions for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating costs of carbon emissions for {int(calendar_year)}')
        calc_carbon_emission_costs(calendar_year)

    if common.omega_globals.options.calc_criteria_emission_costs:
        for calendar_year in calendar_years:
            print(f'Calculating costs of criteria emissions for {int(calendar_year)}')
            omega_log.logwrite(f'Calculating costs of criteria emissions for {int(calendar_year)}')
            calc_criteria_emission_costs(calendar_year)
