"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""

from usepa_omega2 import *

import numpy as np

import consumer.sales as consumer


def calc_reg_class_demand(session, model_year):
    """
    This is really a placeholder but somehow we need reg class demand from market class demand...

    :param session: database session
    :param model_year: year in which to convert consumer demand (by market class) to regulatory demand (by reg class)
    :return: dict of sales by reg class
    """

    consumer_sales = consumer.demand_sales(session, model_year)

    producer_sales = dict()

    # for now: non hauling = car, hauling = truck
    producer_sales['car'] = consumer_sales['non hauling']
    producer_sales['truck'] = consumer_sales['hauling']

    return producer_sales


def calc_hauling_class_demand(session, model_year):
    """
    This is really a placeholder but somehow we need reg class demand from market class demand...

    :param session: database session
    :param model_year: year in which to convert consumer demand (by market class) to regulatory demand (by reg class)
    :return: dict of sales by reg class
    """

    return consumer.demand_sales(session, model_year)


def inherit_vehicles(from_year, to_year, manufacturer_id):
    # this works, but ignores annual data like initial registered count (needs to be joined from vehicle_annual_data)
    # which will be fine when are getting sales from the consumer module or creating them as part of the unconstrained
    # full factorial tech combos
    cn = sql_get_column_names('vehicles', exclude='vehicle_id')
    session.execute('CREATE TABLE new_vehicles AS SELECT %s FROM vehicles \
                     WHERE model_year==%d AND manufacturer_id=="%s"' % (cn, from_year, manufacturer_id))
    session.execute('UPDATE new_vehicles SET model_year=%d' % to_year)
    session.execute('INSERT INTO vehicles (%s) SELECT %s FROM new_vehicles' % (cn, cn))
    session.execute('DROP TABLE new_vehicles')


def calculate_cert_target_co2_Mg(model_year, manufacturer_id):
    from vehicles import Vehicle
    return session.query(func.sum(Vehicle.cert_target_CO2_Mg)). \
        filter(Vehicle.manufacturer_ID == manufacturer_id). \
        filter(Vehicle.model_year == model_year).scalar()


def calculate_cert_co2_Mg(model_year, manufacturer_id):
    from vehicles import Vehicle
    return session.query(func.sum(Vehicle.cert_CO2_Mg)). \
        filter(Vehicle.manufacturer_ID == manufacturer_id). \
        filter(Vehicle.model_year == model_year).scalar()


# placeholder for producer deemed generalized vehicle cost:
def calculate_generalized_cost(cost_factors):
    pass


def run_compliance_model(session):
    from manufacturers import Manufacturer
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from cost_curves import CostCurve

    for manufacturer in session.query(Manufacturer.manufacturer_ID).all():
        manufacturer_ID = manufacturer[0]
        print(manufacturer_ID)

        for calendar_year in range(o2_options.analysis_initial_year, o2_options.analysis_final_year + 1):
        # for calendar_year in range(o2_options.analysis_initial_year, o2_options.analysis_initial_year + 1):
            print(calendar_year)
            # pull in last year's vehicles:
            manufacturer_prior_vehicles = session.query(Vehicle). \
                filter(Vehicle.manufacturer_ID == manufacturer_ID). \
                filter(Vehicle.model_year == calendar_year - 1). \
                all()

            manufacturer_new_vehicles = []
            # update each vehicle and calculate compliance target for each vehicle
            for prior_veh in manufacturer_prior_vehicles:
                new_veh = Vehicle()
                new_veh.inherit_vehicle(prior_veh)
                new_veh.model_year = calendar_year
                new_veh.set_initial_registered_count(prior_veh.get_initial_registered_count())
                new_veh.set_cert_target_CO2_grams_per_mile()
                new_veh.set_cert_target_CO2_Mg()
                manufacturer_new_vehicles.append(new_veh)

            # calculate this year's target Mg
            cert_target_co2_Mg = calculate_cert_target_co2_Mg(calendar_year, manufacturer_ID)

            # set up number of tech options and BEV shares
            num_tech_options = 10
            market_shares_frac = dict()
            market_shares_frac['hauling'] = dict()
            market_shares_frac['non hauling'] = dict()
            market_shares_frac['hauling']['BEV'] = np.unique(np.linspace(0, 1, 10))
            market_shares_frac['non hauling']['BEV'] = np.unique(np.linspace(0, 1, 10))
            market_share_groups = dict()
            market_share_groups['hauling'] = fueling_classes
            market_share_groups['non hauling'] = fueling_classes

            # WAS WORKING ON DE-HAND-CODING THE SWEEP FACTORS... HAD AN IDEA ABOUT HAVING BOTH ICE AND BEV SHARES
            # IN THE MARKET SHARE TABLE, BUT THEY HAVE TO ADD UP TO ONE... FACTORIAL THEM AND THROW OUT COMBOS THAT
            # EXCEED 1.0?  SOME OTHER METHOD?  THEN USE EACH VEHICLES MARKET CLASS TO LOOK UP IT'S SHARE...?
            # NOT REALLY SURE, EXACTLY...

            vehicle_tables = dict()
            tech_table_columns = dict()
            new_vehicles_by_hauling_class = dict()
            for hc in hauling_classes:
                vehicle_tables[hc] = []
                tech_table_columns[hc] = set()
                new_vehicles_by_hauling_class[hc] = dict()
                for fc in fueling_classes:
                    new_vehicles_by_hauling_class[hc][fc] = []
                for ms in ['BEV']:
                    market_share_table_name = sql_valid_name('%s_shares_%s' % (ms, hc))
                    session.execute('DROP TABLE IF EXISTS %s' % market_share_table_name)
                    session.execute('CREATE TABLE %s (%s_share_%s_frac FLOAT)' % (market_share_table_name, sql_valid_name(ms),
                                                                                                  sql_valid_name(hc)))
                    session.execute('DELETE FROM %s' % market_share_table_name)  # clear table
                    session.execute('INSERT INTO %s VALUES %s' %
                                    (market_share_table_name, sql_format_value_list_str(market_shares_frac[hc][ms])))

            # create tech package options, for each vehicle
            new_vehicle_co2_dict = dict()
            for new_veh in manufacturer_new_vehicles:
                new_vehicles_by_hauling_class[new_veh.hauling_class][new_veh.fueling_class].append(new_veh)
                tech_table_name = 'tech_options_veh_%d_%d' % (new_veh.vehicle_ID, new_veh.model_year)
                tech_table_co2_gpmi_col = 'veh_%d_co2_gpmi' % new_veh.vehicle_ID
                tech_table_cost_dollars = 'veh_%d_cost_dollars' % new_veh.vehicle_ID
                if o2_options.allow_backsliding:
                    max_co2_gpmi = CostCurve.get_max_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year)
                else:
                    max_co2_gpmi = new_veh.cert_CO2_grams_per_mile
                co2_gpmi_options = np.linspace(
                    CostCurve.get_min_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year),
                    max_co2_gpmi,
                    num=num_tech_options).tolist()
                tech_cost_options = CostCurve.get_cost(session,
                                                       cost_curve_class=new_veh.cost_curve_class,
                                                       model_year=new_veh.model_year,
                                                       target_co2_gpmi=co2_gpmi_options)
                session.execute('CREATE TABLE %s (%s FLOAT, %s FLOAT)' % (tech_table_name,
                                                                          tech_table_co2_gpmi_col,
                                                                          tech_table_cost_dollars))
                session.execute('INSERT INTO %s VALUES %s' %
                                (tech_table_name, sql_format_value_list_str(zip(co2_gpmi_options, tech_cost_options))))

                tech_table_columns[new_veh.hauling_class].add(tech_table_co2_gpmi_col)
                tech_table_columns[new_veh.hauling_class].add(tech_table_cost_dollars)
                vehicle_tables[new_veh.hauling_class].append(tech_table_name)
                new_vehicle_co2_dict[new_veh] = tech_table_co2_gpmi_col

            # combine tech package options, by hauling class
            for hc in hauling_classes:
                tech_combo_table_name = 'tech_combos_%d_%s' % (calendar_year, sql_valid_name(hc))
                session.execute(
                    'CREATE TABLE %s AS SELECT %s FROM %s' % (tech_combo_table_name,
                                                              sql_format_list_str(tech_table_columns[hc]),
                                                              sql_format_list_str(vehicle_tables[hc])
                                                              ))
                # combine tech combos with bev shares
                tech_share_combos_table_name = 'tech_share_combos_%d_%s' % (calendar_year, sql_valid_name(hc))
                session.execute(
                    'CREATE TABLE %s AS SELECT %s, bev_share_%s_frac FROM %s, bev_shares_%s' %
                    (tech_share_combos_table_name,
                     sql_format_list_str(tech_table_columns[hc]),
                     sql_valid_name(hc),
                     tech_combo_table_name, sql_valid_name(hc)
                     ))

                # set BEV sales
                session.execute('ALTER TABLE %s ADD COLUMN bev_%s_sales' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET bev_%s_sales=bev_share_%s_frac*%f' %
                                (tech_share_combos_table_name, sql_valid_name(hc), sql_valid_name(hc),
                                consumer.demand_sales(session, calendar_year)[hc]))

                # set ICE sales
                session.execute('ALTER TABLE %s ADD COLUMN ice_%s_sales' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET ice_%s_sales=(1-bev_share_%s_frac)*%f' %
                                (tech_share_combos_table_name, sql_valid_name(hc), sql_valid_name(hc),
                                consumer.demand_sales(session, calendar_year)[hc]))

                # tally up BEV vehicle costs
                bev_vehicles_by_market_class = ['veh_' + str(v.vehicle_ID) for v in
                                                    new_vehicles_by_hauling_class[hc]['BEV']]
                cost_str = '('
                for bev in bev_vehicles_by_market_class:
                    cost_str = cost_str + bev + '_cost_dollars*bev_%s_sales' % sql_valid_name(hc) + '+'
                cost_str = cost_str[:-1]
                cost_str = cost_str + ')'
                session.execute('ALTER TABLE %s ADD COLUMN bev_%s_cost_dollars' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET bev_%s_cost_dollars=%s' %
                                (tech_share_combos_table_name, sql_valid_name(hc), cost_str))

                if hc == 'hauling':
                    lifetime_vmt = o2_options.GHG_standard.calculate_cert_lifetime_vmt(RegClass.truck.name, calendar_year)
                else:
                    lifetime_vmt = o2_options.GHG_standard.calculate_cert_lifetime_vmt(RegClass.car.name, calendar_year)

                # tally up fake-o BEV Mg
                co2_Mg_str = '('
                for bev in bev_vehicles_by_market_class:
                    co2_Mg_str = co2_Mg_str + bev + '_co2_gpmi*bev_%s_sales*%f/1e6' % (sql_valid_name(hc), lifetime_vmt) + '+'
                co2_Mg_str = co2_Mg_str[:-1]
                co2_Mg_str = co2_Mg_str + ')'
                session.execute('ALTER TABLE %s ADD COLUMN bev_%s_co2_megagrams' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET bev_%s_co2_megagrams=%s' %
                                (tech_share_combos_table_name, sql_valid_name(hc), co2_Mg_str))

                # tally up ICE vehicle costs
                ice_vehicles_by_market_class = ['veh_' + str(v.vehicle_ID) for v in
                                                    new_vehicles_by_hauling_class[hc]['ICE']]
                cost_str = '('
                for ice in ice_vehicles_by_market_class:
                    cost_str = cost_str + ice + '_cost_dollars*ice_%s_sales' % sql_valid_name(hc) + '+'
                cost_str = cost_str[:-1]
                cost_str = cost_str + ')'
                session.execute('ALTER TABLE %s ADD COLUMN ice_%s_cost_dollars' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET ice_%s_cost_dollars=%s' %
                                (tech_share_combos_table_name, sql_valid_name(hc), cost_str))

                # tally up fake-o ICE Mg
                co2_Mg_str = '('
                for ice in ice_vehicles_by_market_class:
                    co2_Mg_str = co2_Mg_str + ice + '_co2_gpmi*ice_%s_sales*%f/1e6' % (sql_valid_name(hc), lifetime_vmt) + '+'
                co2_Mg_str = co2_Mg_str[:-1]
                co2_Mg_str = co2_Mg_str + ')'
                session.execute('ALTER TABLE %s ADD COLUMN ice_%s_co2_megagrams' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET ice_%s_co2_megagrams=%s' %
                                (tech_share_combos_table_name, sql_valid_name(hc), co2_Mg_str))

                # tally up total ICE/BEV combo cost
                session.execute('ALTER TABLE %s ADD COLUMN %s_combo_cost_dollars' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET %s_combo_cost_dollars=bev_%s_cost_dollars+ice_%s_cost_dollars' %
                                (tech_share_combos_table_name, sql_valid_name(hc),
                                 sql_valid_name(hc), sql_valid_name(hc))
                                )

                # tally up total ICE/BEV Mg
                session.execute('ALTER TABLE %s ADD COLUMN %s_combo_co2_megagrams' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET %s_combo_co2_megagrams=bev_%s_co2_megagrams+ice_%s_co2_megagrams' %
                                (tech_share_combos_table_name, sql_valid_name(hc),
                                 sql_valid_name(hc), sql_valid_name(hc))
                                )

                # remove duplicate Mg outcomes and costs
                # (this cuts down on the full factorial combinations by a significant amount)
                # TODO: there's a SQL way to do this, involving partitioning data and assigning row numbers, but I couldn't understand it
                megagrams_set = set()
                unique_data = []
                res = session.execute('SELECT %s_combo_co2_megagrams, %s_combo_cost_dollars, * FROM %s' %
                                      (sql_valid_name(hc), sql_valid_name(hc), tech_share_combos_table_name)).fetchall()
                for r in res:
                    combo_co2_megagrams = r['%s_combo_co2_megagrams' % sql_valid_name(hc)]
                    combo_cost_dollars = r['%s_combo_cost_dollars' % sql_valid_name(hc)]
                    combo_data = r[2:]
                    if (combo_co2_megagrams, combo_cost_dollars) not in megagrams_set:
                        megagrams_set.add((combo_co2_megagrams, combo_cost_dollars))
                        unique_data.append(combo_data)
                # clear table
                session.execute('DELETE FROM %s' % tech_share_combos_table_name)
                # toss unique data back in
                for ud in unique_data:
                    session.execute('INSERT INTO %s (%s) VALUES %s' %
                                    (tech_share_combos_table_name,
                                     sql_get_column_names(tech_share_combos_table_name),
                                     ud))

            # if False:
            session.execute(
                'CREATE TABLE tech_share_combos_total_%d AS SELECT %s, %s FROM tech_share_combos_%d_hauling, tech_share_combos_%d_non_hauling' % (
                    calendar_year,
                    sql_get_column_names('tech_share_combos_%d_hauling' % calendar_year),
                    sql_get_column_names('tech_share_combos_%d_non_hauling' % calendar_year),
                    calendar_year, calendar_year))

            session.execute('ALTER TABLE tech_share_combos_total_%d ADD COLUMN total_combo_co2_megagrams' % calendar_year)
            session.execute('UPDATE tech_share_combos_total_%d SET total_combo_co2_megagrams=non_hauling_combo_co2_megagrams+hauling_combo_co2_megagrams' % calendar_year)

            session.execute('ALTER TABLE tech_share_combos_total_%d ADD COLUMN total_combo_cost_dollars' % calendar_year)
            session.execute('UPDATE tech_share_combos_total_%d SET total_combo_cost_dollars=non_hauling_combo_cost_dollars+hauling_combo_cost_dollars' % calendar_year)

            # pick a winner!!
            sel = 'SELECT * FROM tech_share_combos_total_%d WHERE ' \
                  'total_combo_co2_megagrams<=%f ORDER BY total_combo_cost_dollars LIMIT 1' % (calendar_year, cert_target_co2_Mg)
            winning_combo = session.execute(sel).fetchone()

            # assign co2 values to vehicles...
            for new_veh, co2_gpmi_col in new_vehicle_co2_dict.items():
                new_veh.set_cert_co2_grams_per_mile(winning_combo[co2_gpmi_col])
                print(new_veh.cert_CO2_grams_per_mile)
                new_veh.set_cert_CO2_Mg()
                print(new_veh.cert_CO2_Mg)

            ManufacturerAnnualData.update_manufacturer_annual_data(calendar_year,
                                                                   manufacturer_ID, cert_target_co2_Mg,
                                                                   winning_combo['total_combo_co2_megagrams'],
                                                                   winning_combo['total_combo_cost_dollars'])

            # yeah... this doesn't work!! Columns don't come in a predictable order
            # if calendar_year==o2_options.analysis_initial_year:
            #     session.execute('CREATE TABLE winners AS %s' % sel)
            #     session.execute('ALTER TABLE winners ADD COLUMN calendar_year')
            #     session.execute('ALTER TABLE winners ADD COLUMN cert_target_co2_megagrams')
            #     session.execute('UPDATE winners SET calendar_year=%d' % calendar_year)
            #     session.execute('UPDATE winners SET cert_target_co2_megagrams=%d' % cert_target_co2_Mg)
            # else:
            #     winning_combo_list = list(winning_combo)
            #     winning_combo_list.append(calendar_year)
            #     winning_combo_list.append(cert_target_co2_Mg)
            #     session.execute('INSERT INTO winners (%s, calendar_year, cert_target_co2_Mg) VALUES %s' %
            #                     (winning_combo.keys(), tuple(winning_combo_list)))

            if not o2_options.verbose:
                # drop big ass table
                session.execute('DROP TABLE tech_share_combos_total_%d' % (calendar_year))
            elif o2_options.slice_tech_combo_cloud_tables:
                # only preserve points within a range of target, to make a small ass table
                slice_width = 0.005 * cert_target_co2_Mg
                session.execute('DELETE FROM tech_share_combos_total_%d WHERE total_combo_co2_megagrams NOT BETWEEN %f AND %f' %
                                (calendar_year, cert_target_co2_Mg-slice_width, cert_target_co2_Mg + slice_width))

            session.add_all(manufacturer_new_vehicles)
            session.flush()


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))
