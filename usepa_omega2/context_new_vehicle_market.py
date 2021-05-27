"""
vehicles.py
===========


"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class ContextNewVehicleMarket(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'context_new_vehicle_market'
    index = Column('index', Integer, primary_key=True)
    context_ID = Column('context_id', String)
    case_ID = Column('case_id', String)
    context_size_class = Column('context_size_class', String)
    calendar_year = Column(Numeric)
    context_reg_class_ID = Column('context_reg_class_ID', Enum(*reg_classes, validate_strings=True))
    sales_share_of_regclass = Column(Numeric)
    sales_share_of_total = Column(Numeric)
    sales = Column(Numeric)
    weight_lbs = Column(Numeric)
    horsepower = Column(Numeric)
    horsepower_to_weight_ratio = Column(Numeric)
    mpg_conventional = Column(Numeric)
    mpg_conventional_onroad = Column(Numeric)
    mpg_alternative = Column(Numeric)
    mpg_alternative_onroad = Column(Numeric)
    onroad_to_cycle_mpg_ratio = Column(Numeric)
    ice_price_dollars = Column(Numeric)
    bev_price_dollars = Column(Numeric)

    hauling_context_size_class_info = dict()
    context_size_classes = dict()
    _new_vehicle_generalized_costs = dict()

    @classmethod
    def init_context_new_vehicle_generalized_costs(cls, filename):
        """
        Load context new vehicle prices from file or clear context_new_vehicle_generalized_costs and start from scratch

        Returns: updates context_new_vehicle_generalized_costs dict/dataframe

        """

        cls._new_vehicle_generalized_costs.clear()

        if not o2.options.generate_context_new_vehicle_generalized_costs_file:
            df = pd.read_csv(filename, index_col=0, dtype=str)
            # cls._new_vehicle_generalized_costs = df['new_vehicle_price_dollars'].to_dict()
            # OK, this is really weird and you shouldn't have to do this, but for whatever reason, when pandas
            # converts the strings to floats... they have different values than what's in the file
            # This is the workaround: let python do the conversion
            for key, value in df['new_vehicle_price_dollars'].items():
                cls._new_vehicle_generalized_costs[key] = float(value)

    @classmethod
    def save_context_new_vehicle_generalized_costs(cls, filename):
        """
        Save context_new_vehicle_generalized_costs to a .csv file

        """
        # pd.DataFrame.from_dict(cls._new_vehicle_generalized_costs, orient='index', columns=['new_vehicle_price_dollars']).to_csv(
        #     filename, index=True)

        # you shouldn't have to do this either... but somehow pandas (or maybe the OS) rounds the numbers when they get
        # written out to the file... this is the workaround: write the file yourself!
        with open(filename, 'w') as price_file:
            price_file.write(',new_vehicle_price_dollars\n')
            for k, v in ContextNewVehicleMarket._new_vehicle_generalized_costs.items():
                price_file.write('%d, %.38f\n' % (k, v))

    @classmethod
    def new_vehicle_generalized_costs(cls, calendar_year):
        """

        Args:
            calendar_year:

        Returns: context new vehicle price for the given calendar year

        """
        return cls._new_vehicle_generalized_costs[calendar_year]

    @classmethod
    def set_new_vehicle_generalized_cost(cls, calendar_year, generalized_cost):
        """
        Set context new vehicle price for the given calendar year to the given price
        Args:
            calendar_year:
            generalized_cost:

        """
        cls._new_vehicle_generalized_costs[calendar_year] = generalized_cost

    @staticmethod
    def new_vehicle_sales(calendar_year, context_size_class=None, context_reg_class=None):
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
                        sales_share_of_regclass=df.loc[i, 'sales_share_of_regclass'],
                        sales_share_of_total=df.loc[i, 'sales_share_of_total'],
                        sales=df.loc[i, 'sales'],
                        weight_lbs=df.loc[i, 'weight_lbs'],
                        horsepower=df.loc[i, 'horsepower'],
                        horsepower_to_weight_ratio=df.loc[i, 'horsepower_to_weight_ratio'],
                        mpg_conventional=df.loc[i, 'mpg_conventional'],
                        mpg_conventional_onroad=df.loc[i, 'mpg_conventional_onroad'],
                        mpg_alternative=df.loc[i, 'mpg_alternative'],
                        mpg_alternative_onroad=df.loc[i, 'mpg_alternative_onroad'],
                        onroad_to_cycle_mpg_ratio=df.loc[i, 'onroad_to_cycle_mpg_ratio'],
                        ice_price_dollars=df.loc[i, 'ice_price_dollars'],
                        bev_price_dollars=df.loc[i, 'bev_price_dollars'],
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
        init_fail = init_fail + ContextNewVehicleMarket.init_database_from_file(
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
