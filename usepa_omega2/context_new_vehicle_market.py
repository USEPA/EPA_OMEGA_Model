"""
context_new_vehicle_market.py
=============================

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

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class ContextNewVehicleMarket(SQABase, OMEGABase):
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

        if not o2.options.generate_context_new_vehicle_generalized_costs_file:
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
            for k, v in ContextNewVehicleMarket._new_vehicle_generalized_costs.items():
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
        if o2.options.flat_context:
            calendar_year = o2.options.flat_context_year

        cache_key = '%s_%s_%s_%s_%s_new_vehicle_sales' % (o2.options.context_id, o2.options.context_case_id,
                                                          calendar_year, context_size_class, context_reg_class)

        if cache_key not in cache:
            if context_size_class and context_reg_class:
                projection_sales = (o2.session.query(func.sum(ContextNewVehicleMarket.sales))
                                    .filter(ContextNewVehicleMarket.context_ID == o2.options.context_id)
                                    .filter(ContextNewVehicleMarket.case_ID == o2.options.context_case_id)
                                    .filter(ContextNewVehicleMarket.context_size_class == context_size_class)
                                    .filter(ContextNewVehicleMarket.context_reg_class_ID == context_reg_class)
                                    .filter(ContextNewVehicleMarket.calendar_year == calendar_year).scalar())
                if projection_sales is None:
                    cache[cache_key] = 0
                else:
                    cache[cache_key] = float(projection_sales)
            elif context_size_class:
                cache[cache_key] = float(o2.session.query(func.sum(ContextNewVehicleMarket.sales))
                                         .filter(ContextNewVehicleMarket.context_ID == o2.options.context_id)
                                         .filter(ContextNewVehicleMarket.case_ID == o2.options.context_case_id)
                                         .filter(ContextNewVehicleMarket.context_size_class == context_size_class)
                                         .filter(ContextNewVehicleMarket.calendar_year == calendar_year).scalar())
            else:
                cache[cache_key] = float(o2.session.query(func.sum(ContextNewVehicleMarket.sales))
                                         .filter(ContextNewVehicleMarket.context_ID == o2.options.context_id)
                                         .filter(ContextNewVehicleMarket.case_ID == o2.options.context_case_id)
                                         .filter(ContextNewVehicleMarket.calendar_year == calendar_year).scalar())

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

        ContextNewVehicleMarket.hauling_context_size_class_info = dict()

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
                    obj_list.append(ContextNewVehicleMarket(
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
        o2.engine.echo = True
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail += ContextNewVehicleMarket.init_database_from_file(
            o2.options.context_new_vehicle_market_file, verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)
            print(ContextNewVehicleMarket.new_vehicle_sales(2021))
            # print(ContextNewVehicleMarket.get_new_vehicle_sales_weighted_price(2021))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)