"""

**OMEGA effects session settings.**

----

**CODE**

"""

import sys
from pathlib import Path

from omega_effects.effects_code.effects.vehicles import Vehicles
from omega_effects.effects_code.effects.vehicle_annual_data import VehicleAnnualData

from omega_effects.effects_code.effects.emission_rates_egu import EmissionRatesEGU
from omega_effects.effects_code.effects.emission_factors_refinery import EmissionFactorsRefinery
from omega_effects.effects_code.effects.emission_rates_refinery import EmissionRatesRefinery
from omega_effects.effects_code.effects.emission_rates_vehicles import EmissionRatesVehicles
from omega_effects.effects_code.effects.safety_values import SafetyValues
from omega_effects.effects_code.effects.fatality_rates import FatalityRates
from omega_effects.effects_code.context.powertrain_cost import PowertrainCost


class SessionSettings:
    """

    OMEGA effects SessionSettings class.

    """
    def __init__(self):
        self.session_policy = None
        self.session_name = None

        self.inputs_filelist = list()
        self.powersector_emission_rates_file = None
        self.refinery_emission_factors_file = None
        self.refinery_emission_rates_file = None
        self.vehicle_emission_rates_file = None
        self.safety_values_file = None
        self.fatality_rates_file = None
        self.powertrain_cost_file = None

        self.vehicles_file = None
        self.vehicle_annual_data_file = None

        self.emission_rates_egu = None
        self.emission_factors_refinery = None
        self.emission_rates_refinery = None
        self.emission_rates_vehicles = None
        self.safety_values = None
        self.fatality_rates = None
        self.powertrain_cost = None

        self.vehicles = None
        self.vehicle_annual_data = None

    def get_context_session_settings(self, batch_settings, effects_log):
        """

        This method is used to generate a context fuel cost per mile file if one is not provided in batch_settings.csv

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

        self.vehicles_file \
            = path_session_out / f'{batch_settings.batch_name}_{batch_settings.context_session_name}_vehicles.csv'
        self.vehicle_annual_data_file \
            = path_session_out / f'{batch_settings.batch_name}_{batch_settings.context_session_name}_vehicle_annual_data.csv'

        self.init_context_classes(effects_log)

    def get_session_settings(self, batch_settings, session_num, effects_log):
        """
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
        self.vehicles_file \
            = path_session_out / f'{batch_settings.batch_name}_{self.session_name}_vehicles.csv'
        self.vehicle_annual_data_file \
            = path_session_out / f'{batch_settings.batch_name}_{self.session_name}_vehicle_annual_data.csv'

        # Get effects-specific files from appropriate folder as specified in batch_settings.csv.
        self.powersector_emission_rates_file \
            = batch_settings.get_attribute_value(('Context Powersector Emission Rates File', f'{self.session_policy}'), 'full_path')

        try:
            self.refinery_emission_factors_file \
                = batch_settings.get_attribute_value(('Context Refinery Emission Factors File', f'{self.session_policy}'), 'full_path')
        except Exception as e:
            effects_log.logwrite(f'Refinery Emission Factors file not used, {e}')
        try:
            self.refinery_emission_rates_file \
                = batch_settings.get_attribute_value(('Context Refinery Emission Rates File', f'{self.session_policy}'), 'full_path')
        except Exception as e:
            effects_log.logwrite(f'Refinery Emission Rates file not used, {e}')

        self.vehicle_emission_rates_file \
            = batch_settings.get_attribute_value(('Context Vehicle Emission Rates File', f'{self.session_policy}'), 'full_path')
        self.safety_values_file \
            = batch_settings.get_attribute_value(('Context Safety Values File', f'{self.session_policy}'), 'full_path')
        self.fatality_rates_file \
            = batch_settings.get_attribute_value(('Context Fatality Rates File', f'{self.session_policy}'), 'full_path')

        find_string = None
        try:
            find_string = 'powertrain_cost'
            self.powertrain_cost_file = self.find_file(path_session_in, find_string)
        except FileNotFoundError:
            effects_log(f'{path_session_in} does not contain a {find_string} file.')
            sys.exit()

        self.init_session_classes(self.session_name, effects_log)

    def init_context_classes(self, effects_log):
        """

        Args:
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

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()

    def init_session_classes(self, session_name, effects_log):
        """

        Args:
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

            self.emission_rates_egu = EmissionRatesEGU()
            self.emission_rates_egu.init_from_file(self.powersector_emission_rates_file, effects_log)
            self.inputs_filelist.append(self.powersector_emission_rates_file)

            if self.refinery_emission_factors_file:
                self.emission_factors_refinery = EmissionFactorsRefinery()
                self.emission_factors_refinery.init_from_file(self.refinery_emission_factors_file, effects_log)
                self.inputs_filelist.append(self.refinery_emission_factors_file)
            else:
                self.emission_rates_refinery = EmissionRatesRefinery()
                self.emission_rates_refinery.init_from_file(self.refinery_emission_rates_file, effects_log)
                self.inputs_filelist.append(self.refinery_emission_rates_file)

            self.emission_rates_vehicles = EmissionRatesVehicles()
            self.emission_rates_vehicles.init_from_file(self.vehicle_emission_rates_file, effects_log)
            self.inputs_filelist.append(self.vehicle_emission_rates_file)

            self.safety_values = SafetyValues()
            self.safety_values.init_from_file(self.safety_values_file, effects_log)
            self.inputs_filelist.append(self.safety_values_file)

            self.fatality_rates = FatalityRates()
            self.fatality_rates.init_from_file(self.fatality_rates_file, effects_log)
            self.inputs_filelist.append(self.fatality_rates_file)

            self.powertrain_cost = PowertrainCost()
            self.powertrain_cost.init_from_file(self.powertrain_cost_file, effects_log)
            self.inputs_filelist.append(self.powertrain_cost_file)

        except Exception as e:
            effects_log.logwrite(e)
            sys.exit()

    @staticmethod
    def find_file(folder, file_id_string):
        """

        Args:
            folder:
            file_id_string:

        Returns:

        """
        files_in_folder = (entry for entry in folder.iterdir() if entry.is_file())
        for file in files_in_folder:
            filename = Path(file).name
            if file_id_string in filename:
                return Path(file)
