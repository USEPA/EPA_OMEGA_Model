"""

Top-level includes/definitions for the OMEGA model

Defines class OMEGASessionSettings which control an individual simulation session


----

**CODE**

"""

# OMEGA code version number
code_version = "2.3.0"
print('loading omega version %s' % code_version)

import os, sys

if 'darwin' in sys.platform:
    os.environ['QT_MAC_WANTS_LAYER'] = '1'  # for pyqtgraph on MacOS

# CU

import traceback

try:
    import time

    import pandas as pd
    # from warnings import simplefilter
    # simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
    pd.set_option('chained_assignment', 'raise')
    from pandas.api.types import is_numeric_dtype

    import numpy as np
    np.seterr(all='raise')

    import copy

    from common.omega_globals import *
    from common.omega_types import *
    from common import omega_globals
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
    fueling_classes = OMEGAEnum(['ICE', 'BEV', 'PHEV'])
    ownership_classes = OMEGAEnum(['shared', 'private'])
    legacy_reg_classes = OMEGAEnum(['car', 'truck', 'mediumduty'])
    fuel_units = OMEGAEnum(['gallon', 'kWh'])

    class OMEGASessionSettings(OMEGABase):
        """
        Define the settings required for a simulation session

        """
        def __init__(self):
            """
            Create an OMEGASessionSettings object with default settings used for testing and development.

            The primary way to create an OMEGASessionSettings object is via the batch process.

            See Also:
                omega_batch.py, producer.vehicle_aggregation.py

            """
            import time

            path = os.path.dirname(os.path.abspath(__file__)) + os.sep
            self.inputfile_metadata = []  #: stores information about input files such as filepath, filename and a unique checksum
            self.session_unique_name = 'OMEGA Quick Test'  #: used by the batch process to give each session within a batch a unique name
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')  #: datetime string used to timestamp the session run
            self.start_time = 0  #: used to track session duration
            self.end_time = 0  #: used to track session duration
            self.output_folder_base = 'out' + os.sep  #: output folder base name e.g. '2024_01_18_09_32_54_BatchName_SessionName/'
            self.output_folder = self.output_folder_base  #: path to the session output folder
            self.logfile_prefix = 'o2log_'  #: prefix of the session log file name, used in combination with the session unique name
            self.logfilename = ''  #: stores the full filepathname of the session log file
            self.session_is_reference = True  #: = ``True`` if this session is the reference (context) session
            self.auto_close_figures = True  #: auto close postproc figures if ``True``
            self.save_preliminary_outputs = True  #: retains preliminary (i.e. first pass) outputs if ``True``
            self.omega_model_path = path  #: absolute path to the ``omega_model`` directory
            self.analysis_initial_year = None  #: stores the analysis initial year, e.g. vehicle base year + 1
            self.consolidate_manufacturers = None  #: run compliance model with a single, consolidated, manufacturer instead of individual manufacturers
            self.manufacturer_gigawatthour_data = None  #: stores first pass total battery GWh consumption by manufacturer for use in limiting second pass GWh
            self.generate_context_calibration_files = True  #: if ``True`` (i.e. ``session_is_reference``) generate context session outputs for use by non-context sessions
            self.context_new_vehicle_generalized_costs_file = None  #: filepathname of the context session new vehicle generalized costs
            self.sales_share_calibration_file = None   #: filepathname of the context session sales share calibration file, if any
            self.vehicles_df = pd.DataFrame()  #: used to store base year vehicle data as a result of vehicle aggregation

            # user context settings:
            self.analysis_final_year = 2024  #: must be >= ``analysis_initial_year``
            # Note that the implicit_price_deflator.csv input file must contain data for this entry:
            self.analysis_dollar_basis = 2022  #: the 'dollar year' of analysis ouputs, for comparing costs adjusted for inflation/deflation
            self.context_id = 'AEO2021'  #: id of the context data used for the context session, e.g. 'AEO2021'
            self.context_case_id = 'Reference case'  #: id of the context sub-case, e.g. 'Reference case', 'High oil price', etc
            self.credit_market_efficiency = 1  #: 1.0 = 'perfect trading', less than 1.0 implies less than perfect trading of GHG compliance credits, 0.0 implies no trading and all manufacturers must meet their standards using only averaging and banking
            self.context_fuel_prices_file = path + 'test_inputs/context_fuel_prices.csv'  #: path the context fuel prices file, used by ``context.fuel_prices``
            self.context_electricity_prices_file = path + 'test_inputs/context_electricity_prices_aeo.csv'  #: path to the context electricity prices file, used by the user-definable ``ElectricityPrices`` class
            self.context_new_vehicle_market_file = path + 'test_inputs/context_new_vehicle_market-body_style.csv'  #: path to the context new vehicle market file, used by the user-definable ``NewVehicleMarket`` class
            self.manufacturers_file = path + 'test_inputs/manufacturers.csv'  #: path to the manufacturers file, used by ``producer.manufacturers``
            self.market_classes_file = path + 'test_inputs/market_classes_ice_bev_phev-body_style.csv'  #: path the market class definition file, used by the user-definable ``MarketClass`` class
            self.new_vehicle_price_elasticity_of_demand = -0.4  #: indicates change in sales v. change in price at the industry level, used to project action session total sales
            self.onroad_fuels_file = path + 'test_inputs/onroad_fuels.csv'  #: path to the onroad fuels file, used by ``context.onroad_fuels``
            self.onroad_vehicle_calculations_file = path + 'test_inputs/onroad_vehicle_calculations.csv'  #: path the onroad vehicle calculations file, used by the ``Vehicle`` class
            self.onroad_vmt_file = path + 'test_inputs/annual_vmt_fixed_by_age_ice_bev_phev-body_style.csv'  #: path the onroad annual vehicle miles travelled file, used by the user-definable ``OnroadVMT`` class
            self.consumer_pricing_multiplier_max = 1.1  #: maximum market class price multiplier during producer cross-subsidy
            self.consumer_pricing_multiplier_min = 1/1.1  #: minimum market class price multiplier during producer cross-subsidy (ideally should be ``1/consumer_pricing_multiplier_max``)
            self.producer_generalized_cost_file = path + 'test_inputs/producer_generalized_cost-body_style.csv'  #: path to the producer generalized cost file, used by the user-definable ``ProducerGeneralizedCost`` class
            self.production_constraints_file = path + 'test_inputs/production_constraints-body_style.csv'  #: path to the production constraings file, used by ``context.production_constraints``
            self.sales_share_file = path + 'test_inputs/sales_share_params_ice_bev_phev_body_style.csv'  #: path to the sales share file, used by the user-definable ``SalesShare`` class
            self.vehicle_price_modifications_file = path + 'test_inputs/vehicle_price_modifications-body_style.csv'  #: path the vehicle price modifications (e.g. 'incentives') file, used by ``context.price_modifications``
            self.vehicle_reregistration_file = path + 'test_inputs/reregistration_fixed_by_age_ice_bev_phev-body_style.csv'  #: path to the vehicle re-registration file, used by the user-definable ``Reregistration`` class
            self.ice_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_ice.csv'  #: path the ICE vehicles simulation results file, used by the user-definable ``CostCloud`` class
            self.bev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_bev.csv'  #: path the BEV vehicles simulation results file, used by the user-definable ``CostCloud`` class
            self.phev_vehicle_simulation_results_file = path + 'test_inputs/simulated_vehicles_rse_phev.csv'  #: path the PHEV vehicles simulation results file, used by the user-definable ``CostCloud`` class
            self.vehicles_file = path + 'test_inputs/vehicles.csv'  #: path the base year vehicles file, used by ``producer.vehicle_aggregation``
            self.powertrain_cost_input_file = path + 'test_inputs/powertrain_cost_frm.csv'  #: path to the power train costs file, used by the user-definable ``PowertrainCost`` class
            self.glider_cost_input_file = path + 'test_inputs/glider_cost.csv'  #: path the glider cost file, used by ``context.glider_cost``
            self.body_styles_file = path + 'test_inputs/body_styles.csv'  #: path the body styles file, used by ``context.body_styles``
            self.mass_scaling_file = path + 'test_inputs/mass_scaling.csv'  #: path the mass scaling file, used by ``context.mass_scaling``
            self.workfactor_definition_file = path + 'test_inputs/workfactor_definition.csv'  #: path to the workfactor definition file, used by ``policy.workfactor_definition``

            # user session settings:
            self.session_name = 'OMEGA Quick Test'  #: session name string

            # user policy settings:
            self.drive_cycle_weights_file = path + 'test_inputs/drive_cycle_weights.csv'  #: path to drive cycle weights file, used by ``policy.drive_cycle_weights``
            self.drive_cycle_ballast_file = path + 'test_inputs/drive_cycle_ballast.csv'  #: path to drive cycle ballast file, used by ``policy.drive_cycle_ballast``
            self.drive_cycles_file = path + 'test_inputs/drive_cycles.csv'  #: path to drive cycles file, used by ``policy.drive_cycles``
            self.ghg_credit_params_file = path + 'test_inputs/ghg_credit_params.csv'  #: path to GHG credit params file, used by ``policy.credit_banking``
            self.ghg_credits_file = path + 'test_inputs/ghg_credits.csv'  #: path to GHG credits file, used by ``policy.credit_banking``
            self.policy_targets_file = path + 'test_inputs/ghg_standards-footprint_NTR-FRM-CFR-form.csv'  #: path to policy target definitions file, used by user-definable ``VehicleTargets`` class
            self.offcycle_credits_file = path + 'test_inputs/offcycle_credits.csv'  #: path to offcycle credits file, used by user-definable ``OffCycleCredits`` class
            self.fuel_upstream_methods_file = path + 'test_inputs/policy_fuel_upstream_methods_zero.csv'  #: path to upstream methods file, used by ``policy.upstream_methods``
            self.utility_factor_methods_file = path + 'test_inputs/policy_utility_factor_methods.csv'  #: path to utility factor methods file, used by ``policy.utility_factors``
            self.policy_fuels_file = path + 'test_inputs/policy_fuels.csv'  #: path to policy fuels file, used by ``policy.policy_fuels``
            self.production_multipliers_file = path + 'test_inputs/production_multipliers.csv'  #: path to production multipliers file, used by ``policy.incentives``
            self.policy_reg_classes_file = path + 'test_inputs/regulatory_classes.csv'  #: path to policy reg classes file, used by user-definable ``RegulatoryClasses`` class
            self.required_sales_share_file = path + 'test_inputs/required_sales_share-body_style.csv'  #: path to required sales share file, used by ``policy.required_sales_share``

            # user postproc settings:
            self.ip_deflators_file = path + 'test_inputs/implicit_price_deflators.csv'  #: path to implicit price deflators file, used by ``context.ip_deflators``

            # "developer" settings:
            self.use_prerun_context_outputs = False  #: if ``True`` then use context session outputs from a previously run context session
            self.prerun_context_folder = ''  #: path to the previously run context session, if ``use_prerun_context_outputs`` is ``True``
            self.battery_GWh_limit_years = [2020]  #: used in combination with ``battery_GWh_limit`` to create industry-level battery production capacity limits year over year
            self.battery_GWh_limit = [1e9]  #: used in combination with ``battery_GWh_limit_years`` to create industry-level battery production capacity limits year over year
            self.producer_price_modification_scaler = 0.0  #: if non-zero then some scalar portion of vehicle incentives (price modifications) are incorporated into the producer vehicle generalized cost
            self.producer_footprint_wtp = 200  #: producer's estimate of consumer willingness to pay for increases in vehicle footprint, used in producer vehicle generalized cost
            self.footprint_min_scaler = 1/1.05  #: vehicle footprint minimum scaler in producer footprint sweep as part of composite vehicle cost cloud generation
            self.footprint_max_scaler = 1.05  #: vehicle footprint maximum scaler in producer footprint sweep as part of composite vehicle cost cloud generation
            self.redesign_interval_gain_years = [2020]  #: used in combination with ``redesign_interval_gain`` to allow modification of vehicle redesign cadence if desired
            self.redesign_interval_gain = [1.0]  #: used in combination with ``redesign_interval_gain_years`` to allow modification of vehicle redesign cadence if desired
            self.non_context_session_process_scaler = 1  #: used to modify the number of processes used by non-context sessions when multiprocessing, (e.g. 2 = use 1/2 the default number of processes)
            self.producer_shares_mode = True  #: if ``True`` then consumer share response is ignored.  Used for development, troubleshooting, or quicker runtime during testing
            self.producer_compliance_search_multipoint = True  #: if ``True`` then the producer compliance search will simultaneously approach compliance from points above and below compliance (if possible)
            self.powertrain_cost_with_ira = True  #: if ``True`` then Inflation Reduction Act incentives will apply to powertrain costs
            self.powertrain_cost_with_gpf = True  #: if ``True`` then gasoline particulate filter costs will apply to powertrain costs
            self.powertrain_cost_tracker = True  #: if ``True`` then detailed powertrain cost outputs will be generated
            self.base_year_min_sales = 0  #: minimum base year vehicles sales threshhold to consider when reading the base year vehicles file (e.g. ignore low-volume vehicles)
            self.phev_range_mi = 40  #: target PHEV charge-depleting range, miles
            self.bev_of_ice_rlhp60_scaler = 0.85  #: scaler for BEV roadload horsepower at 60 MPH (BEVs more aerodynamic than their ICE equivalent if scaler < 1.0)
            self.no_backsliding = False  #: if ``True`` then ICE vehicles must maintain or improve CO2e g/mi across redesign cycles
            self.nmc_share_BEV = {2022: 1}  #: used to define year over year share of BEVs with Nickel Manganese Cobalt battery type
            self.nmc_share_PHEV = {2022: 1}  #: used to define year over year share of PHEVs with Nickel Manganese Cobalt battery type
            self.nmc_share_HEV = {2022: 1}  #: used to define year over year share of HEVs with Nickel Manganese Cobalt battery type
            self.battery_cost_constant_thru = 2025  #: hold battery costs constant through this year
            self.producer_market_category_ramp_limit = 0.2  #: used to constrain producer sales shift between market classes (e.g ICE/BEV).  0.2 => five years to fully switch from one class to another
            self.producer_strategic_compliance_buffer_years = [2020]  #: used in combination with ``producer_strategic_compliance_buffer`` to allow manually banking (or burning) GHG credits year over year
            self.producer_strategic_compliance_buffer = [0.0]  #: used in combination with ``producer_strategic_compliance_buffer_years`` to allow manually banking (or burning) GHG credits year over year
            self.relax_second_pass_GWh = False  #: if ``True`` then second pass battery GWh production may exceed first pass production

            # advanced developer settings:
            self.vehicles_file_base_year_offset = None  #: added to the base year vehicles file model year and prior redesign year
            self.bev_range_mi = 300  #: target BEV charge-depleting range, miles
            self.bev_mdv_van_range_mi = 150  #: target medium-duty van charge-depleting range, miles
            self.kwh_per_mile_scale_years = [2020]  #: used in combination with ``kwh_per_mile_scale`` to scale BEV kWh/mile consumption values year over year, e.g. simulate improvements over time relative to the original simulation results
            self.kwh_per_mile_scale = [1.0]  #: used in combination with ``kwh_per_mile_scale_years`` to scale BEV kWh/mile consumption values year over year, e.g. simulate improvements over time relative to the original simulation results
            self.rlhp20_min_scaler = 1.0  #: minimum roadload horsepower at 20 MPH scaler when sweeping RLHP20
            self.rlhp20_max_scaler = 1.0  #: maximum roadload horsepower at 20 MPH scaler when sweeping RLHP20
            self.rlhp60_min_scaler = 1.0  #: minimum roadload horsepower at 60 MPH scaler when sweeping RLHP60
            self.rlhp60_max_scaler = 1.0  #: maximum roadload horsepower at 60 MPH scaler when sweeping RLHP60
            self.allow_ice_of_bev = False  #: if ``True`` then base year BEVs will have ICE-equivalent alternative powertrain vehicles available starting at first redesign
            self.phev_battery_kwh = None  #: ``'RSE'`` => use RSE, ``None`` => use range calc, otherwise use scalar value to size PHEV battery capacity
            self.force_two_pass = False  #: can be used to force two pass (consolidated and non-consolidated compliance passes) as desired
            self.include_manufacturers_list = 'all'  #: ``'all'`` to include all base year vehicle manufacturers, else list of manufacturers to include, e.g. ``['Ford', 'Honda', ...]``
            self.exclude_manufacturers_list = 'none'  #: ``'none'`` to include all base year vehicle manufacturers, else list of manufacturers to exclude, e.g. ``['Ferrari', 'Bugatti', ...]``
            self.cost_curve_frontier_affinity_factor = 0.75  #: used in calculation cloud frontiers, lower values generate a more 'approximate' fit to the cloud and a lower number of points on the frontier, higher values generate a tighter fit and generally more points
            self.slice_tech_combo_cloud_tables = False  #: if ``True`` then only save producer search production options data within +- 20% of the target Mg, used in combination with ``log_producer_compliance_search_years`` and ``verbose_log_modules``
            self.verbose = False  #: if ``True`` then enable optional console outputs
            self.iterate_producer_consumer = True  #: enable producer-consumer cross subsidy iteration when ``True``
            self.second_pass_production_constraints = False  #: if ``True`` then apply industry-level production constraints on the second pass
            self.producer_voluntary_overcompliance = False  #: enable producer voluntary overcompliance if ``True``, experimental
            self.flat_context = False  #: if ``True`` then all context values are determined by ``flat_context_year`` instead of model year, for troubleshooting
            self.flat_context_year = 2021  #: used in combination with ``flat_context`` to set constant context values
            self.run_profiler = False  #: run profiler if ``True``
            self.multiprocessing = True and not self.run_profiler and not getattr(sys, 'frozen', False)  #: enables multiprocessing if ``True``

            # search and convergence-related developer settings:
            self.producer_num_market_share_options = 3  #: nominal number of market share options considered per producer compliance search iteration
            self.producer_num_tech_options_per_ice_vehicle = 3  #: nominal number of tech options per ICE vehicle considered per producer compliance search iteration
            self.producer_num_tech_options_per_bev_vehicle = 1  #: nominal number of tech options per BEV vehicle considered per producer compliance search iteration
            self.producer_compliance_search_min_share_range = 1e-5  #: the minimum share range used during producer compliance search iteration
            self.producer_compliance_search_convergence_factor = 0.9  #: producer search share range = ``producer_compliance_search_convergence_factor ** iteration_num``
            self.producer_compliance_search_tolerance = 1e-6  #: used to determine if producer compliance search as found an acceptable solution, relative to 1.0 being perfect compliance
            self.producer_voluntary_overcompliance_min_benefit_frac = 0.01  #: minimum benefit of voluntary overcompliance, as a fraction of compliance cost, experimental
            self.producer_voluntary_overcompliance_min_strategic_compliance_ratio = 0.9999  #: determines the maxinum voluntary overcompliance to consider, experimental
            self.producer_consumer_max_iterations = 5  #: determines the maximum number of producer-consumer cross subsidy iterations to consider
            self.producer_consumer_convergence_tolerance = 5e-4  #: the threshhold for determining producer-consumer share convergence, absolute market share
            self.consumer_pricing_num_options = 14  #: the number of cross-subsidy pricing options to consider per cross-subsidy iteration per market class
            self.producer_cross_subsidy_price_tolerance = 5e-4  #: the threshhold for determining producer-consumer price convergence, relative to 1.0 being perfect price convergence

            # logging and verbosity-related settings:
            # list of modules to allow verbose log files, or empty to disable:
            self.verbose_log_modules = ['producer_compliance_search', 'cross_subsidy_search_',
                                        'cv_cost_curves_', 'v_cost_curves_', 'v_cost_clouds_',
                                        'v_cloud_plots_', 'cv_cloud_plots', 'effects_']  #: used to enable verbose log file outputs for various modules

            # list of modules to allow verbose console output, or empty to disable
            self.verbose_console_modules = ['producer_compliance_search_',
                                            'p-c_shares_and_costs', 'p-c_max_iterations_',
                                            'cross_subsidy_search_', 'cross_subsidy_multipliers_',
                                            'cross_subsidy_convergence_']  #: used to enable verbose console outputs for various modules

            self.verbose_postproc = ['iteration_']  #: used to control verbose postproc outputs

            self.canary_byvid = -1  #: canary base year vehicle ID, for development or troubleshooting

            self.log_vehicle_cloud_years = []  #: = ``'all'`` or list of years to log, empty list to disable logging

            self.log_producer_compliance_search_years = []  #: = ``'all'`` or list of years to log, empty list to disable logging

            self.log_consumer_iteration_years = [2050]  #: = ``'all'`` or list of years to log, empty list to disable logging

            self.log_producer_decision_and_response_years = []  #: = ``'all'`` or list of years to log, empty list to disable logging

            self.plot_and_log_vehicles = []  #: list of vehicles to plot in log_producer_compliance_search_years, by namem e.g. ``['ICE Large Van truck minivan 4WD']``

            # dynamic modules / classes
            self.RegulatoryClasses = None  #: reference to user-definable RegulatoryClasses class
            self.VehicleTargets = None  #: reference to user-definable VehicleTargets class
            self.OffCycleCredits = None  #: reference to user-definable OffCycleCredits class
            self.Reregistration = None  #: reference to user-definable Reregistration class
            self.OnroadVMT = None  #: reference to user-definable OnroadVMT class
            self.SalesShare = None  #: reference to user-definable SalesShare class
            self.ProducerGeneralizedCost = None  #: reference to user-definable ProducerGeneralizedCost class
            self.MarketClass = None  #: reference to user-definable MarketClass class
            self.CostCloud = None  #: reference to user-definable CostCloud class
            self.PowertrainCost = None  #: reference to user-definable PowertrainCost class
            self.ElectricityPrices = None  #: reference to user-definable ElectricityPrices class

            self.notification_destination = None  #: for optional text notifications, see ``common.omega_functions.send_text()``
            self.notification_email = None  #: for optional text notifications, see ``common.omega_functions.send_text()``
            self.notification_password = None  #: for optional text notifications, see ``common.omega_functions.send_text()``

except:
    print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
    sys.exit(-1)
