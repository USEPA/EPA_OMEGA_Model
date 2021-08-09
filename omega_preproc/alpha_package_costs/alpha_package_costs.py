"""

**INPUT FILE FORMAT**

The file consists of several Worksheets within an Excel Workbook and should be saved in a folder named
"inputs" within the omega_preproc/alpha_package_costs Python package. Note that throughout the input file cost values must be entered with
a "dollar_basis" term which denotes the doller-year for the cost estimate (i.e., is the cost in 2012 dollars? 2018 dollars?).

The individual Worksheets and their contents are:

inputs_code
    :run_ID:
        A user defined ID for the given run of the alpha_package_costs module. This run_ID will be included in the output filename.
    :optional_run_description:
        An optional description for the run. This is not used other than here.
    :start_year:
        The start year for cost calculations and the year from which learning effects will occur.
    :end_year:
        The last year for cost calculations.
    :learning_rate_weight:
        The year-over-year learning rate to be applied to weight-related technologies.
    :learning_rate_ice_powertrain:
        The year-over-year learning rate to be applied to ICE powertrain technologies.
    :learning_rate_roadload:
        The year-over-year learning rate to be applied to roadload related technologies.
    :learning_rate_bev:
        The year-over-year learning rate to be applied to BEV related technologies (battery/motor).
    :boost_multiplier:
        The cost multiplier to be applied to ICE engine cylinder and displacement costs to reflect the extra costs associated with boost.

inputs_workbook
    :Markup:
        The indirect cost markup factor to use.
    :TRX10:
        The cost estimate associated with a TRX10 transmission (i.e., a 4 speed automatic transmission without modern efficiency elements).
    :AWD_scaler:
        The multiplier to be applied to transmission costs for any vehicle with AWD.

pev_metrics
    :usable_soc_bev:
        The usable state-of-charge for a BEV battery.
    :gap_bev:
        The on-road "gap" for a BEV.
    :powertrain_markup_bev:
        The indirect cost multiplier to be used for BEV related costs (battery/motor)
    :usable_soc_phev:
        The usable state-of-charge for a PHEV battery.
    :gap_phev:
        The on-road "gap" for a PHEV.
    :powertrain_markup_phev:
        The indirect cost multiplier to be used for PHEV related costs (battery/motor).

hev_metrics
    :usable_soc_hev:
        The usable state-of-charge for a HEV battery.
    :gap_hev:
        The on-road "gap" for a HEV.
    :powertrain_markup_hev:
        The indirect cost multiplier to be used for HEV related costs (battery/motor).
    :co2_reduction_cycle_hev:
        The 2-cycle CO2 reduction provided by adding HEV tech.
    :co2_reduction_city_hev:
        The city-cycle CO2 reduction provided by adding HEV tech.
    :co2_reduction_hwy_hev:
        The highway-cycle CO2 reduction provided by adding HEV tech.

bev_curves and hev_curves

    These entries are curves according to the equation x * (Ax^3 +Bx^2 + Cx + D), where the capital letters are the entries in the worksheet and x is the attribute.

    :kW_DCDC_converter:
        DC to DC converter power in kW.
    :dollars_per_kWh_curve:
        The battery cost per kWh.
    :kWh_pack_per_kg_pack_curve:
        The energy density of the battery pack.

bev_nonbattery_single, bev_nonbattery_dual, and hev_nonbattery

    The quantity, cost curve slopes and intercepts, the cost scalers (e.g., vehicle/motor power, vehicle size) and dollar-basis can be
    set for each of the following "non-battery" components

    :motor:

    :inverter:

    :induction_motor:

    :induction_inverter:

    :DCDC_converter:

    :HV_orange_cables:

    :LV_battery:

    :HVAC:

    :single_speed_gearbox:

    :powertrain_cooling_loop:

    :charging_cord_kit:

    :DC_fast_charge_circuitry:

    :power_management_and_distribution:

    :brake_sensors_actuators:

    :additional_pair_of_half_shafts:

price_class
    A concept that would allow for different cost scalers depending on the luxury/economy/etc. class of a vehicle package. This is not being used.

engine
    Cost entries for engine-related technologies (e.g., dollars per cylinder, dollars per liter, direct injection, turbochargning, etc.).

trans
    Cost entries for transmissions.

accessory
    Cost entries for accessory technologies (e.g., electric power steering).

start-stop
    Cost entries for start-stop technology; these vary by curb weight.

weight_ice and weight_pev
    Cost entries associated with weight for ICE and for PEV; these vary by ladder-frame vs. unibody.

aero and nonaero
    Cost entries for roadload aero and nonaero tech, respectively; these vary by ladder-frame and unibody.

ac
    Cost entries air conditioning related tech needed to earn the full AC credit (both leakage and efficiency).

et_dmc
    Cost entries for individual techs; some of these costs are pulled in to the sheets above for calculations.
    These costs are from EPA's past GHG work.

----

**CODE**

"""


import pandas as pd
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
from pathlib import Path

from omega_preproc.context_aeo import SetInputs as context_aeo_inputs


weight_cost_cache = dict()


def cost_vs_plot(input_settings, df, path, *years):
    """

    Args:
        input_settings: The InputSettings class.
        df: A DataFrame cost cloud consisting of ICE, BEV and HEV packages.
        path: The path for saving the plot.
        years: The years for which cost cloud plots are to be generated and saved.

    Returns:
        Nothing, but plots for the given years will be saved to the passed path.

    """
    ice_classes = [x for x in df['cost_curve_class'].unique() if 'ice' in x]
    bev_classes = [x for x in df['cost_curve_class'].unique() if 'bev' in x]
    hev_classes = [x for x in df['cost_curve_class'].unique() if 'hev' in x and 'phev' not in x]
    for year in years:
        ice_data = dict()
        ice_plot = list()
        ice_legends = list()
        bev_data = dict()
        bev_plot = list()
        bev_legends = list()
        hev_data = dict()
        hev_plot = list()
        hev_legends = list()
        for cost_curve_class in ice_classes:
            ice_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cs_cert_direct_oncycle_co2e_grams_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            ice_plot.append(ice_data[cost_curve_class])
            ice_legends.append(cost_curve_class)
        for cost_curve_class in bev_classes:
            bev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cd_cert_direct_oncycle_kwh_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            bev_plot.append(bev_data[cost_curve_class])
            bev_legends.append(cost_curve_class)
        for cost_curve_class in hev_classes:
            hev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cs_cert_direct_oncycle_co2e_grams_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            hev_plot.append(hev_data[cost_curve_class])
            hev_legends.append(cost_curve_class)

        ice_plot = tuple(ice_plot)
        ice_legends = tuple(ice_legends)
        bev_plot = tuple(bev_plot)
        bev_legends = tuple(bev_legends)
        hev_plot = tuple(hev_plot)
        hev_legends = tuple(hev_legends)

        # create ice plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for ice_plot, ice_legends in zip(ice_plot, ice_legends):
            x, y = ice_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=ice_legends)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            plt.legend(loc=2)
            plt.title(f'ice_{year}')
            plt.savefig(path / f'ice_{year}_{input_settings.name_id}.png')

        # create bev plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for bev_plot, bev_legends in zip(bev_plot, bev_legends):
            x, y = bev_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=bev_legends)
            ax.set(xlim=(0, 0.5), ylim=(10000, 60000))
            plt.legend(loc=4)
            plt.title(f'bev_{year}')
            plt.savefig(path / f'bev_{year}_{input_settings.name_id}.png')

        # create hev plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for hev_plot, hev_legends in zip(hev_plot, hev_legends):
            x, y = hev_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=hev_legends)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            plt.legend(loc=2)
            plt.title(f'hev_{year}')
            plt.savefig(path / f'hev_{year}_{input_settings.name_id}.png')


def create_cost_df_in_consistent_dollar_basis(deflators, dollar_basis, file, sheet_name, *args, index_col=0):
    """

    Args:
        deflators: A dictionary of GDP deflators with years as the keys.
        dollar_basis: The dollar basis to which all monetized values are to be converted.
        file: The file containing monetized values to be converted into dollar_basis dollars.
        sheet_name: The specific worksheet within file for which monetized values are to be converted.
        args: The arguments to be converted.

    Returns:
         A DataFrame of monetized values in a consistent dollar_basis valuation.

    """
    df = pd.read_excel(file, sheet_name, index_col=index_col)
    df = convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args)
    return df


def convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args):
    """

    Args:
        df: A DataFrame containing monetized values to be converted into a consistent dollar_basis.
        deflators: A dictionary of GDP deflators with years as the keys.
        dollar_basis: The dollar basis to which all monetized values are to be converted.
        args: The arguments to be converted.

    Returns:
        A DataFrame of monetized values in a consistent dollar_basis valuation.

    """
    dollar_years = pd.Series(df.loc[df['dollar_basis'] > 0, 'dollar_basis']).unique()
    for year in dollar_years:
        for arg in args:
            df.loc[df['dollar_basis'] == year, arg] = df[arg] * deflators[year]['adjustment_factor']
    df['dollar_basis'] = dollar_basis
    return df


def calc_year_over_year_costs(df, arg, years, learning_rate):
    """

    Args:
        df: A DataFrame of ALPHA packages with costs for a single start year.
        arg: The argument for which year-over-year costs are to be calculated.
        years: The years for which year-over-year costs are to be calculated.
        learning_rate: The learning rate to apply to start year costs to calculated year-over-year costs.

    Returns:
        A DataFrame of ALPHA packages with costs for all years passed.

    """
    for year in years:
        df.insert(len(df.columns), f'{arg}_{year}', df[arg] * (1 - learning_rate) ** (year - years[0]))
    return df


def sum_vehicle_parts(df, years, new_arg, *args):
    """

    Args:
        df: A DataFrame of ALPHA packages with year-over-year costs for all years.
        years: The years for which new_arg year-over-year costs are to be calculated.
        args: The arguments to sum into a single new_arg value for each of the passed years.

    Returns:
        A DataFrame of year-over-year costs that now includes summed args expressed as the new_arg.

    """
    for year in years:
        df.insert(len(df.columns), f'{new_arg}_{year}', 0)
        for arg in args:
             df[f'{new_arg}_{year}'] += df[f'{arg}_{year}']
    return df


def reshape_df_for_cloud_file(runtime_settings, input_settings, df_source, *id_args):
    """

    Args:
        runtime_settings: The RuntimeSettings class.
        input_settings: The InputSettings class.
        df_source: A DataFrame of ALPHA packages containing year-over-year costs to be reshaped into the cost cloud.
        id_args: The arguments to use as ID variables in the reshaped DataFrame (pd.melt).

    Return:
        A DataFrame in the desired shape of the cost cloud file.

    """
    df_return = pd.DataFrame()
    id_variables = [id_arg for id_arg in id_args]
    tech_flag_list = ['ac_leakage', 'ac_efficiency', 'high_eff_alternator', 'start_stop', 'hev', 'phev', 'bev',
                      'weight_reduction', 'curb_weight', 'deac_pd', 'deac_fc', 'cegr', 'atk2', 'gdi', 'turb12', 'turb11',
                      ]
    for tech in tech_flag_list:
        id_variables.append(tech)
    if runtime_settings.run_bev or runtime_settings.run_phev:
        for arg in df_source.columns:
            if arg.__contains__('kwh_per_mile'):
                id_variables.append(arg)
    if runtime_settings.run_ice or runtime_settings.run_hev or runtime_settings.run_phev:
        for arg in df_source.columns:
            if arg.__contains__('grams_per_mile'):
                id_variables.append(arg)
    source_args = id_variables.copy()
    for year in input_settings.years:
        source_args.append(f'new_vehicle_mfr_cost_dollars_{year}')
    for year in input_settings.years:
        temp = pd.melt(df_source[source_args], id_vars=id_variables, value_vars=f'new_vehicle_mfr_cost_dollars_{year}', value_name='new_vehicle_mfr_cost_dollars')
        temp.insert(1, 'model_year', year)
        temp.drop(columns='variable', inplace=True)
        df_return = pd.concat([df_return, temp], ignore_index=True, axis=0)
    return df_return


def drop_columns(df, *args):
    """

    Args:
        df: A DataFrame in which a column is to be dropped.
        args: The column names to be dropped.

    Returns:
        A DataFrame without columns=args.

    """
    cols_to_drop = list()
    for arg in args:
        if arg in df.columns:
            cols_to_drop.append(arg)
        else: pass
    df.drop(columns=cols_to_drop, inplace=True)
    return df


def clean_alpha_data(input_df, *args):
    """

    Args:
        input_df: A DataFrame based on a single ALPHA file is which some data is to be cleaned.
        args: The arguments for which cleaning is to be done.

    Returns:
        The passed DataFrame with data cleaned (text values converted to integers, % signs removed, etc.).

    """
    # clean data with percent signs
    df = input_df.copy()
    df = pd.DataFrame(df.loc[df['Engine'] != 'engine_future_Ricardo_EGRB_1L0_Tier2', :])
    test_args = [arg for arg in df.columns.tolist() if arg in args]
    for arg in test_args:
        df = df.join(df[arg].str.split('.', expand=True))
        df.drop(columns=[arg, 1], inplace=True)
        df.rename(columns={0: arg}, inplace=True)
        df[arg] = pd.to_numeric(df[arg])
    return df


def add_elements_for_package_key(input_df):
    """

    Args:
        input_df: A DataFrame of ALPHA packages for which columns are to be created for use in the package key.

    Returns:
        The passed DataFrame with additional columns for use in the package key.

    """
    df = input_df.copy().fillna(0)
    df = pd.DataFrame(df.loc[df['Vehicle Type'] != 0, :]).reset_index(drop=True)
    df.insert(0, 'Structure Class', 'unibody')
    for index, row in df.iterrows():
        if row['Vehicle Type'] == 'Truck': df.loc[index, 'Structure Class'] = 'ladder'
        else: pass

    df.insert(df.columns.get_loc('Key'), 'Price Class', 1)
    return df


def calc_battery_kwh_gross(input_settings, input_df):
    """

    Args:
        input_settings: The InputSettings class.
        input_df: A DataFrame of plug-in vehicles for which battery gross kWh is to be calculated based on values set in the module's input file.

    Returns:
        A list of gross kWh values indexed exactly as the input_df.

    """
    battery_kwh_list = list()
    for kwh_per_100_miles in input_df['Combined Consumption Rate']:
        battery_kwh_list.append(input_settings.onroad_bev_range_miles / input_settings.bev_usable_soc * (kwh_per_100_miles / 100) / (1 - input_settings.bev_gap))
    return battery_kwh_list


def calc_battery_weight(input_settings, battery_kwh_list, curves_dict):
    """

    Args:
        input_settings: The InputSettings class.
        battery_kwh_list: A list of gross battery kWh values for which battery weights are to be calculated.
        curves_dict: A dictionary of battery metrics including kWh_pack_per_kg_pack_curve.

    Returns:
        A list of battery weights for each battery in the passed battery_kwh_list.

    """
    battery_weight_list = list()
    for battery_kwh in battery_kwh_list:
        battery_weight_list.append(input_settings.lbs_per_kg * battery_kwh / (curves_dict['kWh_pack_per_kg_pack_curve']['x_cubed_factor'] * battery_kwh ** 3
                                                                              + curves_dict['kWh_pack_per_kg_pack_curve']['x_squared_factor'] * battery_kwh ** 2
                                                                              + curves_dict['kWh_pack_per_kg_pack_curve']['x_factor'] * battery_kwh
                                                                              + curves_dict['kWh_pack_per_kg_pack_curve']['constant']))
    return battery_weight_list


def calc_glider_weight(input_settings, battery_weight_list, curb_weight_series, fuel_id):
    """
    Args:
        input_settings: The InputSettings class.
        battery_weight_list: A list of battery weights.
        curb_weight_series: A Series of curb weights.
        fuel_id: The fuel ID (i.e., 'ice', 'bev', 'hev').

    Returns:
        A list of glider weights for fuel_id vehicles having the curb weights and battery weights according to the passed lists.

    """
    glider_weight_list = list()
    if fuel_id == 'ice':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] * input_settings.ice_glider_share)
    if fuel_id == 'bev':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] - battery_weight)
    if fuel_id == 'hev':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] * input_settings.ice_glider_share - battery_weight)
    return glider_weight_list


def create_package_dict(input_settings, input_df, fuel_id):
    """

    Args:
        input_settings: The InputSettings class.
        input_df: A DataFrame of ALPHA packages having the passed fuel_id (i.e., 'ice', 'bev', 'hev').
        fuel_id: The fuel ID (i.e., 'ice', 'bev', 'hev').

    Returns:
        The passed DataFrame converted to a dictionary having package_keys as the dictionary keys.

    """
    df = input_df.copy().fillna(0)
    alpha_keys = pd.Series(df['Key'])
    fuel_keys = pd.Series([fuel_id] * len(df))
    structure_keys = pd.Series(df['Structure Class'])
    price_keys = pd.Series(df['Price Class'])
    alpha_class_keys = pd.Series(df['Vehicle Type'])
    if fuel_id != 'bev':
        engine_keys = pd.Series(zip(df['Engine'], df['Engine Displacement L'], df['Engine Cylinders'].astype(int),
                                    df['DEAC D Cyl.'].astype(int), df['DEAC C Cyl.'].astype(int), df['Start Stop']))
    else: engine_keys = pd.Series([0] * len(df))
    if fuel_id == 'ice':
        hev_keys = pd.Series([0] * len(df))
        pev_keys = pd.Series([0] * len(df))
    if fuel_id == 'bev':
        hev_keys = pd.Series([0] * len(df))
        battery_kwh_gross_list = calc_battery_kwh_gross(input_settings, df)
        # determine onboard charger specs
        onboard_charger_kw_list = list()
        for battery_kwh_gross in battery_kwh_gross_list:
            if battery_kwh_gross < 70: onboard_charger_kw_list.append(7)
            elif 70 <= battery_kwh_gross < 100: onboard_charger_kw_list.append(11)
            else: onboard_charger_kw_list.append(19)
        # determine single or dual motor bev
        number_of_motors_list = list()
        for structure_class in structure_keys:
            if structure_class == 'unibody': number_of_motors_list.append('single')
            else: number_of_motors_list.append('dual')
        size_scaler_list = pd.cut(df['Test Weight lbs'] - 300, input_settings.size_bins, labels=list(range(1, input_settings.size_bins + 1)))
        pev_keys = pd.Series(zip(pd.Series([input_settings.onroad_bev_range_miles] * len(df)),
                                 df['Combined Consumption Rate'] / 100,
                                 pd.Series([input_settings.bev_usable_soc] * len(df)),
                                 pd.Series([input_settings.bev_gap] * len(df)),
                                 battery_kwh_gross_list,
                                 pd.Series([input_settings.bev_motor_power] * len(df)),
                                 number_of_motors_list,
                                 onboard_charger_kw_list,
                                 size_scaler_list))
    if fuel_id == 'hev':
        pev_keys = pd.Series([0] * len(df))
        battery_kwh_gross_list = df['battery_kwh_gross']
        motor_kw_list = df['motor_kw']
        size_scaler_list = pd.cut(df['Test Weight lbs'] - 300, input_settings.size_bins, labels=list(range(1, input_settings.size_bins + 1)))
        hev_keys = pd.Series(zip(pd.Series([input_settings.hev_metrics_dict['usable_soc_hev']['value']] * len(df)),
                                 pd.Series([input_settings.hev_metrics_dict['gap_hev']['value']] * len(df)),
                                 battery_kwh_gross_list,
                                 motor_kw_list,
                                 size_scaler_list))
    if fuel_id != 'bev': trans_keys = pd.Series(df['Transmission'])
    else: trans_keys = pd.Series([0] * len(df))

    if fuel_id != 'bev': accessory_keys = pd.Series(df['Accessory'])
    else: accessory_keys = pd.Series(['REGEN'] * len(df))

    if fuel_id != 'bev': aero_keys = pd.Series(df['Aero Improvement %'])
    else: aero_keys = pd.Series([20] * len(df))

    if fuel_id != 'bev': nonaero_keys = pd.Series(df['Crr Improvement %'])
    else: nonaero_keys = pd.Series([20] * len(df))

    curb_weights_series = pd.Series(df['Test Weight lbs'] - 300)

    if fuel_id == 'ice':
        battery_weight_list = pd.Series([0] * len(df))
        glider_weight_list = calc_glider_weight(input_settings, battery_weight_list, curb_weights_series, fuel_id)
        weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, df['Weight Reduction %']))
    if fuel_id == 'bev':
        battery_weight_list = calc_battery_weight(input_settings, battery_kwh_gross_list, input_settings.bev_curves_dict)
        glider_weight_list = calc_glider_weight(input_settings, battery_weight_list, curb_weights_series, fuel_id)
        weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, pd.Series([input_settings.bev_weight_reduction] * len(df))))
    if fuel_id == 'hev':
        battery_weight_list = calc_battery_weight(input_settings, battery_kwh_gross_list, input_settings.hev_curves_dict)
        glider_weight_list = calc_glider_weight(input_settings, battery_weight_list, curb_weights_series, fuel_id)
        weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, df['Weight Reduction %']))
    else:
        pass
    cost_keys = pd.Series(zip(fuel_keys, structure_keys, price_keys, alpha_class_keys,
                              engine_keys, hev_keys, pev_keys,
                              trans_keys, accessory_keys, aero_keys, nonaero_keys, weight_keys))
    keys = pd.Series(zip(alpha_keys, cost_keys))
    df.insert(0, 'cost_key', cost_keys)
    df.insert(0, 'alpha_key', alpha_keys)
    df.insert(0, 'key', keys)
    df.set_index('key', inplace=True)
    df_dict = df.to_dict('index')
    # return keys, df_dict
    return df_dict


def create_tech_flags_from_cost_key(df, engine_key, weight_key, accessory_key, fuel_key):
    """

    Args:
        df: A DataFrame of simulated vehicle packages.
        engine_key: The engine key set by the create_package_dict function.
        weight_key: The weight key set by the create_package_dict function.
        accessory_key: The accessory key set by the create_package_dict function
        fuel_key: The fuel key set by the create_package_dict which is first set within main().

    Return:
        The passed DataFrame with tech flags (0, 1, etc.) added.

    """
    # set tech flags to 0, indicating that the tech is not present on the package
    turb11_value, turb12_value, di_value, atk2_value, cegr_value, deacpd_value, deacfc_value, accessory_value, startstop, hev_value, bev_value, phev_value \
        = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    # set tech flags to 1 where applicable
    curb_weight, glider_weight, battery_weight, weight_rdxn = weight_key
    if accessory_key.__contains__('REGEN'): accessory_value = 1
    if fuel_key != 'bev':
        engine_name, disp, cyl, deacpd, deacfc, startstop = engine_key
        turb, finj, atk, cegr = Engines().get_techs(engine_name)
        if turb == 'TURB11': turb11_value = 1
        if turb == 'TURB12': turb12_value = 1
        if finj == 'DI': di_value = 1
        if atk == 'ATK2': atk2_value = 1
        if cegr == 'CEGR': cegr_value = 1
        if deacpd != 0: deacpd_value = 1
        if deacfc != 0: deacfc_value = 1
    if fuel_key == 'bev':
        startstop = 1
        accessory_value = 1
        bev_value = 1
    if fuel_key == 'hev': hev_value = 1
    if fuel_key == 'phev': phev_value = 1

    df.insert(0, 'ac_leakage', 1)
    df.insert(0, 'ac_efficiency', 1)
    df.insert(0, 'high_eff_alternator', accessory_value)
    df.insert(0, 'bev', bev_value)
    df.insert(0, 'phev', phev_value)
    df.insert(0, 'hev', hev_value)
    df.insert(0, 'start_stop', startstop)
    df.insert(0, 'curb_weight', curb_weight)
    df.insert(0, 'weight_reduction', weight_rdxn / 100)
    df.insert(0, 'deac_fc', deacfc_value)
    df.insert(0, 'deac_pd', deacpd_value)
    df.insert(0, 'cegr', cegr_value)
    df.insert(0, 'atk2', atk2_value)
    df.insert(0, 'gdi', di_value)
    df.insert(0, 'turb12', turb12_value)
    df.insert(0, 'turb11', turb11_value)

    return df


def ice_package_results(runtime_settings, input_settings, key, alpha_file_dict, alpha_file_name):
    """

    This function generates costs, etc., of ICE packages or ICE elements of electrified packages.

    Args:
        runtime_settings: The RuntimeSettings class.
        input_settings: The InputSettings class.
        key: The key within the alpha_file_dict that uniquely identifies the package (see the create_package_dict function).
        alpha_file_dict: A dictionary of ALPHA packages created by the create_package_dict function.
        alpha_file_name: The name of the file from which the ALPHA packages are derived.

    Returns:
        A single row DataFrame containing necessary cycle results, credit flags, and first year costs of the given package.

    """
    pkg_obj = PackageCost(key)
    alpha_key, cost_key = pkg_obj.get_object_attributes(['alpha_key', 'cost_key'])
    print(cost_key)

    fuel_key, alpha_class_key, engine_key, accessory_key, weight_key \
        = pkg_obj.get_object_attributes(['fuel_key', 'alpha_class_key', 'engine_key', 'accessory_key', 'weight_key'])
    ftp1_co2, ftp2_co2, ftp3_co2, hwy_co2, combined_co2 = alpha_file_dict[key]['EPA_FTP_1 gCO2e/mi'], \
                                                          alpha_file_dict[key]['EPA_FTP_2 gCO2e/mi'], \
                                                          alpha_file_dict[key]['EPA_FTP_3 gCO2e/mi'], \
                                                          alpha_file_dict[key]['EPA_HWFET gCO2e/mi'], \
                                                          alpha_file_dict[key]['Combined GHG gCO2e/mi']
    engine_cost = pkg_obj.engine_cost(input_settings.engine_cost_dict, input_settings.startstop_cost_dict, input_settings.boost_multiplier)
    trans_cost = pkg_obj.calc_trans_cost(input_settings.trans_cost_dict)
    accessories_cost = pkg_obj.calc_accessory_cost(input_settings.accessories_cost_dict)
    ac_cost = pkg_obj.calc_ac_cost(input_settings.ac_cost_dict)
    if fuel_key == 'hev':
        hev_key = pkg_obj.get_object_attributes(['hev_key'])
        battery_cost, non_battery_cost, hev_cost = pkg_obj.electrification_cost(input_settings)
    else: hev_cost = 0
    powertrain_cost = engine_cost + trans_cost + accessories_cost + ac_cost + hev_cost
    powertrain_cost_df = pd.DataFrame(powertrain_cost, columns=['ice_powertrain'], index=[alpha_key])

    aero_cost = pkg_obj.calc_aero_cost(input_settings.aero_cost_dict)
    nonaero_cost = pkg_obj.calc_nonaero_cost(input_settings.nonaero_cost_dict)
    roadload_cost = aero_cost + nonaero_cost
    roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[alpha_key])

    weight_cost = pkg_obj.calc_weight_cost(input_settings.weight_cost_ice_dict, input_settings.price_class_dict)
    body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[alpha_key])

    package_cost_df = powertrain_cost_df.join(roadload_cost_df).join(body_cost_df)
    package_cost_df.insert(0, 'cs_cert_direct_oncycle_co2e_grams_per_mile', combined_co2)
    package_cost_df.insert(0, 'cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile', hwy_co2)
    package_cost_df.insert(0, 'cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile', ftp2_co2) ## FOR NOW ONLY!!! -KNew
    package_cost_df.insert(0, 'cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile', ftp3_co2)
    package_cost_df.insert(0, 'cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile', ftp2_co2)
    package_cost_df.insert(0, 'cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile', ftp1_co2)
    if runtime_settings.set_tech_tracking_flags:
        package_cost_df = create_tech_flags_from_cost_key(package_cost_df, engine_key, weight_key, accessory_key, fuel_key)
    package_cost_df.insert(0, 'dollar_basis', input_settings.dollar_basis)
    package_cost_df.insert(0, 'cost_curve_class', f'ice_{alpha_class_key}')
    package_cost_df.insert(0, 'cost_key', str(cost_key))
    package_cost_df.insert(0, 'alpha_filename', alpha_file_name)

    return package_cost_df


def pev_package_results(runtime_settings, input_settings, key, alpha_file_dict, alpha_file_name):
    """

    This function generates costs, etc., of BEV packages or plug-in electric elements of electrified packages.

    Args:
        runtime_settings: The RuntimeSettings class.
        input_settings: The InputSettings class.
        key: The key within the alpha_file_dict that uniquely identifies the package (see the create_package_dict function).
        alpha_file_dict: A dictionary of ALPHA packages created by the create_package_dict function.
        alpha_file_name: The name of the file from which the ALPHA packages are derived.

    Returns:
        A single row DataFrame containing necessary cycle results, credit flags, and first year costs of the given package.

    """
    pkg_obj = PackageCost(key)
    alpha_key, cost_key = pkg_obj.get_object_attributes(['alpha_key', 'cost_key'])
    print(cost_key)
    fuel_key, alpha_class_key, pev_key, engine_key, weight_key, accessory_key \
        = pkg_obj.get_object_attributes(['fuel_key', 'alpha_class_key', 'pev_key', 'engine_key', 'weight_key', 'accessory_key'])
    onroad_range, oncycle_kwh_per_mile, usable_soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = pev_key
    ftp1_kwh, ftp2_kwh, ftp3_kwh, hwy_kwh, combined_kwh = alpha_file_dict[key]['EPA_FTP_1_kWhr/100mi'] / 100, \
                                                          alpha_file_dict[key]['EPA_FTP_2_kWhr/100mi'] / 100, \
                                                          alpha_file_dict[key]['EPA_FTP_3_kWhr/100mi'] / 100, \
                                                          alpha_file_dict[key]['EPA_HWFET_kWhr/100mi'] / 100, \
                                                          oncycle_kwh_per_mile
    ac_cost = pkg_obj.calc_ac_cost(input_settings.ac_cost_dict)
    battery_cost, nonbattery_cost, pev_cost = pkg_obj.electrification_cost(input_settings)
    powertrain_cost = pev_cost + ac_cost
    powertrain_cost_df = pd.DataFrame({'pev_battery': battery_cost, 'pev_nonbattery': nonbattery_cost, 'pev_powertrain': powertrain_cost}, index=[alpha_key])
    aero_cost = pkg_obj.calc_aero_cost(input_settings.aero_cost_dict)
    nonaero_cost = pkg_obj.calc_nonaero_cost(input_settings.nonaero_cost_dict)
    roadload_cost = aero_cost + nonaero_cost
    roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[alpha_key])

    weight_cost = pkg_obj.calc_weight_cost(input_settings.weight_cost_pev_dict, input_settings.price_class_dict)
    body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[alpha_key])

    package_cost_df = powertrain_cost_df.join(roadload_cost_df).join(body_cost_df)
    package_cost_df.insert(0, 'cd_cert_direct_oncycle_kwh_per_mile', combined_kwh)
    package_cost_df.insert(0, 'cd_hwfet:cert_direct_oncycle_kwh_per_mile', hwy_kwh)
    package_cost_df.insert(0, 'cd_ftp_4:cert_direct_oncycle_kwh_per_mile', ftp2_kwh) ## FOR NOW ONLY!!! -KNew
    package_cost_df.insert(0, 'cd_ftp_3:cert_direct_oncycle_kwh_per_mile', ftp3_kwh)
    package_cost_df.insert(0, 'cd_ftp_2:cert_direct_oncycle_kwh_per_mile', ftp2_kwh)
    package_cost_df.insert(0, 'cd_ftp_1:cert_direct_oncycle_kwh_per_mile', ftp1_kwh)
    if runtime_settings.set_tech_tracking_flags:
        package_cost_df = create_tech_flags_from_cost_key(package_cost_df, engine_key, weight_key, accessory_key, fuel_key)
    package_cost_df.insert(0, 'battery_kwh_gross', battery_kwh_gross)
    package_cost_df.insert(0, 'dollar_basis', input_settings.dollar_basis)
    package_cost_df.insert(0, 'cost_curve_class', f'{fuel_key}_{alpha_class_key}')
    package_cost_df.insert(0, 'cost_key', str(cost_key))
    package_cost_df.insert(0, 'alpha_filename', alpha_file_name)

    return package_cost_df


def read_and_clean_file(input_settings, alpha_file, fuel_id):
    """

    Args:
        input_settings: The InputSettings class.
        alpha_file: The name of the file from which the ALPHA packages are derived.
        fuel_id: The fuel ID (i.e., 'ice', 'bev', 'hev').

    Returns:
         A dictionary based on the passed alpha_file created by the create_package_dict function with data cleaned as stipulated by the clean_alpha_data function.

    """
    df = pd.read_csv(alpha_file, skiprows=range(1, 2))
    if fuel_id == 'ice':
        df = clean_alpha_data(df, 'Aero Improvement %', 'Crr Improvement %', 'Weight Reduction %')
    df = add_elements_for_package_key(df)
    alpha_file_dict = create_package_dict(input_settings, df, fuel_id)
    return alpha_file_dict


class Engines:
    """

    The Engines class defines specific technologies on each ALPHA engine benchmarked by EPA.

    """
    def __init__(self):
        self._engines = {'engine_2013_GM_Ecotec_LCV_2L5_PFI_Tier3': {'turb': '',
                                                                     'finj': 'PFI',
                                                                     'atk': '',
                                                                     'cegr': '',
                                                                     },
                         'engine_2013_GM_Ecotec_LCV_2L5_Tier3': {'turb': '',
                                                                 'finj': 'DI',
                                                                 'atk': '',
                                                                 'cegr': '',
                                                                 },
                         'engine_2014_GM_EcoTec3_LV3_4L3_Tier2_PFI_no_deac': {'turb': '',
                                                                              'finj': 'PFI',
                                                                              'atk': '',
                                                                              'cegr': '',
                                                                              },
                         'engine_2014_GM_EcoTec3_LV3_4L3_Tier2_no_deac': {'turb': '',
                                                                          'finj': 'DI',
                                                                          'atk': '',
                                                                          'cegr': '',
                                                                          },
                         'engine_2015_Ford_EcoBoost_2L7_Tier2': {'turb': 'TURB11',
                                                                 'finj': 'DI',
                                                                 'atk': '',
                                                                 'cegr': '',
                                                                 },
                         'engine_2013_Ford_EcoBoost_1L6_Tier2': {'turb': 'TURB11',
                                                                 'finj': 'DI',
                                                                 'atk': '',
                                                                 'cegr': '',
                                                                 },
                         'engine_2016_Honda_L15B7_1L5_Tier2': {'turb': 'TURB12',
                                                               'finj': 'DI',
                                                               'atk': '',
                                                               'cegr': 'CEGR',
                                                               },
                         'engine_2014_Mazda_Skyactiv_US_2L0_Tier2': {'turb': '',
                                                                     'finj': 'DI',
                                                                     'atk': 'ATK2',
                                                                     'cegr': '',
                                                                     },
                         'engine_2016_toyota_TNGA_2L5_paper_image': {'turb': '',
                                                                     'finj': 'DI',
                                                                     'atk': 'ATK2',
                                                                     'cegr': 'CEGR',
                                                                     },
                         'engine_future_EPA_Atkinson_r2_2L5': {'turb': '',
                                                               'finj': 'DI',
                                                               'atk': 'ATK2',
                                                               'cegr': 'CEGR',
                                                               },
                         'engine_future_Ricardo_EGRB_1L0_Tier2': {'turb': 'TURB12',
                                                                  'finj': 'DI',
                                                                  'atk': '',
                                                                  'cegr': 'CEGR',
                                                                  },
                         }

    def get_techs(self, engine_name):
        """

        Args:
            engine_name: The ALPHA engine name read from the ALPHA file.

        Returns:
            The technology cost codes for specific engine technologies.

        """
        turb, finj, atk, cegr = self._engines.get(engine_name).values()
        return turb, finj, atk, cegr


class EngineCost:
    """

    The EngineCost class calculates the cost of specific technologies contained on the given engine.

    """
    def __init__(self, engine_key, weight_key):
        self.engine_name, self.disp, self.cyl, self.deacpd, self.deacfc, self.startstop = engine_key
        self.weight_key = weight_key

    def calc_engine_cost(self, engine_cost_dict, startstop_cost_dict, boost_multiplier, fuel_id):
        """

        Args:
            engine_cost_dict: A dictionary of engine costs as read from the alpha package cost input file.
            startstop_cost_dict: A dictionary of start-stop cost metrics as read from the alpha package cost input file.
            boost_multiplier: A numeric value entered in the alpha package cost input file that represents the multiplier to be applied to engine costs to reflect the additional costs
            associated with boosted engines.
            fuel_id: The fuel ID (i.e., 'ice', 'bev', 'hev').

        Returns:
            A numeric value representing the cost of the given engine in the given package.

        """
        turb, finj, atk, cegr = Engines().get_techs(self.engine_name)
        curb_wt, glider_weight, battery_weight, weight_rdxn = self.weight_key
        cost = self.disp * engine_cost_dict['dollars_per_liter']['item_cost']
        cost += self.cyl * engine_cost_dict[f'dollars_per_cyl_{self.cyl}']['item_cost']
        if turb: cost += cost * (boost_multiplier - 1) + engine_cost_dict[f'{turb}_{self.cyl}']['item_cost']
        if cegr: cost += engine_cost_dict['CEGR']['item_cost']
        if finj: cost += engine_cost_dict[f'DI_{self.cyl}']['item_cost']
        if self.deacpd != 0: cost += engine_cost_dict[f'DeacPD_{self.cyl}']['item_cost']
        if self.deacfc != 0: cost += engine_cost_dict[f'DeacFC']['item_cost']
        if atk: cost += engine_cost_dict[f'ATK2_{self.cyl}']['item_cost']
        # reminder that ss_cost is included in HEV costs so not double counted here (PHEV?)
        ss_cost = 0
        if self.startstop == 1 and fuel_id == 'ice':
            for ss_key in startstop_cost_dict.keys():
                if startstop_cost_dict[ss_key]['curb_weight_min'] < curb_wt <= startstop_cost_dict[ss_key]['curb_weight_max']:
                    ss_cost = startstop_cost_dict[ss_key]['item_cost']
                else:
                    pass
            cost += ss_cost
        return cost


class PackageCost:
    """

    The PackageCost class calculates the cost of the passed package based on the package cost key.

    """
    def __init__(self, key):
        self.alpha_key, self.cost_key = key
        self.fuel_key, self.structure_key, self.price_key, self.alpha_class_key, self.engine_key, self.hev_key, self.pev_key, \
        self.trans_key, self.accessory_key, self.aero_key, self.nonaero_key, self.weight_key = self.cost_key

    def get_object_attributes(self, attribute_list):
        """

        Args:
            self: the object to get attributes from
            attribute_list: a list of attribute names

        Returns:
            A list containing the values of the requested attributes

        """
        return [self.__getattribute__(attr) for attr in attribute_list]

    def engine_cost(self, engine_cost_dict, startstop_cost_dict, boost_multiplier):
        """

        The engine_cost function passes necessary data to the EngineCost class.

        Args:
            engine_cost_dict: A dictionary of engine costs as read from the alpha package cost input file.
            startstop_cost_dict: A dictionary of start-stop cost metrics as read from the alpha package cost input file.
            boost_multiplier: A numeric value entered in the alpha package cost input file that represents the multiplier to be applied to engine costs to reflect the additional costs
            associated with boosted engines.

        Returns:
            The engine cost after resulting from the EngineCost class.

        """
        return EngineCost(self.engine_key, self.weight_key).calc_engine_cost(engine_cost_dict, startstop_cost_dict, boost_multiplier, self.fuel_key)

    def electrification_cost(self, input_settings):
        """
        The electrification_cost function calculates the cost of batteries and motors.

        Args:
            input_settings: The InputSettings class.

        Returns:
            The battery cost, the motor cost and the combined cost for the given package.

        """
        battery_kwh_gross, motor_power, markup = 0, 0, 0
        curves_dict = dict()
        if self.fuel_key == 'bev':
            range, energy_rate, soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = self.pev_key
            curves_dict = input_settings.bev_curves_dict
            if number_of_motors == 'single':
                nonbattery_dict = input_settings.bev_nonbattery_single_dict
                motor_power_divisor = 1
            else:
                nonbattery_dict = input_settings.bev_nonbattery_dual_dict
                motor_power_divisor = 2
            markup = input_settings.bev_powertrain_markup
            dcdc_converter_plus_obc = curves_dict['kW_DCDC_converter']['constant'] + onboard_charger_kw

        elif self.fuel_key == 'hev':
            soc, gap, battery_kwh_gross, motor_power, size_scaler = self.hev_key
            curves_dict = input_settings.hev_curves_dict
            nonbattery_dict = input_settings.hev_nonbattery_dict
            markup = input_settings.hev_metrics_dict['powertrain_markup_hev']['value']
            onboard_charger_kw = 0
            motor_power_divisor = 1
            dcdc_converter_plus_obc = curves_dict['kW_DCDC_converter']['constant'] + onboard_charger_kw

        battery_cost = battery_kwh_gross * (curves_dict['dollars_per_kWh_curve']['x_cubed_factor'] * battery_kwh_gross ** 3
                                            + curves_dict['dollars_per_kWh_curve']['x_squared_factor'] * battery_kwh_gross ** 2
                                            + curves_dict['dollars_per_kWh_curve']['x_factor'] * battery_kwh_gross
                                            + curves_dict['dollars_per_kWh_curve']['constant'])

        motor_cost = nonbattery_dict['motor']['quantity'] * (nonbattery_dict['motor']['slope'] * motor_power / motor_power_divisor + nonbattery_dict['motor']['intercept'])
        inverter_cost = nonbattery_dict['inverter']['quantity'] * (nonbattery_dict['inverter']['slope'] * motor_power / motor_power_divisor + nonbattery_dict['inverter']['intercept'])
        induction_motor_cost = nonbattery_dict['induction_motor']['quantity'] * nonbattery_dict['induction_motor']['slope'] * motor_power / motor_power_divisor
        induction_inverter_cost = nonbattery_dict['induction_inverter']['quantity'] * nonbattery_dict['induction_inverter']['slope'] * motor_power / motor_power_divisor
        dcdc_converter_cost = nonbattery_dict['DCDC_converter']['quantity'] * nonbattery_dict['DCDC_converter']['slope'] * dcdc_converter_plus_obc
        hv_orange_cables_cost =  nonbattery_dict['HV_orange_cables']['quantity'] * nonbattery_dict['HV_orange_cables']['slope'] * size_scaler + nonbattery_dict['HV_orange_cables']['intercept']
        lv_battery_cost = nonbattery_dict['LV_battery']['quantity'] * nonbattery_dict['LV_battery']['slope'] * size_scaler + nonbattery_dict['LV_battery']['intercept']
        hvac_cost = nonbattery_dict['HVAC']['quantity'] * nonbattery_dict['HVAC']['slope'] * size_scaler + nonbattery_dict['HVAC']['intercept']
        single_speed_gearbox_cost = nonbattery_dict['single_speed_gearbox']['quantity'] * nonbattery_dict['single_speed_gearbox']['intercept']
        powertrain_cooling_loop_cost = nonbattery_dict['powertrain_cooling_loop']['quantity'] * nonbattery_dict['powertrain_cooling_loop']['intercept']
        charging_cord_kit_cost = nonbattery_dict['charging_cord_kit']['quantity'] * nonbattery_dict['charging_cord_kit']['intercept']
        DC_fast_charge_circuitry_cost = nonbattery_dict['DC_fast_charge_circuitry']['quantity'] * nonbattery_dict['DC_fast_charge_circuitry']['intercept']
        power_management_and_distribution_cost = nonbattery_dict['power_management_and_distribution']['quantity'] * nonbattery_dict['power_management_and_distribution']['intercept']
        additional_pair_of_half_shafts_cost = nonbattery_dict['additional_pair_of_half_shafts']['quantity'] * nonbattery_dict['additional_pair_of_half_shafts']['intercept']
        brake_sensors_actuators_cost = nonbattery_dict['brake_sensors_actuators']['quantity'] * nonbattery_dict['brake_sensors_actuators']['intercept']

        non_battery_cost = motor_cost + inverter_cost + induction_motor_cost + induction_inverter_cost \
                           + dcdc_converter_cost + hv_orange_cables_cost + lv_battery_cost + hvac_cost \
                           + single_speed_gearbox_cost + powertrain_cooling_loop_cost + charging_cord_kit_cost \
                           + DC_fast_charge_circuitry_cost + power_management_and_distribution_cost \
                           + additional_pair_of_half_shafts_cost + brake_sensors_actuators_cost

        battery_cost = battery_cost * markup
        non_battery_cost = non_battery_cost * markup
        cost = battery_cost + non_battery_cost
        return battery_cost, non_battery_cost, cost

    def calc_phev_cost(self):
        """

        Args:

        Returns:

        """
        cost = 0
        return cost

    def calc_trans_cost(self, trans_cost_dict):
        """

        Args:
            trans_cost_dict: A dictionary of transmission costs as read from the alpha package cost input file.

        Returns:
            The transmission cost for the given package based on its trans_key.

        """
        return trans_cost_dict[self.trans_key]['item_cost']

    def calc_accessory_cost(self, accessory_cost_dict):
        """

        Args:
            accessory_cost_dict: A dictionary of accessory costs as read from the alpha package cost input file.

        Returns:
            The accessory cost for the given package based on its accessory_key.

        """
        return accessory_cost_dict[self.accessory_key]['item_cost']

    def calc_aero_cost(self, aero_cost_dict):
        """

        Args:
            aero_cost_dict: A dictionary of aero costs as read from the alpha package cost input file.

        Returns:
            The aero cost for the given package based on its aero_key.

        """
        tech_class = f'{self.structure_key}_{self.aero_key}'
        return aero_cost_dict[tech_class]['item_cost']

    def calc_nonaero_cost(self, nonaero_cost_dict):
        """

        Args:
            aero_cost_dict: A dictionary of aero costs as read from the alpha package cost input file.

        Returns:
            The aero cost for the given package based on its aero_key.

        """
        tech_class = f'{self.structure_key}_{self.nonaero_key}'
        return nonaero_cost_dict[tech_class]['item_cost']

    def calc_ac_cost(self, ac_cost_dict):
        """

        Args:
            ac_cost_dict: A dictionary of ac costs as read from the alpha package cost input file.

        Returns:
            The ac cost for the given package based on its structure_key.

        """
        return ac_cost_dict[self.structure_key]['item_cost']

    def calc_weight_cost(self, weight_cost_dict, price_class_dict):
        """

        Weight costs are calculated as an absolute cost associated with the curb weight of the vehicle and are then adjusted according to the weight reduction.

        Args:
            weight_cost_dict: A dictionary of weight costs as read from the alpha package cost input file.
            price_class_dict: A dictionary of price class multipliers as read from the alpha package cost input file. These are applied as multipliers to the weight costs..

        Returns:
            The cost associated with the steel, aluminum, plastic, etc., of the given vehicle package.

        """
        curb_wt, glider_weight, battery_weight, weight_rdxn = self.weight_key
        weight_rdxn = weight_rdxn / 100
        weight_cost_cache_key = (self.weight_key, self.price_key, self.structure_key, self.fuel_key)
        if weight_cost_cache_key in weight_cost_cache.keys():
            cost = weight_cost_cache[weight_cost_cache_key]
        else:
            weight_removed = glider_weight / (1 - weight_rdxn) - glider_weight
            base_wt = glider_weight + weight_removed
            base_weight_cost_per_lb = weight_cost_dict[self.structure_key]['item_cost'] * price_class_dict[self.price_key]['scaler']
            dmc_ln_coeff = weight_cost_dict[self.structure_key]['DMC_ln_coefficient']
            dmc_constant = weight_cost_dict[self.structure_key]['DMC_constant']
            ic_slope = weight_cost_dict[self.structure_key]['IC_slope']
            cost = base_wt * base_weight_cost_per_lb
            if weight_rdxn != 0:
                cost += ((dmc_ln_coeff * np.log(weight_rdxn) + dmc_constant) + (ic_slope * weight_rdxn)) * weight_removed
            weight_cost_cache[weight_cost_cache_key] = cost
        return cost


class RuntimeSettings:
    """

    The RuntimeSettings class determines what costs to calculate and what, if any, simulated_vehicles files to generate by setting entries
    equal to True or False.

    """
    def __init__(self):
        """

        Make runtime selections.

        """
        # set what to run (i.e., what outputs to generate)
        self.run_ice = True
        self.run_bev = True
        self.run_phev = False
        self.run_hev = True
        self.generate_simulated_vehicles_file = True
        self.generate_simulated_vehicles_verbose_file = False

        # set tech to track via tech flags
        self.set_tech_tracking_flags = True


class InputSettings:
    """

    The InputSettings class sets input values for this module as well as reading the input file and creating dictionaries for use throughout the module.

    """
    def __init__(self):
        """

        Read input files and convert monetized values to a consistent dollar basis.

        """
        self.path_to_file = Path(__file__).parent
        self.path_preproc = self.path_to_file.parent
        self.path_project = self.path_preproc.parent
        self.path_inputs = self.path_to_file / 'inputs'
        self.path_outputs = self.path_to_file / 'outputs'
        self.path_alpha_inputs = self.path_to_file / 'ALPHA'
        self.path_input_templates = self.path_project / 'omega_model/demo_inputs'

        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

        # get the price deflators
        self.dollar_basis = int(context_aeo_inputs.aeo_version) - 1

        # set input filenames
        self.gdp_deflators_file = self.path_preproc / f'bea_tables/implicit_price_deflators_{self.dollar_basis}.csv'
        self.techcosts_file = pd.ExcelFile(self.path_inputs / 'alpha_package_costs_module_inputs.xlsx')

        try:
            self.gdp_deflators = pd.read_csv(self.path_preproc / f'bea_tables/implicit_price_deflators_{self.dollar_basis}.csv', index_col=0)
            self.gdp_deflators = self.gdp_deflators.to_dict('index')
            self.techcosts_file = pd.ExcelFile(self.path_inputs / 'alpha_package_costs_module_inputs.xlsx')
            self.price_class_dict = pd.read_excel(self.techcosts_file, 'price_class', index_col=0).to_dict('index')
            # read tech costs input file, convert dollar values to dollar basis, and create dictionaries
            self.engine_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                   'engine', 'item_cost', 'dmc').to_dict('index')
            self.trans_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                  'trans', 'item_cost', 'dmc', 'dmc_increment').to_dict('index')
            self.accessories_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                        'accessories', 'item_cost', 'dmc').to_dict('index')
            self.startstop_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                      'start-stop', 'item_cost', 'dmc').to_dict('index')
            self.weight_cost_ice_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                       'weight_ice', 'item_cost', 'dmc_per_pound').to_dict('index')
            self. weight_cost_pev_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                        'weight_pev', 'item_cost', 'dmc_per_pound').to_dict('index')
            self.aero_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                 'aero', 'item_cost', 'dmc').to_dict('index')
            self.nonaero_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                    'nonaero', 'item_cost', 'dmc').to_dict('index')
            self.ac_cost_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                               'ac', 'item_cost', 'dmc').to_dict('index')

            self.bev_curves_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                  'bev_curves', 'x_cubed_factor', 'x_squared_factor',
                                                                                  'x_factor', 'constant').to_dict('index')
            self.hev_curves_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                  'hev_curves', 'x_cubed_factor', 'x_squared_factor',
                                                                                  'x_factor', 'constant').to_dict('index')

            self.bev_nonbattery_single_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                             'bev_nonbattery_single',
                                                                                             'slope', 'intercept').to_dict('index')
            self.bev_nonbattery_dual_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                           'bev_nonbattery_dual',
                                                                                           'slope', 'intercept').to_dict('index')
            self.hev_nonbattery_dict = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators, self.dollar_basis, self.techcosts_file,
                                                                                      'hev_nonbattery',
                                                                                      'slope', 'intercept').to_dict('index')
            # phev_curves_dict = 0
            self.pev_metrics_dict = pd.read_excel(self.techcosts_file, sheet_name='pev_metrics', index_col=0).to_dict('index')
            self.hev_metrics_dict = pd.read_excel(self.techcosts_file, sheet_name='hev_metrics', index_col=0).to_dict('index')

            # set inputs
            self.cost_inputs = pd.read_excel(self.techcosts_file, 'inputs_code', index_col=0).to_dict('index')
            self.start_year = int(self.cost_inputs['start_year']['value'])
            self.end_year = int(self.cost_inputs['end_year']['value'])
            self.years = range(self.start_year, self.end_year + 1)
            self.learning_rate_weight = self.cost_inputs['learning_rate_weight']['value']
            self.learning_rate_ice_powertrain = self.cost_inputs['learning_rate_ice_powertrain']['value']
            self.learning_rate_roadload = self.cost_inputs['learning_rate_roadload']['value']
            self.learning_rate_bev = self.cost_inputs['learning_rate_bev']['value']
            self.boost_multiplier = self.cost_inputs['boost_multiplier']['value']
            self.run_id = self.cost_inputs['run_ID']['value']
            if self.run_id != '':
                self.name_id = f'{self.run_id}_{self.start_time_readable}'
            else:
                self.name_id = self.start_time_readable

            self.ice_glider_share = 0.85

            # for now, set a BEV range and motor power here
            self.onroad_bev_range_miles = 300
            self.bev_motor_power = 150
            self.bev_weight_reduction = 0
            self.bev_usable_soc = self.pev_metrics_dict['usable_soc_bev']['value']
            self.bev_gap = self.pev_metrics_dict['gap_bev']['value']
            self.bev_powertrain_markup = self.pev_metrics_dict['powertrain_markup_bev']['value']

            self.size_bins = 7
            # for now, set HEV size bins here
            self.hev_size_bins = 7
            self.bin_size_scaling_interval = 0.05
            self.bin_with_scaler_equal_1 = 3

            # set constants
            self.lbs_per_kg = 2.2

        except:
            import traceback
            print(traceback.format_exc())

    def create_cost_df_in_consistent_dollar_basis(self, deflators, dollar_basis, file, sheet_name, *args, index_col=0):
        """

        Args:
            deflators: A dictionary of GDP deflators with years as the keys.
            dollar_basis: The dollar basis to which all monetized values are to be converted.
            file: The file containing monetized values to be converted into dollar_basis dollars.
            sheet_name: The specific worksheet within file for which monetized values are to be converted.
            args: The arguments to be converted.

        Returns:
             A DataFrame of monetized values in a consistent dollar_basis valuation.

        """
        df = pd.read_excel(file, sheet_name, index_col=index_col)
        df = self.convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args)
        return df

    def convert_dollars_to_analysis_basis(self, df, deflators, dollar_basis, *args):
        """

        Args:
            df: A DataFrame containing monetized values to be converted into a consistent dollar_basis.
            deflators: A dictionary of GDP deflators with years as the keys.
            dollar_basis: The dollar basis to which all monetized values are to be converted.
            args: The arguments to be converted.

        Returns:
            A DataFrame of monetized values in a consistent dollar_basis valuation.

        """
        dollar_years = pd.Series(df.loc[df['dollar_basis'] > 0, 'dollar_basis']).unique()
        for year in dollar_years:
            for arg in args:
                df.loc[df['dollar_basis'] == year, arg] = df[arg] * deflators[year]['adjustment_factor']
        df['dollar_basis'] = dollar_basis
        return df


def main():

    runtime_settings = RuntimeSettings()
    input_settings = InputSettings()
    # settings = SetInputs()

    ice_packages_df, bev_packages_df, hev_packages_df, phev_packages_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    if runtime_settings.run_bev:
        fuel_id = 'bev'
        alpha_folder = input_settings.path_alpha_inputs / 'BEV'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = read_and_clean_file(input_settings, alpha_file_name, fuel_id)
            for key in alpha_file_dict.keys():
                package_result = pev_package_results(runtime_settings, input_settings, key, alpha_file_dict, alpha_file_name)
                bev_packages_df = pd.concat([bev_packages_df, package_result], axis=0, ignore_index=False)

    if runtime_settings.run_phev:
        fuel_id = 'phev'
        alpha_folder = input_settings.path_alpha_inputs / 'PHEV'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = read_and_clean_file(input_settings, alpha_file_name, fuel_id)
            for key in alpha_file_dict.keys():
                package_result = pev_package_results(runtime_settings, input_settings, key, alpha_file_dict, alpha_file_name)
                phev_packages_df = pd.concat([phev_packages_df, package_result], axis=0, ignore_index=False)

    if runtime_settings.run_hev:
        fuel_id = 'hev'
        alpha_folder = input_settings.path_alpha_inputs / 'HEV'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = read_and_clean_file(input_settings, alpha_file_name, fuel_id)
            for key in alpha_file_dict.keys():
                package_result = ice_package_results(runtime_settings, input_settings, key, alpha_file_dict, alpha_file_name)
                hev_packages_df = pd.concat([hev_packages_df, package_result], axis=0, ignore_index=False)

    if runtime_settings.run_ice:
        fuel_id = 'ice'
        alpha_folder = input_settings.path_alpha_inputs / 'ICE'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = read_and_clean_file(input_settings, alpha_file_name, fuel_id)
            for key in alpha_file_dict.keys():
            # keys, alpha_file_dict = read_and_clean_file(settings, alpha_file_name, fuel_id)
            # for key in keys:
                package_result = ice_package_results(runtime_settings, input_settings, key, alpha_file_dict, alpha_file_name)
                ice_packages_df = pd.concat([ice_packages_df, package_result], axis=0, ignore_index=False)

    # calculate YoY bev costs with learning
    if runtime_settings.run_bev:
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_battery', input_settings.years, input_settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_nonbattery', input_settings.years, input_settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_powertrain', input_settings.years, input_settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'roadload', input_settings.years, input_settings.learning_rate_roadload)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'body', input_settings.years, input_settings.learning_rate_weight)
        bev_packages_df.reset_index(drop=False, inplace=True)
        bev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'bev_{idx}' for idx in range(1, len(bev_packages_df) + 1)]
        bev_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        bev_packages_df = sum_vehicle_parts(bev_packages_df, input_settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'pev_powertrain', 'roadload', 'body')

    # calculate YoY hev costs with learning
    if runtime_settings.run_hev:
        hev_packages_df = calc_year_over_year_costs(hev_packages_df, 'ice_powertrain', input_settings.years, input_settings.learning_rate_ice_powertrain)
        hev_packages_df = calc_year_over_year_costs(hev_packages_df, 'roadload', input_settings.years, input_settings.learning_rate_roadload)
        hev_packages_df = calc_year_over_year_costs(hev_packages_df, 'body', input_settings.years, input_settings.learning_rate_weight)
        hev_packages_df.reset_index(drop=False, inplace=True)
        hev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'hev_{idx}' for idx in range(1, len(hev_packages_df) + 1)]
        hev_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        hev_packages_df = sum_vehicle_parts(hev_packages_df, input_settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'roadload', 'body')

    # calculate YoY ice costs with learning
    if runtime_settings.run_ice:
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'ice_powertrain', input_settings.years, input_settings.learning_rate_ice_powertrain)
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'roadload', input_settings.years, input_settings.learning_rate_roadload)
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'body', input_settings.years, input_settings.learning_rate_weight)
        ice_packages_df.reset_index(drop=False, inplace=True)
        ice_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'ice_{idx}' for idx in range(1, len(ice_packages_df) + 1)]
        ice_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        ice_packages_df = sum_vehicle_parts(ice_packages_df, input_settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'roadload', 'body')

    input_settings.path_outputs.mkdir(exist_ok=True)
    input_settings.path_of_run_folder = input_settings.path_outputs / f'{input_settings.name_id}'
    input_settings.path_of_run_folder.mkdir(exist_ok=False)

    cost_cloud, cost_cloud_bev, cost_cloud_phev, cost_cloud_hev, cost_cloud_ice \
        = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    if runtime_settings.run_bev:
        cost_cloud_bev = reshape_df_for_cloud_file(runtime_settings, input_settings, bev_packages_df,
                                                   'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')
    if runtime_settings.run_phev:
        cost_cloud_phev = reshape_df_for_cloud_file(runtime_settings, input_settings, phev_packages_df,
                                                    'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')
    if runtime_settings.run_hev:
        cost_cloud_hev = reshape_df_for_cloud_file(runtime_settings, input_settings, hev_packages_df,
                                                   'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')
    if runtime_settings.run_ice:
        cost_cloud_ice = reshape_df_for_cloud_file(runtime_settings, input_settings, ice_packages_df,
                                                   'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')

    cost_cloud = pd.concat([cost_cloud_bev, cost_cloud_phev, cost_cloud_hev, cost_cloud_ice], axis=0, ignore_index=True)

    cost_cloud_verbose = cost_cloud.copy()
    cost_cloud.fillna(0, inplace=True)

    cost_vs_plot(input_settings, cost_cloud, input_settings.path_of_run_folder, 2020, 2030, 2040)

    bev_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_bev_{input_settings.name_id}.csv', index=False)
    ice_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_ice_{input_settings.name_id}.csv', index=False)
    hev_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_hev_{input_settings.name_id}.csv', index=False)

    if runtime_settings.generate_simulated_vehicles_file:
        cost_cloud = drop_columns(cost_cloud, 'cert_co2e_grams_per_mile', 'cert_kWh_per_mile', 'alpha_key',
                                  'alpha_filename', 'cs_cert_direct_oncycle_co2e_grams_per_mile',
                                  'cd_cert_direct_oncycle_kwh_per_mile')
        # open the 'simulated_vehicles.csv' input template into which results will be placed.
        cost_clouds_template_info = pd.read_csv(input_settings.path_input_templates.joinpath('simulated_vehicles.csv'), 'b', nrows=0)
        temp = ' '.join((item for item in cost_clouds_template_info))
        temp2 = temp.split(',')
        temp2 = temp2[:4]
        temp2.append(f'{input_settings.name_id}')
        df = pd.DataFrame(columns=temp2)
        df.to_csv(input_settings.path_of_run_folder.joinpath('simulated_vehicles.csv'), index=False)

        with open(input_settings.path_of_run_folder.joinpath('simulated_vehicles.csv'), 'a', newline='') as cloud_file:
            cost_cloud.to_csv(cloud_file, index=False)

    if runtime_settings.generate_simulated_vehicles_verbose_file:
        df.to_csv(input_settings.path_of_run_folder.joinpath('simulated_vehicles_verbose.csv'), index=False)

        with open(input_settings.path_of_run_folder.joinpath('simulated_vehicles_verbose.csv'), 'a', newline='') as cloud_file:
            cost_cloud_verbose.to_csv(cloud_file, index=False)
        # cost_cloud_verbose.to_csv(settings.path_of_run_folder / f'simulated_vehicles_verbose.csv', index=False)

    # save additional outputs
    modified_costs = pd.ExcelWriter(input_settings.path_of_run_folder.joinpath(f'techcosts_in_{input_settings.dollar_basis}_dollars.xlsx'))
    pd.DataFrame(input_settings.engine_cost_dict).transpose().to_excel(modified_costs, sheet_name='engine', index=True)
    pd.DataFrame(input_settings.trans_cost_dict).transpose().to_excel(modified_costs, sheet_name='trans', index=True)
    pd.DataFrame(input_settings.startstop_cost_dict).transpose().to_excel(modified_costs, sheet_name='start-stop', index=False)
    pd.DataFrame(input_settings.accessories_cost_dict).transpose().to_excel(modified_costs, sheet_name='accessories', index=True)
    pd.DataFrame(input_settings.aero_cost_dict).transpose().to_excel(modified_costs, sheet_name='aero', index=False)
    pd.DataFrame(input_settings.nonaero_cost_dict).transpose().to_excel(modified_costs, sheet_name='nonaero', index=False)
    pd.DataFrame(input_settings.weight_cost_ice_dict).transpose().to_excel(modified_costs, sheet_name='weight_ice', index=True)
    pd.DataFrame(input_settings.weight_cost_pev_dict).transpose().to_excel(modified_costs, sheet_name='weight_pev', index=True)
    pd.DataFrame(input_settings.ac_cost_dict).transpose().to_excel(modified_costs, sheet_name='ac', index=True)
    pd.DataFrame(input_settings.bev_curves_dict).transpose().to_excel(modified_costs, sheet_name='bev_curves', index=True)
    pd.DataFrame(input_settings.hev_curves_dict).transpose().to_excel(modified_costs, sheet_name='hev_curves', index=True)
    modified_costs.save()

    # copy input files into the output folder
    input_files_list = [input_settings.techcosts_file]
    filename_list = [Path(path).name for path in input_files_list]
    for file in filename_list:
        path_source = input_settings.path_inputs.joinpath(file)
        path_destination = input_settings.path_of_run_folder.joinpath(file)
        shutil.copy2(path_source, path_destination)  # copy2 should maintain date/timestamps

    print(f'\nOutput files have been saved to {input_settings.path_of_run_folder}')


if __name__ == '__main__':
    import os, traceback

    try:
        main()
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
