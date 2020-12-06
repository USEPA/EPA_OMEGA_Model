"""

emission_costs.py
=================
"""
import pandas as pd
from itertools import product

import o2
from usepa_omega2 import *

# create some empty dicts in which to store VehicleFinal objects and scc/criteria cost factors
vehicles_dict = dict()
scf_dict = dict()
ccf_dict = dict()


def get_scc_cf(calendar_year, query=False):
    from effects.cost_factors_scc import CostFactorsSCC

    scf_dict_id = f'{calendar_year}'

    if scf_dict_id in scf_dict and not query:
        co2_domestic_25, co2_domestic_30, co2_domestic_70, \
        ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
        n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
        co2_global_25, co2_global_30, co2_global_70, \
        ch4_global_25, ch4_global_30, ch4_global_70, \
        n2o_global_25, n2o_global_30, n2o_global_70 \
            = scf_dict[scf_dict_id]
    else:
        co2_domestic_25, co2_domestic_30, co2_domestic_70, \
        ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
        n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
        co2_global_25, co2_global_30, co2_global_70, \
        ch4_global_25, ch4_global_30, ch4_global_70, \
        n2o_global_25, n2o_global_30, n2o_global_70 \
            = o2.session.query(CostFactorsSCC.co2_domestic_cost_factor_25, 
                               CostFactorsSCC.co2_domestic_cost_factor_30, 
                               CostFactorsSCC.co2_domestic_cost_factor_70,
                               CostFactorsSCC.ch4_domestic_cost_factor_25,
                               CostFactorsSCC.ch4_domestic_cost_factor_30,
                               CostFactorsSCC.ch4_domestic_cost_factor_70,
                               CostFactorsSCC.n2o_domestic_cost_factor_25,
                               CostFactorsSCC.n2o_domestic_cost_factor_30,
                               CostFactorsSCC.n2o_domestic_cost_factor_70,
                               CostFactorsSCC.co2_global_cost_factor_25,
                               CostFactorsSCC.co2_global_cost_factor_30,
                               CostFactorsSCC.co2_global_cost_factor_70,
                               CostFactorsSCC.ch4_global_cost_factor_25,
                               CostFactorsSCC.ch4_global_cost_factor_30,
                               CostFactorsSCC.ch4_global_cost_factor_70,
                               CostFactorsSCC.n2o_global_cost_factor_25,
                               CostFactorsSCC.n2o_global_cost_factor_30,
                               CostFactorsSCC.n2o_global_cost_factor_70).\
            filter(CostFactorsSCC.calendar_year == calendar_year).one()

        scf_dict[scf_dict_id] = co2_domestic_25, co2_domestic_30, co2_domestic_70, \
                                ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
                                n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
                                co2_global_25, co2_global_30, co2_global_70, \
                                ch4_global_25, ch4_global_30, ch4_global_70, \
                                n2o_global_25, n2o_global_30, n2o_global_70

    return co2_domestic_25, co2_domestic_30, co2_domestic_70, \
           ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
           n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
           co2_global_25, co2_global_30, co2_global_70, \
           ch4_global_25, ch4_global_30, ch4_global_70, \
           n2o_global_25, n2o_global_30, n2o_global_70


def get_criteria_cf(calendar_year, query=False):
    from effects.cost_factors_criteria import CostFactorsCriteria

    ccf_dict_id = f'{calendar_year}'

    if ccf_dict_id in ccf_dict and not query:
        pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7 = ccf_dict[ccf_dict_id]
    else:
        pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7 \
            = o2.session.query(CostFactorsCriteria.pm25_low_mortality_30, 
                               CostFactorsCriteria.pm25_high_mortality_30, 
                               CostFactorsCriteria.nox_low_mortality_30,
                               CostFactorsCriteria.nox_high_mortality_30,
                               CostFactorsCriteria.pm25_low_mortality_70,
                               CostFactorsCriteria.pm25_high_mortality_70,
                               CostFactorsCriteria.nox_low_mortality_70,
                               CostFactorsCriteria.nox_high_mortality_70).\
            filter(CostFactorsCriteria.calendar_year == calendar_year).one()

        ccf_dict[ccf_dict_id] = pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7

    return pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7


def calc_carbon_emission_costs(calendar_year):
    """
    Calculate social costs associated with carbon emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the monetized effects data table that is empty at this point.
    """
    from vehicle_annual_data import VehicleAnnualData
    from effects.monetized_effects_data import MonetizedEffectsData

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData).filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE monetized effects data
    # Since the monetized effects data table is empty, the med_list will store all data for this calendar year
    # and write to that table in bulk via the add all.
    med_list = list()
    for vad_veh in vad_vehs:
        co2_domestic_25, co2_domestic_30, co2_domestic_70, \
        ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
        n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
        co2_global_25, co2_global_30, co2_global_70, \
        ch4_global_25, ch4_global_30, ch4_global_70, \
        n2o_global_25, n2o_global_30, n2o_global_70 \
            = get_scc_cf(calendar_year, query=query)

        co2_domestic_25_social_cost_dollars = vad_veh.co2_total_metrictons * co2_domestic_25
        co2_domestic_30_social_cost_dollars = vad_veh.co2_total_metrictons * co2_domestic_30
        co2_domestic_70_social_cost_dollars = vad_veh.co2_total_metrictons * co2_domestic_70

        ch4_domestic_25_social_cost_dollars = vad_veh.ch4_total_metrictons * ch4_domestic_25
        ch4_domestic_30_social_cost_dollars = vad_veh.ch4_total_metrictons * ch4_domestic_30
        ch4_domestic_70_social_cost_dollars = vad_veh.ch4_total_metrictons * ch4_domestic_70

        n2o_domestic_25_social_cost_dollars = vad_veh.n2o_total_metrictons * n2o_domestic_25
        n2o_domestic_30_social_cost_dollars = vad_veh.n2o_total_metrictons * n2o_domestic_30
        n2o_domestic_70_social_cost_dollars = vad_veh.n2o_total_metrictons * n2o_domestic_70

        co2_global_25_social_cost_dollars = vad_veh.co2_total_metrictons * co2_global_25
        co2_global_30_social_cost_dollars = vad_veh.co2_total_metrictons * co2_global_30
        co2_global_70_social_cost_dollars = vad_veh.co2_total_metrictons * co2_global_70

        ch4_global_25_social_cost_dollars = vad_veh.ch4_total_metrictons * ch4_global_25
        ch4_global_30_social_cost_dollars = vad_veh.ch4_total_metrictons * ch4_global_30
        ch4_global_70_social_cost_dollars = vad_veh.ch4_total_metrictons * ch4_global_70

        n2o_global_25_social_cost_dollars = vad_veh.n2o_total_metrictons * n2o_global_25
        n2o_global_30_social_cost_dollars = vad_veh.n2o_total_metrictons * n2o_global_30
        n2o_global_70_social_cost_dollars = vad_veh.n2o_total_metrictons * n2o_global_70

        med_list.append(MonetizedEffectsData(vehicle_ID = vad_veh.vehicle_ID,
                                             calendar_year = vad_veh.calendar_year,
                                             age = vad_veh.age,
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
    o2.session.add_all(med_list)


def calc_criteria_emission_costs(calendar_year):
    """
    Calculate social costs associated with criteria emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the vehicle_annual_data table that has not been filled to this point.
    """
    from vehicle_annual_data import VehicleAnnualData
    from effects.monetized_effects_data import MonetizedEffectsData

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData).filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE monetized effects data
    for vad_veh in vad_vehs:
        med_veh = o2.session.query(MonetizedEffectsData).\
            filter(MonetizedEffectsData.vehicle_ID == vad_veh.vehicle_ID).\
            filter(MonetizedEffectsData.calendar_year == calendar_year).\
            filter(MonetizedEffectsData.age == vad_veh.age).filter(MonetizedEffectsData.discount_status == 'undiscounted').one()

        pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7 \
            = get_criteria_cf(calendar_year, query=query)

        pm25_low_mortality_30_social_cost_dollars = vad_veh.pm25_total_ustons * pm25_low_3
        pm25_high_mortality_30_social_cost_dollars = vad_veh.pm25_total_ustons * pm25_high_3

        nox_low_mortality_30_social_cost_dollars = vad_veh.nox_total_ustons * nox_low_3
        nox_high_mortality_30_social_cost_dollars = vad_veh.nox_total_ustons * nox_high_3

        pm25_low_mortality_70_social_cost_dollars = vad_veh.pm25_total_ustons * pm25_low_7
        pm25_high_mortality_70_social_cost_dollars = vad_veh.pm25_total_ustons * pm25_high_7

        nox_low_mortality_70_social_cost_dollars = vad_veh.nox_total_ustons * nox_low_7
        nox_high_mortality_70_social_cost_dollars = vad_veh.nox_total_ustons * nox_high_7

        med_dict = {'pm25_low_mortality_30_social_cost_dollars': pm25_low_mortality_30_social_cost_dollars,
                    'pm25_high_mortality_30_social_cost_dollars': pm25_high_mortality_30_social_cost_dollars,
                    'nox_low_mortality_30_social_cost_dollars': nox_low_mortality_30_social_cost_dollars,
                    'nox_high_mortality_30_social_cost_dollars': nox_high_mortality_30_social_cost_dollars,
                    'pm25_low_mortality_70_social_cost_dollars': pm25_low_mortality_70_social_cost_dollars,
                    'pm25_high_mortality_70_social_cost_dollars': pm25_high_mortality_70_social_cost_dollars,
                    'nox_low_mortality_70_social_cost_dollars': nox_low_mortality_70_social_cost_dollars,
                    'nox_high_mortality_70_social_cost_dollars': nox_high_mortality_70_social_cost_dollars,
                    }

        MonetizedEffectsData.update_undiscounted_monetized_effects_data(med_veh, med_dict)
