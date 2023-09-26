"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents refinery emission rate curves.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,emission_rates_refinery,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,co_grams_per_gallon,co2_grams_per_gallon,n2o_grams_per_gallon,nox_grams_per_gallon,pm25_grams_per_gallon,sox_grams_per_gallon,voc_grams_per_gallon
        2030,0.221366923,776.3322717,0.006565074,0.333376711,0.079500558,0.099981211,0.23941677
        2031,0.225401153,790.8154639,0.006687551,0.339531504,0.080958362,0.101826973,0.24376566
        2032,0.229435383,805.2986561,0.006810029,0.345686296,0.082416166,0.103672736,0.248114551
        2033,0.233469613,819.7818483,0.006932506,0.351841089,0.083873971,0.105518498,0.252463441

Data Column Name and Description

    :calendar_year:
        The calendar year for which rates are sought.

    :co_grams_per_gallon:
        The CO emission rate in grams per gallon of fuel refined.

    :co2_grams_per_gallon:
        The CO2 emission rate in grams per gallon of fuel refined.

    :n2o_grams_per_gallon:
        The N2O emission rate in grams per gallon of fuel refined.

    :nox_grams_per_gallon:
        The NOx emission rate in grams per gallon of fuel refined.

    :pm25_grams_per_gallon:
        The PM2.5 emission rate in grams per gallon of fuel refined.

    :sox_grams_per_gallon:
        The SOx emission rate in grams per gallon of fuel refined.

    :voc_grams_per_gallon:
        The VOC emission rate in grams per gallon of fuel refined.

----

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class EmissionRatesRefinery:
    """
    Loads and provides access to power sector emissions factors  by calendar year.

    """
    def __init__(self):
        self._data = {}
        self.calendar_year_min = None
        self.calendar_year_max = None
        self.rate_names = []

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
        input_template_name = 'emission_rates_refinery'
        input_template_version = 0.2
        input_template_columns = {
            'calendar_year',
            'co_grams_per_gallon',
            'co2_grams_per_gallon',
            'n2o_grams_per_gallon',
            'nox_grams_per_gallon',
            'pm25_grams_per_gallon',
            'sox_grams_per_gallon',
            'voc_grams_per_gallon',
        }
        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self.rate_names = [rate_name for rate_name in df.columns if 'year' not in rate_name]
        self.calendar_year_min = int(min(df['calendar_year']))
        self.calendar_year_max = int(max(df['calendar_year']))

        df.set_index(df['calendar_year'], inplace=True)

        self._data = df.to_dict('index')

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
            rates.append(self._data[calendar_year][rate_name])

        return rates
