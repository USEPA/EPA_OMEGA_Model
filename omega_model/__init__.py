"""

Top-level includes/definitions for the OMEGA model

Defines class OMEGARuntimeOptions which control an individual simulation session


----

**CODE**

"""

# OMEGA code version number
code_version = "0.8.0"
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
    from producer.producer_base_classes import *

    import scipy.interpolate

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
            self.session_name = 'OMEGA Demo'
            self.session_unique_name = 'OMEGA Demo'
            self.session_is_reference = True
            self.auto_close_figures = False
            self.output_folder = 'out' + os.sep
            self.database_dump_folder = self.output_folder + '__dump' + os.sep
            self.consolidate_manufacturers = False
            self.manufacturers_file = path + 'demo_inputs/manufacturers.csv'
            self.market_classes_file = path + 'demo_inputs/market_classes.csv'
            self.vehicles_file = path + 'demo_inputs/vehicles.csv'
            self.onroad_vehicle_calculations_file = path + 'demo_inputs/onroad_vehicle_calculations.csv'
            self.sales_share_file = path + 'demo_inputs/sales_share-gcam.csv'
            self.onroad_fuels_file = path + 'demo_inputs/onroad_fuels.csv'
            self.context_id = 'AEO2021'
            self.context_case_id = 'Reference case'
            self.context_new_vehicle_generalized_costs_file = 'context_new_vehicle_prices.csv'
            self.generate_context_new_vehicle_generalized_costs_file = True
            self.context_fuel_prices_file = path + 'demo_inputs/context_fuel_prices.csv'
            self.fuel_upstream_methods_file = path + 'demo_inputs/policy_fuel_upstream_methods.csv'
            self.vehicle_price_modifications_file = path + 'demo_inputs/vehicle_price_modifications.csv'
            self.drive_cycles_file = path + 'demo_inputs/drive_cycles.csv'
            self.drive_cycle_weights_file = path + 'demo_inputs/drive_cycle_weights.csv'
            self.context_new_vehicle_market_file = path + 'demo_inputs/context_new_vehicle_market.csv'
            self.vehicle_simulation_results_and_costs_file = path + 'demo_inputs/simulated_vehicles.csv'
            self.analysis_initial_year = None
            self.analysis_final_year = 2021
            self.logfile_prefix = 'o2log_'
            self.logfilename = ''
            self.consumer_calc_generalized_cost = None
            self.policy_targets_file = path + 'demo_inputs/ghg_standards-footprint.csv'
            self.policy_reg_classes_file = path + 'demo_inputs/regulatory_classes.csv'
            self.production_multipliers_file = path + 'demo_inputs/production_multipliers.csv'
            self.policy_fuels_file = path + 'demo_inputs/policy_fuels.csv'
            self.ghg_credits_file = path + 'demo_inputs/ghg_credits.csv'
            self.required_sales_share_file = path + 'demo_inputs/required_sales_share.csv'
            self.producer_generalized_cost_file = path + 'demo_inputs/producer_generalized_cost.csv'
            self.production_constraints_file = path + 'demo_inputs/production_constraints.csv'
            self.vehicle_reregistration_file = path + 'demo_inputs/reregistration_fixed_by_age.csv'
            self.onroad_vmt_file = path + 'demo_inputs/annual_vmt_fixed_by_age.csv'
            self.offcycle_credits_file = path + 'demo_inputs/offcycle_credits.csv'

            self.consumer_pricing_num_options = 4
            self.consumer_pricing_multiplier_min = 0.95
            self.consumer_pricing_multiplier_max = 1.05

            self.new_vehicle_price_elasticity_of_demand = -0.5
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')

            self.calc_effects = True
            self.analysis_dollar_basis = 2020 # Note that the implicit_price_deflator.csv input file must contain data for this entry.
            self.discount_values_to_year = 2021
            self.cost_accrual = 'end-of-year'  # end-of-year means costs accrue at year's end; beginning-of-year means cost accrue at year's beginning
            self.calc_criteria_emission_costs = True
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

            # developer settings
            self.producer_num_market_share_options = 5
            self.producer_num_tech_options_per_ice_vehicle = 5
            self.producer_num_tech_options_per_bev_vehicle = 1
            self.cost_curve_frontier_affinity_factor = 0.75
            self.slice_tech_combo_cloud_tables = True
            self.verbose = False
            self.iterate_producer_consumer = True

            self.producer_consumer_max_iterations = 2  # recommend 2+
            self.producer_consumer_convergence_tolerance = 1e-3
            self.producer_compliance_search_max_iterations = 15
            self.producer_compliance_search_convergence_factor = 0.33
            self.producer_compliance_search_tolerance = 1e-6
            self.producer_cross_subsidy_price_tolerance = 1e-4
            self.run_profiler = False
            self.flat_context = False
            self.flat_context_year = 2021

            self.verbose_console_modules = []  # list of modules to allow verbose console output, or empty to disable
            self.log_producer_iteration_years = []  # = 'all' or list of years to log, empty list to disable logging
            self.log_consumer_iteration_years = [2050]  # = 'all' or list of years to log, empty list to disable logging
            self.log_producer_decision_and_response_years = []  # = 'all' or list of years to log, empty list to disable logging

            # dynamic modules / classes
            self.RegulatoryClasses = None
            self.VehicleTargets = None
            self.OffCycleCredits = None
            self.Reregistration = None
            self.OnroadVMT = None
            self.SalesShare = None
            self.ProducerGeneralizedCost = None
            self.MarketClass = None

except:
    print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
    os._exit(-1)
