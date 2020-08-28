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
                # new_veh.set_initial_registered_count(prior_veh.get_initial_registered_count())
                # new_veh.set_cert_target_CO2_Mg()  # can't do this without sales
                manufacturer_new_vehicles.append(new_veh)

            # calculate this year's target Mg, requires vehicle level Mg first (which requires sales and a target g/mi)
            # cert_target_co2_Mg = calculate_cert_target_co2_Mg(calendar_year, manufacturer_ID)

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

            # WAS WORKING ON DE-HAND-CODING THE SWEEP FACTORS... HAD AN IDEA ABOUT HAVING BOTH ICE AND BEV SHARES
            # IN THE MARKET SHARE TABLE, BUT THEY HAVE TO ADD UP TO ONE... FACTORIAL THEM AND THROW OUT COMBOS THAT
            # EXCEED 1.0?  SOME OTHER METHOD?  THEN USE EACH VEHICLES MARKET CLASS TO LOOK UP IT'S SHARE...?
            # NOT REALLY SURE, EXACTLY...

            vehicle_tables = dict()
            vehicle_combo_tables = dict()
            tech_table_columns = dict()
            new_vehicles_by_hauling_class = dict()
            for hc in hauling_classes:
                vehicle_tables[hc] = []
                vehicle_combo_tables[hc] = []
                tech_table_columns[hc] = set()
                new_vehicles_by_hauling_class[hc] = dict()
                for fc in fueling_classes:
                    new_vehicles_by_hauling_class[hc][fc] = []
                # create market share table
                market_share_table_name = sql_valid_name('%s_shares' % hc)
                o2.session.execute('DROP TABLE IF EXISTS %s' % market_share_table_name)
                o2.session.execute('CREATE TABLE %s (%s)' %
                                   (market_share_table_name,
                                    sql_format_list_str(['%s_%s_share_frac FLOAT' % (sql_valid_name(ms), sql_valid_name(hc)) for ms in market_shares_frac[hc]])))
                # add values to table, all at once, each row should add up to 1.0
                ms_values = [tuple(market_shares_frac[hc][ms]) for ms in market_shares_frac[hc]]
                o2.session.execute('INSERT INTO %s VALUES %s' %
                                   (market_share_table_name,
                                    sql_format_value_list_str(zip(*ms_values))))

            # create tech package options, for each vehicle
            new_vehicle_co2_dict = create_vehicle_tech_options(manufacturer_new_vehicles, new_vehicles_by_hauling_class,
                                                               num_tech_options, tech_table_columns, vehicle_tables)

            # combine tech package options, by hauling class
            create_tech_combos_by_hauling_class(calendar_year, market_share_groups, market_shares_frac,
                                                new_vehicles_by_hauling_class, tech_table_columns, vehicle_combo_tables,
                                                vehicle_tables)

            create_tech_share_combos_total(calendar_year)

            calculate_compliance_outcomes(calendar_year)

            # TODO: pick a winner!! (cheapest one where total_combo_credits_co2_megagrams >= 0... or minimum...??)
            sel = 'SELECT * FROM tech_share_combos_total_%d WHERE ' \
                  'total_combo_credits_co2_megagrams>=0 ORDER BY total_combo_cost_dollars LIMIT 1' % \
                  (calendar_year)

            winning_combo = o2.session.execute(sel).fetchone()

            # for k, v in zip(winning_combo.keys(), winning_combo):
            #     print('%s = %f' % (k, v))

            # assign co2 values and sales to vehicles...
            for new_veh, co2_gpmi_col in new_vehicle_co2_dict.items():
                # print(new_veh, co2_gpmi_col)
                new_veh.set_cert_co2_grams_per_mile(winning_combo[co2_gpmi_col])

                # TODO: *** THIS IS NOT THE RIGHT WAY TO DO THIS ***
                if new_veh.market_class_ID == 'BEV non hauling':
                    new_veh.set_initial_registered_count(winning_combo['bev_non_hauling_sales'])
                elif new_veh.market_class_ID == 'BEV hauling':
                    new_veh.set_initial_registered_count(winning_combo['bev_hauling_sales'])
                elif new_veh.market_class_ID == 'ICE non hauling':
                    new_veh.set_initial_registered_count(winning_combo['ice_non_hauling_sales'])
                else:
                    new_veh.set_initial_registered_count(winning_combo['ice_hauling_sales'])

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
                                                                   bev_non_hauling_share_frac=winning_combo['bev_non_hauling_share_frac'],
                                                                   ice_non_hauling_share_frac=winning_combo['ice_non_hauling_share_frac'],
                                                                   bev_hauling_share_frac=winning_combo['bev_hauling_share_frac'],
                                                                   ice_hauling_share_frac=winning_combo['ice_hauling_share_frac'],
                                                                   )

            if not o2.options.verbose:
                # drop big ass table
                o2.session.execute('DROP TABLE tech_share_combos_total_%d' % calendar_year)
                # drop vehicle tech options tables
                for k, tables in vehicle_tables.items():
                    for t in tables:
                        o2.session.execute('DROP TABLE %s' % t)
                for k, tables in vehicle_combo_tables.items():
                    for t in tables:
                        o2.session.execute('DROP TABLE %s' % t)
            elif o2.options.slice_tech_combo_cloud_tables:
                # only preserve points within a range of target, to make a small ass table
                slice_width = 0.01 * cert_co2_Mg
                o2.session.execute(
                    'DELETE FROM tech_share_combos_total_%d WHERE total_combo_cert_co2_megagrams NOT BETWEEN %f AND %f' %
                    (calendar_year, cert_co2_Mg - slice_width, cert_co2_Mg + slice_width))

            o2.session.add_all(manufacturer_new_vehicles)
            o2.session.flush()
            # age0_stock_vmt(calendar_year)
            # prior_year_stock_registered_count(calendar_year)
            # prior_year_stock_vmt(calendar_year)


def create_vehicle_tech_options(manufacturer_new_vehicles, new_vehicles_by_hauling_class, num_tech_options,
                                tech_table_columns, vehicle_tables):
    from cost_curves import CostCurve

    new_vehicle_co2_dict = dict()
    for new_veh in manufacturer_new_vehicles:
        new_vehicles_by_hauling_class[new_veh.hauling_class][new_veh.fueling_class].append(new_veh)
        tech_table_name = 'tech_options_veh_%d_%d' % (new_veh.vehicle_ID, new_veh.model_year)
        vehicle_tables[new_veh.hauling_class].append(tech_table_name)
        tech_table_co2_gpmi_col = 'veh_%d_co2_gpmi' % new_veh.vehicle_ID
        tech_table_cost_dollars = 'veh_%d_cost_dollars' % new_veh.vehicle_ID
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
        o2.session.execute('CREATE TABLE %s (%s FLOAT, %s FLOAT)' % (tech_table_name,
                                                                     tech_table_co2_gpmi_col,
                                                                     tech_table_cost_dollars))
        o2.session.execute('INSERT INTO %s VALUES %s' %
                           (tech_table_name,
                            sql_format_value_list_str(zip(co2_gpmi_options, tech_cost_options))))

        tech_table_columns[new_veh.hauling_class].add(tech_table_co2_gpmi_col)
        tech_table_columns[new_veh.hauling_class].add(tech_table_cost_dollars)
        new_vehicle_co2_dict[new_veh] = tech_table_co2_gpmi_col
    return new_vehicle_co2_dict


def create_tech_combos_by_hauling_class(calendar_year, market_share_groups, market_shares_frac,
                                        new_vehicles_by_hauling_class, tech_table_columns, vehicle_combo_tables,
                                        vehicle_tables):
    for hc in hauling_classes:
        tech_combo_table_name = 'tech_combos_%d_%s' % (calendar_year, sql_valid_name(hc))
        vehicle_combo_tables[hc].append(tech_combo_table_name)
        o2.session.execute(
            'CREATE TABLE %s AS SELECT %s FROM %s' % (tech_combo_table_name,
                                                      sql_format_list_str(tech_table_columns[hc]),
                                                      # TODO: convert to sql_get_column_names()?
                                                      sql_format_list_str(vehicle_tables[hc])
                                                      # TODO: convert to sql_get_column_names()?
                                                      ))
        # combine tech combos with bev shares
        tech_share_combos_table_name = 'tech_share_combos_%d_%s' % (calendar_year, sql_valid_name(hc))
        vehicle_combo_tables[hc].append(tech_share_combos_table_name)
        o2.session.execute(
            'CREATE TABLE %s AS SELECT %s, %s FROM %s, %s_shares' %
            (tech_share_combos_table_name,
             sql_get_column_names(tech_combo_table_name),
             sql_get_column_names('%s_shares' % sql_valid_name(hc)),
             tech_combo_table_name, sql_valid_name(hc)
             ))

        # set market share sales
        for ms in market_shares_frac[hc]:
            o2.session.execute('ALTER TABLE %s ADD COLUMN %s_%s_sales FLOAT' %
                               (tech_share_combos_table_name, sql_valid_name(ms), sql_valid_name(hc)))
            o2.session.execute('UPDATE %s SET %s_%s_sales=%s_%s_share_frac*%f' % (
                tech_share_combos_table_name, sql_valid_name(ms), sql_valid_name(hc), sql_valid_name(ms),
                sql_valid_name(hc),
                consumer.sales.demand_sales(calendar_year)[hc]))

            # tally up costs by market share
            veh_prefixes_by_ms = ['veh_' + str(v.vehicle_ID) for v in
                                  new_vehicles_by_hauling_class[hc][ms]]
            # TODO: instead of (veh_6_cost_dollars*bev_sales) should be (veh_6_cost_dollars*veh_6_segment_share*bev_sales) or something, if there is more than one veh in the segment
            # TODO: then sum up vehicle costs into market share costs, instead of assuming one vehicle per segment (unless we always aggregate...)
            cost_str = '('
            for veh_prefix in veh_prefixes_by_ms:
                cost_str = cost_str + veh_prefix + '_cost_dollars*%s_%s_sales' % (
                sql_valid_name(ms), sql_valid_name(hc)) + '+'
            cost_str = cost_str[:-1]
            cost_str = cost_str + ')'
            for veh_prefix in veh_prefixes_by_ms:
                o2.session.execute('ALTER TABLE %s ADD COLUMN %s_total_cost_dollars' %
                                   (tech_share_combos_table_name, veh_prefix))
                o2.session.execute('UPDATE %s SET %s_total_cost_dollars=%s' %
                                   (tech_share_combos_table_name, veh_prefix, cost_str))
            # tally up vehicle costs by market segment
            cost_str = ''
            for veh_prefix in veh_prefixes_by_ms:
                cost_str = cost_str + '%s_total_cost_dollars+' % veh_prefix
            cost_str = cost_str[:-1]
            o2.session.execute('ALTER TABLE %s ADD COLUMN %s_%s_cost_dollars' %
                               (tech_share_combos_table_name, sql_valid_name(ms), sql_valid_name(hc)))
            o2.session.execute('UPDATE %s SET %s_%s_cost_dollars=%s' % (
                tech_share_combos_table_name, sql_valid_name(ms), sql_valid_name(hc), cost_str))

            # calc cert and target Mg for each vehicle CO2 g/mi
            for veh, veh_prefix in zip(new_vehicles_by_hauling_class[hc][ms], veh_prefixes_by_ms):
                sales = sql_unpack_result(o2.session.query('%s_%s_sales FROM %s' % (
                sql_valid_name(ms), sql_valid_name(hc), tech_share_combos_table_name)).all())
                co2_gpmi = sql_unpack_result(
                    o2.session.query('%s_co2_gpmi FROM %s' % (veh_prefix, tech_share_combos_table_name)).all())
                cert_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(veh, co2_gpmi_variants=co2_gpmi,
                                                                            sales_variants=sales)
                target_co2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(veh, sales_variants=sales)

                combo_data = o2.session.execute('SELECT * FROM %s' % tech_share_combos_table_name).fetchall()
                new_data = [(*c, cm, tm) for c, cm, tm in zip(combo_data, cert_co2_Mg, target_co2_Mg)]
                o2.session.execute('DELETE FROM %s' % tech_share_combos_table_name)

                o2.session.execute('ALTER TABLE %s ADD COLUMN %s_%s_cert_co2_megagrams FLOAT' % (
                    tech_share_combos_table_name, sql_valid_name(ms), sql_valid_name(hc)))
                o2.session.execute('ALTER TABLE %s ADD COLUMN %s_%s_target_co2_megagrams FLOAT' % (
                    tech_share_combos_table_name, sql_valid_name(ms), sql_valid_name(hc)))

                o2.session.execute(
                    'INSERT INTO %s VALUES %s' % (tech_share_combos_table_name, sql_format_value_list_str(new_data)))

        combo_str = ''
        for ms in market_share_groups[hc]:
            combo_str = combo_str + '%s_%s_cost_dollars+' % (sql_valid_name(ms), sql_valid_name(hc))
        combo_str = combo_str[:-1]
        # tally up total market segment combo cost
        o2.session.execute('ALTER TABLE %s ADD COLUMN %s_combo_cost_dollars' %
                           (tech_share_combos_table_name, sql_valid_name(hc)))
        o2.session.execute('UPDATE %s SET %s_combo_cost_dollars=%s' %
                           (tech_share_combos_table_name, sql_valid_name(hc), combo_str))

        combo_str = ''
        for ms in market_share_groups[hc]:
            combo_str = combo_str + '%s_%s_cert_co2_megagrams+' % (sql_valid_name(ms), sql_valid_name(hc))
        combo_str = combo_str[:-1]
        # tally up total market segment Mg
        o2.session.execute('ALTER TABLE %s ADD COLUMN %s_combo_cert_co2_megagrams' %
                           (tech_share_combos_table_name, sql_valid_name(hc)))
        o2.session.execute('UPDATE %s SET %s_combo_cert_co2_megagrams=%s' %
                           (tech_share_combos_table_name, sql_valid_name(hc), combo_str))

        combo_str = ''
        for ms in market_share_groups[hc]:
            combo_str = combo_str + '%s_%s_target_co2_megagrams+' % (sql_valid_name(ms), sql_valid_name(hc))
        combo_str = combo_str[:-1]
        # tally up total market segment Mg
        o2.session.execute('ALTER TABLE %s ADD COLUMN %s_combo_target_co2_megagrams' %
                           (tech_share_combos_table_name, sql_valid_name(hc)))
        o2.session.execute('UPDATE %s SET %s_combo_target_co2_megagrams=%s' %
                           (tech_share_combos_table_name, sql_valid_name(hc), combo_str))

        remove_duplicate_combos(hc, tech_share_combos_table_name)


def remove_duplicate_combos(hc, tech_share_combos_table_name):
    # remove duplicate Mg outcomes and costs
    # (this cuts down on the full factorial combinations by a significant amount)
    # TODO: there's a SQL way to do this, involving partitioning data and assigning row numbers,
    #  but I couldn't understand it
    megagrams_set = set()
    unique_data = []
    res = o2.session.execute('SELECT %s_combo_cert_co2_megagrams, %s_combo_cost_dollars, * FROM %s' %
                             (sql_valid_name(hc), sql_valid_name(hc),
                              tech_share_combos_table_name)).fetchall()
    for r in res:
        combo_cert_co2_megagrams = r['%s_combo_cert_co2_megagrams' % sql_valid_name(hc)]
        combo_cost_dollars = r['%s_combo_cost_dollars' % sql_valid_name(hc)]
        combo_data = r[2:]
        if (combo_cert_co2_megagrams, combo_cost_dollars) not in megagrams_set:
            megagrams_set.add((combo_cert_co2_megagrams, combo_cost_dollars))
            unique_data.append(combo_data)
    # clear table
    o2.session.execute('DELETE FROM %s' % tech_share_combos_table_name)
    # toss unique data back in
    for ud in unique_data:
        o2.session.execute('INSERT INTO %s (%s) VALUES %s' %
                           (tech_share_combos_table_name,
                            sql_get_column_names(tech_share_combos_table_name),
                            ud))


def add_Mg_columns(calendar_year):
    # add up cert Mg
    o2.session.execute(
        'ALTER TABLE tech_share_combos_total_%d ADD COLUMN total_combo_cert_co2_megagrams' % calendar_year)
    # add up target Mg
    o2.session.execute(
        'ALTER TABLE tech_share_combos_total_%d ADD COLUMN total_combo_target_co2_megagrams' % calendar_year)
    # calculate credits (positive = under target... for now anyway... not sure the convention)
    o2.session.execute(
        'ALTER TABLE tech_share_combos_total_%d ADD COLUMN total_combo_credits_co2_megagrams' % calendar_year)
    o2.session.execute(
        'ALTER TABLE tech_share_combos_total_%d ADD COLUMN total_combo_cost_dollars' % calendar_year)


def calculate_compliance_outcomes(calendar_year):
    add_Mg_columns(calendar_year)

    o2.session.execute(
        'UPDATE tech_share_combos_total_%d SET \
            total_combo_cert_co2_megagrams=non_hauling_combo_cert_co2_megagrams+hauling_combo_cert_co2_megagrams, \
            total_combo_target_co2_megagrams=non_hauling_combo_target_co2_megagrams+hauling_combo_target_co2_megagrams, \
            total_combo_cost_dollars=non_hauling_combo_cost_dollars+hauling_combo_cost_dollars' %
        calendar_year)

    o2.session.execute(
        'UPDATE tech_share_combos_total_%d SET \
            total_combo_credits_co2_megagrams=total_combo_target_co2_megagrams-total_combo_cert_co2_megagrams' %
        calendar_year)


def create_tech_share_combos_total(calendar_year):
    o2.session.execute(
        'CREATE TABLE tech_share_combos_total_%d AS SELECT %s, %s FROM tech_share_combos_%d_hauling, \
            tech_share_combos_%d_non_hauling' % (
            calendar_year,
            sql_get_column_names('tech_share_combos_%d_hauling' % calendar_year),
            sql_get_column_names('tech_share_combos_%d_non_hauling' % calendar_year),
            calendar_year, calendar_year))


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
