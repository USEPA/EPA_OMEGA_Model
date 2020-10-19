import pandas as pd
import datetime
import numpy as np
def Subconfig_ModelType_Footprint_Bodyid_Expansion(input_path, footprint_filename, footprint_lineage_filename, bodyid_filename, \
                        bool_run_new_manual_filter, manual_filter_name, expanded_footprint_filename, \
                        subconfig_filename, model_type_filename, vehghg_filename, output_path, \
                        footprint_exceptions_table, modeltype_exceptions_table, year, roadload_coefficient_table_filename, \
                        ftp_drivecycle_filename, hwfet_drivecycle_filename):
    footprint_file = pd.read_csv(input_path + '\\' + footprint_filename, encoding = "ISO-8859-1" )
    lineage_file = pd.read_csv(input_path + '\\' + footprint_lineage_filename, encoding = "ISO-8859-1")
    body_id_table_readin = pd.read_excel(input_path + '\\' + bodyid_filename, \
                                         converters={'LineageID': int, 'BodyID': int})
    body_id_table_readin = body_id_table_readin[body_id_table_readin['BodyID EndYear'] != 'xx'].reset_index(drop=True)
    body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['BodyID EndYear'])) \
                                             & (body_id_table_readin['BodyID StartYear'] <= year)].reset_index(drop=True)
    body_id_int_not_null_endyear = body_id_table_int[
        ~body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
    body_id_int_not_null_endyear['BodyID EndYear'] = body_id_int_not_null_endyear['BodyID EndYear'].astype(float)
    body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['BodyID EndYear'] >= year], \
                               body_id_table_int[
                                   body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')]]).reset_index(
        drop=True)
    body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
    body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)

    footprint_file = footprint_file[footprint_file['MODEL_YEAR'] == year].reset_index(drop=True)
    for error_check_count in range(0, len(footprint_exceptions_table)):
        if footprint_exceptions_table['Numeric (y/n)'][error_check_count] == 'y':
            footprint_file.loc[(footprint_file['MODEL_YEAR'] == footprint_exceptions_table['MODEL_YEAR'][error_check_count]) & \
                                (footprint_file['CAFE_ID'] == footprint_exceptions_table['CAFE_ID'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_DIVISION_NM'] == footprint_exceptions_table['FOOTPRINT_DIVISION_NM'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_DIVISION_CD'] == footprint_exceptions_table['FOOTPRINT_DIVISION_CD'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_CARLINE_CD'] == footprint_exceptions_table['FOOTPRINT_CARLINE_CD'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_INDEX'] == footprint_exceptions_table['FOOTPRINT_INDEX'][error_check_count]) & \
                               (footprint_file[footprint_exceptions_table['Column Name'][error_check_count]] == float(
                                    footprint_exceptions_table['Old Value'][error_check_count])), \
                                footprint_exceptions_table['Column Name'][error_check_count]] = \
                footprint_exceptions_table['New Value'][error_check_count]
        else:
            footprint_file.loc[(footprint_file['MODEL_YEAR'] == footprint_exceptions_table['MODEL_YEAR'][error_check_count]) & \
                                (footprint_file['CAFE_ID'] == footprint_exceptions_table['CAFE_ID'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_DIVISION_NM'] == footprint_exceptions_table['FOOTPRINT_DIVISION_NM'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_DIVISION_CD'] == footprint_exceptions_table['FOOTPRINT_DIVISION_CD'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_CARLINE_CD'] == footprint_exceptions_table['FOOTPRINT_CARLINE_CD'][error_check_count]) & \
                               (footprint_file['FOOTPRINT_INDEX'] == footprint_exceptions_table['FOOTPRINT_INDEX'][error_check_count]) & \
                               (footprint_file[footprint_exceptions_table['Column Name'][error_check_count]] ==
                                    footprint_exceptions_table['Old Value'][error_check_count]), \
                                footprint_exceptions_table['Column Name'][error_check_count]] = \
                footprint_exceptions_table['New Value'][error_check_count]
    footprint_id_categories = ['MODEL_YEAR', 'FOOTPRINT_INDEX', 'CAFE_ID', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_CARLINE_NM', \
                               'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_DIVISION_NM']
    footprint_filter_table = footprint_file[list(footprint_id_categories) + ['WHEEL_BASE_INCHES'] + ['FOOTPRINT_DESC']].merge(
        lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', \
        on=footprint_id_categories)
    footprint_file_with_lineage = footprint_file\
        .merge(lineage_file[list(footprint_id_categories) + ['LineageID']],how='left', on=footprint_id_categories)
    full_expanded_footprint_filter_table = footprint_filter_table.merge(
        body_id_table, how='left', on='LineageID')
    full_expanded_footprint_file = footprint_file_with_lineage\
        .merge(body_id_table, how='left', on='LineageID')
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    try:
        #BodyID table is found, no new manual filter sought
        previous_filter_table = pd.read_csv(input_path+'\\'+manual_filter_name + '.csv', encoding = "ISO-8859-1")
        previous_filter_table = previous_filter_table[previous_filter_table['MODEL_YEAR']==year].reset_index(drop=True)
    except OSError:
        #New BodyID table to be made, no previous data
        full_filter_table_save_name = manual_filter_name + ' ' + date_and_time + '.csv'
        full_expanded_footprint_filter_table.to_csv(output_path.replace('\VehghgID', '\intermediate files') \
                                                    + '\\' + full_filter_table_save_name, index=False)
    else:
        if bool_run_new_manual_filter == 'n':
            import math
            from Unit_Conversion import hp2lbfmph, kgpm32slugpft3, mph2ftps, in2m, n2lbf, mph2mps, btu2mj, kg2lbm, \
                ftps2mph, lbfmph2hp, in2mm
            full_expanded_footprint_file = full_expanded_footprint_file.merge \
                (previous_filter_table[list(footprint_id_categories) + ['BodyID'] + ['POSSIBLE_BODYID']], how='left', \
                 on=list(footprint_id_categories) + ['BodyID'])
            full_expanded_footprint_file = full_expanded_footprint_file[\
                full_expanded_footprint_file['POSSIBLE_BODYID'] == 'y'].reset_index(drop=True)
            subconfig_file = pd.read_csv(input_path + '\\' + subconfig_filename)
            subconfig_file = subconfig_file[subconfig_file['MODEL_YEAR'] == year].reset_index(drop=True)
            model_type_file = pd.read_csv(input_path + '\\' + model_type_filename, encoding = "ISO-8859-1")
            model_type_file = model_type_file[model_type_file['CAFE_MODEL_YEAR']==year].reset_index(drop=True)
            footprint_indexing_categories = ['FOOTPRINT_DIVISION_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_INDEX']
            subconfig_indexing_categories = ['MFR_DIVISION_NM', 'MODEL_TYPE_INDEX', 'SS_ENGINE_FAMILY', 'CARLINE_CODE', \
                                             'LDFE_CAFE_ID', 'BASE_LEVEL_INDEX', 'CONFIG_INDEX', 'SUBCONFIG_INDEX']
            modeltype_indexing_categories = ['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'CAFE_MODEL_YEAR', 'CARLINE_MFR_CODE','MFR_DIVISION_NM', \
                                   'CALC_ID', 'CAFE_ID', 'CARLINE_NAME']
            if type(modeltype_exceptions_table) != str:
                for error_check_count in range(0, len(modeltype_exceptions_table)):
                    if modeltype_exceptions_table['Numeric (y/n)'][error_check_count] == 'y':
                        model_type_file.loc[(model_type_file['CARLINE_NAME'] == modeltype_exceptions_table['Model'][error_check_count]) & \
                                         (model_type_file['MODEL_TYPE_INDEX'] == modeltype_exceptions_table['Model Type Index'][error_check_count]) & \
                                        (model_type_file[modeltype_exceptions_table['Column Name'][error_check_count]] == float(modeltype_exceptions_table['Old Value'][error_check_count])), \
                                         modeltype_exceptions_table['Column Name'][error_check_count]] = \
                            modeltype_exceptions_table['New Value'][error_check_count]
                    else:
                        model_type_file.loc[(model_type_file['CARLINE_NAME'] == modeltype_exceptions_table['Model'][error_check_count]) & \
                                         (model_type_file['MODEL_TYPE_INDEX'] == modeltype_exceptions_table['Model Type Index'][error_check_count]) & \
                                        (model_type_file[modeltype_exceptions_table['Column Name'][error_check_count]] == modeltype_exceptions_table['Old Value'][error_check_count]), \
                                         modeltype_exceptions_table['Column Name'][error_check_count]] = \
                            modeltype_exceptions_table['New Value'][error_check_count]
            model_type_file['CALC_ID'] = model_type_file['CALC_ID'].astype(int)
            # model_type_file.to_csv(output_path+'\\'+'Corrected Model Type File.csv', index=False)
            vehghg_file_data_pt1 = subconfig_file.merge(full_expanded_footprint_file, how='left', \
                                                    left_on=['MODEL_YEAR', 'CARLINE_CODE', 'CAFE_MFR_CD', 'MFR_DIVISION_NM'], \
                                                    right_on=['MODEL_YEAR', 'FOOTPRINT_CARLINE_CD', 'CAFE_MFR_CD', 'FOOTPRINT_DIVISION_NM'])
            vehghg_file_full_merged_data = vehghg_file_data_pt1\
                .merge(model_type_file, how='left', \
                       left_on = ['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'MODEL_YEAR', 'CAFE_MFR_CD', 'MFR_DIVISION_NM', \
             'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'CAFE_ID', 'CARLINE_NAME'],right_on = modeltype_indexing_categories)
            vehghg_file_data = vehghg_file_full_merged_data[vehghg_file_full_merged_data['SS_LD_CARLINE_HEADER_ID'] == \
                 vehghg_file_full_merged_data['LD_CARLINE_HEADER_ID']] .reset_index(drop=True)
            vehghg_file = vehghg_file_data.dropna(\
                subset = list(footprint_indexing_categories)+list(subconfig_indexing_categories), how='any').reset_index(drop=True)
            missing_entries_1 = vehghg_file[pd.isnull(vehghg_file['LineageID'])].reset_index(drop=True)
            missing_entries_2 = vehghg_file[pd.isnull(vehghg_file['TOTAL_NUM_TRANS_GEARS'])].reset_index(drop=True)
            missing_entries = pd.concat([missing_entries_1,missing_entries_2]).reset_index(drop=True)
            if len(missing_entries) > 0:
                try:
                    missing_entries.to_csv(output_path + '\\' + vehghg_filename.replace('.csv','') + '_Missing Entries.csv' ,
                                       index=False)
                except OSError:
                    pass
            vehghg_file = vehghg_file[(~pd.isnull(vehghg_file['LineageID'])) \
                & (~pd.isnull(vehghg_file['TOTAL_NUM_TRANS_GEARS']))].reset_index(drop=True)
            vehghg_file = vehghg_file.loc[:,~vehghg_file.columns.str.contains('^Unnamed')]
            matching_cyl_layout = pd.Series(np.zeros(len(vehghg_file)),name='Cylinder Layout Category').replace(0,'').astype(str)
            matching_cyl_layout[~pd.isnull(vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'])] = \
                vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'][~pd.isnull(vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'])]
            matching_cyl_layout[pd.isnull(vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'])] = 'ELE'
            
            matching_cyl_num = pd.Series(np.zeros(len(vehghg_file)),name='Number of Cylinders Category')
            matching_cyl_num[~pd.isnull(vehghg_file['NUM_CYLINDRS_ROTORS'])] = vehghg_file['NUM_CYLINDRS_ROTORS']\
                [~pd.isnull(vehghg_file['NUM_CYLINDRS_ROTORS'])].astype(float).astype(int)
            matching_cyl_num[pd.isnull(vehghg_file['NUM_CYLINDRS_ROTORS'])] = 0
            matching_cyl_num = matching_cyl_num.astype(int)

            matching_eng_disp = pd.Series(np.zeros(len(vehghg_file)), name='Engine Displacement Category')
            matching_eng_disp[~pd.isnull(vehghg_file['ENG_DISPL'])] = vehghg_file['ENG_DISPL']\
                [~pd.isnull(vehghg_file['ENG_DISPL'])].astype(float).round(1)
            matching_eng_disp[pd.isnull(vehghg_file['ENG_DISPL'])] = int(0)

            matching_drvtrn_layout = pd.Series(vehghg_file['DRV_SYS'], name='Drivetrain Layout Category').astype(
                str).replace(['F', 'R'], '2WD').replace(['A', '4'], '4WD').replace('P', '2WD')
            matching_trns_numgears = pd.Series(vehghg_file['TOTAL_NUM_TRANS_GEARS'].astype(float),
                                               name='Number of Transmission Gears Category').astype(int)
            matching_trns_numgears[vehghg_file['TRANS_TYPE'] == 'SCV'] = 1
            matching_trns_category = pd.Series(vehghg_file['TRANS_TYPE'],
                                               name='Transmission Type Category').replace(['AMS', 'SA', 'SCV'],
                                                                                          ['AM', 'A', 'CVT'])
            matching_trns_category[matching_trns_numgears == 1] = '1ST'
            matching_trns_category[(matching_trns_category == 'OT') & \
                                   vehghg_file['TRANS_TYPE_IF_OTHER'].str.contains('Automated Manual')] = 'AM'
            matching_trns_category[(matching_trns_category == 'OT') & \
                                   vehghg_file['TRANS_TYPE_IF_OTHER'].str.contains('Automatic Manual')] = 'AM'
            matching_boost_category = pd.Series(vehghg_file['AIR_ASP'], name='Boost Type Category').astype(
                str).str.upper().replace(['NA', 'NAN'], 'N')
            matching_boost_category[vehghg_file['FUEL_USAGE'] == 'EL'] = 'ELE'
            matching_boost_category[vehghg_file['FUEL_USAGE'] == 'H'] = 'ELE'
            matching_mfr_category = pd.Series(vehghg_file['MFR_DIVISION_NM'], name='Make Category').astype(str) \
                .str.split().str.get(0).str.upper().str.replace('Aston'.upper(), 'Aston Martin'.upper()) \
                .str.replace('Land'.upper(), 'Land Rover'.upper()).str.replace('Alfa'.upper(),
                'Alfa Romeo'.upper()).replace('Electric'.upper(), 'BYD').replace('The'.upper(), 'MV-1')\
                    .replace('Fisker'.upper(), 'Fisker Karma'.upper()).str.strip()
            matching_fuel_category = pd.Series(vehghg_file['FUEL_USAGE'].astype(str).str[0],
                                               name='Fuel Type Category').replace(['H','C','L'], ['E', 'CNG', 'LPG'])
            matching_fuel_category[vehghg_file['FUEL_USAGE'] == 'EL'] = 'E'
            matching_fuel_category[vehghg_file['FUEL_USAGE'] == 'E'] = 'Eth'
            matching_electrification = pd.Series(np.zeros(len(vehghg_file)), name = 'Electrification Category').replace(0,'N')
            matching_electrification[(vehghg_file['HYBRID_YN'] == 'Y') & (vehghg_file['OFF_BOARD_CHARGE_CAPABLE_YN'] == 'Y')] = 'REEV'
            matching_electrification[(vehghg_file['HYBRID_YN'] == 'N') & (vehghg_file['OFF_BOARD_CHARGE_CAPABLE_YN'] == 'Y')] = 'EV'
            matching_electrification[(vehghg_file['HYBRID_YN'] == 'Y') & (vehghg_file['OFF_BOARD_CHARGE_CAPABLE_YN'] == 'N')] = 'HEV'
            vehghg_file = pd.concat([vehghg_file, matching_cyl_layout, matching_cyl_num, \
                                          matching_eng_disp, matching_drvtrn_layout, matching_trns_category, \
                                          matching_trns_numgears, matching_boost_category, matching_mfr_category, \
                                          matching_fuel_category, matching_electrification], axis=1).reset_index(drop=True)
            vehghg_file['LineageID'] = vehghg_file['LineageID'].astype(int)
            vehghg_file['BodyID'] = vehghg_file['BodyID'].astype(int)
            #Resolve flex fuel vehicles
            vehghg_file_nonflexfuel = vehghg_file[vehghg_file['FUEL_USAGE'] != 'E'].reset_index(drop=True)
            #Model Type Volumes
            model_type_volumes = model_type_file[['CALC_ID', 'PRODUCTION_VOLUME_FE_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE']].groupby('CALC_ID').sum().reset_index()
            vehghg_file_nonflexfuel= pd.merge_ordered(vehghg_file_nonflexfuel.drop(\
                ['PRODUCTION_VOLUME_FE_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE'],axis=1), model_type_volumes, how='left', on='CALC_ID').reset_index(drop=True)
            merging_columns = list(vehghg_file_nonflexfuel.drop(['FINAL_MODEL_YR_GHG_PROD_UNITS', \
                'PROD_VOL_GHG_TOTAL_50_STATE','PRODUCTION_VOLUME_GHG_50_STATE',\
                       'PRODUCTION_VOLUME_FE_50_STATE', 'PROD_VOL_GHG_TLAAS_50_STATE', 'PROD_VOL_GHG_STD_50_STATE'],axis=1).columns)
            #Powertrain Efficiency
            roadload_coefficient_table = pd.read_csv(input_path+'\\'+roadload_coefficient_table_filename)
            roadload_coefficient_table = roadload_coefficient_table[roadload_coefficient_table['MODEL_YEAR']==year]\
                .groupby(['LDFE_CAFE_SUBCONFIG_INFO_ID','TARGET_COEF_A','TARGET_COEF_B','TARGET_COEF_C',\
                'FUEL_NET_HEATING_VALUE','FUEL_GRAVITY']).first().reset_index().drop('MODEL_YEAR',axis=1).reset_index(drop=True)
            vehghg_file_nonflexfuel = pd.merge_ordered(vehghg_file_nonflexfuel, roadload_coefficient_table, \
                how='left', on=['LDFE_CAFE_SUBCONFIG_INFO_ID','LDFE_CAFE_ID','LDFE_CAFE_MODEL_TYPE_CALC_ID','CAFE_MFR_CD','LABEL_MFR_CD','MODEL_TYPE_INDEX','MFR_DIVISION_SHORT_NM','CARLINE_NAME','INERTIA_WT_CLASS','CONFIG_INDEX','SUBCONFIG_INDEX','TRANS_TYPE','HYBRID_YN']).reset_index(drop=True)

            vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'] = pd.Series(\
                vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE']*vehghg_file_nonflexfuel['FUEL_GRAVITY']*btu2mj*kg2lbm)
            import Calculate_Powertrain_Efficiency
            vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='TEMP_ID') + 1, \
                vehghg_file_nonflexfuel],axis=1)
            vehghg_file_nonflexfuel['ENG_DISPL'] = vehghg_file_nonflexfuel['ENG_DISPL'].astype(float)
            output_array = Calculate_Powertrain_Efficiency.Calculate_Powertrain_Efficiency(\
                vehghg_file_nonflexfuel['TEMP_ID'], vehghg_file_nonflexfuel['TARGET_COEF_A'], vehghg_file_nonflexfuel['TARGET_COEF_B'], \
                vehghg_file_nonflexfuel['TARGET_COEF_C'], vehghg_file_nonflexfuel['ETW'], vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_FE_4'], \
                input_path, ftp_drivecycle_filename, hwfet_drivecycle_filename, vehghg_file_nonflexfuel['ENG_DISPL'].astype(float), vehghg_file_nonflexfuel['ENG_RATED_HP'], \
                vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'])
            vehghg_file_nonflexfuel = pd.merge_ordered(vehghg_file_nonflexfuel, output_array, how='left', \
                on = ['TEMP_ID']).reset_index(drop=True)\
                .rename(columns={'Combined Powertrain Efficiency (%)':'PTEFF_FROM_RLCOEFFS'}).drop('TEMP_ID',axis=1)

            #Resolve Volumes
            total_allocated_volumes_to_footprint = pd.DataFrame(vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['FINAL_MODEL_YR_GHG_PROD_UNITS'].sum().reset_index())\
                .rename(columns = {'FINAL_MODEL_YR_GHG_PROD_UNITS':'Total Subconfig Volume Allocated to Footprint'})
            total_allocated_volumes_to_subconfig = pd.DataFrame(vehghg_file_nonflexfuel.groupby(subconfig_indexing_categories)['PROD_VOL_GHG_TOTAL_50_STATE'].sum().reset_index()) \
                .rename(columns={'PROD_VOL_GHG_TOTAL_50_STATE': 'Total Footprint Volume Allocated to Subconfig'})
            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.merge(total_allocated_volumes_to_footprint, how='left', on=footprint_indexing_categories)\
                .merge(total_allocated_volumes_to_subconfig, how='left', on=subconfig_indexing_categories).reset_index(drop=True)
            #vehghg_file_nonflexfuel.to_csv(output_path+'\\'+'Test File.csv', index=False)
            footprint_volumes = vehghg_file_nonflexfuel['PROD_VOL_GHG_TOTAL_50_STATE'].replace(np.nan,0).reset_index(drop=True)
            footprint_tlaas_volumes = vehghg_file_nonflexfuel['PROD_VOL_GHG_TLAAS_50_STATE'].replace(np.nan, 0).reset_index(
                drop=True)
            footprint_std_volumes = vehghg_file_nonflexfuel['PROD_VOL_GHG_STD_50_STATE'].replace(np.nan, 0).reset_index(
                drop=True)
            modeltype_ghg_volumes = pd.to_numeric(vehghg_file_nonflexfuel['PRODUCTION_VOLUME_GHG_50_STATE'].replace(np.nan, 0).reset_index(
                drop=True))
            modeltype_fe_volumes = pd.to_numeric(vehghg_file_nonflexfuel['PRODUCTION_VOLUME_FE_50_STATE'].replace(np.nan, 0).reset_index(
                drop=True))

            subconfig_volumes = vehghg_file_nonflexfuel['FINAL_MODEL_YR_GHG_PROD_UNITS'].replace(np.nan,0).reset_index(drop=True)
            # total_footprint_volumes = pd.Series(footprint_volumes.replace(np.nan,0).unique()).sum()
            # total_subconfig_volumes = pd.Series(subconfig_volumes[vehghg_file_nonflexfuel['SS_LD_CARLINE_HEADER_ID'] == \
            #      vehghg_file_nonflexfuel['LD_CARLINE_HEADER_ID']].replace(np.nan,0).unique()).sum()
            distributed_volumes_footprint = pd.Series(footprint_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PROD_VOL_GHG_TOTAL_50_STATE'].transform(len), name= 'Distributed Footprint Volumes')
            distributed_tlaas_volumes_footprint = pd.Series(footprint_tlaas_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PROD_VOL_GHG_TLAAS_50_STATE'].transform(len), name='Distributed Footprint TLAAS Volumes')
            distributed_std_volumes_footprint = pd.Series(footprint_std_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PROD_VOL_GHG_STD_50_STATE'].transform(len), name='Distributed Footprint Standard Volumes')
            distributed_ghg_volumes_modeltype = pd.Series(modeltype_ghg_volumes / vehghg_file_nonflexfuel.groupby(modeltype_indexing_categories)['PRODUCTION_VOLUME_GHG_50_STATE'].transform(len), name='Distributed Model Type GHG Volumes')
            distributed_fe_volumes_modeltype = pd.Series(modeltype_fe_volumes / vehghg_file_nonflexfuel.groupby(modeltype_indexing_categories)['PRODUCTION_VOLUME_FE_50_STATE'].transform(len), name='Distributed Model Type FE Volumes')
            distributed_volumes_subconfig = pd.Series(subconfig_volumes / vehghg_file_nonflexfuel.groupby(subconfig_indexing_categories)['FINAL_MODEL_YR_GHG_PROD_UNITS'].transform(len), name = 'Distributed Subconfig Volumes')
            distributed_volumes = pd.concat([distributed_volumes_footprint, distributed_volumes_subconfig, \
                distributed_tlaas_volumes_footprint, distributed_std_volumes_footprint, distributed_ghg_volumes_modeltype, \
                distributed_fe_volumes_modeltype],axis=1).reset_index(drop=True)
            mixed_volumes_footprint = pd.Series((footprint_volumes * subconfig_volumes / vehghg_file_nonflexfuel['Total Subconfig Volume Allocated to Footprint']), name = 'FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES')
            mixed_volumes_subconfig = pd.Series((footprint_volumes * subconfig_volumes / vehghg_file_nonflexfuel['Total Footprint Volume Allocated to Subconfig']), name = 'SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES')
            mixed_volumes = pd.concat([mixed_volumes_footprint, mixed_volumes_subconfig],axis=1).reset_index(drop=True)
            mixed_volumes['FOOTPRINT_SUBCONFIG_VOLUMES'] = mixed_volumes[['FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES', 'SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES']].mean(axis=1)
            vehghg_file_nonflexfuel = pd.concat([vehghg_file_nonflexfuel, distributed_volumes, mixed_volumes],axis=1)

            vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='Vehghg_ID') + 1, \
                vehghg_file_nonflexfuel],axis=1)

            vehghg_file_flexfuel = vehghg_file[vehghg_file['FUEL_USAGE'] == 'E'].reset_index(drop=True)\
                .drop(['FINAL_MODEL_YR_GHG_PROD_UNITS', 'PROD_VOL_GHG_TOTAL_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE',\
                       'PRODUCTION_VOLUME_FE_50_STATE', 'PROD_VOL_GHG_TLAAS_50_STATE', 'PROD_VOL_GHG_STD_50_STATE'],axis=1)
            vehghg_file_flexfuel = pd.merge_ordered(vehghg_file_flexfuel, \
                vehghg_file_nonflexfuel[['Vehghg_ID', 'BodyID', 'FOOTPRINT_INDEX', 'CONFIG_INDEX','SUBCONFIG_INDEX', 'SS_ENGINE_FAMILY']], how='left', \
                on=['BodyID', 'FOOTPRINT_INDEX', 'CONFIG_INDEX','SUBCONFIG_INDEX', 'SS_ENGINE_FAMILY']).sort_values('Vehghg_ID').reset_index(drop=True)

            # vehghg_file_nonflexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()]\
            #     = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()].replace(np.nan,'none')
            # vehghg_file_flexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()]\
            #     = vehghg_file_flexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()].replace(np.nan,'none')
            vehghg_file_output = pd.merge_ordered(vehghg_file_nonflexfuel, vehghg_file_flexfuel, \
                how='outer', on=merging_columns+['Vehghg_ID']).sort_values('Vehghg_ID').reset_index(drop=True)
            # vehghg_file_output = vehghg_file_output.replace('none', np.nan)
            del vehghg_file
            vehghg_file_output = vehghg_file_output.loc[:,~vehghg_file_output.columns.str.contains('^Unnamed')]
            vehghg_file_output['Distributed Footprint Volumes'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0
            vehghg_file_output['Distributed Subconfig Volumes'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0
            vehghg_file_output['Total Subconfig Volume Allocated to Footprint'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0
            vehghg_file_output['Total Footprint Volume Allocated to Subconfig'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0
            vehghg_file_output['FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0
            vehghg_file_output['SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0
            vehghg_file_output['FOOTPRINT_SUBCONFIG_VOLUMES'][vehghg_file_output['FUEL_USAGE'] == 'E'] = 0


            vehghg_file_output['RLHP_FROM_RLCOEFFS'] = ((vehghg_file_output['TARGET_COEF_A']+(50*vehghg_file_output['TARGET_COEF_B']) \
                + ((50*50)*vehghg_file_output['TARGET_COEF_C']))*50*lbfmph2hp).replace(0,np.nan)
            v_aero_mph = 45
            air_density = 1.17 * kgpm32slugpft3
            vehghg_file_output['CDA_FROM_RLCOEFFS'] = pd.Series((vehghg_file_output['TARGET_COEF_B']+2*vehghg_file_output['TARGET_COEF_C']*v_aero_mph)\
                *ftps2mph/(air_density*v_aero_mph*mph2ftps)).replace(0,np.nan)
            vehghg_file_output['TOTAL_ROAD_LOAD_FORCE_50MPH'] = vehghg_file_output['RLHP_FROM_RLCOEFFS'] * hp2lbfmph *(1/50)
            vehghg_file_output['AERO_FORCE_50MPH']=0.5*air_density*vehghg_file_output['CDA_FROM_RLCOEFFS']*((50*mph2ftps)**2)
            vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'] = (vehghg_file_output['TOTAL_ROAD_LOAD_FORCE_50MPH'] - vehghg_file_output['AERO_FORCE_50MPH']).replace(0,np.nan)
            vehghg_file_output=vehghg_file_output.drop(['TOTAL_ROAD_LOAD_FORCE_50MPH', 'AERO_FORCE_50MPH'],axis=1)

            vehghg_file_output['FRONT_TIRE_RADIUS_IN'] = pd.Series(vehghg_file_output['FRONT_BASE_TIRE_CODE']).str.split( \
                'R').str.get(1).str.extract('(\d+)').astype(float)*0.5
            vehghg_file_output['REAR_TIRE_RADIUS_IN'] = pd.Series(vehghg_file_output['REAR_BASE_TIRE_CODE']).str.split( \
                'R').str.get(1).str.extract('(\d+)').astype(float)*0.5
            vehghg_file_output['TIRE_WIDTH_INS'] = pd.Series(vehghg_file_output['FRONT_BASE_TIRE_CODE']).str.split('/').str.get(
                0).str.extract('(\d+)').astype(float) / in2mm

            F_brake = 2 * (0.4 / (vehghg_file_output['FRONT_TIRE_RADIUS_IN'] * in2m)) * n2lbf + 2 * ( \
            0.4 / (vehghg_file_output['REAR_TIRE_RADIUS_IN'] * in2m)) * n2lbf
            rpm_front = 50 * mph2mps * (1 / (vehghg_file_output['FRONT_TIRE_RADIUS_IN'] * in2m)) * (60 / (2 * math.pi))
            rpm_rear = 50 * mph2mps * (1 / (vehghg_file_output['REAR_TIRE_RADIUS_IN'] * in2m)) * (60 / (2 * math.pi))
            F_hub = 2 * (((-2e-6 *rpm_front ** 2) + (.0023 *rpm_front + 1.2157)/(vehghg_file_output['FRONT_TIRE_RADIUS_IN']*in2m))*n2lbf) \
                + 2 * (((-2e-6 *rpm_rear ** 2) + (.0023 *rpm_rear + 1.2157)/(vehghg_file_output['REAR_TIRE_RADIUS_IN']*in2m))*n2lbf)
            F_drivetrain = 20 * n2lbf
            vehghg_file_output['ROLLING_FORCE_50MPH'] = vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS']-F_hub-F_brake-F_drivetrain
            vehghg_file_output['RRC_FROM_RLCOEFFS'] = (1000*vehghg_file_output['ROLLING_FORCE_50MPH']/vehghg_file_output['ETW']).replace(0,np.nan)
            vehghg_file_output = vehghg_file_output.drop(['ROLLING_FORCE_50MPH'],axis=1)
            vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS_NORMALIZED_BY_ETW'] = \
                vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS']/vehghg_file_output['ETW']
            vehghg_file_output['Transmission Short Name'] = pd.Series(vehghg_file_output['TRANS_TYPE'] + \
                vehghg_file_output['TOTAL_NUM_TRANS_GEARS'].astype(str)).replace('CVT1', 'CVT')

            vehghg_file_output['ROAD_LOAD_LABEL'] = pd.Series(vehghg_file_output['CALC_ID'].astype(float).astype(int).astype(str)+'_'\
            +vehghg_file_output['FOOTPRINT_CARLINE_NM']+'_'+vehghg_file_output['BodyID'].astype(str)+'_'\
            +vehghg_file_output['ENG_DISPL'].astype(str)+'_'+vehghg_file_output['Transmission Short Name']+'_'+\
            'Axle Ratio:(' + vehghg_file_output['AXLE_RATIO'].round(2).astype(str)+')'+'_'+\
            \
            'RLHP:(' + vehghg_file_output['RLHP_FROM_RLCOEFFS'].round(2).astype(str)+')'+'_'+\
            \
            'CDA:(' + vehghg_file_output['CDA_FROM_RLCOEFFS'].round(2).astype(str)+')'+'_'+ \
            \
            'Non-Aero:(' + vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'].round(2).astype(str) + ')'+'_'+\
            \
            'RRC:(' + vehghg_file_output['RRC_FROM_RLCOEFFS'].round(1).astype(str)+')'+'_'+\
            \
            vehghg_file_output['FRONT_BASE_TIRE_CODE']+'_'+\
            vehghg_file_output['ETW'].replace(np.nan,0).astype(float).round(0).astype(int).replace(0,'na').astype(str))

            vehghg_file_output.to_csv(output_path + '\\' + date_and_time + vehghg_filename, index=False)
        else:
            #New BodyID table sought, previous data included
            full_expanded_footprint_filter_table = full_expanded_footprint_filter_table.merge \
                (previous_filter_table[list(footprint_id_categories) + ['BodyID'] + ['POSSIBLE_BODYID']], how='left', \
                 on=list(footprint_id_categories) + ['BodyID'])
            #full_expanded_footprint_filter_table['POSSIBLE_BODYID']
            changed_lineageids = pd.Series(full_expanded_footprint_filter_table['LineageID'][pd.isnull(full_expanded_footprint_filter_table['POSSIBLE_BODYID'])]).unique()
            full_expanded_footprint_filter_table['POSSIBLE_BODYID'][full_expanded_footprint_filter_table['LineageID'].isin(changed_lineageids)] = np.nan
            full_filter_table_save_name = manual_filter_name + ' ' + date_and_time + '.csv'
            full_expanded_footprint_filter_table.to_csv(output_path.replace('\VehghgID', '\intermediate files') \
                                                        + '\\' + full_filter_table_save_name, index=False)