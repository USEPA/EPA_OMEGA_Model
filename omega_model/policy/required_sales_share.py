"""

**Routines to load and apply (optional) required sales shares by market class.**

This module could be used to investigate the effect of ZEV mandates, for example.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents required minimum sales shares by market class ID and start year.  Shares are relative
to the market category, not absolute.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,required_sales_share,input_template_version:,0.2

The data header consists of a ``start_year`` column followed by zero or more required sales share columns.

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,hauling.BEV:minimum_share,non_hauling.BEV:minimum_share
        2020,0.05,0.1

Data Column Name and Description

:start_year:
    Start year of required sales share, sales share applies until the next available start year

**Optional Columns**

:``{market_class_id}:minimum_share``:
    Holds the value of the minimum sales share,  [0..1]

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

min_share_units_str = 'minimum_share'


class RequiredSalesShare(OMEGABase):
    """
    **Loads and provides access to minimum required sales shares by year and market class ID.**

    Can be used to investigate the effects of policies like a ZEV mandate.

    """
    _data = pd.DataFrame()

    _cache = dict()

    @staticmethod
    def get_minimum_share(calendar_year, market_class_id):
        """

        Args:
            calendar_year (int): calendar year to get minimum production constraint for
            market_class_id (str): market class id, e.g. 'hauling.ICE'

        Returns:
            The minimum production share for the given year and market class ID

        See Also:
            ``producer.compliance_strategy.create_tech_and_share_sweeps()``

        """
        cache_key = (calendar_year, market_class_id)

        if cache_key not in RequiredSalesShare._cache:

            minimum_share = 0

            start_years = RequiredSalesShare._data['start_year']
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                min_key = '%s:%s' % (market_class_id, min_share_units_str)
                if min_key in RequiredSalesShare._data:
                    minimum_share = RequiredSalesShare._data['%s:%s' % (market_class_id, min_share_units_str)].loc[
                        RequiredSalesShare._data['start_year'] == calendar_year].item()

            RequiredSalesShare._cache[cache_key] = minimum_share

        return RequiredSalesShare._cache[cache_key]

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
        RequiredSalesShare._data = pd.DataFrame()

        RequiredSalesShare._cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'required_sales_share'
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
            share_columns = [c for c in df.columns if (min_share_units_str in c)]

            for sc in share_columns:
                # validate data
                template_errors += omega_globals.options.MarketClass.validate_market_class_id(sc.split(':')[0])

        if not template_errors:
            RequiredSalesShare._data = df

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []
        omega_log.init_logfile()

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

        init_fail += RequiredSalesShare.init_from_file(omega_globals.options.required_sales_share_file,
                                                       verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.output_folder)
            RequiredSalesShare._data.to_csv(
                omega_globals.options.output_folder + os.sep + 'required_zev_shares.csv', index=False)

            print(RequiredSalesShare.get_minimum_share(2020, 'hauling.BEV'))
            print(RequiredSalesShare.get_minimum_share(2020, 'non_hauling.BEV'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
