"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""

import o2  # import global variables
from omega_functions import cartesian_prod
from usepa_omega2 import *
import numpy as np
import consumer

use_composite_vehicles = True

partition_dict = dict()
def partition(columns, max_values=[1.0], increment=0.01, min_level=0.01, verbose=False):
    """

    :param columns: number of columns or list of column names
    :param max_values: list of max values for groups of columns
    :param increment: increment from 0 to max_values
    :param min_level: minimum output value (max output value will be max_value - min_level)
    :param verbose: if True then print result
    :return: pandas Dataframe of result, rows of which add up to sum(max_values)
    """
    import sys

    if type(columns) is list:
        num_columns = len(columns)
    else:
        num_columns = columns
        columns = [i for i in range(num_columns)]

    partition_name = '%s_%s_%s_%s' % (columns, max_values, increment, min_level)

    if not partition_name in partition_dict:
        dfs = []
        for mv in max_values:
            members = []
            for i in range(num_columns):
                members.append(pd.DataFrame(np.arange(0, mv + increment, increment), columns=[columns[i]]))

            x = pd.DataFrame()
            for m in members:
                x = cartesian_prod(x, m)
                x = x[mv - x.sum(axis=1, numeric_only=True) >= -sys.float_info.epsilon]  # sum <= mv

            x = x[abs(x.sum(axis=1) - mv) <= sys.float_info.epsilon]
            x[x == 0] = min_level
            x[x == mv] = mv - min_level
            dfs.append(x)

        ans = pd.DataFrame()
        for df in dfs:
            ans = cartesian_prod(ans, df)

        if verbose:
            with pd.option_context('display.max_rows', None, 'display.max_columns', None):
                print(ans)

        ans = ans[abs(ans.sum(axis=1, numeric_only=True) - sum(max_values)) <= sys.float_info.epsilon]
        ans = ans.drop('_', axis=1)

        partition_dict[partition_name] = ans

    return partition_dict[partition_name]


def calculate_cert_target_co2_Mg(model_year, manufacturer_id):
    from vehicles import VehicleFinal
    return o2.session.query(func.sum(VehicleFinal.cert_target_CO2_Mg)). \
        filter(VehicleFinal.manufacturer_ID == manufacturer_id). \
        filter(VehicleFinal.model_year == model_year).scalar()


# placeholder for producer deemed generalized vehicle cost:
def calculate_generalized_cost(cost_factors):
    pass


sweep_list = ['ICE', 'BEV']
# sweep_list = ['hauling', 'non hauling']
# sweep_list = ['ICE', 'BEV', 'hauling', 'non hauling']
def create_tech_options_from_market_class_tree(calendar_year, market_class_dict, consumer_bev_share, parent='', verbose=False):
    """

    :param market_class_dict:
    :return:
    """
    child_df_list = []

    children = list(market_class_dict)

    for k in market_class_dict:
        if verbose:
            print('processing ' + k)
        if type(market_class_dict[k]) is dict:
            # process subtree
            child_df_list.append(create_tech_options_from_market_class_tree(calendar_year, market_class_dict[k], consumer_bev_share, parent=k,))
        else:
            # process leaf
            for new_veh in market_class_dict[k]:
                df = pd.DataFrame()

                if new_veh.fueling_class == 'ICE':
                    num_tech_options = o2.options.num_tech_options_per_ice_vehicle
                else:
                    num_tech_options = o2.options.num_tech_options_per_bev_vehicle

                if consumer_bev_share is None or new_veh.fueling_class == 'BEV':
                    if o2.options.allow_backsliding:
                        max_co2_gpmi = new_veh.get_max_co2_gpmi()
                    else:
                        max_co2_gpmi = new_veh.cert_CO2_grams_per_mile

                    co2_gpmi_options = np.linspace(
                        new_veh.get_min_co2_gpmi(),
                        max_co2_gpmi,
                        num=num_tech_options).tolist()
                else:  # ICE vehicle and consumer_bev_share available
                    if o2.options.allow_backsliding:
                        max_co2_gpmi = consumer_bev_share['veh_%d_co2_gpmi' % new_veh.vehicle_ID] * 1.1
                    else:
                        max_co2_gpmi = min(new_veh.cert_CO2_grams_per_mile,
                                           consumer_bev_share['veh_%d_co2_gpmi' % new_veh.vehicle_ID] * 1.1)

                    min_co2_gpmi = max(new_veh.get_min_co2_gpmi(),
                                       consumer_bev_share['veh_%d_co2_gpmi' % new_veh.vehicle_ID] * 0.9)

                    co2_gpmi_options = np.linspace(min_co2_gpmi, max_co2_gpmi, num=num_tech_options)

                tech_cost_options = new_veh.get_cost(co2_gpmi_options)

                df['veh_%d_co2_gpmi' % new_veh.vehicle_ID] = co2_gpmi_options
                df['veh_%d_cost_dollars' % new_veh.vehicle_ID] = tech_cost_options

                child_df_list.append(df)

    if parent:
        sales_share_column_names = ['producer_' + parent + '.' + c + '_share_frac' for c in children]
    else:
        sales_share_column_names = ['producer_' + c + '_share_frac' for c in children]

    if all(s in sweep_list for s in children) and consumer_bev_share is None:
        sales_share_df = partition(sales_share_column_names, increment=1/(o2.options.num_share_options-1), min_level=0.001)
    else:
        sales_share_df = pd.DataFrame()
        for c, cn in zip(children, sales_share_column_names):
            if consumer_bev_share is None or cn.replace('producer', 'consumer') not in consumer_bev_share:
                # maintain initial fleet market share (for now...)
                sales_share_df[cn] = [consumer.sales.demand_sales(calendar_year)[c] /
                                      consumer.sales.demand_sales(calendar_year)['total']]
            else:
                sales_share_df[cn] = [consumer_bev_share[cn.replace('producer', 'consumer')]]

    if verbose:
        print('combining ' + str(children))
    tech_combos_df = pd.DataFrame()
    for df in child_df_list:
        tech_combos_df = cartesian_prod(tech_combos_df, df)

    tech_share_combos_df = cartesian_prod(tech_combos_df, sales_share_df)

    return tech_share_combos_df


calendar_year_initial_vehicle_data = dict()
def run_compliance_model(manufacturer_ID, calendar_year, consumer_bev_share):

    manufacturer_new_vehicles, market_class_tree = get_initial_vehicle_data(calendar_year, manufacturer_ID)

    tech_share_combos_total = create_tech_options_from_market_class_tree(calendar_year, market_class_tree, consumer_bev_share)

    calculate_tech_share_combos_total(calendar_year, manufacturer_new_vehicles, tech_share_combos_total)

    # pick a winner!! (cheapest one where total_combo_credits_co2_megagrams >= 0 or least bad compliance option)
    winning_combo = select_winning_combo(tech_share_combos_total)

    import copy
    manufacturer_new_vehicles = copy.deepcopy(manufacturer_new_vehicles)

    # assign co2 values and sales to vehicles...
    for new_veh in manufacturer_new_vehicles:
        new_veh.cert_CO2_grams_per_mile = winning_combo['veh_%d_co2_gpmi' % new_veh.vehicle_ID]
        new_veh.initial_registered_count = winning_combo['veh_%d_sales' % new_veh.vehicle_ID]
        if use_composite_vehicles:
            new_veh.decompose()
        new_veh.set_new_vehicle_mfr_cost_dollars()
        new_veh.set_cert_target_CO2_Mg()
        new_veh.set_cert_CO2_Mg()

    return manufacturer_new_vehicles, winning_combo


def get_initial_vehicle_data(calendar_year, manufacturer_ID):
    from vehicles import VehicleFinal, Vehicle
    from market_classes import MarketClass, populate_market_classes

    if calendar_year not in calendar_year_initial_vehicle_data:
        # pull in last year's vehicles:
        manufacturer_prior_vehicles = o2.session.query(VehicleFinal). \
            filter(VehicleFinal.manufacturer_ID == manufacturer_ID). \
            filter(VehicleFinal.model_year == calendar_year - 1). \
            all()

        Vehicle.reset_vehicle_IDs()

        manufacturer_new_vehicles = []
        # update each vehicle and calculate compliance target for each vehicle
        for prior_veh in manufacturer_prior_vehicles:
            new_veh = Vehicle()
            new_veh.inherit_vehicle(prior_veh, model_year=calendar_year)
            manufacturer_new_vehicles.append(new_veh)

        # aggregate by market class / reg class
        mctrc = dict()
        for mc in MarketClass.market_classes:
            mctrc[mc] = {'car': [], 'truck': []}
        for new_veh in manufacturer_new_vehicles:
            mctrc[new_veh.market_class_ID][new_veh.reg_class_ID].append(new_veh)

        from vehicles import CompositeVehicle
        CompositeVehicle.reset_vehicle_IDs()
        composite_vehicles = []
        for mc in mctrc:
            for rc in reg_classes:
                if mctrc[mc][rc]:
                    cv = CompositeVehicle(mctrc[mc][rc])
                    composite_vehicles.append(cv)

        if use_composite_vehicles:
            manufacturer_new_vehicles = composite_vehicles

        # get empty market class tree
        market_class_tree = MarketClass.get_market_class_tree()
        # populate tree with vehicle objects
        for new_veh in manufacturer_new_vehicles:
            populate_market_classes(market_class_tree, new_veh.market_class_ID, new_veh)

        calendar_year_initial_vehicle_data[calendar_year] = {'manufacturer_new_vehicles': manufacturer_new_vehicles,
                                                             'market_class_tree': market_class_tree}
    else:
        manufacturer_new_vehicles = calendar_year_initial_vehicle_data[calendar_year]['manufacturer_new_vehicles']
        market_class_tree = calendar_year_initial_vehicle_data[calendar_year]['market_class_tree']
    return manufacturer_new_vehicles, market_class_tree


def finalize_production(calendar_year, manufacturer_ID, manufacturer_candidate_vehicles, winning_combo):
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import VehicleFinal

    manufacturer_new_vehicles = []

    if use_composite_vehicles:
        for cv in manufacturer_candidate_vehicles:
            for v in cv.vehicle_list:
                new_veh = VehicleFinal()
                new_veh.inherit_vehicle(v)
                manufacturer_new_vehicles.append(new_veh)
    else:
        for cv in manufacturer_candidate_vehicles:
            new_veh = VehicleFinal()
            new_veh.inherit_vehicle(cv)
            manufacturer_new_vehicles.append(new_veh)

    o2.session.add_all(manufacturer_new_vehicles)

    cert_target_co2_Mg = calculate_cert_target_co2_Mg(calendar_year, manufacturer_ID)

    ManufacturerAnnualData. \
        create_manufacturer_annual_data(calendar_year=calendar_year,
                                        manufacturer_ID=manufacturer_ID,
                                        cert_target_co2_Mg=cert_target_co2_Mg,
                                        cert_co2_Mg=winning_combo['total_combo_cert_co2_megagrams'],
                                        manufacturer_vehicle_cost_dollars=winning_combo['total_combo_cost_dollars'],
                                        bev_non_hauling_share_frac=winning_combo['producer_non hauling.BEV_share_frac'] *
                                                                   winning_combo['producer_non hauling_share_frac'],
                                        ice_non_hauling_share_frac=winning_combo['producer_non hauling.ICE_share_frac'] *
                                                                   winning_combo['producer_non hauling_share_frac'],
                                        bev_hauling_share_frac=winning_combo['producer_hauling.BEV_share_frac'] *
                                                               winning_combo['producer_hauling_share_frac'],
                                        ice_hauling_share_frac=winning_combo['producer_hauling.ICE_share_frac'] *
                                                               winning_combo['producer_hauling_share_frac'],
                                        )
    # tech_share_combos_total.to_csv('%stech_share_combos_total_%d.csv' % (o2.options.output_folder, calendar_year))
    # if not o2.options.verbose:
    #     # drop big ass table
    #     o2.session.execute('DROP TABLE tech_share_combos_total_%d' % calendar_year)
    #     # drop vehicle tech options tables
    #     for k, tables in vehicle_tech_options.items():
    #         for t in tables:
    #             o2.session.execute('DROP TABLE %s' % t)
    #     for k, tables in hauling_class_tech_combos.items():
    #         for t in tables:
    #             o2.session.execute('DROP TABLE %s' % t)
    # elif o2.options.slice_tech_combo_cloud_tables:
    #     # only preserve points within a range of target, to make a small ass table
    #     slice_width = 0.01 * cert_co2_Mg
    #     o2.session.execute(
    #         'DELETE FROM tech_share_combos_total_%d WHERE total_combo_cert_co2_megagrams NOT BETWEEN %f AND %f' %
    #         (calendar_year, cert_co2_Mg - slice_width, cert_co2_Mg + slice_width))

    o2.session.flush()


def calculate_tech_share_combos_total(calendar_year, manufacturer_new_vehicles, tech_share_combos_total):
    total_sales = consumer.sales.demand_sales(calendar_year)['total']
    total_target_co2_Mg = 0
    total_cert_co2_Mg = 0
    total_cost_dollars = 0
    for new_veh in manufacturer_new_vehicles:
        # assign sales to vehicle based on market share fractions
        market_class = new_veh.market_class_ID
        substrs = market_class.split('.')
        chain = []
        for i in range(len(substrs)):
            str = 'producer_'
            for j in range(i + 1):
                str = str + substrs[j] + '.' * (j != i)
            str = str + '_share_frac'
            chain.append(str)
        vehicle_sales = total_sales
        for c in chain:
            vehicle_sales = vehicle_sales * tech_share_combos_total[c]
        tech_share_combos_total['veh_%d_sales' % new_veh.vehicle_ID] = vehicle_sales

        # calculate vehicle total cost
        vehicle_total_cost_dollars = vehicle_sales * tech_share_combos_total['veh_%d_cost_dollars' % new_veh.vehicle_ID]
        tech_share_combos_total['veh_%d_total_cost_dollars' % new_veh.vehicle_ID] = vehicle_total_cost_dollars

        # calculate cert and target Mg for the vehicle
        co2_gpmi = tech_share_combos_total['veh_%d_co2_gpmi' % new_veh.vehicle_ID]

        cert_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(new_veh, co2_gpmi_variants=co2_gpmi,
                                                                    sales_variants=vehicle_sales)
        target_co2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(new_veh,
                                                                        sales_variants=vehicle_sales)
        tech_share_combos_total['veh_%d_cert_co2_megagrams' % new_veh.vehicle_ID] = cert_co2_Mg
        tech_share_combos_total['veh_%d_target_co2_megagrams' % new_veh.vehicle_ID] = target_co2_Mg
        # update totals
        total_target_co2_Mg = total_target_co2_Mg + target_co2_Mg
        total_cert_co2_Mg = total_cert_co2_Mg + cert_co2_Mg
        total_cost_dollars = total_cost_dollars + vehicle_total_cost_dollars

    tech_share_combos_total['total_combo_target_co2_megagrams'] = total_target_co2_Mg
    tech_share_combos_total['total_combo_cert_co2_megagrams'] = total_cert_co2_Mg
    tech_share_combos_total['total_combo_cost_dollars'] = total_cost_dollars
    tech_share_combos_total['total_combo_credits_co2_megagrams'] = total_target_co2_Mg - total_cert_co2_Mg


def select_winning_combo(tech_share_combos_total):
    # tech_share_combos_total = tech_share_combos_total.drop_duplicates('total_combo_credits_co2_megagrams')
    mini_df = pd.DataFrame()
    mini_df['total_combo_credits_co2_megagrams'] = tech_share_combos_total['total_combo_credits_co2_megagrams']
    mini_df['total_combo_cost_dollars'] = tech_share_combos_total['total_combo_cost_dollars']

    potential_winners = mini_df[mini_df['total_combo_credits_co2_megagrams'] >= 0]
    if not potential_winners.empty:
        winning_combo = tech_share_combos_total.loc[potential_winners['total_combo_cost_dollars'].idxmin()]
    else:
        winning_combo = tech_share_combos_total.loc[mini_df['total_combo_credits_co2_megagrams'].idxmax()]

    return winning_combo.copy()


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
