import pandas as pd
import numpy as np
import math

from Unit_Conversion import km2mi, gal2l, s2hr
def Tractive_Energy_Calculation(A,B,C,ETW,Enghp, \
                                drivecycle_dist_mi, drivecycle_time, drivecycle_dt, \
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

def Calculate_Powertrain_Efficiency_SL(ID_col, TEST_PROC_CATEGORY_col, A_col, B_col, C_col, ETW_col, mpg_col, run_input_path, \
                                    drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames, engdisp_col, ratedhp_col, \
                                    fuelhv_col):
    import Drive_Cycle_Differentiation_and_Integration_SL
    from Unit_Conversion import lbf2n, gravity_mps2, mph2mps, mi2km, mph22mps2, hps2kwhr, mj2kwhr, km2mi

    from Unit_Conversion import mph2mps,mph22mps2
    (FTP_array, HWFET_array, US06_Array) = Drive_Cycle_Differentiation_and_Integration_SL.\
        Drive_Cycle_Differentiation_and_Integration_SL(run_input_path, drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames)

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

    if len(US06_Array) > 0:
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

    output_table['Tractive Road Energy Intensity (kWh/100mi)'] = drivecycle_troadwork_kWhp100mi_col
    output_table['Tractive Energy (kWhr)'] = drivecycle_tractive_kWhr_col
    output_table['Load Factor'] = drivecycle_LF_col
    output_table['MPGe (kWh/100mi)'] = 3370.5/mpg_col # 1 gallon gasoline = 33.705 kWh
    fuel_intensity_mjpkm_col = pd.Series((1/pd.to_numeric(mpg_col))*fuelhv_col*km2mi*gal2l).replace([math.inf,''], np.nan)
    output_table['Fuel Energy Intensity (kWh/100mi)'] = fuel_intensity_mjpkm_col * (mj2kwhr/km2mi*100)    # mj/km -> kwh/mi: mj2kwhr/km2mi

    engdisp_col = engdisp_col.replace([0,''],np.nan)
    output_table['Displacement Specific Tractive Road Energy Intensity (kWh/100mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0,'')
    output_table['Displacement Specific Tractive Road Energy Intensity (kWh/100mi/L)'][~pd.isnull(engdisp_col)] = \
        pd.Series(drivecycle_troadwork_mjpkm_col[~pd.isnull(engdisp_col)] * (mj2kwhr/km2mi*100)/engdisp_col[~pd.isnull(engdisp_col)])

    output_table['Displacement Specific Fuel Energy Intensity (kWh/100mi/L)'] = pd.Series(np.zeros(len(output_table))).replace(0, '')
    output_table['Displacement Specific Fuel Energy Intensity (kWh/100mi/L)'] = fuel_intensity_mjpkm_col/engdisp_col * (mj2kwhr / km2mi*100)  # mj/km -> kwh/mi: mj2kwhr/km2mi
    output_table['Powertrain Efficiency (%)'] = 100 * drivecycle_troadwork_mjpkm_col / fuel_intensity_mjpkm_col

    output_table = output_table.drop([A_col.name, B_col.name, C_col.name, ETW_col.name, ratedhp_col.name, mpg_col.name, fuelhv_col.name], axis=1).replace(0,np.nan)
    del drivecycle_troadwork_mjpkm_col, drivecycle_troadwork_kWhp100mi_col, drivecycle_tractive_kWhr_col, drivecycle_LF_col
    return output_table
