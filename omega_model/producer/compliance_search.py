"""

Compliance strategy implements the producer search algorithm to find a low-cost combination of technologies (via
vehicle CO2e g/mi) and market shares that achieve a targeted certification outcome.


----

**CODE**

"""

import time
import pandas as pd
import numpy as np

from common import omega_globals, omega_log

from producer.vehicles import *
from common.omega_functions import *

from consumer.sales_volume import context_new_vehicle_sales

from context.production_constraints import ProductionConstraints
from context.new_vehicle_market import NewVehicleMarket

from policy.required_sales_share import RequiredSalesShare

from producer.manufacturer_annual_data import ManufacturerAnnualData

import matplotlib.pyplot as plt

_cache = dict()


def error_callback(e):
    print('error_callback_%s' % __name__)
    print(e)


def create_tech_sweeps(composite_vehicles, candidate_production_decisions, share_range, verbose=False):
    """
    Create tech sweeps is responsible for creating tech (CO2e g/mi levels) options to
    develop a set of candidate compliance outcomes for the manufacturer in the given year as a function of the
    active policy.

    Called from ``search_production_options()``.

    The combination of shares (to determine vehicle sales) and g/mi levels determines the CO2e Mg compliance outcome of
    each option outside of this function.

    On the first pass through this function, there are no ``candidate_production_decisions``
    so the result of the first pass is effectively unconstrained
    (in the absence of required minimum production levels or production constraints).

    On the second pass, the producer has chosen one or more candidate production options from the prior cloud of
    choices, the share range is compressed based on the ``producer_compliance_search_convergence_factor`` setting.
    Subsequent tech options will be generated around the ``candidate_production_decisions``.

    Calls from ``search_production_options()`` continue with subsequently tighter share ranges until the compliance
    target has been met within a tolerance. Ultimately a single candidate production decision is selected and passed
    to the consumer which reacts to the generalized cost of each option with a desired market share.

    Args:
        composite_vehicles ([CompositeVehicle]): the list of producer composite vehicles
        candidate_production_decisions (None, DataFrame): zero or 1 or 2 candidate production decisions chosen from the
            results of the previous search iteration
        share_range (float): determines the numerical range of share and tech options that are considered
        verbose (bool): enables additional console output if ``True``

    Returns:
        A dataframe containing a range of composite vehicle CO2e g/mi options factorially combined

    """
    child_df_list = []

    start_time = time.time()
    # Generate tech options (CO2e g/mi levels)
    for cv in composite_vehicles:
        start_time = time.time()
        incremented = False

        if share_range == 1.0:
            cv.tech_option_iteration_num = 0  # reset vehicle tech option progression

        if cv.fueling_class == 'ICE':
            num_tech_options = omega_globals.options.producer_num_tech_options_per_ice_vehicle
        else:
            num_tech_options = omega_globals.options.producer_num_tech_options_per_bev_vehicle

        veh_min_cost_curve_index = cv.get_min_cost_curve_index()
        veh_max_cost_curve_index = cv.get_max_cost_curve_index()

        if candidate_production_decisions is not None:
            cost_curve_options = np.array([])
            for idx, combo in candidate_production_decisions.iterrows():

                if ((combo['veh_%s_sales' % cv.vehicle_id] > 0) or (cv.tech_option_iteration_num > 0)) and \
                        not incremented:
                    cv.tech_option_iteration_num += 1
                    incremented = True

                tech_share_range = omega_globals.options.producer_compliance_search_convergence_factor ** \
                                   cv.tech_option_iteration_num
                veh_cost_curve_index = combo['veh_%s_cost_curve_indices' % cv.vehicle_id]
                min_value = max(veh_min_cost_curve_index, veh_cost_curve_index * (1 - tech_share_range))
                max_value = min(veh_max_cost_curve_index, veh_cost_curve_index * (1 + tech_share_range))
                cost_curve_options = \
                    np.append(np.append(cost_curve_options,
                                        np.linspace(min_value, max_value, num=num_tech_options)), veh_cost_curve_index)

            if num_tech_options == 1:
                # cost_curve_options = [veh_min_cost_curve_index]  # was max g/mi -> min credits
                best_index = (cv.cost_curve.credits_co2e_Mg_per_vehicle / cv.cost_curve.new_vehicle_mfr_generalized_cost_dollars).idxmax()
                cost_curve_options = [cv.cost_curve[cost_curve_interp_key].loc[best_index]]
            else:
                cost_curve_options = np.unique(cost_curve_options)  # filter out redundant tech options
        else:  # first producer pass, generate full range of options
            if num_tech_options == 1:
                # cost_curve_options = [veh_min_cost_curve_index]  # was max g/mi -> min credits
                best_index = (cv.cost_curve.credits_co2e_Mg_per_vehicle / cv.cost_curve.new_vehicle_mfr_generalized_cost_dollars).idxmax()
                cost_curve_options = [cv.cost_curve[cost_curve_interp_key].loc[best_index]]
            else:
                cost_curve_options = np.linspace(veh_min_cost_curve_index, veh_max_cost_curve_index, num=num_tech_options)

        if len(cv.cost_curve['credits_co2e_Mg_per_vehicle']) > 1:
            from scipy.interpolate import interp1d
            nn_fun = interp1d(cv.cost_curve['credits_co2e_Mg_per_vehicle'],
                              cv.cost_curve['credits_co2e_Mg_per_vehicle'], kind='nearest',
                              fill_value=(cv.cost_curve['credits_co2e_Mg_per_vehicle'].min(),
                                      cv.cost_curve['credits_co2e_Mg_per_vehicle'].max()), bounds_error=False)
            cost_curve_options = np.unique(nn_fun(cost_curve_options))
        else:
            cost_curve_options = [cv.cost_curve['credits_co2e_Mg_per_vehicle'].min()]

        tech_cost_options = \
            cv.get_from_cost_curve('new_vehicle_mfr_cost_dollars', cost_curve_options)
        tech_generalized_cost_options = \
            cv.get_from_cost_curve('new_vehicle_mfr_generalized_cost_dollars', cost_curve_options)
        tech_kwh_options = \
            cv.get_from_cost_curve('battery_kwh', cost_curve_options)
        # tech_kwh_per_mile_options = \
        #     cv.get_from_cost_curve('cert_direct_kwh_per_mile', cost_curve_options)

        d = {'veh_%s_cost_curve_indices' % cv.vehicle_id: cost_curve_options,
             'veh_%s_battery_kwh' % cv.vehicle_id: tech_kwh_options,
             # 'veh_%s_kwh_pmi' % cv.vehicle_id: tech_kwh_per_mile_options,
             'veh_%s_cost_dollars' % cv.vehicle_id: tech_cost_options,
             'veh_%s_generalized_cost_dollars' % cv.vehicle_id: tech_generalized_cost_options}
        df = pd.DataFrame.from_dict(d)

        child_df_list.append(df)

        # print('for cv in composite_vehicles = %f' % (time.time() - start_time))

    start_time = time.time()

    tech_combos_df = pd.DataFrame()
    for df in child_df_list:
        tech_combos_df = cartesian_prod(tech_combos_df, df)

    # print('cartesian_prod tech options time = %f' % (time.time() - start_time))

    return tech_combos_df


def create_share_sweeps(calendar_year, market_class_dict, candidate_production_decisions, share_range,
                        consumer_response, context_based_total_sales, prior_producer_decision_and_response,
                        producer_consumer_iteration_num, node_name='', verbose=False):
    """
    Create share sweeps is responsible for creating market share options to
    develop a set of candidate compliance outcomes for the manufacturer in the given year as a function of the
    active policy.  The function recursively navigates the ``market_class_dict`` as a tree of market categories.

    Called from ``search_production_options()``.

    The combination of shares (to determine vehicle sales) and g/mi levels determines the CO2e Mg compliance outcome of
    each option outside of this function.

    On the first pass through this function, there are no ``candidate_production_decisions`` and there is not yet a
    ``consumer_response`` to those production decisions so the result of the first pass is effectively unconstrained
    (in the absence of required minimum production levels or production constraints).

    On the second pass, the producer has chosen one or more candidate production options from the prior cloud of
    choices, the share range is compressed based on the ``producer_compliance_search_convergence_factor`` setting.
    Subsequent market shares will be generated around the ``candidate_production_decisions``.

    Calls from ``search_production_options()`` continue with subsequently tighter share ranges until the compliance
    target has been met within a tolerance. Ultimately a single candidate production decision is selected and passed
    to the consumer which reacts to the generalized cost of each option with a desired market share.

    If none of the outcomes are within the market share convergence tolerance then subsequent calls to this function
    include the ``consumer_response`` and are used as to generate nearby market share options, again as a function of
    the ``share_range`` as the producer continues to search compliance options.

    Args:
        calendar_year (int): the year in which the compliance calculations take place
        market_class_dict (dict): a dict of CompositeVehicle object lists hiearchically grouped by market categories
            into market classes
        candidate_production_decisions (None, DataFrame): zero or 1 or 2 candidate production decisions chosen from the
            results of the previous search iteration
        share_range (float): determines the numerical range of share and tech options that are considered
        consumer_response (Series): a pandas Series containing the final producer decision from prior iterations and
            containing the consumer desired market shares based on that decision and the producer's cross-subsidy, if
            any
        node_name (str): name of the node in the ``market_class_dict``, used to traverse the market class tree
        verbose (bool): enables additional console output if ``True``

    Returns:
        A dataframe containing a range of market share options factorially combined

    """
    child_df_list = []

    children = list(market_class_dict)

    children = [c for c in children if market_class_dict[c]]

    start_time = time.time()
    for k in market_class_dict:
        if verbose:
            print('processing ' + k)
        if type(market_class_dict[k]) is dict and set(market_class_dict[k].keys()) != {'ALT', 'NO_ALT'}:
            # process subtree
            child_df_list.append(create_share_sweeps(calendar_year, market_class_dict[k],
                                candidate_production_decisions, share_range,
                                consumer_response, context_based_total_sales,
                                prior_producer_decision_and_response, producer_consumer_iteration_num,
                                node_name=k))

    if node_name:
        abs_share_column_names = ['producer_abs_share_frac_' + node_name + '.' + c + '.' + alt
                                  for alt in ['ALT', 'NO_ALT'] for c in children]
    else:
        abs_share_column_names = ['producer_abs_share_frac_' + c for c in children]

    if node_name == '' and share_range == 1.0 and consumer_response is not None and \
            consumer_response['total_battery_GWh'] > consumer_response['battery_GWh_limit']:
        omega_log.logwrite('### Production Constraints Violated, Modifying Constraints ###')

        if consumer_response['total_ALT_battery_GWh'] > 0:
            constraint_ratio = max(0, 0.99 * ((consumer_response['battery_GWh_limit'] -
                                   consumer_response['total_NO_ALT_battery_GWh']) /
                                   consumer_response['total_ALT_battery_GWh']))
        else:
            constraint_ratio = 0

        print('*** constraint ratio %f, %f, %f, %f, %f->%f' %
              (constraint_ratio,
               consumer_response['battery_GWh_limit'],
               consumer_response['total_battery_GWh'],
               consumer_response['total_NO_ALT_battery_GWh'],
               consumer_response['total_ALT_battery_GWh'],
               consumer_response['total_ALT_battery_GWh'] * constraint_ratio))

    responsive_children = [s in omega_globals.options.MarketClass.responsive_market_categories for s in children if
                           market_class_dict[s]]

    # Generate market share options
    # if consumer_response is not None and \
    #         consumer_response['total_battery_GWh'] <= consumer_response['battery_GWh_limit']:
    if consumer_response is not None and (not all(responsive_children)): # or producer_consumer_iteration_num>=30):
        # inherit absolute market shares from consumer response for non-responsive children
        sales_share_dict = dict()
        for cn in abs_share_column_names:
            if cn.replace('producer', 'consumer') in consumer_response:
                sales_share_dict[cn] = [consumer_response[cn.replace('producer', 'consumer')]]

        sales_share_df = pd.DataFrame.from_dict(sales_share_dict)

        if 'min_constraints_%s' % node_name in consumer_response:
            # pass constraints to next iteration
            sales_share_df['min_constraints_%s' % node_name] = consumer_response['min_constraints_%s' % node_name]
            sales_share_df['max_constraints_%s' % node_name] = consumer_response['max_constraints_%s' % node_name]
    else:
    # if True:
        # generate producer desired market shares for responsive market sectors and/or adjust constraints to maintain
        # GWh limit
        if all(responsive_children):
            if responsive_children:
                if len(responsive_children) > 1:

                    if consumer_response is None:
                        node_abs_share = _cache['mcat_data_%d' % calendar_year][node_name]['abs_share']
                    else:
                        node_abs_share = consumer_response['consumer_abs_share_frac_%s' % node_name]

                    if share_range == 1.0:
                        locked_consumer_shares = False

                        if consumer_response is not None:
                            max_constraints = Eval.eval(consumer_response['max_constraints_%s' % node_name])
                            min_constraints = Eval.eval(consumer_response['min_constraints_%s' % node_name])
                            keys = max_constraints.copy().keys()

                        if consumer_response is not None and \
                                consumer_response['total_battery_GWh'] > consumer_response['battery_GWh_limit']:
                            print("consumer_response['total_battery_GWh'] > consumer_response['battery_GWh_limit']")
                            # adjust constraints
                            if consumer_response['total_ALT_battery_GWh'] > 0:
                                constraint_ratio = max(0, 0.99 * ((consumer_response['battery_GWh_limit'] -
                                                               consumer_response['total_NO_ALT_battery_GWh']) /
                                                               consumer_response['total_ALT_battery_GWh']))
                            else:
                                constraint_ratio = 0

                            for k in keys:
                                if 'BEV.ALT' in k:  # TODO: un-hardcode the 'BEV' part here...
                                    max_constraints[k] = \
                                        (consumer_response[k.replace('producer', 'consumer')] /
                                         consumer_response['consumer_abs_share_frac_%s' % node_name] *
                                         constraint_ratio)
                                    min_constraints[k] = min(min_constraints[k], max_constraints[k])
                                elif '.ALT' in k:
                                    # pop other max ALTs, avoid internal inconsistency in constraints and bad partition
                                    max_constraints.pop(k)

                        elif consumer_response is not None:
                            if 'p-c_shares_and_costs' in omega_globals.options.verbose_console_modules:
                                print("consumer_response['total_battery_GWh'] <= consumer_response['battery_GWh_limit']")
                            node_market_classes = [node_name + '.' + c for c in children]

                            # pop non-partition keys
                            for k in [node_name] + children:
                                if k in min_constraints:
                                    min_constraints.pop(k)
                                if k in max_constraints:
                                    max_constraints.pop(k)

                            # print('min_constraints')
                            # print_dict(min_constraints)
                            # print('max_constraints')
                            # print_dict(max_constraints)
                            #
                            # for nmc in node_market_classes:
                            #     print('cost_multiplier_%s' % nmc, consumer_response['cost_multiplier_%s' % nmc])

                            consumer_node_abs_share = consumer_response['consumer_abs_share_frac_%s' % node_name]

                            # don't lock anything in on iteration zero, cross subsdies might be maxed just on the
                            # basis of body style share mismatch, for example
                            if producer_consumer_iteration_num > 1 or omega_globals.options.session_is_reference:
                                if min_constraints == max_constraints:
                                    locked_consumer_shares = True
                                else:
                                    # constrain shares that are at min or max cross subsidy, let the others float
                                    for nmc in node_market_classes:
                                        if 'cost_multiplier_%s' % nmc in consumer_response:
                                            multiplier = consumer_response['cost_multiplier_%s' % nmc]
                                            if ((multiplier >= 0.99 * omega_globals.options.consumer_pricing_multiplier_max or multiplier <= 1.01 * omega_globals.options.consumer_pricing_multiplier_min) and (consumer_response['max_share_delta_market_class'] == node_name or consumer_response['max_share_delta_market_class'] is None)) or \
                                                    (multiplier == 1.0 and consumer_response['consumer_constrained_%s' % node_name]):
                                                locked_consumer_shares = True
                                                for k in min_constraints.keys():
                                                    if '.ALT' in k:
                                                        if 'p-c_shares_and_costs' in omega_globals.options.verbose_console_modules:
                                                            print('%50s, %.5f, %.5f, %.5f, %.5f' % (
                                                            k, min_constraints[k], max_constraints[k],
                                                            consumer_response[k] / node_abs_share,
                                                            consumer_response[k.replace('producer', 'consumer')] / consumer_node_abs_share))
                                                        min_constraints[k] = consumer_response[k.replace('producer', 'consumer')] / consumer_node_abs_share
                                                        max_constraints[k] = min_constraints[k]
                                        else:  # no cross-subsidy, non-full-line manufacturer, possible epsilon discrepancy
                                            locked_consumer_shares = True
                                            max_constraints = min_constraints
                        else:
                            # set up initial constraints for mandatory "NO_ALT" vehicle shares
                            # calculate RELATIVE share constraints for partition, even though the keys indicate absolute shares:
                            # --- they will be USED to determine absolute shares ---
                            min_constraints = dict()
                            max_constraints = dict()
                            locked_shares = 0

                            for c, scn in zip(children + children, abs_share_column_names):
                                if 'NO_ALT' in scn.split('.'):
                                    if scn not in min_constraints:
                                        min_constraints[scn] = 0
                                        max_constraints[scn] = 0
                                    for cv in market_class_dict[c]['NO_ALT']:
                                        # min() to protect against floating point error going a femto over 1
                                        no_alt_share = sum([v.projected_sales for v in cv.vehicle_list]) / \
                                                       context_based_total_sales / node_abs_share
                                        min_constraints[scn] = min(1.0, min_constraints[scn] + no_alt_share)
                                        max_constraints[scn] = min_constraints[scn]
                                        locked_shares += no_alt_share

                            node_market_classes = [node_name + '.' + c for c in children]

                            prior_market_class_shares_dict = dict()
                            if prior_producer_decision_and_response is not None:
                                # use prior production decision as a starting point for this year => constrain
                                # ALT shares within a range

                                # calculate prior child partition- first calc total abs shares then normalize:
                                total_share = 0
                                for nmc in node_market_classes:
                                    prior_market_class_shares_dict[nmc] = \
                                        prior_producer_decision_and_response['producer_abs_share_frac_%s' % nmc]

                                    total_share += prior_market_class_shares_dict[nmc]

                                # normalize
                                for nmc in node_market_classes:
                                    prior_market_class_shares_dict[nmc] /= total_share

                            else:
                                # use base year data for nominal partition data
                                for nmc in node_market_classes:
                                    if nmc in NewVehicleMarket.base_year_other_sales:
                                        sales = NewVehicleMarket.base_year_other_sales[nmc]
                                    else:
                                        sales = 0
                                    prior_market_class_shares_dict[nmc] = \
                                        sales / NewVehicleMarket.base_year_other_sales[node_name]

                            production_min = dict()
                            production_max = dict()
                            for nmc in node_market_classes:
                                if omega_globals.pass_num == 0:
                                    min_production_share = ProductionConstraints.get_minimum_share(calendar_year, nmc)
                                    required_zev_share = RequiredSalesShare.get_minimum_share(calendar_year, nmc)
                                    production_min[nmc] = max(min_production_share, required_zev_share)
                                    production_max[nmc] = ProductionConstraints.get_maximum_share(calendar_year, nmc)
                                else:
                                    # no production limits on second pass, they only apply to the consolidated industry
                                    production_min[nmc] = 0
                                    production_max[nmc] = 1

                            if abs(1-locked_shares) > sys.float_info.epsilon:
                                # calc max subtract = min(producer_damping_max_delta, current share - minimum (NO_ALT))
                                max_sub_dict = dict()
                                for nmc in node_market_classes:
                                    onmc_add = 0
                                    for onmc in [mc for mc in node_market_classes if mc != nmc]:
                                        onmc_add += max(production_max[onmc], max_constraints['producer_abs_share_frac_%s.NO_ALT' % onmc]) - prior_market_class_shares_dict[onmc]
                                    max_sub = max(0, min(onmc_add, (prior_market_class_shares_dict[nmc] -
                                               max(production_min[nmc], min_constraints['producer_abs_share_frac_%s.NO_ALT' % nmc]))))

                                    max_sub_dict[nmc] = \
                                        min(omega_globals.options.producer_market_category_ramp_limit, max_sub)

                                # calc max addition = min(producer_damping_max_delta, sum of max subtract of all other shares)
                                max_add_dict = dict()
                                for nmc in node_market_classes:
                                    # add up max subtract for other node market classes
                                    total_max_sub = 0
                                    for onmc in [mc for mc in node_market_classes if mc != nmc]:
                                        total_max_sub += max_sub_dict[onmc]

                                    max_add_dict[nmc] = \
                                        min(omega_globals.options.producer_market_category_ramp_limit, total_max_sub,
                                            production_max[nmc] - prior_market_class_shares_dict[nmc])

                                # figure out ALT ranges based on prior shares and max add and max subtract limits
                                for nmc in node_market_classes:
                                    min_constraints['producer_abs_share_frac_%s.ALT' % nmc] = \
                                        max(0, prior_market_class_shares_dict[nmc] - max_sub_dict[nmc] - \
                                        min_constraints['producer_abs_share_frac_%s.NO_ALT' % nmc])
                                    max_constraints['producer_abs_share_frac_%s.ALT' % nmc] = \
                                        min(1, prior_market_class_shares_dict[nmc] + max_add_dict[nmc] - \
                                        max_constraints['producer_abs_share_frac_%s.NO_ALT' % nmc])

                        if locked_consumer_shares:
                            print('%s locked consumer shares' % node_name)
                            node_partition = pd.DataFrame.from_dict([min_constraints])
                        else:
                            node_partition = partition(abs_share_column_names,
                                      num_levels=omega_globals.options.producer_num_market_share_options,
                                      min_constraints=min_constraints, max_constraints=max_constraints)

                        if abs(1-sum_dict(node_partition.iloc[0])) > 1e-6:
                            print('*** bad_partition! ***')
                            print('min_constraints')
                            print_dict(min_constraints)
                            print('max_constraints')
                            print_dict(min_constraints)
                            print('')

                        sales_share_df = node_abs_share * node_partition

                        # capture constraints
                        for c in children:
                            min_constraints[c] = 0
                            max_constraints[c] = 0
                        min_constraints[node_name] = 0
                        for scn in sales_share_df.columns:
                            min_constraints[scn] = sales_share_df[scn].min() / node_abs_share
                            max_constraints[scn] = sales_share_df[scn].max() / node_abs_share
                            for c in children:
                                if c in scn.split('.'):
                                    min_constraints[c] += min_constraints[scn]
                                    max_constraints[c] += max_constraints[scn]
                            if 'NO_ALT' in scn.split('.'):
                                min_constraints[node_name] += min_constraints[scn]

                        # pass constraints to next iteration
                        sales_share_df['min_constraints_%s' % node_name] = str(min_constraints)
                        sales_share_df['max_constraints_%s' % node_name] = str(max_constraints)

                    else:
                        # narrow search span to a range of shares around the winners
                        min_constraints = Eval.eval(candidate_production_decisions['min_constraints_%s' % node_name].iloc[0])
                        max_constraints = Eval.eval(candidate_production_decisions['max_constraints_%s' % node_name].iloc[0])

                        # convert abs shares to relative shares for generate_constrained_nearby_shares, then scale
                        # the output by node_abs_share
                        cpd = candidate_production_decisions.copy()  # create temporary copy for relative shares
                        for scn in abs_share_column_names:
                            cpd[scn] /= node_abs_share

                        sales_share_df = \
                            node_abs_share * generate_constrained_nearby_shares(abs_share_column_names, cpd,
                                                               share_range,
                                                               omega_globals.options.producer_num_market_share_options,
                                                               min_constraints=min_constraints,
                                                               max_constraints=max_constraints)

                        # pass constraints to next iteration
                        sales_share_df['min_constraints_%s' % node_name] = str(min_constraints)
                        sales_share_df['max_constraints_%s' % node_name] = str(max_constraints)
            else:
                sales_share_df = pd.DataFrame()
        else:
            # I'm not even sure if we need to do this... if we're setting absolute shares at the leaves...
            # but I guess it adds some tracking info to the dataframe which might be useful for debugging?
            sales_share_dict = dict()
            for c, scn in zip(children, abs_share_column_names):
                sales_share_dict[scn] = [_cache['mcat_data_%d' % calendar_year][c]['abs_share']]

            sales_share_df = pd.DataFrame.from_dict(sales_share_dict)

    child_df_list.append(sales_share_df)

    # Combine tech and market share options
    if verbose:
        print('combining ' + str(children))
    share_combos_df = pd.DataFrame()
    for df in child_df_list:
        if not df.empty:
            share_combos_df = cartesian_prod(share_combos_df, df)

    return share_combos_df


def apply_production_decision_to_composite_vehicles(composite_vehicles, selected_production_decision):
    """
    Apply the selected production decision to the given composite vehicles (g/mi results and sales) and decompose the
    composite values down to the source vehicles.  Update the composite vehicle CO2e Mg and cost values based on the
    weighted values of the source vehicles.

    Args:
        composite_vehicles (list): list of ``CompositeVehicle`` objects
        selected_production_decision (Series): the production decision as a result of the compliance search

    Returns:
        A list of updated `CompositeVehicle`` objects

    """

    # assign co2 values and sales to vehicles...
    for cv in composite_vehicles:
        cv.credits_co2e_Mg_per_vehicle = selected_production_decision['veh_%s_cost_curve_indices' % cv.vehicle_id]
        # cv.cert_co2e_grams_per_mile = selected_production_decision['veh_%s_co2e_grams_per_mile' % cv.vehicle_id]
        # cv.cert_direct_kwh_per_mile = selected_production_decision['veh_%s_kwh_pmi' % cv.vehicle_id]
        cv.initial_registered_count = selected_production_decision['veh_%s_sales' % cv.vehicle_id]
        # VehicleOnroadCalculations.perform_onroad_calculations(cv)
        cv.decompose()
        cv.new_vehicle_mfr_cost_dollars = \
            cv.get_weighted_attribute('new_vehicle_mfr_cost_dollars')
        cv.new_vehicle_mfr_generalized_cost_dollars = \
            cv.get_weighted_attribute('new_vehicle_mfr_generalized_cost_dollars')
        cv.target_co2e_Mg = \
            cv.get_weighted_attribute('target_co2e_Mg')
        cv.cert_co2e_Mg = \
            cv.get_weighted_attribute('cert_co2e_Mg')

    return composite_vehicles


def search_production_options(compliance_id, calendar_year, producer_decision_and_response,
                              producer_consumer_iteration_num, strategic_target_offset_Mg,
                              prior_producer_decision_and_response):
    """
    This function implements the producer search for a set of technologies (CO2e g/mi values) and market shares that
    achieve a desired compliance outcome taking into consideration the strategic target offset which allows
    intentional under- or over-compliance based on the producer's credit situation, for example.

    This function is called from ``omega.run_producer_consumer()``.

    On the first pass through, there is no ``producer_decision_and_response`` yet.  On subsequent iterations
    (``producer_consumer_iteration_num`` > 0) the producer decision and consumer response is used to constrain the range
    of market shares under consideration by the producer.

    Args:
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        calendar_year (int): the year of the compliance search
        producer_decision_and_response (Series): pandas Series containing the producer's selected production decision
            from the prior iteration and the consumer's desired market shares
        producer_consumer_iteration_num (int): the number of the producer-consumer iteration
        strategic_target_offset_Mg (float): if positive, the raw compliance outcome will be under-compliance, if
            negative then the raw compliance outcome will be over-compliance. Used to strategically under- or over-
            comply, perhaps as a result of the desired to earn or burn prior credits in the credit bank

    Returns:
        A tuple of ``composite_vehicles`` (list of CompositeVehicle objects),
        ``selected_production_decision`` (pandas Series containing the result of the serach),
        ``market_class_tree`` (dict of CompositeVehicle object lists hiearchically grouped by market categories
        into market classes), and ``producer_compliance_possible`` (bool that indicates whether compliance was
        achievable)

    """
    candidate_production_decisions = None
    producer_compliance_possible = False

    if (calendar_year == omega_globals.options.analysis_initial_year) and (producer_consumer_iteration_num == 0):
        _cache.clear()

    producer_iteration_log = \
        omega_log.IterationLog('%s%d_%d_producer_compliance_search.csv' % (
            omega_globals.options.output_folder, calendar_year, producer_consumer_iteration_num))

    continue_search = True
    search_iteration = 0
    best_candidate_production_decision = None
    most_strategic_production_decision = None
    constraint_ratio = 1.0

    while continue_search:
        share_range = omega_globals.options.producer_compliance_search_convergence_factor ** search_iteration

        composite_vehicles, pre_production_vehicles, market_class_tree, context_based_total_sales = \
            create_composite_vehicles(calendar_year, compliance_id)

        tech_sweeps = create_tech_sweeps(composite_vehicles, candidate_production_decisions, share_range)

        share_sweeps = create_share_sweeps(calendar_year, market_class_tree,
                                           candidate_production_decisions, share_range,
                                           producer_decision_and_response, context_based_total_sales,
                                           prior_producer_decision_and_response, producer_consumer_iteration_num)

        tech_and_share_sweeps = cartesian_prod(tech_sweeps, share_sweeps)

        production_options = create_production_options_from_shares(composite_vehicles, tech_and_share_sweeps,
                                                                   context_based_total_sales)

        # insert code to cull production options based on policy here #

        if omega_globals.options.manufacturer_gigawatthour_data is None:
            # individual OEM data not yet be populated, use the default values
            battery_GWh_limit = np.interp(calendar_year, omega_globals.options.battery_GWh_limit_years,
                              omega_globals.options.battery_GWh_limit)
        else:
            # use individual OEM data from first pass
            battery_GWh_limit = np.interp(calendar_year,
                                          omega_globals.options.manufacturer_gigawatthour_data['analysis_years'],
                                          omega_globals.options.manufacturer_gigawatthour_data[compliance_id])

        production_options['battery_GWh_limit'] = battery_GWh_limit
        valid_production_options = \
            production_options[production_options['total_battery_GWh'] <= battery_GWh_limit].copy()

        if valid_production_options.empty:
            omega_log.logwrite('### Production Constraints Violated ... limit: %f, min / max: %f / %f ###' %
                               (battery_GWh_limit,
                                production_options['total_battery_GWh'].min(),
                                production_options['total_battery_GWh'].max())
                               )
            # take the closest one(s), see how that goes...
            valid_production_options = \
                production_options[production_options['total_battery_GWh'] ==
                                   production_options['total_battery_GWh'].min()].copy()

        production_options = valid_production_options

        if production_options.empty:
            producer_compliance_possible = None
            selected_production_decision = None

        if producer_compliance_possible is not None:
            production_options['share_range'] = share_range

            production_options['strategic_compliance_ratio'] = \
                (production_options['total_cert_co2e_megagrams'] - strategic_target_offset_Mg) / \
                np.maximum(1, production_options['total_target_co2e_megagrams'])

            production_options['strategic_target_offset_Mg'] = strategic_target_offset_Mg

            candidate_production_decisions, compliance_possible = \
                select_candidate_manufacturing_decisions(production_options, calendar_year, search_iteration,
                                                         producer_iteration_log, strategic_target_offset_Mg)

            producer_compliance_possible |= compliance_possible

            most_strategic_index = candidate_production_decisions['strategic_compliance_error'].idxmin()
            most_strategic_points = candidate_production_decisions.loc[[most_strategic_index]]
            most_strategic_point = most_strategic_points.loc[[most_strategic_points['total_generalized_cost_dollars'].idxmin()]].iloc[0]
            cheapest_index = candidate_production_decisions['total_generalized_cost_dollars'].idxmin()
            cheapest_points = candidate_production_decisions.loc[[cheapest_index]]
            most_strategic_cheapest_point = cheapest_points.loc[[cheapest_points['strategic_compliance_ratio'].idxmin()]].iloc[0]

            cheapest_compliant = most_strategic_cheapest_point['strategic_compliance_ratio'] <= 1.0

            if (most_strategic_production_decision is None) or \
                    (candidate_production_decisions['strategic_compliance_error'].min() <
                     most_strategic_production_decision['strategic_compliance_error'].min()):
                most_strategic_production_decision = most_strategic_point

            if omega_globals.options.producer_voluntary_overcompliance:
                if best_candidate_production_decision is None:
                    # if cheapest is compliant, it's the best
                    if cheapest_compliant:
                        best_candidate_production_decision = most_strategic_cheapest_point
                    else:
                        # if cheapest is non-compliant, most strategic is the best
                        best_candidate_production_decision = most_strategic_point
                else:
                    # if new candidate is cheaper than the old best and compliant, it's the best
                    if (most_strategic_cheapest_point['total_generalized_cost_dollars'] <
                            best_candidate_production_decision['total_generalized_cost_dollars']) and \
                            cheapest_compliant:
                        best_candidate_production_decision = most_strategic_cheapest_point
                    elif best_candidate_production_decision['strategic_compliance_error'] > 1.0:
                        # if old best was non compliant, new best is most strategic
                        best_candidate_production_decision = most_strategic_point
            else:
                best_candidate_production_decision = most_strategic_production_decision

            if 'producer_compliance_search' in omega_globals.options.verbose_console_modules:
                omega_log.logwrite(('%d_%d_%d' % (calendar_year, producer_consumer_iteration_num,
                                                  search_iteration)).ljust(12) + 'SR:%f CR:%.10f BCR:%.10f' % (share_range,
                                        most_strategic_production_decision['strategic_compliance_ratio'],
                                        best_candidate_production_decision['strategic_compliance_ratio']))

            search_iteration += 1

            continue_search = producer_compliance_possible is not None and \
                        (abs(1 - most_strategic_production_decision['strategic_compliance_ratio']) >
                         omega_globals.options.producer_compliance_search_tolerance) and \
                          (share_range > omega_globals.options.producer_compliance_search_min_share_range)

    if producer_compliance_possible is not None:
        if 'producer_compliance_search' in omega_globals.options.verbose_console_modules:
            omega_log.logwrite('PRODUCER FINAL COMPLIANCE DELTA %f' % abs(1 - best_candidate_production_decision['strategic_compliance_ratio']),
                               echo_console=True)

            omega_log.logwrite('Target GHG Offset Mg %.0f, Actual GHG Offset Mg %.0f' % (-best_candidate_production_decision['strategic_target_offset_Mg'], best_candidate_production_decision['total_credits_co2e_megagrams']),
                               echo_console=True)

            omega_log.logwrite('Target Compliance Ratio %3.3f, Actual Compliance Ratio %3.3f' %
                               ((best_candidate_production_decision['total_cert_co2e_megagrams']-best_candidate_production_decision['strategic_target_offset_Mg'])/max(1, best_candidate_production_decision['total_target_co2e_megagrams']),
                                best_candidate_production_decision['strategic_compliance_ratio']),
                               echo_console=True)

        selected_production_decision = series_to_numeric(best_candidate_production_decision)

        selected_production_decision = \
            selected_production_decision.rename({'strategic_compliance_ratio': 'strategic_compliance_ratio_initial',
                                                 'strategic_compliance_error': 'strategic_compliance_error_initial'})

        # log the final iteration, as opposed to the winning iteration:
        selected_production_decision['producer_search_iteration'] = search_iteration - 1

        # if 'producer_compliance_search' in omega_globals.options.verbose_console_modules:
        #     for mc in sorted(omega_globals.options.MarketClass.market_classes):
        #         if 'producer_abs_share_frac_%s' % mc in selected_production_decision:
        #             omega_log.logwrite(('%d producer_abs_share_frac_%s' % (calendar_year, mc)).ljust(50) + '= %.6f' %
        #                            (selected_production_decision['producer_abs_share_frac_%s' % mc]))
        #     omega_log.logwrite('')

        composite_vehicles = apply_production_decision_to_composite_vehicles(composite_vehicles,
                                                                             selected_production_decision)

    return composite_vehicles, pre_production_vehicles, selected_production_decision, market_class_tree, \
           producer_compliance_possible, battery_GWh_limit


def calc_composite_vehicles(mc, rc, alt, mctrc):
    cv = CompositeVehicle(mctrc[mc][rc][alt], vehicle_id='%s.%s.%s' % (mc, rc, alt), weight_by='model_year_prevalence')
    # cv.market_class_share_frac = sum([v.projected_sales for v in cv.vehicle_list]) / mctrc[mc]['sales']
    cv.market_class_share_frac = sum([v.projected_sales for v in cv.vehicle_list]) / mctrc[mc]['%s_sales' % alt]
    cv.alt_type = alt

    return cv


def create_composite_vehicles(calendar_year, compliance_id):
    """
    Create composite vehicles based on the prior year's finalized vehicle production and update the sales mix based on
    projections from the context and caclulate this year's nominal sales for the compliance ID based on the context.

    Args:
        calendar_year (int): the year of the compliance search
        compliance_id (str): manufacturer name, or 'consolidated_OEM'

    Returns:
        tuple ``composite_vehicles`` (list of CompositeVehicle objects),
        ``market_class_tree`` (dict of CompositeVehicle object lists hiearchically grouped by market categories
        into market classes), ``context_based_total_sales`` (total vehicle sales based on the context for the given
        ``compliance_id``)

    """

    cache_key = calendar_year
    if cache_key not in _cache:
        # pull in last year's vehicles:
        manufacturer_prior_vehicles = VehicleFinal.get_compliance_vehicles(calendar_year - 1, compliance_id)

        manufacturer_vehicles = []
        pre_production_vehicles = []

        start_time = time.time()

        # transfer prior vehicle data to this year's vehicles
        for prior_veh in manufacturer_prior_vehicles:
            new_veh = Vehicle()
            transfer_vehicle_data(prior_veh, new_veh, model_year=calendar_year)

            new_veh.in_production = new_veh.in_production or \
                                    new_veh.model_year - new_veh.prior_redesign_year >= new_veh.redesign_interval

            if new_veh.in_production:
                manufacturer_vehicles.append(new_veh)
            else:
                pre_production_vehicles.append(new_veh)

        if omega_globals.options.multiprocessing:
            results = []
            for new_veh in manufacturer_vehicles:
                results.append(omega_globals.pool.apply_async(func=calc_vehicle_frontier,
                                                              args=[new_veh],
                                                              callback=None,
                                                              error_callback=error_callback))
            manufacturer_vehicles = [r.get() for r in results]
        else:
            for new_veh in manufacturer_vehicles:
                calc_vehicle_frontier(new_veh)

        print('Created manufacturer_vehicles %.20f' % (time.time() - start_time))

        alt_vehs = [new_veh for new_veh in manufacturer_vehicles if not new_veh.base_year_product]
        byp_vehs = [new_veh for new_veh in manufacturer_vehicles if new_veh.base_year_product]

        alt_byvids = set([v.base_year_vehicle_id for v in alt_vehs])
        byp_byvids = set([v.base_year_vehicle_id for v in byp_vehs])
        non_covered_byvids = set.difference(byp_byvids, alt_byvids)

        non_covered_vehs = [v for v in manufacturer_vehicles if v.base_year_vehicle_id in non_covered_byvids]
        covered_vehs = [v for v in manufacturer_vehicles if v.base_year_vehicle_id not in non_covered_byvids]

        # for v in non_covered_vehs:
        #     print('%80s %20s %10s %20s' % (v.name, v.market_class_id, v.reg_class_id, v.context_size_class))
        #
        # print('\nEND non_covered_vehs ##################################\n')

        # sum([new_veh.base_year_market_share for new_veh in manufacturer_vehicles]) ~= 2.0 at this point due to
        # intentional duplicate entries for "alternative" powertrain vehicles, but "market_share" is used for relative
        # proportions

        context_based_total_sales = 0  # sales total by compliance id size class share
        for csc in NewVehicleMarket.base_year_context_size_class_sales: # for each context size class
            context_based_total_sales += \
                NewVehicleMarket.new_vehicle_data(calendar_year, context_size_class=csc) \
                * VehicleFinal.mfr_base_year_share_data[compliance_id][csc]

        # update new vehicle prevalence based on vehicle size mix from context (base year data)
        for new_veh in manufacturer_vehicles:
            new_veh.model_year_prevalence = \
                new_veh.base_year_market_share * \
                VehicleFinal.mfr_base_year_share_data[compliance_id][new_veh.context_size_class]

        # group by context size class
        csc_dict = dict()
        for new_veh in manufacturer_vehicles:
            if new_veh.base_year_product:
                if new_veh.context_size_class not in csc_dict:
                    csc_dict[new_veh.context_size_class] = []
                csc_dict[new_veh.context_size_class].append(new_veh)

        # distribute context size class sales to manufacturer_vehicles by relative market share
        for csc in csc_dict: # for each context size class
            projection_initial_registered_count = \
                NewVehicleMarket.new_vehicle_data(calendar_year, context_size_class=csc) \
                * VehicleFinal.mfr_base_year_share_data[compliance_id][csc]

            distribute_by_attribute(csc_dict[csc], projection_initial_registered_count,
                                    weight_by='model_year_prevalence',
                                    distribute_to='projected_sales')

        for new_veh in manufacturer_vehicles:
            new_veh.model_year_prevalence = 0

        # calculate new prevalence based on vehicle size mix from context
        myp_dict = dict()
        for new_veh in manufacturer_vehicles:
            if new_veh.base_year_product:
                new_veh.model_year_prevalence = new_veh.projected_sales / context_based_total_sales
                myp_dict['myp_%s' % new_veh.base_year_vehicle_id] = new_veh.model_year_prevalence
                myp_dict['ps_%s' % new_veh.base_year_vehicle_id] = new_veh.projected_sales

        # for v in manufacturer_vehicles:
        #     print('%80s %20s %10s %20s %10f %10d' % (
        #         v.name, v.market_class_id, v.reg_class_id, v.context_size_class, v.model_year_prevalence,
        #         v.projected_sales))
        #
        # print('\nEND manufacturer_vehicles ##################################\n')

        # sum([new_veh.model_year_prevalence for new_veh in manufacturer_vehicles]) == 1.0 at this point,
        # sum([new_veh.projected_sales for new_veh in manufacturer_vehicles]) = context_based_total_sales

        for v in manufacturer_vehicles:
            v.model_year_prevalence = myp_dict['myp_%s' % v.base_year_vehicle_id]
            v.projected_sales = myp_dict['ps_%s' % v.base_year_vehicle_id]

        # for v in manufacturer_vehicles:
        #     print('%80s %20s %10s %20s %10f %10d' % (
        #         v.name, v.market_class_id, v.reg_class_id, v.context_size_class, v.model_year_prevalence,
        #         v.projected_sales))
        #
        # print('\nEND manufacturer_vehicles ##################################\n')
        #
        # for v in non_covered_vehs:
        #     print('%80s %20s %10s %20s %10f %10d' % (
        #         v.name, v.market_class_id, v.reg_class_id, v.context_size_class, v.model_year_prevalence,
        #         v.projected_sales))
        #
        # print('\nEND non_covered_vehs ##################################\n')

        # sum([v.model_year_prevalence for v in manufacturer_vehicles]) >= 1.0 and that's ok
        # sum([v.model_year_prevalence for v in byp_vehs]) == 1.0 and alt vehicles get the myp of their respective base vehicles

        # # group by market class (base year products) just to double check total prevalence for debugging
        # mct = dict()
        # for mc in omega_globals.options.MarketClass.market_classes:
        #     mct[mc] = []
        # for new_veh in manufacturer_vehicles:
        #     if new_veh.base_year_product:
        #         mct[new_veh.market_class_id].append(new_veh)
        #
        # mc_sum = 0
        # for k in mct:
        #     print(k, sum([v.model_year_prevalence for v in mct[k]]))
        #     mc_sum += sum([v.model_year_prevalence for v in mct[k]])
        # print('total %f' % mc_sum)

        # sales by market category, ALT / NO_ALT
        _cache['mcat_data_%d' % calendar_year] = dict()
        for mcat in omega_globals.options.MarketClass.market_categories:
            _cache['mcat_data_%d' % calendar_year][mcat] = {'sales': 0, 'abs_share': 0,
                                                            'NO_ALT_sales': 0, 'ALT_sales': 0,
                                                            'NO_ALT_abs_share': 0, 'ALT_abs_share': 0}
        for mcat in omega_globals.options.MarketClass.market_categories:
            for new_veh in manufacturer_vehicles:
                new_veh_abs_share = new_veh.projected_sales / context_based_total_sales
                if new_veh.base_year_vehicle_id in non_covered_byvids:
                    if mcat in str.split(new_veh.market_class_id, '.'):
                        _cache['mcat_data_%d' % calendar_year][mcat]['NO_ALT_sales'] += new_veh.projected_sales
                        _cache['mcat_data_%d' % calendar_year][mcat]['NO_ALT_abs_share'] += new_veh_abs_share
                        _cache['mcat_data_%d' % calendar_year][mcat]['sales'] += new_veh.projected_sales
                        _cache['mcat_data_%d' % calendar_year][mcat]['abs_share'] += new_veh_abs_share
                else:
                    if mcat in str.split(new_veh.market_class_id, '.'):
                        if new_veh.base_year_product:
                            _cache['mcat_data_%d' % calendar_year][mcat]['ALT_sales'] += new_veh.projected_sales
                            _cache['mcat_data_%d' % calendar_year][mcat]['ALT_abs_share'] += new_veh_abs_share
                            _cache['mcat_data_%d' % calendar_year][mcat]['sales'] += new_veh.projected_sales
                            _cache['mcat_data_%d' % calendar_year][mcat]['abs_share'] += new_veh_abs_share
        # print_dict(_cache['mcat_data_%d' % calendar_year])

        # group by market class / reg class
        mctrc = {'ALT_sales': 0, 'NO_ALT_sales': 0}
        for mc in omega_globals.options.MarketClass.market_classes:
            mctrc[mc] = {'sales': 0, 'byp_prevalence': 0,
                         'NO_ALT_sales': 0, 'ALT_sales': 0,
                         'NO_ALT_abs_share': 0, 'ALT_abs_share': 0}
            for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                mctrc[mc][rc] = {'ALT': [], 'NO_ALT': []}
        for new_veh in manufacturer_vehicles:
            new_veh_abs_share = new_veh.projected_sales / context_based_total_sales
            if new_veh.base_year_vehicle_id in non_covered_byvids:
                # NO_ALT
                mctrc[new_veh.market_class_id][new_veh.reg_class_id]['NO_ALT'].append(new_veh)
                mctrc[new_veh.market_class_id]['NO_ALT_sales'] += new_veh.projected_sales
                mctrc[new_veh.market_class_id]['NO_ALT_abs_share'] += new_veh_abs_share
                if new_veh.base_year_product:
                    mctrc['NO_ALT_sales'] += new_veh.projected_sales
            else:
                mctrc[new_veh.market_class_id][new_veh.reg_class_id]['ALT'].append(new_veh)
                mctrc[new_veh.market_class_id]['ALT_sales'] += new_veh.projected_sales
                mctrc[new_veh.market_class_id]['ALT_abs_share'] += new_veh_abs_share
                if new_veh.base_year_product:
                    mctrc['ALT_sales'] += new_veh.projected_sales
            mctrc[new_veh.market_class_id]['sales'] += new_veh.projected_sales
            mctrc[new_veh.market_class_id]['byp_prevalence'] += new_veh.model_year_prevalence * new_veh.base_year_product
        # print_dict(mctrc)

        mcrc_priority_list = []
        for mc in omega_globals.options.MarketClass.market_classes:
            for rc in omega_globals.options.RegulatoryClasses.reg_classes:
                for alt in ['ALT', 'NO_ALT']:
                    if mctrc[mc][rc][alt]:
                        mcrc_priority_list.append((mc, rc, alt, len(mctrc[mc][rc][alt])))

        # sort composite vehicles by number of source vehicles
        mcrc_priority_list = sorted(mcrc_priority_list, key=lambda x: x[-1], reverse=True)

        start_time = time.time()

        composite_vehicles = []

        if omega_globals.options.multiprocessing:
            results = []
            # start longest jobs first!
            for mc, rc, alt, _ in mcrc_priority_list:
                results.append(omega_globals.pool.apply_async(func=calc_composite_vehicles,
                                                              args=[mc, rc, alt, mctrc],
                                                              callback=None,
                                                              error_callback=error_callback))

            composite_vehicles = [r.get() for r in results]
        else:
            for mc, rc, alt, _ in mcrc_priority_list:
                composite_vehicles.append(calc_composite_vehicles(mc, rc, alt, mctrc))

        print('Composite Vehicles Elapsed Time %f' % (time.time() - start_time))
        # get empty market class tree
        market_class_tree = omega_globals.options.MarketClass.get_market_class_tree()

        # populate tree with vehicle objects
        for new_veh in composite_vehicles:
            omega_globals.options.MarketClass.\
                populate_market_classes(market_class_tree,
                                        '%s.%s' % (new_veh.market_class_id, new_veh.alt_type),
                                        new_veh)

        # cull branches that don't contain vehicles (e.g. missing body styles)
        keys = list(market_class_tree.keys())
        for k in keys:
            if k not in VehicleFinal.mfr_base_year_share_data[compliance_id] or VehicleFinal.mfr_base_year_share_data[compliance_id][k] == 0.0:
                market_class_tree.pop(k)

        _cache[cache_key] = {'composite_vehicles': composite_vehicles,
                             'pre_production_vehicles': pre_production_vehicles,
                             'market_class_tree': market_class_tree,
                             'context_based_total_sales': context_based_total_sales,
                             # 'context_based_alt_sales': context_based_alt_sales,
                             # 'context_based_no_alt_sales': context_based_no_alt_sales,
                             }
    else:
        # pull cached composite vehicles (avoid recompute of composite frontiers, etc)
        composite_vehicles = _cache[cache_key]['composite_vehicles']
        pre_production_vehicles = _cache[cache_key]['pre_production_vehicles']
        market_class_tree = _cache[cache_key]['market_class_tree']
        context_based_total_sales = _cache[cache_key]['context_based_total_sales']

    return composite_vehicles, pre_production_vehicles, market_class_tree, context_based_total_sales


def finalize_production(calendar_year, compliance_id, candidate_mfr_composite_vehicles, pre_production_vehicles,
                        producer_decision):
    """
    Finalize vehicle production at the conclusion of the compliance search and producer-consumer market share
    iteration.  Source ``Vehicle`` objects from the composite vehicles are converted to ``VehicleFinal`` objects
    and stored in the database.  Manufacturer Annual Data is updated with the certification results in CO2e Mg

    Args:
        calendar_year (int): the year of the compliance search
        compliance_id (str): manufacturer name, or 'consolidated_OEM'
        candidate_mfr_composite_vehicles (list): list of ``CompositeVehicle`` objects
        producer_decision (Series): the production decision as a result of the compliance search

    Returns:
        Nothing, updates the OMEGA database with the finalized vehicles

    """
    from consumer import sales_volume

    manufacturer_new_vehicles = []

    # pull final vehicles from composite vehicles
    decompose_candidate_vehicles(calendar_year, candidate_mfr_composite_vehicles, producer_decision)

    for cv in candidate_mfr_composite_vehicles:
        if (omega_globals.options.log_vehicle_cloud_years == 'all') or \
                (calendar_year in omega_globals.options.log_vehicle_cloud_years):
            if 'cv_cost_curves' in omega_globals.options.verbose_log_modules:
                filename = '%s%d_%s_%s_cost_curve.csv' % (omega_globals.options.output_folder, cv.model_year,
                                                          cv.name.replace(':', '-'), cv.vehicle_id)
                cv.cost_curve.to_csv(filename, columns=sorted(cv.cost_curve.columns), index=False)

        for veh in cv.vehicle_list:
            veh_final = VehicleFinal()
            transfer_vehicle_data(veh, veh_final)
            manufacturer_new_vehicles.append(veh_final)

    # propagate pre-production vehicles
    for ppv in pre_production_vehicles:
        veh_final = VehicleFinal()
        transfer_vehicle_data(ppv, veh_final)
        manufacturer_new_vehicles.append(veh_final)

    # save generalized costs
    sales_volume.log_new_vehicle_generalized_cost(calendar_year, compliance_id,
                                                  producer_decision['average_new_vehicle_mfr_generalized_cost'])

    omega_globals.session.add_all(manufacturer_new_vehicles)

    target_co2e_Mg = VehicleFinal.calc_target_co2e_Mg(calendar_year, compliance_id)

    cert_co2e_Mg = VehicleFinal.calc_cert_co2e_Mg(calendar_year, compliance_id)

    ManufacturerAnnualData. \
        create_manufacturer_annual_data(model_year=calendar_year,
                                        compliance_id=compliance_id,
                                        target_co2e_Mg=target_co2e_Mg,
                                        calendar_year_cert_co2e_Mg=cert_co2e_Mg,
                                        manufacturer_vehicle_cost_dollars=
                                            producer_decision['total_cost_dollars'],
                                        )
    omega_globals.session.flush()


def decompose_candidate_vehicles(calendar_year, candidate_mfr_composite_vehicles, producer_decision):
    for cv in candidate_mfr_composite_vehicles:
        # update sales, which may have changed due to consumer response and iteration
        cv.initial_registered_count = producer_decision['veh_%s_sales' % cv.vehicle_id]
        cv.decompose()  # propagate sales to source vehicles and interpolate cost curve data


def create_production_options_from_shares(composite_vehicles, tech_and_share_combinations, total_sales):
    """
    Create a set of production options, including compliance outcomes, based on the given tech and share combinations.

    On the first time through, from the ``producer`` module, total_sales is based on context, market shares
    come from the producer desired market shares.

    On the second time through, from the ``omega`` module, total_sales is determined by sales response, market shares
    come from the consumer demanded market shares.

    Args:
        composite_vehicles (list): list of ``CompositeVehicle`` objects
        tech_and_share_combinations (DataFrame): the result of ``create_tech_and_share_sweeps()``
        total_sales (float): manufacturer total vehicle sales based on the context or the consumer response

    Returns:
        ``production_options`` DataFrame of technology and share options including compliance outcomes in CO2e Mg

    """
    production_options = tech_and_share_combinations

    is_series = type(production_options) == pd.Series

    total_battery_GWh = 0
    total_NO_ALT_battery_GWh = 0
    total_ALT_battery_GWh = 0
    total_target_co2e_Mg = 0
    total_cert_co2e_Mg = 0
    total_cost_dollars = 0
    total_generalized_cost_dollars = 0

    # clear prior values, if any
    # for composite_veh in composite_vehicles:
    #     # share_id = composite_veh.market_class_id
    #     share_id = composite_veh.market_class_id + '.' + composite_veh.alt_type
    #     if ('producer_abs_share_frac_%s' % share_id) in production_options:
    #         production_options['producer_abs_share_frac_%s' % share_id] = 0

    for composite_veh in composite_vehicles:
        # assign sales to vehicle based on market share fractions and reg class share fractions
        # share_id = composite_veh.market_class_id
        share_id = composite_veh.market_class_id + '.' + composite_veh.alt_type

        if ('consumer_abs_share_frac_%s' % share_id) in production_options and not omega_globals.producer_shares_mode:
            if is_series:
                market_class_sales = total_sales * production_options[
                    'consumer_abs_share_frac_%s' % share_id]
            else:
                market_class_sales = total_sales * production_options[
                    'consumer_abs_share_frac_%s' % share_id].values

        elif ('producer_abs_share_frac_%s' % share_id) in production_options:
            if is_series:
                market_class_sales = total_sales * production_options[
                    'producer_abs_share_frac_%s' % share_id]
            else:
                market_class_sales = total_sales * production_options[
                    'producer_abs_share_frac_%s' % share_id].values

        composite_veh_sales = market_class_sales * composite_veh.market_class_share_frac
        production_options['veh_%s_sales' % composite_veh.vehicle_id] = composite_veh_sales

        # calculate vehicle total cost
        if is_series:
            composite_veh_total_cost_dollars = \
                composite_veh_sales * production_options[
                    'veh_%s_cost_dollars' % composite_veh.vehicle_id]

            composite_veh_total_generalized_cost_dollars = \
                composite_veh_sales * production_options[
                    'veh_%s_generalized_cost_dollars' % composite_veh.vehicle_id]

            composite_veh_total_GWh = \
                composite_veh_sales * production_options[
                    'veh_%s_battery_kwh' % composite_veh.vehicle_id] / 1e6

            composite_veh_cost_curve_options = production_options[
                'veh_%s_cost_curve_indices' % composite_veh.vehicle_id]

        else:
            composite_veh_total_cost_dollars = \
                composite_veh_sales * production_options[
                    'veh_%s_cost_dollars' % composite_veh.vehicle_id].values

            composite_veh_total_generalized_cost_dollars = \
                composite_veh_sales * production_options[
                    'veh_%s_generalized_cost_dollars' % composite_veh.vehicle_id].values

            composite_veh_total_GWh = \
                composite_veh_sales * production_options[
                    'veh_%s_battery_kwh' % composite_veh.vehicle_id].values / 1e6

            composite_veh_cost_curve_options = production_options[
                'veh_%s_cost_curve_indices' % composite_veh.vehicle_id].values

        production_options['veh_%s_total_cost_dollars' % composite_veh.vehicle_id] = composite_veh_total_cost_dollars

        # composite_veh_credits_co2e_Mg = \
        #     composite_veh_sales * composite_veh_cost_curve_options

        # get cert and target Mg for the composite vehicle from the composite cost curve
        composite_veh_cert_co2e_Mg = \
            composite_veh_sales * \
            DecompositionAttributes.interp1d(composite_veh, composite_veh.cost_curve, cost_curve_interp_key,
                                             composite_veh_cost_curve_options, 'cert_co2e_Mg_per_vehicle')

        composite_veh_target_co2e_Mg = \
            composite_veh_sales * \
            DecompositionAttributes.interp1d(composite_veh, composite_veh.cost_curve, cost_curve_interp_key,
                                             composite_veh_cost_curve_options, 'target_co2e_Mg_per_vehicle')

        production_options['veh_%s_cert_co2e_megagrams' % composite_veh.vehicle_id] = composite_veh_cert_co2e_Mg
        production_options['veh_%s_target_co2e_megagrams' % composite_veh.vehicle_id] = composite_veh_target_co2e_Mg

        # update totals
        total_battery_GWh += composite_veh_total_GWh
        if composite_veh.alt_type == 'NO_ALT':
            total_NO_ALT_battery_GWh += composite_veh_total_GWh
        else:
            total_ALT_battery_GWh += composite_veh_total_GWh
        total_target_co2e_Mg += composite_veh_target_co2e_Mg
        total_cert_co2e_Mg += composite_veh_cert_co2e_Mg
        total_cost_dollars += composite_veh_total_cost_dollars
        total_generalized_cost_dollars += composite_veh_total_generalized_cost_dollars

    # TODO: looks like we'll need to calculate these, too?  Or use credits directly to select production decisions, not target/cert/strategic_offset...
    production_options['total_battery_GWh'] = total_battery_GWh
    production_options['total_NO_ALT_battery_GWh'] = total_NO_ALT_battery_GWh
    production_options['total_ALT_battery_GWh'] = total_ALT_battery_GWh
    production_options['total_target_co2e_megagrams'] = total_target_co2e_Mg
    production_options['total_cert_co2e_megagrams'] = total_cert_co2e_Mg
    production_options['total_cost_dollars'] = total_cost_dollars
    production_options['total_generalized_cost_dollars'] = total_generalized_cost_dollars
    production_options['total_credits_co2e_megagrams'] = total_target_co2e_Mg - total_cert_co2e_Mg
    production_options['total_sales'] = total_sales

    return production_options


def _plot_tech_share_combos_total(calendar_year, production_options):
    """
    Optional function that can bse used to investigate production options via various plots

    Args:
        calendar_year (int): the calendar year of the production options
        production_options (DataFrame): dataframe of the production options, including compliance outcomes in Mg

    """
    plt.figure()
    plt.plot(production_options['total_cert_co2e_megagrams'],
             production_options['total_cost_dollars'], '.')
    plt.plot(production_options['total_target_co2e_megagrams'],
             production_options['total_cost_dollars'], 'r.')
    plt.xlabel('CO2e WITHOUT Offset [Mg]')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(production_options['total_cert_co2e_megagrams'] - production_options['strategic_target_offset_Mg'],
             production_options['total_cost_dollars'], '.')
    plt.plot(production_options['total_target_co2e_megagrams'],
             production_options['total_cost_dollars'], 'r.')
    plt.xlabel('CO2e WITH Offset [Mg]')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(production_options['strategic_compliance_ratio'],
             production_options['total_cost_dollars'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(production_options['strategic_compliance_ratio'],
             production_options['total_generalized_cost_dollars'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Generalized Cost [$]')
    plt.title('%s' % calendar_year)
    plt.grid()

    plt.figure()
    plt.plot(production_options['strategic_compliance_ratio'],
             production_options['total_credits_co2e_megagrams'] +
             production_options['strategic_target_offset_Mg'], '.')
    plt.plot([1, 1], plt.ylim(), 'r')
    plt.xlabel('Compliance Ratio WITH Offset')
    plt.ylabel('Credits WITH Offset [Mg]')
    plt.title('%s' % calendar_year)
    plt.grid()


prior_most_strategic_compliant_tech_share_option = None
prior_most_strategic_non_compliant_tech_share_option = None
cloud_slope = None


def select_candidate_manufacturing_decisions(production_options, calendar_year, search_iteration,
                                             producer_iteration_log, strategic_target_offset_Mg):
    """
    Select candidate manufacturing decisions from the cloud of production options.  If possible, there will be two
    candidates, one on either side of the compliance target.  If not possible then the closest option will be selected.

    Args:
        production_options (DataFrame): dataframe of the production options, including compliance outcomes in Mg
        calendar_year (int): the calendar year of the production options
        search_iteration (int): the iteration number of the compliance search
        producer_iteration_log (IterationLog): used to optionally log the production options based on developer settings
        strategic_target_offset_Mg (float): if positive, the raw compliance outcome will be under-compliance, if
            negative then the raw compliance outcome will be over-compliance. Used to strategically under- or over-
            comply, perhaps as a result of the desired to earn or burn prior credits in the credit bank

    Returns:
        tuple ``candidate_production_decisions`` (the best available production decisions),
        ``compliance_possible`` (bool indicating whether compliance was possible)

    """
    # production_options = production_options.drop_duplicates('total_credits_co2e_megagrams')

    global prior_most_strategic_compliant_tech_share_option, prior_most_strategic_non_compliant_tech_share_option, \
        cloud_slope

    cost_name = 'total_generalized_cost_dollars'

    mini_df = pd.DataFrame()
    mini_df['total_credits_with_offset_co2e_megagrams'] = \
        production_options['total_credits_co2e_megagrams'] + strategic_target_offset_Mg
    mini_df['total_cost_dollars'] = production_options['total_cost_dollars']
    mini_df['total_generalized_cost_dollars'] = production_options['total_generalized_cost_dollars']
    mini_df['strategic_compliance_ratio'] = production_options['strategic_compliance_ratio']

    production_options['producer_search_iteration'] = search_iteration
    production_options['selected_production_option'] = False
    production_options['candidate_production_option'] = False
    production_options['strategic_compliance_error'] = abs(1 - production_options['strategic_compliance_ratio'].values)

    if search_iteration == 0:
        prior_most_strategic_compliant_tech_share_option = None
        prior_most_strategic_non_compliant_tech_share_option = None
        cheapest_index = production_options[cost_name].idxmin()
        most_expensive_index = production_options[cost_name].idxmax()
        if production_options['strategic_compliance_ratio'].loc[cheapest_index] >= \
                production_options['strategic_compliance_ratio'].loc[most_expensive_index]:
            cloud_slope = -1
        else:
            cloud_slope = 1

    compliant_tech_share_options = mini_df[mini_df['total_credits_with_offset_co2e_megagrams'].values >= 0].copy()
    non_compliant_tech_share_options = mini_df[mini_df['total_credits_with_offset_co2e_megagrams'].values < 0].copy()

    non_compliant_tech_share_options = cull_non_compliant_points(non_compliant_tech_share_options,
                                                                 prior_most_strategic_non_compliant_tech_share_option)

    if not compliant_tech_share_options.empty and not non_compliant_tech_share_options.empty:
        # tech share options straddle compliance target
        compliance_possible = True

        # grab lowest-cost compliant option
        lowest_cost_compliant_tech_share_option = \
            production_options.loc[[compliant_tech_share_options[cost_name].idxmin()]]

        compliant_tech_share_options = cull_compliant_points(compliant_tech_share_options,
                                                             prior_most_strategic_compliant_tech_share_option)

        if len(non_compliant_tech_share_options) > 1:
            # grab best non-compliant option
            non_compliant_tech_share_options['weighted_slope'] = \
                non_compliant_tech_share_options['strategic_compliance_ratio'].values * \
                ((non_compliant_tech_share_options[cost_name].values - lowest_cost_compliant_tech_share_option[cost_name].item()) /
                (non_compliant_tech_share_options['strategic_compliance_ratio'].values -
                lowest_cost_compliant_tech_share_option['strategic_compliance_ratio'].item()))

            most_strategic_non_compliant_tech_share_option = \
                production_options.loc[[non_compliant_tech_share_options['weighted_slope'].idxmin()]]
        else:
            if len(non_compliant_tech_share_options.columns) == len(mini_df.columns):
                most_strategic_non_compliant_tech_share_option = \
                    production_options.loc[[non_compliant_tech_share_options.index[0]]]
            else:
                most_strategic_non_compliant_tech_share_option = non_compliant_tech_share_options.iloc[[0]]

        three_points = False
        if cloud_slope > 0:
            if len(compliant_tech_share_options) > 1:
                # cost cloud up-slopes from left to right, calculate slope relative to best non-compliant option
                compliant_tech_share_options['weighted_slope'] = \
                    compliant_tech_share_options['strategic_compliance_ratio'].values * \
                    ((compliant_tech_share_options[cost_name].values - most_strategic_non_compliant_tech_share_option[cost_name].item()) /
                    (compliant_tech_share_options['strategic_compliance_ratio'].values -
                     most_strategic_non_compliant_tech_share_option['strategic_compliance_ratio'].item()))

                most_strategic_compliant_tech_share_option = \
                    production_options.loc[[compliant_tech_share_options['weighted_slope'].idxmax()]]
            else:
                if len(compliant_tech_share_options.columns) == len(mini_df.columns):
                    most_strategic_compliant_tech_share_option = production_options.loc[[compliant_tech_share_options.index[0]]]
                else:
                    most_strategic_compliant_tech_share_option = compliant_tech_share_options.iloc[[0]]

            three_points = True
        else:
            most_strategic_compliant_tech_share_option = lowest_cost_compliant_tech_share_option

        lowest_cost_dollars = lowest_cost_compliant_tech_share_option[cost_name].item()
        most_strategic_cost_dollars = most_strategic_compliant_tech_share_option[cost_name].item()

        if three_points and omega_globals.options.producer_voluntary_overcompliance and \
            lowest_cost_dollars / most_strategic_cost_dollars < \
            (1 - omega_globals.options.producer_voluntary_overcompliance_min_benefit_frac):
                # take lowest cost if it's at least X percent cheaper than the most strategic
                candidate_production_decisions =\
                    pd.concat([most_strategic_compliant_tech_share_option, most_strategic_non_compliant_tech_share_option,
                        lowest_cost_compliant_tech_share_option])
        else:
            candidate_production_decisions = \
                pd.concat(
                    [most_strategic_compliant_tech_share_option, most_strategic_non_compliant_tech_share_option])

        prior_most_strategic_compliant_tech_share_option = most_strategic_compliant_tech_share_option
        prior_most_strategic_non_compliant_tech_share_option = most_strategic_non_compliant_tech_share_option

    elif compliant_tech_share_options.empty:
        # all options non-compliant, grab best non-compliant option (least under-compliance)
        compliance_possible = False

        non_compliant_tech_share_options = \
            cull_non_compliant_points(non_compliant_tech_share_options,
                                      prior_most_strategic_non_compliant_tech_share_option)

        if len(non_compliant_tech_share_options.columns) == len(mini_df.columns):
            most_strategic_non_compliant_tech_share_option = \
                production_options.loc[[non_compliant_tech_share_options['strategic_compliance_ratio'].idxmin()]]
        else:
            most_strategic_non_compliant_tech_share_option = non_compliant_tech_share_options.iloc[[0]]

        candidate_production_decisions = most_strategic_non_compliant_tech_share_option

        prior_most_strategic_non_compliant_tech_share_option = most_strategic_non_compliant_tech_share_option

    else:
        # all options compliant, grab best compliant option (least over-compliant OR lowest cost)
        compliance_possible = True

        compliant_tech_share_options = cull_compliant_points(compliant_tech_share_options,
                                                             prior_most_strategic_compliant_tech_share_option)

        if len(compliant_tech_share_options.columns) == len(mini_df.columns):
            lowest_cost_dollars = \
                production_options.loc[[compliant_tech_share_options[cost_name].idxmin()]][cost_name].item()
            most_strategic_cost_dollars = \
                production_options.loc[[compliant_tech_share_options['strategic_compliance_ratio'].idxmax()]][cost_name].item()

            if omega_globals.options.producer_voluntary_overcompliance and \
                    lowest_cost_dollars / most_strategic_cost_dollars < \
                    (1 - omega_globals.options.producer_voluntary_overcompliance_min_benefit_frac):
                # take lowest cost if it's at least X percent cheaper than the most strategic
                most_strategic_compliant_tech_share_option = \
                    production_options.loc[[compliant_tech_share_options[cost_name].idxmin()]]
            else:
                # take closest to strategic taraget
                most_strategic_compliant_tech_share_option = \
                    production_options.loc[[compliant_tech_share_options['strategic_compliance_ratio'].idxmax()]]
        else:
            most_strategic_compliant_tech_share_option = compliant_tech_share_options.iloc[[0]]

        candidate_production_decisions = most_strategic_compliant_tech_share_option
        prior_most_strategic_compliant_tech_share_option = most_strategic_compliant_tech_share_option

    candidate_production_decisions['selected_production_option'] = candidate_production_decisions.index

    if (omega_globals.options.log_producer_compliance_search_years == 'all') or \
            (calendar_year in omega_globals.options.log_producer_compliance_search_years):
        if 'producer_compliance_search' in omega_globals.options.verbose_log_modules:
            # log (some or all) production options cloud and tag selected points
            try:
                production_options.loc[candidate_production_decisions.index, 'candidate_production_option'] = True
            except:
                # candidate may be from a prior iteration, index may not be available
                pass
            if omega_globals.options.slice_tech_combo_cloud_tables:
                production_options = production_options[production_options['strategic_compliance_ratio'].values <= 1.2]
            producer_iteration_log.write(production_options)
        else:
            # log candidate production decisions only
            producer_iteration_log.write(candidate_production_decisions)

    candidate_production_decisions = candidate_production_decisions.drop_duplicates()

    return candidate_production_decisions.copy(), compliance_possible


def cull_compliant_points(compliant_tech_share_options, prior_most_strategic_compliant_tech_share_option):
    """

    Args:
        compliant_tech_share_options:
        prior_most_strategic_compliant_tech_share_option:

    Returns:

    """
    if prior_most_strategic_compliant_tech_share_option is not None:
        good_points = compliant_tech_share_options['strategic_compliance_ratio'] >= \
                      prior_most_strategic_compliant_tech_share_option['strategic_compliance_ratio'].item()
        compliant_tech_share_options = compliant_tech_share_options[good_points]
        if compliant_tech_share_options.empty:
            compliant_tech_share_options = prior_most_strategic_compliant_tech_share_option

    return compliant_tech_share_options


def cull_non_compliant_points(non_compliant_tech_share_options, prior_most_strategic_non_compliant_tech_share_option):
    """

    Args:
        non_compliant_tech_share_options:
        prior_most_strategic_non_compliant_tech_share_option:

    Returns:

    """
    if prior_most_strategic_non_compliant_tech_share_option is not None:
        good_points = non_compliant_tech_share_options['strategic_compliance_ratio'] <= \
                      prior_most_strategic_non_compliant_tech_share_option['strategic_compliance_ratio'].item()
        non_compliant_tech_share_options = non_compliant_tech_share_options[good_points]
        if non_compliant_tech_share_options.empty:
            non_compliant_tech_share_options = prior_most_strategic_non_compliant_tech_share_option

    return non_compliant_tech_share_options


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
