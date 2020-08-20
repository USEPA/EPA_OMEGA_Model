"""
sales_gcam.py
===========



"""

from usepa_omega2 import *

def demand_sales(model_year):
    """
    :param session: database session
    :param model_year: not used, for now
    :return: dict of sales by consumer (market) categories
    """

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta
    logit_exponent_mu = -8
    for calendar_year in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
        tmp_sales_share_denominator_all_market_classes = 0
        print(calendar_year)
        market_class_ids = o2.session.query(DemandedSalesAnnualData.market_class_ID).filter(DemandedSalesAnnualData.calendar_year == calendar_year).distinct()
        for pass_num in range(1,3):
            for market_class_id in market_class_ids:
                # for testing purposes, assign a dummy cost that increases over time. This will come from a generalized cost function
                vehicle_demanded_sales_annual_data = o2.session.query(DemandedSalesAnnualData).filter(DemandedSalesAnnualData.calendar_year == calendar_year).filter(DemandedSalesAnnualData.market_class_ID == market_class_id[0])
                tmp_pap = vehicle_demanded_sales_annual_data[0].price_amortization_period
                tmp_dr = vehicle_demanded_sales_annual_data[0].discount_rate
                tmp_annualization_factor = tmp_pap + tmp_pap/(((1 + tmp_pap)**tmp_dr) - 1)
                # this cost assignment below is temporary -- will be replaced with vehicle costs from producer module
                if (market_class_id[0]=='BEV non hauling'):
                    tmp_total_capital_costs = 45000 + 500 * (calendar_year - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 1600
                    tmp_fuel_cost_per_VMT = 0.03
                elif (market_class_id[0] == 'BEV hauling'):
                    tmp_total_capital_costs = 65000 + 500 * (calendar_year - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 1600
                    tmp_fuel_cost_per_VMT = 0.04
                elif (market_class_id[0] == 'ICE non hauling'):
                    tmp_total_capital_costs = 35000 + 1000 * (calendar_year - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 2000
                    tmp_fuel_cost_per_VMT = 0.10
                elif (market_class_id[0] == 'ICE hauling'):
                    tmp_total_capital_costs = 50000 + 1000 * (calendar_year - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 2000
                    tmp_fuel_cost_per_VMT = 0.10
                vehicle_demanded_sales_annual_data[0].consumer_generalized_cost_dollars = tmp_total_capital_costs
                tmp_annualized_capital_costs = tmp_annualization_factor * tmp_total_capital_costs
                tmp_annual_VMT = vehicle_demanded_sales_annual_data[0].annual_VMT
                tmp_total_non_fuel_costs_per_VMT = (tmp_annualized_capital_costs + tmp_annual_o_m_costs)/1.383/float(tmp_annual_VMT)
                tmp_total_cost_w_fuel_per_VMT = tmp_total_non_fuel_costs_per_VMT + tmp_fuel_cost_per_VMT
                tmp_total_cost_w_fuel_per_PMT = tmp_total_cost_w_fuel_per_VMT / 1.58
                tmp_sales_share_numerator = vehicle_demanded_sales_annual_data[0].share_weight * (tmp_total_cost_w_fuel_per_PMT ** logit_exponent_mu)
                if (pass_num == 1):
                    tmp_sales_share_denominator_all_market_classes = tmp_sales_share_numerator + tmp_sales_share_denominator_all_market_classes
                    vehicle_demanded_sales_annual_data[0].demanded_sales_count = tmp_sales_share_denominator_all_market_classes
                    o2.session.commit()
                else:
                    vehicle_demanded_sales_annual_data[0].demanded_sales_count = tmp_sales_share_numerator/tmp_sales_share_denominator_all_market_classes
                    o2.session.commit()

if __name__ == '__main__':
    if '__file__' in locals():
        print(fileio.get_filenameext(__file__))

    # set up global variables:
    o2.options = OMEGARuntimeOptions()
    init_omega_db()
    omega_log.init_logfile()

    from manufacturers import Manufacturer  # needed for manufacturers table
    from market_classes import MarketClass  # needed for market class ID
    from fuels import Fuel  # needed for showroom fuel ID
    from demanded_sales_annual_data import DemandedSalesAnnualData
    from cost_curves import CostCurve
    from GHG_standards_footprint import GHGStandardFootprint
    o2.options.GHG_standard = GHGStandardFootprint
    o2.options.ghg_standards_file = 'input_templates/ghg_standards-footprint.csv'
    from vehicles import Vehicle
    from vehicle_annual_data import VehicleAnnualData

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file, verbose=o2.options.verbose)
    init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file, verbose=o2.options.verbose)
    init_fail = init_fail + DemandedSalesAnnualData.init_database_from_file(o2.options.demanded_sales_annual_data_file, verbose=o2.options.verbose)
    init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
    init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file, verbose=o2.options.verbose)
    init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)
    init_fail = init_fail + Vehicle.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

    if not init_fail:
        o2.options.analysis_initial_year = 2021
        o2.options.analysis_final_year = 2050
        o2.options.database_dump_folder = '__dump'
        sales_demand = demand_sales(o2.options.analysis_initial_year)
        dump_omega_db_to_csv(o2.options.database_dump_folder)
