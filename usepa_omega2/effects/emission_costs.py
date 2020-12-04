"""

emission_costs.py
============
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


def calc_carbon_emission_costs(calendar_year):
    """
    Calculate social costs associated with carbon emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the vehicle_annual_data table that has not been filled to this point.
    """
    from vehicle_annual_data import VehicleAnnualData

    query = False

    vad_vehs = o2.session.query(VehicleAnnualData).filter(VehicleAnnualData.calendar_year == calendar_year).all()

    # UPDATE vehicle annual data related to effects
    for vad_veh in vad_vehs:
        co2_domestic_25, co2_domestic_30, co2_domestic_70, \
        ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
        n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
        co2_global_25, co2_global_30, co2_global_70, \
        ch4_global_25, ch4_global_30, ch4_global_70, \
        n2o_global_25, n2o_global_30, n2o_global_70 \
            = get_scc_cf(calendar_year, query=query)

        co2_metrictons = vad_veh.co2_vehicle_metrictons + vad_veh.co2_upstream_metrictons
        ch4_metrictons = vad_veh.ch4_vehicle_metrictons + vad_veh.ch4_upstream_metrictons
        n2o_metrictons = vad_veh.n2o_vehicle_metrictons + vad_veh.n2o_upstream_metrictons
        
        vad_veh.co2_domestic_25_social_cost_dollars = co2_metrictons * co2_domestic_25
        vad_veh.co2_domestic_30_social_cost_dollars = co2_metrictons * co2_domestic_30
        vad_veh.co2_domestic_70_social_cost_dollars = co2_metrictons * co2_domestic_70

        vad_veh.ch4_domestic_25_social_cost_dollars = ch4_metrictons * ch4_domestic_25
        vad_veh.ch4_domestic_30_social_cost_dollars = ch4_metrictons * ch4_domestic_30
        vad_veh.ch4_domestic_70_social_cost_dollars = ch4_metrictons * ch4_domestic_70

        vad_veh.n2o_domestic_25_social_cost_dollars = n2o_metrictons * n2o_domestic_25
        vad_veh.n2o_domestic_30_social_cost_dollars = n2o_metrictons * n2o_domestic_30
        vad_veh.n2o_domestic_70_social_cost_dollars = n2o_metrictons * n2o_domestic_70
        
        vad_veh.co2_global_25_social_cost_dollars = co2_metrictons * co2_global_25
        vad_veh.co2_global_30_social_cost_dollars = co2_metrictons * co2_global_30
        vad_veh.co2_global_70_social_cost_dollars = co2_metrictons * co2_global_70

        vad_veh.ch4_global_25_social_cost_dollars = ch4_metrictons * ch4_global_25
        vad_veh.ch4_global_30_social_cost_dollars = ch4_metrictons * ch4_global_30
        vad_veh.ch4_global_70_social_cost_dollars = ch4_metrictons * ch4_global_70

        vad_veh.n2o_global_25_social_cost_dollars = n2o_metrictons * n2o_global_25
        vad_veh.n2o_global_30_social_cost_dollars = n2o_metrictons * n2o_global_30
        vad_veh.n2o_global_70_social_cost_dollars = n2o_metrictons * n2o_global_70


def calc_criteria_emission_costs(calendar_year):
    """
    Calculate social costs associated with criteria emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the vehicle_annual_data table that has not been filled to this point.
    """
    pass
