"""

Top-level includes/definitions for the OMEGA model

Defines class OMEGARuntimeOptions which control an individual simulation session


----

**CODE**

"""

# OMEGA code version number
code_version = "2.0.1"
print('loading omega version %s' % code_version)

import os, sys

if 'darwin' in sys.platform:
    os.environ['QT_MAC_WANTS_LAYER'] = '1'  # for pyqtgraph on MacOS

# print('omega_model __init__.py path = %s' % os.path.abspath(__file__))
# print('SYS Path = %s' % sys.path)

# print(sys._MEIPASS)
# path = os.path.dirname(os.path.abspath(__file__))
# print(sys.path)
# sys.path.insert(0, path)
# print(sys.path)

import traceback

try:
    import time
    import pandas as pd
    pd.set_option('chained_assignment', 'raise')
    from pandas.api.types import is_numeric_dtype
    import numpy as np
    import copy

    from common.omega_globals import *
    from common.omega_types import *
    from common.omega_db import *
    from common import file_io, omega_log
    from common.input_validation import *
    from common.omega_functions import *
    from common.omega_eval import *
    from context.context_base_classes import *
    from context.onroad_fuels import *
    from policy.policy_base_classes import *
    from consumer.consumer_base_classes import *
    from producer.producer_base_classes import *

    # --- OMEGA2 global constants ---

    # enumerated values
    fueling_classes = OMEGAEnum(['BEV', 'ICE'])
    ownership_classes = OMEGAEnum(['shared', 'private'])
    legacy_reg_classes = OMEGAEnum(['car', 'truck'])
    fuel_units = OMEGAEnum(['gallon', 'kWh'])


    class OMEGASessionSettings(OMEGABase):
        """
        Define the settings required for a simulation session

        """
        def __init__(self):
            """
            Create an OMEGARuntimeOptions object with default settings used for testing and development.

            The primary way to create an OMEGARuntimeOptions object is via the batch process.

            See Also:
                omega_batch.py

            """

            import time

            path = os.path.dirname(os.path.abspath(__file__)) + os.sep
            self.inputfile_metadata = []
            self.session_name = 'OMEGA Quick Test'
            self.session_unique_name = 'OMEGA Quick Test'
            self.session_is_reference = True
            self.auto_close_figures = True
            self.save_preliminary_outputs = True
            self.output_folder_base = 'out' + os.sep
            self.output_folder = self.output_folder_base
            self.database_dump_folder = self.output_folder + '__dump' + os.sep
            self.omega_model_path = path
            self.use_prerun_context_outputs = False
            self.credit_market_efficiency = 0.5
            self.consolidate_manufacturers = None
            self.include_manufacturers_list = 'all'
            self.exclude_manufacturers_list = 'none'
            self.manufacturers_file = path + 'test_inputs/manufacturers.csv'
            self.vehicles_file = path + 'test_inputs/vehicles.csv'
            self.vehicles_file_base_year = None
            self.vehicles_df = pd.DataFrame()
            self.onroad_vehicle_calculations_file = path + 'test_inputs/onroad_vehicle_calculations.csv'
            self.onroad_fuels_file = path + 'test_inputs/onroad_fuels.csv'
            self.context_id = 'AEO2021'
            self.context_case_id = 'Reference case'
            self.context_new_vehicle_generalized_costs_file = None
            self.sales_share_calibration_file = None
            self.generate_context_calibration_files = True
            self.context_fuel_prices_file = path + 'test_inputs/context_fuel_prices.csv'
            self.fuel_upstream_methods_file = path + 'test_inputs/policy_fuel_upstream_methods.csv'
            self.drive_cycles_file = path + 'test_inputs/drive_cycles.csv'
            self.drive_cycle_weights_file = path + 'test_inputs/drive_cycle_weights_5545.csv'
            self.drive_cycle_ballast_file = path + 'test_inputs/drive_cycle_ballast.csv'
            self.context_stock_vmt_file = path + 'test_inputs/context_stock_vmt.csv'

            self.ice_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_ice.csv'
            self.bev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_bev.csv'
            self.phev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_phev.csv'

            self.powertrain_cost_input_file = path + 'test_inputs/powertrain_cost.csv'
            self.glider_cost_input_file = path + 'test_inputs/glider_cost.csv'
            self.body_styles_file = path + 'test_inputs/body_styles.csv'
            self.mass_scaling_file = path + 'test_inputs/mass_scaling.csv'

            self.analysis_initial_year = None
            self.analysis_final_year = 2021
            self.logfile_prefix = 'o2log_'
            self.logfilename = ''
            self.consumer_calc_generalized_cost = None
            self.policy_targets_file = path + 'test_inputs/ghg_standards-footprint_NTR-FRM-CFR-form.csv'
            self.policy_reg_classes_file = path + 'test_inputs/regulatory_classes.csv'
            self.production_multipliers_file = path + 'test_inputs/production_multipliers.csv'
            self.policy_fuels_file = path + 'test_inputs/policy_fuels.csv'
            self.ghg_credit_params_file = path + 'test_inputs/ghg_credit_params.csv'
            self.ghg_credits_file = path + 'test_inputs/ghg_credits.csv'

            self.context_new_vehicle_market_file = path + 'test_inputs/context_new_vehicle_market-body_style.csv'
            self.market_classes_file = path + 'test_inputs/market_classes-body_style.csv'
            self.producer_generalized_cost_file = path + 'test_inputs/producer_generalized_cost-body_style.csv'
            self.production_constraints_file = path + 'test_inputs/production_constraints-body_style.csv'
            self.vehicle_reregistration_file = path + 'test_inputs/reregistration_fixed_by_age-body_style.csv'
            self.sales_share_file = path + 'test_inputs/sales_share_params_ice_bev_body_style.csv'
            self.required_sales_share_file = path + 'test_inputs/required_sales_share-body_style.csv'
            self.onroad_vmt_file = path + 'test_inputs/annual_vmt_fixed_by_age-body_style.csv'
            self.vehicle_price_modifications_file = path + 'test_inputs/vehicle_price_modifications-body_style.csv'

            self.offcycle_credits_file = path + 'test_inputs/offcycle_credits.csv'

            self.consumer_pricing_num_options = 4
            self.consumer_pricing_multiplier_min = 0.9
            self.consumer_pricing_multiplier_max = 1.1

            self.new_vehicle_price_elasticity_of_demand = -0.4
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')

            self.calc_effects = 'Physical and Costs' # options are 'No', 'Physical' and 'Physical and Costs' as strings
            self.analysis_dollar_basis = 2020 # Note that the implicit_price_deflator.csv input file must contain data for this entry.
            self.discount_values_to_year = 2021
            self.cost_accrual = 'end-of-year'  # end-of-year means costs accrue at year's end; beginning-of-year means cost accrue at year's beginning
            self.allow_ice_of_bev = False
            self.vmt_rebound_rate = 0

            # effects modeling files
            self.general_inputs_for_effects_file = path + 'test_inputs/general_inputs_for_effects.csv'
            self.ip_deflators_file = path + 'test_inputs/implicit_price_deflators.csv'
            self.cpi_deflators_file = path + 'test_inputs/cpi_price_deflators.csv'
            self.scc_cost_factors_file = path + 'test_inputs/cost_factors_scc.csv'
            self.criteria_cost_factors_file = path + 'test_inputs/cost_factors_criteria.csv'
            self.energysecurity_cost_factors_file = path + 'test_inputs/cost_factors_energysecurity.csv'
            self.congestion_noise_cost_factors_file = path + 'test_inputs/cost_factors_congestion_noise.csv'
            self.emission_factors_vehicles_file = path + 'test_inputs/emission_rates_vehicles-no_gpf.csv'
            self.emission_factors_powersector_file = path + 'test_inputs/emission_rates_egu.csv'
            self.emission_factors_refinery_file = path + 'test_inputs/emission_factors_refinery.csv'
            self.maintenance_cost_inputs_file = path + 'test_inputs/maintenance_cost.csv'
            self.repair_cost_inputs_file = path + 'test_inputs/repair_cost.csv'
            self.refueling_cost_inputs_file = path + 'test_inputs/refueling_cost.csv'
            self.safety_values_file = path + 'test_inputs/safety_values.csv'
            self.fatality_rates_file = path + 'test_inputs/fatality_rates.csv'
            self.legacy_fleet_file = path + 'test_inputs/legacy_fleet.csv'

            self.start_time = 0
            self.end_time = 0

            # developer settings
            self.producer_shares_mode = 'auto'
            self.producer_num_market_share_options = 3
            self.producer_num_tech_options_per_ice_vehicle = 3
            self.producer_num_tech_options_per_bev_vehicle = 1
            self.cost_curve_frontier_affinity_factor = 0.75
            self.slice_tech_combo_cloud_tables = False
            self.verbose = False
            self.iterate_producer_consumer = True

            self.producer_consumer_max_iterations = 2  # recommend 2+
            self.producer_consumer_convergence_tolerance = 5e-4
            self.producer_compliance_search_min_share_range = 1e-5
            self.producer_compliance_search_convergence_factor = 0.9
            self.producer_compliance_search_tolerance = 1e-6
            self.producer_cross_subsidy_price_tolerance = 1e-4
            self.run_profiler = False
            self.multiprocessing = True and not self.run_profiler and not getattr(sys, 'frozen', False)
            self.flat_context = False
            self.flat_context_year = 2021

            self.battery_GWh_limit_years = [2020, 2021, 2022, 2023, 2024, 2025, 2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035, 2036, 2037, 2038, 2039, 2040]
            self.battery_GWh_limit = {
                "Consolidated_OEM": [30, 48, 79, 134, 159, 190, 250, 356, 502, 651, 792, 936, 1080, 1224, 1364, 1500, 1500, 1500, 1500, 1500, 1500],
                "Aston Martin Lagonda": [0, 0, 0, 0.000981, 0.027921, 0.034275, 0.059635, 0.081652, 0.099305, 0.109338,
                                         0.087887, 0.267344, 0.270624, 0.238528, 0.098719, 0.052378, 0.055233, 0.058735,
                                         0.240619, 0.238638, 0.237891],
                "BMW": [0.075725, 0.104503, 0.106905, 0.505791, 2.41537, 2.985789, 8.145877, 12.408773, 12.11695, 16.049279,
                        18.967262, 25.41508, 29.017523, 21.695981, 21.380483, 18.088491, 18.320414, 18.619724, 23.012588,
                        22.981904, 23.017739],
                "FCA": [1.72864, 1.173006, 1.125039, 26.159503, 27.310539, 45.06382, 48.314748, 76.209504, 93.555726,
                        123.569793, 138.479765, 116.862576, 138.728802, 123.79492, 142.417676, 176.715071, 180.287472,
                        182.909315, 148.308893, 151.778481, 153.457747],
                "Ferrari": [0, 0, 0, 0.001394, 0.03971, 0.048163, 0.084632, 0.115638, 0.14021, 0.154503, 0.123977, 0.377815,
                            0.381391, 0.336507, 0.139132, 0.073802, 0.077779, 0.082662, 0.338415, 0.335903, 0.334169],
                "Ford": [0.250687, 0.296506, 0.842467, 25.284519, 26.524088, 50.077871, 38.988701, 59.461071, 83.9048,
                         105.687021, 106.677201, 98.426686, 110.299527, 114.416902, 104.462488, 146.156092, 150.111376,
                         152.834139, 137.597715, 141.153324, 142.287637],
                "General Motors": [1.471502, 1.657527, 1.782402, 30.489786, 32.481221, 51.001475, 53.604278, 83.658284,
                                   102.897859, 135.266008, 151.240864, 131.350122, 155.190105, 138.9417, 155.974175,
                                   192.528783, 196.560056, 199.524009, 165.629069, 169.263516, 170.756035],
                "Honda": [0.314854, 0.405809, 0.426009, 2.618862, 8.890986, 12.136718, 32.366702, 50.424919, 50.355775,
                          67.895549, 82.142249, 96.309205, 112.312667, 82.787504, 91.770766, 83.626747, 84.736733,
                          86.040452, 90.074385, 90.516293, 90.820539],
                "Hyundai": [0.360186, 0.4101, 0.437148, 0.556133, 3.130825, 3.798493, 12.464311, 19.665843, 18.954682,
                            25.991105, 32.725676, 38.227886, 45.053209, 32.11206, 37.16966, 32.682988, 33.097809, 33.608232,
                            34.833738, 34.887603, 35.021628],
                "JLR": [0.305809, 0.331145, 0.348215, 0.373422, 0.590092, 0.685669, 3.197342, 5.24523, 4.536448, 6.777236,
                        9.628742, 7.152387, 9.522079, 5.732358, 10.81412, 10.343311, 10.393792, 10.47116, 6.675813,
                        6.726687, 6.868074],
                "Kia": [0.232012, 0.204896, 0.228074, 0.343077, 2.97847, 3.554362, 10.643935, 16.387569, 16.232711,
                        21.50498, 25.373884, 34.48604, 39.05925, 29.186598, 28.559871, 24.089733, 24.415074, 24.831126,
                        30.859732, 30.913315, 30.810102],
                "Maserati": [0.003023, 0.003368, 0.003542, 0.008156, 0.113214, 0.136036, 0.471279, 0.747579, 0.721276,
                             0.983933, 1.207586, 1.48579, 1.725658, 1.245157, 1.362473, 1.18001, 1.193721, 1.211339,
                             1.336155, 1.339525, 1.341162],
                "Mazda": [0.132924, 0.155365, 0.164404, 0.206831, 1.012369, 1.272219, 5.6125, 9.184024, 8.439418, 12.148844,
                          16.428882, 15.412117, 19.355359, 12.678897, 18.599597, 17.072687, 17.248103, 17.461503, 14.318933,
                          14.346028, 14.631923],
                "McLaren": [0, 0, 0, 0.000598, 0.017036, 0.020399, 0.035826, 0.048646, 0.058378, 0.064517, 0.050819,
                            0.158051, 0.157955, 0.139854, 0.057608, 0.030524, 0.032093, 0.034035, 0.138966, 0.138323,
                            0.136563],
                "Mercedes Benz": [0.065884, 0.071966, 0.077724, 0.148019, 1.712444, 2.326866, 7.526, 11.818534, 11.436997,
                                  15.517516, 19.161565, 22.794931, 26.812074, 19.133599, 21.5177, 18.744947, 18.957824,
                                  19.234747, 20.661939, 20.63426, 20.849389],
                "Mitsubishi": [0.012472, 0.015085, 0.016044, 0.032357, 0.330823, 0.39688, 2.388224, 3.977855, 3.609034,
                               5.295054, 7.401716, 6.468591, 8.307399, 5.306098, 8.403252, 7.818769, 7.875309, 7.97106,
                               6.054786, 6.063898, 6.182413],
                "Nissan": [0.945504, 0.889955, 1.047469, 3.925847, 8.376765, 12.967102, 25.092122, 38.356242, 40.817688,
                           53.656209, 62.412841, 73.450877, 84.306764, 66.046601, 68.068745, 65.854223, 66.851608,
                           67.916413, 72.371335, 72.900248, 72.997864],
                "Subaru": [0.41146, 0.487068, 0.516421, 0.621754, 2.369043, 2.814374, 16.191795, 27.129104, 24.18069,
                           35.965339, 50.687021, 41.964113, 54.701013, 34.055135, 57.626497, 54.102914, 54.557732,
                           55.161958, 39.336856, 39.516952, 40.461626],
                "Tesla": [7.209903, 6.880072, 7.628624, 7.774628, 7.918045, 8.145904, 8.258708, 8.18241, 8.22696, 8.307013,
                          8.191777, 8.303678, 8.243026, 8.305693, 8.278119, 8.082496, 7.931681, 7.871587, 7.839342,
                          7.761507, 7.590336],
                "Toyota": [0.368212, 0.280085, 0.282834, 0.639751, 7.53827, 28.778377, 46.203668, 72.213846, 79.436553,
                           105.830205, 123.008984, 127.127844, 148.668806, 118.937472, 131.819226, 139.066197, 141.275731,
                           143.323641, 134.333146, 136.076356, 136.838658],
                "Volvo": [0.007642, 0.00864, 0.007899, 0.170353, 0.431574, 0.4891, 2.677849, 4.489544, 3.8628, 5.830106,
                          8.294602, 6.646141, 8.725784, 5.423885, 9.386899, 8.854406, 8.917327, 8.998755, 6.264072,
                          6.294806, 6.39717],
                "VW": [1.314671, 1.485027, 1.563803, 1.724241, 5.129493, 6.275568, 17.9536, 27.472432, 26.535913, 35.655308,
                       43.935652, 51.444905, 60.381601, 43.396315, 49.194607, 43.172467, 43.61407, 44.211487, 46.776525,
                       46.722379, 47.102584]
            }

            # list of modules to allow verbose log files, or empty to disable:
            self.verbose_log_modules = ['database_', 'producer_compliance_search_', 'cross_subsidy_search_',
                                        'cv_cost_curves_', 'v_cost_curves_', 'v_cost_clouds_', 'v_cloud_plots_']

            # list of modules to allow verbose console output, or empty to disable
            self.verbose_console_modules = ['producer_compliance_search_',
                                            'p-c_shares_and_costs_', 'p-c_max_iterations_',
                                            'cross_subsidy_search_', 'cross_subsidy_multipliers_',
                                            'cross_subsidy_convergence_']

            self.verbose_postproc = ['iteration_']

            self.log_vehicle_cloud_years = []  # = 'all' or list of years to log, empty list to disable logging
            self.log_producer_compliance_search_years = []  # = 'all' or list of years to log, empty list to disable logging
            self.log_consumer_iteration_years = [2050]  # = 'all' or list of years to log, empty list to disable logging
            self.log_producer_decision_and_response_years = []  # = 'all' or list of years to log, empty list to disable logging

            # list of vehicles to plot in log_producer_compliance_search_years:
            self.plot_and_log_vehicles = []  # ['ICE Large Van truck minivan 4WD']

            # dynamic modules / classes
            self.RegulatoryClasses = None
            self.VehicleTargets = None
            self.OffCycleCredits = None
            self.Reregistration = None
            self.OnroadVMT = None
            self.SalesShare = None
            self.ProducerGeneralizedCost = None
            self.MarketClass = None
            self.CostCoud = None

except:
    print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
    os._exit(-1)
