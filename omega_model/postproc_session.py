"""

post-compliance-modeling output generation (charts, summary files, etc)


----

**CODE**

"""
import numpy as np

from omega_model import *
from common.omega_plot import *
from policy.credit_banking import CreditBank
from producer.vehicle_annual_data import VehicleAnnualData
import consumer

market_classes = []
market_categories = []

vehicle_data = []
vehicle_annual_data = None
mfr_cost_data = None
mfr_market_share_results = None


def run_postproc(iteration_log, credit_banks):
    """
    Generate charts and output files for a single simulation

    Args:
        iteration_log (DataFrame): dataframe storing information on producer-consumer iteration
        credit_banks (dict of CreditBanks): credit banking information per compliance_id

    Returns:
        Results summary DataFrame

    """
    from producer.vehicles import Vehicle
    import pandas as pd
    global vehicle_data, vehicle_annual_data

    global market_classes, market_categories
    market_classes = omega_globals.options.MarketClass.market_classes
    market_categories = omega_globals.options.MarketClass.market_categories

    global mfr_cost_data
    mfr_cost_data = None
    mfr_market_share_results = None

    if not omega_globals.options.standalone_run:
        omega_log.logwrite('%s: Post Processing ...' % omega_globals.options.session_name)

    vehicle_years = list(range(omega_globals.options.analysis_initial_year - 1,
                               omega_globals.options.analysis_final_year + 1))

    vehicle_data = sorted([v for v in omega_globals.finalized_vehicles if v.in_production])

    vehicle_annual_data_df = pd.DataFrame(VehicleAnnualData._data)
    # index vehicle annual data by compliance id, vehicle id and age for quick access and save to csv
    # vehicle_annual_data_df = vehicle_annual_data_df.set_index(['compliance_id', 'vehicle_id', 'age'])
    vehicle_annual_data = (
        vehicle_annual_data_df.set_index(['compliance_id', 'vehicle_id', 'age']).copy().to_dict(orient='index'))

    # create temporary columns for sorting purposes
    vehicle_annual_data_df['mfr'] = vehicle_annual_data_df['vehicle_id'].apply(lambda x: x.split('_')[0])
    vehicle_annual_data_df['num'] = vehicle_annual_data_df['vehicle_id'].apply(lambda x: int(x.split('_')[1]))
    # rename vehicle ids
    vehicle_annual_data_df['vehicle_id'] = \
            vehicle_annual_data_df['vehicle_id'] + '_' + vehicle_annual_data_df['reg_class_id']
    # sort and drop temporary columns
    vehicle_annual_data_df = (
        vehicle_annual_data_df.sort_values(by=['mfr', 'num']).drop(['mfr', 'num', 'reg_class_id'], axis=1))
    vehicle_annual_data_df.to_csv(omega_globals.options.output_folder + omega_globals.options.session_unique_name
                                  + '_vehicle_annual_data.csv', columns=sorted(vehicle_annual_data_df.columns))

    analysis_years = vehicle_years[1:]

    vehicles_table = pd.DataFrame([v.to_dict(types=[int, float, bool, str, np.int64, np.float64])
                                   for v in sorted(omega_globals.finalized_vehicles)])
    vehicles_table['vehicle_id'] = vehicles_table['vehicle_id'] + '_' + vehicles_table['reg_class_id']
    vehicles_table.to_csv(
        omega_globals.options.output_folder + omega_globals.options.session_unique_name + '_vehicles.csv',
        columns=sorted(vehicles_table.columns), index=False)

    manufacturer_ids = sorted(vehicles_table['manufacturer_id'].unique())

    if omega_globals.manufacturer_aggregation and omega_globals.options.consolidate_manufacturers and len(manufacturer_ids) > 1:
        # create individual OEM annual data from production vehicle data
        from producer.manufacturer_annual_data import ManufacturerAnnualData
        from producer.vehicle_aggregation import aggregation_columns

        vehicles_table = dataframe_to_numeric(vehicles_table)

        # generate after-the-fact manufacturer annual data for individual producers
        for manufacturer_id in manufacturer_ids:
            for calendar_year in vehicle_years[1:]:
                mfr_data = vehicles_table[(vehicles_table['manufacturer_id'] == manufacturer_id) &
                                          (vehicles_table['model_year'] == calendar_year)]

                ManufacturerAnnualData. \
                    create_manufacturer_annual_data(model_year=calendar_year,
                                                    compliance_id=manufacturer_id,
                                                    target_co2e_Mg=sum(mfr_data['target_co2e_Mg']),
                                                    calendar_year_cert_co2e_Mg=sum(mfr_data['cert_co2e_Mg']),
                                                    manufacturer_vehicle_cost_dollars=sum(
                                                        mfr_data['new_vehicle_mfr_cost_dollars'] *
                                                        mfr_data['_initial_registered_count']),
                                                    )

                credit_banks[manufacturer_id] = None

    elif not omega_globals.options.consolidate_manufacturers:
        # create consolidated_OEM annual data from individual OEM annual data
        from producer.manufacturer_annual_data import ManufacturerAnnualData

        vehicles_table = dataframe_to_numeric(vehicles_table)

        manufacturer_id = 'consolidated_OEM'

        non_consolidated_madt = pd.DataFrame(ManufacturerAnnualData._data)

        for calendar_year in vehicle_years[1:]:
            mfr_data = vehicles_table[vehicles_table['model_year'] == calendar_year]

            model_year_cert_co2e_megagrams = sum(non_consolidated_madt['model_year_cert_co2e_megagrams'].loc[
                                                     non_consolidated_madt['model_year'] == calendar_year])

            # initialize the starting point for the synthesized consolidated manufacturer annual data to the
            # point where the OEMs left off (model year cert) and then trading/transfers go from there further below.
            # This way the consolidated compliance chart makes sense.
            ManufacturerAnnualData. \
                create_manufacturer_annual_data(model_year=calendar_year,
                                                compliance_id=manufacturer_id,
                                                target_co2e_Mg=sum(mfr_data['target_co2e_Mg']),
                                                calendar_year_cert_co2e_Mg=model_year_cert_co2e_megagrams,
                                                manufacturer_vehicle_cost_dollars=sum(
                                                    mfr_data['new_vehicle_mfr_cost_dollars'] *
                                                    mfr_data['_initial_registered_count']),
                                                model_year_cert_co2e_megagrams=model_year_cert_co2e_megagrams,
                                                )

    # pull in initial compliance data (data is final on first pass)
    manufacturer_annual_data_table = pd.DataFrame(ManufacturerAnnualData._data)
    manufacturer_annual_data_table = dataframe_to_numeric(manufacturer_annual_data_table)

    session_results = dict()
    session_results['calendar_year'] = analysis_years
    session_results['session_name'] = omega_globals.options.session_name

    context_sales, total_sales, manufacturer_sales = \
        plot_total_sales(vehicle_years, sorted(list(set(Vehicle.compliance_ids + list(manufacturer_ids)))))

    session_results['sales_total'] = total_sales[1:]
    session_results['sales_context'] = context_sales
    for manufacturer in manufacturer_sales:
        session_results['%s_sales_total' % manufacturer] = manufacturer_sales[manufacturer][1:]

    # generate manufacturer-specific plots and data if not consolidating
    if omega_globals.manufacturer_aggregation:
        compliance_ids = vehicles_table['manufacturer_id'].unique()
        compliance_ids = np.unique(np.append(compliance_ids, vehicles_table['compliance_id'].unique()))
    else:
        compliance_ids = Vehicle.compliance_ids

    if not omega_globals.options.consolidate_manufacturers:
        # create consolidated_OEM credits and transactions based on individual OEM cert by model year
        from policy.credit_banking import CreditBank

        compliance_id = 'consolidated_OEM'

        # setup consolidated_OEM without banked historical credits for now (would have to account for those used by OEMs)
        credit_banks[compliance_id] = (
            CreditBank(omega_globals.options.ghg_credit_params_file, None, compliance_id))

        for calendar_year in \
                range(omega_globals.options.analysis_initial_year,
                      omega_globals.options.analysis_final_year + 1):
            credit_banks[compliance_id].update_credit_age(calendar_year)

            mad = manufacturer_annual_data_table[(manufacturer_annual_data_table['compliance_id'] == compliance_id) &
                                                 (manufacturer_annual_data_table['model_year'] == calendar_year)]

            credit_Mg = mad['target_co2e_megagrams'].item() - mad['model_year_cert_co2e_megagrams'].item()

            credit_banks[compliance_id].handle_credit(calendar_year, credit_Mg)

        credit_banks[compliance_id].credit_bank.to_csv(omega_globals.options.output_folder +
                                                       omega_globals.options.session_unique_name +
                                                       ' %s GHG_credit_balances.csv' % compliance_id,
                                                       columns=sorted(credit_banks[compliance_id].credit_bank.columns),
                                                       index=False)

        credit_banks[compliance_id].transaction_log.to_csv(
            omega_globals.options.output_folder + omega_globals.options.session_unique_name +
            ' %s GHG_credit_transactions.csv' % compliance_id,
            columns=sorted(credit_banks[compliance_id].transaction_log.columns), index=False)

        compliance_ids = np.append(compliance_ids, 'consolidated_OEM')

    # save manufacturer annual data >after< any second-pass credit transfers/trading
    manufacturer_annual_data_table = pd.DataFrame(ManufacturerAnnualData._data)  # pull in updated compliance data
    manufacturer_annual_data_table.to_csv(omega_globals.options.output_folder +
                                          omega_globals.options.session_unique_name + '_manufacturer_annual_data.csv',
                                          columns=sorted(manufacturer_annual_data_table.columns))

    total_calendar_year_cert_co2e_Mg = np.zeros_like(analysis_years, dtype='float')
    total_model_year_cert_co2e_Mg = np.zeros_like(analysis_years, dtype='float')
    total_target_co2e_Mg = np.zeros_like(analysis_years, dtype='float')
    for compliance_id in compliance_ids:
        if compliance_id in credit_banks:
            calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, target_co2e_Mg = \
                plot_manufacturer_compliance(analysis_years, compliance_id, credit_banks[compliance_id])

            total_calendar_year_cert_co2e_Mg += calendar_year_cert_co2e_Mg
            total_model_year_cert_co2e_Mg += model_year_cert_co2e_Mg
            total_target_co2e_Mg += target_co2e_Mg

            session_results['%s_target_co2e_Mg' % compliance_id] = target_co2e_Mg
            session_results['%s_calendar_year_cert_co2e_Mg' % compliance_id] = calendar_year_cert_co2e_Mg
            session_results['%s_model_year_cert_co2e_Mg' % compliance_id] = model_year_cert_co2e_Mg

    for compliance_id in Vehicle.compliance_ids:
        if 'iteration' in omega_globals.options.verbose_postproc:
            plot_iteration(iteration_log, compliance_id)

        if not omega_globals.options.consolidate_manufacturers:

            mfr_market_share_results = plot_manufacturer_market_shares(vehicle_years, compliance_id,
                                                                       manufacturer_sales[compliance_id])

            mfr_average_cost_data = plot_manufacturer_vehicle_cost(analysis_years, compliance_id)

    gigawatthour_data = plot_vehicle_GWh(analysis_years)

    mfr_gigawatthour_limit_data = {'analysis_years': analysis_years}
    for manufacturer_id in vehicles_table['manufacturer_id'].unique():
        mfr_gigawatthour_data = plot_vehicle_GWh(analysis_years, manufacturer_id)['vehicle']
        for idx, ay in enumerate(analysis_years):
            GWh_limit = \
                (np.interp(ay, omega_globals.options.battery_GWh_limit_years, omega_globals.options.battery_GWh_limit))
            if gigawatthour_data['vehicle'][idx] > 0 and omega_globals.options.relax_second_pass_GWh:
                mfr_gigawatthour_data[idx] = mfr_gigawatthour_data[idx] * GWh_limit / gigawatthour_data['vehicle'][idx]
        mfr_gigawatthour_limit_data[manufacturer_id] = mfr_gigawatthour_data

    if not omega_globals.options.consolidate_manufacturers:
        for msr in mfr_market_share_results:
            session_results[msr] = mfr_market_share_results[msr][1:]

        for macd in mfr_average_cost_data:
            session_results['average_%s_cost' % macd] = mfr_average_cost_data[macd]

    market_share_results = plot_market_shares(vehicle_years, total_sales)

    average_cost_data = plot_vehicle_cost(analysis_years)

    average_generalized_cost_data = plot_vehicle_generalized_cost(analysis_years)

    megagrams_data = plot_vehicle_megagrams(analysis_years)

    average_cert_co2e_gpmi_data = plot_cert_co2e_gpmi(analysis_years)

    average_cert_direct_oncycle_co2e_gpmi_data = plot_cert_direct_oncycle_co2e_gpmi(analysis_years)

    average_cert_direct_kwh_pmi_data = plot_cert_direct_kwh_pmi(analysis_years)

    average_target_co2e_gpmi_data = plot_target_co2e_gpmi(analysis_years)

    # market share results include base year data, but the rest of the data doesn't, so drop the
    # base year data, otherwise the dataframe at the end will fail due to inconsistent column lengths

    for msr in market_share_results:
        session_results[msr] = market_share_results[msr][1:]

    session_results = pd.DataFrame.from_dict(session_results)

    for cat in market_categories + market_classes + ['vehicle']:
        session_results \
            = pd.concat([session_results, pd.Series(average_cost_data[cat],
                                                    name=f'average_{cat}_cost')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(average_generalized_cost_data[cat],
                                                    name=f'average_{cat}_generalized_cost')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(average_cert_co2e_gpmi_data[cat],
                                                    name=f'average_{cat}_cert_co2e_gpmi')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(average_cert_direct_oncycle_co2e_gpmi_data[cat],
                                                    name=f'average_{cat}_cert_direct_oncycle_co2e_gpmi')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(average_cert_direct_kwh_pmi_data[cat],
                                                    name=f'average_{cat}_cert_direct_kwh_pmi')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(average_target_co2e_gpmi_data[cat],
                                                    name=f'average_{cat}_target_co2e_gpmi')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(megagrams_data[cat],
                                                    name=f'{cat}_co2e_Mg')], axis=1)
        session_results \
            = pd.concat([session_results, pd.Series(gigawatthour_data[cat],
                                                    name=f'{cat}_GWh')], axis=1)

    total_vehicle_cost_billions = session_results['average_vehicle_cost'] * session_results['sales_total'] / 1e9
    session_results \
        = pd.concat([session_results, pd.Series(total_vehicle_cost_billions,
                                                name='total_vehicle_cost_billions')], axis=1)

    # write output files
    summary_filename = omega_globals.options.output_folder + omega_globals.options.session_unique_name \
                       + '_summary_results.csv'

    session_results.to_csv(summary_filename, index=False, columns=sorted(session_results.columns))

    if omega_globals.options.powertrain_cost_tracker:
        powertrain_costs_filename = omega_globals.options.output_folder + omega_globals.options.session_unique_name \
                                    + '_powertrain_cost_results.csv'
        pt_cost_df = pd.DataFrame.from_dict(omega_globals.options.PowertrainCost.cost_tracker, orient='index')
        pt_cost_df.to_csv(powertrain_costs_filename, index=False)

    return manufacturer_annual_data_table, mfr_gigawatthour_limit_data


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

        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        ax1.plot(calendar_years, physical_effects['vehicle_stock_CO2_megagrams'], '.-')
        ax1.legend(['Vehicle Stock CO2 Mg'])
        label_xyt(ax1, 'Year', 'CO2 [Mg]', '%s\nVehicle Stock CO2 Mg' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s ALL Stock CO2 Mg.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        ax1.plot(calendar_years, physical_effects['vehicle_stock_consumption_gasoline_gallons'], '.-')
        ax1.legend(['Vehicle Stock Fuel Consumption Gallons'])
        label_xyt(ax1, 'Year', 'Fuel Consumption [Gasoline gallons]',
                  '%s\nVehicle Stock Fuel Consumption Gasoline Gallons' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s ALL Stock Gas Gallons.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        ax1.plot(calendar_years, physical_effects['vehicle_stock_consumption_kwh'], '.-')
        ax1.legend(['Vehicle Stock Fuel Consumption kWh'])
        label_xyt(ax1, 'Year', 'Consumption [kWh]',
                  '%s\nVehicle Stock Fuel Consumption kWh' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s ALL Stock kWh.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        ax1.plot(calendar_years, physical_effects['vehicle_stock_vmt'], '.-')
        ax1.legend(['Vehicle Stock Miles Travelled'])
        label_xyt(ax1, 'Year', 'Distance Travelled [miles]',
                  '%s\nVehicle Stock Miles Travelled' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s ALL Stock VMT.png'
                    % omega_globals.options.session_unique_name)

        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        ax1.plot(calendar_years, np.array(physical_effects['registered_count']) / 1e6, '.-')
        ax1.legend(['Vehicle Stock Registered Count'])
        label_xyt(ax1, 'Year', 'Registered Count [millions]',
                  '%s\nVehicle Stock Registered Count' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s ALL Stock Count.png'
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
        vehicle_id_and_vmt_and_co2gpmi = [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.cert_co2e_grams_per_mile)
                                          for v in vehicle_data if v.model_year == cy]

        for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
            weighted_value += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

        co2e_data['vehicle'].append(weighted_value / max(1, count))

    # tally up market_category sales- and VMT- weighted co2
    for mcat in market_categories:
        market_category_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi_market_class_id = \
                [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.cert_co2e_grams_per_mile, v.market_class_id)
                 for v in vehicle_data if v.model_year == cy]

            for vehicle_id, lifetime_vmt, co2gpmi, market_class_id in vehicle_id_and_vmt_and_co2gpmi_market_class_id:
                if mcat in market_class_id.split('.'):
                    weighted_value += \
                        vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

            market_category_co2e.append(weighted_value / max(1, count))

        co2e_data[mcat] = market_category_co2e

    # tally up market_class sales- and VMT- weighted co2
    for mc in market_classes:
        market_class_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi = \
                [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.cert_co2e_grams_per_mile) for v in
                 vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
                weighted_value += \
                    vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

            market_class_co2e.append(weighted_value / max(1, count))

        co2e_data[mc] = market_class_co2e

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, co2e_data[mcat], **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, co2e_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert CO2e g/mi by Market Category v Year' %
              omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cert CO2e gpmi Mkt Cat.png' %
        omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, co2e_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert CO2e g/mi  by Market Class v Year' %
              omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cert CO2e gpmi Mkt Cls.png' %
        omega_globals.options.session_unique_name)

    return co2e_data


def plot_cert_direct_oncycle_co2e_gpmi(calendar_years):
    """
    Plot cert direct oncycle CO2e g/mi versus model year, by market class and market category.

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
        vehicle_id_and_vmt_and_co2gpmi = [((v.compliance_id, v.vehicle_id), v.lifetime_VMT,
                                           v.cert_direct_oncycle_co2e_grams_per_mile)
                                          for v in vehicle_data if v.model_year == cy]

        for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
            weighted_value += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

        co2e_data['vehicle'].append(weighted_value / max(1, count))

    # tally up market_category sales- and VMT- weighted co2
    for mcat in market_categories:
        market_category_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi_market_class_id = \
                [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.cert_direct_oncycle_co2e_grams_per_mile,
                  v.market_class_id)
                 for v in vehicle_data if v.model_year == cy]

            for vehicle_id, lifetime_vmt, co2gpmi, market_class_id in vehicle_id_and_vmt_and_co2gpmi_market_class_id:
                if mcat in market_class_id.split('.'):
                    weighted_value += \
                        vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

            market_category_co2e.append(weighted_value / max(1, count))

        co2e_data[mcat] = market_category_co2e

    # tally up market_class sales- and VMT- weighted co2
    for mc in market_classes:
        market_class_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi = \
                [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.cert_direct_oncycle_co2e_grams_per_mile) for v in
                 vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
                weighted_value += \
                    vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

            market_class_co2e.append(weighted_value / max(1, count))

        co2e_data[mc] = market_class_co2e

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, co2e_data[mcat], **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, co2e_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert Direct Oncycle CO2e g/mi by Market Category v Year' %
              omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cert CO2e Direct gpmi Mkt Cat.png' %
        omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, co2e_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Cert Direct Oncycle CO2e g/mi  by Market Class v Year' %
              omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cert CO2e Direct gpmi Mkt Cls.png' %
        omega_globals.options.session_unique_name)

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
        vehicle_id_and_kwh = \
            [((v.compliance_id, v.vehicle_id), v.cert_direct_kwh_per_mile) for v in vehicle_data if v.model_year == cy]

        for vehicle_id, kwh in vehicle_id_and_kwh:
            weighted_value += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * kwh
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

        average_cert_direct_kwh_data['vehicle'].append(weighted_value / max(1, count))

    # tally up market_category sales weighted kWh
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_value = 0
            count = 0

            vehicle_id_and_market_class_id_and_kwh = \
                [((v.compliance_id, v.vehicle_id), v.market_class_id, v.cert_direct_kwh_per_mile)
                 for v in vehicle_data if v.model_year == cy]

            for vehicle_id, market_class_id, kwh in vehicle_id_and_market_class_id_and_kwh:
                if mcat in market_class_id.split('.'):
                    weighted_value += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * kwh
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_cost.append(weighted_value / max(1, count))

        average_cert_direct_kwh_data[mcat] = market_category_cost

    # tally up market_class sales weighted kWh
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_value = 0
            count = 0

            vehicle_id_and_kwh = \
                [((v.compliance_id, v.vehicle_id), v.cert_direct_kwh_per_mile)
                 for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, kwh in vehicle_id_and_kwh:
                weighted_value += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * kwh
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_class_cost.append(weighted_value / max(1, count))

        average_cert_direct_kwh_data[mc] = market_class_cost

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cert_direct_kwh_data[mcat],
                 **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, average_cert_direct_kwh_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi by Market Category v Year' %
              omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cert kWh pmi Mkt Cat.png' %
        omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, average_cert_direct_kwh_data[mc],
                 **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'Energy Consumption [kWh/mi]',
              '%s\nAverage Vehicle Cert kWh/mi  by Market Class v Year' %
              omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cert kWh pmi Mkt Cls.png' %
        omega_globals.options.session_unique_name)
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
        vehicle_id_and_vmt_and_co2gpmi = \
            [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.target_co2e_grams_per_mile)
             for v in vehicle_data if v.model_year == cy]

        for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
            weighted_value += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

        co2e_data['vehicle'].append(weighted_value / max(1, count))

    # tally up market_category sales- and VMT- weighted co2
    for mcat in market_categories:
        market_category_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi_market_class_id = \
                [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.target_co2e_grams_per_mile, v.market_class_id)
                 for v in vehicle_data if v.model_year == cy]

            for vehicle_id, lifetime_vmt, co2gpmi, market_class_id in vehicle_id_and_vmt_and_co2gpmi_market_class_id:
                if mcat in market_class_id.split('.'):
                    weighted_value += \
                        vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

            market_category_co2e.append(weighted_value / max(1, count))

        co2e_data[mcat] = market_category_co2e

    # tally up market_class sales- and VMT- weighted co2
    for mc in market_classes:
        market_class_co2e = []
        for cy in calendar_years:
            weighted_value = 0
            count = 0
            vehicle_id_and_vmt_and_co2gpmi = \
                [((v.compliance_id, v.vehicle_id), v.lifetime_VMT, v.target_co2e_grams_per_mile) for v in
                 vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, lifetime_vmt, co2gpmi in vehicle_id_and_vmt_and_co2gpmi:
                weighted_value += \
                    vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt * co2gpmi
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * lifetime_vmt

            market_class_co2e.append(weighted_value / max(1, count))

        co2e_data[mc] = market_class_co2e

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, co2e_data[mcat], **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, co2e_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Target CO2e g/mi by Market Category v Year' %
              omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Target CO2e gpmi Mkt Cat.png' %
        omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, co2e_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'CO2e [g/mi]',
              '%s\nAverage Vehicle Target CO2e g/mi  by Market Class v Year' %
              omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Target CO2e gpmi Mkt Cls.png' %
        omega_globals.options.session_unique_name)

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
        vehicle_id_and_cost = [((v.compliance_id, v.vehicle_id), v.new_vehicle_mfr_cost_dollars)
                               for v in vehicle_data if v.model_year == cy]
        for vehicle_id, cost in vehicle_id_and_cost:
            weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

        average_cost_data['vehicle'].append(weighted_cost / max(1, count))

    # tally up market_category costs
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0
            vehicle_id_and_market_class_id_and_cost = \
                [((v.compliance_id, v.vehicle_id), v.market_class_id, v.new_vehicle_mfr_cost_dollars)
                 for v in vehicle_data if v.model_year == cy]

            for vehicle_id, market_class_id, cost in vehicle_id_and_market_class_id_and_cost:
                if mcat in market_class_id.split('.'):
                    weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_cost.append(weighted_cost / max(1, count))

        average_cost_data[mcat] = market_category_cost

    # tally up market_class costs
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0
            vehicle_id_and_cost = [((v.compliance_id, v.vehicle_id), v.new_vehicle_mfr_cost_dollars)
                                   for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]
            for vehicle_id, cost in vehicle_id_and_cost:
                weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_class_cost.append(weighted_cost / max(1, count))

        average_cost_data[mc] = market_class_cost

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, average_cost_data[mcat],
                 **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, average_cost_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cost Mkt Cat.png' % omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, average_cost_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Cost  by Market Class v Year' % omega_globals.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V Cost Mkt Cls.png' % omega_globals.options.session_unique_name)

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
    global mfr_cost_data
    if mfr_cost_data is None:
        mfr_cost_data = dict()

    # tally up total sales weighted cost
    mfr_cost_data['%s_total' % compliance_id] = []
    for cy in calendar_years:
        weighted_cost = 0
        count = 0
        vehicle_id_and_cost = [((v.compliance_id, v.vehicle_id), v.new_vehicle_mfr_cost_dollars) for v in vehicle_data
                               if v.model_year == cy and v.compliance_id == compliance_id]

        for vehicle_id, cost in vehicle_id_and_cost:
            weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

        mfr_cost_data['%s_total' % compliance_id].append(weighted_cost / max(1, count))

    # tally up market_category costs
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_market_class_id_and_cost = \
                [((v.compliance_id, v.vehicle_id), v.market_class_id, v.new_vehicle_mfr_cost_dollars)
                 for v in vehicle_data if v.model_year == cy and v.compliance_id == compliance_id]

            for vehicle_id, market_class_id, cost in vehicle_id_and_market_class_id_and_cost:
                if mcat in market_class_id.split('.'):
                    weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_cost.append(weighted_cost / max(1, count))

        mfr_cost_data['%s_%s' % (compliance_id, mcat)] = market_category_cost

    # tally up market_class costs
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_cost = \
                [((v.compliance_id, v.vehicle_id), v.new_vehicle_mfr_cost_dollars)
                 for v in vehicle_data if v.model_year == cy and v.market_class_id == mc and
                 v.compliance_id == compliance_id]

            for vehicle_id, cost in vehicle_id_and_cost:
                weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_class_cost.append(weighted_cost / max(1, count))

        mfr_cost_data['%s_%s' % (compliance_id, mc)] = market_class_cost

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, mfr_cost_data['%s_%s' % (compliance_id, mcat)],
                 **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, mfr_cost_data['%s_total' % compliance_id], '.-')
    ax1.legend(market_categories + ['%s_total' % compliance_id])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s %s\nAverage Vehicle Cost by Market Category v Year' %
              (compliance_id, omega_globals.options.session_unique_name))
    fig.savefig(omega_globals.options.output_folder + '%s %s V Cost Mkt Cat.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, mfr_cost_data['%s_%s' % (compliance_id, mc)],
                 **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s %s\nAverage Vehicle Cost  by Market Class v Year'
              % (compliance_id, omega_globals.options.session_unique_name))
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(omega_globals.options.output_folder + '%s %s V Cost Mkt Cls.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    return mfr_cost_data


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
        vehicle_id_and_cost = [((v.compliance_id, v.vehicle_id), v.new_vehicle_mfr_generalized_cost_dollars)
                               for v in vehicle_data if v.model_year == cy]

        for vehicle_id, cost in vehicle_id_and_cost:
            weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
            count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

        cost_data['vehicle'].append(weighted_cost / max(1, count))

    # tally up market_category costs
    for mcat in market_categories:
        market_category_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_market_class_id_and_cost = \
                [((v.compliance_id, v.vehicle_id), v.market_class_id, v.new_vehicle_mfr_generalized_cost_dollars)
                 for v in vehicle_data if v.model_year == cy]

            for vehicle_id, market_class_id, cost in vehicle_id_and_market_class_id_and_cost:
                if mcat in market_class_id.split('.'):
                    weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_cost.append(weighted_cost / max(1, count))

        cost_data[mcat] = market_category_cost

    # tally up market_class costs
    for mc in market_classes:
        market_class_cost = []
        for idx, cy in enumerate(calendar_years):
            weighted_cost = 0
            count = 0

            vehicle_id_and_cost = \
                [((v.compliance_id, v.vehicle_id), v.new_vehicle_mfr_generalized_cost_dollars)
                 for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]

            for vehicle_id, cost in vehicle_id_and_cost:
                weighted_cost += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count'] * cost
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_class_cost.append(weighted_cost / max(1, count))

        cost_data[mc] = market_class_cost

    # market category chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, cost_data[mcat], **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, cost_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized Cost by Market Category v Year' %
              omega_globals.options.session_unique_name)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V GenCost Mkt Cat.png' %
        omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, cost_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

    label_xyt(ax1, 'Year', 'Cost [$]',
              '%s\nAverage Vehicle Generalized_Cost  by Market Class v Year' %
              omega_globals.options.session_unique_name)
    # ax1.set_ylim(15e3, 80e3)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL V GenCost Mkt Cls.png' %
        omega_globals.options.session_unique_name)

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
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, Mg_data[mcat], **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.plot(calendar_years, Mg_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    ax1.legend(market_categories + ['vehicle'])
    label_xyt(ax1, 'Year', 'CO2e [Mg]',
              '%s\nVehicle CO2e Mg by Market Category v Year' % omega_globals.options.session_unique_name)
    fig.savefig(omega_globals.options.output_folder + '%s ALL V Mg Mkt Cat.png' %
                omega_globals.options.session_unique_name)

    # market class chart
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, Mg_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

    ax1.plot(calendar_years, Mg_data['vehicle'],
             **omega_globals.options.MarketClass.get_linestyle('vehicle'))
    label_xyt(ax1, 'Year', 'CO2e [Mg]',
              '%s\nVehicle CO2e Mg  by Market Class v Year' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes + ['vehicle'])
    fig.savefig(omega_globals.options.output_folder + '%s ALL V Mg Mkt Cls.png' %
                omega_globals.options.session_unique_name)

    return Mg_data


def plot_vehicle_GWh(calendar_years, manufacturer_id=None):
    """
    Plot vehicle cert CO2e Mg v. model year, by market class and market category.

    Args:
        calendar_years ([years]): list of model years
        manufacturer_id (str): manufacturer id

    Returns:
        dict of vehicle cert CO2e Mg data by total, market class and market category

    """
    GWh_data = dict()

    # tally up total Mg
    GWh_data['vehicle'] = []
    for cy in calendar_years:
        GWh_data['vehicle'].append(
            sum([v.initial_registered_count * v.battery_kwh / 1e6 for v in vehicle_data
                 if v.model_year == cy and (manufacturer_id is None or v.manufacturer_id == manufacturer_id)]))

    for mcat in market_categories:
        market_category_GWh = []
        for idx, cy in enumerate(calendar_years):
            market_id_and_Mg = \
                [(v.market_class_id, v.initial_registered_count*v.battery_kwh/1e6) for v in vehicle_data
                 if v.model_year == cy and (manufacturer_id is None or v.manufacturer_id == manufacturer_id)]
            Mg = 0
            for market_class_id, cert_co2e_Mg in market_id_and_Mg:
                if mcat in market_class_id.split('.'):
                    Mg += float(cert_co2e_Mg)
            market_category_GWh.append(Mg)

        GWh_data[mcat] = market_category_GWh

    for mc in market_classes:
        market_class_GWh = []
        for idx, cy in enumerate(calendar_years):
            market_class_GWh.append(sum([v.initial_registered_count * v.battery_kwh / 1e6 for v in vehicle_data
                                         if v.model_year == cy and v.market_class_id == mc and
                                         (manufacturer_id is None or v.manufacturer_id == manufacturer_id)]))

        GWh_data[mc] = market_class_GWh

    if manufacturer_id is None:
        manufacturer_id = 'ALL'

        # market category chart
        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        for mcat in market_categories:
            ax1.plot(calendar_years, GWh_data[mcat],
                     **omega_globals.options.MarketClass.get_linestyle(mcat))
        ax1.plot(calendar_years, GWh_data['vehicle'],
                 **omega_globals.options.MarketClass.get_linestyle('vehicle'))
        ax1.set_xlim(ax1.get_xlim())
        ax1.set_ylim(ax1.get_ylim())
        ax1.plot(omega_globals.options.battery_GWh_limit_years,
                 omega_globals.options.battery_GWh_limit, 'r.--')
        ax1.legend(market_categories + ['total_GWh', 'limit'])
        label_xyt(ax1, 'Year', 'GWh',
                  '%s\nVehicle GWh by Market Category v Year' % omega_globals.options.session_unique_name)
        fig.savefig(omega_globals.options.output_folder + '%s %s V GWh Mkt Cat.png' %
                    (omega_globals.options.session_unique_name, manufacturer_id))

        # market class chart
        fig, ax1 = figure(omega_globals.options.auto_close_figures)
        for mc in market_classes:
            ax1.plot(calendar_years, GWh_data[mc], **omega_globals.options.MarketClass.get_linestyle(mc))

        ax1.plot(calendar_years, GWh_data['vehicle'],
                 **omega_globals.options.MarketClass.get_linestyle('vehicle'))
        ax1.set_xlim(ax1.get_xlim())
        ax1.set_ylim(ax1.get_ylim())
        ax1.plot(omega_globals.options.battery_GWh_limit_years,
                 omega_globals.options.battery_GWh_limit, 'r.--')
        label_xyt(ax1, 'Year', 'GWh]',
                  '%s\nVehicle GWh  by Market Class v Year' % omega_globals.options.session_unique_name)
        ax1.legend(market_classes + ['total_GWh', 'limit'])
        fig.savefig(omega_globals.options.output_folder + '%s %s V GWh Mkt Cls.png' %
                    (omega_globals.options.session_unique_name, manufacturer_id))

    return GWh_data


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
            vehicle_id_and_market_class_id = [((v.compliance_id, v.vehicle_id), v.market_class_id)
                                              for v in vehicle_data if v.model_year == cy]
            for vehicle_id, market_class_id in vehicle_id_and_market_class_id:
                if mcat in market_class_id.split('.'):
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))

        market_share_results['abs_share_frac_%s' % mcat] = market_category_abs_share_frac

    # tally up market class sales
    for mc in market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [(v.compliance_id, v.vehicle_id)
                           for v in vehicle_data if v.model_year == cy and v.market_class_id == mc]
            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))
        market_share_results['abs_share_frac_%s' % mc] = market_category_abs_share_frac

    # tally up context size class sales
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [(v.compliance_id, v.vehicle_id)
                           for v in vehicle_data if v.model_year == cy and v.context_size_class == csc]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))
        market_share_results['abs_share_frac_%s' % csc] = market_category_abs_share_frac

    # tally up reg class sales
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [(v.compliance_id, v.vehicle_id)
                           for v in vehicle_data if v.model_year == cy and v.reg_class_id == rc]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))
        market_share_results['abs_share_frac_%s' % rc] = market_category_abs_share_frac

    # plot market category results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mcat in market_categories:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % mcat],
                 **omega_globals.options.MarketClass.get_linestyle(mcat))
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nMarket Category Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(market_categories)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL Mkt Cat Shares.png' % omega_globals.options.session_unique_name)

    # plot market class results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for mc in market_classes:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % mc],
                 **omega_globals.options.MarketClass.get_linestyle(mc))
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nMarket Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(market_classes)
    fig.savefig(
        omega_globals.options.output_folder + '%s ALL Mkt Cls Shares.png' % omega_globals.options.session_unique_name)

    # plot context size class results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % csc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nContext Size Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(NewVehicleMarket.base_year_context_size_class_sales.keys(), ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s ALL CSC Shares.png' %
                omega_globals.options.session_unique_name)

    # plot reg class results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        ax1.plot(calendar_years, market_share_results['abs_share_frac_%s' % rc], '.--')
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]',
              '%s\nReg Class Absolute Market Shares' % omega_globals.options.session_unique_name)
    ax1.legend(omega_globals.options.RegulatoryClasses.reg_classes, ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s ALL RC Shares.png' %
                omega_globals.options.session_unique_name)

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

    global mfr_market_share_results
    if mfr_market_share_results is None:
        mfr_market_share_results = dict()

    # tally up market_category sales
    for mcat in market_categories:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_id_and_market_class_id = [((v.compliance_id, v.vehicle_id), v.market_class_id) for v in vehicle_data
                                              if v.model_year == cy and v.compliance_id == compliance_id]
            for vehicle_id, market_class_id in vehicle_id_and_market_class_id:
                if mcat in market_class_id.split('.'):
                    count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))

        mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, mcat)] = market_category_abs_share_frac

    # tally up market class sales
    for mc in market_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [(v.compliance_id, v.vehicle_id)
                           for v in vehicle_data if v.model_year == cy and v.market_class_id == mc and
                           v.compliance_id == compliance_id]
            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))
        mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, mc)] = market_category_abs_share_frac

    # tally up context size class sales
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [(v.compliance_id, v.vehicle_id)
                           for v in vehicle_data if v.model_year == cy and v.context_size_class == csc
                           and v.compliance_id == compliance_id]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))
        mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, csc)] = market_category_abs_share_frac

    # tally up reg class sales
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        market_category_abs_share_frac = []
        for idx, cy in enumerate(calendar_years):
            count = 0
            vehicle_ids = [(v.compliance_id, v.vehicle_id) for v in vehicle_data if v.model_year == cy
                           and v.reg_class_id == rc and v.compliance_id == compliance_id]

            for vehicle_id in vehicle_ids:
                count += vehicle_annual_data[vehicle_id + tuple([0])]['registered_count']

            market_category_abs_share_frac.append(float(count) / max(1, total_sales[idx]))
        mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, rc)] = market_category_abs_share_frac

    # plot market category results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    labels = []
    for mcat in market_categories:
        if max(mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, mcat)]) > 0:
            ax1.plot(calendar_years, mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, mcat)],
                     **omega_globals.options.MarketClass.get_linestyle(mcat))
            labels += [mcat]
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nMarket Category Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(labels)
    fig.savefig(omega_globals.options.output_folder + '%s %s Mkt Cat Shares.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # plot market class results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    labels = []
    for mc in market_classes:
        if max(mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, mc)]) > 0:
            ax1.plot(calendar_years, mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, mc)],
                     **omega_globals.options.MarketClass.get_linestyle(mc))
            labels += [mc]
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nMarket Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    ax1.legend(labels)
    fig.savefig(omega_globals.options.output_folder + '%s %s Mkt Cls Shares.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # plot context size class results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    labels = []
    for csc in NewVehicleMarket.base_year_context_size_class_sales:
        if max(mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, csc)]) > 0:
            ax1.plot(calendar_years, mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, csc)], '.--')
            labels += [csc]
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nContext Size Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    # ax1.legend(NewVehicleMarket.base_year_context_size_class_sales.keys(), ncol=2, loc='upper center')
    ax1.legend(labels, ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s %s CSC Shares.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    # plot reg class results
    fig, ax1 = figure(omega_globals.options.auto_close_figures)
    labels = []
    for rc in omega_globals.options.RegulatoryClasses.reg_classes:
        if max(mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, rc)]) > 0:
            ax1.plot(calendar_years, mfr_market_share_results['abs_share_frac_%s_%s' % (compliance_id, rc)], '.--')
            labels += [rc]
    ax1.set_ylim(-0.05, 1.05)
    label_xyt(ax1, 'Year', 'Absolute Market Share [%]', '%s %s\nReg Class Absolute Market Shares'
              % (compliance_id, omega_globals.options.session_unique_name))
    # ax1.legend(omega_globals.options.RegulatoryClasses.reg_classes, ncol=2, loc='upper center')
    ax1.legend(labels, ncol=2, loc='upper center')
    fig.savefig(omega_globals.options.output_folder + '%s %s RC Shares.png'
                % (omega_globals.options.session_unique_name, compliance_id))

    return mfr_market_share_results


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

    from context import new_vehicle_market

    total_sales = []
    for cy in calendar_years:
        count = 0
        vad_ids = [(v.compliance_id, v.vehicle_id, 0) for v in vehicle_data if v.model_year == cy]
        for vad_id in vad_ids:
            count += vehicle_annual_data[vad_id]['registered_count']
        total_sales.append(count)

    total_sales = np.array(total_sales)

    manufacturer_sales = dict()
    for compliance_id in compliance_ids:
        manufacturer_sales[compliance_id] = []
        for cy in calendar_years:
            count = 0
            if omega_globals.options.consolidate_manufacturers:
                vad_ids = [('consolidated_OEM', v.vehicle_id, 0) for v in vehicle_data
                           if v.model_year == cy and v.manufacturer_id == compliance_id]
            else:
                vad_ids = [(v.manufacturer_id, v.vehicle_id, 0) for v in vehicle_data
                       if v.model_year == cy and v.manufacturer_id == compliance_id]
            for vad_id in vad_ids:
                count += vehicle_annual_data[vad_id]['registered_count']
            manufacturer_sales[compliance_id].append(count)

    # TOTAL expected sales if ALL vehicle type represented in the base year vehicles file
    # context_sales = np.array(
    #     [consumer.sales_volume.context_new_vehicle_sales(cy)['total'] for cy in calendar_years[1:]])

    for calendar_year in calendar_years:
        context_based_total_sales = 0
        for csc in new_vehicle_market.NewVehicleMarket.base_year_context_size_class_sales:
            context_based_total_sales += \
                new_vehicle_market.NewVehicleMarket.new_vehicle_data(calendar_year, context_size_class=csc)
        new_vehicle_market.NewVehicleMarket.context_based_total_sales[calendar_year] = context_based_total_sales

    # Total expected sales for vehicle types actually represented in the base year vehicles file)
    context_sales = np.array(
        [new_vehicle_market.NewVehicleMarket.context_based_total_sales[cy] for cy in calendar_years[1:]])

    fig, ax1 = fplothg(calendar_years[1:], context_sales / 1e6, '.-',
                       reuse_figure=omega_globals.options.auto_close_figures)

    ax1.plot(calendar_years, total_sales / 1e6)

    for manufacturer in manufacturer_sales:
        ax1.plot(calendar_years, np.array(manufacturer_sales[manufacturer]) / 1e6)

    ax1.legend(['context sales', 'sales'] + list(manufacturer_sales.keys()))
    label_xyt(ax1, 'Year', 'Sales [millions]', '%s\nTotal Sales Versus Calendar Year\n Total Sales %.2f Million' % (
        omega_globals.options.session_unique_name, total_sales.sum() / 1e6))

    fig.savefig(omega_globals.options.output_folder + '%s ALL Sales v Year.png' % omega_globals.options.session_unique_name)

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
        """
        Draw credit transfer arrow from source model year to destination model year

        Args:
            src_x (float): credit source x-axis value
            src_y (float): credit source y-axis value
            dest_x (float): credit destination x-axis value
            dest_y (float): credit destination y-axis value

        """
        ax1.annotate('', xy=(dest_x, dest_y), xycoords='data',
                     xytext=(src_x, src_y), textcoords='data',
                     arrowprops=dict(arrowstyle='-|>', color='green', shrinkA=2, shrinkB=2,
                                     patchA=None, patchB=None, connectionstyle="arc3,rad=1"))

    def draw_expiration_arrow(src_x, src_y, color):
        """
        Draw credit expiration arrow

        Args:
            src_x (float): credit source x-axis value
            src_y (float): credit source y-axis value
            color (str): color name or format

        """
        ax1.annotate('', xy=(src_x, src_y), xycoords='data',
                     xytext=(src_x, ax1.get_ylim()[0]), textcoords='data',
                     arrowprops=dict(arrowstyle='<-', color=color, shrinkA=5, shrinkB=5,
                                     patchA=None, patchB=None, connectionstyle="arc3,rad=0"))

    from producer.manufacturer_annual_data import ManufacturerAnnualData

    target_co2e_Mg = ManufacturerAnnualData.get_target_co2e_Mg(compliance_id)
    calendar_year_cert_co2e_Mg = ManufacturerAnnualData.get_calendar_year_cert_co2e_Mg(compliance_id)
    model_year_cert_co2e_Mg = ManufacturerAnnualData.get_model_year_cert_co2e_Mg(compliance_id)
    total_cost_billions = ManufacturerAnnualData.get_total_cost_billions(compliance_id)
    # compliance chart
    ax1, fig = plot_compliance(calendar_years, compliance_id, target_co2e_Mg, calendar_year_cert_co2e_Mg,
                               model_year_cert_co2e_Mg)
    label_xyt(ax1, 'Year', 'CO2e [Mg]', '%s %s\nCert and Compliance Versus Year\n Total Cost $%.2f Billion' % (
        compliance_id, omega_globals.options.session_unique_name, total_cost_billions))

    target_co2e_Mg_dict = dict(zip(calendar_years, target_co2e_Mg))
    calendar_year_cert_co2e_Mg_dict = dict(zip(calendar_years, calendar_year_cert_co2e_Mg))
    model_year_cert_co2e_Mg_dict = dict(zip(calendar_years, model_year_cert_co2e_Mg))

    if credit_history is not None:
        for _, t in credit_history.transaction_log.iterrows():
            try:
                if type(t.credit_destination) is not str and t.model_year in calendar_year_cert_co2e_Mg_dict:
                    draw_transfer_arrow(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year],
                                    t.credit_destination, target_co2e_Mg_dict[t.credit_destination])
                elif type(t.credit_destination) is not str and t.model_year not in calendar_year_cert_co2e_Mg_dict:
                    ax1.plot(t.model_year, target_co2e_Mg_dict[calendar_years[0]], 'o', color='orange')
                    draw_transfer_arrow(t.model_year, target_co2e_Mg_dict[calendar_years[0]],
                                        t.credit_destination, model_year_cert_co2e_Mg_dict[t.credit_destination])
                    ax1.set_xlim(calendar_years[0] - 5, ax1.get_xlim()[1])
                elif t.credit_destination == 'EXPIRATION' and t.model_year in calendar_year_cert_co2e_Mg_dict:
                    # expiration of analysis year credits
                    if compliance_id != 'consolidated_OEM' and omega_globals.pass_num > 0:
                        color = '#929591'
                    else:
                        color = 'red'
                    draw_expiration_arrow(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], color=color)
                elif t.credit_destination == 'EXPIRATION' and t.model_year not in calendar_year_cert_co2e_Mg_dict:
                    # exipration of credit banked prior to first analysis year
                    ax1.plot(t.model_year, target_co2e_Mg_dict[calendar_years[0]], 'o', color='orange')
                    if compliance_id != 'consolidated_OEM' and omega_globals.pass_num > 0:
                        color = '#929591'
                    else:
                        color = 'red'
                    draw_expiration_arrow(t.model_year, target_co2e_Mg_dict[calendar_years[0]], color=color)
                else:  # "PAST_DUE"
                    if compliance_id != 'consolidated_OEM' and omega_globals.pass_num > 0:
                        color = '#929591'
                    else:
                        color = 'red'
                    ax1.plot(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], 'x', color=color)
                    plt.scatter(t.model_year, calendar_year_cert_co2e_Mg_dict[t.model_year], s=80, facecolors='none',
                                edgecolors=color)
            except:
                pass

    fig.savefig(omega_globals.options.output_folder + '%s %s Cert Mg v Year.png' %
                (omega_globals.options.session_unique_name, compliance_id))

    return calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg, target_co2e_Mg


def plot_compliance(calendar_years, compliance_id, target_co2e_Mg, calendar_year_cert_co2e_Mg, model_year_cert_co2e_Mg):
    """
    Plot compliance target Mg, calendar year cert Mg and model year compliance Mg

    Args:
        calendar_years (list): list of years to plot
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        target_co2e_Mg (list): list of target co2e Mg
        calendar_year_cert_co2e_Mg (list): list of calendar year cert co2e Mg
        model_year_cert_co2e_Mg (list): list of model year compliance co2e Mg

    """
    fig, ax1 = fplothg(calendar_years, target_co2e_Mg, 'o-', reuse_figure=omega_globals.options.auto_close_figures)
    if compliance_id == 'consolidated_OEM' and omega_globals.pass_num > 0:
        ax1.plot(calendar_years, calendar_year_cert_co2e_Mg, '.-', color='#929591')
        ax1.plot(calendar_years, model_year_cert_co2e_Mg, '-')
        ax1.legend(['target_co2e_Mg', 'model_year_pre_trading_cert_co2e_Mg', 'model_year_cert_co2e_Mg'])

    elif omega_globals.pass_num > 0:
        ax1.plot(calendar_years, calendar_year_cert_co2e_Mg, 'r.-')
        ax1.plot(calendar_years, model_year_cert_co2e_Mg, '-', color='#929591')
        ax1.legend(['target_co2e_Mg', 'calendar_year_cert_co2e_Mg', 'model_year_pre_trading_cert_co2e_Mg'])

    else:
        ax1.plot(calendar_years, calendar_year_cert_co2e_Mg, 'r.-')
        ax1.plot(calendar_years, model_year_cert_co2e_Mg, '-')
        ax1.legend(['target_co2e_Mg', 'calendar_year_cert_co2e_Mg', 'model_year_cert_co2e_Mg'])

    return ax1, fig


def plot_iteration(iteration_log, compliance_id):
    """
    Plot producer-consumer iteration data.

    Args:
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        iteration_log (DataFrame): iteration data

    """
    iteration_log = iteration_log.loc[iteration_log['compliance_id'] == compliance_id]

    for iteration in [0, -1]:
        if iteration == 0:
            iteration_label = 'initial'
        else:
            iteration_label = 'final'

        year_iter_labels = \
            ['%d_%d' % (cy - 2000, it) for cy, it in
             zip(iteration_log['calendar_year'][iteration_log['cross_subsidy_iteration_num'] == iteration],
                 (iteration_log['producer_consumer_iteration_num']
                 [iteration_log['cross_subsidy_iteration_num'] == iteration]))]

        for mc in market_classes:
            if 'consumer_abs_share_frac_%s' % mc in iteration_log:
                plt.figure()
                plt.plot(year_iter_labels,
                         iteration_log['producer_abs_share_frac_%s' % mc][
                             iteration_log['cross_subsidy_iteration_num'] == iteration], '--', linewidth=3)
                plt.xticks(rotation=90)
                plt.plot(year_iter_labels,
                         iteration_log['consumer_abs_share_frac_%s' % mc][
                             iteration_log['cross_subsidy_iteration_num'] == iteration])
                plt.title('%s %s iteration %s' % (compliance_id, mc, iteration_label))
                plt.grid()
                plt.legend(['producer_abs_share_frac_%s' % mc, 'consumer_abs_share_frac_%s' % mc])
                plt.ylim([0, 1])
                plt.savefig('%s%s %s Iter %s %s.png' % (
                    omega_globals.options.output_folder, omega_globals.options.session_unique_name, compliance_id,
                    mc, iteration_label))

        first_logged = iteration_log.loc[iteration_log['cross_subsidy_iteration_num'] == 0]
        last_logged = iteration_log.loc[iteration_log['cross_subsidy_iteration_num'] == -1]

        plt.figure()
        if iteration == -1:
            for mc in market_classes:
                if 'consumer_generalized_cost_dollars_%s' % mc in last_logged:
                    plt.plot(last_logged['calendar_year'],
                             last_logged['consumer_generalized_cost_dollars_%s' % mc], '.-')
        else:
            for mc in market_classes:
                if 'consumer_generalized_cost_dollars_%s' % mc in first_logged:
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
                if 'cost_multiplier_%s' % mc in last_logged:
                    plt.plot(last_logged['calendar_year'],
                         last_logged['cost_multiplier_%s' % mc], '.-')
        else:
            for mc in market_classes:
                if 'cost_multiplier_%s' % mc in first_logged:
                    plt.plot(first_logged['calendar_year'],
                             first_logged['cost_multiplier_%s' % mc], '.-')
        plt.legend(['cost_multiplier_%s' % mc for mc in market_classes])
        plt.ylabel('Cost Multiplier')
        plt.title('%s Producer Cost Multipliers %s' % (compliance_id, iteration_label))
        plt.grid()
        plt.savefig('%s%s %s Producer Cost Multipliers %s.png' % (
            omega_globals.options.output_folder, omega_globals.options.session_unique_name, compliance_id,
            iteration_label))

    fig, ax1 = fplothg(last_logged['calendar_year'], last_logged['producer_consumer_iteration_num'], '.-',
                       reuse_figure=omega_globals.options.auto_close_figures)
    label_xyt(ax1, '', 'Iteration [#]', '%s Iteration mean = %.2f' %
              (compliance_id, last_logged['producer_consumer_iteration_num'].mean()))

    fig.savefig('%s%s %s Iter Counts.png' % (omega_globals.options.output_folder,
                                             omega_globals.options.session_unique_name, compliance_id))

    # plot producer initial share and g/mi decisions
    plt.figure()
    for mc in market_classes:
        plt.plot(first_logged['calendar_year'], first_logged['producer_abs_share_frac_%s' % mc], '.-')
    plt.title('%s Producer Initial Absolute Market Shares' % compliance_id)
    plt.grid()
    plt.legend(['producer_abs_share_frac_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer Abs Shares Initial.png' % (omega_globals.options.output_folder,
                                                             omega_globals.options.session_unique_name, compliance_id))

    # plot producer initial share and g/mi decisions
    plt.figure()
    for mc in market_classes:
        plt.plot(last_logged['calendar_year'], last_logged['producer_abs_share_frac_%s' % mc], '.-')
    plt.title('%s Producer Final Absolute Market Shares' % compliance_id)
    plt.grid()
    plt.legend(['producer_abs_share_frac_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer Abs Shares Final.png' % (omega_globals.options.output_folder,
                                                             omega_globals.options.session_unique_name, compliance_id))

    plt.figure()
    for mc in market_classes:
        plt.plot(first_logged['calendar_year'], first_logged['average_onroad_direct_co2e_gpmi_%s' % mc], '.-')
    plt.title('%s Producer Initial CO2e g/mi' % compliance_id)
    plt.grid()
    plt.legend(['average_onroad_direct_co2e_gpmi_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer CO2e gpmi Initial.png' % (omega_globals.options.output_folder,
                                                            omega_globals.options.session_unique_name, compliance_id))

    plt.figure()
    for mc in market_classes:
        plt.plot(last_logged['calendar_year'], last_logged['average_onroad_direct_co2e_gpmi_%s' % mc], '.-')
    plt.title('%s Producer Final CO2e g/mi' % compliance_id)
    plt.grid()
    plt.legend(['average_onroad_direct_co2e_gpmi_%s' % mc for mc in market_classes])
    plt.savefig('%s%s %s Producer CO2e gpmi Final.png' % (omega_globals.options.output_folder,
                                                            omega_globals.options.session_unique_name, compliance_id))
