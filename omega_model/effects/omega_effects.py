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
from omega_model.effects.physical_effects import calc_physical_effects, calc_annual_physical_effects
from omega_model.effects.cost_effects import calc_cost_effects
from omega_model.effects.general_functions import save_dict_to_csv
from omega_model.effects.discounting import discount_values
from omega_model.effects.present_and_annualized_values import calc_present_and_annualized_values
from omega_model.effects.tech_tracking import TechTracking


def run_effects_calcs():
    """

    A function to run specific effects calculations such as inventory effects and the costs associated with those inventory attributes.

    """
    from producer.vehicle_annual_data import VehicleAnnualData

    physical_effects_df = cost_effects_df = present_and_annualized_cost_df = pd.DataFrame()

    calendar_years = pd.Series(VehicleAnnualData.get_calendar_years()).unique()
    # calendar_years = np.unique(np.array(VehicleAnnualData.get_calendar_years()))
    calendar_years = [int(year) for year in calendar_years if year >= omega_globals.options.analysis_initial_year]

    omega_log.logwrite('\nCalculating tech volumes and shares', echo_console=True)
    tech_tracking = TechTracking()
    tech_tracking.create_dict(calendar_years)
    tech_tracking_dict = tech_tracking._data
    # tech_tracking_dict = calc_tech_tracking(calendar_years)

    tech_tracking_filename = f'{omega_globals.options.output_folder}' + \
                             f'{omega_globals.options.session_unique_name}_tech_tracking.csv'

    if omega_globals.options.multiprocessing:
        print('Starting multiprocess save_dict_to_csv...')
        tech_tracking_result = omega_globals.pool.apply_async(func=save_dict_to_csv,
                                                              args=[tech_tracking_dict, tech_tracking_filename, False],
                                                              callback=None,
                                                              error_callback=None)
    else:
        tech_tracking_df = save_dict_to_csv(tech_tracking_dict, tech_tracking_filename, index=False)

    if 'Physical' in omega_globals.options.calc_effects:
        omega_log.logwrite('\nCalculating physical effects', echo_console=True)
        physical_effects_dict = calc_physical_effects(calendar_years)

        physical_effects_filename = f'{omega_globals.options.output_folder}' + \
                                    f'{omega_globals.options.session_unique_name}_physical_effects.csv'

        if omega_globals.options.multiprocessing:
            print('Starting multiprocess save_dict_to_csv...')
            physical_effects_result = omega_globals.pool.apply_async(func=save_dict_to_csv,
                                                                     args=[physical_effects_dict, physical_effects_filename,
                                                                           False],
                                                                     callback=None,
                                                                     error_callback=None)
        else:
            physical_effects_df = save_dict_to_csv(physical_effects_dict, physical_effects_filename, index=False)

        if not omega_globals.options.multiprocessing:
            print('Saving Annual Physical Effects...')
            annual_physical_effects_filename = f'{omega_globals.options.output_folder}' + \
                                               f'{omega_globals.options.session_unique_name}_annual_physical_effects.csv'

            annual_physical_effects_df = calc_annual_physical_effects(physical_effects_df)
            annual_physical_effects_df.to_csv(annual_physical_effects_filename, index=False)

        if 'Costs' in omega_globals.options.calc_effects:
            cost_effects_dict = dict()

            omega_log.logwrite('\nCalculating cost effects', echo_console=True)
            cost_effects_dict.update(calc_cost_effects(physical_effects_dict))

            omega_log.logwrite('\nDiscounting costs', echo_console=True)
            cost_effects_dict = discount_values(cost_effects_dict)

            cost_effects_filename = f'{omega_globals.options.output_folder}' + \
                                    f'{omega_globals.options.session_unique_name}_cost_effects.csv'

            if omega_globals.options.multiprocessing:
                print('Starting multiprocess save_dict_to_csv...')
                cost_effects_result = omega_globals.pool.apply_async(func=save_dict_to_csv,
                                                                     args=[cost_effects_dict, cost_effects_filename,
                                                                           False],
                                                                     callback=None,
                                                                     error_callback=None)
            else:
                cost_effects_df = save_dict_to_csv(cost_effects_dict, cost_effects_filename, index=False)

            omega_log.logwrite('\nCalculating annual, present and annualized values', echo_console=True)
            present_and_annualized_dict = calc_present_and_annualized_values(cost_effects_dict, calendar_years)

            present_and_annualized_filename = f'{omega_globals.options.output_folder}' + \
                                              f'{omega_globals.options.session_unique_name}_annual_present_and_annualized_cost_effects.csv'

            present_and_annualized_cost_df = \
                save_dict_to_csv(present_and_annualized_dict, present_and_annualized_filename, index=False)

    if omega_globals.options.multiprocessing:
        if omega_globals.options.calc_effects == 'Physical and Costs':
            while not all([tech_tracking_result.ready(), physical_effects_result.ready(), cost_effects_result.ready()]):
                pass

            tech_tracking_df = tech_tracking_result.get()
            physical_effects_df = physical_effects_result.get()
            cost_effects_df = cost_effects_result.get()
        elif omega_globals.options.calc_effects == 'Physical':
            while not all([tech_tracking_result.ready(), physical_effects_result.ready()]):
                pass

            tech_tracking_df = tech_tracking_result.get()
            physical_effects_df = physical_effects_result.get()
        else:
            while not all([tech_tracking_result.ready()]):
                pass

            tech_tracking_df = tech_tracking_result.get()

        if 'Physical' in omega_globals.options.calc_effects:
            print('Saving Annual Physical Effects...')
            annual_physical_effects_filename = f'{omega_globals.options.output_folder}' + \
                                               f'{omega_globals.options.session_unique_name}_annual_physical_effects.csv'

            annual_physical_effects_df = calc_annual_physical_effects(physical_effects_df)
            annual_physical_effects_df.to_csv(annual_physical_effects_filename, index=False)

    print('OMEGA Effects Complete')

    return tech_tracking_df, physical_effects_df, cost_effects_df, present_and_annualized_cost_df
