"""


----

**CODE**

"""

from omega_model import *


def get_demanded_shares(market_class_data, calendar_year):
    """

    :param market_class_data: dict-like data structure with 'average_MC_cost' and 'average_MC_co2e_gpmi' keys
                                where MC = market class ID
    :param calendar_year: calendar year to calculate market shares in
    :return: dict of demanded ICE/BEV share by hauling / non_hauling market segments
    """
    from consumer.demanded_shares_gcam import DemandedSharesGCAM
    from consumer.market_classes import MarketClass
    from context.onroad_fuels import OnroadFuel

    if omega_globals.options.flat_context:
        calendar_year = omega_globals.options.flat_context_year

    #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta

    sales_share_denominator_all_hauling = 0
    sales_share_denominator_all_nonhauling = 0

    sales_share_numerator = dict()

    for pass_num in [0, 1]:
        for market_class_id in MarketClass.market_classes:
            if pass_num == 0:
                fuel_cost = market_class_data['average_fuel_price_%s' % market_class_id]

                gcam_data_cy = DemandedSharesGCAM.get_gcam_params(calendar_year, market_class_id)

                logit_exponent_mu = gcam_data_cy.logit_exponent_mu

                price_amortization_period = float(gcam_data_cy.price_amortization_period)
                discount_rate = gcam_data_cy.discount_rate
                annualization_factor = discount_rate + discount_rate / (
                        ((1 + discount_rate) ** price_amortization_period) - 1)

                total_capital_costs = market_class_data['average_modified_cross_subsidized_price_%s' % market_class_id]
                average_co2e_gpmi = market_class_data['average_co2e_gpmi_%s' % market_class_id]
                average_kwh_pmi = market_class_data['average_kwh_pmi_%s' % market_class_id]

                carbon_intensity_gasoline = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                          'direct_co2e_grams_per_unit')

                refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                  'refuel_efficiency')

                recharge_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'US electricity',
                                                                    'refuel_efficiency')

                annual_o_m_costs = gcam_data_cy.o_m_costs

                # TODO: will eventually need utility factor for PHEVs here
                fuel_cost_per_VMT = fuel_cost * average_kwh_pmi / recharge_efficiency
                fuel_cost_per_VMT += fuel_cost * average_co2e_gpmi / carbon_intensity_gasoline / refuel_efficiency

                # consumer_generalized_cost_dollars = total_capital_costs
                annualized_capital_costs = annualization_factor * total_capital_costs
                annual_VMT = float(gcam_data_cy.annual_VMT)

                total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / 1.383 / annual_VMT
                total_cost_w_fuel_per_VMT = total_non_fuel_costs_per_VMT + fuel_cost_per_VMT
                total_cost_w_fuel_per_PMT = total_cost_w_fuel_per_VMT / gcam_data_cy.average_occupancy
                sales_share_numerator[market_class_id] = gcam_data_cy.share_weight * (
                        total_cost_w_fuel_per_PMT ** logit_exponent_mu)

                market_class_data['consumer_generalized_cost_dollars_%s' % market_class_id] = total_cost_w_fuel_per_PMT

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

        from producer.manufacturers import Manufacturer  # needed for manufacturers table
        from consumer.market_classes import MarketClass  # needed for market class ID
        from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        from consumer.demanded_shares_gcam import DemandedSharesGCAM
        from policy.targets_footprint import VehicleTargets
        from context.cost_clouds import CostCloud

        omega_globals.options.VehicleTargets = VehicleTargets

        from producer.vehicles import VehicleFinal
        from producer.vehicle_annual_data import VehicleAnnualData

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)
        init_fail += DemandedSharesGCAM.init_database_from_file(omega_globals.options.demanded_shares_file,
                                                                verbose=omega_globals.options.verbose)
        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.cost_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)
        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.vehicle_onroad_calculations_file,
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = 2021
            omega_globals.options.analysis_final_year = 2035
            omega_globals.options.database_dump_folder = '__dump'

            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            # test market shares at different CO2e and price levels
            mcd = pd.DataFrame()
            for mc in MarketClass.market_classes:
                mcd['average_modified_cross_subsidized_price_%s' % mc] = [35000, 25000]
                mcd['average_kwh_pmi_%s' % mc] = [0, 0]
                mcd['average_co2e_gpmi_%s' % mc] = [125, 150]
                mcd['average_fuel_price_%s' % mc] = [2.75, 3.25]
                mcd['producer_abs_share_frac_non_hauling'] = [0.8, 0.85]
                mcd['producer_abs_share_frac_hauling'] = [0.2, 0.15]

            share_demand = get_demanded_shares(mcd, omega_globals.options.analysis_initial_year)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
