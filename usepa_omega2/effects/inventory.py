"""

inventory.py
============
"""
import pandas as pd
import o2
from usepa_omega2 import *


grams_per_us_ton = 907185
grams_per_metric_ton = 1000000
transloss = 0.07
gap_ice = 0.8
gap_bev = 0.7
co2_indolene = 8887
kwh_per_mile_cycle = 0.2 # TODO Placeholder - what are we doing about calculating energy consumption on vehicles?


# create some empty dicts in which to store VehicleFinal objects and vehicle/refinery/powersector emission factors
vehicles_dict = dict()


def get_vehicle_info(vehicle_id):
    from vehicles import VehicleFinal

    # add kwh_per_mile_cycle here when available in VehicleFinal
    attribute_list = ['model_year', 'reg_class_ID', 'in_use_fuel_ID', 'cert_CO2_grams_per_mile']

    if vehicle_id not in vehicles_dict:
        vehicles_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)

    return vehicles_dict[vehicle_id]


def get_vehicle_ef(calendar_year, model_year, reg_class_id, query=False):
    from effects.emission_factors_vehicles import EmissionFactorsVehicles

    emission_factors = [
        'voc_grams_per_mile',
        'co_grams_per_mile',
        'nox_grams_per_mile',
        'pm25_grams_per_mile',
        'sox_grams_per_gallon',
        'benzene_grams_per_mile',
        'butadiene13_grams_per_mile',
        'formaldehyde_grams_per_mile',
        'acetaldehyde_grams_per_mile',
        'acrolein_grams_per_mile',
        'ch4_grams_per_mile',
        'n2o_grams_per_mile',
    ]

    age = calendar_year - model_year

    return EmissionFactorsVehicles.get_emission_factors(model_year, age, reg_class_id, emission_factors)


def get_powersector_ef(calendar_year, query=False):
    from effects.emission_factors_powersector import EmissionFactorsPowersector

    emission_factors = [
        'voc_grams_per_kWh',
        'co_grams_per_kWh',
        'nox_grams_per_kWh',
        'pm25_grams_per_kWh',
        'sox_grams_per_kWh',
        'benzene_grams_per_kWh',
        'butadiene13_grams_per_kWh',
        'formaldehyde_grams_per_kWh',
        'acetaldehyde_grams_per_kWh',
        'acrolein_grams_per_kWh',
        'co2_grams_per_kWh',
        'ch4_grams_per_kWh',
        'n2o_grams_per_kWh',
    ]

    return EmissionFactorsPowersector.get_emission_factors(calendar_year, emission_factors)


def get_refinery_ef(calendar_year):
    from effects.emission_factors_refinery import EmissionFactorsRefinery

    emission_factors = [
        'voc_grams_per_gallon',
        'co_grams_per_gallon',
        'nox_grams_per_gallon',
        'pm25_grams_per_gallon',
        'sox_grams_per_gallon',
        'benzene_grams_per_gallon',
        'butadiene13_grams_per_gallon',
        'formaldehyde_grams_per_gallon',
        'acetaldehyde_grams_per_gallon',
        'acrolein_grams_per_gallon',
        'naphthalene_grams_per_gallon',
        'co2_grams_per_gallon',
        'ch4_grams_per_gallon',
        'n2o_grams_per_gallon',
    ]

    return EmissionFactorsRefinery.get_emission_factors(calendar_year, emission_factors)


def calc_inventory(calendar_year):
    """
    Calculate onroad CO2 grams/mile, kWh/mile, fuel consumption, vehicle and upstream emission inventories
    by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the vehicle_annual_data table that has not been filled to this point.
    """
    from vehicle_annual_data import VehicleAnnualData

    query = False

    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

    # UPDATE vehicle annual data related to effects
    for vad in vads:
        model_year, reg_class_ID, in_use_fuel_ID, cert_CO2_grams_per_mile = get_vehicle_info(vad.vehicle_ID)  # add kwh_per_mile_cycle here

        # co2 and fuel consumption
        if in_use_fuel_ID == 'US electricity':
            vad.onroad_co2_grams_per_mile = 0
            vad.onroad_fuel_consumption_rate = kwh_per_mile_cycle / gap_bev  # TODO placeholder for now
            vad.fuel_consumption = vad.vmt * vad.onroad_fuel_consumption_rate
        else:
            vad.onroad_co2_grams_per_mile = cert_CO2_grams_per_mile / gap_ice  # TODO how are we doing this - simply gap? what about AC, off-cycle, etc.?
            vad.onroad_fuel_consumption_rate = vad.onroad_co2_grams_per_mile / co2_indolene  # TODO is this how we're doing this?
            vad.fuel_consumption = vad.vmt * vad.onroad_fuel_consumption_rate

        # vehicle inventory
        if in_use_fuel_ID == 'US electricity':
            vad.voc_vehicle_ustons = 0
            vad.co_vehicle_ustons = 0
            vad.nox_vehicle_ustons = 0
            vad.pm25_vehicle_ustons = 0
            vad.benzene_vehicle_ustons = 0
            vad.butadiene13_vehicle_ustons = 0
            vad.formaldehyde_vehicle_ustons = 0
            vad.acetaldehyde_vehicle_ustons = 0
            vad.acrolein_vehicle_ustons = 0

            vad.sox_vehicle_ustons = 0

            vad.ch4_vehicle_metrictons = 0
            vad.n2o_vehicle_metrictons = 0
            vad.co2_vehicle_metrictons = 0
        else:
            voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, ch4, n2o \
                = get_vehicle_ef(calendar_year, model_year, reg_class_ID, query=query)

            vad.voc_vehicle_ustons = vad.vmt * voc / grams_per_us_ton
            vad.co_vehicle_ustons = vad.vmt * co / grams_per_us_ton
            vad.nox_vehicle_ustons = vad.vmt * nox / grams_per_us_ton
            vad.pm25_vehicle_ustons = vad.vmt * pm25 / grams_per_us_ton
            vad.benzene_vehicle_ustons = vad.vmt * benzene / grams_per_us_ton
            vad.butadiene13_vehicle_ustons = vad.vmt * butadiene13 / grams_per_us_ton
            vad.formaldehyde_vehicle_ustons = vad.vmt * formaldehyde / grams_per_us_ton
            vad.acetaldehyde_vehicle_ustons = vad.vmt * acetaldehyde / grams_per_us_ton
            vad.acrolein_vehicle_ustons = vad.vmt * acrolein / grams_per_us_ton

            vad.sox_vehicle_ustons = vad.fuel_consumption * sox / grams_per_us_ton

            vad.ch4_vehicle_metrictons = vad.vmt * ch4 / grams_per_metric_ton
            vad.n2o_vehicle_metrictons = vad.vmt * n2o / grams_per_metric_ton
            vad.co2_vehicle_metrictons = vad.vmt * vad.onroad_co2_grams_per_mile / grams_per_metric_ton

        # upstream inventory
        if in_use_fuel_ID == 'US electricity':
            voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, co2, ch4, n2o \
                = get_powersector_ef(calendar_year, query=query)
        else:
            voc, co, nox, pm25, sox, benzene, butadiene13, formaldehyde, acetaldehyde, acrolein, naphthalene, co2, ch4, n2o \
                = get_refinery_ef(calendar_year, query=query)

        vad.voc_upstream_ustons = vad.fuel_consumption * voc / grams_per_us_ton
        vad.co_upstream_ustons = vad.fuel_consumption * co / grams_per_us_ton
        vad.nox_upstream_ustons = vad.fuel_consumption * nox / grams_per_us_ton
        vad.pm25_upstream_ustons = vad.fuel_consumption * pm25 / grams_per_us_ton
        vad.benzene_upstream_ustons = vad.fuel_consumption * benzene / grams_per_us_ton
        vad.butadiene13_upstream_ustons = vad.fuel_consumption * butadiene13 / grams_per_us_ton
        vad.formaldehyde_upstream_ustons = vad.fuel_consumption * formaldehyde / grams_per_us_ton
        vad.acetaldehyde_upstream_ustons = vad.fuel_consumption * acetaldehyde / grams_per_us_ton
        vad.acrolein_upstream_ustons = vad.fuel_consumption * acrolein / grams_per_us_ton

        if in_use_fuel_ID == 'US electricity':
            vad.naphthalene_upstream_ustons = 0
        else:
            vad.naphthalene_upstream_ustons = vad.fuel_consumption * naphthalene / grams_per_us_ton

        vad.sox_upstream_ustons = vad.fuel_consumption * sox / grams_per_us_ton

        vad.ch4_upstream_metrictons = vad.fuel_consumption * ch4 / grams_per_metric_ton
        vad.n2o_upstream_metrictons = vad.fuel_consumption * n2o / grams_per_metric_ton
        vad.co2_upstream_metrictons = vad.fuel_consumption * co2 / grams_per_metric_ton

        # sum vehicle and upstream into totals
        vad.voc_total_ustons = vad.voc_vehicle_ustons + vad.voc_upstream_ustons
        vad.co_total_ustons = vad.co_vehicle_ustons + vad.co_upstream_ustons
        vad.nox_total_ustons = vad.nox_vehicle_ustons + vad.nox_upstream_ustons
        vad.pm25_total_ustons = vad.pm25_vehicle_ustons + vad.pm25_upstream_ustons
        vad.benzene_total_ustons = vad.benzene_vehicle_ustons + vad.benzene_upstream_ustons
        vad.butadiene13_total_ustons = vad.butadiene13_vehicle_ustons + vad.butadiene13_upstream_ustons
        vad.formaldehyde_total_ustons = vad.formaldehyde_vehicle_ustons + vad.formaldehyde_upstream_ustons
        vad.acetaldehyde_total_ustons = vad.acetaldehyde_vehicle_ustons + vad.acetaldehyde_upstream_ustons
        vad.acrolein_total_ustons = vad.acrolein_vehicle_ustons + vad.acrolein_upstream_ustons
        vad.naphthalene_total_ustons = vad.naphthalene_upstream_ustons
        vad.sox_total_ustons = vad.sox_vehicle_ustons + vad.sox_upstream_ustons
        vad.ch4_total_metrictons = vad.ch4_vehicle_metrictons + vad.ch4_upstream_metrictons
        vad.n2o_total_metrictons = vad.n2o_vehicle_metrictons + vad.n2o_upstream_metrictons
        vad.co2_total_metrictons = vad.co2_vehicle_metrictons + vad.co2_upstream_metrictons
