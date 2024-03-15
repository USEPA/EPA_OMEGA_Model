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

        calendar_year,fuel_reduction_leading_to_reduced_domestic_refining,onroad_fuel_refinery_co_ustons,onroad_fuel_refinery_co2_ustons,onroad_fuel_refinery_ch4_ustons,onroad_fuel_refinery_n2o_ustons,onroad_fuel_refinery_nox_ustons,onroad_fuel_refinery_pm25_ustons,onroad_fuel_refinery_sox_ustons,onroad_fuel_refinery_voc_ustons,co_emission_apportionment_gasoline,co2_emission_apportionment_gasoline,ch4_emission_apportionment_gasoline,n2o_emission_apportionment_gasoline,nox_emission_apportionment_gasoline,pm25_emission_apportionment_gasoline,sox_emission_apportionment_gasoline,voc_emission_apportionment_gasoline,co_emission_apportionment_diesel,co2_emission_apportionment_diesel,ch4_emission_apportionment_diesel,n2o_emission_apportionment_diesel,nox_emission_apportionment_diesel,pm25_emission_apportionment_diesel,sox_emission_apportionment_diesel,voc_emission_apportionment_diesel,retail_gasoline_million_barrels_per_day,diesel_million_barrels_per_day,other_million_barrels_per_day,net_exports_million_barrels_per_day,gasoline_exports_million_barrels_per_day,diesel_exports_million_barrels_per_day,product_exports_million_barrels_per_day,export_scaler,context_scaler_car_gasoline,context_scaler_truck_gasoline,context_scaler_mediumduty_gasoline,context_scaler_car_diesel,context_scaler_truck_diesel,context_scaler_mediumduty_diesel
        2030,0.5,50462.97861,179019969.9,9608.310168,1529.019319,75349.63788,17737.65461,22955.33617,57273.72581,0.602405743,0.591,0.639935949,0.582657883,0.609500939,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.052711594,0.062889415,0.05570409,0.053464368,0.058421274,0.058337953,8.115856,3.312032,8.154782,6.082668,0.867,1.011,3.087,1.525625282,0.316962715,0.617086695,0.06595059,0.017490849,0.111502501,0.87100665
        2035,0.5,50497.76358,179497794.8,9583.178366,1533.100448,75483.7425,17759.06091,22996.09832,57297.53722,0.602405743,0.591,0.639935949,0.582657883,0.609500939,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.052711594,0.062889415,0.05570409,0.053464368,0.058421274,0.058337953,7.609757,3.221002,8.465063,6.562512,0.867,1.011,3.087,1.645977427,0.249231644,0.675120958,0.075647398,0.006043383,0.137434554,0.856522062
        2040,0.5,50829.41372,180908447.2,9620.738704,1545.148906,76168.63053,17883.352,23133.89863,57416.13093,0.602405743,0.591,0.639935949,0.582657883,0.609500939,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.052711594,0.062889415,0.05570409,0.053464368,0.058421274,0.058337953,7.299925,3.191927,8.794727,6.797757,0.867,1.011,3.087,1.704980436,0.208930401,0.708259977,0.082809622,0.001546558,0.152468031,0.845985411
        2045,0.5,51266.15504,183618187.9,9662.433075,1568.292949,76944.91407,18054.04705,23316.37403,57608.23559,0.602405743,0.591,0.639935949,0.582657883,0.609500939,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.052711594,0.062889415,0.05570409,0.053464368,0.058421274,0.058337953,7.234634,3.196052,9.160675,6.858117,0.867,1.011,3.087,1.720119639,0.195203495,0.71804962,0.086746885,0.000148156,0.154498952,0.845352891
        2050,0.5,51793.53884,186521729.1,9743.280669,1593.092253,77829.83767,18253.15804,23501.20676,57829.42994,0.602405743,0.591,0.639935949,0.582657883,0.609500939,0.620404538,0.596420189,0.570155224,0.057134474,0.061,0.052711594,0.062889415,0.05570409,0.053464368,0.058421274,0.058337953,7.431168,3.204183,9.527437,6.431421,0.867,1.011,3.087,1.613097818,0.189893857,0.719549292,0.090556851,1.08646E-05,0.150382554,0.849606582

Data Column Name and Description

    :calendar_year:
        The calendar year for which the data are applicable.

    :fuel_reduction_leading_to_reduced_domestic_refining:
        The share of fuel savings that result in reduced domestic refining.

    :onroad_fuel_refinery_pollutant_id_ustons:
        The pollutant_id inventory in US (short) tons where pollutant_id can be co, co2, n2o, nox, pm25, sox, voc.
        These inventories represent emissions from refineries that refine onroad fuel.

    :pollutant_id_emission_apportionment_gasoline:
        The portion of refinery emissions attributable to the pollutant_id when refining gasoline.

    :pollutant_id_emission_apportionment_diesel:
        The portion of refinery emissions attributable to the pollutant_id when refining diesel.

    :retail_gasoline_million_barrels_per_day:
        The retail gasoline gallons used in generating refinery emission rates.

    :diesel_million_barrels_per_day:
        The diesel gallons used in generating refinery emission rates.

    :other_million_barrels_per_day:
        The other petroleum products used in generating refinery emission rates.

    :net_exports_million_barrels_per_day:
        The net exports of petroleum products outside the United States.

    :gasoline_exports_million_barrels_per_day:
        The US exports of gasoline in 2022 used to estimate the share of future net exports that are gasoline.

    :diesel_exports_million_barrels_per_day:
        The US exports of 15 ppm low sulfur diesel fuel in 2022 used to estimate the share of future net exports that
        are 15 ppm low sulfur diesel fuel.

    :product_exports_million_barrels_per_day:
        The US exports of other petroleum products in 2022 used to estimate the share of future net exports that are
        other petroleum products.

    :export_scaler:
        A scaler used to project future growth in US petroleum product exports.

    :context_scaler_regclass_id_fuel:
        A scaler used to estimate the future share of the indicated fuel that is consumed by vehicles of the indicated
        regclass_id where regclass_id can be car, truck, mediumduty and fuel can be gasoline or diesel.

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
        self.cache = {}
        self.years = None
        self.calendar_year_min = None
        self.calendar_year_max = None
        self.rate_names = []
        self.rate_basis = 'liquid_fuel_gallons'  # 'liquid_fuel_gallons' or 'petroleum_gallons' should be entered
        self.pollutant_ids = [
            'co',
            'co2',
            'ch4',
            'n2o',
            'nox',
            'pm25',
            'sox',
            'voc',
        ]

    def init_from_file(self, batch_settings, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            batch_settings: an instance of the BatchSettings class.
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_name = 'refinery_data'
        input_template_version = 0.11

        prefixes = [
            'onroad_fuel_refinery',
        ]
        suffixes = [
            'emission_apportionment_gasoline',
            'emission_apportionment_diesel',
        ]
        input_template_columns = [
            'calendar_year',
            'retail_gasoline_million_barrels_per_day',
            'diesel_million_barrels_per_day',
            'other_million_barrels_per_day',
            'net_exports_million_barrels_per_day',
            'gasoline_exports_million_barrels_per_day',
            'diesel_exports_million_barrels_per_day',
            'product_exports_million_barrels_per_day',
            'export_scaler',
            'context_scaler_lmdv_car_gasoline',
            'context_scaler_lmdv_truck_gasoline',
            'context_scaler_lmdv_mediumduty_gasoline',
            'context_scaler_lmdv_car_diesel',
            'context_scaler_lmdv_truck_diesel',
            'context_scaler_lmdv_mediumduty_diesel',
            'context_scaler_lmdv_gasoline',
            'context_scaler_lmdv_diesel',
            'fuel_reduction_leading_to_reduced_domestic_refining',
        ]
        for prefix, pollutant_id in product(prefixes, self.pollutant_ids):
            input_template_columns.append(f'{prefix}_{pollutant_id}_ustons')

        for pollutant_id, suffix in product(self.pollutant_ids, suffixes):
            input_template_columns.append(f'{pollutant_id}_{suffix}')

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df_rates = self.calc_rates(batch_settings, df)
        df_rates = pd.concat([
            df_rates,
            df['fuel_reduction_leading_to_reduced_domestic_refining'],
            df['context_scaler_lmdv_car_gasoline'],
            df['context_scaler_lmdv_truck_gasoline'],
            df['context_scaler_lmdv_mediumduty_gasoline'],
            df['context_scaler_lmdv_car_diesel'],
            df['context_scaler_lmdv_truck_diesel'],
            df['context_scaler_lmdv_mediumduty_diesel'],
            df['context_scaler_lmdv_gasoline'],
            df['context_scaler_lmdv_diesel'],
        ], axis=1)

        self.rate_names = [rate_name for rate_name in df_rates.columns if 'year' not in rate_name]
        self.years = df_rates['calendar_year'].unique()
        self.calendar_year_min = int(min(df_rates['calendar_year']))
        self.calendar_year_max = int(max(df_rates['calendar_year']))

        df_rates.set_index(df_rates['calendar_year'], inplace=True)

        self.data = df_rates.to_dict('index')

        self.interpolate_input_data()

    def calc_rates(self, batch_settings, df):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            df (DataFrame): the refinery input data.

        Returns:
            A DataFrame of refinery emission rates based on the input data.

        """
        grams_per_uston = batch_settings.general_inputs_for_effects.get_value('grams_per_us_ton')
        df_rates = pd.DataFrame(df['calendar_year'])

        net_exports_gasoline = pd.Series(
            df['gasoline_exports_million_barrels_per_day'] * df['export_scaler'],
            name='net_exports_gasoline_million_barrels_per_day'
        )
        net_exports_diesel = pd.Series(
            df['diesel_exports_million_barrels_per_day'] * df['export_scaler'],
            name='net_exports_diesel_million_barrels_per_day'
        )
        net_exports_other = pd.Series(
            df['net_exports_million_barrels_per_day'] - net_exports_gasoline - net_exports_diesel,
            name='net_exports_other_million_barrels_per_day'
        )
        domestic_refined_gasoline = pd.Series(
            df['retail_gasoline_million_barrels_per_day'] + net_exports_gasoline,
            name='domestic_refined_gasoline_million_barrels_per_day'
        )
        domestic_refined_diesel = pd.Series(
            df['diesel_million_barrels_per_day'] + net_exports_diesel,
            name='domestic_refined_diesel_million_barrels_per_day'
        )
        domestic_refined_other = pd.Series(
            df['other_million_barrels_per_day'] + net_exports_other,
            name='domestic_refined_other_million_barrels_per_day'
        )
        df_rates = pd.concat([
            df_rates, domestic_refined_gasoline, domestic_refined_diesel, domestic_refined_other
        ], axis=1
        )
        for fuel in ['gasoline', 'diesel']:
            for pollutant_id in self.pollutant_ids:

                apportionment = df[f'{pollutant_id}_emission_apportionment_{fuel}']
                rates = pd.Series(
                    df[f'onroad_fuel_refinery_{pollutant_id}_ustons'] * apportionment * pow(10, 9) /
                    (df_rates[f'domestic_refined_{fuel}_million_barrels_per_day'] * pow(10, 6) * 42 * 365),
                    name=f'{fuel}_{pollutant_id}_ustons_per_billion_gallons'
                )
                df_rates = pd.concat([df_rates, rates], axis=1)

                rates = pd.Series(
                    df_rates[f'{fuel}_{pollutant_id}_ustons_per_billion_gallons'] * grams_per_uston / pow(10, 9),
                    name=f'{fuel}_{pollutant_id}_grams_per_gallon'
                )
                df_rates = pd.concat([df_rates, rates], axis=1)

        return df_rates

    def get_data(self, calendar_year, reg_class_id, fuel, *args):
        """

        Get emission rates by calendar year

        Args:
            calendar_year (int): calendar year for which to get emission rates
            reg_class_id (str): 'car', 'truck', 'mediumduty'
            fuel (str): the fuel of interest, e.g., 'gasoline' or 'diesel'
            args (str, [strs]): attribute name of data to get

        Returns:
            A list of refinery data for the given calendar_year.

        """
        if calendar_year < self.calendar_year_min:
            calendar_year = self.calendar_year_min
        if calendar_year > self.calendar_year_max:
            calendar_year = self.calendar_year_max

        return_data = []
        if (calendar_year, reg_class_id, fuel) in self.cache:
            return self.cache[calendar_year, reg_class_id, fuel]

        for arg in args:
            return_data.append(self.data[calendar_year][arg])

        self.cache[calendar_year, reg_class_id, fuel] = return_data

        return return_data

    def interpolate_input_data(self):
        """

        Returns:
             Nothing, but it builds the data dictionary of interpolated inputs based on the limited years of input data.

        """
        for idx, year in enumerate(self.years):

            if year < self.calendar_year_max:
                year_1, year_2 = year, self.years[idx + 1]

                for yr in range(year_1 + 1, year_2):
                    self.data.update({yr: {'calendar_year': yr}})

                    for rate_name in self.rate_names:
                        value_1 = self.data[year_1][rate_name]
                        value_2 = self.data[year_2][rate_name]

                        m = (value_2 - value_1) / (year_2 - year_1)

                        value_new = m * (yr - year_1) + value_1
                        self.data[yr][rate_name] = value_new
