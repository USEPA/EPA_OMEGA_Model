"""
omega2.py
=========

OMEGA2 top level code

"""

print('importing %s' % __file__)

from usepa_omega2 import *
import os
from usepa_omega2.consumer import stock
import postproc_session


def logwrite_shares_and_costs(calendar_year, convergence_error, producer_decision_and_response, iteration_num,
                              producer_pricing_iteration):
    """

    Args:
        calendar_year:
        convergence_error:
        producer_decision_and_response:
        iteration_num:
        producer_pricing_iteration:

    Returns:

    """
    from consumer.market_classes import MarketClass
    import consumer

    for mc in MarketClass.market_classes:
        omega_log.logwrite(('%d producer/consumer_abs_share_frac_%s' % (calendar_year, mc)).ljust(50) +
                           '= %.4f / %.4f (DELTA:%f, CE:%f)' % (
                               producer_decision_and_response['producer_abs_share_frac_%s' % mc],
                               producer_decision_and_response['consumer_abs_share_frac_%s' % mc],
                               abs(producer_decision_and_response['producer_abs_share_frac_%s' % mc] -
                                   producer_decision_and_response[
                                       'consumer_abs_share_frac_%s' % mc]),
                               abs(1 - producer_decision_and_response['producer_abs_share_frac_%s' % mc] /
                                   producer_decision_and_response[
                                       'consumer_abs_share_frac_%s' % mc])
                           ), echo_console=True)
        omega_log.logwrite(
            ('cross subsidized price / cost %s' % mc).ljust(50) + '$%d / $%d R:%f' % (
            producer_decision_and_response['average_cross_subsidized_price_%s' % mc],
            producer_decision_and_response['average_cost_%s' % mc],
            producer_decision_and_response['average_cross_subsidized_price_%s' % mc] /
            producer_decision_and_response['average_cost_%s' % mc]
            ), echo_console=True)

    omega_log.logwrite('convergence_error = %f' % convergence_error, echo_console=True)

    for cat in consumer.market_categories:
        omega_log.logwrite(
            ('cross subsidized price / cost %s' % cat).ljust(50) + '$%d / $%d R:%f' % (
            producer_decision_and_response['average_cross_subsidized_price_%s' % cat],
            producer_decision_and_response['average_cost_%s' % cat],
            producer_decision_and_response['average_cross_subsidized_price_%s' % cat] /
            producer_decision_and_response['average_cost_%s' % cat]
            ), echo_console=True)

    omega_log.logwrite(
        'cross subsidized price / cost TOTAL'.ljust(50) + '$%d / $%d R:%f' % (producer_decision_and_response['average_cross_subsidized_price_total'],
                                                             producer_decision_and_response['average_cost_total'],
                                                             producer_decision_and_response['average_cross_subsidized_price_total'] /
                                                             producer_decision_and_response['average_cost_total']
                                                             ), echo_console=True)
    omega_log.logwrite(
        '%d_%d_%d  SCORE:%f  SWSD:%f  SR:%f' % (calendar_year, iteration_num, producer_pricing_iteration,
                                                producer_decision_and_response['pricing_convergence_score'],
                                                producer_decision_and_response['abs_share_delta_total'],
                                                producer_decision_and_response['sales_ratio']), echo_console=True)


def update_iteration_log(calendar_year, converged, iteration_log, iteration_num, producer_pricing_iteration,
                         compliant, convergence_error):
    """

    Args:
        calendar_year:
        converged:
        iteration_log:
        iteration_num:
        producer_pricing_iteration:
        compliant:
        convergence_error:

    Returns:

    """
    iteration_log.loc[iteration_log.index[-1], 'iteration'] = iteration_num
    iteration_log.loc[iteration_log.index[-1], 'pricing_iteration'] = producer_pricing_iteration
    iteration_log.loc[iteration_log.index[-1], 'calendar_year'] = calendar_year
    iteration_log.loc[iteration_log.index[-1], 'converged'] = converged
    iteration_log.loc[iteration_log.index[-1], 'compliant'] = compliant
    iteration_log.loc[iteration_log.index[-1], 'convergence_error'] = convergence_error
    if o2.options.log_consumer_iteration_years == 'all' or calendar_year in o2.options.log_consumer_iteration_years:
        iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder, index=False)


def run_producer_consumer():
    """
    Create producer cost-minimizing technology and market share options, in consideration of market response from
    the consumer module, possibly with iteration between the two

    :return: iteration log dataframe, updated omega database with final vehicle technology and market share data
    """

    from manufacturers import Manufacturer
    import producer
    from GHG_credits import GHG_credit_bank

    for manufacturer in o2.session.query(Manufacturer.manufacturer_ID).all():
        manufacturer_ID = manufacturer[0]
        omega_log.logwrite("Running %s: Manufacturer=%s" % (o2.options.session_unique_name, manufacturer_ID), echo_console=True)

        iteration_log = pd.DataFrame()

        if o2.options.num_analysis_years is None:
            analysis_end_year = o2.options.analysis_final_year + 1
        else:
            analysis_end_year = o2.options.analysis_initial_year + o2.options.num_analysis_years

        credit_bank = GHG_credit_bank(o2.options.ghg_credits_file, manufacturer_ID)

        for calendar_year in range(o2.options.analysis_initial_year, analysis_end_year):

            credit_bank.update_credit_age(calendar_year)
            expiring_credits_Mg = credit_bank.get_expiring_credits_Mg(calendar_year)
            expiring_debits_Mg = credit_bank.get_expiring_debits_Mg(calendar_year)
            credits_offset_Mg = expiring_credits_Mg + expiring_debits_Mg

            credits_offset_Mg = 0
            # current_credits, current_debits = credit_bank.get_credit_info(calendar_year)
            # for c in current_credits + current_debits:
            #     credits_offset_Mg += (c.remaining_balance_Mg / c.remaining_years)

            producer_decision_and_response = None
            best_winning_combo_with_sales_response = None

            iteration_num = 0
            iterate = True

            while iterate:
                omega_log.logwrite("Running %s:  Year=%s  Iteration=%s" %
                                   (o2.options.session_unique_name, calendar_year, iteration_num),
                                   echo_console=True)

                candidate_mfr_composite_vehicles, winning_combo, market_class_tree, producer_compliant = \
                    producer.run_compliance_model(manufacturer_ID, calendar_year, producer_decision_and_response,
                                                  iteration_num, credits_offset_Mg)

                market_class_vehicle_dict = calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles,
                                                                   winning_combo)

                best_winning_combo_with_sales_response, iteration_log, producer_decision_and_response = \
                    iterate_producer_consumer_pricing(calendar_year, best_winning_combo_with_sales_response,
                                                      candidate_mfr_composite_vehicles, iteration_log,
                                                      iteration_num, market_class_vehicle_dict, winning_combo,
                                                      credits_offset_Mg)

                producer_consumer_iteration = -1  # flag end of pricing subiteration

                converged, convergence_error = \
                    detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

                iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)
                update_iteration_log(calendar_year, converged, iteration_log, iteration_num,
                                     producer_consumer_iteration, producer_compliant, convergence_error)

                # decide whether to iterate or not
                iterate = o2.options.iterate_producer_consumer \
                          and iteration_num < o2.options.producer_consumer_max_iterations \
                          and not converged
                if iterate:
                    iteration_num += 1
                else:
                    if iteration_num >= o2.options.producer_consumer_max_iterations:
                        omega_log.logwrite('PRODUCER-CONSUMER MAX ITERATIONS EXCEEDED, ROLLING BACK TO BEST ITERATION', echo_console=True)
                        producer_decision_and_response = best_winning_combo_with_sales_response

            credit_bank.handle_credit(calendar_year, manufacturer_ID,
                                      producer_decision_and_response['total_combo_credits_co2_megagrams'])

            producer.finalize_production(calendar_year, manufacturer_ID, candidate_mfr_composite_vehicles,
                                         producer_decision_and_response)

            stock.update_stock(calendar_year)  # takes about 7.5 seconds

        iteration_log.to_csv(
            o2.options.output_folder + o2.options.session_unique_name + '_producer_consumer_iteration_log.csv',
            index=False)

        credit_bank.credit_bank.to_csv(o2.options.output_folder + o2.options.session_unique_name + '_credit_bank.csv',
                                       index=False)
        credit_bank.transaction_log.to_csv(
            o2.options.output_folder + o2.options.session_unique_name + '_credit_bank_transactions.csv', index=False)

    return iteration_log


def iterate_producer_consumer_pricing(calendar_year, best_producer_decision_and_response, candidate_mfr_composite_vehicles,
                                      iteration_log, iteration_num, market_class_vehicle_dict,
                                      producer_decision, credit_offset_Mg):
    """

    Args:
        calendar_year:
        best_producer_decision_and_response:
        candidate_mfr_composite_vehicles:
        iteration_log:
        iteration_num:
        market_class_vehicle_dict:
        producer_decision:

    Returns:

    """
    from consumer.market_classes import MarketClass
    import producer
    import consumer
    from consumer.sales_share_gcam import get_demanded_shares

    producer_decision['winning_combo_share_weighted_cost'] = 0
    for mc in market_class_vehicle_dict:
        producer_decision['winning_combo_share_weighted_cost'] = producer_decision['winning_combo_share_weighted_cost'] + \
                                                                 producer_decision['average_cost_%s' % mc] * \
                                                                 producer_decision['producer_abs_share_frac_%s' % mc]

    producer_decision['total_sales'] = \
        consumer.sales_volume.new_vehicle_sales_response(calendar_year,
                                                         producer_decision['winning_combo_share_weighted_cost'])

    unsubsidized_sales = producer_decision['total_sales']
    multiplier_columns = ['cost_multiplier_%s' % mc for mc in MarketClass.market_classes]

    producer_pricing_iteration = 0
    producer_decision_and_response = pd.DataFrame()

    prev_multiplier_range = dict()
    continue_search = True
    while continue_search:
        price_options_df = producer_decision.to_frame().transpose()

        continue_search, price_options_df = calculate_price_options(calendar_year, continue_search, multiplier_columns,
                                                                    prev_multiplier_range, price_options_df,
                                                                    producer_decision_and_response)

        producer_decision_and_response = get_demanded_shares(price_options_df, calendar_year)

        ###############################################################################################################
        calculate_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response)
        # propagate total sales down to composite vehicles by market class share and reg class share,
        # calculate new compliance status for each producer-technology / consumer response combination
        producer.calculate_tech_share_combos_total(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response,
                                                   total_sales=producer_decision_and_response['new_vehicle_sales'])
        # propagate vehicle sales up to market class sales
        calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response)
        ###############################################################################################################

        producer_decision_and_response['sales_ratio'] = \
            producer_decision_and_response['new_vehicle_sales'] / unsubsidized_sales

        producer_decision_and_response['compliance_ratio'] = \
            (producer_decision_and_response['total_combo_cert_co2_megagrams'] - credit_offset_Mg) / \
            producer_decision_and_response['total_combo_target_co2_megagrams']

        # calculate "distance to origin" (minimal price and market share errors):
        pricing_convergence_score = producer_decision_and_response['abs_share_delta_total']**2
        # add terms to maintain prices of non-responsive market categories during convergence:
        for cat in consumer.non_responsive_market_categories:
            pricing_convergence_score += abs(1 - producer_decision_and_response['average_cross_subsidized_price_%s' % cat] /
                                        producer_decision_and_response['average_cost_%s' % cat])**1

        producer_decision_and_response['pricing_convergence_score'] = pricing_convergence_score**1

        if o2.options.log_producer_decision_and_response_years == 'all' or \
                calendar_year in o2.options.log_producer_decision_and_response_years:
            producer_decision_and_response.to_csv('%sproducer_decision_and_response_%s_%s_%s.csv' %
                                (o2.options.output_folder, calendar_year, iteration_num, producer_pricing_iteration))

        producer_decision_and_response = \
            producer_decision_and_response.loc[producer_decision_and_response['pricing_convergence_score'].idxmin()]

        # if this code is uncommented, the reference case sales will match context sales EXACTLY, by compensating for
        # any slight offset during the convergence process:
        # ###############################################################################################################
        # if o2.options.session_is_reference:
        #     calculate_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response)
        #     # propagate total sales down to composite vehicles by market class share and reg class share,
        #     # calculate new compliance status for each producer-technology / consumer response combination
        #     producer.calculate_tech_share_combos_total(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response,
        #                                                total_sales=producer_decision_and_response['new_vehicle_sales'])
        #
        #     # propagate vehicle sales up to market class sales
        #     calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response)
        # ###############################################################################################################

        producer_decision_and_response['price_cost_ratio_total'] = \
            (producer_decision_and_response['average_cross_subsidized_price_total'] /
             producer_decision_and_response['average_cost_total'])

        converged, convergence_error = detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

        if (best_producer_decision_and_response is None) or (producer_decision_and_response['pricing_convergence_score'] < best_producer_decision_and_response['pricing_convergence_score']):
            best_producer_decision_and_response = producer_decision_and_response.copy()

        iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)

        if 'consumer' in o2.options.verbose_console:
            logwrite_shares_and_costs(calendar_year, convergence_error, producer_decision_and_response, iteration_num,
                                      producer_pricing_iteration)

        update_iteration_log(calendar_year, converged, iteration_log, iteration_num,
                             producer_pricing_iteration, converged, convergence_error)

        producer_pricing_iteration += 1

    if 'consumer' in o2.options.verbose_console:
        for mc, cc in zip(MarketClass.market_classes, multiplier_columns):
            omega_log.logwrite(('FINAL %s' % cc).ljust(50) + '= %.5f' % producer_decision_and_response[cc], echo_console=True)
        if converged:
            omega_log.logwrite('PRODUCER-CONSUMER CONVERGED CE:%f' % convergence_error, echo_console=True)

        omega_log.logwrite('', echo_console=True)

    # if o2.options.log_consumer_iteration_years == 'all' or calendar_year in o2.options.log_consumer_iteration_years:
    #     iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder, index=False)

    return best_producer_decision_and_response, iteration_log, producer_decision_and_response


def calculate_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response):
    """

    Args:
        calendar_year:
        market_class_vehicle_dict:
        producer_decision_and_response:

    Returns:

    """
    import consumer

    producer_decision_and_response['abs_share_delta_total'] = 0
    producer_decision_and_response['average_cross_subsidized_price_total'] = 0
    producer_decision_and_response['average_modified_cross_subsidized_price_total'] = 0
    producer_decision_and_response['average_cost_total'] = 0

    for mc in market_class_vehicle_dict:
        producer_decision_and_response['abs_share_delta_total'] += abs(
            producer_decision_and_response['producer_abs_share_frac_%s' % mc] -
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc])

        producer_decision_and_response['average_cross_subsidized_price_total'] += \
            producer_decision_and_response['average_cross_subsidized_price_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

        producer_decision_and_response['average_modified_cross_subsidized_price_total'] += \
            producer_decision_and_response['average_modified_cross_subsidized_price_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

        producer_decision_and_response['average_cost_total'] += \
            producer_decision_and_response['average_cost_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

    # calculate new total sales demand based on total share weighted price
    producer_decision_and_response['new_vehicle_sales'] = \
        consumer.sales_volume.new_vehicle_sales_response(calendar_year,
                                                         producer_decision_and_response[
                                                             'average_modified_cross_subsidized_price_total'])


def calculate_price_options(calendar_year, continue_search, multiplier_columns, prev_multiplier_range, price_options_df,
                            producer_decision_and_response):
    """

    Args:
        continue_search:
        multiplier_columns:
        prev_multiplier_range:
        price_options_df:
        producer_decision_and_response:

    Returns:

    """
    import numpy as np
    from consumer.market_classes import MarketClass
    from price_modifications import PriceModifications

    if producer_decision_and_response.empty:
        # first time through, span full range
        multiplier_range = \
            np.unique(np.append(np.linspace(o2.options.consumer_pricing_multiplier_min,
                                o2.options.consumer_pricing_multiplier_max,
                                o2.options.consumer_pricing_num_options), 1.0))

    search_collapsed = True
    for mc, mcc in zip(MarketClass.market_classes, multiplier_columns):
        if not producer_decision_and_response.empty:
            # subsequent passes, tighten up search range to find convergent multipliers
            multiplier_range, search_collapsed = tighten_multiplier_range(mcc, prev_multiplier_range,
                                                                          producer_decision_and_response,
                                                                          search_collapsed)

        price_options_df = cartesian_prod(price_options_df, pd.DataFrame(multiplier_range, columns=[mcc]))

        price_options_df['average_cross_subsidized_price_%s' % mc] = price_options_df['average_cost_%s' % mc] * price_options_df[mcc]

        price_modification = PriceModifications.get_price_modification(calendar_year, mc)
        price_options_df['average_modified_cross_subsidized_price_%s' % mc] = price_options_df['average_cross_subsidized_price_%s' % mc] + price_modification

        prev_multiplier_range[mcc] = multiplier_range

    if not producer_decision_and_response.empty and search_collapsed:
        continue_search = False
        if 'consumer' in o2.options.verbose_console:
            omega_log.logwrite('SEARCH COLLAPSED')

    return continue_search, price_options_df


def tighten_multiplier_range(mcc, prev_multiplier_range, producer_decision_and_response,
                             search_collapsed):
    """

    Args:
        mcc:
        prev_multiplier_range:
        producer_decision_and_response:
        search_collapsed:

    Returns:

    """
    import numpy as np

    prev_multiplier_span_frac = prev_multiplier_range[mcc][-1] / prev_multiplier_range[mcc][0] - 1
    index = np.nonzero(prev_multiplier_range[mcc] == producer_decision_and_response[mcc])[0][0]
    if index == 0:
        min_val = max(o2.options.consumer_pricing_multiplier_min,
                      producer_decision_and_response[mcc] - prev_multiplier_span_frac *
                      producer_decision_and_response[mcc])
    else:
        min_val = prev_multiplier_range[mcc][index - 1]
    if index == len(prev_multiplier_range[mcc]) - 1:
        max_val = min(o2.options.consumer_pricing_multiplier_max,
                      producer_decision_and_response[mcc] + prev_multiplier_span_frac *
                      producer_decision_and_response[mcc])
    else:
        max_val = prev_multiplier_range[mcc][index + 1]
    # try new range, include prior value in range...
    multiplier_range = np.unique(np.append(
        np.linspace(min_val, max_val, o2.options.consumer_pricing_num_options),
        producer_decision_and_response[mcc]))
    search_collapsed = search_collapsed and ((len(multiplier_range) == 2) or ((max_val / min_val - 1) <= 1e-3))
    if 'consumer' in o2.options.verbose_console:
        omega_log.logwrite(('%s' % mcc).ljust(50) + '= %.5f MR:%s R:%f' % (
            producer_decision_and_response[mcc], multiplier_range, max_val / min_val), echo_console=True)

    return multiplier_range, search_collapsed


def calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, winning_combo):
    """

    Args:
        calendar_year:
        candidate_mfr_composite_vehicles: list of candidate composite vehicles that minimize producer compliance cost
        winning_combo: pandas Series that corresponds with candidate_mfr_composite_vehicles, has market shares, costs,
            compliance data (Mg CO2)

    Returns: dictionary of candidate vehicles binned by market class and reg class, updates producer_decision with
            sales-weighted average cost and CO2 g/mi by market class

    """

    from consumer.market_classes import MarketClass
    from omega_functions import weighted_value

    # group vehicles by market class
    market_class_vehicle_dict = MarketClass.get_market_class_dict()
    for new_veh in candidate_mfr_composite_vehicles:
        market_class_vehicle_dict[new_veh.market_class_ID].add(new_veh)

    # calculate sales-weighted co2 g/mi and cost by market class
    for mc in MarketClass.market_classes:
        market_class_vehicles = market_class_vehicle_dict[mc]
        if market_class_vehicles:
            winning_combo['average_co2_gpmi_%s' % mc] = weighted_value(market_class_vehicles,
                                                                       'initial_registered_count',
                                                                       'cert_CO2_grams_per_mile')

            winning_combo['average_kwh_pmi_%s' % mc] = weighted_value(market_class_vehicles,
                                                                       'initial_registered_count',
                                                                       'cert_kWh_per_mile')

            winning_combo['average_cost_%s' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'new_vehicle_mfr_cost_dollars')

            winning_combo['average_generalized_cost_%s' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'new_vehicle_mfr_generalized_cost_dollars')

            winning_combo['average_fuel_price_%s' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'retail_fuel_price_dollars_per_unit')

            winning_combo['sales_%s' % mc] = 0
            for v in market_class_vehicles:
                winning_combo['sales_%s' % mc] += winning_combo['veh_%s_sales' % v.vehicle_ID]  # was v.initial_registered_count
        else:
            winning_combo['average_co2_gpmi_%s' % mc] = 0
            winning_combo['average_kwh_pmi_%s' % mc] = 0
            winning_combo['average_cost_%s' % mc] = 0
            winning_combo['average_generalized_cost_%s' % mc] = 0
            winning_combo['sales_%s' % mc] = 0

        # winning_combo['producer_abs_market_share_frac_%s' % mc] = winning_combo['sales_%s' % mc] / winning_combo['total_sales']

    calculate_market_sector_data(winning_combo)

    return market_class_vehicle_dict


def calculate_market_sector_data(winning_combo):
    """

    Args:
        winning_combo:

    Returns:

    """
    import numpy as np
    import consumer
    from consumer.market_classes import MarketClass

    for mcat in consumer.market_categories:
        winning_combo['average_cost_%s' % mcat] = 0
        winning_combo['average_generalized_cost_%s' % mcat] = 0
        winning_combo['average_cross_subsidized_price_%s' % mcat] = 0
        winning_combo['sales_%s' % mcat] = 0
        winning_combo['producer_abs_share_frac_%s' % mcat] = 0

        for mc in MarketClass.market_classes:
            if mcat in mc.split('.'):
                winning_combo['average_cost_%s' % mcat] += winning_combo['average_cost_%s' % mc] * np.maximum(1, winning_combo['sales_%s' % mc])
                winning_combo['average_generalized_cost_%s' % mcat] += winning_combo['average_generalized_cost_%s' % mc] * np.maximum(1, winning_combo['sales_%s' % mc])
                if 'average_cross_subsidized_price_%s' % mc in winning_combo:
                    winning_combo['average_cross_subsidized_price_%s' % mcat] += winning_combo['average_cross_subsidized_price_%s' % mc] * np.maximum(1, winning_combo['sales_%s' % mc])
                winning_combo['sales_%s' % mcat] += np.maximum(1, winning_combo['sales_%s' % mc])
                winning_combo['producer_abs_share_frac_%s' % mcat] += winning_combo['producer_abs_share_frac_%s' % mc]

        winning_combo['average_cost_%s' % mcat] = winning_combo['average_cost_%s' % mcat] / winning_combo['sales_%s' % mcat]
        winning_combo['average_generalized_cost_%s' % mcat] = winning_combo['average_generalized_cost_%s' % mcat] / winning_combo['sales_%s' % mcat]
        winning_combo['average_cross_subsidized_price_%s' % mcat] = winning_combo['average_cross_subsidized_price_%s' % mcat] / winning_combo['sales_%s' % mcat]


def detect_convergence(producer_decision_and_response, market_class_dict):
    """

    Args:
        producer_decision_and_response:
        market_class_dict:

    Returns:

    """
    # TODO: paramaterize the 1e-4?
    converged = abs(1 - producer_decision_and_response['price_cost_ratio_total']) <= 1e-4
    convergence_error = 0
    for mc in market_class_dict:
        convergence_error = \
            max(convergence_error, abs(producer_decision_and_response['producer_abs_share_frac_%s' % mc] - \
                                    producer_decision_and_response['consumer_abs_share_frac_%s' % mc]))
        converged = converged and (convergence_error <= o2.options.producer_consumer_iteration_tolerance)

    return converged, convergence_error


# noinspection PyUnresolvedReferences
def init_omega(o2_options):
    """

    Args:
        o2_options:

    Returns:

    """
    from omega_log import OMEGALog

    # set up global variables:
    o2.options = o2_options

    if o2.options.auto_close_figures:
        import matplotlib
        matplotlib.use('Agg')

    omega_log.init_logfile()

    init_omega_db()
    o2.engine.echo = o2.options.verbose

    init_fail = []

    # import database modules to populate ORM context
    from fuels import Fuel
    from policy_fuel_upstream import PolicyFuelUpstream
    from policy_fuel_upstream_methods import PolicyFuelUpstreamMethods
    from context_fuel_prices import ContextFuelPrices
    from context_new_vehicle_market import ContextNewVehicleMarket
    from consumer.market_classes import MarketClass
    from cost_clouds import CostCloud
    from consumer.demanded_shares_gcam import DemandedSharesGCAM
    from manufacturers import Manufacturer
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.reregistration_fixed_by_age import ReregistrationFixedByAge
    from consumer.annual_vmt_fixed_by_age import AnnualVMTFixedByAge
    from effects.cost_factors_criteria import CostFactorsCriteria
    from effects.cost_factors_scc import CostFactorsSCC
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise
    from effects.emission_factors_powersector import EmissionFactorsPowersector
    from effects.emission_factors_refinery import EmissionFactorsRefinery
    from effects.emission_factors_vehicles import EmissionFactorsVehicles
    from effects.cost_effects_scc import CostEffectsSCC
    from effects.cost_effects_criteria import CostEffectsCriteria
    from effects.cost_effects_non_emissions import CostEffectsNonEmissions
    from required_zev_share import RequiredZevShare
    from price_modifications import PriceModifications
    from production_constraints import ProductionConstraints
    from drive_cycles import DriveCycles
    from drive_cycle_weights import DriveCycleWeights

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

    from GHG_standards_fuels import GHGStandardFuels

    from GHG_credits import GHG_credit_bank

    # instantiate database tables
    SQABase.metadata.create_all(o2.engine)

    import consumer.sales_volume as consumer
    import producer

    fileio.validate_folder(o2.options.output_folder)

    o2.options.producer_calculate_generalized_cost = producer.calculate_generalized_cost
    o2.options.consumer_calculate_generalized_cost = consumer.calculate_generalized_cost

    try:
        init_fail += Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        init_fail += PolicyFuelUpstream.init_from_file(o2.options.fuel_upstream_file, verbose=o2.options.verbose)
        
        init_fail += PolicyFuelUpstreamMethods.init_from_file(o2.options.fuel_upstream_methods_file, 
                                                              verbose=o2.options.verbose)
        
        init_fail += ContextFuelPrices.init_database_from_file(o2.options.context_fuel_prices_file, 
                                                               verbose=o2.options.verbose)

        init_fail += ContextNewVehicleMarket.init_database_from_file(o2.options.context_new_vehicle_market_file, 
                                                                     verbose=o2.options.verbose)
        
        ContextNewVehicleMarket.init_context_new_vehicle_prices(o2.options.context_new_vehicle_prices_file)

        init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file, verbose=o2.options.verbose)

        init_fail += CostCloud.init_cost_clouds_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        init_fail += o2.options.GHG_standard.init_database_from_file(o2.options.ghg_standards_file, 
                                                                     verbose=o2.options.verbose)

        init_fail += GHGStandardFuels.init_database_from_file(o2.options.ghg_standards_fuels_file, 
                                                              verbose=o2.options.verbose)

        init_fail += GHG_credit_bank.validate_ghg_credits_template(o2.options.ghg_credits_file, 
                                                                   verbose=o2.options.verbose)

        init_fail += DemandedSharesGCAM.init_database_from_file(o2.options.demanded_shares_file, 
                                                                verbose=o2.options.verbose)

        init_fail += Manufacturer.init_database_from_file(o2.options.manufacturers_file, verbose=o2.options.verbose)
        
        init_fail += VehicleFinal.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        init_fail += ReregistrationFixedByAge.init_database_from_file(o2.options.reregistration_fixed_by_age_file, 
                                                                      verbose=o2.options.verbose)
        
        o2.options.stock_scrappage = ReregistrationFixedByAge

        init_fail += AnnualVMTFixedByAge.init_database_from_file(o2.options.annual_vmt_fixed_by_age_file, 
                                                                 verbose=o2.options.verbose)
        
        o2.options.stock_vmt = AnnualVMTFixedByAge

        init_fail += CostFactorsCriteria.init_database_from_file(o2.options.criteria_cost_factors_file,
                                                                 o2.options.cpi_deflators_file,
                                                                 verbose=o2.options.verbose)

        init_fail += CostFactorsSCC.init_database_from_file(o2.options.scc_cost_factors_file,
                                                            verbose=o2.options.verbose)

        init_fail += CostFactorsEnergySecurity.init_database_from_file(o2.options.energysecurity_cost_factors_file,
                                                                       verbose=o2.options.verbose)

        init_fail += CostFactorsCongestionNoise.init_database_from_file(o2.options.congestion_noise_cost_factors_file,
                                                                        verbose=o2.options.verbose)

        init_fail += EmissionFactorsPowersector.init_database_from_file(o2.options.emission_factors_powersector_file,
                                                                        verbose=o2.options.verbose)

        init_fail += EmissionFactorsRefinery.init_database_from_file(o2.options.emission_factors_refinery_file,
                                                                     verbose=o2.options.verbose)

        init_fail += EmissionFactorsVehicles.init_database_from_file(o2.options.emission_factors_vehicles_file,
                                                                     verbose=o2.options.verbose)

        init_fail += RequiredZevShare.init_from_file(o2.options.required_zev_share_file, verbose=o2.options.verbose)

        init_fail += PriceModifications.init_from_file(o2.options.price_modifications_file, verbose=o2.options.verbose)

        init_fail += ProductionConstraints.init_from_file(o2.options.production_constraints_file,
                                                          verbose=o2.options.verbose)

        init_fail += DriveCycles.init_from_file(o2.options.drive_cycles_file, verbose=o2.options.verbose)

        init_fail += DriveCycleWeights.init_from_file(o2.options.drive_cycle_weights_file, verbose=o2.options.verbose)

        # initial year = initial fleet model year (latest year of data)
        o2.options.analysis_initial_year = int(o2.session.query(func.max(VehicleFinal.model_year)).scalar()) + 1
        # final year = last year of cost curve data
        # o2.options.analysis_final_year = int(o2.session.query(func.max(CostCurve.model_year)).scalar())
        # o2.options.analysis_final_year = 2022
        o2.options.analysis_final_year = CostCloud.get_max_year()

        stock.update_stock(o2.options.analysis_initial_year - 1)  # update vehicle annual data for base year fleet
    finally:
        return init_fail


def run_omega(o2_options, standalone_run=False):
    """

    Args:
        o2_options:
        standalone_run:

    Returns:

    """
    import traceback
    import time

    o2_options.start_time = time.time()

    print('OMEGA2 greets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    print('run_omega(%s)' % o2_options.session_name)

    try:
        init_fail = init_omega(o2_options)

        omega_log.logwrite("Running %s: OMEGA 2 Version %s" % (o2.options.session_unique_name, code_version))

        if not init_fail:
            if o2.options.run_profiler:
                # run with profiler
                import cProfile
                import re
                cProfile.run('iteration_log = run_producer_consumer()', filename='omega2_profile.dmp')
                session_summary_results = postproc_session.run_postproc(globals()['iteration_log'], standalone_run)  # return values of cProfile.run() show up in the globals namespace
            else:
                # run without profiler
                iteration_log = run_producer_consumer()
                session_summary_results = postproc_session.run_postproc(iteration_log, standalone_run)

            # write output files
            summary_filename = o2.options.output_folder + o2.options.session_unique_name + '_summary_results.csv'
            session_summary_results.to_csv(summary_filename, index=False)
            dump_omega_db_to_csv(o2.options.database_dump_folder)

            if o2.options.session_is_reference and o2.options.generate_context_new_vehicle_prices_file:
                from context_new_vehicle_market import ContextNewVehicleMarket
                ContextNewVehicleMarket.save_context_new_vehicle_prices(o2.options.context_new_vehicle_prices_file)

            omega_log.end_logfile("\nSession Complete")

            if o2.options.run_profiler:
                os.system('snakeviz omega2_profile.dmp')

            # shut down the db
            o2.session.close()
            o2.engine.dispose()
            o2.engine = None
            o2.session = None
            o2.options = None
        else:
            omega_log.logwrite("\n#INIT FAIL")
            omega_log.logwrite(init_fail)
            omega_log.end_logfile("\nSession Fail")
            return init_fail

    except Exception as e:
        if init_fail:
            omega_log.logwrite("\n#INIT FAIL")
            omega_log.logwrite(init_fail)
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("### Check OMEGA log for error messages ###")
        omega_log.logwrite("### Check OMEGA log for error messages ###")
        omega_log.logwrite("### RUNTIME FAIL ###")
        omega_log.end_logfile("\nSession Fail")
        dump_omega_db_to_csv(o2.options.database_dump_folder)


if __name__ == "__main__":
    try:
        import producer
        run_omega(OMEGARuntimeOptions(), standalone_run=True)  # to view in terminal: snakeviz omega2_profile.dmp
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
