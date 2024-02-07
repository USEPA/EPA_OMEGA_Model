"""

**Routines to load and access fuel prices from the analysis context**

Context fuel price data includes retail and pre-tax costs in dollars per unit (e.g. $/gallon, $/kWh)

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents fuel prices by context case, fuel type, and calendar year.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,context_fuel_prices,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,dollar_basis,case_id,fuel_id,calendar_year,retail_dollars_per_unit,pretax_dollars_per_unit
        AEO2020,2019,Reference case,pump gasoline,2019,2.665601,2.10838
        AEO2020,2019,Reference case,US electricity,2019,0.12559407,0.10391058

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :dollar_basis:
        The dollar basis of the fuel prices in the given AEO version. Note that this dollar basis is
        converted in-code to 'analysis_dollar_basis' using the implicit_price_deflators input file.

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', etc

    :fuel_id:
        The name of the vehicle in-use fuel, must be in the table loaded by ``class fuels.Fuel`` and consistent with
        the base year vehicles file (column ``in_use_fuel_id``) loaded by ``class vehicles.Vehicle``

    :calendar_year:
        The calendar year of the fuel costs

    :retail_dollars_per_unit:
        Retail dollars per unit

    :pretax_dollars_per_unit:
        Pre-tax dollars per unit

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class FuelPrice(OMEGABase):
    """
    **Loads and provides access to fuel prices from the analysis context**

    """

    _data = dict()

    @staticmethod
    def get_fuel_prices(calendar_year, price_types, fuel_id):
        """
            Get fuel price data for fuel_id in calendar_year

        Args:
            calendar_year (numeric): calendar year to get price in
            price_types (str, [str1, str2...]): ContextFuelPrices attributes to get
            fuel_id (str): fuel ID

        Returns:
            Fuel price or tuple of fuel prices if multiple attributes were requested

        Example:
            ::

                pretax_pump_gas_price_dollars_2030 =
                ContextFuelPrices.get_fuel_prices(2030, 'pretax_dollars_per_unit', 'pump gasoline')

                pump_gas_attributes_2030 =
                ContextFuelPrices.get_fuel_prices(2030, ['retail_dollars_per_unit', 'pretax_dollars_per_unit'], 'pump gasoline')

        """
        cache_key = (calendar_year, str(price_types), fuel_id)

        if cache_key not in FuelPrice._data:
            if omega_globals.options.flat_context:
                calendar_year = omega_globals.options.flat_context_year
            else:
                calendar_year = max(
                    FuelPrice._data['min_calendar_year'],
                    min(calendar_year, FuelPrice._data['max_calendar_year'])
                )

            if type(price_types) is not list:
                price_types = [price_types]

            prices = []
            for pt in price_types:
                prices.append(
                    FuelPrice._data[
                        omega_globals.options.context_id,
                        omega_globals.options.context_case_id,
                        fuel_id,
                        calendar_year
                    ][pt]
                )
            if len(prices) == 1:
                FuelPrice._data[cache_key] = prices[0]
            else:
                FuelPrice._data[cache_key] = prices

        return FuelPrice._data[cache_key]

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
        FuelPrice._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        # don't forget to update the module docstring with changes here
        input_template_name = 'context_fuel_prices'
        input_template_version = 0.2
        input_template_columns = {'context_id', 'dollar_basis', 'case_id', 'fuel_id', 'calendar_year',
                                  'retail_dollars_per_unit', 'pretax_dollars_per_unit'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            from context.new_vehicle_market import NewVehicleMarket
            from context.onroad_fuels import OnroadFuel

            # validate columns
            validation_dict = {'context_id': NewVehicleMarket.context_ids,
                               'case_id': NewVehicleMarket.context_case_ids,
                               'fuel_id': OnroadFuel.fuel_ids,
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            df = df.loc[(df['context_id'] == omega_globals.options.context_id) &
                        (df['case_id'] == omega_globals.options.context_case_id), :]
            aeo_dollar_basis = df['dollar_basis'].mean()
            cols_to_convert = [col for col in df.columns if 'dollars_per_unit' in col]

            deflators = pd.read_csv(omega_globals.options.ip_deflators_file, skiprows=1, index_col=0).to_dict('index')

            adjustment_factor = deflators[omega_globals.options.analysis_dollar_basis]['price_deflator'] \
                                / deflators[aeo_dollar_basis]['price_deflator']

            for col in cols_to_convert:
                df[col] = df[col] * adjustment_factor

            df['dollar_basis'] = omega_globals.options.analysis_dollar_basis

            if not template_errors:
                FuelPrice._data = df.set_index(['context_id', 'case_id', 'fuel_id', 'calendar_year']).sort_index()\
                    .to_dict(orient='index')
                FuelPrice._data['min_calendar_year'] = df['calendar_year'].min()
                FuelPrice._data['max_calendar_year'] = df['calendar_year'].max()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        from context.onroad_fuels import OnroadFuel
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)

        from context.new_vehicle_market import NewVehicleMarket
        init_fail += NewVehicleMarket.init_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        init_fail += FuelPrice.init_from_file(omega_globals.options.context_fuel_prices_file,
                                              verbose=omega_globals.options.verbose)

        if not init_fail:
            print(FuelPrice.get_fuel_prices(2020, 'retail_dollars_per_unit', 'pump gasoline'))
            print(FuelPrice.get_fuel_prices(2020, 'pretax_dollars_per_unit', 'pump gasoline'))
            print(FuelPrice.get_fuel_prices(2020, ['retail_dollars_per_unit', 'pretax_dollars_per_unit'],
                                            'pump gasoline'))

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
