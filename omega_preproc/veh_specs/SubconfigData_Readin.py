import pandas as pd
import datetime
import numpy as np
def Tractive_Energy_Calculation(A,B,C,ETW,FTP_Array, HWFET_Array, TechPac, Enghp):
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, lbfmph2hp
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
        Comb_DSOL_num = 0.55*((FTP_tractive_kWhr * 3600*1000)/(FTP_dist_mi*mi2km*1000)) + 0.45*((HWFET_tractive_kWhr * 3600*1000)/(HWFET_dist_mi*mi2km*1000))
        Comb_DSOL_den = 0.55*(Enghp * hp2kw*1000*FTP_time.max()/(FTP_dist_mi*mi2km*1000)) + 0.45*(Enghp * hp2kw*1000*HWFET_time.max()/(HWFET_dist_mi*mi2km*1000))
        Comb_DSOL = Comb_DSOL_num/Comb_DSOL_den
    else:
        Comb_DSOL = 0
    return (FTP_troadwork_mjpkm, HWFET_troadwork_mjpkm, Comb_DSOL, FTP_tractive_kWhr, HWFET_tractive_kWhr, \
            comb_forceavg_speed_mph)

def SubconfigData_Readin(rawdata_input_path, run_input_path, input_filename, output_path, \
                        exceptions_table, bodyid_filename, matched_bodyid_filename, unit_change_table, \
                         year, ratedhp_filename, ftp_drivecycle_filename, hwfet_drivecycle_filename, lineageid_filename):
    import Unit_Conversion
    from Unit_Conversion import hps2kwhr, mph2ftps, ftps2mph, kgpm32slugpft3
    v_aero_mph = 45
    air_density = 1.17 * kgpm32slugpft3

    raw_data = pd.read_csv(rawdata_input_path+'\\'+input_filename, encoding = "ISO-8859-1") #utf-8
    raw_data = raw_data[raw_data['MODEL_YEAR']==year].reset_index(drop=True)
    raw_data_city = raw_data[raw_data['TEST_PROC_CATEGORY'] == 'FTP75'].reset_index(drop=True)
    raw_data_hwy = raw_data[raw_data['TEST_PROC_CATEGORY'] == 'HWY'].reset_index(drop=True)

    raw_data_city = raw_data_city.rename(columns={'TEST_UNROUNDED_UNADJUSTED_FE': 'TEST_UNROUNDED_UNADJUSTED_FE_FTP'}).drop('TEST_PROC_CATEGORY',axis=1).reset_index(drop=True)
    raw_data_hwy = raw_data_hwy.rename(columns={'TEST_UNROUNDED_UNADJUSTED_FE': 'TEST_UNROUNDED_UNADJUSTED_FE_HWY'}).drop('TEST_PROC_CATEGORY',axis=1).reset_index(drop=True)

    #merge_columns = pd.Series(['LDFE_CAFE_SUBCONFIG_INFO_ID', 'VEH_CONFIG_NUM'])
    merge_columns = pd.Series(raw_data.columns)
    merge_columns = merge_columns[(merge_columns != 'TEST_UNROUNDED_UNADJUSTED_FE') \
        & (merge_columns != 'TEST_PROC_CATEGORY') & (merge_columns != 'TEST_NUMBER')].reset_index(drop=True)
    raw_data_merged = raw_data_city.merge(raw_data_hwy[['LDFE_CAFE_SUBCONFIG_INFO_ID']+['TEST_UNROUNDED_UNADJUSTED_FE_HWY']+['VEH_CONFIG_NUM']], how='left', \
        on = ['LDFE_CAFE_SUBCONFIG_INFO_ID', 'VEH_CONFIG_NUM']) # on = list(merge_columns)
    for unit_change_count in range(0,len(unit_change_table)):
        target_column_name = str(unit_change_table['Target Column'][unit_change_count])
        old_unit = str(unit_change_table['Old Unit'][unit_change_count]).replace('/','p').lower()
        new_unit = str(unit_change_table['New Unit'][unit_change_count]).replace('/','p').lower()
        unit_conversion = getattr(__import__('Unit_Conversion', fromlist=[str(old_unit + '2' + new_unit)]), str(old_unit + '2' + new_unit))
        raw_data_merged[target_column_name] = raw_data_merged[target_column_name] * unit_conversion
        raw_data_merged = raw_data_merged.rename(columns={target_column_name:target_column_name+'_'+new_unit.upper()})
    raw_data_merged['FUEL_NET_HEATING_VALUE_MJPL'] = pd.Series(raw_data_merged['FUEL_NET_HEATING_VALUE_MJPKG'] * raw_data_merged['FUEL_GRAVITY']).astype(float)
    raw_data_merged['TEST_UNROUNDED_UNADJUSTED_FE_COMB'] = pd.Series((0.55/raw_data_merged['TEST_UNROUNDED_UNADJUSTED_FE_FTP'] \
                                 + 0.45/raw_data_merged['TEST_UNROUNDED_UNADJUSTED_FE_HWY'])**-1)
    from Unit_Conversion import gal2l, km2mi
    raw_data_merged['Combined Fuel Energy Intensity (MJ/km)'] = pd.Series((1/raw_data_merged['TEST_UNROUNDED_UNADJUSTED_FE_COMB'])*raw_data_merged['FUEL_NET_HEATING_VALUE_MJPL']\
                                             *gal2l*km2mi)
    import Drive_Cycle_Differentiation_and_Integration
    (FTP_array, HWFET_array) = Drive_Cycle_Differentiation_and_Integration.\
        Drive_Cycle_Differentiation_and_Integration(run_input_path, ftp_drivecycle_filename, hwfet_drivecycle_filename)
    FTP_troadwork_mjpkm_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'FTP Tractive Road Energy Intensity (MJ/km)')
    HWFET_troadwork_mjpkm_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'HWFET Tractive Road Energy Intensity (MJ/km)')
    Comb_loadfactor_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'Combined Load Factor (%)')
    FTP_tractive_kWhr_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'FTP Tractive Energy (kWhr)')
    HWFET_tractive_kWhr_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'HWFET Tractive Energy (kWhr)')
    comb_forceavg_speed_mph_col = pd.Series(np.zeros(len(raw_data_merged)), name = 'COMB_FORCEAVG_SPEED_MPH')
    for subconfig_data_count in range (0,len(raw_data_merged)):
        (FTP_troadwork_mjpkm_col[subconfig_data_count], HWFET_troadwork_mjpkm_col[subconfig_data_count], \
         Comb_loadfactor_col[subconfig_data_count], FTP_tractive_kWhr_col[subconfig_data_count], \
         HWFET_tractive_kWhr_col[subconfig_data_count], comb_forceavg_speed_mph_col[subconfig_data_count]) = Tractive_Energy_Calculation(\
            raw_data_merged['TARGET_COEF_A'][subconfig_data_count], raw_data_merged['TARGET_COEF_B'][subconfig_data_count], \
            raw_data_merged['TARGET_COEF_C'][subconfig_data_count], raw_data_merged['VEH_ETW'][subconfig_data_count], \
            FTP_array, HWFET_array, 'TP00', 1)
    subconfig_data_table = pd.concat([raw_data_merged, FTP_troadwork_mjpkm_col, \
                                      HWFET_troadwork_mjpkm_col, FTP_tractive_kWhr_col, \
                                      HWFET_tractive_kWhr_col, comb_forceavg_speed_mph_col],axis=1)
    from Unit_Conversion import lbfmph2hp
    subconfig_data_table['CDA_EST'] = pd.Series(np.zeros(len(subconfig_data_table))).replace(0,'')
    subconfig_data_table['TOT_ROAD_LOAD_FORCE'] = pd.Series(np.zeros(len(subconfig_data_table))).replace(0, '')
    subconfig_data_table['RLHP_CALC'] = pd.Series(np.zeros(len(subconfig_data_table))).replace(0, '')
    subconfig_data_table['NON_AERO_ROAD_LOAD_FORCE'] = pd.Series(np.zeros(len(subconfig_data_table))).replace(0, '')
    subconfig_data_table['CDA_EST'][~pd.isnull(subconfig_data_table['TARGET_COEF_B'])]  = \
        ((subconfig_data_table['TARGET_COEF_B'][~pd.isnull(subconfig_data_table['TARGET_COEF_B'])] + \
        2*subconfig_data_table['TARGET_COEF_C'][~pd.isnull(subconfig_data_table['TARGET_COEF_B'])]*v_aero_mph) * (1/mph2ftps)) / \
        (air_density * v_aero_mph * mph2ftps)
    subconfig_data_table['TOT_ROAD_LOAD_FORCE'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] = \
        subconfig_data_table['TARGET_COEF_A'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] + \
        subconfig_data_table['TARGET_COEF_B'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] * \
        subconfig_data_table['COMB_FORCEAVG_SPEED_MPH'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] + \
        subconfig_data_table['TARGET_COEF_C'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] * \
        subconfig_data_table['COMB_FORCEAVG_SPEED_MPH'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])]**2
    subconfig_data_table['RLHP_CALC'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] = \
        50*lbfmph2hp*(subconfig_data_table['TARGET_COEF_A'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] + \
        subconfig_data_table['TARGET_COEF_B'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] * 50 + \
        subconfig_data_table['TARGET_COEF_C'][~pd.isnull(subconfig_data_table['TARGET_COEF_A'])] * (50*50))
    subconfig_data_table['NON_AERO_ROAD_LOAD_FORCE'][(subconfig_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (subconfig_data_table['CDA_EST'] != '')] = \
        subconfig_data_table['TOT_ROAD_LOAD_FORCE'][(subconfig_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (subconfig_data_table['CDA_EST'] != '')] - \
        0.5*air_density*subconfig_data_table['CDA_EST'][(subconfig_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (subconfig_data_table['CDA_EST'] != '')]* \
        (subconfig_data_table['COMB_FORCEAVG_SPEED_MPH'][(subconfig_data_table['TOT_ROAD_LOAD_FORCE'] != '') & (subconfig_data_table['CDA_EST'] != '')] * mph2ftps)**2

    subconfig_data_table['Combined Tractive Road Energy Intensity (MJ/km)'] \
        = pd.Series(0.55*subconfig_data_table['FTP Tractive Road Energy Intensity (MJ/km)'] + \
                    0.45*subconfig_data_table['HWFET Tractive Road Energy Intensity (MJ/km)'])
    subconfig_data_table['Displacement Specific Combined Tractive Road Energy Intensity (MJ/km/L)'] = \
        pd.Series(np.zeros(len(subconfig_data_table))).replace(0,'')
    subconfig_data_table['Displacement Specific Combined Fuel Energy Intensity (MJ/km/L)'] = \
        pd.Series(np.zeros(len(subconfig_data_table))).replace(0,'')
    subconfig_data_table['Displacement Specific Combined Tractive Road Energy Intensity (MJ/km/L)'][subconfig_data_table['DISPLACEMENT'] > 0] = \
        pd.Series(subconfig_data_table['Combined Tractive Road Energy Intensity (MJ/km)'][subconfig_data_table['DISPLACEMENT'] > 0] \
        /subconfig_data_table['DISPLACEMENT'][subconfig_data_table['DISPLACEMENT'] > 0])
    subconfig_data_table['Displacement Specific Combined Fuel Energy Intensity (MJ/km/L)'][subconfig_data_table['DISPLACEMENT'] > 0] = \
        pd.Series(subconfig_data_table['Combined Fuel Energy Intensity (MJ/km)'][subconfig_data_table['DISPLACEMENT'] > 0] \
        /subconfig_data_table['DISPLACEMENT'][subconfig_data_table['DISPLACEMENT'] > 0])

    subconfig_data_table['Combined Tractive Energy (kWhr)'] \
        = pd.Series(0.55*subconfig_data_table['FTP Tractive Energy (kWhr)'] + \
                    0.45*subconfig_data_table['HWFET Tractive Energy (kWhr)'])
    subconfig_data_table['Combined Powertrain Efficiency (%)'] = pd.Series(100*subconfig_data_table[\
        'Combined Tractive Road Energy Intensity (MJ/km)']/subconfig_data_table['Combined Fuel Energy Intensity (MJ/km)'])
    subconfig_data_table['Fuel Type Category'] = subconfig_data_table['SUBCFG_FUEL_USAGE']
    ratedhp_array = pd.read_csv(run_input_path+'\\'+ratedhp_filename)
    subconfig_data_table = pd.merge_ordered(subconfig_data_table, ratedhp_array, how='left', \
        on = 'LDFE_CAFE_SUBCONFIG_INFO_ID').reset_index(drop=True)
    subconfig_data_table['Combined Load Factor (%)'] = pd.Series(np.zeros(len(subconfig_data_table))).replace(0,'')
    subconfig_data_table['Combined Load Factor (%)'][subconfig_data_table['ENG_RATED_HP'] > 0] = subconfig_data_table[\
        'Combined Tractive Energy (kWhr)'][subconfig_data_table['ENG_RATED_HP'] > 0]*100 \
        /(subconfig_data_table['ENG_RATED_HP'][subconfig_data_table['ENG_RATED_HP'] > 0]* \
          ((0.55*FTP_array['Time (s)'].max() + 0.45*HWFET_array['Time (s)'].max()) * hps2kwhr))
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    subconfig_data_table.to_csv(output_path + '\\' + 'Subconfig Data Readin'+'_MY'+str(year) +' ' +date_and_time+'.csv', \
                                index=False, encoding = "ISO-8859-1")
