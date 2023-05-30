"""

**OMEGA effects vehicle annual data module.**

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.general_functions import calc_rebound_effect


class VehicleAnnualData:
    """
    Vehicle annual data class definition

    """
    def __init__(self):
        self._dict = {}
        self.adjusted_vads = []

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log, index_col=0)

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
            Vehicle annual data for the given calendar year.

        """
        return [v for k, v in self._dict.items() if k[1] == calendar_year]

    def get_adjusted_vehicle_annual_data_by_calendar_year(self, calendar_year):
        """
        Get adjusted vehicle annual data by calendar year.

        Args:
            calendar_year (int): the calendar year to retrieve data for

        Returns:
            Adjusted vehicle annual data for the given calendar year.

        """
        return [v for v in self.adjusted_vads if v.calendar_year == calendar_year]
        # return [v for k, v in self.vad_adjusted.items() if k[1] == calendar_year]

    def get_vehicle_annual_data_by_vehicle_id(self, calendar_year, vehicle_id, *attribute_names):
        """
        Get vehicle annual data by vehicle id.

        Args:
            calendar_year (int): the calendar year to retrieve data for
            vehicle_id: vehicle id
            *attribute_names: the attribute names to retrieve

        Returns:
            Vehicle annual data by vehicle id.

        """
        attribute_list = list()
        for attribute_name in attribute_names:
            attribute_list.append(self._dict[(vehicle_id, calendar_year)][attribute_name])
        if len(attribute_list) == 1:
            return attribute_list[0]

        return attribute_list

    def adjust_vad(self, batch_settings, session_settings, vmt_adjustments_session, context_fuel_cpm_list):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            session_settings: an instance of the SessionSettings class.
            vmt_adjustments_session: an instance of the AdjustmentsVMT class.
            context_fuel_cpm_list (list): the list of VehicleCostPerMile class objects for the batch context.

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
        ]
        rebound_rate_ice = batch_settings.vmt_rebound_rate_ice
        rebound_rate_bev = batch_settings.vmt_rebound_rate_bev

        vehicle_info_dict = {}

        calendar_years = batch_settings.calendar_years
        for calendar_year in calendar_years:

            vads = self.get_vehicle_annual_data_by_calendar_year(calendar_year)

            context_vmt_adjustment = vmt_adjustments_session.get_vmt_adjustment(calendar_year)

            for vad in vads:
                if vad['registered_count'] >= 1:

                    # need vehicle info once for each vehicle, not every calendar year for each vehicle
                    vehicle_id = int(vad['vehicle_id'])

                    if vehicle_id not in vehicle_info_dict:
                        vehicle_info_dict[vehicle_id] \
                            = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

                    base_year_vehicle_id, manufacturer_id, model_year, in_use_fuel_id, base_year_powertrain_type, \
                        onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile \
                        = vehicle_info_dict[vehicle_id]

                    # exclude any vehicle_ids that are considered legacy fleet
                    if model_year >= calendar_years[0]:

                        adjusted_vad = AdjustedVehicleAnnualData()

                        age = int(vad['age'])
                        registered_count = vad['registered_count']

                        onroad_kwh_per_mile = onroad_gallons_per_mile = fuel_cpm = 0

                        rebound_rate = rebound_effect = 0
                        fuel_dict = eval(in_use_fuel_id)
                        fuel_flag = 0

                        for fuel, fuel_share in fuel_dict.items():

                            retail_price = \
                                batch_settings.context_fuel_prices.get_fuel_prices(
                                    batch_settings, calendar_year, 'retail_dollars_per_unit', fuel
                                )
                            # calc fuel cost per mile
                            if fuel == 'US electricity' and onroad_direct_kwh_per_mile:
                                onroad_kwh_per_mile += onroad_direct_kwh_per_mile
                                fuel_cpm += onroad_kwh_per_mile * retail_price
                                rebound_rate = rebound_rate_bev
                                fuel_flag += 1

                            elif fuel != 'US electricity' and onroad_direct_co2e_grams_per_mile:
                                refuel_efficiency = \
                                    batch_settings.onroad_fuels.get_fuel_attribute(
                                        calendar_year, fuel, 'refuel_efficiency'
                                    )
                                co2_emissions_grams_per_unit \
                                    = batch_settings.onroad_fuels.get_fuel_attribute(
                                        calendar_year, fuel, 'direct_co2e_grams_per_unit') / refuel_efficiency
                                onroad_gallons_per_mile += \
                                    onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                                fuel_cpm += onroad_gallons_per_mile * retail_price
                                rebound_rate = rebound_rate_ice
                                fuel_flag += 1

                        # get context fuel cost per mile
                        # context_fuel_cpm_dict_key = \
                        #     (int(base_year_vehicle_id), base_year_powertrain_type, int(model_year), age)
                        context_fuel_cpm = \
                            [v.fuel_cost_per_mile for v in context_fuel_cpm_list 
                             if v.base_year_vehicle_id == base_year_vehicle_id 
                             and v.base_year_powertrain_type == base_year_powertrain_type 
                             and v.model_year == model_year 
                             and v.age == age][0]
                        # context_fuel_cpm = context_fuel_cpm_dict[context_fuel_cpm_dict_key]['fuel_cost_per_mile']

                        if fuel_flag == 2:
                            rebound_rate = rebound_rate_ice
                        if context_fuel_cpm > 0:
                            rebound_effect = calc_rebound_effect(context_fuel_cpm, fuel_cpm, rebound_rate)
                        else:
                            rebound_effect = 0

                        vmt = vad['vmt'] * context_vmt_adjustment
                        vmt_rebound = vmt * rebound_effect

                        vmt += vmt_rebound
                        annual_vmt_adjusted = vmt / registered_count
                        annual_vmt_rebound = vmt_rebound / registered_count

                        if age == 0:
                            odometer = annual_vmt_adjusted
                        else:
                            odometer_last_year = [v.odometer for v in self.adjusted_vads
                                                  if v.vehicle_id == vehicle_id
                                                  and v.calendar_year == calendar_year - 1
                                                  and v.age == age - 1][0]
                            odometer = odometer_last_year + annual_vmt_adjusted
                            # odometer_last_year = self.vad_adjusted[(vehicle_id, calendar_year - 1, age - 1)]['odometer']
                            # odometer_adjusted = odometer_last_year + annual_vmt_adjusted

                        adjusted_vad.update_value({
                            'manufacturer_id': manufacturer_id,
                            'vehicle_id': vehicle_id,
                            'age': age,
                            'calendar_year': calendar_year,
                            'registered_count': registered_count,
                            'context_vmt_adjustment': context_vmt_adjustment,
                            'annual_vmt': annual_vmt_adjusted,
                            'annual_vmt_rebound': annual_vmt_rebound,
                            'odometer': odometer,
                            'vmt': vmt,
                            'vmt_rebound': vmt_rebound,
                        })
                        self.adjusted_vads.append(adjusted_vad)
                        # self.vad_adjusted[(vehicle_id, calendar_year, age)] = update_dict


class AdjustedVehicleAnnualData:
    
    def __init__(self):

        self.manufacturer_id = None
        self.vehicle_id = None
        self.age = None
        self.calendar_year = None
        self.registered_count = None
        self.context_vmt_adjustment = None
        self.annual_vmt = None
        self.annual_vmt_rebound = None
        self.odometer = None
        self.vmt = None
        self.vmt_rebound = None

    def update_value(self, update_dict):
        """

        Args:
            update_dict (dict): the class instance attributes as keys along with their values.

        Returns:
            Nothing, but it sets class instance attributes to the values contained in update_dict.

        """
        for k, v in update_dict.items():
            self.__setattr__(k, v)
