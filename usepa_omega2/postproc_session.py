"""
postproc_session.py
===================

post-compliance-modeling output generation (charts, summary files, etc)

"""

from usepa_omega2 import *
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
    from consumer.market_classes import MarketClass
    import consumer
    import pandas as pd

    if o2.options.calc_effects:
        from effects.o2_effects import run_effects_calcs
        run_effects_calcs()

    if not standalone_run:
        omega_log.logwrite('%s: Post Processing ...' % o2.options.session_name)

    calendar_years = ManufacturerAnnualData.get_calendar_years()

    plot_iteration(iteration_log)

    cert_co2_Mg, cert_target_co2_Mg, total_cost_billions = plot_manufacturer_compliance(calendar_years)

    context_sales, total_sales = plot_total_sales(calendar_years)

    market_share_results = plot_market_shares(calendar_years, total_sales)

    average_cost_data = plot_vehicle_cost(calendar_years)

    average_generalized_cost_data = plot_vehicle_generalized_cost(calendar_years)

    megagrams_data = plot_vehicle_megagrams(calendar_years)

    average_cert_co2_gpmi_data = plot_cert_co2_gpmi(calendar_years)

    average_cert_kwh_pmi_data = plot_cert_kwh_pmi(calendar_years)

    average_target_co2_gpmi_data = plot_target_co2_gpmi(calendar_years)

    session_results = pd.DataFrame()
    session_results['calendar_year'] = calendar_years
    session_results['sales_total'] = total_sales
    session_results['sales_context'] = context_sales
    session_results['session_name'] = o2.options.session_name
    session_results['cert_target_co2_Mg'] = cert_target_co2_Mg
    session_results['cert_co2_Mg'] = cert_co2_Mg
    session_results['total_cost_billions'] = total_cost_billions

    for k in market_share_results:
        session_results[k] = market_share_results[k]

    for cat in consumer.market_categories + MarketClass.market_classes + ['total']:
        session_results['average_%s_cost' % cat] = average_cost_data[cat]
        session_results['average_%s_generalized_cost' % cat] = average_generalized_cost_data[cat]
        session_results['average_%s_cert_co2_gpmi' % cat] = average_cert_co2_gpmi_data[cat]
        session_results['average_%s_cert_kwh_pmi' % cat] = average_cert_kwh_pmi_data[cat]
        session_results['average_%s_target_co2_gpmi' % cat] = average_target_co2_gpmi_data[cat]
        session_results['%s_co2_Mg' % cat] = megagrams_data[cat]

    return session_results


def plot_cert_co2_gpmi(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.market_classes import MarketClass
    import consumer

    average_cert_co2_data = dict()

    # tally up total sales weighted co2
    average_cert_co2_data['total'] = []
    for cy in calendar_years:
        average_cert_co2_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales weighted co2
    for mcat in consumer.market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_ID_and_co2 = o2.session.query(VehicleAnnualData.registered_count,
                                                                       VehicleFinal.market_class_ID,
                                                                       VehicleFinal.cert_CO2_grams_per_mile) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_ID_and_co2:
                if mcat in result.market_class_ID.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.cert_CO2_grams_per_mile)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cert_co2_data[mcat] = market_category_cost

    # cost/market category chart
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, average_cert_co2_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_co2_data['total'], '.-')
    ax1.legend(consumer.market_categories + ['total'])
    label_xyt(ax1, 'Year', 'CO2 [g/mi]',
              '%s\nAverage Vehicle Cert CO2 g/mi by Market Category v Year' % o2.options.session_unique_name)
    fig.savefig(o2.options.output_folder + '%s V Cert CO2 gpmi Mkt Cat.png' % o2.options.session_unique_name)

    # cost/market class chart
    fig, ax1 = figure()
    for mc in MarketClass.market_classes:
        average_cert_co2_data[mc] = []
        for cy in calendar_years:
            average_cert_co2_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cert_co2_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cert_co2_data[mc], '.--')

    label_xyt(ax1, 'Year', 'CO2 [g/mi]',
              '%s\nAverage Vehicle Cert CO2 g/mi  by Market Class v Year' % o2.options.session_unique_name)
    ax1.legend(MarketClass.market_classes)
    fig.savefig(o2.options.output_folder + '%s V Cert CO2 gpmi Mkt Cls.png' % o2.options.session_unique_name)
    return average_cert_co2_data


def plot_cert_kwh_pmi(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.market_classes import MarketClass
    import consumer

    average_cert_kwh_data = dict()

    # tally up total sales weighted kWh
    average_cert_kwh_data['total'] = []
    for cy in calendar_years:
        average_cert_kwh_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.cert_kWh_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales weighted kWh
    for mcat in consumer.market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_ID_and_kwh = o2.session.query(VehicleAnnualData.registered_count,
                                                                       VehicleFinal.market_class_ID,
                                                                       VehicleFinal.cert_kWh_per_mile) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_ID_and_kwh:
                if mcat in result.market_class_ID.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.cert_kWh_per_mile)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cert_kwh_data[mcat] = market_category_cost

    # cost/market category chart
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, average_cert_kwh_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_kwh_data['total'], '.-')
    ax1.legend(consumer.market_categories + ['total'])
    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi by Market Category v Year' % o2.options.session_unique_name)
    fig.savefig(o2.options.output_folder + '%s V Cert kWh pmi Mkt Cat.png' % o2.options.session_unique_name)

    # cost/market class chart
    fig, ax1 = figure()
    for mc in MarketClass.market_classes:
        average_cert_kwh_data[mc] = []
        for cy in calendar_years:
            average_cert_kwh_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.cert_kWh_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cert_kwh_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cert_kwh_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi  by Market Class v Year' % o2.options.session_unique_name)
    ax1.legend(MarketClass.market_classes)
    fig.savefig(o2.options.output_folder + '%s V Cert kWh pmi Mkt Cls.png' % o2.options.session_unique_name)
    return average_cert_kwh_data


def plot_target_co2_gpmi(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.market_classes import MarketClass
    import consumer

    average_cert_co2_data = dict()

    # tally up total sales weighted co2
    average_cert_co2_data['total'] = []
    for cy in calendar_years:
        average_cert_co2_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.cert_target_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales weighted co2
    for mcat in consumer.market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_ID_and_co2 = o2.session.query(VehicleAnnualData.registered_count,
                                                                       VehicleFinal.market_class_ID,
                                                                       VehicleFinal.cert_target_CO2_grams_per_mile) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_ID_and_co2:
                if mcat in result.market_class_ID.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.cert_target_CO2_grams_per_mile)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cert_co2_data[mcat] = market_category_cost

    # cost/market category chart
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, average_cert_co2_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_co2_data['total'], '.-')
    ax1.legend(consumer.market_categories + ['total'])
    label_xyt(ax1, 'Year', 'CO2 [g/mi]',
              '%s\nAverage Vehicle Target CO2 g/mi by Market Category v Year' % o2.options.session_unique_name)
    fig.savefig(o2.options.output_folder + '%s V Tgt CO2 gpmi Mkt Cat.png' % o2.options.session_unique_name)

    # cost/market class chart
    fig, ax1 = figure()
    for mc in MarketClass.market_classes:
        average_cert_co2_data[mc] = []
        for cy in calendar_years:
            average_cert_co2_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.cert_target_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cert_co2_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cert_co2_data[mc], '.--')

    label_xyt(ax1, 'Year', 'CO2 [g/mi]',
              '%s\nAverage Vehicle Target CO2 g/mi by Market Class v Year' % o2.options.session_unique_name)
    ax1.legend(MarketClass.market_classes)
    fig.savefig(o2.options.output_folder + '%s V Tgt CO2 gpmi Mkt Cls.png' % o2.options.session_unique_name)
    return average_cert_co2_data


def plot_vehicle_cost(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.market_classes import MarketClass
    import consumer

    average_cost_data = dict()

    # tally up total sales weighted cost
    average_cost_data['total'] = []
    for cy in calendar_years:
        average_cost_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales
    for mcat in consumer.market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_ID_and_cost = o2.session.query(VehicleAnnualData.registered_count,
                                                                       VehicleFinal.market_class_ID,
                                                                       VehicleFinal.new_vehicle_mfr_cost_dollars) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_ID_and_cost:
                if mcat in result.market_class_ID.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.new_vehicle_mfr_cost_dollars)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cost_data[mcat] = market_category_cost

    # cost/market category chart
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, average_cost_data[mcat], '.--')
    ax1.plot(calendar_years, average_cost_data['total'], '.-')
    ax1.legend(consumer.market_categories + ['total'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost by Market Category v Year' % o2.options.session_unique_name)
    fig.savefig(o2.options.output_folder + '%s V Cost Mkt Cat.png' % o2.options.session_unique_name)

    # cost/market class chart
    fig, ax1 = figure()
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

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost  by Market Class v Year' % o2.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(MarketClass.market_classes)
    fig.savefig(o2.options.output_folder + '%s V Cost by Mkt Cls.png' % o2.options.session_unique_name)
    return average_cost_data


def plot_vehicle_generalized_cost(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.market_classes import MarketClass
    import consumer

    average_cost_data = dict()

    # tally up total sales weighted cost
    average_cost_data['total'] = []
    for cy in calendar_years:
        average_cost_data['total'].append(o2.session.query(
            func.sum(VehicleFinal.new_vehicle_mfr_generalized_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales
    for mcat in consumer.market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_ID_and_cost = o2.session.query(VehicleAnnualData.registered_count,
                                                                       VehicleFinal.market_class_ID,
                                                                       VehicleFinal.new_vehicle_mfr_generalized_cost_dollars) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_ID_and_cost:
                if mcat in result.market_class_ID.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.new_vehicle_mfr_generalized_cost_dollars)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cost_data[mcat] = market_category_cost

    # cost/market category chart
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, average_cost_data[mcat], '.--')
    ax1.plot(calendar_years, average_cost_data['total'], '.-')
    ax1.legend(consumer.market_categories + ['total'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized Cost by Market Category v Year' % o2.options.session_unique_name)
    fig.savefig(o2.options.output_folder + '%s V GenCost Mkt Cat.png' % o2.options.session_unique_name)

    # cost/market class chart
    fig, ax1 = figure()
    for mc in MarketClass.market_classes:
        average_cost_data[mc] = []
        for cy in calendar_years:
            average_cost_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.new_vehicle_mfr_generalized_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cost_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cost_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized_Cost  by Market Class v Year' % o2.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(MarketClass.market_classes)
    fig.savefig(o2.options.output_folder + '%s V GenCost Mkt Cls.png' % o2.options.session_unique_name)
    return average_cost_data


def plot_vehicle_megagrams(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData
    from consumer.market_classes import MarketClass
    import consumer

    Mg_data = dict()

    # tally up total Mg
    Mg_data['total'] = []
    for cy in calendar_years:
        Mg_data['total'].append(
            o2.session.query(func.sum(VehicleFinal.cert_CO2_Mg)).
                                          filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category Mg
    for mcat in consumer.market_categories:
        market_category_Mg = []
        for idx, cy in enumerate(calendar_years):
            market_ID_and_Mg = o2.session.query(VehicleFinal.market_class_ID,
                                                VehicleFinal.cert_CO2_Mg) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_Mg = 0
            for result in market_ID_and_Mg:
                if mcat in result.market_class_ID.split('.'):
                    sales_weighted_Mg += float(result.cert_CO2_Mg)
            market_category_Mg.append(sales_weighted_Mg)

        Mg_data[mcat] = market_category_Mg

    # cost/market category chart
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, Mg_data[mcat], '.--')
    ax1.plot(calendar_years, Mg_data['total'], '.-')
    ax1.legend(consumer.market_categories + ['total'])
    label_xyt(ax1, 'Year', 'CO2 [Mg]',
              '%s\nVehicle CO2 Megagrams by Market Category v Year' % o2.options.session_unique_name)
    fig.savefig(o2.options.output_folder + '%s V Mg Mkt Cat.png' % o2.options.session_unique_name)

    # cost/market class chart
    fig, ax1 = figure()
    for mc in MarketClass.market_classes:
        Mg_data[mc] = []
        for cy in calendar_years:
            Mg_data[mc].append(o2.session.query(
                func.sum(VehicleFinal.cert_CO2_Mg)).
                                         filter(VehicleFinal.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())

        if 'ICE' in mc:
            ax1.plot(calendar_years, Mg_data[mc], '.-')
        else:
            ax1.plot(calendar_years, Mg_data[mc], '.--')
    ax1.plot(calendar_years, Mg_data['total'], '.-')
    label_xyt(ax1, 'Year', 'CO2 [Mg]',
              '%s\nVehicle CO2 Megagrams  by Market Class v Year' % o2.options.session_unique_name)
    ax1.legend(MarketClass.market_classes + ['total'])
    fig.savefig(o2.options.output_folder + '%s V Mg Mkt Cls.png' % o2.options.session_unique_name)
    return Mg_data



def plot_market_shares(calendar_years, total_sales):
    """

    Args:
        calendar_years:
        total_sales:

    Returns:

    """
    from consumer.market_classes import MarketClass
    from vehicle_annual_data import VehicleAnnualData
    from vehicles import VehicleFinal
    import consumer

    market_share_results = dict()

    # tally up market_category sales
    for mcat in consumer.market_categories:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_ID = o2.session.query(VehicleAnnualData.registered_count, VehicleFinal.market_class_ID) \
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            count = 0
            for result in registered_count_and_market_ID:
                if mcat in result.market_class_ID.split('.'):
                    count += result.registered_count
            market_category_abs_share_frac.append(float(count) / total_sales[idx])

        market_share_results['abs_share_frac_%s' % mcat] = market_category_abs_share_frac

    # tally up market class sales
    for mc in MarketClass.market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            market_category_abs_share_frac.append(float(o2.session.query(func.sum(VehicleAnnualData.registered_count))
                .filter(VehicleAnnualData.vehicle_ID == VehicleFinal.vehicle_ID)
                .filter(VehicleFinal.market_class_ID == mc)
                .filter(VehicleAnnualData.calendar_year == cy)
                .filter(VehicleAnnualData.age == 0).scalar()) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % mc] = market_category_abs_share_frac

    # plot market category results
    fig, ax1 = figure()
    for mcat in consumer.market_categories:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % mcat], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s\nMarket Category Absolute Market Shares' % o2.options.session_unique_name)
    ax1.legend(consumer.market_categories)
    fig.savefig(o2.options.output_folder + '%s Mkt Cat Shares.png' % o2.options.session_unique_name)

    # plot market class results
    fig, ax1 = figure()
    for mc in MarketClass.market_classes:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % mc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s\nMarket Class Absolute Market Shares' % o2.options.session_unique_name)
    ax1.legend(MarketClass.market_classes)
    fig.savefig(o2.options.output_folder + '%s Mkt Cls Shares.png' % o2.options.session_unique_name)

    return market_share_results


def plot_total_sales(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
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
    fig.savefig(o2.options.output_folder + '%s Sales v Year.png' % o2.options.session_unique_name)

    return context_sales, total_sales


def plot_manufacturer_compliance(calendar_years):
    """

    Args:
        calendar_years:

    Returns:

    """
    from manufacturer_annual_data import ManufacturerAnnualData

    cert_target_co2_Mg = ManufacturerAnnualData.get_cert_target_co2_Mg()
    cert_co2_Mg = ManufacturerAnnualData.get_cert_co2_Mg()
    total_cost_billions = ManufacturerAnnualData.get_total_cost_billions()
    # compliance chart
    fig, ax1 = fplothg(calendar_years, cert_target_co2_Mg, '.-')
    ax1.plot(calendar_years, cert_co2_Mg, '.-')
    ax1.legend(['cert_target_co2_Mg', 'cert_co2_Mg'])
    label_xyt(ax1, 'Year', 'CO2 [Mg]', '%s\nCompliance Versus Calendar Year\n Total Cost $%.2f Billion' % (
        o2.options.session_unique_name, total_cost_billions))
    fig.savefig(o2.options.output_folder + '%s Cert Mg v Year.png' % o2.options.session_unique_name)

    return cert_co2_Mg, cert_target_co2_Mg, total_cost_billions


def plot_iteration(iteration_log):
    """

    Args:
        iteration_log:

    Returns:

    """
    from consumer.market_classes import MarketClass

    # year_iter_labels = ['%d_%d_%d' % (cy - 2000, it, it_sub) for cy, it, it_sub in
    #                     zip(iteration_log['calendar_year'][iteration_log['pricing_iteration'] == -1],
    #                         iteration_log['iteration'][iteration_log['pricing_iteration'] == -1],
    #                         iteration_log['pricing_iteration'][iteration_log['pricing_iteration'] == -1])]


    for iteration in [0,-1]:
        year_iter_labels = ['%d_%d' % (cy - 2000, it) for cy, it in
                            zip(iteration_log['calendar_year'][iteration_log['pricing_iteration'] == iteration],
                                iteration_log['iteration'][iteration_log['pricing_iteration'] == iteration])]

        for mc in MarketClass.get_market_class_dict():
            plt.figure()
            plt.plot(year_iter_labels,
                     iteration_log['producer_abs_share_frac_%s' % mc][iteration_log['pricing_iteration'] == iteration])
            plt.xticks(rotation=90)
            plt.plot(year_iter_labels,
                     iteration_log['consumer_abs_share_frac_%s' % mc][iteration_log['pricing_iteration'] == iteration])
            plt.title('%s iteration %d' % (mc, iteration))
            plt.grid()
            plt.legend(['producer_abs_share_frac_%s' % mc, 'consumer_abs_share_frac_%s' % mc])
            # plt.ylim([0, 1])
            plt.savefig('%s%s Iter %s %s.png' % (o2.options.output_folder, o2.options.session_unique_name, mc, iteration))

        plt.figure()
        if iteration == -1:
            for mc in MarketClass.get_market_class_dict():
                plt.plot(iteration_log['calendar_year'][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['converged'] == True)] - 2000,
                         iteration_log['consumer_generalized_cost_dollars_%s' % mc][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['converged'] == True)], '.-')
        else:
            for mc in MarketClass.get_market_class_dict():
                plt.plot(iteration_log['calendar_year'][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['iteration'] == 0)] - 2000,
                         iteration_log['consumer_generalized_cost_dollars_%s' % mc][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['iteration'] == 0)], '.-')

        plt.xticks(rotation=90)
        plt.legend(['consumer_generalized_cost_dollars_%s' % mc for mc in MarketClass.get_market_class_dict()])
        plt.ylabel('Cost $ / mi')
        plt.title('Consumer Generalized Cost %d' % iteration)
        # plt.ylim([0.0, 0.9])
        plt.grid()
        plt.savefig('%s%s ConsumerGC %s.png' % (o2.options.output_folder, o2.options.session_unique_name, iteration))

        plt.figure()
        if iteration == -1:
            for mc in MarketClass.get_market_class_dict():
                plt.plot(iteration_log['calendar_year'][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['converged'] == True)] - 2000,
                         iteration_log['cost_multiplier_%s' % mc][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['converged'] == True)], '.-')
        else:
            for mc in MarketClass.get_market_class_dict():
                plt.plot(iteration_log['calendar_year'][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['iteration'] == 0)] - 2000,
                         iteration_log['cost_multiplier_%s' % mc][
                             (iteration_log['pricing_iteration'] == iteration) & (iteration_log['iteration'] == 0)], '.-')

        plt.xticks(rotation=90)
        plt.legend(['cost_multiplier_%s' % mc for mc in MarketClass.get_market_class_dict()])
        plt.ylabel('Cost Multiplier')
        plt.title('Producer Cost Multipliers %d' % iteration)
        # plt.ylim([0.0, 0.9])
        plt.grid()
        plt.savefig('%s%s Producer Cost Multipliers %d.png' % (o2.options.output_folder, o2.options.session_unique_name, iteration))


    fig, ax1 = fplothg(year_iter_labels, iteration_log['iteration'][iteration_log['pricing_iteration'] == -1])
    ax1.set_xticklabels(ax1.get_xticks(), rotation=90)
    label_xyt(ax1, '', 'Iteration [#]', 'Iteration mean = %.2f' % (
                2.0 * iteration_log['iteration'][iteration_log['pricing_iteration'] == -1].mean()))
    fig.savefig('%s%s Iter Counts.png' % (o2.options.output_folder, o2.options.session_unique_name))

    # plot producer initial share and g/mi decisions
    pts = (iteration_log['iteration'] == 0) & (iteration_log['pricing_iteration'] == 0)
    plt.figure()
    for mc in MarketClass.get_market_class_dict():
        plt.plot(iteration_log['calendar_year'][pts] - 2000, iteration_log['producer_abs_share_frac_%s' % mc][pts])
    plt.xticks(rotation=90)
    plt.title('Producer Initial Absolute Market Shares')
    plt.grid()
    plt.legend(['producer_abs_share_frac_%s' % mc for mc in MarketClass.get_market_class_dict()])
    plt.savefig('%s%s Producer Initial Abs Shares.png' % (o2.options.output_folder, o2.options.session_unique_name))

    plt.figure()
    for mc in MarketClass.get_market_class_dict():
        plt.plot(iteration_log['calendar_year'][pts] - 2000, iteration_log['average_co2_gpmi_%s' % mc][pts])
    plt.xticks(rotation=90)
    plt.title('Producer Initial CO2 g/mi')
    plt.grid()
    plt.legend(['average_co2_gpmi_%s' % mc for mc in MarketClass.get_market_class_dict()])
    plt.savefig('%s%s Producer Initial CO2 gpmi.png' % (o2.options.output_folder, o2.options.session_unique_name))
