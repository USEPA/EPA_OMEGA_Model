import pandas as pd


def get_scc_cf(batch_settings, calendar_year):
    """
    Get social cost of carbon cost factors

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year (int): The calendar year for which social cost of GHG cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
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

    return batch_settings.scc_cost_factors.get_cost_factors(calendar_year, cost_factors)


def get_criteria_cf(batch_settings, calendar_year, source_id):
    """

    Get criteria cost factors

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year (int): The calendar year for which criteria cost factors are needed.
        source_id (str): the pollutant source, e.g., 'car pump gasoline', 'egu', 'refinery'

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    cost_factors = ('pm25_low_3.0_USD_per_uston',
                    'sox_low_3.0_USD_per_uston',
                    'nox_low_3.0_USD_per_uston',
                    'pm25_low_7.0_USD_per_uston',
                    'sox_low_7.0_USD_per_uston',
                    'nox_low_7.0_USD_per_uston',
                    'pm25_high_3.0_USD_per_uston',
                    'sox_high_3.0_USD_per_uston',
                    'nox_high_3.0_USD_per_uston',
                    'pm25_high_7.0_USD_per_uston',
                    'sox_high_7.0_USD_per_uston',
                    'nox_high_7.0_USD_per_uston',
                    )

    return batch_settings.criteria_cost_factors.get_cost_factors(calendar_year, source_id, cost_factors)


def get_energysecurity_cf(batch_settings, calendar_year):
    """
    Get energy security cost factors

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year: The calendar year for which energy security related factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    cost_factors = ('dollars_per_bbl',
                    )

    return batch_settings.energy_security_cost_factors.get_cost_factors(calendar_year, cost_factors)


def calc_benefits(batch_settings, annual_physical_effects_df, annual_cost_effects_df, calc_health_effects=False):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        annual_physical_effects_df (DataFrame): a DataFrame of physical effects by calendar year, reg class, fuel type.
        annual_cost_effects_df (DataFrame): a DataFrame of cost effects by calendar year, reg class, fuel type.
        calc_health_effects (bool): criteria air pollutant benefits will be calculated if True.

    Returns:
        Two dictionaries: one of benefits for each action session relative to the no_action session; and one of physical
        effects for each action session relative to the no_action session.

    """
    keys = pd.Series(zip(
        annual_physical_effects_df['session_policy'],
        annual_physical_effects_df['calendar_year'],
        annual_physical_effects_df['reg_class_id'],
        annual_physical_effects_df['in_use_fuel_id'],
    ))
    annual_physical_effects_df.set_index(keys, inplace=True)
    physical_effects_dict = annual_physical_effects_df.to_dict('index')

    keys = pd.Series(zip(
        annual_cost_effects_df['session_policy'],
        annual_cost_effects_df['calendar_year'],
        annual_cost_effects_df['reg_class_id'],
        annual_cost_effects_df['in_use_fuel_id'],
    ))
    annual_cost_effects_df.set_index(keys, inplace=True)
    cost_effects_dict = annual_cost_effects_df.to_dict('index')

    benefits_dict = dict()
    delta_physical_effects_dict = dict()
    for key in physical_effects_dict:
        
        session_policy, calendar_year, reg_class_id, in_use_fuel_id = key
        fueling_class = physical_effects_dict[key]['fueling_class']

        flag = None
        benefits_dict_for_key = dict()
        physical_effects_dict_for_key = dict()
        if session_policy != 'no_action':
            flag = 1
            no_action_key = ('no_action', calendar_year, reg_class_id, in_use_fuel_id)
            physical_na = physical_effects_dict[no_action_key]
            physical_a = physical_effects_dict[key]
            cost_na = cost_effects_dict[no_action_key]
            cost_a = cost_effects_dict[key]
            
            energy_security_benefit_dollars = drive_value_benefit_dollars = 0
    
            fuel_dict = eval(in_use_fuel_id)
            fuel = None
            for fuel, fuel_share in fuel_dict.items():
                fuel, fuel_share = fuel, fuel_share

            oper_attrs_dict = dict()
            oper_attrs_list = [
                'vmt',
                'vmt_rebound',
                'vmt_liquid_fuel',
                'vmt_electricity',
                'fuel_consumption_kWh',
                'fuel_consumption_gallons',
            ]
            for oper_attr in oper_attrs_list:
                oper_attrs_dict[oper_attr] = physical_na[oper_attr] - physical_a[oper_attr]            
    
            # energy security benefits
            oil_barrels = physical_na['barrels_of_oil'] - physical_a['barrels_of_oil']
            imported_oil_bbl = physical_na['barrels_of_imported_oil'] - physical_a['barrels_of_imported_oil']
            imported_oil_bbl_per_day = physical_na['barrels_of_imported_oil_per_day'] \
                                       - physical_a['barrels_of_imported_oil_per_day']
            energy_security_cf = get_energysecurity_cf(batch_settings, calendar_year)
            if fuel == 'US electricity':
                pass
            elif fuel != 'US electricity':
                energy_security_benefit_dollars += imported_oil_bbl * energy_security_cf
    
            # calc drive value as drive_value_cost in action less drive_value_cost in no_action
            drive_value_benefit_dollars = cost_a['drive_value_cost_dollars'] - cost_na['drive_value_cost_dollars']
                
            # climate effects
            # get scc cost factors
            co2_global_5, co2_global_3, co2_global_25, co2_global_395, \
            ch4_global_5, ch4_global_3, ch4_global_25, ch4_global_395, \
            n2o_global_5, n2o_global_3, n2o_global_25, n2o_global_395 \
                = get_scc_cf(batch_settings, calendar_year)
            
            ghg_tons_dict = dict()
            ghg_list = [
                'co2_vehicle_metrictons',
                'co2_upstream_metrictons',
                'co2_total_metrictons',
                'ch4_vehicle_metrictons',
                'ch4_upstream_metrictons',
                'ch4_total_metrictons',
                'n2o_vehicle_metrictons',
                'n2o_upstream_metrictons',
                'n2o_total_metrictons',
            ]
            for ghg in ghg_list:
                ghg_tons_dict[ghg] = physical_na[ghg] - physical_a[ghg]
    
            # calculate climate cost effects
            co2_tons = ghg_tons_dict['co2_total_metrictons']
            co2_global_5_benefit_dollars = co2_tons * co2_global_5
            co2_global_3_benefit_dollars = co2_tons * co2_global_3
            co2_global_25_benefit_dollars = co2_tons * co2_global_25
            co2_global_395_benefit_dollars = co2_tons * co2_global_395
        
            ch4_tons = ghg_tons_dict['ch4_total_metrictons']
            ch4_global_5_benefit_dollars = ch4_tons * ch4_global_5
            ch4_global_3_benefit_dollars = ch4_tons * ch4_global_3
            ch4_global_25_benefit_dollars = ch4_tons * ch4_global_25
            ch4_global_395_benefit_dollars = ch4_tons * ch4_global_395
    
            n2o_tons = ghg_tons_dict['n2o_total_metrictons']
            n2o_global_5_benefit_dollars = n2o_tons * n2o_global_5
            n2o_global_3_benefit_dollars = n2o_tons * n2o_global_3
            n2o_global_25_benefit_dollars = n2o_tons * n2o_global_25
            n2o_global_395_benefit_dollars = n2o_tons * n2o_global_395

            ghg_global_5_benefit_dollars = co2_global_5_benefit_dollars \
                                           + ch4_global_5_benefit_dollars \
                                           + n2o_global_5_benefit_dollars
            ghg_global_3_benefit_dollars = co2_global_3_benefit_dollars \
                                           + ch4_global_3_benefit_dollars \
                                           + n2o_global_3_benefit_dollars
            ghg_global_25_benefit_dollars = co2_global_25_benefit_dollars \
                                            + ch4_global_25_benefit_dollars \
                                            + n2o_global_25_benefit_dollars
            ghg_global_395_benefit_dollars = co2_global_395_benefit_dollars \
                                             + ch4_global_395_benefit_dollars \
                                             + n2o_global_395_benefit_dollars
            
            # toxics
            toxics_tons_dict = dict()
            toxics_list = [
                'acetaldehyde_vehicle_ustons',
                'acrolein_vehicle_ustons',
                'benzene_exhaust_ustons',
                'benzene_evaporative_ustons',
                'benzene_vehicle_ustons',
                'ethylbenzene_exhaust_ustons',
                'ethylbenzene_evaporative_ustons',
                'ethylbenzene_vehicle_ustons',
                'formaldehyde_vehicle_ustons',
                'naphthalene_exhaust_ustons',
                'naphthalene_evaporative_ustons',
                'naphthalene_vehicle_ustons',
                '13_butadiene_vehicle_ustons',
                '15pah_vehicle_ustons',
            ]
            for toxic in toxics_list:
                toxics_tons_dict[toxic] = physical_na[toxic] - physical_a[toxic]
                
            # criteria air pollutant (cap) benefits
            cap_tons_dict = dict()
            if calc_health_effects:

                # criteria air pollutant (cap) tons
                cap_list = [
                    'pm25_vehicle_ustons',
                    'pm25_upstream_ustons',
                    'pm25_total_ustons',
                    'nox_vehicle_ustons',
                    'nox_upstream_ustons',
                    'nox_total_ustons',
                    'sox_vehicle_ustons',
                    'sox_upstream_ustons',
                    'sox_total_ustons',
                    'nmog_vehicle_ustons',
                    'voc_upstream_ustons',
                    'nmog_and_voc_total_ustons',
                    'co_vehicle_ustons',
                    'co_upstream_ustons',
                    'co_total_ustons',
                ]
                for cap in cap_list:
                    cap_tons_dict[cap] = physical_na[cap] - physical_a[cap]
                
                # get vehicle criteria cost factors
                source_id = f'{reg_class_id} {fuel}'
                pm25_low_3, sox_low_3, nox_low_3, \
                    pm25_low_7, sox_low_7, nox_low_7, \
                    pm25_high_3, sox_high_3, nox_high_3, \
                    pm25_high_7, sox_high_7, nox_high_7 = get_criteria_cf(batch_settings, calendar_year, source_id)

                pm25_tons, sox_tons, nox_tons = \
                    cap_tons_dict['pm25_vehicle_ustons'], cap_tons_dict['sox_vehicle_ustons'], cap_tons_dict['nox_vehicle_ustons']
                pm25_veh_low_3_benefit_dollars = pm25_tons * pm25_low_3
                sox_veh_low_3_benefit_dollars = sox_tons * sox_low_3
                nox_veh_low_3_benefit_dollars = nox_tons * nox_low_3
                pm25_veh_low_7_benefit_dollars = pm25_tons * pm25_low_7
                sox_veh_low_7_benefit_dollars = sox_tons * sox_low_7
                nox_veh_low_7_benefit_dollars = nox_tons * nox_low_7
                pm25_veh_high_3_benefit_dollars = pm25_tons * pm25_high_3
                sox_veh_high_3_benefit_dollars = sox_tons * sox_high_3
                nox_veh_high_3_benefit_dollars = nox_tons * nox_high_3
                pm25_veh_high_7_benefit_dollars = pm25_tons * pm25_high_7
                sox_veh_high_7_benefit_dollars = sox_tons * sox_high_7
                nox_veh_high_7_benefit_dollars = nox_tons * nox_high_7
    
                # get upstream criteria cost factors
                if 'electricity' in fuel:
                    source_id = 'egu'
                else:
                    source_id = 'refinery'
    
                pm25_low_3, sox_low_3, nox_low_3, \
                    pm25_low_7, sox_low_7, nox_low_7, \
                    pm25_high_3, sox_high_3, nox_high_3, \
                    pm25_high_7, sox_high_7, nox_high_7 = get_criteria_cf(batch_settings, calendar_year, source_id)

                pm25_tons, sox_tons, nox_tons = \
                    cap_tons_dict['pm25_upstream_ustons'], cap_tons_dict['sox_upstream_ustons'], cap_tons_dict['nox_upstream_ustons']
                pm25_up_low_3_benefit_dollars = pm25_tons * pm25_low_3
                sox_up_low_3_benefit_dollars = sox_tons * sox_low_3
                nox_up_low_3_benefit_dollars = nox_tons * nox_low_3
                pm25_up_low_7_benefit_dollars = pm25_tons * pm25_low_7
                sox_up_low_7_benefit_dollars = sox_tons * sox_low_7
                nox_up_low_7_benefit_dollars = nox_tons * nox_low_7
                pm25_up_high_3_benefit_dollars = pm25_tons * pm25_high_3
                sox_up_high_3_benefit_dollars = sox_tons * sox_high_3
                nox_up_high_3_benefit_dollars = nox_tons * nox_high_3
                pm25_up_high_7_benefit_dollars = pm25_tons * pm25_high_7
                sox_up_high_7_benefit_dollars = sox_tons * sox_high_7
                nox_up_high_7_benefit_dollars = nox_tons * nox_high_7
    
                criteria_veh_low_3_benefit_dollars = pm25_veh_low_3_benefit_dollars \
                                                  + sox_veh_low_3_benefit_dollars \
                                                  + nox_veh_low_3_benefit_dollars
                criteria_veh_low_7_benefit_dollars = pm25_veh_low_7_benefit_dollars \
                                                  + sox_veh_low_7_benefit_dollars \
                                                  + nox_veh_low_7_benefit_dollars
                criteria_veh_high_3_benefit_dollars = pm25_veh_high_3_benefit_dollars \
                                                   + sox_veh_high_3_benefit_dollars \
                                                   + nox_veh_high_3_benefit_dollars
                criteria_veh_high_7_benefit_dollars = pm25_veh_high_7_benefit_dollars \
                                                   + sox_veh_high_7_benefit_dollars \
                                                   + nox_veh_high_7_benefit_dollars
    
                criteria_up_low_3_benefit_dollars = pm25_up_low_3_benefit_dollars \
                                                 + sox_up_low_3_benefit_dollars \
                                                 + nox_up_low_3_benefit_dollars
                criteria_up_low_7_benefit_dollars = pm25_up_low_7_benefit_dollars \
                                                 + sox_up_low_7_benefit_dollars \
                                                 + nox_up_low_7_benefit_dollars
                criteria_up_high_3_benefit_dollars = pm25_up_high_3_benefit_dollars \
                                                  + sox_up_high_3_benefit_dollars \
                                                  + nox_up_high_3_benefit_dollars
                criteria_up_high_7_benefit_dollars = pm25_up_high_7_benefit_dollars \
                                                  + sox_up_high_7_benefit_dollars \
                                                  + nox_up_high_7_benefit_dollars

                criteria_low_3_benefit_dollars = criteria_veh_low_3_benefit_dollars + \
                                                 criteria_up_low_3_benefit_dollars

                criteria_low_7_benefit_dollars = criteria_veh_low_7_benefit_dollars + \
                                                 criteria_up_low_7_benefit_dollars

                criteria_high_3_benefit_dollars = criteria_veh_high_3_benefit_dollars + \
                                                  criteria_up_high_3_benefit_dollars

                criteria_high_7_benefit_dollars = criteria_veh_high_7_benefit_dollars + \
                                                  criteria_up_high_7_benefit_dollars

            # save monetized benefit results in the benefits_dict for this key
            benefits_dict_for_key = {
                'session_policy': cost_a['session_policy'],
                'session_name': cost_a['session_name'],
                'discount_rate': 0,
                'series': 'AnnualValue',
                'periods': 1,
                'calendar_year': calendar_year,
                'reg_class_id': reg_class_id,
                'in_use_fuel_id': in_use_fuel_id,
                'fueling_class': fueling_class,

                'energy_security_benefit_dollars': energy_security_benefit_dollars,
                'drive_value_benefit_dollars': drive_value_benefit_dollars,

                'co2_global_5.0_benefit_dollars': co2_global_5_benefit_dollars,
                'co2_global_3.0_benefit_dollars': co2_global_3_benefit_dollars,
                'co2_global_2.5_benefit_dollars': co2_global_25_benefit_dollars,
                'co2_global_3.95_benefit_dollars': co2_global_395_benefit_dollars,
                'ch4_global_5.0_benefit_dollars': ch4_global_5_benefit_dollars,
                'ch4_global_3.0_benefit_dollars': ch4_global_3_benefit_dollars,
                'ch4_global_2.5_benefit_dollars': ch4_global_25_benefit_dollars,
                'ch4_global_3.95_benefit_dollars': ch4_global_395_benefit_dollars,
                'n2o_global_5.0_benefit_dollars': n2o_global_5_benefit_dollars,
                'n2o_global_3.0_benefit_dollars': n2o_global_3_benefit_dollars,
                'n2o_global_2.5_benefit_dollars': n2o_global_25_benefit_dollars,
                'n2o_global_3.95_benefit_dollars': n2o_global_395_benefit_dollars,
                'ghg_global_5.0_benefit_dollars': ghg_global_5_benefit_dollars,
                'ghg_global_3.0_benefit_dollars': ghg_global_3_benefit_dollars,
                'ghg_global_2.5_benefit_dollars': ghg_global_25_benefit_dollars,
                'ghg_global_3.95_benefit_dollars': ghg_global_395_benefit_dollars,
            }
            if calc_health_effects:
                benefits_dict_for_key.update({
                    'pm25_vehicle_low_3.0_benefit_dollars': pm25_veh_low_3_benefit_dollars,
                    'sox_vehicle_low_3.0_benefit_dollars': sox_veh_low_3_benefit_dollars,
                    'nox_vehicle_low_3.0_benefit_dollars': nox_veh_low_3_benefit_dollars,
                    'pm25_vehicle_low_7.0_benefit_dollars': pm25_veh_low_7_benefit_dollars,
                    'sox_vehicle_low_7.0_benefit_dollars': sox_veh_low_7_benefit_dollars,
                    'nox_vehicle_low_7.0_benefit_dollars': nox_veh_low_7_benefit_dollars,

                    'pm25_vehicle_high_3.0_benefit_dollars': pm25_veh_high_3_benefit_dollars,
                    'sox_vehicle_high_3.0_benefit_dollars': sox_veh_high_3_benefit_dollars,
                    'nox_vehicle_high_3.0_benefit_dollars': nox_veh_high_3_benefit_dollars,
                    'pm25_vehicle_high_7.0_benefit_dollars': pm25_veh_high_7_benefit_dollars,
                    'sox_vehicle_high_7.0_benefit_dollars': sox_veh_high_7_benefit_dollars,
                    'nox_vehicle_high_7.0_benefit_dollars': nox_veh_high_7_benefit_dollars,

                    'pm25_upstream_low_3.0_benefit_dollars': pm25_up_low_3_benefit_dollars,
                    'sox_upstream_low_3.0_benefit_dollars': sox_up_low_3_benefit_dollars,
                    'nox_upstream_low_3.0_benefit_dollars': nox_up_low_3_benefit_dollars,
                    'pm25_upstream_low_7.0_benefit_dollars': pm25_up_low_7_benefit_dollars,
                    'sox_upstream_low_7.0_benefit_dollars': sox_up_low_7_benefit_dollars,
                    'nox_upstream_low_7.0_benefit_dollars': nox_up_low_7_benefit_dollars,

                    'pm25_upstream_high_3.0_benefit_dollars': pm25_up_high_3_benefit_dollars,
                    'sox_upstream_high_3.0_benefit_dollars': sox_up_high_3_benefit_dollars,
                    'nox_upstream_high_3.0_benefit_dollars': nox_up_high_3_benefit_dollars,
                    'pm25_upstream_high_7.0_benefit_dollars': pm25_up_high_7_benefit_dollars,
                    'sox_upstream_high_7.0_benefit_dollars': sox_up_high_7_benefit_dollars,
                    'nox_upstream_high_7.0_benefit_dollars': nox_up_high_7_benefit_dollars,

                    'criteria_vehicle_low_3.0_benefit_dollars': criteria_veh_low_3_benefit_dollars,
                    'criteria_vehicle_low_7.0_benefit_dollars': criteria_veh_low_7_benefit_dollars,
                    'criteria_vehicle_high_3.0_benefit_dollars': criteria_veh_high_3_benefit_dollars,
                    'criteria_vehicle_high_7.0_benefit_dollars': criteria_veh_high_7_benefit_dollars,

                    'criteria_upstream_low_3.0_benefit_dollars': criteria_up_low_3_benefit_dollars,
                    'criteria_upstream_low_7.0_benefit_dollars': criteria_up_low_7_benefit_dollars,
                    'criteria_upstream_high_3.0_benefit_dollars': criteria_up_high_3_benefit_dollars,
                    'criteria_upstream_high_7.0_benefit_dollars': criteria_up_high_7_benefit_dollars,

                    'criteria_low_3.0_benefit_dollars': criteria_low_3_benefit_dollars,
                    'criteria_low_7.0_benefit_dollars': criteria_low_7_benefit_dollars,
                    'criteria_high_3.0_benefit_dollars': criteria_high_3_benefit_dollars,
                    'criteria_high_7.0_benefit_dollars': criteria_high_7_benefit_dollars,
                }
                )
            # save physical effects (reductions) to delta_physical_effects_dict, these were calculated as no_action
            # minus action, but the output file will be better as action minus no_action, so change sign
            physical_effects_dict_for_key = {
                'session_policy': physical_a['session_policy'],
                'session_name': physical_a['session_name'],
                'calendar_year': calendar_year,
                'reg_class_id': reg_class_id,
                'in_use_fuel_id': in_use_fuel_id,
                'fueling_class': fueling_class,
                'vmt': - oper_attrs_dict['vmt'],
                'vmt_rebound': - oper_attrs_dict['vmt_rebound'],
                'vmt_liquid_fuel': - oper_attrs_dict['vmt_liquid_fuel'],
                'vmt_electricity': - oper_attrs_dict['vmt_electricity'],
                'fuel_consumption_kWh': - oper_attrs_dict['fuel_consumption_kWh'],
                'fuel_consumption_gallons': - oper_attrs_dict['fuel_consumption_gallons'],
                'barrels_of_oil': - oil_barrels,
                'barrels_of_imported_oil': - imported_oil_bbl,
                'barrels_of_imported_oil_per_day': - imported_oil_bbl_per_day,
                'session_fatalities': physical_a['session_fatalities'] - physical_na['session_fatalities'],
                'co2_vehicle_metrictons': - ghg_tons_dict['co2_vehicle_metrictons'],
                'co2_upstream_metrictons': - ghg_tons_dict['co2_upstream_metrictons'],
                'co2_total_metrictons': - ghg_tons_dict['co2_total_metrictons'],
                'ch4_vehicle_metrictons': - ghg_tons_dict['ch4_vehicle_metrictons'],
                'ch4_upstream_metrictons': - ghg_tons_dict['ch4_upstream_metrictons'],
                'ch4_total_metrictons': - ghg_tons_dict['ch4_total_metrictons'],
                'n2o_vehicle_metrictons': - ghg_tons_dict['n2o_vehicle_metrictons'],
                'n2o_upstream_metrictons': - ghg_tons_dict['n2o_upstream_metrictons'],
                'n2o_total_metrictons': - ghg_tons_dict['n2o_total_metrictons'],
                'pm25_vehicle_ustons': - cap_tons_dict['pm25_vehicle_ustons'],
                'pm25_upstream_ustons': - cap_tons_dict['pm25_upstream_ustons'],
                'pm25_total_ustons': - cap_tons_dict['pm25_total_ustons'],
                'nox_vehicle_ustons': - cap_tons_dict['nox_vehicle_ustons'],
                'nox_upstream_ustons': - cap_tons_dict['nox_upstream_ustons'],
                'nox_total_ustons': - cap_tons_dict['nox_total_ustons'],
                'sox_vehicle_ustons': - cap_tons_dict['sox_vehicle_ustons'],
                'sox_upstream_ustons': - cap_tons_dict['sox_upstream_ustons'],
                'sox_total_ustons': - cap_tons_dict['sox_total_ustons'],
                'nmog_vehicle_ustons': - cap_tons_dict['nmog_vehicle_ustons'],
                'voc_upstream_ustons': - cap_tons_dict['voc_upstream_ustons'],
                'nmog_and_voc_total_ustons':- cap_tons_dict['nmog_and_voc_total_ustons'],
                'co_vehicle_ustons': - cap_tons_dict['co_vehicle_ustons'],
                'co_upstream_ustons': - cap_tons_dict['co_upstream_ustons'],
                'co_total_ustons': - cap_tons_dict['co_total_ustons'],
                'acetaldehyde_vehicle_ustons': - toxics_tons_dict['acetaldehyde_vehicle_ustons'],
                'acrolein_vehicle_ustons': - toxics_tons_dict['acrolein_vehicle_ustons'],
                'benzene_exhaust_ustons': - toxics_tons_dict['benzene_exhaust_ustons'],
                'benzene_evaporative_ustons': - toxics_tons_dict['benzene_evaporative_ustons'],
                'benzene_vehicle_ustons': - toxics_tons_dict['benzene_vehicle_ustons'],
                'ethylbenzene_exhaust_ustons': - toxics_tons_dict['ethylbenzene_exhaust_ustons'],
                'ethylbenzene_evaporative_ustons': - toxics_tons_dict['ethylbenzene_evaporative_ustons'],
                'ethylbenzene_vehicle_ustons': - toxics_tons_dict['ethylbenzene_vehicle_ustons'],
                'formaldehyde_vehicle_ustons': - toxics_tons_dict['formaldehyde_vehicle_ustons'],
                'naphthalene_exhaust_ustons': - toxics_tons_dict['naphthalene_exhaust_ustons'],
                'naphthalene_evaporative_ustons': - toxics_tons_dict['naphthalene_evaporative_ustons'],
                'naphthalene_vehicle_ustons': - toxics_tons_dict['naphthalene_vehicle_ustons'],
                '13_butadiene_vehicle_ustons': - toxics_tons_dict['13_butadiene_vehicle_ustons'],
                '15pah_vehicle_ustons': - toxics_tons_dict['15pah_vehicle_ustons'],
            }

        if flag:
            benefits_dict[key] = benefits_dict_for_key
            delta_physical_effects_dict[key] = physical_effects_dict_for_key

    return benefits_dict, delta_physical_effects_dict
