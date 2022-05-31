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
            self.auto_close_figures = False
            self.output_folder = 'out' + os.sep
            self.database_dump_folder = self.output_folder + '__dump' + os.sep
            self.omega_model_path = path
            self.consolidate_manufacturers = True
            self.manufacturers_file = path + 'test_inputs/manufacturers.csv'
            self.market_classes_file = path + 'test_inputs/market_classes.csv'
            self.vehicles_file = path + 'test_inputs/vehicles.csv'
            self.vehicles_df = pd.DataFrame()
            self.onroad_vehicle_calculations_file = path + 'test_inputs/onroad_vehicle_calculations.csv'
            self.sales_share_file = path + 'test_inputs/sales_share_params.csv'
            self.onroad_fuels_file = path + 'test_inputs/onroad_fuels.csv'
            self.context_id = 'AEO2021'
            self.context_case_id = 'Reference case'
            self.context_new_vehicle_generalized_costs_file = 'context_new_vehicle_prices.csv'
            self.sales_share_calibration_file = 'context_sales_share_calibration.csv'
            self.generate_context_calibration_files = True
            self.context_fuel_prices_file = path + 'test_inputs/context_fuel_prices.csv'
            self.fuel_upstream_methods_file = path + 'test_inputs/policy_fuel_upstream_methods.csv'
            self.vehicle_price_modifications_file = path + 'test_inputs/vehicle_price_modifications.csv'
            self.drive_cycles_file = path + 'test_inputs/drive_cycles.csv'
            self.drive_cycle_weights_file = path + 'test_inputs/drive_cycle_weights.csv'
            self.drive_cycle_ballast_file = path + 'test_inputs/drive_cycle_ballast.csv'
            self.context_new_vehicle_market_file = path + 'test_inputs/context_new_vehicle_market.csv'

            # self.ice_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_ice.csv'
            # self.bev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_bev.csv'
            # self.phev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_phev.csv'

            self.ice_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_ice.csv'
            self.bev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_bev.csv'
            self.phev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_phev.csv'

            # TODO: add these to the batch process
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
            self.required_sales_share_file = path + 'test_inputs/required_sales_share.csv'
            self.producer_generalized_cost_file = path + 'test_inputs/producer_generalized_cost.csv'
            self.production_constraints_file = path + 'test_inputs/production_constraints.csv'
            self.vehicle_reregistration_file = path + 'test_inputs/reregistration_fixed_by_age.csv'
            self.onroad_vmt_file = path + 'test_inputs/annual_vmt_fixed_by_age.csv'
            self.offcycle_credits_file = path + 'test_inputs/offcycle_credits.csv'

            self.consumer_pricing_num_options = 4
            self.consumer_pricing_multiplier_min = 0.9
            self.consumer_pricing_multiplier_max = 1.1

            self.new_vehicle_price_elasticity_of_demand = -0.4
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')

            # self.calc_effects = True
            self.calc_effects = 'Physical and Costs' # options are 'None', 'Physical' and 'Physical and Costs' as strings
            self.analysis_dollar_basis = 2020 # Note that the implicit_price_deflator.csv input file must contain data for this entry.
            self.discount_values_to_year = 2021
            self.cost_accrual = 'end-of-year'  # end-of-year means costs accrue at year's end; beginning-of-year means cost accrue at year's beginning
            # self.calc_criteria_emission_costs = False # no longer functional in omega.py
            # effects modeling files
            self.general_inputs_for_effects_file = path + 'test_inputs/general_inputs_for_effects.csv'
            self.ip_deflators_file = path + 'test_inputs/implicit_price_deflators.csv'
            self.cpi_deflators_file = path + 'test_inputs/cpi_price_deflators.csv'
            self.scc_cost_factors_file = path + 'test_inputs/cost_factors_scc.csv'
            self.criteria_cost_factors_file = path + 'test_inputs/cost_factors_criteria.csv'
            self.energysecurity_cost_factors_file = path + 'test_inputs/cost_factors_energysecurity.csv'
            self.congestion_noise_cost_factors_file = path + 'test_inputs/cost_factors_congestion_noise.csv'
            self.emission_factors_vehicles_file = path + 'test_inputs/emission_rates_vehicles-NTR.csv'
            # self.emission_factors_vehicles_file = path + 'test_inputs/emission_factors_vehicles.csv'
            self.emission_factors_powersector_file = path + 'test_inputs/emission_factors_powersector.csv'
            self.emission_factors_refinery_file = path + 'test_inputs/emission_factors_refinery.csv'
            self.maintenance_cost_inputs_file = path + 'test_inputs/maintenance_cost.csv'
            self.repair_cost_inputs_file = path + 'test_inputs/repair_cost.csv'
            self.refueling_cost_inputs_file = path + 'test_inputs/refueling_cost.csv'

            self.start_time = 0
            self.end_time = 0

            # developer settings
            self.producer_num_market_share_options = 3
            self.producer_num_tech_options_per_ice_vehicle = 3
            self.producer_num_tech_options_per_bev_vehicle = 1
            self.cost_curve_frontier_affinity_factor = 0.75
            self.slice_tech_combo_cloud_tables = True
            self.verbose = False
            self.iterate_producer_consumer = True

            self.producer_consumer_max_iterations = 20  # recommend 2+
            self.producer_consumer_convergence_tolerance = 5e-4
            self.producer_compliance_search_min_share_range = 1e-5
            self.producer_compliance_search_convergence_factor = 0.9
            self.producer_compliance_search_tolerance = 1e-6
            self.producer_cross_subsidy_price_tolerance = 1e-4
            self.run_profiler = False
            self.multiprocessing = True and not self.run_profiler and not getattr(sys, 'frozen', False)
            self.flat_context = False
            self.flat_context_year = 2021

            # list of modules to allow verbose log files, or empty to disable:
            self.verbose_log_modules = ['database_', 'producer_compliance_search', 'cross_subsidy_search_',
                                        'cv_cost_curves_', 'v_cost_curves_']

            # list of modules to allow verbose console output, or empty to disable
            self.verbose_console_modules = ['producer_compliance_search_',
                                            'p-c_shares_and_costs', 'p-c_max_iterations_',
                                            'cross_subsidy_search_', 'cross_subsidy_multipliers_',
                                            'cross_subsidy_convergence_']

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
