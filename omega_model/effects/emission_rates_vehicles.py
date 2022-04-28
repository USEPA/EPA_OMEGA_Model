"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents tailpipe emission rates by model year, age, reg-class and fuel type as estimated by EPA's MOVES model.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,emission_factors_vehicles,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        model_year,age,reg_class_id,in_use_fuel_id,voc_grams_per_mile,co_grams_per_mile,nox_grams_per_mile,pm25_grams_per_mile,sox_grams_per_gallon,benzene_grams_per_mile,butadiene13_grams_per_mile,formaldehyde_grams_per_mile,acetaldehyde_grams_per_mile,acrolein_grams_per_mile,co2_grams_per_mile,n2o_grams_per_mile,ch4_grams_per_mile
        2020,0,car,pump gasoline,0.038838978,0.934237929,0.041727278,0.001925829,0.001648851,0.001641638,0.0003004,0.000441563,0.000767683,4.91E-05,,0.004052681,0.005520596
        2020,0,truck,pump gasoline,0.035665375,1.068022441,0.054597497,0.002444363,0.002240974,0.001499163,0.000262733,0.000411881,0.000764069,4.45E-05,,0.005146965,0.007103921


Data Column Name and Description
    :model_year:
        The model year of vehicles, e.g. 2020

    :age:
        The age of vehicles

    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :voc_grams_per_mile:
        The vehicle emission factors follow the structure pollutant_units where units are grams per mile.

----

**CODE**

"""

from omega_model import *


class EmissionRatesVehicles(OMEGABase):
    """
    Loads and provides access to vehicle emission factors by model year, age, legacy reg class ID and in-use fuel ID.

    """

    _data = dict()  # private dict, emission factors vehicles by model year, age, legacy reg class ID and in-use fuel ID
    _cache = dict()

    @staticmethod
    def get_emission_rate(model_year, reg_class_id, in_use_fuel_id, ind_var_name, independent_variable, rate_name):
        """

        Args:
            model_year (int): vehicle model year for which to get emission factors
            reg_class_id (str): the regulatory class, e.g., 'car' or 'truck'
            in_use_fuel_id (str): the liquid fuel ID, e.g., 'pump gasoline'
            ind_var_dict (dictionary): the independent_variable and value e.g., {'age': 10} or {'odometer': 75000}).
            rate_name: name of emission rate to get

        Returns:
            The emission rate or list of emission rates

        """
        locals_dict = locals()
        cache_key = (model_year, reg_class_id, in_use_fuel_id, rate_name, ind_var_name)
        rate = 0
        rate_name_keys = [k for k in EmissionRatesVehicles._data.keys()
                          if k[1] == reg_class_id
                          and k[2] == in_use_fuel_id
                          and k[3] == rate_name
                          and k[4] == ind_var_name]
        if cache_key not in EmissionRatesVehicles._cache:
            max_start_year = max([k[0] for k in rate_name_keys])
            year = min(model_year, max_start_year)
            rate = eval(EmissionRatesVehicles._data[year, reg_class_id, in_use_fuel_id, rate_name, ind_var_name]['equation'], {},
                        locals_dict)
            EmissionRatesVehicles._cache[cache_key] = rate
        else:
            rate = EmissionRatesVehicles._cache[cache_key]

        return rate

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

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'emission_rates_vehicles'
        input_template_version = 0.1
        input_template_columns = {'start_year',
                                  'reg_class_id',
                                  'market_class_id',
                                  'in_use_fuel_id',
                                  'rate_name',
                                  'independent_variable',
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
            validation_dict = {'in_use_fuel_id': OnroadFuel.fuel_ids,
                               'reg_class_id': list(legacy_reg_classes)}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:

            rate_keys = zip(df['start_year'],
                            df['reg_class_id'],
                            df['in_use_fuel_id'],
                            df['rate_name'],
                            df['independent_variable'])

            for rate_key in rate_keys:

                EmissionRatesVehicles._data[rate_key] = dict()
                start_year, reg_class_id, fuel_id, rate_name, ind_var_name = rate_key

                rate_info = df[(df['start_year'] == start_year)
                               & (df['reg_class_id'] == reg_class_id)
                               & (df['in_use_fuel_id'] == fuel_id)
                               & (df['rate_name'] == rate_name)
                               & (df['independent_variable'] == ind_var_name)].iloc[0]

                EmissionRatesVehicles._data[rate_key] = {'equation': None}

                EmissionRatesVehicles._data[rate_key]['equation'] = compile(rate_info['equation'], '<string>', 'eval')

        return template_errors
