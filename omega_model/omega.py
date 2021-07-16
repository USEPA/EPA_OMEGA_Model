"""

OMEGA2 top level code

Runs a single session.

----

**CODE**

"""

print('importing %s' % __file__)

import sys, os

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(path, '..'))  # picks up omega_model sub-packages

from omega_model import *
from omega_model.consumer import stock
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
        '%d_%d_%d  SCORE:%f  SWSD:%f' % (calendar_year, iteration_num, producer_pricing_iteration,
                                                producer_decision_and_response['pricing_convergence_score'],
                                                producer_decision_and_response['abs_share_delta_total']), echo_console=True)


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


def run_producer_consumer():
    """
    Create producer cost-minimizing technology and market share options, in consideration of market response from
    the consumer module, possibly with iteration between the two

    :return: iteration log dataframe, updated omega database with final vehicle technology and market share data

    """

    from producer.manufacturers import Manufacturer
    from producer import compliance_strategy
    from policy.credit_banking import CreditBank

    for manufacturer in omega_globals.session.query(Manufacturer.manufacturer_id).all():
        manufacturer_id = manufacturer[0]
        omega_log.logwrite("Running %s: Manufacturer=%s" % (omega_globals.options.session_unique_name, manufacturer_id),
                           echo_console=True)

        iteration_log = pd.DataFrame()

        analysis_end_year = omega_globals.options.analysis_final_year + 1

        credit_bank = CreditBank(omega_globals.options.ghg_credits_file, manufacturer_id)

        for calendar_year in range(omega_globals.options.analysis_initial_year, analysis_end_year):

            credit_bank.update_credit_age(calendar_year)

            # TODO: make credit strategy modular, like upstream methods?
            # strategy: use expiring credits, pay any expiring debits in one shot:
            # expiring_credits_Mg = credit_bank.get_expiring_credits_Mg(calendar_year)
            # expiring_debits_Mg = credit_bank.get_expiring_debits_Mg(calendar_year)
            # strategic_target_offset_Mg = expiring_credits_Mg + expiring_debits_Mg

            # strategy: use credits and pay debits over their remaining lifetime, instead of all at once:
            # current_credits, current_debits = credit_bank.get_credit_info(calendar_year)
            # for c in current_credits + current_debits:
            #     strategic_target_offset_Mg += (c.remaining_balance_Mg / c.remaining_years)

            # strategy: try to hit the target and make up for minor previous compliance discrepancies
            #           (ignoring base year banked credits):
            strategic_target_offset_Mg = 0
            current_credits, current_debits = credit_bank.get_credit_info(calendar_year)
            for c in current_debits:
                strategic_target_offset_Mg += c.remaining_balance_Mg

            producer_decision_and_response = None
            best_winning_combo_with_sales_response = None

            iteration_num = 0
            iterate_producer_consumer = True

            while iterate_producer_consumer:
                omega_log.logwrite("Running %s:  Year=%s  Iteration=%s" %
                                   (omega_globals.options.session_unique_name, calendar_year, iteration_num),
                                   echo_console=True)

                candidate_mfr_composite_vehicles, winning_combo, market_class_tree, producer_compliant = \
                    compliance_strategy.search_production_options(manufacturer_id, calendar_year,
                                                                  producer_decision_and_response,
                                                                  iteration_num, strategic_target_offset_Mg)

                market_class_vehicle_dict = calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles,
                                                                   winning_combo)

                best_winning_combo_with_sales_response, iteration_log, producer_decision_and_response = \
                    iterate_producer_cross_subsidy(calendar_year, best_winning_combo_with_sales_response,
                                                   candidate_mfr_composite_vehicles, iteration_log,
                                                   iteration_num, market_class_vehicle_dict, winning_combo,
                                                   strategic_target_offset_Mg)

                producer_consumer_iteration = -1  # flag end of pricing subiteration

                converged, convergence_error = \
                    detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

                iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)

                update_iteration_log(calendar_year, converged, iteration_log, iteration_num,
                                     producer_consumer_iteration, producer_compliant, convergence_error)

                # decide whether to continue iterating or not
                iterate_producer_consumer = omega_globals.options.iterate_producer_consumer \
                                            and iteration_num < omega_globals.options.producer_consumer_max_iterations \
                                            and not converged

                if iterate_producer_consumer:
                    iteration_num += 1
                else:
                    if iteration_num >= omega_globals.options.producer_consumer_max_iterations:
                        omega_log.logwrite('PRODUCER-CONSUMER MAX ITERATIONS EXCEEDED, ROLLING BACK TO BEST ITERATION',
                                           echo_console=True)
                        producer_decision_and_response = best_winning_combo_with_sales_response

            compliance_strategy.finalize_production(calendar_year, manufacturer_id, candidate_mfr_composite_vehicles,
                                                    producer_decision_and_response)

            credit_bank.handle_credit(calendar_year, manufacturer_id,
                                      producer_decision_and_response['total_credits_co2e_megagrams'])

            stock.update_stock(calendar_year)  # takes about 7.5 seconds

        if (omega_globals.options.log_consumer_iteration_years == 'all') or \
                (calendar_year in omega_globals.options.log_consumer_iteration_years)\
                or (calendar_year == analysis_end_year-1):
            iteration_log.to_csv(omega_globals.options.output_folder + omega_globals.options.session_unique_name +
                                 '_producer_consumer_iteration_log.csv', index=False)

        credit_bank.credit_bank.to_csv(omega_globals.options.output_folder + omega_globals.options.session_unique_name +
                                       '_credit_bank.csv', index=False)

        credit_bank.transaction_log.to_csv(
            omega_globals.options.output_folder + omega_globals.options.session_unique_name +
            '_credit_bank_transactions.csv', index=False)

    return iteration_log, credit_bank


def iterate_producer_cross_subsidy(calendar_year, best_producer_decision_and_response, candidate_mfr_composite_vehicles,
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
    from producer import compliance_strategy
    import consumer
    from consumer.sales_share_gcam import get_demanded_shares

    producer_decision['winning_combo_share_weighted_cost'] = 0
    producer_decision['winning_combo_share_weighted_generalized_cost'] = 0
    for mc in market_class_vehicle_dict:
        producer_decision['winning_combo_share_weighted_cost'] += producer_decision['average_cost_%s' % mc] * \
                                                                  producer_decision['producer_abs_share_frac_%s' % mc]
        producer_decision['winning_combo_share_weighted_generalized_cost'] += producer_decision['average_generalized_cost_%s' % mc] * \
                                                                  producer_decision['producer_abs_share_frac_%s' % mc]

    consumer.sales_volume.new_vehicle_sales_response(calendar_year,
                                                     producer_decision['winning_combo_share_weighted_generalized_cost'])  #, producer_decision['winning_combo_share_weighted_generalized_cost']

    multiplier_columns = ['cost_multiplier_%s' % mc for mc in MarketClass.market_classes]

    producer_pricing_iteration = 0
    producer_decision_and_response = pd.DataFrame()

    prev_multiplier_range = dict()
    continue_search = True
    while continue_search:
        price_options_df = producer_decision.to_frame().transpose()

        continue_search, price_options_df = calc_price_options(calendar_year, continue_search, multiplier_columns,
                                                                    prev_multiplier_range, price_options_df,
                                                                    producer_decision_and_response)

        producer_decision_and_response = get_demanded_shares(price_options_df, calendar_year)

        ###############################################################################################################
        calc_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response)
        # propagate total sales down to composite vehicles by market class share and reg class share,
        # calculate new compliance status for each producer-technology / consumer response combination
        compliance_strategy.create_production_options(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response,
                                                      total_sales=producer_decision_and_response['new_vehicle_sales'])
        # propagate vehicle sales up to market class sales
        calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response)
        ###############################################################################################################

        producer_decision_and_response['strategic_compliance_ratio'] = \
            (producer_decision_and_response['total_cert_co2e_megagrams'] - credit_offset_Mg) / \
            producer_decision_and_response['total_target_co2e_megagrams']

        # calculate "distance to origin" (minimal price and market share errors):
        pricing_convergence_score = producer_decision_and_response['abs_share_delta_total']**1
        # add terms to maintain prices of non-responsive market categories during convergence:
        for cat in consumer.non_responsive_market_categories:
            pricing_convergence_score += abs(1 - producer_decision_and_response['average_cross_subsidized_price_%s' % cat] /
                                        producer_decision_and_response['average_cost_%s' % cat])**1

        producer_decision_and_response['pricing_convergence_score'] = pricing_convergence_score**1

        if omega_globals.options.log_producer_decision_and_response_years == 'all' or \
                calendar_year in omega_globals.options.log_producer_decision_and_response_years:
            producer_decision_and_response.to_csv('%sproducer_decision_and_response_%s_%s_%s.csv' %
                                                  (omega_globals.options.output_folder, calendar_year, iteration_num, producer_pricing_iteration))

        producer_decision_and_response = \
            producer_decision_and_response.loc[producer_decision_and_response['pricing_convergence_score'].idxmin()]

        # if this code is uncommented, the reference case sales will match context sales EXACTLY, by compensating for
        # any slight offset during the convergence process:
        # ###############################################################################################################
        # if o2.options.session_is_reference:
        #     calc_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response)
        #     # propagate total sales down to composite vehicles by market class share and reg class share,
        #     # calculate new compliance status for each producer-technology / consumer response combination
        #     compliance_strategy.calc_tech_share_combos_total(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response,
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

        if 'consumer' in omega_globals.options.verbose_console:
            logwrite_shares_and_costs(calendar_year, convergence_error, producer_decision_and_response, iteration_num,
                                      producer_pricing_iteration)

        update_iteration_log(calendar_year, converged, iteration_log, iteration_num,
                             producer_pricing_iteration, converged, convergence_error)

        producer_pricing_iteration += 1

        continue_search = continue_search and not converged

    if 'consumer' in omega_globals.options.verbose_console:
        for mc, cc in zip(MarketClass.market_classes, multiplier_columns):
            omega_log.logwrite(('FINAL %s' % cc).ljust(50) + '= %.5f' % producer_decision_and_response[cc], echo_console=True)
        if converged:
            omega_log.logwrite('PRODUCER-CONSUMER CONVERGED CE:%f' % convergence_error, echo_console=True)

        omega_log.logwrite('', echo_console=True)

    return best_producer_decision_and_response, iteration_log, producer_decision_and_response


def calc_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response):
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
    producer_decision_and_response['average_generalized_cost_total'] = 0

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

        producer_decision_and_response['average_generalized_cost_total'] += \
            producer_decision_and_response['average_generalized_cost_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

    producer_decision_and_response['new_vehicle_sales'] = \
        consumer.sales_volume.new_vehicle_sales_response(calendar_year,
                                                         producer_decision_and_response['average_generalized_cost_total'])


def calc_price_options(calendar_year, continue_search, multiplier_columns, prev_multiplier_range, price_options_df,
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
    from context.price_modifications import PriceModifications

    if producer_decision_and_response.empty:
        # first time through, span full range
        multiplier_range = \
            np.unique(np.append(np.linspace(omega_globals.options.consumer_pricing_multiplier_min,
                                            omega_globals.options.consumer_pricing_multiplier_max,
                                            omega_globals.options.consumer_pricing_num_options), 1.0))

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
        if 'consumer' in omega_globals.options.verbose_console:
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
        min_val = max(omega_globals.options.consumer_pricing_multiplier_min,
                      producer_decision_and_response[mcc] - prev_multiplier_span_frac *
                      producer_decision_and_response[mcc])
    else:
        min_val = prev_multiplier_range[mcc][index - 1]
    if index == len(prev_multiplier_range[mcc]) - 1:
        max_val = min(omega_globals.options.consumer_pricing_multiplier_max,
                      producer_decision_and_response[mcc] + prev_multiplier_span_frac *
                      producer_decision_and_response[mcc])
    else:
        max_val = prev_multiplier_range[mcc][index + 1]
    # try new range, include prior value in range...
    multiplier_range = np.unique(np.append(
        np.linspace(min_val, max_val, omega_globals.options.consumer_pricing_num_options),
        producer_decision_and_response[mcc]))
    search_collapsed = search_collapsed and ((len(multiplier_range) == 2) or ((max_val / min_val - 1) <= 1e-3))
    if 'consumer' in omega_globals.options.verbose_console:
        omega_log.logwrite(('%s' % mcc).ljust(50) + '= %.5f MR:%s R:%f' % (
            producer_decision_and_response[mcc], multiplier_range, max_val / min_val), echo_console=True)

    return multiplier_range, search_collapsed


def calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, winning_combo):
    """

    Args:
        calendar_year:
        candidate_mfr_composite_vehicles: list of candidate composite vehicles that minimize producer compliance cost
        winning_combo: pandas Series that corresponds with candidate_mfr_composite_vehicles, has market shares, costs,
            compliance data (Mg CO2e)

    Returns: dictionary of candidate vehicles binned by market class and reg class, updates producer_decision with
            sales-weighted average cost and CO2e g/mi by market class

    """

    from consumer.market_classes import MarketClass
    from common.omega_functions import weighted_value

    # group vehicles by market class
    market_class_vehicle_dict = MarketClass.get_market_class_dict()
    for new_veh in candidate_mfr_composite_vehicles:
        market_class_vehicle_dict[new_veh.market_class_id].append(new_veh)

    # calculate sales-weighted co2 g/mi and cost by market class
    for mc in MarketClass.market_classes:
        market_class_vehicles = market_class_vehicle_dict[mc]
        if market_class_vehicles:
            winning_combo['average_co2e_gpmi_%s' % mc] = weighted_value(market_class_vehicles,
                                                                       'initial_registered_count',
                                                                       'onroad_direct_co2e_grams_per_mile')

            winning_combo['average_kwh_pmi_%s' % mc] = weighted_value(market_class_vehicles,
                                                                       'initial_registered_count',
                                                                       'onroad_direct_kwh_per_mile')

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
                winning_combo['sales_%s' % mc] += winning_combo['veh_%s_sales' % v.vehicle_id]  # was v.initial_registered_count
        else:
            winning_combo['average_co2e_gpmi_%s' % mc] = 0
            winning_combo['average_kwh_pmi_%s' % mc] = 0
            winning_combo['average_cost_%s' % mc] = 0
            winning_combo['average_generalized_cost_%s' % mc] = 0
            winning_combo['sales_%s' % mc] = 0

        # winning_combo['producer_abs_market_share_frac_%s' % mc] = winning_combo['sales_%s' % mc] / winning_combo['total_sales']

    calc_market_sector_data(winning_combo)

    return market_class_vehicle_dict


def calc_market_sector_data(winning_combo):
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
        converged = converged and (convergence_error <= omega_globals.options.producer_consumer_iteration_tolerance)

    return converged, convergence_error


def init_user_definable_modules():
    """
    Import dynamic modules that are specified by the input file input template name and set the session runtime
    options appropriately.

    Returns:
        List of template/input errors, else empty list on success

    """
    import importlib

    init_fail = []

    # pull in reg classes before building database tables (declaring classes) that check reg class validity
    module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
    omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
    init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
        omega_globals.options.policy_reg_classes_file)

    module_name = get_template_name(omega_globals.options.policy_targets_file)
    omega_globals.options.VehicleTargets = importlib.import_module(module_name).VehicleTargets

    module_name = get_template_name(omega_globals.options.reregistration_file)
    omega_globals.options.Reregistration = importlib.import_module(module_name).Reregistration

    module_name = get_template_name(omega_globals.options.annual_vmt_file)
    omega_globals.options.AnnualVMT = importlib.import_module(module_name).AnnualVMT

    return init_fail


def init_user_definable_decomposition_attributes(verbose_init):
    """


    Args:
        verbose_init (bool): if True enable additional init output to console

    Returns:
        List of template/input errors, else empty list on success

    """

    from policy.offcycle_credits import OffCycleCredits
    from producer.vehicles import VehicleFinal, DecompositionAttributes

    init_fail = []

    init_fail += OffCycleCredits.init_from_file(omega_globals.options.offcycle_credits_file,
                                                verbose=verbose_init)
    DecompositionAttributes.init()
    # dynamically add decomposition attributes (which may vary based on user inputs, such as off-cycle credits)
    for attr in DecompositionAttributes.values:
        if attr not in VehicleFinal.__dict__:
            if int(sqlalchemy.__version__.split('.')[1]) > 3:
                sqlalchemy.ext.declarative.DeclarativeMeta.__setattr__(VehicleFinal, attr, Column(attr, Float))
            else:
                sqlalchemy.ext.declarative.api.DeclarativeMeta.__setattr__(VehicleFinal, attr, Column(attr, Float))

    return init_fail


def init_omega(session_runtime_options):
    """
    Initialize OMEGA data structures.

    Args:
        session_runtime_options (OMEGARuntimeOptions):

    Returns:
        List of template/input errors, else empty list on success

    """

    # set up global variables:
    omega_globals.options = session_runtime_options

    if omega_globals.options.auto_close_figures:
        import matplotlib
        matplotlib.use('Agg')

    omega_log.init_logfile()

    omega_log.logwrite("Initializing %s:" % omega_globals.options.session_unique_name, echo_console=True)

    init_fail = []

    init_omega_db(omega_globals.options.verbose)

    init_fail += init_user_definable_modules()

    # import database modules to populate ORM context
    from consumer.market_classes import MarketClass
    from consumer.demanded_shares_gcam import DemandedSharesGCAM

    from context.onroad_fuels import OnroadFuel
    from context.fuel_prices import FuelPrice
    from context.new_vehicle_market import NewVehicleMarket
    from context.price_modifications import PriceModifications # needs market classes
    from context.production_constraints import ProductionConstraints
    from context.cost_clouds import CostCloud

    from policy.offcycle_credits import OffCycleCredits
    from policy.upstream_methods import UpstreamMethods
    from policy.required_zev_share import RequiredZevShare
    from policy.drive_cycles import DriveCycles
    from policy.drive_cycle_weights import DriveCycleWeights
    from policy.incentives import Incentives
    from policy.policy_fuels import PolicyFuel
    from policy.credit_banking import CreditBank

    from producer.manufacturers import Manufacturer
    from producer.manufacturer_annual_data import ManufacturerAnnualData
    from producer.vehicles import VehicleFinal, DecompositionAttributes
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer import compliance_strategy

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

    file_io.validate_folder(omega_globals.options.output_folder)

    omega_globals.options.producer_calc_generalized_cost = compliance_strategy.calc_generalized_cost

    verbose_init = omega_globals.options.verbose

    try:
        init_fail = init_user_definable_decomposition_attributes(verbose_init)

        # instantiate database tables
        SQABase.metadata.create_all(omega_globals.engine)

        # load remaining input data
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=verbose_init)

        init_fail += DemandedSharesGCAM.init_database_from_file(omega_globals.options.demanded_shares_file,
                                                                verbose=verbose_init)

        init_fail += omega_globals.options.Reregistration.init_from_file(omega_globals.options.reregistration_file,
                                                   verbose=verbose_init)

        init_fail += omega_globals.options.AnnualVMT.init_database_from_file(omega_globals.options.annual_vmt_file,
                                                                 verbose=verbose_init)

        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=verbose_init)

        init_fail += FuelPrice.init_database_from_file(omega_globals.options.context_fuel_prices_file,
                                                       verbose=verbose_init)

        init_fail += NewVehicleMarket.init_database_from_file(omega_globals.options.context_new_vehicle_market_file,
                                                              verbose=verbose_init)

        NewVehicleMarket.init_context_new_vehicle_generalized_costs(
            omega_globals.options.context_new_vehicle_generalized_costs_file)

        init_fail += PriceModifications.init_from_file(omega_globals.options.price_modifications_file,
                                                       verbose=verbose_init)

        init_fail += ProductionConstraints.init_from_file(omega_globals.options.production_constraints_file,
                                                          verbose=verbose_init)

        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.cost_file,
                                                          verbose=verbose_init)

        init_fail += UpstreamMethods.init_from_file(omega_globals.options.fuel_upstream_methods_file,
                                                    verbose=verbose_init)

        init_fail += RequiredZevShare.init_from_file(omega_globals.options.required_zev_share_file,
                                                     verbose=verbose_init)

        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=verbose_init)

        init_fail += DriveCycleWeights.init_from_file(omega_globals.options.drive_cycle_weights_file,
                                                      verbose=verbose_init)

        init_fail += Incentives.init_from_file(omega_globals.options.production_multipliers_file,
                                               verbose=verbose_init)

        init_fail += omega_globals.options.VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                                         verbose=verbose_init)

        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=verbose_init)

        init_fail += CreditBank.validate_ghg_credits_template(omega_globals.options.ghg_credits_file,
                                                              verbose=verbose_init)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=verbose_init)
        
        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.vehicle_onroad_calculations_file,
                                                          verbose=verbose_init)

        if omega_globals.options.calc_criteria_emission_costs:
            init_fail += CostFactorsCriteria.init_database_from_file(omega_globals.options.criteria_cost_factors_file,
                                                                     omega_globals.options.cpi_deflators_file,
                                                                     verbose=verbose_init)

            init_fail += CostFactorsSCC.init_database_from_file(omega_globals.options.scc_cost_factors_file,
                                                                verbose=verbose_init)

            init_fail += CostFactorsEnergySecurity.init_database_from_file(
                omega_globals.options.energysecurity_cost_factors_file,
                verbose=verbose_init)

            init_fail += CostFactorsCongestionNoise.init_database_from_file(
                omega_globals.options.congestion_noise_cost_factors_file,
                verbose=verbose_init)

        if omega_globals.options.calc_effects:
            init_fail += EmissionFactorsPowersector.init_database_from_file(
                omega_globals.options.emission_factors_powersector_file,
                verbose=verbose_init)

            init_fail += EmissionFactorsRefinery.init_database_from_file(
                omega_globals.options.emission_factors_refinery_file,
                verbose=verbose_init)

            init_fail += EmissionFactorsVehicles.init_database_from_file(
                omega_globals.options.emission_factors_vehicles_file,
                verbose=verbose_init)

        # initial year = initial fleet model year (latest year of data)
        omega_globals.options.analysis_initial_year = \
            int(omega_globals.session.query(func.max(VehicleFinal.model_year)).scalar()) + 1

        # update vehicle annual data for base year fleet
        stock.update_stock(omega_globals.options.analysis_initial_year - 1)

    except Exception as e:
        init_fail += ["\n#INIT FAIL\n%s\n" % traceback.format_exc()]

    return init_fail


def run_omega(session_runtime_options, standalone_run=False):
    """
    Run a single OMEGA simulation session and run session postproc.

    Args:
        session_runtime_options (OMEGARuntimeOptions): session runtime options
        standalone_run (bool): True if session is run outside of the batch process

    """
    import traceback
    import time

    session_runtime_options.start_time = time.time()

    init_fail = None

    try:

        init_fail = init_omega(session_runtime_options)

        if not init_fail:
            omega_log.logwrite("Running %s:" % omega_globals.options.session_unique_name, echo_console=True)

            if omega_globals.options.run_profiler:
                # run with profiler
                import cProfile
                import re
                # return values of cProfile.run() show up in the globals namespace
                cProfile.run('iteration_log, credit_history = run_producer_consumer()', filename='omega2_profile.dmp')
                session_summary_results = postproc_session.run_postproc(
                    omega_globals()['iteration_log', 'credit_history'], standalone_run)
            else:
                # run without profiler
                iteration_log, credit_history = run_producer_consumer()
                session_summary_results = postproc_session.run_postproc(iteration_log, credit_history, standalone_run)

            # write output files
            summary_filename = omega_globals.options.output_folder + omega_globals.options.session_unique_name +\
                               '_summary_results.csv'
            session_summary_results.to_csv(summary_filename, index=False)
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            if omega_globals.options.session_is_reference and \
                    omega_globals.options.generate_context_new_vehicle_generalized_costs_file:
                from context.new_vehicle_market import NewVehicleMarket
                NewVehicleMarket.save_context_new_vehicle_generalized_costs(
                    omega_globals.options.context_new_vehicle_generalized_costs_file)

            omega_log.end_logfile("\nSession Complete")

            if omega_globals.options.run_profiler:
                os.system('snakeviz omega2_profile.dmp')

            # shut down the db
            omega_globals.session.close()
            omega_globals.engine.dispose()
            omega_globals.engine = None
            omega_globals.session = None
            omega_globals.options = None
        else:
            omega_log.logwrite(init_fail, echo_console=True)
            omega_log.end_logfile("\nSession Fail")
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

    except:
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc(), echo_console=True)
        print("### Check OMEGA log for error messages ###")
        omega_log.end_logfile("\nSession Fail")
        dump_omega_db_to_csv(omega_globals.options.database_dump_folder)


if __name__ == "__main__":
    try:
        import producer
        run_omega(OMEGARuntimeOptions(), standalone_run=True)  # to view in terminal: snakeviz omega2_profile.dmp
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
