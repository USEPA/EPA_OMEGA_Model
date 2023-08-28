from omega_effects.effects.physical_effects import get_inputs_for_effects


def get_egu_emission_rate(session_settings, calendar_year, kwh_consumption, kwh_generation):
    """

    Args:
        session_settings: an instance of the SessionSettings class.
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

    return session_settings.emission_rates_egu.get_emission_rate(
        session_settings, calendar_year, kwh_consumption, kwh_generation, rate_names
    )


def calc_egu_inventory(batch_settings, session_settings, physical_effects_dict):
    """

    Args:
        batch_settings: an instance of the BatchSettings class
        session_settings: an instance of the SessionSettings class
        physical_effects_dict (dict): the physical effects for which to calculate EGU inventories

    Returns:
        The passed physical effects dictionary with EGU inventories included

    """
    grams_per_us_ton, grams_per_metric_ton, gal_per_bbl, e0_share, e0_energy_density_ratio, \
        diesel_energy_density_ratio, fuel_reduction_leading_to_reduced_domestic_refining = \
        get_inputs_for_effects(batch_settings)

    calendar_years = batch_settings.calendar_years

    for calendar_year in calendar_years:

        vad = [
            v for v in physical_effects_dict.values()
            if v['calendar_year'] == calendar_year and v['fuel_consumption_kwh'] != 0
        ]

        # first a loop to determine kwh demand for this calendar year for use in calculating EGU emission rates
        fuel_consumption_kwh_annual = fuel_generation_kwh_annual = 0
        for v in vad:
            fuel_consumption_kwh_annual += v['fuel_consumption_kwh']
            fuel_generation_kwh_annual += v['fuel_generation_kwh']

        # EGU emission rates for this calendar year to apply to electric fuel operation
        voc_egu_rate, co_egu_rate, nox_egu_rate, pm25_egu_rate, sox_egu_rate, \
            co2_egu_rate, ch4_egu_rate, n2o_egu_rate, hcl_egu_rate, hg_egu_rate = \
            get_egu_emission_rate(
                session_settings, calendar_year, fuel_consumption_kwh_annual, fuel_generation_kwh_annual
            )

        for v in physical_effects_dict.values():

            kwhs = v['fuel_consumption_kwh']

            if v['calendar_year'] == calendar_year:

                v['voc_egu_ustons'] = kwhs * voc_egu_rate / grams_per_us_ton
                v['co_egu_ustons'] = kwhs * co_egu_rate / grams_per_us_ton
                v['nox_egu_ustons'] = kwhs * nox_egu_rate / grams_per_us_ton
                v['pm25_egu_ustons'] = kwhs * pm25_egu_rate / grams_per_us_ton
                v['sox_egu_ustons'] = kwhs * sox_egu_rate / grams_per_us_ton
                v['hcl_egu_ustons'] = kwhs * hcl_egu_rate / grams_per_us_ton
                v['hg_egu_ustons'] = kwhs * hg_egu_rate / grams_per_us_ton

                v['co2_egu_metrictons'] = kwhs * co2_egu_rate / grams_per_metric_ton
                v['ch4_egu_metrictons'] = kwhs * ch4_egu_rate / grams_per_metric_ton
                v['n2o_egu_metrictons'] = kwhs * n2o_egu_rate / grams_per_metric_ton

    return physical_effects_dict
