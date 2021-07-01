"""


----

**CODE**

"""

# import pandas as pd
# from itertools import product

from omega_model import *

# TODO refueling time; drive value; maintenance
def get_scc_cf(calendar_year):
    from cost_factors_scc import CostFactorsSCC

    cost_factors = ['co2_global_5',
                    'co2_global_3',
                    'co2_global_25',
                    'co2_global_395',
                    'ch4_global_5',
                    'ch4_global_3',
                    'ch4_global_25',
                    'ch4_global_395',
                    'n2o_global_5',
                    'n2o_global_3',
                    'n2o_global_25',
                    'n2o_global_395',
                    ]

    return CostFactorsSCC.get_cost_factors(calendar_year, cost_factors)


def get_criteria_cf(calendar_year):
    from cost_factors_criteria import CostFactorsCriteria

    cost_factors = ['pm25_tailpipe_3',
                    'pm25_upstream_3',
                    'nox_tailpipe_3',
                    'nox_upstream_3',
                    'so2_tailpipe_3',
                    'so2_upstream_3',
                    'pm25_tailpipe_7',
                    'pm25_upstream_7',
                    'nox_tailpipe_7',
                    'nox_upstream_7',
                    'so2_tailpipe_7',
                    'so2_upstream_7',
                    ]

    return CostFactorsCriteria.get_cost_factors(calendar_year, cost_factors)


def get_energysecurity_cf(calendar_year):
    from cost_factors_energysecurity import CostFactorsEnergySecurity

    cost_factors = ['dollars_per_gallon',
                    'foreign_oil_fraction',
                    ]

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_congestion_noise_cf(reg_class_id):
    from cost_factors_congestion_noise import CostFactorsCongestionNoise

    cost_factors = ['congestion_cost_dollars_per_mile',
                    'noise_cost_dollars_per_mile',
                    ]

    return CostFactorsCongestionNoise.get_cost_factors(reg_class_id, cost_factors)


def calc_carbon_emission_costs(calendar_year):
    """
    Calculate social costs associated with carbon emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects scc data table that is empty at this point.
    """
    from omega_model.producer.vehicle_annual_data import VehicleAnnualData
    from cost_effects_scc import CostEffectsSCC

    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year, ['vehicle_ID', 'age', 'co2_total_metrictons',
                                                                     'ch4_total_metrictons', 'n2o_total_metrictons'
                                                                     ]
                                                     )

    # UPDATE cost effects data
    # Since the monetized effects data table is empty, the ed_list will store all data for this calendar year
    # and write to that table in bulk via the add all.
    ed_list = list()
    for vad in vads:
        # get tons
        vehicle_ID, age, co2_tons, ch4_tons, n2o_tons = vad
        
        # get cost factors
        co2_global_5, co2_global_3, co2_global_25, co2_global_395, \
        ch4_global_5, ch4_global_3, ch4_global_25, ch4_global_395, \
        n2o_global_5, n2o_global_3, n2o_global_25, n2o_global_395 \
            = get_scc_cf(calendar_year)

        co2_global_5_cost_dollars = co2_tons * co2_global_5
        co2_global_3_cost_dollars = co2_tons * co2_global_3
        co2_global_25_cost_dollars = co2_tons * co2_global_25
        co2_global_395_cost_dollars = co2_tons * co2_global_395

        ch4_global_5_cost_dollars = ch4_tons * ch4_global_5
        ch4_global_3_cost_dollars = ch4_tons * ch4_global_3
        ch4_global_25_cost_dollars = ch4_tons * ch4_global_25
        ch4_global_395_cost_dollars = ch4_tons * ch4_global_395

        n2o_global_5_cost_dollars = n2o_tons * n2o_global_5
        n2o_global_3_cost_dollars = n2o_tons * n2o_global_3
        n2o_global_25_cost_dollars = n2o_tons * n2o_global_25
        n2o_global_395_cost_dollars = n2o_tons * n2o_global_395

        ed_list.append(CostEffectsSCC(vehicle_ID = vehicle_ID,
                                      calendar_year = calendar_year,
                                      age = age,
                                      discount_rate = 0,
                                      co2_global_5_cost_dollars = co2_global_5_cost_dollars,
                                      co2_global_3_cost_dollars = co2_global_3_cost_dollars,
                                      co2_global_25_cost_dollars = co2_global_25_cost_dollars,
                                      co2_global_395_cost_dollars = co2_global_395_cost_dollars,
                                      ch4_global_5_cost_dollars = ch4_global_5_cost_dollars,
                                      ch4_global_3_cost_dollars = ch4_global_3_cost_dollars,
                                      ch4_global_25_cost_dollars = ch4_global_25_cost_dollars,
                                      ch4_global_395_cost_dollars = ch4_global_395_cost_dollars,
                                      n2o_global_5_cost_dollars = n2o_global_5_cost_dollars,
                                      n2o_global_3_cost_dollars = n2o_global_3_cost_dollars,
                                      n2o_global_25_cost_dollars = n2o_global_25_cost_dollars,
                                      n2o_global_395_cost_dollars = n2o_global_395_cost_dollars,
                                      )
                       )
    common.omega_globals.session.add_all(ed_list)


def calc_criteria_emission_costs(calendar_year):
    """
    Calculate social costs associated with criteria emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects criteria table that has not been filled to this point.
    """
    from omega_model.producer.vehicle_annual_data import VehicleAnnualData
    from cost_effects_criteria import CostEffectsCriteria

    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year,
                                                     ['vehicle_ID', 'age', 
                                                      'pm25_tailpipe_ustons', 'nox_tailpipe_ustons', 'so2_tailpipe_ustons',
                                                      'pm25_upstream_ustons', 'nox_upstream_ustons', 'so2_upstream_ustons',
                                                      ]
                                                     )

    # UPDATE cost effects data
    ed_list = list()
    for vad in vads:
        # get tons and gallons
        vehicle_ID, age, pm25_tp_tons, nox_tp_tons, so2_tp_tons, pm25_up_tons, nox_up_tons, so2_up_tons = vad

        # get cost factors
        pm25_tailpipe_3, pm25_upstream_3, nox_tailpipe_3, nox_upstream_3, so2_tailpipe_3, so2_upstream_3, \
        pm25_tailpipe_7, pm25_upstream_7, nox_tailpipe_7, nox_upstream_7, so2_tailpipe_7, so2_upstream_7 = get_criteria_cf(calendar_year)

        pm25_tailpipe_3_cost_dollars = pm25_tp_tons * pm25_tailpipe_3
        pm25_upstream_3_cost_dollars = pm25_up_tons * pm25_upstream_3

        nox_tailpipe_3_cost_dollars = nox_tp_tons * nox_tailpipe_3
        nox_upstream_3_cost_dollars = nox_up_tons * nox_upstream_3

        so2_tailpipe_3_cost_dollars = so2_tp_tons * so2_tailpipe_3
        so2_upstream_3_cost_dollars = so2_up_tons * so2_upstream_3

        pm25_tailpipe_7_cost_dollars = pm25_tp_tons * pm25_tailpipe_7
        pm25_upstream_7_cost_dollars = pm25_up_tons * pm25_upstream_7

        nox_tailpipe_7_cost_dollars = nox_tp_tons * nox_tailpipe_7
        nox_upstream_7_cost_dollars = nox_up_tons * nox_upstream_7

        so2_tailpipe_7_cost_dollars = so2_tp_tons * so2_tailpipe_7
        so2_upstream_7_cost_dollars = so2_up_tons * so2_upstream_7
        
        criteria_tailpipe_3_cost_dollars = pm25_tailpipe_3_cost_dollars + nox_tailpipe_3_cost_dollars + so2_tailpipe_3_cost_dollars
        criteria_upstream_3_cost_dollars = pm25_upstream_3_cost_dollars + nox_upstream_3_cost_dollars + so2_upstream_3_cost_dollars

        criteria_tailpipe_7_cost_dollars = pm25_tailpipe_7_cost_dollars + nox_tailpipe_7_cost_dollars + so2_tailpipe_7_cost_dollars
        criteria_upstream_7_cost_dollars = pm25_upstream_7_cost_dollars + nox_upstream_7_cost_dollars + so2_upstream_7_cost_dollars

        criteria_3_cost_dollars = criteria_tailpipe_3_cost_dollars + criteria_upstream_3_cost_dollars
        criteria_7_cost_dollars = criteria_tailpipe_7_cost_dollars + criteria_upstream_7_cost_dollars
        
        ed_list.append(CostEffectsCriteria(vehicle_ID = vehicle_ID,
                                           calendar_year = calendar_year,
                                           age = age,
                                           discount_rate = 0,
                                           pm25_tailpipe_3_cost_dollars = pm25_tailpipe_3_cost_dollars,
                                           pm25_upstream_3_cost_dollars = pm25_upstream_3_cost_dollars,
                                           nox_tailpipe_3_cost_dollars = nox_tailpipe_3_cost_dollars,
                                           nox_upstream_3_cost_dollars = nox_upstream_3_cost_dollars,
                                           so2_tailpipe_3_cost_dollars = so2_tailpipe_3_cost_dollars,
                                           so2_upstream_3_cost_dollars = so2_upstream_3_cost_dollars,
                                           pm25_tailpipe_7_cost_dollars = pm25_tailpipe_7_cost_dollars,
                                           pm25_upstream_7_cost_dollars = pm25_upstream_7_cost_dollars,
                                           nox_tailpipe_7_cost_dollars = nox_tailpipe_7_cost_dollars,
                                           nox_upstream_7_cost_dollars = nox_upstream_7_cost_dollars,
                                           so2_tailpipe_7_cost_dollars = so2_tailpipe_7_cost_dollars,
                                           so2_upstream_7_cost_dollars = so2_upstream_7_cost_dollars,
                                           criteria_tailpipe_3_cost_dollars=criteria_tailpipe_3_cost_dollars,
                                           criteria_upstream_3_cost_dollars=criteria_upstream_3_cost_dollars,
                                           criteria_tailpipe_7_cost_dollars=criteria_tailpipe_7_cost_dollars,
                                           criteria_upstream_7_cost_dollars=criteria_upstream_7_cost_dollars,
                                           criteria_3_cost_dollars=criteria_3_cost_dollars,
                                           criteria_7_cost_dollars=criteria_7_cost_dollars,
                                           )
                        )
    common.omega_globals.session.add_all(ed_list)


def calc_non_emission_costs(calendar_year): # TODO congestion/noise/other?
    """
    Calculate social costs associated with fuel consumption by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects non-emissions table that has not been filled to this point.
    """
    from omega_model.producer.vehicle_annual_data import VehicleAnnualData
    from cost_effects_non_emissions import CostEffectsNonEmissions
    from omega_model.context.fuel_prices import FuelPrice
    from omega_model.producer.vehicles import VehicleFinal

    # get vehicle annual data
    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year, ['vehicle_ID', 'age', 'fuel_consumption', 'vmt'])

    # UPDATE cost effects data
    ed_list = list()
    for vehicle_ID, age, fuel_consumption, vmt in vads:

        # get vehicle final data
        reg_class_ID, in_use_fuel_ID = VehicleFinal.get_vehicle_attributes(vehicle_ID, ['reg_class_ID', 'in_use_fuel_ID'])

        # get fuel prices
        # retail, pretax = ContextFuelPrices.get_fuel_prices(calendar_year,
        #                                                   ['retail_dollars_per_unit', 'pretax_dollars_per_unit'],
        #                                                   in_use_fuel_ID)

        retail = 0
        fuel_dict = eval(in_use_fuel_ID, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            retail += FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel) * fuel_share

        pretax = 0
        fuel_dict = eval(in_use_fuel_ID, {'__builtins__': None}, {})
        for fuel, fuel_share in fuel_dict.items():
            pretax += FuelPrice.get_fuel_prices(calendar_year, 'pretax_dollars_per_unit', fuel) * fuel_share

        # fuel costs
        fuel_retail_cost_dollars = fuel_consumption * retail
        fuel_pretax_cost_dollars = fuel_consumption * pretax

        # get energy security cost factors
        es_cost_factor, foreign_oil_fraction = get_energysecurity_cf(calendar_year)

        # energy security
        if in_use_fuel_ID == 'pump gasoline':
            energy_security_cost_dollars = fuel_consumption * es_cost_factor * foreign_oil_fraction
        else:
            energy_security_cost_dollars = 0

        # get congestion and noise cost factors
        congestion_cf, noise_cf = get_congestion_noise_cf(reg_class_ID)

        # congestion and noise costs
        congestion_cost_dollars = vmt * congestion_cf
        noise_cost_dollars = vmt * noise_cf

        ed_list.append(CostEffectsNonEmissions(vehicle_ID=vehicle_ID,
                                               calendar_year=calendar_year,
                                               age=age,
                                               discount_status=0,
                                               fuel_retail_cost_dollars=fuel_retail_cost_dollars,
                                               fuel_pretax_cost_dollars=fuel_pretax_cost_dollars,
                                               energy_security_cost_dollars=energy_security_cost_dollars,
                                               congestion_cost_dollars=congestion_cost_dollars,
                                               noise_cost_dollars=noise_cost_dollars,
                                               )
                        )
    common.omega_globals.session.add_all(ed_list)
