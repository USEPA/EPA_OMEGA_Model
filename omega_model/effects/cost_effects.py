"""

A series of functions to calculate costs associated with the policy. The calc_cost_effects function is called by the omega_effects module and
other functions here are called from within the calc_cost_effects function.

----

**CODE**

"""
from omega_model import *


def get_scc_cf(calendar_year):
    """
    Get social cost of carbon cost factors

    Args:
        calendar_year (int): The calendar year for which social cost of GHG cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_scc import CostFactorsSCC

    cost_factors = ('co2_global_5.0_USD_per_metricton',
                    'co2_global_3.0_USD_per_metricton',
                    'co2_global_2.5_USD_per_metricton',
                    'co2_global_3.95_USD_per_metricton',
                    'ch4_global_5.0_USD_per_metricton',
                    'ch4_global_3.0_USD_per_metricton',
                    'ch4_global_2.5_USD_per_metricton',
                    'ch4_global_3.95_USD_per_metricton',
                    'n2o_global_5.0_USD_per_metricton',
                    'n2o_global_3.0_USD_per_metricton',
                    'n2o_global_2.5_USD_per_metricton',
                    'n2o_global_3.95_USD_per_metricton',
                    )

    return CostFactorsSCC.get_cost_factors(calendar_year, cost_factors)


def get_criteria_cf(calendar_year):
    """

    Get criteria cost factors

    Args:
        calendar_year (int): The calendar year for which criteria cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_criteria import CostFactorsCriteria

    cost_factors = ('pm25_tailpipe_3.0_USD_per_uston',
                    'pm25_upstream_3.0_USD_per_uston',
                    'nox_tailpipe_3.0_USD_per_uston',
                    'nox_upstream_3.0_USD_per_uston',
                    'sox_tailpipe_3.0_USD_per_uston',
                    'sox_upstream_3.0_USD_per_uston',
                    'pm25_tailpipe_7.0_USD_per_uston',
                    'pm25_upstream_7.0_USD_per_uston',
                    'nox_tailpipe_7.0_USD_per_uston',
                    'nox_upstream_7.0_USD_per_uston',
                    'sox_tailpipe_7.0_USD_per_uston',
                    'sox_upstream_7.0_USD_per_uston',
                    )

    return CostFactorsCriteria.get_cost_factors(calendar_year, cost_factors)


def get_energysecurity_cf(calendar_year):
    """
    Get energy security cost factors

    Args:
        calendar_year: The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity

    cost_factors = ('dollars_per_bbl',
                    )

    return CostFactorsEnergySecurity.get_cost_factors(calendar_year, cost_factors)


def get_congestion_noise_cf(reg_class_id):
    """
    Get congestion and noise cost factors

    Args:
        reg_class_id: The (legacy) regulatory class ID for which congestion and noise cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise

    cost_factors = ('congestion_cost_dollars_per_mile',
                    'noise_cost_dollars_per_mile',
                    )

    return CostFactorsCongestionNoise.get_cost_factors(reg_class_id, cost_factors)


def get_maintenance_cost(veh_type):
    """

    Args:
        veh_type: (str) 'BEV', 'PHEV', 'ICE', 'HEV'

    Returns:
        Curve coefficient values to calculate maintenance costs per mile at any odometer value.

    """
    from context.maintenance_cost import MaintenanceCost

    d = MaintenanceCost.get_maintenance_cost_curve_coefficients(veh_type)

    return d['slope'], d['intercept']


def calc_cost_effects(physical_effects_dict, calc_health_effects=False):
    """
    Calculate cost effects

    Args:
        physical_effects_dict: A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the values are a
        dictionary of attributes and attribute value pairs.
        calc_health_effects: boolean; pass True to use $/ton values to calculate health effects.

    Returns:
        A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age, discount_rate) and the values are a dictionary
        of attributes and attribute value pairs.

    """
    from context.fuel_prices import FuelPrice
    from producer.vehicles import VehicleFinal
    from context.repair_cost import RepairCost
    from context.refueling_cost import RefuelingCost
    from common.omega_eval import Eval
    from effects.legacy_fleet import LegacyFleet

    # UPDATE cost effects data
    costs_dict = dict()
    vehicle_info_dict = dict()
    refueling_bev_dict = dict()
    refueling_liquid_dict = dict()
    fuel = None
    
    for key in physical_effects_dict:
        vehicle_id, calendar_year, age = key
        physical = physical_effects_dict[key]
        onroad_direct_co2e_grams_per_mile = physical['onroad_direct_co2e_grams_per_mile']
        onroad_direct_kwh_per_mile = physical['onroad_direct_kwh_per_mile']

        veh_effects_dict = dict()
        flag = None
        if onroad_direct_co2e_grams_per_mile or onroad_direct_kwh_per_mile:
            flag = 1

            vehicle_cost_dollars = 0
            fuel_retail_cost_dollars = 0
            fuel_pretax_cost_dollars = 0
            energy_security_cost_dollars = 0
            congestion_cost_dollars = 0
            noise_cost_dollars = 0
            maintenance_cost_dollars = 0
            repair_cost_dollars = 0
            refueling_cost_dollars = 0
            driving_cost_dollars = 0
            pm25_tailpipe_3 = pm25_upstream_3 = nox_tailpipe_3 = nox_upstream_3 = sox_tailpipe_3 = sox_upstream_3 = 0
            pm25_tailpipe_7 = pm25_upstream_7 = nox_tailpipe_7 = nox_upstream_7 = sox_tailpipe_7 = sox_upstream_7 = 0
            pm25_vehicle_3_cost_dollars = pm25_upstream_3_cost_dollars = 0
            pm25_vehicle_7_cost_dollars = pm25_upstream_7_cost_dollars = 0
            nox_vehicle_3_cost_dollars = nox_upstream_3_cost_dollars = 0
            nox_vehicle_7_cost_dollars = nox_upstream_7_cost_dollars = 0
            sox_vehicle_3_cost_dollars = sox_upstream_3_cost_dollars = 0
            sox_vehicle_7_cost_dollars = sox_upstream_7_cost_dollars = 0
            criteria_vehicle_3_cost_dollars = criteria_upstream_3_cost_dollars = 0
            criteria_vehicle_7_cost_dollars = criteria_upstream_7_cost_dollars = 0
            criteria_3_cost_dollars = criteria_7_cost_dollars = 0

            mfr_id, name, base_year_reg_class_id, reg_class_id, in_use_fuel_id, market_class_id, fueling_class, base_year_powertrain_type \
                = physical['manufacturer_id'], \
                  physical['name'], \
                  physical['base_year_reg_class_id'], \
                  physical['reg_class_id'], \
                  physical['in_use_fuel_id'], \
                  physical['market_class_id'], \
                  physical['fueling_class'], \
                  physical['base_year_powertrain_type']

            vehicle_count, annual_vmt, odometer, vmt, vmt_liquid, vmt_elec, kwh, gallons, imported_bbl \
                = physical['registered_count'], \
                  physical['annual_vmt'], \
                  physical['odometer'], \
                  physical['vmt'], \
                  physical['vmt_liquid_fuel'], \
                  physical['vmt_electricity'], \
                  physical['fuel_consumption_kWh'], \
                  physical['fuel_consumption_gallons'], \
                  physical['barrels_of_imported_oil']

            # ghg tons
            co2_tons, ch4_tons, n2o_tons \
                = physical['co2_total_metrictons'], \
                  physical['ch4_total_metrictons'], \
                  physical['n2o_total_metrictons']

            # criteria air pollutant tons
            pm25_tp_tons, pm25_up_tons, nox_tp_tons, nox_up_tons, sox_tp_tons, sox_up_tons \
                = physical['pm25_vehicle_ustons'], \
                  physical['pm25_upstream_ustons'], \
                  physical['nox_vehicle_ustons'], \
                  physical['nox_upstream_ustons'], \
                  physical['sox_vehicle_ustons'], \
                  physical['sox_upstream_ustons']

            if vehicle_id not in vehicle_info_dict:
                if vehicle_id < pow(10, 6):
                    attribute_list = ['new_vehicle_mfr_cost_dollars']
                    vehicle_info_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)[0]
                else:
                    legacy_fleet_key = (vehicle_id, calendar_year, age)
                    vehicle_info_dict[vehicle_id] = LegacyFleet._legacy_fleet[legacy_fleet_key]['transaction_price_dollars']

            new_vehicle_cost = vehicle_info_dict[vehicle_id]
            # tech costs, only for age=0
            if age == 0:
                vehicle_cost_dollars = vehicle_count * new_vehicle_cost

            # fuel costs
            fuel_dict = Eval.eval(in_use_fuel_id, {'__builtins__': None}, {})
            for fuel, fuel_share in fuel_dict.items():
                retail_price = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', fuel)
                pretax_price = FuelPrice.get_fuel_prices(calendar_year, 'pretax_dollars_per_unit', fuel)
                if fuel == 'US electricity' and kwh:
                    fuel_retail_cost_dollars += retail_price * kwh
                    fuel_pretax_cost_dollars += pretax_price * kwh
                elif fuel != 'US electricity' and gallons:
                    fuel_retail_cost_dollars += retail_price * gallons
                    fuel_pretax_cost_dollars += pretax_price * gallons

            # maintenance costs
            slope, intercept = get_maintenance_cost(base_year_powertrain_type)
            maintenance_cost_per_mile = slope * odometer + intercept
            maintenance_cost_dollars = maintenance_cost_per_mile * vmt

            # repair costs
            if name.__contains__('car'):
                operating_veh_type = 'car'
            elif name.__contains__('Pickup'):
                operating_veh_type = 'truck'
            else:
                operating_veh_type = 'suv'

            repair_cost_per_mile \
                = RepairCost.calc_repair_cost_per_mile(new_vehicle_cost, base_year_powertrain_type, operating_veh_type, age)
            repair_cost_dollars = repair_cost_per_mile * vmt

            # refueling costs
            if base_year_powertrain_type == 'BEV':
                range = 300 # TODO do we stay with this or will range be an attribute tracked within omega
                if (operating_veh_type, range) in refueling_bev_dict.keys():
                    refueling_cost_per_mile = refueling_bev_dict[(operating_veh_type, range)]
                else:
                    refueling_cost_per_mile = RefuelingCost.calc_bev_refueling_cost_per_mile(operating_veh_type, range)
                    refueling_bev_dict.update({(operating_veh_type, range): refueling_cost_per_mile})
                refueling_cost_dollars = refueling_cost_per_mile * vmt
            else:
                if operating_veh_type in refueling_liquid_dict.keys():
                    refueling_cost_per_gallon = refueling_liquid_dict[operating_veh_type]
                else:
                    refueling_cost_per_gallon = RefuelingCost.calc_liquid_refueling_cost_per_gallon(operating_veh_type)
                    refueling_liquid_dict.update({operating_veh_type: refueling_cost_per_gallon})
                refueling_cost_dollars = refueling_cost_per_gallon * gallons

            # get energy security cost factors
            energy_security_cf = get_energysecurity_cf(calendar_year)

            # energy security
            if fuel == 'US electricity':
                pass
            elif fuel != 'US electricity' and gallons:
                energy_security_cost_dollars += imported_bbl * energy_security_cf

            # get congestion and noise cost factors
            congestion_cf, noise_cf = get_congestion_noise_cf(base_year_reg_class_id)

            # congestion and noise costs (maybe congestion and noise cost factors will differ one day?)
            if vmt_elec:
                congestion_cost_dollars += vmt_elec * congestion_cf
                noise_cost_dollars += vmt_elec * noise_cf
            if vmt_liquid:
                congestion_cost_dollars += vmt_liquid * congestion_cf
                noise_cost_dollars += vmt_liquid * noise_cf

            # climate effects

            # get scc cost factors
            co2_global_5, co2_global_3, co2_global_25, co2_global_395, \
            ch4_global_5, ch4_global_3, ch4_global_25, ch4_global_395, \
            n2o_global_5, n2o_global_3, n2o_global_25, n2o_global_395 \
                = get_scc_cf(calendar_year)

            # calculate climate cost effects
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

            ghg_global_5_cost_dollars = co2_global_5_cost_dollars \
                                        + ch4_global_5_cost_dollars \
                                        + n2o_global_5_cost_dollars
            ghg_global_3_cost_dollars = co2_global_3_cost_dollars \
                                        + ch4_global_3_cost_dollars \
                                        + n2o_global_3_cost_dollars
            ghg_global_25_cost_dollars = co2_global_25_cost_dollars \
                                         + ch4_global_25_cost_dollars \
                                         + n2o_global_25_cost_dollars
            ghg_global_395_cost_dollars = co2_global_395_cost_dollars \
                                          + ch4_global_395_cost_dollars \
                                          + n2o_global_395_cost_dollars

            # criteria effects
            if calc_health_effects:
                # get criteria cost factors
                pm25_tailpipe_3, pm25_upstream_3, nox_tailpipe_3, nox_upstream_3, sox_tailpipe_3, sox_upstream_3, \
                pm25_tailpipe_7, pm25_upstream_7, nox_tailpipe_7, nox_upstream_7, sox_tailpipe_7, sox_upstream_7 \
                    = get_criteria_cf(calendar_year)

                # calculate criteria cost effects
                pm25_vehicle_3_cost_dollars = pm25_tp_tons * pm25_tailpipe_3
                pm25_upstream_3_cost_dollars = pm25_up_tons * pm25_upstream_3

                nox_vehicle_3_cost_dollars = nox_tp_tons * nox_tailpipe_3
                nox_upstream_3_cost_dollars = nox_up_tons * nox_upstream_3

                sox_vehicle_3_cost_dollars = sox_tp_tons * sox_tailpipe_3
                sox_upstream_3_cost_dollars = sox_up_tons * sox_upstream_3

                pm25_vehicle_7_cost_dollars = pm25_tp_tons * pm25_tailpipe_7
                pm25_upstream_7_cost_dollars = pm25_up_tons * pm25_upstream_7

                nox_vehicle_7_cost_dollars = nox_tp_tons * nox_tailpipe_7
                nox_upstream_7_cost_dollars = nox_up_tons * nox_upstream_7

                sox_vehicle_7_cost_dollars = sox_tp_tons * sox_tailpipe_7
                sox_upstream_7_cost_dollars = sox_up_tons * sox_upstream_7

                criteria_vehicle_3_cost_dollars = pm25_vehicle_3_cost_dollars \
                                                   + nox_vehicle_3_cost_dollars \
                                                   + sox_vehicle_3_cost_dollars
                criteria_upstream_3_cost_dollars = pm25_upstream_3_cost_dollars \
                                                   + nox_upstream_3_cost_dollars \
                                                   + sox_upstream_3_cost_dollars

                criteria_vehicle_7_cost_dollars = pm25_vehicle_7_cost_dollars \
                                                  + nox_vehicle_7_cost_dollars \
                                                  + sox_vehicle_7_cost_dollars
                criteria_upstream_7_cost_dollars = pm25_upstream_7_cost_dollars \
                                                   + nox_upstream_7_cost_dollars \
                                                   + sox_upstream_7_cost_dollars

                criteria_3_cost_dollars = criteria_vehicle_3_cost_dollars + criteria_upstream_3_cost_dollars
                criteria_7_cost_dollars = criteria_vehicle_7_cost_dollars + criteria_upstream_7_cost_dollars

            # save results in the vehicle effects dict for this vehicle
            veh_effects_dict = {
                'session_name': omega_globals.options.session_name,
                'discount_rate': 0,
                'vehicle_id': vehicle_id,
                'manufacturer_id': mfr_id,
                'name': name,
                'calendar_year': calendar_year,
                'model_year': calendar_year - age,
                'age': age,
                'base_year_reg_class_id': base_year_reg_class_id,
                'reg_class_id': reg_class_id,
                'in_use_fuel_id': in_use_fuel_id,
                'fueling_class': fueling_class,
                'base_year_powertrain_type': base_year_powertrain_type,
                'registered_count': vehicle_count,
                'annual_vmt': annual_vmt,
                'odometer': odometer,
                'vmt': vmt,
                'vmt_liquid_fuel': vmt_liquid,
                'vmt_electricity': vmt_elec,
                'vehicle_cost_dollars': vehicle_cost_dollars,
                'fuel_retail_cost_dollars': fuel_retail_cost_dollars,
                'fuel_pretax_cost_dollars': fuel_pretax_cost_dollars,
                'fuel_taxes_cost_dollars': fuel_retail_cost_dollars - fuel_pretax_cost_dollars,
                'energy_security_cost_dollars': energy_security_cost_dollars,
                'congestion_cost_dollars': congestion_cost_dollars,
                'noise_cost_dollars': noise_cost_dollars,
                'maintenance_cost_dollars': maintenance_cost_dollars,
                'repair_cost_dollars': repair_cost_dollars,
                'refueling_cost_dollars': refueling_cost_dollars,
                'driving_cost_dollars': driving_cost_dollars,

                'co2_global_5.0_cost_dollars': co2_global_5_cost_dollars,
                'co2_global_3.0_cost_dollars': co2_global_3_cost_dollars,
                'co2_global_2.5_cost_dollars': co2_global_25_cost_dollars,
                'co2_global_3.95_cost_dollars': co2_global_395_cost_dollars,
                'ch4_global_5.0_cost_dollars': ch4_global_5_cost_dollars,
                'ch4_global_3.0_cost_dollars': ch4_global_3_cost_dollars,
                'ch4_global_2.5_cost_dollars': ch4_global_25_cost_dollars,
                'ch4_global_3.95_cost_dollars': ch4_global_395_cost_dollars,
                'n2o_global_5.0_cost_dollars': n2o_global_5_cost_dollars,
                'n2o_global_3.0_cost_dollars': n2o_global_3_cost_dollars,
                'n2o_global_2.5_cost_dollars': n2o_global_25_cost_dollars,
                'n2o_global_3.95_cost_dollars': n2o_global_395_cost_dollars,
                'ghg_global_5.0_cost_dollars': ghg_global_5_cost_dollars,
                'ghg_global_3.0_cost_dollars': ghg_global_3_cost_dollars,
                'ghg_global_2.5_cost_dollars': ghg_global_25_cost_dollars,
                'ghg_global_3.95_cost_dollars': ghg_global_395_cost_dollars,
            }
            if calc_health_effects:
                veh_effects_dict.update({
                    'pm25_vehicle_3.0_cost_dollars': pm25_vehicle_3_cost_dollars,
                    'pm25_upstream_3.0_cost_dollars': pm25_upstream_3_cost_dollars,
                    'nox_vehicle_3.0_cost_dollars': nox_vehicle_3_cost_dollars,
                    'nox_upstream_3.0_cost_dollars': nox_upstream_3_cost_dollars,
                    'sox_vehicle_3.0_cost_dollars': sox_vehicle_3_cost_dollars,
                    'sox_upstream_3.0_cost_dollars': sox_upstream_3_cost_dollars,
                    'pm25_vehicle_7.0_cost_dollars': pm25_vehicle_7_cost_dollars,
                    'pm25_upstream_7.0_cost_dollars': pm25_upstream_7_cost_dollars,
                    'nox_vehicle_7.0_cost_dollars': nox_vehicle_7_cost_dollars,
                    'nox_upstream_7.0_cost_dollars': nox_upstream_7_cost_dollars,
                    'sox_vehicle_7.0_cost_dollars': sox_vehicle_7_cost_dollars,
                    'sox_upstream_7.0_cost_dollars': sox_upstream_7_cost_dollars,
                    'criteria_vehicle_3.0_cost_dollars': criteria_vehicle_3_cost_dollars,
                    'criteria_upstream_3.0_cost_dollars': criteria_upstream_3_cost_dollars,
                    'criteria_vehicle_7.0_cost_dollars': criteria_vehicle_7_cost_dollars,
                    'criteria_upstream_7.0_cost_dollars': criteria_upstream_7_cost_dollars,
                    'criteria_3.0_cost_dollars': criteria_3_cost_dollars,
                    'criteria_7.0_cost_dollars': criteria_7_cost_dollars,
                }
                )

        if flag:
            discount_rate = 0
            key = (vehicle_id, calendar_year, age, discount_rate)
            costs_dict[key] = veh_effects_dict

    return costs_dict
