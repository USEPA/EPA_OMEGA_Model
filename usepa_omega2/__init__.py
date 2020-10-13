"""
__init.py__
===========


"""

# OMEGA2 code version number
code_version = "0.2.1"
print('loading usepa_omega2 version %s' % code_version)

import os, traceback

try:
    import pandas as pd
    pd.set_option('chained_assignment', 'raise')

    from omega_db import *
    from omega_types import *
    import omega_log
    import file_eye_oh as fileio
    from input_validation import *

    import scipy.interpolate

    # --- OMEGA2 global constants ---

    # enumerated values
    fueling_classes = OMEGAEnum(['BEV', 'ICE'])
    hauling_classes = OMEGAEnum(['hauling', 'non hauling'])
    ownership_classes = OMEGAEnum(['shared', 'private'])
    reg_classes = OMEGAEnum(['car', 'truck'])
    fuel_units = OMEGAEnum(['gallon', 'kWh'])

    class OMEGARuntimeOptions(object):
        def __init__(self):
            import time

            self.session_name = 'OMEGA2 Demo'
            self.session_unique_name = 'OMEGA2 Demo'
            self.verbose = False
            self.output_folder = 'output' + os.sep
            self.database_dump_folder = '__dump' + os.sep
            self.manufacturers_file = 'input_samples/manufacturers.csv'
            self.market_classes_file = 'input_samples/market_classes.csv'
            self.vehicles_file = 'input_samples/vehicles.csv'
            self.demanded_shares_file = 'input_samples/demanded_shares-gcam.csv'
            self.fuels_file = 'input_samples/fuels.csv'
            self.fuels_context_file = 'input_samples/fuels_context.csv'
            self.cost_file_type = 'curves'
            self.cost_file = 'input_samples/cost_curves.csv'
            self.cost_curve_frontier_affinity_factor = 0.75
            self.analysis_initial_year = None
            self.analysis_final_year = None
            self.logfile_prefix = 'o2log_'
            self.logfilename = ''
            self.producer_calculate_generalized_cost = None
            self.consumer_calculate_generalized_cost = None
            self.GHG_standard = 'flat'
            if self.GHG_standard == 'flat':
                self.ghg_standards_file = 'input_samples/ghg_standards-flat.csv'
            else:
                self.ghg_standards_file = 'input_samples/ghg_standards-footprint.csv'
            self.ghg_standards_fuels_file = 'input_samples/ghg_standards-fuels.csv'
            self.required_zev_share_file = 'input_samples/required_zev_share.csv'
            self.stock_scrappage = 'fixed'
            self.stock_vmt = 'fixed'
            if self.stock_scrappage == 'fixed':
                self.reregistration_fixed_by_age_file = 'input_samples/reregistration_fixed_by_age.csv'
            else:
                pass
            if self.stock_vmt == 'fixed':
                self.annual_vmt_fixed_by_age_file = 'input_samples/annual_vmt_fixed_by_age.csv'
            else:
                pass
            self.context_folder = ''
            self.context_name = ''
            self.slice_tech_combo_cloud_tables = False
            self.allow_backsliding = False
            self.producer_consumer_max_iterations = 20
            self.producer_consumer_iteration_tolerance = 0.01
            self.num_share_options = 15
            self.num_tech_options_per_ice_vehicle = 15
            self.num_tech_options_per_bev_vehicle = 2
            self.iterate_producer_consumer = True
            self.timestamp_str = time.strftime('%Y%m%d_%H%M%S')
            self.start_time = 0
            self.end_time = 0


    from omega2 import run_omega

except:
    print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
    os._exit(-1)
