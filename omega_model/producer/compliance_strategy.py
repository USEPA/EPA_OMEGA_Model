"""

Compliance strategy implements the producer search algorithm to find a low-cost combination of technologies (via
vehicle CO2e g/mi) and market shares that achieve a targeted certification outcome.


----

**CODE**

"""


from omega_model import *
import numpy as np
import consumer

cache = dict()


def create_tech_and_share_sweeps(calendar_year, market_class_dict, winning_combos, share_range, consumer_response,
                                 node_name='', verbose=False):
    """

    Args:
        calendar_year:
        market_class_dict:
        winning_combos:
        share_range:
        consumer_response:
        node_name:
        verbose:

    Returns:

    """

    child_df_list = []

    children = list(market_class_dict)

    for k in market_class_dict:
        if verbose:
            print('processing ' + k)
        if type(market_class_dict[k]) is dict:
            # process subtree
            child_df_list.append(
                create_tech_and_share_sweeps(calendar_year, market_class_dict[k],
                                             winning_combos, share_range,
                                             consumer_response,
                                             node_name=k))
        else:
            # process leaf
            for new_veh in market_class_dict[k]:
                df = pd.DataFrame()

                if share_range == 1.0:
                    new_veh.tech_option_iteration_num = 0  # reset vehicle tech option progression

                if new_veh.fueling_class == 'ICE':
                    num_tech_options = omega_globals.options.producer_num_tech_options_per_ice_vehicle
                else:
                    num_tech_options = omega_globals.options.producer_num_tech_options_per_bev_vehicle

                veh_min_co2e_gpmi = new_veh.get_min_co2e_gpmi()

                if omega_globals.options.allow_backsliding:
                    veh_max_co2e_gpmi = new_veh.get_max_co2e_gpmi()
                else:
                    veh_max_co2e_gpmi = new_veh.cert_co2e_grams_per_mile

                if winning_combos is not None:
                    co2_gpmi_options = np.array([])
                    for idx, combo in winning_combos.iterrows():

                        if (combo['veh_%s_sales' % new_veh.vehicle_id] > 0) or (new_veh.tech_option_iteration_num > 0):
                            new_veh.tech_option_iteration_num += 1

                        tech_share_range = omega_globals.options.producer_convergence_factor ** new_veh.tech_option_iteration_num
                        veh_co2e_gpmi = combo['veh_%s_co2e_gpmi' % new_veh.vehicle_id]
                        min_co2e_gpmi = max(veh_min_co2e_gpmi, veh_co2e_gpmi * (1 - tech_share_range))
                        max_co2e_gpmi = min(veh_max_co2e_gpmi, veh_co2e_gpmi * (1 + tech_share_range))
                        co2_gpmi_options = \
                            np.append(np.append(co2_gpmi_options,
                                      np.linspace(min_co2e_gpmi, max_co2e_gpmi, num=num_tech_options)), veh_co2e_gpmi)

                    if num_tech_options == 1:
                        co2_gpmi_options = [veh_max_co2e_gpmi]
                    else:
                        co2_gpmi_options = np.unique(co2_gpmi_options)  # filter out redundant tech options
                else:  # first producer pass, generate full range of options
                    if num_tech_options == 1:
                        co2_gpmi_options = [veh_max_co2e_gpmi]
                    else:
                        co2_gpmi_options = np.linspace(veh_min_co2e_gpmi, veh_max_co2e_gpmi, num=num_tech_options)

                tech_cost_options = new_veh.get_cost_from_cost_curve(co2_gpmi_options)
                tech_generalized_cost_options = new_veh.get_generalized_cost_from_cost_curve(co2_gpmi_options)
                tech_kwh_options = new_veh.get_kwh_pmi(co2_gpmi_options)

                df['veh_%s_co2e_gpmi' % new_veh.vehicle_id] = co2_gpmi_options
                df['veh_%s_kwh_pmi' % new_veh.vehicle_id] = tech_kwh_options
                df['veh_%s_cost_dollars' % new_veh.vehicle_id] = tech_cost_options
                df['veh_%s_generalized_cost_dollars' % new_veh.vehicle_id] = tech_generalized_cost_options

                child_df_list.append(df)

    if consumer_response is None:
        # generate producer desired market shares for responsive market sectors
        producer_prefix = 'producer_share_frac_'
        if node_name:
            share_column_names = [producer_prefix + node_name + '.' + c for c in children]
        else:
            share_column_names = [producer_prefix + c for c in children]

        if all(s in consumer.responsive_market_categories for s in children):
            from context.production_constraints import ProductionConstraints
            from policy.required_sales_share import RequiredSalesShare

            min_constraints = dict()
            max_constraints = dict()
            for c in share_column_names:
                production_min = ProductionConstraints.get_minimum_share(calendar_year, c.replace(producer_prefix, ''))
                production_max = ProductionConstraints.get_maximum_share(calendar_year, c.replace(producer_prefix, ''))
                required_zev_share = RequiredSalesShare.get_minimum_share(calendar_year, c.replace(producer_prefix, ''))

                max_constraints[c] = production_max
                min_constraints[c] = min(production_max, max(required_zev_share, production_min))

            if share_range == 1.0:
                # span the whole space of shares
                sales_share_df = partition(share_column_names, num_levels=omega_globals.options.producer_num_market_share_options,
                                           min_constraints=min_constraints, max_constraints=max_constraints)
            else:
                # narrow search span to a range of shares around the winners
                from common.omega_functions import generate_constrained_nearby_shares
                sales_share_df = generate_constrained_nearby_shares(share_column_names, winning_combos, share_range,
                                                                    omega_globals.options.producer_num_market_share_options,
                                                                    min_constraints=min_constraints,
                                                                    max_constraints=max_constraints)
        else:
            sales_share_df = pd.DataFrame()
            for c, cn in zip(children, share_column_names):
                sales_share_df[cn] = [consumer.sales_volume.context_new_vehicle_sales(calendar_year)[c] /
                                      consumer.sales_volume.context_new_vehicle_sales(calendar_year)['total']]
    else:
        # inherit absolute market shares from consumer response
        if node_name:
            abs_share_column_names = ['producer_abs_share_frac_' + node_name + '.' + c for c in children]
        else:
            abs_share_column_names = ['producer_abs_share_frac_' + c for c in children]

        sales_share_df = pd.DataFrame()
        share_total = 0
        for cn in abs_share_column_names:
            if cn.replace('producer', 'consumer') in consumer_response:
                sales_share_df[cn] = [consumer_response[cn.replace('producer', 'consumer')]]
                share_total += sales_share_df[cn]

    if verbose:
        print('combining ' + str(children))
    tech_combos_df = pd.DataFrame()
    for df in child_df_list:
        tech_combos_df = cartesian_prod(tech_combos_df, df)

    if not sales_share_df.empty:
        tech_share_combos_df = cartesian_prod(tech_combos_df, sales_share_df)
    else:
        tech_share_combos_df = tech_combos_df

    return tech_share_combos_df


def apply_production_decision_to_composite_vehicles(composite_vehicles, selected_production_decision):
    """

    Args:
        composite_vehicles:
        selected_production_decision:

    Returns:

    """
    import copy

    composite_vehicles = copy.deepcopy(composite_vehicles)
    from producer.vehicles import VehicleAttributeCalculations

    # assign co2 values and sales to vehicles...
    for new_veh in composite_vehicles:
        new_veh.cert_co2e_grams_per_mile = selected_production_decision['veh_%s_co2e_gpmi' % new_veh.vehicle_id]
        new_veh.cert_direct_kwh_per_mile = selected_production_decision['veh_%s_kwh_pmi' % new_veh.vehicle_id]
        new_veh.initial_registered_count = selected_production_decision['veh_%s_sales' % new_veh.vehicle_id]
        VehicleAttributeCalculations.perform_attribute_calculations(new_veh)
        new_veh.decompose()
        new_veh.set_new_vehicle_mfr_cost_dollars()
        new_veh.set_cert_target_co2e_Mg()
        new_veh.set_cert_co2e_Mg()

    return composite_vehicles


def search_production_options(compliance_id, calendar_year, producer_decision_and_response, iteration_num,
                              strategic_target_offset_Mg):
    """

    Args:
        compliance_id:
        calendar_year:
        producer_decision_and_response:
        iteration_num:

    Returns:

    """
    candidate_production_decisions = None
    producer_compliance_possible = False

    if (calendar_year == omega_globals.options.analysis_initial_year) and (iteration_num == 0):
        cache.clear()

    producer_iteration_log = \
        omega_log.IterationLog('%s%d_%d_producer_iteration_log.csv' % (
            omega_globals.options.output_folder, calendar_year, iteration_num))

    continue_search = True
    search_iteration = 0
    best_candidate_production_decision = None

    while continue_search and search_iteration < omega_globals.options.producer_max_iterations:
        share_range = omega_globals.options.producer_convergence_factor ** search_iteration

        composite_vehicles, market_class_tree, context_based_total_sales = \
            create_composite_vehicles(calendar_year, compliance_id)

        tech_and_share_sweeps = create_tech_and_share_sweeps(calendar_year, market_class_tree,
                                                             candidate_production_decisions, share_range,
                                                             producer_decision_and_response)

        production_options = create_production_options(calendar_year, composite_vehicles, tech_and_share_sweeps,
                                                       context_based_total_sales)

        # insert code to cull production options based on policy here #

        production_options['share_range'] = share_range

        production_options['strategic_compliance_ratio'] = \
            (production_options['total_cert_co2e_megagrams'] - strategic_target_offset_Mg) / \
            np.maximum(1, production_options['total_target_co2e_megagrams'])

        production_options['strategic_target_offset_Mg'] = strategic_target_offset_Mg

        candidate_production_decisions, compliance_possible = \
            select_candidate_manufacturing_decisions(production_options, calendar_year, search_iteration,
                                                     producer_iteration_log, strategic_target_offset_Mg)

        producer_compliance_possible |= compliance_possible

        if (best_candidate_production_decision is None) or \
                (candidate_production_decisions['strategic_compliance_error'].min() <
                 best_candidate_production_decision['strategic_compliance_error'].min()):
            best_candidate_production_decision = \
                candidate_production_decisions.loc[candidate_production_decisions['strategic_compliance_error'].idxmin()]

        if 'producer' in omega_globals.options.verbose_console:
            omega_log.logwrite(('%d_%d_%d' % (calendar_year, iteration_num,
                                              search_iteration)).ljust(12) + 'SR:%f CR:%.10f' % (share_range,
                                    best_candidate_production_decision['strategic_compliance_ratio']), echo_console=True)

        search_iteration += 1

        continue_search = abs(1 - best_candidate_production_decision['strategic_compliance_ratio']) > \
                           omega_globals.options.producer_iteration_tolerance

    if 'producer' in omega_globals.options.verbose_console:
        omega_log.logwrite('PRODUCER FINAL COMPLIANCE DELTA %f' % abs(1 - best_candidate_production_decision['strategic_compliance_ratio']),
                           echo_console=True)

        omega_log.logwrite('Target GHG Offset Mg %.0f, Actual GHG Offset Mg %.0f' % (-best_candidate_production_decision['strategic_target_offset_Mg'], best_candidate_production_decision['total_credits_co2e_megagrams']),
                           echo_console=True)

        omega_log.logwrite('Target Compliance Ratio %3.3f, Actual Compliance Ratio %3.3f' %
                           ((best_candidate_production_decision['total_cert_co2e_megagrams']-best_candidate_production_decision['strategic_target_offset_Mg'])/max(1, best_candidate_production_decision['total_target_co2e_megagrams']),
                            best_candidate_production_decision['strategic_compliance_ratio']),
                           echo_console=True)

    selected_production_decision = pd.to_numeric(best_candidate_production_decision)

    selected_production_decision = \
        selected_production_decision.rename({'strategic_compliance_ratio': 'initial_strategic_compliance_ratio'})

    # log the final iteration, as opposed to the winning iteration:
    selected_production_decision['producer_search_iteration'] = search_iteration - 1

    if 'producer' in omega_globals.options.verbose_console:
        for mc in omega_globals.options.MarketClass.market_classes:
            omega_log.logwrite(('%d producer_abs_share_frac_%s' % (calendar_year, mc)).ljust(50) + '= %s' %
                               (selected_production_decision['producer_abs_share_frac_%s' % mc]), echo_console=True)
        omega_log.logwrite('', echo_console=True)

    composite_vehicles = apply_production_decision_to_composite_vehicles(composite_vehicles,
                                                                         selected_production_decision)

    return composite_vehicles, selected_production_decision, market_class_tree, \
           producer_compliance_possible


def create_composite_vehicles(calendar_year, compliance_id):
    """

    Args:
        calendar_year:
        compliance_id:

    Returns:

    """
    from producer.vehicles import VehicleFinal, Vehicle, CompositeVehicle
    from consumer.sales_volume import context_new_vehicle_sales
    from context.new_vehicle_market import NewVehicleMarket

    cache_key = calendar_year
    if cache_key not in cache:
        # pull in last year's vehicles:
        manufacturer_prior_vehicles = VehicleFinal.get_compliance_vehicles(calendar_year - 1, compliance_id)

        Vehicle.reset_vehicle_ids()

        manufacturer_vehicles = []
        # update each vehicle and calculate compliance target for each vehicle
        for prior_veh in manufacturer_prior_vehicles:
            new_veh = Vehicle()
            new_veh.convert_vehicle(prior_veh, model_year=calendar_year)
            manufacturer_vehicles.append(new_veh)
            new_veh.initial_registered_count = new_veh.market_share

        # sum([new_veh.market_share for new_veh in manufacturer_vehicles]) == 2.0 at this point due to intentional
        # duplicate entries for "alternative" powertrain vehicles, but "market_share" is used for relative proportions

        total_sales = 0  # sales total by compliance id size class share
        for csc in NewVehicleMarket.context_size_classes: # for each context size class
            total_sales += \
                NewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=csc) \
                * VehicleFinal.mfr_base_year_size_class_share[compliance_id][csc]

        # group by non responsive market group
        from consumer import non_responsive_market_categories

        nrmc_dict = dict()
        for nrmc in non_responsive_market_categories:
            nrmc_dict[nrmc] = []
        for new_veh in manufacturer_vehicles:
            nrmc_dict[new_veh.non_responsive_market_group].append(new_veh)

        # distribute non responsive market class sales to manufacturer_vehicles by relative market share
        for nrmc in non_responsive_market_categories:
            nrmc_initial_registered_count = context_new_vehicle_sales(calendar_year)[nrmc]
            distribute_by_attribute(nrmc_dict[nrmc], nrmc_initial_registered_count,
                                    weight_by='market_share',
                                    distribute_to='initial_registered_count')

            # print('%s:%s' % (nrmc, nrmc_initial_registered_count))

        # calculate new vehicle absolute market share based on vehicle size mix from context
        for new_veh in manufacturer_vehicles:
            new_veh.market_share = \
                new_veh.initial_registered_count * \
                VehicleFinal.mfr_base_year_size_class_share[compliance_id][new_veh.context_size_class] / \
                total_sales

        # # group by context size class and legacy reg class
        # csc_dict = dict()
        # for new_veh in manufacturer_vehicles:
        #     if new_veh.context_size_class not in csc_dict:
        #         csc_dict[new_veh.context_size_class] = dict()
        #     if new_veh.legacy_reg_class_id not in csc_dict[new_veh.context_size_class]:
        #         csc_dict[new_veh.context_size_class][new_veh.legacy_reg_class_id] = []
        #     csc_dict[new_veh.context_size_class][new_veh.legacy_reg_class_id].append(new_veh)
        #
        # # distribute context size class sales to manufacturer_vehicles by relative market share
        # for csc in csc_dict: # for each context size class
        #     for lrc in csc_dict[csc]: # for each context (legacy) reg class
        #         projection_initial_registered_count = \
        #             ContextNewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=csc,
        #                                                       context_reg_class=lrc)
        #
        #         print('%s:%s:%s' % (csc, lrc, projection_initial_registered_count))
        #
        #         distribute_by_attribute(csc_dict[csc][lrc], projection_initial_registered_count,
        #                             weight_by='market_share',
        #                             distribute_to='initial_registered_count')

        # group by context size class
        csc_dict = dict()
        for new_veh in manufacturer_vehicles:
            if new_veh.context_size_class not in csc_dict:
                csc_dict[new_veh.context_size_class] = []
            csc_dict[new_veh.context_size_class].append(new_veh)

        # distribute context size class sales to manufacturer_vehicles by relative market share
        for csc in csc_dict: # for each context size class
            projection_initial_registered_count = \
                NewVehicleMarket.new_vehicle_sales(calendar_year, context_size_class=csc) \
                * VehicleFinal.mfr_base_year_size_class_share[compliance_id][csc]

            distribute_by_attribute(csc_dict[csc], projection_initial_registered_count,
                                    weight_by='market_share',
                                    distribute_to='initial_registered_count')

        # calculate new vehicle market share based on vehicle size mix from context
        for new_veh in manufacturer_vehicles:
            new_veh.market_share = new_veh.initial_registered_count / total_sales

        # sum([new_veh.market_share for new_veh in manufacturer_vehicles]) == 1.0 at this point,
        # sum([new_veh.initial_registered_count for new_veh in manufacturer_vehicles]) = total_sales

        # group by market class / reg class
        mctrc = dict()
        for mc in omega_globals.options.MarketClass.market_classes:
            mctrc[mc] = {'sales': 0}
            for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                mctrc[mc][rc] = []
        for new_veh in manufacturer_vehicles:
            mctrc[new_veh.market_class_id][new_veh.reg_class_id].append(new_veh)
            mctrc[new_veh.market_class_id]['sales'] += new_veh.initial_registered_count

        CompositeVehicle.reset_vehicle_ids()
        manufacturer_composite_vehicles = []
        for mc in mctrc:
            for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                if mctrc[mc][rc]:
                    cv = CompositeVehicle(mctrc[mc][rc], calendar_year, weight_by='market_share')
                    cv.vehicle_id = mc + '.' + rc
                    cv.composite_vehicle_share_frac = cv.initial_registered_count / mctrc[mc]['sales']
                    manufacturer_composite_vehicles.append(cv)

        # get empty market class tree
        market_class_tree = omega_globals.options.MarketClass.get_market_class_tree()

        # populate tree with vehicle objects
        for new_veh in manufacturer_composite_vehicles:
            omega_globals.options.MarketClass.populate_market_classes(market_class_tree, new_veh.market_class_id, new_veh)

        cache[cache_key] = {'manufacturer_composite_vehicles': manufacturer_composite_vehicles,
                            'market_class_tree': market_class_tree,
                            'total_sales': total_sales}
    else:
        # pull cached composite vehicles (avoid recompute of composite frontiers, etc)
        manufacturer_composite_vehicles = cache[cache_key]['manufacturer_composite_vehicles']
        market_class_tree = cache[cache_key]['market_class_tree']
        total_sales = cache[cache_key]['total_sales']

    return manufacturer_composite_vehicles, market_class_tree, total_sales


def finalize_production(calendar_year, compliance_id, manufacturer_composite_vehicles, winning_combo):
    """

    Args:
        calendar_year:
        compliance_id:
        manufacturer_composite_vehicles:
        winning_combo:

    Returns:

    """
    from producer.manufacturer_annual_data import ManufacturerAnnualData
    from producer.vehicles import VehicleFinal

    manufacturer_new_vehicles = []

    # pull final vehicles from composite vehicles
    for cv in manufacturer_composite_vehicles:
        # update sales, which may have changed due to consumer response and iteration
        cv.initial_registered_count = winning_combo['veh_%s_sales' % cv.vehicle_id]
        if ((omega_globals.options.log_producer_iteration_years == 'all') or
            (calendar_year in omega_globals.options.log_producer_iteration_years)) and 'producer' in omega_globals.options.verbose_console:
            cv.cost_curve.to_csv(omega_globals.options.output_folder + '%s_%s_cost_curve.csv' % (cv.model_year, cv.vehicle_id))
        cv.decompose()  # propagate sales to source vehicles
        for v in cv.vehicle_list:
            # if 'producer' in o2.options.verbose_console:
            #     v.cost_cloud.to_csv(o2.options.output_folder + '%s_%s_cost_cloud.csv' % (v.model_year, v.vehicle_id))
            new_veh = VehicleFinal()
            new_veh.convert_vehicle(v)
            manufacturer_new_vehicles.append(new_veh)

    omega_globals.session.add_all(manufacturer_new_vehicles)

    cert_target_co2e_Mg = VehicleFinal.calc_cert_target_co2e_Mg(calendar_year, compliance_id)

    cert_co2e_Mg = VehicleFinal.calc_cert_co2e_Mg(calendar_year, compliance_id)

    ManufacturerAnnualData. \
        create_manufacturer_annual_data(model_year=calendar_year,
                                        compliance_id=compliance_id,
                                        cert_target_co2e_Mg=cert_target_co2e_Mg,
                                        calendar_year_cert_co2e_Mg=cert_co2e_Mg,
                                        manufacturer_vehicle_cost_dollars=winning_combo['total_cost_dollars'],
                                        )
    omega_globals.session.flush()


def create_production_options(calendar_year, manufacturer_composite_vehicles, tech_and_share_combinations,
                              total_sales):
    """
    on the first time through, from the producer module, total_sales is based on context, market shares
    come from the producer desired market shares
    on the second time through, from the omega2 module, total_sales is determined by sales response, market shares
    come from the consumer demanded market shares...

    Args:
        calendar_year:
        manufacturer_composite_vehicles:
        tech_and_share_combinations:
        total_sales:

    Returns:
        production_options

    """

    production_options = tech_and_share_combinations

    total_target_co2e_Mg = 0
    total_cert_co2e_Mg = 0
    total_cost_dollars = 0
    total_generalized_cost_dollars = 0

    for composite_veh in manufacturer_composite_vehicles:
        # assign sales to vehicle based on market share fractions and reg class share fractions
        market_class = composite_veh.market_class_id

        if ('consumer_abs_share_frac_%s' % market_class) in production_options:
            composite_veh_sales = total_sales * production_options['consumer_abs_share_frac_%s' % market_class]

        elif ('producer_abs_share_frac_%s' % market_class) in production_options:
            composite_veh_sales = total_sales * production_options['producer_abs_share_frac_%s' % market_class]

        else:
            substrs = market_class.split('.')
            chain = []

            for i in range(len(substrs)):
                str = 'producer_share_frac_'
                for j in range(i + 1):
                    str = str + substrs[j] + '.' * (j != i)
                chain.append(str)

            composite_veh_sales = total_sales

            for c in chain:
                composite_veh_sales = composite_veh_sales * production_options[c]

            if ('producer_abs_share_frac_%s' % market_class) not in production_options:
                production_options['producer_abs_share_frac_%s' % market_class] = composite_veh_sales / total_sales
            else:
                production_options['producer_abs_share_frac_%s' % market_class] += composite_veh_sales / total_sales

        composite_veh_sales = composite_veh_sales * composite_veh.composite_vehicle_share_frac
        production_options['veh_%s_sales' % composite_veh.vehicle_id] = composite_veh_sales

        # calculate vehicle total cost
        composite_veh_total_cost_dollars = composite_veh_sales * \
                                           production_options['veh_%s_cost_dollars' % composite_veh.vehicle_id]

        production_options['veh_%s_total_cost_dollars' % composite_veh.vehicle_id] = composite_veh_total_cost_dollars

        composite_veh_total_generalized_cost_dollars = composite_veh_sales * \
                                                       production_options['veh_%s_generalized_cost_dollars' %
                                                                          composite_veh.vehicle_id]

        # calculate cert and target Mg for the vehicle
        composite_veh_cert_co2_gpmi = production_options['veh_%s_co2e_gpmi' % composite_veh.vehicle_id]

        composite_veh_cert_co2e_Mg = composite_veh.normalized_cert_co2e_Mg * composite_veh_cert_co2_gpmi * \
                                     composite_veh_sales

        composite_veh_target_co2e_Mg = composite_veh.normalized_cert_target_co2e_Mg * composite_veh_sales

        production_options['veh_%s_cert_co2e_megagrams' % composite_veh.vehicle_id] = composite_veh_cert_co2e_Mg
        production_options['veh_%s_target_co2e_megagrams' % composite_veh.vehicle_id] = composite_veh_target_co2e_Mg

        # update totals
        total_target_co2e_Mg += composite_veh_target_co2e_Mg
        total_cert_co2e_Mg += composite_veh_cert_co2e_Mg
        total_cost_dollars += composite_veh_total_cost_dollars
        total_generalized_cost_dollars += composite_veh_total_generalized_cost_dollars

    production_options['total_target_co2e_megagrams'] = total_target_co2e_Mg
    production_options['total_cert_co2e_megagrams'] = total_cert_co2e_Mg
    production_options['total_cost_dollars'] = total_cost_dollars
    production_options['total_generalized_cost_dollars'] = total_generalized_cost_dollars
    production_options['total_credits_co2e_megagrams'] = total_target_co2e_Mg - total_cert_co2e_Mg
    production_options['total_sales'] = total_sales

    return production_options


def plot_tech_share_combos_total(calendar_year, tech_share_combos_total):
    """

    Args:
        calendar_year:
        tech_share_combos_total:

    """
    import matplotlib.pyplot as plt
    plt.figure()
    plt.plot(tech_share_combos_total['total_cert_co2e_megagrams'],
             tech_share_combos_total['total_cost_dollars'], '.')
    plt.plot(tech_share_combos_total['total_target_co2e_megagrams'],
             tech_share_combos_total['total_cost_dollars'], 'r.')
    plt.xlabel('CO2e WITHOUT Offset [Mg]')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['total_cert_co2e_megagrams'] - tech_share_combos_total['strategic_target_offset_Mg'],
             tech_share_combos_total['total_cost_dollars'], '.')
    plt.plot(tech_share_combos_total['total_target_co2e_megagrams'],
             tech_share_combos_total['total_cost_dollars'], 'r.')
    plt.xlabel('CO2e WITH Offset [Mg]')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['strategic_compliance_ratio'],
             tech_share_combos_total['total_cost_dollars'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['strategic_compliance_ratio'],
             tech_share_combos_total['total_generalized_cost_dollars'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Generalized Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(tech_share_combos_total['strategic_compliance_ratio'],
             tech_share_combos_total['total_credits_co2e_megagrams'] +
             tech_share_combos_total['strategic_target_offset_Mg'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Credits WITH Offset [Mg]')
    plt.title('%s' % calendar_year)
    plt.grid()


def select_candidate_manufacturing_decisions(tech_share_combos_total, calendar_year, search_iteration,
                                             producer_iteration_log, strategic_target_offset_Mg):
    """

    Args:
        tech_share_combos_total:
        calendar_year:
        search_iteration:
        producer_iteration_log:

    Returns:

    """
    # tech_share_combos_total = tech_share_combos_total.drop_duplicates('total_credits_co2e_megagrams')

    cost_name = 'total_generalized_cost_dollars'

    mini_df = pd.DataFrame()
    mini_df['total_credits_with_offset_co2e_megagrams'] = \
        tech_share_combos_total['total_credits_co2e_megagrams'] + strategic_target_offset_Mg
    mini_df['total_cost_dollars'] = tech_share_combos_total['total_cost_dollars']
    mini_df['total_generalized_cost_dollars'] = tech_share_combos_total['total_generalized_cost_dollars']
    mini_df['strategic_compliance_ratio'] = tech_share_combos_total['strategic_compliance_ratio']

    tech_share_combos_total['producer_search_iteration'] = search_iteration
    tech_share_combos_total['winner'] = False
    tech_share_combos_total['strategic_compliance_error'] = abs(1-tech_share_combos_total['strategic_compliance_ratio'])  # / tech_share_combos_total['total_generalized_cost_dollars']
    tech_share_combos_total['slope'] = 0

    compliant_tech_share_options = mini_df[(mini_df['total_credits_with_offset_co2e_megagrams']) >= 0].copy()
    non_compliant_tech_share_options = mini_df[(mini_df['total_credits_with_offset_co2e_megagrams']) < 0].copy()

    if not compliant_tech_share_options.empty and not non_compliant_tech_share_options.empty:
        # tech share options straddle compliance target
        compliance_possible = True

        # grab lowest-cost compliant option
        lowest_cost_compliant_tech_share_option = tech_share_combos_total.loc[[compliant_tech_share_options[cost_name].idxmin()]]

        # grab best non-compliant option
        non_compliant_tech_share_options['weighted_slope'] = \
            non_compliant_tech_share_options['strategic_compliance_ratio'] * \
            ((non_compliant_tech_share_options[cost_name] - float(lowest_cost_compliant_tech_share_option[cost_name])) /
            (non_compliant_tech_share_options['strategic_compliance_ratio'] - float(lowest_cost_compliant_tech_share_option['strategic_compliance_ratio'])))

        best_non_compliant_tech_share_option = tech_share_combos_total.loc[[non_compliant_tech_share_options['weighted_slope'].idxmin()]]

        if float(best_non_compliant_tech_share_option[cost_name]) > float(lowest_cost_compliant_tech_share_option[cost_name]):
            # cost cloud up-slopes from left to right, calculate slope relative to best non-compliant option
            compliant_tech_share_options['weighted_slope'] = \
                compliant_tech_share_options['strategic_compliance_ratio'] * \
                ((compliant_tech_share_options[cost_name] - float(best_non_compliant_tech_share_option[cost_name])) /
                (compliant_tech_share_options['strategic_compliance_ratio'] - float(best_non_compliant_tech_share_option['strategic_compliance_ratio'])))

            best_compliant_tech_share_option = tech_share_combos_total.loc[[compliant_tech_share_options['weighted_slope'].idxmax()]]
        else:
            best_compliant_tech_share_option = lowest_cost_compliant_tech_share_option

        winning_combos = pd.DataFrame.append(best_compliant_tech_share_option, best_non_compliant_tech_share_option)

    elif compliant_tech_share_options.empty:
        # grab best non-compliant option (least under-compliance)
        compliance_possible = False
        winning_combos = tech_share_combos_total.loc[[mini_df['total_credits_with_offset_co2e_megagrams'].idxmax()]]

    else: # non_compliant_tech_share_options.empty:
        # grab best compliant option (least over-compliant OR lowest cost?)
        compliance_possible = True
        # least over-compliant:
        winning_combos = tech_share_combos_total.loc[[mini_df['total_credits_with_offset_co2e_megagrams'].idxmin()]]
        # lowest cost:
        # winning_combos = tech_share_combos_total.loc[[[cost_name].idxmin()]]

    if (omega_globals.options.log_producer_iteration_years == 'all') or (calendar_year in omega_globals.options.log_producer_iteration_years):
        if 'producer' in omega_globals.options.verbose_console:
            tech_share_combos_total.loc[winning_combos.index, 'winner'] = True
            if omega_globals.options.slice_tech_combo_cloud_tables:
                tech_share_combos_total = tech_share_combos_total[tech_share_combos_total['strategic_compliance_ratio'] <= 1.2]
            producer_iteration_log.write(tech_share_combos_total)
        else:
            winning_combos['winner'] = True
            producer_iteration_log.write(winning_combos)

    return winning_combos.copy(), compliance_possible


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
