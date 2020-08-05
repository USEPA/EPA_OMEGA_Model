"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""

from usepa_omega2 import *

import numpy as np

import  consumer.sales as consumer
import copy


# class BEVNonHaulingTech(SQABase):
#     # --- database table properties ---
#     __tablename__ = 'BEV_non_hauling'
#     name = Column('BEV_non_hauling_co2_gpmi', Float)
#
#     def clear(self):
#         session.execute('DELETE FROM %s' % self.__tablename__)


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

        # for calendar_year in range(o2_options.analysis_initial_year, o2_options.analysis_final_year + 1):
        for calendar_year in range(o2_options.analysis_initial_year, o2_options.analysis_initial_year + 1):
            print(calendar_year)

            # inherit_vehicles(calendar_year-1, calendar_year, manufacturer_ID)
            #
            # # pull in new vehicles:
            # manufacturer_new_vehicles = session.query(Vehicle). \
            #     filter(Vehicle.manufacturer_ID == manufacturer_ID). \
            #     filter(Vehicle.model_year == calendar_year). \
            #     all()
            #
            # for new_veh in manufacturer_new_vehicles:
            #     new_vehicle_sales = 1e6  # has to come from somewhere...
            #     new_veh.set_initial_registered_count(sales=new_vehicle_sales)
            #     new_veh.get_cert_target_CO2_grams_per_mile()
            #     new_veh.set_cert_target_CO2_Mg()

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
            ManufacturerAnnualData.update_cert_target_co2_Mg(manufacturer_ID, calendar_year, cert_target_co2_Mg)

            # TODO: determine new CO2 g/mi for this model year
            # new_veh.cert_CO2_grams_per_mile = SOMETHING
            # new_veh.set_cert_CO2_Mg()
            num_tech_points = 10
            bev_shares_frac = np.linspace(0, 100, 11) / 100

            vehicle_tables = dict()
            tech_table_columns = dict()
            new_vehicles_by_hauling_class = dict()
            for hc in hauling_classes:
                vehicle_tables[hc] = []
                tech_table_columns[hc] = set()
                new_vehicles_by_hauling_class[hc] = dict()
                for fc in fueling_classes:
                    new_vehicles_by_hauling_class[hc][fc] = []
                session.execute('CREATE TABLE bev_shares_%s (bev_share_%s_frac FLOAT)' % (sql_valid_name(hc),
                                                                                          sql_valid_name(hc)))
                session.execute('INSERT INTO bev_shares_%s VALUES %s' %
                                (sql_valid_name(hc), sql_format_value_list_str(bev_shares_frac)))


            # create tech package options, for each vehicle, by hauling class
            for new_veh in manufacturer_new_vehicles:
                new_vehicles_by_hauling_class[new_veh.hauling_class][new_veh.fueling_class].append(new_veh)
                tech_table_name = 'tech_options_%d_' % new_veh.model_year + new_veh.cost_curve_class
                tech_table_co2_gpmi_col = new_veh.cost_curve_class + '_co2_gpmi'
                tech_table_cost_dollars = new_veh.cost_curve_class + '_cost_dollars'
                co2_gpmi_options = np.linspace(
                    CostCurve.get_min_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year),
                    CostCurve.get_max_co2_gpmi(new_veh.cost_curve_class, new_veh.model_year),
                    num=num_tech_points).tolist()
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
                bev_vehicles_by_cost_curve_class = [v.cost_curve_class for v in
                                                    new_vehicles_by_hauling_class[hc]['BEV']]
                cost_str = '('
                for bev in bev_vehicles_by_cost_curve_class:
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
                for bev in bev_vehicles_by_cost_curve_class:
                    co2_Mg_str = co2_Mg_str + bev + '_co2_gpmi*bev_%s_sales*%f/1e6' % (sql_valid_name(hc), lifetime_vmt) + '+'
                co2_Mg_str = co2_Mg_str[:-1]
                co2_Mg_str = co2_Mg_str + ')'
                session.execute('ALTER TABLE %s ADD COLUMN bev_%s_co2_megagrams' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET bev_%s_co2_megagrams=%s' %
                                (tech_share_combos_table_name, sql_valid_name(hc), co2_Mg_str))

                # tally up ICE vehicle costs
                ice_vehicles_by_cost_curve_class = [v.cost_curve_class for v in
                                                    new_vehicles_by_hauling_class[hc]['ICE']]
                cost_str = '('
                for ice in ice_vehicles_by_cost_curve_class:
                    cost_str = cost_str + ice + '_cost_dollars*ice_%s_sales' % sql_valid_name(hc) + '+'
                cost_str = cost_str[:-1]
                cost_str = cost_str + ')'
                session.execute('ALTER TABLE %s ADD COLUMN ice_%s_cost_dollars' %
                                (tech_share_combos_table_name, sql_valid_name(hc)))
                session.execute('UPDATE %s SET ice_%s_cost_dollars=%s' %
                                (tech_share_combos_table_name, sql_valid_name(hc), cost_str))

                # tally up fake-o ICE Mg
                co2_Mg_str = '('
                for ice in ice_vehicles_by_cost_curve_class:
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

            # if False:
            session.execute(
                'CREATE TABLE tech_share_combos_total AS SELECT %s, %s FROM tech_share_combos_2021_hauling, tech_share_combos_2021_non_hauling' % (
                    sql_get_column_names('tech_share_combos_2021_hauling'),
                    sql_get_column_names('tech_share_combos_2021_non_hauling')))

            session.execute('ALTER TABLE tech_share_combos_total ADD COLUMN total_combo_co2_megagrams')
            session.execute('UPDATE tech_share_combos_total SET total_combo_co2_megagrams=non_hauling_combo_co2_megagrams+hauling_combo_co2_megagrams')

            session.execute('ALTER TABLE tech_share_combos_total ADD COLUMN total_combo_cost_dollars')
            session.execute('UPDATE tech_share_combos_total SET total_combo_cost_dollars=non_hauling_combo_cost_dollars+hauling_combo_cost_dollars')

            session.add_all(manufacturer_new_vehicles)
            session.flush()


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))
