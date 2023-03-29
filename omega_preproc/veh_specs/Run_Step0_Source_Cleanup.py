import pandas as pd
import importlib
import os
import time
from pathlib import *

main_path = 'I:\Project\Midterm Review\Trends\Original Trends Team Data Gathering and Analysis\Tech Specifications'\
            +'\\'+'techspecconsolidator\Source Cleanup Runs'
# main_path = 'I:/Project/Midterm Review/Trends/Original Trends Team Data Gathering and Analysis/Tech Specifications/techspecconsolidator/Source Cleanup Runs'
run_folder = str(input('Enter Run Folder Name: '))

run_controller = pd.read_csv(main_path + '\\' + run_folder + '/Source Cleanup Run Controller.csv')
full_unit_table = pd.read_csv(main_path + '\\' + run_folder +  '/Source Cleanup Unit Conversion.csv')
# run_controller = pd.read_csv('Source Cleanup Run Controller.csv')
# full_unit_table = pd.read_csv('Source Cleanup Unit Conversion.csv')
for run_count in range(0,len(run_controller)):
    run_folder = str(run_controller['Run Folder'][run_count])
    input_path = main_path+'\\'+run_folder+'\\'+'inputs'
    output_path = main_path+'\\'+run_folder+'\\'+'outputs'
    bool_run_cleanup = str(run_controller['Run Cleanup?'][run_count])
    if bool_run_cleanup == 'y':
        raw_data_filepath = str(run_controller['Raw Data Filepath'][run_count])
        raw_data_filename = str(run_controller['Raw Data Filename'][run_count])
        data_source = str(run_controller['Data Source'][run_count])
        cleanup_function_txt = str(run_controller['Cleanup Function'][run_count])
        unit_table = full_unit_table[full_unit_table['Data Source'] == data_source].reset_index(drop=True)
        exception_table_filename = str(run_controller['Exceptions Table Filename'][run_count])
        bodyid_filename = str(run_controller['BodyID Filename'][run_count])
        matched_bodyid_filename = str(run_controller['Matched BodyID Filename'][run_count])
        ratedhp_filename = str(run_controller['Matched RatedHp Filename'][run_count])
        try:
            model_year = int(run_controller['Model Year'][run_count])
            print(data_source + ': ' + str(model_year))
        except ValueError:
            model_year = 0
        ftp_drivecycle_filename = str(run_controller['FTP Drive Cycle Filename'][run_count])
        hwfet_drivecycle_filename = str(run_controller['HWFET Drive Cycle Filename'][run_count])
        lineageid_filename = str(run_controller['LineageID Filename'][run_count])
        if exception_table_filename != 'N':
            exceptions_table = pd.read_csv(raw_data_filepath + '\\' + exception_table_filename)
        else:
            exceptions_table = 'N'
        # aero_table_filename = str(run_controller['Aero Table Filename'][run_count])

        cleanup_function = getattr(importlib.import_module(cleanup_function_txt, package=None), cleanup_function_txt)
        cleanup_function(raw_data_filepath, input_path, raw_data_filename, output_path, exceptions_table, \
                         bodyid_filename, matched_bodyid_filename, unit_table, model_year, \
                         ratedhp_filename, ftp_drivecycle_filename, hwfet_drivecycle_filename,  \
                         lineageid_filename)
# Wards_Readin.Wards_Readin(input_path_Wards,output_path,joining_path,file_Wards, merging_categories_file)
# FE_Readin.FE_Readin(input_path_FE, output_path, joining_path, file_FE, merging_categories_file)
# AllData_Readin.AllData_Readin(input_path_AllData, output_path, file_AllData, merging_categories_file)
