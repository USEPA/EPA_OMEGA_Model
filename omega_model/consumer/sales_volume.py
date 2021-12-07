"""

**Routines to retrieve overall sales from the context and total consumer sales response as a function of total
sales-weighted generalized cost.**

----

**CODE**

"""

from omega_model import *


def context_new_vehicle_sales(calendar_year):
    """
    Get new vehicle sales from the context.

    Args:
        calendar_year (int): the year to get sales for

    Returns:
        dict of vehicle sales by non-responsive market category, and ``total``

    """
    #  PHASE0: hauling/non, EV/ICE, We don't need shared/private for beta
    from context.new_vehicle_market import NewVehicleMarket

    sales_dict = dict()

    if omega_globals.options.flat_context:
        calendar_year = omega_globals.options.flat_context_year

    # calculate sales by non-responsive market category as a function of context size class sales and
    # base year share of those vehicles in the non-responsive market category
    for nrmc in NewVehicleMarket.context_size_class_info_by_nrmc:
        sales_dict[nrmc] = 0
        for csc in NewVehicleMarket.context_size_class_info_by_nrmc[nrmc]:
            sales_dict[nrmc] += NewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=csc) * \
                                     NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['share']

    # get total sales from context
    sales_dict['total'] = NewVehicleMarket.new_vehicle_sales(calendar_year)

    return sales_dict


def new_vehicle_sales_response(calendar_year, compliance_id, P, update_context_new_vehicle_generalized_cost=True):
    """
    Calculate new vehicle sales fraction relative to a reference sales volume and average new vehicle generalized cost.
    Updates generalized cost table associated with the reference session so those costs can become the reference
    costs for subsequent sessions.

    Args:
        calendar_year (int): the calendar year to calculate sales in
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        P ($, [$]): a single price or a list/vector of prices
        update_context_new_vehicle_generalized_cost (bool): update context new vehicle generalized cost (P0) if ``True``

    Returns:
        Relative new vehicle sales volume at each price, e.g. ``0.97``, ``1.03``, etc

    """
    from context.new_vehicle_market import NewVehicleMarket

    if type(P) is list:
        import numpy as np
        P = np.array(P)

    if omega_globals.options.session_is_reference and isinstance(P, float) and \
            update_context_new_vehicle_generalized_cost:
        NewVehicleMarket.set_context_new_vehicle_generalized_cost(calendar_year, compliance_id, P)

    if isinstance(P, float):
        NewVehicleMarket.set_session_new_vehicle_generalized_cost(calendar_year, compliance_id, P)

    Q0 = 1
    P0 = NewVehicleMarket.get_context_new_vehicle_generalized_cost(calendar_year, compliance_id)

    E = omega_globals.options.new_vehicle_price_elasticity_of_demand

    M = -(Q0*E - Q0) / (P0/E - P0)  # slope of linear response

    Q = Q0 + M * (P-P0)  # point-slope equation of a line

    return Q/Q0


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
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

        from producer.vehicles import VehicleFinal, DecompositionAttributes
        from producer.vehicle_annual_data import VehicleAnnualData
        from producer.manufacturers import Manufacturer  # needed for manufacturers table
        from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        from context.cost_clouds import CostCloud  # needed for vehicle cost from CO2e
        from context.new_vehicle_market import NewVehicleMarket
        from omega_model.omega import init_user_definable_decomposition_attributes, get_module

        module_name = get_template_name(omega_globals.options.policy_targets_file)
        omega_globals.options.VehicleTargets = get_module(module_name).VehicleTargets

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = get_module(module_name).MarketClass

        module_name = get_template_name(omega_globals.options.offcycle_credits_file)
        omega_globals.options.OffCycleCredits = get_module(module_name).OffCycleCredits

        init_fail += init_user_definable_decomposition_attributes(omega_globals.options.verbose)

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file, verbose=omega_globals.options.verbose)

        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.vehicle_simulation_results_and_costs_file, verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                                         verbose=omega_globals.options.verbose)

        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.onroad_vehicle_calculations_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += NewVehicleMarket.init_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = VehicleFinal.get_max_model_year() + 1

            sales_demand = context_new_vehicle_sales(omega_globals.options.analysis_initial_year)
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
