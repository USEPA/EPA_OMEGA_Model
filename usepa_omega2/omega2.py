"""
omega2.py
=========

OMEGA2 top level code

"""
from usepa_omega2 import omega_log

print('importing %s' % __file__)


import o2  # import global variables
from usepa_omega2 import *
from omega_plot import *
import os
from usepa_omega2.consumer import stock


def run_postproc(iteration_log: pd.DataFrame, single_shot: bool):
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from market_classes import MarketClass
    from effects.o2_effects import run_effects_calcs
    import pandas as pd

    import matplotlib.pyplot as plt

    if o2.options.calc_effects:
        run_effects_calcs()

    if not single_shot:
        omega_log.logwrite('%s: Post Processing ...' % o2.options.session_name)

    year_iter_labels = ['%d_%d_%d' % (cy - 2000, it, it_sub) for cy, it, it_sub in
                        zip(iteration_log['calendar_year'][iteration_log['pricing_iteration'] == -1], iteration_log['iteration'][iteration_log['pricing_iteration'] == -1], iteration_log['pricing_iteration'][iteration_log['pricing_iteration'] == -1])]
    for mc in MarketClass.get_market_class_dict():
        plt.figure()
        plt.plot(year_iter_labels, iteration_log['producer_share_frac_%s' % mc][iteration_log['pricing_iteration'] == -1])
        plt.plot(year_iter_labels, iteration_log['consumer_share_frac_%s' % mc][iteration_log['pricing_iteration'] == -1])
        plt.title('%s iteration' % mc)
        plt.grid()
        plt.legend(['producer_share_frac_%s' % mc, 'consumer_share_frac_%s' % mc])
        plt.ylim([0,1])
        plt.savefig('%s%s Iteration %s.png' % (o2.options.output_folder, o2.options.session_unique_name, mc))

    fig, ax1 = fplothg(year_iter_labels, iteration_log['iteration'][iteration_log['pricing_iteration'] == -1])
    label_xyt(ax1, '', 'iteration', 'iteration mean = %.2f' % (2.0 * iteration_log['iteration'][iteration_log['pricing_iteration'] == -1].mean()))
    fig.savefig('%s%s Iteration Counts.png' % (o2.options.output_folder, o2.options.session_unique_name))

    calendar_years = ManufacturerAnnualData.get_calendar_years()
    cert_target_co2_Mg = ManufacturerAnnualData.get_cert_target_co2_Mg()
    cert_co2_Mg = ManufacturerAnnualData.get_cert_co2_Mg()
    total_cost_billions = ManufacturerAnnualData.get_total_cost_billions()

    # compliance chart
    fig, ax1 = fplothg(calendar_years, cert_target_co2_Mg, '.-')
    ax1.plot(calendar_years, cert_co2_Mg, '.-')
    ax1.legend(['cert_target_co2_Mg', 'cert_co2_Mg'])
    label_xyt(ax1, 'Year', 'CO2 Mg', '%s\nCompliance Versus Calendar Year\n Total Cost $%.2f Billion' % (
        o2.options.session_unique_name, total_cost_billions))
    fig.savefig(o2.options.output_folder + '%s Compliance v Year' % o2.options.session_unique_name)

    import numpy as np
    import consumer
    total_sales = []
    for cy in calendar_years:
        total_sales.append(float(o2.session.query(func.sum(VehicleAnnualData.registered_count))
                           .filter(VehicleAnnualData.calendar_year == cy)
                           .filter(VehicleAnnualData.age == 0).scalar()))
    total_sales = np.array(total_sales)
    context_sales = np.array([consumer.sales_volume.context_new_vehicle_sales(cy)['total'] for cy in calendar_years])
    fig, ax1 = fplothg(calendar_years, context_sales / 1e6, '.-')
    ax1.plot(calendar_years, total_sales / 1e6)
    ax1.legend(['context sales', 'sales'])
    label_xyt(ax1, 'Year', 'Sales [millions]', '%s\nTotal Sales Versus Calendar Year\n Total Sales %.2f Million' % (
        o2.options.session_unique_name, total_sales.sum() / 1e6))
    fig.savefig(o2.options.output_folder + '%s Total Sales v Year' % o2.options.session_unique_name)

    bev_non_hauling_share_frac = np.array(sql_unpack_result(
        o2.session.query(ManufacturerAnnualData.bev_non_hauling_share_frac).all()))
    ice_non_hauling_share_frac = np.array(sql_unpack_result(
        o2.session.query(ManufacturerAnnualData.ice_non_hauling_share_frac).all()))
    bev_hauling_share_frac = np.array(sql_unpack_result(o2.session.query(ManufacturerAnnualData.bev_hauling_share_frac).all()))
    ice_hauling_share_frac = np.array(sql_unpack_result(o2.session.query(ManufacturerAnnualData.ice_hauling_share_frac).all()))
    hauling_share_frac = bev_hauling_share_frac + ice_hauling_share_frac
    non_hauling_share_frac = bev_non_hauling_share_frac + ice_non_hauling_share_frac

    fig, ax1 = fplothg(calendar_years, bev_non_hauling_share_frac, '.--')
    ax1.plot(calendar_years, ice_non_hauling_share_frac, '.-')
    ax1.plot(calendar_years, bev_hauling_share_frac, '.--')
    ax1.plot(calendar_years, ice_hauling_share_frac, '.-')
    ax1.plot(calendar_years, hauling_share_frac, '.-')
    ax1.plot(calendar_years, non_hauling_share_frac, '.-')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Market Share Frac', '%s\nMarket Shares' % o2.options.session_unique_name)
    ax1.legend(['bev_non_hauling', 'ice_non_hauling', 'bev_hauling', 'ice_hauling', 'hauling', 'non_hauling'])
    fig.savefig(o2.options.output_folder + '%s Market Shares' % o2.options.session_unique_name)

    # cost/vehicle chart
    fig, ax1 = figure()
    average_cost_data = dict()
    for hc in hauling_classes:
        average_cost_data[hc] = []
        for cy in calendar_years:
            average_cost_data[hc].append(o2.session.query(
                func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.hauling_class == hc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_years, average_cost_data[hc])

    for mc in MarketClass.market_classes:
        average_cost_data[mc] = []
        for cy in calendar_years:
            average_cost_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cost_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cost_data[mc], '.--')

    average_cost_data['total'] = []
    for cy in calendar_years:
        average_cost_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())
    ax1.plot(calendar_years, average_cost_data['total'])

    label_xyt(ax1, 'Year', 'Average Vehicle Cost [$]', '%s\nAverage Vehicle Cost v Year' % o2.options.session_unique_name)
    ax1.set_ylim(15e3, 60e3)
    ax1.legend(average_cost_data.keys())
    fig.savefig(o2.options.output_folder + '%s Average Vehicle Cost' % o2.options.session_unique_name)

    # g/mi chart
    fig, ax1 = figure()
    average_co2_gpmi_data = dict()
    for hc in hauling_classes:
        average_co2_gpmi_data[hc] = []
        for cy in calendar_years:
            average_co2_gpmi_data[hc].append(o2.session.query(
                func.sum(VehicleFinal.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                             filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                             filter(VehicleFinal.model_year == cy).
                                             filter(VehicleFinal.hauling_class == hc).
                                             filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_years, average_co2_gpmi_data[hc])

    for mc in MarketClass.market_classes:
        average_co2_gpmi_data[mc] = []
        for cy in calendar_years:
            average_co2_gpmi_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                             filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                             filter(VehicleFinal.model_year == cy).
                                             filter(VehicleFinal.market_class_ID == mc).
                                             filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_co2_gpmi_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_co2_gpmi_data[mc], '.--')

    average_co2_gpmi_data['total'] = []
    for cy in calendar_years:
        average_co2_gpmi_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                              filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                              filter(VehicleFinal.model_year == cy).
                                              filter(VehicleAnnualData.age == 0).scalar())
    ax1.plot(calendar_years, average_co2_gpmi_data['total'])

    label_xyt(ax1, 'Year', 'Average Vehicle Cert CO2 [g/mi]',
              '%s\nAverage Vehicle Cert CO2 g/mi v Year' % o2.options.session_unique_name)
    ax1.set_ylim(0, 500)
    ax1.legend(average_co2_gpmi_data.keys())
    fig.savefig(o2.options.output_folder + '%s Average Vehicle Cert CO2 gpmi' % o2.options.session_unique_name)

    session_results = pd.DataFrame()
    session_results['calendar_year'] = calendar_years
    session_results['session_name'] = o2.options.session_name
    session_results['cert_target_co2_Mg'] = cert_target_co2_Mg
    session_results['cert_co2_Mg'] = cert_co2_Mg
    session_results['total_cost_billions'] = total_cost_billions

    session_results['bev_non_hauling_share_frac'] = bev_non_hauling_share_frac
    session_results['ice_non_hauling_share_frac'] = ice_non_hauling_share_frac
    session_results['bev_hauling_share_frac'] = bev_hauling_share_frac
    session_results['ice_hauling_share_frac'] = ice_hauling_share_frac

    for hc in hauling_classes:
        session_results['average_%s_cost' % hc] = average_cost_data[hc]
        session_results['average_%s_co2_gpmi' % hc] = average_co2_gpmi_data[hc]
    session_results['average_vehicle_cost'] = average_cost_data['total']
    session_results['average_vehicle_co2_gpmi'] = average_co2_gpmi_data['total']

    for mc in MarketClass.market_classes:
        session_results['average_co2_gpmi_%s' % mc] = average_co2_gpmi_data[mc]
        session_results['average_cost_%s' % mc] = average_cost_data[mc]

    return session_results


def run_producer_consumer():
    """
    Create producer cost-minimizing technology and market share options, in consideration of market response from
    the consumer module, possibly with iteration between the two

    :return: iteration log dataframe, updated omega database with final vehicle technology and market share data
    """

    from manufacturers import Manufacturer
    import producer

    for manufacturer in o2.session.query(Manufacturer.manufacturer_ID).all():
        manufacturer_ID = manufacturer[0]
        omega_log.logwrite("Running: Manufacturer=" + str(manufacturer_ID), echo_console=True)

        iteration_log = pd.DataFrame()

        if o2.options.num_analysis_years is None:
            analysis_end_year = o2.options.analysis_final_year + 1
        else:
            analysis_end_year = o2.options.analysis_initial_year + o2.options.num_analysis_years

        for calendar_year in range(o2.options.analysis_initial_year, analysis_end_year):

            producer_decision_and_response = None
            prev_producer_decision_and_response = None
            prev_candidate_mfr_composite_vehicles = None
            best_winning_combo_with_sales_response = None

            iteration_num = 0
            iterate = True

            while iterate:
                omega_log.logwrite("Running: Year=" + str(calendar_year) + "  Iteration=" + str(iteration_num),
                                   echo_console=True)

                candidate_mfr_composite_vehicles, winning_combo, market_class_tree, producer_compliant = \
                    producer.run_compliance_model(manufacturer_ID, calendar_year, producer_decision_and_response,
                                                  iteration_num)

                if producer_compliant or True:
                    market_class_vehicle_dict = calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles,
                                                                       winning_combo)

                    best_winning_combo_with_sales_response, iteration_log, producer_decision_and_response = \
                        iterate_producer_consumer_pricing(calendar_year, best_winning_combo_with_sales_response,
                                                          candidate_mfr_composite_vehicles, iteration_log,
                                                          iteration_num, market_class_vehicle_dict, winning_combo)

                    producer_consumer_iteration = -1  # flag end of pricing subiteration

                    converged, convergence_error = \
                        detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

                    iteration_log = iteration_log.append(producer_decision_and_response, ignore_index=True)
                    update_iteration_log(calendar_year, converged, iteration_log, iteration_num,
                                         producer_consumer_iteration, producer_compliant, convergence_error)

                    prev_producer_decision_and_response = producer_decision_and_response
                    prev_candidate_mfr_composite_vehicles = candidate_mfr_composite_vehicles
                else:
                    # roll back to prior iteration result, can't comply based on consumer response
                    producer_decision_and_response = prev_producer_decision_and_response
                    candidate_mfr_composite_vehicles = prev_candidate_mfr_composite_vehicles

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

            producer.finalize_production(calendar_year, manufacturer_ID, candidate_mfr_composite_vehicles,
                                         producer_decision_and_response)

            stock.update_stock(calendar_year)  # takes about 7.5 seconds

        iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder, index=False)

    return iteration_log


def iterate_producer_consumer_pricing(calendar_year, best_producer_decision_and_response, candidate_mfr_composite_vehicles,
                                      iteration_log, iteration_num, market_class_vehicle_dict,
                                      producer_decision):

    from market_classes import MarketClass
    import producer
    import consumer
    from consumer.sales_share_gcam import get_demanded_shares

    producer_decision['winning_combo_share_weighted_cost'] = 0
    for mc in market_class_vehicle_dict:
        producer_decision['winning_combo_share_weighted_cost'] = producer_decision['winning_combo_share_weighted_cost'] + \
                                                                 producer_decision['average_cost_%s' % mc] * \
                                                                 producer_decision['producer_abs_market_share_frac_%s' % mc]

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

        continue_search, price_options_df = calculate_price_options(continue_search, multiplier_columns,
                                                                    prev_multiplier_range, price_options_df,
                                                                    producer_decision_and_response)

        producer_decision_and_response = get_demanded_shares(price_options_df, calendar_year)

        calculate_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response)

        # propagate total sales down to composite vehicles by market class share and reg class share,
        # calculate new compliance status for each producer-technology / consumer response combination
        producer.calculate_tech_share_combos_total(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response,
                                                   total_sales=producer_decision_and_response['new_vehicle_sales'])

        # propagate vehicle sales up to market class sales
        calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, producer_decision_and_response)

        producer_decision_and_response['sales_ratio'] = \
            producer_decision_and_response['new_vehicle_sales'] / unsubsidized_sales

        producer_decision_and_response['compliance_ratio'] = \
            producer_decision_and_response['total_combo_cert_co2_megagrams'] / \
            producer_decision_and_response['total_combo_target_co2_megagrams']

        # calculate distance to origin (minimal price and market share error):
        score_sum_of_squares = producer_decision_and_response['share_weighted_share_delta']**2
        for hc in hauling_classes:
            score_sum_of_squares += abs(1 - producer_decision_and_response['average_price_%s' % hc] /
                                        producer_decision_and_response['average_cost_%s' % hc])**2
        producer_decision_and_response['pricing_score'] = score_sum_of_squares**0.5

        if o2.options.log_producer_decision_and_response_years == 'all' or \
                calendar_year in o2.options.log_producer_decision_and_response_years:
            producer_decision_and_response.to_csv('%sproducer_decision_and_response_%s_%s_%s.csv' %
                                (o2.options.output_folder, calendar_year, iteration_num, producer_pricing_iteration))

        producer_decision_and_response = \
            producer_decision_and_response.loc[producer_decision_and_response['pricing_score'].idxmin()]

        producer_decision_and_response['price_cost_ratio_total'] = \
            producer_decision_and_response['average_price_total'] / producer_decision_and_response['average_cost_total']

        converged, convergence_error = detect_convergence(producer_decision_and_response, market_class_vehicle_dict)

        if (best_producer_decision_and_response is None) or (producer_decision_and_response['pricing_score'] < best_producer_decision_and_response['pricing_score']):
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

    if o2.options.log_consumer_iteration_years is 'all' or calendar_year in o2.options.log_consumer_iteration_years:
        iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder, index=False)

    return best_producer_decision_and_response, iteration_log, producer_decision_and_response


def calculate_sales_totals(calendar_year, market_class_vehicle_dict, producer_decision_and_response):
    import consumer

    producer_decision_and_response['share_weighted_share_delta'] = 0
    producer_decision_and_response['average_price_total'] = 0
    producer_decision_and_response['average_cost_total'] = 0
    for mc in market_class_vehicle_dict:
        producer_decision_and_response['share_weighted_share_delta'] += abs(
            producer_decision_and_response['producer_share_frac_%s' % mc] -
            producer_decision_and_response['consumer_share_frac_%s' % mc]) \
                                                                        * producer_decision_and_response[
                                                                            'consumer_abs_share_frac_%s' % mc]

        producer_decision_and_response['average_price_total'] += producer_decision_and_response[
                                                                     'average_price_%s' % mc] * \
                                                                 producer_decision_and_response[
                                                                     'consumer_abs_share_frac_%s' % mc]

        producer_decision_and_response['average_cost_total'] += producer_decision_and_response['average_cost_%s' % mc] * \
                                                                producer_decision_and_response[
                                                                    'consumer_abs_share_frac_%s' % mc]
    # calculate new total sales demand based on total share weighted price
    producer_decision_and_response['new_vehicle_sales'] = \
        consumer.sales_volume.new_vehicle_sales_response(calendar_year,
                                                         producer_decision_and_response['average_price_total'])


def calculate_price_options(continue_search, multiplier_columns, prev_multiplier_range, price_options_df,
                            producer_decision_and_response):

    import numpy as np
    from market_classes import MarketClass

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
        price_options_df['average_price_%s' % mc] = price_options_df['average_cost_%s' % mc] * price_options_df[mcc]
        prev_multiplier_range[mcc] = multiplier_range

    if not producer_decision_and_response.empty and search_collapsed:
        continue_search = False
        if 'consumer' in o2.options.verbose_console:
            omega_log.logwrite('SEARCH COLLAPSED')

    return continue_search, price_options_df


def tighten_multiplier_range(mcc, prev_multiplier_range, producer_decision_and_response,
                             search_collapsed):

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


def logwrite_shares_and_costs(calendar_year, convergence_error, producer_decision_and_response, iteration_num, producer_pricing_iteration):
    from market_classes import MarketClass

    for mc in MarketClass.market_classes:
        omega_log.logwrite(('%d producer/consumer_share_frac_%s' % (calendar_year, mc)).ljust(50) +
                           '= %.4f / %.4f (DELTA:%f, CE:%f)' % (
                               producer_decision_and_response['producer_share_frac_%s' % mc],
                               producer_decision_and_response['consumer_share_frac_%s' % mc],
                               abs(producer_decision_and_response['producer_share_frac_%s' % mc] - producer_decision_and_response[
                                   'consumer_share_frac_%s' % mc]),
                               abs(1 - producer_decision_and_response['producer_share_frac_%s' % mc] / producer_decision_and_response[
                                   'consumer_share_frac_%s' % mc])
                           ), echo_console=True)
    omega_log.logwrite('convergence_error = %f' % convergence_error, echo_console=True)
    for hc in hauling_classes:
        omega_log.logwrite(
            ('price / cost %s' % hc).ljust(50) + '$%d / $%d R:%f' % (producer_decision_and_response['average_price_%s' % hc],
                                                                     producer_decision_and_response['average_cost_%s' % hc],
                                                                     producer_decision_and_response['average_price_%s' % hc] /
                                                                     producer_decision_and_response['average_cost_%s' % hc]
                                                                     ), echo_console=True)
    omega_log.logwrite('price / cost TOTAL'.ljust(50) + '$%d / $%d R:%f' % (producer_decision_and_response['average_price_total'],
                                                                            producer_decision_and_response['average_cost_total'],
                                                                            producer_decision_and_response['average_price_total'] /
                                                                            producer_decision_and_response['average_cost_total']
                                                                            ), echo_console=True)
    omega_log.logwrite(
        '%d_%d_%d  SCORE:%f  SWSD:%f  SR:%f' % (calendar_year, iteration_num, producer_pricing_iteration,
                                                           producer_decision_and_response['pricing_score'],
                                                           producer_decision_and_response['share_weighted_share_delta'],
                                                           producer_decision_and_response['sales_ratio']), echo_console=True)


def update_iteration_log(calendar_year, converged, iteration_log, iteration_num, producer_pricing_iteration,
                         compliant, convergence_error):
    iteration_log.loc[iteration_log.index[-1], 'iteration'] = iteration_num
    iteration_log.loc[iteration_log.index[-1], 'pricing_iteration'] = producer_pricing_iteration
    iteration_log.loc[iteration_log.index[-1], 'calendar_year'] = calendar_year
    iteration_log.loc[iteration_log.index[-1], 'converged'] = converged
    iteration_log.loc[iteration_log.index[-1], 'compliant'] = compliant
    iteration_log.loc[iteration_log.index[-1], 'convergence_error'] = convergence_error
    if o2.options.log_consumer_iteration_years is 'all' or calendar_year in o2.options.log_consumer_iteration_years:
        iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder, index=False)


def calc_market_class_data(calendar_year, candidate_mfr_composite_vehicles, winning_combo):
    """

    :param candidate_mfr_composite_vehicles: list of candidate composite vehicles that minimize producer compliance cost
    :param winning_combo: pandas Series that corresponds with candidate_mfr_composite_vehicles, has market shares, costs,
            compliance data (Mg CO2)
    :return: dictionary of candidate vehicles binned by market class and reg class, updates producer_decision with
            sales-weighted average cost and CO2 g/mi by market class
    """

    from market_classes import MarketClass
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

            winning_combo['average_cost_%s' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'new_vehicle_mfr_cost_dollars')

            winning_combo['average_fuel_price_%s' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'retail_fuel_price')

            winning_combo['sales_%s' % mc] = 0
            for v in market_class_vehicles:
                winning_combo['sales_%s' % mc] += winning_combo['veh_%s_sales' % v.vehicle_ID]  # was v.initial_registered_count
        else:
            winning_combo['average_co2_gpmi_%s' % mc] = 0
            winning_combo['average_cost_%s' % mc] = 0
            winning_combo['sales_%s' % mc] = 0

        winning_combo['producer_abs_market_share_frac_%s' % mc] = winning_combo['sales_%s' % mc] / winning_combo['total_sales']

    calculate_hauling_class_data(winning_combo)

    return market_class_vehicle_dict


def calculate_hauling_class_data(winning_combo):
    from market_classes import MarketClass

    for hc in hauling_classes:
        winning_combo['average_cost_%s' % hc] = 0
        winning_combo['average_price_%s' % hc] = 0
        winning_combo['sales_%s' % hc] = 0

        for mc in MarketClass.market_classes:
            if mc.startswith(hc):
                winning_combo['average_cost_%s' % hc] += winning_combo['average_cost_%s' % mc] * winning_combo['sales_%s' % mc]
                if 'average_price_%s' % mc in winning_combo:
                    winning_combo['average_price_%s' % hc] += winning_combo['average_price_%s' % mc] * winning_combo['sales_%s' % mc]
                winning_combo['sales_%s' % hc] += winning_combo['sales_%s' % mc]

        winning_combo['average_cost_%s' % hc] = winning_combo['average_cost_%s' % hc] / winning_combo['sales_%s' % hc]
        winning_combo['average_price_%s' % hc] = winning_combo['average_price_%s' % hc] / winning_combo['sales_%s' % hc]


def detect_convergence(producer_decision_and_response, market_class_dict):
    converged = abs(1 - producer_decision_and_response['price_cost_ratio_total']) <= 1e-4
    convergence_error = 0
    for mc in market_class_dict:
        # relative percentage convergence on largest market shares:
        if producer_decision_and_response['producer_share_frac_%s' % mc] >= 0.5:
            convergence_error = \
                max(convergence_error, abs(1 - producer_decision_and_response['producer_share_frac_%s' % mc] / \
                                        producer_decision_and_response['consumer_share_frac_%s' % mc]))
            converged = converged and (convergence_error <= o2.options.producer_consumer_iteration_tolerance)

    return converged, convergence_error


def init_omega(o2_options):
    from omega_log import OMEGALog

    # set up global variables:
    o2.options = o2_options

    omega_log.init_logfile()

    init_omega_db()
    o2.engine.echo = o2.options.verbose

    init_fail = []

    # import database modules to populate ORM context
    from fuels import Fuel
    from context_fuel_prices import ContextFuelPrices
    from context_new_vehicle_market import ContextNewVehicleMarket
    from context_fuel_upstream import ContextFuelUpstream
    from market_classes import MarketClass
    from cost_curves import CostCurve, input_template_name as cost_curve_template_name
    from cost_clouds import CostCloud
    from demanded_shares_gcam import DemandedSharesGCAM
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

    # instantiate database tables
    SQABase.metadata.create_all(o2.engine)

    import consumer.sales_volume as consumer
    import producer

    fileio.validate_folder(o2.options.output_folder)

    o2.options.producer_calculate_generalized_cost = producer.calculate_generalized_cost
    o2.options.consumer_calculate_generalized_cost = consumer.calculate_generalized_cost

    try:
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)

        init_fail = init_fail + ContextFuelPrices.init_database_from_file(
            o2.options.context_fuel_prices_file, verbose=o2.options.verbose)

        init_fail = init_fail + ContextFuelUpstream.init_database_from_file(o2.options.context_fuel_upstream_file,
                                                                          verbose=o2.options.verbose)

        init_fail = init_fail + ContextNewVehicleMarket.init_database_from_file(
            o2.options.context_new_vehicle_market_file, verbose=o2.options.verbose)

        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)

        if get_template_name(o2.options.cost_file) == cost_curve_template_name:
            init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        else:
            init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        init_fail = init_fail + o2.options.GHG_standard.init_database_from_file(o2.options.ghg_standards_file,
                                                                                verbose=o2.options.verbose)

        init_fail = init_fail + GHGStandardFuels.init_database_from_file(o2.options.ghg_standards_fuels_file,
                                                                         verbose=o2.options.verbose)
        init_fail = init_fail + DemandedSharesGCAM.init_database_from_file(
            o2.options.demanded_shares_file, verbose=o2.options.verbose)

        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + VehicleFinal.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

        init_fail = init_fail + ReregistrationFixedByAge.init_database_from_file(
            o2.options.reregistration_fixed_by_age_file, verbose=o2.options.verbose)
        o2.options.stock_scrappage = ReregistrationFixedByAge

        init_fail = init_fail + AnnualVMTFixedByAge.init_database_from_file(o2.options.annual_vmt_fixed_by_age_file,
                                                                            verbose=o2.options.verbose)
        o2.options.stock_vmt = AnnualVMTFixedByAge

        init_fail = init_fail + CostFactorsCriteria.init_database_from_file(o2.options.criteria_cost_factors_file,
                                                                            verbose=o2.options.verbose)
        init_fail = init_fail + CostFactorsSCC.init_database_from_file(o2.options.scc_cost_factors_file,
                                                                       verbose=o2.options.verbose)
        init_fail = init_fail + CostFactorsEnergySecurity.init_database_from_file(o2.options.energysecurity_cost_factors_file,
                                                                                  verbose=o2.options.verbose)
        init_fail = init_fail + CostFactorsCongestionNoise.init_database_from_file(o2.options.congestion_noise_cost_factors_file,
                                                                                   verbose=o2.options.verbose)
        init_fail = init_fail + EmissionFactorsPowersector.init_database_from_file(o2.options.emission_factors_powersector_file,
                                                                                   verbose=o2.options.verbose)
        init_fail = init_fail + EmissionFactorsRefinery.init_database_from_file(o2.options.emission_factors_refinery_file,
                                                                                verbose=o2.options.verbose)
        init_fail = init_fail + EmissionFactorsVehicles.init_database_from_file(o2.options.emission_factors_vehicles_file,
                                                                                verbose=o2.options.verbose)

        # initial year = initial fleet model year (latest year of data)
        o2.options.analysis_initial_year = int(o2.session.query(func.max(VehicleFinal.model_year)).scalar()) + 1
        # final year = last year of cost curve data
        o2.options.analysis_final_year = int(o2.session.query(func.max(CostCurve.model_year)).scalar())
        # o2.options.analysis_final_year = 2022

        stock.update_stock(o2.options.analysis_initial_year - 1)  # update vehicle annual data for base year fleet
    finally:
        return init_fail


def run_omega(o2_options, single_shot=False):
    import traceback
    import time

    o2_options.start_time = time.time()

    print('OMEGA2 greets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    print('run_omega(%s)' % o2_options.session_name)

    try:
        init_fail = init_omega(o2_options)

        omega_log.logwrite("Running: OMEGA 2 Version " + str(code_version))

        if not init_fail:
            if o2.options.run_profiler:
                # run with profiler
                import cProfile
                import re
                cProfile.run('iteration_log = run_producer_consumer()', filename='omega2_profile.dmp')
                session_summary_results = run_postproc(globals()['iteration_log'], single_shot)  # return values of cProfile.run() show up in the globals namespace
            else:
                # run without profiler
                iteration_log = run_producer_consumer()
                session_summary_results = run_postproc(iteration_log, single_shot)

            publish_summary_results(session_summary_results, single_shot)

            dump_omega_db_to_csv(o2.options.database_dump_folder)

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


def publish_summary_results(session_summary_results, single_shot):
    if single_shot:
        session_summary_results.to_csv(o2.options.output_folder + 'summary_results.csv', mode='w')
    else:
        if not os.access('%s_summary_results.csv' % fileio.get_filename(os.getcwd()), os.F_OK):
            session_summary_results.to_csv(
                '%s_summary_results.csv' % fileio.get_filename(os.getcwd()), mode='w')
        else:
            session_summary_results.to_csv(
                '%s_summary_results.csv ' % fileio.get_filename(os.getcwd()), mode='a', header=False)


if __name__ == "__main__":
    try:
        import producer
        run_omega(OMEGARuntimeOptions(), single_shot=True)  # to view in terminal: snakeviz omega2_profile.dmp
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
