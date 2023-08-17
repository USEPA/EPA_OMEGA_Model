import pandas as pd
import numpy as np
import datetime
import os

OMEGA_outputs = False
pd.options.mode.chained_assignment = None  # default='warn'
cols_safety = ["DUAL FRONT SIDE-MOUNTED AIRBAGS", "DUAL FRONT WITH HEAD PROTECTION CHAMBERS SIDE-MOUNTED AIRBAGS",
                "DUAL FRONT AND DUAL REAR SIDE-MOUNTED AIRBAGS",
                "DUAL FRONT AND DUAL REAR WITH HEAD PROTECTION CHAMBERS SIDE-MOUNTED AIRBAGS",
                "DRIVER ONLY WITH HEAD PROTECTION CHAMBER SIDE-MOUNTED AIRBAGS",
                "FRONT, REAR AND THIRD ROW HEAD AIRBAGS", "FRONT AND REAR HEAD AIRBAGS", "FRONT HEAD AIRBAGS",
                "STABILITY CONTROL", "TRACTION CONTROL", "TIRE PRESSURE MONITORING"]
cols_OMEGA_inputs = ['CAFE_MFR_CD',	'MODEL_TYPE_INDEX',	'Electrification Category',	'Boost Type Category', 'CARLINE_CLASS_DESC_all', 'CARLINE_MFR_NAME_all', 'CARLINE_NAME_all', 'TARGET_COEF_BEST_MTH_min',
                     'TARGET_COEF_BEST_MTH_max', 'TARGET_COEF_BEST_MTH_all', 'TARGET_COEF_A_BEST', 'TARGET_COEF_B_BEST', 'TARGET_COEF_C_BEST', 'FTP_FE Bag 1', 'FTP_FE Bag 2', 'FTP_FE Bag 3', 'FTP_FE Bag 4', 'US06_FE',
                     'US06_FE Bag 1', 'US06_FE Bag 2', 'CAFE_MODEL_YEAR_all', 'RLHP_FROM_RLCOEFFS',	'ROUNDED_CARGO_CARRYING_VOL', 'BodyID_all',	'Combined Load Factor (%)',	'City Powertrain Efficiency (%)',
                     'City Tractive Road Energy Intensity (Wh/mi)', 'Hwy Powertrain Efficiency (%)', 'Hwy Tractive Road Energy Intensity (Wh/mi)', 'US06 Powertrain Efficiency (%)', 'US06 Tractive Road Energy Intensity (Wh/mi)',
                     'COMPLIANCE_CATEGORY_CD_all', 'COOLED_EGR_YN_all', 'Curb Weight', 'CYL_DEACT_all', 'CYL_DEACT_DESC_all', 'DRV_SYS_all', 'Drive Sys tstcar_all', 'DRV_SYS_DESC_all', 'EGR_YN_all', 'EGR_TYPE_all',
                     'Electric Power Steering_all', 'ENG_BLOCK_ARRANGEMENT_CD_all', 'ENG_BLOCK_ARRANGEMENT_DESC_all', 'ENG_DISPL_all', 'DISPL_UNIT_all', 'Engine Displacement Category_all', 'ENG_TYPE_all', 'ENG_TYPE_DESC_all',
                     'ENGINE_TYPE_DETAIL_DESC_all',	'AXLE_RATIO', 'ETW', 'FINAL_CALC_CITY_FE_4', 'FINAL_CALC_HWY_FE_4', 'FOOTPRINT', 'FOOTPRINT_CARLINE_NM_all', 'FOOTPRINT_DESC_all', 'FOOTPRINT_DIVISION_NM_all', 'FOOTPRINT_MFR_NM_all',
                     'FRONT_TRACK_WIDTH_INCHES', 'FUEL_CELL_YN_all', 'FUEL_METERING_all', 'FUEL_METERING_DESC_all', 'Fuel Recommended_all', 'Fuel Tank Capacity', 'FUEL_USAGE_all', 'FUEL_USAGE_DESC_all', 'Gross Vehicle Weight Rating',
                     'Ground Clearance', 'Height', 'Horsepower at RPM_all', 'HYBRID_YN_all', 'HYBRID_TYPE_all', 'HYBRID_TYPE_DESC_all', 'Interior Volume', 'Length', 'LineageID_all', 'MSRP', 'NUM_CYLINDRS_ROTORS_all', 'TOTAL_NUM_TRANS_GEARS_all',
                     'NV_RATIO_BEST', 'OFF_BOARD_CHARGE_CAPABLE_YN_all', 'Passenger Capacity', 'Payload Capacity', 'PRODUCTION_VOLUME_GHG_50_STATE', 'ENG_RATED_HP', 'REAR_TRACK_WIDTH_INCHES', 'RECHARGE_ENERGY_STORAGE_SYS_YN_all', 'TOT_ROAD_LOAD_HP',
                     'STOP_START_ENG_MGT_all', 'STOP_START_ENG_MGT_DESC_all', 'THREE_ROWS_DES_SEATING_POS_YN_all', 'Torque_all', 'Towing Capacity', 'OEM Towing Capacity', 'Transmission Type Category_all', 'Wheelbase', 'Width', 'TARGET_COEF_BEST_MTH']
cols_id_clean_worksheet = ['lookup01', 'carline_mfr_name', 'carline_name', 'vehicle_name', 'manufacturer_id', 'model_year', 'reg_class_id', 'epa_size_class',
                           'context_size_class', 'electrification_class', 'cost_curve_class', 'in_use_fuel_id', 'cert_fuel_id', 'sales', 'cert_direct_oncycle_co2e_grams_per_mile',
                           'cert_direct_oncycle_kwh_per_mile', 'footprint_ft2', 'eng_rated_hp', 'tot_road_load_hp', 'etw_lbs', 'length_in', 'width_in', 'height_in',
                           'ground_clearance_in', 'wheelbase_in', 'interior_volume_cuft', 'msrp_dollars', 'passenger_capacity', 'payload_capacity_lbs', 'towing_capacity_lbs',
                           'unibody_structure', 'body_style', 'structure_material', 'drive_system', 'gvwr_lbs', 'gcwr_lbs', 'curbweight_lbs', 'eng_cyls_num', 'eng_disp_liters',
                           'high_eff_alternator', 'start_stop', 'hev', 'phev', 'bev', 'deac_pd', 'deac_fc', 'cegr', 'atk2', 'gdi', 'turb12', 'turb11', 'gas_fuel', 'diesel_fuel',
                           'target_coef_a', 'target_coef_b', 'target_coef_c']

def weighted_average(grp):
    if grp[weighting_field]._get_numeric_data().sum() == 0: # if all the weighting factors are zero, take a simple average. Otherwise, it will calculate as 0/0.
        return grp._get_numeric_data().multiply(1, axis=0).sum()/((~pd.isnull(grp)).multiply(1,axis=0).sum())
    else: # take a weighted average
        return grp._get_numeric_data().multiply(grp[weighting_field], axis=0).sum()/((~pd.isnull(grp)).multiply(grp[weighting_field],axis=0).sum())

    # if pd.notnull(grp[information_toget_source_column_name]).multiply(grp[weighting_field], axis=0).sum() == 0:
    #     grp_information_toget_source_column_avg = grp[information_toget_source_column_name]._get_numeric_data().mean()
    # else:
    #     grp_information_toget_source_column_avg = grp[information_toget_source_column_name]._get_numeric_data().multiply(grp[weighting_field], axis=0).mean() \
    #                 / pd.notnull(grp[information_toget_source_column_name]).multiply(grp[weighting_field], axis=0).mean()
    # if len(grp) > 1: grp.drop(grp.index[1:len(grp)], inplace=True)
    # grp.loc[grp.index[0], information_toget_source_column_name] = grp_information_toget_source_column_avg
    #
    # return grp

def scraping_Edmunds_MSRPs (omega_outputs0, df_edms):
    omega_outputs = omega_outputs0.copy()
    # df_edms = pd.read_csv("I:/Project/Midterm Review/Trends/Trends Data/Edmunds/2022 Measurements" + '\\' + 'Edmunds_MY2022_20230721-055344.csv', encoding="ISO-8859-1")
    # omega_outputs = pd.read_csv('I:/Project/Midterm Review/Trends/Original Trends Team Data Gathering and Analysis/Tech Specifications/techspecconsolidator/Query Runs/20230815/outputs' + '\\' + \
    #                        '2022Query_plus_MTH_34_OMEGA_20230815 132716.csv', encoding="ISO-8859-1")

    df_edms['Model'].replace(regex=['F-'],value='F', inplace=True)

    df_ford = df_edms.loc[df_edms['Make'] == 'Ford', :]
    df_edms['Model'].replace('-', ' ', inplace=True, regex=True)
    df_edms['Model'].replace(regex=['MACH E'],value='MACH-E', inplace=True)
    df_edms['Model'].replace(regex=['CX 5'],value='CX-5', inplace=True)
    df_edms['Model'].replace(regex=['CX 30'],value='CX-30', inplace=True)
    df_edms['Model'].replace(regex=['MX 30'],value='MX-30', inplace=True)
    df_edms['Model'].replace(regex=['E TRON'],value='E-TRON', inplace=True)
    df_edms['Model'].replace(regex=[' FACE'],value='-FACE', inplace=True)
    df_edms['Model'].replace(regex=[' PACE'],value='-PACE', inplace=True)
    df_edms['Model'].replace(regex=[' TYPE'],value='-TYPE', inplace=True)
    df_edms['Trims'] = df_edms['Trims'].str.upper()

    omega_outputs['CARLINE_MFR_NAME_all'] = omega_outputs['CARLINE_MFR_NAME_all'].str.upper()
    omega_outputs['CARLINE_NAME_all'] = omega_outputs['CARLINE_NAME_all'].str.upper()
    _idx_msrp = np.nan
    _matching_steps = ['exact', 'model', 'model_trims', 'base']
    for k in range(len(_matching_steps)):
        matching_step = _matching_steps[k]
        _models_MSRP_nulls = omega_outputs.loc[omega_outputs['MSRP'].astype(str) == 'nan', 'CARLINE_NAME_all'].unique()

        for i in range(len(_models_MSRP_nulls)):
            _modelname=_models_MSRP_nulls[i]
            _idx = omega_outputs.loc[omega_outputs['CARLINE_NAME_all'] == _modelname, :].index[0]
            _maker = omega_outputs.loc[_idx, 'CARLINE_MFR_NAME_all']
            _model = omega_outputs.loc[_idx, 'CARLINE_NAME_all']
            if 'NX 250' in _model: _model = 'NX 250'
            if 'NX 350' in _model: _model = 'NX 350'
            if 'NX 450h+ AWD' in _model: _model = 'NX-450HPLUS'
            if ('i4eDrive40GranCoupe'.upper() in _model):_model = 'I4'
            _modelsplitted = _model.split(' ')
            if (matching_step == 'model_trims') and (len(_modelsplitted) > 1):
                _model = _modelsplitted[0]
                _trim = _modelsplitted[1]
                if _modelsplitted[0] =='SILVERADO':
                    _model ='SILVERADO 1500'
                    _trim = _modelsplitted[1]
                if _modelsplitted[0] == 'TRANSIT':
                    _model = 'TRANSIT CONNECT'
                    _trim = _modelsplitted[2]
            if (matching_step == 'model_trims') and (len(_modelsplitted) == 1): _model = _modelsplitted[0]
            if (matching_step == 'base'): _model = _model.split(' ')[0]
            if _model == 'SILVERADO':
                _model = 'SILVERADO 1500'
            try:
                _idx_most_popular = df_edms.loc[(df_edms['Make'] == _maker) & (df_edms['Model'] ==_model), :].index
                if _idx_most_popular.size == 0:
                    _idx_most_popular = df_edms.loc[(df_edms['Model'] == _model), :].index
                if (_idx_most_popular.size == 0) and (' ' in _model):
                    _model = _model.split(' ')[0]
                    _idx_most_popular = df_edms.loc[(df_edms['Model'] == _model), :].index
                if (_idx_most_popular.size == 0) and (' ' in _model):
                    _model = _model.split(' ')[0]
                    _idx_most_popular = df_edms.loc[(df_edms['Trims'].str.contains(_model)), :].index
                if (_idx_most_popular.size == 0) and (matching_step == 'model_trims') and (len(_modelsplitted) > 1):
                    _idx_most_popular = df_edms.loc[((df_edms['Model'].str.contains(_model)) & (df_edms['Trims'].str.contains(_trim))) | \
                                                    (df_edms['Model'].str.contains(_model)), :].index
                if _idx_most_popular.size == 0:
                    try:
                        _idx_most_popular = df_edms.loc[(df_edms['Trims'].str.contains(_model)) | (df_edms['Model'] == _model), :].index
                    except KeyError:
                        continue

                    if _idx_most_popular.size == 0: continue
                try:
                    for j in range(len(_idx_most_popular)):
                        if '(Most Popular)' in df_edms.loc[_idx_most_popular, 'MSRP'][_idx_most_popular[j]]:
                            _idx_msrp = _idx_most_popular[j]
                            break

                    omega_outputs.loc[(omega_outputs['CARLINE_NAME_all'] == _modelname) & (omega_outputs['MSRP'].astype(str) == 'nan'), 'MSRP'] = df_edms.loc[_idx_msrp, 'MSRP'].replace(',', '').split(' ')[0]
                    print(_maker, _modelname, omega_outputs.loc[(omega_outputs['CARLINE_NAME_all'] == _modelname), 'MSRP'][0], ' (Most Popular)')
                except KeyError:
                    continue
            except KeyError:
                continue

    return omega_outputs

def GCWRs_from_towing_guide(df_twgd, df_query):
    df_query['CARLINE_MFR_NAME_all'] = df_query['CARLINE_MFR_NAME_all'].str.upper()
    df_query['CARLINE_NAME_all'] = df_query['CARLINE_NAME_all'].str.upper()
    df_query.insert(len(df_query.columns), 'GCWR', pd.DataFrame(np.zeros(len(df_query))))
    df_query['GCWR'] = np.nan

    _mfrs = df_twgd['Maker'].unique()
    for k in range(len(_mfrs)):
        _mfr = _mfrs[k]
        _modelnames = df_query.loc[df_query['CARLINE_MFR_NAME_all'] == _mfr, 'CARLINE_NAME_all'].unique()
        for i in range(len(_modelnames)):
            _modelname = _modelnames[i]
            _idx = df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, :].index[0]
            _maker = df_query.loc[_idx, 'CARLINE_MFR_NAME_all']
            _model = df_query.loc[_idx, 'CARLINE_NAME_all']
            if (_maker not in df_twgd['Maker'].unique()): continue

            _wheelbase = df_query.loc[_idx, 'Wheelbase']
            _num_cyl = df_query.loc[_idx, 'NUM_CYLINDRS_ROTORS_all']
            _displ = df_query.loc[_idx, 'ENG_DISPL_all']
            _drivetrain = df_query.loc[_idx, 'DRV_SYS_all']
            _fuel_type = df_query.loc[_idx, 'FUEL_USAGE_all'][0]
            _axle_ratio = df_query.loc[_idx, 'AXLE_RATIO']
            _curv_weight = df_query.loc[_idx, 'Curb Weight']
            _payload = df_query.loc[_idx, 'Payload Capacity']
            _cargo_weight = 1250
            if (_drivetrain == '4') or (_drivetrain == 'A') or (_drivetrain == 'All'):
                _drivetrain = '4WD'
            else:
                _drivetrain = '2WD'

            _base_model = _model.split(' ')[0]
            _chk_maker_model_drivetrain_fuel_type_ncyl_displ_axle_ratio = ((df_twgd['Maker'] == _maker) & (df_twgd['Model'].str.contains(_base_model)) & (df_twgd['Drivetrain Layout Category'] == _drivetrain) &
                                                                           (df_twgd['Fuel Type Category'] == _fuel_type) & (df_twgd['Number of Cylinders Category'] == _num_cyl) &
                                                                           (df_twgd['Engine Displacement Category'] == _displ) & (abs(df_twgd['AXLE_RATIO'] - _axle_ratio) <= 0.2))
            _chk_maker_model_drivetrain_fuel_type_ncyl_displ = ((df_twgd['Maker'] == _maker) & (df_twgd['Model'].str.contains(_base_model)) & (df_twgd['Drivetrain Layout Category'] == _drivetrain) &
                                                                           (df_twgd['Fuel Type Category'] == _fuel_type) & (df_twgd['Number of Cylinders Category'] == _num_cyl) &
                                                                           (df_twgd['Engine Displacement Category'] == _displ))
            _chk_maker_model_drivetrain_fuel_type = ((df_twgd['Maker'] == _maker) & (df_twgd['Model'].str.contains(_base_model)) & (df_twgd['Drivetrain Layout Category'] == _drivetrain) &
                                                                           (df_twgd['Fuel Type Category'] == _fuel_type))
            _chk_maker_model_drivetrain = ((df_twgd['Maker'] == _maker) & (df_twgd['Model'].str.contains(_base_model)) & (df_twgd['Drivetrain Layout Category'] == _drivetrain))

            if len(df_twgd.loc[_chk_maker_model_drivetrain_fuel_type_ncyl_displ_axle_ratio, :]) > 0:
                df_tmp = df_twgd.loc[_chk_maker_model_drivetrain_fuel_type_ncyl_displ_axle_ratio, :]
            elif len(df_twgd.loc[_chk_maker_model_drivetrain_fuel_type_ncyl_displ, :]) > 0:
                df_tmp = df_twgd.loc[_chk_maker_model_drivetrain_fuel_type_ncyl_displ, :]
            elif len(df_twgd.loc[_chk_maker_model_drivetrain, :]) > 0:
                df_tmp = df_twgd.loc[_chk_maker_model_drivetrain, :]
            elif (_base_model == 'SIERRA') or (_base_model == 'SILVERADO'):
                _max_trailer_weight = df_twgd.loc[
                    (df_twgd['Maker'] == _maker) & (df_twgd['Model'].str.contains(_base_model)) & (
                                df_twgd['Drivetrain Layout Category'] == _drivetrain), 'Max Loaded Trailer Weight']
            else:
                continue

            df_closest_wheelbase = df_tmp.iloc[(df_tmp['WHEELBASE'] - _wheelbase).abs().argsort()[:1]]
            if len(df_closest_wheelbase) == 0:
                df_closest_axle_ratio = df_tmp.iloc[(df_tmp['AXLE_RATIO'] - _axle_ratio).abs().argsort()[:]]
                if len(df_closest_axle_ratio) == 0: continue
                if (df_tmp.loc[df_closest_wheelbase.index[0], 'GCWR'].astype(str) == 'nan'):
                    if _payload.astype(str) == 'nan': _payload = 1250
                    if _curv_weight.astype(str) == 'nan': _curv_weight = df_query.loc[
                        df_query['CARLINE_NAME_all'] == _modelname, 'Curb Weight'].mean()
                    _max_trailer_weight = df_tmp.loc[df_closest_axle_ratio.index[0], 'Max Loaded Trailer Weight']
                    df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, 'GCWR'] = _curv_weight + _payload + _max_trailer_weight + 3 * 150
                else:
                    df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, 'GCWR'] = df_tmp.loc[df_closest_axle_ratio.index[0], 'GCWR']
            else:
                if (df_tmp.loc[df_closest_wheelbase.index[0], 'GCWR'].astype(str) == 'nan'):
                    # https: // www.readingtruck.com / calculating - your - trucks - maximum - payload - and -towing - capacity /
                    _max_trailer_weight = df_tmp.loc[df_closest_wheelbase.index[0], 'Max Loaded Trailer Weight']
                    if _payload.astype(str) == 'nan': _payload = 1250
                    if _curv_weight.astype(str) == 'nan': _curv_weight = df_query.loc[
                        df_query['CARLINE_NAME_all'] == _modelname, 'Curb Weight'].mean()
                    df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, 'GCWR'] = _curv_weight + _payload + _max_trailer_weight + 3 * 150
                else:
                    df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, 'GCWR'] = df_tmp.loc[df_closest_wheelbase.index[0], 'GCWR']

            print(_modelname, df_closest_wheelbase.index[0], df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, 'GCWR'])
            # df_query.loc[df_query['CARLINE_NAME_all'] == _modelname, 'GCWR'] = df_tmp.loc[df_closest_wheelbase.index[0], 'GCWR']
    return df_query

def mode(df, key_cols, value_col, count_col):
    return df.groupby(key_cols + [value_col]).size() \
        .to_frame(count_col).reset_index() \
        .sort_values(count_col, ascending=False) \
        .drop_duplicates(subset=key_cols)

print(os.getcwd())
main_path = 'I:/Project/Midterm Review/Trends/Original Trends Team Data Gathering and Analysis/Tech Specifications/techspecconsolidator/Query Runs'
run_folder = str(input('Enter Run Folder Name: '))
run_folder_path = os.path.join(main_path, run_folder)
run_controller_file = os.path.join(run_folder_path, 'Run Query Controller.csv')

run_controller = pd.read_csv(run_controller_file, encoding="ISO-8859-1")
run_controller = run_controller.replace(np.nan, '', regex=True)
_rows, _cols = run_controller.shape
SetBodyIDtoLineageID = int(run_controller.SetBodyIDtoLineageID[0])
model_year = []
# master_index_source = []
aggregating_fields_input = []
for _row in range(_rows):
    MY = run_controller['model_year'][_row]
    if MY != '' and str(MY).replace('.', '').isnumeric():
        model_year.append(int(MY))
    elif MY == '' or MY == 'Done':
        break

for _row in range(_rows):
    _master_index_source = run_controller['master_index_source'][_row]
    if _master_index_source != '' and len(_master_index_source) > 0:
        master_index_source = _master_index_source
    elif _master_index_source == '' or _master_index_source == 'Done':
        break

for _row in range(_rows):
    query_field_input = run_controller['aggregating_fields_input'][_row]
    if query_field_input != '' and len(query_field_input) > 0:
        aggregating_fields_input.append(query_field_input)
    elif query_field_input == '' or query_field_input == 'Done':
        break

field_mapping_filename = run_controller['database_definition_files'][0]
data_sources_filename = run_controller['database_definition_files'][1]
main_mapping_category_key_filename = run_controller['database_definition_files'][2]

if ',' in aggregating_fields_input:
    aggregating_fields = pd.Series(aggregating_fields_input.split(','), name='Category').str.strip()
    # aggregating_fields = pd.Series(list(aggregating_fields_input.split(',')), name='Category').str.strip()
else:
    aggregating_fields = pd.Series(aggregating_fields_input, name='Category').str.strip()
if ',' in str(model_year):
    model_years = pd.Series(list(model_year.split(',')), name='Category').str.strip()
else:
    model_years = pd.Series(model_year)
model_years = model_years
# model_years = model_years.astype(int)

for model_year in model_years:
    run_controller = pd.read_csv(main_path + '\\' + run_folder + '\Run Query Controller.csv')
    run_controller = run_controller[run_controller['USE_YN']=='y'].reset_index(drop=True)

    input_path = main_path+'\\'+run_folder+'\\'+'inputs'
    output_path = main_path+'\\'+run_folder+'\\'+'outputs'
    field_mapping_df = pd.read_csv(input_path + '\\' + field_mapping_filename)
    data_sources_df = pd.read_csv(input_path + '\\' + data_sources_filename)
    master_category_check_file = pd.read_csv(input_path + '\\' + main_mapping_category_key_filename)

    master_category_check_df = master_category_check_file.set_index(master_category_check_file['Readin Sources'].values)

    field_mapping_df['UserFriendlyName'].fillna('', inplace=True)
    aggregating_columns = pd.Series(np.zeros(len(aggregating_fields))).replace(0, '')
    master_schema = data_sources_df['SourceSchema'][data_sources_df['SourceSchema'][(data_sources_df['SourceName']==master_index_source) & \
        (data_sources_df['MY']==model_year)].index[0]]
    for i in range(0, len(aggregating_fields)):
        aggregating_columns[i] = field_mapping_df[master_schema+'Field'][field_mapping_df[master_schema+'Field'][ \
            field_mapping_df['UserFriendlyName'] == aggregating_fields[i]].index[0]]

    #Determine Total Number of Schemas
    total_schema_count = 0
    for run_count in range(0, len(run_controller)):
        information_toget = str(run_controller['Desired Field'][run_count])
        information_priority = field_mapping_df[
            list(pd.Series(field_mapping_df.columns)[pd.Series(field_mapping_df.columns).str.contains('Priority')])] \
            [field_mapping_df['UserFriendlyName'] == information_toget].reset_index(drop=True)
        # if information_toget == 'EPA Time To Charge Battery (At 240V)': print(information_toget)
        total_schema_count += len(information_priority.columns[~pd.isnull(information_priority).iloc[0]])
    #From list of desired quantities, get all sources, filenames and fieldnames in order
    all_schemas = pd.Series(np.zeros(total_schema_count), name = 'SourceSchema')
    all_column_names = pd.Series(np.zeros(total_schema_count), name = 'Column Name')
    all_query_types = pd.Series(np.zeros(total_schema_count), name = 'QueryType')
    all_weighting_fields = pd.Series(np.zeros(total_schema_count), name = 'AvgWtField')
    all_bounding_fields = pd.Series(np.zeros(total_schema_count), name = 'BoundingField')
    all_aggregating_fields = pd.Series(np.zeros(total_schema_count), name = 'AggregatingFields')
    all_desired_fields = pd.Series(np.zeros(total_schema_count), name = 'Desired Field')
    all_priority_values = pd.Series(np.zeros(total_schema_count), name = 'Priority')
    schema_track = 0
    for run_count in range(0, len(run_controller)):
        information_toget = str(run_controller['Desired Field'][run_count])
        query_type_input = str(run_controller['QueryType'][run_count])
        weighting_field = str(run_controller['AvgWtField'][run_count])
        bounding_field = str(run_controller['BoundingField'][run_count])
        information_priority = field_mapping_df[list(pd.Series(field_mapping_df.columns)[pd.Series(field_mapping_df.columns).str.contains('Priority')])][field_mapping_df['UserFriendlyName'] == information_toget].reset_index(drop=True)
        source_schemas = pd.Series(\
            information_priority.columns[~pd.isnull(information_priority.iloc[0].reset_index(drop=True))], \
            name = 'SourceSchema').str[0:5].reset_index(drop=True)
        column_names = field_mapping_df[
            list(pd.Series(field_mapping_df.columns)[pd.Series(field_mapping_df.columns).str.contains('Field')])] \
            [field_mapping_df['UserFriendlyName'] == information_toget].drop('FieldName',axis=1).reset_index(drop=True)
        source_column_names = column_names.iloc[0][~pd.isnull(column_names.iloc[0])].reset_index(drop=True)
        priority_values = information_priority.iloc[0][~pd.isnull(information_priority.iloc[0])].reset_index(drop=True)
        all_schemas[schema_track:schema_track+len(source_schemas)] = source_schemas
        all_column_names[schema_track:schema_track+len(source_column_names)] = source_column_names
        all_query_types[schema_track:schema_track+len(source_schemas)] = query_type_input
        all_weighting_fields[schema_track:schema_track + len(source_schemas)] = weighting_field
        all_bounding_fields[schema_track:schema_track + len(source_schemas)] = bounding_field
        all_desired_fields[schema_track:schema_track + len(source_schemas)] = information_toget
        all_priority_values[schema_track:schema_track + len(source_schemas)] = priority_values
        schema_track += len(source_schemas)
    model_year_column = pd.Series(np.zeros(total_schema_count), name = 'MY').replace(0,model_year)
    controller_index = pd.Series(all_schemas.index.values, name = 'Controller Index')
    all_array = pd.merge_ordered(pd.concat([controller_index, all_schemas, all_column_names, all_query_types, all_weighting_fields, all_bounding_fields,\
        all_priority_values, all_desired_fields, model_year_column], axis=1), data_sources_df, how='left', on=['SourceSchema', 'MY']).replace(str(np.nan), np.nan)
    all_array = pd.merge_ordered(all_array, field_mapping_df[['UserFriendlyName', 'FieldName']], how='left', \
        left_on = 'Desired Field', right_on = 'UserFriendlyName').drop(['UserFriendlyName'],axis=1)\
        .sort_values('Controller Index').drop('Controller Index',axis=1)
    del (all_schemas, all_column_names, all_query_types, all_weighting_fields, all_bounding_fields, all_desired_fields)
    all_array['Output Column'] = pd.Series(all_array['FieldName']+'_'+all_array['QueryType'])\
        .replace(['_top1', '_avg', '_sum'],'', regex=True)
    all_array['Output Column'][~pd.isnull(all_array['BoundingField'])] = \
        all_array['FieldName'][~pd.isnull(all_array['BoundingField'])]+'_at'+all_array['QueryType'][~pd.isnull(\
        all_array['BoundingField'])] + all_array['BoundingField'][~pd.isnull(all_array['BoundingField'])]
    all_array['Output Column Name'] = all_array['Output Column'] + '_' + all_array['SourceName']
    #all_array is in the correct order up until this point
    all_array = all_array[~pd.isnull(all_array['SourceFile'])].reset_index(drop=True)
    for aggregating_field in aggregating_fields:
        all_array = all_array[all_array['Desired Field'] != aggregating_field].reset_index(drop=True)
    #Get Master Index File
    master_index_filepath = data_sources_df['SourceDirectory'][data_sources_df['SourceDirectory'][ \
        (data_sources_df['SourceName'] == master_index_source) & \
        (data_sources_df['MY'] == model_year)].index[0]]
    master_index_filename = data_sources_df['SourceFile'][data_sources_df['SourceFile'][ \
        (data_sources_df['SourceName'] == master_index_source) & \
        (data_sources_df['MY'] == model_year)].index[0]]
    master_index_file = pd.read_csv(master_index_filepath + '\\' + master_index_filename, encoding="ISO-8859-1", \
                                    converters={'LineageID': int, 'BodyID': int, 'MODEL_YEAR': int,'Vehghg_ID': int, 'CabinID': float}).astype(str)
    try:
        master_index_file['CabinID'] = master_index_file['CabinID'].astype(float).astype(int).astype(str)
    except KeyError:
        pass
    try:
        master_index_file['Number of Transmission Gears Category'] = master_index_file['Number of Transmission Gears Category'] \
            .replace([np.nan, str(np.nan), ''], float(0)).astype(float).astype(int).astype(str)
    except (KeyError, ValueError):
        pass
    try:
        master_index_file['Number of Cylinders Category'][(master_index_file['Number of Cylinders Category'].astype(str) != 'ELE') & (master_index_file['Number of Cylinders Category'] != str(np.nan))] = \
            master_index_file['Number of Cylinders Category'][(master_index_file['Number of Cylinders Category'].astype(str) != 'ELE') & (master_index_file['Number of Cylinders Category'] != str(np.nan))].astype(float).astype(int).astype(str)
    except KeyError:
        pass
    try:
        master_index_file['TOTAL_NUM_TRANS_GEARS'] = master_index_file['TOTAL_NUM_TRANS_GEARS'] \
            .replace([np.nan, str(np.nan), ''], float(0)).astype(float).astype(int).astype(str)
        master_index_file['LDFE_CAFE_SUBCONFIG_INFO_ID'] = master_index_file[
            'LDFE_CAFE_SUBCONFIG_INFO_ID'].astype(float).astype(int).astype(str)
        master_index_file['FOOTPRINT_SUBCONFIG_VOLUMES'] = master_index_file['FOOTPRINT_SUBCONFIG_VOLUMES'].astype(float) \
            .replace([np.nan, str(np.nan), ''], float(0))
    except KeyError:
        pass
    try:
        master_index_file['CALC_ID'][~pd.isnull(master_index_file['CALC_ID'])] = \
            master_index_file['CALC_ID'][~pd.isnull(master_index_file['CALC_ID'])].astype(float).astype(str)
            # master_index_file['CALC_ID'][~pd.isnull(master_index_file['CALC_ID'])].astype(float).astype(int).astype(str)
    except KeyError:
        pass

    unique_source_info = all_array[['SourceName', 'SourceFile', 'SourceDirectory']].drop_duplicates()
    unique_source_info = unique_source_info[~pd.isnull(unique_source_info['SourceName'])]
    source_matching_categories_source = master_category_check_df.loc[master_index_source]
    source_matching_categories = pd.Series(source_matching_categories_source[source_matching_categories_source != 0].index.values)[1:].reset_index(drop=True)
    for unique_sourcename, unique_filename, unique_filepath in unique_source_info.itertuples(index=False):
        all_subarray = all_array[all_array['SourceFile'] == unique_filename].reset_index(drop=True)
        matching_categories_source = master_category_check_df.loc[unique_sourcename]
        matching_categories = pd.Series(matching_categories_source[matching_categories_source != 0].index.values)[1:].reset_index(drop=True)

        if unique_sourcename == 'Edmunds':
            if 'WHEELBASE' in master_index_file.columns and 'WHEELBASE' not in list(matching_categories):
                if 'WHEEL_BASE_INCHES' not in master_index_file.columns:
                    master_index_file.rename(columns={'WHEELBASE': 'WHEEL_BASE_INCHES'}, inplace=True)
                else:
                    master_index_file.rename(columns={'WHEELBASE': 'WHEEL_BASE_INCHES_bkp'}, inplace=True)
            if 'WHEELBASE' not in master_index_file.columns and 'WHEELBASE' in list(matching_categories):
                master_index_file.rename(columns={'WHEEL_BASE_INCHES': 'WHEELBASE'}, inplace=True)
                master_index_file['WHEELBASE'] = master_index_file['WHEELBASE'].astype(float).round(decimals=0).astype(str)
        elif unique_sourcename == 'OEM Towing Guide' and 'WHEELBASE' not in master_index_file.columns and 'WHEELBASE' in list(matching_categories):
            master_index_file.rename(columns={'WHEEL_BASE_INCHES': 'WHEELBASE'}, inplace=True)
            master_index_file['WHEELBASE'] = master_index_file['WHEELBASE'].astype(float).round(decimals=0).astype(str)

        if master_index_source != 'Master Index' and unique_sourcename == 'Master Index':
            vehghg_filepath = unique_filepath
            vehghg_filename = unique_filename
            vehghg_matching_categories = matching_categories
        if unique_sourcename != master_index_source: #If the current source is not the master index, readin the source file
            try:
                source_file = pd.read_csv(unique_filepath+ '\\' + unique_filename, converters={'LineageID': int, 'BodyID': int}).astype(str)

            except ValueError:
                try:
                    source_file = pd.read_csv(unique_filepath + '\\' + unique_filename).astype(str)
                except UnicodeDecodeError:
                    source_file = pd.read_csv(unique_filepath + '\\' + unique_filename, encoding = "ISO-8859-1").astype(str)
            except UnicodeDecodeError:
                source_file = pd.read_csv(unique_filepath + '\\' + unique_filename, encoding = "ISO-8859-1", \
                    converters={'LineageID': int, 'BodyID': int}).astype(str)
            except FileNotFoundError:
                print(unique_filename, 'not found!!!')
                continue
            try:
                if SetBodyIDtoLineageID == 1:
                    source_file['BodyID'] = source_file['LineageID']
            except KeyError:
                pass

            if unique_sourcename == 'Edmunds':
                try:
                    source_file['WHEELS-raw'] = pd.Series(np.zeros(len(source_file['WHEELS'])), name='WHEELS-raw')
                    source_file['WHEELS-raw'] = source_file['WHEELS']
                    for i in range(len(source_file['WHEELS-raw'])):
                        source_file['WHEELS'][i] = float(source_file['WHEELS-raw'][i].split(' ')[0])
                    source_file['WHEELS'] = source_file['WHEELS'].astype(float).round(1)
                except KeyError:
                    pass
            try:
                source_file['CALC_ID'] = source_file['CALC_ID'].astype(float).astype(int).astype(str)
                if 'WHEELBASE' in list(matching_categories):
                    source_file['WHEELBASE'] = source_file['WHEELBASE'].astype(float).round(decimals=0).astype(str)
            except KeyError:
                pass
            try:
                source_file['Number of Cylinders Category'][
                    (source_file['Number of Cylinders Category'].astype(str) != 'ELE') & (
                    source_file['Number of Cylinders Category'] != str(np.nan))] = \
                    source_file['Number of Cylinders Category'][
                        (source_file['Number of Cylinders Category'].astype(str) != 'ELE') & (
                        source_file['Number of Cylinders Category'] != str(np.nan))].astype(float).astype(
                        int).astype(str)
            except KeyError:
                pass

            try:
                if 'WHEELS' in list(matching_categories): print(matching_categories)
                master_index_file[list(matching_categories)]
                # print(master_index_file.WHEEL_BASE_INCHES)
            except KeyError: #Matching Column not in master index file
                missing_matching_categories = list(set(matching_categories)-set(master_index_file.columns))
                present_matching_categories = list(set(matching_categories)-set(missing_matching_categories))
                try:
                    vehghg_file = pd.read_csv(vehghg_filepath+'\\'+vehghg_filename,\
                    converters={'LineageID': int, 'BodyID': int}).astype(str)
                except UnicodeDecodeError:
                    vehghg_file = pd.read_csv(vehghg_filepath+'\\'+vehghg_filename,\
                    converters={'LineageID':int,'BodyID':int}, encoding = "ISO-8859-1").astype(str)
                try:
                    vehghg_file['Number of Cylinders Category'][
                        (vehghg_file['Number of Cylinders Category'].astype(str) != 'ELE') & (
                            vehghg_file['Number of Cylinders Category'] != str(np.nan))] = \
                        vehghg_file['Number of Cylinders Category'][
                            (vehghg_file['Number of Cylinders Category'].astype(str) != 'ELE') & (
                                vehghg_file['Number of Cylinders Category'] != str(np.nan))].astype(float).astype(
                            int).astype(str)
                except KeyError:
                    pass
                if len(present_matching_categories) > 0:
                    master_index_file = pd.merge_ordered(\
                        master_index_file, vehghg_file[list(present_matching_categories) + list(missing_matching_categories)], how='left', \
                        on=list(present_matching_categories))
                else:
                    master_index_file = pd.merge_ordered(\
                        master_index_file, vehghg_file[list(vehghg_matching_categories) + list(missing_matching_categories)], how='left', \
                        on=list(vehghg_matching_categories))
                try:
                    master_index_file['CALC_ID'][~pd.isnull(master_index_file['CALC_ID'])] = \
                        master_index_file['CALC_ID'][~pd.isnull(master_index_file['CALC_ID'])].astype(float).astype(int).astype(str)
                except KeyError:
                    pass
                del vehghg_file
            try:
                master_index_file[list(pd.Series(pd.Series(all_array['AvgWtField']).unique()).dropna().reset_index(drop=True))]
            except KeyError: #Master Index File is missing avgerage weighting fields
                try:
                    master_index_file[list(matching_categories)]
                except KeyError:  # Matching Column not in master index file
                    missing_matching_categories = list(set(matching_categories) - set(master_index_file.columns))
                    present_matching_categories = list(set(matching_categories) - set(missing_matching_categories))
                else:
                    present_matching_categories = matching_categories
                missing_weighitng_fields = list(set(list(pd.Series(pd.Series(all_array['AvgWtField']).unique()).dropna().reset_index(drop=True)))\
                    -set(master_index_file.columns))
                try:
                    vehghg_file = pd.read_csv(vehghg_filepath+'\\'+vehghg_filename,\
                    converters={'LineageID': int, 'BodyID': int}).astype(str)
                except UnicodeDecodeError:
                    vehghg_file = pd.read_csv(vehghg_filepath+'\\'+vehghg_filename,\
                    converters={'LineageID':int,'BodyID':int}, encoding = "ISO-8859-1").astype(str)
                try:
                    source_file['Number of Cylinders Category'][
                        (source_file['Number of Cylinders Category'].astype(str) != 'ELE') & (
                            source_file['Number of Cylinders Category'] != str(np.nan))] = \
                        source_file['Number of Cylinders Category'][
                            (source_file['Number of Cylinders Category'].astype(str) != 'ELE') & (
                                source_file['Number of Cylinders Category'] != str(np.nan))].astype(float).astype(
                            int).astype(str)
                except KeyError:
                    pass
                vehghg_file[missing_weighitng_fields] = vehghg_file[missing_weighitng_fields].astype(float)
                missing_weighting_fields_groups = vehghg_file[list(present_matching_categories)+list(missing_weighitng_fields)]\
                    .groupby(list(present_matching_categories)).sum().reset_index()
                missing_weighting_fields_groups[list(present_matching_categories)] = missing_weighting_fields_groups[\
                    list(present_matching_categories)].astype(str)
                master_index_file = pd.merge_ordered(master_index_file, missing_weighting_fields_groups, \
                    how='left', on=list(present_matching_categories))
                del vehghg_file
            try: #Add in the columns to the master file from the source file
                # master_index_file_with_desired_fields_all_merges = master_index_file.merge( \
                #     source_file[list(pd.Series(list(matching_categories) + list(all_subarray['Column Name'].unique())).unique())], \
                #     how='left', on=list(matching_categories)).loc[(master_index_file['WHEEL_BASE_INCHES'].astype(float) - source_file['WHEEL_BASE_INCHES'].astype(float)).abs() <= 0.9].replace([str(np.nan), ''], np.nan)
                # if unique_sourcename in 'OEM Towing Guide' and 'Max Loaded Trailer Weight' in source_file.columns:
                #     source_file['Max Loaded Trailer Weight'] = source_file['Max Loaded Trailer Weight'].astype(str)
                if 'WHEELBASE' in list(matching_categories):
                    source_file['WHEELBASE'] = source_file['WHEELBASE'].astype(float).round(decimals=0).astype(str)
                    if unique_sourcename in 'OEM Towing Guide':
                        OEM_towing_quide_unique_LineageID_list = source_file['LineageID'].unique().tolist()
                master_index_file_with_desired_fields_all_merges = master_index_file.merge( \
                # master_index_file_with_desired_fields_all_merges=pd.merge_ordered(master_index_file, \
                    source_file[list(pd.Series(list(matching_categories) + list(all_subarray['Column Name'].unique())).unique())], \
                    # how='left', on=list(matching_categories), left_by='WHEELBASE').replace([str(np.nan), ''], np.nan)
                    how='left', on=list(matching_categories)).replace([str(np.nan), ''], np.nan)
            except KeyError: #Master file is missing at least one of the data columns from the source file
                original_source_columns = list(pd.Series(list(matching_categories)+list(all_subarray['Column Name'].unique())).unique())
                new_source_columns = list(set(original_source_columns)-(set(original_source_columns)-set(list(source_file.columns))))
                master_index_file_with_desired_fields_all_merges = master_index_file.merge( \
                    source_file[list(new_source_columns)],how='left',on=list(matching_categories)).replace([str(np.nan),''], np.nan)
            del source_file
        else:
            master_index_file_with_desired_fields_all_merges = master_index_file.replace([str(np.nan), ''], np.nan)

        # 'City PTEFF_FROM_RLCOEFFS'
        for all_subarray_count in range(0, len(all_subarray)):
            query_type = all_subarray['QueryType'][all_subarray_count]
            weighting_field = all_subarray['AvgWtField'][all_subarray_count]
            bounding_field = all_subarray['BoundingField'][all_subarray_count]
            information_toget_source_column_name = all_subarray['Column Name'][all_subarray_count]
            information_toget = all_subarray['Desired Field'][all_subarray_count]
            if information_toget_source_column_name ==  'City PTEFF_FROM_RLCOEFFS': #'STABILITY CONTROL':
                print(information_toget_source_column_name)
            if information_toget_source_column_name not in master_index_file_with_desired_fields_all_merges.columns:
                print('*** ', information_toget_source_column_name, ' Not found ***')
                continue

            if (aggregating_fields==information_toget).sum() == 0 and len(master_index_file_with_desired_fields_all_merges[\
                    ~pd.isnull(master_index_file_with_desired_fields_all_merges[information_toget_source_column_name])]) > 0:
                print(str(1 + all_subarray_count) + ': ' + information_toget_source_column_name + ' ' + unique_sourcename + ' ' + query_type)
                try:
                    master_index_file_with_desired_field_all_merges = master_index_file_with_desired_fields_all_merges[\
                        (~pd.isnull(master_index_file_with_desired_fields_all_merges[information_toget_source_column_name]))].reset_index(drop=True)
                except KeyError:
                    continue
                if query_type == 'max' or query_type == 'min' or query_type == 'avg' \
                        or query_type == 'std' or query_type == 'sum':
                    try:
                        # master_index_file_with_desired_field_all_merges[information_toget_source_column_name] = \
                        #     master_index_file_with_desired_field_all_merges[information_toget_source_column_name].astype(float)
                        master_index_file_with_desired_field_all_merges[information_toget_source_column_name] = \
                            pd.to_numeric(master_index_file_with_desired_field_all_merges[information_toget_source_column_name], errors='coerce')
                        # if (unique_sourcename == 'Edmunds') and ('CURB WEIGHT' in master_index_file_with_desired_field_all_merges.columns):
                        #     print(master_index_file_with_desired_field_all_merges['CURB WEIGHT'])  # = pd.Series(source_file['CURB WEIGHT']).str.extract("(\d*\.?\d+)", expand=True).astype(float)
                    except ValueError:
                        testing_column = master_index_file_with_desired_field_all_merges[ \
                            information_toget_source_column_name].str.extract("(\d*\.?\d+)", expand=True).astype(float)
                        # information_toget_source_column_name].str.extract('(\d+\.\d+)').astype(float)
                        if pd.isnull(testing_column).sum() >= 0:
                            master_index_file_with_desired_field_all_merges[information_toget_source_column_name] = \
                                master_index_file_with_desired_field_all_merges[information_toget_source_column_name].str.extract('(\d+)').astype(float)
                        else:
                            master_index_file_with_desired_field_all_merges[information_toget_source_column_name] = testing_column
                if query_type == 'max':
                    if bounding_field == str(np.nan) or pd.isnull(bounding_field):
                        query_output_source = master_index_file_with_desired_field_all_merges[ \
                            list(aggregating_columns) + [information_toget_source_column_name]] \
                            .groupby(list(aggregating_columns)).max().reset_index()
                    else:
                        master_index_with_boundingfield_max = master_index_file_with_desired_field_all_merges[ \
                            list(aggregating_columns) + [bounding_field]] \
                            .groupby(list(aggregating_columns)).max().reset_index() \
                            .rename(columns={bounding_field: bounding_field + '_max'})
                        query_output_source = master_index_with_boundingfield_max.merge( \
                            master_index_file_with_desired_field_all_merges[ \
                                list(aggregating_columns) + [bounding_field] + [information_toget_source_column_name]],
                            how='left', \
                            left_on=list(aggregating_columns) + [bounding_field + '_max'],
                            right_on=list(aggregating_columns) + [bounding_field]) \
                            .groupby(list(aggregating_columns) + [bounding_field + '_max']).median().reset_index() \
                            .drop([bounding_field + '_max'], axis=1)
                        del master_index_with_boundingfield_max
                elif query_type == 'min':
                    if bounding_field == str(np.nan) or  pd.isnull(bounding_field):
                        query_output_source = master_index_file_with_desired_field_all_merges[ \
                            list(aggregating_columns) + [information_toget_source_column_name]] \
                            .groupby(list(aggregating_columns)).min().reset_index()
                    else:
                        master_index_with_boundingfield_min = master_index_file_with_desired_field_all_merges[ \
                            list(aggregating_columns) + [bounding_field]] \
                            .groupby(list(aggregating_columns)).min().reset_index() \
                            .rename(columns={bounding_field: bounding_field + '_min'})
                        query_output_source = master_index_with_boundingfield_min.merge( \
                            master_index_file_with_desired_field_all_merges[ \
                                list(aggregating_columns) + [bounding_field] + [information_toget_source_column_name]],
                            how='left', \
                            left_on=list(aggregating_columns) + [bounding_field + '_min'],
                            right_on=list(aggregating_columns) + [bounding_field]) \
                            .groupby(list(aggregating_columns) + [bounding_field + '_min']).median().reset_index() \
                            .drop([bounding_field + '_min'], axis=1)
                        del master_index_with_boundingfield_min
                elif query_type == 'top1':
                    query_output_source = mode(master_index_file_with_desired_field_all_merges[ \
                        list(aggregating_columns) + [information_toget_source_column_name]], list(aggregating_columns), \
                        information_toget_source_column_name, 'count')
                elif query_type == 'sum':
                    query_output_source = master_index_file_with_desired_field_all_merges[ \
                        list(aggregating_columns) + [information_toget_source_column_name]].groupby(
                        list(aggregating_columns)) \
                        .sum().reset_index()
                elif query_type == 'all':
                    # if information_toget_source_column_name == 'FINAL_CALC_CITY_FE_4':
                    #     print(information_toget_source_column_name)
                    query_output_source = master_index_file_with_desired_field_all_merges[ \
                        list(aggregating_columns) + [information_toget_source_column_name]].groupby(\
                        list(aggregating_columns))[information_toget_source_column_name].apply(lambda x: '|'.join(map(str, x))).reset_index()
                    for all_count in range(0, len(query_output_source)):
                        query_output_source[information_toget_source_column_name][all_count] = \
                            '|'.join(list(pd.Series(query_output_source[information_toget_source_column_name][all_count].split('|')).unique()))
                elif query_type == 'avg':
                    master_index_file_with_desired_field_all_merges[information_toget_source_column_name] = \
                        pd.to_numeric(master_index_file_with_desired_field_all_merges[information_toget_source_column_name], errors='coerce')
                    if weighting_field == str(np.nan) or pd.isnull(weighting_field):
                        query_output_source = master_index_file_with_desired_field_all_merges[ \
                            list(aggregating_columns) + [information_toget_source_column_name]].groupby(
                            list(aggregating_columns)).mean().reset_index()
                    else:
                        query_output_source = master_index_file_with_desired_field_all_merges[ \
                         list(aggregating_columns) + [weighting_field] + [information_toget_source_column_name]].groupby(list(aggregating_columns)).apply(weighted_average)
                        query_output_source = query_output_source.drop(weighting_field, axis=1).replace(0, np.nan) # drop weighting_field column
                        # query_output_source.dropna(subset=list(aggregating_columns), inplace=True)
                        # query_output_source = query_output_source.drop_duplicates(list(aggregating_columns)).reset_index() # don't drop np.nan and '' for many empty max. towing capacity
                    try:
                        query_output_source = query_output_source.drop(list(aggregating_columns), axis=1).reset_index()
                    except KeyError:
                        query_output_source = query_output_source.reset_index()
                # master_index_with_desired_field = master_index_with_desired_field.drop(weighting_field, axis=1)
                del master_index_file_with_desired_field_all_merges
                query_output_source = query_output_source \
                    .rename(columns={information_toget_source_column_name: all_subarray['Output Column Name'][all_subarray_count]})
                query_columns = pd.Series(query_output_source.columns)
                query_output_source = query_output_source[list(query_columns[~query_columns.astype(str).str.contains(str(np.nan))])]
                try:
                    query_output
                except NameError:  # First query output
                    query_output = query_output_source.sort_values(list(aggregating_columns)).reset_index(drop=True)
                else:
                    query_output = pd.merge_ordered(query_output, query_output_source, how='outer', \
                        on=list(aggregating_columns)).sort_values(list(aggregating_columns)).reset_index(drop=True)
                del query_output_source
        del master_index_file_with_desired_fields_all_merges
        # if unique_sourcename == 'OEM Towing Guide':
            # print(query_output)
        #     query_output = query_output.drop(['Towing Capacity_Edmunds'], axis=1)
        #     query_output = pd.concat([Edmunds_query_output, query_output], axis=1)
    unique_column_names = pd.Series(all_array['Output Column'].unique()).dropna().reset_index(drop=True)
    for output_column in unique_column_names:
        print(output_column)
        new_column = pd.Series(np.zeros(len(query_output)), name = output_column).replace(0,np.nan)
        applicable_array = all_array[['Priority', 'Output Column Name']][all_array['Output Column']==output_column]\
            .sort_values('Priority').reset_index(drop=True)
        for applicable_column in applicable_array['Output Column Name']:
            try:
                query_output[applicable_column]
            except KeyError:
                query_output[applicable_column] = pd.Series(np.zeros(len(query_output))).replace(0,np.nan)
            try:
                new_column[pd.isnull(new_column)] = query_output[applicable_column][pd.isnull(new_column)]
            except KeyError:
                new_column[pd.isnull(new_column)] = pd.Series(np.zeros(len(query_output))).replace(0,np.nan)
        query_output = pd.concat([query_output, new_column],axis=1)

    # _trims = ['V6', 'V8', 'V12', 'WITH RANGE EXTENDER', '(COUPE)', 'COUPE', 'XDRIVE', 'SDRIVE', '(CONVERTIBLE)', 'CONVERTIBLE', 'SRT', 'AWD', 'RWD', 'FWD', '4X2', '4X4', 'CLASSIC', 'UNLIMITED', '4-DOOR', '5-DOOR', \
    #           'REAR', 'WHEEL', 'DRIVE', '(RWD)', 'HYBRID', '2DR', '4DR', '5DR', '4MATIC', 'ALL4', 'F SPORT', 'SPORT', 'HEV', 'PHEV', 'ES', 'ECO', 'LE', 'XLE', 'HATCHBACK', 'XSE', 'FFV', 'CAB', 'PICKUP', 'CHASSIS', \
    #           'BADGE', 'BLACK', 'GRAN', 'TURISMO', 'COMPETITION', 'SPORTS', 'WAGON', 'EWB', 'LWB', 'BASE', 'PAYLOAD', 'LT', 'TIRE', 'USPS', 'A-SPEC', 'XL', 'ULTIMATE', 'BLUE', 'PLUG-IN HYBRID', 'SPORTBRAKE', \
    #           'SV', 'SVA', 'SVR', 'MHEV', 'SI4', 'TOURING', 'NISMO', 'SR/PLATINUM', 'RED', 'PRO-4X', 'PLATINUM', 'CARGO', 'VAN', 'SV/SL', 'LE/XLE/SE/LTD', 'LE/SE', 'XLE/XSE', 'SPORTWAGEN', '4MOTION', 'ALLTRACK', \
    #           'EXECUTIVE', 'ST', 'E-HYBRID', '2WD', '4WD', 'INCOMPLETE', 'SQ4', 'S', 'GTS', 'GEN2', 'SI4', 'MANUAL', 'P250', 'P300', 'GVWR>7599', 'LBS', '5.0L']
    #
    # df_query_output_grp = query_output.groupby(['CAFE_MFR_CD', 'CARLINE_NAME_all_Master Index', 'BodyID']).mean() # ELECTRIC POWER STEERING Edmunds all
    # carline_name_empty = []
    # for i in range(len(df_query_output_grp)):
    #     _cafe_mfr_cd = df_query_output_grp.index[i][0]
    #     _carline_name_all = df_query_output_grp.index[i][1]
    #     _bodyid = df_query_output_grp.index[i][2]
    #
    #     if 'F150' in _carline_name_all: _carline_name_base = 'F150'
    #     elif 'FUSION' in _carline_name_all: _carline_name_base = 'FUSION'
    #     elif 'MUSTANG' in _carline_name_all: _carline_name_base = 'MUSTANG'
    #     elif 'TRANSIT CONNECT' in _carline_name_all: _carline_name_base = 'TRANSIT CONNECT'
    #     elif 'CAMRY' in _carline_name_all: _carline_name_base = 'CAMRY'
    #     elif 'COROLLA' in _carline_name_all: _carline_name_base = 'COROLLA'
    #     elif 'TACOMA' in _carline_name_all: _carline_name_base = 'TACOMA'
    #     elif 'BOXSTER' in _carline_name_all: _carline_name_base = 'BOXSTER'
    #     elif 'CAYMAN' in _carline_name_all: _carline_name_base = 'CAYMAN'
    #     elif 'C10' in _carline_name_all: _carline_name_base = 'C10'
    #     elif 'K10' in _carline_name_all: _carline_name_base = 'K10'
    #     elif 'C15' in _carline_name_all: _carline_name_base = 'C15'
    #     elif 'K15' in _carline_name_all: _carline_name_base = 'K15'
    #     elif 'C1500' in _carline_name_all: _carline_name_base = 'C1500'
    #     elif 'K1500' in _carline_name_all: _carline_name_base = 'K1500'
    #     elif 'K1500' in _carline_name_all: _carline_name_base = 'K1500'
    #     else:
    #         _carline_name = str(_carline_name_all).strip().split(' ')
    #         if len(_carline_name) > 1:
    #             tmp = []
    #             for i in range(len(_carline_name)):
    #                 if ('(' in _carline_name[i]) and (')' not in _carline_name[i]):
    #                     pass
    #                 elif (')' in _carline_name[i]) and ('(' not in _carline_name[i]):
    #                     pass
    #                 elif (_carline_name[i] not in _trims):
    #                     tmp.append(_carline_name[i].strip())
    #             _carline_name_base = ' '.join(tmp)
    #
    #     try:
    #         carline_name_checks = (query_output['CAFE_MFR_CD'] == _cafe_mfr_cd) & (query_output['CARLINE_NAME_all_Master Index'].str.contains(_carline_name_base))
    #     except KeyError:
    #         try:
    #             print(_carline_name_base)
    #             _carline_name_base = _carline_name_base.strip().split(' ')[0]
    #             carline_name_checks = (query_output['CAFE_MFR_CD'] == _cafe_mfr_cd) & (query_output['CARLINE_NAME_all_Master Index'].str.contains(_carline_name_base))
    #         except KeyError:
    #             continue
    #     try:
    #         df_query_output = query_output.loc[carline_name_checks, :]
    #     except KeyError:
    #         print(_carline_name_base, _carline_name_all)
    #         continue
    #     if pd.isnull(df_query_output['Electric Power Steering_all']).sum() == 0: continue
    #     if (~pd.isnull(df_query_output['Electric Power Steering_all']) == True).sum() == 0: continue
    #     df_query_output_index = list(df_query_output.index)
    #     df_query_output.reset_index(drop=True, inplace=True)
    #     _eps_yes_index = df_query_output.loc[df_query_output['Electric Power Steering_all'] == 'yes', 'Electric Power Steering_all'].index
    #     _eps_no_index = df_query_output.loc[df_query_output['Electric Power Steering_all'] != 'yes', 'Electric Power Steering_all'].index
    #     for j in range(len(_eps_no_index)):
    #         query_output['Electric Power Steering_all'][df_query_output_index[_eps_no_index[j]]] = 'yes' # query_output.loc did not work

    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    query_output = query_output.replace([np.nan, str(np.nan)], '')
    query_output = query_output[list(aggregating_columns) + list(all_array['Output Column'].unique())+list(all_array['Output Column Name'].unique())]
    query_output = query_output.sort_values(list(aggregating_columns)).reset_index(drop=True)
    query_output = query_output.loc[:, ~query_output.columns.duplicated()]
    query_output.loc[(query_output['TARGET_COEF_BEST_MTH_min'] == 0) & (query_output['TARGET_COEF_BEST_MTH_max'] == 0), 'TARGET_COEF_BEST_MTH'] = 0 #.replace('', 0, inplace=True, regex=True)
    query_output.loc[(query_output['TARGET_COEF_BEST_MTH_min'] == 0) & (query_output['TARGET_COEF_BEST_MTH_max'] == 1), 'TARGET_COEF_BEST_MTH'] = 0 #.

    _FE_columns = ['FINAL_CALC_CITY_FE_4', 'FINAL_CALC_HWY_FE_4', 'FINAL_CALC_COMB_FE_4']
    _ELEC_columns = ['ELEC_KWH_100MILES_CITY_FE_4', 'ELEC_KWH_100MILES_HWY_FE_4', 'ELEC_KWH_100MILES_COMB_FE_4']
    _idx_HWY_GHG_1_all = query_output.columns.get_loc('FINAL_CALC_HWY_GHG_1_all')
    df_tmp = pd.DataFrame(np.zeros(len(query_output['FINAL_CALC_CITY_FE_4'])))
    for i in range(len(_ELEC_columns)):
        _col_name = _ELEC_columns[i]
        query_output.insert(_idx_HWY_GHG_1_all + i + 1, _col_name, df_tmp)

    for i in range(len(query_output)):
        for j in range(len(_ELEC_columns)):
            _col_name_FE = _FE_columns[j]
            _col_name_ELEC = _ELEC_columns[j]
            if(query_output.loc[i, 'Electrification Category'] == 'EV'):
                try:
                    query_output.loc[i, _col_name_ELEC] = round(33.705 * 100 / query_output.loc[i, _col_name_FE], 1)
                except KeyError:
                    pass
            else:
                query_output.loc[i, _col_name_ELEC] = np.nan

    if '_plus_MTH_34' in master_index_filename: Query_filename = 'Query_plus_MTH_34'
    else: Query_filename = 'Query_MTH_012'

    query_output.loc[query_output['Drive System Code_all'] == 'F|A', 'Drive System Code_all'] = 'A|F'
    query_output.loc[query_output['Drive System Code_all'] == 'R|A', 'Drive System Code_all'] = 'A|R'
    query_output=query_output.rename({'Drive System Code_all': 'Drive Sys tstcar_all', 'DRIVE TYPE_all': 'Drive Sys Edmunds_all'}, axis=1)

    # _airbags = query_output.columns[query_output.columns.str.contains('AIRBAG')].tolist() + ['STABILITY CONTROL_all', 'TRACTION CONTROL_all', 'TIRE PRESSURE MONITORING_all']
    # for i in range(len(_airbags)):
    #     _airbag = _airbags[i]
    #     query_output.loc[query_output[_airbag] == 'null-|yes', _airbag] = 'yes|null'
    #     query_output.loc[query_output[_airbag] == 'yes|null-', _airbag] = 'yes|null'
    #     query_output.loc[query_output[_airbag] == 'null-', _airbag] = 'null'
    _idx_nulls = query_output.loc[query_output['PRODUCTION_VOLUME_GHG_50_STATE'] == 0, :].index
    query_output.drop(_idx_nulls, inplace=True)

    query_output.to_csv(output_path + '\\' + str(model_year) + '_' + Query_filename + '_' + date_and_time + '.csv',index=False)

    query_output = query_output.drop(query_output.filter(regex='Master Index').columns, axis=1)
    query_output = query_output.drop(query_output.filter(regex='Edmunds').columns, axis=1)
    query_output = query_output.drop(query_output.filter(regex='OEM Towing Guide').columns, axis=1)
    query_output.to_csv(output_path + '\\' + str(model_year) + Query_filename + ' ' + date_and_time + '_noduplicatecolumns.csv',index=False)
    del all_array
    del master_index_file

    if (OMEGA_outputs == True):
        for i in range(len(cols_OMEGA_inputs)):
            if cols_OMEGA_inputs[i] not in query_output.columns:
                print(i, cols_OMEGA_inputs[i])

        omega_outputs = query_output.loc[:, cols_OMEGA_inputs]
        omega_outputs['cert_direct_oncycle_co2e_grams_per_mile']  = query_output['FINAL_CALC_COMB_GHG_1']
        omega_outputs['cert_direct_oncycle_kwh_per_mile']  = 33.705/query_output['FINAL_CALC_COMB_FE_4']
        df_edms = pd.read_csv("I:/Project/Midterm Review/Trends/Trends Data/Edmunds/2022 Measurements" + '\\' + 'Edmunds_MY2022_20230721-055344.csv', encoding="ISO-8859-1")
        df_twgd = pd.read_csv('I:/Project/Midterm Review/Trends/Trends Data/OEMTowingGuide' + '\\' + 'MY2019_OEMTowingGuide_Readin.csv', encoding="ISO-8859-1")

        omega_outputs = scraping_Edmunds_MSRPs(omega_outputs, df_edms)
        omega_outputs = GCWRs_from_towing_guide(df_twgd, omega_outputs)
        del query_output
        omega_outputs.to_csv(output_path + '\\' + str(model_year) + Query_filename + '_OMEGA_' + date_and_time + '.csv', index=False)
        del omega_outputs
    else:
        del query_output