"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents tailpipe emission rates by model year, age, reg-class and fuel type as estimated by EPA's MOVES model.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,emission_rates_vehicles,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,sourcetype_name,reg_class_id,market_class_id,in_use_fuel_id,rate_name,independent_variable,equation
        2017,passenger car,car,non_hauling.ICE,pump gasoline,pm25_exhaust_grams_per_mile,age,((0.00020321 * age) + 0.0017372)
        2017,passenger car,car,non_hauling.ICE,pump gasoline,nmog_exhaust_grams_per_mile,age,((0.00039006 * age) + 0.05267)


Data Column Name and Description
    :start_year:
        The model year to which the rate applies; model years not shown will apply the start_year rate less than or equal
        to the model year.

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

    :equation:
        The emission rate equation used to calculate an emission rate at the given age (or other independent variable).

----

**CODE**

"""

from omega_model import *

_cache = dict()


class EmissionRatesVehicles(OMEGABase):
    """
    Loads and provides access to vehicle emission factors by model year, age, legacy reg class ID and in-use fuel ID.

    """
    _data = dict()  # private dict, emission factors vehicles by model year, age, legacy reg class ID and in-use fuel ID
    startyear_min = 0

    @staticmethod
    def get_emission_rate(model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age, *rate_names):
        """

        Args:
            model_year (int): vehicle model year for which to get emission factors
            sourcetype_name (str): the MOVES sourcetype name (e.g., 'passenger car', 'light commercial truck')
            reg_class_id (str): the regulatory class, e.g., 'car' or 'truck'
            in_use_fuel_id (str): the liquid fuel ID, e.g., 'pump gasoline'
            age (int): the vehicle age
            rate_names: name of emission rate(s) to get

        Returns:
            A list of emission rates for the given type of vehicle of the given model_year and age.

        """
        locals_dict = locals()
        rate = 0
        return_rates = list()

        if model_year < EmissionRatesVehicles.startyear_min:
            model_year = EmissionRatesVehicles.startyear_min

        for rate_name in rate_names:

            cache_key = (model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age, rate_name)
            if cache_key in _cache:
                rate = _cache[cache_key]
            else:
                rate_keys = [
                    k for k in EmissionRatesVehicles._data
                    if k[0] <= model_year
                       and k[1] == sourcetype_name
                       and k[2] == reg_class_id
                       and k[3] == in_use_fuel_id
                       and k[4] == rate_name
                ]
                if rate_keys == []:
                    rate_keys = [
                        k for k in EmissionRatesVehicles._data
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

                rate = eval(EmissionRatesVehicles._data[rate_key]['equation'], {}, locals_dict)

                if rate < 0:
                    temp_key = (model_year, sourcetype_name, reg_class_id, in_use_fuel_id, age - 1, rate_name)
                    rate = _cache[temp_key]

                _cache[cache_key] = rate

            return_rates.append(rate)

        return return_rates

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        EmissionRatesVehicles._data.clear()
        _cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

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

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

        if not template_errors:
            from context.onroad_fuels import OnroadFuel

            # validate columns
            # TODO: add sourcetype_name to validation_dict if we add that attribute
            validation_dict = {
                'in_use_fuel_id': OnroadFuel.fuel_ids,
                'reg_class_id': list(legacy_reg_classes)
            }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:

            rate_keys = zip(
                df['start_year'],
                df['sourcetype_name'],
                df['reg_class_id'],
                df['in_use_fuel_id'],
                df['rate_name']
            )
            df.set_index(rate_keys, inplace=True)

            EmissionRatesVehicles.startyear_min = min(df['start_year'])

            EmissionRatesVehicles._data = df.to_dict('index')

            for rate_key in rate_keys:

                rate_eq = EmissionRatesVehicles._data[rate_key]['equation']

                EmissionRatesVehicles._data[rate_key].update({'equation': compile(rate_eq, '<string>', 'eval')})

        return template_errors
