"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""

from usepa_omega2 import *

import numpy as np

import consumer
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


def inherit_vehicles(from_year, to_year, manufacturer_id):
    # this works, but ignores annual data like initial registered count (needs to be joined from vehicle_annual_data)
    # which will be fine when are getting sales from the consumer module or creating them as part of the unconstrained
    # full factorial tech combos
    cn = get_column_names('vehicles', exclude='vehicle_id')
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

        for calendar_year in range(o2_options.analysis_initial_year, o2_options.analysis_final_year+1):
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
            vehicle_tables = []
            tech_table_cols = set()
            # tech_table_cost_dollars_cols = set()
            for new_veh in manufacturer_new_vehicles:
                tech_table_name = 'tech_options_' + new_veh.cost_curve_class + '_%d' % new_veh.model_year
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
                values_str = ''
                for (co2, cost) in zip(co2_gpmi_options, tech_cost_options):
                    values_str = values_str + '(%f, %f),' % (co2, cost)
                values_str = values_str[:-1]
                session.execute('CREATE TABLE %s (%s FLOAT, %s FLOAT)' % (tech_table_name,
                                                                          tech_table_co2_gpmi_col,
                                                                          tech_table_cost_dollars ))
                session.execute('INSERT INTO %s VALUES %s' % (tech_table_name, values_str))  # insert three rows...

                tech_table_cols.add(tech_table_co2_gpmi_col)
                tech_table_cols.add(tech_table_cost_dollars)
                vehicle_tables.append(tech_table_name)

            session.execute(
                'CREATE TABLE tech_combos_%d AS SELECT %s FROM %s' % (calendar_year,
                                                                 sql_format_list_str(tech_table_cols),
                                                                 sql_format_list_str(vehicle_tables)
                                                                 ))

            session.add_all(manufacturer_new_vehicles)
            session.flush()


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))
