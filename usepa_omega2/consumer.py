"""
consumer.py
===========

Consumer module stub (for now)

"""

from usepa_omega2 import *


def demand_sales(session, model_year):
    """
    :param session: database session
    :param model_year: not used, for now
    :return: dict of sales by consumer (market) categories
    """

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta

    sales_dict = dict()

    # get sales numbers from initial fleet
    initial_ICE_sales = session.query(func.sum(VehicleAnnualData.registered_count)).join(Vehicle).filter(
        Vehicle.fueling_class == 'ICE').filter(VehicleAnnualData.calendar_year == o2_options.analysis_inital_year).scalar()

    initial_BEV_sales = session.query(func.sum(VehicleAnnualData.registered_count)).join(Vehicle).filter(
        Vehicle.fueling_class == 'BEV').filter(VehicleAnnualData.calendar_year == o2_options.analysis_inital_year).scalar()

    initial_hauling_sales = session.query(func.sum(VehicleAnnualData.registered_count)).join(Vehicle).filter(
        Vehicle.hauling_class == 'hauling').filter(VehicleAnnualData.calendar_year == o2_options.analysis_inital_year).scalar()

    initial_non_hauling_sales = session.query(func.sum(VehicleAnnualData.registered_count)).join(Vehicle).filter(
        Vehicle.hauling_class == 'non hauling').filter(VehicleAnnualData.calendar_year == o2_options.analysis_inital_year).scalar()

    sales_dict['hauling'] = initial_hauling_sales
    sales_dict['non hauling'] = initial_non_hauling_sales
    sales_dict['BEV'] = initial_BEV_sales
    sales_dict['ICE'] = initial_ICE_sales

    return sales_dict


if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    from vehicles import *
    from vehicle_annual_data import *

    from manufacturers import *  # needed for manufacturers table
    from market_classes import *  # needed for market class ID
    from fuels import *  # needed for showroom fuel ID
    from cost_curves import *  # needed for vehicle cost from CO2
    from cost_clouds import *  # needed for vehicle cost from CO2

    SQABase.metadata.create_all(engine)

    init_fail = []
    init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + MarketClass.init_database_from_file(o2_options.market_classes_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + Fuel.init_database_from_file(o2_options.fuels_file, session, verbose=o2_options.verbose)
    # init_fail = init_fail + CostCloud.init_database_from_file(o2_options.cost_clouds_file, session, verbose=o2_options.verbose)
    init_fail = init_fail + CostCurve.init_database_from_file(o2_options.cost_curves_file, session, verbose=o2_options.verbose)

    init_fail = init_fail + Vehicle.init_database_from_file(o2_options.vehicles_file, session, verbose=o2_options.verbose)

    if not init_fail:
        o2_options.analysis_inital_year = session.query(func.max(Vehicle.model_year)).scalar()

        sales_demand = demand_sales(session)
