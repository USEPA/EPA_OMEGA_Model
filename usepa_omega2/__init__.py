"""
__init.py__
===========


"""

import pandas as pd
pd.set_option('chained_assignment', 'raise')

from omega_db import *
from omega_types import *
import omega_log
import file_eye_oh as fileio
from input_validation import *

import scipy.interpolate

import os

# --- OMEGA2 global constants ---

# enumerated values
fueling_classes = OMEGAEnum(['BEV', 'ICE'])
hauling_classes = OMEGAEnum(['hauling', 'non hauling'])
ownership_classes = OMEGAEnum(['shared', 'private'])
reg_classes = OMEGAEnum(['car', 'truck'])
fuel_units = OMEGAEnum(['gallon', 'kWh'])

# OMEGA2 code version number
code_version = "phase0.1"

print('loading usepa_omega2 version %s' % code_version)


class OMEGARuntimeOptions(object):
    def __init__(self):
        self.session_name = 'OMEGA2 Demo'
        self.verbose = True
        self.output_folder = 'output' + os.sep
        self.database_dump_folder = '__dump'  + os.sep
        self.manufacturers_file = 'input_templates/manufacturers.csv'
        self.market_classes_file = 'input_templates/market_classes.csv'
        self.vehicles_file = 'input_templates/vehicles.csv'
        self.demanded_shares_file = 'input_templates/demanded_shares-gcam.csv'
        self.fuels_file = 'input_templates/fuels.csv'
        self.fuel_scenarios_file = 'input_templates/fuel_scenarios.csv'
        self.fuel_scenario_annual_data_file = 'input_templates/fuel_scenario_annual_data.csv'
        self.cost_file_type = 'curves'
        self.cost_file = 'input_templates/cost_curves.csv'
        self.cost_curve_frontier_affinity_factor = 0.75
        self.analysis_initial_year = None
        self.analysis_final_year = None
        self.logfile_prefix = 'o2log_'
        self.logfilename = ''
        self.producer_calculate_generalized_cost = None
        self.consumer_calculate_generalized_cost = None
        self.GHG_standard = 'flat'
        if self.GHG_standard == 'flat':
            self.ghg_standards_file = 'input_templates/ghg_standards-flat.csv'
        else:
            self.ghg_standards_file = 'input_templates/ghg_standards-footprint.csv'
        self.stock_scrappage = 'fixed'
        self.stock_vmt = 'fixed'
        if self.stock_scrappage == 'fixed':
            self.reregistration_fixed_by_age_file = 'input_templates/reregistration_fixed_by_age.csv'
        else:
            pass
        if self.stock_vmt == 'fixed':
            self.annual_vmt_fixed_by_age_file = 'input_templates/annual_vmt_fixed_by_age.csv'
        else:
            pass
        self.slice_tech_combo_cloud_tables = False
        self.allow_backsliding = False
        self.num_tech_options_per_vehicle = 5


from omega2 import run_omega
