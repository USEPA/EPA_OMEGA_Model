"""

**Routines to retrieve overall sales from the context and total consumer sales response as a function of total
sales-weighted generalized cost.**

----

**CODE**

"""

from omega_model import *


def calc_generalized_cost(cost_factors):
    """
    Placeholder for consumer generalized cost calculations.

    Args:
        cost_factors: data to base costs on

    Returns:
        nothing yet

    """
    pass


def context_new_vehicle_sales(calendar_year):
    """
    Get new vehicle sales from the context.

    Args:
        calendar_year (int): the year to get sales for

    Returns:
        dict of vehicle sales

    """
    #  PHASE0: hauling/non, EV/ICE, We don't need shared/private for beta
    from context.new_vehicle_market import NewVehicleMarket

    sales_dict = dict()

    if omega_globals.options.flat_context:
        calendar_year = omega_globals.options.flat_context_year

    # get total sales from context
    total_sales = NewVehicleMarket.new_vehicle_sales(calendar_year)

    # pulling in hauling sales, non_hauling = total minus hauling
    hauling_sales = 0
    for hsc in NewVehicleMarket.hauling_context_size_class_info:
        hauling_sales += NewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=hsc) * \
                         NewVehicleMarket.hauling_context_size_class_info[hsc]['hauling_share']

    sales_dict['hauling'] = hauling_sales
    sales_dict['non_hauling'] = total_sales - hauling_sales
    sales_dict['total'] = total_sales

    return sales_dict


def new_vehicle_sales_response(calendar_year, P):
    """
    Calculate new vehicle sales, relative to a reference sales volume and average new vehicle price.
    Updates generalized cost table associated with the reference session so those costs can become the reference
    costs for subsequent sessions.

    Args:
        calendar_year (int):
        P ($, [$]): a single price or a list/vector of prices

    Returns:
        Total new vehicle sales volume at each price.

    """
    from context.new_vehicle_market import NewVehicleMarket

    if type(P) is list:
        import numpy as np
        P = np.array(P)

    if omega_globals.options.session_is_reference and isinstance(P, float):
        NewVehicleMarket.set_new_vehicle_generalized_cost(calendar_year, P)

    Q0 = NewVehicleMarket.new_vehicle_sales(calendar_year)
    P0 = NewVehicleMarket.new_vehicle_generalized_cost(calendar_year)

    E = omega_globals.options.new_vehicle_sales_response_elasticity

    M = -(Q0*E - Q0) / (P0/E - P0)  # slope of linear response

    Q = Q0 + M * (P-P0)  # point-slope equation of a line

    return Q


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)
        # override reg_classes from __init__.py:
        importlib.import_module('omega_model').reg_classes = omega_globals.options.RegulatoryClasses.reg_classes

        from producer.vehicles import VehicleFinal
        from producer.vehicle_annual_data import VehicleAnnualData
        from producer.manufacturers import Manufacturer  # needed for manufacturers table
        from consumer.market_classes import MarketClass  # needed for market class ID
        from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        from context.cost_clouds import CostCloud  # needed for vehicle cost from CO2
        from context.new_vehicle_market import NewVehicleMarket

        module_name = get_template_name(omega_globals.options.policy_targets_file)
        omega_globals.options.PolicyTargets = importlib.import_module(module_name).Targets

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file, verbose=omega_globals.options.verbose)

        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.cost_file, verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.PolicyTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                                        verbose=omega_globals.options.verbose)

        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.vehicle_onroad_calculations_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += NewVehicleMarket.init_database_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = VehicleFinal.get_max_model_year() + 1

            sales_demand = context_new_vehicle_sales(omega_globals.options.analysis_initial_year)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
