"""
__init.py__
===========


"""

# OMEGA2 code version number
code_version = "0.4.0"
print('loading usepa_omega2 version %s' % code_version)

import os, sys
# print('usepa_omega2 __init__.py path = %s' % os.path.abspath(__file__))
# print('SYS Path = %s' % sys.path)

# print(sys._MEIPASS)
# path = os.path.dirname(os.path.abspath(__file__))
# print(sys.path)
# sys.path.insert(0, path)
# print(sys.path)

import traceback

try:
    import pandas as pd
    pd.set_option('chained_assignment', 'raise')

    from o2 import OMEGABase
    from omega_db import *
    from omega_types import *
    import omega_log
    import file_eye_oh as fileio
    from input_validation import *
    from omega_functions import *

    import scipy.interpolate

    # --- OMEGA2 global constants ---

    # enumerated values
    fueling_classes = OMEGAEnum(['BEV', 'ICE'])
    hauling_classes = OMEGAEnum(['hauling', 'non_hauling'])
    ownership_classes = OMEGAEnum(['shared', 'private'])
    reg_classes = OMEGAEnum(['car', 'truck'])
    fuel_units = OMEGAEnum(['gallon', 'kWh'])

    class OMEGARuntimeOptions(OMEGABase):
        def __init__(self):
            import time

            path = os.path.dirname(os.path.abspath(__file__)) + os.sep
            self.session_name = 'OMEGA2 Demo'
            self.session_unique_name = 'OMEGA2 Demo'
            self.session_is_reference = True
            self.verbose = False
            self.auto_close_figures = True
            self.output_folder = 'out' + os.sep
            self.database_dump_folder = self.output_folder + '__dump' + os.sep
            self.manufacturers_file = path + 'test_inputs/manufacturers.csv'
            self.market_classes_file = path + 'test_inputs/market_classes.csv'
            self.vehicles_file = path + 'test_inputs/vehicles.csv'
            self.demanded_shares_file = path + 'test_inputs/demanded_shares-gcam.csv'
            self.fuels_file = path + 'test_inputs/fuels.csv'
            self.context_folder = ''
            self.context_id = 'AEO2020'
            self.context_case_id = 'Reference case'
            self.context_new_vehicle_prices_file = path + 'test_inputs/context_new_vehicle_prices.csv'
            self.generate_context_new_vehicle_prices_file = False
            self.context_fuel_prices_file = path + 'test_inputs/context_fuel_prices.csv'
            self.fuel_upstream_file = path + 'test_inputs/fuel_upstream.csv'
            self.context_new_vehicle_market_file = path + 'test_inputs/context_new_vehicle_market.csv'
            self.cost_file = path + 'test_inputs/cost_curves.csv'
            self.cost_curve_frontier_affinity_factor = 0.75
            self.analysis_initial_year = None
            self.analysis_final_year = None
            self.logfile_prefix = 'o2log_'
            self.logfilename = ''
            self.producer_calculate_generalized_cost = None
            self.consumer_calculate_generalized_cost = None
            self.ghg_standards_file = path + 'test_inputs/ghg_standards-footprint.csv'
            self.ghg_standards_fuels_file = path + 'test_inputs/ghg_standards-fuels.csv'
            self.ghg_credits_file = path + 'test_inputs/ghg_credits.csv'
            self.required_zev_share_file = path + 'test_inputs/required_zev_share.csv'
            self.reregistration_fixed_by_age_file = path + 'test_inputs/reregistration_fixed_by_age.csv'
            self.annual_vmt_fixed_by_age_file = path + 'test_inputs/annual_vmt_fixed_by_age.csv'
            self.slice_tech_combo_cloud_tables = False

            self.allow_backsliding = False

            self.producer_max_iterations = 15
            self.producer_num_market_share_options = 5
            self.producer_num_tech_options_per_ice_vehicle = 5
            self.producer_num_tech_options_per_bev_vehicle = 1
            self.producer_iteration_tolerance = 1e-6

            self.iterate_producer_consumer = True
            self.producer_consumer_max_iterations = 20
            self.producer_consumer_iteration_tolerance = 1e-3

            self.consumer_pricing_num_options = 4
            self.consumer_pricing_multiplier_min = 0.95
            self.consumer_pricing_multiplier_max = 1.05

            self.new_vehicle_sales_response_elasticity = -0.5
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')

            self.calc_effects = False
            self.calc_criteria_emission_costs = False
            # effects modeling files
            self.ip_deflators_file = path + 'test_inputs/implicit_price_deflators.csv'
            self.cpi_deflators_file = path + 'test_inputs/cpi_price_deflators.csv'
            self.scc_cost_factors_file = path + 'test_inputs/cost_factors-scc.csv'
            self.criteria_cost_factors_file = path + 'test_inputs/cost_factors-criteria.csv'
            self.energysecurity_cost_factors_file = path + 'test_inputs/cost_factors-energysecurity.csv'
            self.congestion_noise_cost_factors_file = path + 'test_inputs/cost_factors-congestion-noise.csv'
            self.emission_factors_vehicles_file = path + 'test_inputs/emission_factors-vehicles.csv'
            self.emission_factors_powersector_file = path + 'test_inputs/emission_factors-powersector.csv'
            self.emission_factors_refinery_file = path + 'test_inputs/emission_factors-refinery.csv'

            self.start_time = 0
            self.end_time = 0

            # debugging options
            self.verbose_console = []  # ['producer', 'consumer']  # list of modules to allow verbose console output, or empty to disable
            self.run_profiler = False
            self.flat_context = False
            self.flat_context_year = 2021
            self.num_analysis_years = None  # number of years to run, if not all (None = run all)
            self.log_producer_iteration_years = []  # = 'all' or list of years to log, empty list to disable logging
            self.log_consumer_iteration_years = [2050]  # = 'all' or list of years to log, empty list to disable logging
            self.log_producer_decision_and_response_years = []  # [2029]  # 'all'  # = 'all' or list of years to log, empty list to disable logging

    from omega2 import run_omega

except:
    print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
    os._exit(-1)
