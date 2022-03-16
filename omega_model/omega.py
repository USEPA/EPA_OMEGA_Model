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


def calc_cross_subsidy_options_and_response(calendar_year, market_class_tree, compliance_id, producer_decision,
                                            cross_subsidy_options_and_response, producer_consumer_iteration_num,
                                            iteration_log, node_name='', verbose=False):
    """
    Traverse the market class tree and generate cross subsidy multipliers and the associated consumer response for
    responsive market categories/classes

    Args:
        calendar_year (int): the year in which the compliance calculations take place
        market_class_tree (dict): a dict of CompositeVehicle object lists hiearchically grouped by market categories
            into market classes
        compliance_id (str): name of manufacturer, e.g. 'consolidated_OEM'
        producer_decision (Series): result of producer compliance search, *without* consumer response
        cross_subsidy_options_and_response (DataFrame, Series): initiall empty dataframe or Series containing cross
            subsidy options and response
        producer_consumer_iteration_num (int): producer-consumer iteration number
        iteration_log (DataFrame): DataFrame of producer-consumer iteration data
        node_name (str): name of the current node
        verbose (bool): enable additional console output if True

    Returns:
        tuple of ``cross_subsidy_options_and_response``, updated ``iteration_log``

    """
    children = list(market_class_tree)
    if verbose:
        print('children: %s' % children)

    if node_name:
        cross_subsidy_pair = [node_name + '.' + c for c in children]
    else:
        cross_subsidy_pair = [c for c in children]

    if all(s in omega_globals.options.MarketClass.responsive_market_categories for s in children):
        if verbose:
            print('responsive: %s' % cross_subsidy_pair)

        # search cross subsidy options at this level of the tree
        cross_subsidy_options_and_response, iteration_log = \
            search_cross_subsidies(calendar_year, compliance_id, node_name, cross_subsidy_pair, producer_decision,
                                   cross_subsidy_options_and_response, producer_consumer_iteration_num, iteration_log)

    else:
        if verbose:
            print('non-responsive: %s' % cross_subsidy_pair)
        # do no search cross-subsidy options at this level of the tree

    for child in market_class_tree:
        if type(market_class_tree[child]) is dict:
            if verbose:
                print('processing child ' + child)
            # process subtree
            cross_subsidy_options_and_response, iteration_log = \
                calc_cross_subsidy_options_and_response(calendar_year, market_class_tree[child], compliance_id,
                                                        producer_decision, cross_subsidy_options_and_response,
                                                        producer_consumer_iteration_num, iteration_log, node_name=child,
                                                        verbose=verbose)

    return cross_subsidy_options_and_response, iteration_log


def logwrite_shares_and_costs(calendar_year, share_convergence_error, cross_subsidy_pricing_error,
                              producer_decision_and_response, producer_consumer_iteration_num,
                              cross_subsidy_iteration_num):
    """
    Write detailed producer-consumer cross-subsidy iteration data to the log and console.  For investigation of
    cross-subsidy search behavior.  Optionally called from ``iterate_producer_cross_subsidy()``

    Args:
        calendar_year (int): calendar year of the data
        share_convergence_error (float): producer-consumer convergence error
        cross_subsidy_pricing_error (float): cross-subsidy pricing error
        producer_decision_and_response (Series): producer compliance search result with consumer share response
        producer_consumer_iteration_num (int): producer-consumer iteration number
        cross_subsidy_iteration_num (int): cross-subsidy iteration number

    Example:

        ::

            2020 producer / consumer_abs_share_frac_hauling.BEV    = 0.0002 / 0.0033 (DELTA:0.003084)
            2020 producer / consumer_abs_share_frac_hauling.ICE    = 0.1699 / 0.1668 (DELTA:0.003084)
            2020 producer / consumer_abs_share_frac_non_hauling.BEV= 0.0008 / 0.0190 (DELTA:0.018211)
            2020 producer / consumer_abs_share_frac_non_hauling.ICE= 0.8291 / 0.8109 (DELTA:0.018211)

            cross subsidized price / cost hauling.BEV         $56595 / $53900 R:1.050000
            cross subsidized price / cost hauling.ICE         $36656 / $36709 R:0.998562
            cross subsidized price / cost non_hauling.BEV     $40763 / $38821 R:1.050000
            cross subsidized price / cost non_hauling.ICE     $26512 / $26562 R:0.998125

            cross subsidized price / cost BEV                 $43073 / $41022 R:1.050000
            cross subsidized price / cost ICE                 $28243 / $28294 R:0.998222
            cross subsidized price / cost hauling             $37037 / $37038 R:0.999994
            cross subsidized price / cost non_hauling         $26839 / $26843 R:0.999847
            cross subsidized price / cost TOTAL               $28574 / $28577 R:0.999879

            2020_0_0  SCORE:0.000845, CE:0.018211, CSPE:0.000121

    """
    omega_log.logwrite('', echo_console=True)

    for mc in sorted(omega_globals.options.MarketClass.market_classes):
        omega_log.logwrite(('%d producer / consumer_abs_share_frac_%s' % (calendar_year, mc)).ljust(55) +
                           '= %.4f / %.4f (DELTA:%f)' % (
                               producer_decision_and_response['producer_abs_share_frac_%s' % mc],
                               producer_decision_and_response['consumer_abs_share_frac_%s' % mc],
                               abs(producer_decision_and_response['producer_abs_share_frac_%s' % mc] -
                                   producer_decision_and_response['consumer_abs_share_frac_%s' % mc])
                           ), echo_console=True)

    omega_log.logwrite('', echo_console=True)

    for mc in sorted(omega_globals.options.MarketClass.market_classes):
        omega_log.logwrite(
            ('cross subsidized price / cost %s' % mc).ljust(50) + '$%d / $%d R:%f' % (
                producer_decision_and_response['average_cross_subsidized_price_%s' % mc],
                producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mc],
                producer_decision_and_response['average_cross_subsidized_price_%s' % mc] /
                producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mc]
            ), echo_console=True)

    omega_log.logwrite('', echo_console=True)

    for mcat in sorted(omega_globals.options.MarketClass.market_categories):
        omega_log.logwrite(
            ('cross subsidized price / cost %s' % mcat).ljust(50) + '$%d / $%d R:%f' % (
                producer_decision_and_response['average_cross_subsidized_price_%s' % mcat],
                producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mcat],
                producer_decision_and_response['average_cross_subsidized_price_%s' % mcat] /
                producer_decision_and_response['average_new_vehicle_mfr_cost_%s' % mcat]
            ), echo_console=True)

    omega_log.logwrite(
        'cross subsidized price / cost TOTAL'.ljust(50) + '$%d / $%d R:%f' % (
            producer_decision_and_response['average_cross_subsidized_price_total'],
            producer_decision_and_response['average_new_vehicle_mfr_cost'],
            producer_decision_and_response['average_cross_subsidized_price_total'] /
            producer_decision_and_response['average_new_vehicle_mfr_cost']
        ), echo_console=True)

    omega_log.logwrite('', echo_console=True)

    omega_log.logwrite(
        '%d_%d_%d  SCORE:%f, CE:%f, CSPE:%f\n' % (calendar_year, producer_consumer_iteration_num,
                                                  cross_subsidy_iteration_num,
                                                  producer_decision_and_response['pricing_score'],
                                                  share_convergence_error, cross_subsidy_pricing_error), echo_console=True)


def update_cross_subsidy_log_data(producer_decision_and_response, calendar_year, compliance_id, converged,
                                  producer_consumer_iteration_num, compliant, share_convergence_error):
    """
    Adds/updates data in the producer decision and response for the given arguments.

    Args:
        producer_decision_and_response (Series): producer decision and cross-subsidy iteration response data
        calendar_year (int): calendar year of the data
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        converged (bool): ``True`` if producer and consumer market shares are within tolerance
        producer_consumer_iteration_num (int): producer-consumer iteration number
        compliant (bool): ``True`` if producer was able to find a compliant production option
        share_convergence_error (float): producer-consumer convergence error

    """
    producer_decision_and_response['calendar_year'] = calendar_year
    producer_decision_and_response['compliance_id'] = compliance_id
    producer_decision_and_response['converged'] = converged
    producer_decision_and_response['producer_consumer_iteration_num'] = producer_consumer_iteration_num
    producer_decision_and_response['compliant'] = compliant
    producer_decision_and_response['share_convergence_error'] = share_convergence_error


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
                                   (omega_globals.options.session_unique_name, calendar_year,
                                    producer_consumer_iteration_num),
                                   echo_console=True)

                candidate_mfr_composite_vehicles, producer_decision, market_class_tree, producer_compliant = \
                    compliance_search.search_production_options(compliance_id, calendar_year,
                                                                producer_decision_and_response,
                                                                producer_consumer_iteration_num,
                                                                strategic_target_offset_Mg)

                producer_market_classes = calc_market_data(candidate_mfr_composite_vehicles, producer_decision)

                best_winning_combo_with_sales_response, iteration_log, producer_decision_and_response = \
                    iterate_producer_cross_subsidy(calendar_year, compliance_id, best_winning_combo_with_sales_response,
                                                   candidate_mfr_composite_vehicles, iteration_log,
                                                   producer_consumer_iteration_num, producer_market_classes,
                                                   producer_decision, strategic_target_offset_Mg)

                converged, share_convergence_error, cross_subsidy_pricing_error = \
                    detect_convergence(producer_decision_and_response, producer_market_classes)

                # decide whether to continue iterating or not
                iterate_producer_consumer = omega_globals.options.iterate_producer_consumer \
                                            and producer_consumer_iteration_num < omega_globals.options.producer_consumer_max_iterations \
                                            and not converged

                if iterate_producer_consumer:
                    producer_consumer_iteration_num += 1
                else:
                    if producer_consumer_iteration_num >= omega_globals.options.producer_consumer_max_iterations:
                        if 'p-c_max_iterations' in omega_globals.options.verbose_console_modules:
                            omega_log.logwrite('PRODUCER-CONSUMER MAX ITERATIONS EXCEEDED, ROLLING BACK TO BEST ITERATION',
                                           echo_console=True)
                        producer_decision_and_response = best_winning_combo_with_sales_response

            update_cross_subsidy_log_data(producer_decision_and_response, calendar_year, compliance_id, converged,
                                          producer_consumer_iteration_num, producer_compliant, share_convergence_error)

            producer_decision_and_response['cross_subsidy_iteration_num'] = -1  # tag final result

            iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)

            compliance_search.finalize_production(calendar_year, compliance_id, candidate_mfr_composite_vehicles,
                                                  producer_decision_and_response)

            credit_banks[compliance_id].handle_credit(calendar_year,
                                                     producer_decision_and_response['total_credits_co2e_megagrams'])

            stock.update_stock(calendar_year, compliance_id)

        credit_banks[compliance_id].credit_bank.to_csv(omega_globals.options.output_folder +
                                                       omega_globals.options.session_unique_name +
                                                       '_GHG_credit_balances %s.csv' % compliance_id, index=False)

        credit_banks[compliance_id].transaction_log.to_csv(
            omega_globals.options.output_folder + omega_globals.options.session_unique_name +
            '_GHG_credit_transactions %s.csv' % compliance_id, index=False)

    iteration_log.to_csv(
        omega_globals.options.output_folder + omega_globals.options.session_unique_name +
        '_producer_consumer_iteration_log.csv', columns=sorted(iteration_log.columns))

    return iteration_log, credit_banks


def calc_cross_subsidy_metrics(mcat, cross_subsidy_pair, producer_decision, cross_subsidy_options_and_response):
    """
    Calculate cross-subsidy metrics (prices and share deltas).

    Args:
        mcat (str): market category, e.g. 'hauling' / 'non_hauling'
        cross_subsidy_pair (list): list of cross-subsidized market classes, e.g. ['hauling.BEV', 'hauling.ICE']
        producer_decision (Series): result of producer compliance search, *without* consumer response
        cross_subsidy_options_and_response (DataFrame): dataframe containing cross subsidy options and response

    Returns:
        Nothing, updates ``cross_subsidy_options_and_response``

    """
    cross_subsidy_options_and_response['average_new_vehicle_mfr_cost_%s' % mcat] = 0
    cross_subsidy_options_and_response['average_cross_subsidized_price_%s' % mcat] = 0
    cross_subsidy_options_and_response['abs_share_delta_%s' % mcat] = 0

    if mcat == '':
        cross_subsidy_options_and_response['consumer_abs_share_frac_%s' % mcat] = 1.0

    for mc in cross_subsidy_pair:
        cross_subsidy_options_and_response['average_new_vehicle_mfr_cost_%s' % mcat] += \
            producer_decision['average_new_vehicle_mfr_cost_%s' % mc] * \
            cross_subsidy_options_and_response['consumer_abs_share_frac_%s' % mc] / \
            cross_subsidy_options_and_response['consumer_abs_share_frac_%s' % mcat]

        cross_subsidy_options_and_response['average_cross_subsidized_price_%s' % mcat] += \
            cross_subsidy_options_and_response['average_cross_subsidized_price_%s' % mc] * \
            cross_subsidy_options_and_response['consumer_abs_share_frac_%s' % mc] / \
            cross_subsidy_options_and_response['consumer_abs_share_frac_%s' % mcat]

        cross_subsidy_options_and_response['abs_share_delta_%s' % mc] = abs(
            producer_decision['producer_abs_share_frac_%s' % mc] -
            cross_subsidy_options_and_response['consumer_abs_share_frac_%s' % mc])

        cross_subsidy_options_and_response['abs_share_delta_%s' % mcat] += \
            0.5 * cross_subsidy_options_and_response['abs_share_delta_%s' % mc]

    cross_subsidy_options_and_response['pricing_price_ratio_delta_%s' % mcat] = \
        abs(1 - cross_subsidy_options_and_response['average_cross_subsidized_price_%s' % mcat] /
            cross_subsidy_options_and_response['average_new_vehicle_mfr_cost_%s' % mcat])


def iterate_producer_cross_subsidy(calendar_year, compliance_id, best_producer_decision_and_response,
                                   candidate_mfr_composite_vehicles, iteration_log, producer_consumer_iteration_num,
                                   producer_market_classes, producer_decision, strategic_target_offset_Mg):
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
        producer_market_classes (list): list of candidate_mfr_composite_vehicles grouped by market class
        producer_decision (Series): result of producer compliance search, *without* consumer response
        strategic_target_offset_Mg (float): desired producer distance from compliance, in CO2e Mg, zero for compliance,
            > 0 for under-compliance, < 0 for over-compliance

    Returns:
        tuple of best producer decision and response, the iteration log, and last producer decision and response
        (best_producer_decision_and_response, iteration_log, cross_subsidy_options_and_response)

    """
    import numpy as np
    from producer import compliance_search
    import consumer

    producer_decision['average_new_vehicle_mfr_generalized_cost_initial'] = \
        calc_new_vehicle_mfr_generalized_cost(producer_decision, producer_market_classes)

    producer_decision['context_new_vehicle_sales'] = producer_decision['total_sales']

    consumer.sales_volume.new_vehicle_sales_response(calendar_year, compliance_id,
                                                     producer_decision['average_new_vehicle_mfr_generalized_cost_initial'],
                                                     update_context_new_vehicle_generalized_cost=True)

    cross_subsidy_options_and_response = pd.DataFrame()

    market_class_tree = omega_globals.options.MarketClass.get_market_class_tree()

    cross_subsidy_options_and_response, iteration_log = \
        calc_cross_subsidy_options_and_response(calendar_year, market_class_tree, compliance_id, producer_decision,
                                                cross_subsidy_options_and_response, producer_consumer_iteration_num,
                                                iteration_log, node_name='', verbose=False)

    duplicate_columns = set.intersection(set(producer_decision.index), set(cross_subsidy_options_and_response.index))
    producer_decision = producer_decision.drop(duplicate_columns)
    producer_decision_and_response = producer_decision.append(cross_subsidy_options_and_response)

    producer_decision_and_response['cross_subsidy_iteration_num'] = producer_consumer_iteration_num

    calc_sales_and_cost_data_from_shares(calendar_year, compliance_id, producer_market_classes,
                                         producer_decision_and_response)

    compliance_search.create_production_options_from_shares(candidate_mfr_composite_vehicles,
                                                            producer_decision_and_response,
                                                            total_sales=
                                                            producer_decision_and_response['new_vehicle_sales'])

    calc_market_data(candidate_mfr_composite_vehicles, producer_decision_and_response)

    # the 0.01 factors in the below equation protect against divide by zero when/if standards are zero
    producer_decision_and_response['strategic_compliance_ratio'] = \
        (producer_decision_and_response['total_cert_co2e_megagrams'] - strategic_target_offset_Mg + 0.01) / \
        (producer_decision_and_response['total_target_co2e_megagrams'] + 0.01)

    compliant = producer_decision_and_response['strategic_compliance_ratio'] <= 1.0 or \
                abs(1 - producer_decision_and_response['strategic_compliance_ratio']) <= \
                    omega_globals.options.producer_compliance_search_tolerance

    mcat_converged, share_convergence_error, cross_subsidy_pricing_error = \
        detect_convergence(producer_decision_and_response, producer_market_classes)

    if (best_producer_decision_and_response is None) or \
            (producer_decision_and_response['pricing_score']
             < best_producer_decision_and_response['pricing_score']):
        best_producer_decision_and_response = producer_decision_and_response.copy()

    update_cross_subsidy_log_data(producer_decision_and_response, calendar_year, compliance_id, mcat_converged,
                                  producer_consumer_iteration_num, compliant, share_convergence_error)

    iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)

    return best_producer_decision_and_response, iteration_log, producer_decision_and_response


def search_cross_subsidies(calendar_year, compliance_id, mcat, cross_subsidy_pair, producer_decision,
                           cross_subsidy_options_and_response, producer_consumer_iteration_num, iteration_log):
    """
    Search the available cross-subsidy space (as determined by min and max pricing multipliers) for multipliers that
    minimize the error between producer and consumer market shares while maintaining revenue neutrality for the
    producer.

    Args:
        calendar_year (int): the year in which the compliance calculations take place
        compliance_id (str): name of manufacturer, e.g. 'consolidated_OEM'
        mcat (str): market category, e.g. 'hauling' / 'non_hauling'
        cross_subsidy_pair (list): list of cross-subsidized market classes, e.g. ['hauling.BEV', 'hauling.ICE']
        producer_decision (Series): result of producer compliance search, *without* consumer response
        cross_subsidy_options_and_response (DataFrame, Series): initially empty dataframe or Series containing cross
            subsidy options and response
        producer_consumer_iteration_num (int): producer-consumer iteration number
        iteration_log (DataFrame): DataFrame of producer-consumer iteration data

    Returns:
        tuple of ``cross_subsidy_options_and_response``, updated ``iteration_log``

    """
    multiplier_columns = ['cost_multiplier_%s' % mc for mc in cross_subsidy_pair]

    mcat_cross_subsidy_iteration_num = 0
    prev_multiplier_range = dict()
    continue_search = True

    while continue_search:
        continue_search, cross_subsidy_options = \
            create_cross_subsidy_options(calendar_year, continue_search, cross_subsidy_pair, multiplier_columns,
                                         prev_multiplier_range, producer_decision, cross_subsidy_options_and_response)

        cross_subsidy_options_and_response = \
            omega_globals.options.SalesShare.calc_shares(calendar_year, producer_decision, cross_subsidy_options, mcat,
                                                         cross_subsidy_pair)

        calc_cross_subsidy_metrics(mcat, cross_subsidy_pair, producer_decision, cross_subsidy_options_and_response)

        price_weight = 0.925

        # calculate score, weighted distance to the origin
        cross_subsidy_options_and_response['pricing_score'] = \
            ((1 - price_weight) * cross_subsidy_options_and_response['abs_share_delta_%s' % mcat] ** 2 +
             price_weight * cross_subsidy_options_and_response['pricing_price_ratio_delta_%s' % mcat] ** 2) ** 0.5

        # select best score
        selected_cross_subsidy_index = cross_subsidy_options_and_response['pricing_score'].idxmin()

        # note selected option
        cross_subsidy_options_and_response['selected_cross_subsidy_option'] = 0
        cross_subsidy_options_and_response.loc[selected_cross_subsidy_index, 'selected_cross_subsidy_option'] = 1

        cross_subsidy_options_and_response['cross_subsidy_iteration_num_%s' % mcat] = \
            mcat_cross_subsidy_iteration_num

        if 'cross_subsidy_search' in omega_globals.options.verbose_log_modules:
            iteration_log = iteration_log.append(cross_subsidy_options_and_response, ignore_index=True)

        # select best cross subsidy option
        cross_subsidy_options_and_response = \
            cross_subsidy_options_and_response.loc[selected_cross_subsidy_index].copy()

        share_convergence_error = cross_subsidy_options_and_response['abs_share_delta_%s' % mcat]
        cross_subsidy_pricing_error = cross_subsidy_options_and_response['pricing_price_ratio_delta_%s' % mcat]

        mcat_converged = (cross_subsidy_pricing_error <=
                          omega_globals.options.producer_cross_subsidy_price_tolerance) \
                         and \
                         (share_convergence_error <= omega_globals.options.producer_consumer_convergence_tolerance)

        mcat_cross_subsidy_iteration_num += 1

        # update iteration log
        update_cross_subsidy_log_data(cross_subsidy_options_and_response, calendar_year, compliance_id, mcat_converged,
                                      producer_consumer_iteration_num, None,
                                      cross_subsidy_options_and_response['abs_share_delta_%s' % mcat])

        iteration_log = iteration_log.append(cross_subsidy_options_and_response, ignore_index=True)

        continue_search = continue_search and not mcat_converged

    update_market_classes_console_log(calendar_year, mcat, cross_subsidy_pair, share_convergence_error,
                                      cross_subsidy_pricing_error, mcat_converged, producer_consumer_iteration_num,
                                      cross_subsidy_options_and_response)

    if 'cross_subsidy_search' in omega_globals.options.verbose_console_modules:
        omega_log.logwrite('', echo_console=True)

    return cross_subsidy_options_and_response, iteration_log


def update_market_classes_console_log(calendar_year, mcat, cross_subsidy_pair, share_convergence_error,
                                      cross_subsidy_pricing_error,
                                      mcat_converged, producer_consumer_iteration_num, producer_decision_and_response):
    """
    Write producer-consumer cross subsidy data to the console and log, if enabled by ``verbose_console_modules``.

    Args:
        calendar_year (int): the year in which the compliance calculations take place
        share_convergence_error (float): producer-consumer convergence error
        cross_subsidy_pricing_error (float): cross-subsidy pricing error
        mcat_converged (bool): ``True`` if the market class price/cost ratioand the
            producer-consumer shares are within tolerance
        producer_consumer_iteration_num (int): producer-consumer iteration number
        producer_decision_and_response (Series): producer decision and cross-subsidy iteration response data

    """
    if 'p-c_shares_and_costs' in omega_globals.options.verbose_console_modules:
        logwrite_shares_and_costs(calendar_year, share_convergence_error, cross_subsidy_pricing_error,
                                  producer_decision_and_response, producer_consumer_iteration_num,
                                  producer_consumer_iteration_num)
    multiplier_columns = ['cost_multiplier_%s' % mc for mc in cross_subsidy_pair]

    if 'cross_subsidy_multipliers' in omega_globals.options.verbose_console_modules:
        for mc, cc in zip(omega_globals.options.MarketClass.market_classes, multiplier_columns):
            omega_log.logwrite(('FINAL %s' % cc).ljust(50) + '= %.5f' % producer_decision_and_response[cc],
                               echo_console=True)

    if 'cross_subsidy_convergence' in omega_globals.options.verbose_console_modules:
        if mcat_converged:
            omega_log.logwrite('   PRODUCER-CONSUMER CONVERGED %s CE:%f, CSPE:%f' %
                               (' / '.join(cross_subsidy_pair), share_convergence_error, cross_subsidy_pricing_error), echo_console=True)
        else:
            omega_log.logwrite('** PRODUCER-CONSUMER CONVERGENCE FAIL %s CE:%f, CSPE:%f **' %
                               (' / '.join(cross_subsidy_pair), share_convergence_error, cross_subsidy_pricing_error), echo_console=True)


def calc_new_vehicle_mfr_generalized_cost(producer_decision, producer_market_classes):
    """

    Args:
        producer_decision (Series): result of producer compliance search, *without* consumer response
        producer_market_classes:

    Returns:

    """
    average_new_vehicle_mfr_generalized_cost = 0
    for mc in producer_market_classes:
        average_new_vehicle_mfr_generalized_cost += \
            producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mc] * \
            producer_decision['producer_abs_share_frac_%s' % mc]

    return average_new_vehicle_mfr_generalized_cost


def calc_sales_and_cost_data_from_shares(calendar_year, compliance_id, producer_market_classes,
                                         producer_decision_and_response):
    """
    Calculate sales and cost/price data.  Namely, the absolute share delta between producer and consumer
    absolute market shares, the share weighted average cross subsidized price by market class, the total share weighted 
    average cross subsidized price, the average modified cross subsidized price by market class, the average new
    vehicle manufacturer cost and generalized cost, and total new vehicle sales, including the market response to
    average new vehicle manufacturer generalized cost.

    Args:
        calendar_year (int): calendar year of the iteration
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        producer_market_classes (list): list of producer market classes
        producer_decision_and_response (Series): producer compliance search result with consumer share response

    Returns:
        Updates ``producer_decision_and_response`` columns
        
    """
    import numpy as np
    import consumer
    from context.price_modifications import PriceModifications

    producer_decision_and_response['average_cross_subsidized_price_total'] = 0
    producer_decision_and_response['average_modified_cross_subsidized_price_total'] = 0
    producer_decision_and_response['average_new_vehicle_mfr_cost'] = 0
    producer_decision_and_response['average_new_vehicle_mfr_generalized_cost'] = 0

    for mc in producer_market_classes:
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
            producer_decision_and_response['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mc] * \
            producer_decision_and_response['consumer_abs_share_frac_%s' % mc]

    producer_decision_and_response['new_vehicle_sales'] = \
        producer_decision_and_response['context_new_vehicle_sales'] * \
        consumer.sales_volume.new_vehicle_sales_response(calendar_year, compliance_id,
                                                         producer_decision_and_response[
                                                             'average_new_vehicle_mfr_generalized_cost'])


def create_cross_subsidy_options(calendar_year, continue_search, mc_pair, multiplier_columns, prev_multiplier_range,
                                 producer_decision, producer_decision_and_response):
    """
    Calculate cross subsidy pricing options based on the allowable multiplier range, within a subsequently smaller
    range as iteration progresses, until the search collapses (min multiplier == max multiplier).

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

    first_pass = not all([mc in producer_decision_and_response for mc in multiplier_columns])

    if first_pass and producer_decision_and_response.empty:
        price_options_df = pd.DataFrame()
    else:
        price_options_df = producer_decision_and_response.to_frame().transpose()
        # drop multiplier columns to prevent duplicates during cartesian product:
        price_options_df = price_options_df.drop(multiplier_columns, axis=1, errors='ignore')

    if first_pass:
        # first time through, span full range, including all 1's
        multiplier_range = \
            np.unique(np.append(np.linspace(omega_globals.options.consumer_pricing_multiplier_min,
                                            omega_globals.options.consumer_pricing_multiplier_max,
                                            omega_globals.options.consumer_pricing_num_options), 1.0))
    search_collapsed = True
    for mc, mcc in zip(mc_pair, multiplier_columns):

        if not first_pass:
            # subsequent passes, tighten up search range to find convergent multipliers
            multiplier_range, search_collapsed = tighten_multiplier_range(mcc, prev_multiplier_range,
                                                                          producer_decision_and_response,
                                                                          search_collapsed)
        else:
            if 'cross_subsidy_search' in omega_globals.options.verbose_console_modules:
                omega_log.logwrite(('%s' % mcc).ljust(35) + '= MR:%s' % multiplier_range,
                                   echo_console=True)

        price_options_df = cartesian_prod(price_options_df, pd.DataFrame(multiplier_range, columns=[mcc]))

        price_options_df['average_cross_subsidized_price_%s' % mc] = \
            producer_decision['average_new_vehicle_mfr_cost_%s' % mc] * price_options_df[mcc]

        price_modification = PriceModifications.get_price_modification(calendar_year, mc)

        price_options_df['average_modified_cross_subsidized_price_%s' % mc] = \
            price_options_df['average_cross_subsidized_price_%s' % mc] + price_modification

        prev_multiplier_range[mcc] = multiplier_range

    if not first_pass and search_collapsed:
        continue_search = False
        if 'cross_subsidy_search' in omega_globals.options.verbose_console_modules:
            omega_log.logwrite('SEARCH COLLAPSED', echo_console=True)

    return continue_search, price_options_df


def tighten_multiplier_range(multiplier_column, prev_multiplier_ranges, producer_decision_and_response,
                             search_collapsed):
    """
    Tighten cross subsidy multiplier range.

    Args:
        multiplier_column (str): name of the multiplier range to tighten, e.g. 'cost_multiplier_hauling.BEV'
        prev_multiplier_ranges (dict): empty on first pass then contains a dict of previous multiplier ranges by market
            class, e.g. {'cost_multiplier_hauling.BEV': array([0.95, 0.98333333, 1.0, 1.01666667, 1.05]), ...}
        producer_decision_and_response (Series): contains producer compliance search result and most-convergent
            consumer response to previous cross subsidy options
        search_collapsed (bool): prior value of search collapsed, gets ANDed with collapse condition

    Returns:
        tuple of multiplier range array (e.g. array([1.01666667, 1.02777778, 1.03888889, 1.05])) and whether search has
        collapsed (multiplier_range, search_collapsed)

    """
    import numpy as np

    prev_multiplier = producer_decision_and_response[multiplier_column]
    prev_multiplier_range = prev_multiplier_ranges[multiplier_column]
    span_frac_gain = 6

    prev_multiplier_span_frac = \
        prev_multiplier_range[-1] / prev_multiplier_range[0] - 1

    index = np.nonzero(prev_multiplier_range == prev_multiplier)[0][0]

    if index == 0:
        min_val = max(omega_globals.options.consumer_pricing_multiplier_min,
                      prev_multiplier * (1 - prev_multiplier_span_frac * span_frac_gain))

        if prev_multiplier > omega_globals.options.consumer_pricing_multiplier_min and \
                'cross_subsidy_search' in omega_globals.options.verbose_console_modules:
            print('++ hit minimum %s %f : %f' % (multiplier_column, prev_multiplier, min_val))
    else:
        min_val = prev_multiplier_range[index - 1]

    if index == len(prev_multiplier_range) - 1:
        max_val = min(omega_globals.options.consumer_pricing_multiplier_max,
                      prev_multiplier * (1 + prev_multiplier_span_frac * span_frac_gain))

        if prev_multiplier > omega_globals.options.consumer_pricing_multiplier_max and \
                'cross_subsidy_search' in omega_globals.options.verbose_console_modules:
            print('++ hit maximum %s %f : %f' % (multiplier_column, prev_multiplier, max_val))
    else:
        max_val = prev_multiplier_range[index + 1]

    # try new range, include prior value in range...
    multiplier_range = np.unique(np.append(
        np.linspace(min_val, max_val, omega_globals.options.consumer_pricing_num_options),
        prev_multiplier))

    # search_collapsed = search_collapsed and ((len(multiplier_range) == 2) or ((max_val / min_val - 1) <= 1e-3))
    search_collapsed = search_collapsed and ((len(multiplier_range) == 2) or (max_val - min_val <= 1e-4))
    if 'cross_subsidy_search' in omega_globals.options.verbose_console_modules:
        mr_str = str(['%.8f' % m for m in multiplier_range]).replace("'", '')
        omega_log.logwrite(('%s' % multiplier_column).ljust(35) + '= %.5f MR:%s R:%f' % (
            prev_multiplier, mr_str, max_val - min_val), echo_console=True)

    return multiplier_range, search_collapsed


def calc_market_data(candidate_mfr_composite_vehicles, producer_decision):
    """
    Creates a dictionary of candidate vehicles binned by market class, calculates market class and market category
    data via ``calc_market_class_data()`` and ``calc_market_category_data()``

    Args:
        candidate_mfr_composite_vehicles (list): list of candidate composite vehicles that minimize producer compliance cost
        producer_decision (Series): Series that corresponds with candidate_mfr_composite_vehicles, has producer market
            shares, costs, compliance data (Mg CO2e), may also contain consumer response

    Returns:
        list of producer market classes (market classes with candidate vehicles),
        updates producer_decision with calculated market data

    See Also:
        ``calc_market_class_data()``, ``calc_market_category_data()``

    """
    # group vehicles by market class
    market_class_vehicle_dict = omega_globals.options.MarketClass.get_market_class_dict()
    for new_veh in candidate_mfr_composite_vehicles:
        market_class_vehicle_dict[new_veh.market_class_id].append(new_veh)

    calc_market_class_data(market_class_vehicle_dict, producer_decision)

    calc_market_category_data(producer_decision)

    return list(market_class_vehicle_dict.keys())


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
            producer_decision['average_onroad_direct_co2e_gpmi_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'onroad_direct_co2e_grams_per_mile')

            producer_decision['average_onroad_direct_kwh_pmi_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'onroad_direct_kwh_per_mile')

            producer_decision['average_new_vehicle_mfr_cost_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'new_vehicle_mfr_cost_dollars')

            producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count',
                               'new_vehicle_mfr_generalized_cost_dollars')

            producer_decision['average_retail_fuel_price_dollars_per_unit_%s' % mc] = \
                weighted_value(market_class_vehicles, 'initial_registered_count', 'retail_fuel_price_dollars_per_unit')

            producer_decision['sales_%s' % mc] = 0
            for v in market_class_vehicles:
                producer_decision['sales_%s' % mc] += producer_decision['veh_%s_sales' % v.vehicle_id]
        else:
            producer_decision['average_onroad_direct_co2e_gpmi_%s' % mc] = 0
            producer_decision['average_onroad_direct_kwh_pmi_%s' % mc] = 0
            producer_decision['average_new_vehicle_mfr_cost_%s' % mc] = 0
            producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mc] = 0
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
        producer_decision['average_new_vehicle_mfr_cost_%s' % mcat] = 0
        producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mcat] = 0
        producer_decision['average_cross_subsidized_price_%s' % mcat] = 0
        producer_decision['sales_%s' % mcat] = 0
        producer_decision['producer_abs_share_frac_%s' % mcat] = 0

        for mc in omega_globals.options.MarketClass.market_classes:
            if mcat in mc.split('.'):
                producer_decision['average_new_vehicle_mfr_cost_%s' % mcat] += \
                    producer_decision['average_new_vehicle_mfr_cost_%s' % mc] * \
                    np.maximum(1, producer_decision['sales_%s' % mc])

                producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mcat] += \
                    producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mc] * \
                    np.maximum(1, producer_decision['sales_%s' % mc])

                if 'average_cross_subsidized_price_%s' % mc in producer_decision:
                    producer_decision['average_cross_subsidized_price_%s' % mcat] += \
                        producer_decision['average_cross_subsidized_price_%s' % mc] * \
                        np.maximum(1, producer_decision['sales_%s' % mc])

                producer_decision['sales_%s' % mcat] += \
                    np.maximum(1, producer_decision['sales_%s' % mc])

                producer_decision['producer_abs_share_frac_%s' % mcat] += \
                    producer_decision['producer_abs_share_frac_%s' % mc]

        producer_decision['average_new_vehicle_mfr_cost_%s' % mcat] = \
            producer_decision['average_new_vehicle_mfr_cost_%s' % mcat] / producer_decision['sales_%s' % mcat]

        producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mcat] = \
            (producer_decision['average_new_vehicle_mfr_generalized_cost_dollars_%s' % mcat] /
             producer_decision['sales_%s' % mcat])

        producer_decision['average_cross_subsidized_price_%s' % mcat] = \
            (producer_decision['average_cross_subsidized_price_%s' % mcat] /
             producer_decision['sales_%s' % mcat])


def detect_convergence(producer_decision_and_response, producer_market_classes):
    """
    Detect producer-consumer market share convergence.

    Args:
        producer_decision_and_response (Series): contains producer compliance search result and most-convergent
            consumer response to previous cross subsidy options
        producer_market_classes (list): list of producer market classes

    Returns:
        tuple of convergence bool and convergence error, (converged, share_convergence_error)

    """
    producer_decision_and_response['price_cost_ratio_total'] = \
        (producer_decision_and_response['average_cross_subsidized_price_total'] /
         producer_decision_and_response['average_new_vehicle_mfr_cost'])

    cross_subsidy_pricing_error = abs(1-producer_decision_and_response['price_cost_ratio_total'])
    converged = cross_subsidy_pricing_error <= omega_globals.options.producer_cross_subsidy_price_tolerance

    share_convergence_error = 0
    for mc in producer_market_classes:
        if 'consumer_abs_share_frac_%s' % mc in producer_decision_and_response:
            share_convergence_error = \
                max(share_convergence_error, abs(producer_decision_and_response['producer_abs_share_frac_%s' % mc] -
                                           producer_decision_and_response['consumer_abs_share_frac_%s' % mc]))
            converged = converged and (share_convergence_error <= omega_globals.options.producer_consumer_convergence_tolerance)

    return converged, share_convergence_error, cross_subsidy_pricing_error


def get_module(module_name):
    """
    Get a Python module by module name

    Args:
        module_name (str): e.g. 'consumer.market_classes'

    Returns:
        The module specified by the module name

    """
    import importlib
    import importlib.util

    if module_name in sys.modules:
        module = sys.modules[module_name]
    else:
        module_relpath = str.rsplit(module_name, '.', maxsplit=1)[0].replace('.', os.sep)
        module_suffix = str.split(module_name, '.')[1]
        module_path = omega_globals.options.omega_model_path + os.sep + module_relpath + os.sep + '%s.py' % module_suffix

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

    return module


def init_user_definable_submodules():
    """
    Import dynamic modules that are specified by the input file input template name and set the session runtime
    options appropriately.

    Returns:
        List of template/input errors, else empty list on success

    """
    init_fail = []

    # user-definable context modules
    module_name = get_template_name(omega_globals.options.ice_vehicle_simulation_results_file)
    omega_globals.options.CostCloud = get_module(module_name).CostCloud

    # user-definable policy modules
    # pull in reg classes before building database tables (declaring classes) that check reg class validity
    module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
    omega_globals.options.RegulatoryClasses = get_module(module_name).RegulatoryClasses

    init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
        omega_globals.options.policy_reg_classes_file)

    module_name = get_template_name(omega_globals.options.policy_targets_file)
    omega_globals.options.VehicleTargets = get_module(module_name).VehicleTargets

    module_name = get_template_name(omega_globals.options.offcycle_credits_file)
    omega_globals.options.OffCycleCredits = get_module(module_name).OffCycleCredits

    # user-definable consumer modules
    module_name = get_template_name(omega_globals.options.vehicle_reregistration_file)
    omega_globals.options.Reregistration = get_module(module_name).Reregistration

    module_name = get_template_name(omega_globals.options.onroad_vmt_file)
    omega_globals.options.OnroadVMT = get_module(module_name).OnroadVMT

    module_name = get_template_name(omega_globals.options.sales_share_file)
    omega_globals.options.SalesShare = get_module(module_name).SalesShare

    module_name = get_template_name(omega_globals.options.market_classes_file)
    omega_globals.options.MarketClass = get_module(module_name).MarketClass

    # user-definable producer modules
    module_name = get_template_name(omega_globals.options.producer_generalized_cost_file)
    omega_globals.options.ProducerGeneralizedCost = get_module(module_name).ProducerGeneralizedCost

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

    init_fail = []

    init_fail += omega_globals.options.CostCloud. \
        init_cost_clouds_from_files(omega_globals.options.ice_vehicle_simulation_results_file,
                                    omega_globals.options.bev_vehicle_simulation_results_file,
                                    omega_globals.options.phev_vehicle_simulation_results_file,
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

    from effects.general_inputs_for_effects import GeneralInputsForEffects
    from effects.cost_factors_criteria import CostFactorsCriteria
    from effects.cost_factors_scc import CostFactorsSCC
    from effects.cost_factors_energysecurity import CostFactorsEnergySecurity
    from effects.cost_factors_congestion_noise import CostFactorsCongestionNoise
    from effects.emission_factors_powersector import EmissionFactorsPowersector
    from effects.emission_factors_refinery import EmissionFactorsRefinery
    from effects.emission_factors_vehicles import EmissionFactorsVehicles
    from effects.cpi_price_deflators import CPIPriceDeflators
    from effects.ip_deflators import ImplictPriceDeflators
    from context.maintenance_cost_inputs import MaintenanceCostInputs
    from context.repair_cost_inputs import RepairCostInputs
    from context.refueling_cost_inputs import RefuelingCostInputs

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

        init_fail += FuelPrice.init_from_file(omega_globals.options.context_fuel_prices_file,
                                              verbose=verbose_init)

        init_fail += NewVehicleMarket.init_from_file(omega_globals.options.context_new_vehicle_market_file,
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

        if omega_globals.options.calc_effects == 'Physical and Costs':
            init_fail += GeneralInputsForEffects.init_from_file(omega_globals.options.general_inputs_for_effects_file,
                                                          verbose=verbose_init)

            init_fail += CPIPriceDeflators.init_from_file(omega_globals.options.cpi_deflators_file,
                                                          verbose=verbose_init)

            init_fail += ImplictPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=verbose_init)

            init_fail += EmissionFactorsPowersector.init_from_file(omega_globals.options.emission_factors_powersector_file,
                                                                   verbose=verbose_init)

            init_fail += EmissionFactorsRefinery.init_from_file(omega_globals.options.emission_factors_refinery_file,
                                                                verbose=verbose_init)

            init_fail += EmissionFactorsVehicles.init_from_file(omega_globals.options.emission_factors_vehicles_file,
                                                                verbose=verbose_init)

            init_fail += CostFactorsCriteria.init_from_file(omega_globals.options.criteria_cost_factors_file,
                                                            verbose=verbose_init)

            init_fail += CostFactorsSCC.init_from_file(omega_globals.options.scc_cost_factors_file,
                                                       verbose=verbose_init)

            init_fail += CostFactorsEnergySecurity.init_from_file(omega_globals.options.energysecurity_cost_factors_file,
                                                                  verbose=verbose_init)

            init_fail += CostFactorsCongestionNoise.init_from_file(omega_globals.options.congestion_noise_cost_factors_file,
                                                                   verbose=verbose_init)

            init_fail += MaintenanceCostInputs.init_from_file(omega_globals.options.maintenance_cost_inputs_file,
                                                              verbose=verbose_init)

            init_fail += RepairCostInputs.init_from_file(omega_globals.options.repair_cost_inputs_file,
                                                         verbose=verbose_init)

            init_fail += RefuelingCostInputs.init_from_file(omega_globals.options.refueling_cost_inputs_file,
                                                            verbose=verbose_init)

        if omega_globals.options.calc_effects == 'Physical':
            init_fail += GeneralInputsForEffects.init_from_file(omega_globals.options.general_inputs_for_effects_file,
                                                                verbose=verbose_init)

            init_fail += EmissionFactorsPowersector.init_from_file(omega_globals.options.emission_factors_powersector_file,
                                                                   verbose=verbose_init)

            init_fail += EmissionFactorsRefinery.init_from_file(omega_globals.options.emission_factors_refinery_file,
                                                                verbose=verbose_init)

            init_fail += EmissionFactorsVehicles.init_from_file(omega_globals.options.emission_factors_vehicles_file,
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
    session_runtime_options.standalone_run = standalone_run

    init_fail = None

    try:

        init_fail = init_omega(session_runtime_options)

        if not init_fail:
            omega_log.logwrite("Running %s:" % omega_globals.options.session_unique_name, echo_console=True)

            if omega_globals.options.run_profiler:
                # run with profiler
                omega_log.logwrite('Enabling Profiler...')
                import cProfile, pstats
                profiler = cProfile.Profile()
                profiler.enable()

            iteration_log, credit_banks = run_producer_consumer()

            if omega_globals.options.run_profiler:
                profiler.disable()
                stats = pstats.Stats(profiler)
                omega_log.logwrite('Generating Profiler Dump...')
                stats.dump_stats('omega_profile.dmp')

            postproc_session.run_postproc(iteration_log, credit_banks)

            from context.new_vehicle_market import NewVehicleMarket

            if omega_globals.options.session_is_reference and \
                    omega_globals.options.generate_context_new_vehicle_generalized_costs_file:
                NewVehicleMarket.save_context_new_vehicle_generalized_costs(
                    omega_globals.options.context_new_vehicle_generalized_costs_file)

            NewVehicleMarket.save_session_new_vehicle_generalized_costs(
                omega_globals.options.output_folder + omega_globals.options.session_unique_name +
                '_new_vehicle_prices.csv')

            omega_log.end_logfile("\nSession Complete")

            if 'database' in omega_globals.options.verbose_log_modules:
                dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

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
