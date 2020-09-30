"""
sales_gcam.py
=============



"""

from usepa_omega2 import *
import numpy as np

def get_demanded_shares(df):
    """

    :param df:
    :return:
    """
    from demanded_shares_gcam import DemandedSharesGCAM
    from market_classes import MarketClass

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta
    logit_exponent_mu = -8

    demanded_share_data = dict()
    # ToDo: These fuels items should be populated from the fuels class
    fuel_cost_gasoline = 3.5  # dollars per gallon
    fuel_cost_electricity = 0.12  # dollars per kWh
    carbon_intensity_gasoline = 8887  # g per CO2 per gallon
    carbon_intensity_electricity = 534  # g per kWh generated

    for cy in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
        tmp_sales_share_denominator_all_hauling = 0
        tmp_sales_share_denominator_all_nonhauling = 0

        for pass_num in [0, 1]:
            for market_class_id in MarketClass.market_classes:
                print('%s %s' % (cy, market_class_id))

                # for testing purposes, assign a dummy cost that increases over time. This will come from a generalized cost function
                vehicle_demanded_share = o2.session.query(DemandedSharesGCAM).filter(DemandedSharesGCAM.calendar_year == cy).filter(DemandedSharesGCAM.market_class_ID == market_class_id).one()
                tmp_pap = vehicle_demanded_share.price_amortization_period
                tmp_dr = vehicle_demanded_share.discount_rate
                tmp_annualization_factor = tmp_pap + tmp_pap/(((1 + tmp_pap)**tmp_dr) - 1)

                tmp_total_capital_costs = df[df.calendar_year == cy]['average_%s_cost' % sql_valid_name(market_class_id)].iloc[0]
                average_co2_gpmi = df[df.calendar_year == cy]['average_%s_co2_gpmi' % sql_valid_name(market_class_id)].iloc[0]

                if market_class_id == 'non hauling.BEV':
                    tmp_fuel_cost_per_VMT = fuel_cost_electricity * average_co2_gpmi / carbon_intensity_electricity
                    tmp_annual_o_m_costs = 1600
                elif market_class_id == 'hauling.BEV':
                    tmp_fuel_cost_per_VMT = fuel_cost_electricity * average_co2_gpmi / carbon_intensity_electricity
                    tmp_annual_o_m_costs = 1600
                elif market_class_id == 'non hauling.ICE':
                    tmp_fuel_cost_per_VMT = fuel_cost_gasoline * average_co2_gpmi / carbon_intensity_gasoline
                    tmp_annual_o_m_costs = 2000
                elif market_class_id == 'hauling.ICE':
                    tmp_fuel_cost_per_VMT = fuel_cost_gasoline * average_co2_gpmi / carbon_intensity_gasoline
                    tmp_annual_o_m_costs = 2000

                vehicle_demanded_share.consumer_generalized_cost_dollars = tmp_total_capital_costs
                tmp_annualized_capital_costs = tmp_annualization_factor * tmp_total_capital_costs
                tmp_annual_VMT = 12000

                tmp_total_non_fuel_costs_per_VMT = (tmp_annualized_capital_costs + tmp_annual_o_m_costs) / 1.383 / float(tmp_annual_VMT)
                tmp_total_cost_w_fuel_per_VMT = tmp_total_non_fuel_costs_per_VMT + tmp_fuel_cost_per_VMT
                tmp_total_cost_w_fuel_per_PMT = tmp_total_cost_w_fuel_per_VMT / 1.58
                tmp_sales_share_numerator = vehicle_demanded_share.share_weight * (tmp_total_cost_w_fuel_per_PMT ** logit_exponent_mu)

                if pass_num == 0:
                    if 'non hauling' in market_class_id:
                        tmp_sales_share_denominator_all_nonhauling = tmp_sales_share_numerator + \
                                                                     tmp_sales_share_denominator_all_nonhauling
                        vehicle_demanded_share.demanded_share = tmp_sales_share_denominator_all_nonhauling
                    else:
                        tmp_sales_share_denominator_all_hauling = tmp_sales_share_numerator + \
                                                                  tmp_sales_share_denominator_all_hauling
                        vehicle_demanded_share.demanded_share = tmp_sales_share_denominator_all_hauling
                else:
                    if 'non hauling' in market_class_id:
                        vehicle_demanded_share.demanded_share = tmp_sales_share_numerator / \
                                                                tmp_sales_share_denominator_all_nonhauling
                    else:
                        vehicle_demanded_share.demanded_share = tmp_sales_share_numerator / \
                                                                tmp_sales_share_denominator_all_hauling

                    if market_class_id not in demanded_share_data:
                        demanded_share_data[market_class_id] = []

                    demanded_share_data[market_class_id].append(o2.session.query(DemandedSharesGCAM.demanded_share).filter(DemandedSharesGCAM.calendar_year == cy).filter(DemandedSharesGCAM.market_class_ID == market_class_id).scalar())

    o2.session.commit()
    # write to summary file
    for market_class_id in MarketClass.market_classes:
        df['demanded_%s_share-gcam' % sql_valid_name(market_class_id)] = demanded_share_data[market_class_id]

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
