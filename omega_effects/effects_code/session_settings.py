"""

**OMEGA effects session settings.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row header followed by subsequent data rows.

The data represents OMEGA effects session settings.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       parameter,session_policy,value,full_path

Sample Data Rows
    .. csv-table::
        :widths: auto

        Batch Settings,,,,
        batch_folder,all,,omega/runs/2023_03_14_22_42_30_central_3alts_20230314,
        Vehicles File Base Year,all,2021,,this should be consistent with the OMEGA compliance run
        Analysis Final Year,all,2055,,this should be <= the value used in the OMEGA compliance run
        Cost Accrual,all,end-of-year,,
        Discount Values to Year,all,2027,,
        Analysis Dollar Basis,all,2020,,
        Batch Analysis Context Settings,,,,
        Context Name,all,AEO2021,,
        Context Case,all,Reference case,,
        VMT Rebound Rate ICE,all,-0.1,,
        VMT Rebound Rate BEV,all,0,,
        SC-GHG in Net Benefits,all,both,,"enter 'global' or 'domestic' or 'both' (note that both global and domesitc benefits are calculated, this only impacts net benefits)"
        Maintenance Costs File,all,,omega/inputs/master_all/effects/maintenance_cost.csv,
        Repair Costs File,all,,omega/inputs/master_all/effects/repair_cost.csv,
        Refueling Costs File,all,,omega/inputs/master_all/effects/refueling_cost.csv,
        General Inputs for Effects File,all,,omega/inputs/master_all/effects/general_inputs_for_effects.csv,
        Context Criteria Cost Factors File,all,,omega/inputs/master_all/effects/cost_factors_criteria.csv,
        Context SCC Cost Factors File,all,,omega/inputs/master_all/effects/cost_factors_scc_global_domestic_2020.csv,
        Context Energy Security Cost Factors File,all,,omega/inputs/master_all/effects/cost_factors_energysecurity.csv,
        Context Congestion-Noise Cost Factors File,all,,omega/inputs/master_all/effects/cost_factors_congestion_noise.csv,
        Context Legacy Fleet File,all,,omega/inputs/master_all/effects/legacy_fleet.csv,
        blank,,,,
        Session Name,context,SAFE,,
        Context Stock and VMT File,context,,omega/inputs/master_all/effects/context_stock_vmt.csv,
        blank0,,,,
        Session Name,no_action,NTR,,
        Context Powersector Emission Rates File,no_action,,omega/inputs/master_all/effects/emission_rates_egu.csv,
        Context Refinery Emission Rates File,no_action,,omega/inputs/master_all/effects/emission_rates_refinery.csv,
        Context Refinery Emission Factors File,no_action,,,
        Context Vehicle Emission Rates File,no_action,,omega/inputs/master_all/effects/emission_rates_vehicles-no_gpf.csv,
        Context Safety Values File,no_action,,omega/inputs/master_all/effects/safety_values.csv,
        Context Fatality Rates File,no_action,,omega/inputs/master_all/effects/fatality_rates.csv,

Data Row Name and Description

:batch_folder:
    Pathname of the batch bundle folder to run effects on

:Vehicles File Base Year:
    The intended model year of the base year vehicles file, should be consistent with the OMEGA compliance run

:Analysis Final Year:
    The final effects year, should be <= the value used in the OMEGA compliance run

:Cost Accrual:
    The time of year when costs are assumed to accrue, ``end-of-year`` or ``beginning-of-year``

:Discount Values to Year:
    The year to which all monetized values in the cost effects outputs will be discounted

:Analysis Dollar Basis:
    The dollar valuation for all monetized values in the cost effects outputs, i.e., costs are expressed in "Dollar Basis" dollars

:Batch Analysis Context Settings:
    Decorator, not evaluated

:Context Name *(str)*:
    Context name, e.g. ``AEO2021``

:VMT Rebound Rate ICE:
    VMT rebound rate for internal combustion engines

:VMT Rebound Rate BEV:
    VMT rebound rate for battery-electric vehicles

:SC-GHG in Net Benefits *(str)*:
    'global' or 'domestic' or 'both' (note that both global and domesitc benefits are calculated, this only impacts net benefits)

:Maintenance Costs File *(str)*:
    The relative or absolute path to the maintenance cost inputs file,
    loaded by ``context.maintenance_cost.MaintenanceCost``

:Repair Costs File *(str)*:
    The relative or absolute path to the repair cost inputs file,
    loaded by ``context.repair_cost.RepairCost``

:Refueling Costs File *(str)*:
    The relative or absolute path to the refueling cost inputs file,
    loaded by ``context.refueling_cost.RefuelingCost``

:General Inputs for Effects File *(str)*:
    The relative or absolute path to the general inputs used for effects calculations,
    loaded by ``general.general_inputs_for_effects.GeneralInputsForEffects``

:Context Criteria Cost Factors File *(str)*:
    The relative or absolute path to the criteria pollutant costs file,
    loaded by ``effects.cost_factors_criteria.CostFactorsCriteria``

:Context SCC Cost Factors File *(str)*:
    The relative or absolute path to the social cost of carbon and carbon-equivalent pollutants file,
    loaded by ``effects.cost_factors_scc.CostFactorsSCC``

:Context Energy Security Cost Factors File *(str)*:
    The relative or absolute path to the energy security cost factors file,
    loaded by ``effects.cost_factors_energysecurity.CostFactorsEnergySecurity``

:Context Congestion-Noise Cost Factors File *(str)*:
    The relative or absolute path to the congestion and noise cost factors file,
    loaded by ``effects.cost_factors_congestion_noise.CostFactorsCongestionNoise``

:Context Legacy Fleet File *(str)*:
    The relative or absolute path to the legacy fleet file,
    loaded by ``effects.legacy_fleet.LegacyFleet``

**Context session settings.**

:Context Stock and VMT File:
    Context Stock and VMT File

**Per-session settings.**

:Context Powersector Emission Rates File *(str)*:
    The relative or absolute path to the power sector emission rates file,
    loaded by ``effects.emission_rates_egu.EmissionRatesEGU``

:Context Refinery Emission Rates File:
    The relative or absolute path to the refinery emission Rates file,
    loaded by ``effects.emission_rates_refinery.EmissionRatesRefinery``

:Context Refinery Emission Factors File *(str)*:
    The relative or absolute path to the refinery emission factors file,
    loaded by ``effects.emission_factors_refinery.EmissionFactorsRefinery``

:Context Vehicle Emission Rates File *(str)*:
    The relative or absolute path to the vehicle emission rates file,
    loaded by ``effects.emission_rates_vehicles.EmissionRatesVehicles``

:Context Safety Values File *(str)*:
    The relative or absolute path to the safety values file,
    loaded by ``effects.safety_values.SafetyValues``

:Context Fatality Rates File *(str)*:
    The relative or absolute path to the fatality rates file,
    loaded by ``effects.fatality_rates.FatalityRates``

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
