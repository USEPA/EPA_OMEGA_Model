"""

A series of functions to calculate costs associated with the policy. The calc_cost_effects function is called by the
omega_effects module and other functions here are called from within the calc_cost_effects function.

----

**CODE**

"""
import pandas as pd

from omega_effects.effects.discounting_costs import discount_model_year_values


def get_congestion_noise_cf(batch_settings, reg_class_id):
    """
    Get congestion and noise cost factors

    Args:
        batch_settings: an instance of the BatchSettings class.
        reg_class_id: The (legacy) regulatory class ID for which congestion and noise cost factors are needed.

    Returns:
        A list of cost factors as specified in the cost_factors list for the given calendar year.

    """
    cost_factors = ('congestion_cost_dollars_per_mile',
                    'noise_cost_dollars_per_mile',
                    )

    return batch_settings.congestion_noise_cost_factors.get_cost_factors(reg_class_id, cost_factors)


def get_maintenance_cost(batch_settings, veh_type):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        veh_type: (str) 'BEV', 'PHEV', 'ICE', 'HEV'

    Returns:
        Curve coefficient values to calculate maintenance costs per mile at any odometer value.

    """
    d = batch_settings.maintenance_cost.get_maintenance_cost_curve_coefficients(veh_type)

    return d['slope'], d['intercept']


def calc_cost_effects(batch_settings, session_settings, session_fleet_physical, context_fuel_cpm_dict):
    """
    Calculate cost effects

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        session_fleet_physical: A dictionary of physical effects for each vehicle in each analysis year.
        context_fuel_cpm_dict: dictionary; the context session fuel costs per mile by vehicle_id and age.

    Returns:
        A dictionary of cost effects for each vehicle in each analysis year.

    Notes:
        The average purchase price will include possible battery tax credits and reflects the expected price of a
        vehicle on the dealer lot. The average price modification reflects possible purchase tax credits which would
        be deducted from the average purchase price to reflect out-of-pocket purchase costs. Insurance, sales taxes,
        and any other cost tied to the value of a vehicle use the average purchase price in applicable calculations. An
        exception to that would be repair costs which are tied to the manufacturer cost and not purchase prices. The
        manufacturer cost includes applicable battery tax credits which may reduce the cost to the manufacturer.

    """
    costs_dict = {}
    vehicle_info_dict = {}
    refueling_bev_dict = {}
    refueling_liquid_dict = {}
    cumulative_maint_cost_dict = {}

    for v in session_fleet_physical.values():

        if v['onroad_direct_co2e_grams_per_mile'] or v['onroad_direct_kwh_per_mile']:

            mfr_cost_dollars = purchase_price_dollars = purchase_credit_dollars = battery_cost_dollars = 0
            avg_mfr_cost = avg_purchase_price = avg_purchase_credit = battery_cost_dollars_per_kwh = 0
            fuel_retail_cost_dollars = fuel_pretax_cost_dollars = 0
            congestion_cost_dollars = noise_cost_dollars = 0
            maintenance_cost_dollars = repair_cost_dollars = 0
            refueling_cost_dollars = drive_value_cost_dollars = 0
            battery_credit_dollars = 0
            discount_rate = 0
            powertrain_type = None

            if v['vehicle_id'] not in vehicle_info_dict:
                if (v['vehicle_id'], v['calendar_year']) not in batch_settings.legacy_fleet.adjusted_legacy_fleet:
                    attribute_list = [
                        'new_vehicle_mfr_cost_dollars',
                        'price_dollars',
                        'price_modification_dollars',
                        'battery_cost',
                        'onroad_charge_depleting_range_mi',
                    ]
                    vehicle_info_dict[v['vehicle_id']] = \
                        session_settings.vehicles.get_vehicle_attributes(v['vehicle_id'], *attribute_list)

                else:
                    price_data = batch_settings.legacy_fleet.get_legacy_fleet_price(v['vehicle_id'], v['calendar_year'])
                    avg_mfr_cost, avg_purchase_price, avg_purchase_credit = 3 * [price_data]
                    battery_cost = 0  # this won't matter for legacy fleet since calculated only for age==0
                    charge_depleting_range = 0
                    if v['base_year_powertrain_type'] == 'BEV':
                        charge_depleting_range = 300  # this is for legacy fleet only

                    vehicle_info_dict[v['vehicle_id']] = [
                        avg_mfr_cost, avg_purchase_price, avg_purchase_credit, battery_cost, charge_depleting_range
                    ]

                if 'BEV' in v['name']:
                    powertrain_type = 'BEV'
                elif 'PHEV' in v['name']:
                    powertrain_type = 'PHEV'
                elif 'HEV' in v['name']:
                    powertrain_type = 'HEV'
                else:
                    powertrain_type = 'ICE'

                vehicle_info_dict[v['vehicle_id']].append(powertrain_type)

            [avg_mfr_cost, avg_purchase_price, avg_purchase_credit, battery_cost, charge_depleting_range,
             powertrain_type
             ] = vehicle_info_dict[v['vehicle_id']]

            # tech costs, only for age=0 _______________________________________________________________________________
            if v['age'] == 0:
                mfr_cost_dollars = v['registered_count'] * avg_mfr_cost
                purchase_price_dollars = v['registered_count'] * avg_purchase_price
                purchase_credit_dollars = v['registered_count'] * avg_purchase_credit
                battery_cost_dollars = v['registered_count'] * battery_cost
                if v['battery_kwh'] > 0:
                    battery_cost_dollars_per_kwh = battery_cost_dollars / v['battery_kwh']

                if powertrain_type in ['BEV', 'PHEV'] and v['battery_kwh_per_veh'] >= 7:
                    battery_credit_dollars = \
                        session_settings.powertrain_cost.get_battery_tax_offset(
                            v['model_year'], v['battery_kwh'], powertrain_type
                        )

            # fuel costs _______________________________________________________________________________________________
            if v['fuel_consumption_kwh'] > 0:  # this is consumption at the wall so includes charging losses
                retail_price, pretax_price = session_settings.electricity_prices.get_fuel_price(
                    v['calendar_year'], 'retail_dollars_per_unit', 'pretax_dollars_per_unit'
                )
                # pretax_price = retail_price
                fuel_retail_cost_dollars += retail_price * v['fuel_consumption_kwh']
                fuel_pretax_cost_dollars += pretax_price * v['fuel_consumption_kwh']
            if v['fuel_consumption_gallons'] > 0:
                fuel_dict = eval(v['in_use_fuel_id'])
                fuel = [item for item in fuel_dict.keys()][0]
                retail_price = batch_settings.context_fuel_prices.get_fuel_price(
                    v['calendar_year'], fuel, 'retail_dollars_per_unit'
                )
                pretax_price = batch_settings.context_fuel_prices.get_fuel_price(
                    v['calendar_year'], fuel, 'pretax_dollars_per_unit'
                )
                fuel_retail_cost_dollars += retail_price * v['fuel_consumption_gallons']
                fuel_pretax_cost_dollars += pretax_price * v['fuel_consumption_gallons']

            # maintenance costs ________________________________________________________________________________________
            slope, intercept = get_maintenance_cost(batch_settings, powertrain_type)
            maintenance_cost_per_mile = slope * v['odometer'] + intercept
            cumulative_maintenance_cost_thru_now = 0.5 * v['odometer'] * maintenance_cost_per_mile
            if v['vehicle_id'] in cumulative_maint_cost_dict:
                maintenance_cost_this_year = (
                        cumulative_maintenance_cost_thru_now - cumulative_maint_cost_dict[v['vehicle_id']]
                )
                cumulative_maint_cost_dict[v['vehicle_id']] = cumulative_maintenance_cost_thru_now
            else:
                maintenance_cost_this_year = cumulative_maintenance_cost_thru_now
                cumulative_maint_cost_dict[v['vehicle_id']] = maintenance_cost_this_year

            maintenance_cost_dollars = maintenance_cost_this_year * v['registered_count']

            # repair costs _____________________________________________________________________________________________
            if 'car' in v['name']:
                operating_veh_type = repair_type = 'car'
            elif 'Pickup' in v['name'] and 'mediumduty' not in v['reg_class_id']:
                operating_veh_type = repair_type = 'truck'
            elif 'mediumduty' in v['reg_class_id']:
                if 'Pickup' in v['name']:
                    operating_veh_type = 'mediumduty_pickup'
                    repair_type = 'md_pickup'
                else:
                    operating_veh_type = 'mediumduty_van'
                    repair_type = 'md_van'
            else:
                operating_veh_type = repair_type = 'suv'

            repair_cost_per_mile = batch_settings.repair_cost.calc_repair_cost_per_mile(
                avg_mfr_cost, powertrain_type, repair_type, v['age']
            )
            repair_cost_dollars = repair_cost_per_mile * v['vmt']

            # sales taxes ______________________________________________________________________________________________
            sales_tax_rate = batch_settings.insurance_and_taxes_cost_factors.get_tax_rate(
                'average_state_tax_rate'
            )
            sales_tax_dollars = sales_tax_rate * purchase_price_dollars

            # insurance costs __________________________________________________________________________________________
            avg_insurance_cost = batch_settings.insurance_and_taxes_cost_factors.calc_insurance_cost(
                avg_purchase_price, powertrain_type, v['body_style'], v['age']
            )
            insurance_cost_dollars = avg_insurance_cost * v['registered_count']

            # refueling costs for time spent during mid-trip refueling events (assume PHEVs do not recharge mid-trip) __
            if powertrain_type == 'BEV':
                if (operating_veh_type, charge_depleting_range) in refueling_bev_dict:
                    refueling_cost_per_mile = refueling_bev_dict[(operating_veh_type, charge_depleting_range)]
                else:
                    refueling_cost_per_mile \
                        = batch_settings.refueling_cost.calc_bev_refueling_cost_per_mile(
                        operating_veh_type, charge_depleting_range
                    )
                    refueling_bev_dict.update({(operating_veh_type, charge_depleting_range): refueling_cost_per_mile})
                refueling_cost_dollars = refueling_cost_per_mile * v['vmt']
            else:
                if operating_veh_type in refueling_liquid_dict:
                    refueling_cost_per_gallon = refueling_liquid_dict[operating_veh_type]
                else:
                    refueling_cost_per_gallon \
                        = batch_settings.refueling_cost.calc_liquid_refueling_cost_per_gallon(operating_veh_type)
                    refueling_liquid_dict.update({operating_veh_type: refueling_cost_per_gallon})
                refueling_cost_dollars = refueling_cost_per_gallon * v['fuel_consumption_gallons']

            # congestion and noise costs (maybe congestion and noise cost factors will differ one day?) ________________
            congestion_cf, noise_cf = get_congestion_noise_cf(batch_settings, v['base_year_reg_class_id'])
            if v['fuel_consumption_kwh'] > 0 and v['fuel_consumption_gallons'] == 0:
                congestion_cost_dollars += v['vmt'] * congestion_cf
                noise_cost_dollars += v['vmt'] * noise_cf
            if v['fuel_consumption_gallons'] > 0:
                congestion_cost_dollars += v['vmt'] * congestion_cf
                noise_cost_dollars += v['vmt'] * noise_cf

            # calc drive value relative to the context as value of rebound vmt plus the drive surplus __________________
            cost_per_mile_group = 'nonBEV'
            if v['fueling_class'] == 'BEV':
                cost_per_mile_group = 'BEV'
            fuel_cpm = fuel_retail_cost_dollars / v['vmt']
            context_fuel_cpm_dict_key = (
                cost_per_mile_group, v['context_size_class'], int(v['model_year']), int(v['age'])
            )
            if context_fuel_cpm_dict_key in context_fuel_cpm_dict:
                context_fuel_cpm = context_fuel_cpm_dict[context_fuel_cpm_dict_key]['fuel_cost_per_mile']
                drive_value_cost_dollars = 0.5 * v['vmt_rebound'] * (fuel_cpm + context_fuel_cpm)

            # save results in the vehicle effects dict for this vehicle ________________________________________________
            veh_effects_dict = {
                'session_policy': session_settings.session_policy,
                'session_name': session_settings.session_name,
                'discount_rate': discount_rate,
                'vehicle_id': v['vehicle_id'],
                'base_year_vehicle_id': v['base_year_vehicle_id'],
                'manufacturer_id': v['manufacturer_id'],
                'name': v['name'],
                'calendar_year': v['calendar_year'],
                'model_year': int(v['model_year']),
                'age': v['age'],
                'base_year_reg_class_id': v['base_year_reg_class_id'],
                'reg_class_id': v['reg_class_id'],
                'in_use_fuel_id': v['in_use_fuel_id'],
                'fueling_class': v['fueling_class'],
                'base_year_powertrain_type': v['base_year_powertrain_type'],
                'powertrain_type': powertrain_type,
                'body_style': v['body_style'],
                'footprint_ft2': v['footprint_ft2'],
                'workfactor': v['workfactor'],
                'registered_count': v['registered_count'],
                'annual_vmt': v['annual_vmt'],
                'odometer': v['odometer'],
                'vmt': v['vmt'],
                'battery_kwh': v['battery_kwh'],
                'vehicle_cost_dollars': mfr_cost_dollars,
                'battery_cost_dollars': battery_cost_dollars,
                'battery_cost_per_kWh': battery_cost_dollars_per_kwh,
                'battery_credit_dollars': battery_credit_dollars,
                'purchase_price_dollars': purchase_price_dollars,
                'purchase_credit_dollars': purchase_credit_dollars,
                'sales_taxes_cost_dollars': sales_tax_dollars,
                'insurance_cost_dollars': insurance_cost_dollars,
                'fuel_retail_cost_dollars': fuel_retail_cost_dollars,
                'fuel_pretax_cost_dollars': fuel_pretax_cost_dollars,
                'fuel_taxes_cost_dollars': fuel_retail_cost_dollars - fuel_pretax_cost_dollars,
                'congestion_cost_dollars': congestion_cost_dollars,
                'noise_cost_dollars': noise_cost_dollars,
                'maintenance_cost_dollars': maintenance_cost_dollars,
                'repair_cost_dollars': repair_cost_dollars,
                'refueling_cost_dollars': refueling_cost_dollars,
                'drive_value_cost_dollars': drive_value_cost_dollars,
            }

            costs_dict[(v['vehicle_id'], v['calendar_year'], discount_rate)] = veh_effects_dict

    return costs_dict


def calc_annual_cost_effects(input_df):
    """

    Args:
        input_df: DataFrame of cost effects by vehicle in each analysis year.

    Returns:
        A DataFrame of cost effects by calendar year, reg class and fuel type.

    """
    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['registered_count', 'dollars', 'battery_kwh']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # note that the groupby_cols must include fuel_id to calculate benefits since vehicle emission rates differ by fuel
    groupby_cols = ['session_policy', 'session_name', 'discount_rate', 'calendar_year', 'reg_class_id',
                    'in_use_fuel_id', 'fueling_class'
                    ]
    return_df = input_df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(return_df.columns.get_loc('calendar_year') + 1, 'series', 'AnnualValue')

    return_df['battery_cost_per_kwh'] = return_df['battery_cost_dollars'] / return_df['battery_kwh']

    return return_df


def calc_period_consumer_view(batch_settings, input_df, periods):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        input_df: DataFrame of cost effects by vehicle in each analysis year.
        periods (int): the number of periods (years) to include in the consumer view, set via the
        general_inputs_for_effects_file.

    Returns:
        A DataFrame of cost effects by model year of available lifetime, body style and fuel type.

    """
    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['registered_count', 'dollars']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # eliminate legacy_fleet and ages not desired for consumer view
    # if periods = 8, then max_age should be 7 since year 1 is age=0
    max_age = periods - 1
    df = input_df.loc[(input_df['manufacturer_id'] != 'legacy_fleet') & (input_df['age'] <= max_age), :]

    # now create a sales column for use in some of the 'per vehicle' calcs below
    df.insert(df.columns.get_loc('registered_count'), 'sales', df['registered_count'])
    df.loc[df['age'] != 0, 'sales'] = 0

    discounted_df = discount_model_year_values(df)

    df = pd.concat([df, discounted_df], axis=0, ignore_index=True)
    df.reset_index(inplace=True, drop=True)

    # groupby model year, body_style, powertrain and fuel
    if ('car' or 'truck') not in [item for item in input_df['reg_class_id']]:
        groupby_cols = ['session_policy', 'session_name', 'discount_rate', 'model_year', 'body_style', 'in_use_fuel_id']
    else:
        groupby_cols = ['session_policy', 'session_name', 'discount_rate', 'model_year', 'body_style', 'fueling_class']
    include_powertrain = batch_settings.general_inputs_for_effects.get_value(
        'include_powertrain_type_in_consumer_cost_view'
    )
    if include_powertrain == 1:
        groupby_cols.append('powertrain_type')  # note: this will break out HEVs

    attributes.append('sales')
    return_df = df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(return_df.columns.get_loc('model_year') + 1, 'periods', 0)
    return_df.insert(return_df.columns.get_loc('model_year') + 1, 'series', 'PeriodValue')

    # calc periods
    model_years = df['model_year'].unique()
    for model_year in model_years:
        max_age = max(df.loc[df['model_year'] == model_year, 'age'])
        return_df.loc[return_df['model_year'] == model_year, 'periods'] = max_age + 1

    # now calc total values per vehicle over the period and average annual values per vehicle over the period
    for attribute in attributes:
        if attribute in ['sales', 'registered_count']:
            pass
        elif attribute in [
            'vehicle_cost_dollars', 'purchase_price_dollars', 'purchase_credit_dollars', 'sales_taxes_cost_dollars'
        ]:
            s = pd.Series(return_df[attribute] / return_df['sales'], name=f'{attribute}_per_period')
            return_df = pd.concat([return_df, s], axis=1)

            s = pd.Series(return_df[attribute] / return_df['sales'] / return_df['periods'],
                          name=f'{attribute}_per_year_in_period')
            return_df = pd.concat([return_df, s], axis=1)
        else:
            s = pd.Series((return_df[attribute] / return_df['registered_count']) * return_df['periods'],
                          name=f'{attribute}_per_period')
            return_df = pd.concat([return_df, s], axis=1)

            s = pd.Series(return_df[attribute] / return_df['registered_count'], name=f'{attribute}_per_year_in_period')
            return_df = pd.concat([return_df, s], axis=1)

    # and values per mile
    for attribute in attributes:
        s = pd.Series(return_df[attribute] / return_df['vmt'], name=f'{attribute}_per_mile_in_period')
        return_df = pd.concat([return_df, s], axis=1)

    return return_df
