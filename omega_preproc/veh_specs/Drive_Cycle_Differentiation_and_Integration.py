def Drive_Cycle_Differentiation_and_Integration(input_path, drivecycle_filenames, drivecycle_input_filenames, drivecycle_output_filenames):
    import pandas as pd
    import numpy as np
    from pathlib import Path
    home = str(Path.home())
    dynamometer_drive_schedules_path = home + '/PycharmProjects/EPA_OMEGA_Model/omega_preproc/veh_specs/dynamometer_drive_schedules/'

#Read in FTP and HWFET drive cycle
    #print ('Evaluating Drive Cycles')
    drivecycle_file_FTP = ''
    drivecycle_file_HWFET = ''
    drivecycle_file_US06 = ''
    drivecycle_file_Custom = ''
    for i in range (len(drivecycle_filenames)):
        drivecycle_filename = drivecycle_filenames[i]
        if 'ftp' in drivecycle_filename: drivecycle_file_FTP = drivecycle_filename
        if 'hwy' in drivecycle_filename: drivecycle_file_HWFET = drivecycle_filename
        if 'us06' in drivecycle_filename: drivecycle_file_US06 = drivecycle_filename
        if ('custom' in drivecycle_filename) or ('Custom' in drivecycle_filename) or ('user-defined' in drivecycle_filename):
            drivecycle_file_Custom = drivecycle_filename

    if drivecycle_file_FTP == '': drivecycle_file_FTP = 'ftpcol10hz.csv'
    if drivecycle_file_HWFET == '': drivecycle_file_HWFET = 'hwycol10hz.csv'
    if drivecycle_file_US06 == '': drivecycle_file_US06 = 'us06col.csv'
    if len(drivecycle_file_FTP) > 0:
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
    else:
        FTP_Array = []

    #Read in HWFET drive cycle
    if len(drivecycle_file_HWFET) > 0:
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
    else:
        HWFET_Array = []

    if len(drivecycle_file_US06) > 0:
        US06_ws = pd.read_csv(dynamometer_drive_schedules_path + '\\' + drivecycle_file_US06, encoding='ISO-8859-1', skiprows=1)
        US06_time = US06_ws['seconds']
        US06_velocity_mph = US06_ws['mph']
        US06_length = len(US06_time)
        US06_disp_mi = np.zeros(US06_length)
        US06_acceleration_mph2 = np.zeros(US06_length)
        for f in range(0, US06_length):
            if f == 0 or f == US06_length - 1:
                US06_acceleration_mph2[f] = 0
            else:
                # US06_acceleration_mph2[f] = (US06_velocity_mph[f+1]-US06_velocity_mph[f-1])/((US06_time[f+1]-US06_time[f-1])/3600)
                US06_acceleration_mph2[f] = (US06_velocity_mph[f] - US06_velocity_mph[f - 1]) / ((US06_time[f] - US06_time[f - 1]) / 3600)
            if f == 0:
                US06_disp_mi[f] = 0
            else:
                US06_disp_mi[f] = 0.5 * (US06_time[f] - US06_time[f - 1]) * (
                            US06_velocity_mph[f - 1] + US06_velocity_mph[f]) / 3600
        US06_time = pd.Series(US06_time, name='Time (s)')
        US06_velocity_mph = pd.Series(US06_velocity_mph, name='Velocity (mph)')
        US06_disp_mi = pd.Series(US06_disp_mi, name='Displacement (mi)')
        US06_acceleration_mph2 = pd.Series(US06_acceleration_mph2, name='Acceleration (mph2)')

        US06_Array = pd.concat([US06_time, US06_velocity_mph, US06_disp_mi, US06_acceleration_mph2], axis=1)
    else:
        US06_Array = []

    if len(drivecycle_file_Custom) > 0:
        Custom_ws = pd.read_csv(dynamometer_drive_schedules_path + '\\' + drivecycle_file_Custom, encoding='ISO-8859-1', skiprows=1)
        Custom_time = Custom_ws['seconds']
        Custom_velocity_mph = Custom_ws['mph']
        Custom_length = len(Custom_time)
        Custom_disp_mi = np.zeros(Custom_length)
        Custom_acceleration_mph2 = np.zeros(Custom_length)
        for f in range(0, Custom_length):
            if f == 0 or f == Custom_length - 1:
                Custom_acceleration_mph2[f] = 0
            else:
                Custom_acceleration_mph2[f] = (Custom_velocity_mph[f] - Custom_velocity_mph[f - 1]) / ((Custom_time[f] - Custom_time[f - 1]) / 3600)
            if f == 0:
                Custom_disp_mi[f] = 0
            else:
                Custom_disp_mi[f] = 0.5 * (Custom_time[f] - Custom_time[f - 1]) * (
                            Custom_velocity_mph[f - 1] + Custom_velocity_mph[f]) / 3600
        Custom_time = pd.Series(Custom_time, name='Time (s)')
        Custom_velocity_mph = pd.Series(Custom_velocity_mph, name='Velocity (mph)')
        Custom_disp_mi = pd.Series(Custom_disp_mi, name='Displacement (mi)')
        Custom_acceleration_mph2 = pd.Series(Custom_acceleration_mph2, name='Acceleration (mph2)')

        Custom_Array = pd.concat([Custom_time, Custom_velocity_mph, Custom_disp_mi, Custom_acceleration_mph2], axis=1)
    else:
        Custom_Array = []

    return (FTP_Array, HWFET_Array, US06_Array, Custom_Array)