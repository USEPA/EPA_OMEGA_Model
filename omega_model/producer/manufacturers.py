"""

**Routines to load manufacturer definition data.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents manufacturer names.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,manufacturers,input_template_version:,0.0003,description:,default

Sample Data Columns
    .. csv-table::
        :widths: auto

        manufacturer_id
        consolidated_OEM
        OEM_A
        OEM_B

Data Column Name and Description

:manufacturer_id:
    The name of the manufacturer

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

# initial_credit_bank = dict()

# _cache = dict()


market_class_data = dict()


class Manufacturer(OMEGABase):
    """
    **Stores information regarding manufacturers, such as manufacturer ID.**

    """
    manufacturers = []  #: stores a list of manufacturer names after init

    @staticmethod
    def update_market_class_data(manufacturer_id, market_class_id):
        """
        Add the given market class id to the market class data for the given manufacturer.

        Args:
            manufacturer_id (str): e.g. 'consolidated_OEM'
            market_class_id (str): e.g. 'hauling.ICE'

        Returns:
            Nothing, updates market_class_data

        """
        if manufacturer_id not in market_class_data:
            market_class_data[manufacturer_id] = set()

        market_class_data[manufacturer_id].add(market_class_id)

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
        # _cache.clear()
        global market_class_data
        market_class_data = dict()

        from policy.credit_banking import CreditBank
        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'manufacturers'
        input_template_version = 0.0003
        input_template_columns = {'manufacturer_id'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                Manufacturer.manufacturers = list(df['manufacturer_id'].unique())

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

        omega_log.init_logfile()

        from context.onroad_fuels import OnroadFuel
        from producer.vehicle_annual_data import VehicleAnnualData

        init_fail += Manufacturer.init_from_file(omega_globals.options.manufacturers_file, 
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
