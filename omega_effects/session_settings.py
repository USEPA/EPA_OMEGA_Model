"""

**OMEGA effects session settings.**

----

**CODE**

"""
import sys
import importlib
from pathlib import Path

from omega_effects.effects.vehicles import Vehicles
from omega_effects.effects.vehicle_annual_data import VehicleAnnualData
from omega_effects.general.input_validation import get_module_name
from omega_effects.context.electricity_prices import ElectricityPrices
from omega_effects.context.powertrain_cost import PowertrainCost


class SessionSettings:
    """

    OMEGA effects SessionSettings class.

    """
    def __init__(self):
        self.session_policy = None
        self.session_name = None

        self.inputs_filelist = list()
        self.vehicle_emission_rates_file = None
        self.powertrain_cost_file = None

        self.vehicles_file = None
        self.vehicle_annual_data_file = None
        self.electricity_prices_file = None

        self.emission_rates_vehicles = None
        self.powertrain_cost = None

        self.vehicles = None
        self.vehicle_annual_data = None
        self.electricity_prices = None

    def get_context_session_settings(self, batch_settings, effects_log):
        """

        This method is used to establish context session settings as specified in the BatchSettings class

        Args:
            batch_settings: an instance of the BatchSettings class.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but it gets context session settings and creates instances of needed classes for the context.

        """
        self.session_policy = 'context'
        self.session_name = batch_settings.context_session_name
        path_session = batch_settings.batch_folder / f'_{self.session_name}'
        path_session_out = path_session / 'out'

        self.vehicles_file = batch_settings.find_file(
            path_session_out, f'{batch_settings.context_session_name}_vehicles.csv'
        )
        self.vehicle_annual_data_file = batch_settings.find_file(
            path_session_out, f'{batch_settings.context_session_name}_vehicle_annual_data.csv'
        )
        self.electricity_prices_file = batch_settings.get_attribute_value(
            ('Context Electricity Prices', 'context'), 'full_path')

        self.init_context_classes(batch_settings, effects_log)

    def get_session_settings(self, batch_settings, session_num, effects_log):
        """

        This method is used to establish no action and action session settings as specified in the BatchSettings class

        Args:
            batch_settings: an instance of the BatchSettings class.
            session_num (int): the session number.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but it gets no_action and action session settings and creates instances of needed classes for
            the session.

        """
        session_deets = batch_settings.session_dict[session_num]
        self.session_policy, self.session_name = session_deets['session_policy'], session_deets['session_name']
        
        path_session = batch_settings.batch_folder / f'_{self.session_name}'
        path_session_in = path_session / 'in'
        path_session_out = path_session / 'out'

        # Get vehicles_file and vehicle_annual_data_file from the batch/session/out folder.
        self.vehicles_file = batch_settings.find_file(
            path_session_out, f'{self.session_name}_vehicles.csv'
        )
        self.vehicle_annual_data_file = batch_settings.find_file(
            path_session_out, f'{self.session_name}_vehicle_annual_data.csv'
        )
        self.electricity_prices_file = batch_settings.get_attribute_value(
            ('Session Electricity Prices', f'{self.session_policy}'), 'full_path'
        )
        self.vehicle_emission_rates_file = batch_settings.get_attribute_value(
            ('Session Vehicle Emission Rates File', f'{self.session_policy}'), 'full_path'
        )

        find_string = None
        try:
            find_string = 'powertrain_cost'
            self.powertrain_cost_file = batch_settings.find_file(path_session_in, find_string)
        except FileNotFoundError:
            effects_log.logwrite(f'{path_session_in} does not contain a {find_string} file.')
            sys.exit()

        self.init_session_classes(batch_settings, self.session_name, effects_log)

    def init_context_classes(self, batch_settings, effects_log):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but it creates instances of needed classes for the context.

        """
        effects_log.logwrite('\nInitializing context')

        try:
            self.vehicles = Vehicles()
            self.vehicles.init_from_file(self.vehicles_file, effects_log)
            self.inputs_filelist.append(self.vehicles_file)

            self.vehicle_annual_data = VehicleAnnualData()
            self.vehicle_annual_data.init_from_file(self.vehicle_annual_data_file, effects_log)
            self.inputs_filelist.append(self.vehicle_annual_data_file)

            self.electricity_prices = ElectricityPrices()
            self.electricity_prices.init_from_file(
                self.electricity_prices_file, batch_settings, effects_log, context=True
            )
            self.inputs_filelist.append(self.electricity_prices_file)

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()

    def init_session_classes(self, batch_settings, session_name, effects_log):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            session_name (str): the session name.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but it creates instances of needed classes for the session.

        """
        effects_log.logwrite(f'\nInitializing session {session_name}')

        try:
            self.vehicles = Vehicles()
            self.vehicles.init_from_file(self.vehicles_file, effects_log)
            self.inputs_filelist.append(self.vehicles_file)

            self.vehicle_annual_data = VehicleAnnualData()
            self.vehicle_annual_data.init_from_file(self.vehicle_annual_data_file, effects_log)
            self.inputs_filelist.append(self.vehicle_annual_data_file)

            self.electricity_prices = ElectricityPrices()
            self.electricity_prices.init_from_file(
                self.electricity_prices_file, batch_settings, effects_log, self, context=False
            )
            self.inputs_filelist.append(self.electricity_prices_file)

            # determine what module to use for vehicle rates
            module_name = get_module_name(self.vehicle_emission_rates_file, effects_log)
            self.emission_rates_vehicles = importlib.import_module(module_name, package=None).EmissionRatesVehicles()
            self.emission_rates_vehicles.init_from_file(self.vehicle_emission_rates_file, effects_log)
            self.inputs_filelist.append(self.vehicle_emission_rates_file)

            self.powertrain_cost = PowertrainCost()
            self.powertrain_cost.init_from_file(batch_settings, self.powertrain_cost_file, effects_log)
            self.inputs_filelist.append(self.powertrain_cost_file)

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()
