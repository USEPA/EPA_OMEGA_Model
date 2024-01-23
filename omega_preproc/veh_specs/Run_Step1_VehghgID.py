#
import os
import pandas as pd
# import numpy as np
# import datetime
from pathlib import Path
# import matplotlib.pyplot as plt
home = str(Path.home())
REMOVE_DUPLICATED_BY_TARGET_COEFS_MTH = True

root_drive_letter = 'I:' # 'C:'
main_path = root_drive_letter + '/Project/Midterm Review/Trends/Original Trends Team Data Gathering and Analysis/Tech Specifications/techspecconsolidator/VehGHG Runs'

run_folder = str(input('Enter Run Folder Name: '))
run_folder_path = os.path.join(main_path, run_folder)
run_controller_file = os.path.join(run_folder_path, 'VehghgID Run Controller.csv')

run_controller = pd.read_csv(run_controller_file, encoding="ISO-8859-1")
# run_controller = run_controller.replace(np.nan, '', regex=True)
for run_count in range(0, len(run_controller)):
    # run_folder = str(run_controller['Run Folder'][run_count])
    input_path = main_path + '\\' + run_folder + '\\' + 'inputs'
    output_path_vehghgid = main_path + '\\' + run_folder + '\\' + 'outputs'
    output_path_intermediate = main_path + '\\' + run_folder + '\\' + 'intermediate files'
    output_path_datasources_matched_to_configid = main_path + '\\' + run_folder + '\\' + 'Datasources Matched to ConfigID'
    bool_run_new_manual_filter = str(run_controller['New Manual Filter?'][run_count])
    bool_run_new_vehghgid = str(run_controller['New Config ID?'][run_count])
    model_year = int(run_controller['Model Year'][run_count])
    footprint_filename = str(run_controller['Footprint Filename'][run_count])
    lineageid_mapping_filename = str(run_controller['LineageID Mapped to Footprint Filename'][run_count])
    bodyid_filename = str(run_controller['BodyID Filename'][run_count])
    manual_filter_filename = str(run_controller['Manual Filter Filename, No Extensions'][run_count])
    expanded_footprint_filename = str(run_controller['Expanded Footprint Filename'][run_count])
    subconfig_filename = str(run_controller['Subconfig Filename'][run_count])  # subconfig_sales
    vehghg_filename = str(run_controller['VehghgID Filename'][run_count])
    model_type_filename = str(run_controller['Model Type Filename'][run_count])
    model_type_exceptions_table_filename = str(run_controller['Model Type File Exceptions Table filename'][run_count])
    subconfig_MY_exceptions_table_filename = str(run_controller['Model Year File Exceptions Table filename'][run_count])
    subconfig_sales_exceptions_table_filename = str(run_controller['Subconfig Sales File Exceptions Table filename'][run_count])
    footprint_exceptions_table_filename = str(run_controller['Footprint File Exceptions Table filename'][run_count])
    roadload_coefficient_table_filename = str(run_controller['Roadload Coefficient Table Filename'][run_count])
    set_roadload_coefficient_table_filename = str(run_controller['tstcar Fuel Economy Test Filename'][run_count])
    tstcar_MY_errta_filename = str(run_controller['tstCar File Exceptions Table filename'][run_count])
    tstcar_MY_carline_name_mapping_filename = str(run_controller['tstCar CARLINE_NAME mapping filename'][run_count])
    set_bodyid_to_lineageid = int(run_controller['SetBodyIDtoLineageID'][run_count])
    tstcar_folder = str(run_controller['tstcar_folder'][run_count])
    drivecycle_filenames = str(run_controller['Drive Cycle Filenames'][run_count])
    if ('[' and ']') in drivecycle_filenames:
        drivecycle_filenames = eval(drivecycle_filenames)

    drivecycle_input_filenames = str(run_controller['Drive Cycle Input Names'][run_count])
    if ('[' and ']') in drivecycle_input_filenames:
        drivecycle_input_filenames = eval(drivecycle_input_filenames)

    for i in range(len(drivecycle_input_filenames)):
        if 'FTP' in drivecycle_input_filenames[i]:
            drivecycle_input_filenames[i] = 'FTP'
        elif 'HWY' in drivecycle_input_filenames[i]:
            drivecycle_input_filenames[i] = 'HWY'
        elif 'US06' in drivecycle_input_filenames[i]:
            drivecycle_input_filenames[i] = 'US06'

    drivecycle_output_filenames = str(run_controller['Drive Cycle Output Names'][run_count])
    if ('[' and ']') in drivecycle_output_filenames:
        drivecycle_output_filenames = eval(drivecycle_output_filenames)
    for i in range(len(drivecycle_output_filenames)):
        if 'FTP' in drivecycle_output_filenames[i]:
            drivecycle_output_filenames[i] = 'FTP'
        elif 'HWY' in drivecycle_output_filenames[i]:
            drivecycle_output_filenames[i] = 'HWY'
        elif 'US06' in drivecycle_output_filenames[i]:
            drivecycle_output_filenames[i] = 'US06'

    footprint_exceptions_table = pd.read_csv(input_path+'\\' + footprint_exceptions_table_filename, encoding="ISO-8859-1")  # encoding='utf-8' encoding='utf-8-sig'  #, converters={'Column Name': eval, 'Old Value': eval, 'New Value': eval})
    # footprint_exceptions_table = footprint_exceptions_table.applymap(lambda s: s.upper() if type(s) == str else s)
    print(model_year)
    if (bool_run_new_manual_filter == 'n') and model_type_exceptions_table_filename != 'N':
        modeltype_exceptions_table = pd.read_csv(input_path+'\\' + model_type_exceptions_table_filename, encoding="ISO-8859-1")
        subconfig_MY_exceptions_table = pd.read_csv(input_path+'\\' + subconfig_MY_exceptions_table_filename, encoding="ISO-8859-1")
        subconfig_sales_exceptions_table = pd.read_csv(input_path+'\\' + subconfig_sales_exceptions_table_filename, encoding="ISO-8859-1")
        tstcar_MY_exceptions_table = pd.read_csv(tstcar_folder + '\\' + tstcar_MY_errta_filename, encoding="ISO-8859-1")
    else:
        modeltype_exceptions_table = 'N'
        subconfig_MY_exceptions_table = 'N'
        subconfig_sales_exceptions_table = 'N'
        tstcar_MY_exceptions_table = 'N'

    if (bool_run_new_vehghgid == 'y'):
        import Subconfig_ModelType_Footprint_Bodyid_Expansion
        Subconfig_ModelType_Footprint_Bodyid_Expansion.Subconfig_ModelType_Footprint_Bodyid_Expansion(input_path, footprint_filename, lineageid_mapping_filename, bodyid_filename, bool_run_new_manual_filter, manual_filter_filename,
                                                                                                      expanded_footprint_filename, subconfig_filename, model_type_filename, vehghg_filename, output_path_vehghgid, footprint_exceptions_table,
                                                                                                      modeltype_exceptions_table, subconfig_MY_exceptions_table, subconfig_sales_exceptions_table, tstcar_MY_exceptions_table, model_year,
                                                                                                      roadload_coefficient_table_filename, set_bodyid_to_lineageid, drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames,
                                                                                                      set_roadload_coefficient_table_filename, tstcar_MY_carline_name_mapping_filename, tstcar_folder)
    print('*** VehGHG Run Completed !!!')