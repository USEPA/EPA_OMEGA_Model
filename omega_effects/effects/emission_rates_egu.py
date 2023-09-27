"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents electricity generating unit emission rates by calendar year.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,emission_rates_egu,input_template_version:,0.3

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,case,kwh_consumption_low_bound,kwh_generation_us,pm25_grams_per_kwh,nox_grams_per_kwh,sox_grams_per_kwh,voc_grams_per_kwh,co_grams_per_kwh,co2_grams_per_kwh,ch4_grams_per_kwh,n2o_grams_per_kwh,hg_grams_per_kwh,hcl_grams_per_kwh
        2028,low_demand,7.95E+10,4.5E+12,0.014937349,0.090888889,0.078,7.33E-03,2.22222E-13,271.1111111,0.016733333,0.00229,5.04444E-07,0.524444444
        2029,low_demand,1.08E+11,4.585E+12,0.013857083,0.081739948,0.067372591,6.78E-03,2.18178E-13,240.4806091,0.014779943,2.01E-03,4.5779E-07,0.439952415
        2030,low_demand,1.37E+11,4.67E+12,0.012776817,0.072591006,0.056745182,6.23E-03,2.14133E-13,209.8501071,0.012826552,0.00172,4.11135E-07,0.355460385

Data Column Name and Description

    :calendar_year:
        The calendar year for which rates are sought.

    :case:
        The Integrated Planning Model (IPM) electricity demand case.

    :kwh_consumption_low_bound:
        The onroad kwh consumption used in IPM.

    :kwh_generation_us:
        The US EGU kwh demand used in IPM.

    :pm25_grams_per_kwh:
        The PM2.5 grams per kwh generated at the EGU.

    :nox_grams_per_kwh:
        The NOx grams per kwh generated at the EGU.

    :sox_grams_per_kwh:
        The SOx grams per kwh generated at the EGU.

    :voc_grams_per_kwh:
        The VOC grams per kwh generated at the EGU.

    :co_grams_per_kwh:
        The CO grams per kwh generated at the EGU.

    :co2_grams_per_kwh:
        The CO2 grams per kwh generated at the EGU.

    :ch4_grams_per_kwh:
        The CH4 grams per kwh generated at the EGU.

    :n2o_grams_per_kwh:
        The N2O grams per kwh generated at the EGU.

    :hg_grams_per_kwh:
        The Hg grams per kwh generated at the EGU.

    :hcl_grams_per_kwh:
        The HCl grams per kwh generated at the EGU.

----

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class EmissionRatesEGU:
    """
    Loads and provides access to power sector emissions factors  by calendar year.

    """
    def __init__(self):
        self._data = {}
        self.cases = None
        self._cache = {}
        self.calendar_year_min = None
        self.calendar_year_max = None
        self.rate_names = None
        self.deets = {}  # this dictionary will not include the legacy fleet

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_name = 'emission_rates_egu'
        input_template_version = 0.3
        input_template_columns = [
            'calendar_year',
            'case',
            'kwh_consumption_low_demand',
            'kwh_generation_us',
            'pm25_grams_per_kwh',
            'nox_grams_per_kwh',
            'sox_grams_per_kwh',
            'voc_grams_per_kwh',
            'co_grams_per_kwh',
            'co2_grams_per_kwh',
            'ch4_grams_per_kwh',
            'n2o_grams_per_kwh',
            'hg_grams_per_kwh',
            'hcl_grams_per_kwh',
        ]
        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self.rate_names = [rate_name for rate_name in df.columns if 'year' not in rate_name]
        self.calendar_year_min = int(min(df['calendar_year']))
        self.calendar_year_max = int(max(df['calendar_year']))
        self.cases = df['case'].unique()

        rate_keys = zip(
            df['calendar_year'],
            df['case'],
        )
        df.set_index(rate_keys, inplace=True)

        self._data = df.to_dict('index')

    def get_emission_rate(self, session_settings, cyear,
                          session_kwh_consumption, session_kwh_generation, rate_names):
        """

        Get emission rates by calendar year

        Args:
            session_settings: an instance of the SessionSettings class
            cyear (int): calendar year for which to get emission rates
            session_kwh_consumption (numeric): the session kwh to use (e.g., kwh_consumption or kwh_generation; this is omega-only)
            session_kwh_generation (numeric): the session kwh generation needed to satisfy kwh_session.
            rate_names (str, [strs]): name of emission rate(s) to get

        Returns:
            A list of emission rates for the given kwh_demand in the given calendar_year.

        """
        rates = []

        if cyear < self.calendar_year_min:
            calendar_year = self.calendar_year_min
        elif cyear > self.calendar_year_max:
            calendar_year = self.calendar_year_max
        else:
            calendar_year = cyear

        if cyear in self._cache:
            return self._cache[cyear]

        # else:
        kwh_demand_low = self._data[(calendar_year, 'low_demand')]['kwh_generation_us']
        kwh_demand_high = self._data[(calendar_year, 'high_demand')]['kwh_generation_us']
        kwh_consumption_ipm = self._data[(calendar_year, 'low_demand')]['kwh_consumption_low_demand']

        # back out the low-bound consumption provided to IPM to establish a base
        kwh_base = kwh_demand_low - kwh_consumption_ipm

        # add the kwh_session to the new kwh base value to determine the US base plus omega session consumption
        us_kwh_generation = session_kwh_generation + kwh_base

        for idx, rate_name in enumerate(rate_names):

            self.deets.update(
                {(cyear, rate_name): {
                    'session_policy': session_settings.session_policy,
                    'session_name': session_settings.session_name,
                    'calendar_year': cyear,
                    'kwh_demand_low': kwh_demand_low,
                    'kwh_demand_high': kwh_demand_high,
                    'kwh_consumption_ipm': kwh_consumption_ipm,
                    'kwh_base': kwh_base,
                    'us_kwh_generation': us_kwh_generation,
                    'fleet_kwh_consumption': session_kwh_consumption,
                    'fleet_kwh_generation': session_kwh_generation,
                    'rate_name': rate_name,
                }})
            rate_low = self._data[(calendar_year, 'low_demand')][rate_name]
            rate_high = self._data[(calendar_year, 'high_demand')][rate_name]

            # interpolate the rate for kwh_demand
            if calendar_year <= self.calendar_year_min:
                rate = rate_low
            else:
                rate = ((us_kwh_generation - kwh_demand_low) * (rate_high - rate_low) / (kwh_demand_high - kwh_demand_low)
                        + rate_low)

            rates.append(rate)
            if rate <= 0:
                rate = self._cache[cyear - 1][idx]

            self.deets[cyear, rate_name].update({
                'rate_low': rate_low,
                'rate_high': rate_high,
                'rate': rate,
                'US_inventory_grams_excl_legacy_fleet': rate * us_kwh_generation,
                'analysis_fleet_inventory_grams': rate * session_kwh_generation,
            })

        self._cache[cyear] = rates

        return rates
