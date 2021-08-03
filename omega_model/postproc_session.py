"""

post-compliance-modeling output generation (charts, summary files, etc)


----

**CODE**

"""

from omega_model import *
from common.omega_plot import *
from policy.credit_banking import CreditBank

market_classes = []
market_categories = []


def run_postproc(iteration_log, credit_banks, standalone_run):
    """
    Generate charts and output files for a single simulation

    Args:
        iteration_log (DataFrame): dataframe storing information on producer-consumer iteration
        credit_banks (dict of CreditBanks): credit banking information per compliance_id
        standalone_run (bool): True if session is run outside of the batch process

    Returns:
        Results summary DataFrame

    """
    from producer.vehicles import VehicleFinal
    import pandas as pd

    global market_classes, market_categories
    market_classes = omega_globals.options.MarketClass.market_classes
    market_categories = omega_globals.options.MarketClass.market_categories

    if omega_globals.options.calc_effects:
        from effects.o2_effects import run_effects_calcs
        run_effects_calcs()

    if not standalone_run:
        omega_log.logwrite('%s: Post Processing ...' % omega_globals.options.session_name)

    vehicle_years = list(range(omega_globals.options.analysis_initial_year - 1,
                               omega_globals.options.analysis_final_year + 1))

    analysis_years = vehicle_years[1:]

    session_results = pd.DataFrame()
    session_results['calendar_year'] = analysis_years
    session_results['session_name'] = omega_globals.options.session_name

    context_sales, total_sales, manufacturer_sales = plot_total_sales(vehicle_years, VehicleFinal.compliance_ids)

    session_results['sales_total'] = total_sales[1:]
    session_results['sales_context'] = context_sales
    for manufacturer in manufacturer_sales:
        session_results['%s_sales_total' % manufacturer] = manufacturer_sales[manufacturer][1:]

        # generate manufacturer-specific plots and data if not consolidating
        for compliance_id in VehicleFinal.compliance_ids:

            calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, cert_target_co2e_Mg, total_cost_billions = \
                plot_manufacturer_compliance(analysis_years, compliance_id, credit_banks[compliance_id])

            session_results['%s_cert_target_co2e_Mg' % compliance_id] = cert_target_co2e_Mg
            session_results['%s_calendar_year_cert_co2e_Mg' % compliance_id] = calendar_year_cert_co2e_Mg
            session_results['%s_model_year_cert_co2e_Mg' % compliance_id] = model_year_cert_co2e_Mg
            session_results['%s_total_cost_billions' % compliance_id] = total_cost_billions

            if not omega_globals.options.consolidate_manufacturers:
                # plot_iteration(iteration_log, compliance_id)

                mfr_market_share_results = plot_manufacturer_market_shares(vehicle_years, compliance_id,
                                                                           manufacturer_sales[compliance_id])

                mfr_average_cost_data = plot_manufacturer_vehicle_cost(analysis_years, compliance_id)

        if not omega_globals.options.consolidate_manufacturers:
            for msr in mfr_market_share_results:
                session_results[msr] = mfr_market_share_results[msr] = mfr_market_share_results[msr][1:]

            for macd in mfr_average_cost_data:
                session_results['average_%s_cost' % macd] = mfr_average_cost_data[macd]

    market_share_results = plot_market_shares(vehicle_years, total_sales)

    average_cost_data = plot_vehicle_cost(analysis_years)

    average_generalized_cost_data = plot_vehicle_generalized_cost(analysis_years)

    megagrams_data = plot_vehicle_megagrams(analysis_years)

    average_cert_co2e_gpmi_data = plot_cert_co2e_gpmi(analysis_years)

    average_cert_direct_kwh_pmi_data = plot_cert_direct_kwh_pmi(analysis_years)

    average_target_co2e_gpmi_data = plot_target_co2e_gpmi(analysis_years)

    # market share results include base year data, but the rest of the data doesn't, so drop the
    # base year data, otherwise the dataframe at the end will fail due to inconsistent column lengths

    for msr in market_share_results:
        session_results[msr] = market_share_results[msr] = market_share_results[msr][1:]

    for cat in market_categories + market_classes + ['total']:
        session_results['average_%s_cost' % cat] = average_cost_data[cat]
        session_results['average_%s_generalized_cost' % cat] = average_generalized_cost_data[cat]
        session_results['average_%s_cert_co2e_gpmi' % cat] = average_cert_co2e_gpmi_data[cat]
        session_results['average_%s_cert_direct_kwh_pmi' % cat] = average_cert_direct_kwh_pmi_data[cat]
        session_results['average_%s_target_co2e_gpmi' % cat] = average_target_co2e_gpmi_data[cat]
        session_results['%s_co2e_Mg' % cat] = megagrams_data[cat]

    return session_results


def plot_cert_co2e_gpmi(calendar_years):
    """
    Plot cert CO2e g/mi versus model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average cert co2e g/mi data by total, market class and market category

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData

    average_cert_co2e_data = dict()

    # tally up total sales weighted co2
    average_cert_co2e_data['total'] = []
    for cy in calendar_years:
        average_cert_co2e_data['total'].append(omega_globals.session.query(
            func.sum(VehicleFinal.cert_co2e_grams_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                               filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                               filter(VehicleFinal.model_year == cy).
                                               filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales weighted co2
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id_and_co2 = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                                 VehicleFinal.market_class_id,
                                                                                 VehicleFinal.cert_co2e_grams_per_mile) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_id_and_co2:
                if mcat in result.market_class_id.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.cert_co2e_grams_per_mile)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cert_co2e_data[mcat] = market_category_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cert_co2e_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_co2e_data['total'], '.-')
    ax1.legend(market_categories + ['total'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert CO2e g/mi by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert CO2e gpmi Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        average_cert_co2e_data[mc] = []
        for cy in calendar_years:
            average_cert_co2e_data[mc].append(omega_globals.session.query(
                func.sum(VehicleFinal.cert_co2e_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                              filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                              filter(VehicleFinal.model_year == cy).
                                              filter(VehicleFinal.market_class_id == mc).
                                              filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cert_co2e_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cert_co2e_data[mc], '.--')

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert CO2e g/mi  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert CO2e gpmi Mkt Cls.png' % omega_globals.options.session_unique_name)
    return average_cert_co2e_data


def plot_cert_direct_kwh_pmi(calendar_years):
    """
    Plot vehicle cert direct kWh/mi v. model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average cert direct kWh/mi data by total, market class and market category

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData
    import consumer

    average_cert_direct_kwh_data = dict()

    # tally up total sales weighted kWh
    average_cert_direct_kwh_data['total'] = []
    for cy in calendar_years:
        average_cert_direct_kwh_data['total'].append(omega_globals.session.query(
            func.sum(VehicleFinal.cert_direct_kwh_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                                     filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                                     filter(VehicleFinal.model_year == cy).
                                                     filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales weighted kWh
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id_and_kwh = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                                 VehicleFinal.market_class_id,
                                                                                 VehicleFinal.cert_direct_kwh_per_mile) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_id_and_kwh:
                if mcat in result.market_class_id.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.cert_direct_kwh_per_mile)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cert_direct_kwh_data[mcat] = market_category_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cert_direct_kwh_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_direct_kwh_data['total'], '.-')
    ax1.legend(market_categories + ['total'])
    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert kWh pmi Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        average_cert_direct_kwh_data[mc] = []
        for cy in calendar_years:
            average_cert_direct_kwh_data[mc].append(omega_globals.session.query(
                func.sum(VehicleFinal.cert_direct_kwh_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                                    filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                                    filter(VehicleFinal.model_year == cy).
                                                    filter(VehicleFinal.market_class_id == mc).
                                                    filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cert_direct_kwh_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cert_direct_kwh_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert kWh pmi Mkt Cls.png' % omega_globals.options.session_unique_name)
    return average_cert_direct_kwh_data


def plot_target_co2e_gpmi(calendar_years):
    """
    Plot vehicle target CO2e g/mi v. model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average cert target CO2e g/mi data by total, market class and market category

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData

    average_cert_target_co2e_data = dict()

    # tally up total sales weighted co2
    average_cert_target_co2e_data['total'] = []
    for cy in calendar_years:
        average_cert_target_co2e_data['total'].append(omega_globals.session.query(
            func.sum(VehicleFinal.cert_target_co2e_grams_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                                      filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                                      filter(VehicleFinal.model_year == cy).
                                                      filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales weighted co2
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id_and_co2 = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                                 VehicleFinal.market_class_id,
                                                                                 VehicleFinal.cert_target_co2e_grams_per_mile) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_id_and_co2:
                if mcat in result.market_class_id.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(
                        result.cert_target_co2e_grams_per_mile)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cert_target_co2e_data[mcat] = market_category_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cert_target_co2e_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_target_co2e_data['total'], '.-')
    ax1.legend(market_categories + ['total'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Target CO2e g/mi by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Tgt CO2e gpmi Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        average_cert_target_co2e_data[mc] = []
        for cy in calendar_years:
            average_cert_target_co2e_data[mc].append(omega_globals.session.query(
                func.sum(VehicleFinal.cert_target_co2e_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                                     filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                                     filter(VehicleFinal.model_year == cy).
                                                     filter(VehicleFinal.market_class_id == mc).
                                                     filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cert_target_co2e_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cert_target_co2e_data[mc], '.--')

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Target CO2e g/mi by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Tgt CO2e gpmi Mkt Cls.png' % omega_globals.options.session_unique_name)
    return average_cert_target_co2e_data


def plot_vehicle_cost(calendar_years):
    """
    Plot average vehicle cost v. model year, by market class and market category, across all manufacturers.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average vehicle cost data by total, market class and market category

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData

    average_cost_data = dict()

    # tally up total sales weighted cost
    average_cost_data['total'] = []
    for cy in calendar_years:
        average_cost_data['total'].append(omega_globals.session.query(
            func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                          filter(VehicleFinal.model_year == cy).
                                          filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id_and_cost = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                                  VehicleFinal.market_class_id,
                                                                                  VehicleFinal.new_vehicle_mfr_cost_dollars) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_id_and_cost:
                if mcat in result.market_class_id.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.new_vehicle_mfr_cost_dollars)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cost_data[mcat] = market_category_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cost_data[mcat], '.--')
    ax1.plot(calendar_years, average_cost_data['total'], '.-')
    ax1.legend(market_categories + ['total'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cost Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        average_cost_data[mc] = []
        for cy in calendar_years:
            average_cost_data[mc].append(omega_globals.session.query(
                func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                         filter(VehicleFinal.model_year == cy).
                                         filter(VehicleFinal.market_class_id == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cost_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cost_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost  by Market Class v Year' % omega_globals.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cost by Mkt Cls.png' % omega_globals.options.session_unique_name)

    return average_cost_data


def plot_manufacturer_vehicle_cost(calendar_years, compliance_id):
    """
    Plot vehicle cost v. model year, by market class and market category, for a single manufacturer.

    Args:
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        calendar_years ([years]): list of model years

    Returns:
        dict of average vehicle cost data by total, market class and market category for the given manufacturer

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData

    average_cost_data = dict()

    # tally up total sales weighted cost
    average_cost_data['%s_total' % compliance_id] = []
    for cy in calendar_years:
        average_cost_data['%s_total' % compliance_id].append(omega_globals.session.query(
            func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                                             filter(
            VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                                             filter(VehicleFinal.compliance_id == compliance_id).
                                                             filter(VehicleFinal.model_year == cy).
                                                             filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id_and_cost = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                                  VehicleFinal.market_class_id,
                                                                                  VehicleFinal.new_vehicle_mfr_cost_dollars) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.compliance_id == compliance_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_id_and_cost:
                if mcat in result.market_class_id.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(result.new_vehicle_mfr_cost_dollars)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        average_cost_data['%s_%s' % (compliance_id, mcat)] = market_category_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cost_data['%s_%s' % (compliance_id, mcat)], '.--')
    ax1.plot(calendar_years, average_cost_data['%s_total' % compliance_id], '.-')
    ax1.legend(market_categories + ['%s_total' % compliance_id])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s %s\nAverage Vehicle Cost by Market Category v Year' %
              (compliance_id, omega_globals.options.session_unique_name))
    fig.savefig(omega_globals.options.output_folder + '%s V Cost Mkt Cat %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        average_cost_data['%s_%s' % (compliance_id, mc)] = []
        for cy in calendar_years:
            average_cost_data['%s_%s' % (compliance_id, mc)].append(omega_globals.session.query(
                func.sum(VehicleFinal.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                                                    filter(
                VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                                                    filter(VehicleFinal.compliance_id == compliance_id).
                                                                    filter(VehicleFinal.model_year == cy).
                                                                    filter(VehicleFinal.market_class_id == mc).
                                                                    filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cost_data['%s_%s' % (compliance_id, mc)], '.-')
        else:
            ax1.plot(calendar_years, average_cost_data['%s_%s' % (compliance_id, mc)], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s %s\nAverage Vehicle Cost  by Market Class v Year'
              % (compliance_id, omega_globals.options.session_unique_name))
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(omega_globals.options.output_folder + '%s V Cost by Mkt Cls %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    return average_cost_data


def plot_vehicle_generalized_cost(calendar_years):
    """
    Plot manufacturer vehicle generalized cost v. model year, by market class and market category,
    for a single manufacturer.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average generalized cost data by total, market class and market category

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData
    import consumer

    generalized_cost_data = dict()

    # tally up total sales weighted cost
    generalized_cost_data['total'] = []
    for cy in calendar_years:
        generalized_cost_data['total'].append(omega_globals.session.query(
            func.sum(VehicleFinal.new_vehicle_mfr_generalized_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                              filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                              filter(VehicleFinal.model_year == cy).
                                              filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category sales
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id_and_cost = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                                  VehicleFinal.market_class_id,
                                                                                  VehicleFinal.new_vehicle_mfr_generalized_cost_dollars) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_cost = 0
            mcat_count = 0
            for result in registered_count_and_market_id_and_cost:
                if mcat in result.market_class_id.split('.'):
                    mcat_count += float(result.registered_count)
                    sales_weighted_cost += float(result.registered_count) * float(
                        result.new_vehicle_mfr_generalized_cost_dollars)
            market_category_cost.append(sales_weighted_cost / max(1, mcat_count))

        generalized_cost_data[mcat] = market_category_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, generalized_cost_data[mcat], '.--')
    ax1.plot(calendar_years, generalized_cost_data['total'], '.-')
    ax1.legend(market_categories + ['total'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized Cost by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V GenCost Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        generalized_cost_data[mc] = []
        for cy in calendar_years:
            generalized_cost_data[mc].append(omega_globals.session.query(
                func.sum(VehicleFinal.new_vehicle_mfr_generalized_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                             filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                                             filter(VehicleFinal.model_year == cy).
                                             filter(VehicleFinal.market_class_id == mc).
                                             filter(VehicleAnnualData.age == 0).scalar())
        if 'ICE' in mc:
            ax1.plot(calendar_years, generalized_cost_data[mc], '.-')
        else:
            ax1.plot(calendar_years, generalized_cost_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized_Cost  by Market Class v Year' % omega_globals.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V GenCost Mkt Cls.png' % omega_globals.options.session_unique_name)
    return generalized_cost_data


def plot_vehicle_megagrams(calendar_years):
    """
    Plot vehicle cert CO2e Mg v. model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of vehicle cert CO2e Mg data by total, market class and market category

    """
    from producer.vehicles import VehicleFinal
    from producer.vehicle_annual_data import VehicleAnnualData

    Mg_data = dict()

    # tally up total Mg
    Mg_data['total'] = []
    for cy in calendar_years:
        Mg_data['total'].append(
            omega_globals.session.query(func.sum(VehicleFinal.cert_co2e_Mg)).
                filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                filter(VehicleFinal.model_year == cy).
                filter(VehicleAnnualData.age == 0).scalar())

    # tally up market_category Mg
    for mcat in market_categories:
        market_category_Mg = []
        for idx, cy in enumerate(calendar_years):
            market_id_and_Mg = omega_globals.session.query(VehicleFinal.market_class_id,
                                                           VehicleFinal.cert_co2e_Mg) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            sales_weighted_Mg = 0
            for result in market_id_and_Mg:
                if mcat in result.market_class_id.split('.'):
                    sales_weighted_Mg += float(result.cert_co2e_Mg)
            market_category_Mg.append(sales_weighted_Mg)

        Mg_data[mcat] = market_category_Mg

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, Mg_data[mcat], '.--')
    ax1.plot(calendar_years, Mg_data['total'], '.-')
    ax1.legend(market_categories + ['total'])
    label_xyt(ax1, 'Year', 'CO2e [Mg]',
              '%s\nVehicle CO2e Mg by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(omega_globals.options.output_folder + '%s V Mg Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        Mg_data[mc] = []
        for cy in calendar_years:
            Mg_data[mc].append(omega_globals.session.query(
                func.sum(VehicleFinal.cert_co2e_Mg)).
                               filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id).
                               filter(VehicleFinal.model_year == cy).
                               filter(VehicleFinal.market_class_id == mc).
                               filter(VehicleAnnualData.age == 0).scalar())

        if 'ICE' in mc:
            ax1.plot(calendar_years, Mg_data[mc], '.-')
        else:
            ax1.plot(calendar_years, Mg_data[mc], '.--')
    ax1.plot(calendar_years, Mg_data['total'], '.-')
    label_xyt(ax1, 'Year', 'CO2e [Mg]',
              '%s\nVehicle CO2e Mg  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes + ['total'])
    fig.savefig(omega_globals.options.output_folder + '%s V Mg Mkt Cls.png' % omega_globals.options.session_unique_name)
    return Mg_data


def plot_market_shares(calendar_years, total_sales):
    """
    Plot absolute market shares v. model year, by market class, market category, context size class and reg class.

    Args:
        calendar_years ([years]): list of model years
        total_sales ([sales]): list of total sales by model year

    Returns:
        dict of market share results, by market class, market category, context size class and reg class.

    """
    from context.new_vehicle_market import NewVehicleMarket
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal

    market_share_results = dict()

    # tally up market_category sales
    for mcat in market_categories:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                         VehicleFinal.market_class_id) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            count = 0
            for result in registered_count_and_market_id:
                if mcat in result.market_class_id.split('.'):
                    count += result.registered_count
            market_category_abs_share_frac.append(float(count) / total_sales[idx])

        market_share_results['abs_share_frac_%s' % mcat] = market_category_abs_share_frac

    # tally up market class sales
    for mc in market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            mc_sales = omega_globals.session.query(func.sum(VehicleAnnualData.registered_count)) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.market_class_id == mc) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).scalar()
            if not mc_sales:
                mc_sales = 0
            market_category_abs_share_frac.append(float(mc_sales) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % mc] = market_category_abs_share_frac

    # tally up context size class sales
    for csc in NewVehicleMarket.context_size_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            csc_sales = omega_globals.session.query(func.sum(VehicleAnnualData.registered_count)) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.context_size_class == csc) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).scalar()
            if not csc_sales:
                csc_sales = 0
            market_category_abs_share_frac.append(float(csc_sales) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % csc] = market_category_abs_share_frac

    # tally up reg class sales
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            rc_sales = omega_globals.session.query(func.sum(VehicleAnnualData.registered_count)) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.reg_class_id == rc) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).scalar()
            if not rc_sales:
                rc_sales = 0
            market_category_abs_share_frac.append(float(rc_sales) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % rc] = market_category_abs_share_frac

    # plot market category results
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % mcat], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nMarket Category Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(market_categories)
    fig.savefig(
        omega_globals.options.output_folder + '%s Mkt Cat Shares.png' % omega_globals.options.session_unique_name)

    # plot market class results
    fig, ax1 = figure()
    for mc in market_classes:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % mc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nMarket Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s Mkt Cls Shares.png' % omega_globals.options.session_unique_name)

    # plot context size class results
    fig, ax1 = figure()
    for csc in NewVehicleMarket.context_size_classes:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % csc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nContext Size Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(NewVehicleMarket.context_size_classes.keys(), ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s CSC Shares.png' % omega_globals.options.session_unique_name)

    # plot reg class results
    fig, ax1 = figure()
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % rc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nReg Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(omega_globals.options.RegulatoryClasses.reg_classes, ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s RC Shares.png' % omega_globals.options.session_unique_name)

    return market_share_results


def plot_manufacturer_market_shares(calendar_years, compliance_id, total_sales):
    """
    Plot absolute market shares v. model year, by market class, market category, context size class and reg class,
    for a single manufacturer.

    Args:
        calendar_years ([years]): list of model years
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        total_sales ([sales]): list of total sales by model year

    Returns:
        dict of market share results, by market class, market category, context size class and reg class, for the given
        manufacturer

    """
    from context.new_vehicle_market import NewVehicleMarket
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal

    market_share_results = dict()

    # tally up market_category sales
    for mcat in market_categories:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            registered_count_and_market_id = omega_globals.session.query(VehicleAnnualData.registered_count,
                                                                         VehicleFinal.market_class_id) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.compliance_id == compliance_id) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).all()
            count = 0
            for result in registered_count_and_market_id:
                if mcat in result.market_class_id.split('.'):
                    count += result.registered_count
            market_category_abs_share_frac.append(float(count) / total_sales[idx])

        market_share_results['%s_abs_share_frac_%s' % (compliance_id, mcat)] = market_category_abs_share_frac

    # tally up market class sales
    for mc in market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            mc_sales = omega_globals.session.query(func.sum(VehicleAnnualData.registered_count)) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.compliance_id == compliance_id) \
                .filter(VehicleFinal.market_class_id == mc) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).scalar()
            if not mc_sales:
                mc_sales = 0
            market_category_abs_share_frac.append(float(mc_sales) / total_sales[idx])
        market_share_results['%s_abs_share_frac_%s' % (compliance_id, mc)] = market_category_abs_share_frac

    # tally up context size class sales
    for csc in NewVehicleMarket.context_size_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            csc_sales = omega_globals.session.query(func.sum(VehicleAnnualData.registered_count)) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.compliance_id == compliance_id) \
                .filter(VehicleFinal.context_size_class == csc) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).scalar()
            if not csc_sales:
                csc_sales = 0
            market_category_abs_share_frac.append(float(csc_sales) / total_sales[idx])
        market_share_results['%s_abs_share_frac_%s' % (compliance_id, csc)] = market_category_abs_share_frac

    # tally up reg class sales
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            rc_sales = omega_globals.session.query(func.sum(VehicleAnnualData.registered_count)) \
                .filter(VehicleAnnualData.vehicle_id == VehicleFinal.vehicle_id) \
                .filter(VehicleFinal.compliance_id == compliance_id) \
                .filter(VehicleFinal.reg_class_id == rc) \
                .filter(VehicleAnnualData.calendar_year == cy) \
                .filter(VehicleAnnualData.age == 0).scalar()
            if not rc_sales:
                rc_sales = 0
            market_category_abs_share_frac.append(float(rc_sales) / total_sales[idx])
        market_share_results['%s_abs_share_frac_%s' % (compliance_id, rc)] = market_category_abs_share_frac

    # plot market category results
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, market_share_results['%s_abs_share_frac_%s' % (compliance_id, mcat)], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nMarket Category Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(market_categories)
    fig.savefig(omega_globals.options.output_folder + '%s Mkt Cat Shares %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # plot market class results
    fig, ax1 = figure()
    for mc in market_classes:
        ax1.plot(calendar_years, market_share_results['%s_abs_share_frac_%s' % (compliance_id, mc)], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nMarket Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(market_classes)
    fig.savefig(omega_globals.options.output_folder + '%s Mkt Cls Shares %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # plot context size class results
    fig, ax1 = figure()
    for csc in NewVehicleMarket.context_size_classes:
        ax1.plot(calendar_years, market_share_results['%s_abs_share_frac_%s' % (compliance_id, csc)], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nContext Size Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(NewVehicleMarket.context_size_classes.keys(), ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s CSC Shares %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # plot reg class results
    fig, ax1 = figure()
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        ax1.plot(calendar_years, market_share_results['%s_abs_share_frac_%s' % (compliance_id, rc)], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nReg Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(omega_globals.options.RegulatoryClasses.reg_classes, ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s RC Shares %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    return market_share_results


def plot_total_sales(calendar_years, compliance_ids):
    """
    Plot vehicle sales v. model year, for all manufacturers.

    Args:
        compliance_ids ([strs]): list of manufacturer names, e.g. ['OEM_A', 'OEM_B', ...]
        calendar_years ([years]): list of model years

    Returns:
        tuple of context sales, total sales, and manufacturer sales by model year
        (context_sales, total_sales, manufacturer_sales)

    """
    import numpy as np
    import consumer
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import VehicleFinal

    total_sales = []
    for cy in calendar_years:
        total_sales.append(float(omega_globals.session.query(func.sum(VehicleAnnualData.registered_count))
                                 .filter(VehicleAnnualData.calendar_year == cy)
                                 .filter(VehicleAnnualData.age == 0).scalar()))
    total_sales = np.array(total_sales)

    manufacturer_sales = dict()
    for compliance_id in compliance_ids:
        manufacturer_sales[compliance_id] = []
        for cy in calendar_years:
            manufacturer_sales[compliance_id].append(
                float(omega_globals.session.query(func.sum(VehicleAnnualData.registered_count))
                      .filter(VehicleFinal.vehicle_id == VehicleAnnualData.vehicle_id)
                      .filter(VehicleFinal.compliance_id == compliance_id)
                      .filter(VehicleAnnualData.calendar_year == cy)
                      .filter(VehicleAnnualData.age == 0).scalar()))

    context_sales = np.array(
        [consumer.sales_volume.context_new_vehicle_sales(cy)['total'] for cy in calendar_years[1:]])
    fig, ax1 = fplothg(calendar_years[1:], context_sales / 1e6, '.-')
    ax1.plot(calendar_years, total_sales / 1e6)

    for manufacturer in manufacturer_sales:
        ax1.plot(calendar_years, np.array(manufacturer_sales[manufacturer]) / 1e6)

    ax1.legend(['context sales', 'sales'] + list(manufacturer_sales.keys()))
    label_xyt(ax1, 'Year', 'Sales [millions]', '%s\nTotal Sales Versus Calendar Year\n Total Sales %.2f Million' % (
        omega_globals.options.session_unique_name, total_sales.sum() / 1e6))

    fig.savefig(omega_globals.options.output_folder + '%s Sales v Year.png' % omega_globals.options.session_unique_name)

    return context_sales, total_sales, manufacturer_sales


def plot_manufacturer_compliance(calendar_years, compliance_id, credit_history):
    """
    Plot manufacturer initial and final cert CO2e Mg, including the effect of credit transfers.

    Args:
        credit_history (CreditBank):
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        calendar_years ([years]): list of model years

    Returns:
        tuple of calendar year cert co2e Mg, model year cert co2e Mg, cert target co2e Mg, total cost in billions
        (calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, cert_target_co2e_Mg, total_cost_billions)

    """
    def draw_transfer_arrow(src_x, src_y, dest_x, dest_y):
        ax1.annotate('', xy=(dest_x, dest_y), xycoords='data',
                     xytext=(src_x, src_y), textcoords='data',
                     arrowprops=dict(arrowstyle='-|>', color='green', shrinkA=2, shrinkB=2,
                                     patchA=None, patchB=None, connectionstyle="arc3,rad=1"))

    def draw_expiration_arrow(src_x, src_y):
        ax1.annotate('', xy=(src_x, src_y), xycoords='data',
                     xytext=(src_x, ax1.get_ylim()[0]), textcoords='data',
                     arrowprops=dict(arrowstyle='<-', color='red', shrinkA=5, shrinkB=5,
                                     patchA=None, patchB=None, connectionstyle="arc3,rad=0"))

    from producer.manufacturer_annual_data import ManufacturerAnnualData

    cert_target_co2e_Mg = ManufacturerAnnualData.get_cert_target_co2e_Mg(compliance_id)
    calendar_year_cert_co2e_Mg = ManufacturerAnnualData.get_calendar_year_cert_co2e_Mg(compliance_id)
    model_year_cert_co2e_Mg = ManufacturerAnnualData.get_model_year_cert_co2e_Mg(compliance_id)
    total_cost_billions = ManufacturerAnnualData.get_total_cost_billions(compliance_id)
    # compliance chart
    fig, ax1 = fplothg(calendar_years, cert_target_co2e_Mg, 'o-')
    ax1.plot(calendar_years, calendar_year_cert_co2e_Mg, 'r.-')
    ax1.plot(calendar_years, model_year_cert_co2e_Mg, '-')
    ax1.legend(['cert_target_co2e_Mg', 'calendar_year_cert_co2e_Mg', 'model_year_cert_co2e_Mg'])
    label_xyt(ax1, 'Year', 'CO2e [Mg]', '%s %s\nCert and Compliance Versus Year\n Total Cost $%.2f Billion' % (
        compliance_id, omega_globals.options.session_unique_name, total_cost_billions))

    cert_target_co2e_Mg_dict = dict(zip(calendar_years, cert_target_co2e_Mg))
    calendar_year_cert_co2e_Mg_dict = dict(zip(calendar_years, calendar_year_cert_co2e_Mg))
    model_year_cert_co2e_Mg_dict = dict(zip(calendar_years, model_year_cert_co2e_Mg))

    for _, t in credit_history.transaction_log.iterrows():
        if type(t.credit_destination) is not str and t.model_year in calendar_year_cert_co2e_Mg_dict:
            draw_transfer_arrow(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year],
                                t.credit_destination, cert_target_co2e_Mg_dict[t.credit_destination])
        elif type(t.credit_destination) is not str and t.model_year not in calendar_year_cert_co2e_Mg_dict:
            ax1.plot(t.model_year, cert_target_co2e_Mg_dict[calendar_years[0]], 'o', color='orange')
            draw_transfer_arrow(t.model_year, cert_target_co2e_Mg_dict[calendar_years[0]],
                                t.credit_destination, model_year_cert_co2e_Mg_dict[t.credit_destination])
            ax1.set_xlim(calendar_years[0] - 5, ax1.get_xlim()[1])
        elif t.credit_destination == 'EXPIRATION' and t.model_year in calendar_year_cert_co2e_Mg_dict:
            draw_expiration_arrow(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year])
        elif t.credit_destination == 'EXPIRATION' and t.model_year not in calendar_year_cert_co2e_Mg_dict:
            ax1.plot(t.model_year, cert_target_co2e_Mg_dict[calendar_years[0]], 'o', color='orange')
            draw_expiration_arrow(t.model_year, cert_target_co2e_Mg_dict[calendar_years[0]])
        else:  # "PAST_DUE"
            ax1.plot(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], 'x', color='red')
            plt.scatter(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], s=80, facecolors='none',
                        edgecolors='r')

    fig.savefig(omega_globals.options.output_folder + '%s Cert Mg v Year %s.png' %
                (omega_globals.options.session_unique_name, compliance_id))

    return calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, cert_target_co2e_Mg, total_cost_billions


def plot_iteration(iteration_log, compliance_id):
    """
    Plot producer-consumer iteration data.

    Args:
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        iteration_log (DataFrame): iteration data

    """
    iteration_log = iteration_log.loc[iteration_log['compliance_id'] == compliance_id]

    for iteration in [0, -1]:
        year_iter_labels = ['%d_%d' % (cy - 2000, it) for cy, it in
                            zip(iteration_log['calendar_year'][
                                    iteration_log['cross_subsidy_iteration_num'] == iteration],
                                iteration_log['producer_consumer_iteration_num'][iteration_log['cross_subsidy_iteration_num'] == iteration])]

        for mc in market_classes:
            plt.figure()
            plt.plot(year_iter_labels,
                     iteration_log['producer_abs_share_frac_%s' % mc][
                         iteration_log['cross_subsidy_iteration_num'] == iteration])
            plt.xticks(rotation=90)
            plt.plot(year_iter_labels,
                     iteration_log['consumer_abs_share_frac_%s' % mc][
                         iteration_log['cross_subsidy_iteration_num'] == iteration])
            plt.title('%s %s iteration %d' % (compliance_id, mc, iteration))
            plt.grid()
            plt.legend(['producer_abs_share_frac_%s' % mc, 'consumer_abs_share_frac_%s' % mc])
            # plt.ylim([0, 1])
            plt.savefig('%s%s %s Iter %s %s.png' % (
                omega_globals.options.output_folder, omega_globals.options.session_unique_name, compliance_id,
                mc, iteration))

        first_logged = iteration_log.drop_duplicates('calendar_year', keep='first')
        last_logged = iteration_log.drop_duplicates('calendar_year', keep='last')

        plt.figure()
        if iteration == -1:
            for mc in market_classes:
                plt.plot(last_logged['calendar_year'],
                         last_logged['consumer_generalized_cost_dollars_%s' % mc], '.-')
        else:
            for mc in market_classes:
                plt.plot(first_logged['calendar_year'],
                         first_logged['consumer_generalized_cost_dollars_%s' % mc], '.-')
        plt.legend(['consumer_generalized_cost_dollars_%s' % mc for mc in market_classes])
        plt.ylabel('Cost $ / mi')
        plt.title('%s Consumer Generalized Cost %d' % (compliance_id, iteration))
        plt.grid()
        plt.savefig('%s%s %s ConsumerGC %s.png' % (omega_globals.options.output_folder,
                                                   omega_globals.options.session_unique_name, compliance_id, iteration))

        plt.figure()
        if iteration == -1:
            for mc in market_classes:
                plt.plot(last_logged['calendar_year'],
                         last_logged['cost_multiplier_%s' % mc], '.-')
        else:
            for mc in market_classes:
                plt.plot(first_logged['calendar_year'],
                         first_logged['cost_multiplier_%s' % mc], '.-')
        plt.legend(['cost_multiplier_%s' % mc for mc in market_classes])
        plt.ylabel('Cost Multiplier')
        plt.title('%s Producer Cost Multipliers %d' % (compliance_id, iteration))
        plt.grid()
        plt.savefig('%s%s %s Producer Cost Multipliers %d.png' % (
            omega_globals.options.output_folder, omega_globals.options.session_unique_name, compliance_id, iteration))

    fig, ax1 = fplothg(last_logged['calendar_year'], last_logged['producer_consumer_iteration_num'], '.-')
    label_xyt(ax1, '', 'Iteration [#]', '%s Iteration mean = %.2f' % (compliance_id, last_logged['producer_consumer_iteration_num'].mean()))

    fig.savefig('%s%s %s Iter Counts.png' % (omega_globals.options.output_folder,
                                             omega_globals.options.session_unique_name, compliance_id))

    # plot producer initial share and g/mi decisions
    plt.figure()
    for mc in market_classes:
        plt.plot(first_logged['calendar_year'], first_logged['producer_abs_share_frac_%s' % mc], '.-')
    plt.title('%s Producer Initial Absolute Market Shares' % compliance_id)
    plt.grid()
    plt.legend(['producer_abs_share_frac_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer Initial Abs Shares.png' % (omega_globals.options.output_folder,
                                                             omega_globals.options.session_unique_name, compliance_id))

    plt.figure()
    for mc in market_classes:
        plt.plot(first_logged['calendar_year'], first_logged['average_co2e_gpmi_%s' % mc], '.-')
    plt.title('%s Producer Initial CO2e g/mi' % compliance_id)
    plt.grid()
    plt.legend(['average_co2e_gpmi_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer Initial CO2e gpmi.png' % (omega_globals.options.output_folder,
                                                            omega_globals.options.session_unique_name, compliance_id))
