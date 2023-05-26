

class VehiclePhysicalData:
    """

    The VehiclePhysicalData class creates objects containing identifying information and rate information needed to
    calculate physical effects for a given vehicle.

    """
    def __init__(self):

        self.session_policy = None
        self.session_name = None
        self.grams_per_us_ton = 0
        self.grams_per_metric_ton = 0
        self.gal_per_bbl = 0
        self.e0_share = 0
        self.e0_energy_density_ratio = 0
        self.diesel_energy_density_ratio = 0
        self.fuel_reduction_leading_to_reduced_domestic_refining = 0

        self.vehicle_id = None
        self.base_year_vehicle_id = None
        self.manufacturer_id = None
        self.name = None
        self.calendar_year = None
        self.model_year = None
        self.age = None
        self.base_year_reg_class_id = None
        self.reg_class_id = None
        self.context_size_class = None
        self.in_use_fuel_id = None
        self.market_class_id = None
        self.fueling_class = None
        self.base_year_powertrain_type = None
        self.body_style = None
        self.footprint_ft2 = None
        self.workfactor = None
        self.registered_count = None
        self.context_vmt_adjustment = None
        self.annual_vmt = 0
        self.odometer = 0
        self.vmt = 0
        self.annual_vmt_rebound = 0
        self.vmt_rebound = 0
        self.vmt_liquid_fuel = 0
        self.vmt_electricity = 0
        self.battery_kwh = 0
        self.battery_kwh_per_veh = 0
        self.onroad_direct_co2e_grams_per_mile = 0
        self.onroad_direct_kwh_per_mile = 0
        self.onroad_gallons_per_mile = 0
        self.onroad_miles_per_gallon = 0
        self.fuel_consumption_gallons = 0
        self.fuel_consumption_kWh = 0
        self.fuel_generation_kWh = 0

        self.session_fatalities = 0
        self.energy_security_import_factor = 0
        self.energy_density_ratio = 0
        self.pure_share = 0

        self.pm25_brakewear_rate_e = 0
        self.pm25_tirewear_rate_e = 0
        self.pm25_brakewear_rate_l = 0
        self.pm25_tirewear_rate_l = 0
        self.pm25_exh_rate = 0

        self.nmog_exh_rate = 0
        self.nmog_permeation_rate = 0
        self.nmog_venting_rate = 0
        self.nmog_leaks_rate = 0
        self.nmog_refuel_disp_rate = 0
        self.nmog_refuel_spill_rate = 0

        self.co_exh_rate = 0
        self.nox_exh_rate = 0
        self.sox_exh_rate = 0
        self.ch4_exh_rate = 0
        self.n2o_exh_rate = 0

        self.acetaldehyde_exh_rate = 0
        self.acrolein_exh_rate = 0

        self.benzene_exh_rate = 0
        self.benzene_permeation_rate = 0
        self.benzene_venting_rate = 0
        self.benzene_leaks_rate = 0
        self.benzene_refuel_disp_rate = 0
        self.benzene_refuel_spill_rate = 0

        self.ethylbenzene_exh_rate = 0
        self.ethylbenzene_permeation_rate = 0
        self.ethylbenzene_venting_rate = 0
        self.ethylbenzene_leaks_rate = 0
        self.ethylbenzene_refuel_disp_rate = 0
        self.ethylbenzene_refuel_spill_rate = 0

        self.formaldehyde_exh_rate = 0
        self.naphthalene_exh_rate = 0
        self.naphthalene_refuel_spill_rate = 0
        self.butadiene13_exh_rate = 0
        self.pah15_exh_rate = 0

        self.voc_ref_rate = 0
        self.co_ref_rate = 0
        self.nox_ref_rate = 0
        self.pm25_ref_rate = 0
        self.sox_ref_rate = 0
        self.co2_ref_rate = 0
        self.ch4_ref_rate = 0
        self.n2o_ref_rate = 0

        self.voc_egu_rate = 0
        self.co_egu_rate = 0
        self.nox_egu_rate = 0
        self.pm25_egu_rate = 0
        self.sox_egu_rate = 0
        self.co2_egu_rate = 0
        self.ch4_egu_rate = 0
        self.n2o_egu_rate = 0
        self.hcl_egu_rate = 0
        self.hg_egu_rate = 0

    def update_value(self, update_dict):
        """

        Args:
            update_dict (dict): the class instance attributes as keys along with their values.

        Returns:
            Nothing, but it sets class instance attributes to the values contained in update_dict.

        """
        for k, v in update_dict.items():
            self.__setattr__(k, v)

    # 
    # def calc_vehicle_physical_effects(self):
    #     """
    # 
    #     Returns:
    #         A dictionary of physical effects for the given class instance (vehicle).
    # 
    #     """
    #     # calc exhaust and evaporative emissions for liquid fuel operation
    #     factor = self.vmt / self.grams_per_us_ton
    #     pm25_exh_ustons = self.pm25_exh_rate * factor
    #     nmog_exh_ustons = self.nmog_exh_rate * factor
    #     co_exh_ustons = self.co_exh_rate * factor
    #     nox_exh_ustons = self.nox_exh_rate * factor
    #     acetaldehyde_exh_ustons = self.acetaldehyde_exh_rate * factor
    #     acrolein_exh_ustons = self.acrolein_exh_rate * factor
    #     benzene_exh_ustons = self.benzene_exh_rate * factor
    #     ethylbenzene_exh_ustons = self.ethylbenzene_exh_rate * factor
    #     formaldehyde_exh_ustons = self.formaldehyde_exh_rate * factor
    #     naphthalene_exh_ustons = self.naphthalene_exh_rate * factor
    #     butadiene13_exh_ustons = self.butadiene13_exh_rate * factor
    #     pah15_exh_ustons = self.pah15_exh_rate * factor
    # 
    #     factor = self.fuel_consumption_gallons / self.grams_per_us_ton
    #     sox_exh_ustons = self.sox_exh_rate * factor
    #     nmog_evap_ustons = sum([self.nmog_permeation_rate,
    #                             self.nmog_venting_rate,
    #                             self.nmog_leaks_rate,
    #                             self.nmog_refuel_disp_rate,
    #                             self.nmog_refuel_spill_rate]) * factor
    #     benzene_evap_ustons = sum([self.benzene_permeation_rate,
    #                                self.benzene_venting_rate,
    #                                self.benzene_leaks_rate,
    #                                self.benzene_refuel_disp_rate,
    #                                self.benzene_refuel_spill_rate]) * factor
    #     ethylbenzene_evap_ustons = sum([self.ethylbenzene_permeation_rate,
    #                                     self.ethylbenzene_venting_rate,
    #                                     self.ethylbenzene_leaks_rate,
    #                                     self.ethylbenzene_refuel_disp_rate,
    #                                     self.ethylbenzene_refuel_spill_rate]) * factor
    #     naphthalene_evap_ustons = self.naphthalene_refuel_spill_rate * factor
    # 
    #     factor = self.vmt / self.grams_per_metric_ton
    #     ch4_veh_metrictons = self.ch4_exh_rate * factor
    #     n2o_veh_metrictons = self.n2o_exh_rate * factor
    #     co2_veh_metrictons = self.onroad_direct_co2e_grams_per_mile * factor
    # 
    #     # calc vehicle inventories as exhaust plus evap (where applicable)
    #     nmog_veh_ustons = nmog_exh_ustons + nmog_evap_ustons
    #     co_veh_ustons = co_exh_ustons
    #     nox_veh_ustons = nox_exh_ustons
    #     sox_veh_ustons = sox_exh_ustons
    #     acetaldehyde_veh_ustons = acetaldehyde_exh_ustons
    #     acrolein_veh_ustons = acrolein_exh_ustons
    #     benzene_veh_ustons = benzene_exh_ustons + benzene_evap_ustons
    #     ethylbenzene_veh_ustons = ethylbenzene_exh_ustons + ethylbenzene_evap_ustons
    #     formaldehyde_veh_ustons = formaldehyde_exh_ustons
    #     naphthalene_veh_ustons = naphthalene_exh_ustons + naphthalene_evap_ustons
    #     butadiene13_veh_ustons = butadiene13_exh_ustons
    #     pah15_veh_ustons = pah15_exh_ustons
    # 
    #     # calc vehicle pm25 emissions
    #     pm25_brakewear_ustons = \
    #         self.vmt * (self.pm25_brakewear_rate_l + self.pm25_brakewear_rate_e) / self.grams_per_us_ton
    #     pm25_tirewear_ustons = \
    #         self.vmt * (self.pm25_tirewear_rate_l + self.pm25_tirewear_rate_e) / self.grams_per_us_ton
    # 
    #     pm25_veh_ustons = pm25_exh_ustons + pm25_brakewear_ustons + pm25_tirewear_ustons
    # 
    #     # calc upstream emissions for both liquid and electric fuel operation
    #     kwhs, gallons = self.fuel_generation_kWh, self.fuel_consumption_gallons
    #     ref_factor = self.fuel_reduction_leading_to_reduced_domestic_refining
    # 
    #     voc_refinery_ustons = gallons * self.voc_ref_rate * ref_factor / self.grams_per_us_ton
    #     co_refinery_ustons = gallons * self.co_ref_rate * ref_factor / self.grams_per_us_ton
    #     nox_refinery_ustons = gallons * self.nox_ref_rate * ref_factor / self.grams_per_us_ton
    #     pm25_refinery_ustons = gallons * self.pm25_ref_rate * ref_factor / self.grams_per_us_ton
    #     sox_refinery_ustons = gallons * self.sox_ref_rate * ref_factor / self.grams_per_us_ton
    # 
    #     voc_egu_ustons = kwhs * self.voc_egu_rate / self.grams_per_us_ton
    #     co_egu_ustons = kwhs * self.co_egu_rate / self.grams_per_us_ton
    #     nox_egu_ustons = kwhs * self.nox_egu_rate / self.grams_per_us_ton
    #     pm25_egu_ustons = kwhs * self.pm25_egu_rate / self.grams_per_us_ton
    #     sox_egu_ustons = kwhs * self.sox_egu_rate / self.grams_per_us_ton
    #     hcl_egu_ustons = kwhs * self.hcl_egu_rate / self.grams_per_us_ton
    #     hg_egu_ustons = kwhs * self.hg_egu_rate / self.grams_per_us_ton
    # 
    #     voc_upstream_ustons = voc_refinery_ustons + voc_egu_ustons
    #     co_upstream_ustons = co_refinery_ustons + co_egu_ustons
    #     nox_upstream_ustons = nox_refinery_ustons + nox_egu_ustons
    #     pm25_upstream_ustons = pm25_refinery_ustons + pm25_egu_ustons
    #     sox_upstream_ustons = sox_refinery_ustons + sox_egu_ustons
    # 
    #     co2_refinery_metrictons = gallons * self.co2_ref_rate * ref_factor / self.grams_per_metric_ton
    #     ch4_refinery_metrictons = gallons * self.ch4_ref_rate * ref_factor / self.grams_per_metric_ton
    #     n2o_refinery_metrictons = gallons * self.n2o_ref_rate * ref_factor / self.grams_per_metric_ton
    # 
    #     co2_egu_metrictons = kwhs * self.co2_egu_rate / self.grams_per_metric_ton
    #     ch4_egu_metrictons = kwhs * self.ch4_egu_rate / self.grams_per_metric_ton
    #     n2o_egu_metrictons = kwhs * self.n2o_egu_rate / self.grams_per_metric_ton
    # 
    #     co2_upstream_metrictons = co2_refinery_metrictons + co2_egu_metrictons
    #     ch4_upstream_metrictons = ch4_refinery_metrictons + ch4_egu_metrictons
    #     n2o_upstream_metrictons = n2o_refinery_metrictons + n2o_egu_metrictons
    # 
    #     # sum vehicle and upstream into totals
    #     voc_total_ustons = voc_upstream_ustons  # + voc_tailpipe_ustons
    #     nmog_total_ustons = nmog_veh_ustons  # + nmog_upstream_ustons
    #     co_total_ustons = co_veh_ustons + co_upstream_ustons
    #     nox_total_ustons = nox_veh_ustons + nox_upstream_ustons
    #     pm25_total_ustons = pm25_veh_ustons + pm25_upstream_ustons
    #     sox_total_ustons = sox_veh_ustons + sox_upstream_ustons
    #     acetaldehyde_total_ustons = acetaldehyde_veh_ustons  # + acetaldehyde_upstream_ustons
    #     acrolein_total_ustons = acrolein_veh_ustons  # + acrolein_upstream_ustons
    #     benzene_total_ustons = benzene_veh_ustons  # + benzene_upstream_ustons
    #     ethylbenzene_total_ustons = ethylbenzene_veh_ustons  # + ethylbenzene_upstream_ustons
    #     formaldehyde_total_ustons = formaldehyde_veh_ustons  # + formaldehyde_upstream_ustons
    #     naphthalene_total_ustons = naphthalene_veh_ustons  # + naphlathene_upstream_ustons
    #     butadiene13_total_ustons = butadiene13_veh_ustons  # + butadiene13_upstream_ustons
    #     pah15_total_ustons = pah15_veh_ustons  # + pah15_upstream_ustons
    #     co2_total_metrictons = co2_veh_metrictons + co2_upstream_metrictons
    #     ch4_total_metrictons = ch4_veh_metrictons + ch4_upstream_metrictons
    #     n2o_total_metrictons = n2o_veh_metrictons + n2o_upstream_metrictons
    # 
    #     # calc energy security related attributes and comparisons to year_for_compares
    #     oil_bbl = self.fuel_consumption_gallons * self.pure_share * self.energy_density_ratio / self.gal_per_bbl
    #     imported_oil_bbl = oil_bbl * self.energy_security_import_factor
    #     imported_oil_bbl_per_day = imported_oil_bbl / 365
    # 
    #     results_dict = {
    #         'session_policy': self.session_policy,
    #         'session_name': self.session_name,
    #         'vehicle_id': self.vehicle_id,
    #         'base_year_vehicle_id': self.base_year_vehicle_id,
    #         'manufacturer_id': self.manufacturer_id,
    #         'name': self.name,
    #         'calendar_year': int(self.calendar_year),
    #         'model_year': self.calendar_year - self.age,
    #         'age': self.age,
    #         'base_year_reg_class_id': self.base_year_reg_class_id,
    #         'reg_class_id': self.reg_class_id,
    #         'context_size_class': self.context_size_class,
    #         'in_use_fuel_id': self.in_use_fuel_id,
    #         'market_class_id': self.market_class_id,
    #         'fueling_class': self.fueling_class,
    #         'base_year_powertrain_type': self.base_year_powertrain_type,
    #         'body_style': self.body_style,
    #         'footprint_ft2': self.footprint_ft2,
    #         'workfactor': self.workfactor,
    #         'registered_count': self.registered_count,
    #         'context_vmt_adjustment': self.context_vmt_adjustment,
    #         'annual_vmt': self.annual_vmt,
    #         'odometer': self.odometer,
    #         'vmt': self.vmt,
    #         'annual_vmt_rebound': self.annual_vmt_rebound,
    #         'vmt_rebound': self.vmt_rebound,
    #         'vmt_liquid_fuel': self.vmt_liquid_fuel,
    #         'vmt_electricity': self.vmt_electricity,
    #         'battery_kwh': self.battery_kwh,  # note: this is kwh/veh * registered_count
    #         'battery_kwh_per_veh': self.battery_kwh_per_veh,  # this is kwh/veh - used for battery tax credit
    #         'onroad_direct_co2e_grams_per_mile': self.onroad_direct_co2e_grams_per_mile,
    #         'onroad_direct_kwh_per_mile': self.onroad_direct_kwh_per_mile,
    #         'onroad_gallons_per_mile': self.onroad_gallons_per_mile,
    #         'onroad_miles_per_gallon': self.onroad_miles_per_gallon,
    #         'fuel_consumption_gallons': self.fuel_consumption_gallons,
    #         'fuel_consumption_kWh': self.fuel_consumption_kWh,
    #         'fuel_generation_kWh': self.fuel_generation_kWh,
    # 
    #         'barrels_of_oil': oil_bbl,
    #         'barrels_of_imported_oil': imported_oil_bbl,
    #         'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,
    # 
    #         'session_fatalities': self.session_fatalities,
    # 
    #         'nmog_exhaust_ustons': nmog_exh_ustons,
    #         'nmog_evaporative_ustons': nmog_evap_ustons,
    #         'nmog_vehicle_ustons': nmog_veh_ustons,
    #         'co_vehicle_ustons': co_veh_ustons,
    #         'nox_vehicle_ustons': nox_veh_ustons,
    #         'pm25_exhaust_ustons': pm25_exh_ustons,
    #         'pm25_brakewear_ustons': pm25_brakewear_ustons,
    #         'pm25_tirewear_ustons': pm25_tirewear_ustons,
    #         'pm25_vehicle_ustons': pm25_veh_ustons,
    #         'sox_vehicle_ustons': sox_veh_ustons,
    #         'acetaldehyde_vehicle_ustons': acetaldehyde_veh_ustons,
    #         'acrolein_vehicle_ustons': acrolein_veh_ustons,
    #         'benzene_exhaust_ustons': benzene_exh_ustons,
    #         'benzene_evaporative_ustons': benzene_evap_ustons,
    #         'benzene_vehicle_ustons': benzene_veh_ustons,
    #         'ethylbenzene_exhaust_ustons': ethylbenzene_exh_ustons,
    #         'ethylbenzene_evaporative_ustons': ethylbenzene_evap_ustons,
    #         'ethylbenzene_vehicle_ustons': ethylbenzene_veh_ustons,
    #         'formaldehyde_vehicle_ustons': formaldehyde_veh_ustons,
    #         'naphthalene_exhaust_ustons': naphthalene_exh_ustons,
    #         'naphthalene_evaporative_ustons': naphthalene_evap_ustons,
    #         'naphthalene_vehicle_ustons': naphthalene_veh_ustons,
    #         '13_butadiene_vehicle_ustons': butadiene13_veh_ustons,
    #         '15pah_vehicle_ustons': pah15_veh_ustons,
    # 
    #         'ch4_vehicle_metrictons': ch4_veh_metrictons,
    #         'n2o_vehicle_metrictons': n2o_veh_metrictons,
    #         'co2_vehicle_metrictons': co2_veh_metrictons,
    # 
    #         'voc_refinery_ustons': voc_refinery_ustons,
    #         'co_refinery_ustons': co_refinery_ustons,
    #         'nox_refinery_ustons': nox_refinery_ustons,
    #         'pm25_refinery_ustons': pm25_refinery_ustons,
    #         'sox_refinery_ustons': sox_refinery_ustons,
    # 
    #         'voc_egu_ustons': voc_egu_ustons,
    #         'co_egu_ustons': co_egu_ustons,
    #         'nox_egu_ustons': nox_egu_ustons,
    #         'pm25_egu_ustons': pm25_egu_ustons,
    #         'sox_egu_ustons': sox_egu_ustons,
    #         'hcl_egu_ustons': hcl_egu_ustons,
    #         'hg_egu_ustons': hg_egu_ustons,
    # 
    #         'voc_upstream_ustons': voc_upstream_ustons,
    #         'co_upstream_ustons': co_upstream_ustons,
    #         'nox_upstream_ustons': nox_upstream_ustons,
    #         'pm25_upstream_ustons': pm25_upstream_ustons,
    #         'sox_upstream_ustons': sox_upstream_ustons,
    # 
    #         'ch4_refinery_metrictons': ch4_refinery_metrictons,
    #         'n2o_refinery_metrictons': n2o_refinery_metrictons,
    #         'co2_refinery_metrictons': co2_refinery_metrictons,
    # 
    #         'ch4_egu_metrictons': ch4_egu_metrictons,
    #         'n2o_egu_metrictons': n2o_egu_metrictons,
    #         'co2_egu_metrictons': co2_egu_metrictons,
    # 
    #         'ch4_upstream_metrictons': ch4_upstream_metrictons,
    #         'n2o_upstream_metrictons': n2o_upstream_metrictons,
    #         'co2_upstream_metrictons': co2_upstream_metrictons,
    # 
    #         'nmog_and_voc_total_ustons': nmog_total_ustons + voc_total_ustons,
    #         'co_total_ustons': co_total_ustons,
    #         'nox_total_ustons': nox_total_ustons,
    #         'pm25_total_ustons': pm25_total_ustons,
    #         'sox_total_ustons': sox_total_ustons,
    #         'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
    #         'acrolein_total_ustons': acrolein_total_ustons,
    #         'benzene_total_ustons': benzene_total_ustons,
    #         'ethylbenzene_total_ustons': ethylbenzene_total_ustons,
    #         'formaldehyde_total_ustons': formaldehyde_total_ustons,
    #         'naphthalene_total_ustons': naphthalene_total_ustons,
    #         '13_butadiene_total_ustons': butadiene13_total_ustons,
    #         '15pah_total_ustons': pah15_total_ustons,
    #         'co2_total_metrictons': co2_total_metrictons,
    #         'ch4_total_metrictons': ch4_total_metrictons,
    #         'n2o_total_metrictons': n2o_total_metrictons,
    #     }
    # 
    #     return results_dict


class VehiclePhysicalEffects:
    """

    The VehiclePhysicalEffects class calculates physical effects for a given vehicle using information in the
    VehiclePhysicalData objects.

    """
    def __init__(self):

        self.session_policy = None
        self.session_name = None
        self.vehicle_id = None
        self.base_year_vehicle_id = None
        self.manufacturer_id = None
        self.name = None
        self.calendar_year = None
        self.model_year = None
        self.age = None
        self.base_year_reg_class_id = None
        self.reg_class_id = None
        self.context_size_class = None
        self.in_use_fuel_id = None
        self.market_class_id = None
        self.fueling_class = None

        self.base_year_powertrain_type = None
        self.body_style = None
        self.footprint_ft2 = None
        self.workfactor = None
        self.registered_count = None

        self.context_vmt_adjustment = None
        self.annual_vmt = 0
        self.odometer = 0
        self.vmt = 0
        self.annual_vmt_rebound = 0
        self.vmt_rebound = 0
        self.vmt_liquid_fuel = 0
        self.vmt_electricity = 0
        self.battery_kwh = 0
        self.battery_kwh_per_veh = 0

        self.onroad_direct_co2e_grams_per_mile = 0
        self.onroad_direct_kwh_per_mile = 0
        self.onroad_gallons_per_mile = 0
        self.onroad_miles_per_gallon = 0
        self.fuel_consumption_gallons = 0
        self.fuel_consumption_kWh = 0
        self.fuel_generation_kWh = 0

        self.barrels_of_oil = None
        self.barrels_of_imported_oil = None
        self.barrels_of_imported_oil_per_day = None

        self.session_fatalities = 0

        self.nmog_exhaust_ustons = None
        self.nmog_evaporative_ustons = None
        self.nmog_vehicle_ustons = None

        # self.co_exhaust_ustons = None
        # self.nox_exhaust_ustons = None
        self.co_vehicle_ustons = None
        self.nox_vehicle_ustons = None

        self.pm25_exhaust_ustons = None
        self.pm25_brakewear_ustons = None
        self.pm25_tirewear_ustons = None
        self.pm25_vehicle_ustons = None

        # self.sox_exhaust_ustons = None
        self.sox_vehicle_ustons = None

        # self.acetaldehyde_exhaust_ustons = None
        self.acetaldehyde_vehicle_ustons = None

        # self.acrolein_exhaust_ustons = None
        self.acrolein_vehicle_ustons = None

        self.benzene_exhaust_ustons = None
        self.benzene_evaporative_ustons = None
        self.benzene_vehicle_ustons = None

        self.ethylbenzene_exhaust_ustons = None
        self.ethylbenzene_evaporative_ustons = None
        self.ethylbenzene_vehicle_ustons = None

        # self.formaldehyde_exhaust_ustons = None
        self.formaldehyde_vehicle_ustons = None

        self.naphthalene_exhaust_ustons = None
        self.naphthalene_evaporative_ustons = None
        self.naphthalene_vehicle_ustons = None

        # self.butadiene13_exhaust_ustons = None
        self.butadiene13_vehicle_ustons = None

        # self.pah15_exhaust_ustons = None
        self.pah15_vehicle_ustons = None

        self.ch4_vehicle_metrictons = None
        self.n2o_vehicle_metrictons = None
        self.co2_vehicle_metrictons = None

        self.voc_refinery_ustons = None
        self.co_refinery_ustons = None
        self.nox_refinery_ustons = None
        self.pm25_refinery_ustons = None
        self.sox_refinery_ustons = None

        self.voc_egu_ustons = None
        self.co_egu_ustons = None
        self.nox_egu_ustons = None
        self.pm25_egu_ustons = None
        self.sox_egu_ustons = None
        self.hcl_egu_ustons = None
        self.hg_egu_ustons = None

        self.voc_upstream_ustons = None
        self.co_upstream_ustons = None
        self.nox_upstream_ustons = None
        self.pm25_upstream_ustons = None
        self.sox_upstream_ustons = None

        self.ch4_refinery_metrictons = None
        self.n2o_refinery_metrictons = None
        self.co2_refinery_metrictons = None

        self.ch4_egu_metrictons = None
        self.n2o_egu_metrictons = None
        self.co2_egu_metrictons = None

        self.ch4_upstream_metrictons = None
        self.n2o_upstream_metrictons = None
        self.co2_upstream_metrictons = None

        self.nmog_and_voc_total_ustons = None
        self.co_total_ustons = None
        self.nox_total_ustons = None
        self.pm25_total_ustons = None
        self.sox_total_ustons = None

        self.acetaldehyde_total_ustons = None
        self.acrolein_total_ustons = None
        self.benzene_total_ustons = None
        self.ethylbenzene_total_ustons = None
        self.formaldehyde_total_ustons = None
        self.naphthalene_total_ustons = None
        self.butadiene13_total_ustons = None
        self.pah15_total_ustons = None

        self.co2_total_metrictons = None
        self.ch4_total_metrictons = None
        self.n2o_total_metrictons = None

    def calc_vehicle_physical_effects(self, vpd):
        """

        Notes:
            Calculates physical effects for a given vehicle based on the passed data (mostly emission rates).

        """
        self.session_policy = vpd.session_policy
        self.session_name = vpd.session_name
        self.vehicle_id = vpd.vehicle_id
        self.base_year_vehicle_id = vpd.base_year_vehicle_id
        self.manufacturer_id = vpd.manufacturer_id
        self.name = vpd.name
        self.calendar_year = vpd.calendar_year
        self.model_year = vpd.model_year
        self.age = vpd.age
        self.base_year_reg_class_id = vpd.base_year_reg_class_id
        self.reg_class_id = vpd.reg_class_id
        self.context_size_class = vpd.context_size_class
        self.in_use_fuel_id = vpd.in_use_fuel_id
        self.market_class_id = vpd.market_class_id
        self.fueling_class = vpd.fueling_class
        self.base_year_powertrain_type = vpd.base_year_powertrain_type
        self.body_style = vpd.body_style
        self.footprint_ft2 = vpd.footprint_ft2
        self.workfactor = vpd.workfactor
        self.registered_count = vpd.registered_count

        self.context_vmt_adjustment = vpd.context_vmt_adjustment
        self.annual_vmt = vpd.annual_vmt
        self.odometer = vpd.odometer
        self.vmt = vpd.vmt
        self.annual_vmt_rebound = vpd.annual_vmt_rebound
        self.vmt_rebound = vpd.vmt_rebound
        self.vmt_liquid_fuel = vpd.vmt_liquid_fuel
        self.vmt_electricity = vpd.vmt_electricity

        self.battery_kwh = vpd.battery_kwh
        self.battery_kwh_per_veh = vpd.battery_kwh_per_veh

        self.onroad_direct_co2e_grams_per_mile = vpd.onroad_direct_co2e_grams_per_mile
        self.onroad_direct_kwh_per_mile = vpd.onroad_direct_kwh_per_mile
        self.onroad_gallons_per_mile = vpd.onroad_gallons_per_mile
        self.onroad_miles_per_gallon = vpd.onroad_miles_per_gallon
        self.fuel_consumption_gallons = vpd.fuel_consumption_gallons
        self.fuel_consumption_kWh = vpd.fuel_consumption_kWh
        self.fuel_generation_kWh = vpd.fuel_generation_kWh

        self.session_fatalities = vpd.session_fatalities

        # calc exhaust and evaporative emissions for liquid fuel operation
        factor = vpd.vmt / vpd.grams_per_us_ton
        self.pm25_exhaust_ustons = vpd.pm25_exh_rate * factor
        self.nmog_exhaust_ustons = vpd.nmog_exh_rate * factor
        co_exhaust_ustons = vpd.co_exh_rate * factor
        nox_exhaust_ustons = vpd.nox_exh_rate * factor
        acetaldehyde_exhaust_ustons = vpd.acetaldehyde_exh_rate * factor
        acrolein_exhaust_ustons = vpd.acrolein_exh_rate * factor
        self.benzene_exhaust_ustons = vpd.benzene_exh_rate * factor
        self.ethylbenzene_exhaust_ustons = vpd.ethylbenzene_exh_rate * factor
        formaldehyde_exhaust_ustons = vpd.formaldehyde_exh_rate * factor
        self.naphthalene_exhaust_ustons = vpd.naphthalene_exh_rate * factor
        butadiene13_exhaust_ustons = vpd.butadiene13_exh_rate * factor
        pah15_exhaust_ustons = vpd.pah15_exh_rate * factor

        factor = vpd.fuel_consumption_gallons / vpd.grams_per_us_ton
        sox_exhaust_ustons = vpd.sox_exh_rate * factor
        self.nmog_evaporative_ustons = sum([vpd.nmog_permeation_rate,
                                            vpd.nmog_venting_rate,
                                            vpd.nmog_leaks_rate,
                                            vpd.nmog_refuel_disp_rate,
                                            vpd.nmog_refuel_spill_rate]) * factor
        self.benzene_evaporative_ustons = sum([vpd.benzene_permeation_rate,
                                               vpd.benzene_venting_rate,
                                               vpd.benzene_leaks_rate,
                                               vpd.benzene_refuel_disp_rate,
                                               vpd.benzene_refuel_spill_rate]) * factor
        self.ethylbenzene_evaporative_ustons = sum([vpd.ethylbenzene_permeation_rate,
                                                    vpd.ethylbenzene_venting_rate,
                                                    vpd.ethylbenzene_leaks_rate,
                                                    vpd.ethylbenzene_refuel_disp_rate,
                                                    vpd.ethylbenzene_refuel_spill_rate]) * factor
        self.naphthalene_evaporative_ustons = vpd.naphthalene_refuel_spill_rate * factor

        factor = vpd.vmt / vpd.grams_per_metric_ton
        self.ch4_vehicle_metrictons = vpd.ch4_exh_rate * factor
        self.n2o_vehicle_metrictons = vpd.n2o_exh_rate * factor
        self.co2_vehicle_metrictons = vpd.onroad_direct_co2e_grams_per_mile * factor

        # calc vehicle inventories as exhaust plus evap (where applicable)
        self.nmog_vehicle_ustons = self.nmog_exhaust_ustons + self.nmog_evaporative_ustons
        self.co_vehicle_ustons = co_exhaust_ustons
        self.nox_vehicle_ustons = nox_exhaust_ustons
        self.sox_vehicle_ustons = sox_exhaust_ustons
        self.acetaldehyde_vehicle_ustons = acetaldehyde_exhaust_ustons
        self.acrolein_vehicle_ustons = acrolein_exhaust_ustons
        self.benzene_vehicle_ustons = self.benzene_exhaust_ustons + self.benzene_evaporative_ustons
        self.ethylbenzene_vehicle_ustons = self.ethylbenzene_exhaust_ustons + self.ethylbenzene_evaporative_ustons
        self.formaldehyde_vehicle_ustons = formaldehyde_exhaust_ustons
        self.naphthalene_vehicle_ustons = self.naphthalene_exhaust_ustons + self.naphthalene_evaporative_ustons
        self.butadiene13_vehicle_ustons = butadiene13_exhaust_ustons
        self.pah15_vehicle_ustons = pah15_exhaust_ustons

        # calc vehicle pm25 emissions
        self.pm25_brakewear_ustons = \
            vpd.vmt * (vpd.pm25_brakewear_rate_l + vpd.pm25_brakewear_rate_e) / vpd.grams_per_us_ton
        self.pm25_tirewear_ustons = \
            vpd.vmt * (vpd.pm25_tirewear_rate_l + vpd.pm25_tirewear_rate_e) / vpd.grams_per_us_ton

        self.pm25_vehicle_ustons = self.pm25_exhaust_ustons + self.pm25_brakewear_ustons + self.pm25_tirewear_ustons

        # calc upstream emissions for both liquid and electric fuel operation
        kwhs, gallons = vpd.fuel_generation_kWh, vpd.fuel_consumption_gallons
        ref_factor = vpd.fuel_reduction_leading_to_reduced_domestic_refining

        self.voc_refinery_ustons = gallons * vpd.voc_ref_rate * ref_factor / vpd.grams_per_us_ton
        self.co_refinery_ustons = gallons * vpd.co_ref_rate * ref_factor / vpd.grams_per_us_ton
        self.nox_refinery_ustons = gallons * vpd.nox_ref_rate * ref_factor / vpd.grams_per_us_ton
        self.pm25_refinery_ustons = gallons * vpd.pm25_ref_rate * ref_factor / vpd.grams_per_us_ton
        self.sox_refinery_ustons = gallons * vpd.sox_ref_rate * ref_factor / vpd.grams_per_us_ton

        self.voc_egu_ustons = kwhs * vpd.voc_egu_rate / vpd.grams_per_us_ton
        self.co_egu_ustons = kwhs * vpd.co_egu_rate / vpd.grams_per_us_ton
        self.nox_egu_ustons = kwhs * vpd.nox_egu_rate / vpd.grams_per_us_ton
        self.pm25_egu_ustons = kwhs * vpd.pm25_egu_rate / vpd.grams_per_us_ton
        self.sox_egu_ustons = kwhs * vpd.sox_egu_rate / vpd.grams_per_us_ton
        self.hcl_egu_ustons = kwhs * vpd.hcl_egu_rate / vpd.grams_per_us_ton
        self.hg_egu_ustons = kwhs * vpd.hg_egu_rate / vpd.grams_per_us_ton

        self.voc_upstream_ustons = self.voc_refinery_ustons + self.voc_egu_ustons
        self.co_upstream_ustons = self.co_refinery_ustons + self.co_egu_ustons
        self.nox_upstream_ustons = self.nox_refinery_ustons + self.nox_egu_ustons
        self.pm25_upstream_ustons = self.pm25_refinery_ustons + self.pm25_egu_ustons
        self.sox_upstream_ustons = self.sox_refinery_ustons + self.sox_egu_ustons

        self.co2_refinery_metrictons = gallons * vpd.co2_ref_rate * ref_factor / vpd.grams_per_metric_ton
        self.ch4_refinery_metrictons = gallons * vpd.ch4_ref_rate * ref_factor / vpd.grams_per_metric_ton
        self.n2o_refinery_metrictons = gallons * vpd.n2o_ref_rate * ref_factor / vpd.grams_per_metric_ton

        self.co2_egu_metrictons = kwhs * vpd.co2_egu_rate / vpd.grams_per_metric_ton
        self.ch4_egu_metrictons = kwhs * vpd.ch4_egu_rate / vpd.grams_per_metric_ton
        self.n2o_egu_metrictons = kwhs * vpd.n2o_egu_rate / vpd.grams_per_metric_ton

        self.co2_upstream_metrictons = self.co2_refinery_metrictons + self.co2_egu_metrictons
        self.ch4_upstream_metrictons = self.ch4_refinery_metrictons + self.ch4_egu_metrictons
        self.n2o_upstream_metrictons = self.n2o_refinery_metrictons + self.n2o_egu_metrictons

        # sum vehicle and upstream into totals
        self.nmog_and_voc_total_ustons = self.nmog_vehicle_ustons + self.voc_upstream_ustons
        self.co_total_ustons = self.co_vehicle_ustons + self.co_upstream_ustons
        self.nox_total_ustons = self.nox_vehicle_ustons + self.nox_upstream_ustons
        self.pm25_total_ustons = self.pm25_vehicle_ustons + self.pm25_upstream_ustons
        self.sox_total_ustons = self.sox_vehicle_ustons + self.sox_upstream_ustons

        self.acetaldehyde_total_ustons = self.acetaldehyde_vehicle_ustons  # + acetaldehyde_upstream_ustons
        self.acrolein_total_ustons = self.acrolein_vehicle_ustons  # + acrolein_upstream_ustons
        self.benzene_total_ustons = self.benzene_vehicle_ustons  # + benzene_upstream_ustons
        self.ethylbenzene_total_ustons = self.ethylbenzene_vehicle_ustons  # + ethylbenzene_upstream_ustons
        self.formaldehyde_total_ustons = self.formaldehyde_vehicle_ustons  # + formaldehyde_upstream_ustons
        self.naphthalene_total_ustons = self.naphthalene_vehicle_ustons  # + naphlathene_upstream_ustons
        self.butadiene13_total_ustons = self.butadiene13_vehicle_ustons  # + butadiene13_upstream_ustons
        self.pah15_total_ustons = self.pah15_vehicle_ustons  # + pah15_upstream_ustons

        self.co2_total_metrictons = self.co2_vehicle_metrictons + self.co2_upstream_metrictons
        self.ch4_total_metrictons = self.ch4_vehicle_metrictons + self.ch4_upstream_metrictons
        self.n2o_total_metrictons = self.n2o_vehicle_metrictons + self.n2o_upstream_metrictons

        # calc energy security related attributes and comparisons to year_for_compares
        self.barrels_of_oil = vpd.fuel_consumption_gallons * vpd.pure_share * vpd.energy_density_ratio / vpd.gal_per_bbl
        self.barrels_of_imported_oil = self.barrels_of_oil * vpd.energy_security_import_factor
        self.barrels_of_imported_oil_per_day = self.barrels_of_imported_oil / 365
