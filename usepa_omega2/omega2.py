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


def run_postproc(iteration_log, single_shot):
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from market_classes import MarketClass
    import pandas as pd

    import matplotlib.pyplot as plt

    if not single_shot:
        omega_log.logwrite('%s: Post Processing ...' % o2.options.session_name)

    year_iter_labels = ['%d_%d' % (cy - 2000, it) for cy, it in
                        zip(iteration_log['calendar_year'], iteration_log['iteration'])]
    for mc in MarketClass.get_market_class_dict():
        plt.figure()
        plt.plot(year_iter_labels, iteration_log['producer_%s_share_frac' % mc])
        plt.plot(year_iter_labels, iteration_log['consumer_%s_share_frac' % mc])
        plt.title('%s iteration' % mc)
        plt.grid()
        plt.legend(['producer_%s_share_frac' % mc, 'consumer_%s_share_frac' % mc])
        plt.ylim([0,1])
        plt.savefig('%s%s Iteration %s.png' % (o2.options.output_folder, o2.options.session_unique_name, mc))

    fig, ax1 = fplothg(year_iter_labels, iteration_log['iteration'])
    label_xyt(ax1, '', 'iteration', 'iteration mean = %.2f' % (2.0 * iteration_log['iteration'].mean()))
    fig.savefig('%s%s Iteration Counts.png' % (o2.options.output_folder, o2.options.session_unique_name))

    calendar_years = sql_unpack_result(o2.session.query(ManufacturerAnnualData.calendar_year).all())
    cert_target_co2_Mg = sql_unpack_result(o2.session.query(ManufacturerAnnualData.cert_target_co2_Mg).all())
    cert_co2_Mg = sql_unpack_result(o2.session.query(ManufacturerAnnualData.cert_co2_Mg).all())
    total_cost_billions = float(
        o2.session.query(func.sum(ManufacturerAnnualData.manufacturer_vehicle_cost_dollars)).scalar()) / 1e9

    # compliance chart
    fig, ax1 = fplothg(calendar_years, cert_target_co2_Mg, '.-')
    ax1.plot(calendar_years, cert_co2_Mg, '.-')
    ax1.legend(['cert_target_co2_Mg', 'cert_co2_Mg'])
    label_xyt(ax1, 'Year', 'CO2 Mg', '%s\nCompliance Versus Calendar Year\n Total Cost $%.2f Billion' % (
        o2.options.session_unique_name, total_cost_billions))
    fig.savefig(o2.options.output_folder + '%s Compliance v Year' % o2.options.session_unique_name)

    import numpy as np
    total_sales = []
    for cy in calendar_years:
        total_sales.append(float(o2.session.query(func.sum(VehicleAnnualData.registered_count))
                           .filter(VehicleAnnualData.calendar_year == cy)
                           .filter(VehicleAnnualData.age == 0).scalar()))
    total_sales = np.array(total_sales)
    fig, ax1 = fplothg(calendar_years, total_sales / 1e6, '.-')
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

    fig, ax1 = fplothg(calendar_years, bev_non_hauling_share_frac, '.-')
    ax1.plot(calendar_years, ice_non_hauling_share_frac, '.-')
    ax1.plot(calendar_years, bev_hauling_share_frac, '.-')
    ax1.plot(calendar_years, ice_hauling_share_frac, '.-')
    ax1.plot(calendar_years, hauling_share_frac, '.-')
    ax1.plot(calendar_years, non_hauling_share_frac, '.-')
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
        ax1.plot(calendar_years, average_cost_data[mc])

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
        ax1.plot(calendar_years, average_co2_gpmi_data[mc])

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
        session_results['average_%s_co2_gpmi' % mc] = average_co2_gpmi_data[mc]
        session_results['average_%s_cost' % mc] = average_cost_data[mc]

    return session_results


def run_producer_consumer():
    """
    Create producer cost-minimizing technology and market share options, in consideration of market response from
    the consumer module, possibly with iteration between the two

    :return: iteration log dataframe, updated omega database with final vehicle technology and market share data
    """

    from manufacturers import Manufacturer
    import producer
    import consumer
    from consumer.sales_share_gcam import get_demanded_shares

    for manufacturer in o2.session.query(Manufacturer.manufacturer_ID).all():
        manufacturer_ID = manufacturer[0]
        print(manufacturer_ID)
        omega_log.logwrite("Running: Manufacturer=" + str(manufacturer_ID))

        iteration_log = pd.DataFrame()
        for calendar_year in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
            consumer_market_share_demand = None
            iteration_num = 0
            iterate = True
            prev_winning_combo = None
            prev_candidate_mfr_new_vehicles = None
            while iterate:
                print('%d_%d' % (calendar_year, iteration_num))
                omega_log.logwrite("Running: Year=" + str(calendar_year) + "  Iteration=" + str(iteration_num))
                candidate_mfr_new_vehicles, winning_combo, market_class_tree = producer.run_compliance_model(manufacturer_ID, calendar_year, consumer_market_share_demand)

                compliant = winning_combo['total_combo_credits_co2_megagrams'] >= 0

                if compliant:

                    market_class_vehicle_dict = calc_market_class_data(calendar_year, candidate_mfr_new_vehicles,
                                                                       winning_combo)

                    # experiment ----------------------- #
                    if calendar_year == 2037:
                        import numpy as np
                        from market_classes import MarketClass
                        from omega_functions import cartesian_prod

                        initial_total_sales = winning_combo['total_sales']
                        winning_combo['winning_combo_share_weighted_price'] = \
                            winning_combo['total_combo_cost_dollars'] / winning_combo['total_sales']

                        multiplier_columns = ['%s_cost_multiplier' % mc for mc in MarketClass.market_classes]

                        multiplier_df = winning_combo.to_frame().transpose()
                        for mc, mcc in zip(MarketClass.market_classes, multiplier_columns):
                            inc = 0.05
                            multiplier_df = cartesian_prod(multiplier_df,
                                                           pd.DataFrame(np.arange(inc, 2.0 + inc, inc), columns=[mcc]))
                            multiplier_df['initial_average_%s_cost' % mc] = multiplier_df['average_%s_cost' % mc]
                            multiplier_df['average_%s_cost' % mc] = multiplier_df['average_%s_cost' % mc] * \
                                                                    multiplier_df[mcc]

                        multiplier_df['initial_revenue'] = 0
                        for mc in market_class_vehicle_dict:
                            multiplier_df['initial_revenue'] = multiplier_df['initial_revenue'] + multiplier_df['%s_sales' % mc] * multiplier_df['initial_average_%s_cost' % mc]

                        sales_demand = get_demanded_shares(multiplier_df, calendar_year)

                        sales_demand['share_weighted_share_delta'] = 0
                        sales_demand['share_weighted_price'] = 0
                        sales_demand['revenue'] = 0
                        for mc in market_class_vehicle_dict:
                            sales_demand['share_weighted_share_delta'] = sales_demand['share_weighted_share_delta'] + \
                                                                         abs(sales_demand['producer_%s_share_frac' % mc] - sales_demand['consumer_%s_share_frac' % mc]) \
                                                                         * sales_demand['consumer_%s_abs_share_frac' % mc]

                            sales_demand['share_weighted_price'] = sales_demand['share_weighted_price'] + \
                                                                   sales_demand['average_%s_cost' % mc] * \
                                                                   sales_demand['consumer_%s_abs_share_frac' % mc]

                        # calculate new total sales demand based on total share weighted price
                        sales_demand['new_vehicle_sales'] = \
                            consumer.sales_volume.new_vehicle_sales_response(calendar_year, sales_demand['share_weighted_price'])

                        # propagate total sales down to composite vehicles by market class share and reg class share,
                        # calculate new compliance status for each producer-technology / consumer response combination
                        producer.calculate_tech_share_combos_total(calendar_year, candidate_mfr_new_vehicles, sales_demand, total_sales=sales_demand['new_vehicle_sales'])

                        sales_demand['revenue'] = sales_demand['share_weighted_price'] * \
                                                  sales_demand['new_vehicle_sales']

                        sales_demand['delta_revenue'] = sales_demand['revenue'] - sales_demand['initial_revenue']
                        sales_demand['profit'] = sales_demand['revenue'] - sales_demand['total_combo_cost_dollars']
                        sales_demand['sales_ratio'] = sales_demand['new_vehicle_sales'] / initial_total_sales
                        sales_demand['revenue_ratio'] = sales_demand['revenue'] / sales_demand['initial_revenue']

                        sales_demand['compliance_ratio'] = sales_demand['total_combo_cert_co2_megagrams'] / \
                                                           sales_demand['total_combo_target_co2_megagrams']

                        sales_demand['price_modification_score'] = \
                            (abs(1 - sales_demand['non hauling.BEV_cost_multiplier']) *
                             sales_demand['consumer_non hauling.BEV_abs_share_frac'] +
                             abs(1 - sales_demand['non hauling.ICE_cost_multiplier']) *
                             sales_demand['consumer_non hauling.ICE_abs_share_frac'] +
                             abs(1 - sales_demand['hauling.BEV_cost_multiplier']) *
                             sales_demand['consumer_hauling.BEV_abs_share_frac'] +
                             abs(1 - sales_demand['hauling.ICE_cost_multiplier']) *
                             sales_demand['consumer_hauling.ICE_abs_share_frac'])

                        non_modified_price = float(sales_demand[
                            (sales_demand['non hauling.BEV_cost_multiplier'] == 1) &
                            (sales_demand['hauling.BEV_cost_multiplier'] == 1) &
                            (sales_demand['non hauling.ICE_cost_multiplier'] == 1) &
                            (sales_demand['hauling.ICE_cost_multiplier'] == 1)]['share_weighted_price'])

                        sales_demand = sales_demand[abs(sales_demand['share_weighted_price'] - non_modified_price) <= 10]

                        # sales_demand.to_csv('%ssales_demand_%s_%s.csv' % (o2.options.output_folder, calendar_year, iteration_num))

                        # experiment ----------------------- #

                    consumer_market_share_demand = get_demanded_shares(winning_combo, calendar_year)

                    iteration_log = iteration_log.append(consumer_market_share_demand, ignore_index=True)

                    converged, thrashing = detect_convergence_and_thrashing(consumer_market_share_demand, iteration_log,
                                                                            iteration_num, market_class_vehicle_dict,
                                                                            o2.options.verbose)

                    update_iteration_log(calendar_year, converged, iteration_log, iteration_num, thrashing, compliant)

                    prev_winning_combo = winning_combo
                    prev_candidate_mfr_new_vehicles = candidate_mfr_new_vehicles
                else:
                    # roll back to prior iteration result, can't comply based on consumer response
                    winning_combo = prev_winning_combo
                    candidate_mfr_new_vehicles = prev_candidate_mfr_new_vehicles

                # decide whether to iterate or not
                iterate = o2.options.iterate_producer_consumer \
                          and iteration_num < o2.options.producer_consumer_max_iterations \
                          and not converged \
                          and not thrashing \
                          and compliant

                if iterate:
                    negotiate_market_shares(consumer_market_share_demand, iteration_num, market_class_vehicle_dict)
                    iteration_num = iteration_num + 1

            producer.finalize_production(calendar_year, manufacturer_ID, candidate_mfr_new_vehicles, winning_combo)
            stock.prior_year_stock_registered_count(calendar_year)
            stock.prior_year_stock_vmt(calendar_year)
            stock.age0_stock_vmt(calendar_year)
        iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder, index=False)

    return iteration_log


def update_iteration_log(calendar_year, converged, iteration_log, iteration_num, thrashing, compliant):
    iteration_log.loc[iteration_log.index[-1], 'iteration'] = iteration_num
    iteration_log.loc[iteration_log.index[-1], 'calendar_year'] = calendar_year
    iteration_log.loc[iteration_log.index[-1], 'thrashing'] = thrashing
    iteration_log.loc[iteration_log.index[-1], 'converged'] = converged
    iteration_log.loc[iteration_log.index[-1], 'compliant'] = compliant


def calc_market_class_data(calendar_year, candidate_mfr_new_vehicles, winning_combo):
    """

    :param candidate_mfr_new_vehicles: list of candidate composite vehicles that minimize producer compliance cost
    :param winning_combo: pandas Series that corresponds with candidate_mfr_new_vehicles, has market shares, costs,
            compliance data (Mg CO2)
    :return: dictionary of candidate vehicles binned by market class and reg class, updates winning_combo with
            sales-weighted average cost and CO2 g/mi by market class
    """

    from market_classes import MarketClass
    from omega_functions import weighted_value

    # group vehicles by market class
    market_class_vehicle_dict = MarketClass.get_market_class_dict()
    for new_veh in candidate_mfr_new_vehicles:
        market_class_vehicle_dict[new_veh.market_class_ID].add(new_veh)

    # calculate sales-weighted co2 g/mi and cost by market class
    for mc in MarketClass.market_classes:
        market_class_vehicles = market_class_vehicle_dict[mc]
        if market_class_vehicles:
            winning_combo['average_%s_co2_gpmi' % mc] = weighted_value(market_class_vehicles,
                                                                       'initial_registered_count',
                                                                       'cert_CO2_grams_per_mile')

            winning_combo['average_%s_cost' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'new_vehicle_mfr_cost_dollars')

            winning_combo['average_%s_fuel_price' % mc] = weighted_value(market_class_vehicles,
                                                                   'initial_registered_count',
                                                                   'retail_fuel_price')

            winning_combo['%s_sales' % mc] = 0
            for v in market_class_vehicles:
                winning_combo['%s_sales' % mc] = winning_combo['%s_sales' % mc] + v.initial_registered_count
        else:
            winning_combo['average_%s_co2_gpmi' % mc] = 0
            winning_combo['average_%s_cost' % mc] = 0
            winning_combo['%s_sales' % mc] = 0

        winning_combo['%s_abs_market_share_frac' % mc] = winning_combo['%s_sales' % mc] / winning_combo['total_sales']

    return market_class_vehicle_dict


def detect_convergence_and_thrashing(consumer_market_share_demand, iteration_log, iteration_num, market_class_dict, verbose):
    converged = True
    thrashing = iteration_num >= 5
    for mc in market_class_dict:
        # relative percentage convergence:
        converged = converged and abs(1 - \
                                      consumer_market_share_demand['producer_%s_share_frac' % mc] / \
                                      consumer_market_share_demand['consumer_%s_share_frac' % mc]) <= \
                    o2.options.producer_consumer_iteration_tolerance

        thrashing = detect_thrashing(iteration_log, mc, thrashing)

    if thrashing and verbose:
        print('!!THRASHING!!')

    return converged, thrashing


def negotiate_market_shares(consumer_market_share_demand, iteration_num, market_class_dict):
    if iteration_num < 1:
        for mc in market_class_dict:
            # try meeting partway (first pass)
            consumer_market_share_demand['consumer_%s_share_frac' % mc] = \
                (0.5 * consumer_market_share_demand['producer_%s_share_frac' % mc] +
                 0.5 * consumer_market_share_demand['consumer_%s_share_frac' % mc])
    else:
        for mc in market_class_dict:
            # try meeting partway
            consumer_market_share_demand['consumer_%s_share_frac' % mc] = \
                (0.33 * consumer_market_share_demand['producer_%s_share_frac' % mc] +
                 0.67 * consumer_market_share_demand['consumer_%s_share_frac' % mc])


def detect_thrashing(iteration_log, mc, thrashing):
    thrashing = thrashing and \
                ((
                         abs(1 - iteration_log['producer_%s_share_frac' % mc].iloc[-3] /
                             iteration_log['producer_%s_share_frac' % mc].iloc[-1])
                         <= o2.options.producer_consumer_iteration_tolerance
                         and
                         abs(1 - iteration_log['consumer_%s_share_frac' % mc].iloc[-3] /
                             iteration_log['consumer_%s_share_frac' % mc].iloc[-1])
                         <= o2.options.producer_consumer_iteration_tolerance
                 ) \
                 or (
                     (abs(1 - iteration_log['producer_%s_share_frac' % mc].iloc[-4] /
                          iteration_log['producer_%s_share_frac' % mc].iloc[-1])
                      <= o2.options.producer_consumer_iteration_tolerance
                      and
                      abs(1 - iteration_log['consumer_%s_share_frac' % mc].iloc[-4] /
                          iteration_log['consumer_%s_share_frac' % mc].iloc[-1])
                      <= o2.options.producer_consumer_iteration_tolerance)
                 )
                 or (
                     (abs(1 - iteration_log['producer_%s_share_frac' % mc].iloc[-5] /
                          iteration_log['producer_%s_share_frac' % mc].iloc[-1])
                      <= o2.options.producer_consumer_iteration_tolerance
                      and
                      abs(1 - iteration_log['consumer_%s_share_frac' % mc].iloc[-5] /
                          iteration_log['consumer_%s_share_frac' % mc].iloc[-1])
                      <= o2.options.producer_consumer_iteration_tolerance)
                 )
                 )
    return thrashing


def init_omega(o2_options):

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

        if o2.options.stock_scrappage == 'fixed':
            init_fail = init_fail + ReregistrationFixedByAge.init_database_from_file(
                o2.options.reregistration_fixed_by_age_file, verbose=o2.options.verbose)
            o2.options.stock_scrappage = ReregistrationFixedByAge
        else:
            pass

        if o2.options.stock_vmt == 'fixed':
            init_fail = init_fail + AnnualVMTFixedByAge.init_database_from_file(o2.options.annual_vmt_fixed_by_age_file,
                                                                                verbose=o2.options.verbose)
            o2.options.stock_vmt = AnnualVMTFixedByAge
        else:
            pass

        # initial year = initial fleet model year (latest year of data)
        o2.options.analysis_initial_year = int(o2.session.query(func.max(VehicleFinal.model_year)).scalar()) + 1
        # final year = last year of cost curve data
        o2.options.analysis_final_year = int(o2.session.query(func.max(CostCurve.model_year)).scalar())
        # o2.options.analysis_final_year = o2.options.analysis_initial_year
    finally:
        return init_fail


def run_omega(o2_options, single_shot=False, profile=False):
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
            if profile:
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

            # o2.session.close()
            o2.engine.dispose()
            o2.engine = None
            # o2.session = None
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
                '%s_summary_results.csv ' % fileio.get_filename(os.getcwd()), mode='a',
                header=False)


if __name__ == "__main__":
    try:
        import producer
        run_omega(OMEGARuntimeOptions(), single_shot=True, profile=False)  # to view in terminal: snakeviz omega2_profile.dmp
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
