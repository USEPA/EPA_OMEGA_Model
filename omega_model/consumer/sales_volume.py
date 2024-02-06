"""

**Routines to retrieve overall sales from the context and total consumer sales response as a function of total
sales-weighted generalized cost.**

----

**CODE**

"""

from omega_model import *


_cache = dict()


def context_new_vehicle_sales(calendar_year):
    """
    Get new vehicle sales from the context.

    Args:
        calendar_year (int): the year to get sales for

    Returns:
        dict of vehicle sales by non-responsive market category, and ``total``

    """
    #  PHASE0: hauling/non, EV/ICE, We don't need shared/private for beta

    if calendar_year not in _cache:
        from context.new_vehicle_market import NewVehicleMarket

        sales_dict = dict()

        if omega_globals.options.flat_context:
            calendar_year = omega_globals.options.flat_context_year

        # calculate sales by non-responsive market category as a function of context size class sales and
        # base year share of those vehicles in the non-responsive market category
        for nrmc in NewVehicleMarket.context_size_class_info_by_nrmc:
            sales_dict[nrmc] = 0
            for csc in NewVehicleMarket.context_size_class_info_by_nrmc[nrmc]:
                sales_dict[nrmc] += NewVehicleMarket.new_vehicle_data(calendar_year, context_size_class=csc) * \
                                    NewVehicleMarket.context_size_class_info_by_nrmc[nrmc][csc]['share']

        for rc in legacy_reg_classes:
            sales_dict[rc] = NewVehicleMarket.new_vehicle_data(calendar_year, context_size_class=None,
                                                               context_reg_class=rc)

        # get total sales from context
        sales_dict['total'] = NewVehicleMarket.new_vehicle_data(calendar_year)

        for nrmc in NewVehicleMarket.context_size_class_info_by_nrmc:
            sales_dict['%s_share' % nrmc] = sales_dict[nrmc] / sales_dict['total']

        for rc in legacy_reg_classes:
            sales_dict['%s_share' % rc] = sales_dict[rc] / sales_dict['total']

        _cache[calendar_year] = sales_dict

    return _cache[calendar_year]


def log_new_vehicle_generalized_cost(calendar_year, compliance_id, P):
    """

    Args:
        calendar_year (int): the calendar year to calculate sales in
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        P ($, [$]): a single price representing the final production decision average new vehicle generalized cost

    """
    from context.new_vehicle_market import NewVehicleMarket

    if omega_globals.options.session_is_reference:
        NewVehicleMarket.set_context_new_vehicle_generalized_cost(calendar_year, compliance_id, P)

    NewVehicleMarket.set_session_new_vehicle_generalized_cost(calendar_year, compliance_id, P)


def new_vehicle_sales_response(calendar_year, compliance_id, P):
    """
    Calculate new vehicle sales fraction relative to a reference sales volume and average new vehicle generalized cost.
    Updates generalized cost table associated with the reference session so those costs can become the reference
    costs for subsequent sessions.

    Args:
        calendar_year (int): the calendar year to calculate sales in
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        P ($, [$]): a single price or a list/vector of prices

    Returns:
        Relative new vehicle sales volume at each price, e.g. ``0.97``, ``1.03``, etc

    """
    from context.new_vehicle_market import NewVehicleMarket

    if omega_globals.options.session_is_reference:
        # disable elasticity for context session
        return 1.0

    else:
        if type(P) is list:
            P = np.array(P)

        Q0 = 1
        P0 = NewVehicleMarket.get_context_new_vehicle_generalized_cost(calendar_year, compliance_id)

        E = omega_globals.options.new_vehicle_price_elasticity_of_demand

        # M = -(Q0*E - Q0) / (P0/E - P0)  # slope of linear response
        # Q = Q0 + M * (P-P0)  # point-slope equation of a line

        Q = 1 + E * (P - P0)/P0

        return Q/Q0


def init_sales_volume():
    """
    Initialize the module by clearing the cache.

    """
    _cache.clear()


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)
        # override reg_classes from __init__.py:
        importlib.import_module('omega_model').reg_classes = omega_globals.options.RegulatoryClasses.reg_classes

        from producer.vehicle_aggregation import VehicleAggregation
        from producer.vehicles import Vehicle, DecompositionAttributes
        from producer.vehicle_annual_data import VehicleAnnualData
        from producer.manufacturers import Manufacturer  # needed for manufacturers table
        from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        from context.new_vehicle_market import NewVehicleMarket
        from context.mass_scaling import MassScaling
        from context.body_styles import BodyStyles
        from context.glider_cost import GliderCost
        from policy.drive_cycles import DriveCycles
        from policy.policy_fuels import PolicyFuel
        from context.ip_deflators import ImplicitPriceDeflators
        from omega_model.omega import init_user_definable_decomposition_attributes, get_module

        module_name = get_template_name(omega_globals.options.policy_targets_file)
        omega_globals.options.VehicleTargets = get_module(module_name).VehicleTargets

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = get_module(module_name).MarketClass

        module_name = get_template_name(omega_globals.options.offcycle_credits_file)
        omega_globals.options.OffCycleCredits = get_module(module_name).OffCycleCredits

        module_name = get_template_name(omega_globals.options.ice_vehicle_simulation_results_file)
        omega_globals.options.CostCloud = get_module(module_name).CostCloud

        module_name = get_template_name(omega_globals.options.sales_share_file)
        omega_globals.options.SalesShare = get_module(module_name).SalesShare

        module_name = get_template_name(omega_globals.options.powertrain_cost_input_file)
        omega_globals.options.PowertrainCost = get_module(module_name).PowertrainCost

        init_fail += init_user_definable_decomposition_attributes(omega_globals.options.verbose)

        init_fail += Manufacturer.init_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.SalesShare.init_from_file(omega_globals.options.sales_share_file,
                                                                     verbose=omega_globals.options.verbose)

        init_fail += BodyStyles.init_from_file(omega_globals.options.body_styles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += MassScaling.init_from_file(omega_globals.options.mass_scaling_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += NewVehicleMarket.init_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        init_fail += ImplicitPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += GliderCost.init_from_file(omega_globals.options.glider_cost_input_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.PowertrainCost.init_from_file(omega_globals.options.powertrain_cost_input_file,
                                                   verbose=omega_globals.options.verbose)

        # init drive cycles PRIOR to CostCloud since CostCloud needs the drive cycle names for validation
        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.CostCloud.\
            init_cost_clouds_from_files(omega_globals.options.ice_vehicle_simulation_results_file,
                                        omega_globals.options.bev_vehicle_simulation_results_file,
                                        omega_globals.options.phev_vehicle_simulation_results_file,
                                        verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                                         verbose=omega_globals.options.verbose)

        init_fail += VehicleAggregation.init_from_file(omega_globals.options.vehicles_file,
                                                       verbose=omega_globals.options.verbose)

        init_fail += Vehicle.init_from_file(omega_globals.options.onroad_vehicle_calculations_file,
                                                 verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = 2024

            sales_demand = context_new_vehicle_sales(omega_globals.options.analysis_initial_year)

            print_dict(sales_demand)
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
