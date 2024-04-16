

class LegacyFleetFuelConsumptionAdjustment:

    def __init__(self):
        self.data = {}
        self.adjustment_factors = {}
        self.fuels = []

    def calc_analysis_start_year_fuel_consumption(self, batch_settings, session_settings):

        vehicle_attribute_list = [
            'model_year',
            'in_use_fuel_id',
            'fueling_class',
            'onroad_direct_co2e_grams_per_mile',
            '_initial_registered_count',
            'onroad_engine_on_distance_frac',
        ]

        calendar_year = batch_settings.analysis_initial_year
        model_year = batch_settings.analysis_initial_year

        # new vehicles in the analysis initial year
        vads = session_settings.vehicle_annual_data.get_vehicle_annual_data_by_calendar_year(model_year)

        fuel_consumption_gallons = 0
        vehicle_info_dict = {}
        for v in vads:

            vehicle_id = v['vehicle_id']

            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] \
                    = session_settings.vehicles.get_vehicle_attributes(vehicle_id, *vehicle_attribute_list)

            (model_year, in_use_fuel_id, fueling_class, onroad_direct_co2e_grams_per_mile,
             registered_count, onroad_engine_on_distance_frac) \
                = vehicle_info_dict[vehicle_id]

            if fueling_class != 'BEV' and onroad_direct_co2e_grams_per_mile > 0:

                fuel_dict = eval(in_use_fuel_id)
                fuel = [item for item in fuel_dict][0]

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

        # legacy fleet vehicles
        vads = [
            v for v in batch_settings.legacy_fleet.adjusted_legacy_fleet.values() if v['calendar_year'] == calendar_year
        ]
        for v in vads:

            if v['miles_per_gallon'] != 0:

                fuel_dict = eval(v['in_use_fuel_id'])
                fuel = [item for item in fuel_dict][0]

                onroad_miles_per_gallon = v['miles_per_gallon'] * 0.8

                fuel_consumption_gallons = v['vmt'] / onroad_miles_per_gallon

                if ('legacy', fuel) in self.data:
                    self.data['legacy', fuel] = self.data['legacy', fuel] + fuel_consumption_gallons
                else:
                    self.data['legacy', fuel] = fuel_consumption_gallons

    def calc_adjustments(self, batch_settings):

        calendar_year = batch_settings.analysis_initial_year

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

        context_gasoline_gallons = context_gasoline * 42 * 365 * pow(10, 6)
        context_diesel_gallons = context_diesel * 42 * 365 * pow(10, 6)

        # TODO provide a control of whether LD or MD
        # fleet_type = 'light_duty'
        fleet_type = 'mediumduty'
        if fleet_type == 'light_duty':
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

        gasoline_adjustment = (
                (context_gasoline_consumption - self.data['new', 'pump gasoline']) / self.data['legacy', 'pump gasoline']
        )
        diesel_adjustment = (
                (context_diesel_consumption - self.data['new', 'pump diesel']) / self.data['legacy', 'pump diesel']
        )

        self.adjustment_factors = {
            'pump gasoline': gasoline_adjustment,
            'pump diesel': diesel_adjustment,
        }
