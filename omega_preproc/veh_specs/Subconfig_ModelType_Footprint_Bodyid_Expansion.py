import pandas as pd
import datetime
import numpy as np

eps = 1e-5
CSV_OUTPUT_DEBUG_MODE = False
DEBUGGING_CAFE_MFR_CD_MODE = False
DEBUGGING_CAFE_MFR_CD = 'FMX'
ESTIMATE_NV_RATIO_SET_COEF_ABC_BY_ROAD_LOAD_HP = False
ESTIMATE_TARGET_COEF_BEST_MTH_3_4 = True
DEBUGGING_ERRTA_FILEs = False

def file_errta_update(errta_fname, footprintSubconfigMY_file, errta_table, year, Column_Name, Old_Value, New_Value, MODEL_YEAR, MFR_DIVISION_NM, MFR_DIVISION_CD, MFR_CARLINE_CD, CAFE_ID, footprintSubconfig_INDEX):
    errta_table = errta_table.loc[errta_table[MODEL_YEAR] == year, :].reset_index(drop=True)
    errta_table['Correction Index'] = errta_table.index;

    errta_table.loc[pd.isnull(errta_table[Old_Value]), Old_Value] = ''
    errta_table.loc[pd.isnull(errta_table[New_Value]), New_Value] = ''
    for error_check_count in range(0, len(errta_table)):
        if pd.isnull(errta_table[Column_Name][error_check_count]):
            break
        # if errta_table[MFR_CARLINE_CD][error_check_count] == 'MKZ HYBRID FWD':
        #     print('MKZ HYBRID FWD')
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

            if (pd.isnull(CAFE_ID)) and (pd.isnull(footprintSubconfig_INDEX)):
                errta_checks = (footprintSubconfigMY_file[MODEL_YEAR] == errta_table[MODEL_YEAR][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_NM] == errta_table[MFR_DIVISION_NM][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_CD] == errta_table[MFR_DIVISION_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_CARLINE_CD] == errta_table[MFR_CARLINE_CD][error_check_count])
                if pd.isnull(errta_table[MFR_CARLINE_CD][error_check_count]):
                    errta_checks = (footprintSubconfigMY_file[MODEL_YEAR] == errta_table[MODEL_YEAR][error_check_count]) & \
                                   (footprintSubconfigMY_file[MFR_DIVISION_NM] == errta_table[MFR_DIVISION_NM][error_check_count]) & \
                                   (footprintSubconfigMY_file[MFR_DIVISION_CD] == errta_table[MFR_DIVISION_CD][error_check_count])
            else:
                errta_checks = (footprintSubconfigMY_file[MODEL_YEAR] == errta_table[MODEL_YEAR][error_check_count]) & \
                    (footprintSubconfigMY_file[CAFE_ID] == errta_table[CAFE_ID][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_NM] == errta_table[MFR_DIVISION_NM][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_DIVISION_CD] == errta_table[MFR_DIVISION_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[MFR_CARLINE_CD] == errta_table[MFR_CARLINE_CD][error_check_count]) & \
                    (footprintSubconfigMY_file[footprintSubconfig_INDEX] == errta_table[footprintSubconfig_INDEX][error_check_count])

                if pd.isnull(errta_table[MFR_CARLINE_CD][error_check_count]):
                    errta_checks = (footprintSubconfigMY_file[MODEL_YEAR] == errta_table[MODEL_YEAR][error_check_count]) & \
                                   (footprintSubconfigMY_file[CAFE_ID] == errta_table[CAFE_ID][error_check_count]) & \
                                   (footprintSubconfigMY_file[MFR_DIVISION_NM] == errta_table[MFR_DIVISION_NM][error_check_count]) & \
                                   (footprintSubconfigMY_file[MFR_DIVISION_CD] == errta_table[MFR_DIVISION_CD][error_check_count]) & \
                                   (footprintSubconfigMY_file[footprintSubconfig_INDEX] == errta_table[footprintSubconfig_INDEX][error_check_count])

            if (len(errta_checks[errta_checks==True]) == 0) and (DEBUGGING_ERRTA_FILEs == True):
                print('MFR_CARLINE_CD = ', errta_table[MFR_CARLINE_CD][error_check_count], ' ', errta_table[New_Value][error_check_count], ' in ', _column_name, ' not updated, check the errta file for ', errta_fname)

            if errta_table['Numeric (y/n)'][error_check_count] == 'y':
                footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]] = pd.to_numeric(footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]], errors='coerce')
                errta_table.loc[error_check_count, New_Value] = pd.to_numeric(errta_table[New_Value][error_check_count], errors='coerce')
                errta_table.loc[error_check_count, Old_Value] = pd.to_numeric(errta_table[Old_Value][error_check_count], errors='coerce')
                errta_checks = errta_checks & \
                               ((footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]] == errta_table[Old_Value][error_check_count]) | \
                               (abs(footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]] - errta_table[Old_Value][error_check_count]) <= eps))
                footprintSubconfigMY_file.loc[errta_checks, errta_table.loc[error_check_count, Column_Name]] = errta_table[New_Value][error_check_count]
            else:
                footprintSubconfigMY_file.loc[errta_checks & (footprintSubconfigMY_file[errta_table.loc[error_check_count, Column_Name]] == errta_table[Old_Value][error_check_count]), \
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

    # grp_vehghg_file_full_merged_data_chk1 = vehghg_file_full_merged_data_chk.groupby(['FOOTPRINT_MFR_CD'])['PROD_VOL_GHG_STD_50_STATE'].sum().reset_index(drop=True)
    # grp_volumes_vehghg_file_full_merged_data_chk1 = grp_vehghg_file_full_merged_data_chk1[distributed_volumes_column_name]

    # print('total_volumes_footprint_file = ', total_volumes_footprint_file, ' total volumes_footprint_file_with_lineage = ', grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'].sum(),
    #       ' grp_volumes_' + data_chk_filename + ' @ merging = ', grp_volumes_vehghg_file_full_merged_data_chk.sum().round(0).astype(int))

    if total_volumes_footprint_file == grp_volumes_vehghg_file_full_merged_data_chk.sum().round(0).astype(int):
        delta_final_model_yr_ghg_prod_units = 0
    else:
        delta_final_model_yr_ghg_prod_units = grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'].sum() - grp_volumes_vehghg_file_full_merged_data_chk.sum().round(0).astype(int)
        # for i in range(min(len(grp_volumes_footprint_file_with_lineage), len(grp_vehghg_file_full_merged_data_chk))):
        #     if abs(grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'][i] - grp_volumes_vehghg_file_full_merged_data_chk[i].round(0).astype(int)) != 0:
        #         print(grp_volumes_footprint_file_with_lineage.index[i], grp_volumes_footprint_file_with_lineage.loc[grp_volumes_footprint_file_with_lineage.index[i], 'PROD_VOL_GHG_STD_50_STATE'], \
        #               grp_volumes_vehghg_file_full_merged_data_chk[i].round(0).astype(int))

    return delta_final_model_yr_ghg_prod_units

def tstcar_target_coef_cafe_mfr_cd_carline_name(set_roadload_coefficient_table, tstcar_MY_errta_table, _model_year, _cafe_mfr_cd, _label_mfr_cd, _carline_name, _mfr_divsion_short_nm, \
                                                _displ, _etw, _num_trans_gears, _engine_displacement_check):
    _num_models = set_roadload_coefficient_table.loc[set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name, 'Represented Test Veh Model'].shape[0]
    _veh_mfr_code = 'Veh Mfr Code'
    _tstcar_displ = _tstcar_drive_system_code = df_tstcar_table = _tstcar_cafe_mfr_cd_carline_name = np.nan
    _trims = ['XSE', 'XLE', 'FFV', 'FWD', 'RWD', '4WD', '2WD', 'AWD', 'BLUE', 'XL', 'LBS', 'PICKUP', 'EXCLUSIVE', 'PERFORMANCE', 'PACKAGE', 'GT', 'MAX', 'LIMITED', 'CLASSIC', 'LD', 'BASE', 'PAYLOAD', 'LT', 'TIRE']
    if _num_models == 0:
        df_carline_name = tstcar_MY_errta_table.loc[tstcar_MY_errta_table['CARLINE_NAME'] == _carline_name, :]
        if df_carline_name.shape[0] == 0:
            # print(_carline_name)
            if ('2WD' and 'F150') in _carline_name: _carline_name.replace('2WD', '4X2')
            if ('4WD' and 'F150') in _carline_name: _carline_name.replace('4WD', '4X4')
            _carline_name = _carline_name.split(' ')
            if len(_carline_name) > 1:
                tmp = []
                for i in range (len(_carline_name)):
                    if (_carline_name[i] not in _trims) and ('GVWR>' not in _carline_name[i]) and ('.5L' not in _carline_name[i]) and ('.0L' not in _carline_name[i]): tmp.append(_carline_name[i])
                _carline_name = ' '.join(tmp)
                _num_models = set_roadload_coefficient_table.loc[set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name, 'Represented Test Veh Model'].shape[0]

            if _num_models == 0: return df_carline_name
        if (df_carline_name.shape[0] > 0):
            _index = df_carline_name.index[0]
            _carline_name = df_carline_name.loc[_index, 'Represented Test Veh Model']
            _tstcar_displ = df_carline_name.loc[_index, 'Test Veh Displacement (L)']
            _tstcar_drive_system_code = df_carline_name.loc[_index, 'Drive System Code']
        elif (_num_models > 0):
            _index = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
                                                        (set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
                                                        (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)'])), :].index[0]
            _tstcar_displ = set_roadload_coefficient_table.loc[_index, 'Test Veh Displacement (L)']
            _tstcar_drive_system_code = set_roadload_coefficient_table.loc[_index, 'Drive System Code']

        if (pd.isnull(_tstcar_displ)) and (~pd.isnull(_tstcar_drive_system_code)):
            _tstcar_cafe_mfr_cd_carline_name = (set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
            (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
            (set_roadload_coefficient_table['Drive System Code'] == _tstcar_drive_system_code) & \
            (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']))
        elif (~pd.isnull(_tstcar_drive_system_code)):
            _tstcar_cafe_mfr_cd_carline_name = (set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
            (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
            (set_roadload_coefficient_table['Test Veh Displacement (L)'].round(1) == _tstcar_displ.round(1)) & \
            (set_roadload_coefficient_table['Drive System Code'] == _tstcar_drive_system_code) & \
            (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']))
    elif (~pd.isnull(_displ)) and (~pd.isnull(_num_trans_gears)) and (set_roadload_coefficient_table.loc[ \
            (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name), 'Test Veh Displacement (L)'].shape[0] > 0) and \
            (set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name), '# of Gears'].shape[0] > 0):
        _tstcar_cafe_mfr_cd_carline_name = (set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
                                           (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
                                           (set_roadload_coefficient_table['Test Veh Displacement (L)'].round(1) == _displ.round(1)) & \
                                           (set_roadload_coefficient_table['# of Gears'] == _num_trans_gears) & \
                                           (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']))
    elif (~pd.isnull(_displ)) and (pd.isnull(_num_trans_gears)) and (set_roadload_coefficient_table.loc[ \
            (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name), 'Test Veh Displacement (L)'].shape[0] > 0):
        _tstcar_cafe_mfr_cd_carline_name = (set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
                                           (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
                                           (set_roadload_coefficient_table['Test Veh Displacement (L)'].round(1) == _displ.round(1)) & \
                                           (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']))
    else:
        _tstcar_cafe_mfr_cd_carline_name = (set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
                                       (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
                                       (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']))

    if _num_models == 0:
        if (set_roadload_coefficient_table.loc[(set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
                                               (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name), 'Represented Test Veh Model'].shape[0] > 0):
            pass
        elif (set_roadload_coefficient_table.loc[(set_roadload_coefficient_table[_veh_mfr_code] == _label_mfr_cd) & \
                                                 (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name), 'Represented Test Veh Model'].shape[0] > 0):
            _cafe_mfr_cd = _label_mfr_cd
    if _num_models > 0 and (set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Represented Test Veh Make'] == _mfr_divsion_short_nm) & \
                                                               (set_roadload_coefficient_table[_veh_mfr_code] != _cafe_mfr_cd) & \
                                                               (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name), 'Represented Test Veh Model'].shape[0] > 0):
            _cafe_mfr_cd = _mfr_divsion_short_nm
            _veh_mfr_code = 'Represented Test Veh Make'

    df_tstcar_table = set_roadload_coefficient_table.loc[_tstcar_cafe_mfr_cd_carline_name, :]
    if df_tstcar_table.shape[0] == 0:
        df_tstcar_table = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table[_veh_mfr_code] == _cafe_mfr_cd) & \
                                       (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
                                       (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)'])), :]
        if (df_tstcar_table.shape[0] == 0) or (_num_models > 0):
            df_tstcar_table = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name) & \
                              (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)'])), :]

    if df_tstcar_table.shape[0] > 0:
        _tstcar_year = ''
        if df_tstcar_table.loc[df_tstcar_table['Model Year'] == _model_year, 'Model Year'].shape[0] > 0:
            _tstcar_year = _model_year
        elif max(df_tstcar_table['Model Year']) < _model_year:
            _tstcar_year = max(df_tstcar_table['Model Year'])
        elif min(df_tstcar_table['Model Year']) > _model_year:
            _tstcar_year = min(df_tstcar_table['Model Year'])

        if _tstcar_year != '': df_tstcar_table = df_tstcar_table.loc[(df_tstcar_table['Model Year'] == _tstcar_year), :]

    if ((len(df_tstcar_table[df_tstcar_table['Test Veh Displacement (L)'] == _displ]) > 0) & (~pd.isnull(_displ) == True)) or (_engine_displacement_check == 'strict'):
        df_tstcar_table = df_tstcar_table.loc[(df_tstcar_table['Test Veh Displacement (L)'] == _displ) & (~pd.isnull(df_tstcar_table['Target Coef A (lbf)'])), :]

    if ((len(df_tstcar_table[df_tstcar_table['Equivalent Test Weight (lbs.)'] == _etw]) > 0) & (~pd.isnull(_etw) == True)) or (_engine_displacement_check == 'strict'):
        df_tstcar_table = df_tstcar_table.loc[(df_tstcar_table['Equivalent Test Weight (lbs.)'] == _etw) & (~pd.isnull(df_tstcar_table['Target Coef A (lbf)'])), :]

    return df_tstcar_table

def manual_filtering(year, footprint_filter_table, footprint_id_categories, footprint_file, lineage_file, body_id_table, input_path, footprint_lineage_filename, output_path, date_and_time):

    if len(lineage_file) == 0:
        lineage_file = pd.read_csv(input_path + '\\' + footprint_lineage_filename, encoding="ISO-8859-1");
        _year = lineage_file['MODEL_YEAR'].iloc[(lineage_file['MODEL_YEAR'] - year).abs().argsort()[:2]].reset_index(drop=True)[0];
        lineage_file = lineage_file[lineage_file['MODEL_YEAR'] == _year].reset_index(drop=True)
        lineage_file['MODEL_YEAR'] = year;
        # lineage_file.append(lineage_file_MY, ignore_index=True)
        # lineage_file = lineage_file_MY;
        # lineage_file_save_name = footprint_lineage_filename.replace('.csv', '') + ' ' + date_and_time + '.csv'
        # lineage_file.to_csv(input_path + '\\' + lineage_file_save_name, index=False)
        # lineage_file = lineage_file[lineage_file['MODEL_YEAR'] == year].reset_index(drop=True)

        footprint_lineageid_categories = ['MODEL_YEAR', 'FOOTPRINT_INDEX', 'FOOTPRINT_CARLINE_NM', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_DIVISION_NM'];
        # footprint_lineageid_categories = ['MODEL_YEAR', 'FOOTPRINT_CARLINE_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_NM'];
        footprint_filter_table = footprint_file[list(footprint_id_categories) + ['WHEEL_BASE_INCHES'] + ['FOOTPRINT_DESC'] + ['PROD_VOL_GHG_STD_50_STATE'] + ['CAFE_MFR_CD'] + ['CAFE_MFR_NM']].merge(
            lineage_file[list(footprint_lineageid_categories) + ['LineageID']], how='left', on=footprint_lineageid_categories)
    else:
        footprint_lineageid_categories = ['MODEL_YEAR', 'FOOTPRINT_INDEX', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_DIVISION_NM'];
        footprint_filter_table = footprint_file[list(footprint_id_categories) + ['WHEEL_BASE_INCHES'] + ['FOOTPRINT_DESC'] + ['PROD_VOL_GHG_STD_50_STATE'] + ['CAFE_MFR_CD'] + ['CAFE_MFR_NM']].merge(
            lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_lineageid_categories)


    footprint_filter_table.insert(14, 'Matching Method', np.nan);
    footprint_filter_table.loc[footprint_filter_table['LineageID'].astype(str) != 'nan', 'Matching Method'] = 0;
    footprint_filter_table = footprint_filter_table.rename({'CAFE_ID_x':'CAFE_ID', 'FOOTPRINT_CARLINE_NM_x':'FOOTPRINT_CARLINE_NM'}, axis=1)
    # print('Direct matching footprint_file volumes = ', footprint_filter_table.loc[footprint_filter_table['LineageID'].astype(str) != 'nan', 'PROD_VOL_GHG_STD_50_STATE'].sum())
    # df = footprint_filter_table.loc[footprint_filter_table['LineageID'].astype(str) != 'nan']

    # footprint_filter_table1 = footprint_filter_table.loc[~pd.isnull(footprint_filter_table['LineageID']), :].reset_index(drop=True)
    # footprint_filter_table0 = footprint_filter_table.loc[pd.isnull(footprint_filter_table['LineageID']), :].reset_index(drop=True)

    for i in range (len(footprint_filter_table)):
        if (footprint_filter_table['LineageID'][i].astype(str) == 'nan') or (footprint_filter_table['LineageID'][i].astype(int) == 0):
            _carline_nm = footprint_filter_table['FOOTPRINT_CARLINE_NM'][i].split(' ');
            _num_carline_nm = len(_carline_nm);
            for j in range(len(lineage_file)):
                if (footprint_filter_table['MODEL_YEAR'][i] == lineage_file['MODEL_YEAR'][j]) and (footprint_filter_table['FOOTPRINT_CARLINE_CD'][i] == lineage_file['FOOTPRINT_CARLINE_CD'][j]) and \
                    (footprint_filter_table['FOOTPRINT_MFR_CD'][i] == lineage_file['FOOTPRINT_MFR_CD'][j]) and (footprint_filter_table['FOOTPRINT_DIVISION_CD'][i] == lineage_file['FOOTPRINT_DIVISION_CD'][j]):
                    if (footprint_filter_table['FOOTPRINT_CARLINE_NM'][i] == lineage_file['FOOTPRINT_CARLINE_NM'][j])  or (lineage_file['FOOTPRINT_CARLINE_NM'][j] == footprint_filter_table['FOOTPRINT_CARLINE_NM'][i]):
                        footprint_filter_table.loc[i, 'LineageID'] = lineage_file['LineageID'][j].astype(int);
                        footprint_filter_table.loc[i, 'Matching Method'] = 1;
                        break;
                elif (footprint_filter_table['MODEL_YEAR'][i] == lineage_file['MODEL_YEAR'][j]) and \
                    (footprint_filter_table['FOOTPRINT_MFR_CD'][i] == lineage_file['FOOTPRINT_MFR_CD'][j]) and (footprint_filter_table['FOOTPRINT_DIVISION_CD'][i] == lineage_file['FOOTPRINT_DIVISION_CD'][j]):
                    _carline_nm = footprint_filter_table['FOOTPRINT_CARLINE_NM'][i].split(' ');
                    for k in range(_num_carline_nm-1, 0, -1):
                        _carline_nm.remove(_carline_nm[k])
                        _carline_nm_k = ' '.join([str(n) for n in _carline_nm])
                        if  ((k == _num_carline_nm-1) or (k >= 2)) and (_carline_nm_k in lineage_file['FOOTPRINT_CARLINE_NM'][j])  or (lineage_file['FOOTPRINT_CARLINE_NM'][j] in footprint_filter_table['FOOTPRINT_CARLINE_NM'][i]):
                            footprint_filter_table.loc[i, 'LineageID'] = lineage_file['LineageID'][j].astype(int);
                            footprint_filter_table.loc[i, 'Matching Method'] = 2;
                            break;
                        elif (k == 1) and (_carline_nm_k in lineage_file['FOOTPRINT_CARLINE_NM'][j])  or (lineage_file['FOOTPRINT_CARLINE_NM'][j] in footprint_filter_table['FOOTPRINT_CARLINE_NM'][i]):
                            footprint_filter_table.loc[i, 'LineageID'] = lineage_file['LineageID'][j].astype(int);
                            footprint_filter_table.loc[i, 'Matching Method'] = 3;
                            break;

    footprint_filter_table.loc[footprint_filter_table['LineageID'].astype(str) == 'nan', 'Matching Method'] = np.nan

    print('total footprint_file volumes = ', footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum())
    print('total footprint_filter_table volumes = ', footprint_filter_table['PROD_VOL_GHG_STD_50_STATE'].sum())
    # footprint_file_max = footprint_file.loc[footprint_file['FOOTPRINT_MFR_CD'] == 'MAX', :].sort_values(by=['FOOTPRINT_CARLINE_CD'])
    # footprint_filter_table1 = footprint_filter_table.loc[footprint_filter_table['FOOTPRINT_MFR_CD'] == 'MAX', :].sort_values(by=['FOOTPRINT_CARLINE_CD'])
    # print('total footprint_file_max volumes = ', footprint_file_max['PROD_VOL_GHG_STD_50_STATE'].sum())
    # print('total footprint_filter_table1 volumes = ', footprint_filter_table1['PROD_VOL_GHG_STD_50_STATE'].sum())

    grp_volumes_footprint_file = footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()
    grp_volumes_footprint_filter_table = footprint_filter_table.groupby(['FOOTPRINT_MFR_CD']).sum()
    # grp_volumes_footprint_file1 = footprint_file.groupby(['FOOTPRINT_MFR_CD'])['PROD_VOL_GHG_STD_50_STATE'].sum()
    # grp_volumes_footprint_file_with_lineage1 = footprint_file_with_lineage.groupby(['FOOTPRINT_MFR_CD'])['PROD_VOL_GHG_STD_50_STATE'].sum()

    for i in range(min(len(grp_volumes_footprint_file), len(grp_volumes_footprint_filter_table))):
        if grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0) != grp_volumes_footprint_filter_table['PROD_VOL_GHG_STD_50_STATE'][i].round(0):
            #### Update CAFE_ID in the footprint errta and footprint-lineageID files
            print(grp_volumes_footprint_file.index[i], grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], grp_volumes_footprint_filter_table['PROD_VOL_GHG_STD_50_STATE'][i])
            df_footprint = footprint_file.loc[footprint_file['FOOTPRINT_MFR_CD'] == grp_volumes_footprint_file.index[i], :];
            df_footprint_filter = footprint_filter_table.loc[footprint_filter_table['FOOTPRINT_MFR_CD'] == grp_volumes_footprint_file.index[i], :].sort_values(by=['FOOTPRINT_CARLINE_CD']);
            df_footprint_filter = df_footprint_filter.drop_duplicates(subset=df_footprint_filter.columns).reset_index(drop=True);
            _carline_nm = df_footprint['FOOTPRINT_CARLINE_NM'].unique();
            for j in range(len(_carline_nm)):
                df_footprint = df_footprint.loc[(df_footprint['FOOTPRINT_CARLINE_NM'] == _carline_nm[j]), :]
                df_footprint_filter = df_footprint_filter.loc[(df_footprint_filter['FOOTPRINT_CARLINE_NM'] == _carline_nm[j]), :]
                if df_footprint['PROD_VOL_GHG_STD_50_STATE'].sum() != df_footprint_filter['PROD_VOL_GHG_STD_50_STATE'].sum():
                    print(_carline_nm[j], df_footprint['PROD_VOL_GHG_STD_50_STATE'].sum(), df_footprint_filter['PROD_VOL_GHG_STD_50_STATE'].sum())

    manual_filter_table = footprint_filter_table.merge(body_id_table, how='left', on='LineageID')
    manual_filter_table['POSSIBLE_BODYID'] = 'y';
    manual_filter_table.loc[manual_filter_table['LineageID'].astype(str) == 'nan', 'POSSIBLE_BODYID'] = np.nan
    manual_filter_table['LineageID'] = pd.to_numeric(manual_filter_table['LineageID'], errors='coerce')
    manual_filter_table = manual_filter_table.sort_values(by=['LineageID'])
    # manual_filter_table = manual_filter_table.drop_duplicates(subset=footprint_id_categories+['PROD_VOL_GHG_STD_50_STATE']).reset_index(drop=True);
    manual_filter_table.loc[manual_filter_table['LineageID'] == 99999, ['LineageID', 'BodyID']] = np.nan;
    # manual_filter_table.loc[manual_filter_table['BodyID'] == 99999, 'BodyID'] = np.nan;
    manual_filter_table.sort_values(by=['FOOTPRINT_MFR_NM'], ascending=True, inplace=True);
    manual_filter_table.reset_index(drop=True, inplace=True);
    manual_filter_table_null = manual_filter_table.loc[pd.isnull(manual_filter_table['LineageID']), :].reset_index(drop=True)
    manual_filter_table_null_carline_nm = manual_filter_table_null['FOOTPRINT_CARLINE_NM'].unique();
    #
    _lineageID = manual_filter_table['LineageID'].max()+1;
    _bodyID_MY_start = _lineageID;

    _carline_nm_unique = [];
    for i in range(len(manual_filter_table_null_carline_nm)):
        _carline_nm_i = manual_filter_table_null_carline_nm[i].split(' ');
        if len(_carline_nm_i) == 1:
            _carline_nm_unique.append(_carline_nm_i[0]);
        elif (len(_carline_nm_i) > 1) and (_carline_nm_i[0] not in _carline_nm_unique):
            if (_carline_nm_i[0] in manual_filter_table_null_carline_nm[i]) and (_carline_nm_i[0] not in _carline_nm_unique):
                if (_carline_nm_i[0] == 'GLB') or (_carline_nm_i[0] == 'Continental'):
                    _carline_nm_unique.append(_carline_nm_i[0] + ' ' + _carline_nm_i[1]);
                else:
                    _carline_nm_unique.append(_carline_nm_i[0]);

    _carline_nm_unique_base = []
    for i in _carline_nm_unique:
        if i not in _carline_nm_unique_base:
            _carline_nm_unique_base.append(i)

    for i in range(len(manual_filter_table_null)):
        manual_filter_table_null_carline_nm_i = manual_filter_table_null['FOOTPRINT_CARLINE_NM'][i].split(' ')[0]
        if (manual_filter_table_null_carline_nm_i == 'GLB') or (manual_filter_table_null_carline_nm_i == 'Continental'):
            manual_filter_table_null_carline_nm_i = manual_filter_table_null['FOOTPRINT_CARLINE_NM'][i].split(' ')[0] + ' ' + manual_filter_table_null['FOOTPRINT_CARLINE_NM'][i].split(' ')[1]

        if manual_filter_table_null_carline_nm_i in _carline_nm_unique_base:
            index = _carline_nm_unique_base.index(manual_filter_table_null_carline_nm_i);
            manual_filter_table_null.loc[i, 'LineageID'] = manual_filter_table['LineageID'].max() + index + 1;

    for i in range(len(manual_filter_table_null)):
        _carline_nm_i = manual_filter_table_null['FOOTPRINT_CARLINE_NM'][i];
        _mfr_nm_i = manual_filter_table_null['FOOTPRINT_MFR_NM'][i];
        manual_filter_table.loc[(manual_filter_table['FOOTPRINT_CARLINE_NM'] == _carline_nm_i) & (manual_filter_table['FOOTPRINT_MFR_NM'] == _mfr_nm_i), 'LineageID'] = manual_filter_table_null['LineageID'][i]
        manual_filter_table.loc[(manual_filter_table['FOOTPRINT_CARLINE_NM'] == _carline_nm_i) & (manual_filter_table['FOOTPRINT_MFR_NM'] == _mfr_nm_i), ['CabinID', 'BedID', 'ref_Make', 'ref_Model', 'ref_BedDescription']] = 9999;
        manual_filter_table.loc[(manual_filter_table['FOOTPRINT_CARLINE_NM'] == _carline_nm_i) & (manual_filter_table['FOOTPRINT_MFR_NM'] == _mfr_nm_i), ['BodyID StartYear', 'CabinID StartYear']] = 9;
        manual_filter_table.loc[(manual_filter_table['FOOTPRINT_CARLINE_NM'] == _carline_nm_i) & (manual_filter_table['FOOTPRINT_MFR_NM'] == _mfr_nm_i), \
                                ['BodyDescription', 'BodyID EndYear',	'Last Observed Year_BodyID', 'CabinID EndYear', 'Last Observed Year_CabinID']] = 'null';

    manual_filter_table.loc[manual_filter_table['BodyID'].astype(str) == 'nan', 'BodyID'] = manual_filter_table['LineageID'];

    # manual_filter_table1 = manual_filter_table[~(manual_filter_table[footprint_id_categories+['PROD_VOL_GHG_STD_50_STATE']].duplicated() & manual_filter_table.index.duplicated()) | \
    #                                            manual_filter_table['LineageID'].astype(str).ne('nan')];
    footprint_mfr = manual_filter_table['FOOTPRINT_MFR_NM'].unique();
    footprint_mfr_cd = manual_filter_table['FOOTPRINT_MFR_CD'].unique();
    cafe_mfr_cd = manual_filter_table['CAFE_MFR_CD'].unique();

    list_with_keys = footprint_mfr_cd;
    list_footprint_div_nm = [];
    for i in range(len(footprint_mfr_cd)):
        list_footprint_div_nm.append(list(manual_filter_table.loc[
                                              manual_filter_table['FOOTPRINT_MFR_CD'] == footprint_mfr_cd[i], 'FOOTPRINT_DIVISION_NM'].unique()));

    dict_mfr_cd = dict(zip(list_with_keys, list_footprint_div_nm))
    dict_mfr_cd.update(BMX=['BMW', 'Mini'])
    # dict_mfr_cd.pop('CRX', 'MASERATI')

    _cafe_mfr_cd = footprint_filter_table['CAFE_MFR_CD'].unique();
    _cafe_mfr_nm = footprint_filter_table['CAFE_MFR_NM'].unique();
    _footprint_mfr_cd = footprint_filter_table['FOOTPRINT_MFR_CD'].unique();

    footprint_cafe_mfr_cd = [];
    for i in range(len(_cafe_mfr_cd)):
        footprint_cafe_mfr_cd.append(list(manual_filter_table.loc[
                                              manual_filter_table['CAFE_MFR_CD'] == _cafe_mfr_cd[i], 'FOOTPRINT_MFR_CD'].unique()));
    dict_footprint_cafe_mfr_cd = dict(zip(_cafe_mfr_cd, footprint_cafe_mfr_cd))
    dict_footprint_cafe_mfr_cd.update(CRX=['CRX'])
    dict_footprint_cafe_mfr_cd.update(TYX=['TYX'])

    # footprint_cafe_mfr_cd_errta = pd.DataFrame()
    # df_footprint_cafe_mfr_cd = manual_filter_table.loc[(manual_filter_table['CAFE_MFR_CD']!= manual_filter_table['FOOTPRINT_MFR_CD']), :].reset_index(drop=True)
    #
    # for i in range(len(df_footprint_cafe_mfr_cd)):
    #     _key = df_footprint_cafe_mfr_cd['CAFE_MFR_CD'][i];
    #     _footprint_mfr_cd = df_footprint_cafe_mfr_cd['FOOTPRINT_MFR_CD'][i];
    #     if _footprint_mfr_cd not in dict_footprint_cafe_mfr_cd[_key]:
    #         df_tmp = pd.DataFrame(df_footprint_cafe_mfr_cd.loc[i, :])
    #         footprint_cafe_mfr_cd_errta = pd.concat([footprint_cafe_mfr_cd_errta, df_tmp]);

    footprint_cafe_mfr_cd_errta = pd.DataFrame()
    for i in range(len(_cafe_mfr_cd)):
        _footprint_mfr_cd = list(footprint_filter_table.loc[footprint_filter_table['CAFE_MFR_CD'] == _cafe_mfr_cd[i], 'FOOTPRINT_MFR_CD'].unique());
        if len(_footprint_mfr_cd) > 1:
            for j in range (len(_footprint_mfr_cd)):
                if _footprint_mfr_cd[j] not in dict_footprint_cafe_mfr_cd[_cafe_mfr_cd[i]]:
                    df_tmp = pd.DataFrame(manual_filter_table.loc[(manual_filter_table['FOOTPRINT_MFR_CD'] == _footprint_mfr_cd[j]) & (manual_filter_table['CAFE_MFR_CD'] == _cafe_mfr_cd[i]), :])
                    footprint_cafe_mfr_cd_errta = pd.concat([footprint_cafe_mfr_cd_errta, df_tmp]);
    #
    # footprint_mfr_div_errta = pd.DataFrame(footprint_mfr_div_errta)
    if len(footprint_cafe_mfr_cd_errta) > 0:
        footprint_cafe_mfr_cd_errta_name = 'footprint_cafe_mfr_cd_errta_' + date_and_time + '.csv'
        footprint_cafe_mfr_cd_errta.to_csv(output_path + '\\' + footprint_cafe_mfr_cd_errta_name, index=False)

    footprint_lineageid_MY = manual_filter_table[['MODEL_YEAR','CAFE_ID', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_DIVISION_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_CARLINE_NM', \
                                                 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_INDEX',	'FOOTPRINT_DESC', 'LineageID', 'PROD_VOL_GHG_STD_50_STATE']];
    footprint_lineageid_MY_fname = 'footprint_lineageid_MY_' + date_and_time + '.csv'
    footprint_lineageid_MY.to_csv(output_path + '\\' + footprint_lineageid_MY_fname, index=False);

    bodyID_MY = manual_filter_table[['BodyID', 'BodyDescription', 'LineageID', 'CabinID', 'BodyID StartYear', 'BodyID EndYear', 'Last Observed Year_BodyID',	'CabinID StartYear', 'CabinID EndYear',	\
                                    'Last Observed Year_CabinID', 'BedID', 'ref_Make', 'ref_Model',	'ref_BedDescription',	\
                                    'Wards Projected BodyID StartYear',	'Wards Projected BodyID EndYear', 'Wards Projected Last Observed Year_BodyID', 'Wards Projected CabinID StartYear', \
                                    'Wards Projected CabinID EndYear', 'Wards Projected Last Observed Year_CabinID', 'WARDS_PROJECTION_YN',	'Notes',	\
                                    'Weblink', 'piclink_3/4FR-1', 'piclink_3/4FR-2', 'piclink_3/4RR-1', 'piclink_3/4RR-2', 'piclink_RR-1']];

    bodyID_MY.sort_values(by=['BodyID'], ascending=True,  inplace=True)
    # bodyID_MY = bodyID_MY.loc[bodyID_MY['BodyID'].astype(int) >= _bodyID_MY_start, :];
    bodyID_MY = bodyID_MY.drop_duplicates(subset=['BodyID']).reset_index(drop=True);
    bodyID_MY_fname = 'bodyID_MY_' + date_and_time + '.csv'
    bodyID_MY.to_csv(output_path + '\\' + bodyID_MY_fname, index=False);

    print('total manual_filter_table volumes = ', manual_filter_table['PROD_VOL_GHG_STD_50_STATE'].sum())

    return manual_filter_table

def Subconfig_ModelType_Footprint_Bodyid_Expansion(input_path, footprint_filename, footprint_lineage_filename, bodyid_filename, \
                                                   bool_run_new_manual_filter, manual_filter_name, expanded_footprint_filename, subconfig_filename, model_type_filename, vehghg_filename, output_path, \
                                                   footprint_exceptions_table, modeltype_exceptions_table, subconfig_MY_exceptions_table, subconfig_sales_exceptions_table, \
                                                   tstcar_MY_exceptions_table, year, roadload_coefficient_table_filename, set_bodyid_to_lineageid, \
                                                   drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames, set_roadload_coefficient_table_filename, \
                                                   tstcar_MY_carline_name_mapping_filename):
    global total_volumes_footprint_file;

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

    footprint_id_categories = ['MODEL_YEAR', 'FOOTPRINT_INDEX', 'CAFE_ID', 'FOOTPRINT_CARLINE_CD',
                               'FOOTPRINT_CARLINE_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_DIVISION_NM']
    footprint_indexing_categories = ['FOOTPRINT_DIVISION_NM', 'FOOTPRINT_MFR_CD', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_INDEX']
    subconfig_indexing_categories = ['MFR_DIVISION_NM', 'MODEL_TYPE_INDEX', 'SS_ENGINE_FAMILY', 'CARLINE_CODE', 'LDFE_CAFE_ID', 'BASE_LEVEL_INDEX', 'CONFIG_INDEX', 'SUBCONFIG_INDEX']
    modeltype_indexing_categories = ['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'CAFE_MODEL_YEAR', 'CAFE_MFR_CODE', 'MFR_DIVISION_NM', 'CALC_ID', 'CAFE_ID', 'CARLINE_NAME', 'DRV_SYS']
    roadload_coefficient_table_indexing_categories = ['LDFE_CAFE_SUBCONFIG_INFO_ID', 'LDFE_CAFE_ID', 'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'CAFE_MFR_CD', \
                                                      'LABEL_MFR_CD', 'MODEL_TYPE_INDEX', 'MFR_DIVISION_SHORT_NM', 'CARLINE_NAME', \
                                                      'INERTIA_WT_CLASS', 'CONFIG_INDEX', 'SUBCONFIG_INDEX', 'TRANS_TYPE', 'HYBRID_YN', 'DRV_SYS']
    CAFE_ID_not_matched = []
    for i in range(len(footprint_file['FOOTPRINT_DIVISION_NM'])):
        for j in range(len(lineage_file['FOOTPRINT_DIVISION_NM'])):
            if (footprint_file['FOOTPRINT_DIVISION_NM'][i] == lineage_file['FOOTPRINT_DIVISION_NM'][j]) and (footprint_file['FOOTPRINT_INDEX'][i] == lineage_file['FOOTPRINT_INDEX'][j]) and \
                    (footprint_file['FOOTPRINT_CARLINE_CD'][i] == lineage_file['FOOTPRINT_CARLINE_CD'][j]) and \
                    (footprint_file['FOOTPRINT_CARLINE_NM'][i] == lineage_file['FOOTPRINT_CARLINE_NM'][j]) and (footprint_file['CAFE_ID'][i] != lineage_file['CAFE_ID'][j]):

                CAFE_ID_not_matched.append([footprint_file.loc[i, 'MODEL_YEAR'], footprint_file.loc[i, 'FOOTPRINT_DIVISION_NM'], footprint_file.loc[i, 'FOOTPRINT_CARLINE_NM'], footprint_file.loc[i, 'FOOTPRINT_INDEX'], \
                     footprint_file.loc[i, 'CAFE_ID'], lineage_file.loc[j, 'CAFE_ID']])
    if len(CAFE_ID_not_matched) > 0:
        df_CAFE_ID_not_matched = pd.DataFrame(CAFE_ID_not_matched, columns=['MODEL_YEAR', 'FOOTPRINT_DIVISION_NM', 'FOOTPRINT_CARLINE_NM', 'FOOTPRINT_INDEX', 'Footprint_MY_CAFE_ID', 'footprint-lineageid_CAFE_ID'])
        if CSV_OUTPUT_DEBUG_MODE: df_CAFE_ID_not_matched.to_csv(output_path + '\\' + 'CAFE_ID_lineageid_neq_Footprint_MY' + '_' + date_and_time + '.csv', index=False)

    if len(footprint_exceptions_table) > 0:
        footprint_file = file_errta_update(footprint_filename, footprint_file, footprint_exceptions_table, year, 'Column Name', 'Old Value', 'New Value', 'MODEL_YEAR', 'FOOTPRINT_DIVISION_NM', \
                                           'FOOTPRINT_DIVISION_CD', 'FOOTPRINT_CARLINE_CD', 'CAFE_ID', 'FOOTPRINT_INDEX')
        if CSV_OUTPUT_DEBUG_MODE: footprint_file.to_csv(output_path+'\\'+'Corrected_Footprint_MY_file' + '_' + date_and_time + '.csv', index=False)
        # print('footprint_file volumes = ', footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum(), 'in the', footprint_filename)

    footprint_filter_table = footprint_file[
        list(footprint_id_categories) + ['WHEEL_BASE_INCHES'] + ['FOOTPRINT_DESC'] + ['PROD_VOL_GHG_STD_50_STATE']].merge(
        lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_id_categories)
    if len(footprint_filter_table.loc[pd.isnull(footprint_filter_table['LineageID']), :]) > 0:
        df_null = footprint_filter_table.loc[pd.isnull(footprint_filter_table['LineageID']), :]
    footprint_filter_table = footprint_filter_table.loc[~pd.isnull(footprint_filter_table['LineageID']), :].reset_index(drop=True)

    footprint_file_with_lineage = footprint_file.merge(lineage_file[list(footprint_id_categories) + ['LineageID']], how='left', on=footprint_id_categories)
    footprint_file_with_lineage = footprint_file_with_lineage.loc[~pd.isnull(footprint_file_with_lineage['LineageID']), :].reset_index(drop=True)
    total_volumes_footprint_file = footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum();

    print('total footprint_file volumes = ', footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum())
    print('total footprint_filter_table volumes = ', footprint_filter_table['PROD_VOL_GHG_STD_50_STATE'].sum())
    print('total footprint_file_with_lineage volumes = ', footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'].sum())
    grp_volumes_footprint_file = footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()
    grp_volumes_footprint_file_with_lineage = footprint_file_with_lineage.groupby(['FOOTPRINT_MFR_CD']).sum()

    if CSV_OUTPUT_DEBUG_MODE == True:
        for i in range(min(len(grp_volumes_footprint_file), len(grp_volumes_footprint_file_with_lineage))):
            if grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0) != grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'][i].round(0):
                print(grp_volumes_footprint_file.index[i], grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], grp_volumes_footprint_file_with_lineage['PROD_VOL_GHG_STD_50_STATE'][i])

    full_expanded_footprint_filter_table = footprint_filter_table.merge(body_id_table, how='left', on='LineageID')
    full_expanded_footprint_file = footprint_file_with_lineage.merge(body_id_table, how='left', on='LineageID')
    try:
        # BodyID table is found, no new manual filter sought
        previous_filter_table = pd.read_csv(input_path + '\\' + manual_filter_name, encoding="ISO-8859-1")
        previous_filter_table = previous_filter_table[previous_filter_table['MODEL_YEAR'] == year].drop_duplicates().reset_index(drop=True)
    except OSError:
        # New BodyID table to be made, no previous data
        manual_filter_table = manual_filtering(year, footprint_filter_table, footprint_id_categories, footprint_file, lineage_file, body_id_table, input_path, footprint_lineage_filename, output_path, date_and_time);
        manual_filter_table_save_name = manual_filter_name.replace('.csv', '') + ' ' + date_and_time + '.csv'
        manual_filter_table.to_csv(output_path + '\\' + manual_filter_table_save_name, index=False)
        # full_expanded_footprint_filter_table.to_csv(output_path.replace('\VehghgID', '\intermediate files') + '\\' + full_filter_table_save_name, index=False)
    else:
        if bool_run_new_manual_filter == 'n':
            import math
            from Unit_Conversion import hp2lbfmph, kgpm32slugpft3, mph2ftps, in2m, n2lbf, mph2mps, btu2mj, kg2lbm, \
                ftps2mph, lbfmph2hp, in2mm

            full_expanded_footprint_file = full_expanded_footprint_file.merge(previous_filter_table[list(footprint_id_categories) + ['BodyID'] + ['POSSIBLE_BODYID']], \
                how='left', on=list(footprint_id_categories) + ['BodyID'])
            full_expanded_footprint_file = full_expanded_footprint_file[full_expanded_footprint_file['POSSIBLE_BODYID'] == 'y'].reset_index(drop=True)

            grp_volumes_footprint_file = footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()
            grp_volumes_full_expanded_footprint_file = full_expanded_footprint_file.groupby(['FOOTPRINT_MFR_CD']).sum()

            if CSV_OUTPUT_DEBUG_MODE == True:
                print('full_expanded_footprint_file volumes = ', grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'].sum())
                for i in range(min(len(grp_volumes_footprint_file), len(grp_volumes_full_expanded_footprint_file))):
                    if (grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0) != grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i].round(0)):
                        print(grp_volumes_footprint_file.index[i], grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i], \
                              (grp_volumes_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i] - grp_volumes_full_expanded_footprint_file['PROD_VOL_GHG_STD_50_STATE'][i]))

            # DRV_SYS 4/P, A, F, R
            model_type_file = pd.read_csv(input_path + '\\' + model_type_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan)
            model_type_file = model_type_file[model_type_file['CAFE_MODEL_YEAR'] == year].reset_index(drop=True)
            footprint_id_categories1 = ['MODEL_YEAR', 'FOOTPRINT_CARLINE_CD', 'FOOTPRINT_CARLINE_NM',
                                        'FOOTPRINT_MFR_CD', 'FOOTPRINT_MFR_NM', 'FOOTPRINT_DIVISION_CD',
                                        'FOOTPRINT_DIVISION_NM']
            # No drive system in the CAFE_Subconfig_Sales, but can be extracted from the CARLINE_NAME
            subconfig_file = pd.read_csv(input_path + '\\' + subconfig_filename, encoding="ISO-8859-1", na_values=['-'])  # subconfig_sales # EVCIS Qlik Sense query results contain hyphens for nan
            subconfig_file = subconfig_file[subconfig_file['MODEL_YEAR'] == year].reset_index(drop=True)
            # _test_fuel_type_description = ['Tier 2 Cert Gasoline', 'Federal Cert Diesel 7-15 PPM Sulfur'];
            subconfig_file.insert(20, 'DRV_SYS', np.nan);

            _carline_names = subconfig_file['CARLINE_NAME'].unique()
            for i in range(len(_carline_names)-1):
                _carline_name= _carline_names[i]
                _drive_system = model_type_file.loc[model_type_file['CARLINE_NAME'] == _carline_name, 'DRV_SYS'].dropna().unique()
                if (len(_drive_system) == 1):
                    subconfig_file.loc[subconfig_file['CARLINE_NAME'] == _carline_name, 'DRV_SYS'] = _drive_system[0]
                elif (len(_drive_system) > 1):
                    # print(i, _carline_name, _drive_system)
                    for j in range(len(_drive_system)):
                        _drive_system_j = _drive_system[j]
                        _model_type_index = model_type_file.loc[model_type_file['CARLINE_NAME'] == _carline_name, 'MODEL_TYPE_INDEX'].dropna().unique()[j]
                        subconfig_file.loc[(subconfig_file['CARLINE_NAME'] == _carline_name) & (subconfig_file['MODEL_TYPE_INDEX'] == _model_type_index), 'DRV_SYS'] = _drive_system_j

            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('4WD'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = '4'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('2WD'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'R'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('AWD'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'A'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('FWD'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'F'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('RWD'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'R'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('xDrive'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'A'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('4MATIC'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'A'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('4x4'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = '4'
            subconfig_file.loc[subconfig_file['CARLINE_NAME'].str.contains(('4x2'), case=False, na=False)  & (pd.isnull(subconfig_file['DRV_SYS'])), 'DRV_SYS'] = 'R'
            subconfig_file = subconfig_file.dropna(axis=1, how='all').reset_index(drop=True)

            if len(modeltype_exceptions_table) > 0:
                if DEBUGGING_CAFE_MFR_CD_MODE: model_type_file = model_type_file.loc[model_type_file['CAFE_MFR_CODE'] == DEBUGGING_CAFE_MFR_CD, :]
                model_type_file = file_errta_update(model_type_filename, model_type_file, modeltype_exceptions_table, year, 'Column Name', 'Old Value', 'New Value', 'CAFE_MODEL_YEAR',  \
                                                    'MFR_DIVISION_NM', 'CAFE_MFR_CODE', 'CARLINE_NAME', 'CAFE_ID', 'MODEL_TYPE_INDEX')
                model_type_file['CALC_ID'] = model_type_file['CALC_ID'].astype(int)
                if CSV_OUTPUT_DEBUG_MODE: model_type_file.to_csv(output_path+'\\'+'Corrected_CAFE_Model_Type_MY_file'+ '_' + date_and_time + '.csv', index=False)
                # print('FUEL_USAGE', len(model_type_file[model_type_file['FUEL_USAGE'] == 'n']))
            if len(subconfig_sales_exceptions_table) > 0:
                if DEBUGGING_CAFE_MFR_CD_MODE: subconfig_file = subconfig_file.loc[subconfig_file['CAFE_MFR_CD'] == DEBUGGING_CAFE_MFR_CD, :]
                subconfig_file = file_errta_update(subconfig_filename, subconfig_file, subconfig_sales_exceptions_table, year, 'Column Name', 'Old Value', 'New Value', 'MODEL_YEAR',  \
                                                   'MFR_DIVISION_SHORT_NM', 'CAFE_MFR_CD', 'CARLINE_NAME', 'LDFE_CAFE_ID', 'MODEL_TYPE_INDEX')
                subconfig_file['LDFE_CAFE_MODEL_TYPE_CALC_ID'] = subconfig_file['LDFE_CAFE_MODEL_TYPE_CALC_ID'].astype(int)
                if CSV_OUTPUT_DEBUG_MODE: subconfig_file.to_csv(output_path+'\\'+'Corrected_CAFE_Subconfig_Sales_MY_file'+ '_' + date_and_time + '.csv', index=False)
            vehghg_file_data_pt1 = subconfig_file.merge(full_expanded_footprint_file, how='left', \
                                                        left_on=['MODEL_YEAR', 'CARLINE_CODE', 'CAFE_MFR_CD', 'MFR_DIVISION_NM'], \
                                                        right_on=['MODEL_YEAR', 'FOOTPRINT_CARLINE_CD', 'CAFE_MFR_CD', 'FOOTPRINT_DIVISION_NM'])

            vehghg_file_full_merged_data = vehghg_file_data_pt1.merge(model_type_file, how='left', left_on=['MODEL_TYPE_INDEX', 'CARLINE_CODE', 'MODEL_YEAR', 'CAFE_MFR_CD', 'MFR_DIVISION_NM', \
                                                                               'LDFE_CAFE_MODEL_TYPE_CALC_ID', 'LDFE_CAFE_ID', 'CARLINE_NAME', 'DRV_SYS'], right_on=modeltype_indexing_categories)
            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file_full_merged_data', vehghg_file_full_merged_data, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            vehghg_file_data = vehghg_file_full_merged_data[vehghg_file_full_merged_data['SS_LD_CARLINE_HEADER_ID'] == vehghg_file_full_merged_data['LD_CARLINE_HEADER_ID']].reset_index(drop=True)
            vehghg_file = vehghg_file_data.dropna(subset=list(footprint_indexing_categories) + list(subconfig_indexing_categories), how='any').reset_index(drop=True)
            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file', vehghg_file, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            missing_entries_1 = vehghg_file[pd.isnull(vehghg_file['LineageID'])].reset_index(drop=True)
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

            if DEBUGGING_CAFE_MFR_CD_MODE != True:
                check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

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

            # DRIVE_SYSTEM 4/P, A, F, R, - in the CAFE_Subconfig_MY file
            roadload_coefficient_table = pd.read_csv(input_path + '\\' + roadload_coefficient_table_filename, encoding="ISO-8859-1", na_values=['-'])  # EVCIS Qlik Sense query results contain hyphens for nan
            roadload_coefficient_table = roadload_coefficient_table[roadload_coefficient_table['MODEL_YEAR'] == year].reset_index(drop=True)
            if len(subconfig_MY_exceptions_table) > 0:
                if DEBUGGING_CAFE_MFR_CD_MODE: roadload_coefficient_table = roadload_coefficient_table.loc[roadload_coefficient_table['CAFE_MFR_CD'] == DEBUGGING_CAFE_MFR_CD, :]
                roadload_coefficient_table = file_errta_update(roadload_coefficient_table_filename, roadload_coefficient_table, subconfig_MY_exceptions_table, year, 'Column Name', 'Old Value', 'New Value', 'MODEL_YEAR',  \
                                                               'MFR_DIVISION_SHORT_NM', 'CAFE_MFR_CD', 'CARLINE_NAME', 'LDFE_CAFE_ID', 'MODEL_TYPE_INDEX')
                roadload_coefficient_table['LDFE_CAFE_MODEL_TYPE_CALC_ID'] = roadload_coefficient_table['LDFE_CAFE_MODEL_TYPE_CALC_ID'].astype(int)
                if CSV_OUTPUT_DEBUG_MODE: roadload_coefficient_table.to_csv(output_path+'\\'+'Corrected_CAFE_Subconfig_MY_file' + '_' + date_and_time + '.csv', index=False)

            roadload_coefficient_table = roadload_coefficient_table[roadload_coefficient_table['MODEL_YEAR'] == year].groupby(['LDFE_CAFE_SUBCONFIG_INFO_ID', 'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', \
                          'FUEL_NET_HEATING_VALUE', 'FUEL_GRAVITY']).first().reset_index().drop('MODEL_YEAR', axis=1).reset_index(drop=True)
            roadload_coefficient_table = roadload_coefficient_table.rename({'DRIVE_SYSTEM': 'DRV_SYS'}, axis=1)

            roadload_coefficient_table_nonflexfuel = roadload_coefficient_table[roadload_coefficient_table['SUBCFG_FUEL_USAGE'] != 'E'].reset_index(drop=True)
            vehghg_file_flexfuel = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['FUEL_USAGE'] == 'E'].reset_index(drop=True)
            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['FUEL_USAGE'] != 'E'].reset_index(drop=True)

            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.merge(roadload_coefficient_table_nonflexfuel, how='left', on=list(roadload_coefficient_table_indexing_categories))

            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            set_roadload_coefficient_table_indexing_categories = ['Model Year', 'Veh Mfr Code', 'Represented Test Veh Make', 'Represented Test Veh Model', 'Test Vehicle ID', 'Test Veh Configuration #', 'Test Number', \
                                                                  'Test Category', 'Rated Horsepower', 'Equivalent Test Weight (lbs.)', 'Test Veh Displacement (L)', 'Actual Tested Testgroup', '# of Gears', 'Drive System Code', 'N/V Ratio', \
                                                                  'CO2 (g/mi)', 'RND_ADJ_FE', 'FE Bag 1', 'FE Bag 2', 'FE Bag 3', 'FE Bag 4', 'US06_FE', 'US06_FE Bag 1', 'US06_FE Bag 2', \
                                                                  'Target Coef A (lbf)', 'Target Coef B (lbf/mph)', 'Target Coef C (lbf/mph**2)', \
                                                                  'Set Coef A (lbf)', 'Set Coef B (lbf/mph)', 'Set Coef C (lbf/mph**2)']
            set_roadload_coefficient_table = pd.read_csv(input_path + '\\' + set_roadload_coefficient_table_filename, encoding="ISO-8859-1", na_values=['-'])

            _test_category = ['FTP', 'HWY', 'US06']; # Test Category
            _test_fuel_type_description = ['Tier 2 Cert Gasoline', 'Federal Cert Diesel 7-15 PPM Sulfur']; #'Test Fuel Type Description'
            set_roadload_coefficient_table = set_roadload_coefficient_table.loc[set_roadload_coefficient_table['Test Category'].str.contains('|'.join(_test_category), case=False, na=False), :]
            set_roadload_coefficient_table = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Procedure Description'] != 'Fed. fuel 50 F exh.') & \
                                                                                (set_roadload_coefficient_table['Test Procedure Description'] != 'Cold CO') & \
                                                                                (set_roadload_coefficient_table['Test Procedure Description'] != "CVS 75 and later (w/o can. load)") & \
                                                                                (set_roadload_coefficient_table['Test Procedure Description'] != "California fuel 2-day exhaust (w/can load)") & \
                                                                                (set_roadload_coefficient_table['Test Procedure Description'] != 'California fuel 3-day exhaust'), :]
            set_roadload_coefficient_table = set_roadload_coefficient_table.dropna(axis=1, how='all').reset_index(drop=True)
            set_roadload_coefficient_table.insert(51, 'US06_FE', float('nan')); set_roadload_coefficient_table.insert(52, 'US06_FE_Bag 1', float('nan')); set_roadload_coefficient_table.insert(53, 'US06_FE_Bag 2', float('nan'));
            set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE'] = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Category'] == 'US06'), 'RND_ADJ_FE']
            set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE Bag 1'] = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Category'] == 'US06'), 'FE Bag 1']
            set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE Bag 2'] = set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Category'] == 'US06'), 'FE Bag 2']

            _test_vehicle_IDs = set_roadload_coefficient_table['Test Vehicle ID'].unique();
            for i in range(len(_test_vehicle_IDs)):
                _test_veh_ID = _test_vehicle_IDs[i]
                if len(set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE Bag 1'])  > 0:
                    set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'FTP'), 'US06_FE'] = \
                        set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE'].values[0];
                    set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'FTP'), 'US06_FE Bag 1'] = \
                        set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE Bag 1'].values[0];
                    set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'FTP'), 'US06_FE Bag 2'] = \
                        set_roadload_coefficient_table.loc[(set_roadload_coefficient_table['Test Vehicle ID'] == _test_veh_ID) & (set_roadload_coefficient_table['Test Category'] == 'US06'), 'US06_FE Bag 2'].values[0];

            if len(tstcar_MY_exceptions_table) > 0:
                set_roadload_coefficient_table = file_errta_update('tstcar_MY_errta', set_roadload_coefficient_table, tstcar_MY_exceptions_table, year, 'Column Name', 'Old Value', 'New Value', 'Model Year', \
                                                               'Represented Test Veh Make', 'Veh Mfr Code', 'Represented Test Veh Model', np.nan, np.nan)
                if DEBUGGING_CAFE_MFR_CD_MODE: set_roadload_coefficient_table = set_roadload_coefficient_table.loc[set_roadload_coefficient_table['Veh Mfr Code'] == DEBUGGING_CAFE_MFR_CD, :]
                if CSV_OUTPUT_DEBUG_MODE: set_roadload_coefficient_table.to_csv(output_path+'\\'+'Corrected_set_roadload_coefficient_table' + '_' + date_and_time + '.csv', index=False)

            set_roadload_coefficient_table = set_roadload_coefficient_table[set_roadload_coefficient_table_indexing_categories]
            set_roadload_coefficient_table = set_roadload_coefficient_table.rename({'Set Coef A (lbf)': 'SET_COEF_A', 'Set Coef B (lbf/mph)': 'SET_COEF_B', 'Set Coef C (lbf/mph**2)': 'SET_COEF_C'}, axis=1)
            set_roadload_coefficient_table = set_roadload_coefficient_table.rename({'FE Bag 1': 'FTP_FE Bag 1', 'FE Bag 2': 'FTP_FE Bag 2', 'FE Bag 3': 'FTP_FE Bag 3', 'FE Bag 4': 'FTP_FE Bag 4'}, axis=1)

            vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_A'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_B_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_B'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_C_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_C'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'] = pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['TARGET_COEF_B_SURRO'] = pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['TARGET_COEF_C_SURRO'] = pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] =  pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'] = vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE'].copy()
            vehghg_file_nonflexfuel['FUEL_GRAVITY_BEST'] = vehghg_file_nonflexfuel['FUEL_GRAVITY'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_MERGING_MTH'] =  pd.Series(np.zeros(len(vehghg_file_nonflexfuel)))
            vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'])), 'TARGET_COEF_BEST_MTH'] = np.nan
            vehghg_file_nonflexfuel['TOT_ROAD_LOAD_HP_SURRO'] = vehghg_file_nonflexfuel['TOT_ROAD_LOAD_HP'].copy()
            vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'] = vehghg_file_nonflexfuel['TARGET_COEF_B_SURRO'] = vehghg_file_nonflexfuel['TARGET_COEF_C_SURRO'] = vehghg_file_nonflexfuel['TARGET_COEF_MERGING_MTH'] = np.nan

            vehghg_file_nonflexfuel['ENG_RATED_HP'] = pd.to_numeric(vehghg_file_nonflexfuel['ENG_RATED_HP'], errors='coerce')
            set_roadload_coefficient_table['Rated Horsepower'] = pd.to_numeric(set_roadload_coefficient_table['Rated Horsepower'], errors='coerce')

            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.merge(set_roadload_coefficient_table, how='left', \
                                                                    left_on=['CAFE_MFR_CD', 'TEST_NUMBER', 'TEST_PROC_CATEGORY'], right_on=['Veh Mfr Code', 'Test Number', 'Test Category'])
            vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['Target Coef A (lbf)']) == True), 'TARGET_COEF_MERGING_MTH'] = 2

            _target_coef_rated_hp_checks = (~pd.isnull(vehghg_file_nonflexfuel['Target Coef A (lbf)']) == True) & (vehghg_file_nonflexfuel['CAFE_MFR_CD'] == vehghg_file_nonflexfuel['Veh Mfr Code']) & \
                                           (vehghg_file_nonflexfuel['TEST_NUMBER'] == vehghg_file_nonflexfuel['Test Number']) & (vehghg_file_nonflexfuel['TEST_PROC_CATEGORY'] == vehghg_file_nonflexfuel['Test Category']) & \
                                           (vehghg_file_nonflexfuel['ENG_RATED_HP'] == vehghg_file_nonflexfuel['Rated Horsepower']) & ((~pd.isnull(vehghg_file_nonflexfuel['ENG_RATED_HP'])) == True)
            vehghg_file_nonflexfuel.loc[_target_coef_rated_hp_checks, :].merge(set_roadload_coefficient_table, how='left', \
                                                                    left_on=['CAFE_MFR_CD', 'TEST_NUMBER', 'TEST_PROC_CATEGORY', 'ENG_RATED_HP'], \
                                                                    right_on=['Veh Mfr Code', 'Test Number', 'Test Category', 'Rated Horsepower'])
            vehghg_file_nonflexfuel.loc[_target_coef_rated_hp_checks, 'TARGET_COEF_MERGING_MTH'] = 1

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

            if (_target_coef_from_set_roadload_coefficient_table.sum() > 0) or (_target_coef_from_engine_family_etw.sum() > 0):
                vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['SET_COEF_A'])), 'TARGET_COEF_BEST_MTH'] = 0
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_A'] = vehghg_file_nonflexfuel['Target Coef A (lbf)']
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_B'] = vehghg_file_nonflexfuel['Target Coef B (lbf/mph)']
                vehghg_file_nonflexfuel.loc[_target_coef_from_set_roadload_coefficient_table, 'TARGET_COEF_C'] = vehghg_file_nonflexfuel['Target Coef C (lbf/mph**2)']
                vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_A']
                vehghg_file_nonflexfuel['TARGET_COEF_B_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_B']
                vehghg_file_nonflexfuel['TARGET_COEF_C_BEST'] = vehghg_file_nonflexfuel['TARGET_COEF_C']
                vehghg_file_nonflexfuel['SET_COEF_A_BEST'] = vehghg_file_nonflexfuel['SET_COEF_A']
                vehghg_file_nonflexfuel['SET_COEF_B_BEST'] = vehghg_file_nonflexfuel['SET_COEF_B']
                vehghg_file_nonflexfuel['SET_COEF_C_BEST'] = vehghg_file_nonflexfuel['SET_COEF_C']
                vehghg_file_nonflexfuel['NV_RATIO_BEST'] = vehghg_file_nonflexfuel['N/V Ratio']
                vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'] = vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE']
                vehghg_file_nonflexfuel['FUEL_GRAVITY_BEST'] = vehghg_file_nonflexfuel['FUEL_GRAVITY']

            vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[:, ~vehghg_file_nonflexfuel.columns.duplicated()]
            vehghg_file_nonflexfuel.loc[pd.isnull(vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_GHG_1']) & (vehghg_file_nonflexfuel['Electrification Category'] != 'EV') & \
                                        (vehghg_file_nonflexfuel['Electrification Category'] != 'FCV') & (vehghg_file_nonflexfuel['CO2 (g/mi)'] > 0), 'EPA_CAFE_MT_CALC_COMB_GHG_1'] = vehghg_file_nonflexfuel['CO2 (g/mi)']
            print('')
            print('# of TARGET_COEF_BEST_MTH = 0 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 0]), ')')
            print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())
            print('')

            vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == 'TSL') & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'n'), 'Fuel Type Category'] = 'E'# delete no fuel vehicles
            vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == 'TSL') & (vehghg_file_nonflexfuel['Electrification Category'] == 'N'), 'Electrification Category'] = 'EV'# delete no fuel vehicles
            vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == 'TSL') & (vehghg_file_nonflexfuel['Boost Type Category'] == 'N'), 'Boost Type Category'] = 'ELE'# delete no fuel vehicles
            vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == 'TSL') & (pd.isnull(vehghg_file_nonflexfuel['Drivetrain Layout Category'])), 'Drivetrain Layout Category'] = '4WD'# delete no fuel vehicles
            vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == 'TSL') & (pd.isnull(vehghg_file_nonflexfuel['Transmission Type Category'])), 'Transmission Type Category'] = '1ST'# delete no fuel vehicles

            df_Cafe_MFR_CD_Mode_Type_Index = vehghg_file_nonflexfuel.groupby(['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'CARLINE_NAME']).mean()
            for i in range(len(df_Cafe_MFR_CD_Mode_Type_Index)):
                _cafe_mfr_cd = df_Cafe_MFR_CD_Mode_Type_Index.index[i][0]
                _model_type_index = df_Cafe_MFR_CD_Mode_Type_Index.index[i][1]
                _carline_name = df_Cafe_MFR_CD_Mode_Type_Index.index[i][2]
                df_vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[(vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & \
                                                                                     (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index) & \
                                                                                     (vehghg_file_nonflexfuel['CARLINE_NAME'] == _carline_name), :]
                if len(df_vehghg_file_nonflexfuel[df_vehghg_file_nonflexfuel['Fuel Type Category'] == 'n']) > 0:
                    df_vehghg_file_nonflexfuel_index = list(df_vehghg_file_nonflexfuel.index)
                    _electrification_category = df_vehghg_file_nonflexfuel.loc[df_vehghg_file_nonflexfuel['Electrification Category'] != 'N', 'Electrification Category']
                    _fuel_category = df_vehghg_file_nonflexfuel.loc[df_vehghg_file_nonflexfuel['Fuel Type Category'] != 'n', 'Fuel Type Category']
                    if len(_electrification_category) > 0:
                        _index_electrification = df_vehghg_file_nonflexfuel.loc[df_vehghg_file_nonflexfuel['Electrification Category'] == 'N', 'Electrification Category'].index
                        vehghg_file_nonflexfuel.loc[_index_electrification, 'Electrification Category']  = _electrification_category[df_vehghg_file_nonflexfuel_index[0]]
                    if len(_fuel_category) > 0:
                        _index_fuel = df_vehghg_file_nonflexfuel.loc[df_vehghg_file_nonflexfuel['Fuel Type Category'] == 'n', 'Fuel Type Category'].index
                        vehghg_file_nonflexfuel.loc[_index_fuel, 'Fuel Type Category']  = _fuel_category[df_vehghg_file_nonflexfuel_index[0]]

                    if (len(_electrification_category) == 0) and ("HYBRID" in _carline_name):
                        _index_hybrid = df_vehghg_file_nonflexfuel.loc[df_vehghg_file_nonflexfuel['CARLINE_NAME'] == _carline_name, 'CARLINE_NAME'].index
                        for j in range(len(_index_hybrid)):
                            vehghg_file_nonflexfuel.loc[_index_hybrid[j], 'Electrification Category'] = 'HEV'
                            if vehghg_file_nonflexfuel.loc[_index_hybrid[j], 'Fuel Type Category'] == 'n':
                                vehghg_file_nonflexfuel.loc[_index_hybrid[j], 'Fuel Type Category'] = 'G'
                                if 'DIESEL' in _carline_name: vehghg_file_nonflexfuel.loc[_index_hybrid[j], 'Fuel Type Category'] = 'D'

            vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'n', 'Fuel Type Category'] = 'G'
            _target_coef_indexing_category = ['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'MFR_DIVISION_SHORT_NM', 'CARLINE_NAME', 'SS_ENGINE_FAMILY', 'ENG_DISPL', 'TOTAL_NUM_TRANS_GEARS', 'ETW', 'BodyID', 'TOT_ROAD_LOAD_HP', 'VEH_TOT_ROAD_LOAD_HP', \
                                              'TARGET_COEF_MERGING_MTH', 'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', 'NV_RATIO', 'SET_COEF_A', 'SET_COEF_B', 'SET_COEF_C', 'ENG_RATED_HP', \
                                              'FUEL_NET_HEATING_VALUE', 'FUEL_GRAVITY', 'Boost Type Category']
            _target_coef_surro_indexing_category = ['MODEL_YEAR', 'CAFE_MFR_CD', 'LABEL_MFR_CD', 'MODEL_TYPE_INDEX', 'CARLINE_NAME', 'MFR_DIVISION_SHORT_NM', 'SS_ENGINE_FAMILY', 'ENG_DISPL', 'TOTAL_NUM_TRANS_GEARS', 'ETW', 'BodyID', 'VEH_TOT_ROAD_LOAD_HP', 'TOT_ROAD_LOAD_HP', \
                                                    'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', 'NV_RATIO', 'TARGET_COEF_BEST_MTH', 'TARGET_COEF_A_SURRO', 'TARGET_COEF_B_SURRO', 'TARGET_COEF_C_SURRO', \
                                                    'SET_COEF_A', 'SET_COEF_B', 'SET_COEF_C', 'SET_COEF_A_SURRO', 'SET_COEF_B_SURRO', 'SET_COEF_C_SURRO', 'TEST_PROC_CATEGORY', 'TARGET_COEF_MERGING_MTH', 'ENG_RATED_HP', \
                                                    'FUEL_NET_HEATING_VALUE', 'FUEL_GRAVITY', 'Boost Type Category']
            df_Cafe_MFR_CD_Mode_Type_Index = vehghg_file_nonflexfuel[pd.isnull(vehghg_file_nonflexfuel['SET_COEF_A'])].groupby(['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'CARLINE_NAME']).mean()
            for i in range(len(df_Cafe_MFR_CD_Mode_Type_Index)):
                try:
                    _cafe_mfr_cd = df_Cafe_MFR_CD_Mode_Type_Index.index[i][0]
                    _model_type_index = df_Cafe_MFR_CD_Mode_Type_Index.index[i][1]
                    _carline_name = df_Cafe_MFR_CD_Mode_Type_Index.index[i][2]
                    _cafe_mfr_cd_model_type_index_carline_name_only = (vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index) & (vehghg_file_nonflexfuel['CARLINE_NAME'] == _carline_name)
                    df_vehghg_file_nonflexfuel_target_coef = vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, _target_coef_indexing_category]
                    df_vehghg_file_nonflexfuel_target_coef_index = list(df_vehghg_file_nonflexfuel_target_coef.index)
                    df_vehghg_file_nonflexfuel_target_coef.reset_index(drop=True, inplace=True)
                    _boost_types = df_vehghg_file_nonflexfuel_target_coef['Boost Type Category'].unique();
                    # _boost_type = df_vehghg_file_nonflexfuel_target_coef.loc[df_vehghg_file_nonflexfuel_target_coef['Boost Type Category'] != 'N', 'Boost Type Category']
                    # _no_boost = df_vehghg_file_nonflexfuel_target_coef.loc[df_vehghg_file_nonflexfuel_target_coef['Boost Type Category'] == 'N', 'Boost Type Category']
                    # if _boost_type.shape[0] > 0: df_vehghg_file_nonflexfuel_target_coef.loc[df_vehghg_file_nonflexfuel_target_coef['Boost Type Category'] != 'N', 'Boost Type Category'] = _boost_type[_boost_type.index[0]]
                    # if _no_boost.shape[0] > 0: df_vehghg_file_nonflexfuel_target_coef.loc[df_vehghg_file_nonflexfuel_target_coef['Boost Type Category'] == 'N', 'Boost Type Category'] = _no_boost[_no_boost.index[0]]
                    if (CSV_OUTPUT_DEBUG_MODE == True) and (len(_boost_types) > 1): print('Boost Types: ', _cafe_mfr_cd, _model_type_index, df_vehghg_file_nonflexfuel_target_coef.loc[0, 'CARLINE_NAME'], _boost_types)
                except KeyError:
                    print("Check the _cafe_mfr_cd")
                for k in range (len(df_vehghg_file_nonflexfuel_target_coef)):
                    try:
                        _index = df_vehghg_file_nonflexfuel_target_coef_index[k]
                        _target_coef_merging_mth = df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_MERGING_MTH']
                        if (_target_coef_merging_mth == 1) or (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] == 0): continue
                        _tot_road_load_hp = df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TOT_ROAD_LOAD_HP']
                        df_sort = df_vehghg_file_nonflexfuel_target_coef.iloc[(df_vehghg_file_nonflexfuel_target_coef['VEH_TOT_ROAD_LOAD_HP'] - _tot_road_load_hp).abs().argsort()[:1]]
                        _index_df_sort = df_sort.index.tolist()[0]
                        if df_sort.shape[0] == 0:
                            print(k, _cafe_mfr_cd, _model_type_index, df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_A'])
                            continue
                    except KeyError:
                        print("Check the df_sort")

                    try:
                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_A']
                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_B']
                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_C']
                    except KeyError:
                        print("Check the TARGET_COEF_A")

                    if pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE']) and (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['FUEL_NET_HEATING_VALUE']).sum() > 0):
                        vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE_BEST'] = df_vehghg_file_nonflexfuel_target_coef['FUEL_NET_HEATING_VALUE'].mean()
                        vehghg_file_nonflexfuel.loc[_index, 'FUEL_GRAVITY_BEST'] = df_vehghg_file_nonflexfuel_target_coef['FUEL_GRAVITY'].mean()
                    if ESTIMATE_NV_RATIO_SET_COEF_ABC_BY_ROAD_LOAD_HP:
                        try:
                            vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'NV_RATIO']
                            vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'SET_COEF_A']
                            vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'SET_COEF_B']
                            vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'SET_COEF_C']
                            vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP_SURRO'] = df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TOT_ROAD_LOAD_HP']
                        except KeyError:
                            print("Check the SET_COEF_A")

                    if (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO'] < 0):
                        print(k, _cafe_mfr_cd, df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'CARLINE_NAME'], _model_type_index, \
                              _index_df_sort, _index, df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_A'], \
                              vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO'])

            vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO']) == True) & (pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'])), 'TARGET_COEF_BEST_MTH'] = 1
            del df_Cafe_MFR_CD_Mode_Type_Index, df_vehghg_file_nonflexfuel_target_coef, df_vehghg_file_nonflexfuel_target_coef_index
            print('# of TARGET_COEF_BEST_MTH = 1 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 1]), ')')
            print('# of TARGET_COEF_A', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A'])).sum())
            print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())
            print('')

            df_Cafe_MFR_CD_Mode_Type_Index = vehghg_file_nonflexfuel[(pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A']))].groupby(['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'CARLINE_NAME']).mean()
            for i in range(len(df_Cafe_MFR_CD_Mode_Type_Index)):
                _cafe_mfr_cd = df_Cafe_MFR_CD_Mode_Type_Index.index[i][0]
                _model_type_index = df_Cafe_MFR_CD_Mode_Type_Index.index[i][1]
                _carline_name = df_Cafe_MFR_CD_Mode_Type_Index.index[i][2]
                _cafe_mfr_cd_model_type_index_carline_name_only = (vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index) & (vehghg_file_nonflexfuel['CARLINE_NAME'] == _carline_name)
                _bodyid = vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, 'BodyID'].unique()
                _engine_family = vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, 'SS_ENGINE_FAMILY'].unique()
                _etw = vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, 'ETW'].unique()
                if len(_engine_family) == 0: continue
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
                                df_vehghg_file_nonflexfuel_target_coef_RL = df_vehghg_file_nonflexfuel_target_coef.loc[(~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['TARGET_COEF_A']) == True) & \
                                                                                                                       (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['VEH_TOT_ROAD_LOAD_HP']) == True), \
                                                                                                                       _target_coef_surro_indexing_category]
                                if len(df_vehghg_file_nonflexfuel_target_coef_RL) == 0: continue
                                df_vehghg_file_nonflexfuel_target_coef_RL.reset_index(drop=True, inplace=True)
                                if (pd.isnull(df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_A_SURRO']) == False) or \
                                        (((df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_BEST_MTH'] == 1) | \
                                          (df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_BEST_MTH'] == 1)) & (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TARGET_COEF_A'])) == True):
                                    continue
                                df_sort = df_vehghg_file_nonflexfuel_target_coef_RL.iloc[(df_vehghg_file_nonflexfuel_target_coef_RL['VEH_TOT_ROAD_LOAD_HP']-df_vehghg_file_nonflexfuel_target_coef.loc[k, 'TOT_ROAD_LOAD_HP']).abs().argsort()[:1]]
                                _index_df_sort = df_sort.index.tolist()[0]
                                _index = df_vehghg_file_nonflexfuel_target_coef_index[k]
                                if (pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'])): pass
                                else: continue
                                if (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] >= 0) and (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] <= 1): continue
                                if _index_df_sort >= len(df_vehghg_file_nonflexfuel_target_coef_RL):
                                    print('_index_df_sort is greater than length of the array', k, _index_df_sort)
                                    continue
                                if df_vehghg_file_nonflexfuel_target_coef.loc[_index_df_sort, 'TARGET_COEF_A'] < 0:
                                    print(_cafe_mfr_cd, _model_type_index)
                                vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TARGET_COEF_A']
                                vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TARGET_COEF_B']
                                vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TARGET_COEF_C']
                                if pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE']) and (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['FUEL_NET_HEATING_VALUE']).sum() > 0):
                                    vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE_BEST'] = df_vehghg_file_nonflexfuel_target_coef_RL['FUEL_NET_HEATING_VALUE'].mean()
                                    vehghg_file_nonflexfuel.loc[_index, 'FUEL_GRAVITY_BEST'] = df_vehghg_file_nonflexfuel_target_coef_RL['FUEL_GRAVITY'].mean()
                                if ESTIMATE_NV_RATIO_SET_COEF_ABC_BY_ROAD_LOAD_HP:
                                    vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'NV_RATIO']
                                    vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'SET_COEF_A']
                                    vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'SET_COEF_B']
                                    vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'SET_COEF_C']
                                vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP_SURRO'] = df_vehghg_file_nonflexfuel_target_coef_RL.loc[_index_df_sort, 'TOT_ROAD_LOAD_HP']

            vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO']) == True) & (pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'])), 'TARGET_COEF_BEST_MTH'] = 2

            del df_Cafe_MFR_CD_Mode_Type_Index
            print('# of TARGET_COEF_BEST_MTH = 2 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 2]), ')')
            print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())
            print('')

            if ESTIMATE_TARGET_COEF_BEST_MTH_3_4:
                tstcar_MY_carline_name_mapping_table = pd.read_csv(input_path + '\\' + tstcar_MY_carline_name_mapping_filename, encoding="ISO-8859-1", na_values=['-'])
                tstcar_MY_carline_name_mapping_table = tstcar_MY_carline_name_mapping_table.applymap(lambda s: s.upper() if type(s) == str else s)
                set_roadload_coefficient_table = set_roadload_coefficient_table.applymap(lambda s: s.upper() if type(s) == str else s)

                df_target_coef_null = vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])), :]
                df_target_coef_null_index = list(df_target_coef_null.index)
                df_target_coef_null.reset_index(drop=True, inplace=True)
                _engine_displacement_check = 'strict'

                df_Cafe_MFR_CD_Mode_Type_Index = vehghg_file_nonflexfuel[pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])].groupby(['CAFE_MFR_CD', 'MODEL_TYPE_INDEX', 'CARLINE_NAME']).mean()
                for i in range(len(df_Cafe_MFR_CD_Mode_Type_Index)):
                    _cafe_mfr_cd = df_Cafe_MFR_CD_Mode_Type_Index.index[i][0]
                    _model_type_index = df_Cafe_MFR_CD_Mode_Type_Index.index[i][1]
                    _carline_name = df_Cafe_MFR_CD_Mode_Type_Index.index[i][2]
                    _cafe_mfr_cd_model_type_index_carline_name_only = (vehghg_file_nonflexfuel['CAFE_MFR_CD'] == _cafe_mfr_cd) & (vehghg_file_nonflexfuel['MODEL_TYPE_INDEX'] == _model_type_index) & (vehghg_file_nonflexfuel['CARLINE_NAME'] == _carline_name)
                    _engine_displacement = vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, 'ENG_DISPL'].unique()
                    _etw = vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, 'ETW'].unique()
                    _rated_hp = pd.to_numeric(vehghg_file_nonflexfuel.loc[_cafe_mfr_cd_model_type_index_carline_name_only, 'ENG_RATED_HP'].unique(), errors='coerce')
                    for j in range (len(_engine_displacement)):
                        _engine_displacement_j = _engine_displacement[j]
                        if (pd.isnull(_engine_displacement_j)): continue
                        for k in range(len(_etw)):
                            _etw_k = _etw[k]
                            if (pd.isnull(_etw_k)): continue
                            try:
                                df_vehghg_file_nonflexfuel_target_coef = vehghg_file_nonflexfuel.loc[(_cafe_mfr_cd_model_type_index_carline_name_only) &  \
                                                            (vehghg_file_nonflexfuel['ENG_DISPL'] == _engine_displacement_j) & (vehghg_file_nonflexfuel['ETW'] == _etw_k), _target_coef_surro_indexing_category]
                            except KeyError:
                                print("Check the ENG_DISPL & ETW")

                            if len(pd.isnull(df_vehghg_file_nonflexfuel_target_coef['TARGET_COEF_A_SURRO'])) == 0: continue
                            df_vehghg_file_nonflexfuel_target_coef_index = list(df_vehghg_file_nonflexfuel_target_coef.index)
                            df_vehghg_file_nonflexfuel_target_coef.reset_index(drop=True, inplace=True)
                            tstcar_checks = (set_roadload_coefficient_table['Veh Mfr Code'] == _cafe_mfr_cd) & (set_roadload_coefficient_table['Represented Test Veh Model'] == _carline_name)
                            if (tstcar_checks & (set_roadload_coefficient_table['Test Veh Displacement (L)'] == _engine_displacement_j)).sum() > 0:
                                tstcar_checks = tstcar_checks & (set_roadload_coefficient_table['Test Veh Displacement (L)'] == _engine_displacement_j)
                            if (tstcar_checks & (set_roadload_coefficient_table['Equivalent Test Weight (lbs.)'] == _etw_k)).sum() > 0:
                                tstcar_checks = tstcar_checks & (set_roadload_coefficient_table['Equivalent Test Weight (lbs.)'] == _etw_k) & \
                                                (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']) == True)
                            else:
                                tstcar_checks = tstcar_checks &  (~pd.isnull(set_roadload_coefficient_table['Target Coef A (lbf)']) == True)

                            if tstcar_checks.sum() == 0:
                                try:
                                    _num_trans_gears = df_vehghg_file_nonflexfuel_target_coef.loc[j, 'TOTAL_NUM_TRANS_GEARS']
                                    _model_year = df_vehghg_file_nonflexfuel_target_coef.loc[j, 'MODEL_YEAR']
                                    _label_mfr_cd = df_vehghg_file_nonflexfuel_target_coef.loc[j, 'LABEL_MFR_CD']
                                    _mfr_divsion_short_nm = df_vehghg_file_nonflexfuel_target_coef.loc[j, 'MFR_DIVISION_SHORT_NM']
                                    df_tstcar_nonflexfuel_target_coef = tstcar_target_coef_cafe_mfr_cd_carline_name(set_roadload_coefficient_table, tstcar_MY_carline_name_mapping_table, _model_year, _cafe_mfr_cd, _label_mfr_cd, \
                                                                                                                _carline_name.upper(), _mfr_divsion_short_nm.upper(), _engine_displacement_j, _etw_k, _num_trans_gears, _engine_displacement_check)
                                except KeyError:
                                    print('Check the _label_mfr_cd, CARLINE_NAME: ', j, _cafe_mfr_cd, _model_type_index, _carline_name)
                            else:
                                df_tstcar_nonflexfuel_target_coef = set_roadload_coefficient_table.loc[tstcar_checks, :]

                            if df_vehghg_file_nonflexfuel_target_coef.shape[0] == 0: continue
                            df_tstcar_nonflexfuel_target_coef.reset_index(drop=True, inplace=True)
                            for k in range (len(df_vehghg_file_nonflexfuel_target_coef)):
                                _index = df_vehghg_file_nonflexfuel_target_coef_index[k]
                                if pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO']): pass
                                else: continue
                                for l in range (len(df_tstcar_nonflexfuel_target_coef)):
                                    if (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] >= 0) and (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] <= 2): continue
                                    if (vehghg_file_nonflexfuel.loc[_index, 'TEST_PROC_CATEGORY'] == df_tstcar_nonflexfuel_target_coef.loc[l, 'Test Category']) or \
                                            (pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'TEST_PROC_CATEGORY'])):
                                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'Target Coef A (lbf)']
                                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'Target Coef B (lbf/mph)']
                                        vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'Target Coef C (lbf/mph**2)']
                                        if pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE']) and (~pd.isnull(df_vehghg_file_nonflexfuel_target_coef['FUEL_NET_HEATING_VALUE']).sum() > 0):
                                            vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE_BEST'] = df_vehghg_file_nonflexfuel_target_coef['FUEL_NET_HEATING_VALUE'].mean()
                                            vehghg_file_nonflexfuel.loc[_index, 'FUEL_GRAVITY_BEST'] = df_vehghg_file_nonflexfuel_target_coef['FUEL_GRAVITY'].mean
                                        if ESTIMATE_NV_RATIO_SET_COEF_ABC_BY_ROAD_LOAD_HP:
                                            vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'SET_COEF_A']
                                            vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'SET_COEF_B']
                                            vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'SET_COEF_C']
                                            vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_SURRO'] = df_tstcar_nonflexfuel_target_coef.loc[l, 'N/V Ratio']

                vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO']) == True) & (pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'])), 'TARGET_COEF_BEST_MTH'] = 3
                vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[:, ~vehghg_file_nonflexfuel.columns.duplicated()]
                # del df_Cafe_MFR_CD_Mode_Type_Index, df_vehghg_file_nonflexfuel_target_coef, df_tstcar_nonflexfuel_target_coef
                print('# of TARGET_COEF_BEST_MTH = 3 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 3]), ')')
                print('# of TARGET_COEF_A_SURRO', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])).sum())
                print('')

            if ESTIMATE_TARGET_COEF_BEST_MTH_3_4:
                _engine_displacement_check = 'relaxed'
                df_target_coef_null = vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO'])), _target_coef_surro_indexing_category]
                df_target_coef_null_index = list(df_target_coef_null.index)
                df_target_coef_null.reset_index(drop=True, inplace=True)
                for i in range(len(df_target_coef_null)):
                    _index = df_target_coef_null_index[i]
                    _model_year = df_target_coef_null.loc[i, 'MODEL_YEAR']
                    _cafe_mfr_cd = df_target_coef_null.loc[i, 'CAFE_MFR_CD']
                    _label_mfr_cd = df_target_coef_null.loc[i, 'LABEL_MFR_CD']
                    _carline_name = df_target_coef_null.loc[i, 'CARLINE_NAME']
                    _mfr_divsion_short_nm = df_target_coef_null.loc[i, 'MFR_DIVISION_SHORT_NM']
                    _etw = df_target_coef_null.loc[i, 'ETW']
                    if pd.isnull(_etw): _etw = df_target_coef_null.loc[i, 'INERTIA_WT_CLASS']
                    _displ = df_target_coef_null.loc[i, 'ENG_DISPL']
                    _num_trans_gears =  df_target_coef_null.loc[i, 'TOTAL_NUM_TRANS_GEARS']
                    _rated_hp = pd.to_numeric(df_target_coef_null.loc[i, 'ENG_RATED_HP'], errors='coerce')
                    df_tstcar_table = tstcar_target_coef_cafe_mfr_cd_carline_name(set_roadload_coefficient_table, tstcar_MY_carline_name_mapping_table, _model_year, _cafe_mfr_cd, \
                                                                                  _label_mfr_cd, _carline_name.upper(), _mfr_divsion_short_nm.upper(), _displ, _etw, _num_trans_gears, _engine_displacement_check)
                    if len(df_tstcar_table) == 0: continue
                    df_sort = df_tstcar_table.iloc[(df_tstcar_table['Equivalent Test Weight (lbs.)'] - _etw).abs().argsort()[:1]]
                    _index_df_sort = df_sort.index.tolist()[0]
                    if pd.isnull(df_tstcar_table.loc[_index_df_sort, 'Target Coef A (lbf)']): continue
                    if (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] >= 0) and (vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_BEST_MTH'] <= 3): continue
                    vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO'] = df_tstcar_table.loc[_index_df_sort, 'Target Coef A (lbf)']
                    vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_SURRO'] = df_tstcar_table.loc[_index_df_sort, 'Target Coef B (lbf/mph)']
                    vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_SURRO'] = df_tstcar_table.loc[_index_df_sort, 'Target Coef C (lbf/mph**2)']
                    if (~pd.isnull(df_target_coef_null.loc[i, 'FUEL_NET_HEATING_VALUE']) == True):
                        vehghg_file_nonflexfuel.loc[_index, 'FUEL_NET_HEATING_VALUE_BEST'] = df_target_coef_null.loc[i, 'FUEL_NET_HEATING_VALUE']
                        vehghg_file_nonflexfuel.loc[_index, 'FUEL_GRAVITY_BEST'] = df_target_coef_null.loc[i, 'FUEL_GRAVITY']
                    if ESTIMATE_NV_RATIO_SET_COEF_ABC_BY_ROAD_LOAD_HP:
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_SURRO'] = df_tstcar_table.loc[_index_df_sort,'SET_COEF_A']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_SURRO'] = df_tstcar_table.loc[_index_df_sort,'SET_COEF_B']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_SURRO'] = df_tstcar_table.loc[_index_df_sort,'SET_COEF_C']
                        vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_SURRO'] = df_tstcar_table.loc[_index_df_sort,'N/V Ratio']

                vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO']) == True) & (pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'])), 'TARGET_COEF_BEST_MTH'] = 4
                vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[:, ~vehghg_file_nonflexfuel.columns.duplicated()]
                del df_target_coef_null, df_target_coef_null_index, df_tstcar_table
                print('# of TARGET_COEF_BEST_MTH = 4 (', len(vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['TARGET_COEF_BEST_MTH'] == 4]), ')')
                print('# of TARGET_COEF_A_BEST (', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'])).sum(), ')')
                print('')

            df_target_coef_corr = vehghg_file_nonflexfuel.loc[(~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_SURRO']) == True) & \
                (~pd.isnull(vehghg_file_nonflexfuel['TOT_ROAD_LOAD_HP_SURRO']) == True), _target_coef_surro_indexing_category]
            df_target_coef_corr_index = list(df_target_coef_corr.index)
            df_target_coef_corr.reset_index(drop=True, inplace=True)
            for i in range(len(df_target_coef_corr)):
                _index = df_target_coef_corr_index[i]
                rlhp_ratio = vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP'] / vehghg_file_nonflexfuel.loc[_index, 'TOT_ROAD_LOAD_HP_SURRO']
                if pd.isnull(vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_BEST']):
                    vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_A_SURRO']
                    vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_B_SURRO']
                    vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'TARGET_COEF_C_SURRO']
                    if ESTIMATE_NV_RATIO_SET_COEF_ABC_BY_ROAD_LOAD_HP:
                        vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'NV_RATIO_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_A_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_B_SURRO']
                        vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_BEST'] = rlhp_ratio * vehghg_file_nonflexfuel.loc[_index, 'SET_COEF_C_SURRO']

            print('# of TARGET_COEF_A_BEST (', (~pd.isnull(vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'])).sum(), ')')

            del set_roadload_coefficient_table, roadload_coefficient_table, df_target_coef_corr, df_target_coef_corr_index
            vehghg_file_nonflexfuel.drop(['Model Year', 'Veh Mfr Code', 'Represented Test Veh Make', 'Represented Test Veh Model', 'Test Number', 'Test Category', 'Equivalent Test Weight (lbs.)', 'Test Veh Displacement (L)', 'N/V Ratio'], axis=1, inplace=True)
            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel_rr', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)

            _num_null_LHVs = len(vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'G'), 'FUEL_NET_HEATING_VALUE_BEST']) + \
                                     len(vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'D'), 'FUEL_NET_HEATING_VALUE_BEST'])
            print('\n# of Null FUEL_NET_HEATING_VALUE_BEST = ', _num_null_LHVs)
            if pd.isnull(vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'G', 'FUEL_NET_HEATING_VALUE_BEST']).sum() > 0:
                vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'G'), 'FUEL_NET_HEATING_VALUE_BEST'] = \
                    vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'G', 'FUEL_NET_HEATING_VALUE'].mean()
                vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_GRAVITY_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'G'), 'FUEL_GRAVITY_BEST'] = \
                    vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'G', 'FUEL_GRAVITY'].mean()
            if pd.isnull(vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'D', 'FUEL_NET_HEATING_VALUE_BEST']).sum() > 0:
                vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'D'), 'FUEL_NET_HEATING_VALUE_BEST'] = \
                    vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'D', 'FUEL_NET_HEATING_VALUE'].mean()
                vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_GRAVITY_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'D'), 'FUEL_GRAVITY_BEST'] = \
                    vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'D', 'FUEL_GRAVITY'].mean()
            vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'E', 'FUEL_NET_HEATING_VALUE_BEST'] = np.nan
            vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['Fuel Type Category'] == 'E', 'FUEL_GRAVITY_BEST'] = np.nan

            _num_null_LHVs = len(vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'G'), 'FUEL_NET_HEATING_VALUE_BEST']) + \
                                     len(vehghg_file_nonflexfuel.loc[(pd.isnull(vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'])) & (vehghg_file_nonflexfuel['Fuel Type Category'] == 'D'), 'FUEL_NET_HEATING_VALUE_BEST'])
            print('# of Null FUEL_NET_HEATING_VALUE_BEST /w Updated = ', _num_null_LHVs)

            vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'] = pd.Series(
                vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_BEST'] * vehghg_file_nonflexfuel['FUEL_GRAVITY_BEST'] * btu2mj * kg2lbm)

            import Calculate_Powertrain_Efficiency
            vehghg_file_nonflexfuel = pd.concat([pd.Series(range(len(vehghg_file_nonflexfuel)), name='TEMP_ID') + 1, vehghg_file_nonflexfuel], axis=1)
            # vehghg_file_nonflexfuel = vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['CARLINE_NAME'] == 'Rio', :]
            output_array = Calculate_Powertrain_Efficiency.Calculate_Powertrain_Efficiency( \
                vehghg_file_nonflexfuel['TEMP_ID'], vehghg_file_nonflexfuel['TEST_PROC_CATEGORY'], \
                vehghg_file_nonflexfuel['TARGET_COEF_A_BEST'], vehghg_file_nonflexfuel['TARGET_COEF_B_BEST'], vehghg_file_nonflexfuel['TARGET_COEF_C_BEST'], vehghg_file_nonflexfuel['VEH_ETW'], \
                vehghg_file_nonflexfuel['TEST_UNROUNDED_UNADJUSTED_FE'], vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_CITY_FE_4'], vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_HWY_FE_4'], \
                vehghg_file_nonflexfuel['EPA_CAFE_MT_CALC_COMB_FE_4'], input_path, drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames, \
                vehghg_file_nonflexfuel['ENG_DISPL'], vehghg_file_nonflexfuel['ENG_RATED_HP'], vehghg_file_nonflexfuel['FUEL_NET_HEATING_VALUE_MJPL'])

            vehghg_file_nonflexfuel = pd.merge(vehghg_file_nonflexfuel, output_array, how='left', \
                                               on=['TEMP_ID', 'TEST_PROC_CATEGORY']).reset_index(drop=True).drop('TEMP_ID', axis=1)

            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file_nonflexfuel_pe', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            # vehghg_file_nonflexfuel = vehghg_file_nonflexfuel[vehghg_file_nonflexfuel['Fuel Type Category'] != 'n'] # delete no fuel vehicles
            # vehghg_file_nonflexfuel.reset_index(drop=True, inplace=True)

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
            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file_output_before', vehghg_file_nonflexfuel, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            # only output non flex fuel
            vehghg_file_output = vehghg_file_nonflexfuel

            vehghg_file_output = vehghg_file_output.loc[:, ~vehghg_file_output.columns.duplicated()]
            vehghg_file_output = vehghg_file_output.loc[:, ~vehghg_file_output.columns.str.contains('^Unnamed')]
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Distributed Footprint Volumes'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Distributed Subconfig Volumes'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Total Subconfig Volume Allocated to Footprint'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'Total Footprint Volume Allocated to Subconfig'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'FOOTPRINT_ALLOCATED_SUBCONFIG_VOLUMES'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'SUBCONFIG_ALLOCATED_FOOTPRINT_VOLUMES'] = 0
            vehghg_file_output.loc[vehghg_file_output['FUEL_USAGE'] == 'E', 'FOOTPRINT_SUBCONFIG_VOLUMES'] = 0

            vehghg_file_output['RLHP_FROM_RLCOEFFS'] = ((vehghg_file_output['TARGET_COEF_A_BEST'] + (50 * vehghg_file_output['TARGET_COEF_B_BEST']) \
                         + ((50 * 50) * vehghg_file_output['TARGET_COEF_C_BEST'])) * 50 * lbfmph2hp).replace(0, np.nan) # dtmp = vehghg_file_nonflexfuel.loc[vehghg_file_nonflexfuel['PTEFF_FROM_RLCOEFFS'] == '', :]
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
            if DEBUGGING_CAFE_MFR_CD_MODE != True: check_final_model_yr_ghg_prod_units('vehghg_file_output', vehghg_file_output, footprint_indexing_categories, subconfig_indexing_categories, grp_volumes_footprint_file_with_lineage)
            vehghg_file_output.rename({'Target Coef A (lbf)': 'Target Coef A (lbf) tstcar', 'Target Coef B (lbf/mph)': 'Target Coef B (lbf/mph) tstcar', 'Target Coef C (lbf/mph**2)': 'Target Coef C (lbf/mph**2) tstcar'}, axis=1)
            vehghg_file_output.drop_duplicates(keep=False, inplace=True)
            vehghg_file_output.reset_index(drop=True, inplace=True)
            vehghg_filename = vehghg_filename.replace('.csv', '')
            if ESTIMATE_TARGET_COEF_BEST_MTH_3_4:
                vehghg_filename = vehghg_filename + '_plus_MTH_34'
            else:
                vehghg_filename = vehghg_filename + '_MTH_012'

            if DEBUGGING_CAFE_MFR_CD_MODE: vehghg_filename = vehghg_filename + '_' + DEBUGGING_CAFE_MFR_CD
            # vehghg_file_output.insert(22, 'DRIVE TYPE', np.nan);
            # vehghg_file_output.loc[vehghg_file_output['DRV_SYS'] == '4', 'DRIVE TYPE'] = '4'
            # vehghg_file_output.loc[vehghg_file_output['DRV_SYS'] == 'P', 'DRIVE TYPE'] = '4'
            # vehghg_file_output.loc[vehghg_file_output['DRV_SYS'] == 'A', 'DRIVE TYPE'] = 'A'
            # vehghg_file_output.loc[vehghg_file_output['DRV_SYS'] == 'F', 'DRIVE TYPE'] = 'F'
            # vehghg_file_output.loc[vehghg_file_output['DRV_SYS'] == 'R', 'DRIVE TYPE'] = 'R'
            # vehghg_file_output.loc[vehghg_file_output['Drive System Code'] == '4'  & (~pd.isnull(vehghg_file_output['Drive System Code'])), 'DRIVE TYPE'] = 'Four wheel drive'

            vehghg_file_output.to_csv(output_path + '\\' + vehghg_filename + '_' + date_and_time + '.csv', index=False)
            print('\nFinish writing the', vehghg_filename, 'in the\n', output_path, 'directory\n')
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
