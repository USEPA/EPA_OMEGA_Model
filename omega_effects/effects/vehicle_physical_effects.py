"""
    Vehicle Physical Effects

"""


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
        self.evse_kwh_per_mile = 0
        self.onroad_gallons_per_mile = 0
        self.onroad_miles_per_gallon = 0
        self.fuel_consumption_gallons = 0
        self.fuel_consumption_kwh = 0
        self.fuel_generation_kwh = 0
        self.curbweight_lbs = 0
        self.gvwr_lbs = 0

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


def calc_vehicle_physical_effects(vpd):
    """

    Args:
        vpd: an instance of the VehiclePhysicalData class.

    Returns:
        A dictionary of physical effects for the given VehiclePhysicalData class instance (vehicle).

    """
    # calc exhaust and evaporative emissions for liquid fuel operation
    factor = vpd.vmt / vpd.grams_per_us_ton
    pm25_exh_ustons = vpd.pm25_exh_rate * factor
    nmog_exh_ustons = vpd.nmog_exh_rate * factor
    co_exh_ustons = vpd.co_exh_rate * factor
    nox_exh_ustons = vpd.nox_exh_rate * factor
    acetaldehyde_exh_ustons = vpd.acetaldehyde_exh_rate * factor
    acrolein_exh_ustons = vpd.acrolein_exh_rate * factor
    benzene_exh_ustons = vpd.benzene_exh_rate * factor
    ethylbenzene_exh_ustons = vpd.ethylbenzene_exh_rate * factor
    formaldehyde_exh_ustons = vpd.formaldehyde_exh_rate * factor
    naphthalene_exh_ustons = vpd.naphthalene_exh_rate * factor
    butadiene13_exh_ustons = vpd.butadiene13_exh_rate * factor
    pah15_exh_ustons = vpd.pah15_exh_rate * factor

    factor = vpd.fuel_consumption_gallons / vpd.grams_per_us_ton
    sox_exh_ustons = vpd.sox_exh_rate * factor
    nmog_evap_ustons = sum([vpd.nmog_permeation_rate,
                            vpd.nmog_venting_rate,
                            vpd.nmog_leaks_rate,
                            vpd.nmog_refuel_disp_rate,
                            vpd.nmog_refuel_spill_rate]) * factor
    benzene_evap_ustons = sum([vpd.benzene_permeation_rate,
                               vpd.benzene_venting_rate,
                               vpd.benzene_leaks_rate,
                               vpd.benzene_refuel_disp_rate,
                               vpd.benzene_refuel_spill_rate]) * factor
    ethylbenzene_evap_ustons = sum([vpd.ethylbenzene_permeation_rate,
                                    vpd.ethylbenzene_venting_rate,
                                    vpd.ethylbenzene_leaks_rate,
                                    vpd.ethylbenzene_refuel_disp_rate,
                                    vpd.ethylbenzene_refuel_spill_rate]) * factor
    naphthalene_evap_ustons = vpd.naphthalene_refuel_spill_rate * factor

    factor = vpd.vmt / vpd.grams_per_metric_ton
    ch4_veh_metrictons = vpd.ch4_exh_rate * factor
    n2o_veh_metrictons = vpd.n2o_exh_rate * factor
    co2_veh_metrictons = vpd.onroad_direct_co2e_grams_per_mile * factor

    # calc vehicle inventories as exhaust plus evap (where applicable)
    nmog_veh_ustons = nmog_exh_ustons + nmog_evap_ustons
    co_veh_ustons = co_exh_ustons
    nox_veh_ustons = nox_exh_ustons
    sox_veh_ustons = sox_exh_ustons
    acetaldehyde_veh_ustons = acetaldehyde_exh_ustons
    acrolein_veh_ustons = acrolein_exh_ustons
    benzene_veh_ustons = benzene_exh_ustons + benzene_evap_ustons
    ethylbenzene_veh_ustons = ethylbenzene_exh_ustons + ethylbenzene_evap_ustons
    formaldehyde_veh_ustons = formaldehyde_exh_ustons
    naphthalene_veh_ustons = naphthalene_exh_ustons + naphthalene_evap_ustons
    butadiene13_veh_ustons = butadiene13_exh_ustons
    pah15_veh_ustons = pah15_exh_ustons

    # calc vehicle pm25 emissions, note that rate_l is 0 for BEVs and rate_e is 0 for non-BEVs (for now)
    pm25_brakewear_ustons = \
        vpd.vmt * (vpd.pm25_brakewear_rate_l + vpd.pm25_brakewear_rate_e) / vpd.grams_per_us_ton
    pm25_tirewear_ustons = \
        vpd.vmt * (vpd.pm25_tirewear_rate_l + vpd.pm25_tirewear_rate_e) / vpd.grams_per_us_ton

    pm25_veh_ustons = pm25_exh_ustons + pm25_brakewear_ustons + pm25_tirewear_ustons

    # calc upstream emissions for both liquid and electric fuel operation
    kwhs, gallons = vpd.fuel_generation_kwh, vpd.fuel_consumption_gallons
    # ref_factor = vpd.fuel_reduction_leading_to_reduced_domestic_refining * vpd.pure_share
    ref_factor = vpd.pure_share

    voc_refinery_ustons = gallons * vpd.voc_ref_rate * ref_factor / vpd.grams_per_us_ton
    co_refinery_ustons = gallons * vpd.co_ref_rate * ref_factor / vpd.grams_per_us_ton
    nox_refinery_ustons = gallons * vpd.nox_ref_rate * ref_factor / vpd.grams_per_us_ton
    pm25_refinery_ustons = gallons * vpd.pm25_ref_rate * ref_factor / vpd.grams_per_us_ton
    sox_refinery_ustons = gallons * vpd.sox_ref_rate * ref_factor / vpd.grams_per_us_ton

    voc_egu_ustons = kwhs * vpd.voc_egu_rate / vpd.grams_per_us_ton
    co_egu_ustons = kwhs * vpd.co_egu_rate / vpd.grams_per_us_ton
    nox_egu_ustons = kwhs * vpd.nox_egu_rate / vpd.grams_per_us_ton
    pm25_egu_ustons = kwhs * vpd.pm25_egu_rate / vpd.grams_per_us_ton
    sox_egu_ustons = kwhs * vpd.sox_egu_rate / vpd.grams_per_us_ton
    hcl_egu_ustons = kwhs * vpd.hcl_egu_rate / vpd.grams_per_us_ton
    hg_egu_ustons = kwhs * vpd.hg_egu_rate / vpd.grams_per_us_ton

    voc_upstream_ustons = voc_refinery_ustons + voc_egu_ustons
    co_upstream_ustons = co_refinery_ustons + co_egu_ustons
    nox_upstream_ustons = nox_refinery_ustons + nox_egu_ustons
    pm25_upstream_ustons = pm25_refinery_ustons + pm25_egu_ustons
    sox_upstream_ustons = sox_refinery_ustons + sox_egu_ustons

    co2_refinery_metrictons = gallons * vpd.co2_ref_rate * ref_factor / vpd.grams_per_metric_ton
    ch4_refinery_metrictons = gallons * vpd.ch4_ref_rate * ref_factor / vpd.grams_per_metric_ton
    n2o_refinery_metrictons = gallons * vpd.n2o_ref_rate * ref_factor / vpd.grams_per_metric_ton

    co2_egu_metrictons = kwhs * vpd.co2_egu_rate / vpd.grams_per_metric_ton
    ch4_egu_metrictons = kwhs * vpd.ch4_egu_rate / vpd.grams_per_metric_ton
    n2o_egu_metrictons = kwhs * vpd.n2o_egu_rate / vpd.grams_per_metric_ton

    co2_upstream_metrictons = co2_refinery_metrictons + co2_egu_metrictons
    ch4_upstream_metrictons = ch4_refinery_metrictons + ch4_egu_metrictons
    n2o_upstream_metrictons = n2o_refinery_metrictons + n2o_egu_metrictons

    # sum vehicle and upstream into totals
    voc_total_ustons = voc_upstream_ustons  # + voc_tailpipe_ustons
    nmog_total_ustons = nmog_veh_ustons  # + nmog_upstream_ustons
    co_total_ustons = co_veh_ustons + co_upstream_ustons
    nox_total_ustons = nox_veh_ustons + nox_upstream_ustons
    pm25_total_ustons = pm25_veh_ustons + pm25_upstream_ustons
    sox_total_ustons = sox_veh_ustons + sox_upstream_ustons
    acetaldehyde_total_ustons = acetaldehyde_veh_ustons  # + acetaldehyde_upstream_ustons
    acrolein_total_ustons = acrolein_veh_ustons  # + acrolein_upstream_ustons
    benzene_total_ustons = benzene_veh_ustons  # + benzene_upstream_ustons
    ethylbenzene_total_ustons = ethylbenzene_veh_ustons  # + ethylbenzene_upstream_ustons
    formaldehyde_total_ustons = formaldehyde_veh_ustons  # + formaldehyde_upstream_ustons
    naphthalene_total_ustons = naphthalene_veh_ustons  # + naphlathene_upstream_ustons
    butadiene13_total_ustons = butadiene13_veh_ustons  # + butadiene13_upstream_ustons
    pah15_total_ustons = pah15_veh_ustons  # + pah15_upstream_ustons
    co2_total_metrictons = co2_veh_metrictons + co2_upstream_metrictons
    ch4_total_metrictons = ch4_veh_metrictons + ch4_upstream_metrictons
    n2o_total_metrictons = n2o_veh_metrictons + n2o_upstream_metrictons

    # calc energy security related attributes and comparisons to year_for_compares
    oil_bbl = vpd.fuel_consumption_gallons * vpd.pure_share * vpd.energy_density_ratio / vpd.gal_per_bbl
    imported_oil_bbl = oil_bbl * vpd.energy_security_import_factor
    imported_oil_bbl_per_day = imported_oil_bbl / 365

    results_dict = {
        'session_policy': vpd.session_policy,
        'session_name': vpd.session_name,
        'vehicle_id': vpd.vehicle_id,
        'base_year_vehicle_id': vpd.base_year_vehicle_id,
        'manufacturer_id': vpd.manufacturer_id,
        'name': vpd.name,
        'calendar_year': int(vpd.calendar_year),
        'model_year': vpd.calendar_year - vpd.age,
        'age': vpd.age,
        'base_year_reg_class_id': vpd.base_year_reg_class_id,
        'reg_class_id': vpd.reg_class_id,
        'context_size_class': vpd.context_size_class,
        'in_use_fuel_id': vpd.in_use_fuel_id,
        'market_class_id': vpd.market_class_id,
        'fueling_class': vpd.fueling_class,
        'base_year_powertrain_type': vpd.base_year_powertrain_type,
        'body_style': vpd.body_style,
        'footprint_ft2': vpd.footprint_ft2,
        'workfactor': vpd.workfactor,
        'registered_count': vpd.registered_count,
        'context_vmt_adjustment': vpd.context_vmt_adjustment,
        'annual_vmt': vpd.annual_vmt,
        'odometer': vpd.odometer,
        'vmt': vpd.vmt,
        'annual_vmt_rebound': vpd.annual_vmt_rebound,
        'vmt_rebound': vpd.vmt_rebound,
        'vmt_liquid_fuel': vpd.vmt_liquid_fuel,
        'vmt_electricity': vpd.vmt_electricity,
        'battery_kwh': vpd.battery_kwh,  # note: this is kwh/veh * registered_count
        'battery_kwh_per_veh': vpd.battery_kwh_per_veh,  # this is kwh/veh - used for battery tax credit
        'onroad_direct_co2e_grams_per_mile': vpd.onroad_direct_co2e_grams_per_mile,
        'onroad_direct_kwh_per_mile': vpd.onroad_direct_kwh_per_mile,
        'evse_kwh_per_mile': vpd.evse_kwh_per_mile,
        'onroad_gallons_per_mile': vpd.onroad_gallons_per_mile,
        'onroad_miles_per_gallon': vpd.onroad_miles_per_gallon,
        'fuel_consumption_gallons': vpd.fuel_consumption_gallons,
        'fuel_consumption_kwh': vpd.fuel_consumption_kwh,
        'fuel_generation_kwh': vpd.fuel_generation_kwh,
        'curbweight_lbs': vpd.curbweight_lbs,
        'gvwr_lbs': vpd.gvwr_lbs,

        'barrels_of_oil': oil_bbl,
        'barrels_of_imported_oil': imported_oil_bbl,
        'barrels_of_imported_oil_per_day': imported_oil_bbl_per_day,

        'session_fatalities': vpd.session_fatalities,

        'nmog_exhaust_ustons': nmog_exh_ustons,
        'nmog_evaporative_ustons': nmog_evap_ustons,
        'nmog_vehicle_ustons': nmog_veh_ustons,
        'co_vehicle_ustons': co_veh_ustons,
        'nox_vehicle_ustons': nox_veh_ustons,
        'pm25_exhaust_ustons': pm25_exh_ustons,
        'pm25_brakewear_ustons': pm25_brakewear_ustons,
        'pm25_tirewear_ustons': pm25_tirewear_ustons,
        'pm25_vehicle_ustons': pm25_veh_ustons,
        'sox_vehicle_ustons': sox_veh_ustons,
        'acetaldehyde_vehicle_ustons': acetaldehyde_veh_ustons,
        'acrolein_vehicle_ustons': acrolein_veh_ustons,
        'benzene_exhaust_ustons': benzene_exh_ustons,
        'benzene_evaporative_ustons': benzene_evap_ustons,
        'benzene_vehicle_ustons': benzene_veh_ustons,
        'ethylbenzene_exhaust_ustons': ethylbenzene_exh_ustons,
        'ethylbenzene_evaporative_ustons': ethylbenzene_evap_ustons,
        'ethylbenzene_vehicle_ustons': ethylbenzene_veh_ustons,
        'formaldehyde_vehicle_ustons': formaldehyde_veh_ustons,
        'naphthalene_exhaust_ustons': naphthalene_exh_ustons,
        'naphthalene_evaporative_ustons': naphthalene_evap_ustons,
        'naphthalene_vehicle_ustons': naphthalene_veh_ustons,
        'butadiene13_vehicle_ustons': butadiene13_veh_ustons,
        'pah15_vehicle_ustons': pah15_veh_ustons,

        'ch4_vehicle_metrictons': ch4_veh_metrictons,
        'n2o_vehicle_metrictons': n2o_veh_metrictons,
        'co2_vehicle_metrictons': co2_veh_metrictons,

        'voc_refinery_ustons': voc_refinery_ustons,
        'co_refinery_ustons': co_refinery_ustons,
        'nox_refinery_ustons': nox_refinery_ustons,
        'pm25_refinery_ustons': pm25_refinery_ustons,
        'sox_refinery_ustons': sox_refinery_ustons,

        'voc_egu_ustons': voc_egu_ustons,
        'co_egu_ustons': co_egu_ustons,
        'nox_egu_ustons': nox_egu_ustons,
        'pm25_egu_ustons': pm25_egu_ustons,
        'sox_egu_ustons': sox_egu_ustons,
        'hcl_egu_ustons': hcl_egu_ustons,
        'hg_egu_ustons': hg_egu_ustons,

        'voc_upstream_ustons': voc_upstream_ustons,
        'co_upstream_ustons': co_upstream_ustons,
        'nox_upstream_ustons': nox_upstream_ustons,
        'pm25_upstream_ustons': pm25_upstream_ustons,
        'sox_upstream_ustons': sox_upstream_ustons,

        'ch4_refinery_metrictons': ch4_refinery_metrictons,
        'n2o_refinery_metrictons': n2o_refinery_metrictons,
        'co2_refinery_metrictons': co2_refinery_metrictons,

        'ch4_egu_metrictons': ch4_egu_metrictons,
        'n2o_egu_metrictons': n2o_egu_metrictons,
        'co2_egu_metrictons': co2_egu_metrictons,

        'ch4_upstream_metrictons': ch4_upstream_metrictons,
        'n2o_upstream_metrictons': n2o_upstream_metrictons,
        'co2_upstream_metrictons': co2_upstream_metrictons,

        'nmog_and_voc_total_ustons': nmog_total_ustons + voc_total_ustons,
        'co_total_ustons': co_total_ustons,
        'nox_total_ustons': nox_total_ustons,
        'pm25_total_ustons': pm25_total_ustons,
        'sox_total_ustons': sox_total_ustons,
        'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
        'acrolein_total_ustons': acrolein_total_ustons,
        'benzene_total_ustons': benzene_total_ustons,
        'ethylbenzene_total_ustons': ethylbenzene_total_ustons,
        'formaldehyde_total_ustons': formaldehyde_total_ustons,
        'naphthalene_total_ustons': naphthalene_total_ustons,
        '13_butadiene_total_ustons': butadiene13_total_ustons,
        '15pah_total_ustons': pah15_total_ustons,
        'co2_total_metrictons': co2_total_metrictons,
        'ch4_total_metrictons': ch4_total_metrictons,
        'n2o_total_metrictons': n2o_total_metrictons,
    }

    return results_dict
