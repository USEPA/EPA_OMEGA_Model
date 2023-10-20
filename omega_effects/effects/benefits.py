"""

**OMEGA effects benefits module.**

----

**CODE**

"""
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
    cost_factors = (
        'co2_global_5.0_USD_per_metricton',
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
        'co2_domestic_5.0_USD_per_metricton',
        'co2_domestic_3.0_USD_per_metricton',
        'co2_domestic_2.5_USD_per_metricton',
        'co2_domestic_3.95_USD_per_metricton',
        'ch4_domestic_5.0_USD_per_metricton',
        'ch4_domestic_3.0_USD_per_metricton',
        'ch4_domestic_2.5_USD_per_metricton',
        'ch4_domestic_3.95_USD_per_metricton',
        'n2o_domestic_5.0_USD_per_metricton',
        'n2o_domestic_3.0_USD_per_metricton',
        'n2o_domestic_2.5_USD_per_metricton',
        'n2o_domestic_3.95_USD_per_metricton',
    )

    return batch_settings.scc_cost_factors.get_cost_factors(calendar_year, cost_factors)


def get_cap_cf(batch_settings, calendar_year, source_id):
    """

    Get criteria cost factors

    Args:
        batch_settings: an instance of the BatchSettings class.
        calendar_year (int): The calendar year for which criteria cost factors are needed.
        source_id (str): the pollutant source, e.g., 'car pump gasoline', 'egu', 'refinery'

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    cost_factors = (
        'pm25_Wu_3.0_USD_per_uston',
        'sox_Wu_3.0_USD_per_uston',
        'nox_Wu_3.0_USD_per_uston',
        'pm25_Wu_7.0_USD_per_uston',
        'sox_Wu_7.0_USD_per_uston',
        'nox_Wu_7.0_USD_per_uston',
        'pm25_Pope_3.0_USD_per_uston',
        'sox_Pope_3.0_USD_per_uston',
        'nox_Pope_3.0_USD_per_uston',
        'pm25_Pope_7.0_USD_per_uston',
        'sox_Pope_7.0_USD_per_uston',
        'nox_Pope_7.0_USD_per_uston',
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


def calc_delta(dict_na, dict_a, arg):

    if dict_na:
        if dict_a:
            return dict_na[arg] - dict_a[arg]
        else:
            return dict_na[arg]
    elif dict_a:
        return - dict_a[arg]
    else:
        return 0


def calc_benefits(batch_settings, annual_physical_effects_df, annual_cost_effects_df, calc_health_effects=False):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        annual_physical_effects_df (DataFrame): a DataFrame of physical effects by calendar year, reg class, fuel type.
        annual_cost_effects_df (DataFrame): a DataFrame of cost effects by calendar year, reg class, fuel type.
        calc_health_effects (bool): criteria air pollutant (cap) benefits will be calculated if True.

    Returns:
        Two dictionaries: one of benefits for each action session relative to the no_action session; and one of physical
        effects for each action session relative to the no_action session.

    """
    policies = annual_cost_effects_df['session_policy'].unique()
    action_policies = [policy for policy in policies if 'no_action' not in policy]
    calendar_years = annual_cost_effects_df['calendar_year'].unique()
    reg_class_ids = annual_cost_effects_df['reg_class_id'].unique()
    in_use_fuel_ids = annual_cost_effects_df['in_use_fuel_id'].unique()
    ice_fuel_ids = [fuel for fuel in in_use_fuel_ids if 'electricity' not in fuel]
    fueling_classes = annual_cost_effects_df['fueling_class'].unique()
    ice_fueling_classes = [fuel_class for fuel_class in fueling_classes if 'BEV' not in fuel_class]

    keys = pd.Series(zip(
        annual_physical_effects_df['session_policy'],
        annual_physical_effects_df['calendar_year'],
        annual_physical_effects_df['reg_class_id'],
        annual_physical_effects_df['in_use_fuel_id'],
        annual_physical_effects_df['fueling_class']
    ))
    annual_physical_effects_df.set_index(keys, inplace=True)
    physical_effects_dict = annual_physical_effects_df.to_dict('index')

    keys = pd.Series(zip(
        annual_cost_effects_df['session_policy'],
        annual_cost_effects_df['calendar_year'],
        annual_cost_effects_df['reg_class_id'],
        annual_cost_effects_df['in_use_fuel_id'],
        annual_cost_effects_df['fueling_class']
    ))
    annual_cost_effects_df.set_index(keys, inplace=True)
    cost_effects_dict = annual_cost_effects_df.to_dict('index')

    benefits_dict = {}
    delta_physical_effects_dict = {}

    for policy in action_policies:
        for calendar_year in calendar_years:
            for reg_class_id in reg_class_ids:
                for in_use_fuel_id in in_use_fuel_ids:
                    for fueling_class in fueling_classes:
                        if ((fueling_class in ice_fueling_classes and in_use_fuel_id in ice_fuel_ids) or
                                (fueling_class == 'BEV' and 'electricity' in in_use_fuel_id)):

                            key_a = (policy, calendar_year, reg_class_id, in_use_fuel_id, fueling_class)
                            key_na = ('no_action', calendar_year, reg_class_id, in_use_fuel_id, fueling_class)

                            if key_a in physical_effects_dict:
                                physical_a = physical_effects_dict[key_a]
                                cost_a = cost_effects_dict[key_a]
                                session_name = physical_a['session_name']
                            else:
                                physical_a = cost_a = None
                            if key_na in physical_effects_dict:
                                physical_na = physical_effects_dict[key_na]
                                cost_na = cost_effects_dict[key_na]
                            else:
                                physical_na = cost_na = None

                            energy_security_benefit_dollars = 0
                            pm25_up_Wu_3_benefit_dollars = sox_up_Wu_3_benefit_dollars = nox_up_Wu_3_benefit_dollars = 0
                            pm25_up_Wu_7_benefit_dollars = sox_up_Wu_7_benefit_dollars = nox_up_Wu_7_benefit_dollars = 0
                            pm25_up_Pope_3_benefit_dollars=sox_up_Pope_3_benefit_dollars=nox_up_Pope_3_benefit_dollars = 0
                            pm25_up_Pope_7_benefit_dollars=sox_up_Pope_7_benefit_dollars=nox_up_Pope_7_benefit_dollars = 0
                            pm25_veh_Wu_3_benefit_dollars = sox_veh_Wu_3_benefit_dollars = nox_veh_Wu_3_benefit_dollars = 0
                            pm25_veh_Wu_7_benefit_dollars = sox_veh_Wu_7_benefit_dollars = nox_veh_Wu_7_benefit_dollars=0
                            pm25_veh_Pope_3_benefit_dollars=sox_veh_Pope_3_benefit_dollars=nox_veh_Pope_3_benefit_dollars=0
                            pm25_veh_Pope_7_benefit_dollars=sox_veh_Pope_7_benefit_dollars=nox_veh_Pope_7_benefit_dollars=0
                            cap_veh_Wu_3_benefit_dollars = cap_veh_Wu_7_benefit_dollars = 0
                            cap_veh_Pope_3_benefit_dollars = cap_veh_Pope_7_benefit_dollars = 0
                            cap_up_Wu_3_benefit_dollars = cap_up_Wu_7_benefit_dollars = 0
                            cap_up_Pope_3_benefit_dollars = cap_up_Pope_7_benefit_dollars = 0
                            cap_Wu_3_benefit_dollars = cap_Wu_7_benefit_dollars = 0
                            cap_Pope_3_benefit_dollars = cap_Pope_7_benefit_dollars = 0

                            fuel_dict = eval(in_use_fuel_id)
                            fuel = [item for item in fuel_dict.keys()][0]

                            # operating costs __________________________________________________________________________
                            oper_attrs_dict = {}
                            oper_attrs_list = [
                                'vmt',
                                'vmt_rebound',
                                'fuel_consumption_kwh',
                                'fuel_consumption_gallons',
                                'petroleum_consumption_gallons',
                                # 'domestic_refined_gallons',
                            ]
                            for oper_attr in oper_attrs_list:
                                oper_attrs_dict[oper_attr] = calc_delta(physical_na, physical_a, oper_attr)

                            # energy security benefits _________________________________________________________________
                            oil_barrels = calc_delta(physical_na, physical_a, 'barrels_of_oil')
                            imported_oil_bbl = calc_delta(physical_na, physical_a, 'change_in_barrels_of_oil_imports')
                            imported_oil_bbl_per_day = calc_delta(
                                physical_na, physical_a, 'change_in_barrels_of_oil_imports_per_day'
                            )
                            energy_security_cf = get_energysecurity_cf(batch_settings, calendar_year)
                            energy_security_benefit_dollars += imported_oil_bbl * energy_security_cf

                            # calc drive value as drive_value_cost in action less drive_value_cost in no_action; negative
                            # sign makes this calc be action minus no_action, which is what we want for this attribute
                            drive_value_benefit_dollars = - calc_delta(cost_na, cost_a, 'drive_value_cost_dollars')

                            # fatalities; negaitve sign makes it action minus no_action_____________________________
                            fatalities = - calc_delta(physical_na, physical_a, 'session_fatalities')

                            # climate inventories __________________________________________________________________
                            ghg_tons_dict = {}
                            ghg_list = [
                                'co2_vehicle_metrictons',
                                'co2_refinery_metrictons',
                                'co2_egu_metrictons',
                                'co2_upstream_metrictons',
                                'co2_total_metrictons',
                                'ch4_vehicle_metrictons',
                                'ch4_refinery_metrictons',
                                'ch4_egu_metrictons',
                                'ch4_upstream_metrictons',
                                'ch4_total_metrictons',
                                'n2o_vehicle_metrictons',
                                'n2o_refinery_metrictons',
                                'n2o_egu_metrictons',
                                'n2o_upstream_metrictons',
                                'n2o_total_metrictons',
                            ]
                            for ghg in ghg_list:
                                ghg_tons_dict[ghg] = calc_delta(physical_na, physical_a, ghg)

                            # calculate climate benefits _______________________________________________________________
                            # get scc cost factors
                            co2_global_5, co2_global_3, co2_global_25, co2_global_395, \
                                ch4_global_5, ch4_global_3, ch4_global_25, ch4_global_395, \
                                n2o_global_5, n2o_global_3, n2o_global_25, n2o_global_395, \
                                co2_domestic_5, co2_domestic_3, co2_domestic_25, co2_domestic_395, \
                                ch4_domestic_5, ch4_domestic_3, ch4_domestic_25, ch4_domestic_395, \
                                n2o_domestic_5, n2o_domestic_3, n2o_domestic_25, n2o_domestic_395 \
                                = get_scc_cf(batch_settings, calendar_year)

                            co2_tons = ghg_tons_dict['co2_total_metrictons']
                            co2_global_5_benefit_dollars = co2_tons * co2_global_5
                            co2_global_3_benefit_dollars = co2_tons * co2_global_3
                            co2_global_25_benefit_dollars = co2_tons * co2_global_25
                            co2_global_395_benefit_dollars = co2_tons * co2_global_395
                            co2_domestic_5_benefit_dollars = co2_tons * co2_domestic_5
                            co2_domestic_3_benefit_dollars = co2_tons * co2_domestic_3
                            co2_domestic_25_benefit_dollars = co2_tons * co2_domestic_25
                            co2_domestic_395_benefit_dollars = co2_tons * co2_domestic_395

                            ch4_tons = ghg_tons_dict['ch4_total_metrictons']
                            ch4_global_5_benefit_dollars = ch4_tons * ch4_global_5
                            ch4_global_3_benefit_dollars = ch4_tons * ch4_global_3
                            ch4_global_25_benefit_dollars = ch4_tons * ch4_global_25
                            ch4_global_395_benefit_dollars = ch4_tons * ch4_global_395
                            ch4_domestic_5_benefit_dollars = ch4_tons * ch4_domestic_5
                            ch4_domestic_3_benefit_dollars = ch4_tons * ch4_domestic_3
                            ch4_domestic_25_benefit_dollars = ch4_tons * ch4_domestic_25
                            ch4_domestic_395_benefit_dollars = ch4_tons * ch4_domestic_395

                            n2o_tons = ghg_tons_dict['n2o_total_metrictons']
                            n2o_global_5_benefit_dollars = n2o_tons * n2o_global_5
                            n2o_global_3_benefit_dollars = n2o_tons * n2o_global_3
                            n2o_global_25_benefit_dollars = n2o_tons * n2o_global_25
                            n2o_global_395_benefit_dollars = n2o_tons * n2o_global_395
                            n2o_domestic_5_benefit_dollars = n2o_tons * n2o_domestic_5
                            n2o_domestic_3_benefit_dollars = n2o_tons * n2o_domestic_3
                            n2o_domestic_25_benefit_dollars = n2o_tons * n2o_domestic_25
                            n2o_domestic_395_benefit_dollars = n2o_tons * n2o_domestic_395

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

                            ghg_domestic_5_benefit_dollars = co2_domestic_5_benefit_dollars \
                                                             + ch4_domestic_5_benefit_dollars \
                                                             + n2o_domestic_5_benefit_dollars
                            ghg_domestic_3_benefit_dollars = co2_domestic_3_benefit_dollars \
                                                             + ch4_domestic_3_benefit_dollars \
                                                             + n2o_domestic_3_benefit_dollars
                            ghg_domestic_25_benefit_dollars = co2_domestic_25_benefit_dollars \
                                                              + ch4_domestic_25_benefit_dollars \
                                                              + n2o_domestic_25_benefit_dollars
                            ghg_domestic_395_benefit_dollars = co2_domestic_395_benefit_dollars \
                                                               + ch4_domestic_395_benefit_dollars \
                                                               + n2o_domestic_395_benefit_dollars

                            # toxics inventories _______________________________________________________________________
                            toxics_tons_dict = {}
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
                                toxics_tons_dict[toxic] = calc_delta(physical_na, physical_a, toxic)

                            # criteria air pollutant (cap) inventories _________________________________________________
                            cap_tons_dict = {}
                            cap_list = [
                                'pm25_vehicle_ustons',
                                'pm25_refinery_ustons',
                                'pm25_egu_ustons',
                                'pm25_upstream_ustons',
                                'pm25_total_ustons',
                                'nox_vehicle_ustons',
                                'nox_refinery_ustons',
                                'nox_egu_ustons',
                                'nox_upstream_ustons',
                                'nox_total_ustons',
                                'sox_vehicle_ustons',
                                'sox_refinery_ustons',
                                'sox_egu_ustons',
                                'sox_upstream_ustons',
                                'sox_total_ustons',
                                'nmog_vehicle_ustons',
                                'voc_refinery_ustons',
                                'voc_egu_ustons',
                                'voc_upstream_ustons',
                                'nmog_and_voc_total_ustons',
                                'co_vehicle_ustons',
                                'co_refinery_ustons',
                                'co_egu_ustons',
                                'co_upstream_ustons',
                                'co_total_ustons',
                            ]
                            for cap in cap_list:
                                cap_tons_dict[cap] = calc_delta(physical_na, physical_a, cap)

                            # calculate cap benefits, if applicable ____________________________________________________
                            if calc_health_effects:

                                # get vehicle cap cost factors
                                source_id = f'{reg_class_id} {fuel}'
                                pm25_Wu_3, sox_Wu_3, nox_Wu_3, \
                                    pm25_Wu_7, sox_Wu_7, nox_Wu_7, \
                                    pm25_Pope_3, sox_Pope_3, nox_Pope_3, \
                                    pm25_Pope_7, sox_Pope_7, nox_Pope_7 = get_cap_cf(
                                    batch_settings, calendar_year, source_id
                                )
                                pm25_tons, sox_tons, nox_tons = (
                                    cap_tons_dict['pm25_vehicle_ustons'],
                                    cap_tons_dict['sox_vehicle_ustons'],
                                    cap_tons_dict['nox_vehicle_ustons']
                                )
                                pm25_veh_Wu_3_benefit_dollars = pm25_tons * pm25_Wu_3
                                sox_veh_Wu_3_benefit_dollars = sox_tons * sox_Wu_3
                                nox_veh_Wu_3_benefit_dollars = nox_tons * nox_Wu_3
                                pm25_veh_Wu_7_benefit_dollars = pm25_tons * pm25_Wu_7
                                sox_veh_Wu_7_benefit_dollars = sox_tons * sox_Wu_7
                                nox_veh_Wu_7_benefit_dollars = nox_tons * nox_Wu_7
                                pm25_veh_Pope_3_benefit_dollars = pm25_tons * pm25_Pope_3
                                sox_veh_Pope_3_benefit_dollars = sox_tons * sox_Pope_3
                                nox_veh_Pope_3_benefit_dollars = nox_tons * nox_Pope_3
                                pm25_veh_Pope_7_benefit_dollars = pm25_tons * pm25_Pope_7
                                sox_veh_Pope_7_benefit_dollars = sox_tons * sox_Pope_7
                                nox_veh_Pope_7_benefit_dollars = nox_tons * nox_Pope_7

                                # get upstream cap cost factors
                                for source_id in ['egu', 'refinery']:
                                    pm25_Wu_3, sox_Wu_3, nox_Wu_3, \
                                        pm25_Wu_7, sox_Wu_7, nox_Wu_7, \
                                        pm25_Pope_3, sox_Pope_3, nox_Pope_3, \
                                        pm25_Pope_7, sox_Pope_7, nox_Pope_7 = get_cap_cf(
                                        batch_settings, calendar_year, source_id
                                    )
                                    pm25_tons, sox_tons, nox_tons = (
                                        cap_tons_dict[f'pm25_{source_id}_ustons'],
                                        cap_tons_dict[f'sox_{source_id}_ustons'],
                                        cap_tons_dict[f'nox_{source_id}_ustons']
                                    )
                                    pm25_up_Wu_3_benefit_dollars += pm25_tons * pm25_Wu_3
                                    sox_up_Wu_3_benefit_dollars += sox_tons * sox_Wu_3
                                    nox_up_Wu_3_benefit_dollars += nox_tons * nox_Wu_3
                                    pm25_up_Wu_7_benefit_dollars += pm25_tons * pm25_Wu_7
                                    sox_up_Wu_7_benefit_dollars += sox_tons * sox_Wu_7
                                    nox_up_Wu_7_benefit_dollars += nox_tons * nox_Wu_7
                                    pm25_up_Pope_3_benefit_dollars += pm25_tons * pm25_Pope_3
                                    sox_up_Pope_3_benefit_dollars += sox_tons * sox_Pope_3
                                    nox_up_Pope_3_benefit_dollars += nox_tons * nox_Pope_3
                                    pm25_up_Pope_7_benefit_dollars += pm25_tons * pm25_Pope_7
                                    sox_up_Pope_7_benefit_dollars += sox_tons * sox_Pope_7
                                    nox_up_Pope_7_benefit_dollars += nox_tons * nox_Pope_7

                                cap_veh_Wu_3_benefit_dollars = (
                                        pm25_veh_Wu_3_benefit_dollars +
                                        sox_veh_Wu_3_benefit_dollars +
                                        nox_veh_Wu_3_benefit_dollars
                                )
                                cap_veh_Wu_7_benefit_dollars = (
                                        pm25_veh_Wu_7_benefit_dollars +
                                        sox_veh_Wu_7_benefit_dollars +
                                        nox_veh_Wu_7_benefit_dollars
                                )
                                cap_veh_Pope_3_benefit_dollars = (
                                        pm25_veh_Pope_3_benefit_dollars +
                                        sox_veh_Pope_3_benefit_dollars +
                                        nox_veh_Pope_3_benefit_dollars
                                )
                                cap_veh_Pope_7_benefit_dollars = (
                                        pm25_veh_Pope_7_benefit_dollars +
                                        sox_veh_Pope_7_benefit_dollars +
                                        nox_veh_Pope_7_benefit_dollars
                                )
                                cap_up_Wu_3_benefit_dollars = (
                                        pm25_up_Wu_3_benefit_dollars +
                                        sox_up_Wu_3_benefit_dollars +
                                        nox_up_Wu_3_benefit_dollars
                                )
                                cap_up_Wu_7_benefit_dollars = (
                                        pm25_up_Wu_7_benefit_dollars +
                                        sox_up_Wu_7_benefit_dollars +
                                        nox_up_Wu_7_benefit_dollars
                                )
                                cap_up_Pope_3_benefit_dollars = (
                                        pm25_up_Pope_3_benefit_dollars +
                                        sox_up_Pope_3_benefit_dollars +
                                        nox_up_Pope_3_benefit_dollars
                                )
                                cap_up_Pope_7_benefit_dollars = (
                                        pm25_up_Pope_7_benefit_dollars +
                                        sox_up_Pope_7_benefit_dollars +
                                        nox_up_Pope_7_benefit_dollars
                                )
                                cap_Wu_3_benefit_dollars = cap_veh_Wu_3_benefit_dollars + cap_up_Wu_3_benefit_dollars
                                cap_Wu_7_benefit_dollars = cap_veh_Wu_7_benefit_dollars + cap_up_Wu_7_benefit_dollars
                                cap_Pope_3_benefit_dollars = (
                                        cap_veh_Pope_3_benefit_dollars + cap_up_Pope_3_benefit_dollars
                                )
                                cap_Pope_7_benefit_dollars = (
                                        cap_veh_Pope_7_benefit_dollars + cap_up_Pope_7_benefit_dollars
                                )

                            # save monetized benefit results in the benefits_dict for this key _________________________
                            benefits_dict_for_key = {
                                'session_policy': policy,
                                'session_name': session_name,
                                'discount_rate': 0,
                                'series': 'AnnualValue',
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

                                'co2_domestic_5.0_benefit_dollars': co2_domestic_5_benefit_dollars,
                                'co2_domestic_3.0_benefit_dollars': co2_domestic_3_benefit_dollars,
                                'co2_domestic_2.5_benefit_dollars': co2_domestic_25_benefit_dollars,
                                'co2_domestic_3.95_benefit_dollars': co2_domestic_395_benefit_dollars,
                                'ch4_domestic_5.0_benefit_dollars': ch4_domestic_5_benefit_dollars,
                                'ch4_domestic_3.0_benefit_dollars': ch4_domestic_3_benefit_dollars,
                                'ch4_domestic_2.5_benefit_dollars': ch4_domestic_25_benefit_dollars,
                                'ch4_domestic_3.95_benefit_dollars': ch4_domestic_395_benefit_dollars,
                                'n2o_domestic_5.0_benefit_dollars': n2o_domestic_5_benefit_dollars,
                                'n2o_domestic_3.0_benefit_dollars': n2o_domestic_3_benefit_dollars,
                                'n2o_domestic_2.5_benefit_dollars': n2o_domestic_25_benefit_dollars,
                                'n2o_domestic_3.95_benefit_dollars': n2o_domestic_395_benefit_dollars,
                                'ghg_domestic_5.0_benefit_dollars': ghg_domestic_5_benefit_dollars,
                                'ghg_domestic_3.0_benefit_dollars': ghg_domestic_3_benefit_dollars,
                                'ghg_domestic_2.5_benefit_dollars': ghg_domestic_25_benefit_dollars,
                                'ghg_domestic_3.95_benefit_dollars': ghg_domestic_395_benefit_dollars,
                            }
                            if calc_health_effects:
                                benefits_dict_for_key.update({
                                    'pm25_vehicle_Wu_3.0_benefit_dollars': pm25_veh_Wu_3_benefit_dollars,
                                    'sox_vehicle_Wu_3.0_benefit_dollars': sox_veh_Wu_3_benefit_dollars,
                                    'nox_vehicle_Wu_3.0_benefit_dollars': nox_veh_Wu_3_benefit_dollars,
                                    'pm25_vehicle_Wu_7.0_benefit_dollars': pm25_veh_Wu_7_benefit_dollars,
                                    'sox_vehicle_Wu_7.0_benefit_dollars': sox_veh_Wu_7_benefit_dollars,
                                    'nox_vehicle_Wu_7.0_benefit_dollars': nox_veh_Wu_7_benefit_dollars,

                                    'pm25_vehicle_Pope_3.0_benefit_dollars': pm25_veh_Pope_3_benefit_dollars,
                                    'sox_vehicle_Pope_3.0_benefit_dollars': sox_veh_Pope_3_benefit_dollars,
                                    'nox_vehicle_Pope_3.0_benefit_dollars': nox_veh_Pope_3_benefit_dollars,
                                    'pm25_vehicle_Pope_7.0_benefit_dollars': pm25_veh_Pope_7_benefit_dollars,
                                    'sox_vehicle_Pope_7.0_benefit_dollars': sox_veh_Pope_7_benefit_dollars,
                                    'nox_vehicle_Pope_7.0_benefit_dollars': nox_veh_Pope_7_benefit_dollars,

                                    'pm25_upstream_Wu_3.0_benefit_dollars': pm25_up_Wu_3_benefit_dollars,
                                    'sox_upstream_Wu_3.0_benefit_dollars': sox_up_Wu_3_benefit_dollars,
                                    'nox_upstream_Wu_3.0_benefit_dollars': nox_up_Wu_3_benefit_dollars,
                                    'pm25_upstream_Wu_7.0_benefit_dollars': pm25_up_Wu_7_benefit_dollars,
                                    'sox_upstream_Wu_7.0_benefit_dollars': sox_up_Wu_7_benefit_dollars,
                                    'nox_upstream_Wu_7.0_benefit_dollars': nox_up_Wu_7_benefit_dollars,

                                    'pm25_upstream_Pope_3.0_benefit_dollars': pm25_up_Pope_3_benefit_dollars,
                                    'sox_upstream_Pope_3.0_benefit_dollars': sox_up_Pope_3_benefit_dollars,
                                    'nox_upstream_Pope_3.0_benefit_dollars': nox_up_Pope_3_benefit_dollars,
                                    'pm25_upstream_Pope_7.0_benefit_dollars': pm25_up_Pope_7_benefit_dollars,
                                    'sox_upstream_Pope_7.0_benefit_dollars': sox_up_Pope_7_benefit_dollars,
                                    'nox_upstream_Pope_7.0_benefit_dollars': nox_up_Pope_7_benefit_dollars,

                                    'cap_vehicle_Wu_3.0_benefit_dollars': cap_veh_Wu_3_benefit_dollars,
                                    'cap_vehicle_Wu_7.0_benefit_dollars': cap_veh_Wu_7_benefit_dollars,
                                    'cap_vehicle_Pope_3.0_benefit_dollars': cap_veh_Pope_3_benefit_dollars,
                                    'cap_vehicle_Pope_7.0_benefit_dollars': cap_veh_Pope_7_benefit_dollars,

                                    'cap_upstream_Wu_3.0_benefit_dollars': cap_up_Wu_3_benefit_dollars,
                                    'cap_upstream_Wu_7.0_benefit_dollars': cap_up_Wu_7_benefit_dollars,
                                    'cap_upstream_Pope_3.0_benefit_dollars': cap_up_Pope_3_benefit_dollars,
                                    'cap_upstream_Pope_7.0_benefit_dollars': cap_up_Pope_7_benefit_dollars,

                                    'cap_Wu_3.0_benefit_dollars': cap_Wu_3_benefit_dollars,
                                    'cap_Wu_7.0_benefit_dollars': cap_Wu_7_benefit_dollars,
                                    'cap_Pope_3.0_benefit_dollars': cap_Pope_3_benefit_dollars,
                                    'cap_Pope_7.0_benefit_dollars': cap_Pope_7_benefit_dollars,
                                }
                                )
                            # save physical effects (reductions) to delta_physical_effects_dict, these were calculated as no_action
                            # minus action, but the output file will be better as action minus no_action, so change sign
                            physical_effects_dict_for_key = {
                                'session_policy': policy,
                                'session_name': session_name,
                                'calendar_year': calendar_year,
                                'reg_class_id': reg_class_id,
                                'in_use_fuel_id': in_use_fuel_id,
                                'fueling_class': fueling_class,
                                'vmt': - oper_attrs_dict['vmt'],
                                'vmt_rebound': - oper_attrs_dict['vmt_rebound'],
                                'fuel_consumption_kwh': - oper_attrs_dict['fuel_consumption_kwh'],
                                'fuel_consumption_gallons': - oper_attrs_dict['fuel_consumption_gallons'],
                                'petroleum_consumption_gallons': - oper_attrs_dict['petroleum_consumption_gallons'],
                                # 'domestic_refined_gallons': - oper_attrs_dict['domestic_refined_gallons'],
                                'barrels_of_oil': - oil_barrels,
                                'change_in_barrels_of_oil_imports': - imported_oil_bbl,
                                'change_in_barrels_of_oil_imports_per_day': - imported_oil_bbl_per_day,
                                'session_fatalities': fatalities,
                                'co2_vehicle_metrictons': - ghg_tons_dict['co2_vehicle_metrictons'],
                                'co2_refinery_metrictons': -ghg_tons_dict['co2_refinery_metrictons'],
                                'co2_egu_metrictons': -ghg_tons_dict['co2_egu_metrictons'],
                                'co2_upstream_metrictons': - ghg_tons_dict['co2_upstream_metrictons'],
                                'co2_total_metrictons': - ghg_tons_dict['co2_total_metrictons'],
                                'ch4_vehicle_metrictons': - ghg_tons_dict['ch4_vehicle_metrictons'],
                                'ch4_refinery_metrictons': -ghg_tons_dict['ch4_refinery_metrictons'],
                                'ch4_egu_metrictons': -ghg_tons_dict['ch4_egu_metrictons'],
                                'ch4_upstream_metrictons': - ghg_tons_dict['ch4_upstream_metrictons'],
                                'ch4_total_metrictons': - ghg_tons_dict['ch4_total_metrictons'],
                                'n2o_vehicle_metrictons': - ghg_tons_dict['n2o_vehicle_metrictons'],
                                'n2o_refinery_metrictons': -ghg_tons_dict['n2o_refinery_metrictons'],
                                'n2o_egu_metrictons': -ghg_tons_dict['n2o_egu_metrictons'],
                                'n2o_upstream_metrictons': - ghg_tons_dict['n2o_upstream_metrictons'],
                                'n2o_total_metrictons': - ghg_tons_dict['n2o_total_metrictons'],
                                'pm25_vehicle_ustons': - cap_tons_dict['pm25_vehicle_ustons'],
                                'pm25_refinery_ustons': -cap_tons_dict['pm25_refinery_ustons'],
                                'pm25_egu_ustons': -cap_tons_dict['pm25_egu_ustons'],
                                'pm25_upstream_ustons': - cap_tons_dict['pm25_upstream_ustons'],
                                'pm25_total_ustons': - cap_tons_dict['pm25_total_ustons'],
                                'nox_vehicle_ustons': - cap_tons_dict['nox_vehicle_ustons'],
                                'nox_refinery_ustons': -cap_tons_dict['nox_refinery_ustons'],
                                'nox_egu_ustons': -cap_tons_dict['nox_egu_ustons'],
                                'nox_upstream_ustons': - cap_tons_dict['nox_upstream_ustons'],
                                'nox_total_ustons': - cap_tons_dict['nox_total_ustons'],
                                'sox_vehicle_ustons': - cap_tons_dict['sox_vehicle_ustons'],
                                'sox_refinery_ustons': -cap_tons_dict['sox_refinery_ustons'],
                                'sox_egu_ustons': -cap_tons_dict['sox_egu_ustons'],
                                'sox_upstream_ustons': - cap_tons_dict['sox_upstream_ustons'],
                                'sox_total_ustons': - cap_tons_dict['sox_total_ustons'],
                                'nmog_vehicle_ustons': - cap_tons_dict['nmog_vehicle_ustons'],
                                'voc_refinery_ustons': -cap_tons_dict['voc_refinery_ustons'],
                                'voc_egu_ustons': -cap_tons_dict['voc_egu_ustons'],
                                'voc_upstream_ustons': - cap_tons_dict['voc_upstream_ustons'],
                                'nmog_and_voc_total_ustons': - cap_tons_dict['nmog_and_voc_total_ustons'],
                                'co_vehicle_ustons': - cap_tons_dict['co_vehicle_ustons'],
                                'co_refinery_ustons': -cap_tons_dict['co_refinery_ustons'],
                                'co_egu_ustons': -cap_tons_dict['co_egu_ustons'],
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

                            benefits_dict[key_a] = benefits_dict_for_key
                            delta_physical_effects_dict[key_a] = physical_effects_dict_for_key

    return benefits_dict, delta_physical_effects_dict
