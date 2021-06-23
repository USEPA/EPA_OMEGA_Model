import os
import pandas as pd
import numpy as np
import datetime
from pathlib import Path
import matplotlib.pyplot as plt

import Subconfig_ModelType_Footprint_Bodyid_Expansion
import Calculate_Powertrain_Efficiency_SL

home = str(Path.home())
dynamometer_drive_schedules = home + '/PycharmProjects/EPA_OMEGA_Model/omega_preproc/veh_specs/dynamometer_drive_schedules/'

input_path = 'C:/Users/slee02/Documents/Python/inputs/'
working_directory = 'C:/Users/slee02/Documents/Python/outputs/'

# main_path = 'I:\Project\Midterm Review\Trends\Original Trends Team Data Gathering and Analysis\Tech Specifications'\
#             +'\\'+'techspecconsolidator\VehGHG Runs'
# run_folder = str(input('Enter Run Folder Name: '))
# run_controller = pd.read_csv(main_path + '\\' + run_folder + '\\' + 'VehghgID Run Controller.csv')
year = 2019
subconfig_filename1 = 'sample_vehicles.csv'
roadload_coefficient_table_filename1 = subconfig_filename1
ftp_drivecycle_filename1 = 'drivetrace_FTP.csv'
hwfet_drivecycle_filename1 = 'drivetrace_HWFE.csv'

# subconfig_filename = 'CAFE_Subconfig_Sales_MY2019_20210213_607c2aa6-c48d-483e-835e-ac4f0de2f88e.csv'
# roadload_coefficient_table_filename = 'CAFE_Subconfig_MY2019_20210213_cc75eaa5-1c57-4c54-bd98-95177db74925.csv'
dynamometer_drive_schedules = home + '/PycharmProjects/EPA_OMEGA_Model/omega_preproc/veh_specs/dynamometer_drive_schedules/'
ftp_drivecycle_filename = dynamometer_drive_schedules + 'ftpcol10hz.csv'
hwfet_drivecycle_filename = dynamometer_drive_schedules + 'hwycol10hz.csv'
us06_drivecycle_filename = dynamometer_drive_schedules + 'us06col.csv'

ftp_drivecycle = pd.read_csv(ftp_drivecycle_filename, encoding="ISO-8859-1", skiprows=1)  # EVCIS Qlik Sense query results contain hyphens for nan
hwfet_drivecycle = pd.read_csv(hwfet_drivecycle_filename, encoding="ISO-8859-1", skiprows=1)  # EVCIS Qlik Sense query results contain hyphens for nan
us06_drivecycle = pd.read_csv(us06_drivecycle_filename, encoding="ISO-8859-1", skiprows=1)  # EVCIS Qlik Sense query results contain hyphens for nan

plt.plot(ftp_drivecycle['seconds'], ftp_drivecycle['mph'])
plt.show()

dftp = {ftp_drivecycle.columns[0]: list(ftp_drivecycle['seconds']), ftp_drivecycle.columns[1]: list(ftp_drivecycle['mph'])}
ftp_time = dftp['seconds'][-1]
plt.plot(dftp['seconds'], dftp['mph'])

# footprint_filename = 'Footprint_MY2019_20210213_ea0f8a20-80e3-4129-9bf0-793bcdd7444d.csv'
# vehghg_filename = 'VehghgID_MY2019.csv'
# model_type_filename = 'CAFE_Model_Type_MY2019_20210213_0ac07e06-3f39-46e7-b812-edcd224b52d1.csv'
# footprint_lineage_filename = lineageid_mapping_filename = 'Footprint Lineage_MYs2012-2019andDummyLineageMYs2017-2019_20210214.csv'
# bodyid_filename = 'BodyID_20210215.csv'
#
# footprint_file = pd.read_csv(input_path + '\\' + footprint_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
# lineage_file = pd.read_csv(input_path + '\\' + footprint_lineage_filename, encoding="ISO-8859-1")
#
# body_id_table_readin = pd.read_csv(input_path + '\\' + bodyid_filename, na_values={''}, keep_default_na=False, encoding="ISO-8859-1")
# body_id_table_readin = body_id_table_readin[body_id_table_readin['BodyID EndYear'] != 'xx'].reset_index(drop=True)
# body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['BodyID EndYear'])) & (body_id_table_readin['BodyID StartYear'] <= year)].reset_index(drop=True)
# body_id_int_not_null_endyear = body_id_table_int[~body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
# body_id_int_not_null_endyear['BodyID EndYear'] = body_id_int_not_null_endyear['BodyID EndYear'].astype(float)
# body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['BodyID EndYear'] >= year], body_id_table_int[body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')]]).reset_index(drop=True)
# body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
# body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)
#
# footprint_file = footprint_file[footprint_file['MODEL_YEAR'] == year].reset_index(drop=True)
#
# footprint_id_categories = ['MODEL_YEAR', 'FOOTPRINT_INDEX', 'CAFE_ID', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_CARLINE_NM', \
#                            'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_DIVISION_NM']
# footprint_indexing_categories = ['FOOTPRINT_DIVISION_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_INDEX']
# subconfig_indexing_categories = ['MFR_DIVISION_NM', 'MODEL_TYPE_INDEX', 'SS_ENGINE_FAMILY', 'CARLINE_CODE', \
#                                  'LDFE_CAFE_ID', 'BASE_LEVEL_INDEX', 'CONFIG_INDEX', 'SUBCONFIG_INDEX']
# modeltype_indexing_categories = ['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'CAFE_MODEL_YEAR', 'CARLINE_MFR_CODE',
#                                  'MFR_DIVISION_NM', 'CALC_ID', 'CAFE_ID', 'CARLINE_NAME']
#
# footprint_filter_table = footprint_file[list(footprint_id_categories) + ['WHEEL_BASE_INCHES'] + ['FOOTPRINT_DESC']].merge(
#     lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_id_categories)
# footprint_file_with_lineage = footprint_file.merge(lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_id_categories)
# full_expanded_footprint_filter_table = footprint_filter_table.merge(body_id_table, how='left', on='LineageID')
# full_expanded_footprint_file = footprint_file_with_lineage.merge(body_id_table, how='left', on='LineageID')
#
# import math
# from Unit_Conversion import hp2lbfmph, kgpm32slugpft3, mph2ftps, in2m, n2lbf, mph2mps, btu2mj, kg2lbm, \
#     ftps2mph, lbfmph2hp, in2mm
#
# subconfig_file = pd.read_csv(input_path + '\\' + subconfig_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
# subconfig_file = subconfig_file[subconfig_file['MODEL_YEAR'] == year].reset_index(drop=True)
# model_type_file = pd.read_csv(input_path + '\\' + model_type_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan)
# model_type_file = model_type_file[model_type_file['CAFE_MODEL_YEAR'] == year].reset_index(drop=True)
#
# vehghg_file_data_pt1 = subconfig_file.merge(full_expanded_footprint_file, how='left', \
#                                             left_on=['MODEL_YEAR', 'CARLINE_CODE', 'CAFE_MFR_CD', 'MFR_DIVISION_NM'], \
#                                             right_on=['MODEL_YEAR', 'FOOTPRINT_CARLINE_CD', 'CAFE_MFR_CD', 'FOOTPRINT_DIVISION_NM'])
# vehghg_file_full_merged_data = vehghg_file_data_pt1.merge(model_type_file, how='left', \
#            left_on=['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'MODEL_YEAR', 'CAFE_MFR_CD', 'MFR_DIVISION_NM', \
#                     'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'CAFE_ID', 'CARLINE_NAME'], right_on=modeltype_indexing_categories)
# vehghg_file_data = vehghg_file_full_merged_data[vehghg_file_full_merged_data['SS_LD_CARLINE_HEADER_ID'] == \
#                                                 vehghg_file_full_merged_data['LD_CARLINE_HEADER_ID']].reset_index(drop=True)
# vehghg_file = vehghg_file_data.dropna(subset=list(footprint_indexing_categories) + list(subconfig_indexing_categories), how='any').reset_index(drop=True)
# vehghg_file_nonflexfuel = vehghg_file[vehghg_file['FUEL_USAGE'] != 'E'].reset_index(drop=True)
# # Model Type Volumes
# model_type_volumes = model_type_file[
#     ['CALC_ID', 'PRODUCTION_VOLUME_FE_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE']].groupby(
#     'CALC_ID').sum().reset_index()
# vehghg_file_nonflexfuel = pd.merge_ordered(vehghg_file_nonflexfuel.drop( \
#     ['PRODUCTION_VOLUME_FE_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE'], axis=1), model_type_volumes, how='left',
#     on='CALC_ID').reset_index(drop=True)
# vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='TEMP_ID') + 1, vehghg_file_nonflexfuel], axis=1)
#
# roadload_coefficient_table = pd.read_csv(input_path + '\\' + roadload_coefficient_table_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
# roadload_coefficient_table = roadload_coefficient_table[roadload_coefficient_table['MODEL_YEAR'] == year].groupby(['LDFE_CAFE_SUBCONFIG_INFO_ID', 'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', \
#               'FUEL_NET_HEATING_VALUE', 'FUEL_GRAVITY']).first().reset_index().drop('MODEL_YEAR', axis=1).reset_index(drop=True)
# vehghg_file_nonflexfuel = pd.merge_ordered(vehghg_file_nonflexfuel, roadload_coefficient_table, \
#                                            how='left', on=['LDFE_CAFE_SUBCONFIG_INFO_ID', 'LDFE_CAFE_ID',
#                                                            'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'CAFE_MFR_CD',
#                                                            'LABEL_MFR_CD', 'MODEL_TYPE_INDEX', 'MFR_DIVISION_SHORT_NM',
#                                                            'CARLINE_NAME', 'INERTIA_WT_CLASS', 'CONFIG_INDEX',
#                                                            'SUBCONFIG_INDEX', 'TRANS_TYPE', 'HYBRID_YN']).reset_index(drop=True)
#
# vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'] = pd.Series(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE'].astype(float) * vehghg_file_nonflexfuel['FUEL_GRAVITY'].astype(float) * btu2mj * kg2lbm)
# import Calculate_Powertrain_Efficiency_SL
#
# vehghg_file_nonflexfuel['ENG_DISPL'] = vehghg_file_nonflexfuel['ENG_DISPL'].astype(float)
#
# merging_columns = list(vehghg_file_nonflexfuel.drop(['FINAL_MODEL_YR_GHG_PROD_UNITS', \
#                                                      'PROD_VOL_GHG_TOTAL_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE', \
#                                                      'PRODUCTION_VOLUME_FE_50_STATE', 'PROD_VOL_GHG_TLAAS_50_STATE',
#                                                      'PROD_VOL_GHG_STD_50_STATE'], axis=1).columns)

# ftp_drivecycle_filename = ftp_drivecycle_filename1
# hwfet_drivecycle_filename = hwfet_drivecycle_filename1
subconfig_file = pd.read_csv(input_path + '\\' + subconfig_filename1, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
subconfig_file = subconfig_file[subconfig_file['MODEL_YEAR'] == year].reset_index(drop=True)
vehghg_file_nonflexfuel = subconfig_file
vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='TEMP_ID') + 1, vehghg_file_nonflexfuel], axis=1)
vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'] =  42.73*0.75

output_array = Calculate_Powertrain_Efficiency_SL.Calculate_Powertrain_Efficiency_SL( \
    vehghg_file_nonflexfuel['TEMP_ID'], vehghg_file_nonflexfuel['TARGET_COEF_A'],
    vehghg_file_nonflexfuel['TARGET_COEF_B'], \
    vehghg_file_nonflexfuel['TARGET_COEF_C'], vehghg_file_nonflexfuel['ETW'],
    vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_FE_4'], \
    input_path, ftp_drivecycle_filename, hwfet_drivecycle_filename, vehghg_file_nonflexfuel['ENG_DISPL'].astype(float),
    vehghg_file_nonflexfuel['ENG_RATED_HP'], \
    vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'])

# output_array = Calculate_Powertrain_Efficiency_SL.Calculate_Powertrain_Efficiency_SL( \
#     vehghg_file_nonflexfuel['TEMP_ID'], vehghg_file_nonflexfuel['TARGET_COEF_A'],
#     vehghg_file_nonflexfuel['TARGET_COEF_B'], \
#     vehghg_file_nonflexfuel['TARGET_COEF_C'], vehghg_file_nonflexfuel['ETW'],
#     vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_FE_4'], \
#     input_path, ftp_drivecycle_filename, hwfet_drivecycle_filename, vehghg_file_nonflexfuel['ENG_DISPL'].astype(float),
#     vehghg_file_nonflexfuel['ENG_RATED_HP'], \
#     vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'])

vehghg_file_nonflexfuel = pd.merge_ordered(vehghg_file_nonflexfuel, output_array, how='left', \
                                           on=['TEMP_ID']).reset_index(drop=True).rename(columns={'Combined Powertrain Efficiency (%)': 'PTEFF_FROM_RLCOEFFS'}).drop('TEMP_ID', axis=1)
date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
vehghg_file_nonflexfuel.to_csv(input_path + '\\' + 'sample_vehicles1' + date_and_time + '.csv', index=False)