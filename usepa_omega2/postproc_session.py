"""
postproc_session.py
===================

post-compliance-modeling output generation (charts, summary files, etc)

"""

from usepa_omega2 import *
import pandas as pd
from omega_plot import *


def run_postproc(iteration_log: pd.DataFrame, standalone_run: bool):
    """
    Generate charts and output files for a single simulation

    Args:
        iteration_log: dataframe storing information on producer-consumer iteration
        standalone_run: True if session is run outside of the batch process

    Returns: results summary dataframe

    """

    from manufacturer_annual_data import ManufacturerAnnualData
    from market_classes import MarketClass
    import pandas as pd
    import numpy as np

    if o2.options.calc_effects:
        from effects.o2_effects import run_effects_calcs
        run_effects_calcs()

    if not standalone_run:
        omega_log.logwrite('%s: Post Processing ...' % o2.options.session_name)

    bev_non_hauling_share_frac = np.array(sql_unpack_result(
        o2.session.query(ManufacturerAnnualData.bev_non_hauling_share_frac).all()))
    ice_non_hauling_share_frac = np.array(sql_unpack_result(
        o2.session.query(ManufacturerAnnualData.ice_non_hauling_share_frac).all()))
    bev_hauling_share_frac = np.array(
        sql_unpack_result(o2.session.query(ManufacturerAnnualData.bev_hauling_share_frac).all()))
    ice_hauling_share_frac = np.array(
        sql_unpack_result(o2.session.query(ManufacturerAnnualData.ice_hauling_share_frac).all()))

    plot_iteration(iteration_log)

    calendar_years = ManufacturerAnnualData.get_calendar_years()

    cert_co2_Mg, cert_target_co2_Mg, total_cost_billions = plot_manufacturer_compliance(calendar_years)

    plot_total_sales(calendar_years)

    plot_market_shares(bev_hauling_share_frac, bev_non_hauling_share_frac, calendar_years, ice_hauling_share_frac,
                       ice_non_hauling_share_frac)

    average_cost_data = plot_vehicle_cost(calendar_years)

    average_co2_gpmi_data = plot_co2_gpmi(calendar_years)

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


def plot_co2_gpmi(calendar_years):
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from market_classes import MarketClass

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
    return average_co2_gpmi_data


def plot_vehicle_cost(calendar_years):
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from market_classes import MarketClass

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
    label_xyt(ax1, 'Year', 'Average Vehicle Cost [$]',
              '%s\nAverage Vehicle Cost v Year' % o2.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(average_cost_data.keys())
    fig.savefig(o2.options.output_folder + '%s Average Vehicle Cost' % o2.options.session_unique_name)
    return average_cost_data


def plot_market_shares(bev_hauling_share_frac, bev_non_hauling_share_frac, calendar_years, ice_hauling_share_frac,
                       ice_non_hauling_share_frac):
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


def plot_total_sales(calendar_years):
    import numpy as np
    import consumer
    from vehicle_annual_data import VehicleAnnualData

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


def plot_manufacturer_compliance(calendar_years):
    from manufacturer_annual_data import ManufacturerAnnualData

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
    return cert_co2_Mg, cert_target_co2_Mg, total_cost_billions


def plot_iteration(iteration_log):
    from market_classes import MarketClass

    year_iter_labels = ['%d_%d_%d' % (cy - 2000, it, it_sub) for cy, it, it_sub in
                        zip(iteration_log['calendar_year'][iteration_log['pricing_iteration'] == -1],
                            iteration_log['iteration'][iteration_log['pricing_iteration'] == -1],
                            iteration_log['pricing_iteration'][iteration_log['pricing_iteration'] == -1])]
    for mc in MarketClass.get_market_class_dict():
        plt.figure()
        plt.plot(year_iter_labels,
                 iteration_log['producer_share_frac_%s' % mc][iteration_log['pricing_iteration'] == -1])
        plt.plot(year_iter_labels,
                 iteration_log['consumer_share_frac_%s' % mc][iteration_log['pricing_iteration'] == -1])
        plt.title('%s iteration' % mc)
        plt.grid()
        plt.legend(['producer_share_frac_%s' % mc, 'consumer_share_frac_%s' % mc])
        plt.ylim([0, 1])
        plt.savefig('%s%s Iteration %s.png' % (o2.options.output_folder, o2.options.session_unique_name, mc))
    fig, ax1 = fplothg(year_iter_labels, iteration_log['iteration'][iteration_log['pricing_iteration'] == -1])
    label_xyt(ax1, '', 'iteration', 'iteration mean = %.2f' % (
                2.0 * iteration_log['iteration'][iteration_log['pricing_iteration'] == -1].mean()))
    fig.savefig('%s%s Iteration Counts.png' % (o2.options.output_folder, o2.options.session_unique_name))
