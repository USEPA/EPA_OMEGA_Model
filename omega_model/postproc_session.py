"""

post-compliance-modeling output generation (charts, summary files, etc)


----

**CODE**

"""
import effects.omega_effects
from omega_model import *
from common.omega_plot import *
from policy.credit_banking import CreditBank
from producer.vehicle_annual_data import VehicleAnnualData
import consumer

market_classes = []
market_categories = []

vehicle_data = None
vehicle_annual_data = None


def run_postproc(iteration_log, credit_banks):
    """
    Generate charts and output files for a single simulation

    Args:
        iteration_log (DataFrame): dataframe storing information on producer-consumer iteration
        credit_banks (dict of CreditBanks): credit banking information per compliance_id

    Returns:
        Results summary DataFrame

    """
    from producer.vehicles import VehicleFinal
    from effects.omega_effects import run_effects_calcs
    from omega_model.input_files import InputFiles
    import pandas as pd
    global vehicle_data, vehicle_annual_data

    global market_classes, market_categories
    market_classes = omega_globals.options.MarketClass.market_classes
    market_categories = omega_globals.options.MarketClass.market_categories

    # this runs tech_tracking always and physical/cost effects based on globals.options:
    tech_tracking_df, physical_effects_df, cost_effects_df, present_and_annualized_cost_df = run_effects_calcs()

    if not omega_globals.options.standalone_run:
        omega_log.logwrite('%s: Post Processing ...' % omega_globals.options.session_name)

    vehicle_years = list(range(omega_globals.options.analysis_initial_year - 1,
                               omega_globals.options.analysis_final_year + 1))

    # collect vehicle data in one database hit then filter it later
    vehicle_data = omega_globals.session.query(VehicleFinal.vehicle_id, VehicleFinal.model_year,
                                               VehicleFinal.market_class_id, VehicleFinal.context_size_class,
                                               VehicleFinal.reg_class_id, VehicleFinal.cert_co2e_Mg,
                                               VehicleFinal.new_vehicle_mfr_generalized_cost_dollars,
                                               VehicleFinal.new_vehicle_mfr_cost_dollars,
                                               VehicleFinal.target_co2e_grams_per_mile,
                                               VehicleFinal.cert_co2e_grams_per_mile,
                                               VehicleFinal.cert_direct_kwh_per_mile,
                                               VehicleFinal.lifetime_VMT, VehicleFinal.compliance_id).all()

    # index vehicle annual data by vehicle id and age for quick access
    vehicle_annual_data_df = pd.DataFrame(VehicleAnnualData._data).set_index(['vehicle_id', 'age'])
    vehicle_annual_data = vehicle_annual_data_df.to_dict(orient='index')

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

            calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, target_co2e_Mg = \
                plot_manufacturer_compliance(analysis_years, compliance_id, credit_banks[compliance_id])

            session_results['%s_target_co2e_Mg' % compliance_id] = target_co2e_Mg
            session_results['%s_calendar_year_cert_co2e_Mg' % compliance_id] = calendar_year_cert_co2e_Mg
            session_results['%s_model_year_cert_co2e_Mg' % compliance_id] = model_year_cert_co2e_Mg

            plot_iteration(iteration_log, compliance_id)

            if not omega_globals.options.consolidate_manufacturers:

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

    physical_effects = plot_effects(analysis_years, physical_effects_df)

    # market share results include base year data, but the rest of the data doesn't, so drop the
    # base year data, otherwise the dataframe at the end will fail due to inconsistent column lengths

    for msr in market_share_results:
        session_results[msr] = market_share_results[msr] = market_share_results[msr][1:]

    for cat in market_categories + market_classes + ['vehicle']:
        session_results['average_%s_cost' % cat] = average_cost_data[cat]
        session_results['average_%s_generalized_cost' % cat] = average_generalized_cost_data[cat]
        session_results['average_%s_cert_co2e_gpmi' % cat] = average_cert_co2e_gpmi_data[cat]
        session_results['average_%s_cert_direct_kwh_pmi' % cat] = average_cert_direct_kwh_pmi_data[cat]
        session_results['average_%s_target_co2e_gpmi' % cat] = average_target_co2e_gpmi_data[cat]
        session_results['%s_co2e_Mg' % cat] = megagrams_data[cat]

    session_results['total_vehicle_cost_billions'] = \
        session_results['average_vehicle_cost'] * session_results['sales_total'] / 1e9

    for k in physical_effects:
        session_results[k] = physical_effects[k]

    # write output files
    summary_filename = omega_globals.options.output_folder + omega_globals.options.session_unique_name \
                       + '_summary_results.csv'

    session_results.to_csv(summary_filename, index=False)

    dump_table_to_csv(omega_globals.options.output_folder, 'vehicles',
                      omega_globals.options.session_unique_name + '_vehicles',
                      omega_globals.options.verbose)

    vehicle_annual_data_df.to_csv(omega_globals.options.output_folder + omega_globals.options.session_unique_name
                                  + '_vehicle_annual_data.csv')

    dump_table_to_csv(omega_globals.options.output_folder, 'manufacturer_annual_data',
                      omega_globals.options.session_unique_name + '_manufacturer_annual_data',
                      omega_globals.options.verbose)

    input_files_df = pd.DataFrame.from_dict(InputFiles._data).transpose()
    input_files_df.to_csv(
        omega_globals.options.output_folder + omega_globals.options.session_unique_name + '_input_file_log.csv',
        index=False)


def plot_effects(calendar_years, physical_effects_df):
    """
    Plot physical effects and aggregate vehicle stock data by calendar year.
    
    Args:
        calendar_years ([years]): list of calendar years
        physical_effects_df (DataFrame): contains physical effects data

    Returns:
        dict of physical effects data for the vehicle stock aggregated by calendar year

    """


    physical_effects = dict()

    if not physical_effects_df.empty:
        physical_effects['vehicle_stock_CO2_megagrams'] = []
        physical_effects['vehicle_stock_consumption_gasoline_gallons'] = []
        physical_effects['vehicle_stock_consumption_kwh'] = []
        physical_effects['vehicle_stock_vmt'] = []
        physical_effects['registered_count'] = []

        for cy in calendar_years:
            physical_effects['vehicle_stock_CO2_megagrams'].append(
                physical_effects_df['co2_total_metrictons'].loc[physical_effects_df['calendar_year'] == cy].sum())
            physical_effects['vehicle_stock_consumption_gasoline_gallons'].append(
                physical_effects_df['fuel_consumption_gallons'].loc[physical_effects_df['calendar_year'] == cy].sum())
            physical_effects['vehicle_stock_consumption_kwh'].append(
                physical_effects_df['fuel_consumption_kWh'].loc[physical_effects_df['calendar_year'] == cy].sum())
            physical_effects['vehicle_stock_vmt'].append(
                physical_effects_df['vmt'].loc[physical_effects_df['calendar_year'] == cy].sum())
            physical_effects['registered_count'].append(
                physical_effects_df['registered_count'].loc[physical_effects_df['calendar_year'] == cy].sum())

        fig, ax1 = figure()
        ax1.plot(calendar_years, physical_effects['vehicle_stock_CO2_megagrams'], '.-')
        ax1.legend(['Vehicle Stock CO2 Mg'])
        label_xyt(ax1, 'Year', 'CO2 [Mg]', '%s\nVehicle Stock CO2 Mg' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s Stock CO2 Mg.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure()
        ax1.plot(calendar_years, physical_effects['vehicle_stock_consumption_gasoline_gallons'], '.-')
        ax1.legend(['Vehicle Stock Fuel Consumption Gallons'])
        label_xyt(ax1, 'Year', 'Fuel Consumption [Gasoline gallons]', '%s\nVehicle Stock Fuel Consumption Gasoline Gallons' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s Stock Gas Gallons.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure()
        ax1.plot(calendar_years, physical_effects['vehicle_stock_consumption_kwh'], '.-')
        ax1.legend(['Vehicle Stock Fuel Consumption kWh'])
        label_xyt(ax1, 'Year', 'Consumption [kWh]', '%s\nVehicle Stock Fuel Consumption kWh' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s Stock kWh.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure()
        ax1.plot(calendar_years, physical_effects['vehicle_stock_vmt'], '.-')
        ax1.legend(['Vehicle Stock Miles Travelled'])
        label_xyt(ax1, 'Year', 'Distance Travelled [miles]', '%s\nVehicle Stock Miles Travelled' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s Stock VMT.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure()
        ax1.plot(calendar_years, np.array(physical_effects['registered_count']) / 1e6, '.-')
        ax1.legend(['Vehicle Stock Registered Count'])
        label_xyt(ax1, 'Year', 'Registered Count [millions]', '%s\nVehicle Stock Registered Count' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s Stock Count.png'
                    % omega_globals.options.session_unique_name)

    return physical_effects


def plot_cert_co2e_gpmi(calendar_years):
    """
    Plot cert CO2e g/mi versus model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average cert co2e g/mi data by total, market class and market category

    """
    co2e_data = dict()

    co2e_data['vehicle'] = []
    for cy in calendar_years:
        weighted_value = 0
        count = 0
        vehicle_id_and_vmt_and_co2gpmi = [(v.vehicle_id, v.lifetime_VMT, v.cert_co2e_grams_per_mile) for v in vehicle_data if v.model_year == cy]

        for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
            weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt * co2gpmi
            count += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt

        co2e_data['vehicle'].append(weighted_value / count)

    # tally up market_category sales- and VMT- weighted co2
    for mcat in market_categories:
        market_category_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi_market_class_id = \
                [(v.vehicle_id, v.lifetime_VMT, v.cert_co2e_grams_per_mile, v.market_class_id) for v in
                 vehicle_data if v.model_year == cy]

            for vehicle_id, lifetime_vmt, co2gpmi, market_class_id in vehicle_id_and_vmt_and_co2gpmi_market_class_id:
                if mcat in market_class_id.split('.'):
                    weighted_value += \
                        vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt * co2gpmi
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt

            market_category_co2e.append(weighted_value / count)

        co2e_data[mcat] = market_category_co2e

    # tally up market_class sales- and VMT- weighted co2
    for mc in market_classes:
        market_class_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi = \
                [(v.vehicle_id, v.lifetime_VMT, v.cert_co2e_grams_per_mile) for v in
                 vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
                weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt * co2gpmi
                count += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt

            market_class_co2e.append(weighted_value / count)

        co2e_data[mc] = market_class_co2e

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, co2e_data[mcat], '.--')
    ax1.plot(calendar_years, co2e_data['vehicle'], '.-')
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert CO2e g/mi by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert CO2e gpmi Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        if 'ICE' in mc:
            ax1.plot(calendar_years, co2e_data[mc], '.-')
        else:
            ax1.plot(calendar_years, co2e_data[mc], '.--')

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert CO2e g/mi  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert CO2e gpmi Mkt Cls.png' % omega_globals.options.session_unique_name)

    return co2e_data


def plot_cert_direct_kwh_pmi(calendar_years):
    """
    Plot vehicle cert direct kWh/mi v. model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average cert direct kWh/mi data by total, market class and market category

    """
    average_cert_direct_kwh_data = dict()

    # tally up total sales weighted kWh
    average_cert_direct_kwh_data['vehicle'] = []
    for cy in calendar_years:
        weighted_value = 0
        count = 0
        vehicle_id_and_kwh = [(v.vehicle_id, v.cert_direct_kwh_per_mile) for v in vehicle_data if v.model_year == cy]

        for vehicle_id, kwh in vehicle_id_and_kwh:
            weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * kwh
            count += vehicle_annual_data[vehicle_id, 0]['registered_count']

        average_cert_direct_kwh_data['vehicle'].append(weighted_value / count)

    # tally up market_category sales weighted kWh
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_value = 0
            count = 0

            vehicle_id_and_market_class_id_and_kwh = \
                [(v.vehicle_id, v.market_class_id, v.cert_direct_kwh_per_mile) for v in vehicle_data if v.model_year == cy]

            for vehicle_id, market_class_id, kwh in vehicle_id_and_market_class_id_and_kwh:
                if mcat in market_class_id.split('.'):
                    weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * kwh
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_cost.append(weighted_value / count)

        average_cert_direct_kwh_data[mcat] = market_category_cost

    # tally up market_class sales weighted kWh
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_value = 0
            count = 0

            vehicle_id_and_kwh = \
                [(v.vehicle_id, v.cert_direct_kwh_per_mile) for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, kwh in vehicle_id_and_kwh:
                weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * kwh
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_class_cost.append(weighted_value / count)

        average_cert_direct_kwh_data[mc] = market_class_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cert_direct_kwh_data[mcat], '.--')
    ax1.plot(calendar_years, average_cert_direct_kwh_data['vehicle'], '.-')
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cert kWh pmi Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
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
    Plot cert CO2e g/mi versus model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average cert co2e g/mi data by total, market class and market category

    """
    co2e_data = dict()

    co2e_data['vehicle'] = []
    for cy in calendar_years:
        weighted_value = 0
        count = 0
        vehicle_id_and_vmt_and_co2gpmi = [(v.vehicle_id, v.lifetime_VMT, v.target_co2e_grams_per_mile) for v in
                                          vehicle_data if v.model_year == cy]

        for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
            weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt * co2gpmi
            count += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt

        co2e_data['vehicle'].append(weighted_value / count)

    # tally up market_category sales- and VMT- weighted co2
    for mcat in market_categories:
        market_category_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi_market_class_id = \
                [(v.vehicle_id, v.lifetime_VMT, v.target_co2e_grams_per_mile, v.market_class_id) for v in
                 vehicle_data if v.model_year == cy]

            for vehicle_id, lifetime_vmt, co2gpmi, market_class_id in vehicle_id_and_vmt_and_co2gpmi_market_class_id:
                if mcat in market_class_id.split('.'):
                    weighted_value += \
                        vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt * co2gpmi
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt

            market_category_co2e.append(weighted_value / count)

        co2e_data[mcat] = market_category_co2e

    # tally up market_class sales- and VMT- weighted co2
    for mc in market_classes:
        market_class_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi = \
                [(v.vehicle_id, v.lifetime_VMT, v.target_co2e_grams_per_mile) for v in
                 vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
                weighted_value += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt * co2gpmi
                count += vehicle_annual_data[vehicle_id, 0]['registered_count'] * lifetime_vmt

            market_class_co2e.append(weighted_value / count)

        co2e_data[mc] = market_class_co2e

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, co2e_data[mcat], '.--')
    ax1.plot(calendar_years, co2e_data['vehicle'], '.-')
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Target CO2e g/mi by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Target CO2e gpmi Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        if 'ICE' in mc:
            ax1.plot(calendar_years, co2e_data[mc], '.-')
        else:
            ax1.plot(calendar_years, co2e_data[mc], '.--')

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Target CO2e g/mi  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Target CO2e gpmi Mkt Cls.png' % omega_globals.options.session_unique_name)

    return co2e_data


def plot_vehicle_cost(calendar_years):
    """
    Plot average vehicle cost v. model year, by market class and market category, across all manufacturers.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average vehicle cost data by total, market class and market category

    """
    average_cost_data = dict()

    # tally up total sales weighted cost
    average_cost_data['vehicle'] = []
    for cy in calendar_years:
        weighted_cost = 0
        count = 0
        vehicle_id_and_cost = [(v.vehicle_id, v.new_vehicle_mfr_cost_dollars) for v in vehicle_data if
                               v.model_year == cy]
        for vehicle_id, cost in vehicle_id_and_cost:
            weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
            count += vehicle_annual_data[vehicle_id, 0]['registered_count']

        average_cost_data['vehicle'].append(weighted_cost / count)

    # tally up market_category costs
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0
            vehicle_id_and_market_class_id_and_cost = \
                [(v.vehicle_id, v.market_class_id, v.new_vehicle_mfr_cost_dollars) for v in vehicle_data if v.model_year == cy]

            for vehicle_id, market_class_id, cost in vehicle_id_and_market_class_id_and_cost:
                if mcat in market_class_id.split('.'):
                    weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_cost.append(weighted_cost / count)

        average_cost_data[mcat] = market_category_cost

    # tally up market_class costs
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0
            vehicle_id_and_cost = [(v.vehicle_id, v.new_vehicle_mfr_cost_dollars) for v in vehicle_data if
                                   v.model_year == cy and v.market_class_id == mc]
            for vehicle_id, cost in vehicle_id_and_cost:
                weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_class_cost.append(weighted_cost / count)

        average_cost_data[mc] = market_class_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cost_data[mcat], '.--')
    ax1.plot(calendar_years, average_cost_data['vehicle'], '.-')
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cost Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        if 'ICE' in mc:
            ax1.plot(calendar_years, average_cost_data[mc], '.-')
        else:
            ax1.plot(calendar_years, average_cost_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost  by Market Class v Year' % omega_globals.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V Cost Mkt Cls.png' % omega_globals.options.session_unique_name)

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
    cost_data = dict()

    # tally up total sales weighted cost
    cost_data['%s_total' % compliance_id] = []
    for cy in calendar_years:
        weighted_cost = 0
        count = 0
        vehicle_id_and_cost = [(v.vehicle_id, v.new_vehicle_mfr_cost_dollars) for v in vehicle_data
                               if v.model_year == cy and v.compliance_id == compliance_id]

        for vehicle_id, cost in vehicle_id_and_cost:
            weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
            count += vehicle_annual_data[vehicle_id, 0]['registered_count']

        cost_data['%s_total' % compliance_id].append(weighted_cost / count)

    # tally up market_category costs
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_market_class_id_and_cost = \
                [(v.vehicle_id, v.market_class_id, v.new_vehicle_mfr_cost_dollars) for v in vehicle_data
                 if v.model_year == cy and v.compliance_id == compliance_id]

            for vehicle_id, market_class_id, cost in vehicle_id_and_market_class_id_and_cost:
                if mcat in market_class_id.split('.'):
                    weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_cost.append(weighted_cost / count)

        cost_data['%s_%s' % (compliance_id, mcat)] = market_category_cost

    # tally up market_class costs
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_cost = \
                [(v.vehicle_id, v.new_vehicle_mfr_cost_dollars) for v in vehicle_data if v.model_year == cy
                 and v.market_class_id == mc and v.compliance_id == compliance_id]

            for vehicle_id, cost in vehicle_id_and_cost:
                weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_class_cost.append(weighted_cost / count)

        cost_data['%s_%s' % (compliance_id, mc)] = market_class_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, cost_data['%s_%s' % (compliance_id, mcat)], '.--')
    ax1.plot(calendar_years, cost_data['%s_total' % compliance_id], '.-')
    ax1.legend(market_categories + ['%s_total' % compliance_id])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s %s\nAverage Vehicle Cost by Market Category v Year' %
              (compliance_id, omega_globals.options.session_unique_name))
    fig.savefig(omega_globals.options.output_folder + '%s V Cost Mkt Cat %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        if 'ICE' in mc:
            ax1.plot(calendar_years, cost_data['%s_%s' % (compliance_id, mc)], '.-')
        else:
            ax1.plot(calendar_years, cost_data['%s_%s' % (compliance_id, mc)], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s %s\nAverage Vehicle Cost  by Market Class v Year'
              % (compliance_id, omega_globals.options.session_unique_name))
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(omega_globals.options.output_folder + '%s V Cost Mkt Cls %s.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    return cost_data


def plot_vehicle_generalized_cost(calendar_years):
    """
    Plot manufacturer vehicle generalized cost v. model year, by market class and market category,
    for a single manufacturer.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of average generalized cost data by total, market class and market category

    """
    cost_data = dict()

    # tally up total sales weighted cost
    cost_data['vehicle'] = []
    for cy in calendar_years:
        weighted_cost = 0
        count = 0
        vehicle_id_and_cost = [(v.vehicle_id, v.new_vehicle_mfr_generalized_cost_dollars) for v in vehicle_data if v.model_year == cy]

        for vehicle_id, cost in vehicle_id_and_cost:
            weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
            count += vehicle_annual_data[vehicle_id, 0]['registered_count']

        cost_data['vehicle'].append(weighted_cost / count)

    # tally up market_category costs
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_market_class_id_and_cost = \
                [(v.vehicle_id, v.market_class_id, v.new_vehicle_mfr_generalized_cost_dollars) for v in vehicle_data if v.model_year == cy]

            for vehicle_id, market_class_id, cost in vehicle_id_and_market_class_id_and_cost:
                if mcat in market_class_id.split('.'):
                    weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_cost.append(weighted_cost / count)

        cost_data[mcat] = market_category_cost

    # tally up market_class costs
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_cost = \
                [(v.vehicle_id, v.new_vehicle_mfr_generalized_cost_dollars) for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, cost in vehicle_id_and_cost:
                weighted_cost += vehicle_annual_data[vehicle_id, 0]['registered_count'] * cost
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_class_cost.append(weighted_cost / count)

        cost_data[mc] = market_class_cost

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, cost_data[mcat], '.--')
    ax1.plot(calendar_years, cost_data['vehicle'], '.-')
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized Cost by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s V GenCost Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        if 'ICE' in mc:
            ax1.plot(calendar_years, cost_data[mc], '.-')
        else:
            ax1.plot(calendar_years, cost_data[mc], '.--')

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized_Cost  by Market Class v Year' % omega_globals.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s V GenCost Mkt Cls.png' % omega_globals.options.session_unique_name)

    return cost_data


def plot_vehicle_megagrams(calendar_years):
    """
    Plot vehicle cert CO2e Mg v. model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years

    Returns:
        dict of vehicle cert CO2e Mg data by total, market class and market category

    """
    Mg_data = dict()

    # tally up total Mg
    Mg_data['vehicle'] = []
    for cy in calendar_years:
        Mg_data['vehicle'].append(
            sum([v.cert_co2e_Mg for v in vehicle_data if v.model_year == cy]))

    for mcat in market_categories:
        market_category_Mg = []
        for idx, cy in enumerate(calendar_years):
            market_id_and_Mg = [(v.market_class_id, v.cert_co2e_Mg) for v in vehicle_data if v.model_year == cy]
            Mg = 0
            for market_class_id, cert_co2e_Mg in market_id_and_Mg:
                if mcat in market_class_id.split('.'):
                    Mg += float(cert_co2e_Mg)
            market_category_Mg.append(Mg)

        Mg_data[mcat] = market_category_Mg

    for mc in market_classes:
        market_class_Mg = []
        for idx, cy in enumerate(calendar_years):
            market_class_Mg.append(sum([v.cert_co2e_Mg for v in vehicle_data if v.model_year == cy
                                        and v.market_class_id == mc]))

        Mg_data[mc] = market_class_Mg

    # market category chart
    fig, ax1 = figure()
    for mcat in market_categories:
        ax1.plot(calendar_years, Mg_data[mcat], '.--')
    ax1.plot(calendar_years, Mg_data['vehicle'], '.-')
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [Mg]',
              '%s\nVehicle CO2e Mg by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(omega_globals.options.output_folder + '%s V Mg Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure()
    for mc in market_classes:
        if 'ICE' in mc:
            ax1.plot(calendar_years, Mg_data[mc], '.-')
        else:
            ax1.plot(calendar_years, Mg_data[mc], '.--')
    ax1.plot(calendar_years, Mg_data['vehicle'], '.-')
    label_xyt(ax1, 'Year', 'CO2e [Mg]',
              '%s\nVehicle CO2e Mg  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes + ['vehicle'])
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

    market_share_results = dict()

    # tally up market_category sales
    for mcat in market_categories:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_id_and_market_class_id = [(v.vehicle_id, v.market_class_id) for v in vehicle_data if v.model_year == cy]
            for vehicle_id, market_class_id in vehicle_id_and_market_class_id:
                if mcat in market_class_id.split('.'):
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])

        market_share_results['abs_share_frac_%s' % mcat] = market_category_abs_share_frac

    # tally up market class sales
    for mc in market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]
            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % mc] = market_category_abs_share_frac

    # tally up context size class sales
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.context_size_class == csc]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % csc] = market_category_abs_share_frac

    # tally up reg class sales
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.reg_class_id == rc]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])
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
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % csc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nContext Size Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(NewVehicleMarket.base_year_context_size_class_sales.keys(), ncol=2, loc='upper center')
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

    market_share_results = dict()

    # tally up market_category sales
    for mcat in market_categories:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_id_and_market_class_id = [(v.vehicle_id, v.market_class_id) for v in vehicle_data
                                              if v.model_year == cy and v.compliance_id == compliance_id]
            for vehicle_id, market_class_id in vehicle_id_and_market_class_id:
                if mcat in market_class_id.split('.'):
                    count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])

        market_share_results['abs_share_frac_%s' % mcat] = market_category_abs_share_frac

    # tally up market class sales
    for mc in market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.market_class_id == mc
                           and v.compliance_id == compliance_id]
            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % (compliance_id, mc)] = market_category_abs_share_frac

    # tally up context size class sales
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.context_size_class == csc
                           and v.compliance_id == compliance_id]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % (compliance_id, csc)] = market_category_abs_share_frac

    # tally up reg class sales
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.reg_class_id == rc
                           and v.compliance_id == compliance_id]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']

            market_category_abs_share_frac.append(float(count) / total_sales[idx])
        market_share_results['abs_share_frac_%s' % (compliance_id, rc)] = market_category_abs_share_frac

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
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        ax1.plot(calendar_years, market_share_results['%s_abs_share_frac_%s' % (compliance_id, csc)], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nContext Size Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(NewVehicleMarket.base_year_context_size_class_sales.keys(), ncol=2, loc='upper center')
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
    total_sales = []
    for cy in calendar_years:
        count = 0
        vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy]
        for vehicle_id in vehicle_ids:
            count += vehicle_annual_data[vehicle_id, 0]['registered_count']
        total_sales.append(count)

    total_sales = np.array(total_sales)

    manufacturer_sales = dict()
    for compliance_id in compliance_ids:
        manufacturer_sales[compliance_id] = []
        for cy in calendar_years:
            count = 0
            vehicle_ids = [v.vehicle_id for v in vehicle_data if v.model_year == cy and v.compliance_id == compliance_id]
            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id, 0]['registered_count']
            manufacturer_sales[compliance_id].append(count)

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
        (calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, target_co2e_Mg)

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

    target_co2e_Mg = ManufacturerAnnualData.get_target_co2e_Mg(compliance_id)
    calendar_year_cert_co2e_Mg = ManufacturerAnnualData.get_calendar_year_cert_co2e_Mg(compliance_id)
    model_year_cert_co2e_Mg = ManufacturerAnnualData.get_model_year_cert_co2e_Mg(compliance_id)
    total_cost_billions = ManufacturerAnnualData.get_total_cost_billions(compliance_id)
    # compliance chart
    fig, ax1 = fplothg(calendar_years, target_co2e_Mg, 'o-')
    ax1.plot(calendar_years, calendar_year_cert_co2e_Mg, 'r.-')
    ax1.plot(calendar_years, model_year_cert_co2e_Mg, '-')
    ax1.legend(['target_co2e_Mg', 'calendar_year_cert_co2e_Mg', 'model_year_cert_co2e_Mg'])
    label_xyt(ax1, 'Year', 'CO2e [Mg]', '%s %s\nCert and Compliance Versus Year\n Total Cost $%.2f Billion' % (
        compliance_id, omega_globals.options.session_unique_name, total_cost_billions))

    target_co2e_Mg_dict = dict(zip(calendar_years, target_co2e_Mg))
    calendar_year_cert_co2e_Mg_dict = dict(zip(calendar_years, calendar_year_cert_co2e_Mg))
    model_year_cert_co2e_Mg_dict = dict(zip(calendar_years, model_year_cert_co2e_Mg))

    for _, t in credit_history.transaction_log.iterrows():
        if type(t.credit_destination) is not str and t.model_year in calendar_year_cert_co2e_Mg_dict:
            draw_transfer_arrow(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year],
                                t.credit_destination, target_co2e_Mg_dict[t.credit_destination])
        elif type(t.credit_destination) is not str and t.model_year not in calendar_year_cert_co2e_Mg_dict:
            ax1.plot(t.model_year, target_co2e_Mg_dict[calendar_years[0]], 'o', color='orange')
            draw_transfer_arrow(t.model_year, target_co2e_Mg_dict[calendar_years[0]],
                                t.credit_destination, model_year_cert_co2e_Mg_dict[t.credit_destination])
            ax1.set_xlim(calendar_years[0] - 5, ax1.get_xlim()[1])
        elif t.credit_destination == 'EXPIRATION' and t.model_year in calendar_year_cert_co2e_Mg_dict:
            draw_expiration_arrow(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year])
        elif t.credit_destination == 'EXPIRATION' and t.model_year not in calendar_year_cert_co2e_Mg_dict:
            ax1.plot(t.model_year, target_co2e_Mg_dict[calendar_years[0]], 'o', color='orange')
            draw_expiration_arrow(t.model_year, target_co2e_Mg_dict[calendar_years[0]])
        else:  # "PAST_DUE"
            ax1.plot(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], 'x', color='red')
            plt.scatter(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], s=80, facecolors='none',
                        edgecolors='r')

    fig.savefig(omega_globals.options.output_folder + '%s Cert Mg v Year %s.png' %
                (omega_globals.options.session_unique_name, compliance_id))

    return calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, target_co2e_Mg


def plot_iteration(iteration_log, compliance_id):
    """
    Plot producer-consumer iteration data.

    Args:
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        iteration_log (DataFrame): iteration data

    """
    iteration_log = iteration_log.loc[iteration_log['compliance_id'] == compliance_id]

    for iteration in [0, -1]:
        if iteration == -1:
            iteration_label = 'initial'
        else:
            iteration_label = 'final'

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
            plt.title('%s %s iteration %s' % (compliance_id, mc, iteration_label))
            plt.grid()
            plt.legend(['producer_abs_share_frac_%s' % mc, 'consumer_abs_share_frac_%s' % mc])
            # plt.ylim([0, 1])
            plt.savefig('%s%s %s Iter %s %s.png' % (
                omega_globals.options.output_folder, omega_globals.options.session_unique_name, compliance_id,
                mc, iteration_label))

        first_logged = iteration_log.loc[iteration_log['cross_subsidy_iteration_num'] == 0]
        last_logged = iteration_log.loc[iteration_log['cross_subsidy_iteration_num'] == -1]

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
        plt.title('%s Consumer Generalized Cost %s' % (compliance_id, iteration_label))
        plt.grid()
        plt.savefig('%s%s %s ConsumerGC %s.png' % (omega_globals.options.output_folder,
                                                   omega_globals.options.session_unique_name, compliance_id,
                                                   iteration_label))

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
        plt.title('%s Producer Cost Multipliers %s' % (compliance_id, iteration_label))
        plt.grid()
        plt.savefig('%s%s %s Producer Cost Multipliers %s.png' % (
            omega_globals.options.output_folder, omega_globals.options.session_unique_name, compliance_id,
            iteration_label))

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
        plt.plot(first_logged['calendar_year'], first_logged['average_onroad_direct_co2e_gpmi_%s' % mc], '.-')
    plt.title('%s Producer Initial CO2e g/mi' % compliance_id)
    plt.grid()
    plt.legend(['average_onroad_direct_co2e_gpmi_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer Initial CO2e gpmi.png' % (omega_globals.options.output_folder,
                                                            omega_globals.options.session_unique_name, compliance_id))
