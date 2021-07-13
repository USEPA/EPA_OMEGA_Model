import pandas as pd
import datetime
import numpy as np

def file_errta_update(footprintSubconfigMY_file, errta_table, Column_Name, Old_Value, New_Value, MODEL_YEAR, CAFE_ID, MFR_DIVISION_NM, MFR_DIVISION_CD, MFR_CARLINE_CD, footprintSubconfig_INDEX):
    errta_table.loc[pd.isnull(errta_table[Old_Value]), Old_Value] = ''
    errta_table.loc[pd.isnull(errta_table[New_Value]), New_Value] = ''
    for error_check_count in range(0, len(errta_table)):
        # if error_check_count == 12:
        #     print(error_check_count)
        if ('[' and ']') in errta_table[Column_Name][error_check_count]:
            _column_name_list = eval(errta_table[Column_Name][error_check_count])
            _old_value_list = eval(errta_table[Old_Value][error_check_count])
            _new_value_list = eval(errta_table[New_Value][error_check_count])
        else:
            _column_name_list = _column_name = errta_table[Column_Name][error_check_count]
            # _old_value_list = errta_table[Old_Value][error_check_count]
            # _new_value_list = errta_table[New_Value][error_check_count]
        _num_column_name_list = 1
        if isinstance(_column_name_list, list): _num_column_name_list = len(_column_name_list)
            # _column_name_list = [elem.strip().split("',") for elem in _column_name_list]
        for i in range(_num_column_name_list):
            if _num_column_name_list > 1:
                errta_table.loc[error_check_count, Column_Name] = _column_name = _column_name_list[i]
                errta_table.loc[error_check_count, Old_Value] = _old_value_list[i]
                errta_table.loc[error_check_count, New_Value] = _new_value_list[i]
                # _column_name = str(_column_name_list[i]).strip("[]'")
            _column_name_isnull_list = pd.Series(pd.isnull(footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]]), name = _column_name)
            if sum(_column_name_isnull_list) > 0: footprintSubconfigMY_file.loc[_column_name_isnull_list, _column_name] = ''

            if errta_table['Numeric (y/n)'][error_check_count] == 'y':
                footprintSubconfigMY_file.loc[
                    (footprintSubconfigMY_file[MODEL_YEAR] == errta_table[MODEL_YEAR][error_check_count]) & \
                    (footprintSubconfigMY_file[CAFE_ID] == errta_table[CAFE_ID][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_NM] == errta_table[MFR_DIVISION_NM][ error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_CD] == errta_table[MFR_DIVISION_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_CARLINE_CD] == errta_table[MFR_CARLINE_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[footprintSubconfig_INDEX] == errta_table[footprintSubconfig_INDEX][error_check_count]) & \
                    (footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]] == float(errta_table[Old_Value][error_check_count])), \
                    errta_table.loc[error_check_count, Column_Name]] = errta_table[New_Value][error_check_count]
            else:
                footprintSubconfigMY_file.loc[
                    (footprintSubconfigMY_file[MODEL_YEAR] == errta_table[MODEL_YEAR][error_check_count]) & \
                    (footprintSubconfigMY_file[CAFE_ID] == errta_table[CAFE_ID][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_NM] == errta_table[MFR_DIVISION_NM][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_CD] == errta_table[MFR_DIVISION_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_CARLINE_CD] == errta_table[MFR_CARLINE_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[footprintSubconfig_INDEX] == errta_table[footprintSubconfig_INDEX][error_check_count]) & \
                    (footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]] == errta_table[Old_Value][error_check_count]), \
                    errta_table.loc[error_check_count, Column_Name]] = errta_table[New_Value][error_check_count]

    return footprintSubconfigMY_file

def check_final_model_yr_ghg_prod_units(data_chk_filename, vehghg_file_full_merged_data, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage):
    vehghg_file_full_merged_data_chk = vehghg_file_full_merged_data[
        vehghg_file_full_merged_data['SS_LD_CARLINE_HEADER_ID'] == vehghg_file_full_merged_data['LD_CARLINE_HEADER_ID']].reset_index(drop=True)
    vehghg_file_full_merged_data_chk = vehghg_file_full_merged_data_chk.dropna(subset=list(footprint_indexing_categories) + list(subconfig_indexing_categories), how='any').reset_index(drop=True)

    distributed_volumes_column_name = 'Distributed Volumes ' + data_chk_filename

    volumes_vehghg_file_full_merged_data_chk = vehghg_file_full_merged_data_chk['FINAL_MODEL_YR_GHG_PROD_UNITS'].replace(np.nan, 0).reset_index(drop=True)
    distributed_volumes_vehghg_file_full_merged_data_chk = pd.Series(volumes_vehghg_file_full_merged_data_chk / vehghg_file_full_merged_data_chk.groupby(
                                                                         subconfig_indexing_categories)['FINAL_MODEL_YR_GHG_PROD_UNITS'].transform(len), name=distributed_volumes_column_name)

    vehghg_file_full_merged_data_chk[distributed_volumes_column_name] = pd.Series(np.zeros(len(vehghg_file_full_merged_data_chk)))
    vehghg_file_full_merged_data_chk[distributed_volumes_column_name] = distributed_volumes_vehghg_file_full_merged_data_chk
    grp_vehghg_file_full_merged_data_chk = vehghg_file_full_merged_data_chk.groupby(['FOOTPRINT_MFR_CD']).sum().reset_index(drop=True)
    grp_volumes_vehghg_file_full_merged_data_chk = grp_vehghg_file_full_merged_data_chk[distributed_volumes_column_name]

    # print('data_chk_filename = ', data_chk_filename)
    print('total volumes = ', grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'].sum(),
          ' grp_volumes_' + data_chk_filename + ' @ merging = ', grp_volumes_vehghg_file_full_merged_data_chk.sum().round(0).astype(int))

    for i in range(min(len(grp_volumes_footprint_file_with_lineage), len(grp_vehghg_file_full_merged_data_chk))):
        if abs(grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'][i] - grp_volumes_vehghg_file_full_merged_data_chk[i].round(0).astype(int)) != 0:
            print(grp_volumes_footprint_file_with_lineage.index[i], grp_volumes_footprint_file_with_lineage[i], grp_volumes_vehghg_file_full_merged_data_chk[i].round(0).astype(int))

    delta_final_model_yr_ghg_prod_units = grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'].sum() - grp_volumes_vehghg_file_full_merged_data_chk.sum().round(0).astype(int)

    return delta_final_model_yr_ghg_prod_units

def Subconfig_ModelType_Footprint_Bodyid_Expansion(root_drive_letter, input_path, footprint_filename, footprint_lineage_filename, bodyid_filename, \
                                                   bool_run_new_manual_filter, manual_filter_name, expanded_footprint_filename, subconfig_filename, model_type_filename, vehghg_filename, output_path, \
                                                   footprint_exceptions_table, modeltype_exceptions_table, subconfig_MY_exceptions_table, subconfig_sales_exceptions_table, \
                                                   year, roadload_coefficient_table_filename, set_bodyid_to_lineageid, \
                                                   drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames, test_car_filename_path, set_roadload_coefficient_table_filename):
    footprint_file = pd.read_csv(input_path + '\\' + footprint_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
    lineage_file = pd.read_csv(input_path + '\\' + footprint_lineage_filename, encoding="ISO-8859-1")
    # body_id_table_readin = pd.read_excel(input_path + '\\' + bodyid_filename, converters={'LineageID': int, 'BodyID': int})
    body_id_table_readin = pd.read_csv(input_path + '\\' + bodyid_filename, na_values={''}, keep_default_na=False, encoding="ISO-8859-1")
    if set_bodyid_to_lineageid == 1: body_id_table_readin['BodyID'] = body_id_table_readin['LineageID']
    body_id_table_readin = body_id_table_readin[body_id_table_readin['BodyID EndYear'] != 'xx'].reset_index(drop=True)
    body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['BodyID EndYear'])) \
                                             & (body_id_table_readin['BodyID StartYear'] <= year)].reset_index(drop=True)
    body_id_int_not_null_endyear = body_id_table_int[
        ~body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
    body_id_int_not_null_endyear['BodyID EndYear'] = body_id_int_not_null_endyear['BodyID EndYear'].astype(float)
    body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['BodyID EndYear'] >= year], \
                               body_id_table_int[body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')]]).reset_index(drop=True)
    body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
    body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)

    footprint_file = footprint_file[footprint_file['MODEL_YEAR'] == year].reset_index(drop=True)
    lineage_file = lineage_file[lineage_file['MODEL_YEAR'] == year].reset_index(drop=True)
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '') .replace('-', '_').replace(' ', '_')

    footprint_indexing_categories = ['FOOTPRINT_DIVISION_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_INDEX']
    subconfig_indexing_categories = ['MFR_DIVISION_NM', 'MODEL_TYPE_INDEX', 'SS_ENGINE_FAMILY', 'CARLINE_CODE',
                                     'LDFE_CAFE_ID', 'BASE_LEVEL_INDEX', 'CONFIG_INDEX', 'SUBCONFIG_INDEX']
    modeltype_indexing_categories = ['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'CAFE_MODEL_YEAR', 'CARLINE_MFR_CODE', 'MFR_DIVISION_NM', 'CALC_ID', 'CAFE_ID', 'CARLINE_NAME']
    roadload_coefficient_table_indexing_categories = ['LDFE_CAFE_SUBCONFIG_INFO_ID', 'LDFE_CAFE_ID', 'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'CAFE_MFR_CD', \
                                                      'LABEL_MFR_CD', 'MODEL_TYPE_INDEX', 'MFR_DIVISION_SHORT_NM', 'CARLINE_NAME', \
                                                      'INERTIA_WT_CLASS', 'CONFIG_INDEX', 'SUBCONFIG_INDEX', 'TRANS_TYPE', 'HYBRID_YN']
    CAFE_ID_not_matched = []
    for i in range(len(footprint_file['FOOTPRINT_DIVISION_NM'])):
        for j in range(len(lineage_file['FOOTPRINT_DIVISION_NM'])):
            if (footprint_file['FOOTPRINT_DIVISION_NM'][i] == lineage_file['FOOTPRINT_DIVISION_NM'][j]) and (footprint_file['FOOTPRINT_INDEX'][i] == lineage_file['FOOTPRINT_INDEX'][j]) and \
                    (footprint_file['FOOTPRINT_CARLINE_CD'][i] == lineage_file['FOOTPRINT_CARLINE_CD'][j]) and \
                    (footprint_file['FOOTPRINT_CARLINE_NM'][i] == lineage_file['FOOTPRINT_CARLINE_NM'][j]) and (footprint_file['CAFE_ID'][i] != lineage_file['CAFE_ID'][j]):

                CAFE_ID_not_matched.append([footprint_file.loc[i, 'MODEL_YEAR'], footprint_file.loc[i, 'FOOTPRINT_DIVISION_NM'], footprint_file.loc[i, 'FOOTPRINT_CARLINE_NM'], footprint_file.loc[i, 'FOOTPRINT_INDEX'], \
                     footprint_file.loc[i, 'CAFE_ID'], lineage_file.loc[j, 'CAFE_ID']])
                # lineage_file.loc[j, 'CAFE_ID'] = footprint_file.loc[i, 'CAFE_ID']
    if len(CAFE_ID_not_matched) > 0:
        df_CAFE_ID_not_matched = pd.DataFrame(CAFE_ID_not_matched, columns=['MODEL_YEAR', 'FOOTPRINT_DIVISION_NM', 'FOOTPRINT_CARLINE_NM', 'FOOTPRINT_INDEX', 'Footprint_MY_CAFE_ID', 'footprint-lineageid_CAFE_ID'])
        df_CAFE_ID_not_matched.to_csv(output_path + '\\' + 'CAFE_ID_lineageid_neq_Footprint_MY' + '_' + date_and_time + '.csv', index=False)

    if len(footprint_exceptions_table) > 0:
        footprint_file = file_errta_update(footprint_file, footprint_exceptions_table, 'Column Name', 'Old Value', 'New Value', 'MODEL_YEAR', 'CAFE_ID', 'FOOTPRINT_DIVISION_NM', \
                                           'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_INDEX')
        footprint_file.to_csv(output_path+'\\'+'Corrected_Footprint_MY_file' + '_' + date_and_time + '.csv', index=False)
        print('footprint_file volumes = ', footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum())

    footprint_id_categories = ['MODEL_YEAR', 'FOOTPRINT_INDEX', 'CAFE_ID', 'FOOTPRINT_CARLINE_CD',
                               'FOOTPRINT_CARLINE_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_DIVISION_NM']
    footprint_filter_table = footprint_file[
        list(footprint_id_categories) + ['WHEEL_BASE_INCHES'] + ['FOOTPRINT_DESC'] + ['PROD_VOL_GHG_STD_50_STATE']].merge(
        lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_id_categories)
    footprint_filter_table = footprint_filter_table.loc[~pd.isnull(footprint_filter_table['LineageID']), :].reset_index(drop=True)

    footprint_file_with_lineage = footprint_file.merge(lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_id_categories)
    footprint_file_with_lineage = footprint_file_with_lineage.loc[~pd.isnull(footprint_file_with_lineage['LineageID']), :].reset_index(drop=True)

    print('total footprint_file volumes = ', footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum())
    print('total footprint_filter_table volumes = ', footprint_filter_table['PROD_VOL_GHG_STD_50_STATE'].sum())
    print('total footprint_file_with_lineage volumes = ', footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'].sum())
    grp_volumes_footprint_file = footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()
    grp_volumes_footprint_file_with_lineage = footprint_file_with_lineage.groupby(['FOOTPRINT_MFR_CD']).sum()
    for i in range(min(len(grp_volumes_footprint_file), len(grp_volumes_footprint_file_with_lineage))):
        if grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0) != grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'][i].round(0):
            print(grp_volumes_footprint_file.index[i], grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'][i])

    full_expanded_footprint_filter_table = footprint_filter_table.merge(body_id_table, how='left', on='LineageID')
    full_expanded_footprint_file = footprint_file_with_lineage.merge(body_id_table, how='left', on='LineageID')
    try:
        # BodyID table is found, no new manual filter sought
        previous_filter_table = pd.read_csv(input_path + '\\' + manual_filter_name, encoding="ISO-8859-1")
        previous_filter_table = previous_filter_table[previous_filter_table['MODEL_YEAR'] == year].reset_index(drop=True)
    except OSError:
        # New BodyID table to be made, no previous data
        full_filter_table_save_name = manual_filter_name.replace('.csv', '') + ' ' + date_and_time + '.csv'
        full_expanded_footprint_filter_table.to_csv(output_path.replace('\VehghgID', '\intermediate files') + '\\' + full_filter_table_save_name, index=False)
    else:
        if bool_run_new_manual_filter == 'n':
            import math
            from Unit_Conversion import hp2lbfmph, kgpm32slugpft3, mph2ftps, in2m, n2lbf, mph2mps, btu2mj, kg2lbm, \
                ftps2mph, lbfmph2hp, in2mm

            full_expanded_footprint_file = full_expanded_footprint_file.merge(previous_filter_table[list(footprint_id_categories) + ['BodyID'] + ['POSSIBLE_BODYID']], \
                how='left', on=list(footprint_id_categories) + ['BodyID'])
            # full_expanded_footprint_file_bodyIDn = full_expanded_footprint_file.loc[full_expanded_footprint_file['POSSIBLE_BODYID'] != 'y', :].reset_index(drop=True)
            # full_expanded_footprint_file_bodyIDn.to_csv(output_path + '\\' + 'full_expanded_footprint_file_bodyIDn' + '_' + date_and_time + '.csv', index=False)
            full_expanded_footprint_file = full_expanded_footprint_file[full_expanded_footprint_file['POSSIBLE_BODYID'] == 'y'].reset_index(drop=True)

            grp_volumes_footprint_file = footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()
            grp_volumes_full_expanded_footprint_file = full_expanded_footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()
            print('full_expanded_footprint_file volumes = ', grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum())
            for i in range(min(len(grp_volumes_footprint_file), len(grp_volumes_full_expanded_footprint_file))):
                if (grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0) != grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0)):
                    print(grp_volumes_footprint_file.index[i], grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], \
                          (grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i] - grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i]))

            subconfig_file = pd.read_csv(input_path + '\\' + subconfig_filename, encoding="ISO-8859-1", na_values=['-'])  # subconfig_sales # EVCIS Qlik Sense query results contain hyphens for nan
            subconfig_file = subconfig_file[subconfig_file['MODEL_YEAR'] == year].reset_index(drop=True)
            model_type_file = pd.read_csv(input_path + '\\' + model_type_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan)
            model_type_file = model_type_file[model_type_file['CAFE_MODEL_YEAR'] == year].reset_index(drop=True)

            if len(modeltype_exceptions_table) > 0:
                model_type_file = file_errta_update(model_type_file, modeltype_exceptions_table, 'Column Name', 'Old Value', 'New Value', 'CAFE_MODEL_YEAR', 'CAFE_ID', 'MODEL_TYPE_INDEX', \
                                                    'MFR_DIVISION_NM', 'CARLINE_NAME', 'CAFE_MODEL_YEAR')
                model_type_file['CALC_ID'] = model_type_file['CALC_ID'].astype(int)
                model_type_file.to_csv(output_path+'\\'+'Corrected_CAFE_Model_Type_MY_file'+ '_' + date_and_time + '.csv', index=False)

            if len(subconfig_sales_exceptions_table) > 0:
                subconfig_file = file_errta_update(subconfig_file, subconfig_sales_exceptions_table, 'Column Name', 'Old Value', 'New Value', 'MODEL_YEAR', 'LDFE_CAFE_ID', 'MODEL_TYPE_INDEX', \
                                                   'MFR_DIVISION_SHORT_NM', 'CARLINE_NAME', 'MODEL_YEAR')
                subconfig_file['LDFE_CAFE_MODEL_TYPE_CALC_ID'] = subconfig_file['LDFE_CAFE_MODEL_TYPE_CALC_ID'].astype(int)
                subconfig_file.to_csv(output_path+'\\'+'Corrected_CAFE_Subconfig_Sales_MY_file'+ '_' + date_and_time + '.csv', index=False)
                # subconfig_file_S209 = subconfig_file[subconfig_file['CARLINE_NAME'] == 'S209']
            vehghg_file_data_pt1 = subconfig_file.merge(full_expanded_footprint_file, how='left', \
                                                        left_on=['MODEL_YEAR', 'CARLINE_CODE', 'CAFE_MFR_CD', 'MFR_DIVISION_NM'], \
                                                        right_on=['MODEL_YEAR', 'FOOTPRINT_CARLINE_CD', 'CAFE_MFR_CD', 'FOOTPRINT_DIVISION_NM'])
            # vehghg_file_data_pt1_S209 = vehghg_file_data_pt1[vehghg_file_data_pt1['CARLINE_NAME'] == 'S209']

            vehghg_file_full_merged_data = vehghg_file_data_pt1.merge(model_type_file, how='left', left_on=['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'MODEL_YEAR', 'CAFE_MFR_CD', 'MFR_DIVISION_NM', \
                                                                               'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'CAFE_ID', 'CARLINE_NAME'], right_on=modeltype_indexing_categories)
            check_final_model_yr_ghg_prod_units('vehghg_file_full_merged_data', vehghg_file_full_merged_data, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            vehghg_file_data = vehghg_file_full_merged_data[vehghg_file_full_merged_data['SS_LD_CARLINE_HEADER_ID'] == vehghg_file_full_merged_data['LD_CARLINE_HEADER_ID']].reset_index(drop=True)
            vehghg_file = vehghg_file_data.dropna(subset=list(footprint_indexing_categories) + list(subconfig_indexing_categories), how='any').reset_index(drop=True)
            check_final_model_yr_ghg_prod_units('vehghg_file', vehghg_file, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            # vehghg_file.loc[pd.isnull(vehghg_file['TOTAL_NUM_TRANS_GEARS']), 'TOTAL_NUM_TRANS_GEARS'] = 1
            missing_entries_1 = vehghg_file[pd.isnull(vehghg_file['LineageID'])].reset_index(drop=True)
            # missing_entries_2 = vehghg_file[pd.isnull(vehghg_file['TOTAL_NUM_TRANS_GEARS'])].reset_index(drop=True)
            # missing_entries = pd.concat([missing_entries_1, missing_entries_2]).reset_index(drop=True)
            missing_entries = pd.concat([missing_entries_1]).reset_index(drop=True)
            if len(missing_entries) > 0:
                try:
                    missing_entries.to_csv(output_path + '\\' + vehghg_filename.replace('.csv', '') + '_Missing Entries.csv', index=False)
                except OSError:
                    pass
            # vehghg_file = vehghg_file[(~pd.isnull(vehghg_file['LineageID'])) & (~pd.isnull(vehghg_file['TOTAL_NUM_TRANS_GEARS']))].reset_index(drop=True)
            vehghg_file = vehghg_file.loc[:, ~vehghg_file.columns.str.contains('^Unnamed')]
            vehghg_file = vehghg_file.loc[:, ~vehghg_file.columns.duplicated()]

            matching_cyl_layout = pd.Series(np.zeros(len(vehghg_file)), name='Cylinder Layout Category').replace(0, '').astype(str)
            matching_cyl_layout[~pd.isnull(vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'])] = \
                vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'][~pd.isnull(vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'])]
            matching_cyl_layout[pd.isnull(vehghg_file['ENG_BLOCK_ARRANGEMENT_CD'])] = 'ELE'

            matching_cyl_num = pd.Series(np.zeros(len(vehghg_file)), name='Number of Cylinders Category')
            matching_cyl_num[~pd.isnull(vehghg_file['NUM_CYLINDRS_ROTORS'])] = vehghg_file['NUM_CYLINDRS_ROTORS'] \
                [~pd.isnull(vehghg_file['NUM_CYLINDRS_ROTORS'])].astype(float).astype(int)
            matching_cyl_num[pd.isnull(vehghg_file['NUM_CYLINDRS_ROTORS'])] = 0
            matching_cyl_num = matching_cyl_num.astype(int)

            matching_eng_disp = pd.Series(np.zeros(len(vehghg_file)), name='Engine Displacement Category')
            matching_eng_disp[~pd.isnull(vehghg_file['ENG_DISPL'])] = vehghg_file['ENG_DISPL'] \
                [~pd.isnull(vehghg_file['ENG_DISPL'])].astype(float).round(1)
            matching_eng_disp[pd.isnull(vehghg_file['ENG_DISPL'])] = int(0)

            matching_drvtrn_layout = pd.Series(vehghg_file['DRV_SYS'], name='Drivetrain Layout Category').astype(
                str).replace(['F', 'R'], '2WD').replace(['A', '4'], '4WD').replace('P', '2WD')

            matching_trns_numgears = pd.Series(vehghg_file['TOTAL_NUM_TRANS_GEARS'].astype(float), name='Number of Transmission Gears Category')
            matching_trns_numgears[vehghg_file['TRANS_TYPE'] == 'SCV'] = 1
            matching_trns_category = pd.Series(vehghg_file['TRANS_TYPE'], name='Transmission Type Category').replace(['AMS', 'SA', 'SCV'], ['AM', 'A', 'CVT'])
            matching_trns_category[matching_trns_numgears == 1] = '1ST'
            matching_trns_category[(matching_trns_category == 'OT') & vehghg_file['TRANS_TYPE_IF_OTHER'].str.contains('Automated Manual')] = 'AM'
            matching_trns_category[(matching_trns_category == 'OT') & vehghg_file['TRANS_TYPE_IF_OTHER'].str.contains('Automatic Manual')] = 'AM'
            matching_boost_category = pd.Series(vehghg_file['AIR_ASP'], name='Boost Type Category').astype(str).str.upper().replace(['NA', 'NAN'], 'N')
            matching_boost_category[vehghg_file['FUEL_USAGE'] == 'EL'] = 'ELE'
            matching_boost_category[vehghg_file['FUEL_USAGE'] == 'H'] = 'ELE'
            matching_mfr_category = pd.Series(vehghg_file['MFR_DIVISION_NM'], name='Make Category').astype(str) \
                .str.split().str.get(0).str.upper().str.replace('Aston'.upper(), 'Aston Martin'.upper()) \
                .str.replace('Land'.upper(), 'Land Rover'.upper()).str.replace('Alfa'.upper(), 'Alfa Romeo'.upper()).replace(
                'Electric'.upper(), 'BYD').replace('The'.upper(), 'MV-1').replace('Fisker'.upper(), 'Fisker Karma'.upper()).str.strip()
            matching_fuel_category = pd.Series(vehghg_file['FUEL_USAGE'].astype(str).str[0], name='Fuel Type Category').replace(['H', 'C', 'L'], ['E', 'CNG', 'LPG'])
            matching_fuel_category[vehghg_file['FUEL_USAGE'] == 'EL'] = 'E'
            matching_fuel_category[vehghg_file['FUEL_USAGE'] == 'E'] = 'Eth'
            matching_electrification = pd.Series(np.zeros(len(vehghg_file)), name='Electrification Category').replace(0, 'N')
            matching_electrification[(vehghg_file['HYBRID_YN'] == 'Y') & (vehghg_file['OFF_BOARD_CHARGE_CAPABLE_YN'] == 'Y')] = 'PHEV'
            matching_electrification[(vehghg_file['HYBRID_YN'] == 'N') & (vehghg_file['OFF_BOARD_CHARGE_CAPABLE_YN'] == 'Y')] = 'EV'
            matching_electrification[(vehghg_file['HYBRID_YN'] == 'Y') & (vehghg_file['OFF_BOARD_CHARGE_CAPABLE_YN'] == 'N')] = 'HEV'
            matching_electrification[vehghg_file['FUEL_USAGE'] == 'H'] = 'FCV'

            vehghg_file = pd.concat([vehghg_file, matching_cyl_layout, matching_cyl_num, \
                                     matching_eng_disp, matching_drvtrn_layout, matching_trns_category, \
                                     matching_trns_numgears, matching_boost_category, matching_mfr_category, \
                                     matching_fuel_category, matching_electrification], axis=1).reset_index(drop=True)
            vehghg_file = vehghg_file.dropna(subset=list(['LineageID', 'BodyID']), how='any').reset_index(drop=True)
            vehghg_file['LineageID'] = vehghg_file['LineageID'].astype(int)
            vehghg_file['BodyID'] = vehghg_file['BodyID'].astype(int)
            vehghg_file_nonflexfuel = vehghg_file  # [vehghg_file['FUEL_USAGE'] != 'E'].reset_index(drop=True)

            check_final_model_yr_ghg_prod_units('vehghg_file', vehghg_file, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            model_type_volumes = model_type_file[['CALC_ID', 'PRODUCTION_VOLUME_FE_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE']].groupby('CALC_ID').sum().reset_index()
            vehghg_file_nonflexfuel = pd.merge_ordered(vehghg_file_nonflexfuel.drop( \
                ['PRODUCTION_VOLUME_FE_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE'], axis=1), model_type_volumes, how='left', on='CALC_ID').reset_index(drop=True)
            merging_columns = list(vehghg_file_nonflexfuel.drop(['FINAL_MODEL_YR_GHG_PROD_UNITS', \
                                                                 'PROD_VOL_GHG_TOTAL_50_STATE',
                                                                 'PRODUCTION_VOLUME_GHG_50_STATE', \
                                                                 'PRODUCTION_VOLUME_FE_50_STATE',
                                                                 'PROD_VOL_GHG_TLAAS_50_STATE',
                                                                 'PROD_VOL_GHG_STD_50_STATE'], axis=1).columns)
            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[:, ~vehghg_file_nonflexfuel.columns.duplicated()]

            roadload_coefficient_table = pd.read_csv(input_path + '\\' + roadload_coefficient_table_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
            if len(subconfig_MY_exceptions_table) > 0:
                roadload_coefficient_table = file_errta_update(roadload_coefficient_table, subconfig_MY_exceptions_table, 'Column Name', 'Old Value', 'New Value', 'MODEL_YEAR', 'LDFE_CAFE_ID', \
                                                               'MODEL_TYPE_INDEX', 'MFR_DIVISION_SHORT_NM', 'CARLINE_NAME', 'MODEL_YEAR')
                roadload_coefficient_table['LDFE_CAFE_MODEL_TYPE_CALC_ID'] = roadload_coefficient_table['LDFE_CAFE_MODEL_TYPE_CALC_ID'].astype(int)
                roadload_coefficient_table.to_csv(output_path+'\\'+'Corrected_CAFE_Subconfig_MY_file' + '_' + date_and_time + '.csv', index=False)

            roadload_coefficient_table = roadload_coefficient_table[roadload_coefficient_table['MODEL_YEAR'] == year].groupby(['LDFE_CAFE_SUBCONFIG_INFO_ID', 'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', \
                          'FUEL_NET_HEATING_VALUE', 'FUEL_GRAVITY']).first().reset_index().drop('MODEL_YEAR', axis=1).reset_index(drop=True)
            # roadload_coefficient_table_flexfuel = roadload_coefficient_table[roadload_coefficient_table['SUBCFG_FUEL_USAGE'] == 'E'].reset_index(drop=True)
            roadload_coefficient_table_nonflexfuel = roadload_coefficient_table[roadload_coefficient_table['SUBCFG_FUEL_USAGE'] != 'E'].reset_index(drop=True)
            # roadload_coefficient_table_nonflexfuel = roadload_coefficient_table_nonflexfuel.rename({'SUBCFG_FUEL_USAGE':'FUEL_USAGE'}, axis=1)
            vehghg_file_flexfuel = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['FUEL_USAGE'] == 'E'].reset_index(drop=True)
            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['FUEL_USAGE'] != 'E'].reset_index(drop=True)
            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.merge(roadload_coefficient_table_nonflexfuel, how='left', on=list(roadload_coefficient_table_indexing_categories))
            vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'] = pd.Series(
                vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE'].astype(float) * vehghg_file_nonflexfuel['FUEL_GRAVITY'].astype(float) * btu2mj * kg2lbm)
            check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            set_roadload_coefficient_table_indexing_categories = ['Model Year', 'Veh Mfr Code', 'Represented Test Veh Model', 'Test Vehicle ID', 'Test Veh Configuration #', 'Test Number', \
                                                                  'Test Category', 'Equivalent Test Weight (lbs.)', 'Test Veh Displacement (L)', 'Actual Tested Testgroup', '# of Gears', 'Drive System Code', 'N/V Ratio', \
                                                                  'CO2 (g/mi)', 'RND_ADJ_FE', 'FE Bag 1', 'FE Bag 2', 'FE Bag 3', \
                                                                  'Target Coef A (lbf)', 'Target Coef B (lbf/mph)', 'Target Coef C (lbf/mph**2)', \
                                                                  'Set Coef A (lbf)', 'Set Coef B (lbf/mph)', 'Set Coef C (lbf/mph**2)']
            set_roadload_coefficient_table = pd.read_csv(root_drive_letter + test_car_filename_path + '\\' + set_roadload_coefficient_table_filename, encoding="ISO-8859-1", na_values=['-'])
            set_roadload_coefficient_table = set_roadload_coefficient_table[set_roadload_coefficient_table_indexing_categories]
            set_roadload_coefficient_table = set_roadload_coefficient_table.rename({'Set Coef A (lbf)': 'SET_COEF_A', 'Set Coef B (lbf/mph)': 'SET_COEF_B', 'Set Coef C (lbf/mph**2)': 'SET_COEF_C'}, axis=1)

            vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_A'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_B_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_B'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_C_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_C'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'] = pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['TARGET_COEF_B_SURRO'] = pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['TARGET_COEF_C_SURRO'] = pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] =  pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'])), 'TARGET_COEF_BEST_MTH'] = np.nan
            vehghg_file_nonflexfuel['TOT_ROAD_LOAD_HP_SURRO'] = vehghg_file_nonflexfuel['TOT_ROAD_LOAD_HP'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'] = vehghg_file_nonflexfuel['TARGET_COEF_B_SURRO'] = vehghg_file_nonflexfuel['TARGET_COEF_C_SURRO'] = np.nan

            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.merge(set_roadload_coefficient_table, how='left',
                                                                    left_on=['CAFE_MFR_CD', 'TEST_NUMBER', 'TEST_PROC_CATEGORY'], right_on=['Veh Mfr Code', 'Test Number', 'Test Category'])
            vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['NV_RATIO'])) & (~pd.isnull(vehghg_file_nonflexfuel['N/V Ratio'])), 'NV_RATIO'] = vehghg_file_nonflexfuel['N/V Ratio']
            vehghg_file_nonflexfuel['SET_COEF_A_BEST'] = vehghg_file_nonflexfuel['SET_COEF_A_SURRO'] = vehghg_file_nonflexfuel['SET_COEF_A'].copy()
            vehghg_file_nonflexfuel['SET_COEF_B_BEST'] = vehghg_file_nonflexfuel['SET_COEF_B_SURRO'] = vehghg_file_nonflexfuel['SET_COEF_B'].copy()
            vehghg_file_nonflexfuel['SET_COEF_C_BEST'] = vehghg_file_nonflexfuel['SET_COEF_C_SURRO'] = vehghg_file_nonflexfuel['SET_COEF_C'].copy()
            vehghg_file_nonflexfuel['NV_RATIO_BEST'] = vehghg_file_nonflexfuel['NV_RATIO_SURRO'] = vehghg_file_nonflexfuel['NV_RATIO'].copy()

            _target_coef_from_set_roadload_coefficient_table = (~pd.isnull(vehghg_file_nonflexfuel['SET_COEF_A']) | ~pd.isnull(vehghg_file_nonflexfuel['SET_COEF_B']) | ~pd.isnull(vehghg_file_nonflexfuel['SET_COEF_C'])) & \
                                                               (pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A']))
            _target_coef_from_engine_family_etw = (vehghg_file_nonflexfuel['CAFE_MFR_CD'] == vehghg_file_nonflexfuel['Veh Mfr Code']) & \
                                                  (vehghg_file_nonflexfuel['Actual Tested Testgroup'] == vehghg_file_nonflexfuel['SS_ENGINE_FAMILY']) & \
                                                  (vehghg_file_nonflexfuel['ETW'] == vehghg_file_nonflexfuel['Equivalent Test Weight (lbs.)']) & (pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A']))
            # print((~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A'])).sum())
            if (_target_coef_from_set_roadload_coefficient_table.sum() > 0) or (_target_coef_from_engine_family_etw.sum() > 0):
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_BEST_MTH'] = 3
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_A'] = vehghg_file_nonflexfuel['Target Coef A (lbf)']
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_B'] = vehghg_file_nonflexfuel['Target Coef B (lbf/mph)']
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_C'] = vehghg_file_nonflexfuel['Target Coef C (lbf/mph**2)']
                vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[:, ~vehghg_file_nonflexfuel.columns.duplicated()]
                vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_A']
                vehghg_file_nonflexfuel['TARGET_COEF_B_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_B']
                vehghg_file_nonflexfuel['TARGET_COEF_C_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_C']
                vehghg_file_nonflexfuel['SET_COEF_A_BEST'] = vehghg_file_nonflexfuel['SET_COEF_A']
                vehghg_file_nonflexfuel['SET_COEF_B_BEST'] = vehghg_file_nonflexfuel['SET_COEF_B']
                vehghg_file_nonflexfuel['SET_COEF_C_BEST'] = vehghg_file_nonflexfuel['SET_COEF_C']
                vehghg_file_nonflexfuel['NV_RATIO_BEST'] = vehghg_file_nonflexfuel['N/V Ratio']

            vehghg_file_nonflexfuel.loc[pd.isnull(vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_GHG_1']) & (vehghg_file_nonflexfuel['Electrification Category'] != 'EV') & \
                                        (vehghg_file_nonflexfuel['Electrification Category'] != 'FCV') & (vehghg_file_nonflexfuel['CO2 (g/mi)'] > 0), 'EPA_CAFE_MT_CALC_COMB_GHG_1'] = vehghg_file_nonflexfuel['CO2 (g/mi)']
            print('# of TARGET_COEF_A', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A'])).sum())
            print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())

            _target_coef_indexing_category = ['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'MFR_DIVISION_SHORT_NM', 'CARLINE_NAME', 'SS_ENGINE_FAMILY', 'ETW', 'BodyID', 'TOT_ROAD_LOAD_HP', 'VEH_TOT_ROAD_LOAD_HP', \
                                              'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', 'NV_RATIO', 'SET_COEF_A', 'SET_COEF_B', 'SET_COEF_C']
            _target_coef_surro_indexing_category = ['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'CARLINE_NAME', 'SS_ENGINE_FAMILY', 'ETW', 'BodyID', 'VEH_TOT_ROAD_LOAD_HP', 'TOT_ROAD_LOAD_HP', \
                                                    'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', 'NV_RATIO', 'TARGET_COEF_BEST_MTH', 'TARGET_COEF_A_SURRO', 'TARGET_COEF_B_SURRO', 'TARGET_COEF_C_SURRO', \
                                                    'SET_COEF_A', 'SET_COEF_B', 'SET_COEF_C', 'SET_COEF_A_SURRO', 'SET_COEF_B_SURRO', 'SET_COEF_C_SURRO']
            df_Cafe_MFR_CD_Mode_Type_Index = vehghg_file_nonflexfuel[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A']))].groupby(['CAFE_MFR_CD', 'MODEL_TYPE_INDEX']).mean()
            for i in range(len(df_Cafe_MFR_CD_Mode_Type_Index)):
                _cafe_mfr_cd = df_Cafe_MFR_CD_Mode_Type_Index.index[i][0]
                _model_type_index = df_Cafe_MFR_CD_Mode_Type_Index.index[i][1]
                df_vehghg_file_nonflexfuel_target_coef = vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A'])) & (vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & \
                                                                                     (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index), _target_coef_indexing_category]
                df_vehghg_file_nonflexfuel_target_coef_index = list(df_vehghg_file_nonflexfuel_target_coef.index)
                df_vehghg_file_nonflexfuel_target_coef.reset_index(drop=True, inplace=True)
                for k in range (len(df_vehghg_file_nonflexfuel_target_coef)):
                    _tot_road_load_hp = df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TOT_ROAD_LOAD_HP']
                    df_sort = df_vehghg_file_nonflexfuel_target_coef.iloc[(df_vehghg_file_nonflexfuel_target_coef['VEH_TOT_ROAD_LOAD_HP'] - _tot_road_load_hp).abs().argsort()[:1]]
                    _index_df_sort = df_sort.index.tolist()[0]
                    _index_vehghg_file_nonflexfuel = df_vehghg_file_nonflexfuel_target_coef_index[k]
                    if pd.isnull(vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_A_SURRO']):
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'NV_RATIO_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'NV_RATIO']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_A']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_B']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_C']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'SET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'SET_COEF_A']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'SET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'SET_COEF_B']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'SET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'SET_COEF_C']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TOT_ROAD_LOAD_HP_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TOT_ROAD_LOAD_HP']
                        vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_BEST_MTH'] = 1

            del df_Cafe_MFR_CD_Mode_Type_Index, df_vehghg_file_nonflexfuel_target_coef, df_vehghg_file_nonflexfuel_target_coef_index
            print('# of TARGET_COEF_BEST_MTH = 1 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 1]), ')')
            print('# of TARGET_COEF_A', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A'])).sum())
            print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())

            df_Cafe_MFR_CD_Mode_Type_Index = vehghg_file_nonflexfuel[(pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A']))].groupby(['CAFE_MFR_CD', 'MODEL_TYPE_INDEX']).mean()
            for i in range(len(df_Cafe_MFR_CD_Mode_Type_Index)):
                _cafe_mfr_cd = df_Cafe_MFR_CD_Mode_Type_Index.index[i][0]
                _model_type_index = df_Cafe_MFR_CD_Mode_Type_Index.index[i][1]
                if _cafe_mfr_cd == 'NSX' and _model_type_index == 591:
                    print(_cafe_mfr_cd, _model_type_index)
                _bodyid = vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index), 'BodyID'].unique()
                _engine_family = vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index), 'SS_ENGINE_FAMILY'].unique()
                _etw = vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index), 'ETW'].unique()
                if len(_engine_family) == 0:
                    print('no _engine_family @ ', _cafe_mfr_cd, _model_type_index)
                    continue
                for j in range (len(_bodyid)):
                    _bodyid_j = _bodyid[j]
                    for j1 in range(len(_engine_family)):
                        _engine_family_j1 = _engine_family[j1]
                        for l in range (len(_etw)):
                            _etw_l = _etw[l]
                            df_vehghg_file_nonflexfuel_target_coef = \
                                vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index) & \
                                                            (vehghg_file_nonflexfuel['SS_ENGINE_FAMILY'] == _engine_family_j1) & (vehghg_file_nonflexfuel['ETW'] == _etw_l) & \
                                                            (vehghg_file_nonflexfuel['BodyID'] == _bodyid_j), _target_coef_surro_indexing_category]
                            if len(df_vehghg_file_nonflexfuel_target_coef) == 0: continue
                            if (len(df_vehghg_file_nonflexfuel_target_coef.loc[~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['TARGET_COEF_A']), 'TARGET_COEF_A']) == 0): # exclude etw
                                df_vehghg_file_nonflexfuel_target_coef = \
                                    vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index) & \
                                        (vehghg_file_nonflexfuel['SS_ENGINE_FAMILY'] == _engine_family_j1) & (vehghg_file_nonflexfuel['BodyID'] == _bodyid_j), _target_coef_surro_indexing_category]
                                if len(df_vehghg_file_nonflexfuel_target_coef) == 0: continue
                            df_vehghg_file_nonflexfuel_target_coef_index = list(df_vehghg_file_nonflexfuel_target_coef.index)
                            df_vehghg_file_nonflexfuel_target_coef.reset_index(drop=True, inplace=True)
                            for k in range (len(df_vehghg_file_nonflexfuel_target_coef)):
                                if df_vehghg_file_nonflexfuel_target_coef.loc[k, 'CARLINE_NAME'] == 'FRONTIER 4WD':
                                    print(df_vehghg_file_nonflexfuel_target_coef.loc[k, 'VEH_TOT_ROAD_LOAD_HP'])
                                df_vehghg_file_nonflexfuel_target_coef_RL = df_vehghg_file_nonflexfuel_target_coef.loc[(~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['TARGET_COEF_A'])) & \
                                                                                                                       (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['VEH_TOT_ROAD_LOAD_HP'])), _target_coef_surro_indexing_category]
                                if len(df_vehghg_file_nonflexfuel_target_coef_RL) == 0: continue
                                df_vehghg_file_nonflexfuel_target_coef_RL.reset_index(drop=True, inplace=True)
                                if (pd.isnull(df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_A_SURRO']) == False) or \
                                        (((df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_BEST_MTH'] == 1) | \
                                          (df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_BEST_MTH'] == 1)) & (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_A']))):
                                    continue
                                df_sort = df_vehghg_file_nonflexfuel_target_coef_RL.iloc[(df_vehghg_file_nonflexfuel_target_coef_RL['VEH_TOT_ROAD_LOAD_HP']-df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TOT_ROAD_LOAD_HP']).abs().argsort()[:1]]
                                _index_df_sort = df_sort.index.tolist()[0]
                                _index_vehghg_file_nonflexfuel = df_vehghg_file_nonflexfuel_target_coef_index[k]
                                if _index_df_sort >= len(df_vehghg_file_nonflexfuel_target_coef_RL):
                                    print('_index_df_sort is greater than length of the array', k, _index_df_sort)
                                    continue
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'NV_RATIO_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'NV_RATIO']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TARGET_COEF_A']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TARGET_COEF_B']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TARGET_COEF_C']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'SET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'SET_COEF_A']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'SET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'SET_COEF_B']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'SET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'SET_COEF_C']
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TOT_ROAD_LOAD_HP_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TOT_ROAD_LOAD_HP']
                                if vehghg_file_nonflexfuel.loc[_index_df_sort, 'TOT_ROAD_LOAD_HP'] <= 0:
                                    vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TOT_ROAD_LOAD_HP_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL['TOT_ROAD_LOAD_HP'].mean()
                                vehghg_file_nonflexfuel.loc[_index_vehghg_file_nonflexfuel, 'TARGET_COEF_BEST_MTH'] = 2

            del df_Cafe_MFR_CD_Mode_Type_Index, df_vehghg_file_nonflexfuel_target_coef, df_vehghg_file_nonflexfuel_target_coef_RL
            print('# of TARGET_COEF_BEST_MTH = 2 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 2]), ')')
            print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())

            df_target_coef_corr = vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])), _target_coef_surro_indexing_category]
            df_target_coef_corr_index = list(df_target_coef_corr.index)
            for i in range(len(df_target_coef_corr)):
                _index = df_target_coef_corr_index[i]
                if vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP_SURRO'] == 0:
                    print(_index, vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP_SURRO'])
                else:
                    rlhp_ratio = vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP']/vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP_SURRO']
                    if pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_BEST']):
                        vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_SURRO']

            print('# of TARGET_COEF_A_BEST (', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'])).sum(), ')')

            del set_roadload_coefficient_table, roadload_coefficient_table
            vehghg_file_nonflexfuel.drop(['Model Year', 'Veh Mfr Code', 'Represented Test Veh Model', 'Test Number', 'Test Category', 'Equivalent Test Weight (lbs.)', 'Test Veh Displacement (L)', 'N/V Ratio'], axis=1, inplace=True)
            check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel_rr', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            import Calculate_Powertrain_Efficiency
            vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='TEMP_ID') + 1, vehghg_file_nonflexfuel], axis=1)
            output_array = Calculate_Powertrain_Efficiency.Calculate_Powertrain_Efficiency( \
                vehghg_file_nonflexfuel['TEMP_ID'], vehghg_file_nonflexfuel['TEST_PROC_CATEGORY'], \
                vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'], vehghg_file_nonflexfuel['TARGET_COEF_B_BEST'], vehghg_file_nonflexfuel['TARGET_COEF_C_BEST'], vehghg_file_nonflexfuel['VEH_ETW'], \
                vehghg_file_nonflexfuel['TEST_UNROUNDED_UNADJUSTED_FE'], vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_CITY_FE_4'], vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_HWY_FE_4'], \
                vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_FE_4'], input_path, drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames, \
                vehghg_file_nonflexfuel['ENG_DISPL'], vehghg_file_nonflexfuel['ENG_RATED_HP'], vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'])

            vehghg_file_nonflexfuel = pd.merge(vehghg_file_nonflexfuel, output_array, how='left', \
                                               on=['TEMP_ID', 'TEST_PROC_CATEGORY']).reset_index(drop=True).rename( \
                columns={'Powertrain Efficiency (%)': 'PTEFF_FROM_RLCOEFFS', 'City Powertrain Efficiency (%)': 'City PTEFF_FROM_RLCOEFFS', 'Hwy Powertrain Efficiency (%)': 'Hwy PTEFF_FROM_RLCOEFFS'}).drop('TEMP_ID', axis=1)

            check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel_pe', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            total_allocated_volumes_to_footprint = pd.DataFrame(vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['FINAL_MODEL_YR_GHG_PROD_UNITS'].sum().reset_index()) \
                .rename(columns={'FINAL_MODEL_YR_GHG_PROD_UNITS': 'Total Subconfig Volume Allocated to Footprint'})
            total_allocated_volumes_to_subconfig = pd.DataFrame(vehghg_file_nonflexfuel.groupby(subconfig_indexing_categories)['PROD_VOL_GHG_TOTAL_50_STATE'].sum().reset_index()) \
                .rename(columns={'PROD_VOL_GHG_TOTAL_50_STATE': 'Total Footprint Volume Allocated to Subconfig'})
            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.merge(total_allocated_volumes_to_footprint, how='left', on=footprint_indexing_categories) \
                .merge(total_allocated_volumes_to_subconfig, how='left', on=subconfig_indexing_categories).reset_index(drop=True)

            footprint_volumes = vehghg_file_nonflexfuel['PROD_VOL_GHG_TOTAL_50_STATE'].replace(np.nan, 0).reset_index(drop=True)
            footprint_tlaas_volumes = vehghg_file_nonflexfuel['PROD_VOL_GHG_TLAAS_50_STATE'].replace(np.nan, 0).reset_index(drop=True)
            footprint_std_volumes = vehghg_file_nonflexfuel['PROD_VOL_GHG_STD_50_STATE'].replace(np.nan, 0).reset_index(drop=True)
            modeltype_ghg_volumes = pd.to_numeric(vehghg_file_nonflexfuel['PRODUCTION_VOLUME_GHG_50_STATE'].replace(np.nan, 0).reset_index(drop=True))
            modeltype_fe_volumes = pd.to_numeric(vehghg_file_nonflexfuel['PRODUCTION_VOLUME_FE_50_STATE'].replace(np.nan, 0).reset_index(drop=True))
            subconfig_volumes = vehghg_file_nonflexfuel['FINAL_MODEL_YR_GHG_PROD_UNITS'].replace(np.nan, 0).reset_index(drop=True)

            distributed_volumes_footprint = pd.Series(footprint_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PROD_VOL_GHG_TOTAL_50_STATE'].transform(len), name='Distributed Footprint Volumes')
            distributed_tlaas_volumes_footprint = pd.Series(footprint_tlaas_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PROD_VOL_GHG_TLAAS_50_STATE'].transform(len), name='Distributed Footprint TLAAS Volumes')
            distributed_std_volumes_footprint = pd.Series(footprint_std_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PROD_VOL_GHG_STD_50_STATE'].transform(len), name='Distributed Footprint Standard Volumes')
            # distributed_ghg_volumes_modeltype = pd.Series(modeltype_ghg_volumes / vehghg_file_nonflexfuel.groupby(footprint_indexing_categories)['PRODUCTION_VOLUME_GHG_50_STATE'].transform(len), name='Distributed Model Type GHG Volumes')
            # distributed_fe_volumes_modeltype = pd.Series(modeltype_fe_volumes / vehghg_file_nonflexfuel.groupby(modeltype_indexing_categories)['PRODUCTION_VOLUME_FE_50_STATE'].transform(len), name='Distributed Model Type FE Volumes')
            distributed_volumes_subconfig = pd.Series(subconfig_volumes / vehghg_file_nonflexfuel.groupby(subconfig_indexing_categories)['FINAL_MODEL_YR_GHG_PROD_UNITS'].transform(len), \
                                                      name='Distributed Subconfig Volumes')
            distributed_volumes = pd.concat([distributed_volumes_footprint, distributed_volumes_subconfig, \
                                             distributed_tlaas_volumes_footprint, distributed_std_volumes_footprint], axis = 1).reset_index(drop=True)
                                             # distributed_ghg_volumes_modeltype, distributed_fe_volumes_modeltype], axis = 1).reset_index(drop=True)
            mixed_volumes_footprint = pd.Series((footprint_volumes * subconfig_volumes / vehghg_file_nonflexfuel['Total Subconfig Volume Allocated to Footprint']), name='FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES')
            mixed_volumes_subconfig = pd.Series((footprint_volumes * subconfig_volumes / vehghg_file_nonflexfuel['Total Footprint Volume Allocated to Subconfig']), name='SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES')
            mixed_volumes = pd.concat([mixed_volumes_footprint, mixed_volumes_subconfig], axis=1).reset_index(drop=True)
            mixed_volumes['FOOTPRINT_SUBCONFIG_VOLUMES'] = mixed_volumes[['FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES', 'SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES']].mean(axis=1)
            vehghg_file_nonflexfuel = pd.concat([vehghg_file_nonflexfuel, distributed_volumes, mixed_volumes], axis=1)
            vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='Vehghg_ID') + 1, vehghg_file_nonflexfuel], axis=1)

            vehghg_file_flexfuel = vehghg_file[vehghg_file['FUEL_USAGE'] == 'E'].reset_index(drop=True).drop(['FINAL_MODEL_YR_GHG_PROD_UNITS', 'PROD_VOL_GHG_TOTAL_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE', 'PRODUCTION_VOLUME_FE_50_STATE', 'PROD_VOL_GHG_TLAAS_50_STATE', 'PROD_VOL_GHG_STD_50_STATE'], axis=1)

            vehghg_file_flexfuel = pd.merge(vehghg_file_flexfuel, vehghg_file_nonflexfuel[['Vehghg_ID', 'BodyID', 'FOOTPRINT_INDEX', 'CONFIG_INDEX', \
                                                 'SUBCONFIG_INDEX', 'SS_ENGINE_FAMILY']], how='left', \
                                            on=['BodyID', 'FOOTPRINT_INDEX', 'CONFIG_INDEX', 'SUBCONFIG_INDEX', 'SS_ENGINE_FAMILY']).sort_values('Vehghg_ID').reset_index(drop=True)

            # vehghg_file_nonflexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()]\
            #     = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()].replace(np.nan,'none')
            # vehghg_file_flexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()]\
            #     = vehghg_file_flexfuel[vehghg_file_nonflexfuel.columns[vehghg_file_nonflexfuel.isnull().all()].tolist()].replace(np.nan,'none')
            # output both flex fuel and non flex fuel
            # vehghg_file_output = pd.merge_ordered(vehghg_file_nonflexfuel, vehghg_file_flexfuel, \
            #    how='outer', on=merging_columns+['Vehghg_ID']).sort_values('Vehghg_ID').reset_index(drop=True)
            check_final_model_yr_ghg_prod_units('vehghg_file_output_before', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            # only output non flex fuel
            vehghg_file_output = vehghg_file_nonflexfuel
            del vehghg_file

            vehghg_file_output = vehghg_file_output.loc[:, ~vehghg_file_output.columns.duplicated()]
            vehghg_file_output = vehghg_file_output.loc[:, ~vehghg_file_output.columns.str.contains('^Unnamed')]
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Distributed Footprint Volumes'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Distributed Subconfig Volumes'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Total Subconfig Volume Allocated to Footprint'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Total Footprint Volume Allocated to Subconfig'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'FOOTPRINT_SUBCONFIG_VOLUMES'] = 0

            vehghg_file_output['RLHP_FROM_RLCOEFFS'] = ((vehghg_file_output['TARGET_COEF_A'] + (50 * vehghg_file_output['TARGET_COEF_B']) \
                         + ((50 * 50) * vehghg_file_output['TARGET_COEF_C'])) * 50 * lbfmph2hp).replace(0, np.nan)
            v_aero_mph = 45
            air_density = 1.17 * kgpm32slugpft3
            vehghg_file_output['CDA_FROM_RLCOEFFS'] = pd.Series(
                (vehghg_file_output['TARGET_COEF_B'] + 2 * vehghg_file_output['TARGET_COEF_C'] * v_aero_mph) \
                * ftps2mph / (air_density * v_aero_mph * mph2ftps)).replace(0, np.nan)
            vehghg_file_output['TOTAL_ROAD_LOAD_FORCE_50MPH'] = vehghg_file_output['RLHP_FROM_RLCOEFFS'] * hp2lbfmph * (1 / 50)
            vehghg_file_output['AERO_FORCE_50MPH'] = 0.5 * air_density * vehghg_file_output['CDA_FROM_RLCOEFFS'] * ((50 * mph2ftps) ** 2)
            vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'] = (vehghg_file_output['TOTAL_ROAD_LOAD_FORCE_50MPH'] - vehghg_file_output[
                    'AERO_FORCE_50MPH']).replace(0, np.nan)
            vehghg_file_output = vehghg_file_output.drop(['TOTAL_ROAD_LOAD_FORCE_50MPH', 'AERO_FORCE_50MPH'], axis=1)

            vehghg_file_output['FRONT_TIRE_RADIUS_IN'] = pd.Series(
                vehghg_file_output['FRONT_BASE_TIRE_CODE']).str.split('R').str.get(1).str.extract('(\d+)').astype(float) * 0.5
            vehghg_file_output['REAR_TIRE_RADIUS_IN'] = pd.Series(vehghg_file_output['REAR_BASE_TIRE_CODE']).str.split('R').str.get(1).str.extract('(\d+)').astype(float) * 0.5
            vehghg_file_output['TIRE_WIDTH_INS'] = pd.Series(vehghg_file_output['FRONT_BASE_TIRE_CODE']).str.split(
                '/').str.get(0).str.extract('(\d+)').astype(float) / in2mm

            F_brake = 2 * (0.4 / (vehghg_file_output['FRONT_TIRE_RADIUS_IN'] * in2m)) * n2lbf + 2 * (0.4 / (vehghg_file_output['REAR_TIRE_RADIUS_IN'] * in2m)) * n2lbf
            rpm_front = 50 * mph2mps * (1 / (vehghg_file_output['FRONT_TIRE_RADIUS_IN'] * in2m)) * (60 / (2 * math.pi))
            rpm_rear = 50 * mph2mps * (1 / (vehghg_file_output['REAR_TIRE_RADIUS_IN'] * in2m)) * (60 / (2 * math.pi))
            F_hub = 2 * (((-2e-6 * rpm_front ** 2) + (.0023 * rpm_front + 1.2157) / (vehghg_file_output['FRONT_TIRE_RADIUS_IN'] * in2m)) * n2lbf) \
                    + 2 * (((-2e-6 * rpm_rear ** 2) + (.0023 * rpm_rear + 1.2157) / (vehghg_file_output['REAR_TIRE_RADIUS_IN'] * in2m)) * n2lbf)
            F_drivetrain = 20 * n2lbf
            vehghg_file_output['ROLLING_FORCE_50MPH'] = vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'] - F_hub - F_brake - F_drivetrain
            vehghg_file_output['RRC_FROM_RLCOEFFS'] = (1000 * vehghg_file_output['ROLLING_FORCE_50MPH'] / vehghg_file_output['ETW']).replace(0, np.nan)
            vehghg_file_output = vehghg_file_output.drop(['ROLLING_FORCE_50MPH'], axis=1)
            vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS_NORMALIZED_BY_ETW'] = vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'] / vehghg_file_output['ETW']
            vehghg_file_output['Transmission Short Name'] = pd.Series(vehghg_file_output['TRANS_TYPE'] + \
                                                                      vehghg_file_output['TOTAL_NUM_TRANS_GEARS'].astype(str)).replace('CVT1', 'CVT')
            vehghg_file_output.loc[:,'CALC_ID'] = vehghg_file_output.loc[:, 'CALC_ID'][~pd.isnull(vehghg_file_output['CALC_ID'])].astype(float).astype(int)
            vehghg_file_output['ROAD_LOAD_LABEL'] = pd.Series(vehghg_file_output['CALC_ID'].astype(str) + '_' \
                + vehghg_file_output['FOOTPRINT_CARLINE_NM'] + '_' + vehghg_file_output['BodyID'].astype(str) + '_' \
                + vehghg_file_output['ENG_DISPL'].astype(str) + '_' + vehghg_file_output['Transmission Short Name'] + '_' + \
                'Axle Ratio:(' + vehghg_file_output['AXLE_RATIO'].round(2).astype(str) + ')' + '_' + \
                'RLHP:(' + vehghg_file_output['RLHP_FROM_RLCOEFFS'].round(2).astype(str) + ')' + '_' + \
                'CDA:(' + vehghg_file_output['CDA_FROM_RLCOEFFS'].round(2).astype(str) + ')' + '_' + \
                'Non-Aero:(' + vehghg_file_output['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'].round(2).astype(str) + ')' + '_' + \
                'RRC:(' + vehghg_file_output['RRC_FROM_RLCOEFFS'].round(1).astype(str) + ')' + '_' + \
                vehghg_file_output['FRONT_BASE_TIRE_CODE'] + '_' + \
                vehghg_file_output['ETW'].replace(np.nan, 0).astype(float).round(0).astype(int).replace(0, 'na').astype(str))
            check_final_model_yr_ghg_prod_units('vehghg_file_output', vehghg_file_output, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            vehghg_file_output.drop_duplicates(keep=False, inplace=True)
            vehghg_file_output.to_csv(output_path + '\\' + vehghg_filename.replace('.csv', '') + '_' + date_and_time + '.csv', index=False)
        else:
            # New BodyID table sought, previous data included
            full_expanded_footprint_filter_table = full_expanded_footprint_filter_table.merge \
                (previous_filter_table[list(footprint_id_categories) + ['BodyID'] + ['POSSIBLE_BODYID']], how='left', \
                 on=list(footprint_id_categories) + ['BodyID'])
            # full_expanded_footprint_filter_table['POSSIBLE_BODYID']
            changed_lineageids = pd.Series(full_expanded_footprint_filter_table['LineageID'][pd.isnull(
                full_expanded_footprint_filter_table['POSSIBLE_BODYID'])]).unique()
            full_expanded_footprint_filter_table['POSSIBLE_BODYID'][
                full_expanded_footprint_filter_table['LineageID'].isin(changed_lineageids)] = np.nan
            full_filter_table_save_name = manual_filter_name.replace('.csv', '') + ' ' + date_and_time + '.csv'
            full_expanded_footprint_filter_table.to_csv(
                output_path.replace('\VehghgID', '\intermediate files') + '\\' + full_filter_table_save_name, index=False)
