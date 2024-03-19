import pandas as pd

from omega_effects.effects.physical_effects import get_inputs_for_effects


def get_egu_emission_rate(batch_settings, v, calendar_year, kwh_consumption, kwh_generation):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        v (dict): a dictionary of annual physical effects values.
        calendar_year (int): The calendar year for which egu emission rates are needed.
        kwh_consumption (float): The energy consumed by the fleet measured at the wall or charger outlet.
        kwh_generation (float): The energy generation required to satisfy kwh_consumption.

    Returns:
        A list of EGU emission rates for the given calendar year.

    """
    rate_names = (
        'voc_grams_per_kwh',
        'co_grams_per_kwh',
        'nox_grams_per_kwh',
        'pm25_grams_per_kwh',
        'sox_grams_per_kwh',
        'co2_grams_per_kwh',
        'ch4_grams_per_kwh',
        'n2o_grams_per_kwh',
        'hcl_grams_per_kwh',
        'hg_grams_per_kwh',
    )

    return batch_settings.egu_data.get_emission_rate(v, calendar_year, kwh_consumption, kwh_generation, rate_names)


def calc_egu_inventory(batch_settings, annual_physical_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class
        annual_physical_df (DataFrame): a DataFrame of annual physical effects

    Returns:
        The passed physical effects dictionary with EGU inventories included

    """
    (grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share,
     e0_energy_density_ratio, diesel_energy_density_ratio, gwp_ch4, gwp_n2o) = get_inputs_for_effects(batch_settings)
    gwp_list = [gwp_ch4, gwp_n2o]

    calendar_years = batch_settings.calendar_years
    session_policies = annual_physical_df['session_policy'].unique()

    keys = pd.Series(zip(
        annual_physical_df['session_policy'],
        annual_physical_df['calendar_year'],
        annual_physical_df['reg_class_id'],
        annual_physical_df['in_use_fuel_id'],
        annual_physical_df['fueling_class'],
    ))
    df = annual_physical_df.set_index(keys)
    sessions_dict = df.to_dict('index')

    for session_policy in session_policies:
        for calendar_year in calendar_years:

            vad = [
                v for v in sessions_dict.values()
                if v['session_policy'] == session_policy and
                   v['calendar_year'] == calendar_year and
                   v['fuel_consumption_kwh'] != 0
            ]

            # first a loop to determine kwh demand for this calendar year for use in calculating EGU emission rates
            fuel_consumption_kwh_annual = fuel_generation_kwh_annual = 0
            for v in vad:
                fuel_consumption_kwh_annual += v['fuel_consumption_kwh']
                fuel_generation_kwh_annual += v['fuel_generation_kwh']

            for k, v in sessions_dict.items():

                if v['session_policy'] == session_policy and v['calendar_year'] == calendar_year:

                    # EGU emission rates for this calendar year to apply to electric fuel operation
                    voc_egu_rate, co_egu_rate, nox_egu_rate, pm25_egu_rate, sox_egu_rate, \
                        co2_egu_rate, ch4_egu_rate, n2o_egu_rate, hcl_egu_rate, hg_egu_rate = \
                        get_egu_emission_rate(
                            batch_settings, v, calendar_year, fuel_consumption_kwh_annual, fuel_generation_kwh_annual
                        )

                    kwhs = v['fuel_generation_kwh']

                    voc_egu_ustons = kwhs * voc_egu_rate / grams_per_us_ton
                    co_egu_ustons = kwhs * co_egu_rate / grams_per_us_ton
                    nox_egu_ustons = kwhs * nox_egu_rate / grams_per_us_ton
                    pm25_egu_ustons = kwhs * pm25_egu_rate / grams_per_us_ton
                    sox_egu_ustons = kwhs * sox_egu_rate / grams_per_us_ton
                    hcl_egu_ustons = kwhs * hcl_egu_rate / grams_per_us_ton
                    hg_egu_ustons = kwhs * hg_egu_rate / grams_per_us_ton

                    co2_egu_metrictons = kwhs * co2_egu_rate / grams_per_metric_ton
                    ch4_egu_metrictons = kwhs * ch4_egu_rate / grams_per_metric_ton
                    n2o_egu_metrictons = kwhs * n2o_egu_rate / grams_per_metric_ton
                    co2e_egu_metrictons = (
                            co2_egu_metrictons + (ch4_egu_metrictons * gwp_ch4) + (n2o_egu_metrictons * gwp_n2o)
                    )
                    update_dict = {
                        'voc_egu_ustons': voc_egu_ustons,
                        'co_egu_ustons': co_egu_ustons,
                        'nox_egu_ustons': nox_egu_ustons,
                        'pm25_egu_ustons': pm25_egu_ustons,
                        'sox_egu_ustons': sox_egu_ustons,
                        'hcl_egu_ustons': hcl_egu_ustons,
                        'hg_egu_ustons': hg_egu_ustons,
                        'co2_egu_metrictons': co2_egu_metrictons,
                        'ch4_egu_metrictons': ch4_egu_metrictons,
                        'n2o_egu_metrictons': n2o_egu_metrictons,
                        'co2e_egu_metrictons': co2e_egu_metrictons,
                    }
                    for attribute_name, attribute_value in update_dict.items():
                        sessions_dict[k][attribute_name] = attribute_value

    df = pd.DataFrame(sessions_dict).transpose()
    df.reset_index(drop=True, inplace=True)

    return df
