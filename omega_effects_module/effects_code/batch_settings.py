import pandas as pd
import sys
from pathlib import Path

from general.general_functions import read_input_file
from effects.ip_deflators import ImplictPriceDeflators
from effects.cpi_price_deflators import CPIPriceDeflators
from effects.cost_factors_criteria import CostFactorsCriteria
from effects.cost_factors_scc import CostFactorsSCC
from effects.cost_factors_energysecurity import CostFactorsEnergySecurity
from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise
from effects.legacy_fleet import LegacyFleet

from consumer.annual_vmt_fixed_by_age import OnroadVMT
from consumer.reregistration_fixed_by_age import Reregistration

from context.fuel_prices import FuelPrice
from context.context_stock_vmt import ContextStockVMT
from context.onroad_fuels import OnroadFuel
from context.maintenance_cost import MaintenanceCost
from context.repair_cost import RepairCost
from context.refueling_cost import RefuelingCost

from general.general_inputs_for_effects import GeneralInputsForEffects


class BatchSettings:
    """

    Settings that apply to the whole batch of effects to run.

    """

    def __init__(self):
        self.batch_df = pd.DataFrame()
        self.batch_program = None
        self.batch_folder = None
        self.batch_name = None
        self._dict = dict()
        self.session_dict = dict()
        self.analysis_initial_year = 0
        self.analysis_final_year = 0
        self.calendar_years = 0
        self.cost_accrual = None
        self.discount_values_to_year = 0
        self.analysis_dollar_basis = 0
        self.context_name = None
        self.context_case = None
        self.vmt_rebound_rate_ice = None
        self.vmt_rebound_rate_bev = None

        self.maintenance_costs_file = None
        self.repair_costs_file = None
        self.refueling_costs_file = None
        self.general_inputs_for_effects_file = None
        self.criteria_cost_factors_file = None
        self.scc_cost_factors_file = None
        self.energy_security_cost_factors_file = None
        self.congestion_noise_cost_factors_file = None
        self.legacy_fleet_file = None

        self.context_fuel_prices_file = None
        self.context_stock_and_vmt_file = None
        self.onroad_fuels_file = None
        self.onroad_vehicle_calculations_file = None
        self.onroad_vmt_file = None
        self.vehicle_reregistration_file = None
        self.ip_deflators_file = None
        self.cpi_deflators_file = None

        self.context_session_name = None

        self.maintenance_cost = None
        self.repair_cost = None
        self.refueling_cost = None
        self.general_inputs_for_effects = None
        self.criteria_cost_factors = None
        self.scc_cost_factors = None
        self.energy_security_cost_factors = None
        self.congestion_noise_cost_factors = None

        self.context_fuel_prices = None
        self.onroad_vmt = None
        self.reregistration = None
        self.context_stock_and_vmt = None
        self.onroad_fuels = None
        self.context_fuel_cost_per_mile = None
        self.legacy_fleet = None
        self.ip_deflators = None
        self.cpi_deflators = None

        self.true_false_dict = dict({
            True: True,
            False: False,
            'True': True,
            'False': False,
            'TRUE': True,
            'FALSE': False,
            'None': None,
        })

    def init_from_file(self, filepath, effects_log):
        """

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        """
        df = read_input_file(filepath, effects_log, usecols=lambda x: 'Type' not in x)

        self.batch_df = df.copy()

        key = pd.Series(zip(
            df['parameter'],
            df['session_policy']
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

        self.get_batch_settings(effects_log)

        self.init_batch_classes(effects_log)

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

    def get_batch_settings(self, effects_log):
        """

        Args:
            effects_log: an instance fo the EffectsLog class.

        Returns:
             Nothing, but it sets the class attributes included in the class init.

        """
        self.batch_folder = self.get_attribute_value(('batch_folder', 'all'), 'full_path')
        self.batch_name = Path(self.batch_folder).name

        self.analysis_initial_year \
            = pd.to_numeric(self.get_attribute_value(('Analysis Initial Year', 'all'), 'value'))
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

        self.context_name = self.get_attribute_value(('Context Name', 'all'), 'value')
        self.context_case = self.get_attribute_value(('Context Case', 'all'), 'value')

        self.maintenance_costs_file = self.get_attribute_value(('Maintenance Costs File', 'all'), 'full_path')
        self.repair_costs_file = self.get_attribute_value(('Repair Costs File', 'all'), 'full_path')
        self.refueling_costs_file = self.get_attribute_value(('Refueling Costs File', 'all'), 'full_path')
        self.general_inputs_for_effects_file \
            = self.get_attribute_value(('General Inputs for Effects File', 'all'), 'full_path')
        self.criteria_cost_factors_file \
            = self.get_attribute_value(('Context Criteria Cost Factors File', 'all'), 'full_path')
        self.scc_cost_factors_file \
            = self.get_attribute_value(('Context SCC Cost Factors File', 'all'), 'full_path')
        self.energy_security_cost_factors_file \
            = self.get_attribute_value(('Context Energy Security Cost Factors File', 'all'), 'full_path')
        self.congestion_noise_cost_factors_file \
            = self.get_attribute_value(('Context Congestion-Noise Cost Factors File', 'all'), 'full_path')
        self.legacy_fleet_file = self.get_attribute_value(('Context Legacy Fleet File', 'all'), 'full_path')
        self.ip_deflators_file = self.get_attribute_value(('Context Implicit Price Deflators File', 'all'), 'full_path')
        self.cpi_deflators_file = self.get_attribute_value(('Context Consumer Price Index File', 'all'), 'full_path')

        self.context_session_name = self.get_attribute_value(('Session Name', 'context'), 'value')
        self.context_fuel_prices_file = self.get_attribute_value(('Context Fuel Prices File', 'context'), 'full_path')
        self.context_stock_and_vmt_file = self.get_attribute_value(('Context Stock and VMT File', 'context'), 'full_path')
        self.onroad_fuels_file = self.get_attribute_value(('Onroad Fuels File', 'context'), 'full_path')
        self.onroad_vehicle_calculations_file = self.get_attribute_value(('Onroad Vehicle Calculations File', 'context'), 'full_path')
        self.onroad_vmt_file = self.get_attribute_value(('Onroad VMT File', 'context'), 'full_path')
        self.vehicle_reregistration_file = self.get_attribute_value(('Vehicle Reregistration File', 'context'), 'full_path')

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

        if not self.session_dict[0]:
            effects_log.logwrite('Must have a no_action session name')
            sys.exit()
        if not self.session_dict[1]:
            effects_log.logwrite('Must have an action_1 session name')
            sys.exit()

    def init_batch_classes(self, effects_log):
        """

        Args:
            effects_log: an instance fo the EffectsLog class.

        Returns:
             Nothing, but it creates instances of classes needed for the batch.

        """
        effects_log.logwrite('\nInitializing batch')

        try:
            self.ip_deflators = ImplictPriceDeflators()
            self.ip_deflators.init_from_file(self.ip_deflators_file, effects_log)

            self.cpi_deflators = CPIPriceDeflators()
            self.cpi_deflators.init_from_file(self.cpi_deflators_file, effects_log)

            self.maintenance_cost = MaintenanceCost()
            self.maintenance_cost.init_from_file(self.maintenance_costs_file, self, effects_log)

            self.repair_cost = RepairCost()
            self.repair_cost.init_from_file(self.repair_costs_file, effects_log)

            self.refueling_cost = RefuelingCost()
            self.refueling_cost.init_from_file(self.refueling_costs_file, self, effects_log)

            self.general_inputs_for_effects = GeneralInputsForEffects()
            self.general_inputs_for_effects.init_from_file(self.general_inputs_for_effects_file, effects_log)

            self.criteria_cost_factors = CostFactorsCriteria()
            self.criteria_cost_factors.init_from_file(self.criteria_cost_factors_file, self, effects_log)

            self.scc_cost_factors = CostFactorsSCC()
            self.scc_cost_factors.init_from_file(self.scc_cost_factors_file, self, effects_log)

            self.energy_security_cost_factors = CostFactorsEnergySecurity()
            self.energy_security_cost_factors.init_from_file(self.energy_security_cost_factors_file, self, effects_log)

            self.congestion_noise_cost_factors = CostFactorsCongestionNoise()
            self.congestion_noise_cost_factors.init_from_file(self.congestion_noise_cost_factors_file, self, effects_log)
            self.context_fuel_prices = FuelPrice()
            self.context_fuel_prices.init_from_file(self.context_fuel_prices_file, self, effects_log)

            self.reregistration = Reregistration()
            self.reregistration.init_from_file(self.vehicle_reregistration_file, effects_log)

            self.onroad_vmt = OnroadVMT()
            self.onroad_vmt.init_from_file(self.onroad_vmt_file, effects_log)

            self.onroad_fuels = OnroadFuel()
            self.onroad_fuels.init_from_file(self.onroad_fuels_file, effects_log)

            self.legacy_fleet = LegacyFleet()
            self.legacy_fleet.init_from_file(self.legacy_fleet_file, self.analysis_initial_year, effects_log)

            self.context_stock_and_vmt = ContextStockVMT()
            self.context_stock_and_vmt.init_from_file(self.context_stock_and_vmt_file, self, effects_log)

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
