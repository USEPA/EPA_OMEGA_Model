import pandas as pd
import numpy as np
import datetime
def ID_Creation(input_path, output_path, raw_data_filenames, footprint_plots, \
                load_factor_plots, credit_integration, target_credit, credit_legend_category, credit_filenames, \
                sales_weighted_bool, remove_scatter_bool, FTP_time, HWFET_time, color_array_filename, \
                bool_max_peffid_filepaths, id_type, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                      aeroclass_table_filename, ALPHA_class_filename, OMEGA_index_filename, tire_dimension_filename, \
                     cd_grouping_category):
    if ',' in raw_data_filenames:
        filenames = pd.Series(list(raw_data_filenames.split(','))).str.strip()
    else:
        filenames = pd.Series([raw_data_filenames])
    min_model_year = 1e4
    max_model_year = 0

    if id_type == 'EngineID':
        ID_categories = ['CARLINE_MFR_NAME', 'NUM_CYLINDRS_ROTORS', 'ENG_DISPL', 'AIR_ASP_DESC', \
           'CYL_DEACT']
        minmax_categories = ['MODEL_YEAR', 'ENG_RATED_HP']
    elif id_type == 'TransmissionID':
        ID_categories = ['CARLINE_MFR_NAME', 'TRANS_TYPE', 'TOTAL_NUM_TRANS_GEARS']
        minmax_categories = ['MODEL_YEAR']
    elif id_type == 'PowertrainID':
        ID_categories = ['CARLINE_MFR_NAME', 'NUM_CYLINDRS_ROTORS', 'ENG_DISPL', 'AIR_ASP_DESC', \
            'TRANS_TYPE', 'TOTAL_NUM_TRANS_GEARS', 'DRV_SYS', 'HYBRID_YN', 'OFF_BOARD_CHARGE_CAPABLE_YN', 'CYL_DEACT']
        minmax_categories = ['MODEL_YEAR', 'ENG_RATED_HP', 'PTEFF_FROM_RLCOEFFS']

    for id_filename in filenames:
        model_year = int(id_filename[0:4])
        print(model_year)
        min_model_year = min(min_model_year, model_year)
        max_model_year = max(model_year, max_model_year)
        try:
            id_file_modelyear = pd.read_csv(input_path+'\\'+id_filename)
        except UnicodeDecodeError:
            id_file_modelyear = pd.read_csv(input_path+'\\'+id_filename, encoding = 'ISO-8859-1')
        # id_file_modelyear_columns_int = pd.Series(id_file_modelyear.columns)
        # id_file_modelyear_columns = id_file_modelyear_columns_int[(~id_file_modelyear_columns_int.str.contains('Master Index')) & \
        #     (~id_file_modelyear_columns_int.str.contains('Subconfig Data')) & \
        #     (~id_file_modelyear_columns_int.str.contains('Edmunds')) & (~id_file_modelyear_columns_int.str.contains('Test Car')) & \
        #     (~id_file_modelyear_columns_int.str.contains('FEGuide')) & (~id_file_modelyear_columns_int.str.contains('Wards')) & \
        #     (~id_file_modelyear_columns_int.str.contains('AllData'))].reset_index(drop=True)
        #id_file_modelyear = id_file_modelyear[id_file_modelyear_columns]
        # id_file_modelyear = id_file_modelyear[ID_categories+minmax_categories]
        id_file_modelyear['FUEL_USAGE_GROUP'] = pd.Series(id_file_modelyear['FUEL_USAGE'].str[0])
        id_file_modelyear['FUEL_USAGE_GROUP'][id_file_modelyear['FUEL_USAGE'] == 'E'] = 'Eth'
        if (pd.Series(id_file_modelyear.columns)=='MODEL_YEAR').sum() == 0:
            id_file_modelyear = pd.concat([pd.Series(np.zeros(len(id_file_modelyear)),name = 'MODEL_YEAR')\
                .astype(int).replace(0,model_year), id_file_modelyear],axis=1)
        id_file_modelyear = id_file_modelyear[id_file_modelyear['FUEL_USAGE'] != 'E'].reset_index(drop=True)\
            .rename(columns = {'FOOTPRINT_SUBCONFIG_VOLUMES': 'FOOTPRINT_SUBCONFIG_VOLUMES'+'_'+str(model_year)})
        try:
            id_file_modelyear[minmax_categories]
        except KeyError:
            missing_cols = list(set(minmax_categories)-set(id_file_modelyear.columns))
            for missing_col in missing_cols:
                id_file_modelyear[missing_col] = pd.Series(np.zeros(len(id_file_modelyear))).replace(0,np.nan)
        id_file_modelyear = id_file_modelyear[ID_categories+minmax_categories+['FUEL_USAGE_GROUP']+['CARLINE_NAME']\
            +['FOOTPRINT_SUBCONFIG_VOLUMES'+'_'+str(model_year)]]
        try:
            #joining_columns = list(set(id_file_all.columns)-(set(id_file_all.columns)-set(id_file_modelyear.columns)))
            joining_columns = ID_categories+minmax_categories+['FUEL_USAGE_GROUP']+['CARLINE_NAME']
            id_file_all = pd.merge_ordered(id_file_all, id_file_modelyear, how='outer', on=joining_columns)
        except NameError:
            id_file_all = id_file_modelyear

    volume_columns = list(pd.Series(id_file_all.columns)[pd.Series(id_file_all.columns).str.contains('FOOTPRINT_SUBCONFIG_VOLUMES')])
    id_file_all = id_file_all[['CARLINE_NAME']+volume_columns+ID_categories+minmax_categories]
    id_file_all[ID_categories] = id_file_all[ID_categories].replace(np.nan, 'null')
    id_file_all[volume_columns] = id_file_all[volume_columns].replace(np.nan,0)
    all_aggregation = id_file_all[ID_categories+['CARLINE_NAME']].groupby(ID_categories)['CARLINE_NAME'].apply(lambda x: '|'.join(map(str, x))).reset_index()
    for all_aggregate_count in range(0,len(all_aggregation)):
        all_aggregation['CARLINE_NAME'][all_aggregate_count] = '|'.join(list(pd.Series(all_aggregation['CARLINE_NAME'][all_aggregate_count].split('|')).unique()))
    sum_aggregation = id_file_all[ID_categories+volume_columns].groupby(ID_categories).sum().reset_index()
    min_aggregation = id_file_all[ID_categories+minmax_categories].groupby(ID_categories).min()
    min_aggregation.columns = pd.Series(min_aggregation.columns).str.cat(list(pd.Series(np.zeros(len(min_aggregation.columns))).replace(0,'min')), sep='_')
    min_aggregation = min_aggregation.reset_index()
    max_aggregation = id_file_all[ID_categories+minmax_categories].groupby(ID_categories).max()
    max_aggregation.columns = pd.Series(max_aggregation.columns).str.cat(list(pd.Series(np.zeros(len(max_aggregation.columns))).replace(0,'max')), sep='_')
    max_aggregation = max_aggregation.reset_index()
    minmax_aggregation = pd.merge_ordered(min_aggregation, max_aggregation, how='left', on=ID_categories)
    minmax_columns = pd.Series(list(set(minmax_aggregation.columns)-set(ID_categories))).sort_values(ascending=False)
    minmax_aggregation = minmax_aggregation[ID_categories+list(minmax_columns)]
    id_file = pd.merge_ordered(minmax_aggregation, all_aggregation, how='left', on=ID_categories)
    id_file = pd.merge_ordered(id_file, sum_aggregation, how='left', on=ID_categories)
    id_file = pd.concat([1+pd.Series(range(len(id_file)), name = id_type), id_file],axis=1)

    id_file = id_file.rename(columns={'MODEL_YEAR_min':'FirstObservedYear','MODEL_YEAR_max':'LastObservedYear'})
    id_file['StartYear'] = pd.Series(np.zeros(len(id_file)))
    id_file['EndYear'] = pd.Series(np.zeros(len(id_file)))
    id_file['StartYear'][id_file['FirstObservedYear'] == min_model_year] = 'pre-' + str(int(min_model_year+1))
    id_file['StartYear'][id_file['FirstObservedYear'] != min_model_year] = id_file['FirstObservedYear'][id_file['FirstObservedYear'] != min_model_year]
    id_file['EndYear'][id_file['LastObservedYear'] == max_model_year] = 'null'
    id_file['EndYear'][id_file['LastObservedYear'] != max_model_year] = id_file['LastObservedYear'][id_file['LastObservedYear'] != max_model_year]

    id_file_columns = pd.Series(id_file.columns)
    id_file_columns_a = id_file_columns[(~id_file_columns.str.contains('Year')) & (~id_file_columns.str.contains('VOLUMES'))]
    id_file_columns_b = id_file_columns[id_file_columns.str.contains('Year')]
    id_file_columns_c = id_file_columns[id_file_columns.str.contains('VOLUMES')]
    id_file = id_file[list(id_file_columns_a) + list(id_file_columns_b)+list(id_file_columns_c)]
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    id_file.to_csv(output_path+'\\'+id_type+' '+date_and_time+'.csv', index=False)