"""

emission_costs.py
=================
"""
# import pandas as pd
# from itertools import product

import o2
from usepa_omega2 import *

# create some empty dicts in which to store VehicleFinal objects and scc/criteria cost factors
es_dict = dict()
cn_dict = dict()


def get_scc_cf(calendar_year, query=False):
    from effects.cost_factors_scc import CostFactorsSCC

    cost_factors = ['co2_domestic_cost_factor_25',
                    'co2_domestic_cost_factor_30',
                    'co2_domestic_cost_factor_70',
                    'ch4_domestic_cost_factor_25',
                    'ch4_domestic_cost_factor_30',
                    'ch4_domestic_cost_factor_70',
                    'n2o_domestic_cost_factor_25',
                    'n2o_domestic_cost_factor_30',
                    'n2o_domestic_cost_factor_70',
                    'co2_global_cost_factor_25',
                    'co2_global_cost_factor_30',
                    'co2_global_cost_factor_70',
                    'ch4_global_cost_factor_25',
                    'ch4_global_cost_factor_30',
                    'ch4_global_cost_factor_70',
                    'n2o_global_cost_factor_25',
                    'n2o_global_cost_factor_30',
                    'n2o_global_cost_factor_70',
                    ]

    return CostFactorsSCC.get_cost_factors(calendar_year, cost_factors)


def get_criteria_cf(calendar_year, query=False):
    from effects.cost_factors_criteria import CostFactorsCriteria

    cost_factors = ['pm25_low_mortality_30',
                    'pm25_high_mortality_30',
                    'nox_low_mortality_30',
                    'nox_high_mortality_30',
                    'pm25_low_mortality_70',
                    'pm25_high_mortality_70',
                    'nox_low_mortality_70',
                    'nox_high_mortality_70',
                    ]

    return CostFactorsCriteria.get_cost_factors(calendar_year, cost_factors)


def get_energysecurity_cf(calendar_year, query=False):
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    es_dict_id = f'{calendar_year}'

    if es_dict_id in es_dict and not query:
        es_cf, foreign_oil_fraction = es_dict[es_dict_id]
    else:
        es_cf, foreign_oil_fraction = o2.session.query(CostFactorsEnergySecurity.dollars_per_gallon,
                                                       CostFactorsEnergySecurity.foreign_oil_fraction). \
            filter(CostFactorsEnergySecurity.calendar_year == calendar_year).one()

        es_dict[es_dict_id] = es_cf, foreign_oil_fraction

    return es_cf, foreign_oil_fraction


def get_congestion_noise_cf(reg_class_id, query=False):
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise

    cn_dict_id = f'{reg_class_id}'

    if cn_dict_id in cn_dict and not query:
        congestion_cf, noise_cf = cn_dict[cn_dict_id]
    else:
        congestion_cf, noise_cf = o2.session.query(CostFactorsCongestionNoise.congestion_cost_dollars_per_mile,
                                                   CostFactorsCongestionNoise.noise_cost_dollars_per_mile). \
            filter(CostFactorsCongestionNoise.reg_class_id == reg_class_id).one()

        cn_dict[cn_dict_id] = congestion_cf, noise_cf

    return congestion_cf, noise_cf


def calc_carbon_emission_costs(calendar_year):
    """
    Calculate social costs associated with carbon emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects scc data table that is empty at this point.
    """
    from vehicle_annual_data import VehicleAnnualData
    from effects.cost_effects_scc import CostEffectsSCC

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData.vehicle_ID,
                                VehicleAnnualData.age,
                                VehicleAnnualData.co2_total_metrictons,
                                VehicleAnnualData.ch4_total_metrictons,
                                VehicleAnnualData.n2o_vehicle_metrictons).\
        filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE cost effects data
    # Since the monetized effects data table is empty, the med_list will store all data for this calendar year
    # and write to that table in bulk via the add all.
    ed_list = list()
    for vad_veh in vad_vehs:
        # get tons
        vehicle_ID, age, co2_tons, ch4_tons, n2o_tons = vad_veh[0], vad_veh[1], vad_veh[2], vad_veh[3], vad_veh[4]
        
        # get cost factors
        co2_domestic_25, co2_domestic_30, co2_domestic_70, \
        ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
        n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
        co2_global_25, co2_global_30, co2_global_70, \
        ch4_global_25, ch4_global_30, ch4_global_70, \
        n2o_global_25, n2o_global_30, n2o_global_70 \
            = get_scc_cf(calendar_year, query=query)

        co2_domestic_25_social_cost_dollars = co2_tons * co2_domestic_25
        co2_domestic_30_social_cost_dollars = co2_tons * co2_domestic_30
        co2_domestic_70_social_cost_dollars = co2_tons * co2_domestic_70

        ch4_domestic_25_social_cost_dollars = ch4_tons * ch4_domestic_25
        ch4_domestic_30_social_cost_dollars = ch4_tons * ch4_domestic_30
        ch4_domestic_70_social_cost_dollars = ch4_tons * ch4_domestic_70

        n2o_domestic_25_social_cost_dollars = n2o_tons * n2o_domestic_25
        n2o_domestic_30_social_cost_dollars = n2o_tons * n2o_domestic_30
        n2o_domestic_70_social_cost_dollars = n2o_tons * n2o_domestic_70

        co2_global_25_social_cost_dollars = co2_tons * co2_global_25
        co2_global_30_social_cost_dollars = co2_tons * co2_global_30
        co2_global_70_social_cost_dollars = co2_tons * co2_global_70

        ch4_global_25_social_cost_dollars = ch4_tons * ch4_global_25
        ch4_global_30_social_cost_dollars = ch4_tons * ch4_global_30
        ch4_global_70_social_cost_dollars = ch4_tons * ch4_global_70

        n2o_global_25_social_cost_dollars = n2o_tons * n2o_global_25
        n2o_global_30_social_cost_dollars = n2o_tons * n2o_global_30
        n2o_global_70_social_cost_dollars = n2o_tons * n2o_global_70

        ed_list.append(CostEffectsSCC(vehicle_ID = vehicle_ID,
                                      calendar_year = calendar_year,
                                      age = age,
                                      discount_status = 'undiscounted',
                                      co2_domestic_25_social_cost_dollars = co2_domestic_25_social_cost_dollars,
                                      co2_domestic_30_social_cost_dollars = co2_domestic_30_social_cost_dollars,
                                      co2_domestic_70_social_cost_dollars = co2_domestic_70_social_cost_dollars,
                                      ch4_domestic_25_social_cost_dollars = ch4_domestic_25_social_cost_dollars,
                                      ch4_domestic_30_social_cost_dollars = ch4_domestic_30_social_cost_dollars,
                                      ch4_domestic_70_social_cost_dollars = ch4_domestic_70_social_cost_dollars,
                                      n2o_domestic_25_social_cost_dollars = n2o_domestic_25_social_cost_dollars,
                                      n2o_domestic_30_social_cost_dollars = n2o_domestic_30_social_cost_dollars,
                                      n2o_domestic_70_social_cost_dollars = n2o_domestic_70_social_cost_dollars,
                                      co2_global_25_social_cost_dollars = co2_global_25_social_cost_dollars,
                                      co2_global_30_social_cost_dollars = co2_global_30_social_cost_dollars,
                                      co2_global_70_social_cost_dollars = co2_global_70_social_cost_dollars,
                                      ch4_global_25_social_cost_dollars = ch4_global_25_social_cost_dollars,
                                      ch4_global_30_social_cost_dollars = ch4_global_30_social_cost_dollars,
                                      ch4_global_70_social_cost_dollars = ch4_global_70_social_cost_dollars,
                                      n2o_global_25_social_cost_dollars = n2o_global_25_social_cost_dollars,
                                      n2o_global_30_social_cost_dollars = n2o_global_30_social_cost_dollars,
                                      n2o_global_70_social_cost_dollars = n2o_global_70_social_cost_dollars,
                                      )
                        )
    o2.session.add_all(ed_list)


def calc_criteria_emission_costs(calendar_year):
    """
    Calculate social costs associated with criteria emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects criteria table that has not been filled to this point.
    """
    from vehicle_annual_data import VehicleAnnualData
    from effects.cost_effects_criteria import CostEffectsCriteria

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData.vehicle_ID,
                                VehicleAnnualData.age,
                                VehicleAnnualData.pm25_total_ustons,
                                VehicleAnnualData.nox_total_ustons,).\
        filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE cost effects data
    ed_list = list()
    for vad_veh in vad_vehs:
        # get tons
        vehicle_ID, age, pm25_tons, nox_tons = vad_veh[0], vad_veh[1], vad_veh[2], vad_veh[3]

        # get cost factors
        pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7 \
            = get_criteria_cf(calendar_year, query=query)

        pm25_low_mortality_30_social_cost_dollars = pm25_tons * pm25_low_3
        pm25_high_mortality_30_social_cost_dollars = pm25_tons * pm25_high_3

        nox_low_mortality_30_social_cost_dollars = nox_tons * nox_low_3
        nox_high_mortality_30_social_cost_dollars = nox_tons * nox_high_3

        pm25_low_mortality_70_social_cost_dollars = pm25_tons * pm25_low_7
        pm25_high_mortality_70_social_cost_dollars = pm25_tons * pm25_high_7

        nox_low_mortality_70_social_cost_dollars = nox_tons * nox_low_7
        nox_high_mortality_70_social_cost_dollars = nox_tons * nox_high_7

        ed_list.append(CostEffectsCriteria(vehicle_ID = vehicle_ID,
                                           calendar_year = calendar_year,
                                           age = age,
                                           discount_status = 'undiscounted',
                                           pm25_low_mortality_30_social_cost_dollars = pm25_low_mortality_30_social_cost_dollars,
                                           pm25_high_mortality_30_social_cost_dollars = pm25_high_mortality_30_social_cost_dollars,
                                           nox_low_mortality_30_social_cost_dollars = nox_low_mortality_30_social_cost_dollars,
                                           nox_high_mortality_30_social_cost_dollars = nox_high_mortality_30_social_cost_dollars,
                                           pm25_low_mortality_70_social_cost_dollars = pm25_low_mortality_70_social_cost_dollars,
                                           pm25_high_mortality_70_social_cost_dollars = pm25_high_mortality_70_social_cost_dollars,
                                           nox_low_mortality_70_social_cost_dollars = nox_low_mortality_70_social_cost_dollars,
                                           nox_high_mortality_70_social_cost_dollars = nox_high_mortality_70_social_cost_dollars,
                                           )
                        )
    o2.session.add_all(ed_list)


def calc_non_emission_costs(calendar_year): # TODO congestion/noise/other?
    """
    Calculate social costs associated with fuel consumption by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects non-emissions table that has not been filled to this point.
    """
    from vehicle_annual_data import VehicleAnnualData
    from effects.cost_effects_non_emissions import CostEffectsNonEmissions
    from context_fuel_prices import ContextFuelPrices
    from vehicles import VehicleFinal

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData.vehicle_ID,
                                VehicleAnnualData.age,
                                VehicleAnnualData.fuel_consumption,
                                VehicleAnnualData.vmt, ). \
        filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE cost effects data
    ed_list = list()
    for vad_veh in vad_vehs:
        # get vehicle annual data
        vehicle_ID, age, fuel_consumption, vmt = vad_veh[0], vad_veh[1], vad_veh[2], vad_veh[3]

        # get vehicle final data
        reg_class_ID, in_use_fuel_ID = VehicleFinal.get_vehicle_attributes(vehicle_ID, ['reg_class_ID', 'in_use_fuel_ID'])

        # get fuel prices
        retail, pretax = ContextFuelPrices.get_fuel_prices(calendar_year,
                                                          ['retail_dollars_per_unit', 'pretax_dollars_per_unit'],
                                                          in_use_fuel_ID)

        # fuel costs
        fuel_30_retail_cost_dollars = fuel_consumption * retail
        fuel_70_retail_cost_dollars = fuel_consumption * retail
        fuel_30_social_cost_dollars = fuel_consumption * pretax
        fuel_70_social_cost_dollars = fuel_consumption * pretax

        # get energy security cost factors
        es_cost_factor, foreign_oil_fraction = get_energysecurity_cf(calendar_year, query=query)

        # energy security
        if in_use_fuel_ID == 'pump gasoline':
            energy_security_30_social_cost_dollars = fuel_consumption * es_cost_factor * foreign_oil_fraction
            energy_security_70_social_cost_dollars = fuel_consumption * es_cost_factor * foreign_oil_fraction
        else:
            energy_security_30_social_cost_dollars, energy_security_70_social_cost_dollars = 0, 0

        # get congestion and noise cost factors
        congestion_cf, noise_cf = get_congestion_noise_cf(reg_class_ID, query=query)

        # congestion and noise costs
        congestion_30_social_cost_dollars = vmt * congestion_cf
        congestion_70_social_cost_dollars = vmt * congestion_cf
        noise_30_social_cost_dollars = vmt * noise_cf
        noise_70_social_cost_dollars = vmt * noise_cf

        ed_list.append(CostEffectsNonEmissions(vehicle_ID=vehicle_ID,
                                               calendar_year=calendar_year,
                                               age=age,
                                               discount_status='undiscounted',
                                               fuel_30_retail_cost_dollars=fuel_30_retail_cost_dollars,
                                               fuel_70_retail_cost_dollars=fuel_70_retail_cost_dollars,
                                               fuel_30_social_cost_dollars=fuel_30_social_cost_dollars,
                                               fuel_70_social_cost_dollars=fuel_70_social_cost_dollars,
                                               energy_security_30_social_cost_dollars=energy_security_30_social_cost_dollars,
                                               energy_security_70_social_cost_dollars=energy_security_70_social_cost_dollars,
                                               congestion_30_social_cost_dollars=congestion_30_social_cost_dollars,
                                               congestion_70_social_cost_dollars=congestion_70_social_cost_dollars,
                                               noise_30_social_cost_dollars=noise_30_social_cost_dollars,
                                               noise_70_social_cost_dollars=noise_70_social_cost_dollars,
                                               )
                        )
    o2.session.add_all(ed_list)
