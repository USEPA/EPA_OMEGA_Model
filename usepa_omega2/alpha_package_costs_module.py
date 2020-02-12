import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

PATH_PROJECT = Path.cwd()
PATH_INPUTS = PATH_PROJECT.joinpath('inputs')
PATH_ALPHA_INPUTS = PATH_INPUTS.joinpath('ALPHA')
PATH_OUTPUTS = PATH_PROJECT.joinpath('outputs')
YEARS = [year for year in range(1, 11)]
FUTURE_YEARS = [year for year in range(2, 11)]
LEARNING_FACTOR = 0.02

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
           ]


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
            self.df.loc[(self.df['Test Weight lbs'] - 300 > curb_weight_min) & (self.df['Test Weight lbs'] - 300 <= curb_weight_max) & (self.df['Start Stop'] == 1), 'start-stop_cost'] = startstop_cost
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

    def weight_cost(self, techcosts_weight, work_class):
        # self.df.insert(len(self.df.columns), 'weight_cost', 0)
        base_weight_cost = techcosts_weight.at[work_class, 'cost_per_pound']
        dmc_ln_coeff = techcosts_weight.at[work_class, 'DMC_ln_coefficient']
        dmc_constant = techcosts_weight.at[work_class, 'DMC_constant']
        ic_slope = techcosts_weight.at[work_class, 'IC_slope']
        self.df.loc[self.df['weight_reduction'] == 0, 'weight_cost_year1'] = (self.df['Test Weight lbs'] - 300) * base_weight_cost
        self.df.loc[self.df['weight_reduction'] != 0, 'weight_cost_year1'] = ((self.df['Test Weight lbs'] - 300) / (1 - self.df['weight_reduction'] / 100)) * base_weight_cost \
                                                                             + ((dmc_ln_coeff * np.log(self.df['weight_reduction'] / 100) + dmc_constant) \
                                                                             * ((self.df['Test Weight lbs'] - 300) / (1- self.df['weight_reduction'] / 100)) * (self.df['weight_reduction'] / 100)) \
                                                                             + (ic_slope * (self.df['weight_reduction'] / 100)) * ((self.df['Test Weight lbs'] - 300) / (1 - self.df['weight_reduction'] / 100)) \
                                                                             * (self.df['weight_reduction'] / 100)
        return self.df

    def package_cost(self):
        self.df['powertrain_cost_year1'] = self.df[['engine_cost', 'trans_cost', 'deac_cost', 'accessory_cost', 'start-stop_cost']].sum(axis=1)
        self.df['roadload_cost_year1'] = self.df[['aero_cost', 'nonaero_cost']].sum(axis=1)
        self.df['package_cost_year1'] = self.df[['powertrain_cost_year1', 'roadload_cost_year1', 'weight_cost_year1']].sum(axis=1)
        return self.df

    def year_over_year_cost(self, FUTURE_YEARS):
        for year in FUTURE_YEARS:
            for metric in ['weight_cost', 'powertrain_cost', 'roadload_cost', 'package_cost']:
                self.df[metric + '_year' + str(year)] = self.df[metric + '_year1'] * (1 - LEARNING_FACTOR) ** (year - 1)
        return self.df


start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')
techcosts_file = pd.ExcelFile(PATH_INPUTS.joinpath('TechCosts.xlsx'))
techcosts_engine = pd.read_excel(techcosts_file, 'engine')
techcosts_deac = pd.read_excel(techcosts_file, 'deac', index_col='Cylinders')
techcosts_trans = pd.read_excel(techcosts_file, 'trans')
techcosts_accessories = pd.read_excel(techcosts_file, 'accessories')
techcosts_startstop = pd.read_excel(techcosts_file, 'start-stop')
techcosts_weight = pd.read_excel(techcosts_file, 'weight', index_col=0)
techcosts_aero = pd.read_excel(techcosts_file, 'aero')
techcosts_nonaero = pd.read_excel(techcosts_file, 'nonaero')

techcosts_engine.insert(0, 'ALPHA_engine, Cylinders', list(zip(techcosts_engine['ALPHA_engine'], techcosts_engine['actual_cylinders'])))

alpha_files = dict()
for folder_num in range(0, len(ALPHA_FOLDERS)):
    alpha_files[folder_num] = [file for file in ALPHA_FOLDERS[folder_num].iterdir() if file.name.__contains__('.csv')]

# this loop concatenates 2016 and future files for each ALPHA class into a single ALPHA file containing both 2016 and future results
alpha_file = dict()
for file_num in range(0, len(alpha_files[0])):
    alpha_file[file_num] = pd.DataFrame()
    for folder_num in range(0, len(ALPHA_FOLDERS)):
        alpha_file_temp = pd.read_csv(alpha_files[folder_num][file_num], skiprows=range(1, 2))
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
    alpha_file[file_num].insert(len(alpha_file[file_num].columns), 'ALPHA_engine, Cylinders',
                                list(zip(alpha_file[file_num]['Engine'], alpha_file[file_num]['Engine Cylinders'])))
    alpha_file[file_num] = alpha_file[file_num].merge(techcosts_engine[['ALPHA_engine, Cylinders', 'engine_architecture', 'engine_cost']],
                                                      on=['ALPHA_engine, Cylinders'], how='left')

# this loop breaks each ALPHA file into package dictionaries identified by the identifying tuple
package_dict = dict()
effectiveness_class_dict = dict()
for file_num in range(0, len(alpha_files[0])):
    effectiveness_class = CreatePackageDictTuple(alpha_file[file_num]).effectiveness_class()
    print(f'Working on {effectiveness_class}')
    effectiveness_class_dict[effectiveness_class] = pd.DataFrame()
    engine_architectures = CreatePackageDictTuple(alpha_file[file_num]).engine_architecture()
    percent_weight_reductions = CreatePackageDictTuple(alpha_file[file_num]).percent_weight_reduction()
    aero_improvements = CreatePackageDictTuple(alpha_file[file_num]).aero_improvement()
    nonaero_improvements = CreatePackageDictTuple(alpha_file[file_num]).nonaero_improvement()
    work_class = CreatePackageDictTuple(alpha_file[file_num]).work_class_identifier()
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
                    # insert new columns
                    temp_df = package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class].copy()
                    temp_df.insert(len(temp_df.columns), 'deac_cost', 0)
                    temp_df = CalcCosts(temp_df).deac_cost(techcosts_deac)
                    temp_df = CalcCosts(temp_df).trans_cost(techcosts_trans)
                    temp_df = CalcCosts(temp_df).accessory_cost(techcosts_accessories)
                    temp_df.insert(len(temp_df.columns), 'start-stop_cost', 0)
                    temp_df = CalcCosts(temp_df).startstop_cost(techcosts_startstop)
                    temp_df = CalcCosts(temp_df).aero_cost(techcosts_aero, work_class)
                    temp_df = CalcCosts(temp_df).nonaero_cost(techcosts_nonaero)
                    for year in YEARS:
                        temp_df.insert(len(temp_df.columns), 'weight_cost_year' + str(year), 0)
                    for year in YEARS:
                        temp_df.insert(len(temp_df.columns), 'powertrain_cost_year' + str(year), 0)
                    for year in YEARS:
                        temp_df.insert(len(temp_df.columns), 'roadload_cost_year' + str(year), 0)
                    for year in YEARS:
                        temp_df.insert(len(temp_df.columns), 'package_cost_year' + str(year), 0)
                    temp_df = CalcCosts(temp_df).weight_cost(techcosts_weight, work_class)
                    temp_df = CalcCosts(temp_df).package_cost()
                    temp_df = CalcCosts(temp_df).year_over_year_cost(FUTURE_YEARS)
                    effectiveness_class_dict[effectiveness_class] = pd.concat([effectiveness_class_dict[effectiveness_class], temp_df], axis=0, ignore_index=True, sort=False)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0]) \
                    #     .deac_cost(techcosts_deac)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0])\
                    #     .trans_cost(techcosts_trans)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0])\
                    #     .accessory_cost(techcosts_accessories)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0])\
                    #     .startstop_cost(techcosts_startstop)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0])\
                    #     .aero_cost(techcosts_aero, work_class)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0]) \
                    #     .nonaero_cost(techcosts_nonaero)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0])\
                    #     .weight_cost(techcosts_weight, work_class)
                    # package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0] \
                    #     = CalcCosts(package_dict[effectiveness_class, engine_architecture, percent_weight_reduction, aero_improvement, nonaero_improvement, work_class, 0])\
                    #     .package_cost()
                    # effectiveness_class_dict[effectiveness_class] \
                    #     = pd.concat([effectiveness_class_dict[effectiveness_class], package_dict[effectiveness_class, engine_architecture, percent_weight_reduction,
                    #                                                                              aero_improvement, nonaero_improvement, work_class, 0]], axis=0, ignore_index=True, sort=False)

# save output files
PATH_OUTPUTS.mkdir(exist_ok=True)
path_of_run_folder = PATH_OUTPUTS.joinpath(start_time_readable)
path_of_run_folder.mkdir(exist_ok=False)
for effectiveness_class in [*effectiveness_class_dict]:
    print(f'Saving {effectiveness_class}.csv')
    effectiveness_class_dict[effectiveness_class].to_csv(path_of_run_folder.joinpath(effectiveness_class + '.csv'), index=False)
