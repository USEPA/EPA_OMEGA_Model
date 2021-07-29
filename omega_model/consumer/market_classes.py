"""

**Routines to implement market-class related functionality.**

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents characteristics of the consumer module's market classes.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,market_classes,input_template_version:,0.3

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,hauling_class,fueling_class,ownership_class
        non_hauling.BEV,non_hauling,BEV,private
        hauling.ICE,hauling,ICE,private

Data Column Name and Description

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:hauling_class:
    Market class hauling class, e.g. 'hauling', 'non_hauling'

:fueling_class:
    Market class fueling class, e.g. 'BEV', 'ICE'

:ownership_class:
    Market class ownership class, e.g. 'private', 'shared'

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


cache = dict()


class MarketClass(OMEGABase, SQABase, MarketClassBase):
    """
    Loads market class definition data and provides market-class-related functionality.

    """
    # --- database table properties ---
    __tablename__ = 'market_classes'
    market_class_id = Column('market_class_id', String, primary_key=True)  #: market class id, e.g. 'non_hauling.ICE'
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))  #: fueling class, e.g. 'ICE', 'BEV'
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))  #: hauling class, e.g. 'hauling'
    ownership_class = Column(Enum(*ownership_classes, validate_strings=True))  #: ownership class, e.g. 'private'

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
        if vehicle.hauling_class == 'hauling' and vehicle.electrification_class == 'EV':
            market_class_id = 'hauling.BEV'
            non_responsive_market_group = 'hauling'
        elif vehicle.hauling_class == 'hauling' and vehicle.electrification_class != 'EV':
            market_class_id = 'hauling.ICE'
            non_responsive_market_group = 'hauling'
        elif vehicle.electrification_class == 'EV':
            market_class_id = 'non_hauling.BEV'
            non_responsive_market_group = 'non_hauling'
        else:
            market_class_id = 'non_hauling.ICE'
            non_responsive_market_group = 'non_hauling'

        return market_class_id, non_responsive_market_group

    @staticmethod
    # override this method in the user-defined MarketClass
    def get_non_responsive_market_category(market_class_id):
        """
        Returns the non-responsive market category of the given market class ID

        Args:
            market_class_id (str): market class ID, e.g. 'non_hauling.ICE'

        Returns:
            The non-responsive market category of the given market class ID

        """
        if 'non_hauling' in market_class_id.split('.'):
            return 'non_hauling'
        else:
            return 'hauling'

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
        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        MarketClassBase._market_class_dict = dict()  # empty set market class dict, accessed by get_market_class_dict()
        MarketClassBase._market_class_tree_dict = dict()  # empty set market class tree dict accessed by get_market_class_tree()
        MarketClassBase._market_class_tree_dict_rc = dict()  # empty set market class tree dict with reg class leaves accessed by get_market_class_tree(by_reg_class=True)

        input_template_name = __name__
        input_template_version = 0.31
        input_template_columns = {'market_class_id', 'hauling_class', 'fueling_class', 'ownership_class'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version, verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(MarketClass(
                        market_class_id=df.loc[i, 'market_class_id'],
                        fueling_class=df.loc[i, 'fueling_class'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        ownership_class=df.loc[i, 'ownership_class'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                MarketClassBase.market_classes = list(df['market_class_id'].unique())
                MarketClassBase.market_classes.sort()
                for mc in MarketClass.market_classes:
                    MarketClassBase._market_class_dict[mc] = []

                MarketClassBase._market_class_tree_dict = MarketClass.parse_market_classes(df['market_class_id'])
                MarketClassBase._market_class_tree_dict_rc = MarketClass.parse_market_classes(df['market_class_id'], by_reg_class=True)

        return template_errors


if __name__ == '__main__':

    __name__ = 'consumer.market_classes'

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


        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += MarketClass.init_from_file(omega_globals.options.market_classes_file, verbose=omega_globals.options.verbose)

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
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)