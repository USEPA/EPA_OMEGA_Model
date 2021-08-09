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
from omega_model.effects.physical_effects import calc_physical_effects
from omega_model.effects.cost_effects import calc_cost_effects
from omega_model.effects.general_functions import save_dict_to_csv
from omega_model.effects.discounting import discount_values
from omega_model.effects.tech_tracking import calc_tech_volumes


def run_effects_calcs():
    """

    A function to run specific effects calculations such as inventory effects and the costs associated with those inventory attributes.

    """
    from producer.vehicle_annual_data import VehicleAnnualData

    calendar_years = pd.Series(VehicleAnnualData.get_calendar_years()).unique()
    calendar_years = [year for year in calendar_years if year >= omega_globals.options.analysis_initial_year]

    physical_effects_dict = dict()
    for calendar_year in calendar_years:
        print(f'Calculating physical effects for {int(calendar_year)}')
        omega_log.logwrite(f'Calculating physical effects for {int(calendar_year)}')
        physical_effects_dict.update(calc_physical_effects(calendar_year))

    print('Calculating tech volumes')
    omega_log.logwrite('Calculating tech volumes')
    tech_volumes_dict = calc_tech_volumes(physical_effects_dict)

    cost_effects_dict = dict()
    print('Calculating cost effects')
    omega_log.logwrite('Calculating cost effects')
    cost_effects_dict.update(calc_cost_effects(physical_effects_dict))

    print('Discounting costs')
    omega_log.logwrite('Discounting costs')
    cost_effects_dict = discount_values(cost_effects_dict)

    save_dict_to_csv(physical_effects_dict, omega_globals.options.output_folder + '%s_physical_effects' %
                     omega_globals.options.session_unique_name, list(), 'vehicle_id', 'calendar_year', 'age')

    save_dict_to_csv(tech_volumes_dict, omega_globals.options.output_folder + '%s_tech_volumes' %
                     omega_globals.options.session_unique_name, list(), 'vehicle_id', 'calendar_year', 'age')

    save_dict_to_csv(cost_effects_dict, omega_globals.options.output_folder + '%s_cost_effects' %
                     omega_globals.options.session_unique_name, list(), 'vehicle_id', 'calendar_year', 'age', 'discount_rate')
