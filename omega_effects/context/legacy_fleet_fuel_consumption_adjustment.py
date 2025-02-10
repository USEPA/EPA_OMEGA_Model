from omega_effects.general.general_functions import calc_electricity_consumption


class LegacyFleetFuelConsumptionAdjustment:

    def __init__(self):
        self.data = {}
        self.adjustment_factors = {}
        self.fuels = []
        self.gasoline_name = None
        self.diesel_name = None
        self.electricity_name = None

    def calc_analysis_start_year_fuel_consumption(self, batch_settings, session_settings):

        vehicle_attribute_list = [
            'model_year',
            'in_use_fuel_id',
            'fueling_class',
            'onroad_direct_co2e_grams_per_mile',
            'onroad_direct_kwh_per_mile',
            '_initial_registered_count',
            'onroad_engine_on_distance_frac',
        ]

        calendar_year = batch_settings.analysis_initial_year
        model_year = batch_settings.analysis_initial_year

        # new vehicles in the analysis initial year
        vads = session_settings.vehicle_annual_data.get_vehicle_annual_data_by_calendar_year(model_year)

        vehicle_info_dict = {}
        for v in vads:

            vehicle_id = v['vehicle_id']

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

            (model_year, in_use_fuel_id, fueling_class, onroad_direct_co2e_grams_per_mile, onroad_direct_kwh_per_mile,
             registered_count, onroad_engine_on_distance_frac) \
                = vehicle_info_dict[vehicle_id]

            fuel_dict = eval(in_use_fuel_id)
            fuel = [item for item in fuel_dict][0]

            if fueling_class != 'BEV' and onroad_direct_co2e_grams_per_mile > 0:

                if not self.gasoline_name and 'gasoline' in fuel:
                    self.gasoline_name = fuel
                if not self.diesel_name and 'diesel' in fuel:
                    self.diesel_name = fuel

                co2_emissions_grams_per_unit = \
                    batch_settings.onroad_fuels.get_fuel_attribute(
                        calendar_year, fuel, 'direct_co2e_grams_per_unit'
                    )
                onroad_gallons_per_mile = onroad_direct_co2e_grams_per_mile / co2_emissions_grams_per_unit
                fuel_consumption_gallons = v['vmt'] * onroad_gallons_per_mile

                if ('new', fuel) in self.data:
                    self.data['new', fuel] = self.data['new', fuel] + fuel_consumption_gallons
                else:
                    self.data['new', fuel] = fuel_consumption_gallons

            if fueling_class == 'BEV' and onroad_direct_kwh_per_mile > 0:

                self.electricity_name = fuel
                fuel_consumption_kwh, fuel_generation_kwh, evse_kwh_per_mile = calc_electricity_consumption(
                    batch_settings, v, onroad_direct_kwh_per_mile
                )

                if ('new', fuel) in self.data:
                    self.data['new', fuel] = self.data['new', fuel] + fuel_consumption_kwh
                else:
                    self.data['new', fuel] = fuel_consumption_kwh

        # legacy fleet vehicles
        vads = [
            v for v in batch_settings.legacy_fleet.adjusted_legacy_fleet.values() if v['calendar_year'] == calendar_year
        ]
        for v in vads:

            fuel_dict = eval(v['in_use_fuel_id'])
            fuel = [item for item in fuel_dict][0]

            if v['miles_per_gallon'] != 0:

                onroad_miles_per_gallon = v['miles_per_gallon']

                fuel_consumption_gallons = v['vmt'] / onroad_miles_per_gallon

                if ('legacy', fuel) in self.data:
                    self.data['legacy', fuel] = self.data['legacy', fuel] + fuel_consumption_gallons
                else:
                    self.data['legacy', fuel] = fuel_consumption_gallons

            if v['kwh_per_mile'] != 0:

                onroad_direct_kwh_per_mile = v['kwh_per_mile']

                fuel_consumption_kwh, fuel_generation_kwh, evse_kwh_per_mile = calc_electricity_consumption(
                    batch_settings, v, onroad_direct_kwh_per_mile
                )

                if ('legacy', fuel) in self.data:
                    self.data['legacy', fuel] = self.data['legacy', fuel] + fuel_consumption_kwh
                else:
                    self.data['legacy', fuel] = fuel_consumption_kwh

    def calc_adjustments(self, batch_settings, fleet):
        """

        Args:
            batch_settings: An instance of the BatchSettings class.
            fleet (str): e.g., 'ld', 'md'

        Returns:
            Nothing, but it builds the fuel consumption adjustment factors Class dictionary.

        """
        calendar_year = batch_settings.analysis_initial_year
        gal_per_bbl = batch_settings.general_inputs_for_effects.get_value('gal_per_bbl')

        args_gasoline = [
            'retail_gasoline_million_barrels_per_day',
            'context_scaler_lmdv_car_gasoline',
            'context_scaler_lmdv_truck_gasoline',
            'context_scaler_lmdv_mediumduty_gasoline',
            'context_scaler_lmdv_gasoline'
        ]
        args_diesel = [
            'diesel_million_barrels_per_day',
            'context_scaler_lmdv_car_diesel',
            'context_scaler_lmdv_truck_diesel',
            'context_scaler_lmdv_mediumduty_diesel',
            'context_scaler_lmdv_diesel'
        ]
        context_gasoline, gasoline_car_scaler, gasoline_truck_scaler, gasoline_md_scaler, gasoline_lmdv_scaler = (
            batch_settings.refinery_data.get_data(calendar_year, None, None, *args_gasoline)
        )
        context_diesel, diesel_car_scaler, diesel_truck_scaler, diesel_md_scaler, diesel_lmdv_scaler = (
            batch_settings.refinery_data.get_data(calendar_year, None, None, *args_diesel)
        )
        context_electricity, fleet_share = batch_settings.context_electricity_consumption.get_attribute_value(
            calendar_year, fleet
        )

        context_gasoline_gallons = context_gasoline * gal_per_bbl * 365 * pow(10, 6)
        context_diesel_gallons = context_diesel * gal_per_bbl * 365 * pow(10, 6)

        if fleet == 'ld':
            context_gasoline_consumption = (
                    context_gasoline_gallons * gasoline_lmdv_scaler * (gasoline_car_scaler + gasoline_truck_scaler)
            )
            context_diesel_consumption = (
                    context_diesel_gallons * diesel_lmdv_scaler * (diesel_car_scaler + diesel_truck_scaler)
            )
        else:
            context_gasoline_consumption = (
                    context_gasoline_gallons * gasoline_lmdv_scaler * gasoline_md_scaler
            )
            context_diesel_consumption = (
                    context_diesel_gallons * diesel_lmdv_scaler * diesel_md_scaler
            )

        context_electricity_consumption = context_electricity * fleet_share

        gasoline_adjustment = diesel_adjustment = electricity_adjustment = 1

        if ('legacy', self.gasoline_name) in self.data and self.data['legacy', self.gasoline_name] != 0:
            gasoline_adjustment = self.calc_adjustment(context_gasoline_consumption, self.gasoline_name)

        if ('legacy', self.diesel_name) in self.data and self.data['legacy', self.diesel_name] != 0:
            diesel_adjustment = self.calc_adjustment(context_diesel_consumption, self.diesel_name)

        if ('legacy', self.electricity_name) in self.data and self.data['legacy', self.electricity_name] != 0:
            electricity_adjustment = self.calc_adjustment(context_electricity_consumption, self.electricity_name)

        self.adjustment_factors = {
            self.gasoline_name: gasoline_adjustment,
            self.diesel_name: diesel_adjustment,
            self.electricity_name: electricity_adjustment,
        }

    def calc_adjustment(self, context_consumption, fuel_name):
        """

        Args:
            context_consumption (float): consumption from the context for the given fuel_name
            fuel_name (str): the name of the fuel for which to calculate an adjustment

        Returns:
            A factor to be applied to legacy fleet consumption to be consistent with the context

        """
        adjustment = (context_consumption - self.data['new', fuel_name]) / self.data['legacy', fuel_name]

        return adjustment
