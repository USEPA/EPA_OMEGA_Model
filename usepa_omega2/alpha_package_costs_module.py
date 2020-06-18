import pandas as pd
import numpy as np
from pathlib import Path, PurePath
from datetime import datetime
import shutil
from usepa_omega2.drive_cycle_energy_calcs import SAEJ2951_target_inertia_and_roadload_weight_combined_calcs


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
            self.df[['engine_cost', 'trans_cost', 'deac_cost', 'accessory_cost', 'start-stop_cost']].sum(axis=1)
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
            self.df[f'vehicle_cost_{year}'] = \
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
                self.df[arg + f'_{year}'] = self.df[arg + f'_{start_year}'] * (1 - learning_factor) ** (year - start_year)
        return self.df

    def convert_dollars_to_analysis_basis(self, deflators, dollar_basis, *args):
        dollar_years = pd.Series(self.df['dollar_basis']).unique()
        for year in dollar_years:
            for arg in args:
                self.df.loc[self.df['dollar_basis'] == year, arg] = self.df[arg] * deflators[year]['adjustment']
        self.df['dollar_basis'] = dollar_basis
        return self.df


class Targets:
    def __init__(self, reg_class, fp, coefficients, upstream):
        self.reg_class = reg_class
        self.fp = fp
        self.coefficients = coefficients
        self.upstream = upstream

    def calc_targets(self, years):
        return_dict = dict()
        a = f'{self.reg_class}_a'
        b = f'{self.reg_class}_b'
        c = f'{self.reg_class}_c'
        d = f'{self.reg_class}_d'
        fp_min = f'{self.reg_class}_fp_min'
        fp_max = f'{self.reg_class}_fp_max'
        for year in years:
            if self.fp <= self.coefficients[year][fp_min]:
                return_dict[year] = {'CO2_target': self.coefficients[year][fp_min]}
            elif self.fp > self.coefficients[year][fp_max]:
                return_dict[year] = {'CO2_target': self.coefficients[year][fp_max]}
            else:
                return_dict[year] = {'CO2_target': self.coefficients[year][c] * self.fp + self.coefficients[year][d]}
            return_dict[year].update({'CO2_refinery': return_dict[year]['CO2_target']
                                                      * self.upstream[year]['CO2pGal_Refinery'] / self.upstream[year]['CO2pGal_TestFuel']})
        return return_dict


def calc_bev_co2(df, years, targets_dict, upstream):
    for year in years:
        df.insert(len(df.columns), f'CO2_cycle_{year}', 0)
        df[f'CO2_cycle_{year}'] = df['kWhpMi_cycle'] \
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


def main():
    PATH_PROJECT = Path.cwd()
    PATH_INPUTS = PATH_PROJECT.joinpath('inputs')
    PATH_ALPHA_INPUTS = PATH_INPUTS.joinpath('ALPHA')
    PATH_OUTPUTS = PATH_PROJECT.joinpath('outputs')
    BEV_WR_RANGE = [x / 2 for x in range(0, 41, 1)]

    ALPHA_FOLDERS = [folder for folder in PATH_ALPHA_INPUTS.iterdir()]
    METRICS = ['Configuration',
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
               'Engine',
               'Engine Displacement L',
               'Engine Cylinders',
               'Combined GHG gCO2/mi',
               'Combined Target Total Efficiency %',
               'Inertial_Work_J/m',
               'Net_RoadLoad_Work_J/m',
               ]

    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
    techcosts_file = pd.ExcelFile(PATH_INPUTS.joinpath('alpha_package_costs_module_inputs.xlsx'))
    techcosts_engine = pd.read_excel(techcosts_file, 'engine')
    techcosts_deac = pd.read_excel(techcosts_file, 'deac', index_col='Cylinders')
    techcosts_trans = pd.read_excel(techcosts_file, 'trans')
    techcosts_accessories = pd.read_excel(techcosts_file, 'accessories')
    techcosts_startstop = pd.read_excel(techcosts_file, 'start-stop')
    techcosts_weight = pd.read_excel(techcosts_file, 'weight', index_col=0)
    techcosts_aero = pd.read_excel(techcosts_file, 'aero')
    techcosts_nonaero = pd.read_excel(techcosts_file, 'nonaero')
    techcosts_bev = pd.read_excel(techcosts_file, 'bev', index_col=0)
    upstream = pd.read_excel(techcosts_file, 'upstream', index_col=0)
    upstream = upstream.to_dict('index')
    coefficients = pd.read_excel(techcosts_file, 'coefficients', index_col=0)
    coefficients = coefficients.to_dict('index')
    gdp_deflators = pd.read_excel(techcosts_file, 'gdp_deflators', index_col=0)
    gdp_deflators.insert(len(gdp_deflators.columns), 'adjustment', 0) # adjustment values are filled below
    gdp_deflators = gdp_deflators.to_dict('index')

    # set inputs
    inputs = pd.read_excel(techcosts_file, 'inputs_code', index_col=0)
    inputs = inputs.to_dict('index')
    START_YEAR = int(inputs['start_year']['value'])
    END_YEAR = int(inputs['end_year']['value'])
    YEARS = range(START_YEAR, END_YEAR + 1)
    LEARNING_RATE_WEIGHT = inputs['learning_rate_weight']['value']
    LEARNING_RATE_POWERTRAIN = inputs['learning_rate_powertrain']['value']
    LEARNING_RATE_ROADLOAD = inputs['learning_rate_roadload']['value']
    LEARNING_RATE_BEV = inputs['learning_rate_bev']['value']
    DOLLAR_BASIS = int(inputs['analysis_year_dollars']['value'])

    # update gdp_deflators dict with adjustment values
    for key in gdp_deflators:
        gdp_deflators[key]['adjustment'] = gdp_deflators[DOLLAR_BASIS]['factor'] / gdp_deflators[key]['factor']

    techcosts_engine.insert(0, 'ALPHA_engine, Cylinders', list(zip(techcosts_engine['ALPHA_engine'], techcosts_engine['actual_cylinders'])))

    # convert all dollars in to consistent, analysis dollars
    techcosts_engine = CalcCosts(techcosts_engine).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'engine_cost')
    techcosts_deac = CalcCosts(techcosts_deac).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'deac_cost')
    techcosts_trans = CalcCosts(techcosts_trans).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'trans_cost')
    techcosts_accessories = CalcCosts(techcosts_accessories).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'accessory_cost')
    techcosts_startstop = CalcCosts(techcosts_startstop).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'start-stop_cost')
    techcosts_weight = CalcCosts(techcosts_weight).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'cost_per_pound', 'DMC_ln_coefficient', 'DMC_constant', 'IC_slope')
    techcosts_aero = CalcCosts(techcosts_aero).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'aero_cost')
    techcosts_nonaero = CalcCosts(techcosts_nonaero).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'nonaero_cost')
    techcosts_bev = CalcCosts(techcosts_bev).convert_dollars_to_analysis_basis(gdp_deflators, DOLLAR_BASIS, 'bev_cost_slope', 'bev_cost_intercept', 'dollar/kWh_0WR', 'dollar/kWh_20WR')
    techcosts_bev = techcosts_bev.to_dict('index')

    alpha_files = dict()
    for folder_num in range(0, len(ALPHA_FOLDERS)):
        alpha_files[folder_num] = [file for file in ALPHA_FOLDERS[folder_num].iterdir() if file.name.__contains__('.csv')]

    # this loop vertically concatenates 2016 and future files for each ALPHA class into a single ALPHA file containing both 2016 and future results
    alpha_file = dict()
    for file_num in range(0, len(alpha_files[0])):
        alpha_file[file_num] = pd.DataFrame()
        for folder_num in range(0, len(ALPHA_FOLDERS)):
            alpha_file_temp = pd.read_csv(alpha_files[folder_num][file_num], skiprows=range(1, 2))
            # check for necessary energy consumptions in ALPHA files - if there, pass; if not then calculate, add to file and save (overwrite) file to same path
            if 'Inertial_Work_J/m' in alpha_file_temp.columns.tolist():
                pass
            else:
                print(f'Getting energy consumption metrics for ALPHA file {file_num} of {len(alpha_files[0])} in folder {folder_num} of {len(ALPHA_FOLDERS)}')
                alpha_file_temp.insert(len(alpha_file_temp.columns), 'Inertial_Work_J/m', 0)
                alpha_file_temp.insert(len(alpha_file_temp.columns), 'Net_RoadLoad_Work_J/m', 0)
                alpha_file_temp = get_energy_consumption_metrics(alpha_file_temp, file_num, folder_num)
                alpha_file_temp.to_csv(alpha_files[folder_num][file_num], index=False)
            alpha_file_temp = alpha_file_temp[METRICS]
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
        # temp.to_csv(PATH_ALPHA_INPUTS.joinpath('file_num' + str(file_num) + '.csv'))
        for engine_architecture in engine_architectures:
            for percent_weight_reduction in percent_weight_reductions:
                for aero_improvement in aero_improvements:
                    for nonaero_improvement in nonaero_improvements:
                        package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class] \
                            = alpha_file[file_num].loc[(alpha_file[file_num]['engine_architecture'] == engine_architecture)
                                                       & (alpha_file[file_num]['weight_reduction'] == percent_weight_reduction)
                                                       & (alpha_file[file_num]['aero'] == aero_improvement)
                                                       & (alpha_file[file_num]['nonaero'] == nonaero_improvement)]
                        package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class]\
                            .reset_index(drop=True, inplace=True)
                        # insert and calculate new cost columns
                        temp_df = package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class].copy()
                        temp_df.insert(len(temp_df.columns), 'deac_cost', 0)
                        cost_object = CalcCosts(temp_df)
                        temp_df = cost_object.deac_cost(techcosts_deac)
                        temp_df = cost_object.trans_cost(techcosts_trans)
                        temp_df = cost_object.accessory_cost(techcosts_accessories)
                        temp_df.insert(len(temp_df.columns), 'start-stop_cost', 0)
                        temp_df = cost_object.startstop_cost(techcosts_startstop)
                        temp_df = cost_object.aero_cost(techcosts_aero, work_class)
                        temp_df = cost_object.nonaero_cost(techcosts_nonaero)
                        for year in YEARS:
                            temp_df.insert(len(temp_df.columns), f'weight_cost_{year}', 0)
                        for year in YEARS:
                            temp_df.insert(len(temp_df.columns), f'powertrain_cost_{year}', 0)
                        for year in YEARS:
                            temp_df.insert(len(temp_df.columns), f'roadload_cost_{year}', 0)
                        for year in YEARS:
                            temp_df.insert(len(temp_df.columns), f'vehicle_cost_{year}', 0)
                        cost_object.weight_cost(START_YEAR, techcosts_weight, work_class)
                        # sum individual techs into system-level costs (powertrain, roadload)
                        cost_object.powertrain_cost(START_YEAR)
                        cost_object.roadload_cost(START_YEAR)
                        # apply learning
                        cost_object.year_over_year_cost(START_YEAR, YEARS, LEARNING_RATE_WEIGHT, 'weight_cost')
                        cost_object.year_over_year_cost(START_YEAR, YEARS, LEARNING_RATE_POWERTRAIN, 'powertrain_cost')
                        cost_object.year_over_year_cost(START_YEAR, YEARS, LEARNING_RATE_ROADLOAD, 'roadload_cost')
                        cost_object.vehicle_cost(YEARS)
                        effectiveness_class_dict[effectiveness_class] = pd.concat([effectiveness_class_dict[effectiveness_class], temp_df], axis=0, ignore_index=True, sort=False)

    # save ALPHA-based output files
    PATH_OUTPUTS.mkdir(exist_ok=True)
    path_of_run_folder = PATH_OUTPUTS.joinpath(f'{start_time_readable}_O2-TechCosts')
    path_of_run_folder.mkdir(exist_ok=False)
    for effectiveness_class in [*effectiveness_class_dict]:
        print(f'Saving {effectiveness_class}.csv')
        effectiveness_class_dict[effectiveness_class].to_csv(path_of_run_folder.joinpath(f'ice_{effectiveness_class}.csv'), index=False)

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
        bev_cost_co2[key] = pd.DataFrame({'effectiveness_class': eff_class, 'weight_reduction': pd.Series(BEV_WR_RANGE), 'Test Weight lbs': etw,
                                          'Reg_Class': reg_class, 'Hauling_Class': work_class, 'bev_tech': f'bev_{bev_range}'})

        # calc the pack size and energy consumption
        bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), 'kWh_pack',
                                      kWh_pack_slope * bev_cost_co2[key]['weight_reduction'] / 100 + kWh_pack_intercept)
        bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), 'kWhpMi_cycle', 0)
        bev_cost_co2[key]['kWhpMi_cycle'] = bev_cost_co2[key]['kWh_pack'] * usuable_SOC * (1 - gap) * utility_factor / (bev_range * (1 - loss_charging))

        # start work on costs
        cost_object = CalcCosts(bev_cost_co2[key])
        for year in YEARS:
            bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), f'weight_cost_{year}', 0)
        for year in YEARS:
            bev_cost_co2[key].insert(len(bev_cost_co2[key].columns), f'bev_cost_{year}', 0)
        bev_cost_co2[key] = cost_object.weight_cost(START_YEAR, techcosts_weight, work_class)
        bev_cost_co2[key] = cost_object.year_over_year_cost(START_YEAR, YEARS, LEARNING_RATE_WEIGHT, 'weight_cost')
        bev_cost_co2[key][f'bev_cost_{START_YEAR}'] = cost_slope * bev_cost_co2[key]['weight_reduction'] / 100 + cost_intercept
        bev_cost_co2[key] = cost_object.year_over_year_cost(START_YEAR, YEARS, LEARNING_RATE_BEV, 'bev_cost')
        for year in YEARS:
            bev_cost_co2[key].insert(len(bev_cost_co2[key].columns),
                                          f'vehicle_cost_{year}',
                                          bev_cost_co2[key][[f'weight_cost_{year}', f'bev_cost_{year}']].sum(axis=1))

        # calc targets and upstream petroleum CO2 (CO2_refinery)
        targets = Targets(reg_class, fp, coefficients, upstream)
        targets_dict = targets.calc_targets(YEARS)

        calc_bev_co2(bev_cost_co2[key], YEARS, targets_dict, upstream)
        print(f'Saving {key}')
        bev_cost_co2[key].to_csv(path_of_run_folder.joinpath(f'{key}.csv'), index=False)

    modified_costs = pd.ExcelWriter(path_of_run_folder.joinpath(f'techcosts_in_{DOLLAR_BASIS}_dollars.xlsx'))
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

    input_files_list = [techcosts_file]
    filename_list = [PurePath(path).name for path in input_files_list]
    for file in filename_list:
        path_source = PATH_INPUTS.joinpath(file)
        path_destination = path_of_run_folder.joinpath(file)
        shutil.copy(path_source, path_destination)

if __name__ == '__main__':
    main()
