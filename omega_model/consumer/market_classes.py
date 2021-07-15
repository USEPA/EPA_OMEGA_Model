"""

**Routines to implement market-class related functionality.**

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


def populate_market_classes(market_class_dict, market_class_id, obj):
    """
    Populate the leaves of a market class tree implemented as a dict (or dict of dicts) where the keys represent market
    categories and the leaves are lists of objects grouped by market class.

    Args:
        market_class_dict (dict): dict of dicts of market classes
        market_class_id (str): dot separated market class name e.g. 'hauling.BEV', possibly with reg class suffix e.g. 'non_hauling.ICE.car' depending on the market_class_dict
        obj (object): object to place in a set in the appropriate leaf

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
            populate_market_classes(market_class_dict[prefix], *suffix, obj)
        else:
            Exception()


def parse_market_classes(market_class_list, market_class_dict=None, by_reg_class=False):
    """
    Returns a nested dictionary of market classes from a dot-formatted list of market class names.

    Args:
        market_class_list ([strs]): list of dot-separted market class names e.g. ['hauling.BEV', 'hauling.ICE'] etc
        market_class_dict (dict, dict of dicts): recursive input and also the output data structure
        by_reg_class (bool): if true then leaves are lists in reg class dicts, otherwise leaves are lists by market segment

    Returns:
        market_class_dict

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
                        market_class_dict[prefix][rc] = []
                else:
                    market_class_dict[prefix] = []
            else:
                # create new dictionary
                if by_reg_class:
                    rc_dict = {prefix: dict()}
                    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                        rc_dict[prefix][rc] = []
                    return rc_dict
                else:
                    return {prefix: []}
        else:
            if prefix in market_class_dict:
                # update existing dictionary
                parse_market_classes(suffix, market_class_dict=market_class_dict[prefix], by_reg_class=by_reg_class)
            else:
                # new entry, create dictionary
                market_class_dict[prefix] = parse_market_classes(suffix, by_reg_class=by_reg_class)

    return market_class_dict


cache = dict()


class MarketClass(SQABase, OMEGABase):
    """
    Loads market class definition data and provides market-class-related functionality.

    """
    # --- database table properties ---
    __tablename__ = 'market_classes'
    market_class_ID = Column('market_class_id', String, primary_key=True)  #: market class id, e.g. 'non_hauling.ICE'
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))  #: fueling class, e.g. 'ICE', 'BEV'
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))  #: hauling class, e.g. 'hauling'
    ownership_class = Column(Enum(*ownership_classes, validate_strings=True))  #: ownership class, e.g. 'private'
    producer_generalized_cost_fuel_years = Column(Float)  #: years of fuel consumption, for producer generalized cost calcs
    producer_generalized_cost_annual_vmt = Column(Float)  #: annual vehicle miles travelled, for producer generalized cost calcs

    market_classes = ()  #: tuple of market classes
    _market_class_dict = dict()  # empty set market class dict, accessed by get_market_class_dict()
    _market_class_tree_dict = dict()  # empty set market class tree dict accessed by get_market_class_tree()
    _market_class_tree_dict_rc = dict()  # empty set market class tree dict with reg class leaves accessed by get_market_class_tree(by_reg_class=True)

    @staticmethod
    def get_market_class_dict():
        """
        Get a copy of the market class dict with empty lists for each market class.

        Returns:
            A copy of the market class dict.

        """
        import copy
        return copy.deepcopy(MarketClass._market_class_dict)

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
        import copy
        if by_reg_class:
            return copy.deepcopy(MarketClass._market_class_tree_dict_rc)
        else:
            return copy.deepcopy(MarketClass._market_class_tree_dict)

    @staticmethod
    def get_vehicle_market_class(vehicle):
        """
        Get vehicle market class ID based on vehicle characteristics

        :param vehicle: a vehicles.VehicleFinal object
        :return: the vehicle's market class ID based on vehicle characteristics
        """

        if vehicle.hauling_class == 'hauling' and vehicle.electrification_class == 'EV':
            market_class_ID = 'hauling.BEV'
            non_responsive_market_group = 'hauling'
        elif vehicle.hauling_class == 'hauling' and vehicle.electrification_class != 'EV':
            market_class_ID = 'hauling.ICE'
            non_responsive_market_group = 'hauling'
        elif vehicle.electrification_class == 'EV':
            market_class_ID = 'non_hauling.BEV'
            non_responsive_market_group = 'non_hauling'
        else:
            market_class_ID = 'non_hauling.ICE'
            non_responsive_market_group = 'non_hauling'

        return market_class_ID, non_responsive_market_group

    @staticmethod
    def get_producer_generalized_cost_attributes(market_class_id, attribute_types):
        """

        Args:
            market_class_id:
            attribute_types:

        Returns:

        """
        cache_key = '%s_%s' % (market_class_id, attribute_types)

        if cache_key not in cache:
            if type(attribute_types) is not list:
                attribute_types = [attribute_types]

            attrs = MarketClass.get_class_attributes(attribute_types)

            result = omega_globals.session.query(*attrs). \
                filter(MarketClass.market_class_ID == market_class_id).all()[0]

            if len(attribute_types) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
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

        MarketClass._market_class_dict = dict()  # empty set market class dict, accessed by get_market_class_dict()
        MarketClass._market_class_tree_dict = dict()  # empty set market class tree dict accessed by get_market_class_tree()
        MarketClass._market_class_tree_dict_rc = dict()  # empty set market class tree dict with reg class leaves accessed by get_market_class_tree(by_reg_class=True)

        input_template_name = 'market_classes'
        input_template_version = 0.2
        input_template_columns = {'market_class_id', 'hauling_class', 'fueling_class', 'ownership_class',
                                  'producer_generalized_cost_fuel_years', 'producer_generalized_cost_annual_vmt'}

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
                        market_class_ID=df.loc[i, 'market_class_id'],
                        fueling_class=df.loc[i, 'fueling_class'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        ownership_class=df.loc[i, 'ownership_class'],
                        producer_generalized_cost_fuel_years=df.loc[i, 'producer_generalized_cost_fuel_years'],
                        producer_generalized_cost_annual_vmt=df.loc[i, 'producer_generalized_cost_annual_vmt'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                MarketClass.market_classes = list(df['market_class_id'].unique())
                MarketClass.market_classes.sort()
                for mc in MarketClass.market_classes:
                    MarketClass._market_class_dict[mc] = []

                MarketClass._market_class_tree_dict = parse_market_classes(df['market_class_id'])
                MarketClass._market_class_tree_dict_rc = parse_market_classes(df['market_class_id'], by_reg_class=True)

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()

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
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file, verbose=omega_globals.options.verbose)

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

            market_class_dict = parse_market_classes(market_class_list)
            print_dict(market_class_dict)

            market_class_dict_rc = parse_market_classes(market_class_list, by_reg_class=True)
            print_dict(market_class_dict_rc)

            populate_market_classes(market_class_dict, 'hauling.ICE', 'F150')
            populate_market_classes(market_class_dict, 'hauling.ICE', 'Silverado')
            populate_market_classes(market_class_dict, 'hauling.BEV', 'Cybertruck')
            populate_market_classes(market_class_dict, 'non_hauling.ICE', '240Z')
            populate_market_classes(market_class_dict, 'non_hauling.BEV', 'Tesla3')
            populate_market_classes(market_class_dict, 'non_hauling.BEV', 'TeslaS')
            print_dict(market_class_dict)

            populate_market_classes(market_class_dict_rc, 'hauling.ICE.truck', 'F150')
            populate_market_classes(market_class_dict_rc, 'hauling.ICE.truck', 'Silverado')
            populate_market_classes(market_class_dict_rc, 'hauling.BEV.truck', 'Cybertruck')
            populate_market_classes(market_class_dict_rc, 'non_hauling.ICE.car', '240Z')
            populate_market_classes(market_class_dict_rc, 'non_hauling.ICE.car', 'Sentra')
            populate_market_classes(market_class_dict_rc, 'non_hauling.BEV.car', 'Tesla3')
            print_dict(market_class_dict_rc)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)