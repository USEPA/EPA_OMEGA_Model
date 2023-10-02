"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent refinery data used to generate emission rates for refinery inventory estimates within OMEGA.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,refinery_data,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,co_ustons,co2_ustons,n2o_ustons,n590_ustons,nh3_ustons,nox_ustons,pm10_ustons,pm25_ustons,sox_ustons,voc_ustons,co_emission_apportionment_gasoline,co2_emission_apportionment_gasoline,n2o_emission_apportionment_gasoline,n590_emission_apportionment_gasoline,nh3_emission_apportionment_gasoline,nox_emission_apportionment_gasoline,pm10_emission_apportionment_gasoline,pm25_emission_apportionment_gasoline,sox_emission_apportionment_gasoline,voc_emission_apportionment_gasoline,co_emission_apportionment_diesel,co2_emission_apportionment_diesel,n2o_emission_apportionment_diesel,n590_emission_apportionment_diesel,nh3_emission_apportionment_diesel,nox_emission_apportionment_diesel,pm10_emission_apportionment_diesel,pm25_emission_apportionment_diesel,sox_emission_apportionment_diesel,voc_emission_apportionment_diesel,retail_gasoline_gallons,diesel_gallons,e0_gallons,fuel_reduction_leading_to_reduced_domestic_refining,share_of_fuel_refined_domestically
        2030,50462.97861,179019969.9,1529.019319,3.785179636,2956.138021,75349.63788,20162.0694,17737.65461,22955.33617,57273.72581,0.602405743,0.591,0.582657883,0,0,0.609500939,0.620268794,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.062889415,0,0,0.05570409,0.054043799,0.053464368,0.058421274,0.058337953,1.06E+11,40994637600,95400000000,0.96,1
        2035,50497.76358,179497794.8,1533.100448,3.792387328,2959.758688,75483.7425,20186.34113,17759.06091,22996.09832,57297.53722,0.602405743,0.591,0.582657883,0,0,0.609500939,0.620268794,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.062889415,0,0,0.05570409,0.054043799,0.053464368,0.058421274,0.058337953,95739161297,38925071208,86165245167,0.96,1
        2040,50829.41372,180908447.2,1545.148906,3.818696712,2974.205209,76168.63053,20319.4776,17883.352,23133.89863,57416.13093,0.602405743,0.591,0.582657883,0,0,0.609500939,0.620268794,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.062889415,0,0,0.05570409,0.054043799,0.053464368,0.058421274,0.058337953,90309519467,38045783960,81278567520,0.96,1
        2045,51266.15504,183618187.9,1568.292949,3.864572756,2994.751015,76944.91407,20504.4112,18054.04705,23316.37403,57608.23559,0.602405743,0.591,0.582657883,0,0,0.609500939,0.620268794,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.062889415,0,0,0.05570409,0.054043799,0.053464368,0.058421274,0.058337953,88839748081,38098041450,79955773273,0.96,1
        2050,51793.53884,186521729.1,1593.092253,3.917621474,3015.069294,77829.83767,20718.07605,18253.15804,23501.20676,57829.42994,0.602405743,0.591,0.582657883,0,0,0.609500939,0.620268794,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.062889415,0,0,0.05570409,0.054043799,0.053464368,0.058421274,0.058337953,90647428047,38546346116,81582685242,0.96,1

Data Column Name and Description

    :calendar_year:
        The calendar year for which the data are applicable.

    :pollutant_id_ustons:
        The pollutant_id inventory in US (short) tons where pollutant_id can be co, co2, n2o, n590, nh3, nox, pm10,
        pm25, sox, voc. These inventories were generated for air quality modeling (AQM) and are inputs to OMEGA.

    :pollutant_id_emission_apportionment_gasoline:
        The portion of refinery emissions attributable to the pollutant_id when refining gasoline.

    :pollutant_id_emission_apportionment_diesel:
        The portion of refinery emissions attributable to the pollutant_id when refining diesel.

    :retail_gasoline_gallons:
        The retail gasoline gallons used in generating the AQM refinery inventory data.

    :diesel_gallons:
        The diesel gallons used in generating the AQM refinery inventory data.

    :e0_gallons:
        The petroleum portion of the retail gasoline gallons used in generating the AQM refinery inventory data.

    :fuel_reduction_leading_to_reduced_domestic_refining:
        The share of fuel savings that result in reduced domestic refining.

    :share_of_fuel_refined_domestically:
        The share of the AQM refinery inventory gallons considered to have been refined domestically within OMEGA.

----

**CODE**

"""
import pandas as pd
from itertools import product

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class RefineryData:
    """
    Loads and provides access to refinery data and emission rates by calendar year.

    """
    def __init__(self):
        self.data = {}
        self.years = None
        self.calendar_year_min = None
        self.calendar_year_max = None
        self.rate_names = []
        self.pollutant_ids = [
            'co',
            'co2',
            'n2o',
            'nox',
            'pm25',
            'sox',
            'voc',
        ]

    def init_from_file(self, batch_settings, session_settings, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            batch_settings: an instance of the BatchSettings class.
            session_settings: an instance of the SessionSettings class.
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_name = 'refinery_data'
        input_template_version = 0.1

        suffixes = [
            'ustons',
            'emission_apportionment_gasoline',
            'emission_apportionment_diesel',
        ]
        input_template_columns = [
            'calendar_year',
            'retail_gasoline_gallons',
            'diesel_gallons',
            'e0_gallons',
            'fuel_reduction_leading_to_reduced_domestic_refining',
            'share_of_fuel_refined_domestically',
        ]
        for pollutant_id, suffix in product(self.pollutant_ids, suffixes):
            input_template_columns.append(f'{pollutant_id}_{suffix}')

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df_rates = self.calc_rates(batch_settings, df)
        df_rates = pd.concat([df_rates, df['fuel_reduction_leading_to_reduced_domestic_refining']], axis=1)
        df_rates = pd.concat([df_rates, df['share_of_fuel_refined_domestically']], axis=1)

        self.rate_names = [rate_name for rate_name in df_rates.columns if 'year' not in rate_name]
        self.years = df_rates['calendar_year'].unique()
        self.calendar_year_min = int(min(df_rates['calendar_year']))
        self.calendar_year_max = int(max(df_rates['calendar_year']))

        df_rates.set_index(df_rates['calendar_year'], inplace=True)

        df_rates.insert(0, 'session_name', '')

        self.data = df_rates.to_dict('index')

        self.interpolate_input_data(session_settings)

    def calc_rates(self, batch_settings, df):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            df (DataFrame): the refinery input data.

        Returns:
            A DataFrame of refinery emission rates based on the input data.

        """
        grams_per_uston = batch_settings.general_inputs_for_effects.get_value('grams_per_us_ton')
        df.insert(0, 'petroleum_gallons', df['e0_gallons'] + df['diesel_gallons'])
        df_rates = pd.DataFrame(df['calendar_year'])
        for pollutant_id in self.pollutant_ids:
            apportionment = (df[f'{pollutant_id}_emission_apportionment_gasoline'] +
                             df[f'{pollutant_id}_emission_apportionment_diesel'])
            rates = pd.Series(
                df[f'{pollutant_id}_ustons'] * grams_per_uston * apportionment / df['petroleum_gallons'],
                name=f'{pollutant_id}_grams_per_gallon'
            )
            df_rates = pd.concat([df_rates, rates], axis=1)

        return df_rates

    def get_emission_rate(self, calendar_year, rate_names):
        """

        Get emission rates by calendar year

        Args:
            calendar_year (int): calendar year for which to get emission rates
            rate_names (str, [strs]): name of emission rate(s) to get

        Returns:
            A list of emission rates for the given kwh_demand in the given calendar_year.

        """
        if calendar_year < self.calendar_year_min:
            calendar_year = self.calendar_year_min
        if calendar_year > self.calendar_year_max:
            calendar_year = self.calendar_year_max

        rates = []
        for rate_name in rate_names:
            rates.append(self.data[calendar_year][rate_name])

        return rates

    def interpolate_input_data(self, session_settings):
        """

        Parameters:
            session_settings: an instance of the SessionSettings class.

        Returns:
             Nothing, but it builds the data dictionary of interpolated inputs based on the limited years of input data.

        """
        for idx, year in enumerate(self.years):
            self.data[year]['session_name'] = session_settings.session_name

            if year < self.calendar_year_max:
                year_1, year_2 = year, self.years[idx + 1]

                for yr in range(year_1 + 1, year_2):
                    self.data.update({yr: {
                        'session_name': session_settings.session_name,
                        'calendar_year': yr}})

                    for rate_name in self.rate_names:
                        value_1 = self.data[year_1][rate_name]
                        value_2 = self.data[year_2][rate_name]

                        m = (value_2 - value_1) / (year_2 - year_1)

                        value_new = m * (yr - year_1) + value_1
                        self.data[yr][rate_name] = value_new
