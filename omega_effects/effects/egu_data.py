"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent electricity generating unit (EGU) data used to generate emission rates for EGU inventory estimates
within OMEGA.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,egu_data,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,case,kwh_demand,kwh_generation_us,sox_metrictons,pm25_metrictons,nox_metrictons,voc_metrictons,co2_metrictons,ch4_metrictons,n2o_metrictons,hg_metrictons,hcl_metrictons
        2028,low_demand,79544639445.48,4497701954660.72,351072.8942,67218.07241,409162.2661,33001.24309,1217556478,75270.3264,10333.44158,2.266368225,2356910.393
        2030,low_demand,136558511832.60,4670151092867.58,264774.1044,59667.73307,338642.6739,29077.65143,980444588.3,59870.49167,8050.273584,1.924340284,1658513.655
        2035,low_demand,251608375612.76,5095669022035.69,119985.3562,42787.22665,197024.4201,23023.12353,619769856.1,36184.84215,4718.077117,1.463955288,844965.4172
        2040,low_demand,337855975636.14,5537703812563.29,82765.50429,35133.53722,149311.1201,19945.30642,485460423.1,28218.38031,3658.722776,1.322392791,645510.4954
        2045,low_demand,395977141924.21,5950705341882.59,39601.46297,27478.64502,103515.9881,16877.89892,415403127.8,17387.75667,2136.312547,1.055589504,215388.0036
        2050,low_demand,429009640863.85,6436548029793.40,16511.33781,24217.59845,87459.74149,15520.55116,363816428.8,13906.12554,1668.277298,0.961601679,117719.2093

Data Column Name and Description

    :calendar_year:
        The calendar year for which the data are applicable.

    :case:
        The Integrated Planning Model (IPM) electricity demand case.

    :kwh_demand:
        The onroad kwh demand used in IPM.

    :kwh_generation_us:
        The EGU kwh generation used in IPM runs for the United States.

    :pollutant_id_metrictons:
        The EGU inventory of pollutant_id emissions where pollutant_id can be sox, pm25, nox, voc, co2, ch4, n2o, hg,
        and hcl. All inventories are in metric tons in the indicated year.

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class EGUdata:
    """
    Loads and provides access to EGU data and emission rates by calendar year.

    """
    def __init__(self):
        self._data = {}  # the input data along with pw linear interpolations of that input data
        self.cases = None
        self._cache = {}  # a storehouse of calculated rates for the given session
        self.years = None
        self.calendar_year_min = None
        self.calendar_year_max = None
        self.rate_names = None
        self.deets = {}  # all the calc details; this dictionary will not include the legacy fleet
        self.pollutant_ids = [
            'pm25',
            'nox',
            'sox',
            'voc',
            'co',
            'co2',
            'ch4',
            'n2o',
            'hg',
            'hcl',
        ]

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
        input_template_name = 'egu_data'
        input_template_version = 0.1
        input_template_columns = [
            'calendar_year',
            'case',
            'kwh_demand',
            'kwh_generation_us',
        ]
        suffixes = 'metrictons'
        for pollutant_id in self.pollutant_ids:
            input_template_columns.append(f'{pollutant_id}_{suffixes}')

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df_rates = self.calc_rates(df)

        self.rate_names = [
            rate_name for rate_name in df_rates.columns if 'year' not in rate_name and 'case' not in rate_name
        ]
        self.years = df_rates['calendar_year'].unique()
        self.calendar_year_min = int(min(df_rates['calendar_year']))
        self.calendar_year_max = int(max(df_rates['calendar_year']))
        self.cases = df_rates['case'].unique()

        rate_keys = zip(
            df_rates['calendar_year'],
            df_rates['case'],
        )
        df_rates.set_index(rate_keys, inplace=True)

        self._data = df_rates.to_dict('index')

        self.interpolate_input_data()

    def calc_rates(self, df):
        """

        Args:
            df (DataFrame): The egu input data.

        Returns:
            A DataFrame of egu emission rates based on the input data.

        """
        df_rates = df[['calendar_year', 'case', 'kwh_demand', 'kwh_generation_us']]
        for pollutant_id in self.pollutant_ids:
            rates = pd.Series(
                df[f'{pollutant_id}_metrictons'] * pow(10, 6) / df['kwh_generation_us'],
                name=f'{pollutant_id}_grams_per_kwh'
            )
            df_rates = pd.concat([df_rates, rates], axis=1)

        return df_rates

    def get_emission_rate(self, v, cyear, session_kwh_consumption, session_kwh_generation, rate_names):
        """

        Get emission rates by calendar year

        Args:
            v (dict): a dictionary of annual physical effects values
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

        if (v['session_policy'], cyear) in self._cache:
            return self._cache[v['session_policy'], cyear]

        kwh_generation_us_low = self._data[(calendar_year, 'low_demand')]['kwh_generation_us']
        kwh_generation_us_high = self._data[(calendar_year, 'high_demand')]['kwh_generation_us']
        kwh_demand_fleet_ipm = self._data[(calendar_year, 'low_demand')]['kwh_demand']

        # back out the low_demand case fleet demand provided to IPM to establish a base working base
        kwh_generation_us_base = kwh_generation_us_low - kwh_demand_fleet_ipm

        # add the kwh_session to the new kwh base value to determine the US generation for this session
        kwh_generation_us_session = session_kwh_generation + kwh_generation_us_base

        for idx, rate_name in enumerate(rate_names):
            self.deets.update({(v['session_policy'], cyear, rate_name): {}})

            self.deets[(v['session_policy'], cyear, rate_name)] = {
                    'session_policy': v['session_policy'],
                    'session_name': v['session_name'],
                    'calendar_year': cyear,
                    'kwh_generation_us_low': kwh_generation_us_low,
                    'kwh_generation_us_high': kwh_generation_us_high,
                    'kwh_demand_fleet_ipm': kwh_demand_fleet_ipm,
                    'kwh_generation_us_base': kwh_generation_us_base,
                    'kwh_generation_us_session': kwh_generation_us_session,
                    'fleet_kwh_consumption': session_kwh_consumption,
                    'fleet_kwh_generation': session_kwh_generation,
                    'rate_name': rate_name,
                }
            rate_low = self._data[(calendar_year, 'low_demand')][rate_name]
            rate_high = self._data[(calendar_year, 'high_demand')][rate_name]

            # interpolate the rate for kwh_demand
            if calendar_year <= self.calendar_year_min:
                rate = rate_low
            else:
                rate = ((kwh_generation_us_session - kwh_generation_us_low) * (rate_high - rate_low)
                        / (kwh_generation_us_high - kwh_generation_us_low)
                        + rate_low)

            rates.append(rate)
            if rate <= 0:
                rate = (rate_low + rate_high) / 2

            self.deets[v['session_policy'], cyear, rate_name].update({
                'rate_low': rate_low,
                'rate_high': rate_high,
                'rate': rate,
                'US_inventory_grams': rate * kwh_generation_us_session,
                'analysis_fleet_inventory_grams': rate * session_kwh_generation,
            })

        self._cache[v['session_policy'], cyear] = rates

        return rates

    def interpolate_input_data(self):
        """

        Returns:
             Nothing, but it builds the data dictionary of interpolated inputs based on the limited years of input data.

        """
        for case in self.cases:
            for idx, year in enumerate(self.years):
                if year < self.calendar_year_max:
                    year_1, year_2 = year, self.years[idx + 1]

                    for yr in range(year_1 + 1, year_2):
                        self._data.update({(yr, case): {
                            'calendar_year': yr,
                            'case': case,
                        }})

                        for rate_name in self.rate_names:
                            value_1 = self._data[(year_1, case)][rate_name]
                            value_2 = self._data[(year_2, case)][rate_name]

                            m = (value_2 - value_1) / (year_2 - year_1)

                            value_new = m * (yr - year_1) + value_1
                            self._data[(yr, case)][rate_name] = value_new
