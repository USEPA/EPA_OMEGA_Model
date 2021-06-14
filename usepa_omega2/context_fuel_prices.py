"""
context_fuel_prices.py
======================

**Routines to load and access fuel prices from the analysis context**

Context fuel price data includes retail and pre-tax costs in dollars per unit (e.g. $/gallon, $/kWh)


"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class ContextFuelPrices(SQABase, OMEGABase):
    """
    **Loads and provides access to fuel prices from the analysis context**

    """

    # --- database table properties ---
    __tablename__ = 'context_fuels'  # database table name
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

        if o2.options.flat_context:
            calendar_year = o2.options.flat_context_year

        cache_key = '%s_%s_%s_%s_%s' % \
                    (o2.options.context_id, o2.options.context_case_id, calendar_year, price_types, fuel_id)

        if cache_key not in cache:
            if type(price_types) is not list:
                price_types = [price_types]

            attrs = ContextFuelPrices.get_class_attributes(price_types)

            result = o2.session.query(*attrs).\
                filter(ContextFuelPrices.context_ID == o2.options.context_id).\
                filter(ContextFuelPrices.case_ID == o2.options.context_case_id).\
                filter(ContextFuelPrices.calendar_year == calendar_year).\
                filter(ContextFuelPrices.fuel_ID == fuel_id).all()[0]

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
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(ContextFuelPrices(
                        context_ID=df.loc[i, 'context_id'],
                        case_ID=df.loc[i, 'case_id'],
                        fuel_ID=df.loc[i, 'fuel_id'],
                        calendar_year=df.loc[i, 'calendar_year'],
                        retail_dollars_per_unit=df.loc[i, 'retail_dollars_per_unit'],
                        pretax_dollars_per_unit=df.loc[i, 'pretax_dollars_per_unit'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail += ContextFuelPrices.init_database_from_file(o2.options.context_fuel_prices_file,
                                                                          verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            print(ContextFuelPrices.get_retail_fuel_price(2020, 'pump gasoline'))
            print(ContextFuelPrices.get_pretax_fuel_price(2020, 'pump gasoline'))

            print(ContextFuelPrices.get_fuel_price(2020, 'retail_dollars_per_unit', 'pump gasoline'))
            print(ContextFuelPrices.get_fuel_price(2020, 'pretax_dollars_per_unit', 'pump gasoline'))
            print(ContextFuelPrices.get_fuel_price(2020, ['retail_dollars_per_unit', 'pretax_dollars_per_unit'], 'pump gasoline'))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)