"""

Top-level includes/definitions for the OMEGA model

Defines class OMEGARuntimeOptions which control an individual simulation session


----

**CODE**

"""

# OMEGA2 code version number
code_version = "0.7.1"
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
    import pandas as pd
    pd.set_option('chained_assignment', 'raise')

    from common.omega_globals import *
    from common.omega_types import *
    from common.omega_db import *
    from common import file_io, omega_log
    from common.input_validation import *
    from common.omega_functions import *
    from policy.policy_base_classes import *
    from consumer.consumer_base_classes import *

    import scipy.interpolate

    # --- OMEGA2 global constants ---

    # enumerated values
    fueling_classes = OMEGAEnum(['BEV', 'ICE'])
    hauling_classes = OMEGAEnum(['hauling', 'non_hauling'])
    ownership_classes = OMEGAEnum(['shared', 'private'])
    legacy_reg_classes = OMEGAEnum(['car', 'truck'])
    fuel_units = OMEGAEnum(['gallon', 'kWh'])

    class OMEGARuntimeOptions(OMEGABase):
        """
        An OMEGARuntimeOptions object defines the settings required for a simulation session

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
            self.session_name = 'OMEGA2 Demo'
            self.session_unique_name = 'OMEGA2 Demo'
            self.session_is_reference = True
            self.verbose = False
            self.auto_close_figures = False
            self.output_folder = 'out' + os.sep
            self.database_dump_folder = self.output_folder + '__dump' + os.sep
            self.manufacturers_file = path + 'demo_inputs/manufacturers.csv'
            self.market_classes_file = path + 'demo_inputs/market_classes.csv'
            self.vehicles_file = path + 'demo_inputs/vehicles.csv'
            self.vehicle_onroad_calculations_file = path + 'demo_inputs/vehicle_onroad_calculations.csv'
            self.demanded_shares_file = path + 'demo_inputs/demanded_shares-gcam.csv'
            self.onroad_fuels_file = path + 'demo_inputs/onroad_fuels.csv'
            self.context_folder = ''
            self.context_id = 'AEO2021'
            self.context_case_id = 'Reference case'
            self.context_new_vehicle_generalized_costs_file = path + 'demo_inputs/context_new_vehicle_prices.csv'
            self.generate_context_new_vehicle_generalized_costs_file = False
            self.context_fuel_prices_file = path + 'demo_inputs/context_fuel_prices.csv'
            self.fuel_upstream_methods_file = path + 'demo_inputs/policy_fuel_upstream_methods.csv'
            self.price_modifications_file = path + 'demo_inputs/price_modifications.csv'
            self.drive_cycles_file = path + 'demo_inputs/drive_cycles.csv'
            self.drive_cycle_weights_file = path + 'demo_inputs/drive_cycle_weights.csv'
            self.context_new_vehicle_market_file = path + 'demo_inputs/context_new_vehicle_market.csv'
            self.cost_file = path + 'demo_inputs/simulated_vehicles.csv'
            self.cost_curve_frontier_affinity_factor = 0.75
            self.analysis_initial_year = None
            self.analysis_final_year = 2020
            self.logfile_prefix = 'o2log_'
            self.logfilename = ''
            self.producer_calc_generalized_cost = None
            self.consumer_calc_generalized_cost = None
            self.policy_targets_file = path + 'demo_inputs/ghg_standards-footprint.csv'
            self.policy_reg_classes_file = path + 'demo_inputs/regulatory_classes.csv'
            self.production_multipliers_file = path + 'demo_inputs/production_multipliers.csv'
            self.policy_fuels_file = path + 'demo_inputs/policy_fuels.csv'
            self.ghg_credits_file = path + 'demo_inputs/ghg_credits.csv'
            self.required_zev_share_file = path + 'demo_inputs/required_zev_share.csv'
            self.production_constraints_file = path + 'demo_inputs/production_constraints.csv'
            self.reregistration_file = path + 'demo_inputs/reregistration_fixed_by_age.csv'
            self.annual_vmt_file = path + 'demo_inputs/annual_vmt_fixed_by_age.csv'
            self.slice_tech_combo_cloud_tables = True
            self.offcycle_credits_file = path + 'demo_inputs/offcycle_credits.csv'

            self.allow_backsliding = True

            self.producer_max_iterations = 15
            self.producer_num_market_share_options = 5
            self.producer_num_tech_options_per_ice_vehicle = 5
            self.producer_num_tech_options_per_bev_vehicle = 1
            self.producer_iteration_tolerance = 1e-6
            self.producer_convergence_factor = 0.33

            self.iterate_producer_consumer = True
            self.producer_consumer_max_iterations = 2  # recommend 2+
            self.producer_consumer_iteration_tolerance = 1e-3

            self.consumer_pricing_num_options = 4
            self.consumer_pricing_multiplier_min = 0.95
            self.consumer_pricing_multiplier_max = 1.05

            self.new_vehicle_sales_response_elasticity = -0.5
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')

            self.calc_effects = False
            self.calc_criteria_emission_costs = False
            # effects modeling files
            self.ip_deflators_file = path + 'demo_inputs/implicit_price_deflators.csv'
            self.cpi_deflators_file = path + 'demo_inputs/cpi_price_deflators.csv'
            self.scc_cost_factors_file = path + 'demo_inputs/cost_factors-scc.csv'
            self.criteria_cost_factors_file = path + 'demo_inputs/cost_factors-criteria.csv'
            self.energysecurity_cost_factors_file = path + 'demo_inputs/cost_factors-energysecurity.csv'
            self.congestion_noise_cost_factors_file = path + 'demo_inputs/cost_factors-congestion-noise.csv'
            self.emission_factors_vehicles_file = path + 'demo_inputs/emission_factors-vehicles.csv'
            self.emission_factors_powersector_file = path + 'demo_inputs/emission_factors-powersector.csv'
            self.emission_factors_refinery_file = path + 'demo_inputs/emission_factors-refinery.csv'

            self.start_time = 0
            self.end_time = 0

            # debugging options
            self.verbose_console = []  # ['producer', 'consumer']  # list of modules to allow verbose console output, or empty to disable
            self.run_profiler = False
            self.flat_context = False
            self.flat_context_year = 2021
            self.log_producer_iteration_years = []  # = 'all' or list of years to log, empty list to disable logging
            self.log_consumer_iteration_years = [2050]  # = 'all' or list of years to log, empty list to disable logging
            self.log_producer_decision_and_response_years = []  # [2029]  # 'all'  # = 'all' or list of years to log, empty list to disable logging

            # dynamic modules / classes
            self.RegulatoryClasses = None
            self.VehicleTargets = None
            self.Reregistration = None
            self.AnnualVMT = None

except:
    print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
    os._exit(-1)
