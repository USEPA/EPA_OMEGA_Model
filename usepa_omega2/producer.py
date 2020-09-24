"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""

import o2  # import global variables
from usepa_omega2 import *

import numpy as np

import consumer


def unique(vector):
    """

    :param vector:
    :return:
    """
    indexes = np.unique(vector, return_index=True)[1]
    return [vector[index] for index in sorted(indexes)]

partition_dict = dict()
def partition(num_columns, num_levels, min_level=0.001, verbose=False):
    """
    Returns a set of columns, the rows of which add up to 1.0, with num_levels between 0-1
    ex: >>> partition(num_columns=2, num_levels=3, verbose=True)
            1.00	0.00
            0.50	0.50
            0.00	1.00

    :param num_columns: number of columns in the output
    :param num_levels: number of values from 0-1
    :param verbose: if True then result is printed to the console
    :return: a set of columns, the rows of which add up to 1.0
    """

    partition_name = '%d_%d_%s' % (num_columns, num_levels, min_level)

    if not partition_name in partition_dict:
        from pyDOE2 import fullfact

        permutations = np.minimum(1 - min_level, np.maximum(min_level, fullfact([num_levels] * num_columns) / (num_levels - 1)))
        valid_combinations = np.array([permutation for permutation in permutations if sum(permutation) == 1.0])

        if verbose:
            for i in valid_combinations:
                s = ''
                for e in i:
                    s = s + '\t%.3f' % e
                print(s)

        partition_dict[partition_name] = valid_combinations.transpose()

    return partition_dict[partition_name]


def cartesian_prod(left_df, right_df):
    """
    Calculate cartesian product of the dataframe rows

    :param left_df: 'left' dataframe
    :param right_df: 'right' dataframe
    :return: cartesian product of the dataframe rows
    """
    import pandas as pd

    if left_df.empty:
        return right_df
    else:
        if not '_' in left_df:
            left_df['_'] = 1

        if not '_' in right_df:
            right_df['_'] = 1

        leftXright = pd.merge(left_df, right_df, on='_')  # .drop('_', axis=1)

        # left_df.drop('_', axis=1, inplace=True)
        # right_df.drop('_', axis=1, inplace=True, errors='ignore')

        return leftXright


def inherit_vehicles(from_year, to_year, manufacturer_id):
    # this works, but ignores annual data like initial registered count (needs to be joined from vehicle_annual_data)
    # which will be fine when are getting sales from the consumer module or creating them as part of the unconstrained
    # full factorial tech combos
    cn = sql_get_column_names('vehicles', exclude='vehicle_id')
    o2.session.execute('CREATE TABLE new_vehicles AS SELECT %s FROM vehicles \
                     WHERE model_year==%d AND manufacturer_id=="%s"' % (cn, from_year, manufacturer_id))
    o2.session.execute('UPDATE new_vehicles SET model_year=%d' % to_year)
    o2.session.execute('INSERT INTO vehicles (%s) SELECT %s FROM new_vehicles' % (cn, cn))
    o2.session.execute('DROP TABLE new_vehicles')


def calculate_cert_target_co2_Mg(model_year, manufacturer_id):
    from vehicles import Vehicle
    return o2.session.query(func.sum(Vehicle.cert_target_CO2_Mg)). \
        filter(Vehicle.manufacturer_ID == manufacturer_id). \
        filter(Vehicle.model_year == model_year).scalar()


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

    children = [k for k in market_class_dict]
    num_children = len(children)

    for k in market_class_dict:
        if verbose:
            print('processing ' + k)
        if type(market_class_dict[k]) is dict:
            # process subtree
            child_df_list.append(create_tech_options_from_market_class_tree(calendar_year, market_class_dict[k], consumer_bev_share, parent=k,))
        else:
            # process leaf
            from cost_curves import CostCurve
            for new_veh in market_class_dict[k]:
                df = pd.DataFrame()

                if o2.options.allow_backsliding:
                    max_co2_gpmi = CostCurve.get_max_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year)
                else:
                    max_co2_gpmi = new_veh.cert_CO2_grams_per_mile

                if new_veh.fueling_class == 'ICE':
                    num_tech_options = o2.options.num_tech_options_per_ice_vehicle
                else:
                    num_tech_options = o2.options.num_tech_options_per_bev_vehicle

                co2_gpmi_options = np.linspace(
                    CostCurve.get_min_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year),
                    max_co2_gpmi,
                    num=num_tech_options).tolist()

                tech_cost_options = CostCurve.get_cost(cost_curve_class=new_veh.cost_curve_class,
                                                       model_year=new_veh.model_year,
                                                       target_co2_gpmi=co2_gpmi_options)

                df['veh_%d_co2_gpmi' % new_veh.vehicle_ID] = co2_gpmi_options
                df['veh_%d_cost_dollars' % new_veh.vehicle_ID] = tech_cost_options

                child_df_list.append(df)

    if all(s in sweep_list for s in children):
        sales_share_frac = partition(num_children, o2.options.num_share_options)
    else:
        sales_share_frac = []  # [[i] for i in [1/num_children] * num_children] # assume equal shares between children (for now...)
        for c in children:
            # maintain initial fleet market share (for now...)
            sales_share_frac.append([consumer.sales.demand_sales(calendar_year)[c] /
                                     consumer.sales.demand_sales(calendar_year)['total']])

    sales_share_df = pd.DataFrame()
    i = 0
    for c in children:
        if parent:
            if consumer_bev_share:
                if c == 'BEV':
                    sales_share_df[parent + '.' + c + ' share_frac'] = [consumer_bev_share]
                else:
                    sales_share_df[parent + '.' + c + ' share_frac'] = [1-consumer_bev_share]
            else:
                sales_share_df[parent + '.' + c + ' share_frac'] = sales_share_frac[i]
        else:
            sales_share_df[c + ' share_frac'] = sales_share_frac[i]
        i = i + 1

    if verbose:
        print('combining ' + str(children))
    tech_combos_df = pd.DataFrame()
    for df in child_df_list:
        tech_combos_df = cartesian_prod(tech_combos_df, df)

    tech_share_combos_df = cartesian_prod(tech_combos_df, sales_share_df)

    return tech_share_combos_df


def run_compliance_model(manufacturer_ID, calendar_year, consumer_bev_share):
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from market_classes import MarketClass, populate_market_classes, print_market_class_dict

    from consumer.stock import prior_year_stock_registered_count, prior_year_stock_vmt, age0_stock_vmt

    # pull in last year's vehicles:
    manufacturer_prior_vehicles = o2.session.query(Vehicle). \
        filter(Vehicle.manufacturer_ID == manufacturer_ID). \
        filter(Vehicle.model_year == calendar_year - 1). \
        all()

    # TODO: aggregate...? By market class...? Or not....? Or only for USA Motors?
    # TODO: aggregate by reg class within market class and create sales weighted cost curves and
    #  vehicle attributes

    manufacturer_new_vehicles = []
    # update each vehicle and calculate compliance target for each vehicle
    for prior_veh in manufacturer_prior_vehicles:
        new_veh = Vehicle()
        new_veh.inherit_vehicle(prior_veh)
        new_veh.model_year = calendar_year
        new_veh.set_cert_target_CO2_grams_per_mile()
        manufacturer_new_vehicles.append(new_veh)

    # get empty market class tree
    mct = MarketClass.get_market_class_tree()
    # populate tree with vehicle objects
    for new_veh in manufacturer_new_vehicles:
        populate_market_classes(mct, new_veh.market_class_ID, new_veh)
        # populate_market_classes(mct, new_veh.market_class_ID + '.' + new_veh.reg_class_ID, new_veh)

    tech_share_combos_total = create_tech_options_from_market_class_tree(calendar_year, mct, consumer_bev_share)

    calculate_tech_share_combos_total(calendar_year, manufacturer_new_vehicles, tech_share_combos_total)

    # tech_share_combos_total.to_csv('%stech_share_combos_total_%d.csv' % (o2.options.output_folder, calendar_year))

    # TODO: pick a winner!! (cheapest one where total_combo_credits_co2_megagrams >= 0... or minimum...??)
    winning_combo = select_winning_combo(tech_share_combos_total)

    # for k, v in zip(winning_combo.keys(), winning_combo):
    #     print('%s = %f' % (k, v))

    # assign co2 values and sales to vehicles...
    for new_veh in manufacturer_new_vehicles:
        new_veh.set_cert_co2_grams_per_mile(winning_combo['veh_%d_co2_gpmi' % new_veh.vehicle_ID])
        new_veh.set_initial_registered_count(winning_combo['veh_%d_sales' % new_veh.vehicle_ID])
        new_veh.set_cert_target_CO2_Mg()
        new_veh.set_cert_CO2_Mg()

    cert_target_co2_Mg = calculate_cert_target_co2_Mg(calendar_year, manufacturer_ID)

    ManufacturerAnnualData.create_manufacturer_annual_data(calendar_year=calendar_year,
                                                           manufacturer_ID=manufacturer_ID,
                                                           cert_target_co2_Mg=cert_target_co2_Mg,
                                                           cert_co2_Mg=winning_combo['total_combo_cert_co2_megagrams'],
                                                           manufacturer_vehicle_cost_dollars=winning_combo['total_combo_cost_dollars'],
                                                           bev_non_hauling_share_frac=winning_combo['non hauling.BEV share_frac'] * winning_combo['non hauling share_frac'],
                                                           ice_non_hauling_share_frac=winning_combo['non hauling.ICE share_frac'] * winning_combo['non hauling share_frac'],
                                                           bev_hauling_share_frac=winning_combo['hauling.BEV share_frac'] * winning_combo['hauling share_frac'],
                                                           ice_hauling_share_frac=winning_combo['hauling.ICE share_frac'] * winning_combo['hauling share_frac'],
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

    o2.session.add_all(manufacturer_new_vehicles)
    o2.session.flush()
    # age0_stock_vmt(calendar_year)
    # prior_year_stock_registered_count(calendar_year)
    # prior_year_stock_vmt(calendar_year)


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
            str = ''
            for j in range(i + 1):
                str = str + substrs[j] + '.' * (j != i)
            str = str + ' share_frac'
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

    return winning_combo


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
