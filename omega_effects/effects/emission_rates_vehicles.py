"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents vehicle emission rates by model year, age, reg-class and fuel type as estimated by
EPA's MOVES model.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,effects.emission_rates_vehicles,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,age,reg_class_id,sourcetype_name,in_use_fuel_id,pm25_exhaust_grams_per_mile,nmog_exhaust_grams_per_mile,acetaldehyde_exhaust_grams_per_mile,acrolein_exhaust_grams_per_mile,benzene_exhaust_grams_per_mile,13_butadiene_exhaust_grams_per_mile,ethylbenzene_exhaust_grams_per_mile,formaldehyde_exhaust_grams_per_mile,naphthalene_exhaust_grams_per_mile,15pah_exhaust_grams_per_mile,thc_exhaust_grams_per_mile,co_exhaust_grams_per_mile,nox_exhaust_grams_per_mile,ch4_exhaust_grams_per_mile,n2o_exhaust_grams_per_mile,nmhc_exhaust_grams_per_mile,pm25_brakewear_grams_per_mile,pm25_tirewear_grams_per_mile,nmog_evap_permeation_grams_per_gallon,nmog_evap_fuel_vapor_venting_grams_per_gallon,nmog_evap_fuel_leaks_grams_per_gallon,nmog_refueling_displacement_grams_per_gallon,nmog_refueling_spillage_grams_per_gallon,benzene_evap_permeation_grams_per_gallon,benzene_evap_fuel_vapor_venting_grams_per_gallon,benzene_evap_fuel_leaks_grams_per_gallon,benzene_refueling_displacement_grams_per_gallon,benzene_refueling_spillage_grams_per_gallon,ethylbenzene_evap_permeation_grams_per_gallon,ethylbenzene_evap_fuel_vapor_venting_grams_per_gallon,ethylbenzene_evap_fuel_leaks_grams_per_gallon,ethylbenzene_refueling_displacement_grams_per_gallon,ethylbenzene_refueling_spillage_grams_per_gallon,naphthalene_refueling_spillage_grams_per_gallon,sox_exhaust_grams_per_gallon
        1995,22,car,passenger car,pump gasoline,0.026012552,0.760144752,0.009408835,0.00046439,0.025028029,0.003978624,0.014277742,0.009888105,0.001530756,3.27E-05,0.858350773,17.90824361,2.140360297,0.125313562,0.02561411,0.733036905,0.002771515,0.001283189,7.70485875,19.21041082,11.21596483,4.61563711,0.331955427,0.047341593,0.067338101,0.037754896,0.015598022,0.001133856,0.007728421,0.330846081,0.193164016,0.079491647,0.005717013,,0.12715278
        1995,23,car,passenger car,pump gasoline,0.026033127,0.759549974,0.009380668,0.000464027,0.025060109,0.003972801,0.01426657,0.009863367,0.001529562,3.28E-05,0.857679295,17.91679716,2.139972443,0.125215512,0.025672278,0.73246352,0.002771514,0.001283188,7.898657131,19.56287328,11.42982548,4.617193593,0.331955378,0.048762991,0.068972206,0.03869661,0.015684556,0.00113956,0.007922814,0.336916293,0.196847155,0.079518442,0.005717012,,0.117743255
        1995,24,car,passenger car,pump gasoline,0.026053702,0.758955197,0.009352502,0.000463663,0.02509219,0.003966978,0.014255397,0.00983863,0.001528368,3.28E-05,0.857007818,17.92535071,2.139584589,0.125117462,0.025730446,0.731890134,0.002771513,0.001283188,8.092455512,19.91533574,11.64368614,4.618750075,0.33195533,0.050184389,0.070606311,0.039638324,0.015771089,0.001145263,0.008117207,0.342986504,0.200530294,0.079545237,0.005717011,,0.108333729

Data Column Name and Description
    :start_year:
        The model year to which the rate applies; model years not shown will apply the start_year rate
        less than or equal to the model year.

    :age:
        The vehicle age within its model year.

    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :sourcetype_name:
        The MOVES sourcetype name (e.g., passenger car, passenger truck, light-commercial truck, etc.).

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :rate_name:
        The emission rate providing the pollutant, the source (e.g., exhaust, evap, refueling) and units (e.g.,
        'grams_per_mile' or 'grams_per_gallon'

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class EmissionRatesVehicles:
    """
    Loads and provides access to vehicle emission factors by model year, age, legacy reg class ID and in-use fuel ID.

    """
    def __init__(self):
        self.data = {}
        self.startyear_min = 0
        self.start_years = None
        self.deets = None
        self.max_ages_dict = {}
        self.gasoline_rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile',
            'pm25_exhaust_grams_per_mile',
            'nmog_exhaust_grams_per_mile',
            'nmog_evap_permeation_grams_per_mile',
            'nmog_evap_fuel_vapor_venting_grams_per_mile',
            'nmog_evap_fuel_leaks_grams_per_mile',
            'nmog_refueling_displacement_grams_per_gallon',
            'nmog_refueling_spillage_grams_per_gallon',
            'co_exhaust_grams_per_mile',
            'nox_exhaust_grams_per_mile',
            'sox_exhaust_grams_per_gallon',
            'ch4_exhaust_grams_per_mile',
            'n2o_exhaust_grams_per_mile',
            'acetaldehyde_exhaust_grams_per_mile',
            'acrolein_exhaust_grams_per_mile',
            'benzene_exhaust_grams_per_mile',
            'benzene_evap_permeation_grams_per_mile',
            'benzene_evap_fuel_vapor_venting_grams_per_mile',
            'benzene_evap_fuel_leaks_grams_per_mile',
            'benzene_refueling_displacement_grams_per_gallon',
            'benzene_refueling_spillage_grams_per_gallon',
            'ethylbenzene_exhaust_grams_per_mile',
            'ethylbenzene_evap_fuel_vapor_venting_grams_per_mile',
            'ethylbenzene_evap_fuel_leaks_grams_per_mile',
            'ethylbenzene_evap_permeation_grams_per_mile',
            'ethylbenzene_refueling_displacement_grams_per_gallon',
            'ethylbenzene_refueling_spillage_grams_per_gallon',
            'formaldehyde_exhaust_grams_per_mile',
            'naphthalene_exhaust_grams_per_mile',
            '13_butadiene_exhaust_grams_per_mile',
            '15pah_exhaust_grams_per_mile',
        ]
        self.diesel_rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile',
            'pm25_exhaust_grams_per_mile',
            'nmog_exhaust_grams_per_mile',
            'nmog_refueling_spillage_grams_per_gallon',
            'co_exhaust_grams_per_mile',
            'nox_exhaust_grams_per_mile',
            'sox_exhaust_grams_per_gallon',
            'ch4_exhaust_grams_per_mile',
            'n2o_exhaust_grams_per_mile',
            'acetaldehyde_exhaust_grams_per_mile',
            'acrolein_exhaust_grams_per_mile',
            'benzene_exhaust_grams_per_mile',
            'benzene_refueling_spillage_grams_per_gallon',
            'ethylbenzene_exhaust_grams_per_mile',
            'ethylbenzene_refueling_spillage_grams_per_gallon',
            'formaldehyde_exhaust_grams_per_mile',
            'naphthalene_exhaust_grams_per_mile',
            'naphthalene_refueling_spillage_grams_per_gallon',
            '13_butadiene_exhaust_grams_per_mile',
            '15pah_exhaust_grams_per_mile',
        ]
        self.bev_rate_names = [
            'pm25_brakewear_grams_per_mile',
            'pm25_tirewear_grams_per_mile'
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
        input_template_name = 'effects.emission_rates_vehicles'
        input_template_version = 0.1
        input_template_columns = {
            'start_year',
            'age',
            'reg_class_id',
            'sourcetype_name',
            'in_use_fuel_id',
        }
        df = read_input_file(filepath, effects_log)
        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        keys = zip(
            df['start_year'],
            df['sourcetype_name'],
            df['reg_class_id'],
            df['in_use_fuel_id'],
            df['age'],
        )
        df.set_index(keys, inplace=True)

        for idx, row in df.iterrows():
            key = (
                row['start_year'], row['sourcetype_name'], row['reg_class_id'], row['in_use_fuel_id'], row['age']
            )
            if 'gasoline' in row['in_use_fuel_id']:
                self.data[key] = row[self.gasoline_rate_names].values
            elif 'diesel' in row['in_use_fuel_id']:
                self.data[key] = row[self.diesel_rate_names].values
            else:
                self.data[key] = row[self.bev_rate_names].values

        self.startyear_min = min(df['start_year'])
        self.start_years = df['start_year'].unique()

        for start_year in self.start_years:
            self.max_ages_dict[start_year] = max(df.loc[df['start_year'] == start_year, 'age'])

    def get_emission_rate(self, session_settings, model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age):
        """

        Args:
            session_settings: an instance of the SessionSettings class
            model_year (int): vehicle model year for which to get emission factors
            sourcetype_name (str): the MOVES sourcetype name (e.g., 'passenger car', 'light commercial truck')
            reg_class_id (str): the regulatory class, e.g., 'car' or 'truck'
            in_use_fuel_id (str): the liquid fuel ID, e.g., 'pump gasoline'
            age (int): vehicle age in years

        Returns:
            A list of emission rates for the given type of vehicle of the given model_year and age.

        """
        if model_year < self.startyear_min:
            start_year = self.startyear_min
        else:
            start_year = max([yr for yr in self.start_years if yr <= model_year])

        max_age_in_data_for_model_year = self.max_ages_dict[start_year]
        data_age = min(30, age, max_age_in_data_for_model_year)

        rates = self.data[(start_year, sourcetype_name, reg_class_id, in_use_fuel_id, data_age)]

        return rates
