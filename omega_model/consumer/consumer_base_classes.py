"""
**A set of base classes used to define the program interface(s) and to serve as templates for user-defined classes**

Ordinarily these classes might be implemented as Python abstract classes but abstract classes cause issues when
combined with SQLAlchemy base classes, so the implementation here is a workaround - if a child class fails to implement
one of the required methods, the class will throw a runtime Exception or return an error message.

"""

import inspect

from omega_model import *


class ReregistrationBase:
    """
    **Load and provide access to vehicle re-registration data by model year, market class ID and age.**

    """
    @staticmethod
    def get_reregistered_proportion(model_year, market_class_id, age):
        """
        Get vehicle re-registered proportion [0..1] by market class and age.

        Args:
            model_year (int): the model year of the re-registration data
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            Re-registered proportion [0..1]

        """
        raise Exception('**Attempt to call abstract method ReregistrationBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method ReregistrationBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class AnnualVMTBase:
    """
    **Loads and provides access to annual Vehicle Miles Travelled by calendar year, market class, and age.**

    """

    @staticmethod
    def get_vmt(calendar_year, market_class_id, age):
        """
        Get vehicle miles travelled by calendar year, market class and age.

        Args:
            calendar_year (int): calendar year of the VMT data
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            (float) Annual vehicle miles travelled.

        """
        raise Exception('**Attempt to call abstract method OnroadVMT.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method OnroadVMT.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class SalesShareBase:
    """
    Class to calculate absolute market shares by market class

    """

    @staticmethod
    def calc_shares(calendar_year, compliance_id, producer_decision, market_class_data, mc_parent, mc_pair):
        """
        Determine consumer desired market shares for the given vehicles, their costs, etc.  Relative shares are first
        calculated within non-responsive market categories then converted to absolute shares.

        Args:
            calendar_year (int): calendar year to calculate market shares in
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            producer_decision (Series): selected producer compliance option
            market_class_data (DataFrame): DataFrame with 'average_fuel_price_MC',
                'average_modified_cross_subsidized_price_MC', 'average_co2e_gpmi_MC', 'average_kwh_pmi_MC'
                columns, where MC = market class ID
            mc_parent (str): e.g. '' for the total market, 'hauling' or 'non_hauling', etc
            mc_pair ([strs]): e.g. '['hauling', 'non_hauling'] or ['hauling.ICE', 'hauling.BEV'], etc

        Returns:
            A copy of ``market_class_data`` with demanded ICE/BEV share columns by market class, e.g.
            'consumer_share_frac_MC', 'consumer_abs_share_frac_MC', and 'consumer_generalized_cost_dollars_MC' where
            MC = market class ID

        """
        raise Exception('**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def save_calibration(filename):
        """
            Save calibration data (if necessary) that aligns reference session market shares with context

        Args:
            filename (str): name of the calibration file

        """
        raise Exception('**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def store_producer_decision_and_response(producer_decision_and_response):
        """
            Store producer decision and response (if necessary) for reference in future years

        Args:
            producer_decision_and_response (Series): producer decision and consumer response

        """
        raise Exception('**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def calc_base_year_data(base_year_vehicles_df):
        """
            Calculate base year data (if necessary) such as sales-weighted curbweight, etc, if needed for reference
            in future years

        Args:
            base_year_vehicles_df (DataFrame): base year vehicle data

        """
        raise Exception('**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class MarketClassBase:
    """
    Loads market class definition data and provides market-class-related functionality.

    """

    market_classes = ()  #: tuple of market classes
    _market_class_dict = dict()  # empty set market class dict, accessed by get_market_class_dict()
    _market_class_tree_dict = dict()  # empty set market class tree dict accessed by get_market_class_tree()
    _market_class_tree_dict_rc = dict()  # empty set market class tree dict with reg class leaves accessed by get_market_class_tree(by_reg_class=True)

    market_categories = []
    responsive_market_categories = []
    non_responsive_market_categories = []
    electrified_market_categories = []
    linked_market_classes = dict()

    @staticmethod
    def get_linestyle(varname):
        """

        Args:
            varname (str): variable name, e.g. 'sedan_wagon.ICE', 'BEV', etc

        Returns:
            dict of linestyle arguments

        For colors see: https://matplotlib.org/stable/gallery/color/named_colors.html
        For linestyles see: https://matplotlib.org/stable/gallery/lines_bars_and_markers/linestyles.html
        """
        style_dict = {'marker': '.', 'linestyle': '-'}

        return style_dict

    @staticmethod
    def parse_market_classes(market_class_list, market_class_dict=None, by_reg_class=False):
        """
        Returns a nested dictionary of market classes from a dot-formatted list of market class names.

        Args:
            market_class_list ([strs]): list of dot-separted market class names e.g. ['hauling.BEV', 'hauling.ICE'] etc
            market_class_dict (dict, dict of dicts): recursive input and also the output data structure
            by_reg_class (bool): if true then leaves are lists in reg class dicts,
                otherwise leaves are lists by market segment

        Returns:
            Market class tree represented as a dict or dict of dicts, with an empty list at each leaf.
            e.g. ``{'non_hauling': {'BEV': [], 'ICE': []}, 'hauling': {'BEV': [], 'ICE': []}}``

        """
        if market_class_dict is None:
            market_class_dict = dict()
        for market_class in market_class_list:
            substrs = market_class.split('.', maxsplit=1)
            prefix = substrs[0]
            suffix = substrs[1:]
            if not suffix:
                # end of the string
                if market_class_dict:
                    # if dict not empty, add new entry
                    if by_reg_class:
                        market_class_dict[prefix] = dict()
                        for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                            market_class_dict[prefix][rc] = {'ALT': [], 'NO_ALT': []}
                    else:
                        market_class_dict[prefix] = {'ALT': [], 'NO_ALT': []}
                else:
                    # create new dictionary
                    if by_reg_class:
                        rc_dict = {prefix: dict()}
                        for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                            rc_dict[prefix][rc] = {'ALT': [], 'NO_ALT': []}
                        return rc_dict
                    else:
                        return {prefix: {'ALT': [], 'NO_ALT': []}}
            else:
                if prefix in market_class_dict:
                    # update existing dictionary
                    MarketClassBase.parse_market_classes(suffix, market_class_dict=market_class_dict[prefix],
                                                         by_reg_class=by_reg_class)
                else:
                    # new entry, create dictionary
                    market_class_dict[prefix] = MarketClassBase.parse_market_classes(suffix, by_reg_class=by_reg_class)

        return market_class_dict

    @staticmethod
    def populate_market_classes(market_class_dict, market_class_id, obj):
        """
        Populate the leaves of a market class tree implemented as a dict (or dict of dicts) where the keys
        represent market categories and the leaves are lists of objects grouped by market class.

        Args:
            market_class_dict (dict): dict of dicts of market classes
            market_class_id (str): dot separated market class name e.g. 'hauling.BEV', possibly with reg class suffix
                e.g. 'non_hauling.ICE.car' depending on the market_class_dict
            obj (obj): object to place in a list in the appropriate leaf, as in a CompositeVehicle

        Returns:
            Nothing, modifies ``market_class_dict`` data

        """
        substrs = market_class_id.split('.', maxsplit=1)
        prefix = substrs[0]
        suffix = substrs[1:]
        if not suffix:
            # end of the string
            if market_class_dict:
                # if dict not empty, add new entry
                market_class_dict[prefix].append(obj)
        else:
            if prefix in market_class_dict:
                # update existing dictionary
                MarketClassBase.populate_market_classes(market_class_dict[prefix], *suffix, obj)
            else:
                Exception()

    @staticmethod
    def get_market_class_dict():
        """
        Get a copy of the market class dict with an empty list for each market class.

        Returns:
            A copy of the market class dict.

        """
        return copy.deepcopy(MarketClassBase._market_class_dict)

    @staticmethod
    def get_market_class_tree(by_reg_class=False):
        """
        Get a copy of a hierarchical market class dict with empty lists for each market class or by regulatory
        class within the market class.

        Args:
            by_reg_class (bool): if True then return a tree by reg class within market class.

        Returns:
            A copy of the appropriate hierarchical market class dict.

        """
        if by_reg_class:
            return copy.deepcopy(MarketClassBase._market_class_tree_dict_rc)
        else:
            return copy.deepcopy(MarketClassBase._market_class_tree_dict)

    @staticmethod
    # override this method in the user-defined MarketClass
    def get_vehicle_market_class(vehicle):
        """
        Get vehicle market class ID based on vehicle characteristics

        Args:
            vehicle (Vehicle): the vehicle to determine the market class of

        Returns:
            The vehicle's market class ID based on vehicle characteristics.

        """
        raise Exception('**Attempt to call abstract method MarketClassBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    # override this method in the user-defined MarketClass
    def get_non_responsive_market_category(market_class_id):
        """
        Returns the non-responsive market category of the given market class ID

        Args:
            market_class_id (str): market class ID, e.g. 'hauling.ICE'

        Returns:
            The non-responsive market category of the given market class ID

        """
        raise Exception('**Attempt to call abstract method MarketClassBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    # override this method in the user-defined MarketClass
    def validate_market_class_id(market_class_id):
        """
        Validate market class ID

        Args:
            market_class_id (str): market class ID, e.g. 'hauling.ICE'

        Returns:
            Error message in a list if market_class_id is not valid

        """
        raise Exception('**Attempt to call abstract method MarketClassBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    # override this method in the user-defined MarketClass
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        return ['**Attempt to call abstract method MarketClassBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]
