"""

**Code to load and implement production constraints by market class and year.**

Market classes are assumed to have no minimum or maximum constraint unless specified in the input file, and it
is only necessary to specify the limiting constraints, i.e. a minimum can be specified without specifying a
maximum, and vice versa.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents production constraints (specified as a market share) by market class ID and start year.
Shares are relative to the market category, not absolute.

File Type
    comma-separated values (CSV)

The data header consists of a ``start_year`` column followed by zero or more production constraint columns.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        start_year, ``{market_class_id}:{minimum_share or maximum_share}``, ...

Sample Header
    .. csv-table::

       input_template_name:,production_constraints,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,hauling.BEV:minimum_share,non_hauling.BEV:minimum_share,hauling.BEV:maximum_share,non_hauling.BEV:maximum_share
        2020,0.001,0.001,0.1,0.97

Data Column Name and Description

:start_year:
    Start year of production constraint, constraint applies until the next available start year

**Optional Columns**

:``{market_class_id}:{minimum_share or maximum_share}``:
    Holds the value of the minimum or maximum production constraint, as required, [0..1]

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

min_share_units = 'minimum_share'
max_share_units = 'maximum_share'


class ProductionConstraints(OMEGABase):
    """
    **Loads and provides access to production constraint data.**

    """
    _data = pd.DataFrame()

    _cache = dict()

    @staticmethod
    def get_minimum_share(calendar_year, market_class_id):
        """
        Get the minimum possible market share for the given calendar year and market class ID

        Args:
            calendar_year (int): calendar year to get minimum production constraint for
            market_class_id (str): market class id, e.g. 'hauling.ICE'

        Returns:
            The minimum production share for the given year and market class ID


        See Also:
            ``producer.compliance_strategy.create_tech_and_share_sweeps()``

        """
        cache_key = ('minimum_share', calendar_year, market_class_id)

        if cache_key not in ProductionConstraints._cache:
            minimum_share = 0

            start_years = ProductionConstraints._data['start_year']
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                min_key = '%s:%s' % (market_class_id, min_share_units)

                if min_key in ProductionConstraints._data:
                    minimum_share = ProductionConstraints._data[min_key].loc[
                        ProductionConstraints._data['start_year'] == calendar_year].item()

            ProductionConstraints._cache[cache_key] = minimum_share

        return ProductionConstraints._cache[cache_key]

    @staticmethod
    def get_maximum_share(calendar_year, market_class_id):
        """
        Get the maximum possible market share for the given calendar year and market class ID

        Args:
            calendar_year (int): calendar year to get maximum production constraint for
            market_class_id (str): market class id, e.g. 'hauling.ICE'

        Returns:
            The maximum production share for the given year and market class ID

        See Also:
            ``producer.compliance_strategy.create_tech_and_share_sweeps()``

        """
        cache_key = ('maximum_share', calendar_year, market_class_id)

        if cache_key not in ProductionConstraints._cache:
            maximum_share = 1

            start_years = ProductionConstraints._data['start_year']
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                max_key = '%s:%s' % (market_class_id, max_share_units)

                if max_key in ProductionConstraints._data:
                    maximum_share = ProductionConstraints._data[max_key].loc[
                        ProductionConstraints._data['start_year'] == calendar_year].item()

            ProductionConstraints._cache[cache_key] = maximum_share

        return ProductionConstraints._cache[cache_key]

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
        ProductionConstraints._data = pd.DataFrame()

        ProductionConstraints._cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'production_constraints'
        input_template_version = 0.2
        input_template_columns = {'start_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:

                share_columns = [c for c in df.columns if (min_share_units in c) or (max_share_units in c)]

                for sc in share_columns:
                    # validate data
                    template_errors += omega_globals.options.MarketClass.validate_market_class_id(sc.split(':')[0])

            if not template_errors:
                ProductionConstraints._data = df

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        # pull in reg classes before initializing classes that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        # pull in market classes before initializing classes that check market class validity
        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += ProductionConstraints.init_from_file(omega_globals.options.production_constraints_file,
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.output_folder)
            ProductionConstraints._data.to_csv(
                omega_globals.options.output_folder + os.sep + 'production_constraints.csv', index=False)

            print(ProductionConstraints.get_minimum_share(2020, 'hauling.BEV'))
            print(ProductionConstraints.get_minimum_share(2020, 'non_hauling.BEV'))
            print(ProductionConstraints.get_maximum_share(2020, 'hauling.ICE'))
            print(ProductionConstraints.get_maximum_share(2020, 'non_hauling.ICE'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
