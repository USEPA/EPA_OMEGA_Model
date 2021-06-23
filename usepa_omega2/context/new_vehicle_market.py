"""

**Routines to load, access, and save new vehicle market data from/relative to the analysis context**

Market data includes total sales as well as sales by context size class (e.g. 'Small Crossover')

This module also saves new vehicle generalized costs (based in part on OMEGA tech costs)
from the reference session corresponding to the analysis context.  The reference session vehicle sales (new vehicle market)
will follow the analysis context sales, but prices/generalized costs within OMEGA will be different from prices within the
context due to differences in costing approaches, etc.  By saving the sales-weighted new vehicle generalized costs from
the reference session, subsequent sessions (with higher, lower, or the same costs) will have an internally consistent
(lower, higher or the same, respectively) overall sales response.  Whether the vehicle generalized costs file will be
loaded from a file or created from scratch is controlled by the batch process.  Generally speaking, best practice is to
always auto-generate the new vehicle generalized costs file from the reference session to guarantee consistency with the
simulated vehicles file costs and all other factors affecting generalized cost (such as fuel prices, cost years, etc).

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents vehicle sales broken out by size class and regulatory class for each year of data for various
context cases.  Some size classes are represented in more than one regulatory class, some are not.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_new_vehicle_market,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,case_id,context_size_class,calendar_year,reg_class_id,sales_share_of_regclass,sales_share_of_total,sales,weight_lbs,horsepower,horsepower_to_weight_ratio,mpg_conventional,mpg_conventional_onroad,mpg_alternative,mpg_alternative_onroad,onroad_to_cycle_mpg_ratio,ice_price_dollars,bev_price_dollars
        AEO2020,Reference case,Minicompact,2019,car,0.42,0.19,30958.78204,2938.287598,266.538513,0.090712193,32.889961,26.8584355,57.07032,46.60447937,0.816615,76875.038,0
        AEO2020,Reference case,Large Utility,2019,truck,5.01,2.67,419179.8267,5278.119141,347.891754,0.065912069,25.18989,20.53877833,28.389875,23.1479117,0.815358,62510.323,109753.937

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', etc

    :context_size_class:
        The name of the vehicle size class, e.g. 'Minicompact', 'Large Utility', etc

    :calendar_year:
        The calendar year of the vehicle market data

    :reg_class_id:
        The regulatory class of the vehicle data (within the context, reg class definitions may differ across
        years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical' or
        'legacy' reg class.

    :sales_share_of_regclass:
        Sales share of the size class within its regulatory class

    :sales_share_of_total:
        Sales share of the total vehicle sales

    :sales:
        Number of vehicles sold of the size class

    :weight_lbs:
        Sales weighted average vehicle weight (pounds) of the size class

    :horsepower:
        Sales weighted average vehicle power (horsepower) of the size class

    :horsepower_to_weight_ratio:
        Sales weighted average vehicle power to weight ratio (horsepower/pound) of the size class

    :mpg_conventional:
        Sales weighted average certification fuel economy (miles per gallon, MPG)

    :mpg_conventional_onroad:
        Sales weighted average in-use fuel economy (miles per gallon, MPG), lower than the certification fuel economy by
        the ``onroad_to_cycle_mpg_ratio``

    :mpg_alternative:
        Sales weighted average battery electric certification fuel economy (miles per gallon equivalent, MPGe)

    :mpg_alternative_onroad:
        Sales weighted average battery electric in-use fuel economy (miles per gallon equivalent, MPGe)

    :onroad_to_cycle_mpg_ratio:
        The ratio of in-use to certfication fuel economy

    :ice_price_dollars:
        Sales weighted average internal combustion engine (ICE) vehicle price (dollars)

    :bev_price_dollars:
        Sales weighted average battery electric vehicle (BEV) vehicle price (dollars)

----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class NewVehicleMarket(SQABase, OMEGABase):
    """
    **Loads, provides access to and saves new vehicle market data from/relative to the analysis context**

    For each calendar year, context total vehicle sales are broken down by size class, with one row for each unique
    combination of size class and reg class

    """

    # --- database table properties ---
    __tablename__ = 'context_new_vehicle_market'  # database table name
    index = Column('index', Integer, primary_key=True)  #: database table index
    context_ID = Column('context_id', String)  #: str: e.g. 'AEO2020'
    case_ID = Column('case_id', String)  #: str: e.g. 'Reference case'
    context_size_class = Column('context_size_class', String)   #: str: e.g. 'Small Crossover'
    calendar_year = Column(Numeric)  #: numeric: calendar year of the market data
    context_reg_class_ID = Column('context_reg_class_ID', Enum(*reg_classes, validate_strings=True))  #: str: e.g. 'car', 'truck'
    # sales_share_of_regclass = Column(Numeric)   #: numeric: percent of reg class represented by the context size class
    # sales_share_of_total = Column(Numeric)  #: numeric: percent of total sales represented by the context size class
    sales = Column(Numeric)  #: numeric:  size class new vehicle sales
    # weight_lbs = Column(Numeric)  #: numeric: sales-weighted average weight (lbs) of a vehicle in the size class
    # horsepower = Column(Numeric)  #: numeric: sales-weighted average horsepower of a vehicle in the size class
    # horsepower_to_weight_ratio = Column(Numeric)  #: numeric: sales-weighted average horsepower to weight ratio of a vehicle in the size class
    # mpg_conventional = Column(Numeric)  #: numeric: sales-weighted average miles per gallon (mpg) of a vehicle in the size class
    # mpg_conventional_onroad = Column(Numeric)  #: numeric: sales-weighted average on-road miles per gallon (mpg) of a vehicle in the size class
    # mpg_alternative = Column(Numeric)  #: numeric: sales-weighted average MPGe of a vehicle in the size class
    # mpg_alternative_onroad = Column(Numeric)  #: numeric: sales-weighted average onroad MPGe of a vehicle in the size class
    # onroad_to_cycle_mpg_ratio = Column(Numeric)  #: numeric: ratio of on-road to 2-cycle miles per gallon
    # ice_price_dollars = Column(Numeric)  #: numeric: sales-weighted average price of an internal combustion engine (ICE) vehicle in the size class
    # bev_price_dollars = Column(Numeric)  #: numeric: sales-weighted average price of an battery-electric vehicle (BEV) in the size class

    hauling_context_size_class_info = dict()  #: dict: information about which context size classes are considered hauling and non-hauling as well as what share of the size class is hauling or not.  Populated by vehicles.py in VehicleFinal.init_vehicles_from_file()
    context_size_classes = dict()  #: dict: lists for each context size class represented in the base year vehicles input file (e.g 'vehicles.csv').  Populated by vehicles.py in VehicleFinal.init_vehicles_from_file()
    _new_vehicle_generalized_costs = dict()  # private dict,  stores total sales-weighted new vehicle generalized costs for use in determining overall sales response as a function of new vehicle generalized cost

    @classmethod
    def init_context_new_vehicle_generalized_costs(cls, filename):
        """
        Load context new vehicle prices from file or clear context_new_vehicle_generalized_costs and start from scratch

        Args:
            filename (str): name of file to load new vehicle generalized costs from if not generating a new one

        """

        cls._new_vehicle_generalized_costs.clear()

        if not globals.options.generate_context_new_vehicle_generalized_costs_file:
            df = pd.read_csv(filename, index_col=0, dtype=str)
            # wanted to do: cls._new_vehicle_generalized_costs = df['new_vehicle_price_dollars'].to_dict()
            # OK, this is really weird and you shouldn't have to do this, but for whatever reason, when pandas
            # converts the strings to floats... they have different values than what's in the file
            # This is the workaround: let python do the conversion
            for key, value in df['new_vehicle_price_dollars'].items():
                cls._new_vehicle_generalized_costs[key] = float(value)

    @classmethod
    def save_context_new_vehicle_generalized_costs(cls, filename):
        """
        Save context_new_vehicle_generalized_costs to a .csv file

        Args:
            filename (str): name of file to save new vehicle generalized costs to

        """

        # wanted to do: pd.DataFrame.from_dict(cls._new_vehicle_generalized_costs, orient='index',
        #       columns=['new_vehicle_price_dollars']).to_csv(filename, index=True)

        # you shouldn't have to do this either... but somehow pandas (or maybe the OS) rounds the numbers when they get
        # written out to the file... this is the workaround: write the file yourself!
        with open(filename, 'w') as price_file:
            price_file.write(',new_vehicle_price_dollars\n')
            for k, v in NewVehicleMarket._new_vehicle_generalized_costs.items():
                price_file.write('%d, %.38f\n' % (k, v))

    @classmethod
    def new_vehicle_generalized_cost(cls, calendar_year):
        """
        Get sales-weighted new vehicle generalized cost for a given year, in OMEGA-centric dollars

        Args:
            calendar_year (numeric): calendar year

        Returns:
            OMEGA-centric context new vehicle generalized cost for the given calendar year


        """

        return cls._new_vehicle_generalized_costs[calendar_year]

    @classmethod
    def set_new_vehicle_generalized_cost(cls, calendar_year, generalized_cost):
        """
        Store new vehicle generalized cost for the given calendar year

        Args:
            calendar_year (numeric): calendar year
            generalized_cost (float): total sales-weighted OMEGA-centric generalized cost for the calendar year

        """

        cls._new_vehicle_generalized_costs[calendar_year] = generalized_cost

    @staticmethod
    def new_vehicle_sales(calendar_year, context_size_class=None, context_reg_class=None):
        """
        Get new vehicle sales by session context ID, session context case, calendar year, context size class
        and context reg class.  User can specify total sales (no optional arguments) or sales by context size class or
        sales by context size class and context reg class depending on the arguments provided

        Args:
            calendar_year (numeric): calendar year
            context_size_class (str): optional context size class, e.g. 'Small Crossover'
            context_reg_class (str): optional context reg class, e.g. 'car' or 'truck'

        Returns:
            new vehicle total sales or sales by context size class or by context size class and reg class

        Examples:
            ::

                total_new_vehicle_sales_2030 =
                    ContextNewVehicleMarket.new_vehicle_sales(2030)

                small_crossover_new_vehicle_sales_2030 =
                    ContextNewVehicleMarket.new_vehicle_sales(2030, context_size_class='Small Crossover')

                small_crossover_car_new_vehicle_sales_2030 =
                    ContextNewVehicleMarket.new_vehicle_sales(2030, context_size_class='Small Crossover', context_reg_class='car')

        """
        if globals.options.flat_context:
            calendar_year = globals.options.flat_context_year

        cache_key = '%s_%s_%s_%s_%s_new_vehicle_sales' % (globals.options.context_id, globals.options.context_case_id,
                                                          calendar_year, context_size_class, context_reg_class)

        if cache_key not in cache:
            if context_size_class and context_reg_class:
                projection_sales = (globals.session.query(func.sum(NewVehicleMarket.sales))
                                    .filter(NewVehicleMarket.context_ID == globals.options.context_id)
                                    .filter(NewVehicleMarket.case_ID == globals.options.context_case_id)
                                    .filter(NewVehicleMarket.context_size_class == context_size_class)
                                    .filter(NewVehicleMarket.context_reg_class_ID == context_reg_class)
                                    .filter(NewVehicleMarket.calendar_year == calendar_year).scalar())
                if projection_sales is None:
                    cache[cache_key] = 0
                else:
                    cache[cache_key] = float(projection_sales)
            elif context_size_class:
                cache[cache_key] = float(globals.session.query(func.sum(NewVehicleMarket.sales))
                                         .filter(NewVehicleMarket.context_ID == globals.options.context_id)
                                         .filter(NewVehicleMarket.case_ID == globals.options.context_case_id)
                                         .filter(NewVehicleMarket.context_size_class == context_size_class)
                                         .filter(NewVehicleMarket.calendar_year == calendar_year).scalar())
            else:
                cache[cache_key] = float(globals.session.query(func.sum(NewVehicleMarket.sales))
                                         .filter(NewVehicleMarket.context_ID == globals.options.context_id)
                                         .filter(NewVehicleMarket.case_ID == globals.options.context_case_id)
                                         .filter(NewVehicleMarket.calendar_year == calendar_year).scalar())

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

        NewVehicleMarket.hauling_context_size_class_info = dict()

        input_template_name = 'context_new_vehicle_market'
        input_template_version = 0.1
        input_template_columns = {'context_id',	'case_id', 'context_size_class', 'calendar_year', 'reg_class_id',
                                  'sales_share_of_regclass', 'sales_share_of_total', 'sales', 'weight_lbs',
                                  'horsepower', 'horsepower_to_weight_ratio', 'mpg_conventional',
                                  'mpg_conventional_onroad', 'mpg_alternative', 'mpg_alternative_onroad',
                                  'onroad_to_cycle_mpg_ratio', 'ice_price_dollars', 'bev_price_dollars'}

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
                    obj_list.append(NewVehicleMarket(
                        context_ID=df.loc[i, 'context_id'],
                        case_ID=df.loc[i, 'case_id'],
                        context_size_class=df.loc[i, 'context_size_class'],
                        calendar_year=df.loc[i, 'calendar_year'],
                        context_reg_class_ID=df.loc[i, 'reg_class_id'],
                        # sales_share_of_regclass=df.loc[i, 'sales_share_of_regclass'],
                        # sales_share_of_total=df.loc[i, 'sales_share_of_total'],
                        sales=df.loc[i, 'sales'],
                        # weight_lbs=df.loc[i, 'weight_lbs'],
                        # horsepower=df.loc[i, 'horsepower'],
                        # horsepower_to_weight_ratio=df.loc[i, 'horsepower_to_weight_ratio'],
                        # mpg_conventional=df.loc[i, 'mpg_conventional'],
                        # mpg_conventional_onroad=df.loc[i, 'mpg_conventional_onroad'],
                        # mpg_alternative=df.loc[i, 'mpg_alternative'],
                        # mpg_alternative_onroad=df.loc[i, 'mpg_alternative_onroad'],
                        # onroad_to_cycle_mpg_ratio=df.loc[i, 'onroad_to_cycle_mpg_ratio'],
                        # ice_price_dollars=df.loc[i, 'ice_price_dollars'],
                        # bev_price_dollars=df.loc[i, 'bev_price_dollars'],
                    ))
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
        globals.engine.echo = True
        omega_log.init_logfile()

        SQABase.metadata.create_all(globals.engine)

        init_fail = []
        init_fail += NewVehicleMarket.init_database_from_file(
            globals.options.context_new_vehicle_market_file, verbose=globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(globals.options.database_dump_folder)
            print(NewVehicleMarket.new_vehicle_sales(2021))
            # print(ContextNewVehicleMarket.get_new_vehicle_sales_weighted_price(2021))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
