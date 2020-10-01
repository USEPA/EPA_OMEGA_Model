"""
sales_gcam.py
=============



"""

from usepa_omega2 import *
import numpy as np


def get_demanded_shares(market_class_data, calendar_year):
    """

    :param market_class_data: dict-like data structure with 'average_MC_cost' and 'average_MC_co2_gpmi' keys
                                where MC = market class ID
    :param calendar_year: calendar year to calculate market shares in
    :return: dict of demanded ICE/BEV share by hauling / non_hauling market segments
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

    sales_share_denominator_all_hauling = 0
    sales_share_denominator_all_nonhauling = 0

    for pass_num in [0, 1]:
        for market_class_id in MarketClass.market_classes:
            # for testing purposes, assign a dummy cost that increases over time. This will come from a generalized cost function
            gcam_data_cy = o2.session.query(DemandedSharesGCAM). \
                filter(DemandedSharesGCAM.calendar_year == calendar_year). \
                filter(DemandedSharesGCAM.market_class_ID == market_class_id).one()

            price_amortization_period = gcam_data_cy.price_amortization_period
            discount_rate = gcam_data_cy.discount_rate
            annualization_factor = price_amortization_period + \
                                   price_amortization_period / (((1 + price_amortization_period) ** discount_rate) - 1)

            total_capital_costs = market_class_data['average_%s_cost' % market_class_id]
            average_co2_gpmi = market_class_data['average_%s_co2_gpmi' % market_class_id]

            if market_class_id == 'non hauling.BEV':
                fuel_cost_per_VMT = fuel_cost_electricity * average_co2_gpmi / carbon_intensity_electricity
                annual_o_m_costs = 1600
            elif market_class_id == 'hauling.BEV':
                fuel_cost_per_VMT = fuel_cost_electricity * average_co2_gpmi / carbon_intensity_electricity
                annual_o_m_costs = 1600
            elif market_class_id == 'non hauling.ICE':
                fuel_cost_per_VMT = fuel_cost_gasoline * average_co2_gpmi / carbon_intensity_gasoline
                annual_o_m_costs = 2000
            elif market_class_id == 'hauling.ICE':
                fuel_cost_per_VMT = fuel_cost_gasoline * average_co2_gpmi / carbon_intensity_gasoline
                annual_o_m_costs = 2000

            gcam_data_cy.consumer_generalized_cost_dollars = total_capital_costs
            annualized_capital_costs = annualization_factor * total_capital_costs
            annual_VMT = float(gcam_data_cy.annual_VMT)

            total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / 1.383 / annual_VMT
            total_cost_w_fuel_per_VMT = total_non_fuel_costs_per_VMT + fuel_cost_per_VMT
            total_cost_w_fuel_per_PMT = total_cost_w_fuel_per_VMT / 1.58
            sales_share_numerator = gcam_data_cy.share_weight * (total_cost_w_fuel_per_PMT ** logit_exponent_mu)

            if pass_num == 0:
                if 'non hauling' in market_class_id:
                    sales_share_denominator_all_nonhauling = sales_share_numerator + sales_share_denominator_all_nonhauling
                else:
                    sales_share_denominator_all_hauling = sales_share_numerator + sales_share_denominator_all_hauling
            else:
                if 'non hauling' in market_class_id:
                    # gcam_data_cy.demanded_share = market_class_data[
                    #                                   'desired_non hauling share_frac'] * sales_share_numerator / sales_share_denominator_all_nonhauling
                    gcam_data_cy.demanded_share = sales_share_numerator / sales_share_denominator_all_nonhauling
                else:
                    # gcam_data_cy.demanded_share = market_class_data['desired_hauling share_frac'] * sales_share_numerator / sales_share_denominator_all_hauling
                    gcam_data_cy.demanded_share = sales_share_numerator / sales_share_denominator_all_hauling

                market_class_data['demanded_%s_share_frac' % market_class_id] = gcam_data_cy.demanded_share

    return market_class_data.copy()


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
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + DemandedSharesGCAM.init_database_from_file(o2.options.demanded_shares_file,
                                                                           verbose=o2.options.verbose)
        init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)
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
