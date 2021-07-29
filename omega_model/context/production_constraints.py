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

Template Header
    .. csv-table::

       input_template_name:,production_constraints,input_template_version:,0.2

The data header consists of a ``start_year`` column followed by zero or more production constraint columns.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        start_year, ``{market_class_id}:{minimum_share or maximum_share}``, ...

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
    Holds the value of the minimum or maximum production contraint, as required, [0..1]

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

min_share_units = 'minimum_share'
max_share_units = 'maximum_share'

cache = dict()


class ProductionConstraints(OMEGABase):
    values = pd.DataFrame()

    @staticmethod
    def get_minimum_share(calendar_year, market_class_id):

        start_years = cache['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        min_key = '%s:%s' % (market_class_id, min_share_units)

        if min_key in ProductionConstraints.values:
            return ProductionConstraints.values[min_key].loc[
                ProductionConstraints.values['start_year'] == calendar_year].item()
        else:
            return 0

    @staticmethod
    def get_maximum_share(calendar_year, market_class_id):

        start_years = cache['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        max_key = '%s:%s' % (market_class_id, max_share_units)

        if max_key in ProductionConstraints.values:
            return ProductionConstraints.values[max_key].loc[
                ProductionConstraints.values['start_year'] == calendar_year].item()
        else:
            return 1

    @staticmethod
    def init_from_file(filename, verbose=False):

        import numpy as np

        cache.clear()

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

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                ProductionConstraints.values['start_year'] = df['start_year']

                share_columns = [c for c in df.columns if (min_share_units in c) or (max_share_units in c)]

                for sc in share_columns:
                    market_class = sc.split(':')[0]
                    if market_class in omega_globals.options.MarketClass.market_classes:
                        ProductionConstraints.values[sc] = df[sc]
                    else:
                        template_errors.append('*** Invalid Market Class "%s" in %s ***' % (market_class, filename))

                cache['start_year'] = np.array(list(df['start_year']))


        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)
        init_fail += ProductionConstraints.init_from_file(omega_globals.options.production_constraints_file,
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            ProductionConstraints.values.to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'production_constraints.csv', index=False)

            print(ProductionConstraints.get_minimum_share(2020, 'hauling.BEV'))
            print(ProductionConstraints.get_minimum_share(2020, 'non_hauling.BEV'))
            print(ProductionConstraints.get_maximum_share(2020, 'hauling.ICE'))
            print(ProductionConstraints.get_maximum_share(2020, 'non_hauling.ICE'))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
