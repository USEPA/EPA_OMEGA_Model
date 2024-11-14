import pandas as pd
import numpy as np
def weighed_average(grp):
    weighting_field = 'Total Volumes by BodyID'
    return grp._get_numeric_data().multiply(grp[weighting_field], axis=0).sum()/((~pd.isnull(grp)).multiply(grp[weighting_field],axis=0).sum())

def Get_Redesign_Stats(input_path, output_path, raw_data_filenames, footprint_plots, \
                load_factor_plots, credit_integration, target_credit, credit_legend_category, credit_filenames, \
                Volumes_weighted_bool, remove_scatter_bool, FTP_time, HWFET_time, color_array_filename, \
                bool_max_peffid_filepaths, id_type, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                aeroclass_table_filename, ALPHA_class_filename, OMEGA_index_filename, tire_dimension_filename, \
                cd_grouping_category):
    bodyid_filepath = 'I:\Project\Midterm Review\Trends\Original Trends Team Data Gathering and Analysis\Lineage\Lineage Database Tables'
    bodyid_filename = 'BodyID.xlsx'
    bodyid_file = pd.read_excel(bodyid_filepath+'\\'+bodyid_filename)
    bodyid_file = bodyid_file[bodyid_file['BodyID EndYear'].astype(str) != 'xx'].reset_index(drop=True)

    MY2016_baseline_filepath = \
        'I:\Project\Midterm Review\Trends\Original Trends Team Data Gathering and Analysis\Tech Specifications' + \
        '\\' + 'techspecconsolidator\Query Postprocessing Runs' + '\\' + '20171214\inputs'
    MY2016_baseline_filename = '2016 Baseline.csv'
    MY2016_baseline = pd.read_csv(MY2016_baseline_filepath+'\\'+MY2016_baseline_filename)

    if ',' in raw_data_filenames:
        filenames = pd.Series(list(raw_data_filenames.split(','))).str.strip()
    else:
        filenames = pd.Series([raw_data_filenames])
    for id_filename in filenames:
        model_year = int(id_filename[0:4])
        print(model_year)
        try:
            id_file_modelyear = pd.read_csv(input_path+'\\'+id_filename)
        except UnicodeDecodeError:
            id_file_modelyear = pd.read_csv(input_path+'\\'+id_filename, encoding = 'ISO-8859-1')
        try:
            id_file_modelyear['FOOTPRINT_SUBCONFIG_VOLUMES']
        except KeyError:
            volume_key = 'Distributed FEProd'
            mfr_key = 'CARLINE_MFR_NAME'
            name_key = 'CARLINE_NAME'
        else:
            volume_key = 'FOOTPRINT_SUBCONFIG_VOLUMES'
            mfr_key = 'CAFE_MFR_NAME'
            name_key = 'CARLINE_NAME'
        id_file_modelyear = id_file_modelyear.rename(columns={volume_key: \
                volume_key + '_' + str(model_year)})
        id_file_modelyear[volume_key + '_' + str(model_year)] = \
            id_file_modelyear[volume_key + '_' + str(model_year)].replace([np.nan,'',str(np.nan)],0).astype(float)
        # if (pd.Series(id_file_modelyear.columns) == 'MODEL_YEAR').sum() == 0:
        #     id_file_modelyear = pd.concat([pd.Series(np.zeros(len(id_file_modelyear)), name='MODEL_YEAR') \
        #         .astype(int).replace(0, model_year), id_file_modelyear], axis=1)
        joining_columns = [mfr_key, 'BodyID', 'BodyID StartYear', 'BodyID EndYear', \
                           'Wards Projected BodyID StartYear', 'Wards Projected BodyID EndYear', 'CabinID', 'CabinID StartYear', 'CabinID EndYear', \
                           'Wards Projected CabinID StartYear', 'Wards Projected CabinID EndYear']
        carline_names_by_BodyID = id_file_modelyear[[name_key, 'BodyID']].rename(\
            columns = {name_key:name_key + '_' + str(model_year)}).groupby('BodyID')[\
            name_key + '_' + str(model_year)].apply(lambda x: '|'.join(map(str, x))).reset_index()
        for all_count in range(0, len(carline_names_by_BodyID)):
            carline_names_by_BodyID[name_key+'_'+str(model_year)][all_count] = \
                '|'.join(list(pd.Series(carline_names_by_BodyID[name_key+'_'+str(model_year)][all_count] \
                                        .split('|')).unique()))
        id_file_modelyear = id_file_modelyear[list(joining_columns)+[volume_key + '_' + str(model_year)]]\
            .groupby(joining_columns).sum().reset_index()
        id_file_modelyear=pd.merge_ordered(id_file_modelyear, carline_names_by_BodyID, how='left', on='BodyID')
        try:
            # joining_columns = list(set(id_file_all.columns)-(set(id_file_all.columns)-set(id_file_modelyear.columns)))
            id_file_all = pd.merge_ordered(id_file_all, id_file_modelyear[['BodyID']+\
                [name_key + '_' + str(model_year)]+[volume_key + '_' + str(model_year)]], how='outer', on='BodyID')
            id_file_all[volume_key + '_' + str(model_year)] = id_file_all[volume_key + '_' + str(model_year)].replace(np.nan,0)
            id_file_all['Total Volumes by BodyID'] = id_file_all['Total Volumes by BodyID'].astype(float) + \
                id_file_all[volume_key + '_' + str(model_year)].astype(float)
        except NameError:
            id_file_all = pd.merge_ordered(bodyid_file, id_file_modelyear[['BodyID']+[name_key + '_' + str(model_year)]\
                +[volume_key + '_' + str(model_year)]], how='outer', on='BodyID')
            id_file_all['Total Volumes by BodyID'] = pd.Series(np.zeros(len(id_file_all))).astype(float) + \
                id_file_all[volume_key + '_' + str(model_year)].astype(float)

    id_file_all['Redesign Length'] = pd.Series(np.zeros(len(id_file_all))).replace(0,np.nan)
    id_file_all['Wards Projected Redesign Length'] = pd.Series(np.zeros(len(id_file_all))).replace(0, np.nan)

    id_file_all['Redesign Length'][id_file_all['CabinID EndYear'].astype(str) != 'null'] = \
        id_file_all['CabinID EndYear'][id_file_all['CabinID EndYear'].astype(str) != 'null'].astype(float).subtract(\
        id_file_all['CabinID StartYear'][id_file_all['CabinID EndYear'].astype(str) != 'null'].astype(float))

    id_file_all['Wards Projected Redesign Length'][id_file_all['Wards Projected CabinID EndYear'].astype(str) != 'null'] = \
        id_file_all['Wards Projected CabinID EndYear'][id_file_all['Wards Projected CabinID EndYear'].astype(str) != 'null'].astype(float).subtract(\
        id_file_all['Wards Projected CabinID StartYear'][id_file_all['Wards Projected CabinID EndYear'].astype(str) != 'null'].astype(float))

    id_file_all['Redesign Length'][id_file_all['CabinID EndYear'].astype(str) != 'null'] = \
        id_file_all['Redesign Length'][id_file_all['CabinID EndYear'].astype(str) != 'null']+1
    id_file_all['Wards Projected Redesign Length'][id_file_all['Wards Projected CabinID EndYear'].astype(str) != 'null'] = \
        id_file_all['Wards Projected Redesign Length'][id_file_all['Wards Projected CabinID EndYear'].astype(str) != 'null'] + 1

    # MY2016_index_byBodyID = MY2016_baseline[['Index', 'BodyID']].rename(columns = {'Index': 'Index_MY2016Baseline'})\
    # .groupby('BodyID')['Index_MY2016Baseline'].apply(lambda x: '|'.join(map(str, x))).reset_index()
    # MY2016_index_byBodyID_singleBodyID = MY2016_index_byBodyID[\
    #     ~(MY2016_index_byBodyID['BodyID'].astype(str).str.contains('|'))].reset_index(drop=True)
    # MY2016_index_byBodyID_multiBodyID = MY2016_index_byBodyID[\
    #     (MY2016_index_byBodyID['BodyID'].astype(str).str.contains('|'))].reset_index(drop=True)
    # for multiBodyID in MY2016_index_byBodyID_multiBodyID['BodyID'].unique():
    #     multi_subarray = MY2016_index_byBodyID_multiBodyID[MY2016_index_byBodyID_multiBodyID['BodyID'] == multiBodyID].reset_index(drop=True)
    #
    # MY2016_index_byBodyID['BodyID'] = MY2016_index_byBodyID['BodyID'].astype(int)
    # id_file_all = pd.merge_ordered(id_file_all, MY2016_index_byBodyID, how='left', on='BodyID')
    # id_file_all = id_file_all[list(joining_columns)+sorted(list(\
    #     set(id_file_all.columns)-set(\
    #         list(set(list(joining_columns))-set(['Total Volumes by BodyID'])-\
    #     set(list(['Redesign Length', 'Wards Projected Redesign Length']))))))]

    # bodyid_file = bodyid_file[~bodyid_file['BodyID'].isin(list(id_file_all['BodyID']))].reset_index(drop=True)
    # id_file_all = pd.merge_ordered(id_file_all, bodyid_file[list(\
    #     set(bodyid_file.columns)-(set(bodyid_file.columns)-set(id_file_all.columns)))], how='outer', on = list(\
    #     set(bodyid_file.columns)-(set(bodyid_file.columns)-set(id_file_all.columns)))).reset_index(drop=True)
    id_file_all = id_file_all.sort_values('BodyID').reset_index(drop=True)
    id_file_all.to_csv(output_path+'\\'+'Full BodyID Statistics.csv', index=False)
    # id_file_final = id_file_all[[mfr_key, 'Redesign Length', 'Total Volumes by BodyID']].groupby([mfr_key])\
    #     .apply(weighed_average).drop([mfr_key, 'Total Volumes by BodyID'],axis=1).reset_index()
    # id_file_final.to_csv(output_path+'\\'+'Manufacturer Redesign Statistics.csv', index=False)