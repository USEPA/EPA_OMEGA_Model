"""

**OMEGA effects batch settings.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row header followed by subsequent data rows.

The data represents OMEGA effects batch settings.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       parameter,fleet,session_policy,value,full_path,notes

Sample Data Rows
    .. csv-table::
        :widths: auto

        RUNTIME OPTIONS,,,,
        Sessions to Run,,,lmdv,,enter ld for ld only or md for md only or lmdv for both
        Run ID,lmdv,all,,,enter a run identifier (in value column) for your output folder name or blank for default (default is omega_effects)
        Run Description,lmdv,,,,
        Save Path,lmdv,all,,C:/omega/effects/outputs,"enter full path, including drive id but do not include unique run identifiers",
        Save Input Files,lmdv,all,FALSE,,enter True to copy over input files or False to save space and not do so
        Save Context Fuel Cost per Mile File,lmdv,all,FALSE,,enter True or False and note that these files can be large especially in CSV format
        Save Vehicle-Level Safety Effects Files,lmdv,all,FALSE,,enter True or False and note that these files can be large especially in CSV format
        Save Vehicle-Level Physical Effects Files,lmdv,all,FALSE,,enter True or False - these files can be large especially in CSV format
        Save Vehicle-Level Cost Effects Files,lmdv,all,FALSE,,enter True or False - these files can be large especially in CSV format
        Format for Vehicle-Level Output Files,lmdv,all,csv,,enter 'csv' for large Excel-readable files 'parquet' for compressed files usable in Pandas
        Powertrain Costs FEV,lmdv,all,TRUE,,enter TRUE or FALSE (must be consistent with the compliance run)
        Run Employment Analysis Costs,lmdv,all,TRUE,,enter TRUE or FALSE
        Use Marginal EGU Rates,lmdv,all,FALSE,,enter TRUE for marginal rates and FALSE for average rates
        BATCH SETTINGS - COMPLIANCE,,,,,
        batch_folder,ld,all,,C:/omega/compliance/<batch folder>,
        batch_folder,md,all,,C:/omega/compliance/<batch folder>,
        Vehicles File Base Year,ld,all,2022,,this should be consistent with the OMEGA compliance run
        Vehicles File Base Year,md,all,2022,,this should be consistent with the OMEGA compliance run
        BATCH SETTINGS - EFFECTS
        Analysis Final Year,lmdv,all,2055,,this should be <= the value used in the OMEGA compliance run
        Cost Accrual,lmdv,all,end-of-year,,
        Discount Values to Year,lmdv,all,2027,,
        Analysis Dollar Basis,lmdv,all,2022,,
        Context Name Liquid Fuel,lmdv,all,AEO2023,,
        Context Case Liquid Fuel,lmdv,all,Reference case,,
        VMT Rebound Rate ICE,lmdv,all,-0.1,,
        VMT Rebound Rate BEV,lmdv,all,0,,
        VMT Rebound post-FRM,lmdv,all,TRUE,,
        SC-GHG in Net Benefits,lmdv,all,global,,"enter 'global' or 'domestic' or 'both' (note that both global and domesitc benefits are calculated, this only impacts net benefits)"
        Maintenance Costs File,lmdv,all,,C:/omega/effects/inputs/maintenance_costs.csv,
        Repair Costs File,lmdv,all,,C:/omega/effects/inputs/repair_costs.csv,
        Refueling Costs File,lmdv,all,,C:/omega/effects/inputs/refueling_costs.csv,
        General Inputs for Effects File,lmdv,all,,C:/omega/effects/inputs/general_inputs_for_effects.csv,
        Criteria Cost Factors File,lmdv,all,,C:/omega/effects/inputs/criteria_cost_factors.csv,
        SCGHG Cost Factors File,lmdv,all,,C:/omega/effects/inputs/scghg_cost_factors.csv,
        Energy Security Cost Factors File,lmdv,all,,C:/omega/effects/inputs/energy_security_cost_factors.csv,
        Congestion-Noise Cost Factors File,lmdv,all,,C:/omega/effects/inputs/congestion_and_noise_cost_factors.csv,
        Insurance and Taxes Cost Factors File,lmdv,all,,C:/omega/effects/inputs/insurance_and_taxes_cost_factors.csv,
        Implicit Price Deflators File,lmdv,all,,C:/omega/effects/inputs/implicit_price_deflators_20230602.csv,
        CPI Price Deflators File,lmdv,all,,C:/omega/effects/inputs/cpi_deflators_file.csv,
        EGU Data File,lmdv,all,,C:/omega/effects/inputs/egu_data.csv,
        Refinery Data File,lmdv,all,,C:/omega/effects/inputs/refinery_data.csv,
        Safety Values File,lmdv,all,,C:/omega/effects/inputs/safety_values.csv,
        Fatality Rates File,lmdv,all,,C:/omega/effects/inputs/fatality_rates.csv,
        Legacy Fleet File,ld,all,,C:/omega/effects/inputs/legacy_fleet_ld.csv,
        Legacy Fleet File,md,all,,C:/omega/effects/inputs/legacy_fleet_md.csv,
        SESSION SETTINGS - LD,,,,,
        Session Name,ld,context,<context session name>,,
        Context Stock and VMT File,ld,context,,C:/omega/effects/inputs/context_stock_vmt_ld.csv,
        Context Electricity Prices,ld,context,,C:/omega/effects/inputs/electricity_prices_aeo.csv,
        Session Name,ld,no_action,<no action session name>,,
        Session Vehicle Emission Rates File,ld,no_action,,C:/omega/effects/inputs/vehicle_emission_rates_no_gpf.csv,
        Session Electricity Prices,ld,no_action,,C:/omega/effects/inputs/electricity_prices_ipm_no_action.csv,
        Session Name,ld,action_1,<action session name>,,
        Session Vehicle Emission Rates File,ld,action_1,,C:/omega/effects/inputs/vehicle_emission_rates_with_gpf.csv,
        Session Electricity Prices,ld,action_1,,C:/omega/effects/inputs/electricity_prices_ipm_action.csv,
        SESSION SETTINGS - MD,,,,,
        Session Name,md,context,<context session name>,,
        Context Stock and VMT File,md,context,,C:/omega/effects/inputs/context_stock_vmt_md.csv,
        Context Electricity Prices,md,context,,C:/omega/effects/inputs/electricity_prices_aeo.csv,
        Session Name,md,no_action,<no action session name>,,
        Session Vehicle Emission Rates File,md,no_action,,C:/omega/effects/inputs/vehicle_emission_rates_no_gpf.csv,
        Session Electricity Prices,md,no_action,,C:/omega/effects/inputs/electricity_prices_ipm_no_action.csv,
        Session Name,md,action_1,<action session name>,,
        Session Vehicle Emission Rates File,md,action_1,,C:/omega/effects/inputs/vehicle_emission_rates_with_gpf.csv,
        Session Electricity Prices,md,action_1,,C:/omega/effects/inputs/electricity_prices_ipm_action.csv,

Data Row Name and Description

**RUNTIME OPTIONS**

:Sessions to Run:
    A user provided choice to run all sessions (lmdv) or limit the run to just light-duty (ld) or medium-duty (md)

:Run ID:
    A user defined run ID (optional; default='omega_effects')

:Run Description:
    A user defined run description

:Save Path:
    A full system path designation to which to save results

:Save Input Files:
    True/False entry for whether to save the input files to the results folder

:Save Context Fuel Cost per Mile File:
    True/False entry for whether to save the context fuel cost per mile file

:Save Vehicle-Level Safety Effects Files:
    True/False entry for whether to save the vehicle-level safety effects file

:Save Vehicle-Level Physical Effects Files:
    True/False entry for whether to save the vehicle-level physical effects file

:Save Vehicle-Level Cost Effects Files:
    True/False entry for whether to save the vehicle-level cost effects file

:Format for Vehicle-Level Output Files:
    'csv' or 'parquet'; this entry must be 'csv' when running from the executable

:Powertrain Costs FEV:
    True/False entry for whether to save the FEV developed powertrain costs

:Run Employment Analysis Costs:
    True/False entry for whether to run a cost summary for use in the employment analysis

:Use Marginal EGU Rates:
    True/False entry for whether to use marginal or average EGU rates

**BATCH SETTINGS - COMPLIANCE**

:batch_folder:
    Pathname of the OMEGA compliance batch folder on which to run effects

:Vehicles File Base Year:
    The intended model year of the base year vehicles file, should be consistent with the OMEGA compliance run

**BATCH SETTINGS - EFFECTS**

:Analysis Final Year:
    The final effects year, should be <= the value used in the OMEGA compliance run

:Cost Accrual:
    The time of year when costs are assumed to accrue, ``end-of-year`` or ``beginning-of-year``

:Discount Values to Year:
    The year to which all monetized values in the cost effects outputs will be discounted

:Analysis Dollar Basis:
    The dollar valuation for all monetized values in the cost effects outputs, i.e., costs are expressed in "Dollar Basis" dollars

:Context Name Liquid Fuel:
    Context name, e.g. ``AEO2021``

:Context Case Liquid Fuel:
    Context case, e.g., ``Reference case``

:VMT Rebound Rate ICE:
    VMT rebound rate for internal combustion engines

:VMT Rebound Rate BEV:
    VMT rebound rate for battery-electric vehicles

:VMT Rebound post-FRM:
    if TRUE - non-context session vehicles are compared back to their context session starting point via
    base_year_vehicle_id and base_year_powertrain_type to be more consistent with the historical approach to calculating rebound

:SC-GHG in Net Benefits *(str)*:
    'global' or 'domestic' or 'both' (note that both global and domesitc benefits are calculated, if available, this only impacts net benefits)

:Maintenance Costs File *(str)*:
    The absolute path to the maintenance cost inputs file,
    loaded by :any:`omega_effects.context.maintenance_cost.py<omega_effects.context.maintenance_cost>`

:Repair Costs File *(str)*:
    The absolute path to the repair cost inputs file,
    loaded by :any:`omega_effects.context.repair_cost.py<omega_effects.context.repair_cost>`

:Refueling Costs File *(str)*:
    The absolute path to the refueling cost inputs file,
    loaded by :any:`omega_effects.context.refueling_cost.py<omega_effects.context.refueling_cost>`

:General Inputs for Effects File *(str)*:
    The absolute path to the general inputs used for effects calculations,
    loaded by :any:`omega_effects.general.general_inputs_for_effects.py<omega_effects.general.general_inputs_for_effects>`

:Criteria Cost Factors File *(str)*:
    The absolute path to the criteria pollutant costs file,
    loaded by :any:`omega_effects.effects.cost_factors_criteria.py<omega_effects.effects.cost_factors_criteria>`

:SCGHG Cost Factors File *(str)*:
    The absolute path to the social cost of carbon and carbon-equivalent pollutants file,
    loaded by :any:`omega_effects.effects.cost_factors_scghg.py<omega_effects.effects.cost_factors_scghg>`

:Energy Security Cost Factors File *(str)*:
    The absolute path to the energy security cost factors file,
    loaded by :any:`omega_effects.effects.cost_factors_energysecurity.py<omega_effects.effects.cost_factors_energysecurity>`

:Congestion-Noise Cost Factors File *(str)*:
    The absolute path to the congestion and noise cost factors file,
    loaded by :any:`omega_effects.effects.cost_factors_congestion_noise.py<omega_effects.effects.cost_factors_congestion_noise>`

:Insurance and Taxes Cost Factors File *(str)*:
    The relative or absolute path to the insurance and taxes file,
    loaded by :any:`omega_effects.consumer.cost_factors_insurance_and_taxes.py<omega_effects.consumer.cost_factors_insurance_and_taxes>`

:Implicit Price Deflators File *(str)*:
    The absolute path to the implicit price deflators file,
    loaded by :any:`omega_effects.context.ip_deflators.py<omega_effects.context.ip_deflators>`

:CPI Price Deflators File *(str)*:
    The absolute path to the CPI price deflators file,
    loaded by :any:`omega_effects.context.cpi_price_deflators.py<omega_effects.context.cpi_price_deflators>`

:EGU Data File *(str)*:
    The absolute path to the EGU data file,
    loaded by :any:`omega_effects.effects.egu_data.py<omega_effects.effects.egu_data>`

:Refinery Data File *(str)*:
    The absolute path to the Refinery data file,
    loaded by :any:`omega_effects.effects.refinery_data.py<omega_effects.effects.refinery_data>`

:Context Safety Values File *(str)*:
    The absolute path to the safety values file,
    loaded by :any:`omega_effects.effects.safety_values.py<omega_effects.effects.safety_values>`

:Context Fatality Rates File *(str)*:
    The absolute path to the fatality rates file,
    loaded by :any:`omega_effects.effects.fatality_rates.py<omega_effects.effects.fatality_rates>`

:Legacy Fleet File *(str)*:
    The absolute path to the legacy fleet file,
    loaded by :any:`omega_effects.effects.legacy_fleet.py<omega_effects.effects.legacy_fleet>`

**SESSION SETTINGS - LD**

:Session Name, context *(str)*:
    Context session name used in the OMEGA compliance run

:Context Stock and VMT File, context *(str)*:
    The absolute path to the context stock and VMT file,
    loaded by :any:`omega_effects.context.context_stock_vmt.py<omega_effects.context.context_stock_vmt>`

:Context Electricity Prices, context *(str)*:
    The absolute path to the context electricity prices file,
    loaded by :any:`omega_effects.context.electricity_prices_ipm.py<omega_effects.context.electricity_prices>`

:Session Name, no_action *(str)*:
    No Action session name used in the OMEGA compliance run

:Session Vehicle Emission Rates File, no_action *(str)*:
    The absolute path to the vehicle emission rates file,
    loaded by :any:`omega_effects.effects.emission_rates_vehicles.py<omega_effects.effects.emission_rates_vehicles>`

:Session Electricity Prices, no_action *(str)*:
    The absolute path to the session electricity prices file,
    loaded by :any:`omega_effects.context.electricity_prices_ipm.py<omega_effects.context.electricity_prices>`

:Session Name, action_1 *(str)*:
    An action session name used in the OMEGA compliance run

:Session Vehicle Emission Rates File, action_1 *(str)*:
    The absolute path to the vehicle emission rates file,
    loaded by :any:`omega_effects.effects.emission_rates_vehicles.py<omega_effects.effects.emission_rates_vehicles>`

:Session Electricity Prices, action_1 *(str)*:
    The absolute path to the session electricity prices file,
    loaded by :any:`omega_effects.context.electricity_prices_ipm.py<omega_effects.context.electricity_prices>`

**SESSION SETTINGS - MD**

:Session Name, context *(str)*:
    Context session name used in the OMEGA compliance run

:Context Stock and VMT File, context *(str)*:
    The absolute path to the context stock and VMT file,
    loaded by :any:`omega_effects.context.context_stock_vmt.py<omega_effects.context.context_stock_vmt>`

:Context Electricity Prices, context *(str)*:
    The absolute path to the context electricity prices file,
    loaded by :any:`omega_effects.context.electricity_prices_aeo.py<omega_effects.context.electricity_prices_aeo>`

:Session Name, no_action *(str)*:
    No Action session name used in the OMEGA compliance run

:Session Vehicle Emission Rates File, no_action *(str)*:
    The absolute path to the vehicle emission rates file,
    loaded by :any:`omega_effects.effects.emission_rates_vehicles.py<omega_effects.effects.emission_rates_vehicles>`

:Session Electricity Prices, no_action *(str)*:
    The absolute path to the session electricity prices file,
    loaded by :any:`omega_effects.context.electricity_prices_ipm.py<omega_effects.context.electricity_prices_ipm>`

:Session Name, action_1 *(str)*:
    An action session name used in the OMEGA compliance run

:Session Vehicle Emission Rates File, action_1 *(str)*:
    The absolute path to the vehicle emission rates file,
    loaded by :any:`omega_effects.effects.emission_rates_vehicles.py<omega_effects.effects.emission_rates_vehicles>`

:Session Electricity Prices, action_1 *(str)*:
    The absolute path to the session electricity prices file,
    loaded by :any:`omega_effects.context.electricity_prices_ipm.py<omega_effects.context.electricity_prices_ipm>`

----

**CODE**

"""
import sys
import importlib
import subprocess
import tkinter as tk
from tkinter import filedialog
import numpy as np
import pandas as pd
from pathlib import Path

from omega_effects.general.general_functions import read_input_file
from omega_effects.context.ip_deflators import ImplicitPriceDeflators
from omega_effects.context.cpi_price_deflators import CPIPriceDeflators
from omega_effects.context.legacy_fleet_fuel_consumption_adjustment import LegacyFleetFuelConsumptionAdjustment
from omega_effects.effects.cost_factors_criteria import CostFactorsCriteria
from omega_effects.effects.cost_factors_scghg import CostFactorsSCGHG
from omega_effects.effects.cost_factors_energysecurity import CostFactorsEnergySecurity
from omega_effects.effects.cost_factors_congestion_noise import CostFactorsCongestionNoise
from omega_effects.effects.legacy_fleet import LegacyFleet
from omega_effects.effects.egu_data import EGUdata
from omega_effects.effects.refinery_data import RefineryData
from omega_effects.effects.safety_values import SafetyValues
from omega_effects.effects.fatality_rates import FatalityRates
from omega_effects.effects.legacy_vs_analysis_fleet import LegacyVsAnalysisFleet

from omega_effects.consumer.annual_vmt_fixed_by_age import OnroadVMT
from omega_effects.consumer.reregistration_fixed_by_age import Reregistration
from omega_effects.consumer.cost_factors_insurance_and_taxes import InsuranceAndTaxes

from omega_effects.context.fuel_prices import FuelPrice
from omega_effects.context.context_stock_vmt import ContextStockVMT
from omega_effects.context.onroad_fuels import OnroadFuel
from omega_effects.context.maintenance_cost import MaintenanceCost
from omega_effects.context.repair_cost import RepairCost
from omega_effects.context.refueling_cost import RefuelingCost

from omega_effects.general.general_inputs_for_effects import GeneralInputsForEffects
from omega_effects.general.input_validation import validate_template_column_names
from omega_effects.general.input_validation import get_module_name


class BatchSettings:
    """

    Settings that apply to the whole batch of effects to run.

    """
    def __init__(self):
        self.effects_package_version = '2025.3.0'
        self.start_time_readable = None
        self.branch_name = None
        self.runtime_info = None
        self.batch_df = pd.DataFrame()
        self.batch_program = None
        self.batch_folder = None
        self.batch_name = None
        self.run_id = None

        # runtime options set via batch settings file
        self.file_format = None
        self.path_outputs = None
        self.save_context_fuel_cost_per_mile_file = None
        self.save_vehicle_safety_effects_files = None
        self.save_vehicle_physical_effects_files = None
        self.save_vehicle_cost_effects_files = None
        self.save_input_files = False
        self.powertrain_costs_fev = True
        self.run_employment_analysis_costs = None
        self.marginal_egu_rates = False  # lmdv frm used average

        self._dict = {}
        self.batch_sessions = {}  # all sessions, ld and md
        self.join_dict = {}
        self.vehicles_base_year = 0
        self.analysis_initial_year = 0
        self.analysis_final_year = 0
        self.calendar_years = 0
        self.cost_accrual = None
        self.discount_values_to_year = 0
        self.analysis_dollar_basis = 0
        self.context_name_liquid_fuel = None
        self.context_case_liquid_fuel = None
        self.vmt_rebound_rate_ice = None
        self.vmt_rebound_rate_bev = None
        self.vmt_rebound_post_frm = False
        self.net_benefit_ghg_scope = 'global'  # default value; change via batch file ('domestic' and 'both' are options)

        self.inputs_filelist = []
        self.inputs_filelist_fleet = []
        self.maintenance_costs_file = None
        self.repair_costs_file = None
        self.refueling_costs_file = None
        self.general_inputs_for_effects_file = None
        self.criteria_cost_factors_file = None
        self.scghg_cost_factors_file = None
        self.energy_security_cost_factors_file = None
        self.congestion_noise_cost_factors_file = None
        self.insurance_and_taxes_cost_factors_file = None
        self.legacy_fleet_file = None

        self.context_fuel_prices_file = None
        self.context_stock_and_vmt_file = None
        self.context_electricity_consumption_file = None
        self.onroad_fuels_file = None
        self.onroad_vehicle_calculations_file = None
        self.onroad_vmt_file = None
        self.vehicle_reregistration_file = None
        self.ip_deflators_file = None
        self.cpi_deflators_file = None

        self.egu_data_file = None
        self.refinery_data_file = None
        self.safety_values_file = None
        self.fatality_rates_file = None

        self.context_session_name = None

        self.maintenance_cost = None
        self.repair_cost = None
        self.refueling_cost = None
        self.general_inputs_for_effects = None
        self.criteria_cost_factors = None
        self.scghg_cost_factors = None
        self.energy_security_cost_factors = None
        self.congestion_noise_cost_factors = None
        self.insurance_and_taxes_cost_factors = None

        self.context_fuel_prices = None
        self.context_electricity_consumption = None
        self.onroad_vmt = None
        self.reregistration = None
        self.context_stock_and_vmt = None
        self.onroad_fuels = None
        self.context_fuel_cost_per_mile = None
        self.legacy_fleet = None
        self.legacy_fleet_fc_adjustment = None
        self.ip_deflators = None
        self.cpi_deflators = None

        self.egu_data = None
        self.refinery_data = None
        self.safety_values = None
        self.fatality_rates = None

        self.legacy_vs_analysis = None

        self.gwp_ch4 = None
        self.gwp_n2o = None

        self.fleets = None
        self.sessions_to_run = None
        self.sessions_completed = []
        self.joins_max = 0
        self.fleet_dict = {
            'LD': 'ld',
            'Light-duty': 'ld',
            'Lightduty': 'ld',
            'light-duty': 'ld',
            'lightduty': 'ld',
            'MD': 'md',
            'Medium-duty': 'md',
            'Mediumduty': 'md',
            'medium-duty': 'md',
            'mediumduty': 'md',
            'LMDV': 'lmdv',
            'LDMD': 'lmdv',
            'ldmd': 'lmdv',
        }

        self.true_false_dict = {
            True: True,
            False: False,
            'True': True,
            'False': False,
            'TRUE': True,
            'FALSE': False,
            'None': None,
            'Yes': True,
            'yes': True,
            'YES': True,
            'Y': True,
            'y': True,
            'No': False,
            'no': False,
            'NO': False,
            'N': False,
            'n': False,
            np.nan: None
        }

    def init_from_file(self, filepath):
        """

        Args:
            filepath: the Path object to the file.

        """
        self.branch_name = self.get_git_branch_name()
        self.set_runtime_info()

        input_template_columns = [
            'fleet',
            'parameter',
            'session_policy',
            'value',
            'full_path',
        ]
        df = read_input_file(filepath, usecols=lambda x: 'notes' not in x)

        validate_template_column_names(filepath, df, input_template_columns)

        self.batch_df = df.copy()

        fleet_entries = df['fleet'].unique()
        for fleet_entry in fleet_entries:
            if fleet_entry in self.fleet_dict:
                df['fleet'] = df['fleet'].replace({fleet_entry: self.fleet_dict[fleet_entry]})

        key = pd.Series(zip(
            df['fleet'],
            df['parameter'],
            df['session_policy']
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        save_path_string = self._dict[('lmdv', 'Save Path', 'all')]['full_path']

        self.path_outputs = Path(save_path_string)

    def get_attribute_value(self, key, attribute_name):
        """

        Args:
            key (tuple): the applicable dictionary key
            attribute_name (str): the name of the parameter to read

        Returns:
            The attribute value as set in the batch file. Path attributes will be returned as Path objects.

        """
        if key in self._dict:
            attribute_value = self._dict[key][attribute_name]
        else:
            return None
        if attribute_value in self.true_false_dict:
            attribute_value = self.true_false_dict[attribute_value]
            return attribute_value
        if attribute_name == 'full_path':
            attribute_value = Path(attribute_value)

        return attribute_value

    def get_compliance_results_batch_deets(self, fleet):
        """

        Args:
            fleet (str): e.g., 'ld', 'md'.

        Returns:
            Nothing, but it sets the compliance results batch folder full path (as a string) and sets the batch name.

        """
        self.batch_folder = self.get_attribute_value((fleet, 'batch_folder', 'all'), 'full_path')
        self.batch_name = Path(self.batch_folder).name
        self.vehicles_base_year \
            = pd.to_numeric(self.get_attribute_value((fleet, 'Vehicles File Base Year', 'all'), 'value'))

    def set_calendar_year_range(self, fleet):
        """

        Args:
            fleet (str): e.g., 'lmdv'.

        Returns:
            Nothing, but it sets the compliance results batch folder full path (as a string) and sets the batch name.

        """
        self.analysis_initial_year = self.vehicles_base_year + 1
        self.analysis_final_year \
            = pd.to_numeric(self.get_attribute_value((fleet, 'Analysis Final Year', 'all'), 'value'))
        self.calendar_years = range(self.analysis_initial_year, self.analysis_final_year + 1)

    def get_run_id(self, fleet):
        """

        Args:
            fleet (str): e.g., 'lmdv'.

        Returns:
            Nothing, but sets the run_id to the user entry, if provided, otherwise use default value.

        """
        self.run_id = self.get_attribute_value((fleet, 'Run ID', 'all'), 'value')
        if self.run_id is None:
            self.run_id = 'omega_effects'

    def get_lmdv_batch_settings(self, fleet):
        """

        Args:
            fleet (str): e.g., 'lmdv' or other entry set in batch input file.

        Returns:
             Nothing, but it sets the class attributes included in the class init.

        """
        self.cost_accrual = self.get_attribute_value((fleet, 'Cost Accrual', 'all'), 'value')
        self.discount_values_to_year = (
            pd.to_numeric(self.get_attribute_value((fleet, 'Discount Values to Year', 'all'), 'value'))
        )
        self.analysis_dollar_basis = (
            pd.to_numeric(self.get_attribute_value((fleet, 'Analysis Dollar Basis', 'all'), 'value'))
        )
        self.vmt_rebound_rate_ice = (
            pd.to_numeric(self.get_attribute_value((fleet, 'VMT Rebound Rate ICE', 'all'), 'value'))
        )
        self.vmt_rebound_rate_bev = (
            pd.to_numeric(self.get_attribute_value((fleet, 'VMT Rebound Rate BEV', 'all'), 'value'))
        )
        self.vmt_rebound_post_frm = (
            self.get_attribute_value((fleet, 'VMT Rebound post-FRM', 'all'), 'value')
        )

        self.context_name_liquid_fuel = self.get_attribute_value((fleet, 'Context Name Liquid Fuel', 'all'), 'value')
        self.context_case_liquid_fuel = self.get_attribute_value((fleet, 'Context Case Liquid Fuel', 'all'), 'value')

        self.net_benefit_ghg_scope = self.get_attribute_value((fleet, 'SC-GHG in Net Benefits', 'all'), 'value')

        self.maintenance_costs_file = self.get_attribute_value((fleet, 'Maintenance Costs File', 'all'), 'full_path')
        self.repair_costs_file = self.get_attribute_value((fleet, 'Repair Costs File', 'all'), 'full_path')
        self.refueling_costs_file = self.get_attribute_value((fleet, 'Refueling Costs File', 'all'), 'full_path')
        self.general_inputs_for_effects_file \
            = self.get_attribute_value((fleet, 'General Inputs for Effects File', 'all'), 'full_path')
        self.criteria_cost_factors_file \
            = self.get_attribute_value((fleet, 'Criteria Cost Factors File', 'all'), 'full_path')
        self.scghg_cost_factors_file \
            = self.get_attribute_value((fleet, 'SCGHG Cost Factors File', 'all'), 'full_path')
        self.energy_security_cost_factors_file \
            = self.get_attribute_value((fleet, 'Energy Security Cost Factors File', 'all'), 'full_path')
        self.congestion_noise_cost_factors_file \
            = self.get_attribute_value((fleet, 'Congestion-Noise Cost Factors File', 'all'), 'full_path')
        self.insurance_and_taxes_cost_factors_file \
            = self.get_attribute_value((fleet, 'Insurance and Taxes Cost Factors File', 'all'), 'full_path')
        self.ip_deflators_file = self.get_attribute_value((fleet, 'Implicit Price Deflators File', 'all'), 'full_path')
        self.cpi_deflators_file = self.get_attribute_value((fleet, 'CPI Price Deflators File', 'all'), 'full_path')
        self.context_electricity_consumption_file = self.get_attribute_value(
            (fleet, 'Context Electricity Consumption File', 'all'), 'full_path'
        )

        # Get effects-specific files from appropriate folder as specified in batch_settings.csv.
        self.egu_data_file \
            = self.get_attribute_value((fleet, 'EGU Data File', 'all'), 'full_path')
        self.refinery_data_file \
            = self.get_attribute_value((fleet, 'Refinery Data File', 'all'), 'full_path')
        self.safety_values_file \
            = self.get_attribute_value((fleet, 'Safety Values File', 'all'), 'full_path')
        self.fatality_rates_file \
            = self.get_attribute_value((fleet, 'Fatality Rates File', 'all'), 'full_path')

    def get_fleet_batch_settings(self, fleet, effects_log):
        """

        Args:
            fleet (str): e.g., 'ld' or 'md'
            effects_log: an instance fo the EffectsLog class.

        Returns:
             Nothing, but it sets the class attributes included in the class init.

        """
        self.legacy_fleet_file = self.get_attribute_value((fleet, 'Legacy Fleet File', 'all'), 'full_path')

        self.legacy_fleet_fc_adjustment = LegacyFleetFuelConsumptionAdjustment()

        self.context_session_name = self.get_attribute_value((fleet, 'Session Name', 'context'), 'value')
        path_context_in = self.batch_folder / f'_{self.context_session_name}' / 'in'

        self.context_stock_and_vmt_file = \
            self.get_attribute_value((fleet, 'Context Stock and VMT File', 'context'), 'full_path')

        self.batch_sessions[fleet] = {}
        self.batch_sessions[fleet][0] = {
            'session_policy': 'no_action',
            'session_name': self.get_attribute_value((fleet, 'Session Name', 'no_action'), 'value'),
        }
        for session_num in range(1, 8):
            session_name = self.get_attribute_value((fleet, 'Session Name', f'action_{session_num}'), 'value')
            if session_name:
                self.batch_sessions[fleet][session_num] = {
                    'session_policy': f'action_{session_num}',
                    'session_name': self.get_attribute_value((fleet, 'Session Name', f'action_{session_num}'), 'value')
                }
        if self.batch_sessions[fleet][0]['session_name']:
            pass
        else:
            effects_log.logwrite(f'\n *** Must have a no_action session name  for {fleet} ***')
            sys.exit()
        if not self.batch_sessions[fleet][1]['session_name']:
            effects_log.logwrite(f'\n *** Must have an action_1 session name for {fleet} ***')
            sys.exit()

        find_string = 'context_fuel_prices'
        try:
            self.context_fuel_prices_file = self.find_file(path_context_in, find_string, effects_log)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} not found or {path_context_in} does not contain a {find_string} file.')
            sys.exit()

        find_string = 'onroad_fuels'
        try:
            self.onroad_fuels_file = self.find_file(path_context_in, find_string, effects_log)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} not found or {path_context_in} does not contain a {find_string} file.')
            sys.exit()

        find_string = 'onroad_vehicle_calculations'
        try:
            self.onroad_vehicle_calculations_file = self.find_file(path_context_in, find_string, effects_log)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} not found or {path_context_in} does not contain a {find_string} file.')
            sys.exit()

        find_string = 'annual_vmt'
        try:
            self.onroad_vmt_file = self.find_file(path_context_in, find_string, effects_log)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} not found or {path_context_in} does not contain a {find_string} file.')
            sys.exit()

        find_string = 'reregistration'
        try:
            self.vehicle_reregistration_file = self.find_file(path_context_in, find_string, effects_log)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} not found or {path_context_in} does not contain a {find_string} file.')
            sys.exit()

    def get_join_settings(self):
        """

        Returns:
            Nothing, but it builds the class join_dict for use in joining ld and md sessions into lmdv results.

        """
        for fleet in self.fleets:
            self.joins_max = max(self.joins_max, len(self.batch_sessions[fleet]))
        for join_num in range(1, self.joins_max):
            for fleet in self.fleets:
                session_name = self.get_attribute_value((fleet, f'join_{join_num}', f'action_{join_num}'), 'value')
                self.join_dict[fleet, join_num] = {
                    'session_policy': f'action_{join_num}',
                    'session_name': session_name,
                }

    def init_batch_classes(self, effects_log):
        """

        Args:
            effects_log: an instance of the EffectsLog class.

        Returns:
             Nothing, but it creates instances of classes needed for the batch.

        """
        effects_log.logwrite('\nInitializing classes used for all effects')

        try:
            # deflator classes must come first so that subsequent classes can do dollar adjustments
            self.ip_deflators = ImplicitPriceDeflators()
            self.ip_deflators.init_from_file(self.ip_deflators_file, effects_log)
            self.inputs_filelist.append(self.ip_deflators_file)

            self.cpi_deflators = CPIPriceDeflators()
            self.cpi_deflators.init_from_file(self.cpi_deflators_file, effects_log)
            self.inputs_filelist.append(self.cpi_deflators_file)

            self.maintenance_cost = MaintenanceCost()
            self.maintenance_cost.init_from_file(self.maintenance_costs_file, self, effects_log)
            self.inputs_filelist.append(self.maintenance_costs_file)

            self.repair_cost = RepairCost()
            self.repair_cost.init_from_file(self.repair_costs_file, effects_log)
            self.inputs_filelist.append(self.repair_costs_file)

            self.refueling_cost = RefuelingCost()
            self.refueling_cost.init_from_file(self.refueling_costs_file, self, effects_log)
            self.inputs_filelist.append(self.refueling_costs_file)

            self.general_inputs_for_effects = GeneralInputsForEffects()
            self.general_inputs_for_effects.init_from_file(self.general_inputs_for_effects_file, effects_log)
            self.inputs_filelist.append(self.general_inputs_for_effects_file)

            self.criteria_cost_factors = CostFactorsCriteria()
            self.criteria_cost_factors.init_from_file(self.criteria_cost_factors_file, self, effects_log)
            self.inputs_filelist.append(self.criteria_cost_factors_file)

            self.scghg_cost_factors = CostFactorsSCGHG()
            self.scghg_cost_factors.init_from_file(self.scghg_cost_factors_file, self, effects_log)
            self.inputs_filelist.append(self.scghg_cost_factors_file)

            self.energy_security_cost_factors = CostFactorsEnergySecurity()
            self.energy_security_cost_factors.init_from_file(self.energy_security_cost_factors_file, self, effects_log)
            self.inputs_filelist.append(self.energy_security_cost_factors_file)

            self.congestion_noise_cost_factors = CostFactorsCongestionNoise()
            self.congestion_noise_cost_factors.init_from_file(self.congestion_noise_cost_factors_file, self, effects_log)
            self.inputs_filelist.append(self.congestion_noise_cost_factors_file)

            self.insurance_and_taxes_cost_factors = InsuranceAndTaxes()
            self.insurance_and_taxes_cost_factors.init_from_file(
                self.insurance_and_taxes_cost_factors_file, self, effects_log
            )
            self.inputs_filelist.append(self.insurance_and_taxes_cost_factors_file)

            self.egu_data = EGUdata()
            self.egu_data.init_from_file(self.egu_data_file, effects_log)
            self.inputs_filelist.append(self.egu_data_file)

            self.refinery_data = RefineryData()
            self.refinery_data.init_from_file(self, self.refinery_data_file, effects_log)
            self.inputs_filelist.append(self.refinery_data_file)

            self.safety_values = SafetyValues()
            self.safety_values.init_from_file(self.safety_values_file, effects_log)
            self.inputs_filelist.append(self.safety_values_file)

            self.fatality_rates = FatalityRates()
            self.fatality_rates.init_from_file(self.fatality_rates_file, effects_log)
            self.inputs_filelist.append(self.fatality_rates_file)

            # determine what module to use for context electricity consumption
            module_name = get_module_name(self.context_electricity_consumption_file, effects_log)
            self.context_electricity_consumption = importlib.import_module(
                module_name, package=None
            ).ContextElectricityConsumption()
            self.context_electricity_consumption.init_from_file(
                self.context_electricity_consumption_file, self, effects_log
            )
            self.inputs_filelist.append(self.context_electricity_consumption_file)

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()

    def init_fleet_batch_classes(self, fleet, effects_log):
        """

        Args:
            fleet (str): e.g., 'ld' or 'md'
            effects_log: an instance of the EffectsLog class.

        Returns:
             Nothing, but it creates instances of classes needed for the batch.

        """
        effects_log.logwrite(f'\nInitializing {fleet}-specific batch classes')

        try:
            self.context_fuel_prices = FuelPrice()
            self.context_fuel_prices.init_from_file(self.context_fuel_prices_file, self, effects_log)
            self.inputs_filelist_fleet.append(self.context_fuel_prices_file)

            self.reregistration = Reregistration()
            self.reregistration.init_from_file(self.vehicle_reregistration_file, effects_log)
            self.inputs_filelist_fleet.append(self.vehicle_reregistration_file)

            self.onroad_vmt = OnroadVMT()
            self.onroad_vmt.init_from_file(self.onroad_vmt_file, effects_log)
            self.inputs_filelist_fleet.append(self.onroad_vmt_file)

            self.onroad_fuels = OnroadFuel()
            self.onroad_fuels.init_from_file(self.onroad_fuels_file, effects_log)
            self.inputs_filelist_fleet.append(self.onroad_fuels_file)

            self.legacy_fleet = LegacyFleet()
            self.legacy_fleet.init_from_file(self.legacy_fleet_file, self.analysis_initial_year, effects_log)
            self.inputs_filelist_fleet.append(self.legacy_fleet_file)

            self.context_stock_and_vmt = ContextStockVMT()
            self.context_stock_and_vmt.init_from_file(self.context_stock_and_vmt_file, self, effects_log)
            self.inputs_filelist_fleet.append(self.context_stock_and_vmt_file)

            self.legacy_vs_analysis = LegacyVsAnalysisFleet()

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()

    @staticmethod
    def find_file(folder, file_id_string, effects_log, identifier=None):
        """

        Args:
            folder: Path object of folder in which to find the file.
            file_id_string (str): The search string in the filename needed.
            effects_log: An instance of the EffectsLog class.
            identifier (str): e.g., 'ld' or 'md' for use in the join process.

        Returns:
            A Path object to the first file found that contains file_id_string in its name.

        """
        if identifier:
            file_id_string = file_id_string + f'_{identifier}'
        files_in_folder = (entry for entry in folder.iterdir() if entry.is_file())
        for file in files_in_folder:
            filename = Path(file).name
            if file_id_string in filename:
                return Path(file)
        effects_log.logwrite(message=f'File {file_id_string} in folder {folder}......  *** NOT FOUND ***. ')

    def get_runtime_options(self, fleet, effects_log):
        """

        Parameters:
            fleet (str): e.g., 'lmdv'
            effects_log: object; an object of the ToolLog class.

        Returns:
            creates a dictionary and other attributes specified in the class __init__.

        """
        effects_log.logwrite(f'Run ID is {self.run_id}')

        string_id = 'Sessions to Run'
        self.sessions_to_run = self._dict[(np.nan, string_id, np.nan)]['value']
        self.fleets = [self.sessions_to_run]
        if self.fleets == ['lmdv']:
            self.fleets = ['ld', 'md']
        effects_log.logwrite(f'{string_id} is {self.sessions_to_run}')

        string_id = 'Save Context Fuel Cost per Mile File'
        self.save_context_fuel_cost_per_mile_file = self._dict[(fleet, string_id, 'all')]['value']
        if self.save_context_fuel_cost_per_mile_file in self.true_false_dict:
            self.save_context_fuel_cost_per_mile_file = self.true_false_dict[self.save_context_fuel_cost_per_mile_file]
            effects_log.logwrite(
                f'{string_id} is {self.save_context_fuel_cost_per_mile_file}')

        string_id = 'Save Vehicle-Level Safety Effects Files'
        self.save_vehicle_safety_effects_files = self._dict[(fleet, string_id, 'all')]['value']
        if self.save_vehicle_safety_effects_files in self.true_false_dict:
            self.save_vehicle_safety_effects_files = self.true_false_dict[self.save_vehicle_safety_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_safety_effects_files}')

        string_id = 'Save Vehicle-Level Physical Effects Files'
        self.save_vehicle_physical_effects_files = self._dict[(fleet, string_id, 'all')]['value']
        if self.save_vehicle_physical_effects_files in self.true_false_dict:
            self.save_vehicle_physical_effects_files = self.true_false_dict[self.save_vehicle_physical_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_physical_effects_files}')

        string_id = 'Save Vehicle-Level Cost Effects Files'
        self.save_vehicle_cost_effects_files = self._dict[(fleet, string_id, 'all')]['value']
        if self.save_vehicle_cost_effects_files in self.true_false_dict:
            self.save_vehicle_cost_effects_files = self.true_false_dict[self.save_vehicle_cost_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_cost_effects_files}')

        try:
            # protect against NaN or empty string
            string_id = 'Format for Vehicle-Level Output Files'
            self.file_format = self._dict[(fleet, string_id, 'all')]['value'].lower()
            if self.save_vehicle_safety_effects_files \
                    or self.save_vehicle_physical_effects_files \
                    or self.save_vehicle_cost_effects_files:
                effects_log.logwrite(f'{string_id} is {self.file_format}')
        except Exception as e:
            effects_log.logwrite(
                '\nVehicle-Level Output File Save Format in RUNTIME OPTIONS must be "csv" or "parquet"')
            effects_log.logwrite(e)
            sys.exit()

        if self.file_format not in ['csv', 'parquet']:
            # protect against improper save format
            effects_log.logwrite(
                '\nVehicle-Level Output File Save Format in RUNTIME OPTIONS must be "csv" or "parquet"')
            sys.exit()

        string_id = 'Save Input Files'
        self.save_input_files = self._dict[(fleet, string_id, 'all')]['value']
        if self.save_input_files in self.true_false_dict:
            self.save_input_files = self.true_false_dict[self.save_input_files]
            effects_log.logwrite(f'{string_id} is {self.save_input_files}')

        string_id = 'Powertrain Costs FEV'
        self.powertrain_costs_fev = self._dict[(fleet, string_id, 'all')]['value']
        if self.powertrain_costs_fev in self.true_false_dict:
            self.powertrain_costs_fev = self.true_false_dict[self.powertrain_costs_fev]
            effects_log.logwrite(f'{string_id} is {self.powertrain_costs_fev}')

        string_id = 'Run Employment Analysis Costs'
        self.run_employment_analysis_costs = self._dict[(fleet, string_id, 'all')]['value']
        if self.run_employment_analysis_costs in self.true_false_dict:
            self.run_employment_analysis_costs = self.true_false_dict[self.run_employment_analysis_costs]
            effects_log.logwrite(f'{string_id} is {self.run_employment_analysis_costs}')
            if self.sessions_to_run != 'lmdv':
                effects_log.logwrite(f'\nSessions to Run must be "lmdv" to {string_id} so Employment Analysis Costs will not be run.')

        string_id = 'Use Marginal EGU Rates'
        self.marginal_egu_rates = self._dict[(fleet, string_id, 'all')]['value']
        if self.marginal_egu_rates in self.true_false_dict:
            self.marginal_egu_rates = self.true_false_dict[self.marginal_egu_rates]
            effects_log.logwrite(f'{string_id} is {self.marginal_egu_rates}')

    @staticmethod
    def path_of_effects_batch_settings_csv():
        """

        Returns:
            An open-file dialog to select the batch settings file to use.

        Note:
            This method allows for a user-interactive means of selecting the desired batch settings file.

        """
        # set full path to the batch settings file
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()

        path_identifier = filedialog.askopenfilename(title='Select the effects batch settings CSV file')

        path_of_csv = Path(path_identifier)

        return path_of_csv

    def set_runtime_info(self):
        """

        Returns:
            Nothing, but it sets the runtime_info for display in the terminal or console and in the effects_messages
            log file to indicate whether the run used the executable (PyInstaller bundle) or a normal Python process.

        """
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.runtime_info = \
                f'Running in a PyInstaller bundle, OMEGA effects package {self.effects_package_version}'
        else:
            if self.branch_name:
                self.runtime_info = \
                    f'Running in a normal Python process, OMEGA effects package {self.effects_package_version}, Current branch {self.branch_name}'
            else:
                self.runtime_info = \
                    f'Running in a normal Python process, OMEGA effects package {self.effects_package_version}'

    @staticmethod
    def get_git_branch_name():
        """

        Returns:
            Name of current Git branch if running code maintained in a Git repository, else None.

        """
        try:
            branch_name = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('utf-8').strip()
            return branch_name
        except subprocess.CalledProcessError:
            return None
