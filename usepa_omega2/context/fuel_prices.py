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

Template Header
    .. csv-table::

       input_template_name:,context_fuel_prices,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,case_id,fuel_id,calendar_year,retail_dollars_per_unit,pretax_dollars_per_unit
        AEO2020,Reference case,pump gasoline,2019,2.665601,2.10838
        AEO2020,Reference case,US electricity,2019,0.12559407,0.10391058

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', etc

    :fuel_id:
        The name of the vehicle in-use fuel, must be in the table loaded by ``class fuels.Fuel`` and consistent with
        the base year vehicles file (column ``in_use_fuel_id``) loaded by ``class vehicles.VehicleFinal``

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

from usepa_omega2 import *

cache = dict()


class FuelPrice(SQABase, OMEGABase):
    """
    **Loads and provides access to fuel prices from the analysis context**

    """

    # --- database table properties ---
    __tablename__ = 'context_fuel_prices'  # database table name
    index = Column('index', Integer, primary_key=True)  #: database table index
    context_ID = Column('context_id', String)  #: str: e.g. 'AEO2020'
    case_ID = Column('case_id', String)  #: str: e.g. 'Reference case'
    fuel_ID = Column('fuel_id', String)  #: str: e.g. 'pump gasoline'
    calendar_year = Column(Numeric)  #: numeric: calendar year of the price values
    retail_dollars_per_unit = Column(Float)  #: float: e.g. retail dollars per gallon, dollars per kWh
    pretax_dollars_per_unit = Column(Float)  #: float: e.g. pre-tax dollars per gallon, dollars per kWh

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

        if globals.options.flat_context:
            calendar_year = globals.options.flat_context_year

        cache_key = '%s_%s_%s_%s_%s' % \
                    (globals.options.context_id, globals.options.context_case_id, calendar_year, price_types, fuel_id)

        if cache_key not in cache:
            if type(price_types) is not list:
                price_types = [price_types]

            attrs = FuelPrice.get_class_attributes(price_types)

            result = globals.session.query(*attrs).\
                filter(FuelPrice.context_ID == globals.options.context_id).\
                filter(FuelPrice.case_ID == globals.options.context_case_id).\
                filter(FuelPrice.calendar_year == calendar_year).\
                filter(FuelPrice.fuel_ID == fuel_id).all()[0]

            if len(price_types) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        # don't forget to update the module docstring with changes here
        input_template_name = 'context_fuel_prices'
        input_template_version = 0.1
        input_template_columns = {'context_id', 'case_id', 'fuel_id', 'calendar_year', 'retail_dollars_per_unit',
                                  'pretax_dollars_per_unit'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                from context.onroad_fuels import OnroadFuel

                obj_list = []
                # load data into database
                for i in df.index:
                    fuel_id = df.loc[i, 'fuel_id']
                    if OnroadFuel.validate_fuel_ID(fuel_id):
                        obj_list.append(FuelPrice(
                            context_ID=df.loc[i, 'context_id'],
                            case_ID=df.loc[i, 'case_id'],
                            fuel_ID=fuel_id,
                            calendar_year=df.loc[i, 'calendar_year'],
                            retail_dollars_per_unit=df.loc[i, 'retail_dollars_per_unit'],
                            pretax_dollars_per_unit=df.loc[i, 'pretax_dollars_per_unit'],
                        ))
                    else:
                        template_errors.append('*** Invalid Context Fuel Price fuel ID "%s" in %s ***' %
                                               (fuel_id, filename))

                globals.session.add_all(obj_list)
                globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(globals.engine)

        init_fail = []
        init_fail += FuelPrice.init_database_from_file(globals.options.context_fuel_prices_file,
                                                       verbose=globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(globals.options.database_dump_folder)

            print(FuelPrice.get_retail_fuel_price(2020, 'pump gasoline'))
            print(FuelPrice.get_pretax_fuel_price(2020, 'pump gasoline'))

            print(FuelPrice.get_fuel_price(2020, 'retail_dollars_per_unit', 'pump gasoline'))
            print(FuelPrice.get_fuel_price(2020, 'pretax_dollars_per_unit', 'pump gasoline'))
            print(FuelPrice.get_fuel_price(2020, ['retail_dollars_per_unit', 'pretax_dollars_per_unit'], 'pump gasoline'))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
