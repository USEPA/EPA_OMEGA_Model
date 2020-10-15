import pandas as pd
import numpy as np
import datetime
def Edmunds_Readin(rawdata_input_path, run_input_path, input_filename, output_path, exceptions_table, \
                   bodyid_filename, matched_bodyid_filename, unit_table, year, \
                   ftp_drivecycle_filename, hwfet_drivecycle_filename, ratedhp_filename, lineageid_filename):
    raw_Edmunds_data = pd.read_csv(rawdata_input_path+'\\'+input_filename, encoding="ISO-8859-1")
    Edmunds_Data = raw_Edmunds_data
    Edmunds_Data['Model'] = Edmunds_Data['Model'].astype(str)
    Edmunds_Data['ELECTRIC POWER STEERING'] = Edmunds_Data['ELECTRIC POWER STEERING'].replace([False,str(False).upper()], 'NOT EPS')\
        .replace([True,str(True).upper()], 'EPS')
    if type(exceptions_table) != str:
        for error_check_count in range(0, len(exceptions_table)):
            Edmunds_Data.loc[(Edmunds_Data['Model'] == exceptions_table['Model'][error_check_count]) & \
                (Edmunds_Data['Trims'] == exceptions_table['Trims'][error_check_count]), exceptions_table['Column Name'][error_check_count]] = \
            exceptions_table['New Value'][error_check_count]

    body_id_table_readin = pd.read_csv(run_input_path + '\\' + bodyid_filename, \
                                         converters={'LineageID': int, 'BodyID': int})
    body_id_table_readin = body_id_table_readin[body_id_table_readin['EndYear'] != 'xx'].reset_index(drop=True)
    body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['EndYear'])) \
                                             & (body_id_table_readin['StartYear'] <= year)].reset_index(drop=True)
    body_id_int_not_null_endyear = body_id_table_int[
        ~body_id_table_int['EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
    body_id_int_not_null_endyear['EndYear'] = body_id_int_not_null_endyear['EndYear'].astype(float)
    body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['EndYear'] >= year], \
                               body_id_table_int[
                                   body_id_table_int['EndYear'].astype(str).str.contains('null')]]).reset_index(
        drop=True)
    body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
    body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)

    Edmunds_matched_bodyid_file_raw = pd.read_csv(rawdata_input_path + '\\' + matched_bodyid_filename, \
                                         converters={'LineageID': int, 'BodyID': int, 'Model':str})
    Edmunds_matched_bodyid_file_notnone = Edmunds_matched_bodyid_file_raw[Edmunds_matched_bodyid_file_raw['LineageID'] != -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_none = Edmunds_matched_bodyid_file_raw[
        Edmunds_matched_bodyid_file_raw['LineageID'] == -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_single = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] != -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_many = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] == -9]\
        .drop('BodyID',axis=1).merge(body_id_table[['LineageID', 'BodyID']], how='left', on = 'LineageID').reset_index(drop=True)
    Edmunds_matched_bodyid = pd.concat([Edmunds_matched_bodyid_file_single, Edmunds_matched_bodyid_file_many, Edmunds_matched_bodyid_file_none]).reset_index(drop=True)
    Edmunds_data_cleaned = Edmunds_Data.merge(Edmunds_matched_bodyid[['Model', 'Trims', 'LineageID', 'BodyID']], \
        how='left', on = ['Model', 'Trims']).reset_index(drop=True)
    Edmunds_data_cleaned['BodyID'] = Edmunds_data_cleaned['BodyID'].astype(float).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].astype(float).astype(int)

    Edmunds_data_cleaned['CYLINDERS'] = Edmunds_data_cleaned['CYLINDERS'].str.replace('inline ', 'I').str.replace('flat ', 'H')\
        .replace([np.nan, str(np.nan), 'FALSE', 'false', 'False'], 'ELE')
    matching_cyl_layout = pd.Series(Edmunds_data_cleaned['CYLINDERS'].astype(str).str[0], name = 'Cylinder Layout Category').replace('E','ELE').astype(str)
    matching_cyl_num = pd.Series(Edmunds_data_cleaned['CYLINDERS'].astype(str).str[1:], name='Number of Cylinders Category').replace(['LE', 'ALSE', str(np.nan)[1:]], 0).astype(float).astype(int)
    matching_eng_disp = pd.Series(Edmunds_data_cleaned['BASE ENGINE SIZE'].str.replace(' L','').str.strip(), name='Engine Displacement Category')\
        .replace(['',np.nan,str(np.nan), 'FALSE', 'False'],0).astype(float).round(1)
    matching_drvtrn_layout = pd.Series(Edmunds_data_cleaned['DRIVE TYPE'], name = 'Drivetrain Layout Category')
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('front')] = '2WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('four')] = '4WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('all')] = '4WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('rear')] = '2WD'
    matching_trns_numgears = pd.Series(Edmunds_data_cleaned['TRANSMISSION'].str[0], name='Number of Transmission Gears Category').replace('c',1).astype(int)
    matching_trns_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Transmission Type Category').replace(0,'A')
    matching_trns_category[matching_trns_numgears == 1] = '1ST'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('automated manual')] = 'AM'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('automatic')] = 'A'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('speed manual')] = 'M'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('continuous')] = '1ST'

    matching_boost_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Boost Type Category').replace(0,'N')
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('Turbo')] = 'TC'
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('Twincharger')] = 'TS'
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('S/C')] = 'SC'
    matching_boost_category[matching_cyl_layout == 'ELE'] = 'ELE'
    matching_mfr_category = pd.Series(Edmunds_data_cleaned['Make'], name='Make Category').astype(str)\
        .replace('ROLLS ROYCE', 'ROLLS-ROYCE')

    matching_fuel_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Fuel Type Category').replace(0,'G')
    Edmunds_data_cleaned['FUEL TYPE'][matching_cyl_layout == 'ELE'] = 'electric fuel'
    Edmunds_data_cleaned['FUEL TYPE'][pd.isnull(Edmunds_data_cleaned['FUEL TYPE'])] = 'gas'
    matching_fuel_category[Edmunds_data_cleaned['FUEL TYPE'].str.contains('diesel')] = 'D'
    matching_fuel_category[matching_cyl_layout == 'ELE'] = 'E'

    electrification_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Electrification Category').replace(0,'N')
    electrification_category[Edmunds_data_cleaned['FUEL TYPE'] == 'electric fuel'] = 'EV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'] == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CITY/HWY)'].astype(str) != '0/0 mi.')] = 'HEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'] == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CITY/HWY)'].astype(str) == '0/0 mi.') ] = 'REEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'] == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CITY/HWY)'].astype(str) == 'false (electric)')] = 'REEV'

    Edmunds_data_cleaned['CAM TYPE SHORT NAME'] = pd.Series(np.zeros(len(Edmunds_data_cleaned))).replace(0,'')
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('DOHC')] = 'DOHC'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('OHV')] = 'OHV'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('SOHC')] = 'SOHC'

    tire_codes = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Tire Code').replace(0,'')
    initial_columns = pd.Series(Edmunds_data_cleaned.columns)

    # tire_categories_pt1 = pd.Series(initial_columns[(initial_columns.str.contains('TIRES')) \
    #     & (initial_columns.str.contains('/')) & (~initial_columns.str.contains('W/'))& \
    #     (~initial_columns.str.contains(' '))].str.strip().unique())
    # tire_categories_pt2 = pd.Series(initial_columns[(initial_columns.str.contains('TIRES')) \
    #     & (initial_columns.str.contains('/')) & (~initial_columns.str.contains('W/'))& \
    #     (initial_columns.str.contains(' '))].str.split(' ').str.get(0).str.strip().unique())
    # tire_categories = pd.Series(initial_columns[(initial_columns.str.contains('TIRES')) \
    #     & (initial_columns.str.contains('/')) & (~initial_columns.str.contains('W/'))].str.strip().unique())
    tire_categories_raw = pd.Series(initial_columns[(initial_columns.str.contains('TIRES'))].str.strip().unique())
    tire_categories = tire_categories_raw[~pd.isnull(tire_categories_raw.str.extract('(\d+)'))].reset_index(drop=True)
    for tire_category in tire_categories:
        tire_trims = pd.Series(Edmunds_data_cleaned['Trims'][Edmunds_data_cleaned[tire_category]==True]).unique()
        if tire_category.find(' ') == -2: #!= -1
            for tire_trim in tire_trims:
                tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] = \
                    tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] + '|' + tire_category[:tire_category.find(' ')]
                tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes == '')] = tire_category[:tire_category.find(' ')]
        else:
            for tire_trim in tire_trims:
                tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] = \
                    tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] + '|' + tire_category
                tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes == '')] = tire_category

    Edmunds_Final_Output = pd.concat([Edmunds_data_cleaned, matching_cyl_layout, matching_cyl_num, \
                                           matching_eng_disp, matching_drvtrn_layout, matching_trns_category, \
                                           matching_trns_numgears, matching_boost_category, matching_mfr_category, \
                                           matching_fuel_category, electrification_category, tire_codes],axis=1)
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    Edmunds_Final_Output.to_csv(output_path+'\\'+'Edmunds Readin'+'_ '+'MY'+str(year)+' '+date_and_time+'.csv', index=False)