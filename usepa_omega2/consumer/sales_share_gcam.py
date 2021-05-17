"""
sales_gcam.py
=============



"""

from usepa_omega2 import *
import matplotlib.pyplot as plt

def get_demanded_shares(market_class_data, calendar_year):
    """

    :param market_class_data: dict-like data structure with 'average_MC_cost' and 'average_MC_co2_gpmi' keys
                                where MC = market class ID
    :param calendar_year: calendar year to calculate market shares in
    :return: dict of demanded ICE/BEV share by hauling / non_hauling market segments
    """
    from consumer.demanded_shares_gcam import DemandedSharesGCAM
    from consumer.market_classes import MarketClass
    from fuels import Fuel

    if o2.options.flat_context:
        calendar_year = o2.options.flat_context_year

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta

    carbon_intensity_gasoline = Fuel.get_fuel_attributes('pump gasoline', 'co2_tailpipe_emissions_grams_per_unit')

    sales_share_denominator_all_hauling = 0
    sales_share_denominator_all_nonhauling = 0

    sales_share_numerator = dict()

    for pass_num in [0, 1]:
        for market_class_id in MarketClass.market_classes:
            if pass_num == 0:
                fuel_cost = market_class_data['average_fuel_price_%s' % market_class_id]

                gcam_data_cy = DemandedSharesGCAM.get_gcam_params(calendar_year, market_class_id)

                logit_exponent_mu = gcam_data_cy.logit_exponent_mu

                price_amortization_period = gcam_data_cy.price_amortization_period
                discount_rate = gcam_data_cy.discount_rate
                annualization_factor = discount_rate + discount_rate / (((1 + discount_rate) ** price_amortization_period) - 1)

                total_capital_costs = market_class_data['average_modified_cross_subsidized_price_%s' % market_class_id]
                average_co2_gpmi = market_class_data['average_co2_gpmi_%s' % market_class_id]
                average_kwh_pmi = market_class_data['average_kwh_pmi_%s' % market_class_id]

                if market_class_id == 'non_hauling.BEV':
                    fuel_cost_per_VMT = fuel_cost * average_kwh_pmi
                    annual_o_m_costs = gcam_data_cy.o_m_costs
                elif market_class_id == 'hauling.BEV':
                    fuel_cost_per_VMT = fuel_cost * average_kwh_pmi
                    annual_o_m_costs = gcam_data_cy.o_m_costs
                elif market_class_id == 'non_hauling.ICE':
                    fuel_cost_per_VMT = fuel_cost * average_co2_gpmi / carbon_intensity_gasoline
                    annual_o_m_costs = gcam_data_cy.o_m_costs
                elif market_class_id == 'hauling.ICE':
                    fuel_cost_per_VMT = fuel_cost * average_co2_gpmi / carbon_intensity_gasoline
                    annual_o_m_costs = gcam_data_cy.o_m_costs

                # consumer_generalized_cost_dollars = total_capital_costs
                annualized_capital_costs = annualization_factor * total_capital_costs
                annual_VMT = float(gcam_data_cy.annual_VMT)

                total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / 1.383 / annual_VMT
                total_cost_w_fuel_per_VMT = total_non_fuel_costs_per_VMT + fuel_cost_per_VMT
                total_cost_w_fuel_per_PMT = total_cost_w_fuel_per_VMT / gcam_data_cy.average_occupancy
                sales_share_numerator[market_class_id] = gcam_data_cy.share_weight * (total_cost_w_fuel_per_PMT ** logit_exponent_mu)

                market_class_data['consumer_generalized_cost_dollars_%s' % market_class_id] = total_cost_w_fuel_per_PMT

                # plt.figure()
                # plt.plot(total_cost_w_fuel_per_PMT)
                # plt.title('%s total_cost_w_fuel_per_PMT' % market_class_id)

                if 'non_hauling' in market_class_id.split('.'):
                    sales_share_denominator_all_nonhauling += sales_share_numerator[market_class_id]
                else:
                    sales_share_denominator_all_hauling += sales_share_numerator[market_class_id]
            else:
                if 'non_hauling' in market_class_id.split('.'):
                    demanded_share = sales_share_numerator[market_class_id] / sales_share_denominator_all_nonhauling
                    demanded_absolute_share = demanded_share * market_class_data['producer_abs_share_frac_non_hauling']
                else:
                    demanded_share = sales_share_numerator[market_class_id] / sales_share_denominator_all_hauling
                    demanded_absolute_share = demanded_share * market_class_data['producer_abs_share_frac_hauling']

                market_class_data['consumer_share_frac_%s' % market_class_id] = demanded_share
                market_class_data['consumer_abs_share_frac_%s' % market_class_id] = demanded_absolute_share

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
        from consumer.market_classes import MarketClass  # needed for market class ID
        from fuels import Fuel  # needed for showroom fuel ID
        from consumer.demanded_shares_gcam import DemandedSharesGCAM
        from GHG_standards_footprint import GHGStandardFootprint
        from cost_clouds import CostCloud

        o2.options.GHG_standard = GHGStandardFootprint
        o2.options.ghg_standards_file = 'test_inputs/ghg_standards-footprint.csv'
        from vehicles import VehicleFinal
        from vehicle_annual_data import VehicleAnnualData

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + DemandedSharesGCAM.init_database_from_file(o2.options.demanded_shares_file,
                                                                           verbose=o2.options.verbose)
        init_fail = init_fail + CostCloud.init_cost_clouds_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                             verbose=o2.options.verbose)
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)
        init_fail = init_fail + VehicleFinal.init_database_from_file(o2.options.vehicles_file,
                                                                     o2.options.vehicle_onroad_calculations_file,
                                                                     verbose=o2.options.verbose)

        if not init_fail:
            o2.options.analysis_initial_year = 2021
            o2.options.analysis_final_year = 2035
            o2.options.database_dump_folder = '__dump'

            dump_omega_db_to_csv(o2.options.database_dump_folder)

            # test market shares at different CO2 and price levels
            mcd = pd.DataFrame()
            for mc in MarketClass.market_classes:
                mcd['average_%s_cost' % mc] = [35000, 25000]
                mcd['average_%s_co2_gpmi' % mc] = [125, 150]
                mcd['average_%s_fuel_price' % mc] = [2.75, 3.25]
                mcd['producer_non_hauling_share_frac'] = [0.8, 0.85]
                mcd['producer_hauling_share_frac'] = [0.2, 0.15]

            share_demand = get_demanded_shares(mcd, o2.options.analysis_initial_year)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
