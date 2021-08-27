"""

The omega_effects module is called by the postproc_session module and is called only if the "Run Effects Calculations" input setting is set to TRUE.
The user is provided the option to calculate the effects because the calculations can add considerably to the runtime and, depending on the
data sought for the given run, a user may not need the effects-related output files.

The omega_effects module first calls the calc_physical_effects function in the physical_effects module to calculate emission inventories from
tailpipe sources (vehicles) and from upstream sources (both refineries and electricity generating units). The physical_effects module also
calculates both liquid fuel consumption and electricity consumption.

The omega_effects module also calls the calc_cost_effects function in the cost_effects module. Each of these physical and cost effects are
calculated on an absolute basis. In other words, an inventory of CO2 tons multiplied by "costs" of CO2 per ton provides the "cost" of CO2
emissions. However, the calculation of criteria and GHG emission impacts is done using the $/ton estimates included in the
cost_factors-criteria.csv and cost_factors-scc.csv input files. The $/ton estimates provided in those files are best understood to be the
marginal costs associated with the reduction of the individual pollutants as opposed to the absolute costs associated with a ton of each
pollutant. As such, the criteria and climate "costs" calculated by the model should not be seen as true costs associated with pollution,
but rather the first step in estimating the benefits associated with reductions of those pollutants. For that reason, the user must be careful
not to consider those as absolute costs, but once compared to the "costs" of another scenario (presumably via calculation of a difference
in "costs" between two scenarios) the result can be interpreted as a benefit.

The omega_effects module also call the calc_tech_volumes function in the tech_tracking module to calculate the volumes of specific technologies
in the fleet over the years within the analysis. This is done for all model-year vehicles of all ages over the calendar years included in the
analysis.

Each of the physical, cost and tech tracking elements, and each parameter within each, is calculated for every vehicle in the analysis and for
each year of its life. The results are then written to the physical_effects, cost_effects and tech_volumes output files.

Note:
    The omega_effects module runs only if the "Run Effects Calculations" input setting is set to TRUE. Otherwise, effects calculations will
    not be done.

----

**CODE**

"""
from omega_model import *
from omega_model.effects.physical_effects import calc_physical_effects
from omega_model.effects.cost_effects import calc_cost_effects
from omega_model.effects.general_functions import save_dict_to_csv
from omega_model.effects.discounting import discount_values
from omega_model.effects.tech_tracking import calc_tech_tracking


def run_effects_calcs():
    """

    A function to run specific effects calculations such as inventory effects and the costs associated with those inventory attributes.

    """
    from producer.vehicle_annual_data import VehicleAnnualData

    calendar_years = pd.Series(VehicleAnnualData.get_calendar_years()).unique()
    calendar_years = [int(year) for year in calendar_years if year >= omega_globals.options.analysis_initial_year]

    print('Calculating tech volumes and shares')
    omega_log.logwrite('Calculating tech volumes and shares')
    tech_tracking_dict = calc_tech_tracking(calendar_years)

    save_dict_to_csv(tech_tracking_dict, f'{omega_globals.options.output_folder}' + f'{omega_globals.options.session_unique_name}_tech_tracking',
                     list(), 'vehicle_id', 'calendar_year', 'age')

    if omega_globals.options.calc_effects.__contains__('Physical'):
        print('Calculating physical effects')
        omega_log.logwrite('Calculating physical effects')
        physical_effects_dict = calc_physical_effects(calendar_years)

        if omega_globals.options.calc_effects.__contains__('Costs'):
            cost_effects_dict = dict()
            print('Calculating cost effects')
            omega_log.logwrite('Calculating cost effects')
            cost_effects_dict.update(calc_cost_effects(physical_effects_dict))

            print('Discounting costs')
            omega_log.logwrite('Discounting costs')
            cost_effects_dict = discount_values(cost_effects_dict)

            save_dict_to_csv(cost_effects_dict, f'{omega_globals.options.output_folder}' + f'{omega_globals.options.session_unique_name}_cost_effects',
                             list(), 'vehicle_id', 'calendar_year', 'age', 'discount_rate')

        save_dict_to_csv(physical_effects_dict, f'{omega_globals.options.output_folder}' + f'{omega_globals.options.session_unique_name}_physical_effects',
                         list(), 'vehicle_id', 'calendar_year', 'age')
