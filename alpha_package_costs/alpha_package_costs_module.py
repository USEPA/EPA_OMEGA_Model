import pandas as pd
import numpy as np
from pathlib import Path, PurePath
from datetime import datetime
from itertools import product
import shutil
import matplotlib.pyplot as plt
from usepa_omega2.drive_cycle_energy_calcs import SAEJ2951_target_inertia_and_roadload_weight_combined_calcs
from usepa_omega2 import *


class CreatePackageDictTuple:
    """
    Create a dictionary of DataFrames where the dictionary keys are a tuple providing (alpha class, engine configuration, percentage weight reduction ,
    aero improvements, non-aero drag improvements, work class)
    """
    def __init__(self, alpha_file):
        self.alpha_file = alpha_file

    def effectiveness_class(self):
        effectiveness_classes = pd.Series(self.alpha_file['Vehicle Type']).unique()
        return effectiveness_classes[0]

    def engine_architecture(self):
        engine_architectures = pd.Series(self.alpha_file['engine_architecture']).unique()
        return engine_architectures

    def percent_weight_reduction(self):
        percent_weight_reductions = pd.Series(self.alpha_file['weight_reduction']).unique()
        return percent_weight_reductions

    def aero_improvement(self):
        aero_improvements = pd.Series(self.alpha_file['aero']).unique()
        return aero_improvements

    def nonaero_improvement(self):
        nonaero_improvements = pd.Series(self.alpha_file['nonaero']).unique()
        return nonaero_improvements

    def work_class_identifier(self):
        temp = CreatePackageDictTuple(self.alpha_file).effectiveness_class()
        if temp == 'Truck':
            work_class = 'haul'
        else:
            work_class = 'nohaul'
        return work_class


class CalcCosts:
    """
    This class largely merges input costs into the working DataFrames (the passed objects) on the appropriate metrics, although the weight_cost method calculates
    actual weight costs and merges those into the working DataFrames.
    """
    def __init__(self, df):
        self.df = df

    def trans_cost(self, techcosts_trans):
        self.df = self.df.merge(techcosts_trans[['trans', 'trans_cost']], on='trans', how='left')
        return self.df

    def accessory_cost(self, techcosts_accessories):
        self.df = self.df.merge(techcosts_accessories[['Accessory', 'accessory_cost']], on='Accessory')
        return self.df

    def startstop_cost(self, techcosts_startstop):
        # self.df.insert(len(self.df.columns), 'start-stop_cost', 0)
        for index, row in techcosts_startstop.iterrows():
            curb_weight_min = row['curb_weight_min']
            curb_weight_max = row['curb_weight_max']
            startstop_cost = row['start-stop_cost']
            self.df.loc[(self.df['Test Weight lbs'] - 300 > curb_weight_min)
                        & (self.df['Test Weight lbs'] - 300 <= curb_weight_max)
                        & (self.df['Start Stop'] == 1), 'start-stop_cost'] = startstop_cost
        self.df.loc[self.df['Start Stop'] == 0, 'start-stop_cost'] = 0
        return self.df

    def deac_cost(self, techcosts_deac):
        # self.df.insert(len(self.df.columns), 'deac_cost', 0)
        cylinders_present = pd.Series(self.df['Engine Cylinders']).unique()
        self.df['DEAC D Cyl.'].fillna(0, inplace=True)
        self.df['DEAC C Cyl.'].fillna(0, inplace=True)
        for cylinders in cylinders_present:
            self.df.loc[(self.df['DEAC D Cyl.'] > 0) & (self.df['Engine Cylinders'] == cylinders), 'deac_cost'] = techcosts_deac.at[cylinders, 'deac_cost']
            self.df.loc[(self.df['DEAC C Cyl.'] > 0) & (self.df['Engine Cylinders'] == cylinders), 'deac_cost'] = techcosts_deac.at[cylinders, 'deac_cost']
        self.df['deac_cost'].fillna(0, inplace=True)
        return self.df

    def aero_cost(self, techcosts_aero, work_class):
        if work_class == 'haul':
            self.df = self.df.merge(techcosts_aero.loc[techcosts_aero['work_class'] == 'haul', ['aero', 'aero_cost']], on='aero', how='left')
        else:
            self.df = self.df.merge(techcosts_aero.loc[techcosts_aero['work_class'] == 'nohaul', ['aero', 'aero_cost']], on='aero', how='left')
        return self.df

    def nonaero_cost(self, techcosts_nonaero):
        self.df = self.df.merge(techcosts_nonaero[['nonaero', 'nonaero_cost']], on='nonaero', how='left')
        return self.df

    def air_conditioning_cost(self, techcosts_ac, work_class):
        df = techcosts_ac.copy()
        df.set_index('work_class', inplace=True)
        ac_cost = df.at[work_class, 'ac_cost']
        self.df.insert(len(self.df.columns), 'ac_cost', ac_cost)
        return self.df

    def weight_cost(self, start_year, techcosts_weight, work_class):
        """
        Weight costs are calculated as an absolute cost associated with the curb weight of the vehicle and are then adjusted according to the weight reduction.
        :param start_year: First year to calc costs.
        :param techcosts_weight: The input DataFrame associated with weight costs.
        :param work_class: Hauling vs Non-hauling work class designation.
        :return: The passed DataFrame with weight costs merged in.
        """
        year = start_year
        base_weight_cost = techcosts_weight.at[work_class, 'cost_per_pound']
        dmc_ln_coeff = techcosts_weight.at[work_class, 'DMC_ln_coefficient']
        dmc_constant = techcosts_weight.at[work_class, 'DMC_constant']
        ic_slope = techcosts_weight.at[work_class, 'IC_slope']
        self.df.loc[self.df['weight_reduction'] == 0, f'weight_cost_{year}'] = (self.df['Test Weight lbs'] - 300) * base_weight_cost
        self.df.loc[self.df['weight_reduction'] != 0, f'weight_cost_{year}'] = ((self.df['Test Weight lbs'] - 300) / (1 - self.df['weight_reduction'] / 100)) * base_weight_cost \
                                                                               + ((dmc_ln_coeff * np.log(self.df['weight_reduction'] / 100) + dmc_constant)
                                                                                  * ((self.df['Test Weight lbs'] - 300) / (1- self.df['weight_reduction'] / 100)) * (self.df['weight_reduction'] / 100)) \
                                                                               + (ic_slope * (self.df['weight_reduction'] / 100)) * ((self.df['Test Weight lbs'] - 300) / (1 - self.df['weight_reduction'] / 100)) \
                                                                               * (self.df['weight_reduction'] / 100)
        return self.df

    def powertrain_cost(self, start_year):
        """
        A summation of powertrain elements into a powertrain cost in start_year (year-over-year costs are calculated in the year_over_year_cost method.
        :param start_year: The first year to calc costs.
        :return:
        """
        self.df[f'powertrain_cost_{start_year}'] = \
            self.df[['engine_cost', 'trans_cost', 'deac_cost', 'accessory_cost', 'start-stop_cost', 'ac_cost']].sum(axis=1)
        return self.df

    def roadload_cost(self, start_year):
        """
        A summation of roadload elements into a roadload cost in start_year (year-over-year costs are calculated in the year_over_year_cost method.
        :param start_year:
        :return:
        """
        self.df[f'roadload_cost_{start_year}'] = self.df[['aero_cost', 'nonaero_cost']].sum(axis=1)
        return self.df

    def vehicle_cost(self, years):
        for year in years:
            self.df[f'new_vehicle_mfr_cost_dollars_{year}'] = \
                self.df[[f'powertrain_cost_{year}', f'roadload_cost_{year}', f'weight_cost_{year}']].sum(axis=1)
        return self.df

    def year_over_year_cost(self, start_year, years, learning_factor, *args):
        """
        Applying learning effects to calculate year-over-year costs from start_year.
        :param start_year: The first year to calc costs.
        :param years: The years for which to calc costs.
        :param args: The metrics for which to calc year-over-year costs.
        :param learning_factor: The learning rate factors entered in the inputs sheet.
        :return: The passed DataFrame with year-over-yar costs for each metric passed.
        """
        for year in years:
            for arg in args:
                self.df[f'{arg}_{year}'] = self.df[f'{arg}_{start_year}'] * (1 - learning_factor) ** (year - start_year)
        return self.df

    def convert_dollars_to_analysis_basis(self, deflators, dollar_basis, *args):
        dollar_years = pd.Series(self.df['dollar_basis']).unique()
        for year in dollar_years:
            for arg in args:
                self.df.loc[self.df['dollar_basis'] == year, arg] = self.df[arg] * deflators[year]['adjustment_factor']
        self.df['dollar_basis'] = dollar_basis
        return self.df


class Targets:
    def __init__(self, reg_class, fp, coefficients, upstream, standards):
        """

        :param reg_class: Regulatory class (e.g., car/truck)
        :param fp: Footprint (in square feet)
        :param coefficients: A dictionary of targets.
        :param upstream: CO2/gallon at the refinery and for test fuel.
        """
        self.reg_class = reg_class
        self.fp = fp
        self.coefficients = coefficients
        self.upstream = upstream
        self.standards = standards

    def get_targets_dict(self):
        """

        :return: A dictionary of targets or target coefficients for the given reg_class.
        """
        regclass_targets_df = self.coefficients.loc[self.coefficients['reg_class_id'] == self.reg_class, :]
        regclass_targets_dict = regclass_targets_df.to_dict('index')
        return regclass_targets_dict

    def calc_targets(self, years):
        """

        :param years: Model/Calendar years (these are interchangeable for new vehicle sales).
        :return: A dictionary of targets and upstream emissions for the given regclass/footprint/upstream for all years.
        """
        if self.standards != 'flat':
            return_dict = dict()
            for year in years:
                if self.fp <= self.get_targets_dict()[year]['fp_min']:
                    return_dict[year] = {'CO2_target': self.get_targets_dict()[year]['a_coeff']}
                elif self.fp > self.get_targets_dict()[year]['fp_max']:
                    return_dict[year] = {'CO2_target': self.get_targets_dict()[year]['b_coeff']}
                else:
                    return_dict[year] = {'CO2_target': self.get_targets_dict()[year]['c_coeff'] * self.fp + self.get_targets_dict()[year]['d_coeff']}
                return_dict[year].update({'CO2_refinery': return_dict[year]['CO2_target']
                                                          * self.upstream[year]['CO2pGal_Refinery'] / self.upstream[year]['CO2pGal_TestFuel']})
        else:
            return_dict = dict()
            for year in years:
                return_dict[year] = {'CO2_target': self.get_targets_dict()[year]['ghg_target_co2_grams_per_mile']}
                return_dict[year].update({'CO2_refinery': return_dict[year]['CO2_target']
                                                          * self.upstream[year]['CO2pGal_Refinery'] / self.upstream[year]['CO2pGal_TestFuel']})
        return return_dict


def calc_bev_co2(df, years, targets_dict, upstream):
    """

    :param df: The passed DataFrame for a given BEV.
    :param years: Model/Calendar years (these are interchangeable for new vehicle sales).
    :param targets_dict: A dictionary of targets and upstream emissions to be attributed to the given BEV at each target level.
    :param upstream: The grid loss factor and upstream emissions per unit of electricity.
    :return:
    """
    for year in years:
        df.insert(len(df.columns), f'cert_co2_grams_per_mile_{year}', 0)
        df[f'cert_co2_grams_per_mile_{year}'] = df['kWhpMi_cycle'] \
                                                * upstream[year]['GHGpkWh'] / (1 - upstream[year]['grid_loss']) \
                                                - targets_dict[year]['CO2_refinery']
    return df


def get_energy_consumption_metrics(file, file_num, folder_num):
    a_coeff = pd.Series(file[['RL A lbf', 'RL_ADJ A lbf']].sum(axis=1))
    b_coeff = pd.Series(file[['RL B lbf/mph', 'RL_ADJ B lbf/mph']].sum(axis=1))
    c_coeff = pd.Series(file[['RL C lbf/mph2', 'RL_ADJ C lbf/mph2']].sum(axis=1))
    etw = pd.Series(file['Test Weight lbs'])
    inertial_work = []
    roadload_work = []
    for index_location in range(0, len(a_coeff)):
        print(f'Row {index_location} of {len(a_coeff)} rows in ALPHA file {file_num} of folder {folder_num}')
        new_energy_consumption_metrics = SAEJ2951_target_inertia_and_roadload_weight_combined_calcs(a_coeff[index_location], b_coeff[index_location], c_coeff[index_location], etw[index_location])
        inertial_work.append(new_energy_consumption_metrics.get('Inertial_Work_J/m'))
        roadload_work.append(new_energy_consumption_metrics.get('Net_RoadLoad_Work_J/m'))
    file['Inertial_Work_J/m'] = inertial_work
    file['Net_RoadLoad_Work_J/m'] = roadload_work
    return file


def reshape_ice_df_for_cloud_file(df_source, effectiveness_class, years):
    df_source.rename(columns={'Combined GHG gCO2/mi': 'cert_co2_grams_per_mile'}, inplace=True)
    df_return = pd.DataFrame()
    for year in years:
        temp = pd.melt(df_source[['cert_co2_grams_per_mile', f'new_vehicle_mfr_cost_dollars_{year}']], id_vars='cert_co2_grams_per_mile', value_vars=f'new_vehicle_mfr_cost_dollars_{year}', value_name='new_vehicle_mfr_cost_dollars')
        temp.insert(0, 'model_year', year)
        temp.drop(columns='variable', inplace=True)
        df_return = pd.concat([df_return, temp], ignore_index=True, axis=0)
    df_return.insert(0, 'cost_curve_class', f'ice_{effectiveness_class}')
    return df_return


def reshape_bev_df_for_cloud_file(df_source, bev_key, years):
    df_return = pd.DataFrame()
    for year in years:
        temp = pd.melt(df_source[[f'cert_co2_grams_per_mile_{year}']], value_vars=f'cert_co2_grams_per_mile_{year}', value_name='cert_co2_grams_per_mile')
        temp.drop(columns='variable', inplace=True)
        temp = temp.join(pd.melt(df_source[[f'new_vehicle_mfr_cost_dollars_{year}']], value_vars=f'new_vehicle_mfr_cost_dollars_{year}', value_name='new_vehicle_mfr_cost_dollars'))
        temp.drop(columns='variable', inplace=True)
        # melt in the kWhpMi data, which doesn't change by year but melting here for ease
        temp = temp.join(pd.melt(df_source[['kWhpMi_cycle']], value_vars='kWhpMi_cycle', value_name='kWh_per_mile_cycle'))
        temp.drop(columns='variable', inplace=True)
        temp.insert(0, 'model_year', year)
        df_return = pd.concat([df_return, temp], ignore_index=True, axis=0)
    df_return.insert(0, 'cost_curve_class', f'{bev_key}')
    return df_return


def dollar_basis_year(df):
    for i in range(len(df)):
        if df.iloc[i]['adjustment_factor'] == 1:
            dollar_year = df.index[i]
    return dollar_year


def cost_vs_co2_plot(df, path, *years):
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
            bev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_co2_grams_per_mile'],
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
            plt.savefig(path / f'ice_{year}.png')

        # create bev plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for bev_plot, bev_legends in zip(bev_plot, bev_legends):
            x, y = bev_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=bev_legends)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            plt.legend(loc=4)
            plt.title(f'bev_{year}')
            plt.savefig(path / f'bev_{year}.png')


def cost_vs_co2_plot_combined(df, path, *years):
    classes = [x for x in df['cost_curve_class'].unique()]
    for year in years:
        class_data = dict()
        class_plot = list()
        class_legends = list()
        for cost_curve_class in classes:
            class_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cert_co2_grams_per_mile'],
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
            plt.savefig(path / f'{year}.png')


def main():
    path_cwd = Path.cwd()
    path_inputs = path_cwd / 'alpha_package_costs/alpha_package_costs_inputs'
    # path_alpha_inputs = Path('I:\Project\OMEGA2\O2_package_cost_test\ALPHA_ToyModel')
    path_alpha_inputs = path_cwd / 'inputs/ALPHA'
    path_input_templates = path_cwd / 'input_samples'
    path_outputs = path_cwd / 'alpha_package_costs/outputs'
    bev_wr_range = [x / 2 for x in range(0, 41, 1)]

    alpha_folders = [folder for folder in path_alpha_inputs.iterdir()]
    metrics = ['Configuration',
               'Vehicle Type',
               'Package',
               'Network Path',
               'Filename',
               'Key',
               'Unique Key',
               'Test Weight lbs',
               'RL A lbf',
               'RL B lbf/mph',
               'RL C lbf/mph2',
               'RL_ADJ A lbf',
               'RL_ADJ B lbf/mph',
               'RL_ADJ C lbf/mph2',
               'RL hp @ 50 mph',
               'Perf Baseline',
               'Perf Neutral',
               'Shift Norm',
               'Transient Penalty',
               'Weight Reduction %',
               'Aero Improvement %',
               'Crr Improvement %',
               'Start Stop',
               'Var Val',
               'DEAC D Cyl.',
               'DEAC C Cyl.',
               'DEAC Time',
               'Electric',
               'Accessory',
               'Transmission',
               'Transmission Vintage',
               'Engine',
               'Engine.1',
               'Engine Displacement L',
               'Engine Cylinders',
               'Engine Max Power kW',
               'Combined GHG gCO2/mi',
               'Combined Target Total Efficiency %',
               'Inertial_Work_J/m',
               'Net_RoadLoad_Work_J/m',
               ]

    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    techcosts_file = pd.ExcelFile(path_inputs.joinpath('alpha_package_costs_module_inputs.xlsx'))
    techcosts_engine = pd.read_excel(techcosts_file, 'engine')
    techcosts_deac = pd.read_excel(techcosts_file, 'deac', index_col='Cylinders')
    techcosts_trans = pd.read_excel(techcosts_file, 'trans')
    techcosts_accessories = pd.read_excel(techcosts_file, 'accessories')
    techcosts_startstop = pd.read_excel(techcosts_file, 'start-stop')
    techcosts_weight = pd.read_excel(techcosts_file, 'weight', index_col=0)
    techcosts_aero = pd.read_excel(techcosts_file, 'aero')
    techcosts_nonaero = pd.read_excel(techcosts_file, 'nonaero')
    techcosts_ac = pd.read_excel(techcosts_file, 'ac')
    techcosts_bev = pd.read_excel(techcosts_file, 'bev', index_col=0)
    upstream = pd.read_excel(techcosts_file, 'upstream', index_col=0)
    upstream = upstream.to_dict('index')

    # get the price deflators
    gdp_deflators = pd.read_csv(path_input_templates / 'context_implicit_price_deflators.csv', skiprows=1, index_col=0)
    # gdp_deflators = gdp_deflators.iloc[:, :-1]
    dollar_basis = dollar_basis_year(gdp_deflators)
    gdp_deflators = gdp_deflators.to_dict('index')

    # set inputs
    inputs = pd.read_excel(techcosts_file, 'inputs_code', index_col=0)
    inputs = inputs.to_dict('index')
    start_year = int(inputs['start_year']['value'])
    end_year = int(inputs['end_year']['value'])
    years = range(start_year, end_year + 1)
    learning_rate_weight = inputs['learning_rate_weight']['value']
    learning_rate_powertrain = inputs['learning_rate_powertrain']['value']
    learning_rate_roadload = inputs['learning_rate_roadload']['value']
    learning_rate_bev = inputs['learning_rate_bev']['value']

    ghg_standards = inputs['ghg_standards']['value']

    coefficients = pd.read_csv(path_input_templates / f'ghg_standards-{ghg_standards}.csv', skiprows=1, index_col='model_year')

    techcosts_engine.insert(0, 'ALPHA_engine, Cylinders', list(zip(techcosts_engine['ALPHA_engine'], techcosts_engine['actual_cylinders'])))

    # convert all dollars in to consistent, analysis dollars
    techcosts_engine = CalcCosts(techcosts_engine).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'engine_cost')
    techcosts_deac = CalcCosts(techcosts_deac).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'deac_cost')
    techcosts_trans = CalcCosts(techcosts_trans).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'trans_cost')
    techcosts_accessories = CalcCosts(techcosts_accessories).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'accessory_cost')
    techcosts_startstop = CalcCosts(techcosts_startstop).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'start-stop_cost')
    techcosts_weight = CalcCosts(techcosts_weight).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'cost_per_pound', 'DMC_ln_coefficient', 'DMC_constant', 'IC_slope')
    techcosts_aero = CalcCosts(techcosts_aero).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'aero_cost')
    techcosts_nonaero = CalcCosts(techcosts_nonaero).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'nonaero_cost')
    techcosts_ac = CalcCosts(techcosts_ac).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'ac_cost')
    techcosts_bev = CalcCosts(techcosts_bev).convert_dollars_to_analysis_basis(gdp_deflators, dollar_basis, 'bev_cost_slope', 'bev_cost_intercept', 'dollar/kWh_0WR', 'dollar/kWh_20WR')
    techcosts_bev = techcosts_bev.to_dict('index')

    alpha_files = dict()
    for folder_num in range(0, len(alpha_folders)):
        alpha_files[folder_num] = [file for file in alpha_folders[folder_num].iterdir() if file.name.__contains__('.csv')]

    # this loop vertically concatenates 2016 and future files for each ALPHA class into a single ALPHA file containing both 2016 and future results
    alpha_file = dict()
    for file_num in range(0, len(alpha_files[0])):
        alpha_file[file_num] = pd.DataFrame()
        for folder_num in range(0, len(alpha_folders)):
            alpha_file_temp = pd.read_csv(alpha_files[folder_num][file_num], skiprows=range(1, 2))
            # check for necessary energy consumptions in ALPHA files - if there, pass; if not then calculate, add to file and save (overwrite) file to same path
            if 'Inertial_Work_J/m' in alpha_file_temp.columns.tolist():
                pass
            else:
                print(f'Getting energy consumption metrics for ALPHA file {file_num} of {len(alpha_files[0])} in folder {folder_num} of {len(alpha_folders)}')
                alpha_file_temp.insert(len(alpha_file_temp.columns), 'Inertial_Work_J/m', 0)
                alpha_file_temp.insert(len(alpha_file_temp.columns), 'Net_RoadLoad_Work_J/m', 0)
                alpha_file_temp = get_energy_consumption_metrics(alpha_file_temp, file_num, folder_num)
                alpha_file_temp.to_csv(alpha_files[folder_num][file_num], index=False)
            alpha_file_temp = alpha_file_temp[metrics]
            alpha_file_temp = alpha_file_temp.loc[:, ~alpha_file_temp.columns.duplicated()]
            alpha_file_temp['Engine Cylinders'] = alpha_file_temp['Engine Cylinders'].astype(int)
            # split costing trans code from ALPHA trans code
            temp = alpha_file_temp[['Transmission']]
            temp = temp.join(temp['Transmission'].str.split('_', expand=True))
            temp.rename(columns={0: 'trans'}, inplace=True)
            alpha_file_temp = alpha_file_temp.join(temp[['trans']])
            # split aero string and convert to numeric
            temp = alpha_file_temp[['Aero Improvement %']]
            temp = temp.join(temp['Aero Improvement %'].str.split('.', expand=True))
            temp.rename(columns={0: 'aero'}, inplace=True)
            temp['aero'] = pd.to_numeric(temp['aero'])
            alpha_file_temp = alpha_file_temp.join(temp[['aero']])
            # split nonaero string and convert to numeric
            temp = alpha_file_temp[['Crr Improvement %']]
            temp = temp.join(temp['Crr Improvement %'].str.split('.', expand=True))
            temp.rename(columns={0: 'nonaero'}, inplace=True)
            temp['nonaero'] = pd.to_numeric(temp['nonaero'])
            alpha_file_temp = alpha_file_temp.join(temp[['nonaero']])
            # split weight reduction string and convert to numeric
            temp = alpha_file_temp[['Weight Reduction %']]
            temp = temp.join(temp['Weight Reduction %'].str.split('.', expand=True))
            temp.rename(columns={0: 'weight_reduction'}, inplace=True)
            temp['weight_reduction'] = pd.to_numeric(temp['weight_reduction'])
            alpha_file_temp = alpha_file_temp.join(temp[['weight_reduction']])
            # concat files into a single large file for the effectiveness class
            alpha_file[file_num] = pd.concat([alpha_file[file_num], alpha_file_temp], axis=0, ignore_index=True)
        # create an ALPHA_engine, #Cylinders column for merging necessary engine cost metrics into file
        alpha_file[file_num].insert(len(alpha_file[file_num].columns), 'ALPHA_engine, Cylinders',
                                    list(zip(alpha_file[file_num]['Engine'], alpha_file[file_num]['Engine Cylinders'])))
        alpha_file[file_num] = alpha_file[file_num].merge(techcosts_engine[['ALPHA_engine, Cylinders', 'engine_architecture', 'engine_cost']],
                                                          on=['ALPHA_engine, Cylinders'], how='left')

    # this loop breaks each ALPHA file into package dictionaries identified by the identifying tuple
    # the inner loop then uses the CalcCosts class to calculate package costs
    package_dict = dict()
    effectiveness_class_dict = dict()
    for file_num in range(0, len(alpha_files[0])):
        tuple_object = CreatePackageDictTuple(alpha_file[file_num])
        effectiveness_class = tuple_object.effectiveness_class()
        print(f'Working on {effectiveness_class}')
        effectiveness_class_dict[effectiveness_class] = pd.DataFrame()
        engine_architectures = tuple_object.engine_architecture()
        percent_weight_reductions = tuple_object.percent_weight_reduction()
        aero_improvements = tuple_object.aero_improvement()
        nonaero_improvements = tuple_object.nonaero_improvement()
        work_class = tuple_object.work_class_identifier()
        # the following lines are useful to determine the unique engines for which costs are needed in the TechCosts input file but are not needed for a general run
        # temp = pd.Series(alpha_file['ALPHA_engine, Cylinders']).unique()
        # temp = pd.DataFrame(temp)
        # temp.to_csv(path_alpha_inputs.joinpath('file_num' + str(file_num) + '.csv'))
        for ea, pwr, ai, nai in product(engine_architectures, percent_weight_reductions, aero_improvements, nonaero_improvements):
            package_dict[effectiveness_class, ea, pwr, ai, nai, work_class] \
                = alpha_file[file_num].loc[(alpha_file[file_num]['engine_architecture'] == ea)
                                           & (alpha_file[file_num]['weight_reduction'] == pwr)
                                           & (alpha_file[file_num]['aero'] == ai)
                                           & (alpha_file[file_num]['nonaero'] == nai)]
            package_dict[effectiveness_class, ea, pwr, ai, nai, work_class].reset_index(drop=True, inplace=True)

            # insert and calculate new cost columns
            temp_df = package_dict[effectiveness_class, ea, pwr, ai, nai, work_class].copy()
            temp_df.insert(len(temp_df.columns), 'deac_cost', 0)
            cost_object = CalcCosts(temp_df)
            temp_df = cost_object.deac_cost(techcosts_deac)
            temp_df = cost_object.trans_cost(techcosts_trans)
            temp_df = cost_object.accessory_cost(techcosts_accessories)
            temp_df.insert(len(temp_df.columns), 'start-stop_cost', 0)
            temp_df = cost_object.startstop_cost(techcosts_startstop)
            temp_df = cost_object.aero_cost(techcosts_aero, work_class)
            temp_df = cost_object.nonaero_cost(techcosts_nonaero)
            temp_df = cost_object.air_conditioning_cost(techcosts_ac, work_class)
            for year in years:
                temp_df.insert(len(temp_df.columns), f'weight_cost_{year}', 0)
            for year in years:
                temp_df.insert(len(temp_df.columns), f'powertrain_cost_{year}', 0)
            for year in years:
                temp_df.insert(len(temp_df.columns), f'roadload_cost_{year}', 0)
            for year in years:
                temp_df.insert(len(temp_df.columns), f'new_vehicle_mfr_cost_dollars_{year}', 0)
            cost_object.weight_cost(start_year, techcosts_weight, work_class)
            # sum individual techs into system-level costs (powertrain, roadload)
            cost_object.powertrain_cost(start_year)
            cost_object.roadload_cost(start_year)
            # apply learning
            cost_object.year_over_year_cost(start_year, years, learning_rate_weight, 'weight_cost')
            cost_object.year_over_year_cost(start_year, years, learning_rate_powertrain, 'powertrain_cost')
            cost_object.year_over_year_cost(start_year, years, learning_rate_roadload, 'roadload_cost')
            cost_object.vehicle_cost(years)
            effectiveness_class_dict[effectiveness_class] = pd.concat([effectiveness_class_dict[effectiveness_class], temp_df], axis=0, ignore_index=True, sort=False)

    # save ALPHA-based output files
    path_outputs.mkdir(exist_ok=True)
    path_of_run_folder = path_outputs.joinpath(f'{start_time_readable}_O2-TechCosts')
    path_of_run_folder.mkdir(exist_ok=False)
    cost_clouds_df = pd.DataFrame()
    for effectiveness_class in [*effectiveness_class_dict]:
        print(f'Saving {effectiveness_class}.csv')
        effectiveness_class_dict[effectiveness_class].to_csv(path_of_run_folder.joinpath(f'ice_{effectiveness_class}.csv'), index=False)
        print(f'Adding ice_{effectiveness_class} results to cost_clouds DataFrame for inclusion in the input template.')
        reshaped_df = reshape_ice_df_for_cloud_file(effectiveness_class_dict[effectiveness_class], effectiveness_class, years)
        cost_clouds_df = pd.concat([cost_clouds_df, reshaped_df], ignore_index=True, axis=0)

    # work on BEVs
    print('Working on BEVs')
    bev_cost_co2 = dict()
    for key in techcosts_bev:
        bev = techcosts_bev[key]
        eff_class = bev['effectiveness_class']
        if eff_class == 'Truck':
            work_class = 'haul'
        else:
            work_class = 'nohaul'
        etw = bev['Test Weight lbs']
        reg_class = bev['reg_class']
        fp = bev['footprint']
        bev_range = bev['range']
        kWh_pack_slope = bev['kWh_pack_slope']
        kWh_pack_intercept = bev['kWh_pack_intercept']
        cost_slope = bev['bev_cost_slope']
        cost_intercept = bev['bev_cost_intercept']
        usuable_SOC = bev['usable_SOC']
        gap = bev['gap']
        loss_charging = bev['loss_charging']
        utility_factor = bev['utility_factor']

        print(f'Working on bev_{bev_range}_{eff_class}')
        bev_cost_co2[key] = pd.DataFrame({'effectiveness_class': eff_class,
                                          'weight_reduction': pd.Series(bev_wr_range),
                                          'Test Weight lbs': etw,
                                          'Reg_Class': reg_class,
                                          'Hauling_Class': work_class,
                                          'bev_tech': f'bev_{bev_range}'})

        # calc the pack size and energy consumption
        bev_cost_co2[key].insert(len(bev_cost_co2[key].columns),
                                 'kWh_pack',
                                 kWh_pack_slope * bev_cost_co2[key]['weight_reduction'] / 100 + kWh_pack_intercept)
        bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), 'kWhpMi_cycle', 0)
        bev_cost_co2[key]['kWhpMi_cycle'] = bev_cost_co2[key]['kWh_pack'] * usuable_SOC * (1 - gap) * utility_factor / (bev_range * (1 - loss_charging))

        # start work on costs
        cost_object = CalcCosts(bev_cost_co2[key])
        for year in years:
            bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), f'weight_cost_{year}', 0)
        for year in years:
            bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), f'bev_cost_{year}', 0)
        bev_cost_co2[key] = cost_object.weight_cost(start_year, techcosts_weight, work_class)
        bev_cost_co2[key] = cost_object.year_over_year_cost(start_year, years, learning_rate_weight, 'weight_cost')
        bev_cost_co2[key][f'bev_cost_{start_year}'] = cost_slope * bev_cost_co2[key]['weight_reduction'] / 100 + cost_intercept
        bev_cost_co2[key] = cost_object.year_over_year_cost(start_year, years, learning_rate_bev, 'bev_cost')
        for year in years:
            bev_cost_co2[key].insert(len(bev_cost_co2[key].columns),
                                     f'new_vehicle_mfr_cost_dollars_{year}',
                                     bev_cost_co2[key][[f'weight_cost_{year}', f'bev_cost_{year}']].sum(axis=1))

        # calc targets and upstream petroleum CO2 (CO2_refinery)
        targets = Targets(reg_class, fp, coefficients, upstream, ghg_standards)
        targets_dict = targets.calc_targets(years)

        calc_bev_co2(bev_cost_co2[key], years, targets_dict, upstream)
        print(f'Saving {key}')
        bev_cost_co2[key].to_csv(path_of_run_folder.joinpath(f'{key}.csv'), index=False)
        print(f'Adding bev_{eff_class} results to cost_clouds DataFrame for inclusion in the input template.')
        reshaped_df = reshape_bev_df_for_cloud_file(bev_cost_co2[key], key, years)
        # reshaped_df has an extra column - kWhpMi_cycle data - so insert that column into the cost_clouds_df if not there already
        try:
            cost_clouds_df.insert(len(cost_clouds_df.columns), 'kWh_per_mile_cycle', np.nan)
        except:
            pass
        cost_clouds_df = pd.concat([cost_clouds_df, reshaped_df], ignore_index=True, axis=0)

    # save outputs
    modified_costs = pd.ExcelWriter(path_of_run_folder.joinpath(f'techcosts_in_{dollar_basis}_dollars.xlsx'))
    techcosts_engine[['ALPHA_engine, Cylinders', 'engine_architecture', 'engine_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='engine', index=False)
    techcosts_deac[['Tech', 'deac_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='deac', index=False)
    techcosts_trans[['trans', 'trans_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='trans', index=False)
    techcosts_aero[['work_class', 'aero', 'aero_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='aero', index=False)
    techcosts_nonaero[['Tech', 'nonaero_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='nonaero', index=False)
    techcosts_accessories[['Accessory', 'accessory_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='accessories', index=False)
    techcosts_startstop[['curb_weight_min', 'curb_weight_max', 'start-stop_cost', 'dollar_basis']].to_excel(modified_costs, sheet_name='start-stop', index=False)
    techcosts_weight.to_excel(modified_costs, sheet_name='weight', index=True)
    techcosts_bev = pd.DataFrame(techcosts_bev)  # from dict to df
    techcosts_bev.to_excel(modified_costs, sheet_name='bev', index=True)
    gdp_deflators = pd.DataFrame(gdp_deflators) # from dict to df
    gdp_deflators.to_excel(modified_costs, sheet_name='gdp_deflators', index=True)
    modified_costs.save()

    # copy input files into the output folder
    input_files_list = [techcosts_file]
    filename_list = [PurePath(path).name for path in input_files_list]
    for file in filename_list:
        path_source = path_inputs.joinpath(file)
        path_destination = path_of_run_folder.joinpath(file)
        shutil.copy2(path_source, path_destination) # copy2 should maintain date/timestamps

    shutil.copy2(path_input_templates / 'cost_clouds.csv', path_of_run_folder / 'cost_clouds.csv')

    # open the 'cost_clouds.csv' input template into which results will be placed.
    cost_clouds_template_info = pd.read_csv(path_of_run_folder.joinpath('cost_clouds.csv'), 'b', nrows=0)
    temp = ' '.join((item for item in cost_clouds_template_info))
    temp2 = temp.split(',')
    df = pd.DataFrame(columns=temp2)
    df.to_csv(path_of_run_folder.joinpath('cost_clouds.csv'), index=False)

    with open(path_of_run_folder.joinpath('cost_clouds.csv'), 'a', newline='') as cloud_file:
        cost_clouds_df.to_csv(cloud_file, index=False)

    cost_vs_co2_plot(cost_clouds_df, path_of_run_folder, 2020, 2030, 2040)
    cost_vs_co2_plot_combined(cost_clouds_df, path_of_run_folder, 2020, 2030, 2040)


if __name__ == '__main__':
    import os, traceback

    try:
        main()
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
