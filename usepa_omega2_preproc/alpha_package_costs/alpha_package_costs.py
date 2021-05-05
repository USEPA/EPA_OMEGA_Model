import pandas as pd
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
from pathlib import Path

from usepa_omega2_preproc.context_aeo import SetInputs as context_aeo_inputs


weight_cost_cache = dict()


def cost_vs_plot(df, path, name_id, *years):
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
            ice_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_co2_grams_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            ice_plot.append(ice_data[cost_curve_class])
            ice_legends.append(cost_curve_class)
        for cost_curve_class in bev_classes:
            bev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_kwh_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            bev_plot.append(bev_data[cost_curve_class])
            bev_legends.append(cost_curve_class)
        for cost_curve_class in hev_classes:
            hev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_co2_grams_per_mile'],
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
            plt.savefig(path / f'ice_{year}_{name_id}.png')

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
            plt.savefig(path / f'bev_{year}_{name_id}.png')

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
            plt.savefig(path / f'hev_{year}_{name_id}.png')


def cost_vs_plot_combined(df, path, name_id, *years): # can't do this with co2/mi and kWh/mi
    classes = [x for x in df['cost_curve_class'].unique()]
    for year in years:
        class_data = dict()
        class_plot = list()
        class_legends = list()
        for cost_curve_class in classes:
            class_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_grams_per_mile'],
                                            df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            class_plot.append(class_data[cost_curve_class])
            class_legends.append(cost_curve_class)

        class_plot = tuple(class_plot)
        class_legends = tuple(class_legends)

        # create ice plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for class_plot, class_legends in zip(class_plot, class_legends):
            x, y = class_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=class_legends)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            plt.legend(loc=1)
            plt.title(f'{year}')
            plt.savefig(path / f'{year}_{name_id}.png')


def create_df_and_convert_dollars(deflators, dollar_basis, file, sheet_name, *args, index_col=0):
    df = pd.read_excel(file, sheet_name, index_col=index_col)
    df = convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args)
    return df


def convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args):
    dollar_years = pd.Series(df['dollar_basis']).unique()
    for year in dollar_years:
        for arg in args:
            df.loc[df['dollar_basis'] == year, arg] = df[arg] * deflators[year]['adjustment_factor']
    df['dollar_basis'] = dollar_basis
    return df


def dollar_basis_year(df):
    for i in range(len(df)):
        if df.iloc[i]['adjustment_factor'] == 1:
            dollar_year = df.index[i]
    return dollar_year


def calc_year_over_year_costs(df, arg, years, learning_rate):
    for year in years:
        df.insert(len(df.columns), f'{arg}_{year}', df[arg] * (1 - learning_rate) ** (year - years[0]))
    return df


def sum_vehicle_parts(df, years, new_arg, *args):
    for year in years:
        df.insert(len(df.columns), f'{new_arg}_{year}', 0)
        for arg in args:
             df[f'{new_arg}_{year}'] += df[f'{arg}_{year}']
    return df


def reshape_df_for_cloud_file(settings, df_source):
    df_return = pd.DataFrame()
    id_variables = ['cost_curve_class', 'alpha_key']
    if settings.run_bev or settings.run_phev:
        for arg in df_source.columns:
            if arg.__contains__('kWh_per_mile'):
                id_variables.append(arg)
    if settings.run_ice or settings.run_hev or settings.run_phev:
        for arg in df_source.columns:
            if arg.__contains__('grams_per_mile'):
                id_variables.append(arg)
    source_args = id_variables.copy()
    for year in settings.years:
        source_args.append(f'new_vehicle_mfr_cost_dollars_{year}')
    for year in settings.years:
        temp = pd.melt(df_source[source_args], id_vars=id_variables, value_vars=f'new_vehicle_mfr_cost_dollars_{year}', value_name='new_vehicle_mfr_cost_dollars')
        temp.insert(1, 'model_year', year)
        temp.drop(columns='variable', inplace=True)
        df_return = pd.concat([df_return, temp], ignore_index=True, axis=0)
    return df_return


def drop_columns(df, arg):
    cols_to_drop = [col for col in df.columns if arg in col]
    df.drop(columns=cols_to_drop, inplace=True)
    return df


def clean_alpha_data(input_df, *args):
    """

    :param input_df: A DataFrame of ALPHA results.
    :param args: Arguments within the passed DataFrame to clean of '%' signs.
    :return: The passed DataFrame with *args washed of % signs.
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

    :param input_df: A DataFrame of ALPHA results.
    :return: The passed DataFrame with additional columns for use in the package_key function.
    """
    df = input_df.copy().fillna(0)
    df = pd.DataFrame(df.loc[df['Vehicle Type'] != 0, :]).reset_index(drop=True)
    df.insert(0, 'Structure Class', 'unibody')
    for index, row in df.iterrows():
        if row['Vehicle Type'] == 'Truck': df.loc[index, 'Structure Class'] = 'ladder'
        else: pass

    df.insert(df.columns.get_loc('Key'), 'Price Class', 1)
    return df


def calc_battery_kwh_gross(settings, input_df):
    battery_kwh_list = list()
    for kwh_per_100_miles in input_df['Combined Consumption Rate']:
        battery_kwh_list.append(settings.onroad_bev_range_miles / settings.bev_usable_soc * (kwh_per_100_miles / 100) / (1 - settings.bev_gap))
    return battery_kwh_list


def calc_battery_weight(settings, battery_kwh_list, curves_dict):
    battery_weight_list = list()
    for battery_kwh in battery_kwh_list:
        battery_weight_list.append(settings.lbs_per_kg * battery_kwh / (curves_dict['x_cubed_factor']['kWh_pack_per_kg_pack_curve'] * battery_kwh ** 3
                                                                        + curves_dict['x_squared_factor']['kWh_pack_per_kg_pack_curve'] * battery_kwh ** 2
                                                                        + curves_dict['x_factor']['kWh_pack_per_kg_pack_curve'] * battery_kwh
                                                                        + curves_dict['constant']['kWh_pack_per_kg_pack_curve']))
    return battery_weight_list


def calc_glider_weight(settings, battery_weight_list, curb_weight_series, fuel_id):
    glider_weight_list = list()
    if fuel_id == 'ice':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] * settings.ice_glider_share)
    if fuel_id == 'bev':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] - battery_weight)
    if fuel_id == 'hev':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] * settings.ice_glider_share - battery_weight)
    return glider_weight_list


def package_key(settings, input_df, fuel_id):
    """

    :param input_df: A DataFrame of ALPHA results.
    :return: A Series of package keys and the passed DataFrame converted to a dictionary.
    """
    df = input_df.copy().fillna(0)
    alpha_keys = pd.Series(df['Key'])
    # unique_keys = pd.Series(df['Unique Key'])
    fuel_keys = pd.Series([fuel_id] * len(df))
    structure_keys = pd.Series(df['Structure Class'])
    price_keys = pd.Series(df['Price Class'])
    alpha_class_keys = pd.Series(df['Vehicle Type'])
    if fuel_id != 'bev':
        engine_keys = pd.Series(zip(df['Engine'], df['Engine Displacement L'], df['Engine Cylinders'].astype(int), df['DEAC D Cyl.'].astype(int), df['Start Stop']))
    else: engine_keys = pd.Series([0] * len(df))
    if fuel_id == 'ice':
        hev_keys = pd.Series([0] * len(df))
        pev_keys = pd.Series([0] * len(df))
    if fuel_id == 'bev':
        hev_keys = pd.Series([0] * len(df))
        battery_kwh_gross_list = calc_battery_kwh_gross(settings, df)
        pev_keys = pd.Series(zip(pd.Series([settings.onroad_bev_range_miles] * len(df)),
                                 df['Combined Consumption Rate'] / 100,
                                 pd.Series([settings.bev_usable_soc] * len(df)),
                                 pd.Series([settings.bev_gap] * len(df)),
                                 battery_kwh_gross_list,
                                 pd.Series([settings.bev_motor_power] * len(df))))
    if fuel_id == 'hev':
        pev_keys = pd.Series([0] * len(df))
        battery_kwh_gross_list = df['battery_kwh_gross']
        motor_kw_list = df['motor_kw']
        hev_keys = pd.Series(zip(pd.Series([settings.hev_metrics_dict['usable_soc_hev']['value']] * len(df)),
                                 pd.Series([settings.hev_metrics_dict['gap_hev']['value']] * len(df)),
                                 battery_kwh_gross_list,
                                 motor_kw_list))
    if fuel_id != 'bev': trans_keys = pd.Series(df['Transmission'])
    else: trans_keys = pd.Series([0] * len(df))

    if fuel_id != 'bev': accessory_keys = pd.Series(df['Accessory'])
    else: accessory_keys = pd.Series([0] * len(df))

    if fuel_id != 'bev': aero_keys = pd.Series(df['Aero Improvement %'])
    else: aero_keys = pd.Series([20] * len(df))

    if fuel_id != 'bev': nonaero_keys = pd.Series(df['Crr Improvement %'])
    else: nonaero_keys = pd.Series([20] * len(df))

    curb_weights_series = pd.Series(df['Test Weight lbs'] - 300)

    if fuel_id == 'ice':
        battery_weight_list = pd.Series([0] * len(df))
        glider_weight_list = calc_glider_weight(settings, battery_weight_list, curb_weights_series, fuel_id)
        weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, df['Weight Reduction %']))
    if fuel_id == 'bev':
        battery_weight_list = calc_battery_weight(settings, battery_kwh_gross_list, settings.bev_curves_dict)
        glider_weight_list = calc_glider_weight(settings, battery_weight_list, curb_weights_series, fuel_id)
        weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, pd.Series([settings.bev_weight_reduction] * len(df))))
    if fuel_id == 'hev':
        battery_weight_list = calc_battery_weight(settings, battery_kwh_gross_list, settings.hev_curves_dict)
        glider_weight_list = calc_glider_weight(settings, battery_weight_list, curb_weights_series, fuel_id)
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
    return keys, df_dict


def ice_package_results(settings, key, alpha_file_dict):
    pkg_obj = PackageCost(key)
    alpha_key, cost_key = pkg_obj.get_object_attributes(['alpha_key', 'cost_key'])
    print(cost_key)

    fuel_key, alpha_class_key = pkg_obj.get_object_attributes(['fuel_key', 'alpha_class_key'])
    ftp1_co2, ftp2_co2, ftp3_co2, hwy_co2, combined_co2 = alpha_file_dict[key]['EPA_FTP_1 gCO2/mi'], \
                                                          alpha_file_dict[key]['EPA_FTP_2 gCO2/mi'], \
                                                          alpha_file_dict[key]['EPA_FTP_3 gCO2/mi'], \
                                                          alpha_file_dict[key]['EPA_HWFET gCO2/mi'], \
                                                          alpha_file_dict[key]['Combined GHG gCO2/mi']
    engine_cost = pkg_obj.engine_cost(settings.engine_cost_dict, settings.startstop_cost_dict, settings.boost_multiplier)
    trans_cost = pkg_obj.calc_trans_cost(settings.trans_cost_dict)
    accessories_cost = pkg_obj.calc_accessory_cost(settings.accessories_cost_dict)
    ac_cost = pkg_obj.calc_ac_cost(settings.ac_cost_dict)
    if fuel_key == 'hev':
        hev_key = pkg_obj.get_object_attributes(['hev_key'])
        battery_cost, motor_cost, hev_cost = pkg_obj.electrification_cost(settings)
    else: hev_cost = 0
    powertrain_cost = engine_cost + trans_cost + accessories_cost + ac_cost + hev_cost
    powertrain_cost_df = pd.DataFrame(powertrain_cost, columns=['ice_powertrain'], index=[alpha_key])

    aero_cost = pkg_obj.calc_aero_cost(settings.aero_cost_dict)
    nonaero_cost = pkg_obj.calc_nonaero_cost(settings.nonaero_cost_dict)
    roadload_cost = aero_cost + nonaero_cost
    roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[alpha_key])

    weight_cost = pkg_obj.calc_weight_cost(settings.weight_cost_ice_dict, settings.price_class_dict)
    body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[alpha_key])

    package_cost_df = powertrain_cost_df.join(roadload_cost_df).join(body_cost_df)
    package_cost_df.insert(0, 'cert_co2_grams_per_mile', combined_co2)
    package_cost_df.insert(0, 'hwfet:co2_grams_per_mile', hwy_co2)
    package_cost_df.insert(0, 'ftp_3:co2_grams_per_mile', ftp3_co2)
    package_cost_df.insert(0, 'ftp_2:co2_grams_per_mile', ftp2_co2)
    package_cost_df.insert(0, 'ftp_1:co2_grams_per_mile', ftp1_co2)
    package_cost_df.insert(0, 'dollar_basis', settings.dollar_basis)
    package_cost_df.insert(0, 'cost_curve_class', f'{fuel_key}_{alpha_class_key}')
    package_cost_df.insert(0, 'cost_key', str(cost_key))

    return package_cost_df


def pev_package_results(settings, key, alpha_file_dict):
    pkg_obj = PackageCost(key)
    alpha_key, cost_key = pkg_obj.get_object_attributes(['alpha_key', 'cost_key'])
    print(cost_key)
    fuel_key, alpha_class_key, pev_key = pkg_obj.get_object_attributes(['fuel_key', 'alpha_class_key', 'pev_key'])
    onroad_range, oncycle_kwh_per_mile, usable_soc, gap, battery_kwh_gross, motor_power = pev_key
    ftp1_kwh, ftp2_kwh, ftp3_kwh, hwy_kwh, combined_kwh = alpha_file_dict[key]['EPA_FTP_1_kWhr/100mi'] / 100, \
                                                          alpha_file_dict[key]['EPA_FTP_2_kWhr/100mi'] / 100, \
                                                          alpha_file_dict[key]['EPA_FTP_3_kWhr/100mi'] / 100, \
                                                          alpha_file_dict[key]['EPA_HWFET_kWhr/100mi'] / 100, \
                                                          oncycle_kwh_per_mile
    ac_cost = pkg_obj.calc_ac_cost(settings.ac_cost_dict)
    battery_cost, motor_cost, pev_cost = pkg_obj.electrification_cost(settings)
    powertrain_cost = pev_cost + ac_cost
    powertrain_cost_df = pd.DataFrame({'pev_battery': battery_cost, 'pev_motor': motor_cost, 'pev_powertrain': powertrain_cost}, index=[alpha_key])
    aero_cost = pkg_obj.calc_aero_cost(settings.aero_cost_dict)
    nonaero_cost = pkg_obj.calc_nonaero_cost(settings.nonaero_cost_dict)
    roadload_cost = aero_cost + nonaero_cost
    roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[alpha_key])

    weight_cost = pkg_obj.calc_weight_cost(settings.weight_cost_pev_dict, settings.price_class_dict)
    body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[alpha_key])

    package_cost_df = powertrain_cost_df.join(roadload_cost_df).join(body_cost_df)
    package_cost_df.insert(0, 'cert_kwh_per_mile', combined_kwh)
    package_cost_df.insert(0, 'hwfet:kWh_per_mile', hwy_kwh)
    package_cost_df.insert(0, 'ftp_3:kWh_per_mile', ftp3_kwh)
    package_cost_df.insert(0, 'ftp_2:kWh_per_mile', ftp2_kwh)
    package_cost_df.insert(0, 'ftp_1:kWh_per_mile', ftp1_kwh)
    package_cost_df.insert(0, 'battery_kwh_gross', battery_kwh_gross)
    package_cost_df.insert(0, 'dollar_basis', settings.dollar_basis)
    package_cost_df.insert(0, 'cost_curve_class', f'{fuel_key}_{alpha_class_key}')
    package_cost_df.insert(0, 'cost_key', str(cost_key))

    return package_cost_df


def read_and_clean_file(settings, alpha_file, fuel_id):
    df = pd.read_csv(alpha_file, skiprows=range(1, 2))
    if fuel_id == 'ice':
        df = clean_alpha_data(df, 'Aero Improvement %', 'Crr Improvement %', 'Weight Reduction %')
    df = add_elements_for_package_key(df)
    keys, alpha_file_dict = package_key(settings, df, fuel_id)
    return keys, alpha_file_dict


class Engines:
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
        turb, finj, atk, cegr = self._engines.get(engine_name).values()
        return turb, finj, atk, cegr


class EngineCost:
    def __init__(self, engine_key, weight_key):
        self.engine_name, self.disp, self.cyl, self.deac, self.startstop = engine_key
        self.weight_key = weight_key

    def calc_engine_cost(self, engine_cost_dict, startstop_cost_dict, boost_multiplier):
        turb, finj, atk, cegr = Engines().get_techs(self.engine_name)
        curb_wt, glider_weight, battery_weight, weight_rdxn = self.weight_key
        cost = self.disp * engine_cost_dict['dollars_per_liter']['item_cost']
        cost += self.cyl * engine_cost_dict[f'dollars_per_cyl_{self.cyl}']['item_cost']
        if turb: cost += cost * (boost_multiplier - 1) + engine_cost_dict[f'{turb}_{self.cyl}']['item_cost']
        if cegr: cost += engine_cost_dict['CEGR']['item_cost']
        if finj: cost += engine_cost_dict[f'DI_{self.cyl}']['item_cost']
        if self.deac != 0: cost += engine_cost_dict[f'DeacPD_{self.cyl}']['item_cost']
        if atk: cost += engine_cost_dict[f'ATK2_{self.cyl}']['item_cost']
        ss_cost = 0
        if self.startstop != 0:
            for ss_key in startstop_cost_dict.keys():
                if startstop_cost_dict[ss_key]['curb_weight_min'] < curb_wt <= startstop_cost_dict[ss_key]['curb_weight_max']:
                    ss_cost = startstop_cost_dict[ss_key]['item_cost']
                else:
                    pass
            cost += ss_cost
        return cost


class PackageCost:
    def __init__(self, key):
        self.alpha_key, self.cost_key = key
        self.fuel_key, self.structure_key, self.price_key, self.alpha_class_key, self.engine_key, self.hev_key, self.pev_key, \
        self.trans_key, self.accessory_key, self.aero_key, self.nonaero_key, self.weight_key = self.cost_key

    def get_object_attributes(self, attribute_list):
        """

        Args:
            self: the object to get attributes from
            attribute_list: a list of attribute names

        Returns: a list containing the values of the requested attributes

        """
        return [self.__getattribute__(attr) for attr in attribute_list]

    def engine_cost(self, engine_cost_dict, startstop_cost_dict, boost_multiplier):
        return EngineCost(self.engine_key, self.weight_key).calc_engine_cost(engine_cost_dict, startstop_cost_dict, boost_multiplier)

    def electrification_cost(self, settings):
        """
        Cost of batteries and motors.
        :return:
        """
        battery_kwh_gross, motor_power, markup = 0, 0, 0
        curves_dict = dict()
        if self.fuel_key == 'bev':
            range, energy_rate, soc, gap, battery_kwh_gross, motor_power = self.pev_key
            curves_dict = settings.bev_curves_dict
            markup = settings.bev_powertrain_markup
        elif self.fuel_key == 'hev':
            soc, gap, battery_kwh_gross, motor_power = self.hev_key
            curves_dict = settings.hev_curves_dict
            markup = settings.hev_metrics_dict['powertrain_markup_hev']['value']
        battery_cost = battery_kwh_gross * (curves_dict['x_cubed_factor']['dollars_per_kwh_curve'] * battery_kwh_gross ** 3 \
                                            + curves_dict['x_squared_factor']['dollars_per_kwh_curve'] * battery_kwh_gross ** 2 \
                                            + curves_dict['x_factor']['dollars_per_kwh_curve'] * battery_kwh_gross \
                                            + curves_dict['constant']['dollars_per_kwh_curve'])
        motor_cost = motor_power * (curves_dict['x_cubed_factor']['dollars_per_kW_curve'] * motor_power ** 3 \
                                    + curves_dict['x_squared_factor']['dollars_per_kW_curve'] * motor_power ** 2 \
                                    + curves_dict['x_factor']['dollars_per_kW_curve'] * motor_power \
                                    + curves_dict['constant']['dollars_per_kW_curve'])
        battery_cost = battery_cost * markup
        motor_cost = motor_cost * markup
        cost = battery_cost + motor_cost
        return battery_cost, motor_cost, cost 

    def calc_phev_cost(self):
        """
        Cost of batteries and motors.
        :return:
        """
        cost = 0
        return cost

    def calc_trans_cost(self, trans_cost_dict):
        return trans_cost_dict[self.trans_key]['item_cost']

    def calc_accessory_cost(self, accessory_cost_dict):
        return accessory_cost_dict[self.accessory_key]['item_cost']

    def calc_aero_cost(self, aero_cost_dict):
        tech_class = f'{self.structure_key}_{self.aero_key}'
        return aero_cost_dict[tech_class]['item_cost']

    def calc_nonaero_cost(self, nonaero_cost_dict):
        tech_class = f'{self.structure_key}_{self.nonaero_key}'
        return nonaero_cost_dict[tech_class]['item_cost']

    def calc_ac_cost(self, ac_cost_dict):
        return ac_cost_dict[self.structure_key]['item_cost']

    def calc_weight_cost(self, weight_cost_dict, price_class_dict):
        """
        Weight costs are calculated as an absolute cost associated with the curb weight of the vehicle and are then adjusted according to the weight reduction.
        :param start_year: First year to calc costs.
        :param techcosts_weight: The input DataFrame associated with weight costs.
        :param work_class: Hauling vs Non-hauling work class designation.
        :return: The passed DataFrame with weight costs merged in.
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


class SetInputs:
    path_cwd = Path.cwd()
    path_preproc = path_cwd / 'usepa_omega2_preproc'
    path_here = path_preproc / 'alpha_package_costs'
    path_outputs = path_here / 'outputs'
    path_alpha_inputs = path_here / 'ALPHA'
    path_input_templates = path_cwd / 'usepa_omega2/test_inputs'

    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

    # set what to run (i.e., what outputs to generate)
    run_ice = True
    run_bev = True
    run_phev = False
    run_hev = True
    generate_cost_cloud_file = True

    # get the price deflators
    dollar_basis = int(context_aeo_inputs.aeo_version) - 1
    gdp_deflators = pd.read_csv(path_preproc / f'bea_tables/implicit_price_deflators_{dollar_basis}.csv', index_col=0)
    gdp_deflators = gdp_deflators.to_dict('index')

    # read tech costs input file, convert dollar values to dollar basis, and create dictionaries
    techcosts_file = pd.ExcelFile(path_here / 'alpha_package_costs_module_inputs.xlsx')
    price_class_dict = pd.read_excel(techcosts_file, 'price_class', index_col=0).to_dict('index')
    engine_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'engine', 'item_cost', 'dmc').to_dict('index')
    trans_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'trans', 'item_cost', 'dmc', 'dmc_increment').to_dict('index')
    accessories_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'accessories', 'item_cost', 'dmc').to_dict('index')
    startstop_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'start-stop', 'item_cost', 'dmc').to_dict('index')
    weight_cost_ice_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'weight_ice', 'item_cost', 'dmc_per_pound').to_dict('index')
    weight_cost_pev_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'weight_pev', 'item_cost', 'dmc_per_pound').to_dict('index')
    aero_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'aero', 'item_cost', 'dmc').to_dict('index')
    nonaero_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'nonaero', 'item_cost', 'dmc').to_dict('index')
    ac_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'ac', 'item_cost', 'dmc').to_dict('index')
    bev_curves_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'bev_curves', 'dollars_per_kwh_curve', 'dollars_per_kW_curve').to_dict('index')
    hev_curves_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'hev_curves', 'dollars_per_kwh_curve', 'dollars_per_kW_curve').to_dict('index')
    # phev_curves_dict = 0
    pev_metrics_dict = pd.read_excel(techcosts_file, sheet_name='pev_metrics', index_col=0).to_dict('index')
    hev_metrics_dict = pd.read_excel(techcosts_file, sheet_name='hev_metrics', index_col=0).to_dict('index')

    # set inputs
    cost_inputs = pd.read_excel(techcosts_file, 'inputs_code', index_col=0).to_dict('index')
    start_year = int(cost_inputs['start_year']['value'])
    end_year = int(cost_inputs['end_year']['value'])
    years = range(start_year, end_year + 1)
    learning_rate_weight = cost_inputs['learning_rate_weight']['value']
    learning_rate_ice_powertrain = cost_inputs['learning_rate_ice_powertrain']['value']
    learning_rate_roadload = cost_inputs['learning_rate_roadload']['value']
    learning_rate_bev = cost_inputs['learning_rate_bev']['value']
    boost_multiplier = cost_inputs['boost_multiplier']['value']
    run_id = cost_inputs['run_ID']['value']

    ice_glider_share = 0.85

    # for now, set a BEV range and motor power here
    onroad_bev_range_miles = 300
    bev_motor_power = 150
    bev_weight_reduction = 0
    bev_usable_soc = pev_metrics_dict['usable_soc_bev']['value']
    bev_charging_loss = pev_metrics_dict['charging_loss_bev']['value']
    bev_gap = pev_metrics_dict['gap_bev']['value']
    bev_powertrain_markup = pev_metrics_dict['powertrain_markup_bev']['value']

    # set constants
    lbs_per_kg = 2.2


def main():

    settings = SetInputs()

    alpha_folders = [folder for folder in settings.path_alpha_inputs.iterdir()]
    alpha_files = dict()
    ice_packages_df, bev_packages_df, hev_packages_df, phev_packages_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    if settings.run_bev:
        fuel_id = 'bev'
        alpha_folder = settings.path_alpha_inputs / 'BEV'
        alpha_files = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file in enumerate(alpha_files):
            keys, alpha_file_dict = read_and_clean_file(settings, alpha_file, fuel_id)
            for key in keys:
                package_result = pev_package_results(settings, key, alpha_file_dict)
                bev_packages_df = pd.concat([bev_packages_df, package_result], axis=0, ignore_index=False)

    if settings.run_phev:
        fuel_id = 'phev'
        alpha_folder = settings.path_alpha_inputs / 'PHEV'
        alpha_files = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file in enumerate(alpha_files):
            keys, alpha_file_dict = read_and_clean_file(settings, alpha_file, fuel_id)
            for key in keys:
                package_result = pev_package_results(settings, key, alpha_file_dict)
                phev_packages_df = pd.concat([phev_packages_df, package_result], axis=0, ignore_index=False)

    if settings.run_hev:
        fuel_id = 'hev'
        alpha_folder = settings.path_alpha_inputs / 'HEV'
        alpha_files = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file in enumerate(alpha_files):
            keys, alpha_file_dict = read_and_clean_file(settings, alpha_file, fuel_id)
            for key in keys:
                package_result = ice_package_results(settings, key, alpha_file_dict)
                hev_packages_df = pd.concat([hev_packages_df, package_result], axis=0, ignore_index=False)

    if settings.run_ice:
        fuel_id = 'ice'
        alpha_folder = settings.path_alpha_inputs / 'ICE'
        alpha_files = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file in enumerate(alpha_files):
            keys, alpha_file_dict = read_and_clean_file(settings, alpha_file, fuel_id)
            for key in keys:
                package_result = ice_package_results(settings, key, alpha_file_dict)
                ice_packages_df = pd.concat([ice_packages_df, package_result], axis=0, ignore_index=False)

    # calculate YoY bev costs with learning
    if settings.run_bev:
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_battery', settings.years, settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_motor', settings.years, settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_powertrain', settings.years, settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'roadload', settings.years, settings.learning_rate_roadload)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'body', settings.years, settings.learning_rate_weight)
        bev_packages_df.reset_index(drop=False, inplace=True)
        bev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        bev_packages_df = sum_vehicle_parts(bev_packages_df, settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'pev_powertrain', 'roadload', 'body')

    # calculate YoY hev costs with learning
    if settings.run_hev:
        hev_packages_df = calc_year_over_year_costs(hev_packages_df, 'ice_powertrain', settings.years, settings.learning_rate_ice_powertrain)
        hev_packages_df = calc_year_over_year_costs(hev_packages_df, 'roadload', settings.years, settings.learning_rate_roadload)
        hev_packages_df = calc_year_over_year_costs(hev_packages_df, 'body', settings.years, settings.learning_rate_weight)
        hev_packages_df.reset_index(drop=False, inplace=True)
        hev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        hev_packages_df = sum_vehicle_parts(hev_packages_df, settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'roadload', 'body')

    # calculate YoY ice costs with learning
    if settings.run_ice:
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'ice_powertrain', settings.years, settings.learning_rate_ice_powertrain)
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'roadload', settings.years, settings.learning_rate_roadload)
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'body', settings.years, settings.learning_rate_weight)
        ice_packages_df.reset_index(drop=False, inplace=True)
        ice_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        ice_packages_df = sum_vehicle_parts(ice_packages_df, settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'roadload', 'body')

    settings.path_outputs.mkdir(exist_ok=True)
    settings.path_of_run_folder = settings.path_outputs / f'{settings.run_id}_O2-TechCosts_{settings.start_time_readable}'
    settings.path_of_run_folder.mkdir(exist_ok=False)

    cost_cloud, cost_cloud_bev, cost_cloud_phev, cost_cloud_hev, cost_cloud_ice = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    if settings.run_bev:
        cost_cloud_bev = reshape_df_for_cloud_file(settings, bev_packages_df)
    if settings.run_phev:
        cost_cloud_phev = reshape_df_for_cloud_file(settings, phev_packages_df)
    if settings.run_hev:
        cost_cloud_hev = reshape_df_for_cloud_file(settings, hev_packages_df)
    if settings.run_ice:
        cost_cloud_ice = reshape_df_for_cloud_file(settings, ice_packages_df)

    cost_cloud = pd.concat([cost_cloud_bev, cost_cloud_phev, cost_cloud_hev, cost_cloud_ice], axis=0, ignore_index=True)

    cost_cloud.fillna(0, inplace=True)

    if settings.run_id != '': name_id = f'{settings.run_id}_{settings.start_time_readable}'
    else: name_id = settings.start_time_readable
    cost_vs_plot(cost_cloud, settings.path_of_run_folder, name_id, 2020, 2030, 2040)
    # cost_vs_plot_combined(cost_cloud, path_of_run_folder, start_time_readable, 2020, 2030, 2040)

    bev_packages_df = drop_columns(bev_packages_df, 'cert')
    ice_packages_df = drop_columns(ice_packages_df, 'cert')
    hev_packages_df = drop_columns(hev_packages_df, 'cert')
    bev_packages_df.to_csv(settings.path_of_run_folder / f'detailed_costs_bev_{name_id}.csv', index=False)
    ice_packages_df.to_csv(settings.path_of_run_folder / f'detailed_costs_ice_{name_id}.csv', index=False)
    hev_packages_df.to_csv(settings.path_of_run_folder / f'detailed_costs_hev_{name_id}.csv', index=False)

    if settings.generate_cost_cloud_file:
        cost_cloud = drop_columns(cost_cloud, 'cert')
        # open the 'cost_clouds.csv' input template into which results will be placed.
        cost_clouds_template_info = pd.read_csv(settings.path_input_templates.joinpath('cost_clouds.csv'), 'b', nrows=0)
        temp = ' '.join((item for item in cost_clouds_template_info))
        temp2 = temp.split(',')
        temp2 = temp2[:4]
        temp2.append(f'{name_id}')
        df = pd.DataFrame(columns=temp2)
        df.to_csv(settings.path_of_run_folder.joinpath('cost_clouds.csv'), index=False)

        with open(settings.path_of_run_folder.joinpath('cost_clouds.csv'), 'a', newline='') as cloud_file:
            cost_cloud.to_csv(cloud_file, index=False)
        # cost_cloud.to_csv(settings.path_of_run_folder / f'cost_clouds.csv', index=False)

    # save additional outputs
    modified_costs = pd.ExcelWriter(settings.path_of_run_folder.joinpath(f'techcosts_in_{settings.dollar_basis}_dollars.xlsx'))
    pd.DataFrame(settings.engine_cost_dict).transpose().to_excel(modified_costs, sheet_name='engine', index=True)
    pd.DataFrame(settings.trans_cost_dict).transpose().to_excel(modified_costs, sheet_name='trans', index=True)
    pd.DataFrame(settings.startstop_cost_dict).transpose().to_excel(modified_costs, sheet_name='start-stop', index=False)
    pd.DataFrame(settings.accessories_cost_dict).transpose().to_excel(modified_costs, sheet_name='accessories', index=True)
    pd.DataFrame(settings.aero_cost_dict).transpose().to_excel(modified_costs, sheet_name='aero', index=False)
    pd.DataFrame(settings.nonaero_cost_dict).transpose().to_excel(modified_costs, sheet_name='nonaero', index=False)
    pd.DataFrame(settings.weight_cost_ice_dict).transpose().to_excel(modified_costs, sheet_name='weight_ice', index=True)
    pd.DataFrame(settings.weight_cost_pev_dict).transpose().to_excel(modified_costs, sheet_name='weight_pev', index=True)
    pd.DataFrame(settings.ac_cost_dict).transpose().to_excel(modified_costs, sheet_name='ac', index=True)
    pd.DataFrame(settings.bev_curves_dict).transpose().to_excel(modified_costs, sheet_name='bev_curves', index=True)
    pd.DataFrame(settings.hev_curves_dict).transpose().to_excel(modified_costs, sheet_name='hev_curves', index=True)
    modified_costs.save()

    # copy input files into the output folder
    input_files_list = [settings.techcosts_file]
    filename_list = [Path(path).name for path in input_files_list]
    for file in filename_list:
        path_source = settings.path_here.joinpath(file)
        path_destination = settings.path_of_run_folder.joinpath(file)
        shutil.copy2(path_source, path_destination)  # copy2 should maintain date/timestamps

    print(f'\nOutput files have been saved to {settings.path_of_run_folder}')


if __name__ == '__main__':
    import os, traceback

    try:
        main()
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
