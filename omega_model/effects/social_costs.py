"""


----

**CODE**

"""

# import pandas as pd
# from itertools import product

from omega_model import *

vehicles_dict = dict()


# TODO refueling time; drive value; maintenance
def get_vehicle_info(vehicle_id, attribute_list):
    """

    """
    from producer.vehicles import VehicleFinal

    if vehicle_id not in vehicles_dict:
        vehicles_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)

    return vehicles_dict[vehicle_id]


def get_scc_cf(calendar_year):
    from effects.cost_factors_scc import CostFactorsSCC

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
    from effects.cost_factors_criteria import CostFactorsCriteria

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
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    # cost_factors = ['dollars_per_gallon',
    #                 'foreign_oil_fraction',
    #                 ]
    cost_factors = ['dollars_per_gallon',
                    ]

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_congestion_noise_cf(reg_class_id):
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise

    cost_factors = ['congestion_cost_dollars_per_mile',
                    'noise_cost_dollars_per_mile',
                    ]

    return CostFactorsCongestionNoise.get_cost_factors(reg_class_id, cost_factors)


def calc_carbon_emission_costs(calendar_year, cost_effects_dict):
    """
    Calculate social costs associated with carbon emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects scc data table that is empty at this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    # from effects.cost_effects_scc import CostEffectsSCC

    # get vehicle annual data
    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

    for vad in vads:

        veh_cost_effects_dict = dict()
        if vad.onroad_direct_co2_grams_per_mile or vad.onroad_direct_kwh_per_mile:

            co2_tons = vad.co2_total_metrictons
            ch4_tons = vad.ch4_total_metrictons
            n2o_tons = vad.n2o_total_metrictons

            # get cost factors
            co2_global_5, co2_global_3, co2_global_25, co2_global_395, \
            ch4_global_5, ch4_global_3, ch4_global_25, ch4_global_395, \
            n2o_global_5, n2o_global_3, n2o_global_25, n2o_global_395 \
                = get_scc_cf(calendar_year)

            # UPDATE cost effects dict
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

            veh_cost_effects_dict.update({'co2_global_5_cost_dollars': co2_global_5_cost_dollars,
                                          'co2_global_3_cost_dollars': co2_global_3_cost_dollars,
                                          'co2_global_25_cost_dollars': co2_global_25_cost_dollars,
                                          'co2_global_395_cost_dollars': co2_global_395_cost_dollars,
                                          'ch4_global_5_cost_dollars': ch4_global_5_cost_dollars,
                                          'ch4_global_3_cost_dollars': ch4_global_3_cost_dollars,
                                          'ch4_global_25_cost_dollars': ch4_global_25_cost_dollars,
                                          'ch4_global_395_cost_dollars': ch4_global_395_cost_dollars,
                                          'n2o_global_5_cost_dollars': n2o_global_5_cost_dollars,
                                          'n2o_global_3_cost_dollars': n2o_global_3_cost_dollars,
                                          'n2o_global_25_cost_dollars': n2o_global_25_cost_dollars,
                                          'n2o_global_395_cost_dollars': n2o_global_395_cost_dollars,
                                          }
                                         )
        discount_rate = 0
        key = (vad.vehicle_ID, calendar_year, vad.age, discount_rate)
        cost_effects_dict[key].update(veh_cost_effects_dict)
    return cost_effects_dict
            # cost_effects_list.append(CostEffectsSCC(vehicle_ID = vad.vehicle_ID,
            #                                         calendar_year = calendar_year,
            #                                         age = vad.age,
            #                                         discount_rate = 0,
            #                                         co2_global_5_cost_dollars = co2_global_5_cost_dollars,
            #                                         co2_global_3_cost_dollars = co2_global_3_cost_dollars,
            #                                         co2_global_25_cost_dollars = co2_global_25_cost_dollars,
            #                                         co2_global_395_cost_dollars = co2_global_395_cost_dollars,
            #                                         ch4_global_5_cost_dollars = ch4_global_5_cost_dollars,
            #                                         ch4_global_3_cost_dollars = ch4_global_3_cost_dollars,
            #                                         ch4_global_25_cost_dollars = ch4_global_25_cost_dollars,
            #                                         ch4_global_395_cost_dollars = ch4_global_395_cost_dollars,
            #                                         n2o_global_5_cost_dollars = n2o_global_5_cost_dollars,
            #                                         n2o_global_3_cost_dollars = n2o_global_3_cost_dollars,
            #                                         n2o_global_25_cost_dollars = n2o_global_25_cost_dollars,
            #                                         n2o_global_395_cost_dollars = n2o_global_395_cost_dollars,
            #                                         )
            #                          )
            # omega_globals.session.add_all(cost_effects_list)


def calc_criteria_emission_costs(calendar_year, cost_effects_dict):
    """
    Calculate social costs associated with criteria emissions by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects criteria table that has not been filled to this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    # from effects.cost_effects_criteria import CostEffectsCriteria

    # get vehicle annual data
    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

    for vad in vads:

        veh_cost_effects_dict = dict()
        if vad.onroad_direct_co2_grams_per_mile or vad.onroad_direct_kwh_per_mile:

            pm25_tp_tons = vad.pm25_tailpipe_ustons
            pm25_up_tons = vad.pm25_upstream_ustons

            nox_tp_tons = vad.nox_tailpipe_ustons
            nox_up_tons = vad.nox_upstream_ustons

            so2_tp_tons = vad.so2_tailpipe_ustons
            so2_up_tons = vad.so2_upstream_ustons

            # get cost factors
            pm25_tailpipe_3, pm25_upstream_3, nox_tailpipe_3, nox_upstream_3, so2_tailpipe_3, so2_upstream_3, \
            pm25_tailpipe_7, pm25_upstream_7, nox_tailpipe_7, nox_upstream_7, so2_tailpipe_7, so2_upstream_7 = get_criteria_cf(calendar_year)

            # UPDATE cost effects data
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

            veh_cost_effects_dict.update({'pm25_tailpipe_3_cost_dollars': pm25_tailpipe_3_cost_dollars,
                                          'pm25_upstream_3_cost_dollars': pm25_upstream_3_cost_dollars,
                                          'nox_tailpipe_3_cost_dollars': nox_tailpipe_3_cost_dollars,
                                          'nox_upstream_3_cost_dollars': nox_upstream_3_cost_dollars,
                                          'so2_tailpipe_3_cost_dollars': so2_tailpipe_3_cost_dollars,
                                          'so2_upstream_3_cost_dollars': so2_upstream_3_cost_dollars,
                                          'pm25_tailpipe_7_cost_dollars': pm25_tailpipe_7_cost_dollars,
                                          'pm25_upstream_7_cost_dollars': pm25_upstream_7_cost_dollars,
                                          'nox_tailpipe_7_cost_dollars': nox_tailpipe_7_cost_dollars,
                                          'nox_upstream_7_cost_dollars': nox_upstream_7_cost_dollars,
                                          'so2_tailpipe_7_cost_dollars': so2_tailpipe_7_cost_dollars,
                                          'so2_upstream_7_cost_dollars': so2_upstream_7_cost_dollars,
                                          'criteria_tailpipe_3_cost_dollars': criteria_tailpipe_3_cost_dollars,
                                          'criteria_upstream_3_cost_dollars': criteria_upstream_3_cost_dollars,
                                          'criteria_tailpipe_7_cost_dollars': criteria_tailpipe_7_cost_dollars,
                                          'criteria_upstream_7_cost_dollars': criteria_upstream_7_cost_dollars,
                                          'criteria_3_cost_dollars': criteria_3_cost_dollars,
                                          'criteria_7_cost_dollars': criteria_7_cost_dollars,
                                          }
                                         )
        discount_rate = 0
        key = (vad.vehicle_ID, calendar_year, vad.age, discount_rate)
        cost_effects_dict[key].update(veh_cost_effects_dict)
    return cost_effects_dict
            
            # cost_effects_list.append(CostEffectsCriteria(vehicle_ID = vad.vehicle_ID,
            #                                              calendar_year = calendar_year,
            #                                              age = vad.age,
            #                                              discount_rate = 0,
            #                                              pm25_tailpipe_3_cost_dollars = pm25_tailpipe_3_cost_dollars,
            #                                              pm25_upstream_3_cost_dollars = pm25_upstream_3_cost_dollars,
            #                                              nox_tailpipe_3_cost_dollars = nox_tailpipe_3_cost_dollars,
            #                                              nox_upstream_3_cost_dollars = nox_upstream_3_cost_dollars,
            #                                              so2_tailpipe_3_cost_dollars = so2_tailpipe_3_cost_dollars,
            #                                              so2_upstream_3_cost_dollars = so2_upstream_3_cost_dollars,
            #                                              pm25_tailpipe_7_cost_dollars = pm25_tailpipe_7_cost_dollars,
            #                                              pm25_upstream_7_cost_dollars = pm25_upstream_7_cost_dollars,
            #                                              nox_tailpipe_7_cost_dollars = nox_tailpipe_7_cost_dollars,
            #                                              nox_upstream_7_cost_dollars = nox_upstream_7_cost_dollars,
            #                                              so2_tailpipe_7_cost_dollars = so2_tailpipe_7_cost_dollars,
            #                                              so2_upstream_7_cost_dollars = so2_upstream_7_cost_dollars,
            #                                              criteria_tailpipe_3_cost_dollars=criteria_tailpipe_3_cost_dollars,
            #                                              criteria_upstream_3_cost_dollars=criteria_upstream_3_cost_dollars,
            #                                              criteria_tailpipe_7_cost_dollars=criteria_tailpipe_7_cost_dollars,
            #                                              criteria_upstream_7_cost_dollars=criteria_upstream_7_cost_dollars,
            #                                              criteria_3_cost_dollars=criteria_3_cost_dollars,
            #                                              criteria_7_cost_dollars=criteria_7_cost_dollars,
            #                                              )
            #                          )
            # omega_globals.session.add_all(cost_effects_list)


def calc_non_emission_costs(calendar_year):
    """
    Calculate social costs associated with fuel consumption by calendar year for vehicles in the vehicle_annual_data table.
    :param calendar_year: calendar year
    :return: Fills data in the cost effects non-emissions table that has not been filled to this point.
    """
    from producer.vehicle_annual_data import VehicleAnnualData
    # from effects.cost_effects_non_emissions import CostEffectsNonEmissions
    from context.fuel_prices import FuelPrice

    # get vehicle annual data
    vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

    # UPDATE cost effects data
    calendar_year_cost_effects_dict = dict()
    fuel = None
    for vad in vads:

        veh_cost_effects_dict = dict()
        if vad.onroad_direct_co2_grams_per_mile or vad.onroad_direct_kwh_per_mile:

            attribute_list = ['reg_class_ID', 'in_use_fuel_ID']
            reg_class_ID, in_use_fuel_ID = get_vehicle_info(vad.vehicle_ID, attribute_list)
            #
            # cost_args = ['fuel_retail_cost_dollars',
            #              'fuel_pretax_cost_dollars',
            #              'energy_security_cost_dollars',
            #              'congestion_cost_dollars',
            #              'noise_cost_dollars',
            #              'maintenance_cost_dollars',
            #              'refueling_cost_dollars',
            #              'driving_cost_dollars',
            #              ]
            # cost_arg_dict = dict()
            # for arg in cost_args:
            #     cost_arg_dict.update({arg: 0})

            fuel_retail_cost_dollars = 0
            fuel_pretax_cost_dollars = 0
            energy_security_cost_dollars = 0
            congestion_cost_dollars = 0
            noise_cost_dollars = 0
            maintenance_cost_dollars = 0
            refueling_cost_dollars = 0
            driving_cost_dollars = 0

            # fuel costs
            fuel_dict = eval(in_use_fuel_ID, {'__builtins__': None}, {})
            for fuel, fuel_share in fuel_dict.items():
                price = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel)
                if fuel == 'US electricity' and vad.fuel_consumption_kWh:
                    fuel_retail_cost_dollars += price * vad.fuel_consumption_kWh
                elif fuel != 'US electricity' and vad.fuel_consumption_gallons:
                    fuel_retail_cost_dollars += price * vad.fuel_consumption_gallons

            for fuel, fuel_share in fuel_dict.items():
                price = FuelPrice.get_fuel_prices(calendar_year, 'pretax_dollars_per_unit', fuel)
                if fuel == 'US electricity' and vad.fuel_consumption_kWh:
                    fuel_pretax_cost_dollars += price * vad.fuel_consumption_kWh
                elif fuel != 'US electricity' and vad.fuel_consumption_gallons:
                    fuel_pretax_cost_dollars += price * vad.fuel_consumption_gallons

            # get energy security cost factors
            energy_security_cf = get_energysecurity_cf(calendar_year)

            # energy security # TODO the import/domestic fraction element should come from an as yet created input file with domestic vs import data
            if fuel == 'US electricity':
                pass
            elif fuel != 'US electricity' and vad.fuel_consumption_gallons:
                energy_security_cost_dollars += vad.fuel_consumption_gallons * energy_security_cf

            # get congestion and noise cost factors
            congestion_cf, noise_cf = get_congestion_noise_cf(reg_class_ID)

            # congestion and noise costs
            if vad.vmt_electricity:
                congestion_cost_dollars += vad.vmt_electricity * congestion_cf
                noise_cost_dollars += vad.vmt_electricity * noise_cf
            if vad.vmt_liquid_fuel:
                congestion_cost_dollars += vad.vmt_liquid_fuel * congestion_cf
                noise_cost_dollars += vad.vmt_liquid_fuel * noise_cf

            veh_cost_effects_dict.update({'model_year': calendar_year - vad.age,
                                          'reg_class_ID': reg_class_ID,
                                          'in_use_fuel_ID': in_use_fuel_ID,
                                          'fuel_retail_cost_dollars': fuel_retail_cost_dollars,
                                          'fuel_pretax_cost_dollars': fuel_pretax_cost_dollars,
                                          'energy_security_cost_dollars': energy_security_cost_dollars,
                                          'congestion_cost_dollars': congestion_cost_dollars,
                                          'noise_cost_dollars': noise_cost_dollars,
                                          'maintenance_cost_dollars': maintenance_cost_dollars,
                                          'refueling_cost_dollars': refueling_cost_dollars,
                                          'driving_cost_dollars': driving_cost_dollars
                                          }
                                         )
        discount_rate = 0
        key = (vad.vehicle_ID, calendar_year, vad.age, discount_rate)
        calendar_year_cost_effects_dict[key] = veh_cost_effects_dict

    return calendar_year_cost_effects_dict
        # return calendar_year_cost_effects_dict
        #     cost_effects_list.append(CostEffectsNonEmissions(vehicle_ID=vad.vehicle_ID,
        #                                                      calendar_year=calendar_year,
        #                                                      age=vad.age,
        #                                                      discount_rate=0,
        #                                                      fuel_retail_cost_dollars=fuel_retail_cost_dollars,
        #                                                      fuel_pretax_cost_dollars=fuel_pretax_cost_dollars,
        #                                                      energy_security_cost_dollars=energy_security_cost_dollars,
        #                                                      congestion_cost_dollars=congestion_cost_dollars,
        #                                                      noise_cost_dollars=noise_cost_dollars,
        #                                                      maintenance_cost_dollars=maintenance_cost_dollars,
        #                                                      refueling_cost_dollars=refueling_cost_dollars,
        #                                                      driving_cost_dollars=driving_cost_dollars,
        #                                                      )
        #                     )
        # omega_globals.session.add_all(cost_effects_list)


def calc_cost_effects(physical_effects_dict):
    # from producer.vehicle_annual_data import VehicleAnnualData
    # from effects.cost_effects_non_emissions import CostEffectsNonEmissions
    from context.fuel_prices import FuelPrice

    # get vehicle annual data
    # vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)
# TODO tech costs come from .... where?
    # UPDATE cost effects data
    costs_dict = dict()
    fuel = None
    for key in physical_effects_dict.keys():

        vehicle_ID, calendar_year, age = key
        physical = physical_effects_dict[key]

        attribute_list = ['reg_class_ID', 'in_use_fuel_ID', 'onroad_direct_co2_grams_per_mile', 'onroad_direct_kwh_per_mile']
        reg_class_ID, in_use_fuel_ID, onroad_direct_co2_grams_per_mile, onroad_direct_kwh_per_mile \
            = get_vehicle_info(vehicle_ID, attribute_list)

        veh_effects_dict = dict()
        flag = None
        if onroad_direct_co2_grams_per_mile or onroad_direct_kwh_per_mile:
            flag = 1

            fuel_retail_cost_dollars = 0
            fuel_pretax_cost_dollars = 0
            energy_security_cost_dollars = 0
            congestion_cost_dollars = 0
            noise_cost_dollars = 0
            maintenance_cost_dollars = 0
            refueling_cost_dollars = 0
            driving_cost_dollars = 0
            pm25_tailpipe_3, pm25_upstream_3, nox_tailpipe_3, nox_upstream_3, so2_tailpipe_3, so2_upstream_3, \
            pm25_tailpipe_7, pm25_upstream_7, nox_tailpipe_7, nox_upstream_7, so2_tailpipe_7, so2_upstream_7 = 12 * [0]

            # fuel costs
            fuel_dict = eval(in_use_fuel_ID, {'__builtins__': None}, {})
            for fuel, fuel_share in fuel_dict.items():
                price = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel)
                if fuel == 'US electricity' and physical['fuel_consumption_kWh']:
                    fuel_retail_cost_dollars += price * physical['fuel_consumption_kWh']
                elif fuel != 'US electricity' and physical['fuel_consumption_gallons']:
                    fuel_retail_cost_dollars += price * physical['fuel_consumption_gallons']

            for fuel, fuel_share in fuel_dict.items():
                price = FuelPrice.get_fuel_prices(calendar_year, 'pretax_dollars_per_unit', fuel)
                if fuel == 'US electricity' and physical['fuel_consumption_kWh']:
                    fuel_pretax_cost_dollars += price * physical['fuel_consumption_kWh']
                elif fuel != 'US electricity' and physical['fuel_consumption_gallons']:
                    fuel_pretax_cost_dollars += price * physical['fuel_consumption_gallons']

            # get energy security cost factors
            energy_security_cf = get_energysecurity_cf(calendar_year)

            # energy security # TODO the import/domestic fraction element should come from an as yet created input file with domestic vs import data
            if fuel == 'US electricity':
                pass
            elif fuel != 'US electricity' and physical['fuel_consumption_gallons']:
                energy_security_cost_dollars += physical['fuel_consumption_gallons'] * energy_security_cf

            # get congestion and noise cost factors
            congestion_cf, noise_cf = get_congestion_noise_cf(reg_class_ID)

            # congestion and noise costs (maybe congestion and noise cost factors will differ one day?)
            if physical['vmt_electricity']:
                congestion_cost_dollars += physical['vmt_electricity'] * congestion_cf
                noise_cost_dollars += physical['vmt_electricity'] * noise_cf
            if physical['vmt_liquid_fuel']:
                congestion_cost_dollars += physical['vmt_liquid_fuel'] * congestion_cf
                noise_cost_dollars += physical['vmt_liquid_fuel'] * noise_cf

            # climate effects
            co2_tons = physical['co2_total_metrictons']
            ch4_tons = physical['ch4_total_metrictons']
            n2o_tons = physical['n2o_total_metrictons']

            # get cost factors
            co2_global_5, co2_global_3, co2_global_25, co2_global_395, \
            ch4_global_5, ch4_global_3, ch4_global_25, ch4_global_395, \
            n2o_global_5, n2o_global_3, n2o_global_25, n2o_global_395 \
                = get_scc_cf(calendar_year)

            # UPDATE cost effects dict
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
            
            ghg_global_5_cost_dollars = co2_global_5_cost_dollars + ch4_global_5_cost_dollars + n2o_global_5_cost_dollars
            ghg_global_3_cost_dollars = co2_global_3_cost_dollars + ch4_global_3_cost_dollars + n2o_global_3_cost_dollars
            ghg_global_25_cost_dollars = co2_global_25_cost_dollars + ch4_global_25_cost_dollars + n2o_global_25_cost_dollars
            ghg_global_395_cost_dollars = co2_global_395_cost_dollars + ch4_global_395_cost_dollars + n2o_global_395_cost_dollars            

            # criteria effects
            if omega_globals.options.calc_criteria_emission_costs:
                pm25_tp_tons = physical['pm25_tailpipe_ustons']
                pm25_up_tons = physical['pm25_upstream_ustons']

                nox_tp_tons = physical['nox_tailpipe_ustons']
                nox_up_tons = physical['nox_upstream_ustons']

                so2_tp_tons = physical['so2_tailpipe_ustons']
                so2_up_tons = physical['so2_upstream_ustons']

                # get cost factors
                pm25_tailpipe_3, pm25_upstream_3, nox_tailpipe_3, nox_upstream_3, so2_tailpipe_3, so2_upstream_3, \
                pm25_tailpipe_7, pm25_upstream_7, nox_tailpipe_7, nox_upstream_7, so2_tailpipe_7, so2_upstream_7 = get_criteria_cf(calendar_year)

                # UPDATE cost effects data
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

            veh_effects_dict.update({'model_year': calendar_year - age,
                                     'reg_class_ID': reg_class_ID,
                                     'in_use_fuel_ID': in_use_fuel_ID,
                                     'fuel_retail_cost_dollars': fuel_retail_cost_dollars,
                                     'fuel_pretax_cost_dollars': fuel_pretax_cost_dollars,
                                     'energy_security_cost_dollars': energy_security_cost_dollars,
                                     'congestion_cost_dollars': congestion_cost_dollars,
                                     'noise_cost_dollars': noise_cost_dollars,
                                     'maintenance_cost_dollars': maintenance_cost_dollars,
                                     'refueling_cost_dollars': refueling_cost_dollars,
                                     'driving_cost_dollars': driving_cost_dollars,

                                     'co2_global_5_cost_dollars': co2_global_5_cost_dollars,
                                     'co2_global_3_cost_dollars': co2_global_3_cost_dollars,
                                     'co2_global_25_cost_dollars': co2_global_25_cost_dollars,
                                     'co2_global_395_cost_dollars': co2_global_395_cost_dollars,
                                     'ch4_global_5_cost_dollars': ch4_global_5_cost_dollars,
                                     'ch4_global_3_cost_dollars': ch4_global_3_cost_dollars,
                                     'ch4_global_25_cost_dollars': ch4_global_25_cost_dollars,
                                     'ch4_global_395_cost_dollars': ch4_global_395_cost_dollars,
                                     'n2o_global_5_cost_dollars': n2o_global_5_cost_dollars,
                                     'n2o_global_3_cost_dollars': n2o_global_3_cost_dollars,
                                     'n2o_global_25_cost_dollars': n2o_global_25_cost_dollars,
                                     'n2o_global_395_cost_dollars': n2o_global_395_cost_dollars,
                                     'ghg_global_5_cost_dollars': ghg_global_5_cost_dollars,
                                     'ghg_global_3_cost_dollars': ghg_global_3_cost_dollars,
                                     'ghg_global_25_cost_dollars': ghg_global_25_cost_dollars,
                                     'ghg_global_395_cost_dollars': ghg_global_395_cost_dollars,

                                     'pm25_tailpipe_3_cost_dollars': pm25_tailpipe_3_cost_dollars,
                                     'pm25_upstream_3_cost_dollars': pm25_upstream_3_cost_dollars,
                                     'nox_tailpipe_3_cost_dollars': nox_tailpipe_3_cost_dollars,
                                     'nox_upstream_3_cost_dollars': nox_upstream_3_cost_dollars,
                                     'so2_tailpipe_3_cost_dollars': so2_tailpipe_3_cost_dollars,
                                     'so2_upstream_3_cost_dollars': so2_upstream_3_cost_dollars,
                                     'pm25_tailpipe_7_cost_dollars': pm25_tailpipe_7_cost_dollars,
                                     'pm25_upstream_7_cost_dollars': pm25_upstream_7_cost_dollars,
                                     'nox_tailpipe_7_cost_dollars': nox_tailpipe_7_cost_dollars,
                                     'nox_upstream_7_cost_dollars': nox_upstream_7_cost_dollars,
                                     'so2_tailpipe_7_cost_dollars': so2_tailpipe_7_cost_dollars,
                                     'so2_upstream_7_cost_dollars': so2_upstream_7_cost_dollars,
                                     'criteria_tailpipe_3_cost_dollars': criteria_tailpipe_3_cost_dollars,
                                     'criteria_upstream_3_cost_dollars': criteria_upstream_3_cost_dollars,
                                     'criteria_tailpipe_7_cost_dollars': criteria_tailpipe_7_cost_dollars,
                                     'criteria_upstream_7_cost_dollars': criteria_upstream_7_cost_dollars,
                                     'criteria_3_cost_dollars': criteria_3_cost_dollars,
                                     'criteria_7_cost_dollars': criteria_7_cost_dollars,
                                     }
                                    )
        if flag:
            discount_rate = 0
            key = (vehicle_ID, calendar_year, age, discount_rate)
            costs_dict[key] = veh_effects_dict

    return costs_dict
