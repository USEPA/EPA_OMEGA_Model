"""

The o2_effects module first calls the inventory module to calculate emission inventories from tailpipe sources (vehicles) and from upstream sources (both refineries and electricity generating units).
The module also calculates fuel consumption, both liquid and electric. The module then calls the "cost_effects_non_emissions" module, the "cost_effects_scc" module and the "cost_effects_criteria"
module (if requested) to calculate the "costs" associated with each.

Each of the cost elements, and each parameter within each, is calculated for every vehicle in the vehicles.csv input file and for each year of its life. The results are then written to the
vehicle_annual_data table and included in the vehicle_annual_data.csv output file.


----

**CODE**

"""
from pathlib import Path
from omega_model import *
from omega_model.effects.inventory import calc_inventory
from omega_model.effects.social_costs import calc_carbon_emission_costs, calc_criteria_emission_costs, calc_non_emission_costs, calc_cost_effects
from omega_model.effects.general_functions import save_dict_to_csv
from omega_model.effects.discounting import discount_values


def run_effects_calcs():
    from producer.vehicle_annual_data import VehicleAnnualData

    calendar_years = pd.Series(VehicleAnnualData.get_calendar_years()).unique()
    calendar_years = [year for year in calendar_years if year >= omega_globals.options.analysis_initial_year]

    physical_effects_dict = dict()
    for calendar_year in calendar_years:
        print(f'Calculating inventories for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating inventories for {int(calendar_year)}')
        physical_effects_dict.update(calc_inventory(calendar_year))

    cost_effects_dict = dict()
    print('Calculating costs')
    omega_log.logwrite('Calculating costs')
    cost_effects_dict.update(calc_cost_effects(physical_effects_dict))

    print('Discounting costs')
    omega_log.logwrite('Discounting costs')
    cost_effects_dict = discount_values(cost_effects_dict)

    save_dict_to_csv(physical_effects_dict, omega_globals.options.output_folder + '%s_physical_effects' %
                     omega_globals.options.session_unique_name, list(), 'vehicle_id', 'calendar_year', 'age')

    save_dict_to_csv(cost_effects_dict, omega_globals.options.output_folder + '%s_cost_effects' %
                     omega_globals.options.session_unique_name, list(), 'vehicle_id', 'calendar_year', 'age', 'discount_rate')

    # # cost_effects_dict = dict()
    # for calendar_year in calendar_years:
    #     print(f'Calculating non-emission-related costs for {int(calendar_year)}')
    #     omega_log.logwrite(f'Calculating non-emission-related costs for {int(calendar_year)}')
    #     cost_effects_dict = calc_non_emission_costs(calendar_year)

    # for calendar_year in calendar_years:
    #     print(f'Calculating costs of carbon emissions for {int(calendar_year)}')
    #     omega_log.logwrite(f'Calculating costs of carbon emissions for {int(calendar_year)}')
    #     cost_effects_dict = calc_carbon_emission_costs(calendar_year, cost_effects_dict)
    #
    # if omega_globals.options.calc_criteria_emission_costs:
    #     for calendar_year in calendar_years:
    #         print(f'Calculating costs of criteria emissions for {int(calendar_year)}')
    #         omega_log.logwrite(f'Calculating costs of criteria emissions for {int(calendar_year)}')
    #         cost_effects_dict = calc_criteria_emission_costs(calendar_year, cost_effects_dict)
