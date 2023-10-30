"""

Total Inventory module.

----

**CODE**

"""
import pandas as pd


def calc_total_inventory(annual_physical_df):
    """
    Calc total inventory

    Args:
        annual_physical_df (DataFrame): a DataFrame of annual physical effects

    Returns:
        physical_effects_dict with emissions data

    """
    keys = pd.Series(zip(
        annual_physical_df['session_policy'],
        annual_physical_df['calendar_year'],
        annual_physical_df['reg_class_id'],
        annual_physical_df['in_use_fuel_id'],
        annual_physical_df['fueling_class'],
    ))
    df = annual_physical_df.set_index(keys)
    sessions_dict = df.to_dict('index')

    for k, v in sessions_dict.items():

        voc_upstream_ustons = v['voc_refinery_ustons'] + v['voc_egu_ustons']
        co_upstream_ustons = v['co_refinery_ustons'] + v['co_egu_ustons']
        nox_upstream_ustons = v['nox_refinery_ustons'] + v['nox_egu_ustons']
        pm25_upstream_ustons = v['pm25_refinery_ustons'] + v['pm25_egu_ustons']
        sox_upstream_ustons = v['sox_refinery_ustons'] + v['sox_egu_ustons']

        co2_upstream_metrictons = v['co2_refinery_metrictons'] + v['co2_egu_metrictons']
        ch4_upstream_metrictons = v['ch4_refinery_metrictons'] + v['ch4_egu_metrictons']
        n2o_upstream_metrictons = v['n2o_refinery_metrictons'] + v['n2o_egu_metrictons']

        # sum vehicle and upstream into totals
        nmog_and_voc_total_ustons = v['nmog_vehicle_ustons'] + voc_upstream_ustons
        co_total_ustons = v['co_vehicle_ustons'] + co_upstream_ustons
        nox_total_ustons = v['nox_vehicle_ustons'] + nox_upstream_ustons
        pm25_total_ustons = v['pm25_vehicle_ustons'] + pm25_upstream_ustons
        sox_total_ustons = v['sox_vehicle_ustons'] + sox_upstream_ustons
        acetaldehyde_total_ustons = v['acetaldehyde_vehicle_ustons']  # + acetaldehyde_upstream_ustons
        acrolein_total_ustons = v['acrolein_vehicle_ustons']  # + acrolein_upstream_ustons
        benzene_total_ustons = v['benzene_vehicle_ustons']  # + benzene_upstream_ustons
        ethylbenzene_total_ustons = v['ethylbenzene_vehicle_ustons']  # + ethylbenzene_upstream_ustons
        formaldehyde_total_ustons = v['formaldehyde_vehicle_ustons']  # + formaldehyde_upstream_ustons
        naphthalene_total_ustons = v['naphthalene_vehicle_ustons']  # + naphlathene_upstream_ustons
        butadiene13_total_ustons = v['13_butadiene_vehicle_ustons']  # + butadiene13_upstream_ustons
        pah15_total_ustons = v['15pah_vehicle_ustons']  # + pah15_upstream_ustons

        co2_total_metrictons = v['co2_vehicle_metrictons'] + co2_upstream_metrictons
        ch4_total_metrictons = v['ch4_vehicle_metrictons'] + ch4_upstream_metrictons
        n2o_total_metrictons = v['n2o_vehicle_metrictons'] + n2o_upstream_metrictons

        update_dict = {
            'voc_upstream_ustons': voc_upstream_ustons,
            'co_upstream_ustons': co_upstream_ustons,
            'nox_upstream_ustons': nox_upstream_ustons,
            'pm25_upstream_ustons': pm25_upstream_ustons,
            'sox_upstream_ustons': sox_upstream_ustons,
            'co2_upstream_metrictons': co2_upstream_metrictons,
            'ch4_upstream_metrictons': ch4_upstream_metrictons,
            'n2o_upstream_metrictons': n2o_upstream_metrictons,
            'nmog_and_voc_total_ustons': nmog_and_voc_total_ustons,
            'co_total_ustons': co_total_ustons,
            'nox_total_ustons': nox_total_ustons,
            'pm25_total_ustons': pm25_total_ustons,
            'sox_total_ustons': sox_total_ustons,
            'acetaldehyde_total_ustons': acetaldehyde_total_ustons,
            'acrolein_total_ustons': acrolein_total_ustons,
            'benzene_total_ustons': benzene_total_ustons,
            'ethylbenzene_total_ustons': ethylbenzene_total_ustons,
            'formaldehyde_total_ustons': formaldehyde_total_ustons,
            'naphthalene_total_ustons': naphthalene_total_ustons,
            '13butadiene_total_ustons': butadiene13_total_ustons,
            '15pah_total_ustons': pah15_total_ustons,
            'co2_total_metrictons': co2_total_metrictons,
            'ch4_total_metrictons': ch4_total_metrictons,
            'n2o_total_metrictons': n2o_total_metrictons,
        }
        for attribute_name, attribute_value in update_dict.items():
            sessions_dict[k][attribute_name] = attribute_value

    df = pd.DataFrame(sessions_dict).transpose()
    df.reset_index(drop=True, inplace=True)

    return df
