import pandas as pd
import datetime
def AllData_Readin(rawdata_input_path, run_input_path, input_filename, output_path, \
                        exceptions_table, bodyid_filename, matched_bodyid_filename, unit_change_table, \
                         year, ftp_drivecycle_filename, hwfet_drivecycle_filename, ratedhp_filename):

    raw_datasheet = pd.read_excel(rawdata_input_path + '\\' +input_filename, converters = {'LineageID':int, 'BodyID':int})
    raw_datasheet = raw_datasheet[(raw_datasheet['Country'] == 'USA')].reset_index(drop=True)\
        .rename(columns = {'Index (AllData)':'ALLDATA_ID'})

    raw_bodyid_file = pd.read_csv(run_input_path+'\\'+bodyid_filename, converters = {'LineageID':int, 'BodyID':int})
    matched_bodyid_file = pd.read_excel(run_input_path+'\\'+matched_bodyid_filename, converters = {'LineageID':int, 'BodyID':int})

    bodyid_file_notnull = raw_bodyid_file[(raw_bodyid_file['StartYear'] <= year) & \
        (raw_bodyid_file['EndYear'] != 'null') & (raw_bodyid_file['EndYear'] != 'xx')]
    bodyid_file_notnull['StartYear'] =  bodyid_file_notnull['StartYear'].astype(int)
    bodyid_file_notnull['EndYear'] = bodyid_file_notnull['EndYear'].astype(int)
    bodyid_file = pd.concat([raw_bodyid_file[(raw_bodyid_file['StartYear'] <= year) &(raw_bodyid_file['EndYear'] == 'null')], \
                            bodyid_file_notnull[bodyid_file_notnull['EndYear'] >= year]]).reset_index(drop=True)
    AllData_SingleBodyID = matched_bodyid_file[(matched_bodyid_file['BodyID'] != -9) & \
                                               (matched_bodyid_file['LineageID'] != -9)].reset_index(drop=True)
    AllData_MultiBodyID = matched_bodyid_file[(matched_bodyid_file['BodyID'] == -9) & \
        (matched_bodyid_file['LineageID'] != -9)].drop('BodyID',axis=1).merge(bodyid_file[['LineageID', 'BodyID']], \
        how='left', on='LineageID').reset_index(drop=True)
    AllData_NoBodyID = matched_bodyid_file[matched_bodyid_file['LineageID'] == -9].reset_index(drop=True)
    AllData_BodyID = pd.concat([AllData_SingleBodyID, AllData_MultiBodyID, AllData_NoBodyID]).sort_values('ALLDATA_ID')
    AllData_Readin_Output = raw_datasheet.merge(AllData_BodyID[['ALLDATA_ID', 'LineageID', 'BodyID']], how='left', on = 'ALLDATA_ID')
    AllData_Readin_Output['BodyID'] = AllData_Readin_Output['BodyID'].astype(float).astype(int)
    AllData_Readin_Output['LineageID'] = AllData_Readin_Output['LineageID'].astype(float).astype(int)
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    AllData_Readin_Output.to_csv(output_path + '\\' 'AllData Readin' + ' ' + date_and_time+'.csv', index=False)