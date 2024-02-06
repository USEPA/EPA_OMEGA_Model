"""

**Routines to load, access, and save new vehicle market data from/relative to the analysis context**

Market data includes total sales as well as sales by context size class (e.g. 'Small Crossover')

This module also saves new vehicle generalized costs (based in part on OMEGA tech costs)
from the reference session corresponding to the analysis context.  The reference session vehicle sales
(new vehicle market) will follow the analysis context sales, but prices/generalized costs within OMEGA will be
different from prices within the context due to differences in costing approaches, etc.  By saving the sales-weighted
new vehicle generalized costs from the reference session, subsequent sessions (with higher, lower, or the same costs)
will have an internally consistent (lower, higher or the same, respectively) overall sales response.
Whether the vehicle generalized costs file will be loaded from a file or created from scratch is controlled by the
batch process.  Generally speaking, best practice is to always auto-generate the new vehicle generalized costs file
from the reference session to guarantee consistency with the simulated vehicles file costs and all other factors
affecting generalized cost (such as fuel prices, cost years, etc).

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents vehicle sales broken out by size class and regulatory class for each year of data for various
context cases.  Some size classes are represented in more than one regulatory class, some are not.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,context_new_vehicle_market,input_template_version:,0.22

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,dollar_basis,case_id,context_size_class,body_style,calendar_year,reg_class_id,sales_share_of_body_style,sales_share_of_regclass,sales_share_of_total,sales,weight_lbs,horsepower,horsepower_to_weight_ratio,mpg_conventional,mpg_conventional_onroad,mpg_alternative,mpg_alternative_onroad,onroad_to_cycle_mpg_ratio,ice_price_dollars,bev_price_dollars
        AEO2020,2019,Reference case,Minicompact,sedan_wagon,2019,car,0.56,0.42,0.19,30958.782039697202,2938.287598,266.538513,0.09071219344948549,32.889961,26.858435502015,57.07032,46.6044793668,0.816615,76875.038,0.0
        AEO2020,2019,Reference case,Subcompact,sedan_wagon,2019,car,6.1,4.52,2.11,331827.2822319624,3315.591309,263.971893,0.07961532903149494,33.923519,27.702454468185,49.373997,40.319546560155004,0.816615,40670.395,0.0


Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :dollar_basis:
        The dollar basis of any monetary values taken from the given AEO version.

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', etc

    :context_size_class:
        The name of the vehicle size class, e.g. 'Minicompact', 'Large Utility', etc

    :body_style:
        The name of the vehicle body style, e.g., 'sedan_wagon', 'cuv_suv_van', 'pickup'

    :calendar_year:
        The calendar year of the vehicle market data

    :reg_class_id:
        The regulatory class of the vehicle data (within the context, reg class definitions may differ across
        years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical' or
        'legacy' reg class.

    :sales_share_of_body_style:
        Sales share of the size class within its body style

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
        The ratio of in-use to certification fuel economy

    :ice_price_dollars:
        Sales weighted average internal combustion engine (ICE) vehicle price (dollars)

    :bev_price_dollars:
        Sales weighted average battery electric vehicle (BEV) vehicle price (dollars)

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class NewVehicleMarket(OMEGABase):
    """
    **Loads, provides access to and saves new vehicle market data from/relative to the analysis context**

    For each calendar year, context total vehicle sales are broken down by size class, with one row for each unique
    combination of size class and reg class.

    """

    _data_by_csc_rc = dict()  # private dict, sales by context size class and legacy reg class
    _data_by_rc = pd.DataFrame()  # private dict, sales by legacy reg class
    _data_by_csc = dict()  # private dict, sales by context size class
    _data_by_bs = dict()  # private dict, sales by context body style
    _data_by_total = dict()  # private dict, total sales

    context_based_total_sales = dict()
    context_size_class_info_by_nrmc = dict()  #: dict of dicts: information about which context size classes are in which non-responsive market categories as well as what share of the size class is within the non-responsive category.  Populated by vehicles.py in Vehicle.init_vehicles_from_file()
    base_year_context_size_class_sales = dict()  #: dict: sales totals for each context size class represented in the base year vehicles input file (e.g 'vehicles.csv').  Populated by vehicles.py in Vehicle.init_vehicles_from_file()
    base_year_other_sales = dict()  #: dict: sales totals by other categories represented in the base year vehicles input file (e.g 'vehicles.csv').  Populated by vehicles.py in Vehicle.init_vehicles_from_file()
    manufacturer_base_year_sales_data = dict()  #: dict: sales totals by various categories by manufacturer represented in the base year vehicles input file (e.g 'vehicles.csv').  Populated by vehicles.py in Vehicle.init_vehicles_from_file()
    _context_new_vehicle_generalized_costs = dict()  # private dict,  stores total sales-weighted new vehicle generalized costs for use in determining overall sales response as a function of new vehicle generalized cost
    _session_new_vehicle_generalized_costs = dict()  # private dict,  stores total sales-weighted new vehicle generalized costs for the current session

    context_size_classes = []  # list of known context size classes from the input file (not all may be used, depending on the composition of the base year fleet)
    context_ids = []  # list of known context IDs from the input file
    context_case_ids = []  # list of known case IDs from the input file

    _data = dict()

    @classmethod
    def init_context_new_vehicle_generalized_costs(cls, filename):
        """
        Load context new vehicle prices from file or clear _context_new_vehicle_generalized_costs
        and start from scratch. Clears _session_new_vehicle_generalized_costs.

        Args:
            filename (str): name of file to load new vehicle generalized costs from if not generating a new one

        """

        cls.context_based_total_sales.clear()
        cls.context_size_class_info_by_nrmc.clear()
        cls.base_year_context_size_class_sales.clear()
        cls.base_year_other_sales.clear()
        cls.manufacturer_base_year_sales_data.clear()
        cls._context_new_vehicle_generalized_costs.clear()
        cls._session_new_vehicle_generalized_costs.clear()

        if not omega_globals.options.generate_context_calibration_files:
            max_year = 0
            df = pd.read_csv(filename, index_col=0, dtype=str)
            # wanted to do: cls._new_vehicle_generalized_costs = df['new_vehicle_price_dollars'].to_dict()
            # OK, this is really weird and you shouldn't have to do this, but for whatever reason, when pandas
            # converts the strings to floats... they have different values than what's in the file
            # This is the workaround: let python do the conversion
            for key, value in df['new_vehicle_price_dollars'].items():
                cls._context_new_vehicle_generalized_costs[key] = float(value)
                year = int(str.split(key, '_')[0])
                max_year = max(max_year, year)

            cls._context_new_vehicle_generalized_costs['max_year'] = max_year

    @classmethod
    def save_context_new_vehicle_generalized_costs(cls, filename):
        """
        Save context_new_vehicle_generalized_costs to a .csv file

        Args:
            filename (str): name of file to save new vehicle generalized costs to

        """
        if omega_globals.options.standalone_run:
            filename = omega_globals.options.output_folder_base + filename

        # wanted to do: pd.DataFrame.from_dict(cls._new_vehicle_generalized_costs, orient='index',
        #       columns=['new_vehicle_price_dollars']).to_csv(filename, index=True)

        # you shouldn't have to do this either... but somehow pandas (or maybe the OS) rounds the numbers when they get
        # written out to the file... this is the workaround: write the file yourself!
        with open(filename, 'w') as price_file:
            price_file.write(',new_vehicle_price_dollars\n')
            for k, v in NewVehicleMarket._context_new_vehicle_generalized_costs.items():
                price_file.write('%s, %.38f\n' % (k, v))

    @classmethod
    def save_session_new_vehicle_generalized_costs(cls, filename):
        """
        Save context_new_vehicle_generalized_costs to a .csv file

        Args:
            filename (str): name of file to save new vehicle generalized costs to

        """

        # wanted to do: pd.DataFrame.from_dict(cls._new_vehicle_generalized_costs, orient='index',
        #       columns=['new_vehicle_price_dollars']).to_csv(filename, index=True)

        # you shouldn't have to do this either... but somehow pandas (or maybe the OS) rounds the numbers when they get
        # written out to the file... this is the workaround: write the file yourself!
        with open(filename, 'a') as price_file:
            price_file.write(',new_vehicle_price_dollars\n')
            for k, v in NewVehicleMarket._session_new_vehicle_generalized_costs.items():
                price_file.write('%s, %.38f\n' % (k, v))

    @classmethod
    def get_context_new_vehicle_generalized_cost(cls, calendar_year, compliance_id):
        """
        Get sales-weighted new vehicle generalized cost for a given year, in OMEGA-centric dollars

        Args:
            calendar_year (numeric): calendar year
            compliance_id (str): manufacturer name, or 'consolidated_OEM'

        Returns:
            OMEGA-centric context new vehicle generalized cost for the given calendar year


        """

        max_year = cls._context_new_vehicle_generalized_costs['max_year']

        if calendar_year > max_year:
            omega_log.logwrite('\n### %d Exceeds context new vehicle gneralized cost max year %d ###' %
                               (calendar_year, max_year))

            calendar_year = max_year

        return cls._context_new_vehicle_generalized_costs['%s_%s' % (calendar_year, compliance_id)]

    @classmethod
    def set_context_new_vehicle_generalized_cost(cls, calendar_year, compliance_id, generalized_cost):
        """
        Store new vehicle generalized cost for the given calendar year

        Args:
            calendar_year (numeric): calendar year
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            generalized_cost (float): total sales-weighted OMEGA-centric generalized cost for the calendar year

        """

        cls._context_new_vehicle_generalized_costs['%s_%s' % (calendar_year, compliance_id)] = generalized_cost

    @classmethod
    def set_session_new_vehicle_generalized_cost(cls, calendar_year, compliance_id, generalized_cost):
        """
        Store new vehicle generalized cost for the given calendar year

        Args:
            calendar_year (numeric): calendar year
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            generalized_cost (float): total sales-weighted OMEGA-centric generalized cost for the calendar year

        """

        cls._session_new_vehicle_generalized_costs['%s_%s' % (calendar_year, compliance_id)] = generalized_cost

    @staticmethod
    def new_vehicle_data(calendar_year, context_size_class=None, context_reg_class=None, context_body_style=None,
                         value='sales'):
        """
        Get new vehicle sales by session context ID, session context case, calendar year, context size class
        and context reg class.  User can specify total sales (no optional arguments) or sales by context size class or
        sales by context size class and context reg class depending on the arguments provided

        Args:
            calendar_year (numeric): calendar year
            context_size_class (str | None): optional context size class, e.g. 'Small Crossover'
            context_reg_class (str | None): optional context reg class, e.g. 'car' or 'truck'
            context_body_style (str | None): e.g. 'sedan_wagon'
            value (str): the column name of the context value to sum

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
        if omega_globals.options.flat_context:
            calendar_year = omega_globals.options.flat_context_year

        if context_size_class and context_reg_class:
            if (omega_globals.options.context_id, omega_globals.options.context_case_id,
                    context_size_class, context_reg_class, calendar_year) in NewVehicleMarket._data_by_csc_rc:
                return np.sum(NewVehicleMarket._data_by_csc_rc[omega_globals.options.context_id,
                                                        omega_globals.options.context_case_id,
                                                        context_size_class, context_reg_class,
                calendar_year]['sales'].values)
            else:
                return 0

        elif context_size_class and not context_reg_class:
            return np.sum(NewVehicleMarket._data_by_csc[value][omega_globals.options.context_id,
                                                    omega_globals.options.context_case_id,
                                                    context_size_class, calendar_year])

        elif context_reg_class and not context_size_class:
            if (omega_globals.options.context_id, omega_globals.options.context_case_id, context_reg_class,
                 calendar_year) in NewVehicleMarket._data_by_rc[value]:
                return NewVehicleMarket._data_by_rc[value].loc[omega_globals.options.context_id,
                                                omega_globals.options.context_case_id,
                                                context_reg_class, calendar_year]
            else:
                return 0

        elif context_body_style:
            return np.sum(NewVehicleMarket._data_by_bs[value].loc[omega_globals.options.context_id,
                                                    omega_globals.options.context_case_id,
                                                    context_body_style, calendar_year])
        else:
            return np.sum(NewVehicleMarket._data_by_total[value][omega_globals.options.context_id,
                                                    omega_globals.options.context_case_id,
                                                    calendar_year].values)

    @staticmethod
    def validate_context_size_class(context_size_class):
        """
        Validate the given context size class

        Args:
            context_size_class (str): e.g. 'Large Pickup', etc

        Returns:
            ''True'' if the given context size class name is valid, ''False'' otherwise

        """
        return context_size_class in NewVehicleMarket.context_size_classes

    @staticmethod
    def validate_context_id(context_id):
        """
        Validate the given context ID

        Args:
            context_id (str): e.g. 'Reference case', etc

        Returns:
            ''True'' if the given context ID name is valid, ''False'' otherwise

        """
        return context_id in NewVehicleMarket.context_ids

    @staticmethod
    def validate_case_id(case_id):
        """
        Validate the given case ID

        Args:
            case_id (str): e.g. 'AEO2021', etc

        Returns:
            ''True'' if the given case ID name is valid, ''False'' otherwise

        """
        return case_id in NewVehicleMarket.context_case_ids

    @staticmethod
    def get_context_size_class_mpg(size_class, reg_class_id, year, onroad=True):
        """

        Args:
            size_class (str): the context_size_class, e.g., "Subcompact", "Large Van"
            reg_class_id (str): e.g., "car", "truck"
            year (int): the calendar year of new vehicles (i.e., the model year for age=0)
            onroad (bool): onroad miles per gallon if True; cycle if False

        Returns:

        """
        arg = 'mpg_conventional_onroad'
        if not onroad:
            arg = 'mpg_conventional'
        if (size_class, reg_class_id, year) in NewVehicleMarket._data:
            return NewVehicleMarket._data[(size_class, reg_class_id, year)][arg]
        elif (size_class, 'car', year) in NewVehicleMarket._data:
            return NewVehicleMarket._data[(size_class, 'car', year)][arg]
        else:
            return NewVehicleMarket._data[(size_class, 'truck', year)][arg]

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

        NewVehicleMarket._data_by_csc_rc.clear()
        NewVehicleMarket._data_by_rc = pd.DataFrame()
        NewVehicleMarket._data_by_csc.clear()
        NewVehicleMarket._data_by_bs.clear()
        NewVehicleMarket._data_by_total.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        NewVehicleMarket.hauling_context_size_class_info = dict()

        input_template_name = 'context_new_vehicle_market'
        input_template_version = 0.22
        input_template_columns = {'context_id', 'dollar_basis',	'case_id', 'context_size_class', 'body_style',
                                  'calendar_year', 'reg_class_id', 'sales'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'reg_class_id': list(legacy_reg_classes)}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            from producer.vehicle_aggregation import sales_weight_average_dataframe
            NewVehicleMarket._data_by_rc = \
                df.groupby(['context_id', 'case_id', 'reg_class_id', 'calendar_year']).\
                    apply(sales_weight_average_dataframe)

            NewVehicleMarket._data_by_csc_rc = \
                df.set_index(['context_id', 'case_id', 'context_size_class', 'reg_class_id', 'calendar_year']).\
                    sort_index().to_dict(orient='series')
            NewVehicleMarket._data_by_csc = \
                df.set_index(['context_id', 'case_id', 'context_size_class', 'calendar_year']).\
                    sort_index().to_dict(orient='series')
            NewVehicleMarket._data_by_bs = \
                df.set_index(['context_id', 'case_id', 'body_style', 'calendar_year']).\
                    sort_index().to_dict(orient='series')
            NewVehicleMarket._data_by_total = \
                df.set_index(['context_id', 'case_id', 'calendar_year']).\
                    sort_index().to_dict(orient='series')
            NewVehicleMarket.context_size_classes = df['context_size_class'].unique().tolist()
            NewVehicleMarket.context_ids = df['context_id'].unique().tolist()
            NewVehicleMarket.context_case_ids = df['case_id'].unique().tolist()

            df = df.loc[(df['context_id'] == omega_globals.options.context_id)
                        & (df['case_id'] == omega_globals.options.context_case_id), :]
            key = pd.Series(zip(
                df['context_size_class'],
                df['reg_class_id'],
                df['calendar_year'],
            ))
            NewVehicleMarket._data = df.set_index(key).to_dict(orient='series')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += NewVehicleMarket.init_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            print(NewVehicleMarket.new_vehicle_data(2021))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
