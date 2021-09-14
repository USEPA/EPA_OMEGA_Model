"""

OMEGA top level code

Runs a single session, writes info to log files and the console, executes session post-processing.

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


def logwrite_shares_and_costs(calendar_year, convergence_error, producer_decision_and_response,
                              producer_consumer_iteration_num, cross_subsidy_iteration_num):
    """
    Write detailed producer-consumer cross-subsidy iteration data to the log and console.  For investigation of
    cross-subsidy search behavior.  Optionally called from ``iterate_producer_cross_subsidy()``

    Args:
        calendar_year (int): calendar year of the data
        convergence_error (float): producer-consumer convergence error
        producer_decision_and_response (Series): producer compliance search result with consumer share response
        producer_consumer_iteration_num (int): producer-consumer iteration number
        cross_subsidy_iteration_num (int): cross-subsidy iteration number

    Example:

        ::

            2020 producer/consumer_abs_share_frac_hauling.BEV = 0.0001 / 0.0034 (DELTA:0.003248, CE:0.958275)
            cross subsidized price / cost hauling.BEV         $56595 / $53900 R:1.050000
            2020 producer/consumer_abs_share_frac_hauling.ICE = 0.1413 / 0.1380 (DELTA:0.003248, CE:0.023530)
            cross subsidized price / cost hauling.ICE         $36749 / $36749 R:1.000000
            2020 producer/consumer_abs_share_frac_non_hauling.BEV= 0.0009 / 0.0293 (DELTA:0.028438, CE:0.970693)
            cross subsidized price / cost non_hauling.BEV     $40740 / $38800 R:1.050000
            2020 producer/consumer_abs_share_frac_non_hauling.ICE= 0.8577 / 0.8293 (DELTA:0.028438, CE:0.034291)
            cross subsidized price / cost non_hauling.ICE     $26526 / $26526 R:1.000000
            convergence_error = 0.028438
            cross subsidized price / cost ICE                 $27985 / $27985 R:1.000000
            cross subsidized price / cost BEV                 $42384 / $40366 R:1.050000
            cross subsidized price / cost hauling             $37225 / $37161 R:1.001738
            cross subsidized price / cost non_hauling         $27011 / $26945 R:1.002457
            cross subsidized price / cost TOTAL               $28456 / $28390 R:1.002324
            2020_0_0  SCORE:0.067565  SWSD:0.063371
            cost_multiplier_hauling.BEV                       = 1.05000 MR:[1.01666667 1.02777778 1.03888889 1.05      ] R:1.032787
            cost_multiplier_hauling.ICE                       = 1.00000 MR:[0.98333333 0.99444444 1.         1.00555556 1.01666667] R:1.033898
            cost_multiplier_non_hauling.BEV                   = 1.05000 MR:[1.01666667 1.02777778 1.03888889 1.05      ] R:1.032787
            cost_multiplier_non_hauling.ICE                   = 1.00000 MR:[0.98333333 0.99444444 1.         1.00555556 1.01666667] R:1.033898

    """
    for mc in omega_globals.options.MarketClass.market_classes:
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
                producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mc],
                producer_decision_and_response['average_cross_subsidized_price_%s' % mc] /
                producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mc]
            ), echo_console=True)

    omega_log.logwrite('convergence_error = %f' % convergence_error, echo_console=True)

    for cat in omega_globals.options.MarketClass.market_categories:
        omega_log.logwrite(
            ('cross subsidized price / cost %s' % cat).ljust(50) + '$%d / $%d R:%f' % (
                producer_decision_and_response['average_cross_subsidized_price_%s' % cat],
                producer_decision_and_response['average_cost_%s' % cat],
                producer_decision_and_response['average_cross_subsidized_price_%s' % cat] /
                producer_decision_and_response['average_cost_%s' % cat]
            ), echo_console=True)

    omega_log.logwrite(
        'cross subsidized price / cost TOTAL'.ljust(50) + '$%d / $%d R:%f' % (
            producer_decision_and_response['average_cross_subsidized_price_total'],
            producer_decision_and_response['average_new_vehicle_mfr_cost'],
            producer_decision_and_response['average_cross_subsidized_price_total'] /
            producer_decision_and_response['average_new_vehicle_mfr_cost']
        ), echo_console=True)

    omega_log.logwrite(
        '%d_%d_%d  SCORE:%f  SWSD:%f\n' % (calendar_year, producer_consumer_iteration_num, cross_subsidy_iteration_num,
                                           producer_decision_and_response['pricing_convergence_score'],
                                           producer_decision_and_response['abs_share_delta_total']), echo_console=True)


def update_iteration_log(iteration_log, calendar_year, compliance_id, converged, producer_consumer_iteration_num,
                         cross_subsidy_iteration_num, compliant, convergence_error):
    """
    Append columns to the iteration log (if not present) and update the value in the last row for the given arguments.

    Args:
        iteration_log (DataFrame): DataFrame of producer-consumer and cross-subsidy iteration data
        calendar_year (int): calendar year of the data
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        converged (bool): ``True`` if producer and consumer market shares are within tolerance
        producer_consumer_iteration_num (int): producer-consumer iteration number
        cross_subsidy_iteration_num (int): cross-subsidy iteration number
        compliant (bool): ``True`` if producer was able to find a compliant production option
        convergence_error (float): producer-consumer convergence error

    """
    iteration_log.loc[iteration_log.index[-1], 'calendar_year'] = calendar_year
    iteration_log.loc[iteration_log.index[-1], 'compliance_id'] = compliance_id
    iteration_log.loc[iteration_log.index[-1], 'converged'] = converged
    iteration_log.loc[iteration_log.index[-1], 'producer_consumer_iteration_num'] = producer_consumer_iteration_num
    iteration_log.loc[iteration_log.index[-1], 'cross_subsidy_iteration_num'] = cross_subsidy_iteration_num
    iteration_log.loc[iteration_log.index[-1], 'compliant'] = compliant
    iteration_log.loc[iteration_log.index[-1], 'convergence_error'] = convergence_error


def run_producer_consumer():
    """
    Create producer cost-minimizing technology and market share options, in consideration of market response from
    the consumer, possibly with iteration between the two. Iterates across years for each compliance ID.  When
    consolidating manufacturers, the compliance ID is 'consolidated_OEM', otherwise the compliance ID is the
    manufacturer name.

    Returns:
         Iteration log dataframe, dict of credit bank information (iteration_log, credit_banks),
         updates omega database with final vehicle technology and market share data

    """

    from producer.vehicles import VehicleFinal
    from producer import compliance_search
    from policy.credit_banking import CreditBank

    iteration_log = pd.DataFrame()

    credit_banks = dict()

    for compliance_id in VehicleFinal.compliance_ids:
        omega_log.logwrite("\nRunning %s: Manufacturer=%s" % (omega_globals.options.session_unique_name, compliance_id),
                           echo_console=True)

        analysis_end_year = omega_globals.options.analysis_final_year + 1

        credit_banks[compliance_id] = CreditBank(
            omega_globals.options.ghg_credit_params_file,
            omega_globals.options.ghg_credits_file, compliance_id)

        for calendar_year in range(omega_globals.options.analysis_initial_year, analysis_end_year):

            credit_banks[compliance_id].update_credit_age(calendar_year)

            # TODO: make credit strategy modular, like upstream methods?
            # strategy: use expiring credits, pay any expiring debits in one shot:
            # expiring_credits_Mg = credit_banks[compliance_id].get_expiring_credits_Mg(calendar_year)
            # expiring_debits_Mg = credit_banks[compliance_id].get_expiring_debits_Mg(calendar_year)
            # strategic_target_offset_Mg = expiring_credits_Mg + expiring_debits_Mg

            # strategy: use credits and pay debits over their remaining lifetime, instead of all at once:
            # current_credits, current_debits = credit_banks[compliance_id].get_credit_info(calendar_year)
            # for c in current_credits + current_debits:
            #     strategic_target_offset_Mg += (c.remaining_balance_Mg / c.remaining_years)

            # strategy: try to hit the target and make up for minor previous compliance discrepancies
            #           (ignoring base year banked credits):
            strategic_target_offset_Mg = 0
            current_credits, current_debits = credit_banks[compliance_id].get_credit_info(calendar_year)
            for c in current_debits:
                strategic_target_offset_Mg += c.remaining_balance_Mg

            producer_decision_and_response = None
            best_winning_combo_with_sales_response = None

            producer_consumer_iteration_num = 0
            iterate_producer_consumer = True

            while iterate_producer_consumer:
                omega_log.logwrite("Running %s:  Year=%s  Iteration=%s" %
                                   (omega_globals.options.session_unique_name, calendar_year, producer_consumer_iteration_num),
                                   echo_console=True)

                candidate_mfr_composite_vehicles, producer_decision, market_class_tree, producer_compliant = \
                    compliance_search.search_production_options(compliance_id, calendar_year,
                                                                producer_decision_and_response,
                                                                producer_consumer_iteration_num, strategic_target_offset_Mg)

                market_class_vehicle_dict = calc_market_data(candidate_mfr_composite_vehicles, producer_decision)

                best_winning_combo_with_sales_response, iteration_log, producer_decision_and_response = \
                    iterate_producer_cross_subsidy(calendar_year, compliance_id, best_winning_combo_with_sales_response,
                                                   candidate_mfr_composite_vehicles, iteration_log,
                                                   producer_consumer_iteration_num, market_class_vehicle_dict,
                                                   producer_decision, strategic_target_offset_Mg)

                converged, convergence_error = \
                    detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

                iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)

                update_iteration_log(iteration_log, calendar_year, compliance_id, converged,
                                     producer_consumer_iteration_num, -1, producer_compliant, convergence_error)

                # decide whether to continue iterating or not
                iterate_producer_consumer = omega_globals.options.iterate_producer_consumer \
                                            and producer_consumer_iteration_num < omega_globals.options.producer_consumer_max_iterations \
                                            and not converged

                if iterate_producer_consumer:
                    producer_consumer_iteration_num += 1
                else:
                    if producer_consumer_iteration_num >= omega_globals.options.producer_consumer_max_iterations:
                        omega_log.logwrite('PRODUCER-CONSUMER MAX ITERATIONS EXCEEDED, ROLLING BACK TO BEST ITERATION',
                                           echo_console=True)
                        producer_decision_and_response = best_winning_combo_with_sales_response

            compliance_search.finalize_production(calendar_year, compliance_id, candidate_mfr_composite_vehicles,
                                                  producer_decision_and_response)

            credit_banks[compliance_id].handle_credit(calendar_year,
                                                     producer_decision_and_response['total_credits_co2e_megagrams'])

            stock.update_stock(calendar_year, compliance_id)

        if (omega_globals.options.log_consumer_iteration_years == 'all') or \
                (calendar_year in omega_globals.options.log_consumer_iteration_years)\
                or (calendar_year == analysis_end_year-1):
            iteration_log.to_csv(omega_globals.options.output_folder + omega_globals.options.session_unique_name +
                                 '_producer_consumer_iteration_log.csv', index=False)

        credit_banks[compliance_id].credit_bank.to_csv(omega_globals.options.output_folder +
                                                       omega_globals.options.session_unique_name +
                                                       '_GHG_credit_balances %s.csv' % compliance_id, index=False)

        credit_banks[compliance_id].transaction_log.to_csv(
            omega_globals.options.output_folder + omega_globals.options.session_unique_name +
            '_GHG_credit_transactions %s.csv' % compliance_id, index=False)

    return iteration_log, credit_banks


def iterate_producer_cross_subsidy(calendar_year, compliance_id, best_producer_decision_and_response,
                                   candidate_mfr_composite_vehicles, iteration_log, producer_consumer_iteration_num,
                                   market_class_vehicle_dict, producer_decision, strategic_target_offset_Mg):
    """
    Perform producer pricing cross-subsidy iteration.  Cross-subsidy maintains the total average price, as well
    as average price by non-responsive market categories.  The goal is to achieve convergence between producer and
    consumer desired absolute market class shares, within a tolerance.  The cross-subsidy is implemented through
    price multipliers, the minimum and maximum range of which are user inputs (e.g. 0.95 -> 1.05).  The initial range
    of multipliers is the full span from min to max, subsequent iterations tighten the range and hone in on the
    multipliers that provide the most convergent result while maintaining the average prices mentioned above.

    Args:
        calendar_year (int): calendar year of the iteration
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        best_producer_decision_and_response (Series): producer compliance search result with
            consumer share response with best convergence
        candidate_mfr_composite_vehicles ([CompositeVehicles]): list of manufacturer composite vehicles, production
            candidates
        iteration_log (DataFrame): DataFrame of producer-consumer and cross-subsidy iteration data
        producer_consumer_iteration_num (int): producer-consumer iteration number
        market_class_vehicle_dict (dict): dict of candidate_mfr_composite_vehicles grouped by market class
        producer_decision (Series): result of producer compliance search, *without* consumer response
        strategic_target_offset_Mg (float): desired producer distance from compliance, in CO2e Mg, zero for compliance,
            > 0 for under-compliance, < 0 for over-compliance

    Returns:
        tuple of best producer decision and response, the iteration log, and last producer decision and response
        (best_producer_decision_and_response, iteration_log, producer_decision_and_response)

    """
    from producer import compliance_search
    import consumer

    producer_decision['winning_combo_share_weighted_cost'] = 0
    producer_decision['winning_combo_share_weighted_generalized_cost'] = 0
    for mc in market_class_vehicle_dict:
        producer_decision['winning_combo_share_weighted_cost'] += producer_decision['average_new_vehicle_mfr_cost_%s' % mc] * \
                                                                  producer_decision['producer_abs_share_frac_%s' % mc]

        producer_decision['winning_combo_share_weighted_generalized_cost'] += \
            producer_decision['average_new_vehicle_mfr_generalized_cost_%s' % mc] * producer_decision['producer_abs_share_frac_%s' % mc]

    consumer.sales_volume.new_vehicle_sales_response(calendar_year, compliance_id,
                                                     producer_decision['winning_combo_share_weighted_generalized_cost'])

    multiplier_columns = ['cost_multiplier_%s' % mc for mc in omega_globals.options.MarketClass.market_classes]

    cross_subsidy_iteration_num = 0
    producer_decision_and_response = pd.DataFrame()

    producer_decision = producer_decision.to_frame().transpose()

    prev_multiplier_range = dict()
    continue_search = True
    while continue_search:
        continue_search, cross_subsidy_options = create_cross_subsidy_options(calendar_year, continue_search,
                                                                              multiplier_columns, prev_multiplier_range,
                                                                              producer_decision,
                                                                              producer_decision_and_response)

        producer_decision_and_response = \
            omega_globals.options.SalesShare.calc_shares(cross_subsidy_options,calendar_year)

        ###############################################################################################################
        calc_sales_and_cost_data(calendar_year, compliance_id, market_class_vehicle_dict, producer_decision_and_response)
        # propagate total sales down to composite vehicles by market class share and reg class share,
        # calculate new compliance status for each producer-technology / consumer response combination
        compliance_search.create_production_options(candidate_mfr_composite_vehicles,
                                                    producer_decision_and_response,
                                                    total_sales=producer_decision_and_response['new_vehicle_sales'])
        # propagate vehicle sales up to market class sales
        calc_market_data(candidate_mfr_composite_vehicles, producer_decision_and_response)
        ###############################################################################################################

        producer_decision_and_response['strategic_compliance_ratio'] = \
            (producer_decision_and_response['total_cert_co2e_megagrams'] - strategic_target_offset_Mg) / \
            producer_decision_and_response['total_target_co2e_megagrams']

        # calculate "distance to origin" (minimal price and market share errors):
        pricing_convergence_score = producer_decision_and_response['abs_share_delta_total']**1
        # add terms to maintain prices of non-responsive market categories during convergence:
        for cat in omega_globals.options.MarketClass.non_responsive_market_categories:
            pricing_convergence_score += abs(1 - producer_decision_and_response['average_cross_subsidized_price_%s' % cat] /
                                        producer_decision_and_response['average_cost_%s' % cat])**1

        producer_decision_and_response['pricing_convergence_score'] = pricing_convergence_score**1

        if omega_globals.options.log_producer_decision_and_response_years == 'all' or \
                calendar_year in omega_globals.options.log_producer_decision_and_response_years:
            producer_decision_and_response.to_csv('%sproducer_decision_and_response_%s_%s_%s.csv' %
                                                  (omega_globals.options.output_folder, calendar_year, producer_consumer_iteration_num, cross_subsidy_iteration_num))

        producer_decision_and_response = \
            producer_decision_and_response.loc[producer_decision_and_response['pricing_convergence_score'].idxmin()]

        # if this code is uncommented, the reference case sales will match context sales EXACTLY, by compensating for
        # any slight offset during the convergence process:
        # ###############################################################################################################
        # if o2.options.session_is_reference:
        #     calc_sales_totals(calendar_year, compliance_id, market_class_vehicle_dict, producer_decision_and_response)
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
             producer_decision_and_response['average_new_vehicle_mfr_cost'])

        converged, convergence_error = detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

        if (best_producer_decision_and_response is None) or (producer_decision_and_response['pricing_convergence_score'] < best_producer_decision_and_response['pricing_convergence_score']):
            best_producer_decision_and_response = producer_decision_and_response.copy()

        iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)

        if 'consumer' in omega_globals.options.verbose_console_modules:
            logwrite_shares_and_costs(calendar_year, convergence_error, producer_decision_and_response, producer_consumer_iteration_num,
                                      cross_subsidy_iteration_num)

        update_iteration_log(iteration_log, calendar_year, compliance_id, converged, producer_consumer_iteration_num,
                             cross_subsidy_iteration_num, converged, convergence_error)

        cross_subsidy_iteration_num += 1

        continue_search = continue_search and not converged

    if 'consumer' in omega_globals.options.verbose_console_modules:
        for mc, cc in zip(omega_globals.options.MarketClass.market_classes, multiplier_columns):
            omega_log.logwrite(('FINAL %s' % cc).ljust(50) + '= %.5f' % producer_decision_and_response[cc], echo_console=True)
        if converged:
            omega_log.logwrite('PRODUCER-CONSUMER CONVERGED CE:%f' % convergence_error, echo_console=True)

        omega_log.logwrite('', echo_console=True)

    return best_producer_decision_and_response, iteration_log, producer_decision_and_response


def calc_sales_and_cost_data(calendar_year, compliance_id, market_class_vehicle_dict, producer_decision_and_response):
    """
    Calculate sales and cost/price data.  Namely, the absolute share delta between producer and consumer
    absolute market shares, the share weighted average cross subsidized price by market class, the total share weighted 
    average cross subsidized price, the average modified cross subsidized price by market class, the average new
    vehicle manufacturer cost and generalized cost, and total new vehicle sales, including the market response to
    average new vehicle manufacturer generalized cost.

    Args:
        calendar_year (int): calendar year of the iteration
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        market_class_vehicle_dict (dict): dict of candidate_mfr_composite_vehicles grouped by market class
        producer_decision_and_response (Series): producer compliance search result with consumer share response

    Returns:
        Updates ``producer_decision_and_response`` columns
        
    """
    import consumer

    producer_decision_and_response['abs_share_delta_total'] = 0
    producer_decision_and_response['average_cross_subsidized_price_total'] = 0
    producer_decision_and_response['average_modified_cross_subsidized_price_total'] = 0
    producer_decision_and_response['average_new_vehicle_mfr_cost'] = 0
    producer_decision_and_response['average_new_vehicle_mfr_generalized_cost'] = 0

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

        producer_decision_and_response['average_new_vehicle_mfr_cost'] += \
            producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

        producer_decision_and_response['average_new_vehicle_mfr_generalized_cost'] += \
            producer_decision_and_response['average_new_vehicle_mfr_generalized_cost_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

    producer_decision_and_response['new_vehicle_sales'] = \
        producer_decision_and_response['total_sales'] * \
        consumer.sales_volume.new_vehicle_sales_response(calendar_year, compliance_id,
                                                         producer_decision_and_response[
                                                             'average_new_vehicle_mfr_generalized_cost'])


def create_cross_subsidy_options(calendar_year, continue_search, multiplier_columns, prev_multiplier_range,
                                 producer_decision, producer_decision_and_response):
    """
    Calculate cross subsidy pricing options based on the allowable multiplier range, within a subsequently smaller
    range as iteration progresses, until the search collapses (min mutliplier == max multiplier).

    Args:
        calendar_year (int): calendar year of the iteration
        continue_search (bool): prior value of ``continue_search``, set to ``False`` if search collapses
        multiplier_columns ([strs]): list of cost multiplier columns,
            e.g. ['cost_multiplier_hauling.BEV', 'cost_multiplier_hauling.ICE', ...]
        prev_multiplier_range (dict): empty on first pass then contains a dict of previous multiplier ranges by market
            class, e.g. {'cost_multiplier_hauling.BEV': array([0.95, 0.98333333, 1.0, 1.01666667, 1.05]), ...}
        producer_decision (DataFrame): producer production decision dataframe
        producer_decision_and_response (DataFrame, Series): empty DataFrame on first pass then contains producer
            compliance search result and most-convergent consumer response to previous cross subsidy options as a
            Series

    Returns:
        tuple of whether to continue cross subsidy search, dataframe of producer decision with cross subsidy pricing
        options (continue_search, price_options_df)

    """
    import numpy as np
    from context.price_modifications import PriceModifications

    price_options_df = producer_decision

    if producer_decision_and_response.empty:
        # first time through, span full range
        multiplier_range = \
            np.unique(np.append(np.linspace(omega_globals.options.consumer_pricing_multiplier_min,
                                            omega_globals.options.consumer_pricing_multiplier_max,
                                            omega_globals.options.consumer_pricing_num_options), 1.0))

    search_collapsed = True
    for mc, mcc in zip(omega_globals.options.MarketClass.market_classes, multiplier_columns):
        if not producer_decision_and_response.empty:
            # subsequent passes, tighten up search range to find convergent multipliers
            multiplier_range, search_collapsed = tighten_multiplier_range(mcc, prev_multiplier_range,
                                                                          producer_decision_and_response,
                                                                          search_collapsed)

        price_options_df = cartesian_prod(price_options_df, pd.DataFrame(multiplier_range, columns=[mcc]))

        price_options_df['average_cross_subsidized_price_%s' % mc] = price_options_df['average_new_vehicle_mfr_cost_%s' % mc] * price_options_df[mcc]

        price_modification = PriceModifications.get_price_modification(calendar_year, mc)
        price_options_df['average_modified_cross_subsidized_price_%s' % mc] = price_options_df['average_cross_subsidized_price_%s' % mc] + price_modification

        prev_multiplier_range[mcc] = multiplier_range

    if not producer_decision_and_response.empty and search_collapsed:
        continue_search = False
        if 'consumer' in omega_globals.options.verbose_console_modules:
            omega_log.logwrite('SEARCH COLLAPSED')

    return continue_search, price_options_df


def tighten_multiplier_range(multiplier_column, prev_multiplier_range, producer_decision_and_response,
                             search_collapsed):
    """
    Tighten cross subsidy multiplier range.

    Args:
        multiplier_column (str): name of the multiplier range to tighten, e.g. 'cost_multiplier_hauling.BEV'
        prev_multiplier_range (dict): empty on first pass then contains a dict of previous multiplier ranges by market
            class, e.g. {'cost_multiplier_hauling.BEV': array([0.95, 0.98333333, 1.0, 1.01666667, 1.05]), ...}
        producer_decision_and_response (Series): contains producer compliance search result and most-convergent
            consumer response to previous cross subsidy options
        search_collapsed (bool): prior value of search collapsed, gets ANDed with collapse condition

    Returns:
        tuple of multiplier range array (e.g. array([1.01666667, 1.02777778, 1.03888889, 1.05])) and whether search has
        collapsed (multiplier_range, search_collapsed)

    """
    import numpy as np

    prev_multiplier_span_frac = \
        prev_multiplier_range[multiplier_column][-1] / prev_multiplier_range[multiplier_column][0] - 1
    index = \
        np.nonzero(prev_multiplier_range[multiplier_column] == producer_decision_and_response[multiplier_column])[0][0]
    if index == 0:
        min_val = max(omega_globals.options.consumer_pricing_multiplier_min,
                      producer_decision_and_response[multiplier_column] - prev_multiplier_span_frac *
                      producer_decision_and_response[multiplier_column])
    else:
        min_val = prev_multiplier_range[multiplier_column][index - 1]
    if index == len(prev_multiplier_range[multiplier_column]) - 1:
        max_val = min(omega_globals.options.consumer_pricing_multiplier_max,
                      producer_decision_and_response[multiplier_column] + prev_multiplier_span_frac *
                      producer_decision_and_response[multiplier_column])
    else:
        max_val = prev_multiplier_range[multiplier_column][index + 1]
    # try new range, include prior value in range...
    multiplier_range = np.unique(np.append(
        np.linspace(min_val, max_val, omega_globals.options.consumer_pricing_num_options),
        producer_decision_and_response[multiplier_column]))
    search_collapsed = search_collapsed and ((len(multiplier_range) == 2) or ((max_val / min_val - 1) <= 1e-3))
    if 'consumer' in omega_globals.options.verbose_console_modules:
        omega_log.logwrite(('%s' % multiplier_column).ljust(50) + '= %.5f MR:%s R:%f' % (
            producer_decision_and_response[multiplier_column], multiplier_range, max_val / min_val), echo_console=True)

    return multiplier_range, search_collapsed


def calc_market_data(candidate_mfr_composite_vehicles, producer_decision):
    """
    Creates a dictionary of candidate vehicles binned by market class, calculates market class and market category
    data via ``calc_market_class_data()`` and ``calc_market_category_data()``

    Args:
        candidate_mfr_composite_vehicles: list of candidate composite vehicles that minimize producer compliance cost
        producer_decision (Series): Series that corresponds with candidate_mfr_composite_vehicles, has producer market
            shares, costs, compliance data (Mg CO2e), may also contain consumer response

    Returns:
        dict of candidate vehicles binned by market class, updates producer_decision with calculated market data

    See Also:
        ``calc_market_class_data()``, ``calc_market_category_data()``

    """
    # group vehicles by market class
    market_class_vehicle_dict = omega_globals.options.MarketClass.get_market_class_dict()
    for new_veh in candidate_mfr_composite_vehicles:
        market_class_vehicle_dict[new_veh.market_class_id].append(new_veh)

    calc_market_class_data(market_class_vehicle_dict, producer_decision)

    calc_market_category_data(producer_decision)

    return market_class_vehicle_dict


def calc_market_class_data(market_class_vehicle_dict, producer_decision):
    """
    Calculate market class average CO2e g/mi, kWh/mi, manufacturer new vehicle cost and generalized cost, average fuel
    price, and sales.

    Args:
        market_class_vehicle_dict (dict): candidate vehicles binned by market class
        producer_decision (Series): Series that corresponds with candidate_mfr_composite_vehicles, has producer market
            shares, costs, compliance data (Mg CO2e), may also contain consumer response

    Returns:
        Nothing, updates ``producer_decsion`` with calculated market data

    """
    # calculate sales-weighted co2 g/mi and cost by market class
    for mc in omega_globals.options.MarketClass.market_classes:
        market_class_vehicles = market_class_vehicle_dict[mc]
        if market_class_vehicles:
            producer_decision['average_co2e_gpmi_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'onroad_direct_co2e_grams_per_mile')

            producer_decision['average_kwh_pmi_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'onroad_direct_kwh_per_mile')

            producer_decision['average_new_vehicle_mfr_cost_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'new_vehicle_mfr_cost_dollars')

            producer_decision['average_new_vehicle_mfr_generalized_cost_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count',
                               'new_vehicle_mfr_generalized_cost_dollars')

            producer_decision['average_fuel_price_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'retail_fuel_price_dollars_per_unit')

            producer_decision['sales_%s' % mc] = 0
            for v in market_class_vehicles:
                producer_decision['sales_%s' % mc] += producer_decision['veh_%s_sales' % v.vehicle_id]
        else:
            producer_decision['average_co2e_gpmi_%s' % mc] = 0
            producer_decision['average_kwh_pmi_%s' % mc] = 0
            producer_decision['average_new_vehicle_mfr_cost_%s' % mc] = 0
            producer_decision['average_new_vehicle_mfr_generalized_cost_%s' % mc] = 0
            producer_decision['sales_%s' % mc] = 0


def calc_market_category_data(producer_decision):
    """
    Calculate market category average cost and generalized cost, average cross subsidized price, sales and producer
    absolute shares.

    Args:
        producer_decision (Series): Series that corresponds with candidate_mfr_composite_vehicles, has producer market
            shares, costs, compliance data (Mg CO2e), may also contain consumer response

    Returns:
        Nothing, updates ``producer_decsion`` with calculated market data

    """
    import numpy as np

    for mcat in omega_globals.options.MarketClass.market_categories:
        producer_decision['average_cost_%s' % mcat] = 0
        producer_decision['average_generalized_cost_%s' % mcat] = 0
        producer_decision['average_cross_subsidized_price_%s' % mcat] = 0
        producer_decision['sales_%s' % mcat] = 0
        producer_decision['producer_abs_share_frac_%s' % mcat] = 0

        for mc in omega_globals.options.MarketClass.market_classes:
            if mcat in mc.split('.'):
                producer_decision['average_cost_%s' % mcat] += \
                    producer_decision['average_new_vehicle_mfr_cost_%s' % mc] * \
                    np.maximum(1, producer_decision['sales_%s' % mc])

                producer_decision['average_generalized_cost_%s' % mcat] += \
                    producer_decision['average_new_vehicle_mfr_generalized_cost_%s' % mc] * \
                    np.maximum(1, producer_decision['sales_%s' % mc])

                if 'average_cross_subsidized_price_%s' % mc in producer_decision:
                    producer_decision['average_cross_subsidized_price_%s' % mcat] += \
                        producer_decision['average_cross_subsidized_price_%s' % mc] * \
                        np.maximum(1, producer_decision['sales_%s' % mc])

                producer_decision['sales_%s' % mcat] += \
                    np.maximum(1, producer_decision['sales_%s' % mc])

                producer_decision['producer_abs_share_frac_%s' % mcat] += \
                    producer_decision['producer_abs_share_frac_%s' % mc]

        producer_decision['average_cost_%s' % mcat] = \
            producer_decision['average_cost_%s' % mcat] / producer_decision['sales_%s' % mcat]

        producer_decision['average_generalized_cost_%s' % mcat] = \
            producer_decision['average_generalized_cost_%s' % mcat] / producer_decision['sales_%s' % mcat]

        producer_decision['average_cross_subsidized_price_%s' % mcat] = \
            producer_decision['average_cross_subsidized_price_%s' % mcat] / producer_decision['sales_%s' % mcat]


def detect_convergence(producer_decision_and_response, market_class_dict):
    """
    Detect producer-consumer market share convergence.

    Args:
        producer_decision_and_response (Series): contains producer compliance search result and most-convergent
            consumer response to previous cross subsidy options
        market_class_dict (dict): dict of candidate vehicles binned by market class

    Returns:
        tuple of convergence bool and convergence error, (converged, convergence_error)

    """
    converged = abs(1 - producer_decision_and_response['price_cost_ratio_total']) <= \
                omega_globals.options.producer_cross_subsidy_price_tolerance

    convergence_error = 0
    for mc in market_class_dict:
        convergence_error = \
            max(convergence_error, abs(producer_decision_and_response['producer_abs_share_frac_%s' % mc] -
                                       producer_decision_and_response['consumer_abs_share_frac_%s' % mc]))
        converged = converged and (convergence_error <= omega_globals.options.producer_consumer_convergence_tolerance)

    return converged, convergence_error


def init_user_definable_submodules():
    """
    Import dynamic modules that are specified by the input file input template name and set the session runtime
    options appropriately.

    Returns:
        List of template/input errors, else empty list on success

    """
    import importlib

    init_fail = []

    # user-definable policy modules
    # pull in reg classes before building database tables (declaring classes) that check reg class validity
    module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
    omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
    init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
        omega_globals.options.policy_reg_classes_file)

    module_name = get_template_name(omega_globals.options.policy_targets_file)
    omega_globals.options.VehicleTargets = importlib.import_module(module_name).VehicleTargets

    module_name = get_template_name(omega_globals.options.offcycle_credits_file)
    omega_globals.options.OffCycleCredits = importlib.import_module(module_name).OffCycleCredits

    # user-definable consumer modules
    module_name = get_template_name(omega_globals.options.vehicle_reregistration_file)
    omega_globals.options.Reregistration = importlib.import_module(module_name).Reregistration

    module_name = get_template_name(omega_globals.options.onroad_vmt_file)
    omega_globals.options.OnroadVMT = importlib.import_module(module_name).OnroadVMT

    module_name = get_template_name(omega_globals.options.sales_share_file)
    omega_globals.options.SalesShare = importlib.import_module(module_name).SalesShare

    module_name = get_template_name(omega_globals.options.market_classes_file)
    omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

    # user-definable producer modules
    module_name = get_template_name(omega_globals.options.producer_generalized_cost_file)
    omega_globals.options.ProducerGeneralizedCost = importlib.import_module(module_name).ProducerGeneralizedCost

    return init_fail


def init_user_definable_decomposition_attributes(verbose_init):
    """
    Init user definable decomposition attributes.  Decomposition attributes are values that are tracked at each point
    in a vehicle's cost curve / frontier during composition and are interpolated during decomposition.  Examples
    of decomposition attributes are individual drive cycle results and off-cycle credit values.  Technology application
    can also be tracked via optional flags in the simulated vehicles (cost cloud) data.

    These values need to be determined before building the database so the dynamic fields can be added to the schema
    via the SQLAlchemy metadata.

    Args:
        verbose_init (bool): if True enable additional init output to console

    Returns:
        List of template/input errors, else empty list on success

    See Also:
        ``producer.vehicles.DecompositionAttributes``, ``producer.vehicles.VehicleFinal``

    """
    from policy.drive_cycles import DriveCycles
    from producer.vehicles import VehicleFinal, DecompositionAttributes
    from context.cost_clouds import CostCloud

    init_fail = []

    init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.vehicle_simulation_results_and_costs_file,
                                                      verbose=verbose_init)

    init_fail += omega_globals.options.OffCycleCredits.init_from_file(omega_globals.options.offcycle_credits_file,
                                                verbose=verbose_init)

    init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                            verbose=verbose_init)

    vehicle_columns = get_template_columns(omega_globals.options.vehicles_file)
    VehicleFinal.dynamic_columns = list(set.difference(set(vehicle_columns), VehicleFinal.base_input_template_columns))
    for dc in VehicleFinal.dynamic_columns:
        VehicleFinal.dynamic_attributes.append(make_valid_python_identifier(dc))

    DecompositionAttributes.init()
    # dynamically add decomposition attributes (which may vary based on user inputs, such as off-cycle credits)
    for attr in DecompositionAttributes.values + VehicleFinal.dynamic_attributes:
        if attr not in VehicleFinal.__dict__:
            if int(sqlalchemy.__version__.split('.')[1]) > 3:
                sqlalchemy.ext.declarative.DeclarativeMeta.__setattr__(VehicleFinal, attr, Column(attr, Float))
            else:
                sqlalchemy.ext.declarative.api.DeclarativeMeta.__setattr__(VehicleFinal, attr, Column(attr, Float))

    return init_fail


def init_omega(session_runtime_options):
    """
    Initialize OMEGA data structures and build the database.

    Args:
        session_runtime_options (OMEGASessionSettings): session runtime options

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

    init_fail += init_user_definable_submodules()

    # import database modules to populate ORM metadata
    from context.onroad_fuels import OnroadFuel
    from context.fuel_prices import FuelPrice
    from context.new_vehicle_market import NewVehicleMarket
    from context.price_modifications import PriceModifications # needs market classes
    from context.production_constraints import ProductionConstraints
    from context.cost_clouds import CostCloud

    from policy.upstream_methods import UpstreamMethods
    from policy.required_sales_share import RequiredSalesShare
    from policy.drive_cycles import DriveCycles
    from policy.drive_cycle_weights import DriveCycleWeights
    from policy.incentives import Incentives
    from policy.policy_fuels import PolicyFuel
    from policy.credit_banking import CreditBank

    from producer.manufacturers import Manufacturer
    from producer.manufacturer_annual_data import ManufacturerAnnualData
    from producer.vehicles import VehicleFinal, DecompositionAttributes
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer import compliance_search

    from effects.cost_factors_criteria import CostFactorsCriteria
    from effects.cost_factors_scc import CostFactorsSCC
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise
    from effects.emission_factors_powersector import EmissionFactorsPowersector
    from effects.emission_factors_refinery import EmissionFactorsRefinery
    from effects.emission_factors_vehicles import EmissionFactorsVehicles
    # from effects.cost_effects_scc import CostEffectsSCC
    # from effects.cost_effects_criteria import CostEffectsCriteria
    # from effects.cost_effects_non_emissions import CostEffectsNonEmissions

    file_io.validate_folder(omega_globals.options.output_folder)

    verbose_init = omega_globals.options.verbose

    try:
        init_fail = init_user_definable_decomposition_attributes(verbose_init)

        # instantiate database tables
        SQABase.metadata.create_all(omega_globals.engine)

        # load remaining input data
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                                      verbose=verbose_init)

        init_fail += omega_globals.options.SalesShare.init_from_file(omega_globals.options.sales_share_file,
                                                                     verbose=verbose_init)

        init_fail += omega_globals.options.Reregistration.init_from_file(omega_globals.options.vehicle_reregistration_file,
                                                                         verbose=verbose_init)

        init_fail += omega_globals.options.OnroadVMT.init_from_file(omega_globals.options.onroad_vmt_file,
                                                                    verbose=verbose_init)

        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=verbose_init)

        init_fail += FuelPrice.init_database_from_file(omega_globals.options.context_fuel_prices_file,
                                                       verbose=verbose_init)

        init_fail += NewVehicleMarket.init_database_from_file(omega_globals.options.context_new_vehicle_market_file,
                                                              verbose=verbose_init)

        NewVehicleMarket.init_context_new_vehicle_generalized_costs(
            omega_globals.options.context_new_vehicle_generalized_costs_file)

        init_fail += PriceModifications.init_from_file(omega_globals.options.vehicle_price_modifications_file,
                                                       verbose=verbose_init)

        init_fail += omega_globals.options.ProducerGeneralizedCost.init_from_file(
            omega_globals.options.producer_generalized_cost_file, verbose=verbose_init)

        init_fail += ProductionConstraints.init_from_file(omega_globals.options.production_constraints_file,
                                                          verbose=verbose_init)

        init_fail += UpstreamMethods.init_from_file(omega_globals.options.fuel_upstream_methods_file,
                                                    verbose=verbose_init)

        init_fail += RequiredSalesShare.init_from_file(omega_globals.options.required_sales_share_file,
                                                       verbose=verbose_init)

        init_fail += DriveCycleWeights.init_from_file(omega_globals.options.drive_cycle_weights_file,
                                                      verbose=verbose_init)

        init_fail += Incentives.init_from_file(omega_globals.options.production_multipliers_file,
                                               verbose=verbose_init)

        init_fail += omega_globals.options.VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                                         verbose=verbose_init)

        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=verbose_init)

        init_fail += CreditBank.validate_ghg_credit_params_template(omega_globals.options.ghg_credit_params_file,
                                                              verbose=verbose_init)

        init_fail += CreditBank.validate_ghg_credits_template(omega_globals.options.ghg_credits_file,
                                                              verbose=verbose_init)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                                        verbose=verbose_init)

        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.onroad_vehicle_calculations_file,
                                                          verbose=verbose_init)

        # if omega_globals.options.calc_criteria_emission_costs:
        #     init_fail += CostFactorsCriteria.init_database_from_file(omega_globals.options.criteria_cost_factors_file,
        #                                                              omega_globals.options.cpi_deflators_file,
        #                                                              verbose=verbose_init)

        if omega_globals.options.calc_effects == 'Physical and Costs':
            init_fail += EmissionFactorsPowersector.init_database_from_file(omega_globals.options.emission_factors_powersector_file,
                                                                            verbose=verbose_init)

            init_fail += EmissionFactorsRefinery.init_database_from_file(omega_globals.options.emission_factors_refinery_file,
                                                                         verbose=verbose_init)

            init_fail += EmissionFactorsVehicles.init_database_from_file(omega_globals.options.emission_factors_vehicles_file,
                                                                         verbose=verbose_init)

            init_fail += CostFactorsCriteria.init_database_from_file(omega_globals.options.criteria_cost_factors_file,
                                                                     omega_globals.options.cpi_deflators_file,
                                                                     verbose=verbose_init)

            init_fail += CostFactorsSCC.init_database_from_file(omega_globals.options.scc_cost_factors_file,
                                                                verbose=verbose_init)

            init_fail += CostFactorsEnergySecurity.init_database_from_file(omega_globals.options.energysecurity_cost_factors_file,
                                                                           verbose=verbose_init)

            init_fail += CostFactorsCongestionNoise.init_database_from_file(omega_globals.options.congestion_noise_cost_factors_file,
                                                                            verbose=verbose_init)

        if omega_globals.options.calc_effects == 'Physical':
            init_fail += EmissionFactorsPowersector.init_database_from_file(omega_globals.options.emission_factors_powersector_file,
                                                                            verbose=verbose_init)

            init_fail += EmissionFactorsRefinery.init_database_from_file(omega_globals.options.emission_factors_refinery_file,
                                                                         verbose=verbose_init)

            init_fail += EmissionFactorsVehicles.init_database_from_file(omega_globals.options.emission_factors_vehicles_file,
                                                                         verbose=verbose_init)

        # initial year = initial fleet model year (latest year of data)
        omega_globals.options.analysis_initial_year = \
            int(omega_globals.session.query(func.max(VehicleFinal.model_year)).scalar()) + 1

        # update vehicle annual data for base year fleet
        stock.update_stock(omega_globals.options.analysis_initial_year - 1)

    except:
        init_fail += ["\n#INIT FAIL\n%s\n" % traceback.format_exc()]

    return init_fail


def run_omega(session_runtime_options, standalone_run=False):
    """
    Run a single OMEGA simulation session and run session postproc.

    Args:
        session_runtime_options (OMEGASessionSettings): session runtime options
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
                import cProfile, pstats
                profiler = cProfile.Profile()
                profiler.enable()

            iteration_log, credit_banks = run_producer_consumer()

            if omega_globals.options.run_profiler:
                profiler.disable()
                stats = pstats.Stats(profiler)
                stats.dump_stats('omega_profile.dmp')

            session_summary_results = postproc_session.run_postproc(iteration_log, credit_banks, standalone_run)

            # write output files
            summary_filename = omega_globals.options.output_folder + omega_globals.options.session_unique_name \
                               + '_summary_results.csv'

            session_summary_results.to_csv(summary_filename, index=False)
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            from context.new_vehicle_market import NewVehicleMarket

            if omega_globals.options.session_is_reference and \
                    omega_globals.options.generate_context_new_vehicle_generalized_costs_file:
                NewVehicleMarket.save_context_new_vehicle_generalized_costs(
                    omega_globals.options.context_new_vehicle_generalized_costs_file)

            NewVehicleMarket.save_session_new_vehicle_generalized_costs(
                omega_globals.options.output_folder + omega_globals.options.session_unique_name +
                '_new_vehicle_prices.csv')

            omega_log.end_logfile("\nSession Complete")

            if omega_globals.options.run_profiler:
                os.system('snakeviz omega_profile.dmp')

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
        run_omega(OMEGASessionSettings(), standalone_run=True)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
