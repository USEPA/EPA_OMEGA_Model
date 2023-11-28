"""

**OMEGA effects vehicle annual data module.**

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.general_functions import calc_rebound_effect, calc_fuel_cost_per_mile


class VehicleAnnualData:
    """
    The VehicleAnnualData class reads the vehicle annual data file resulting from the OMEGA compliance run for a given
    session and adjusts VMT data to account for rebound effects and context expectations that are not applied in the
    OMEGA compliance run.

    """
    def __init__(self):
        self._dict = {}
        self.adjusted_vads = {}

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log)

        key = pd.Series(zip(
            df['vehicle_id'],
            df['calendar_year']
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

    def get_vehicle_annual_data_by_calendar_year(self, calendar_year):
        """
        Get vehicle annual data by calendar year.

        Args:
            calendar_year (int): the calendar year to retrieve data for

        Returns:
            A list of vehicle annual data for the given calendar year.

        """
        return [v for v in self._dict.values() if v['calendar_year'] == calendar_year]

    def get_adjusted_vehicle_annual_data_by_calendar_year(self, calendar_year):
        """
        Get adjusted vehicle annual data by calendar year.

        Args:
            calendar_year (int): the calendar year to retrieve data for

        Returns:
            A list of adjusted vehicle annual data for the given calendar year.

        """
        return [v for v in self.adjusted_vads.values() if v['calendar_year'] == calendar_year]

    def get_vehicle_annual_data_by_vehicle_id(self, calendar_year, vehicle_id, *attribute_names):
        """
        Get vehicle annual data by vehicle id.

        Args:
            calendar_year (int): the calendar year to retrieve data for
            vehicle_id: vehicle id
            *attribute_names: the attribute names to retrieve

        Returns:
            A list or single value of vehicle annual data by vehicle id.

        """
        attribute_list = list()
        for attribute_name in attribute_names:
            attribute_list.append(self._dict[(vehicle_id, calendar_year)][attribute_name])
        if len(attribute_list) == 1:
            return attribute_list[0]

        return attribute_list

    def adjust_vad(self, batch_settings, session_settings, vmt_adjustments_session, context_fuel_cpm_dict):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            session_settings: an instance of the SessionSettings class.
            vmt_adjustments_session: an instance of the AdjustmentsVMT class.
            context_fuel_cpm_dict (dict): the fuel cost per mile dictionary for the batch context.

        Returns:
            The vehicle annual data with adjusted VMT and odometer that adjust for rebound and context VMT expectations.

        """
        vehicle_attribute_list = [
            'base_year_vehicle_id',
            'manufacturer_id',
            'model_year',
            'in_use_fuel_id',
            'base_year_powertrain_type',
            'onroad_direct_co2e_grams_per_mile',
            'onroad_direct_kwh_per_mile',
            'fueling_class',
            'context_size_class',
        ]
        rebound_rate_ice = batch_settings.vmt_rebound_rate_ice
        rebound_rate_bev = batch_settings.vmt_rebound_rate_bev

        vehicle_info_dict = {}

        calendar_years = batch_settings.calendar_years
        for calendar_year in calendar_years:

            vads = self.get_vehicle_annual_data_by_calendar_year(calendar_year)

            # eliminate any adjusted_vads having model_year < the analysis_initial_year
            vads = [v for v in vads if (v['calendar_year'] - v['age']) >= batch_settings.analysis_initial_year]

            context_vmt_adjustment = vmt_adjustments_session.get_vmt_adjustment(calendar_year)

            for v in vads:
                if v['registered_count'] >= 1:
                    age = v['age']
                    # need vehicle info once for each vehicle, not every calendar year for each vehicle
                    vehicle_id = int(v['vehicle_id'])

                    if vehicle_id not in vehicle_info_dict:
                        vehicle_info_dict[vehicle_id] \
                            = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

                    base_year_vehicle_id, manufacturer_id, model_year, in_use_fuel_id, base_year_powertrain_type, \
                        onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile, fueling_class, context_size_class \
                        = vehicle_info_dict[vehicle_id]

                    # onroad_kwh_per_mile = onroad_gallons_per_mile = fuel_cpm = 0
                    rebound_rate = rebound_rate_ice
                    if 'electricity' in in_use_fuel_id:
                        rebound_rate = rebound_rate_bev

                    # calc fuel cost per mile
                    fuel_cost_per_mile = calc_fuel_cost_per_mile(
                        batch_settings, calendar_year, onroad_direct_kwh_per_mile, onroad_direct_co2e_grams_per_mile,
                        in_use_fuel_id
                    )

                    # get context fuel cost per mile
                    cost_per_mile_group = 'nonBEV'
                    if fueling_class == 'BEV':
                        cost_per_mile_group = 'BEV'
                    context_fuel_cpm_dict_key = (cost_per_mile_group, context_size_class, int(model_year), int(age))
                    context_fuel_cpm = context_fuel_cpm_dict[context_fuel_cpm_dict_key]['fuel_cost_per_mile']

                    if context_fuel_cpm > 0:
                        rebound_effect = calc_rebound_effect(context_fuel_cpm, fuel_cost_per_mile, rebound_rate)
                    else:
                        rebound_effect = 0

                    vmt = v['vmt'] * context_vmt_adjustment
                    vmt_rebound = vmt * rebound_effect

                    vmt += vmt_rebound
                    annual_vmt_adjusted = vmt / v['registered_count']
                    annual_vmt_rebound = vmt_rebound / v['registered_count']

                    if v['age'] == 0:
                        odometer = annual_vmt_adjusted
                    else:
                        odometer_last_year = \
                            self.adjusted_vads[(vehicle_id, calendar_year - 1)]['odometer']
                        odometer = odometer_last_year + annual_vmt_adjusted

                    update_dict = {
                        'manufacturer_id': manufacturer_id,
                        'vehicle_id': vehicle_id,
                        'age': v['age'],
                        'calendar_year': calendar_year,
                        'registered_count': v['registered_count'],
                        'context_vmt_adjustment': context_vmt_adjustment,
                        'annual_vmt': annual_vmt_adjusted,
                        'annual_vmt_rebound': annual_vmt_rebound,
                        'odometer': odometer,
                        'vmt': vmt,
                        'vmt_rebound': vmt_rebound,
                    }
                    self.adjusted_vads[(vehicle_id, calendar_year)] = update_dict
