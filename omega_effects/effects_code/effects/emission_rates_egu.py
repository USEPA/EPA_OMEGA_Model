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

        case,rate_name,independent_variable,initial_year,last_year,slope_rate,intercept_rate,ind_variable_data,rate_data,equation_rate_id,kwh_demand_metric,slope_kwh_demand_metric,intercept_kwh_demand_metric,kwh_data_demand_metric,equation_kwh_demand_metric,kwh_consumption_metric,slope_kwh_consumption_metric,intercept_kwh_consumption_metric,kwh_data_consumption_metric,equation_kwh_consumption_metric
        low_bound,pm25_grams_per_kwh,(calendar_year - 2020),2020,2050,-4.42E-04,1.62E-02,"[0, 8, 10, 15, 20, 25, 30]","[0.01494498147830424, 0.014937349424, 0.012776816502783726, 0.008389652283529411, 0.006341793721119133, 0.0046182596672268905, 0.0037604966545031057]",((-0.00044234 * (calendar_year - 2020)) + 0.01622),kWh_generation_us,82260700000,3.90E+12,"[4010000000000.0, 4500000000000.0, 4670000000000.0, 5100000000000.0, 5540000000000.0, 5950000000000.0, 6440000000000.0]",((82260700000.0 * (calendar_year - 2020)) + 3903690000000.0),kWh_consumption_low_bound,13975600000,27523300000,"[70919328891.0, 79544639445.0, 136559000000.0, 252000000000.0, 338000000000.0, 396000000000.0, 429000000000.0]",((13975600000.0 * (calendar_year - 2020)) + 27523300000.0)
        high_bev,nox_grams_per_kwh,(calendar_year - 2020),2020,2050,-0.0030975,0.09796,"[0, 8, 10, 15, 20, 25, 30]","[0.09102244389027432, 0.09, 0.07292110874200426, 0.040115163147792704, 0.026701570680628273, 0.01715210355987055, 0.013273542600896861]",((-0.0030975 * (calendar_year - 2020)) + 0.09796),kWh_generation_us,92384200000,3.86E+12,"[4010000000000.0, 4500000000000.0, 4690000000000.0, 5210000000000.0, 5730000000000.0, 6180000000000.0, 6690000000000.0]",((92384200000.0 * (calendar_year - 2020)) + 3861790000000.0),kWh_consumption_low_bound,13971900000,27643400000,"[70919328891.0, 79544639445.0, 137000000000.0, 252000000000.0, 338000000000.0, 396000000000.0, 429000000000.0]",((13971900000.0 * (calendar_year - 2020)) + 27643400000.0)

Data Column Name and Description

    :case:
        The Integrated Planning Model electricity demand case.

    :rate_name:
        The emission rate providing the pollutant and units.

    :independent_variable:
        The independent variable used in calculating the emission rate.

    :initial_year:
        The initial calendar year from which the rate regression curves were generated.

    :last_year:
        The last calendar year from which the rate regression curves were generated.

    :slope_rate:
        The slope of the linear fit to the emission rate input data.

    :intercept_rate:
        The intercept of the linear fit to the emission rate input data.

    :ind_variable_data:
        Input data for the independent variable used to generate the emission rate curve
        where data are years from the initial_year.

    :rate_data:
        The emission rate data used to generate the emission rate curve.

    :equation_rate_id:
        The linear fit emission rate equation used to calculate an emission rate at the given independent variable.

    :kwh_demand_metric:
        The kwh demand metric used in generating a corresponding energy rate regression
        (e.g., consumption or generation).

    :slope_kwh_demand_metric:
        The slope of the linear fit to the energy demand rate input data.

    :intercept_kwh_demand_metric:
        The intercept of the linear fit to the energy demand rate input data.

    :kwh_data_demand_metric:
        The energy demand rate data used to generate the energy rate curve.

    :equation_kwh_demand_metric:
        The linear fit energy rate equation used to calculate an energy demand rate at the given independent variable.

    :kwh_consumption_metric:
        The kwh consumption metric used in generating a corresponding energy rate regression
        (e.g., consumption or generation).

    :slope_kwh_consumption_metric:
        The slope of the linear fit to the energy consumption rate input data.

    :intercept_kwh_consumption_metric:
        The intercept of the linear fit to the energy consumption rate input data.

    :kwh_data_consumption_metric:
        The energy consumption rate data used to generate the energy rate curve.

    :equation_kwh_consumption_metric:
        The linear fit energy rate equation used to calculate an energy consumption rate at the
        given independent variable.

----

**CODE**

"""

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class EmissionRatesEGU:
    """
    Loads and provides access to power sector emissions factors  by calendar year.

    """
    def __init__(self):
        self._data = dict()  # private dict, emissions factors power sector by calendar year
        self._cases = None
        self._cache = dict()
        self.calendar_year_max = None
        self.kwh_demand_metric = None
        self.kwh_consumption_metric = None

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
            'case',
            'rate_name',
            'independent_variable',
            'last_year',
            'kwh_demand_metric',
            'kwh_consumption_metric',
            'equation_rate_id',
            'equation_kwh_demand_metric',
            'equation_kwh_consumption_metric',
        ]

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        rate_keys = zip(
            df['case'],
            df['rate_name']
        )
        df.set_index(rate_keys, inplace=True)

        self._cases = df['case'].unique()
        self.kwh_demand_metric = df['kwh_demand_metric'][0]
        self.kwh_consumption_metric = df['kwh_consumption_metric'][0]
        self.calendar_year_max = df['last_year'][0]

        self._data = df.to_dict('index')

        # for rate_key in self._data:
        #
        #     rate_eq = self._data[rate_key]['equation_rate_id']
        #     kwh_demand_eq = self._data[rate_key]['equation_kwh_demand_metric']
        #     kwh_consumption_eq = self._data[rate_key]['equation_kwh_consumption_metric']
        #
        #     self._data[rate_key].update({
        #         'equation_rate_id': compile(rate_eq, '<string>', 'eval'),
        #         'equation_kwh_demand_metric': compile(kwh_demand_eq, '<string>', 'eval'),
        #         'equation_kwh_consumption_metric': compile(kwh_consumption_eq, '<string>', 'eval'),
        #     })

    def get_emission_rate(self, calendar_year, kwh_session, rate_names):
        """

        Get emission rates by calendar year

        Args:
            calendar_year (int): calendar year for which to get emission rates
            kwh_session (numeric): the session kWh to use (e.g., kwh_consumption or kwh_generation; this is omega-only)
            rate_names (str, [strs]): name of emission rate(s) to get

        Returns:
            A list of emission rates for the given kwh_demand in the given calendar_year.

        """
        locals_dict = locals()
        return_rates = list()

        kwh_demand_low = kwh_demand_high = kwh_low_bound = 0

        if calendar_year > self.calendar_year_max:
            calendar_year = self.calendar_year_max

        if calendar_year in self._cache:
            return_rates = self._cache[calendar_year]

        else:
            kwh_demand_low \
                = eval(self._data['low_bound', rate_names[0]]['equation_kwh_demand_metric'], {}, locals_dict)

            kwh_demand_high \
                = eval(self._data['high_bev', rate_names[0]]['equation_kwh_demand_metric'], {}, locals_dict)

            kwh_low_bound \
                = eval(self._data['low_bound', rate_names[0]]['equation_kwh_consumption_metric'], {}, locals_dict)

            # back out the low-bound consumption provided to IPM to establish a base without the low bound omega demand
            kwh_base = kwh_demand_low - kwh_low_bound

            # add the kwh_session to the new kwh base value to determine the US demand for the session
            kwh_session += kwh_base

            for idx, rate_name in enumerate(rate_names):
                rate_low = eval(self._data['low_bound', rate_name]['equation_rate_id'], {}, locals_dict)
                rate_high = eval(self._data['high_bev', rate_name]['equation_rate_id'], {}, locals_dict)

                # interpolate the rate for kwh_demand
                rate = (rate_low - (kwh_demand_low - kwh_session) * (rate_low - rate_high) /
                       (kwh_demand_low - kwh_demand_high))

                if rate <= 0:
                    rate = self._cache[calendar_year - 1][idx]

                return_rates.append(rate)

            self._cache[calendar_year] = return_rates

        return return_rates
