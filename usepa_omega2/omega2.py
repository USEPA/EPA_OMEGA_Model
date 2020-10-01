"""
omega2.py
=========

OMEGA2 top level code

"""

print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *
from omega_plot import *
import os

from usepa_omega2.file_eye_oh import gui_comm


def run_postproc():
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from vehicle_annual_data import VehicleAnnualData
    from market_classes import MarketClass
    import pandas as pd

    calendar_years = sql_unpack_result(o2.session.query(ManufacturerAnnualData.calendar_year).all())
    cert_target_co2_Mg = sql_unpack_result(o2.session.query(ManufacturerAnnualData.cert_target_co2_Mg).all())
    cert_co2_Mg = sql_unpack_result(o2.session.query(ManufacturerAnnualData.cert_co2_Mg).all())
    total_cost_billions = float(
        o2.session.query(func.sum(ManufacturerAnnualData.manufacturer_vehicle_cost_dollars)).scalar()) / 1e9

    # compliance chart
    fig, ax1 = fplothg(calendar_years, cert_target_co2_Mg, '.-')
    ax1.plot(calendar_years, cert_co2_Mg, '.-')
    label_xyt(ax1, 'Year', 'CO2 Mg', '%s\nCompliance Versus Calendar Year\n Total Cost $%.2f Billion' % (
        o2.options.session_unique_name, total_cost_billions))
    fig.savefig(o2.options.output_folder + '%s Compliance v Year' % o2.options.session_unique_name)

    bev_non_hauling_share_frac = sql_unpack_result(
        o2.session.query(ManufacturerAnnualData.bev_non_hauling_share_frac).all())
    ice_non_hauling_share_frac = sql_unpack_result(
        o2.session.query(ManufacturerAnnualData.ice_non_hauling_share_frac).all())
    bev_hauling_share_frac = sql_unpack_result(o2.session.query(ManufacturerAnnualData.bev_hauling_share_frac).all())
    ice_hauling_share_frac = sql_unpack_result(o2.session.query(ManufacturerAnnualData.ice_hauling_share_frac).all())

    fig, ax1 = fplothg(calendar_years, bev_non_hauling_share_frac, '.-')
    ax1.plot(calendar_years, ice_non_hauling_share_frac, '.-')
    ax1.plot(calendar_years, bev_hauling_share_frac, '.-')
    ax1.plot(calendar_years, ice_hauling_share_frac, '.-')
    label_xyt(ax1, 'Year', 'Market Share Frac', '%s\nMarket Shares' % o2.options.session_unique_name)
    ax1.legend(['bev_non_hauling', 'ice_non_hauling', 'bev_hauling', 'ice_hauling'])
    fig.savefig(o2.options.output_folder + '%s Market Shares' % o2.options.session_unique_name)

    # cost/vehicle chart
    fig, ax1 = figure()
    average_cost_data = dict()
    for hc in hauling_classes:
        average_cost_data[hc] = []
        for cy in calendar_years:
            average_cost_data[hc].append(o2.session.query(
                func.sum(Vehicle.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(Vehicle.model_year == cy).
                                         filter(Vehicle.hauling_class == hc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_years, average_cost_data[hc])

    for mc in MarketClass.market_classes:
        average_cost_data[mc] = []
        for cy in calendar_years:
            average_cost_data[mc].append(o2.session.query(
                func.sum(Vehicle.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                         filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                         filter(Vehicle.model_year == cy).
                                         filter(Vehicle.market_class_ID == mc).
                                         filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_years, average_cost_data[mc])

    average_cost_data['total'] = []
    for cy in calendar_years:
        average_cost_data['total'].append(o2.session.query(
            func.sum(Vehicle.new_vehicle_mfr_cost_dollars * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                          filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                          filter(Vehicle.model_year == cy).
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
                func.sum(Vehicle.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                             filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                             filter(Vehicle.model_year == cy).
                                             filter(Vehicle.hauling_class == hc).
                                             filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_years, average_co2_gpmi_data[hc])

    for mc in MarketClass.market_classes:
        average_co2_gpmi_data[mc] = []
        for cy in calendar_years:
            average_co2_gpmi_data[mc].append(o2.session.query(
                func.sum(Vehicle.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
                func.sum(VehicleAnnualData.registered_count)).
                                             filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                             filter(Vehicle.model_year == cy).
                                             filter(Vehicle.market_class_ID == mc).
                                             filter(VehicleAnnualData.age == 0).scalar())
        ax1.plot(calendar_years, average_co2_gpmi_data[mc])

    average_co2_gpmi_data['total'] = []
    for cy in calendar_years:
        average_co2_gpmi_data['total'].append(o2.session.query(
            func.sum(Vehicle.cert_CO2_grams_per_mile * VehicleAnnualData.registered_count) /
            func.sum(VehicleAnnualData.registered_count)).
                                              filter(Vehicle.vehicle_ID == VehicleAnnualData.vehicle_ID).
                                              filter(Vehicle.model_year == cy).
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
    from manufacturers import Manufacturer
    import producer
    from market_classes import MarketClass
    import vehicles
    from consumer.sales_share_gcam import get_demanded_shares

    for manufacturer in o2.session.query(Manufacturer.manufacturer_ID).all():
        manufacturer_ID = manufacturer[0]
        print(manufacturer_ID)

        iteration_log = pd.DataFrame()
        for calendar_year in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
            iterate = True
            consumer_market_share_demand = None
            iteration_num = 0
            while iterate:
                print('%d_%d' % (calendar_year, iteration_num))
                candidate_mfr_new_vehicles, winning_combo = producer.run_compliance_model(manufacturer_ID, calendar_year, consumer_market_share_demand)

                # group vehicles by market class
                market_class_dict = MarketClass.get_market_class_dict()
                for new_veh in candidate_mfr_new_vehicles:
                    market_class_dict[new_veh.market_class_ID].add(new_veh)

                for mc in MarketClass.market_classes:
                    market_class_vehicles = market_class_dict[mc]
                    winning_combo['average_%s_co2_gpmi' % mc] = vehicles.sales_weight(market_class_vehicles,
                                                                                          'cert_CO2_grams_per_mile')
                    winning_combo['average_%s_cost' % mc] = vehicles.sales_weight(market_class_vehicles,
                                                                                      'new_vehicle_mfr_cost_dollars')

                consumer_market_share_demand = get_demanded_shares(winning_combo, calendar_year)

                generic_winning_combo_with_market_share_demand = cleanup_vehicle_ids(candidate_mfr_new_vehicles,
                                                            consumer_market_share_demand,
                                                            winning_combo)

                consumer_market_share_demand.loc['iteration'] = iteration_num
                consumer_market_share_demand.loc['calendar_year'] = calendar_year

                iteration_log = iteration_log.append(cleanup_vehicle_ids(candidate_mfr_new_vehicles,
                                                            consumer_market_share_demand,
                                                            winning_combo))

                # decide whether to iterate or not
                iterate = iteration_num < o2.options.producer_consumer_max_iterations

                if iterate:
                    # drop candidates from database, they are no longer needed or desired
                    for cv in candidate_mfr_new_vehicles:
                        o2.session.delete(cv)

                iteration_num = iteration_num + 1

            producer.finalize_production(calendar_year, manufacturer_ID, candidate_mfr_new_vehicles, winning_combo)

        iteration_log.to_csv('%sproducer_consumer_iteration_log.csv' % o2.options.output_folder)

        import matplotlib.pyplot as plt
        for mc in market_class_dict:
            foo = ['%d_%d' % (cy-2000, it) for cy, it in zip(iteration_log['calendar_year'], iteration_log['iteration'])]
            # foo = ['%d' % it for it in iteration_log['iteration']]
            plt.figure()
            plt.plot(foo, iteration_log['desired_%s_share_frac' % mc])
            plt.plot(foo, iteration_log['demanded_%s_share_frac' % mc])
            plt.title('%s iteration' % mc)
            plt.grid()
            plt.savefig('%s%s iteration.png' % (o2.options.output_folder, mc))


def cleanup_vehicle_ids(candidate_mfr_new_vehicles, iteration_log, winning_combo):
    for i, id in enumerate([v.vehicle_ID for v in candidate_mfr_new_vehicles]):
        rename_dict = dict()
        veh_cols = [(c, c.replace(str(id), str(i))) for c in winning_combo.keys() if 'veh_%d' % id in c]
        for vc in veh_cols:
            rename_dict[vc[0]] = vc[1]
        iteration_log = iteration_log.rename(rename_dict, axis='columns')
    return iteration_log


def run_omega(o2_options, single_shot=False, profile=False):
    import traceback
    import time

    o2_options.start_time = time.time()

    print('OMEGA2 greets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    print('run_omega(%s)' % o2_options.session_name)

    # set up global variables:
    o2.options = o2_options
    init_omega_db()
    o2.engine.echo = o2.options.verbose
    omega_log.init_logfile()

    from fuels import Fuel
    from fuels_context import FuelsContext
    from market_classes import MarketClass
    from cost_curves import CostCurve
    from cost_clouds import CostCloud
    from demanded_shares_gcam import DemandedSharesGCAM
    from manufacturers import Manufacturer
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import Vehicle
    from vehicle_annual_data import VehicleAnnualData
    from consumer.reregistration_fixed_by_age import ReregistrationFixedByAge
    from consumer.annual_vmt_fixed_by_age import AnnualVMTFixedByAge
    import consumer.sales as consumer
    import producer
    from consumer.sales_share_gcam import get_demanded_shares

    fileio.validate_folder(o2.options.output_folder)

    if o2.options.GHG_standard == 'flat':
        from GHG_standards_flat import GHGStandardFlat
    else:
        from GHG_standards_footprint import GHGStandardFootprint

    from GHG_standards_fuels import GHGStandardFuels

    o2.options.producer_calculate_generalized_cost = producer.calculate_generalized_cost
    o2.options.consumer_calculate_generalized_cost = consumer.calculate_generalized_cost

    SQABase.metadata.create_all(o2.engine)

    init_fail = []
    try:
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)
        init_fail = init_fail + FuelsContext.init_database_from_file(
            o2.options.fuels_context_file, verbose=o2.options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)

        if o2.options.cost_file_type == 'curves':
            init_fail = init_fail + CostCurve.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)
        else:
            init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=o2.options.verbose)

        if o2.options.GHG_standard == 'flat':
            init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2.options.ghg_standards_file,
                                                                            verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFlat
        else:
            init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2.options.ghg_standards_file,
                                                                                 verbose=o2.options.verbose)
            o2.options.GHG_standard = GHGStandardFootprint

        init_fail = init_fail + GHGStandardFuels.init_database_from_file(o2.options.ghg_standards_fuels_file,
                                                                         verbose=o2.options.verbose)

        init_fail = init_fail + DemandedSharesGCAM.init_database_from_file(
            o2.options.demanded_shares_file, verbose=o2.options.verbose)
        init_fail = init_fail + Manufacturer.init_database_from_file(o2.options.manufacturers_file,
                                                                     verbose=o2.options.verbose)
        init_fail = init_fail + Vehicle.init_database_from_file(o2.options.vehicles_file, verbose=o2.options.verbose)

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
        o2.options.analysis_initial_year = int(o2.session.query(func.max(Vehicle.model_year)).scalar()) + 1
        # final year = last year of cost curve data
        o2.options.analysis_final_year = int(o2.session.query(func.max(CostCurve.model_year)).scalar())

        if not init_fail:
            # dump_database_to_csv(engine, o2.options.database_dump_folder, verbose=False)

            if profile:
                import cProfile
                import re
                cProfile.run('run_producer_consumer()', filename='omega2_profile.dmp')
            else:
                run_producer_consumer()

            if not single_shot:
                gui_comm('%s: Post Processing ...' % o2.options.session_name)

            session_summary_results = run_postproc()

            # for cy in range(o2.options.analysis_initial_year, o2.options.analysis_final_year + 1):
            #      market_share_results_cy = get_demanded_shares(
            #          session_summary_results[session_summary_results.calendar_year==cy].iloc[0], cy)
            #
            # # add market share results to session_summary
            # for mc in MarketClass.market_classes:
            #     session_summary_results['demanded_%s_share' % mc] = \
            #         sql_unpack_result(o2.session.query(DemandedSharesGCAM.demanded_share).
            #             filter(DemandedSharesGCAM.calendar_year <= o2.options.analysis_final_year).
            #             filter(DemandedSharesGCAM.market_class_ID == mc))

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

            dump_omega_db_to_csv(o2.options.database_dump_folder)

            omega_log.end_logfile("\nSession Complete")

            # o2.session.close()
            o2.engine.dispose()
            o2.engine = None
            # o2.session = None
            o2.options = None
        else:
            omega_log.logwrite("\n#INIT FAIL")
            omega_log.end_logfile("\nSession Fail")

    except Exception as e:
        if init_fail:
            omega_log.logwrite("\n#INIT FAIL")
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        print("### Check OMEGA log for error messages ###")
        gui_comm("### Check OMEGA log for error messages ###")
        gui_comm("### RUNTIME FAIL ###")
        omega_log.end_logfile("\nSession Fail")


if __name__ == "__main__":
    try:
        import producer
        run_omega(OMEGARuntimeOptions(), single_shot=True, profile=False)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
