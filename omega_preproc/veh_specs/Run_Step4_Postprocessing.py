import pandas as pd
import importlib
main_path = 'I:\Project\Midterm Review\Trends\Original Trends Team Data Gathering and Analysis\Tech Specifications'\
            +'\\'+'techspecconsolidator\Query Postprocessing Runs'
run_controller = pd.read_csv('PostProcessing Run Controller.csv')
for run_count in range(0,len(run_controller)):
    run_yn = str(run_controller['RUN_YN'][run_count])
    if run_yn == 'y':
        run_folder = str(run_controller['Run Folder'][run_count])
        input_path = main_path+'\\'+run_folder+'\\'+'inputs'
        output_path = main_path+'\\'+run_folder+'\\'+'outputs'
        raw_data_filenames = str(run_controller['Filenames (Separated by Commas)'][run_count])
        postprocess_function_txt = str(run_controller['PostProcess Function'][run_count])
        credit_integration = str(run_controller['Integrate Tech Credits?'][run_count])
        footprint_plots = str(run_controller['Footprint Plots?'][run_count])
        load_factor_plots = str(run_controller['Load Factor Plots?'][run_count])
        target_credit = str(run_controller['Target Credit'][run_count])
        credit_legend_category = str(run_controller['Credit Legend Category'][run_count])
        credit_filenames = str(run_controller['Credit Filename List'][run_count])
        FTP_time = float(run_controller['FTP Time(s)'][run_count])
        HWFET_time = float(run_controller['HWFET Time (s)'][run_count])
        sales_weighted_bool = str(run_controller['Sales Weighted (y/n)?'][run_count])
        remove_scatter_bool  = str(run_controller['Remove Scatter (y/n)?'][run_count])
        color_array_filename = str(run_controller['Plot Color Filename'][run_count])
        bool_max_peff = str(run_controller['Max Powertrain Efficiency (y/n)?'][run_count])
        id_type = str(run_controller['ID Type'][run_count])
        ftp_drivecycle_filename = str(run_controller['FTP Drive Cycle Filename'][run_count])
        hwfet_drivecycle_filename = str(run_controller['HWFET Drive Cycle Filename'][run_count])
        aero_class_filename = str(run_controller['Aero Class Filename'][run_count])
        ALPHA_class_filename = str(run_controller['ALPHA Class Filename'][run_count])
        OMEGA_index_filename = str(run_controller['OMEGA Index Filename'][run_count])
        tire_dimension_filename = str(run_controller['Tire Dimension Filename'][run_count])
        cd_grouping_category = str(run_controller['CD Grouping Category'][run_count])
        print(str(run_count+1)+': ' + postprocess_function_txt)
        cleanup_function = getattr(importlib.import_module(postprocess_function_txt, package=None), postprocess_function_txt)
        cleanup_function(input_path, output_path, raw_data_filenames, footprint_plots, \
                         load_factor_plots, credit_integration, target_credit, credit_legend_category, credit_filenames, \
                         sales_weighted_bool, remove_scatter_bool, FTP_time, HWFET_time, color_array_filename, \
                         bool_max_peff, id_type, ftp_drivecycle_filename, hwfet_drivecycle_filename, aero_class_filename, \
                         ALPHA_class_filename, OMEGA_index_filename, tire_dimension_filename, cd_grouping_category)
# Wards_Readin.Wards_Readin(input_path_Wards,output_path,joining_path,file_Wards, merging_categories_file)
# FE_Readin.FE_Readin(input_path_FE, output_path, joining_path, file_FE, merging_categories_file)
# AllData_Readin.AllData_Readin(input_path_AllData, output_path, file_AllData, merging_categories_file)
