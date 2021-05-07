def Drive_Cycle_Differentiation_and_Integration(input_path, drivecycle_file_FTP, drivecycle_file_HWFET):
    import pandas as pd
    import numpy as np
#Read in FTP and HWFET drive cycle
    #print ('Evaluating Drive Cycles')
    from pathlib import Path
    home = str(Path.home())
    dynamometer_drive_schedules_path = home + '/PycharmProjects/EPA_OMEGA_Model/usepa_omega2_preproc/veh_specs/dynamometer_drive_schedules/'

    FTP_ws = pd.read_csv(dynamometer_drive_schedules_path + '\\' + drivecycle_file_FTP, encoding='ISO-8859-1', skiprows=1)
    FTP_time = FTP_ws['seconds']
    FTP_velocity_mph = FTP_ws['mph']
    FTP_length = len(FTP_time)
    FTP_disp_mi = np.zeros(FTP_length)
    FTP_acceleration_mph2 = np.zeros(FTP_length)
    for f in range (0,FTP_length):
        if f == 0 or f == FTP_length-1:
            FTP_acceleration_mph2[f] = 0
        else:
            # FTP_acceleration_mph2[f] = (FTP_velocity_mph[f+1]-FTP_velocity_mph[f-1])/((FTP_time[f+1]-FTP_time[f-1])/3600)
            FTP_acceleration_mph2[f] = (FTP_velocity_mph[f]-FTP_velocity_mph[f-1])/((FTP_time[f]-FTP_time[f-1])/3600)

        if f == 0:
            FTP_disp_mi[f] = 0
        else:
            FTP_disp_mi[f] = 0.5 * (FTP_time[f] - FTP_time[f - 1]) * (FTP_velocity_mph[f] + FTP_velocity_mph[f-1]) / 3600
    FTP_time = pd.Series(FTP_time,name = 'Time (s)')
    FTP_velocity_mph = pd.Series(FTP_velocity_mph,name = 'Velocity (mph)')
    FTP_disp_mi = pd.Series(FTP_disp_mi,name = 'Displacement (mi)')
    FTP_acceleration_mph2 = pd.Series(FTP_acceleration_mph2,name = 'Acceleration (mph2)')
    
    FTP_Array = pd.concat([FTP_time, FTP_velocity_mph, FTP_disp_mi, FTP_acceleration_mph2],axis=1)
#Read in HWFET drive cycle
    HWFET_ws = pd.read_csv(dynamometer_drive_schedules_path + '\\' + drivecycle_file_HWFET, encoding='ISO-8859-1', skiprows=1)
    HWFET_time = HWFET_ws['seconds']
    HWFET_velocity_mph = HWFET_ws['mph']
    HWFET_length = len(HWFET_time)
    HWFET_disp_mi = np.zeros(HWFET_length)
    HWFET_acceleration_mph2 = np.zeros(HWFET_length)
    for f in range (0,HWFET_length):
        if f == 0 or f == HWFET_length-1:
            HWFET_acceleration_mph2[f] = 0 
        else:
            # HWFET_acceleration_mph2[f] = (HWFET_velocity_mph[f+1]-HWFET_velocity_mph[f-1])/((HWFET_time[f+1]-HWFET_time[f-1])/3600)
            HWFET_acceleration_mph2[f] = (HWFET_velocity_mph[f]-HWFET_velocity_mph[f-1])/((HWFET_time[f]-HWFET_time[f-1])/3600)

        if f == 0:
            HWFET_disp_mi[f] = 0
        else:
            HWFET_disp_mi[f] = 0.5 * (HWFET_time[f] - HWFET_time[f - 1]) * (HWFET_velocity_mph[f - 1] + HWFET_velocity_mph[f]) / 3600
    HWFET_time = pd.Series(HWFET_time,name = 'Time (s)')
    HWFET_velocity_mph = pd.Series(HWFET_velocity_mph,name = 'Velocity (mph)')
    HWFET_disp_mi = pd.Series(HWFET_disp_mi,name = 'Displacement (mi)')
    HWFET_acceleration_mph2 = pd.Series(HWFET_acceleration_mph2,name = 'Acceleration (mph2)')
    
    HWFET_Array = pd.concat([HWFET_time, HWFET_velocity_mph, HWFET_disp_mi, HWFET_acceleration_mph2],axis=1)
    return (FTP_Array, HWFET_Array)