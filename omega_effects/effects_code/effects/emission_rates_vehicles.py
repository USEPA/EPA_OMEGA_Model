"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents tailpipe emission rates by model year, age, reg-class and fuel type as estimated by
EPA's MOVES model.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,emission_rates_vehicles,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,sourcetype_name,reg_class_id,market_class_id,in_use_fuel_id,rate_name,independent_variable,slope,intercept,ind_variable_data,rate_data,equation
        1995,passenger car,car,non_hauling.ICE,pump gasoline,pm25_exhaust_grams_per_mile,age,0.000020575,0.02556,"[22, 30]","[0.02601255162083171, 0.026177151337127946]",((2.0575e-05 * age) + 0.02556)
        1995,passenger car,car,non_hauling.ICE,pump gasoline,nmog_exhaust_grams_per_mile,age,-0.00059478,0.77323,"[22, 30]","[0.7601447516760625, 0.7553865333609487]",((-0.00059478 * age) + 0.77323)

Data Column Name and Description
    :start_year:
        The model year to which the rate applies; model years not shown will apply the start_year rate
        less than or equal to the model year.

    :sourcetype_name:
        The MOVES sourcetype name (e.g., passenger car, passenger truck, light-commercial truck, etc.).

    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :market_class_id:
        The OMEGA market class (e.g., non-hauling.ICE, hauling.BEV, etc.).

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :rate_name:
        The emission rate providing the pollutant and units.

    :independent_variable:
        The independent variable used in calculating the emission rate (e.g., age).

    :slope:
        The slope of the linear fit to the emission rate input data.

    :intercept:
        The intercept of the linear fit to the emission rate input data.

    :ind_variable_data:
        Input data for the independent variable used to generate the emission rate curve where data represent the age
        associated with the corresponding input data.

    :rate_data:
        The emission rate data used to generate the emission rate curve.

    :equation:
        The linear fit emission rate equation used to calculate an emission rate at the given independent variable.

----

**CODE**

"""

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names

_cache = dict()


class EmissionRatesVehicles:
    """
    Loads and provides access to vehicle emission factors by model year, age, legacy reg class ID and in-use fuel ID.

    """
    def __init__(self):
        self._data = dict()  # private dict, emission factors vehicles by model year, age, legacy reg class ID and in-use fuel ID
        self._cache = dict()
        self.startyear_min = 0

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
        input_template_name = 'emission_rates_vehicles'
        input_template_version = 0.2
        input_template_columns = {
            'start_year',
            'sourcetype_name',
            'reg_class_id',
            'market_class_id',
            'in_use_fuel_id',
            'rate_name',
            'equation',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        rate_keys = zip(
            df['start_year'],
            df['sourcetype_name'],
            df['reg_class_id'],
            df['in_use_fuel_id'],
            df['rate_name']
        )
        df.set_index(rate_keys, inplace=True)

        self.startyear_min = min(df['start_year'])

        self._data = df.to_dict('index')

        for rate_key in rate_keys:
            rate_eq = self._data[rate_key]['equation']
            self._data[rate_key].update({'equation': compile(rate_eq, '<string>', 'eval')})

    def get_emission_rate(self, model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age, *rate_names):
        """

        Args:
            model_year (int): vehicle model year for which to get emission factors
            sourcetype_name (str): the MOVES sourcetype name (e.g., 'passenger car', 'light commercial truck')
            reg_class_id (str): the regulatory class, e.g., 'car' or 'truck'
            in_use_fuel_id (str): the liquid fuel ID, e.g., 'pump gasoline'
            age (int): vehicle age in years
            rate_names: name of emission rate(s) to get

        Returns:
            A list of emission rates for the given type of vehicle of the given model_year and age.

        """
        locals_dict = locals()
        rate = 0
        return_rates = list()

        if model_year < self.startyear_min:
            model_year = self.startyear_min

        for rate_name in rate_names:

            cache_key = (model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age, rate_name)
            if cache_key in self._cache:
                rate = self._cache[cache_key]
            else:
                rate_keys = [
                    k for k in self._data
                    if k[0] <= model_year
                       and k[1] == sourcetype_name
                       and k[2] == reg_class_id
                       and k[3] == in_use_fuel_id
                       and k[4] == rate_name
                ]
                if not rate_keys:
                    rate_keys = [
                        k for k in self._data
                        if k[1] == sourcetype_name
                           and k[2] == reg_class_id
                           and k[3] == in_use_fuel_id
                           and k[4] == rate_name
                    ]
                    start_year = min([k[0] for k in rate_keys])
                else:
                    max_start_year = max([k[0] for k in rate_keys])
                    start_year = min(model_year, max_start_year)

                rate_key = start_year, sourcetype_name, reg_class_id, in_use_fuel_id, rate_name

                rate = eval(self._data[rate_key]['equation'], {}, locals_dict)

                if rate < 0:
                    temp_key = (model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age - 1, rate_name)
                    rate = self._cache[temp_key]

                self._cache[cache_key] = rate

            return_rates.append(rate)

        return return_rates
