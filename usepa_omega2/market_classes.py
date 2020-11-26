"""
market_classes.py
=================

"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *


def populate_market_classes(market_class_dict, market_class, obj):
    """

    :param market_class_dict: dict of dicts of market classes
    :param market_class: dot separated market class name e.g. 'hauling.BEV',
        possibly with reg class suffix e.g. 'non hauling.ICE.car' depending on the market_class_dict
    :param obj: object to place in a set in the appropriate leaf
    :return: modifies market_class_dict
    """
    substrs = market_class.split('.', maxsplit=1)
    prefix = substrs[0]
    suffix = substrs[1:]
    if not suffix:
        # end of the string
        if market_class_dict:
            # if dict not empty, add new entry
            market_class_dict[prefix].add(obj)
    else:
        if prefix in market_class_dict:
            # update existing dictionary
            populate_market_classes(market_class_dict[prefix], *suffix, obj)
        else:
            Exception()


def parse_market_classes(market_class_list, market_class_dict=None, by_reg_class=False):
    """
    Returns a nested dictionary of market classes from a dot-formatted list of market class names
    :param market_class_list: list of dot-separted market class names e.g. ['hauling.BEV', 'hauling.ICE'] etc
    :param market_class_dict: recursive input and also the output data structure
    :param by_reg_class: if true then leaves are sets in reg class dicts, otherwise leaves are sets by market segment
    :return: market_class_dict of dicts
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
                    for rc in reg_classes:
                        market_class_dict[prefix][rc] = set()
                else:
                    market_class_dict[prefix] = set()
            else:
                # create new dictionary
                if by_reg_class:
                    rc_dict = {prefix: dict()}
                    for rc in reg_classes:
                        rc_dict[prefix][rc] = set()
                    return rc_dict
                else:
                    return {prefix: set()}
        else:
            if prefix in market_class_dict:
                # update existing dictionary
                parse_market_classes(suffix, market_class_dict=market_class_dict[prefix], by_reg_class=by_reg_class)
            else:
                # new entry, create dictionary
                market_class_dict[prefix] = parse_market_classes(suffix, by_reg_class=by_reg_class)

    return market_class_dict


class MarketClass(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'market_classes'
    market_class_ID = Column('market_class_id', String, primary_key=True)
    fueling_class = Column(Enum(*fueling_classes, validate_strings=True))
    hauling_class = Column(Enum(*hauling_classes, validate_strings=True))
    ownership_class = Column(Enum(*ownership_classes, validate_strings=True))

    market_classes = ()  # tuple of market classes
    _market_class_dict = dict()  # empty set market class dict, accessed by get_market_class_dict()
    _market_class_tree_dict = dict()  # empty set market class tree dict accessed by get_market_class_tree()
    _market_class_tree_dict_rc = dict()  # empty set market class tree dict with reg class leaves accessed by get_market_class_tree(by_reg_class=True)

    @staticmethod
    def get_market_class_dict():
        import copy
        return copy.deepcopy(MarketClass._market_class_dict)

    @staticmethod
    def get_market_class_tree(by_reg_class=False):
        import copy
        if by_reg_class:
            return copy.deepcopy(MarketClass._market_class_tree_dict_rc)
        else:
            return copy.deepcopy(MarketClass._market_class_tree_dict)

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'market_classes'
        input_template_version = 0.0002
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
                        market_class_ID = df.loc[i, 'market_class_id'],
                        fueling_class=df.loc[i, 'fueling_class'],
                        hauling_class=df.loc[i, 'hauling_class'],
                        ownership_class=df.loc[i, 'ownership_class'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

                MarketClass.market_classes = tuple(df['market_class_id'].unique())
                for mc in MarketClass.market_classes:
                    MarketClass._market_class_dict[mc] = set()

                MarketClass._market_class_tree_dict = parse_market_classes(df['market_class_id'])
                MarketClass._market_class_tree_dict_rc = parse_market_classes(df['market_class_id'], by_reg_class=True)

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file, verbose=o2.options.verbose)

        if not init_fail:
            from omega_functions import print_dict

            dump_omega_db_to_csv(o2.options.database_dump_folder)

            market_class_list = [
                'hauling.ice',
                'hauling.bev.bev300.base',
                'hauling.bev.bev300.sport',
                'hauling.bev.bev100',
                'non_hauling.ice',
                'non_hauling.bev',
            ]

            market_class_list = [
                'hauling.ice',
                'hauling.bev',
                'non_hauling.ice',
                'non_hauling.bev',
            ]

            market_class_dict = parse_market_classes(market_class_list)
            print_dict(market_class_dict)

            market_class_dict_rc = parse_market_classes(market_class_list, by_reg_class=True)
            print_dict(market_class_dict_rc)

            populate_market_classes(market_class_dict, 'hauling.ice', 'F150')
            populate_market_classes(market_class_dict, 'hauling.ice', 'Silverado')
            populate_market_classes(market_class_dict, 'hauling.bev', 'Cybertruck')
            populate_market_classes(market_class_dict, 'non_hauling.ice', '240Z')
            populate_market_classes(market_class_dict, 'non_hauling.bev', 'Tesla3')
            populate_market_classes(market_class_dict, 'non_hauling.bev', 'TeslaS')
            print_dict(market_class_dict)

            populate_market_classes(market_class_dict_rc, 'hauling.ice.truck', 'F150')
            populate_market_classes(market_class_dict_rc, 'hauling.ice.truck', 'Silverado')
            populate_market_classes(market_class_dict_rc, 'hauling.bev.truck', 'Cybertruck')
            populate_market_classes(market_class_dict_rc, 'non_hauling.ice.car', '240Z')
            populate_market_classes(market_class_dict_rc, 'non_hauling.ice.car', 'Sentra')
            populate_market_classes(market_class_dict_rc, 'non_hauling.bev.car', 'Tesla3')
            print_dict(market_class_dict_rc)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)