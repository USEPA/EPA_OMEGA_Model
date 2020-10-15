import pandas as pd
import numpy as np
import math

from Unit_Conversion import km2mi, gal2l, s2hr
def Tractive_Energy_Calculation(A,B,C,ETW,Enghp, FTP_dist_mi, FTP_time, FTP_dt, \
    HWFET_dist_mi, HWFET_time, HWFET_dt, FTP_velocity_mph, FTP_velocity_mps, FTP_acceleration_mps2, HWFET_velocity_mph, \
                                HWFET_velocity_mps,HWFET_acceleration_mps2 ):
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr

    # FTP_dist_mi = FTP_Array['Displacement (mi)'].sum()
    # FTP_time = FTP_Array['Time (s)'].max()
    # FTP_dt = FTP_Array['Time (s)'][1]-FTP_Array['Time (s)'][0]

    # HWFET_dist_mi = HWFET_Array['Displacement (mi)'].sum()
    # HWFET_time = HWFET_Array['Time (s)'].max()
    # HWFET_dt = HWFET_Array['Time (s)'][1] - HWFET_Array['Time (s)'][0]

    # FTP_velocity_mph = FTP_Array['Velocity (mph)']
    # FTP_velocity_mps = FTP_velocity_mph * mph2mps
    # FTP_acceleration_mph2 = FTP_Array['Acceleration (mph2)']
    # FTP_acceleration_mps2 = FTP_acceleration_mph2 * mph22mps2
    # 
    # HWFET_velocity_mph = HWFET_Array['Velocity (mph)']
    # HWFET_velocity_mps = HWFET_velocity_mph * mph2mps
    # HWFET_acceleration_mph2 = HWFET_Array['Acceleration (mph2)']
    # HWFET_acceleration_mps2 = HWFET_acceleration_mph2 * mph22mps2

    FTP_inertia_kwhr = ETW * (lbf2n / gravity_mps2) * (FTP_acceleration_mps2 * FTP_velocity_mps / 1000) * FTP_dt * s2hr
    HWFET_inertia_kwhr = ETW * (lbf2n / gravity_mps2) * (HWFET_acceleration_mps2 * HWFET_velocity_mps / 1000) * HWFET_dt * s2hr

    FTP_roadload_kwhr = (A + B * FTP_velocity_mph + C * FTP_velocity_mph ** 2) * (lbf2n * FTP_velocity_mps / 1000) * FTP_dt * s2hr
    HWFET_roadload_kwhr = (A + B * HWFET_velocity_mph + C * HWFET_velocity_mph ** 2) * (lbf2n * HWFET_velocity_mps / 1000) * HWFET_dt * s2hr

    FTP_combined_kwhr = (FTP_inertia_kwhr+FTP_roadload_kwhr)
    HWFET_combined_kwhr = (HWFET_inertia_kwhr+HWFET_roadload_kwhr)

    FTP_tractive_kWhr = FTP_combined_kwhr[FTP_combined_kwhr >= 0].sum()
    HWFET_tractive_kWhr = HWFET_combined_kwhr[HWFET_combined_kwhr >= 0].sum()

    FTP_forceavg_speed_num = (A * FTP_velocity_mph ** 2+ B * FTP_velocity_mph ** 3 + C * FTP_velocity_mph ** 4)
    FTP_energyavg_speed_num = (A * FTP_velocity_mph + B * FTP_velocity_mph ** 2 + C * FTP_velocity_mph ** 3)
    FTP_forceavg_speed_den = FTP_energyavg_speed_num
    FTP_energyavg_speed_den = (A + B * FTP_velocity_mph + C * FTP_velocity_mph ** 2)
    
    HWFET_forceavg_speed_num = (A * HWFET_velocity_mph ** 2+ B * HWFET_velocity_mph ** 3 + C * HWFET_velocity_mph ** 4)
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

    FTP_troadwork_mjpkm = FTP_tractive_kWhr * 3.6 / (FTP_dist_mi * mi2km)
    HWFET_troadwork_mjpkm = HWFET_tractive_kWhr * 3.6 / (HWFET_dist_mi * mi2km)

    if Enghp > 0:
        Comb_LF_num = 0.55*FTP_tractive_kWhr + 0.45*HWFET_tractive_kWhr
        Comb_LF_den = Enghp * (0.55*FTP_time + 0.45*HWFET_time) * hps2kwhr
        Comb_LF = 100*Comb_LF_num/Comb_LF_den
    else:
        Comb_LF = 0
    return (FTP_troadwork_mjpkm, HWFET_troadwork_mjpkm, Comb_LF, FTP_tractive_kWhr, HWFET_tractive_kWhr, \
            FTP_forceavg_speed_mph, HWFET_forceavg_speed_mph,comb_forceavg_speed_mph,FTP_energyavg_speed_mph,\
            HWFET_energyavg_speed_mph,comb_energyavg_speed_mph)

def Calculate_Powertrain_Efficiency(ID_col, A_col, B_col, C_col, ETW_col, combmpg_col, run_input_path, \
                                    ftp_drivecycle_filename, hwfet_drivecycle_filename, engdisp_col, ratedhp_col, \
                                    fuelhv_col):
    import Drive_Cycle_Differentiation_and_Integration
    from Unit_Conversion import mph2mps,mph22mps2
    (FTP_array, HWFET_array) = Drive_Cycle_Differentiation_and_Integration.\
        Drive_Cycle_Differentiation_and_Integration(run_input_path, ftp_drivecycle_filename, hwfet_drivecycle_filename)

    FTP_dist_mi = FTP_array['Displacement (mi)'].sum()
    FTP_time = FTP_array['Time (s)'].max()
    FTP_dt = FTP_array['Time (s)'][1] - FTP_array['Time (s)'][0]

    HWFET_dist_mi = HWFET_array['Displacement (mi)'].sum()
    HWFET_time = HWFET_array['Time (s)'].max()
    HWFET_dt = HWFET_array['Time (s)'][1] - HWFET_array['Time (s)'][0]

    FTP_velocity_mph = FTP_array['Velocity (mph)']
    FTP_velocity_mps = FTP_velocity_mph * mph2mps
    FTP_acceleration_mph2 = FTP_array['Acceleration (mph2)']
    FTP_acceleration_mps2 = FTP_acceleration_mph2 * mph22mps2

    HWFET_velocity_mph = HWFET_array['Velocity (mph)']
    HWFET_velocity_mps = HWFET_velocity_mph * mph2mps
    HWFET_acceleration_mph2 = HWFET_array['Acceleration (mph2)']
    HWFET_acceleration_mps2 = HWFET_acceleration_mph2 * mph22mps2

    input_array = pd.concat([ID_col, A_col, B_col, C_col, ETW_col, ratedhp_col, combmpg_col, fuelhv_col], axis=1)
    unique_tractive_array = input_array[[ID_col.name, A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name]]\
        .groupby([A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name])\
        .first().reset_index().drop(ID_col.name,axis=1)
    A_col_new = unique_tractive_array[A_col.name]
    B_col_new = unique_tractive_array[B_col.name]
    C_col_new = unique_tractive_array[C_col.name]
    ETW_col_new = unique_tractive_array[ETW_col.name]
    ratedhp_col_new = unique_tractive_array[ratedhp_col.name]
    
    FTP_troadwork_mjpkm_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'FTP Tractive Road Energy Intensity (MJ/km)')
    HWFET_troadwork_mjpkm_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'HWFET Tractive Road Energy Intensity (MJ/km)')
    Comb_LF_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'Combined Load Factor (%)')
    FTP_tractive_kWhr_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'FTP Tractive Energy (kWhr)')
    HWFET_tractive_kWhr_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'HWFET Tractive Energy (kWhr)')
    FTP_forceavg_velocity_mph_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'FTP ForceAvg Velocity (mph)')
    HWFET_forceavg_velocity_mph_col = pd.Series(np.zeros(len(unique_tractive_array)), name='HWFET ForceAvg Velocity (mph)')
    comb_forceavg_velocity_mph_col = pd.Series(np.zeros(len(unique_tractive_array)), name='Combined ForceAvg Velocity (mph)')
    FTP_energyavg_velocity_mph_col = pd.Series(np.zeros(len(unique_tractive_array)), name = 'FTP EnergyAvg Velocity (mph)')
    HWFET_energyavg_velocity_mph_col = pd.Series(np.zeros(len(unique_tractive_array)), name='HWFET EnergyAvg Velocity (mph)')
    comb_energyavg_velocity_mph_col = pd.Series(np.zeros(len(unique_tractive_array)), name='Combined EnergyAvg Velocity (mph)')

    for data_count in range (0,len(unique_tractive_array)):
        print(data_count)
        # (FTP_troadwork_mjpkm_col[data_count], HWFET_troadwork_mjpkm_col[data_count], \
        #  Comb_LF_col[data_count], FTP_tractive_kWhr_col[data_count], \
        #  HWFET_tractive_kWhr_col[data_count], \
        #  FTP_forceavg_velocity_mph_col[data_count], HWFET_forceavg_velocity_mph_col[data_count], \
        #  comb_forceavg_velocity_mph_col[data_count], FTP_energyavg_velocity_mph_col[data_count], \
        #  HWFET_energyavg_velocity_mph_col[data_count], comb_energyavg_velocity_mph_col[data_count],) \
        #     = Tractive_Energy_Calculation(\
        #     A_col[data_count], B_col[data_count], \
        #     C_col[data_count], ETW_col[data_count], \
        #     FTP_array, HWFET_array, ratedhp_col[data_count])

        A = A_col_new[data_count]
        B = B_col_new[data_count]
        C = C_col_new[data_count]
        ETW = ETW_col_new[data_count]
        ratedhp = ratedhp_col_new[data_count]

        (FTP_troadwork_mjpkm, HWFET_troadwork_mjpkm, \
         Comb_LF, FTP_tractive_kWhr, \
         HWFET_tractive_kWhr, \
         FTP_forceavg_velocity_mph, HWFET_forceavg_velocity_mph, \
         comb_forceavg_velocity_mph, FTP_energyavg_velocity_mph, \
         HWFET_energyavg_velocity_mph, comb_energyavg_velocity_mph,) \
            = Tractive_Energy_Calculation(A, B, C, ETW, ratedhp, FTP_dist_mi, FTP_time, FTP_dt, \
            HWFET_dist_mi, HWFET_time, HWFET_dt, FTP_velocity_mph, FTP_velocity_mps, FTP_acceleration_mps2, HWFET_velocity_mph, \
            HWFET_velocity_mps,HWFET_acceleration_mps2)

        FTP_troadwork_mjpkm_col[data_count] = FTP_troadwork_mjpkm
        HWFET_troadwork_mjpkm_col[data_count] = HWFET_troadwork_mjpkm
        Comb_LF_col[data_count] = Comb_LF
        FTP_tractive_kWhr_col[data_count] = FTP_tractive_kWhr
        HWFET_tractive_kWhr_col[data_count] = HWFET_tractive_kWhr
        comb_energyavg_velocity_mph_col[data_count] = comb_energyavg_velocity_mph
        
    tractive_table = pd.concat([A_col_new, B_col_new, C_col_new, ETW_col_new, ratedhp_col_new, FTP_troadwork_mjpkm_col, \
                              HWFET_troadwork_mjpkm_col, FTP_tractive_kWhr_col, \
                              HWFET_tractive_kWhr_col, Comb_LF_col, FTP_forceavg_velocity_mph_col, \
                              HWFET_forceavg_velocity_mph_col, comb_forceavg_velocity_mph_col, \
                              FTP_energyavg_velocity_mph_col, \
                              HWFET_energyavg_velocity_mph_col, comb_energyavg_velocity_mph_col
                              ],axis=1)
    output_table = pd.merge_ordered(input_array, tractive_table, how='left', \
        on = [A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name]).sort_values(ID_col.name).reset_index(drop=True)
    engdisp_col = engdisp_col.replace([0,''],np.nan)
    output_table['Combined Tractive Road Energy Intensity (MJ/km)'] \
        = pd.Series(0.55*output_table['FTP Tractive Road Energy Intensity (MJ/km)'] + \
                    0.45*output_table['HWFET Tractive Road Energy Intensity (MJ/km)'])
    output_table['Displacement Specific Combined Tractive Road Energy Intensity (MJ/km/L)'] = \
        pd.Series(np.zeros(len(output_table))).replace(0,'')
    output_table['Displacement Specific Combined Tractive Road Energy Intensity (MJ/km/L)'][~pd.isnull(engdisp_col)] = \
        pd.Series(output_table['Combined Tractive Road Energy Intensity (MJ/km)'][~pd.isnull(engdisp_col)] \
        /engdisp_col[~pd.isnull(engdisp_col)])
    output_table['Combined Tractive Energy (kWhr)'] \
        = pd.Series(0.55*output_table['FTP Tractive Energy (kWhr)'] + \
                    0.45*output_table['HWFET Tractive Energy (kWhr)'])
    output_table['Combined Fuel Energy Intensity (MJ/km)'] \
        = pd.Series((1/pd.to_numeric(combmpg_col))*fuelhv_col*km2mi*gal2l).replace([math.inf,''], np.nan)
    output_table['Displacement Specific Combined Fuel Energy Intensity (MJ/km/L)'] = \
        pd.Series(np.zeros(len(output_table))).replace(0,'')
    output_table['Displacement Specific Combined Fuel Energy Intensity (MJ/km/L)'][~pd.isnull(engdisp_col)] = \
        pd.Series(output_table['Combined Fuel Energy Intensity (MJ/km)'][(~pd.isnull(engdisp_col)) & (~pd.isnull(output_table['Combined Fuel Energy Intensity (MJ/km)']))] \
        /engdisp_col[(~pd.isnull(engdisp_col)) & (~pd.isnull(output_table['Combined Fuel Energy Intensity (MJ/km)']))])
    output_table['Combined Powertrain Efficiency (%)'] = pd.Series(100 * output_table[ \
        'Combined Tractive Road Energy Intensity (MJ/km)'] / output_table['Combined Fuel Energy Intensity (MJ/km)'])
    output_table = output_table.drop([A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name, combmpg_col.name, \
              fuelhv_col.name], axis=1).replace(0,np.nan)
    return output_table
