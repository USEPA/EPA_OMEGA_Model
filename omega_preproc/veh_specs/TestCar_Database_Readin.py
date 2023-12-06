import pandas as pd
import datetime
import numpy as np
from Unit_Conversion import hps2kwhr

testcar_LineageIDs_to_footprint_lineageids_Matching = False
def Tractive_Energy_Calculation(A,B,C,ETW,FTP_Array, HWFET_Array, TechPac, Enghp):
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr, lbfmph2hp
    FTP_dist_mi = FTP_Array['Displacement (mi)'].sum()
    FTP_time = FTP_Array['Time (s)']
    FTP_dt = FTP_time[1]-FTP_time[0]

    HWFET_dist_mi = HWFET_Array['Displacement (mi)'].sum()
    HWFET_time = HWFET_Array['Time (s)']
    HWFET_dt = HWFET_time[1]-HWFET_time[0]

    FTP_velocity_mph = FTP_Array['Velocity (mph)']
    FTP_velocity_mps = FTP_velocity_mph * mph2mps
    FTP_acceleration_mph2 = FTP_Array['Acceleration (mph2)']
    FTP_acceleration_mps2 = FTP_acceleration_mph2 * mph22mps2

    HWFET_velocity_mph = HWFET_Array['Velocity (mph)']
    HWFET_velocity_mps = HWFET_velocity_mph * mph2mps
    HWFET_acceleration_mph2 = HWFET_Array['Acceleration (mph2)']
    HWFET_acceleration_mps2 = HWFET_acceleration_mph2 * mph22mps2

    FTP_inertia_kw = ETW * (lbf2n / gravity_mps2) * FTP_acceleration_mps2 * FTP_velocity_mps / 1000
    HWFET_inertia_kw = ETW * (lbf2n / gravity_mps2) * HWFET_acceleration_mps2 * HWFET_velocity_mps / 1000

    FTP_roadload_kw = -1 * (A + B * FTP_velocity_mph + C * FTP_velocity_mph ** 2) * lbf2n * FTP_velocity_mps / 1000
    HWFET_roadload_kw = -1 * (A + B * HWFET_velocity_mph + C * HWFET_velocity_mph ** 2) * lbf2n * HWFET_velocity_mps / 1000

    FTP_combined = FTP_inertia_kw-FTP_roadload_kw
    HWFET_combined = HWFET_inertia_kw-HWFET_roadload_kw

    FTP_tractive_kw = FTP_combined[FTP_combined >= 0].sum()
    HWFET_tractive_kw = HWFET_combined[HWFET_combined >= 0].sum()

    FTP_tractive_kWhr = FTP_tractive_kw * FTP_dt / 3600
    FTP_troadwork_mjpkm = FTP_tractive_kWhr * 3.6 / (FTP_dist_mi * mi2km)
    HWFET_tractive_kWhr = HWFET_tractive_kw * HWFET_dt / 3600
    HWFET_troadwork_mjpkm = HWFET_tractive_kWhr * 3.6 / (HWFET_dist_mi * mi2km)
    
    FTP_forceavg_speed_num = (A * FTP_velocity_mph ** 2 + B * FTP_velocity_mph ** 3 + C * FTP_velocity_mph ** 4)
    FTP_energyavg_speed_num = (A * FTP_velocity_mph + B * FTP_velocity_mph ** 2 + C * FTP_velocity_mph ** 3)
    FTP_forceavg_speed_den = FTP_energyavg_speed_num
    FTP_energyavg_speed_den = (A + B * FTP_velocity_mph + C * FTP_velocity_mph ** 2)

    HWFET_forceavg_speed_num = (A * HWFET_velocity_mph ** 2 + B * HWFET_velocity_mph ** 3 + C * HWFET_velocity_mph ** 4)
    HWFET_energyavg_speed_num = (A * HWFET_velocity_mph + B * HWFET_velocity_mph ** 2 + C * HWFET_velocity_mph ** 3)
    HWFET_forceavg_speed_den = HWFET_energyavg_speed_num
    HWFET_energyavg_speed_den = (A + B * HWFET_velocity_mph + C * HWFET_velocity_mph ** 2)

    try:
        FTP_forceavg_speed_mph = FTP_forceavg_speed_num.sum() / FTP_forceavg_speed_den.sum()
        HWFET_forceavg_speed_mph = HWFET_forceavg_speed_num.sum() / HWFET_forceavg_speed_den.sum()
        comb_forceavg_speed_mph = (0.55*FTP_forceavg_speed_num.sum() + 0.45*HWFET_forceavg_speed_num.sum()) / \
                              (0.55 * FTP_forceavg_speed_den.sum() + 0.45 * HWFET_forceavg_speed_den.sum())

        FTP_energyavg_speed_mph = FTP_energyavg_speed_num.sum() / FTP_energyavg_speed_den.sum()
        HWFET_energyavg_speed_mph = HWFET_energyavg_speed_num.sum() / HWFET_energyavg_speed_den.sum()
        comb_energyavg_speed_mph = (0.55*FTP_energyavg_speed_num.sum() + 0.45*HWFET_energyavg_speed_num.sum()) / \
                              (0.55 * FTP_energyavg_speed_den.sum() + 0.45 * HWFET_energyavg_speed_den.sum())
    except ZeroDivisionError:
        FTP_forceavg_speed_mph = 'inconclusive'
        HWFET_forceavg_speed_mph = 'inconclusive'
        comb_forceavg_speed_mph = 'inconclusive'
        FTP_energyavg_speed_mph = 'inconclusive'
        HWFET_energyavg_speed_mph = 'inconclusive'
        comb_energyavg_speed_mph = 'inconclusive'

    if TechPac == 'TP00' or Enghp > 0:
        from Unit_Conversion import hp2kw
        Comb_LF_num = 0.55*FTP_tractive_kWhr + 0.45*HWFET_tractive_kWhr
        Comb_LF_den = Enghp * (0.55*FTP_Array['Time (s)'].max() + 0.45*HWFET_Array['Time (s)'].max()) * hps2kwhr
        Comb_LF = 100*Comb_LF_num/Comb_LF_den
    else:
        Comb_LF = 0
    return (FTP_troadwork_mjpkm, HWFET_troadwork_mjpkm, Comb_LF, FTP_tractive_kWhr, HWFET_tractive_kWhr, comb_forceavg_speed_mph)

def get_lineageids(year, run_input_path, matched_bodyid_file_raw, lineageid_filename):
    _lineageid_nulls = matched_bodyid_file_raw.loc[(matched_bodyid_file_raw['LineageID'] == -9) | (matched_bodyid_file_raw['LineageID'] == ''), :]
    _bodyid_nulls = matched_bodyid_file_raw.loc[matched_bodyid_file_raw['BodyID'] == -9, :]

    if (testcar_LineageIDs_to_footprint_lineageids_Matching == True) and ((len(_lineageid_nulls) > 0) or (len(_bodyid_nulls) > 0)):
        footprint_lineageid_in_vehghgid = pd.read_csv(run_input_path + '\\' + lineageid_filename)
        footprint_lineageid_in_vehghgid.rename({'MODEL_YEAR': 'Model Year', 'MFR_DIVISION_SHORT_NM': 'Division', 'CARLINE_NAME': 'Carline',
             'MODEL_TYPE_INDEX': 'Index (Model Type Index)'}, axis=1, inplace=True)
        footprint_lineageid_in_vehghgid['Model Year'] = footprint_lineageid_in_vehghgid['Model Year'].astype(int)
        footprint_lineageid_in_vehghgid['BodyID'] = footprint_lineageid_in_vehghgid['BodyID'].astype(int)
        footprint_lineageid_in_vehghgid['LineageID'] = footprint_lineageid_in_vehghgid['LineageID'].astype(int)
        footprint_lineageid_in_vehghgid['Index (Model Type Index)'] = footprint_lineageid_in_vehghgid['Index (Model Type Index)'].astype(int)
        footprint_lineageid_in_vehghgid = footprint_lineageid_in_vehghgid.drop_duplicates().reset_index(drop=True)
        footprint_lineageid_in_vehghgid_my = footprint_lineageid_in_vehghgid.loc[
                                             footprint_lineageid_in_vehghgid['Model Year'] == year, :].reset_index(drop=True)
        for i in range(len(footprint_lineageid_in_vehghgid_my)):
            _make = footprint_lineageid_in_vehghgid_my.loc[i, 'Division']
            _model = footprint_lineageid_in_vehghgid_my.loc[i, 'Carline']
            _model_splitted = _model.split(' ')

            _lineageid = footprint_lineageid_in_vehghgid_my.loc[i, 'LineageID']
            _bodyid = footprint_lineageid_in_vehghgid_my.loc[i, 'BodyID']
            # _model_type_index = footprint_lineageid_in_vehghgid_my.loc[i, 'Index (Model Type Index)']
            # print(_model)
            # (matched_bodyid_file_raw['Carline'].str.contains((_model), case=False, na=False)) &

            _idx_lineageid = matched_bodyid_file_raw.loc[(matched_bodyid_file_raw['Represented Test Veh Make'].str.contains((_make), case=False, na=False)) &
                                                            (matched_bodyid_file_raw['Represented Test Veh Model'] == _model) &
                                                            (matched_bodyid_file_raw['LineageID'] == -9), :].index
            if len(_idx_lineageid) > 0:
                matched_bodyid_file_raw.loc[_idx_lineageid, 'LineageID'] = _lineageid
            elif len(_model_splitted) > 1:
                _idx_lineageid = matched_bodyid_file_raw.loc[(matched_bodyid_file_raw['Represented Test Veh Make'].str.contains((_make), case=False, na=False)) &
                                                                (matched_bodyid_file_raw['Represented Test Veh Model'].str.contains((_model_splitted[0]), case=False, na=False)) &
                                                                (matched_bodyid_file_raw['LineageID'] == -9), :].index
                if len(_idx_lineageid) > 0:
                    matched_bodyid_file_raw.loc[_idx_lineageid, 'LineageID'] = _lineageid
            try:
                _idx_bodyid = matched_bodyid_file_raw.loc[(matched_bodyid_file_raw['Represented Test Veh Make'].str.contains((_make), case=False, na=False)) &
                                           (matched_bodyid_file_raw['Represented Test Veh Model'] == _model) &
                                           (matched_bodyid_file_raw['BodyID'] == -9), :].index
            except KeyError:
                print(_model)
                continue
            if len(_idx_bodyid) > 0:
                matched_bodyid_file_raw.loc[_idx_bodyid, 'BodyID'] = _bodyid
            elif len(_model_splitted) > 1:
                _idx_bodyid = matched_bodyid_file_raw.loc[(matched_bodyid_file_raw['Represented Test Veh Make'].str.contains((_make), case=False, na=False)) &
                                                             (matched_bodyid_file_raw['Represented Test Veh Model'].str.contains((_model_splitted[0]), case=False, na=False)) &
                                                             (matched_bodyid_file_raw['BodyID'] == -9), 'BodyID'].index
                if len(_idx_bodyid) > 0:
                    matched_bodyid_file_raw.loc[_idx_bodyid, 'BodyID'] = _bodyid

        _lineageid_nulls = matched_bodyid_file_raw.loc[matched_bodyid_file_raw['LineageID']==-9, :]
        _idx_nulls = _lineageid_nulls.index
        if len(_idx_nulls) > 0:
            footprint_lineageid_my = pd.read_csv(run_input_path + '\\' + 'footprint-lineageid_8bca1fd7_20230724.csv')
            footprint_lineageid_my = footprint_lineageid_my.loc[(footprint_lineageid_my['MODEL_YEAR'] == year), :].reset_index(drop=True)

        for i in range(len(_idx_nulls)):
            _idx = _idx_nulls[i]
            _make = matched_bodyid_file_raw.loc[_idx, 'Represented Test Veh Make']
            _model = matched_bodyid_file_raw.loc[_idx, 'Represented Test Veh Model']
            _make0 = _make.split(' ')[0]
            _model0 = _model.split(' ')[0]

            _idx_lineageids = footprint_lineageid_my.loc[((footprint_lineageid_my['FOOTPRINT_DIVISION_NM'] == _make) |
                                                        (footprint_lineageid_my['FOOTPRINT_DIVISION_NM'].str.contains((_make), case=False, na=False))) & \
                                                        ((footprint_lineageid_my['FOOTPRINT_CARLINE_NM'] == _model) |
                                                        (footprint_lineageid_my['FOOTPRINT_CARLINE_NM'].str.contains((_model), case=False, na=False))), 'LineageID'].index
            if (len(_idx_lineageids) > 0):
                matched_bodyid_file_raw.loc[_idx, 'LineageID'] = footprint_lineageid_my.loc[_idx_lineageids[0], 'LineageID']
                # matched_bodyid_file_raw.loc[_idx, 'BodyID'] = footprint_lineageid_my.loc[_idx_lineageids[0], 'BodyID']

        _lineageid_nulls = matched_bodyid_file_raw.loc[matched_bodyid_file_raw['LineageID']==-9, :]
        _idx_nulls = _lineageid_nulls.index
        for i in range(len(_idx_nulls)):
            _idx = _idx_nulls[i]
            _make = matched_bodyid_file_raw.loc[_idx, 'Represented Test Veh Make']
            _model = matched_bodyid_file_raw.loc[_idx, 'Represented Test Veh Model']
            _make0 = _make.split(' ')[0]
            _model0 = _model.split(' ')[0]

            _idx_lineageids = footprint_lineageid_my.loc[((footprint_lineageid_my['FOOTPRINT_DIVISION_NM'] == _make) |
                                                        (footprint_lineageid_my['FOOTPRINT_DIVISION_NM'].str.contains((_make), case=False, na=False))) & \
                                                        ((footprint_lineageid_my['FOOTPRINT_CARLINE_NM'].str.contains((_model), case=False, na=False)) | \
                                                        (footprint_lineageid_my['FOOTPRINT_CARLINE_NM'].str.contains((_model0), case=False, na=False))), 'LineageID'].index
            if (len(_idx_lineageids) > 0):
                matched_bodyid_file_raw.loc[_idx, 'LineageID'] = footprint_lineageid_my.loc[_idx_lineageids[0], 'LineageID']
            # matched_bodyid_file_raw.loc[_idx, 'BodyID'] = footprint_lineageid_my.loc[_idx_lineageids[0], 'BodyID']
    return matched_bodyid_file_raw
def TestCar_Database_Readin(rawdata_input_path, run_input_path, input_filename, output_path, \
                        exceptions_table, bodyid_filename, matched_bodyid_filename, unit_change_table, \
                         year, ratedhp_filename, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                        lineageid_filename, skiprows_vec):
    import Unit_Conversion
    raw_data = pd.read_csv(rawdata_input_path+'\\'+input_filename) #utf-8 , encoding = "ISO-8859-1"
    raw_data = raw_data.loc[raw_data['Model Year'] == year, :]
    exceptions_table = exceptions_table.loc[exceptions_table['Model Year'] == year, :].reset_index(drop=True)
    if (len(exceptions_table) > 0):
        for error_check_count in range(0, len(exceptions_table)):
            if exceptions_table['Numeric (y/n)'][error_check_count] == 'y':
                raw_data.loc[(raw_data['Represented Test Veh Make'] == exceptions_table['Represented Test Veh Make'][error_check_count]) & \
                    (raw_data['Represented Test Veh Model'] == exceptions_table['Represented Test Veh Model'][error_check_count]) & \
                    (raw_data[exceptions_table['Column Name'][error_check_count]].astype(float) == float(exceptions_table['Old Value'][error_check_count])), \
                    exceptions_table['Column Name'][error_check_count]] = float(exceptions_table['New Value'][error_check_count])
            else:
                if exceptions_table.loc[error_check_count, 'Correction Type'] == 'Replace':
                    raw_data.loc[(raw_data['Represented Test Veh Make'] == exceptions_table['Represented Test Veh Make'][error_check_count]) & \
                        (raw_data['Represented Test Veh Model'] == exceptions_table['Represented Test Veh Model'][error_check_count]) & \
                        (raw_data[exceptions_table['Column Name'][error_check_count]] == exceptions_table['Old Value'][error_check_count]), \
                        exceptions_table['Column Name'][error_check_count]] = exceptions_table['New Value'][error_check_count]
                elif exceptions_table.loc[error_check_count, 'Correction Type'] == 'Replace Part':
                    _idx = raw_data.loc[(raw_data['Represented Test Veh Make'] == exceptions_table['Represented Test Veh Make'][error_check_count]) & \
                        (raw_data[exceptions_table['Column Name'][error_check_count]].str.contains((exceptions_table['Old Value'][error_check_count]), case=False, na=False)), :].index

                    raw_data.loc[_idx, exceptions_table['Column Name'][error_check_count]].replace(exceptions_table['Old Value'][error_check_count], exceptions_table['New Value'][error_check_count])
    df_tmp = raw_data.loc[(raw_data['Represented Test Veh Model'].str.contains(('Supra'), case=False, na=False)), :]

    raw_data = raw_data[raw_data['Test Procedure Description'] != 'Cold CO']
    raw_data = raw_data[raw_data['Model Year']==year].reset_index(drop=True)
    cycle_category = pd.Series(raw_data['Test Category'], name = 'Cycle Category')
    cycle_category[raw_data['Test Procedure Description'] == 'Charge Depleting UDDS'] = 'FTP'
    cycle_category[raw_data['Test Procedure Description'] == 'Charge Depleting Highway'] = 'HWY'
    raw_data_city = raw_data[cycle_category == 'FTP'].reset_index(drop=True)
    raw_data_hwy = raw_data[cycle_category == 'HWY'].reset_index(drop=True)

    raw_data_city = raw_data_city.rename(columns={'RND_ADJ_FE': 'RND_ADJ_FE_FTP', \
        'Test Procedure Description' : 'Test Procedure Description_FTP', \
        'Test Fuel Type Description':'Test Fuel Type Description_FTP'}).drop('Test Category',axis=1).reset_index(drop=True)
    raw_data_hwy = raw_data_hwy.rename(columns={'RND_ADJ_FE': 'RND_ADJ_FE_HWY', \
        'Test Procedure Description' : 'Test Procedure Description_HWY', \
        'Test Fuel Type Description':'Test Fuel Type Description_HWY'}).drop('Test Category',axis=1).reset_index(drop=True)

    #merge_columns = pd.Series(['LDFE_CAFE_SUBCONFIG_INFO_ID', 'VEH_CONFIG_NUM'])
    merge_columns = pd.Series(['Test Vehicle ID'] + ['Test Veh Configuration #'])
    raw_data_merged = raw_data_city.merge(raw_data_hwy[list(merge_columns)+\
        ['RND_ADJ_FE_HWY'] + ['Test Procedure Description_HWY'] + ['Test Fuel Type Description_HWY']], how='left', on = list(merge_columns)) # on = list(merge_columns)
    for unit_change_count in range(0,len(unit_change_table)):
        if str(unit_change_table['Data Source'][unit_change_count]) == 'Test Car':
            target_column_name = str(unit_change_table['Target Column'][unit_change_count])
            old_unit = str(unit_change_table['Old Unit'][unit_change_count]).replace('/','p').lower()
            new_unit = str(unit_change_table['New Unit'][unit_change_count]).replace('/','p').lower()
            unit_conversion = getattr(__import__('Unit_Conversion', fromlist=[str(old_unit + '2' + new_unit)]), str(old_unit + '2' + new_unit))
            raw_data_merged[target_column_name] = raw_data_merged[target_column_name] * unit_conversion
            raw_data_merged = raw_data_merged.rename(columns={target_column_name:target_column_name+'_'+new_unit.upper()})
    comb_fueleconomy = pd.Series((0.55/raw_data_merged['RND_ADJ_FE_FTP'] \
                                 + 0.45/raw_data_merged['RND_ADJ_FE_HWY'])**-1, \
                       name = 'RND_ADJ_FE_COMB')
    from Unit_Conversion import gal2l, km2mi, kgpm32slugpft3, mph2ftps, ftps2mph
    # raw_data_merged['Combined Fuel Road Energy Intensity (MJ/km)'] = pd.Series((1/comb_fueleconomy)*raw_data_merged['FUEL_NET_HEATING_VALUE_MJPL']\
    #                                          *gal2l*km2mi)
    # matching_cyl_layout = pd.Series(raw_data_merged['CYLINDERS'].astype(str).str[0], name = 'Cylinder Layout Category').replace('E','ELE').astype(str)
    matching_cyl_num = pd.Series(raw_data_merged['# of Cylinders and Rotors'], name='Number of Cylinders Category').replace([np.nan, str(np.nan)],0).astype(int)
    #matching_cyl_num[matching_cyl_num==0] = 'ELE'
    matching_eng_disp = pd.Series(raw_data_merged['Test Veh Displacement (L)'],name='Engine Displacement Category')
    matching_eng_disp[matching_eng_disp < 0.5] = 1000
    matching_eng_disp[matching_eng_disp > 10] = 1000
    matching_eng_disp[matching_eng_disp == 1000] = 0
    matching_eng_disp = matching_eng_disp.astype(float).round(1)
    matching_drvtrn_layout = pd.Series(raw_data_merged['Drive System Description'], name = 'Drivetrain Layout Category')
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('Front')] = '2WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('4-Wheel')] = '4WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('All')] = '4WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('Rear')] = '2WD'
    matching_trns_numgears = pd.Series(raw_data_merged['# of Gears'], name='Number of Transmission Gears Category')
    matching_trns_category = pd.Series(np.zeros(len(raw_data_merged)), name = 'Transmission Type Category').replace(0,'A')
    matching_trns_category[matching_trns_numgears == 1] = '1ST'
    matching_trns_category[raw_data_merged['Tested Transmission Type'].str.contains('Automated Manual')] = 'AM'
    matching_trns_category[raw_data_merged['Tested Transmission Type'].str.contains('Automatic')] = 'A'
    matching_trns_category[raw_data_merged['Tested Transmission Type']=='Manual'] = 'M'
    matching_trns_category[raw_data_merged['Tested Transmission Type'].str.contains('Continuous')] = '1ST'

    # matching_boost_category = pd.Series(np.zeros(len(raw_data_merged)), name = 'Boost Type Category').replace(0,'N')
    # matching_boost_category[raw_data_merged['Trims'].str.contains('Turbo')] = 'TC'
    # matching_boost_category[raw_data_merged['Trims'].str.contains('Twincharger')] = 'TS'
    # matching_boost_category[raw_data_merged['Trims'].str.contains('S/C')] = 'SC'
    # matching_boost_category[matching_cyl_layout == 'ELE'] = 'ELE'
    matching_mfr_category = pd.Series(raw_data_merged['Represented Test Veh Make'], name='Make Category').astype(str)\
        .str.upper().replace(['ROLLS ROYCE', 'MODEL S','TESLA MODEL S','TESLA MODEL X', 'PAGANI AUTOMOBILI', 'QUANTUM IMPALA', 'SRT'], \
                             ['ROLLS-ROYCE', 'TESLA', 'TESLA','TESLA', 'PAGANI', 'QUANTUM', 'DODGE'])

    matching_fuel_category = pd.Series(np.zeros(len(raw_data_merged)), name = 'Fuel Type Category').replace(0,'G')
    matching_fuel_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('Diesel')] = 'D'
    matching_fuel_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('Electricity')] = 'E'
    matching_fuel_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('Hydrogen')] = 'E'
    matching_fuel_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('CNG')] = 'CNG'
    matching_fuel_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('E85')] = 'Eth'
    matching_fuel_category[matching_eng_disp.astype(str) == 'ELE'] = 'E'

    electrification_category = pd.Series(np.zeros(len(raw_data_merged)), name='Electrification Category').replace(0, 'N')
    REEV_Vehicles = pd.Series(pd.concat([\
        pd.Series(raw_data_merged['Actual Tested Testgroup'][(raw_data_merged['Test Procedure Description_FTP'] == 'Charge Depleting UDDS')]), \
        pd.Series(raw_data_merged['Actual Tested Testgroup'][(raw_data_merged['Test Procedure Description_HWY'] == 'Charge Depleting Highway')])])\
        .unique()).reset_index(drop=True)
    for vehicle in REEV_Vehicles:
        subarray = raw_data_merged[raw_data_merged['Actual Tested Testgroup'] == vehicle]
        if len(subarray[subarray['Test Procedure Description_FTP'] != 'Charge Depleting UDDS']) > 0 or \
            len(subarray[subarray['Test Procedure Description_HWY'] != 'Charge Depleting Highway']) > 0:
            electrification_category[raw_data_merged['Actual Tested Testgroup'] == vehicle] = 'PHEV'
        else:
            electrification_category[raw_data_merged['Actual Tested Testgroup'] == vehicle] = 'EV'
    electrification_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('Hydrogen')] = 'FCV'
    electrification_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('MHEV')] = 'MHEV'
    electrification_category[raw_data_merged['Test Fuel Type Description_FTP'].str.contains('Hydrogen')] = 'FCV'
    # electrification_category[(matching_fuel_category == 'D') & (raw_data_merged['Actual Tested Testgroup'].isin(REEV_Vehicles))] = 'REEV'
    # electrification_category[(matching_fuel_category == 'G') & (raw_data_merged['Test Procedure Description_FTP'] == 'Charge Depleting UDDS')] = 'REEV'
    # electrification_category[(matching_fuel_category == 'G') & (raw_data_merged['Test Procedure Description_HWY'] == 'Charge Depleting Highway')] = 'REEV'
    matching_fuel_category[(matching_fuel_category == 'G') & (raw_data_merged['Test Procedure Description_FTP'] == 'Charge Depleting UDDS')] = 'E'
    matching_fuel_category[(matching_fuel_category == 'G') & (raw_data_merged['Test Procedure Description_HWY'] == 'Charge Depleting Highway')] = 'E'
    #electrification_category[(electrification_category != 'REEV') & (matching_fuel_category == 'E')] = 'EV'
    electrification_category[(electrification_category == 'N') & ~pd.isnull(raw_data_merged['FE Bag 4']) & raw_data_merged['FE Bag 4'].astype(float) > 0] = 'HEV'
    testcar_data_table = pd.concat([raw_data_merged, comb_fueleconomy, matching_cyl_num, matching_eng_disp, matching_drvtrn_layout, \
                                      matching_trns_numgears, matching_trns_category, matching_mfr_category, \
                                      matching_fuel_category, electrification_category],axis=1)
    v_aero_mph = 45
    air_density = 1.17 * kgpm32slugpft3

    import Drive_Cycle_Differentiation_and_Integration
    drivecycle_filenames = ['ftpcol10hz.csv', 'hwycol10hz.csv'];
    drivecycle_input_filenames = ['FTP', 'HWY'];
    drivecycle_output_filenames = ['FTP', 'HWY'];

    (FTP_array, HWFET_array, US06_array, Custom_Array) = Drive_Cycle_Differentiation_and_Integration. \
        Drive_Cycle_Differentiation_and_Integration(run_input_path, drivecycle_filenames, drivecycle_input_filenames,
                                                    drivecycle_output_filenames);
    # (FTP_array, HWFET_array) = Drive_Cycle_Differentiation_and_Integration.\
    #     Drive_Cycle_Differentiation_and_Integration(run_input_path, ftp_drivecycle_filename, hwfet_drivecycle_filename)
    FTP_troadwork_mjpkm_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'FTP Tractive Road Energy Intensity (MJ/km)')
    HWFET_troadwork_mjpkm_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'HWFET Tractive Road Energy Intensity (MJ/km)')
    Comb_LF_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'Combined Load Factor (%)')
    FTP_tractive_kWhr_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'FTP Tractive Energy (kWhr)')
    HWFET_tractive_kWhr_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'HWFET Tractive Energy (kWhr)')
    comb_forceavg_speed_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'COMB_FORCEAVG_SPEED_MPH')
    for subconfig_data_count in range (0,len(raw_data_merged)):
        (FTP_troadwork_mjpkm_col[subconfig_data_count], HWFET_troadwork_mjpkm_col[subconfig_data_count], \
         Comb_LF_col[subconfig_data_count], FTP_tractive_kWhr_col[subconfig_data_count], \
         HWFET_tractive_kWhr_col[subconfig_data_count], comb_forceavg_speed_col[subconfig_data_count]) = Tractive_Energy_Calculation(\
            raw_data_merged['Target Coef A (lbf)'][subconfig_data_count], raw_data_merged['Target Coef B (lbf/mph)'][subconfig_data_count], \
            raw_data_merged['Target Coef C (lbf/mph**2)'][subconfig_data_count], raw_data_merged['Equivalent Test Weight (lbs.)'][subconfig_data_count], \
            FTP_array, HWFET_array, 'TP00', raw_data_merged['Rated Horsepower'][subconfig_data_count])
    testcar_data_table = pd.concat([raw_data_merged, comb_fueleconomy, FTP_troadwork_mjpkm_col, \
                                    HWFET_troadwork_mjpkm_col, FTP_tractive_kWhr_col, \
                                    HWFET_tractive_kWhr_col, Comb_LF_col, comb_forceavg_speed_col, \
                                    matching_cyl_num, matching_eng_disp, matching_drvtrn_layout, matching_trns_numgears, matching_trns_category, matching_mfr_category, \
                                    matching_fuel_category, electrification_category],axis=1)
    from Unit_Conversion import lbfmph2hp
    testcar_data_table['CDA_EST'] = pd.Series(np.zeros(len(testcar_data_table))).replace(0,'')
    testcar_data_table['TOT_ROAD_LOAD_FORCE'] = pd.Series(np.zeros(len(testcar_data_table))).replace(0, '')
    testcar_data_table['RLHP_CALC'] = pd.Series(np.zeros(len(testcar_data_table))).replace(0, '')
    testcar_data_table['NON_AERO_ROAD_LOAD_FORCE'] = pd.Series(np.zeros(len(testcar_data_table))).replace(0, '')
    testcar_data_table['CDA_EST'][~pd.isnull(testcar_data_table['Target Coef B (lbf/mph)'])]  = \
        ((testcar_data_table['Target Coef B (lbf/mph)'][~pd.isnull(testcar_data_table['Target Coef B (lbf/mph)'])] + \
        2*testcar_data_table['Target Coef C (lbf/mph**2)'][~pd.isnull(testcar_data_table['Target Coef B (lbf/mph)'])]*v_aero_mph) * (1/mph2ftps)) / \
        (air_density * v_aero_mph * mph2ftps)
    testcar_data_table['TOT_ROAD_LOAD_FORCE'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] = \
        testcar_data_table['Target Coef A (lbf)'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] + \
        testcar_data_table['Target Coef B (lbf/mph)'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] * \
        testcar_data_table['COMB_FORCEAVG_SPEED_MPH'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] + \
        testcar_data_table['Target Coef C (lbf/mph**2)'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] * \
        testcar_data_table['COMB_FORCEAVG_SPEED_MPH'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])]**2
    testcar_data_table['RLHP_CALC'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] = \
        50 * lbfmph2hp*(testcar_data_table['Target Coef A (lbf)'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] + \
        (testcar_data_table['Target Coef B (lbf/mph)'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] * 50) + \
        (testcar_data_table['Target Coef C (lbf/mph**2)'][~pd.isnull(testcar_data_table['Target Coef A (lbf)'])] * (50*50)))
    testcar_data_table['NON_AERO_ROAD_LOAD_FORCE'][(testcar_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (testcar_data_table['CDA_EST'] != '')] = \
        testcar_data_table['TOT_ROAD_LOAD_FORCE'][(testcar_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (testcar_data_table['CDA_EST'] != '')] - \
        0.5*air_density*testcar_data_table['CDA_EST'][(testcar_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (testcar_data_table['CDA_EST'] != '')]* \
        (testcar_data_table['COMB_FORCEAVG_SPEED_MPH'][(testcar_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (testcar_data_table['CDA_EST'] != '')] * mph2ftps)**2

    testcar_data_table['Combined Load Factor (%)'][matching_fuel_category == 'E'] = ''
    testcar_data_table['Combined Tractive Road Energy Intensity (MJ/km)'] \
        = pd.Series(0.55*testcar_data_table['FTP Tractive Road Energy Intensity (MJ/km)'] + \
                    0.45*testcar_data_table['HWFET Tractive Road Energy Intensity (MJ/km)'])
    testcar_data_table['Displacement Specific Combined Tractive Road Energy Intensity (MJ/km/L)'] = \
        pd.Series(np.zeros(len(testcar_data_table))).replace(0,'')
    testcar_data_table['Displacement Specific Combined Tractive Road Energy Intensity (MJ/km/L)'][matching_eng_disp > 0] = \
        pd.Series(testcar_data_table['Combined Tractive Road Energy Intensity (MJ/km)'][matching_eng_disp > 0] \
        /matching_eng_disp[matching_eng_disp > 0])
    testcar_data_table['Combined Tractive Energy (kWhr)'] \
        = pd.Series(0.55*testcar_data_table['FTP Tractive Energy (kWhr)'] + \
                    0.45*testcar_data_table['HWFET Tractive Energy (kWhr)'])
    testcar_data_table['FUEL_HEATING_VALUE_MJPL'] = pd.Series(np.zeros(len(testcar_data_table))).replace(0,32.05239499)
    testcar_data_table['FUEL_HEATING_VALUE_MJPL'][matching_fuel_category=='D']=36.53
    
    testcar_data_table['Combined Fuel Energy Intensity (MJ/km)'] \
        = pd.Series((1/testcar_data_table['RND_ADJ_FE_COMB'])*testcar_data_table['FUEL_HEATING_VALUE_MJPL']*km2mi*gal2l)
    testcar_data_table['Displacement Specific Combined Fuel Energy Intensity (MJ/km/L)'] = \
        pd.Series(np.zeros(len(testcar_data_table))).replace(0,'')
    testcar_data_table['Displacement Specific Combined Fuel Energy Intensity (MJ/km/L)'][matching_eng_disp > 0] = \
        pd.Series(testcar_data_table['Combined Fuel Energy Intensity (MJ/km)'][matching_eng_disp > 0] \
        /matching_eng_disp[matching_eng_disp > 0])

    if ('.csv' in bodyid_filename):
        # bodyid_file_raw = pd.read_csv(run_input_path + '\\' + bodyid_filename)
        bodyid_file_raw = pd.read_csv(run_input_path + '\\' + bodyid_filename, converters={'LineageID': int, 'BodyID': int, 'BodyID StartYear': int, 'BodyID EndYear': str})
        bodyid_file_raw = bodyid_file_raw.loc[pd.notnull(bodyid_file_raw['BodyID']), :].reset_index(drop=True)
        # bodyid_file_raw['BodyID'] = bodyid_file_raw['BodyID'].astype(int)
        # bodyid_file_raw['LineageID'] = bodyid_file_raw['LineageID'].astype(int)
    else:
        bodyid_file_raw = pd.read_excel(run_input_path + '\\' + bodyid_filename, converters={'LineageID': int, 'BodyID': int})

    bodyid_file_nonfuture = bodyid_file_raw[(bodyid_file_raw['BodyID StartYear'] <= year) & \
        (bodyid_file_raw['BodyID EndYear'] != 'xx')].reset_index(drop=True)
    bodyid_file_notnull = bodyid_file_nonfuture[bodyid_file_nonfuture['BodyID EndYear'] != 'null']
    bodyid_file_notnull['BodyID EndYear'] = bodyid_file_notnull['BodyID EndYear'].astype(int)
    bodyid_file = pd.concat([bodyid_file_notnull[bodyid_file_notnull['BodyID EndYear'] >= year], \
                             bodyid_file_nonfuture[bodyid_file_nonfuture['BodyID EndYear'] == 'null']]).reset_index(drop=True)
    del bodyid_file_raw, bodyid_file_nonfuture, bodyid_file_notnull

    try:
        matched_bodyid_file_raw = pd.read_csv(run_input_path+'\\'+matched_bodyid_filename, converters = {'LineageID': int, \
            'BodyID':int, 'Test Veh Configuration #':int, 'Year':int})
        matched_bodyid_file_raw = matched_bodyid_file_raw.loc[matched_bodyid_file_raw['Year'] == year, :]
        if (testcar_LineageIDs_to_footprint_lineageids_Matching == True):
            matched_bodyid_file_raw = get_lineageids(year, run_input_path, matched_bodyid_file_raw, lineageid_filename)

        matched_bodyid_file_modelyear = matched_bodyid_file_raw[matched_bodyid_file_raw['Year'] == year] \
                    .groupby(['Test Vehicle ID', 'Test Veh Configuration #']).agg(lambda x:x.value_counts().index[0]).reset_index();

        matched_bodyid_file = matched_bodyid_file_modelyear[matched_bodyid_file_modelyear['LineageID'] != -9].reset_index(drop=True);

        matched_bodyid_file_singlematch = matched_bodyid_file[matched_bodyid_file['BodyID'] != -9]
        matched_bodyid_file_multimatch = matched_bodyid_file[matched_bodyid_file['BodyID'] == -9].drop('BodyID',axis=1).reset_index(drop=True)
        matched_bodyid_file_multimatch = matched_bodyid_file_multimatch.merge(bodyid_file[['LineageID'] + ['BodyID']], how='left', on='LineageID').reset_index(drop=True)
        matched_bodyid_file_allmatches = pd.concat([matched_bodyid_file_singlematch, matched_bodyid_file_multimatch]).reset_index(drop=True)
        testcar_data_table = testcar_data_table\
            .merge(matched_bodyid_file_allmatches[['Test Vehicle ID']+['Test Veh Configuration #']+['LineageID'] + ['BodyID']]\
            ,how='left', on = ['Test Vehicle ID', 'Test Veh Configuration #']).reset_index(drop=True)
        date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
        testcar_missingentries = testcar_data_table[pd.isnull(testcar_data_table['LineageID'])].reset_index(drop=True)
        if (len(testcar_missingentries) > 0):
            testcar_missingentries.to_csv(output_path + '\\' + 'Missing Test Car Entries'+'_MY'+str(year) +' ' +date_and_time+'.csv', index=False)
        testcar_data_table = testcar_data_table[(~pd.isnull(testcar_data_table['LineageID'])) \
                                                & (~pd.isnull(testcar_data_table['BodyID']))].reset_index(drop=True)
        testcar_data_table['Combined Powertrain Efficiency (%)'] = pd.Series(100 * testcar_data_table[ \
            'Combined Tractive Road Energy Intensity (MJ/km)'] / testcar_data_table[
                                                                                 'Combined Fuel Energy Intensity (MJ/km)'])
        testcar_data_table['BodyID'] = testcar_data_table['BodyID'].astype(float).astype(int)
        testcar_data_table['LineageID'] = testcar_data_table['LineageID'].astype(float).astype(int)
        testcar_data_table = testcar_data_table[testcar_data_table['Test Fuel Type Description_FTP'] == \
            testcar_data_table['Test Fuel Type Description_HWY']].reset_index(drop=True)
        testcar_data_table = testcar_data_table.replace([np.nan, str(np.nan)], '')

        # aero_table = pd.read_csv(run_input_path+'\\'+aero_table_filename)
        # testcar_data_table_output = pd.merge_ordered(testcar_data_table, aero_table, how='left', on=['CALC_ID', 'BodyID'])
        testcar_data_table.to_csv(output_path + '\\' + 'Test Car' + '_MY' + str(year) + ' ' + date_and_time + '.csv', index=False)
    except FileNotFoundError:
        try:
            possible_bodyid_file = pd.read_csv(rawdata_input_path + '\\' + 'Test Car BodyID Check'+ '.csv')
        except FileNotFoundError:
            lineageid_file_raw = pd.read_csv(rawdata_input_path+'\\'+lineageid_filename, converters = {'LineageID': int})
            possible_bodyid_file = pd.merge_ordered(lineageid_file_raw, \
                bodyid_file[['LineageID', 'BodyID', 'ref_Model', 'ref_Model', 'BodyDescription']], how='left', on = 'LineageID').reset_index(drop=True)
            possible_bodyid_file.to_csv(rawdata_input_path + '\\' + 'Test Car BodyID Check'+ '.csv', \
                                      index=False)