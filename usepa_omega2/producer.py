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


def partition(num_columns, num_levels, verbose=False):
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
    from pyDOE2 import fullfact
    permutations = fullfact([num_levels]*num_columns) / (num_levels-1)
    ans = [permutation for permutation in permutations if sum(permutation) == 1.0]
    if verbose:
        for i in ans:
            s = ''
            for e in i:
                s = s + '\t%.2f' % e
            print(s)
    return ans


def cartesian_prod(left_df, right_df):
    """

    :param left_df: 'left' dataframe
    :param right_df: 'right' dataframe
    :return: cartesian product of the dataframe rows
    """
    import pandas as pd

    if left_df.empty:
        return right_df
    else:
        left_df['_'] = 1
        right_df['_'] = 1

        leftXright = pd.merge(left_df, right_df, on='_').drop('_', axis=1)

        left_df.drop('_', axis=1, inplace=True)
        right_df.drop('_', axis=1, inplace=True, errors='ignore')

        return leftXright


def calc_reg_class_demand(model_year):
    """
    This is really a placeholder but somehow we need reg class demand from market class demand...

    :param model_year: year in which to convert consumer demand (by market class) to regulatory demand (by reg class)
    :return: dict of sales by reg class
    """

    consumer_sales = consumer.sales.get_demanded_shares(model_year)

    producer_sales = dict()

    # for now: non hauling = car, hauling = truck
    producer_sales['car'] = consumer_sales['non hauling']
    producer_sales['truck'] = consumer_sales['hauling']

    return producer_sales


def calc_hauling_class_demand(model_year):
    """
    This is really a placeholder but somehow we need reg class demand from market class demand...

    :param model_year: year in which to convert consumer demand (by market class) to regulatory demand (by reg class)
    :return: dict of sales by reg class
    """

    return consumer.sales.demand_sales(model_year)


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


def calculate_cert_co2_Mg(model_year, manufacturer_id):
    from vehicles import Vehicle
    return o2.session.query(func.sum(Vehicle.cert_CO2_Mg)). \
        filter(Vehicle.manufacturer_ID == manufacturer_id). \
        filter(Vehicle.model_year == model_year).scalar()


# placeholder for producer deemed generalized vehicle cost:
def calculate_generalized_cost(cost_factors):
    pass


def run_compliance_model():
    from manufacturers import Manufacturer
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from consumer.stock import prior_year_stock_registered_count, prior_year_stock_vmt, age0_stock_vmt

    for manufacturer in o2.session.query(Manufacturer.manufacturer_ID).all():
        manufacturer_ID = manufacturer[0]
        print(manufacturer_ID)

        for calendar_year in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
        # for calendar_year in range(o2.options.analysis_initial_year, o2.options.analysis_initial_year + 2):
            print(calendar_year)
            # pull in last year's vehicles:
            manufacturer_prior_vehicles = o2.session.query(Vehicle). \
                filter(Vehicle.manufacturer_ID == manufacturer_ID). \
                filter(Vehicle.model_year == calendar_year - 1). \
                all()

            # TODO: aggregate...? By market class...? Or not....? Or only for USA Motors?

            manufacturer_new_vehicles = []
            # update each vehicle and calculate compliance target for each vehicle
            for prior_veh in manufacturer_prior_vehicles:
                new_veh = Vehicle()
                new_veh.inherit_vehicle(prior_veh)
                new_veh.model_year = calendar_year
                new_veh.set_cert_target_CO2_grams_per_mile()
                manufacturer_new_vehicles.append(new_veh)

            # set up number of tech options and BEV shares
            num_tech_options = o2.options.num_tech_options_per_vehicle
            market_shares_frac = dict()
            market_shares_frac['hauling'] = dict()
            market_shares_frac['non hauling'] = dict()
            market_shares_frac['hauling']['BEV'] = unique(np.linspace(0, 1, 5))
            market_shares_frac['hauling']['ICE'] = unique(np.linspace(1, 0, 5))
            market_shares_frac['non hauling']['BEV'] = unique(np.linspace(0, 1, 5))
            market_shares_frac['non hauling']['ICE'] = unique(np.linspace(1, 0, 5))
            market_share_groups = dict()
            market_share_groups['hauling'] = fueling_classes
            market_share_groups['non hauling'] = fueling_classes

            market_share_tables = dict()  # dict of dataframes

            vehicle_tech_options = dict()
            hauling_class_tech_combos = dict()
            new_vehicles_by_hauling_class = dict()
            for hc in hauling_classes:
                vehicle_tech_options[hc] = dict()  # dict of dataframes
                hauling_class_tech_combos[hc] = dict()  # dict of dataframes
                new_vehicles_by_hauling_class[hc] = dict()  # dict of vehicle objects
                for fc in fueling_classes:
                    new_vehicles_by_hauling_class[hc][fc] = []

                # create market share table
                df = pd.DataFrame()
                for ms in market_shares_frac[hc]:
                    df['%s_%s_share_frac' % (ms, hc)] = market_shares_frac[hc][ms]
                market_share_tables[hc] = df

                # create tech package options, for each vehicle
            new_vehicle_co2_dict = create_vehicle_tech_options(manufacturer_new_vehicles, new_vehicles_by_hauling_class,
                                                               num_tech_options, vehicle_tech_options)

            # combine tech package options, by hauling class
            create_tech_combos_by_hauling_class(calendar_year, market_share_groups, market_shares_frac,
                                                new_vehicles_by_hauling_class, hauling_class_tech_combos,
                                                vehicle_tech_options, market_share_tables)

            tech_share_combos_total = create_tech_share_combos_total(calendar_year, hauling_class_tech_combos)

            calculate_compliance_outcomes(calendar_year, tech_share_combos_total)

            # TODO: pick a winner!! (cheapest one where total_combo_credits_co2_megagrams >= 0... or minimum...??)
            winning_combo = select_winning_combo(tech_share_combos_total)

            # for k, v in zip(winning_combo.keys(), winning_combo):
            #     print('%s = %f' % (k, v))

            # assign co2 values and sales to vehicles...
            for new_veh, co2_gpmi_col in new_vehicle_co2_dict.items():
                # print(new_veh, co2_gpmi_col)
                new_veh.set_cert_co2_grams_per_mile(winning_combo[co2_gpmi_col])

                # TODO: *** THIS IS NOT THE RIGHT WAY TO DO THIS ***
                if new_veh.market_class_ID == 'BEV.non hauling':
                    new_veh.set_initial_registered_count(winning_combo['BEV_non hauling_sales'])
                elif new_veh.market_class_ID == 'BEV.hauling':
                    new_veh.set_initial_registered_count(winning_combo['BEV_hauling_sales'])
                elif new_veh.market_class_ID == 'ICE.non hauling':
                    new_veh.set_initial_registered_count(winning_combo['ICE_non hauling_sales'])
                else:
                    new_veh.set_initial_registered_count(winning_combo['ICE_hauling_sales'])

                # these depend on sales (initial registered count):
                new_veh.set_cert_target_CO2_Mg()
                new_veh.set_cert_CO2_Mg()

            cert_co2_Mg = winning_combo['total_combo_cert_co2_megagrams']
            cert_target_co2_Mg = calculate_cert_target_co2_Mg(calendar_year, manufacturer_ID)

            ManufacturerAnnualData.create_manufacturer_annual_data(calendar_year=calendar_year,
                                                                   manufacturer_ID=manufacturer_ID,
                                                                   cert_target_co2_Mg=cert_target_co2_Mg,
                                                                   cert_co2_Mg=winning_combo['total_combo_cert_co2_megagrams'],
                                                                   manufacturer_vehicle_cost_dollars=winning_combo['total_combo_cost_dollars'],
                                                                   bev_non_hauling_share_frac=winning_combo['BEV_non hauling_share_frac'],
                                                                   ice_non_hauling_share_frac=winning_combo['ICE_non hauling_share_frac'],
                                                                   bev_hauling_share_frac=winning_combo['BEV_hauling_share_frac'],
                                                                   ice_hauling_share_frac=winning_combo['ICE_hauling_share_frac'],
                                                                   )

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


def select_winning_combo(tech_share_combos_total):
    potential_winners = tech_share_combos_total.loc[tech_share_combos_total['total_combo_credits_co2_megagrams'] >= 0]
    winning_combo = potential_winners.loc[potential_winners['total_combo_cost_dollars'].idxmin()]
    return winning_combo


def create_vehicle_tech_options(manufacturer_new_vehicles, new_vehicles_by_hauling_class, num_tech_options,
                                vehicle_tech_options):
    from cost_curves import CostCurve

    new_vehicle_co2_dict = dict()
    for new_veh in manufacturer_new_vehicles:
        new_vehicles_by_hauling_class[new_veh.hauling_class][new_veh.fueling_class].append(new_veh)

        tech_table_name = 'tech_options_veh_%d_%d' % (new_veh.vehicle_ID, new_veh.model_year)
        df = vehicle_tech_options[new_veh.hauling_class][tech_table_name] = pd.DataFrame()
        if o2.options.allow_backsliding:
            max_co2_gpmi = CostCurve.get_max_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year)
        else:
            max_co2_gpmi = new_veh.cert_CO2_grams_per_mile
        co2_gpmi_options = np.linspace(
            CostCurve.get_min_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year),
            max_co2_gpmi,
            num=num_tech_options).tolist()
        tech_cost_options = CostCurve.get_cost(cost_curve_class=new_veh.cost_curve_class,
                                               model_year=new_veh.model_year,
                                               target_co2_gpmi=co2_gpmi_options)

        df['veh_%d_co2_gpmi' % new_veh.vehicle_ID] = co2_gpmi_options
        df['veh_%d_cost_dollars' % new_veh.vehicle_ID] = tech_cost_options

        tech_table_co2_gpmi_col = 'veh_%d_co2_gpmi' % new_veh.vehicle_ID
        new_vehicle_co2_dict[new_veh] = tech_table_co2_gpmi_col
    return new_vehicle_co2_dict


def create_tech_combos_by_hauling_class(calendar_year, market_share_groups, market_shares_frac,
                                        new_vehicles_by_hauling_class, hauling_class_tech_combos,
                                        vehicle_tech_options, market_share_tables):
    for hc in hauling_classes:
        # combine tech options within the hauling class, by vehicle
        df = pd.DataFrame()
        for k in vehicle_tech_options[hc]:
            df = cartesian_prod(df, vehicle_tech_options[hc][k])

        tech_combo_table_name = 'tech_combos_%d_%s' % (calendar_year, hc)
        hauling_class_tech_combos[hc][tech_combo_table_name] = df

        # combine tech combos with bev shares
        tech_share_combos_table_name = 'tech_share_combos_%d_%s' % (calendar_year, hc)
        hauling_class_tech_combos[hc][tech_share_combos_table_name] = cartesian_prod(
            hauling_class_tech_combos[hc][tech_combo_table_name], market_share_tables[hc])

        # set market share sales
        for ms in market_shares_frac[hc]:
            hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_sales' % (ms, hc)] = \
            hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_share_frac' % (ms, hc)] * \
            consumer.sales.demand_sales(calendar_year)[hc]

            hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_sales' % (ms, hc)]
            # tally up costs by market share
            veh_prefixes_by_ms = ['veh_' + str(v.vehicle_ID) for v in new_vehicles_by_hauling_class[hc][ms]]
            hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_cost_dollars' % (ms, hc)] = 0
            for veh_prefix in veh_prefixes_by_ms:
                # TODO: instead of (veh_6_cost_dollars*bev_sales) should be (veh_6_cost_dollars*veh_6_segment_share*bev_sales) or something, if there is more than one veh in the segment
                # TODO: then sum up vehicle costs into market share costs, instead of assuming one vehicle per segment (unless we always aggregate...)
                hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_total_cost_dollars' % veh_prefix] = \
                    hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_cost_dollars' % veh_prefix] * \
                    hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_sales' % (ms, hc)]
                hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_cost_dollars' % (ms, hc)] = \
                    hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_cost_dollars' % (ms, hc)] + \
                    hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_total_cost_dollars' % veh_prefix]

            # calc cert and target Mg for each vehicle CO2 g/mi and sales combination
            for veh, veh_prefix in zip(new_vehicles_by_hauling_class[hc][ms], veh_prefixes_by_ms):
                sales = hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_sales' % (ms, hc)].to_list()
                co2_gpmi = hauling_class_tech_combos[hc][tech_share_combos_table_name][
                    '%s_co2_gpmi' % veh_prefix].to_list()

                cert_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(veh, co2_gpmi_variants=co2_gpmi,
                                                                            sales_variants=sales)
                target_co2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(veh, sales_variants=sales)

                hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_cert_co2_megagrams' % (ms, hc)] = cert_co2_Mg
                hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_target_co2_megagrams' % (ms, hc)] = target_co2_Mg

        # tally up total market segment combo cost, total market segment cert Mg, total market segment target Mg
        for suffix in ['cost_dollars', 'cert_co2_megagrams', 'target_co2_megagrams']:
            hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_combo_%s' % (hc, suffix)] = 0
            for ms in market_share_groups[hc]:
                hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_combo_%s' % (hc, suffix)] = \
                    hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_combo_%s' % (hc, suffix)] + \
                    hauling_class_tech_combos[hc][tech_share_combos_table_name]['%s_%s_%s' % (ms, hc, suffix)]

        hauling_class_tech_combos[hc][tech_share_combos_table_name].drop_duplicates(
            subset='%s_combo_cert_co2_megagrams' % hc, inplace=True, keep='first', ignore_index=False)


def calculate_compliance_outcomes(calendar_year, tech_share_combos_total):
    for suffix in ['cost_dollars', 'cert_co2_megagrams', 'target_co2_megagrams']:
        tech_share_combos_total['total_combo_%s' % suffix] = 0
        for hc in hauling_classes:
            tech_share_combos_total['total_combo_%s' % suffix] = \
                tech_share_combos_total['total_combo_%s' % suffix] + \
                tech_share_combos_total['%s_combo_%s' % (hc, suffix)]

    tech_share_combos_total['total_combo_credits_co2_megagrams'] = \
        tech_share_combos_total['total_combo_target_co2_megagrams'] - \
        tech_share_combos_total['total_combo_cert_co2_megagrams']


def create_tech_share_combos_total(calendar_year, hauling_class_tech_combos):
    df = pd.DataFrame()
    for hc in hauling_classes:
        tech_share_combos_table_name = 'tech_share_combos_%d_%s' % (calendar_year, hc)
        df = cartesian_prod(df, hauling_class_tech_combos[hc][tech_share_combos_table_name])

    return df


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
