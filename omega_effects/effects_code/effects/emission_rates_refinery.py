"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents refinery emission rate curves.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,emission_rates_refinery,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        rate_name,independent_variable,last_year,slope_rate,intercept_rate,equation_rate_id
        pm25_grams_per_gallon,(calendar_year - 2016),2055,-2.58E-04,1.47E-01,((-0.000257743900872186 * (calendar_year - 2016)) + 0.147171057586721)
        nox_grams_per_gallon,(calendar_year - 2016),2055,-0.002233801,0.57763691,((-0.00223380056415021 * (calendar_year - 2016)) + 0.577636910469321)
        sox_grams_per_gallon,(calendar_year - 2016),2055,-0.00030085,0.221705126,((-0.000300850396789525 * (calendar_year - 2016)) + 0.221705126043959)
        voc_grams_per_gallon,(calendar_year - 2016),2055,-2.19E-03,5.00E-01,((-0.00219248448866068 * (calendar_year - 2016)) + 0.500358765360277)

Data Column Name and Description
    :rate_name:
        The emission rate providing the pollutant and units.

    :independent_variable:
        The independent variable used in calculating the emission rate.

    :last_year:
        The last calendar year from which the rate regression curves were generated.

    :slope_rate:
        The slope of the linear fit to the emission rate input data.

    :intercept_rate:
        The intercept of the linear fit to the emission rate input data.

    :equation_rate_id:
        The linear fit emission rate equation used to calculate an emission rate at the given independent variable.

----

**CODE**

"""

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class EmissionRatesRefinery:
    """
    Loads and provides access to power sector emissions factors  by calendar year.

    """
    def __init__(self):
        self._data = dict()  # private dict
        self._cache = dict()
        self.calendar_year_max = None

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
        input_template_version = 0.1
        input_template_columns = {
            'rate_name',
            'independent_variable',
            'last_year',
            'equation_rate_id',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        # rate_keys = zip(
        #     df['rate_name']
        # )
        # df.set_index(rate_keys, inplace=True)
        df.set_index(df['rate_name'], inplace=True)

        self.calendar_year_max = df['last_year'][0]

        self._data = df.to_dict('index')

        # for rate_key in self._data:
        #
        #     rate_eq = self._data[rate_key]['equation_rate_id']
        #
        #     self._data[rate_key].update({
        #         'equation_rate_id': compile(rate_eq, '<string>', 'eval'),
        #     })

    def get_emission_rate(self, calendar_year, rate_names):
        """

        Get emission rates by calendar year

        Args:
            calendar_year (int): calendar year for which to get emission rates
            rate_names (str, [strs]): name of emission rate(s) to get

        Returns:
            A list of emission rates for the given kwh_demand in the given calendar_year.

        """
        locals_dict = locals()
        return_rates = list()

        if calendar_year > self.calendar_year_max:
            calendar_year = self.calendar_year_max

        if calendar_year in self._cache:
            return_rates = self._cache[calendar_year]

        else:
            for idx, rate_name in enumerate(rate_names):
                rate = eval(self._data[rate_name]['equation_rate_id'], {}, locals_dict)

                return_rates.append(rate)

            self._cache[calendar_year] = return_rates

        return return_rates
