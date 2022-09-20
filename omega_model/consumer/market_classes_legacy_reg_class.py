"""

**Routines to implement market-class related functionality.**

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents characteristics of the Consumer Module's market classes.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,0.32

Sample Header
    .. csv-table::

       input_template_name:,consumer.market_classes,input_template_version:,0.32

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,fueling_class,ownership_class
        non_hauling.BEV,BEV,private
        hauling.ICE,ICE,private

Data Column Name and Description

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:fueling_class:
    Market class fueling class, e.g. 'BEV', 'ICE'

:ownership_class:
    Market class ownership class, e.g. 'private', 'shared' (For future development)

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class MarketClass(OMEGABase, MarketClassBase):
    """
    Loads market class definition data and provides market-class-related functionality.

    """

    _data = dict()

    market_categories = ['ICE', 'BEV', 'hauling', 'non_hauling']  #: overall market categories
    responsive_market_categories = ['ICE', 'BEV']  #: market categories that have consumer response (i.e. price -> sales)
    non_responsive_market_categories = ['hauling', 'non_hauling']  #: market categories that do not have consumer response

    @staticmethod
    def get_vehicle_market_class(vehicle):
        """
        Get vehicle market class ID based on vehicle characteristics

        Args:
            vehicle (VehicleFinal): the vehicle to determine the market class of

        Returns:
            The vehicle's market class ID based on vehicle characteristics.

        """
        if vehicle.base_year_reg_class_id == 'truck' and vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
            market_class_id = 'hauling.BEV'
        elif vehicle.base_year_reg_class_id == 'truck' and vehicle.base_year_powertrain_type not in ['BEV', 'FCV']:
            market_class_id = 'hauling.ICE'
        elif vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
            market_class_id = 'non_hauling.BEV'
        else:
            market_class_id = 'non_hauling.ICE'

        return market_class_id

    @staticmethod
    def get_non_responsive_market_category(market_class_id):
        """
        Returns the non-responsive market category of the given market class ID

        Args:
            market_class_id (str): market class ID, e.g. 'hauling.ICE'

        Returns:
            The non-responsive market category of the given market class ID

        """
        if 'non_hauling' in market_class_id.split('.'):
            return 'non_hauling'
        else:
            return 'hauling'

    @staticmethod
    def validate_market_class_id(market_class_id):
        """
        Validate market class ID

        Args:
            market_class_id (str): market class ID, e.g. 'hauling.ICE'

        Returns:
            Error message in a list if market_class_id is not valid

        """
        if market_class_id not in MarketClass._data:
            return ['Unexpected market_class_id "%s"' % market_class_id]
        else:
            return []

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
        MarketClass._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        MarketClassBase._market_class_dict = dict()  # empty set market class dict, accessed by get_market_class_dict()
        MarketClassBase._market_class_tree_dict = dict()  # empty set market class tree dict accessed by get_market_class_tree()
        MarketClassBase._market_class_tree_dict_rc = dict()  # empty set market class tree dict with reg class leaves accessed by get_market_class_tree(by_reg_class=True)

        input_template_name = __name__
        input_template_version = 0.32
        input_template_columns = {'market_class_id', 'fueling_class', 'ownership_class'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

        if not template_errors:
            validation_dict = {'fueling_class': ['ICE', 'BEV', 'PHEV'],  #TODO: fueling class / powertrain type class..?
                               'ownership_class': ['private'],  # for now...
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            MarketClass._data = df.set_index('market_class_id').to_dict(orient='index')

            MarketClassBase.market_classes = df['market_class_id'].to_list()
            for mc in MarketClass.market_classes:
                MarketClassBase._market_class_dict[mc] = []

            MarketClassBase._market_class_tree_dict = MarketClass.parse_market_classes(df['market_class_id'])
            MarketClassBase._market_class_tree_dict_rc = MarketClass.parse_market_classes(df['market_class_id'],
                                                                                          by_reg_class=True)

        return template_errors


if __name__ == '__main__':

    __name__ = 'consumer.market_classes'

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        from omega_model.omega import init_user_definable_decomposition_attributes, get_module
        from producer.manufacturers import Manufacturer
        from producer.vehicles import VehicleFinal, DecompositionAttributes
        from producer.vehicle_annual_data import VehicleAnnualData

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)

        if not init_fail:
            from common.omega_functions import print_dict

            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            market_class_list = [
                'hauling.ICE',
                'hauling.BEV.bev300.base',
                'hauling.BEV.bev300.sport',
                'hauling.BEV.bev100',
                'non_hauling.ICE',
                'non_hauling.BEV',
            ]

            market_class_list = [
                'hauling.ICE',
                'hauling.BEV',
                'non_hauling.ICE',
                'non_hauling.BEV',
            ]

            market_class_dict = MarketClass.parse_market_classes(market_class_list)
            print_dict(market_class_dict)

            market_class_dict_rc = MarketClass.parse_market_classes(market_class_list, by_reg_class=True)
            print_dict(market_class_dict_rc)

            MarketClass.populate_market_classes(market_class_dict, 'hauling.ICE', 'F150')
            MarketClass.populate_market_classes(market_class_dict, 'hauling.ICE', 'Silverado')
            MarketClass.populate_market_classes(market_class_dict, 'hauling.BEV', 'Cybertruck')
            MarketClass.populate_market_classes(market_class_dict, 'non_hauling.ICE', '240Z')
            MarketClass.populate_market_classes(market_class_dict, 'non_hauling.BEV', 'Tesla3')
            MarketClass.populate_market_classes(market_class_dict, 'non_hauling.BEV', 'TeslaS')
            print_dict(market_class_dict)

            MarketClass.populate_market_classes(market_class_dict_rc, 'hauling.ICE.truck', 'F150')
            MarketClass.populate_market_classes(market_class_dict_rc, 'hauling.ICE.truck', 'Silverado')
            MarketClass.populate_market_classes(market_class_dict_rc, 'hauling.BEV.truck', 'Cybertruck')
            MarketClass.populate_market_classes(market_class_dict_rc, 'non_hauling.ICE.car', '240Z')
            MarketClass.populate_market_classes(market_class_dict_rc, 'non_hauling.ICE.car', 'Sentra')
            MarketClass.populate_market_classes(market_class_dict_rc, 'non_hauling.BEV.car', 'Tesla3')
            print_dict(market_class_dict_rc)

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)