"""

A series of functions to calculate costs associated with the policy. The calc_cost_effects function is called by the
omega_effects module and other functions here are called from within the calc_cost_effects function.

----

**CODE**

"""
import pandas as pd


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


def calc_cost_effects(batch_settings, session_settings, physical_effects_dict, context_fuel_cpm_dict):
    """
    Calculate cost effects

    Args:
        batch_settings: an instance of the BatchSettings class.
        session_settings: an instance of the SessionSettings class.
        physical_effects_dict: A dictionary of physical effects for each vehicle in each analysis year.
        context_fuel_cpm_dict: dictionary; the context session fuel costs per mile by vehicle_id and age.

    Returns:
        A dictionary of cost effects for each vehicle in each analysis year.

    """
    costs_dict = dict()
    vehicle_info_dict = dict()
    refueling_bev_dict = dict()
    refueling_liquid_dict = dict()
    fuel = None

    for key in physical_effects_dict:
        vehicle_id, calendar_year, age = key
        physical = physical_effects_dict[key]
        onroad_direct_co2e_grams_per_mile = physical['onroad_direct_co2e_grams_per_mile']
        onroad_direct_kwh_per_mile = physical['onroad_direct_kwh_per_mile']

        veh_effects_dict = dict()
        flag = None
        if onroad_direct_co2e_grams_per_mile or onroad_direct_kwh_per_mile:
            flag = 1

            mfr_cost_dollars = purchase_price_dollars = purchase_credit_dollars = battery_cost_dollars = 0
            avg_mfr_cost = avg_purchase_price = avg_purchase_credit = battery_cost_dollars_per_kwh = 0
            fuel_retail_cost_dollars = 0
            fuel_pretax_cost_dollars = 0
            congestion_cost_dollars = 0
            noise_cost_dollars = 0
            maintenance_cost_dollars = 0
            repair_cost_dollars = 0
            refueling_cost_dollars = 0
            drive_value_cost_dollars = 0
            bev_flag = phev_flag = hev_flag = mhev_flag = 0
            battery_credit_dollars = 0

            base_year_vehicle_id, model_year, mfr_id, name, base_year_reg_class_id, reg_class_id, in_use_fuel_id, \
                market_class_id, fueling_class, base_year_powertrain_type, body_style, footprint, workfactor, \
                battery_kwh \
                = physical['base_year_vehicle_id'], \
                physical['model_year'], \
                physical['manufacturer_id'], \
                physical['name'], \
                physical['base_year_reg_class_id'], \
                physical['reg_class_id'], \
                physical['in_use_fuel_id'], \
                physical['market_class_id'], \
                physical['fueling_class'], \
                physical['base_year_powertrain_type'], \
                physical['body_style'], \
                physical['footprint_ft2'], \
                physical['workfactor'], \
                physical['battery_kwh'],

            vehicle_count, annual_vmt, odometer, vmt, vmt_rebound, vmt_liquid, vmt_elec, kwh, gallons, imported_bbl \
                = physical['registered_count'], \
                  physical['annual_vmt'], \
                  physical['odometer'], \
                  physical['vmt'], \
                  physical['vmt_rebound'], \
                  physical['vmt_liquid_fuel'], \
                  physical['vmt_electricity'], \
                  physical['fuel_consumption_kWh'], \
                  physical['fuel_consumption_gallons'], \
                  physical['barrels_of_imported_oil']

            if vehicle_id not in vehicle_info_dict:
                if vehicle_id < batch_settings.legacy_fleet.legacy_fleet_vehicle_id_start:
                    attribute_list = [
                        'new_vehicle_mfr_cost_dollars',
                        'price_dollars',
                        'price_modification_dollars',
                        'battery_cost',
                        'bev',
                        'phev',
                        'hev',
                        'mhev',
                        'charge_depleting_range_mi',
                    ]
                    vehicle_info_dict[vehicle_id] = \
                        session_settings.vehicles.get_vehicle_attributes(vehicle_id, *attribute_list)

                else:
                    legacy_fleet_key = (vehicle_id, calendar_year, age)
                    price_data = \
                        batch_settings.legacy_fleet._legacy_fleet[legacy_fleet_key]['transaction_price_dollars']
                    avg_mfr_cost, avg_purchase_price, avg_purchase_credit = 3 * [price_data]
                    battery_cost = 0  # this won't matter for legacy fleet since calculated only for age==0
                    charge_depleting_range = 0
                    if base_year_powertrain_type == 'BEV':
                        bev_flag = 1
                        charge_depleting_range = 300  # this is for legacy fleet only
                    elif base_year_powertrain_type == 'PHEV':
                        phev_flag = 1
                    elif base_year_powertrain_type == 'HEV':
                        hev_flag = 1
                    elif base_year_powertrain_type == 'MHEV':
                        mhev_flag = 1
                    else:
                        pass
                    vehicle_info_dict[vehicle_id] = \
                        avg_mfr_cost, avg_purchase_price, avg_purchase_credit, battery_cost, \
                            bev_flag, phev_flag, hev_flag, mhev_flag, charge_depleting_range

            avg_mfr_cost, avg_purchase_price, avg_purchase_credit, battery_cost, \
                bev_flag, phev_flag, hev_flag, mhev_flag, charge_depleting_range = \
                vehicle_info_dict[vehicle_id]

            # tech costs, only for age=0
            if age == 0:
                mfr_cost_dollars = vehicle_count * avg_mfr_cost
                purchase_price_dollars = vehicle_count * avg_purchase_price
                purchase_credit_dollars = vehicle_count * avg_purchase_credit
                battery_cost_dollars = vehicle_count * battery_cost
                if battery_kwh > 0:
                    battery_cost_dollars_per_kwh = battery_cost_dollars / battery_kwh

                if bev_flag == 1:
                    battery_credit_dollars = \
                        session_settings.powertrain_cost.get_battery_tax_offset(model_year, battery_kwh)

            # fuel costs
            fuel_dict = eval(in_use_fuel_id)
            for fuel, fuel_share in fuel_dict.items():
                retail_price \
                    = batch_settings.context_fuel_prices.get_fuel_prices(batch_settings, calendar_year,
                                                                         'retail_dollars_per_unit', fuel)
                pretax_price \
                    = batch_settings.context_fuel_prices.get_fuel_prices(batch_settings, calendar_year,
                                                                         'pretax_dollars_per_unit', fuel)
                if 'electricity' in fuel and kwh:
                    fuel_retail_cost_dollars += retail_price * kwh
                    fuel_pretax_cost_dollars += pretax_price * kwh
                elif 'electricity' not in fuel and gallons:
                    fuel_retail_cost_dollars += retail_price * gallons
                    fuel_pretax_cost_dollars += pretax_price * gallons

            # maintenance costs
            powertrain_type = 'ICE'
            if bev_flag == 1:
                powertrain_type = 'BEV'
            elif phev_flag == 1:
                powertrain_type = 'PHEV'
            elif hev_flag == 1 or mhev_flag == 1:
                powertrain_type = 'HEV'
            slope, intercept = get_maintenance_cost(batch_settings, powertrain_type)
            maintenance_cost_per_mile = slope * odometer + intercept
            maintenance_cost_dollars = maintenance_cost_per_mile * vmt

            # repair costs
            if 'car' in name:
                operating_veh_type = 'car'
            elif 'Pickup' in name:
                operating_veh_type = 'truck'
            else:
                operating_veh_type = 'suv'

            repair_cost_per_mile \
                = batch_settings.repair_cost.calc_repair_cost_per_mile(avg_mfr_cost, powertrain_type,
                                                                       operating_veh_type, age)
            repair_cost_dollars = repair_cost_per_mile * vmt

            # refueling costs
            if bev_flag == 1:
                if (operating_veh_type, charge_depleting_range) in refueling_bev_dict:
                    refueling_cost_per_mile = refueling_bev_dict[(operating_veh_type, charge_depleting_range)]
                else:
                    refueling_cost_per_mile \
                        = batch_settings.refueling_cost.calc_bev_refueling_cost_per_mile(operating_veh_type,
                                                                                         charge_depleting_range)
                    refueling_bev_dict.update({(operating_veh_type, charge_depleting_range): refueling_cost_per_mile})
                refueling_cost_dollars = refueling_cost_per_mile * vmt
            else:
                if operating_veh_type in refueling_liquid_dict:
                    refueling_cost_per_gallon = refueling_liquid_dict[operating_veh_type]
                else:
                    refueling_cost_per_gallon \
                        = batch_settings.refueling_cost.calc_liquid_refueling_cost_per_gallon(operating_veh_type)
                    refueling_liquid_dict.update({operating_veh_type: refueling_cost_per_gallon})
                refueling_cost_dollars = refueling_cost_per_gallon * gallons

            # get congestion and noise cost factors
            congestion_cf, noise_cf = get_congestion_noise_cf(batch_settings, base_year_reg_class_id)

            # congestion and noise costs (maybe congestion and noise cost factors will differ one day?)
            if vmt_elec:
                congestion_cost_dollars += vmt_elec * congestion_cf
                noise_cost_dollars += vmt_elec * noise_cf
            if vmt_liquid:
                congestion_cost_dollars += vmt_liquid * congestion_cf
                noise_cost_dollars += vmt_liquid * noise_cf

            # calc drive value relative to the context as value of rebound vmt plus the drive surplus
            fuel_cpm = fuel_retail_cost_dollars / vmt
            context_fuel_cpm_dict_key = (int(base_year_vehicle_id), base_year_powertrain_type, int(model_year), age)
            if context_fuel_cpm_dict_key in context_fuel_cpm_dict:
                context_fuel_cpm = context_fuel_cpm_dict[context_fuel_cpm_dict_key]['fuel_cost_per_mile']
                drive_value_cost_dollars = 0.5 * vmt_rebound * (fuel_cpm + context_fuel_cpm)

            # save results in the vehicle effects dict for this vehicle
            veh_effects_dict = {
                'session_policy': session_settings.session_policy,
                'session_name': session_settings.session_name,
                # 'discount_rate': 0,
                'vehicle_id': vehicle_id,
                'base_year_vehicle_id': int(base_year_vehicle_id),
                'manufacturer_id': mfr_id,
                'name': name,
                'calendar_year': calendar_year,
                'model_year': int(model_year),
                'age': age,
                'base_year_reg_class_id': base_year_reg_class_id,
                'reg_class_id': reg_class_id,
                'in_use_fuel_id': in_use_fuel_id,
                'fueling_class': fueling_class,
                'base_year_powertrain_type': base_year_powertrain_type,
                'powertrain_type': powertrain_type,
                'body_style': body_style,
                'footprint_ft2': footprint,
                'workfactor': workfactor,
                'registered_count': vehicle_count,
                'annual_vmt': annual_vmt,
                'odometer': odometer,
                'vmt': vmt,
                'vmt_liquid_fuel': vmt_liquid,
                'vmt_electricity': vmt_elec,
                'battery_kwh': battery_kwh,
                'vehicle_cost_dollars': mfr_cost_dollars,
                'battery_cost_dollars': battery_cost_dollars,
                'battery_cost_per_kWh': battery_cost_dollars_per_kwh,
                'battery_credit_dollars': battery_credit_dollars,
                'purchase_price_dollars': purchase_price_dollars,
                'purchase_credit_dollars': purchase_credit_dollars,
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

        if flag:
            discount_rate = 0
            key = (vehicle_id, calendar_year, age, discount_rate)
            costs_dict[key] = veh_effects_dict

    return costs_dict


def calc_annual_cost_effects(input_df):
    """

    Args:
        input_df: DataFrame of cost effects by vehicle in each analysis year.

    Returns:
        A DataFrame of cost effects by calendar year, reg class and fuel type.

    """
    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['count', 'dollars', 'battery_kwh']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # groupby calendar year, regclass and fuel
    groupby_cols = ['session_policy', 'session_name', 'calendar_year', 'reg_class_id', 'in_use_fuel_id']
    return_df = input_df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(return_df.columns.get_loc('in_use_fuel_id') + 1,
                     'fueling_class',
                     '')
    return_df.loc[return_df['in_use_fuel_id'] == "{'US electricity':1.0}", 'fueling_class'] = 'BEV'
    return_df.loc[return_df['in_use_fuel_id'] != "{'US electricity':1.0}", 'fueling_class'] = 'ICE'

    return_df.insert(return_df.columns.get_loc('calendar_year') + 1, 'discount_rate', 0)
    return_df.insert(return_df.columns.get_loc('calendar_year') + 1, 'periods', 1)
    return_df.insert(return_df.columns.get_loc('calendar_year') + 1, 'series', 'AnnualValue')

    return_df['battery_cost_per_kwh'] = return_df['battery_cost_dollars'] / return_df['battery_kwh']

    return return_df


def calc_period_consumer_view(batch_settings, input_df):
    """

    Args:
        batch_settings: an instance of the BatchSettings class.
        input_df: DataFrame of cost effects by vehicle in each analysis year.

    Returns:
        A DataFrame of cost effects by model year of available lifetime, body style and fuel type.

    """
    attributes = [col for col in input_df.columns if ('vmt' in col or 'vmt_' in col) and '_vmt' not in col]
    additional_attributes = ['count', 'dollars']
    for additional_attribute in additional_attributes:
        for col in input_df:
            if additional_attribute in col:
                attributes.append(col)

    # eliminate legacy_fleet and ages not desired for consumer view
    periods = batch_settings.general_inputs_for_effects.get_value('years_in_consumer_view')

    # if periods = 8, then max_age should be 7 since year 1 is age=0
    max_age = periods - 1
    df = input_df.loc[(input_df['manufacturer_id'] != 'legacy_fleet') & (input_df['age'] <= max_age), :]

    # now create a sales column for use in some of the 'per vehicle' calcs below
    df.insert(df.columns.get_loc('registered_count'), 'sales', df['registered_count'])
    df.loc[df['age'] != 0, 'sales'] = 0

    # groupby model year, body_style, powertrain and fuel
    groupby_cols = ['session_policy', 'session_name', 'model_year', 'body_style', 'in_use_fuel_id']
    include_powertrain = \
        batch_settings.general_inputs_for_effects.get_value('include_powertrain_type_in_consumer_cost_view')
    if include_powertrain == 1:
        groupby_cols.append('powertrain_type')

    attributes.append('sales')
    return_df = df[[*groupby_cols, *attributes]]
    return_df = return_df.groupby(by=groupby_cols, axis=0, as_index=False).sum()

    return_df.insert(
        return_df.columns.get_loc('in_use_fuel_id') + 1,
        'fueling_class',
        '')

    return_df.loc[return_df['in_use_fuel_id'] == "{'US electricity':1.0}", 'fueling_class'] = 'BEV'
    return_df.loc[return_df['in_use_fuel_id'] != "{'US electricity':1.0}", 'fueling_class'] = 'ICE'

    return_df.insert(return_df.columns.get_loc('model_year') + 1, 'discount_rate', 0)
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
        elif attribute in ['vehicle_cost_dollars', 'purchase_price_dollars', 'purchase_credit_dollars']:
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
