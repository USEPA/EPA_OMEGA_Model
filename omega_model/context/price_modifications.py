"""

**Code to implement (non-EPA-policy) price modifications, which may be price reductions or increases.**

An example price modification would be BEV rebates.  Price modifications are by market class ID and year.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents price modifications by market class ID and start year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,vehicle_price_modifications,input_template_version:,0.2

The data header consists of a ``start_year`` column followed by zero or more price modification columns.

Dynamic Data Header
    .. csv-table::
        :widths: auto

        start_year, ``{market_class_id}:price_modification_dollars``, ...

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,hauling.BEV:price_modification_dollars,non_hauling.BEV:price_modification_dollars
        2020,-7500,-5000

Data Column Name and Description

:start_year:
    Start year of price modification, modification applies until the next available start year

**Optional Columns**

:``{market_class_id}:price_modification_dollars``:
    Contains the price modification.  Value should be negative to reduce price, positive to increase price.

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

price_modification_str = 'price_modification_dollars'


class PriceModifications(OMEGABase):
    """
    **Loads and provides access to price modification data by model year and market class ID.**

    """
    _values = pd.DataFrame()  #: holds the price modification data

    @staticmethod
    def get_price_modification(calendar_year, market_class_id):
        """
        Get the price modification (if any) for the given year and market class ID.

        Args:
            calendar_year (int): calendar year to get price modification for
            market_class_id (str): market class id, e.g. 'hauling.ICE'

        Returns:
            The requested price modification, or 0 if there is none.

        """
        start_years = PriceModifications._values['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        mod_key = '%s:%s' % (market_class_id, price_modification_str)
        if mod_key in PriceModifications._values:
            return PriceModifications._values['%s:%s' % (market_class_id, price_modification_str)].loc[
                PriceModifications._values['start_year'] == calendar_year].item()
        else:
            return 0

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
        import numpy as np

        PriceModifications._values = pd.DataFrame()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'vehicle_price_modifications'
        input_template_version = 0.2
        input_template_columns = {'start_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                PriceModifications._values['start_year'] = np.array(df['start_year'])

                share_columns = [c for c in df.columns if (price_modification_str in c)]

                for sc in share_columns:
                    market_class = sc.split(':')[0]
                    if market_class in omega_globals.options.MarketClass.market_classes:
                        PriceModifications._values[sc] = df[sc]
                    else:
                        template_errors.append('*** Invalid Market Class "%s" in %s ***' % (market_class, filename))

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
        init_fail += PriceModifications.init_from_file(omega_globals.options.vehicle_price_modifications_file,
                                                       verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            PriceModifications._values.to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'vehicle_price_modifications.csv', index=False)

            print(PriceModifications.get_price_modification(2020, 'hauling.BEV'))
            print(PriceModifications.get_price_modification(2020, 'non_hauling.BEV'))
            print(PriceModifications.get_price_modification(2020, 'hauling.ICE'))
            print(PriceModifications.get_price_modification(2020, 'non_hauling.ICE'))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
