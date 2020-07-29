"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""

from usepa_omega2 import *
import consumer
import copy

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


def run_compliance_model(session):
    from manufacturers import Manufacturer
    from vehicles import Vehicle

    for manufacturer in session.query(Manufacturer.manufacturer_ID).all():

        manufacturer_ID = manufacturer[0]
        print(manufacturer_ID)

        for calendar_year in range(o2_options.analysis_initial_year, o2_options.analysis_final_year+1):
            print(calendar_year)
            # pull in last year's vehicles:
            manufacturer_prior_vehicles = session.query(Vehicle). \
                filter(Vehicle.manufacturer_ID == manufacturer_ID). \
                filter(Vehicle.model_year == calendar_year - 1). \
                all()

            # TODO: maybe it would be more efficient to copy the rows in the database (while updating the model year)
            #  and then query them...??
            manufacturer_new_vehicles = []
            # update each vehicle and calculate compliance target for each vehicle
            for prior_veh in manufacturer_prior_vehicles:
                new_veh = Vehicle()
                new_veh.inherit_vehicle(prior_veh)
                new_veh.model_year = calendar_year
                new_veh.get_cert_target_CO2_grams_per_mile()
                new_veh.set_initial_registered_count(prior_veh.get_initial_registered_count())
                print(prior_veh)
                print(new_veh)
                manufacturer_new_vehicles.append(new_veh)

            # session.add_all(manufacturer_new_vehicles)
            session.flush()


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))
