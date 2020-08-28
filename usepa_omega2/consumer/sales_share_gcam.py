"""
sales_gcam.py
===========



"""

from usepa_omega2 import *
import numpy as np

def get_demanded_shares(df):
    """

    :param df:
    :return:
    """
    from demanded_shares_gcam import DemandedSharesGCAM

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta
    logit_exponent_mu = -8
    df = df.fillna(value=np.nan) # not sure why the df has 'None' values and nan values
    demanded_share_data = dict()
    # ToDo: These fuels items should be populated from the fuels class
    fuel_cost_gasoline = 3.5 # dollars per gallon
    fuel_cost_electricity = 0.12 # dollars per kWh
    carbon_intensity_gasoline = 8887 # g per CO2 per gallon
    carbon_intensity_electricity = 534 # g per kWh generated

    for cy in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
        tmp_sales_share_denominator_all_hauling = 0
        tmp_sales_share_denominator_all_nonhauling = 0
        # print(cy)
        market_class_ids = o2.session.query(DemandedSharesGCAM.market_class_ID).filter(DemandedSharesGCAM.calendar_year == cy).distinct()
        for pass_num in range(1,3):
            for market_class_id in market_class_ids:
                # for testing purposes, assign a dummy cost that increases over time. This will come from a generalized cost function
                vehicle_demanded_share = []
                vehicle_demanded_share = o2.session.query(DemandedSharesGCAM).filter(DemandedSharesGCAM.calendar_year == cy).filter(DemandedSharesGCAM.market_class_ID == market_class_id[0])
                tmp_pap = vehicle_demanded_share[0].price_amortization_period
                tmp_dr = vehicle_demanded_share[0].discount_rate
                tmp_annualization_factor = tmp_pap + tmp_pap/(((1 + tmp_pap)**tmp_dr) - 1)
                # this cost assignment below is temporary -- will be replaced with vehicle costs from producer module
                if (market_class_id[0]=='BEV non hauling'):
                    tmp_total_capital_costs = df[df.calendar_year == cy].average_bev_non_hauling_cost
                    tmp_fuel_cost_per_VMT = fuel_cost_electricity * df[df.calendar_year == cy].average_bev_non_hauling_co2_gpmi / carbon_intensity_electricity
                    #tmp_total_capital_costs = 45000 + 500 * (cy - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 1600
                    #tmp_fuel_cost_per_VMT = 0.03
                elif (market_class_id[0] == 'BEV hauling'):
                    tmp_total_capital_costs = df[df.calendar_year == cy].average_bev_hauling_cost
                    tmp_fuel_cost_per_VMT = fuel_cost_electricity * df[df.calendar_year == cy].average_bev_hauling_co2_gpmi / carbon_intensity_electricity
                    #tmp_total_capital_costs = 65000 + 500 * (cy - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 1600
                    #tmp_fuel_cost_per_VMT = 0.04
                elif (market_class_id[0] == 'ICE non hauling'):
                    tmp_total_capital_costs = df[df.calendar_year == cy].average_ice_non_hauling_cost
                    tmp_fuel_cost_per_VMT = fuel_cost_gasoline * df[df.calendar_year == cy].average_ice_non_hauling_co2_gpmi / carbon_intensity_gasoline
                    #tmp_total_capital_costs = 35000 + 1000 * (cy - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 2000
                    #tmp_fuel_cost_per_VMT = 0.10
                elif (market_class_id[0] == 'ICE hauling'):
                    tmp_total_capital_costs = df[df.calendar_year == cy].average_ice_hauling_cost
                    tmp_fuel_cost_per_VMT = fuel_cost_gasoline * df[df.calendar_year == cy].average_ice_hauling_co2_gpmi / carbon_intensity_gasoline
                    #tmp_total_capital_costs = 50000 + 1000 * (cy - o2.options.analysis_initial_year)
                    tmp_annual_o_m_costs = 2000
                    #tmp_fuel_cost_per_VMT = 0.10
                vehicle_demanded_share[0].consumer_generalized_cost_dollars = tmp_total_capital_costs
                tmp_annualized_capital_costs = tmp_annualization_factor * tmp_total_capital_costs
                tmp_annual_VMT = 12000
                #tmp_annual_VMT = vehicle_demanded_share[0].annual_VMT
                tmp_total_non_fuel_costs_per_VMT = (tmp_annualized_capital_costs + tmp_annual_o_m_costs)/1.383/float(tmp_annual_VMT)
                tmp_total_cost_w_fuel_per_VMT = tmp_total_non_fuel_costs_per_VMT + tmp_fuel_cost_per_VMT
                tmp_total_cost_w_fuel_per_PMT = tmp_total_cost_w_fuel_per_VMT / 1.58
                tmp_sales_share_numerator = vehicle_demanded_share[0].share_weight * (tmp_total_cost_w_fuel_per_PMT ** logit_exponent_mu)
                if (pass_num == 1):
                    if (market_class_id[0] == 'ICE hauling' or market_class_id[0] == 'BEV hauling'):
                        tmp_sales_share_denominator_all_hauling = tmp_sales_share_numerator + tmp_sales_share_denominator_all_hauling
                        vehicle_demanded_share[0].demanded_share = tmp_sales_share_denominator_all_hauling
                    elif (market_class_id[0] == 'ICE non hauling' or market_class_id[0] == 'BEV non hauling'):
                        tmp_sales_share_denominator_all_nonhauling = tmp_sales_share_numerator + tmp_sales_share_denominator_all_nonhauling
                        vehicle_demanded_share[0].demanded_share = tmp_sales_share_denominator_all_nonhauling
                    o2.session.commit()
                else:
                    if (market_class_id[0] == 'ICE hauling' or market_class_id[0] == 'BEV hauling'):
                        vehicle_demanded_share[0].demanded_share = tmp_sales_share_numerator/tmp_sales_share_denominator_all_hauling
                    elif (market_class_id[0] == 'ICE non hauling' or market_class_id[0] == 'BEV non hauling'):
                        vehicle_demanded_share[0].demanded_share = tmp_sales_share_numerator / tmp_sales_share_denominator_all_nonhauling
                    o2.session.commit()
                    if market_class_id[0] not in demanded_share_data:
                        demanded_share_data[market_class_id[0]] = []
                    demanded_share_data[market_class_id[0]].append(o2.session.query(DemandedSharesGCAM.demanded_share).filter(DemandedSharesGCAM.calendar_year == cy).filter(DemandedSharesGCAM.market_class_ID == market_class_id[0]).scalar())
                    o2.session.commit()
    # write to summary file
    for market_class_id in market_class_ids:
        df['demanded_%s_share-gcam' % sql_valid_name(market_class_id[0])] = demanded_share_data[market_class_id[0]]
        o2.session.commit()
    return df

if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        from manufacturers import Manufacturer  # needed for manufacturers table
        from market_classes import MarketClass  # needed for market class ID
        from fuels import Fuel  # needed for showroom fuel ID
        from demanded_shares_gcam import DemandedSharesGCAM
        from cost_curves import CostCurve
        from GHG_standards_footprint import GHGStandardFootprint
        o2.options.GHG_standard = GHGStandardFootprint
        o2.options.ghg_standards_file = 'sample_inputs/ghg_standards-footprint.csv'
        from vehicles import Vehicle
        from vehicle_annual_data import VehicleAnnualData

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file, verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file, verbose=o2.options.verbose)
        init_fail = init_fail + DemandedSharesGCAM.init_database_from_file(o2.options.demanded_shares_file, verbose=o2.options.verbose)
        init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file, verbose=o2.options.verbose)
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)
        init_fail = init_fail + Vehicle.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        if not init_fail:
            o2.options.analysis_initial_year = 2021
            o2.options.analysis_final_year = 2035
            o2.options.database_dump_folder = '__dump'
            # share_demand = get_demanded_shares(o2.options.analysis_initial_year)
            dump_omega_db_to_csv(o2.options.database_dump_folder)
        else:
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
