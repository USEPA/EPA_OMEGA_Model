"""

A series of functions to calculate costs associated with the policy. The calc_cost_effects function is called by the omega_effects module and
other functions here are called from within the calc_cost_effects function.

----

**CODE**

"""

from omega_model import *


def get_scc_cf(calendar_year):
    """

    Args:
        calendar_year: The calendar year for which social cost of GHG cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
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
    """

    Args:
        calendar_year: The calendar year for which criteria cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
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
    """

    Args:
        calendar_year: The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    cost_factors = ['dollars_per_gallon',
                    ]

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_congestion_noise_cf(reg_class_id):
    """

    Args:
        calendar_year: The calendar year for which congestion and noise cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise

    cost_factors = ['congestion_cost_dollars_per_mile',
                    'noise_cost_dollars_per_mile',
                    ]

    return CostFactorsCongestionNoise.get_cost_factors(reg_class_id, cost_factors)


def calc_cost_effects(physical_effects_dict):
    """

    Args:
        physical_effects_dict: A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the values are a
        dictionary of attributes and attribute value pairs.

    Returns:
        A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age, discount_rate) and the values are a dictionary
        of attributes and attribute value pairs.

    """
    from context.fuel_prices import FuelPrice
    from producer.vehicles import VehicleFinal

    # UPDATE cost effects data
    costs_dict = dict()
    vehicle_info_dict = dict()
    fuel = None
    for key in physical_effects_dict.keys():

        vehicle_id, calendar_year, age = key
        physical = physical_effects_dict[key]
        onroad_direct_co2e_grams_per_mile = physical['onroad_direct_co2e_grams_per_mile']
        onroad_direct_kwh_per_mile = physical['onroad_direct_kwh_per_mile']

        veh_effects_dict = dict()
        flag = None
        if onroad_direct_co2e_grams_per_mile or onroad_direct_kwh_per_mile:
            flag = 1

            tech_cost_dollars = 0
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

            attribute_list = ['new_vehicle_mfr_cost_dollars']
            if vehicle_id not in vehicle_info_dict:
                vehicle_info_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)[0]

            new_vehicle_cost = vehicle_info_dict[vehicle_id]

            mfr_id, base_year_reg_class_id, reg_class_id, in_use_fuel_id, market_group, vehicle_count, annual_vmt, vmt, vmt_liquid, vmt_elec \
                = physical['manufacturer_id'], physical['base_year_reg_class_id'], physical['reg_class_id'], \
                  physical['in_use_fuel_id'], physical['non_responsive_market_group'], \
                  physical['registered_count'], physical['annual_vmt'], physical['vmt'], \
                  physical['vmt_liquid_fuel'], physical['vmt_electricity']

            # tech costs, only for age=0
            if age == 0:
                tech_cost_dollars = physical['registered_count'] * new_vehicle_cost

            # fuel costs
            fuel_dict = eval(in_use_fuel_id, {'__builtins__': None}, {})
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
            congestion_cf, noise_cf = get_congestion_noise_cf(base_year_reg_class_id)

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

            veh_effects_dict.update({'manufacturer_id': mfr_id,
                                     'model_year': calendar_year - age,
                                     'base_year_reg_class_id': base_year_reg_class_id,
                                     'reg_class_id': reg_class_id,
                                     'in_use_fuel_id': in_use_fuel_id,
                                     'non_responsive_market_group': market_group,
                                     'registered_count': vehicle_count,
                                     'annual_vmt': annual_vmt,
                                     'vmt': vmt,
                                     'vmt_liquid_fuel': vmt_liquid,
                                     'vmt_electricity': vmt_elec,
                                     'tech_cost_dollars': tech_cost_dollars,
                                     'fuel_retail_cost_dollars': fuel_retail_cost_dollars,
                                     'fuel_pretax_cost_dollars': fuel_pretax_cost_dollars,
                                     'fuel_taxes_cost_dollars': fuel_retail_cost_dollars - fuel_pretax_cost_dollars,
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
            key = (vehicle_id, calendar_year, age, discount_rate)
            costs_dict[key] = veh_effects_dict

    return costs_dict
