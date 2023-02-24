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

    market_categories = ['ICE', 'BEV', 'sedan_wagon_r1nonzev', 'cuv_suv_van_r1nonzev', 'pickup_r1nonzev', 'sedan_wagon_r2zev', 'cuv_suv_van_r2zev', 'pickup_r2zev']  #: overall market categories
    responsive_market_categories = ['ICE', 'BEV']  #: market categories that have consumer response (i.e. price -> sales)
    non_responsive_market_categories = ['sedan_wagon_r1nonzev', 'cuv_suv_van_r1nonzev', 'pickup_r1nonzev', 'sedan_wagon_r2zev', 'cuv_suv_van_r2zev', 'pickup_r2zev']  #: market categories that do not have consumer response

    @staticmethod
    def get_vehicle_market_class(vehicle):
        """
        Get vehicle market class ID based on vehicle characteristics

        Args:
            vehicle (VehicleFinal): the vehicle to determine the market class of

        Returns:
            The vehicle's market class ID based on vehicle characteristics.

        """

        if vehicle.body_style == 'sedan_wagon_r1nonzev':
            if vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
                market_class_id = 'sedan_wagon_r1nonzev.BEV'
            else:
                market_class_id = 'sedan_wagon_r1nonzev.ICE'
        elif vehicle.body_style == 'cuv_suv_van_r1nonzev':
            if vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
                market_class_id = 'cuv_suv_van_r1nonzev.BEV'
            else:
                market_class_id = 'cuv_suv_van_r1nonzev.ICE'
        elif vehicle.body_style == 'pickup_r1nonzev':
            if vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
                market_class_id = 'pickup_r1nonzev.BEV'
            else:
                market_class_id = 'pickup_r1nonzev.ICE'
        elif vehicle.body_style == 'sedan_wagon_r2zev':
            if vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
                market_class_id = 'sedan_wagon_r2zev.BEV'
            else:
                market_class_id = 'sedan_wagon_r2zev.ICE'
        elif vehicle.body_style == 'cuv_suv_van_r2zev':
            if vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
                market_class_id = 'cuv_suv_van_r2zev.BEV'
            else:
                market_class_id = 'cuv_suv_van_r2zev.ICE'
        elif vehicle.body_style == 'pickup_r2zev':
            if vehicle.base_year_powertrain_type in ['BEV', 'FCV']:
                market_class_id = 'pickup_r2zev.BEV'
            else:
                market_class_id = 'pickup_r2zev.ICE'
        else:
            1==1

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
        if 'sedan_wagon_r1nonzev' in market_class_id.split('.'):
            return 'sedan_wagon_r1nonzev'
        elif 'cuv_suv_van_r1nonzev' in market_class_id.split('.'):
            return 'cuv_suv_van_r1nonzev'
        elif 'pickup_r1nonzev' in market_class_id.split('.'):
            return 'pickup_r1nonzev'
        elif 'sedan_wagon_r2zev' in market_class_id.split('.'):
            return 'sedan_wagon_r2zev'
        elif 'cuv_suv_van_r2zev' in market_class_id.split('.'):
            return 'cuv_suv_van_r2zev'
        elif 'pickup_r2zev' in market_class_id.split('.'):
            return 'pickup_r2zev'
        else:
            return ''

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
        input_template_version = 0.1
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

    __name__ = 'consumer.market_classes_body_style_zevregion'

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)