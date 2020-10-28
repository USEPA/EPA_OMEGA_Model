"""
sales_volume.py
========

Consumer module stub (for now)

"""

import o2  # import global variables
from usepa_omega2 import *


# placeholder for consumer generalized vehicle cost:
def calculate_generalized_cost(cost_factors):
    pass


def context_new_vehicle_sales(model_year):
    """
    :param model_year: not used, for now
    :return: dict of sales by consumer (market) categories
    """

    # TODO: needs to get context new vehicle sales from projections (AEO, etc)

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta
    from vehicle_annual_data import VehicleAnnualData
    from vehicles import VehicleFinal

    sales_dict = dict()

    # get sales numbers from initial fleet (for now)
    initial_ICE_sales = o2.session.query(func.sum(VehicleAnnualData.registered_count)).join(VehicleFinal).filter(
        VehicleFinal.fueling_class == 'ICE').filter(
        VehicleAnnualData.calendar_year == o2.options.analysis_initial_year - 1).scalar()

    initial_BEV_sales = o2.session.query(func.sum(VehicleAnnualData.registered_count)).join(VehicleFinal).filter(
        VehicleFinal.fueling_class == 'BEV').filter(
        VehicleAnnualData.calendar_year == o2.options.analysis_initial_year - 1).scalar()

    initial_hauling_sales = o2.session.query(func.sum(VehicleAnnualData.registered_count)).join(VehicleFinal).filter(
        VehicleFinal.hauling_class == 'hauling').filter(
        VehicleAnnualData.calendar_year == o2.options.analysis_initial_year - 1).scalar()

    initial_non_hauling_sales = o2.session.query(func.sum(VehicleAnnualData.registered_count)).join(VehicleFinal).filter(
        VehicleFinal.hauling_class == 'non hauling').filter(
        VehicleAnnualData.calendar_year == o2.options.analysis_initial_year - 1).scalar()

    total_sales = o2.session.query(func.sum(VehicleAnnualData.registered_count)).filter(
        VehicleAnnualData.calendar_year == o2.options.analysis_initial_year - 1).scalar()

    sales_dict['hauling'] = float(initial_hauling_sales)
    sales_dict['non hauling'] = float(initial_non_hauling_sales)
    sales_dict['BEV'] = float(initial_BEV_sales)
    sales_dict['ICE'] = float(initial_ICE_sales)
    sales_dict['total'] = float(total_sales)

    return sales_dict


def new_vehicle_sales(P):
    """
    Calculate new vehicle sales, relative to a reference sales volume and average new vehicle price
    :param P: a single price or a list-like of prices
    :return: total new vehicle sales volume at each price
    """

    if type(P) is list:
        import numpy as np
        P = np.array(P)

    # Q0 = o2.session.query(func.sum(VehicleAnnualData.registered_count)).filter(
    #     VehicleAnnualData.calendar_year == o2.options.analysis_initial_year - 1).filter(VehicleAnnualData.age == 0).one()

    # TODO: un-hardcode these values
    Q0 = 14581209  # from vehicles.csv
    P0 = 30937  # sales-weighted, from vehicles.csv
    E = -0.5  # new vehicle sales elasticity, eventually to come from batch file input

    M = -(Q0*E - Q0) / (P0/E - P0)  # slope of linear response

    Q = Q0 + M * (P-P0)  # point-slope equation of a line

    return Q


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        from vehicles import VehicleFinal
        from vehicle_annual_data import VehicleAnnualData
        from manufacturers import Manufacturer  # needed for manufacturers table
        from market_classes import MarketClass  # needed for market class ID
        from fuels import Fuel  # needed for showroom fuel ID
        from cost_curves import CostCurve  # needed for vehicle cost from CO2
        from cost_clouds import CostCloud  # needed for vehicle cost from CO2

        if o2.options.GHG_standard == 'flat':
            from GHG_standards_flat import GHGStandardFlat
        else:
            from GHG_standards_footprint import GHGStandardFootprint

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        if o2.options.cost_file_type == 'curves':
            init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        else:
            init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        if o2.options.GHG_standard == 'flat':
            init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2.options.ghg_standards_file,
                                                                            verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFlat
        else:
            init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                                 verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFootprint

        init_fail = init_fail + VehicleFinal.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        if not init_fail:
            o2.options.analysis_initial_year = o2.session.query(func.max(VehicleFinal.model_year)).scalar() + 1

            sales_demand = context_new_vehicle_sales(o2.options.analysis_initial_year)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
