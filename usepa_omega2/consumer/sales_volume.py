"""
sales_volume.py
===============

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

    #  PHASE0: hauling/non, EV/ICE, We don't need shared/private for beta
    from vehicle_annual_data import VehicleAnnualData
    from vehicles import VehicleFinal
    from context_new_vehicle_market import ContextNewVehicleMarket

    sales_dict = dict()

    if o2.options.flat_context:
        model_year = o2.options.flat_context_year

    # get total sales from context
    total_sales = ContextNewVehicleMarket.new_vehicle_sales(model_year)

    total_sales_initial = VehicleAnnualData.get_initial_registered_count()
    ICE_share = VehicleAnnualData.get_initial_fueling_class_registered_count('ICE') / total_sales_initial
    BEV_share = VehicleAnnualData.get_initial_fueling_class_registered_count('BEV') / total_sales_initial

    # pulling in hauling sales, non_hauling = total minus hauling
    hauling_sales = 0
    for hsc in ContextNewVehicleMarket.hauling_context_size_class_info:
        hauling_sales = hauling_sales + \
                        ContextNewVehicleMarket.new_vehicle_sales(model_year, context_size_class=hsc) * \
                        ContextNewVehicleMarket.hauling_context_size_class_info[hsc]['hauling_share']

    sales_dict['hauling'] = hauling_sales
    sales_dict['non_hauling'] = total_sales - hauling_sales
    sales_dict['ICE'] = total_sales * ICE_share
    sales_dict['BEV'] = total_sales * BEV_share
    sales_dict['total'] = total_sales

    return sales_dict


def new_vehicle_sales_response(calendar_year, P):
    """
    Calculate new vehicle sales, relative to a reference sales volume and average new vehicle price
    :param P: a single price or a list-like of prices
    :return: total new vehicle sales volume at each price
    """
    from context_new_vehicle_market import ContextNewVehicleMarket

    if type(P) is list:
        import numpy as np
        P = np.array(P)

    if o2.options.session_is_reference and isinstance(P, float):
        ContextNewVehicleMarket.set_new_vehicle_price(calendar_year, P)

    Q0 = ContextNewVehicleMarket.new_vehicle_sales(calendar_year)
    P0 = ContextNewVehicleMarket.new_vehicle_prices(calendar_year)

    E = o2.options.new_vehicle_sales_response_elasticity

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

        init_fail = []

        from vehicles import VehicleFinal
        from vehicle_annual_data import VehicleAnnualData
        from manufacturers import Manufacturer  # needed for manufacturers table
        from consumer.market_classes import MarketClass  # needed for market class ID
        from fuels import Fuel  # needed for showroom fuel ID
        from cost_curves import CostCurve, input_template_name as cost_curve_template_name # needed for vehicle cost from CO2
        from cost_clouds import CostCloud  # needed for vehicle cost from CO2
        from context_new_vehicle_market import ContextNewVehicleMarket

        from GHG_standards_flat import input_template_name as flat_template_name
        from GHG_standards_footprint import input_template_name as footprint_template_name
        ghg_template_name = get_template_name(o2.options.ghg_standards_file)

        if ghg_template_name == flat_template_name:
            from GHG_standards_flat import GHGStandardFlat

            o2.options.GHG_standard = GHGStandardFlat
        elif ghg_template_name == footprint_template_name:
            from GHG_standards_footprint import GHGStandardFootprint

            o2.options.GHG_standard = GHGStandardFootprint
        else:
            init_fail.append('UNKNOWN GHG STANDARD "%s"' % ghg_template_name)

        SQABase.metadata.create_all(o2.engine)

        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        if get_template_name(o2.options.cost_file) == cost_curve_template_name:
            init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        else:
            init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        init_fail = init_fail + o2.options.GHG_standard.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)

        init_fail = init_fail + VehicleFinal.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        init_fail = init_fail + ContextNewVehicleMarket.init_database_from_file(
            o2.options.context_new_vehicle_market_file, verbose=o2.options.verbose)

        if not init_fail:
            o2.options.analysis_initial_year = VehicleFinal.get_max_model_year() + 1

            sales_demand = context_new_vehicle_sales(o2.options.analysis_initial_year)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
