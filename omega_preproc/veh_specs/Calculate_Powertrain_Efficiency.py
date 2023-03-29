import pandas as pd
import numpy as np
import math

from Unit_Conversion import km2mi, gal2l, s2hr
def Tractive_Energy_Calculation(A,B,C,ETW,Enghp, drivecycle_dist_mi, drivecycle_time, drivecycle_dt, \
                                drivecycle_velocity_mph, drivecycle_velocity_mps, drivecycle_acceleration_mps2):
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr

    drivecycle_inertia_kwhr = ETW * (lbf2n / gravity_mps2) * (drivecycle_acceleration_mps2 * drivecycle_velocity_mps / 1000) * drivecycle_dt * s2hr
    drivecycle_roadload_kwhr = (A + B * drivecycle_velocity_mph + C * drivecycle_velocity_mph ** 2) * (lbf2n * drivecycle_velocity_mps / 1000) * drivecycle_dt * s2hr
    drivecycle_combined_kwhr = (drivecycle_inertia_kwhr+drivecycle_roadload_kwhr)
    drivecycle_tractive_kWhr = drivecycle_combined_kwhr[drivecycle_combined_kwhr >= 0].sum()
    drivecycle_troadwork_mjpkm = drivecycle_tractive_kWhr * 3.6 / (drivecycle_dist_mi * mi2km)

    if Enghp > 0:
        drivecycle_LF_coeff = 1.0
        drivecycle_LF_num = drivecycle_LF_coeff*drivecycle_tractive_kWhr
        drivecycle_LF_den = Enghp * (drivecycle_LF_coeff*drivecycle_time) * hps2kwhr
        drivecycle_LF = drivecycle_LF_num/drivecycle_LF_den
    else:
        drivecycle_LF = 0
    return (drivecycle_troadwork_mjpkm, drivecycle_LF, drivecycle_tractive_kWhr)

def Calculate_Powertrain_Efficiency(ID_col, TEST_PROC_CATEGORY_col, A_col, B_col, C_col, ETW_col, mpg_col, city_mpg_col, hwy_mpg_col, comb_mpg_col, run_input_path, \
                                    drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames, engdisp_col, ratedhp_col, fuelhv_col):
    import Drive_Cycle_Differentiation_and_Integration
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr, mj2kwhr, km2mi

    from Unit_Conversion import mph2mps,mph22mps2
    (FTP_array, HWFET_array, US06_array, Custom_Array) = Drive_Cycle_Differentiation_and_Integration.\
        Drive_Cycle_Differentiation_and_Integration(run_input_path, drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames)

    if len(FTP_array) > 0:
        FTP_dist_mi = FTP_array['Displacement (mi)'].sum()
        FTP_time = FTP_array['Time (s)'].max()
        FTP_dt = FTP_array['Time (s)'][1] - FTP_array['Time (s)'][0]
        FTP_velocity_mph = FTP_array['Velocity (mph)']
        FTP_velocity_mps = FTP_velocity_mph * mph2mps
        FTP_acceleration_mph2 = FTP_array['Acceleration (mph2)']
        FTP_acceleration_mps2 = FTP_acceleration_mph2 * mph22mps2

    if len(HWFET_array) > 0:
        HWFET_dist_mi = HWFET_array['Displacement (mi)'].sum()
        HWFET_time = HWFET_array['Time (s)'].max()
        HWFET_dt = HWFET_array['Time (s)'][1] - HWFET_array['Time (s)'][0]
        HWFET_velocity_mph = HWFET_array['Velocity (mph)']
        HWFET_velocity_mps = HWFET_velocity_mph * mph2mps
        HWFET_acceleration_mph2 = HWFET_array['Acceleration (mph2)']
        HWFET_acceleration_mps2 = HWFET_acceleration_mph2 * mph22mps2

    if len(US06_array) > 0:
        US06_dist_mi = US06_array['Displacement (mi)'].sum()
        US06_time = US06_array['Time (s)'].max()
        US06_dt = US06_array['Time (s)'][1] - US06_array['Time (s)'][0]
        US06_velocity_mph = US06_array['Velocity (mph)']
        US06_velocity_mps = US06_velocity_mph * mph2mps
        US06_acceleration_mph2 = US06_array['Acceleration (mph2)']
        US06_acceleration_mps2 = US06_acceleration_mph2 * mph22mps2

    output_table = pd.concat([ID_col, TEST_PROC_CATEGORY_col, A_col, B_col, C_col, ETW_col, ratedhp_col, mpg_col, fuelhv_col], axis=1)
    # unique_tractive_array = input_array[[ID_col.name, TEST_PROC_CATEGORY_col.name, A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name]] \
    #     .groupby([A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name]).first().reset_index().drop(ID_col.name,axis=1)
    TEST_PROC_CATEGORY_col_new = output_table[TEST_PROC_CATEGORY_col.name]
    A_col_new = output_table[A_col.name]
    B_col_new = output_table[B_col.name]
    C_col_new = output_table[C_col.name]
    ETW_col_new = output_table[ETW_col.name]
    ratedhp_col_new = output_table[ratedhp_col.name]

    drivecycle_troadwork_mjpkm_col = pd.Series(np.zeros(len(output_table)))
    drivecycle_troadwork_kWhp100mi_col = pd.Series(np.zeros(len(output_table)))
    drivecycle_tractive_kWhr_col = pd.Series(np.zeros(len(output_table)))
    drivecycle_LF_col = pd.Series(np.zeros(len(output_table)))

    for data_count in range (len(output_table)):
        TEST_PROC_CATEGORY = TEST_PROC_CATEGORY_col_new[data_count]
        if TEST_PROC_CATEGORY == 'FTP':
            drivecycle_dist_mi = FTP_dist_mi
            drivecycle_time = FTP_time
            drivecycle_dt = FTP_dt
            drivecycle_velocity_mph = FTP_velocity_mph
            drivecycle_velocity_mps = FTP_velocity_mps
            drivecycle_acceleration_mps2 = FTP_acceleration_mps2
        elif TEST_PROC_CATEGORY == 'HWY':
            drivecycle_dist_mi = HWFET_dist_mi
            drivecycle_time = HWFET_time
            drivecycle_dt = HWFET_dt
            drivecycle_velocity_mph = HWFET_velocity_mph
            drivecycle_velocity_mps = HWFET_velocity_mps
            drivecycle_acceleration_mps2 = HWFET_acceleration_mps2
        elif TEST_PROC_CATEGORY == 'US06':
            drivecycle_dist_mi = US06_dist_mi
            drivecycle_time = US06_time
            drivecycle_dt = US06_dt
            drivecycle_velocity_mph = US06_velocity_mph
            drivecycle_velocity_mps = US06_velocity_mps
            drivecycle_acceleration_mps2 = US06_acceleration_mps2
        elif TEST_PROC_CATEGORY == 'Custom':
            drivecycle_dist_mi = Custom_dist_mi
            drivecycle_time = Custom_time
            drivecycle_dt = Custom_dt
            drivecycle_velocity_mph = Custom_velocity_mph
            drivecycle_velocity_mps = Custom_velocity_mps
            drivecycle_acceleration_mps2 = Custom_acceleration_mps2
        else:
            continue

        A = A_col_new[data_count]
        B = B_col_new[data_count]
        C = C_col_new[data_count]
        ETW = ETW_col_new[data_count]
        ratedhp = ratedhp_col_new[data_count]

        (drivecycle_troadwork_mjpkm, drivecycle_LF, drivecycle_tractive_kWhr) = Tractive_Energy_Calculation(A, B, C, ETW, ratedhp, drivecycle_dist_mi, drivecycle_time, drivecycle_dt, \
            drivecycle_velocity_mph, drivecycle_velocity_mps, drivecycle_acceleration_mps2)

        drivecycle_troadwork_mjpkm_col[data_count] = drivecycle_troadwork_mjpkm
        drivecycle_troadwork_kWhp100mi_col[data_count] = drivecycle_troadwork_mjpkm * (mj2kwhr/km2mi*100)
        drivecycle_tractive_kWhr_col[data_count] = drivecycle_tractive_kWhr
        drivecycle_LF_col[data_count] = drivecycle_LF

    output_table['Tractive Road Energy Intensity (Wh/mi)'] = 10 * drivecycle_troadwork_kWhp100mi_col
    output_table['Tractive Energy (kWhr)'] = drivecycle_tractive_kWhr_col
    output_table['Load Factor (%)'] = drivecycle_LF_col * 100
    output_table['MPGe (kWh/100mi)'] = 3370.5/mpg_col # 1 gallon gasoline = 33.705 kWh
    fuel_intensity_mjpkm_col = pd.Series((1/pd.to_numeric(mpg_col))*fuelhv_col*km2mi*gal2l).replace([math.inf,''], np.nan)
    comb_fuel_intensity_mjpkm_col = pd.Series((1/pd.to_numeric(comb_mpg_col))*fuelhv_col*km2mi*gal2l).replace([math.inf,''], np.nan)
    output_table['Fuel Energy Intensity (Wh/mi)'] = fuel_intensity_mjpkm_col * 1000 * (mj2kwhr/km2mi)    # mj/km -> kwh/mi: mj2kwhr/km2mi

    engdisp_col = engdisp_col.replace([0,''],np.nan)
    output_table['Displacement Specific Tractive Road Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0,'')
    output_table.loc[engdisp_col > 0, 'Displacement Specific Tractive Road Energy Intensity (Wh/mi/L)'] = drivecycle_troadwork_mjpkm_col * 1000 * (mj2kwhr/km2mi)/engdisp_col

    output_table['Displacement Specific Fuel Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table['Displacement Specific Fuel Energy Intensity (Wh/mi/L)'] = fuel_intensity_mjpkm_col/engdisp_col * 1000 * (mj2kwhr / km2mi)  # mj/km -> kwh/mi: mj2kwhr/km2mi
    output_table['Cycle Powertrain Efficiency (%)'] = 100 * drivecycle_troadwork_mjpkm_col / fuel_intensity_mjpkm_col
    output_table1 = comb_Calculate_Powertrain_Efficiency(ID_col, A_col, B_col, C_col, ETW_col, mpg_col, city_mpg_col, hwy_mpg_col, comb_mpg_col, run_input_path, \
                                         FTP_array, HWFET_array, US06_array, engdisp_col, ratedhp_col, fuelhv_col, output_table)
    output_table1 = output_table1.drop([A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name, mpg_col.name, fuelhv_col.name], axis=1).replace(0,np.nan)
    del drivecycle_troadwork_mjpkm_col, drivecycle_troadwork_kWhp100mi_col, drivecycle_tractive_kWhr_col, drivecycle_LF_col
    return output_table1

def comb_Tractive_Energy_Calculation(A, B, C, ETW, Enghp, FTP_array, HWFET_array, US06_array):
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr, mj2kwhr, km2mi

    FTP_dist_mi = FTP_array['Displacement (mi)'].sum()
    FTP_time = FTP_array['Time (s)'].max()
    FTP_dt = FTP_array['Time (s)'][1] - FTP_array['Time (s)'][0]
    FTP_velocity_mph = FTP_array['Velocity (mph)']
    FTP_velocity_mps = FTP_velocity_mph * mph2mps
    FTP_acceleration_mph2 = FTP_array['Acceleration (mph2)']
    FTP_acceleration_mps2 = FTP_acceleration_mph2 * mph22mps2

    HWFET_dist_mi = HWFET_array['Displacement (mi)'].sum()
    HWFET_time = HWFET_array['Time (s)'].max()
    HWFET_dt = HWFET_array['Time (s)'][1] - HWFET_array['Time (s)'][0]
    HWFET_velocity_mph = HWFET_array['Velocity (mph)']
    HWFET_velocity_mps = HWFET_velocity_mph * mph2mps
    HWFET_acceleration_mph2 = HWFET_array['Acceleration (mph2)']
    HWFET_acceleration_mps2 = HWFET_acceleration_mph2 * mph22mps2

    US06_dist_mi = US06_array['Displacement (mi)'].sum()
    US06_time = US06_array['Time (s)'].max()
    US06_dt = US06_array['Time (s)'][1] - US06_array['Time (s)'][0]
    US06_velocity_mph = US06_array['Velocity (mph)']
    US06_velocity_mps = US06_velocity_mph * mph2mps
    US06_acceleration_mph2 = US06_array['Acceleration (mph2)']
    US06_acceleration_mps2 = US06_acceleration_mph2 * mph22mps2

    FTP_inertia_kwhr = ETW * (lbf2n / gravity_mps2) * (FTP_acceleration_mps2 * FTP_velocity_mps / 1000) * FTP_dt * s2hr
    FTP_roadload_kwhr = (A + B * FTP_velocity_mph + C * FTP_velocity_mph ** 2) * (lbf2n * FTP_velocity_mps / 1000) * FTP_dt * s2hr
    FTP_combined_kwhr = (FTP_inertia_kwhr + FTP_roadload_kwhr)
    FTP_tractive_kWhr = FTP_combined_kwhr[FTP_combined_kwhr >= 0].sum()
    FTP_troadwork_mjpkm = FTP_tractive_kWhr * 3.6 / (FTP_dist_mi * mi2km)

    HWFET_inertia_kwhr = ETW * (lbf2n / gravity_mps2) * (HWFET_acceleration_mps2 * HWFET_velocity_mps / 1000) * HWFET_dt * s2hr
    HWFET_roadload_kwhr = (A + B * HWFET_velocity_mph + C * HWFET_velocity_mph ** 2) * (lbf2n * HWFET_velocity_mps / 1000) * HWFET_dt * s2hr
    HWFET_combined_kwhr = (HWFET_inertia_kwhr + HWFET_roadload_kwhr)
    HWFET_tractive_kWhr = HWFET_combined_kwhr[HWFET_combined_kwhr >= 0].sum()
    HWFET_troadwork_mjpkm = HWFET_tractive_kWhr * 3.6 / (HWFET_dist_mi * mi2km)

    US06_inertia_kwhr = ETW * (lbf2n / gravity_mps2) * (US06_acceleration_mps2 * US06_velocity_mps / 1000) * US06_dt * s2hr
    US06_roadload_kwhr = (A + B * US06_velocity_mph + C * US06_velocity_mph ** 2) * (lbf2n * US06_velocity_mps / 1000) * US06_dt * s2hr
    US06_combined_kwhr = (US06_inertia_kwhr + US06_roadload_kwhr)
    US06_tractive_kWhr = US06_combined_kwhr[US06_combined_kwhr >= 0].sum()
    US06_troadwork_mjpkm = US06_tractive_kWhr * 3.6 / (US06_dist_mi * mi2km)

    # FTP_forceavg_speed_num = (A * FTP_velocity_mph ** 2 + B * FTP_velocity_mph ** 3 + C * FTP_velocity_mph ** 4)
    # FTP_energyavg_speed_num = (A * FTP_velocity_mph + B * FTP_velocity_mph ** 2 + C * FTP_velocity_mph ** 3)
    # FTP_forceavg_speed_den = FTP_energyavg_speed_num
    # FTP_energyavg_speed_den = (A + B * FTP_velocity_mph + C * FTP_velocity_mph ** 2)
    #
    # HWFET_forceavg_speed_num = (A * HWFET_velocity_mph ** 2 + B * HWFET_velocity_mph ** 3 + C * HWFET_velocity_mph ** 4)
    # HWFET_energyavg_speed_num = (A * HWFET_velocity_mph + B * HWFET_velocity_mph ** 2 + C * HWFET_velocity_mph ** 3)
    # HWFET_forceavg_speed_den = HWFET_energyavg_speed_num
    # HWFET_energyavg_speed_den = (A + B * HWFET_velocity_mph + C * HWFET_velocity_mph ** 2)

    # try:
    #     FTP_forceavg_speed_mph = FTP_forceavg_speed_num.sum() / FTP_forceavg_speed_den.sum()
    #     HWFET_forceavg_speed_mph = HWFET_forceavg_speed_num.sum() / HWFET_forceavg_speed_den.sum()
    #     comb_forceavg_speed_mph = (0.55 * FTP_forceavg_speed_num.sum() + 0.45 * HWFET_forceavg_speed_num.sum()) / \
    #                               (0.55 * FTP_forceavg_speed_den.sum() + 0.45 * HWFET_forceavg_speed_den.sum())
    #
    #     FTP_energyavg_speed_mph = FTP_energyavg_speed_num.sum() / FTP_energyavg_speed_den.sum()
    #     HWFET_energyavg_speed_mph = HWFET_energyavg_speed_num.sum() / HWFET_energyavg_speed_den.sum()
    #     comb_energyavg_speed_mph = (0.55 * FTP_energyavg_speed_num.sum() + 0.45 * HWFET_energyavg_speed_num.sum()) / \
    #                                (0.55 * FTP_energyavg_speed_den.sum() + 0.45 * HWFET_energyavg_speed_den.sum())
    # except ZeroDivisionError:
    #     FTP_forceavg_speed_mph = 'inconclusive'
    #     HWFET_forceavg_speed_mph = 'inconclusive'
    #     comb_forceavg_speed_mph = 'inconclusive'
    #     FTP_energyavg_speed_mph = 'inconclusive'
    #     HWFET_energyavg_speed_mph = 'inconclusive'
    #     comb_energyavg_speed_mph = 'inconclusive'

    if Enghp > 0:
        Comb_LF_num = 0.55 * FTP_tractive_kWhr + 0.45 * HWFET_tractive_kWhr
        Comb_LF_den = Enghp * (0.55 * FTP_time + 0.45 * HWFET_time) * hps2kwhr
        Comb_LF = 100 * Comb_LF_num / Comb_LF_den
    else:
        Comb_LF = 0
    return (FTP_troadwork_mjpkm, HWFET_troadwork_mjpkm, US06_troadwork_mjpkm, Comb_LF, FTP_tractive_kWhr, HWFET_tractive_kWhr, US06_tractive_kWhr)

def comb_Calculate_Powertrain_Efficiency(ID_col, A_col, B_col, C_col, ETW_col, mpg_col, city_mpg_col, hwy_mpg_col, combmpg_col, run_input_path, \
                                         FTP_array, HWFET_array, US06_array, engdisp_col, ratedhp_col, fuelhv_col, output_table):
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr, mj2kwhr, km2mi

    # FTP_dist_mi = FTP_array['Displacement (mi)'].sum()
    # FTP_time = FTP_array['Time (s)'].max()
    # FTP_dt = FTP_array['Time (s)'][1] - FTP_array['Time (s)'][0]
    # FTP_velocity_mph = FTP_array['Velocity (mph)']
    # FTP_velocity_mps = FTP_velocity_mph * mph2mps
    # FTP_acceleration_mph2 = FTP_array['Acceleration (mph2)']
    # FTP_acceleration_mps2 = FTP_acceleration_mph2 * mph22mps2
    #
    # HWFET_dist_mi = HWFET_array['Displacement (mi)'].sum()
    # HWFET_time = HWFET_array['Time (s)'].max()
    # HWFET_dt = HWFET_array['Time (s)'][1] - HWFET_array['Time (s)'][0]
    # HWFET_velocity_mph = HWFET_array['Velocity (mph)']
    # HWFET_velocity_mps = HWFET_velocity_mph * mph2mps
    # HWFET_acceleration_mph2 = HWFET_array['Acceleration (mph2)']
    # HWFET_acceleration_mps2 = HWFET_acceleration_mph2 * mph22mps2

    input_array = pd.concat([ID_col, A_col, B_col, C_col, ETW_col, ratedhp_col, mpg_col, combmpg_col, fuelhv_col], axis=1)
    A_col_new = input_array[A_col.name]
    B_col_new = input_array[B_col.name]
    C_col_new = input_array[C_col.name]
    ETW_col_new = input_array[ETW_col.name]
    mpg_col_new = input_array[mpg_col.name]
    ratedhp_col_new = input_array[ratedhp_col.name]

    Comb_LF_col = pd.Series(np.zeros(len(input_array)), name='Combined Load Factor (%)')
    FTP_troadwork_mjpkm_col = pd.Series(np.zeros(len(input_array)), name='FTP Tractive Road Energy Intensity (MJ/km)')
    FTP_tractive_kWhr_col = pd.Series(np.zeros(len(input_array)), name='FTP Tractive Energy (kWhr)')
    HWFET_troadwork_mjpkm_col = pd.Series(np.zeros(len(input_array)), name='HWFET Tractive Road Energy Intensity (MJ/km)')
    HWFET_tractive_kWhr_col = pd.Series(np.zeros(len(input_array)), name='HWFET Tractive Energy (kWhr)')
    US06_troadwork_mjpkm_col = pd.Series(np.zeros(len(input_array)), name='US06 Tractive Road Energy Intensity (MJ/km)')
    US06_tractive_kWhr_col = pd.Series(np.zeros(len(input_array)), name='US06 Tractive Energy (kWhr)')
    # FTP_forceavg_velocity_mph_col = pd.Series(np.zeros(len(input_array)), name='FTP ForceAvg Velocity (mph)')
    # HWFET_forceavg_velocity_mph_col = pd.Series(np.zeros(len(input_array)), name='HWFET ForceAvg Velocity (mph)')
    # comb_forceavg_velocity_mph_col = pd.Series(np.zeros(len(input_array)), name='Combined ForceAvg Velocity (mph)')
    # FTP_energyavg_velocity_mph_col = pd.Series(np.zeros(len(input_array)), name='FTP EnergyAvg Velocity (mph)')
    # HWFET_energyavg_velocity_mph_col = pd.Series(np.zeros(len(input_array)), name='HWFET EnergyAvg Velocity (mph)')
    # comb_energyavg_velocity_mph_col = pd.Series(np.zeros(len(input_array)), name='Combined EnergyAvg Velocity (mph)')
    mpg_col_new.replace(['nan', np.nan, ''], 0, inplace=True)
    for data_count in range(0, len(input_array)):
        A = A_col_new[data_count]
        B = B_col_new[data_count]
        C = C_col_new[data_count]
        ETW = ETW_col_new[data_count]
        ratedhp = ratedhp_col_new[data_count]
        if mpg_col_new[data_count] <= 0: continue
        # if data_count == 19161: print(mpg_col_new[data_count], combmpg_col[data_count])

        [FTP_troadwork_mjpkm, HWFET_troadwork_mjpkm, US06_troadwork_mjpkm, Comb_LF, FTP_tractive_kWhr, HWFET_tractive_kWhr, US06_tractive_kWhr] = \
            comb_Tractive_Energy_Calculation(A, B, C, ETW, ratedhp, FTP_array, HWFET_array, US06_array)

        FTP_troadwork_mjpkm_col[data_count] = FTP_troadwork_mjpkm
        HWFET_troadwork_mjpkm_col[data_count] = HWFET_troadwork_mjpkm
        Comb_LF_col[data_count] = Comb_LF
        FTP_tractive_kWhr_col[data_count] = FTP_tractive_kWhr
        HWFET_tractive_kWhr_col[data_count] = HWFET_tractive_kWhr
        US06_troadwork_mjpkm_col[data_count] = US06_troadwork_mjpkm
        US06_tractive_kWhr_col[data_count] = US06_tractive_kWhr

    engdisp_col = engdisp_col.replace([0, ''], np.nan)
    comb_troadwork_mjpkm_col = pd.Series(0.55 * FTP_troadwork_mjpkm_col + 0.45 * HWFET_troadwork_mjpkm_col)
    city_fuel_energy_mjpkm_col = pd.Series((1 / pd.to_numeric(city_mpg_col)) * fuelhv_col * km2mi * gal2l).replace([math.inf, ''], np.nan)
    hwy_fuel_energy_mjpkm_col = pd.Series((1 / pd.to_numeric(hwy_mpg_col)) * fuelhv_col * km2mi * gal2l).replace([math.inf, ''], np.nan)
    us06_fuel_energy_mjpkm_col = pd.Series((1 / pd.to_numeric(mpg_col)) * fuelhv_col * km2mi * gal2l).replace([math.inf, ''], np.nan)
    comb_fuel_energy_mjpkm_col = pd.Series((1 / pd.to_numeric(combmpg_col)) * fuelhv_col * km2mi * gal2l).replace([math.inf, ''], np.nan)

    output_table['City Tractive Road Energy Intensity (Wh/mi)'] = FTP_troadwork_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific City Tractive Road Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific City Tractive Road Energy Intensity (Wh/mi/L)'] = FTP_troadwork_mjpkm_col/engdisp_col * (mj2kwhr/km2mi) * 1000
    output_table['City Tractive Energy (kWhr)'] = FTP_tractive_kWhr_col
    output_table['City Fuel Energy Intensity (Wh/mi)'] = city_fuel_energy_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific City Fuel Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific City Fuel Energy Intensity (Wh/mi/L)'] = city_fuel_energy_mjpkm_col/engdisp_col * (mj2kwhr / km2mi)*1000
    output_table['City Powertrain Efficiency (%)'] = 100 * FTP_troadwork_mjpkm_col / city_fuel_energy_mjpkm_col

    output_table['Hwy Tractive Road Energy Intensity (Wh/mi)'] = HWFET_troadwork_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific Hwy Tractive Road Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific Hwy Tractive Road Energy Intensity (Wh/mi/L)'] = HWFET_troadwork_mjpkm_col/engdisp_col * (mj2kwhr/km2mi) * 1000
    output_table['Hwy Tractive Energy (kWhr)'] = HWFET_tractive_kWhr_col
    output_table['Hwy Fuel Energy Intensity (Wh/mi)'] = hwy_fuel_energy_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific Hwy Fuel Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific Hwy Fuel Energy Intensity (Wh/mi/L)'] = hwy_fuel_energy_mjpkm_col/engdisp_col * (mj2kwhr / km2mi)*1000
    output_table['Hwy Powertrain Efficiency (%)'] = 100 * HWFET_troadwork_mjpkm_col / hwy_fuel_energy_mjpkm_col

    output_table['Combined MPGe (kWh/100mi)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table['Combined MPGe (kWh/100mi)'] = 3370.5/combmpg_col # 1 gallon gasoline = 33.705 kWh
    output_table['Combined Tractive Road Energy Intensity (Wh/mi)'] = comb_troadwork_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific Combined Tractive Road Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific Combined Tractive Road Energy Intensity (Wh/mi/L)'] = comb_troadwork_mjpkm_col/engdisp_col * (mj2kwhr/km2mi) * 1000
    output_table['Combined Tractive Energy (kWhr)'] = (0.55 * FTP_tractive_kWhr_col + 0.45 * HWFET_tractive_kWhr_col)
    output_table['Combined Fuel Energy Intensity (Wh/mi)'] = comb_fuel_energy_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific Combined Fuel Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific Combined Fuel Energy Intensity (Wh/mi/L)'] = comb_fuel_energy_mjpkm_col/engdisp_col * (mj2kwhr / km2mi)*1000
    output_table['Powertrain Efficiency (%)'] = 100 * comb_troadwork_mjpkm_col / comb_fuel_energy_mjpkm_col

    output_table['US06 Tractive Road Energy Intensity (Wh/mi)'] = US06_troadwork_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific US06 Tractive Road Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific US06 Tractive Road Energy Intensity (Wh/mi/L)'] = US06_troadwork_mjpkm_col/engdisp_col * (mj2kwhr/km2mi) * 1000
    output_table['US06 Tractive Energy (kWhr)'] = US06_tractive_kWhr_col
    output_table['US06 Fuel Energy Intensity (Wh/mi)'] = us06_fuel_energy_mjpkm_col * (mj2kwhr/km2mi)*1000
    output_table['Displacement Specific US06 Fuel Energy Intensity (Wh/mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table.loc[engdisp_col > 0, 'Displacement Specific US06 Fuel Energy Intensity (Wh/mi/L)'] = us06_fuel_energy_mjpkm_col/engdisp_col * (mj2kwhr / km2mi)*1000
    output_table['US06 Powertrain Efficiency (%)'] = 100 * US06_troadwork_mjpkm_col / us06_fuel_energy_mjpkm_col

    return output_table
