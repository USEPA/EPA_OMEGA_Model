import pandas as pd
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
from pathlib import Path
from itertools import product


weight_cost_cache = dict()


def cost_vs_plot(df, path, name_id, *years):
    ice_classes = [x for x in df['cost_curve_class'].unique() if 'ice' in x]
    bev_classes = [x for x in df['cost_curve_class'].unique() if 'bev' in x]
    for year in years:
        ice_data = dict()
        ice_plot = list()
        ice_legends = list()
        bev_data = dict()
        bev_plot = list()
        bev_legends = list()
        for cost_curve_class in ice_classes:
            ice_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_co2_grams_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            ice_plot.append(ice_data[cost_curve_class])
            ice_legends.append(cost_curve_class)
        for cost_curve_class in bev_classes:
            bev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_kWh_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            bev_plot.append(bev_data[cost_curve_class])
            bev_legends.append(cost_curve_class)

        ice_plot = tuple(ice_plot)
        ice_legends = tuple(ice_legends)
        bev_plot = tuple(bev_plot)
        bev_legends = tuple(bev_legends)

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
            ax.set(xlim=(0, 0.5), ylim=(10000, 100000))
            plt.legend(loc=4)
            plt.title(f'bev_{year}')
            plt.savefig(path / f'bev_{year}_{name_id}.png')


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
    id_variables = ['cost_curve_class']
    if settings.run_bev:
        for arg in df_source.columns:
            if arg.__contains__('kWh_per_mile'):
                id_variables.append(arg)
    if settings.run_ice:
        for arg in df_source.columns:
            if arg.__contains__('grams_per_mile'):
                id_variables.append(arg)
    source_args = id_variables.copy()
    for year in settings.years:
        source_args.append(f'new_vehicle_mfr_cost_dollars_{year}')
    for year in settings.years:
        temp = pd.melt(df_source[source_args], id_vars=id_variables, value_vars=f'new_vehicle_mfr_cost_dollars_{year}', value_name='new_vehicle_mfr_cost_dollars')
        # temp = pd.melt(df_source[['cost_curve_class', 'cert_co2_grams_per_mile', 'cert_kWh_per_mile', f'new_vehicle_mfr_cost_dollars_{year}']],
        #                id_vars=['cost_curve_class', 'cert_co2_grams_per_mile', 'cert_kWh_per_mile'],
        #                value_vars=f'new_vehicle_mfr_cost_dollars_{year}',
        #                value_name='new_vehicle_mfr_cost_dollars')
        temp.insert(1, 'model_year', year)
        temp.drop(columns='variable', inplace=True)
        df_return = pd.concat([df_return, temp], ignore_index=True, axis=0)
    return df_return


def clean_alpha_data(input_df, *args):
    """

    :param input_df: A DataFrame of ALPHA results.
    :param args: Arguments within the passed DataFrame to clean of '%' signs.
    :return: The passed DataFrame with *args washed of % signs.
    """
    # clean data with percent signs
    df = input_df.copy()
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


def calc_battery_weight(settings, battery_kwh_list):
    battery_weight_list = list()
    for battery_kwh in battery_kwh_list:
        battery_weight_list.append(settings.lbs_per_kg * battery_kwh / (settings.pev_curves_dict['x_cubed_factor']['kWh_per_kg_curve'] * battery_kwh ** 3
                                                                        + settings.pev_curves_dict['x_squared_factor']['kWh_per_kg_curve'] * battery_kwh ** 2
                                                                        + settings.pev_curves_dict['x_factor']['kWh_per_kg_curve'] * battery_kwh
                                                                        + settings.pev_curves_dict['constant']['kWh_per_kg_curve']))
    return battery_weight_list


def calc_glider_weight(settings, battery_weight_list, curb_weight_series, fuel_id):
    glider_weight_list = list()
    if fuel_id == 'ice':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] * settings.ice_glider_share)
    if fuel_id == 'bev':
        for idx, battery_weight in enumerate(battery_weight_list):
            glider_weight_list.append(curb_weight_series[idx] - battery_weight)
    return glider_weight_list


def package_key(settings, input_df, fuel_id):
    """

    :param input_df: A DataFrame of ALPHA results.
    :return: A Series of package keys and the passed DataFrame converted to a dictionary.
    """
    df = input_df.copy().fillna(0)
    unique_keys = pd.Series(df['Unique Key'])
    fuel_keys = pd.Series([fuel_id] * len(df))
    structure_keys = pd.Series(df['Structure Class'])
    price_keys = pd.Series(df['Price Class'])
    alpha_keys = pd.Series(df['Vehicle Type'])
    if fuel_id != 'bev':
        engine_keys = pd.Series(zip(df['Engine'], df['Engine Displacement L'], df['Engine Cylinders'].astype(int), df['DEAC D Cyl.'].astype(int), df['Start Stop']))
    else: engine_keys = pd.Series([0] * len(df))
    if fuel_id == 'ice': pev_keys = pd.Series([0] * len(df))
    else:
        battery_kwh_gross_list = calc_battery_kwh_gross(settings, df)
        pev_keys = pd.Series(zip(pd.Series([settings.onroad_bev_range_miles] * len(df)),
                                 df['Combined Consumption Rate'] / 100,
                                 pd.Series([settings.bev_usable_soc] * len(df)),
                                 pd.Series([settings.bev_gap] * len(df)),
                                 battery_kwh_gross_list,
                                 pd.Series([settings.bev_motor_power] * len(df))))
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
        battery_weight_list = calc_battery_weight(settings, battery_kwh_gross_list)
        glider_weight_list = calc_glider_weight(settings, battery_weight_list, curb_weights_series, fuel_id)
        weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, pd.Series([settings.bev_weight_reduction] * len(df))))
    else:
        pass
    keys = pd.Series(zip(unique_keys, fuel_keys, structure_keys, price_keys, alpha_keys,
                         engine_keys, pev_keys,
                         trans_keys, accessory_keys, aero_keys, nonaero_keys, weight_keys))
    df.insert(0, 'package_key', keys)
    df.set_index('package_key', inplace=True)
    df_dict = df.to_dict('index')
    return keys, df_dict


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
        self.key = key
        self.unique_key, self.fuel_key, self.structure_key, self.price_key, self.alpha_key, self.engine_key, self.pev_key, \
        self.trans_key, self.accessory_key, self.aero_key, self.nonaero_key, self.weight_key = self.key

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

    def calc_bev_cost(self, pev_curves_dict):
        """
        Cost of batteries and motors.
        :return:
        """
        pev_range, pev_energy_rate, pev_soc, pev_gap, battery_kwh_gross, motor_power = self.pev_key
        battery_cost = battery_kwh_gross * (pev_curves_dict['x_cubed_factor']['dollars_per_kWh_curve'] * battery_kwh_gross ** 3 \
                                            + pev_curves_dict['x_squared_factor']['dollars_per_kWh_curve'] * battery_kwh_gross ** 2 \
                                            + pev_curves_dict['x_factor']['dollars_per_kWh_curve'] * battery_kwh_gross \
                                            + pev_curves_dict['constant']['dollars_per_kWh_curve'])
        motor_cost = motor_power * (pev_curves_dict['x_cubed_factor']['dollars_per_kW_curve'] * motor_power ** 3 \
                                    + pev_curves_dict['x_squared_factor']['dollars_per_kW_curve'] * motor_power ** 2 \
                                    + pev_curves_dict['x_factor']['dollars_per_kW_curve'] * motor_power \
                                    + pev_curves_dict['constant']['dollars_per_kW_curve'])
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
        weight_cost_cache_key = (self.weight_key, self.price_key, self.structure_key)
        if weight_cost_cache_key in weight_cost_cache.keys():
            cost = weight_cost_cache[weight_cost_cache_key]
        else:
            # base_wt = glider_weight / (1 - weight_rdxn)
            weight_removed = glider_weight / (1 - weight_rdxn) - glider_weight
            base_wt = curb_wt + weight_removed
            base_weight_cost_per_lb = weight_cost_dict[self.structure_key]['item_cost'] * price_class_dict[self.price_key]['scaler']
            dmc_ln_coeff = weight_cost_dict[self.structure_key]['DMC_ln_coefficient']
            dmc_constant = weight_cost_dict[self.structure_key]['DMC_constant']
            ic_slope = weight_cost_dict[self.structure_key]['IC_slope']
            cost = base_wt * base_weight_cost_per_lb
            if weight_rdxn != 0:
                # cost += ((dmc_ln_coeff * np.log(weight_rdxn) + dmc_constant) + (ic_slope * weight_rdxn)) * base_wt * weight_rdxn
                cost += ((dmc_ln_coeff * np.log(weight_rdxn) + dmc_constant) + (ic_slope * weight_rdxn)) * weight_removed
            weight_cost_cache[weight_cost_cache_key] = cost
        return cost


def ice_package_results(settings, key, alpha_file_dict):
    print(key)
    pkg_obj = PackageCost(key)
    fuel_key, alpha_key = pkg_obj.get_object_attributes(['fuel_key', 'alpha_key'])
    ftp1_co2, ftp2_co2, ftp3_co2, hwy_co2, combined_co2 = alpha_file_dict[key]['EPA_FTP_1 gCO2/mi'], \
                                                          alpha_file_dict[key]['EPA_FTP_2 gCO2/mi'], \
                                                          alpha_file_dict[key]['EPA_FTP_3 gCO2/mi'], \
                                                          alpha_file_dict[key]['EPA_HWFET gCO2/mi'], \
                                                          alpha_file_dict[key]['Combined GHG gCO2/mi']
    engine_cost = pkg_obj.engine_cost(settings.engine_cost_dict, settings.startstop_cost_dict, settings.boost_multiplier)
    trans_cost = pkg_obj.calc_trans_cost(settings.trans_cost_dict)
    accessories_cost = pkg_obj.calc_accessory_cost(settings.accessories_cost_dict)
    ac_cost = pkg_obj.calc_ac_cost(settings.ac_cost_dict)
    powertrain_cost = engine_cost + trans_cost + accessories_cost + ac_cost
    powertrain_cost_df = pd.DataFrame(powertrain_cost, columns=['ice_powertrain'], index=[key])

    aero_cost = pkg_obj.calc_aero_cost(settings.aero_cost_dict)
    nonaero_cost = pkg_obj.calc_nonaero_cost(settings.nonaero_cost_dict)
    roadload_cost = aero_cost + nonaero_cost
    roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[key])

    weight_cost = pkg_obj.calc_weight_cost(settings.weight_cost_dict, settings.price_class_dict)
    body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[key])

    package_cost_df = powertrain_cost_df.join(roadload_cost_df).join(body_cost_df)
    # package_cost_df.insert(0, 'cert_kWh_per_mile', 0)
    package_cost_df.insert(0, 'cert_co2_grams_per_mile', combined_co2)
    package_cost_df.insert(0, 'hwfet:co2_grams_per_mile', hwy_co2)
    package_cost_df.insert(0, 'ftp_3:co2_grams_per_mile', ftp3_co2)
    package_cost_df.insert(0, 'ftp_2:co2_grams_per_mile', ftp2_co2)
    package_cost_df.insert(0, 'ftp_1:co2_grams_per_mile', ftp1_co2)
    package_cost_df.insert(0, 'cost_curve_class', f'{fuel_key}_{alpha_key}')

    return package_cost_df


def pev_package_results(settings, key, alpha_file_dict):
    print(key)
    pkg_obj = PackageCost(key)
    unique_key, fuel_id, structure_class, price_class_id, alpha_key, engine_key, pev_key, trans_key, accessory_key, aero_key, nonaero_key, weight_key = key
    onroad_range, oncycle_kwh_per_mile, usable_soc, gap, battery_kwh_gross, motor_power = pev_key
    fuel_key, alpha_key = pkg_obj.get_object_attributes(['fuel_key', 'alpha_key'])
    ftp1_kwh, ftp2_kwh, ftp3_kwh, hwy_kwh, combined_kwh = alpha_file_dict[key]['EPA_FTP_1_kWhr/100mi'] / 100,\
                                                          alpha_file_dict[key]['EPA_FTP_2_kWhr/100mi'] / 100,\
                                                          alpha_file_dict[key]['EPA_FTP_3_kWhr/100mi'] / 100,\
                                                          alpha_file_dict[key]['EPA_HWFET_kWhr/100mi'] / 100,\
                                                          oncycle_kwh_per_mile
    ac_cost = pkg_obj.calc_ac_cost(settings.ac_cost_dict)
    battery_cost, motor_cost, pev_cost = pkg_obj.calc_bev_cost(settings.pev_curves_dict)
    powertrain_cost = pev_cost + ac_cost
    powertrain_cost_df = pd.DataFrame({'pev_battery': battery_cost, 'pev_motor': motor_cost, 'pev_powertrain': powertrain_cost}, index=[key])
    aero_cost = pkg_obj.calc_aero_cost(settings.aero_cost_dict)
    nonaero_cost = pkg_obj.calc_nonaero_cost(settings.nonaero_cost_dict)
    roadload_cost = aero_cost + nonaero_cost
    roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[key])

    weight_cost = pkg_obj.calc_weight_cost(settings.weight_cost_dict, settings.price_class_dict)
    body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[key])
    
    package_cost_df = powertrain_cost_df.join(roadload_cost_df).join(body_cost_df)
    package_cost_df.insert(0, 'cert_kWh_per_mile', combined_kwh)
    package_cost_df.insert(0, 'hwfet:kWh_per_mile', hwy_kwh)
    package_cost_df.insert(0, 'ftp_3:kWh_per_mile', ftp3_kwh)
    package_cost_df.insert(0, 'ftp_2:kWh_per_mile', ftp2_kwh)
    package_cost_df.insert(0, 'ftp_1:kWh_per_mile', ftp1_kwh)
    # package_cost_df.insert(0, 'cert_co2_grams_per_mile', 0)
    package_cost_df.insert(0, 'cost_curve_class', f'{fuel_key}_{alpha_key}')
    
    return package_cost_df


class SetInputs:
    path_cwd = Path.cwd()
    path_preproc = path_cwd / 'usepa_omega2_preproc'
    path_here = path_preproc / 'alpha_package_costs'
    path_outputs = path_here / 'outputs'
    path_alpha_inputs = path_here / 'ALPHA'
    # path_input_templates = path_cwd / 'usepa_omega2/test_inputs'

    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

    # set what to run (i.e., what outputs to generate)
    run_ice = True
    run_bev = True
    run_phev = False

    # get the price deflators
    gdp_deflators = pd.read_csv(path_preproc / 'bea_tables/implicit_price_deflators.csv', skiprows=1, index_col=0)
    dollar_basis = dollar_basis_year(gdp_deflators)
    gdp_deflators = gdp_deflators.to_dict('index')

    # read tech costs input file, convert dollar values to dollar basis, and create dictionaries
    techcosts_file = pd.ExcelFile(path_here / 'alpha_package_costs_module_inputs.xlsx')
    price_class_dict = pd.read_excel(techcosts_file, 'price_class', index_col=0).to_dict('index')
    engine_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'engine', 'item_cost', 'dmc').to_dict('index')
    trans_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'trans', 'item_cost', 'dmc', 'dmc_increment').to_dict('index')
    accessories_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'accessories', 'item_cost', 'dmc').to_dict('index')
    startstop_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'start-stop', 'item_cost', 'dmc').to_dict('index')
    weight_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'weight', 'item_cost', 'dmc_per_pound').to_dict('index')
    aero_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'aero', 'item_cost', 'dmc').to_dict('index')
    nonaero_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'nonaero', 'item_cost', 'dmc').to_dict('index')
    ac_cost_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'ac', 'item_cost', 'dmc').to_dict('index')
    pev_curves_dict = create_df_and_convert_dollars(gdp_deflators, dollar_basis, techcosts_file, 'pev_curves', 'dollars_per_kWh_curve', 'dollars_per_kW_curve').to_dict('index')
    bev_metrics_dict = pd.read_excel(techcosts_file, sheet_name='bev_metrics', index_col=0).to_dict('index')

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

    ice_glider_share = 0.85

    # for now, set a BEV range and motor power here
    onroad_bev_range_miles = 350
    bev_motor_power = 150
    bev_weight_reduction = 20
    bev_usable_soc = bev_metrics_dict['usable_soc']['value']
    bev_charging_loss = bev_metrics_dict['charging_loss']['value']
    bev_gap = bev_metrics_dict['gap']['value']

    # set constants
    lbs_per_kg = 2.2


def main():

    settings = SetInputs()

    alpha_folders = [folder for folder in settings.path_alpha_inputs.iterdir()]
    alpha_files = dict()
    ice_packages_df = pd.DataFrame()
    bev_packages_df = pd.DataFrame()
    for idx, folder in enumerate(alpha_folders):
        alpha_files[idx] = [file for file in alpha_folders[idx].iterdir() if file.name.__contains__('.csv')]

        for alpha_file in alpha_files[idx]:
            alpha_file_df = pd.read_csv(alpha_file, skiprows=range(1, 2))
            alpha_file_df = clean_alpha_data(alpha_file_df, 'Aero Improvement %', 'Crr Improvement %', 'Weight Reduction %')
            
            if folder.name.__contains__('BEV') and settings.run_bev:
                fuel_id = 'bev'
                # package_keys = bev_key(settings.bev_metrics_dict, settings.pev_curves_dict, fuel_id)
                alpha_file_df = add_elements_for_package_key(alpha_file_df)
                package_keys, alpha_file_dict = package_key(settings, alpha_file_df, fuel_id)
                for pkg_key in package_keys:
                    package_result = pev_package_results(settings, pkg_key, alpha_file_dict)
                    bev_packages_df = pd.concat([bev_packages_df, package_result], axis=0, ignore_index=False)
                
            elif folder.name.__contains__('PHEV') and settings.run_phev:
                fuel_id = 'phev'
            
            elif settings.run_ice:
                fuel_id = 'ice'
                alpha_file_df = add_elements_for_package_key(alpha_file_df)
                package_keys, alpha_file_dict = package_key(settings, alpha_file_df, fuel_id)
                for pkg_key in package_keys:
                    package_result = ice_package_results(settings, pkg_key, alpha_file_dict)
                    ice_packages_df = pd.concat([ice_packages_df, package_result], axis=0, ignore_index=False)

    # calculate YoY bev costs with learning
    if settings.run_bev:
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_battery', settings.years, settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_motor', settings.years, settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'pev_powertrain', settings.years, settings.learning_rate_bev)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'roadload', settings.years, settings.learning_rate_roadload)
        bev_packages_df = calc_year_over_year_costs(bev_packages_df, 'body', settings.years, settings.learning_rate_weight)
        bev_packages_df.reset_index(drop=False, inplace=True)
        bev_packages_df.rename(columns={'index': 'package'}, inplace=True)
        bev_packages_df = sum_vehicle_parts(bev_packages_df, settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'pev_powertrain', 'roadload', 'body')

    # calculate YoY ice costs with learning
    if settings.run_ice:
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'ice_powertrain', settings.years, settings.learning_rate_ice_powertrain)
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'roadload', settings.years, settings.learning_rate_roadload)
        ice_packages_df = calc_year_over_year_costs(ice_packages_df, 'body', settings.years, settings.learning_rate_weight)
        ice_packages_df.reset_index(drop=False, inplace=True)
        ice_packages_df.rename(columns={'index': 'package'}, inplace=True)
        ice_packages_df = sum_vehicle_parts(ice_packages_df, settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'roadload', 'body')

    settings.path_outputs.mkdir(exist_ok=True)
    settings.path_of_run_folder = settings.path_outputs / f'{settings.start_time_readable}_O2-TechCosts'
    settings.path_of_run_folder.mkdir(exist_ok=False)
    bev_packages_df.to_csv(settings.path_of_run_folder / 'detailed_costs_bev.csv', index=False)
    ice_packages_df.to_csv(settings.path_of_run_folder / 'detailed_costs_ice.csv', index=False)

    if settings.run_ice and settings.run_bev:
        cost_cloud = reshape_df_for_cloud_file(settings, ice_packages_df)
        cost_cloud = pd.concat([cost_cloud, reshape_df_for_cloud_file(settings, bev_packages_df)], axis=0, ignore_index=True)

    if settings.run_bev and not settings.run_ice:
        cost_cloud = reshape_df_for_cloud_file(settings, bev_packages_df)

    cost_cloud.fillna(0, inplace=True)
    cost_cloud.to_csv(settings.path_of_run_folder / 'cost_clouds.csv', index=False)

    cost_vs_plot(cost_cloud, settings.path_of_run_folder, settings.start_time_readable, 2020, 2030, 2040)
    # cost_vs_plot_combined(cost_cloud, path_of_run_folder, start_time_readable, 2020, 2030, 2040)

    # save additional outputs
    modified_costs = pd.ExcelWriter(settings.path_of_run_folder.joinpath(f'techcosts_in_{settings.dollar_basis}_dollars.xlsx'))
    pd.DataFrame(settings.engine_cost_dict).transpose().to_excel(modified_costs, sheet_name='engine', index=True)
    pd.DataFrame(settings.trans_cost_dict).transpose().to_excel(modified_costs, sheet_name='trans', index=True)
    pd.DataFrame(settings.startstop_cost_dict).transpose().to_excel(modified_costs, sheet_name='start-stop', index=False)
    pd.DataFrame(settings.accessories_cost_dict).transpose().to_excel(modified_costs, sheet_name='accessories', index=True)
    pd.DataFrame(settings.aero_cost_dict).transpose().to_excel(modified_costs, sheet_name='aero', index=False)
    pd.DataFrame(settings.nonaero_cost_dict).transpose().to_excel(modified_costs, sheet_name='nonaero', index=False)
    pd.DataFrame(settings.weight_cost_dict).transpose().to_excel(modified_costs, sheet_name='weight', index=True)
    pd.DataFrame(settings.ac_cost_dict).transpose().to_excel(modified_costs, sheet_name='ac', index=True)
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
