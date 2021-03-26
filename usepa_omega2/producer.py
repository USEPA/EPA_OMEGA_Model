"""
producer.py
===========

Producer module, could potentially be part of the manufacturers.py, but maybe it's best if it's separate and
the manufacturers.py is primarily related to the schema and class methods...

"""


from usepa_omega2 import *
import numpy as np
import consumer

cache = dict()


def calculate_generalized_cost(vehicle, cost_curve, co2_name, cost_name):
    """

    Args:
        vehicle: an object of class Vehicle
        cost_curve: the cost curve (frontier) of that vehicle

    Returns:
        A cost curve modified by generalized cost factors

    """

    from consumer.market_classes import MarketClass

    producer_generalized_cost_fuel_years, \
    producer_generalized_cost_annual_vmt = \
        MarketClass.get_producer_generalized_cost_attributes(
            vehicle.market_class_ID,
            ['producer_generalized_cost_fuel_years',
             'producer_generalized_cost_annual_vmt',
             ])

    vehicle_cost = cost_curve[cost_name]

    grams_co2_per_unit = vehicle.fuel_tailpipe_co2_emissions_grams_per_unit()
    kwh_per_mi = vehicle.cert_kWh_per_mile
    liquid_generalized_fuel_cost = 0
    electric_generalized_fuel_cost = 0

    # TODO: calculate liquid and electric fuel costs separately and then add them...?
    if grams_co2_per_unit > 0:
        liquid_generalized_fuel_cost = \
            (vehicle.retail_fuel_price_dollars_per_unit(vehicle.model_year) / grams_co2_per_unit *
             vehicle.cert_CO2_grams_per_mile *
             producer_generalized_cost_annual_vmt *
             producer_generalized_cost_fuel_years)

    if kwh_per_mi > 0:
        electric_generalized_fuel_cost = (kwh_per_mi *
                                         vehicle.retail_fuel_price_dollars_per_unit(vehicle.model_year) *
                                         producer_generalized_cost_annual_vmt * producer_generalized_cost_fuel_years)

    generalized_fuel_cost = liquid_generalized_fuel_cost + electric_generalized_fuel_cost

    cost_curve[cost_name.replace('mfr', 'mfr_generalized')] = generalized_fuel_cost + vehicle_cost

    return cost_curve


def create_compliance_options(calendar_year, market_class_dict, producer_bev_share, share_range, consumer_response,
                              node_name='', verbose=False):
    """

    Args:
        calendar_year:
        market_class_dict:
        producer_bev_share:
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
                create_compliance_options(calendar_year, market_class_dict[k],
                                          producer_bev_share, share_range,
                                          consumer_response,
                                          node_name=k))
        else:
            # process leaf
            for new_veh in market_class_dict[k]:
                df = pd.DataFrame()

                if new_veh.fueling_class == 'ICE':
                    num_tech_options = o2.options.producer_num_tech_options_per_ice_vehicle
                else:
                    num_tech_options = o2.options.producer_num_tech_options_per_bev_vehicle

                # if consumer_bev_share is None or new_veh.fueling_class == 'BEV':
                min_co2_gpmi = new_veh.get_min_co2_gpmi()

                if o2.options.allow_backsliding:
                    max_co2_gpmi = new_veh.get_max_co2_gpmi()
                else:
                    max_co2_gpmi = new_veh.cert_CO2_grams_per_mile

                if producer_bev_share is not None:  # and new_veh.fueling_class != 'BEV':
                    co2_gpmi_options = np.array([])
                    for idx, combo in producer_bev_share.iterrows():
                        veh_co2_gpmi = combo['veh_%s_co2_gpmi' % new_veh.vehicle_ID]
                        min_co2_gpmi = max(min_co2_gpmi, veh_co2_gpmi * (1 - share_range))
                        max_co2_gpmi = min(max_co2_gpmi, veh_co2_gpmi * (1 + share_range))
                        co2_gpmi_options = \
                            np.append(np.append(co2_gpmi_options,
                                      np.linspace(min_co2_gpmi, max_co2_gpmi, num=num_tech_options)), veh_co2_gpmi)

                    if num_tech_options == 1:
                        co2_gpmi_options = [max_co2_gpmi]
                    else:
                        co2_gpmi_options = np.unique(co2_gpmi_options)  # filter out redundant tech options
                else:  # first producer pass, generate normal range of options
                    if num_tech_options == 1:
                        co2_gpmi_options = [max_co2_gpmi]
                    else:
                        co2_gpmi_options = np.linspace(min_co2_gpmi, max_co2_gpmi, num=num_tech_options)

                tech_cost_options = new_veh.get_cost(co2_gpmi_options)
                tech_generalized_cost_options = new_veh.get_generalized_cost(co2_gpmi_options)
                tech_kwh_options = new_veh.get_kwh_pmi(co2_gpmi_options)

                df['veh_%s_co2_gpmi' % new_veh.vehicle_ID] = co2_gpmi_options
                df['veh_%s_kwh_pmi' % new_veh.vehicle_ID] = tech_kwh_options
                df['veh_%s_cost_dollars' % new_veh.vehicle_ID] = tech_cost_options
                df['veh_%s_generalized_cost_dollars' % new_veh.vehicle_ID] = tech_generalized_cost_options

                child_df_list.append(df)

    if consumer_response is None:
        # generate producer desired market shares for responsive market sectors
        producer_prefix = 'producer_share_frac_'
        if node_name:
            share_column_names = [producer_prefix + node_name + '.' + c for c in children]
        else:
            share_column_names = [producer_prefix + c for c in children]

        if all(s in consumer.responsive_market_categories for s in children):
            from production_constraints import ProductionConstraints
            from required_zev_share import RequiredZevShare

            min_constraints = dict()
            max_constraints = dict()
            for c in share_column_names:
                production_min = ProductionConstraints.get_minimum_share(calendar_year, c.replace(producer_prefix, ''))
                production_max = ProductionConstraints.get_maximum_share(calendar_year, c.replace(producer_prefix, ''))
                required_zev_share = RequiredZevShare.get_minimum_share(calendar_year, c.replace(producer_prefix, ''))

                max_constraints[c] = production_max
                min_constraints[c] = min(production_max, max(required_zev_share, production_min))

            if share_range == 1.0:
                # span the whole space of shares
                sales_share_df = partition(share_column_names, num_levels=num_tech_options,
                                           min_constraints=min_constraints, max_constraints=max_constraints)
            else:
                # narrow search span to a range of shares around the winners
                from omega_functions import generate_constrained_nearby_shares
                sales_share_df = generate_constrained_nearby_shares(share_column_names, producer_bev_share, share_range,
                                                        o2.options.producer_num_market_share_options,
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


def run_compliance_model(manufacturer_ID, calendar_year, consumer_bev_share, iteration_num):
    """

    Args:
        manufacturer_ID:
        calendar_year:
        consumer_bev_share:
        iteration_num:

    Returns:

    """
    winning_combos = None
    producer_compliance_possible = False

    if (calendar_year == o2.options.analysis_initial_year) and (iteration_num == 0):
        cache.clear()

    producer_iteration_log = \
        omega_log.IterationLog('%s%d_%d_producer_iteration_log.csv' % (o2.options.output_folder, calendar_year, iteration_num))

    iterate_producer = True
    producer_iteration = 0
    best_combo = None

    while iterate_producer and producer_iteration < o2.options.producer_max_iterations:
        share_range = 0.33**producer_iteration

        manufacturer_composite_vehicles, market_class_tree = get_initial_vehicle_data(calendar_year, manufacturer_ID)

        tech_share_combos_total = create_compliance_options(calendar_year, market_class_tree,
                                                            winning_combos, share_range,
                                                            consumer_bev_share)

        calculate_tech_share_combos_total(calendar_year, manufacturer_composite_vehicles, tech_share_combos_total)

        tech_share_combos_total['share_range'] = share_range
        tech_share_combos_total['compliance_ratio'] = tech_share_combos_total['total_combo_cert_co2_megagrams'] / \
                                           tech_share_combos_total['total_combo_target_co2_megagrams']
        # save initial compliance ratio, it gets overwrriten during the consumer iteration
        tech_share_combos_total['compliance_ratio_producer'] = tech_share_combos_total['compliance_ratio']

        # if calendar_year == 2020:
        #     tech_share_combos_total.to_csv(o2.options.output_folder + '%s_tech_share_combos_total.csv' % calendar_year)

        winning_combos, compliance_possible = \
            select_winning_combos(tech_share_combos_total, calendar_year, producer_iteration, producer_iteration_log)

        producer_compliance_possible = producer_compliance_possible or compliance_possible

        if (best_combo is None) or (winning_combos['compliance_score'].min() < best_combo['compliance_score'].min()):
            best_combo = winning_combos.loc[winning_combos['compliance_score'].idxmin()]

        if 'producer' in o2.options.verbose_console:
            omega_log.logwrite(('%d_%d_%d' % (calendar_year, iteration_num,
                                    producer_iteration)).ljust(12) + 'SR:%f CR:%.10f' % (share_range,
                                    best_combo['compliance_ratio']), echo_console=True)

        producer_iteration += 1

        iterate_producer = abs(1 - best_combo['compliance_ratio']) > o2.options.producer_iteration_tolerance

    if 'producer' in o2.options.verbose_console:
        omega_log.logwrite('PRODUCER FINAL COMPLIANCE DELTA %f' % abs(1 - best_combo['compliance_ratio']),
                           echo_console=True)

    winning_combo = pd.to_numeric(best_combo)

    if 'producer' in o2.options.verbose_console:
        from consumer.market_classes import MarketClass
        for mc in MarketClass.market_classes:
            omega_log.logwrite(('%d producer_abs_share_frac_%s' % (calendar_year, mc)).ljust(50) + '= %s' % (winning_combo['producer_abs_share_frac_%s' % mc]), echo_console=True)
        omega_log.logwrite('', echo_console=True)

    import copy
    manufacturer_composite_vehicles = copy.deepcopy(manufacturer_composite_vehicles)

    # assign co2 values and sales to vehicles...
    for new_veh in manufacturer_composite_vehicles:
        new_veh.cert_CO2_grams_per_mile = winning_combo['veh_%s_co2_gpmi' % new_veh.vehicle_ID]
        new_veh.cert_kWh_per_mile = winning_combo['veh_%s_kwh_pmi' % new_veh.vehicle_ID]
        new_veh.initial_registered_count = winning_combo['veh_%s_sales' % new_veh.vehicle_ID]
        new_veh.decompose()
        new_veh.set_new_vehicle_mfr_cost_dollars()
        new_veh.set_cert_target_CO2_Mg()
        new_veh.set_cert_CO2_Mg()

    return manufacturer_composite_vehicles, winning_combo, market_class_tree, producer_compliance_possible


def get_initial_vehicle_data(calendar_year, manufacturer_ID):
    """

    Args:
        calendar_year:
        manufacturer_ID:

    Returns:

    """
    from vehicles import VehicleFinal, Vehicle
    from consumer.market_classes import MarketClass, populate_market_classes

    cache_key = calendar_year
    if cache_key not in cache:
        # pull in last year's vehicles:
        manufacturer_prior_vehicles = VehicleFinal.get_manufacturer_vehicles(calendar_year - 1, manufacturer_ID)

        Vehicle.reset_vehicle_IDs()

        manufacturer_vehicles = []
        # update each vehicle and calculate compliance target for each vehicle
        for prior_veh in manufacturer_prior_vehicles:
            new_veh = Vehicle()
            new_veh.inherit_vehicle(prior_veh, model_year=calendar_year)
            # TODO: update cert g/mi curve values based on policy upstream and whatever the heck else?? or is it done before here...? when processing the original clouds??
            manufacturer_vehicles.append(new_veh)

        # aggregate by market class / reg class
        mctrc = dict()
        for mc in MarketClass.market_classes:
            mctrc[mc] = {'sales': 0}
            for rc in reg_classes:
                mctrc[mc][rc] = []
        for new_veh in manufacturer_vehicles:
            mctrc[new_veh.market_class_ID][new_veh.reg_class_ID].append(new_veh)
            mctrc[new_veh.market_class_ID]['sales'] = mctrc[new_veh.market_class_ID]['sales'] + new_veh.initial_registered_count

        from vehicles import CompositeVehicle
        CompositeVehicle.reset_vehicle_IDs()
        manufacturer_composite_vehicles = []
        for mc in mctrc:
            for rc in reg_classes:
                if mctrc[mc][rc]:
                    cv = CompositeVehicle(mctrc[mc][rc], calendar_year)
                    cv.reg_class_market_share_frac = cv.initial_registered_count / mctrc[mc]['sales']
                    manufacturer_composite_vehicles.append(cv)

        # get empty market class tree
        market_class_tree = MarketClass.get_market_class_tree()

        # populate tree with vehicle objects
        for new_veh in manufacturer_composite_vehicles:
            populate_market_classes(market_class_tree, new_veh.market_class_ID, new_veh)

        cache[cache_key] = {'manufacturer_composite_vehicles': manufacturer_composite_vehicles,
                            'market_class_tree': market_class_tree}
    else:
        # pull cached composite vehicles (avoid recompute of composite frontiers, etc)
        manufacturer_composite_vehicles = cache[cache_key]['manufacturer_composite_vehicles']
        market_class_tree = cache[cache_key]['market_class_tree']

    return manufacturer_composite_vehicles, market_class_tree


def finalize_production(calendar_year, manufacturer_ID, manufacturer_composite_vehicles, winning_combo):
    """

    Args:
        calendar_year:
        manufacturer_ID:
        manufacturer_composite_vehicles:
        winning_combo:

    Returns:

    """
    from manufacturer_annual_data import ManufacturerAnnualData
    from vehicles import VehicleFinal

    manufacturer_new_vehicles = []

    # pull final vehicles from composite vehicles
    for cv in manufacturer_composite_vehicles:
        # update sales, which may have changed due to consumer response and iteration
        cv.initial_registered_count = winning_combo['veh_%s_sales' % cv.vehicle_ID]
        if 'producer' in o2.options.verbose_console:
            cv.cost_curve.to_csv(o2.options.output_folder + '%s_%s_cost_curve.csv' % (cv.model_year, cv.vehicle_ID))
        cv.decompose()  # propagate sales to source vehicles
        for v in cv.vehicle_list:
            # if 'producer' in o2.options.verbose_console:
            #     v.cost_curve.to_csv(o2.options.output_folder + '%s_%s_cost_curve.csv' % (v.model_year, v.vehicle_ID))
            #     v.cost_cloud.to_csv(o2.options.output_folder + '%s_%s_cost_cloud.csv' % (v.model_year, v.vehicle_ID))
            new_veh = VehicleFinal()
            new_veh.inherit_vehicle(v)
            manufacturer_new_vehicles.append(new_veh)

    o2.session.add_all(manufacturer_new_vehicles)

    cert_target_co2_Mg = VehicleFinal.calc_cert_target_CO2_Mg(calendar_year, manufacturer_ID)

    ManufacturerAnnualData. \
        create_manufacturer_annual_data(calendar_year=calendar_year,
                                        manufacturer_ID=manufacturer_ID,
                                        cert_target_co2_Mg=cert_target_co2_Mg,
                                        cert_co2_Mg=winning_combo['total_combo_cert_co2_megagrams'],
                                        manufacturer_vehicle_cost_dollars=winning_combo['total_combo_cost_dollars'],
                                        )
    o2.session.flush()


def calculate_tech_share_combos_total(calendar_year, manufacturer_composite_vehicles, tech_share_combos_total,
                                      total_sales=None):
    """
    on the first time through, from the producer module, total_sales = None => use context sales, market shares
    come from the producer desired market shares
    on the second time through, from the omega2 module, total_sales is determined by sales response, market shares
    come from the consumer demanded market shares...

    Args:
        calendar_year:
        manufacturer_composite_vehicles:
        tech_share_combos_total:
        total_sales:

    Returns:

    """

    if total_sales is None:
        total_sales = consumer.sales_volume.context_new_vehicle_sales(calendar_year)['total']
        tech_share_combos_total['context_sales'] = total_sales

    total_target_co2_Mg = 0
    total_cert_co2_Mg = 0
    total_cost_dollars = 0
    total_generalized_cost_dollars = 0
    for new_veh in manufacturer_composite_vehicles:
        # assign sales to vehicle based on market share fractions and reg class share fractions
        market_class = new_veh.market_class_ID

        if ('consumer_abs_share_frac_%s' % market_class) in tech_share_combos_total:
            vehicle_sales = total_sales * tech_share_combos_total['consumer_abs_share_frac_%s' % market_class]
        elif ('producer_abs_share_frac_%s' % market_class) in tech_share_combos_total:
            vehicle_sales = total_sales * tech_share_combos_total['producer_abs_share_frac_%s' % market_class]
        else:
            substrs = market_class.split('.')
            chain = []
            for i in range(len(substrs)):
                str = 'producer_share_frac_'
                for j in range(i + 1):
                    str = str + substrs[j] + '.' * (j != i)
                chain.append(str)
            vehicle_sales = total_sales
            for c in chain:
                vehicle_sales = vehicle_sales * tech_share_combos_total[c]

            if ('producer_abs_share_frac_%s' % market_class) not in tech_share_combos_total:
                tech_share_combos_total['producer_abs_share_frac_%s' % market_class] = vehicle_sales / total_sales
            else:
                tech_share_combos_total['producer_abs_share_frac_%s' % market_class] += vehicle_sales / total_sales

        vehicle_sales = vehicle_sales * new_veh.reg_class_market_share_frac
        tech_share_combos_total['veh_%s_sales' % new_veh.vehicle_ID] = vehicle_sales

        # calculate vehicle total cost
        vehicle_total_cost_dollars = vehicle_sales * tech_share_combos_total['veh_%s_cost_dollars' % new_veh.vehicle_ID]
        tech_share_combos_total['veh_%s_total_cost_dollars' % new_veh.vehicle_ID] = vehicle_total_cost_dollars

        vehicle_total_generalized_cost_dollars = vehicle_sales * tech_share_combos_total['veh_%s_generalized_cost_dollars' % new_veh.vehicle_ID]
        tech_share_combos_total['veh_%s_generalized_total_cost_dollars' % new_veh.vehicle_ID] = vehicle_total_generalized_cost_dollars


        # calculate cert and target Mg for the vehicle
        co2_gpmi = tech_share_combos_total['veh_%s_co2_gpmi' % new_veh.vehicle_ID]

        cert_co2_Mg = o2.options.GHG_standard.calculate_cert_co2_Mg(new_veh, co2_gpmi_variants=co2_gpmi,
                                                                    sales_variants=vehicle_sales)
        target_co2_Mg = o2.options.GHG_standard.calculate_target_co2_Mg(new_veh,
                                                                        sales_variants=vehicle_sales)
        tech_share_combos_total['veh_%s_cert_co2_megagrams' % new_veh.vehicle_ID] = cert_co2_Mg
        tech_share_combos_total['veh_%s_target_co2_megagrams' % new_veh.vehicle_ID] = target_co2_Mg
        # update totals
        total_target_co2_Mg = total_target_co2_Mg + target_co2_Mg
        total_cert_co2_Mg = total_cert_co2_Mg + cert_co2_Mg
        total_cost_dollars += vehicle_total_cost_dollars
        total_generalized_cost_dollars += vehicle_total_generalized_cost_dollars

    tech_share_combos_total['total_combo_target_co2_megagrams'] = total_target_co2_Mg
    tech_share_combos_total['total_combo_cert_co2_megagrams'] = total_cert_co2_Mg
    tech_share_combos_total['total_combo_cost_dollars'] = total_cost_dollars
    tech_share_combos_total['total_combo_generalized_cost_dollars'] = total_generalized_cost_dollars
    tech_share_combos_total['total_combo_credits_co2_megagrams'] = total_target_co2_Mg - total_cert_co2_Mg
    tech_share_combos_total['total_sales'] = total_sales


def select_winning_combos(tech_share_combos_total, calendar_year, producer_iteration, producer_iteration_log):
    """

    Args:
        tech_share_combos_total:
        calendar_year:
        producer_iteration:
        producer_iteration_log:

    Returns:

    """
    # tech_share_combos_total = tech_share_combos_total.drop_duplicates('total_combo_credits_co2_megagrams')
    mini_df = pd.DataFrame()
    mini_df['total_combo_credits_co2_megagrams'] = tech_share_combos_total['total_combo_credits_co2_megagrams']
    mini_df['total_combo_cost_dollars'] = tech_share_combos_total['total_combo_cost_dollars']
    mini_df['total_combo_generalized_cost_dollars'] = tech_share_combos_total['total_combo_generalized_cost_dollars']

    tech_share_combos_total['producer_iteration'] = producer_iteration
    tech_share_combos_total['winner'] = False
    tech_share_combos_total['compliance_score'] = abs(1-tech_share_combos_total['compliance_ratio'])
    tech_share_combos_total['slope'] = 0

    if o2.options.log_producer_iteration_years == 'all' or calendar_year in o2.options.log_producer_iteration_years:
        producer_iteration_log.write(tech_share_combos_total)

    potential_winners = mini_df[mini_df['total_combo_credits_co2_megagrams'] >= 0]
    cost_name = 'total_combo_generalized_cost_dollars'

    if not potential_winners.empty:
        winning_combos = tech_share_combos_total.loc[[potential_winners[cost_name].idxmin()]]
        compliance_possible = True

        tech_share_combos_total = tech_share_combos_total[mini_df['total_combo_credits_co2_megagrams'] < 0].copy()
        if not tech_share_combos_total.empty:
            tech_share_combos_total['slope'] = \
                (tech_share_combos_total[cost_name] - float(winning_combos[cost_name])) / \
                (tech_share_combos_total['compliance_ratio'] - float(winning_combos['compliance_ratio']))

            other_winner_index = tech_share_combos_total['slope'].idxmin()

            winning_combos = winning_combos.append(tech_share_combos_total.loc[other_winner_index])
    else:
        winning_combos = tech_share_combos_total.loc[[mini_df['total_combo_credits_co2_megagrams'].idxmax()]]
        compliance_possible = False

    if o2.options.log_producer_iteration_years == 'all' or calendar_year in o2.options.log_producer_iteration_years:
        winning_combos['winner'] = True
        producer_iteration_log.write(winning_combos)

    return winning_combos.copy(), compliance_possible


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
