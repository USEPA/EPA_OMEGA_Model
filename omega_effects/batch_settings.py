"""

**OMEGA effects batch settings.**

----

**CODE**

"""
import sys
import tkinter as tk
from tkinter import filedialog
import numpy as np
import pandas as pd
from pathlib import Path

from omega_effects.general.general_functions import read_input_file
from omega_effects.context.ip_deflators import ImplicitPriceDeflators
from omega_effects.context.cpi_price_deflators import CPIPriceDeflators
from omega_effects.effects.cost_factors_criteria import CostFactorsCriteria
from omega_effects.effects.cost_factors_scghg import CostFactorsSCGHG
from omega_effects.effects.cost_factors_energysecurity import CostFactorsEnergySecurity
from omega_effects.effects.cost_factors_congestion_noise import CostFactorsCongestionNoise
from omega_effects.effects.legacy_fleet import LegacyFleet
from omega_effects.effects.egu_data import EGUdata
from omega_effects.effects.refinery_data import RefineryData
from omega_effects.effects.safety_values import SafetyValues
from omega_effects.effects.fatality_rates import FatalityRates

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
from omega_effects.general.input_validation import validate_template_column_names  #, get_module_name


class BatchSettings:
    """

    Settings that apply to the whole batch of effects to run.

    """
    def __init__(self):
        self.effects_package_version = '2023.12.0'
        self.runtime_info = None
        self.batch_df = pd.DataFrame()
        self.batch_program = None
        self.batch_folder = None
        self.batch_name = None
        self.run_id = 'omega_effects'

        # runtime options set via batch settings file
        self.file_format = None
        self.path_outputs = None
        self.save_context_fuel_cost_per_mile_file = None
        self.save_vehicle_safety_effects_files = None
        self.save_vehicle_physical_effects_files = None
        self.save_vehicle_cost_effects_files = None
        self.save_input_files = False
        self.powertrain_costs_fev = True

        self._dict = {}
        self.session_dict = {}
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
        self.net_benefit_ghg_scope = 'global'  # default value; change via batch file ('domestic' and 'both' are options)

        self.inputs_filelist = []
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
        self.electricity_prices_source = None
        self.onroad_vmt = None
        self.reregistration = None
        self.context_stock_and_vmt = None
        self.onroad_fuels = None
        self.context_fuel_cost_per_mile = None
        self.legacy_fleet = None
        self.ip_deflators = None
        self.cpi_deflators = None

        self.egu_data = None
        self.refinery_data = None
        self.safety_values = None
        self.fatality_rates = None

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
        self.set_runtime_info()

        input_template_columns = [
            'parameter',
            'session_policy',
            'value',
            'full_path'
        ]
        df = read_input_file(filepath, usecols=lambda x: 'notes' not in x)

        validate_template_column_names(filepath, df, input_template_columns)

        self.batch_df = df.copy()

        key = pd.Series(zip(
            df['parameter'],
            df['session_policy']
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        save_path_string = self._dict[('Save Path', 'all')]['full_path']

        self.path_outputs = Path(save_path_string)

    def get_attribute_value(self, key, attribute_name):
        """

        Args:
            key (tuple): the applicable dictionary key
            attribute_name (str): the name of the parameter to read

        Returns:
            The attribute value as set in the batch file. Path attributes will be returned as Path objects.

        """
        attribute_value = self._dict[key][attribute_name]
        if attribute_value in self.true_false_dict:
            attribute_value = self.true_false_dict[attribute_value]
            return attribute_value
        if attribute_name == 'full_path':
            attribute_value = Path(attribute_value)

        return attribute_value

    def get_batch_folder_and_name(self):
        """

        Returns:
            Nothing, but it sets the batch folder full path (as a string) and sets the batch name.

        """
        self.batch_folder = self.get_attribute_value(('batch_folder', 'all'), 'full_path')
        self.batch_name = Path(self.batch_folder).name

    def get_run_id(self):
        """

        Returns:
            Nothing, but sets the run_id to the user entry, if provided, otherwise use default value.

        """
        run_id = self.get_attribute_value(('Run ID', 'all'), 'value')
        if run_id != '':
            self.run_id = run_id

    def get_batch_settings(self, effects_log):
        """

        Args:
            effects_log: an instance fo the EffectsLog class.

        Returns:
             Nothing, but it sets the class attributes included in the class init.

        """
        self.vehicles_base_year \
            = pd.to_numeric(self.get_attribute_value(('Vehicles File Base Year', 'all'), 'value'))
        self.analysis_initial_year = self.vehicles_base_year + 1
        self.analysis_final_year \
            = pd.to_numeric(self.get_attribute_value(('Analysis Final Year', 'all'), 'value'))
        self.cost_accrual = self.get_attribute_value(('Cost Accrual', 'all'), 'value')
        self.discount_values_to_year \
            = pd.to_numeric(self.get_attribute_value(('Discount Values to Year', 'all'), 'value'))
        self.calendar_years = range(self.analysis_initial_year, self.analysis_final_year + 1)
        self.analysis_dollar_basis \
            = pd.to_numeric(self.get_attribute_value(('Analysis Dollar Basis', 'all'), 'value'))
        self.vmt_rebound_rate_ice \
            = pd.to_numeric(self.get_attribute_value(('VMT Rebound Rate ICE', 'all'), 'value'))
        self.vmt_rebound_rate_bev \
            = pd.to_numeric(self.get_attribute_value(('VMT Rebound Rate BEV', 'all'), 'value'))

        self.context_name_liquid_fuel = self.get_attribute_value(('Context Name Liquid Fuel', 'all'), 'value')
        self.context_case_liquid_fuel = self.get_attribute_value(('Context Case Liquid Fuel', 'all'), 'value')
        self.electricity_prices_source = self.get_attribute_value(('Electricity Prices', 'all'), 'value')

        self.net_benefit_ghg_scope = self.get_attribute_value(('SC-GHG in Net Benefits', 'all'), 'value')

        self.maintenance_costs_file = self.get_attribute_value(('Maintenance Costs File', 'all'), 'full_path')
        self.repair_costs_file = self.get_attribute_value(('Repair Costs File', 'all'), 'full_path')
        self.refueling_costs_file = self.get_attribute_value(('Refueling Costs File', 'all'), 'full_path')
        self.general_inputs_for_effects_file \
            = self.get_attribute_value(('General Inputs for Effects File', 'all'), 'full_path')
        self.criteria_cost_factors_file \
            = self.get_attribute_value(('Criteria Cost Factors File', 'all'), 'full_path')
        self.scghg_cost_factors_file \
            = self.get_attribute_value(('SCGHG Cost Factors File', 'all'), 'full_path')
        self.energy_security_cost_factors_file \
            = self.get_attribute_value(('Energy Security Cost Factors File', 'all'), 'full_path')
        self.congestion_noise_cost_factors_file \
            = self.get_attribute_value(('Congestion-Noise Cost Factors File', 'all'), 'full_path')
        self.insurance_and_taxes_cost_factors_file \
            = self.get_attribute_value(('Insurance and Taxes Cost Factors File', 'all'), 'full_path')
        self.legacy_fleet_file = self.get_attribute_value(('Legacy Fleet File', 'all'), 'full_path')
        self.cpi_deflators_file = self.get_attribute_value(('CPI Price Deflators File', 'all'), 'full_path')

        # Get effects-specific files from appropriate folder as specified in batch_settings.csv.
        self.egu_data_file \
            = self.get_attribute_value(('EGU Data File', 'all'), 'full_path')
        self.refinery_data_file \
            = self.get_attribute_value(('Refinery Data File', 'all'), 'full_path')
        self.safety_values_file \
            = self.get_attribute_value(('Safety Values File', 'all'), 'full_path')
        self.fatality_rates_file \
            = self.get_attribute_value(('Fatality Rates File', 'all'), 'full_path')

        self.context_session_name = self.get_attribute_value(('Session Name', 'context'), 'value')
        path_context_in = self.batch_folder / f'_{self.context_session_name}' / 'in'

        self.context_stock_and_vmt_file = \
            self.get_attribute_value(('Context Stock and VMT File', 'context'), 'full_path')

        find_string = find_string_e = None
        try:
            find_string = 'implicit_price_deflators'
            self.ip_deflators_file = self.find_file(path_context_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} does not contain a {find_string} file.')
            sys.exit()

        try:
            find_string = 'context_fuel_prices'
            self.context_fuel_prices_file = self.find_file(path_context_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} does not contain a {find_string} file.')
            sys.exit()

        try:
            find_string = 'onroad_fuels'
            self.onroad_fuels_file = self.find_file(path_context_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} does not contain a {find_string} file.')
            sys.exit()

        try:
            find_string = 'onroad_vehicle_calculations'
            self.onroad_vehicle_calculations_file = self.find_file(path_context_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} does not contain a {find_string} file.')
            sys.exit()

        try:
            find_string = 'annual_vmt'
            self.onroad_vmt_file = self.find_file(path_context_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} does not contain a {find_string} file.')
            sys.exit()

        try:
            find_string = 'reregistration'
            self.vehicle_reregistration_file = self.find_file(path_context_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_context_in} does not contain a {find_string} file.')
            sys.exit()

        self.session_dict[0] = {'session_policy': 'no_action',
                                'session_name': self.get_attribute_value(('Session Name', 'no_action'), 'value'),
                                }
        for session_num in range(1, 8):
            session_name = self.get_attribute_value(('Session Name', f'action_{session_num}'), 'value')
            if session_name:
                self.session_dict[session_num] = {
                    'session_policy': f'action_{session_num}',
                    'session_name': self.get_attribute_value(('Session Name', f'action_{session_num}'), 'value')
                }

        if self.session_dict[0]['session_name']:
            pass
        else:
            effects_log.logwrite('\n *** Must have a no_action session name ***')
            sys.exit()
        if len(self.session_dict) < 2:
            effects_log.logwrite('\n *** Must have an action_1 session name ***')
            sys.exit()

    def init_batch_classes(self, effects_log):
        """

        Args:
            effects_log: an instance of the EffectsLog class.

        Returns:
             Nothing, but it creates instances of classes needed for the batch.

        """
        effects_log.logwrite('\nInitializing batch')

        try:
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

            self.context_fuel_prices = FuelPrice()
            self.context_fuel_prices.init_from_file(self.context_fuel_prices_file, self, effects_log)
            self.inputs_filelist.append(self.context_fuel_prices_file)

            self.reregistration = Reregistration()
            self.reregistration.init_from_file(self.vehicle_reregistration_file, effects_log)
            self.inputs_filelist.append(self.vehicle_reregistration_file)

            self.onroad_vmt = OnroadVMT()
            self.onroad_vmt.init_from_file(self.onroad_vmt_file, effects_log)
            self.inputs_filelist.append(self.onroad_vmt_file)

            self.onroad_fuels = OnroadFuel()
            self.onroad_fuels.init_from_file(self.onroad_fuels_file, effects_log)
            self.inputs_filelist.append(self.onroad_fuels_file)

            self.legacy_fleet = LegacyFleet()
            self.legacy_fleet.init_from_file(self.legacy_fleet_file, self.vehicles_base_year, effects_log)
            self.inputs_filelist.append(self.legacy_fleet_file)

            self.context_stock_and_vmt = ContextStockVMT()
            self.context_stock_and_vmt.init_from_file(self.context_stock_and_vmt_file, self, effects_log)
            self.inputs_filelist.append(self.context_stock_and_vmt_file)

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

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()

    def return_session_policy(self, session_name):
        """

        Args:
            session_name (str): the name of a give session.

        Returns:
            The session_policy (e.g., 'no_action', 'action_1') for the given session_name.

        """
        session_policy = \
            [v['session_policy'] for k, v in self.session_dict.items() if v['session_name'] == session_name]

        return session_policy[0]

    @staticmethod
    def find_file(folder, file_id_string):
        """

        Args:
            folder: Path object of folder in which to find the file.
            file_id_string (str): The search string in the filename needed.

        Returns:
            A Path object to the first file found that contains file_id_string in its name.

        """
        files_in_folder = (entry for entry in folder.iterdir() if entry.is_file())
        for file in files_in_folder:
            filename = Path(file).name
            if file_id_string in filename:
                return Path(file)

    def get_runtime_options(self, effects_log):
        """

        Parameters:
            effects_log: object; an object of the ToolLog class.

        Returns:
            creates a dictionary and other attributes specified in the class __init__.

        """
        effects_log.logwrite(f'Run ID is {self.run_id}')
        effects_log.logwrite(f'Batch folder is {self.batch_folder}')
        effects_log.logwrite(f'Batch name is {self.batch_name}')

        string_id = 'Save Context Fuel Cost per Mile File'
        self.save_context_fuel_cost_per_mile_file = self._dict[(string_id, 'all')]['value']
        if self.save_context_fuel_cost_per_mile_file in self.true_false_dict:
            self.save_context_fuel_cost_per_mile_file = self.true_false_dict[self.save_context_fuel_cost_per_mile_file]
            effects_log.logwrite(
                f'{string_id} is {self.save_context_fuel_cost_per_mile_file}')

        string_id = 'Save Vehicle-Level Safety Effects Files'
        self.save_vehicle_safety_effects_files = self._dict[(string_id, 'all')]['value']
        if self.save_vehicle_safety_effects_files in self.true_false_dict:
            self.save_vehicle_safety_effects_files = self.true_false_dict[self.save_vehicle_safety_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_safety_effects_files}')

        string_id = 'Save Vehicle-Level Physical Effects Files'
        self.save_vehicle_physical_effects_files = self._dict[(string_id, 'all')]['value']
        if self.save_vehicle_physical_effects_files in self.true_false_dict:
            self.save_vehicle_physical_effects_files = self.true_false_dict[self.save_vehicle_physical_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_physical_effects_files}')

        string_id = 'Save Vehicle-Level Cost Effects Files'
        self.save_vehicle_cost_effects_files = self._dict[(string_id, 'all')]['value']
        if self.save_vehicle_cost_effects_files in self.true_false_dict:
            self.save_vehicle_cost_effects_files = self.true_false_dict[self.save_vehicle_cost_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_cost_effects_files}')

        try:
            # protect against NaN or empty string
            string_id = 'Format for Vehicle-Level Output Files'
            self.file_format = self._dict[(string_id, 'all')]['value'].lower()
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
        self.save_input_files = self._dict[(string_id, 'all')]['value']
        if self.save_input_files in self.true_false_dict:
            self.save_input_files = self.true_false_dict[self.save_input_files]
            effects_log.logwrite(f'{string_id} is {self.save_input_files}')

        string_id = 'Powertrain Costs FEV'
        self.powertrain_costs_fev = self._dict[(string_id, 'all')]['value']
        if self.powertrain_costs_fev in self.true_false_dict:
            self.powertrain_costs_fev = self.true_false_dict[self.powertrain_costs_fev]
            effects_log.logwrite(f'{string_id} is {self.powertrain_costs_fev}')

    @staticmethod
    def path_of_batch_settings_csv():
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

        path_identifier = filedialog.askopenfilename(title='Select the batch settings CSV file')

        path_of_csv = Path(path_identifier)

        return path_of_csv

    def set_runtime_info(self):

        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            self.runtime_info = \
                f'Running in a PyInstaller bundle, OMEGA effects package {self.effects_package_version}'
        else:
            self.runtime_info = \
                f'Running in a normal Python process, OMEGA effects package {self.effects_package_version}'
