"""


----

**CODE**

"""

# import pandas as pd
# from itertools import product

from omega_model import *


def get_scc_cf(calendar_year):
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


def get_criteria_cf(calendar_year):
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


def get_energysecurity_cf(calendar_year):
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    cost_factors = [
        'dollars_per_gallon',
        'foreign_oil_fraction',
    ]

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_congestion_noise_cf(reg_class_id):
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise

    cost_factors = [
        'congestion_cost_dollars_per_mile',
        'noise_cost_dollars_per_mile',
    ]

    return CostFactorsCongestionNoise.get_cost_factors(reg_class_id, cost_factors)


def calc_carbon_emission_costs(calendar_year):
    """
    Calculate social costs associated with carbon emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects scc data table that is empty at this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from effects.cost_effects_scc import CostEffectsSCC

    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year, ['vehicle_ID', 'age', 'co2_total_metrictons',
                                                                     'ch4_total_metrictons', 'n2o_vehicle_metrictons'])

    # UPDATE cost effects data
    # Since the monetized effects data table is empty, the ed_list will store all data for this calendar year
    # and write to that table in bulk via the add all.
    ed_list = list()
    for vad in vads:
        # get tons
        vehicle_ID, age, co2_tons, ch4_tons, n2o_tons = vad[0], vad[1], vad[2], vad[3], vad[4]
        
        # get cost factors
        co2_domestic_25, co2_domestic_30, co2_domestic_70, \
        ch4_domestic_25, ch4_domestic_30, ch4_domestic_70, \
        n2o_domestic_25, n2o_domestic_30, n2o_domestic_70, \
        co2_global_25, co2_global_30, co2_global_70, \
        ch4_global_25, ch4_global_30, ch4_global_70, \
        n2o_global_25, n2o_global_30, n2o_global_70 \
            = get_scc_cf(calendar_year)

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
    omega_globals.session.add_all(ed_list)


def calc_criteria_emission_costs(calendar_year):
    """
    Calculate social costs associated with criteria emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects criteria table that has not been filled to this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from effects.cost_effects_criteria import CostEffectsCriteria

    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year,
                                                     ['vehicle_ID', 'age', 'pm25_total_ustons', 'nox_total_ustons'])

    # UPDATE cost effects data
    ed_list = list()
    for vad in vads:
        # get tons
        vehicle_ID, age, pm25_tons, nox_tons = vad[0], vad[1], vad[2], vad[3]

        # get cost factors
        pm25_low_3, pm25_high_3, nox_low_3, nox_high_3, pm25_low_7, pm25_high_7, nox_low_7, nox_high_7 \
            = get_criteria_cf(calendar_year)

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
    omega_globals.session.add_all(ed_list)


def calc_non_emission_costs(calendar_year): # TODO congestion/noise/other?
    """
    Calculate social costs associated with fuel consumption by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects non-emissions table that has not been filled to this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from effects.cost_effects_non_emissions import CostEffectsNonEmissions
    from context.fuel_prices import FuelPrice
    from producer.vehicles import VehicleFinal

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
        fuel_30_retail_cost_dollars = fuel_consumption * retail
        fuel_70_retail_cost_dollars = fuel_consumption * retail
        fuel_30_social_cost_dollars = fuel_consumption * pretax
        fuel_70_social_cost_dollars = fuel_consumption * pretax

        # get energy security cost factors
        es_cost_factor, foreign_oil_fraction = get_energysecurity_cf(calendar_year)

        # energy security
        if in_use_fuel_ID == 'pump gasoline':
            energy_security_30_social_cost_dollars = fuel_consumption * es_cost_factor * foreign_oil_fraction
            energy_security_70_social_cost_dollars = fuel_consumption * es_cost_factor * foreign_oil_fraction
        else:
            energy_security_30_social_cost_dollars, energy_security_70_social_cost_dollars = 0, 0

        # get congestion and noise cost factors
        congestion_cf, noise_cf = get_congestion_noise_cf(reg_class_ID)

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
    omega_globals.session.add_all(ed_list)
