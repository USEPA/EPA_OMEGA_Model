def FE_Readin(input_path, run_input_path, input_filename, output_path, exceptions_table, bodyid_filename, \
              matched_bodyid_filename, unit_table, year, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
              ratedhp_filename, lineageid_filename):
    #Read in the FE Auto Data File and compile the information within it in order to help create an
    # overall data sheet for the U.S. 2016 automotive vehicle fleet
    import pandas as pd
    import numpy as np
    import re
    import datetime
    #I:\Project\Midterm Review\Trends\Trends Data\FE\U.S. Car and Light Truck Specifications and Prices
    save_name = 'FE Readin'
    sheetname_vec = pd.Series(['FEguide', 'EVs', 'PHEVs', 'FCVs']) #Define Sheetnames
    skiprows_vec = [0,7,8,7]
    for i in range (0,len(sheetname_vec)):
        readin_sheet = pd.read_excel(input_path+'\\'+input_filename,sheetname=sheetname_vec[i], skiprows = skiprows_vec[i]) #Read in worksheet
        readin_sheet = readin_sheet.dropna(axis=1, how='all').reset_index(drop=True).astype(str) #Drop clumns with no values
        readin_sheet[readin_sheet.select_dtypes(['object']).columns] = \
            readin_sheet.select_dtypes(['object']).apply(lambda x: x.str.strip()) #Apply str.strip to all entries
        readin_sheet[readin_sheet == 'nan'] = '' #Replace NaN blanks (blanks in original spreadsheet) with empty cells
        if i > 0:
            if sheetname_vec[i] == 'EVs' or sheetname_vec[i] == 'FCVs':
                readin_sheet = readin_sheet[readin_sheet['Fuel Unit - Conventional Fuel'] == 'MPG'].reset_index(drop=True)
            else:
                readin_sheet = readin_sheet[readin_sheet['Model Yr '] != ''].reset_index(drop=True)
            readin_sheet = readin_sheet.rename(columns={'Model Yr ':'Model Year', 'Trans Lockup':'Lockup Torque Converter',\
                                                        'Release Date (gold fill means release date is after 8/2/2012)': 'Release Date'})
            #readin_sheet = readin_sheet[readin_sheet['Index (Model Type Index)'] != ''].reset_index(drop=True)
        readin_sheet = pd.concat([pd.Series(np.zeros(len(readin_sheet)),name = 'Sheet Type').replace(0,sheetname_vec[i]), readin_sheet],axis=1)
        if i == 0: #Create final output array from worksheet outputs
            FE_readin_final_output = readin_sheet
        else:
            concat_start = len(FE_readin_final_output)
            extension_array = pd.DataFrame(np.zeros([len(readin_sheet),FE_readin_final_output.shape[1]]), columns = FE_readin_final_output.columns)
            FE_readin_final_output = pd.concat([FE_readin_final_output,extension_array]).reset_index(drop=True) #Extend final output
            sheet_columns = pd.Series(readin_sheet.columns.values)
            if i > 0:
                output_columns = pd.Series(FE_readin_final_output.columns.values)
                for k in range (0,len(output_columns)):
                    if (sheet_columns == output_columns[k]).sum() == 0:
                        FE_readin_final_output[output_columns[k]][concat_start:] = ''
            for k in range (0,readin_sheet.shape[1]):
                #print(k)
                try:
                    FE_readin_final_output[sheet_columns[k]] #Find new columns
                except KeyError: #Add new columns in
                    FE_readin_final_output.insert(FE_readin_final_output.shape[1],sheet_columns[k],readin_sheet[sheet_columns[k]])
                    FE_readin_final_output[sheet_columns[k]].loc[0:concat_start] = ''
                FE_readin_final_output[sheet_columns[k]].loc[concat_start:] \
                    = pd.Series(readin_sheet[sheet_columns[k]]).tolist()
    #Create separate list items for "/" carlines
    extra_carline_array = FE_readin_final_output[FE_readin_final_output['Carline'].str.contains('/')].reset_index(drop=True)
    for i in range (0,len(extra_carline_array)):
        dash_output_index = FE_readin_final_output['Carline']\
            [FE_readin_final_output['Carline'] == extra_carline_array['Carline'][i]].index[0]
        postdash_trim = extra_carline_array['Carline'][i][extra_carline_array['Carline'][i].find('/')+1:]
        FE_readin_final_output['Carline'][dash_output_index] = \
            FE_readin_final_output['Carline'][dash_output_index][0:FE_readin_final_output['Carline'][dash_output_index].find('/')]
        last_space_index = [m.start() for m in re.finditer(' ', FE_readin_final_output['Carline'][dash_output_index])][-1]
        extra_carline_array['Carline'][i] = FE_readin_final_output['Carline'][dash_output_index]\
            .replace(FE_readin_final_output['Carline'][dash_output_index][1+last_space_index:],postdash_trim).strip()
    FE_readin_final_output = pd.concat([FE_readin_final_output, extra_carline_array])\
        .sort_values(['Mfr Name','Division', 'Carline', 'Index (Model Type Index)']).reset_index(drop=True)
    FE_readin_final_output['Model Year'] = FE_readin_final_output['Model Year'].replace('2016.0', '2016')
    FE_readin_final_output = FE_readin_final_output[FE_readin_final_output['Model Year'] == str(year)].reset_index(drop=True)
    #FE_readin_final_output = pd.concat([pd.Series(range(len(FE_readin_final_output)), name = 'FE_GUIDE_ID')+1,FE_readin_final_output],axis=1)
    
    #Matching Categories
    # import Model_Matching
    matching_cyl_layout = pd.Series(np.zeros(len(FE_readin_final_output)), name = 'Cylinder Layout Category').replace(0,'').astype(str)
    matching_cyl_num = pd.Series(FE_readin_final_output['# Cyl'], name='Number of Cylinders Category').replace('', 0).astype(float).astype(int)
    matching_eng_disp = pd.Series(FE_readin_final_output['Eng Displ'], name='Engine Displacement Category').replace('',0).astype(float).round(1)
    matching_drvtrn_layout = pd.Series(FE_readin_final_output['Drive Sys'], name = 'Drivetrain Layout Category').astype(str).replace(['F', 'R'], '2WD').replace(['A', '4'], '4WD').replace('P', '2WD')
    matching_trns_numgears = pd.Series(FE_readin_final_output['# Gears'].astype(float), name='Number of Transmission Gears Category').astype(int)
    matching_trns_numgears[FE_readin_final_output['Trans'] == 'SCV'] = 1
    matching_trns_category = pd.Series(FE_readin_final_output['Trans'], name='Transmission Type Category').replace(['AMS', 'SA', 'SCV'],['AM', 'A', 'CVT'])
    matching_trns_category[matching_trns_numgears == 1] = '1ST'
    matching_boost_category = pd.Series(FE_readin_final_output['Air Aspir Method'], name='Boost Type Category').astype(str).str.upper().replace([''], 'N')
    matching_boost_category[FE_readin_final_output['Sheet Type'] == 'EVs'] = 'ELE'
    matching_boost_category[FE_readin_final_output['Sheet Type'] == 'FCVs'] = 'ELE'
    matching_mfr_category = pd.Series(FE_readin_final_output['Division'], name='Make Category').astype(str)\
        .str.split().str.get(0).str.upper().str.replace('Aston'.upper(), 'Aston Martin'.upper())\
        .str.replace('Land'.upper(), 'Land Rover'.upper()).str.replace('Alfa'.upper(), 'Alfa Romeo'.upper()).str.strip()
    FE_readin_final_output['Max Ethanol % - Gasoline'][FE_readin_final_output['Max Ethanol % - Gasoline'] == ''] = 0
    matching_fuel_category = pd.Series(FE_readin_final_output['Fuel Usage  - Conventional Fuel'].astype(str).str[0], name='Fuel Type Category').replace('H', 'E')
    matching_fuel_category[FE_readin_final_output['Max Ethanol % - Gasoline'].astype(float) == 85] = 'G'
    electrification_category = pd.Series(np.zeros(len(FE_readin_final_output)), name='Electrification Category').replace(0,'N')
    electrification_category[FE_readin_final_output['Sheet Type'] == 'PHEVs'] = 'REEV'
    electrification_category[FE_readin_final_output['Sheet Type'] == 'EVs'] = 'EV'
    electrification_category[FE_readin_final_output['Sheet Type'] == 'FCVs'] = 'EV'
    electrification_category[(electrification_category == 'N') & (~pd.isnull(FE_readin_final_output['Motor Gen Type Desc'])) & \
                             (FE_readin_final_output['Motor Gen Type Desc'].astype(str) != str(np.nan)) & \
                             (FE_readin_final_output['Motor Gen Type Desc'].astype(str) != '')] = 'HEV'
    FE_readin_final_output = pd.concat([FE_readin_final_output, matching_cyl_layout, matching_cyl_num, matching_eng_disp, matching_drvtrn_layout, \
                           matching_trns_numgears, matching_trns_category, matching_boost_category, matching_mfr_category, \
                           matching_fuel_category, electrification_category],axis=1)
    FE_readin_final_output['Index (Model Type Index)'] = FE_readin_final_output['Index (Model Type Index)']\
        .astype(float).astype(int)
    body_id_table_readin = pd.read_excel(run_input_path + '\\' + bodyid_filename, \
                                         converters={'LineageID': int, 'BodyID': int})
    body_id_table_readin = body_id_table_readin[body_id_table_readin['BodyID EndYear'] != 'xx'].reset_index(drop=True)
    body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['BodyID EndYear'])) \
                                             & (body_id_table_readin['BodyID StartYear'] <= year)].reset_index(drop=True)
    body_id_int_not_null_endyear = body_id_table_int[
        ~body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
    body_id_int_not_null_endyear['BodyID EndYear'] = body_id_int_not_null_endyear['BodyID EndYear'].astype(float)
    body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['BodyID EndYear'] >= year], \
                               body_id_table_int[
                                   body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')]]).reset_index(
        drop=True)
    body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
    body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)

    FE_matched_bodyid_file_raw = pd.read_csv(input_path + '\\' + matched_bodyid_filename, \
                                         converters={'LineageID': int, 'BodyID': int, 'Index (Model Type Index)':int})
    FE_matched_bodyid_file_raw = FE_matched_bodyid_file_raw[FE_matched_bodyid_file_raw['LineageID'] != -9].reset_index(drop=True)
    FE_matched_bodyid_file_single = FE_matched_bodyid_file_raw[FE_matched_bodyid_file_raw['BodyID'] != -9].reset_index(drop=True)
    FE_matched_bodyid_file_many = FE_matched_bodyid_file_raw[FE_matched_bodyid_file_raw['BodyID'] == -9]\
        .drop('BodyID',axis=1).merge(body_id_table[['LineageID', 'BodyID']], how='left', on = 'LineageID').reset_index(drop=True)
    FE_matched_bodyid = pd.concat([FE_matched_bodyid_file_single, FE_matched_bodyid_file_many]).reset_index(drop=True)
    FE_output = FE_readin_final_output.merge(FE_matched_bodyid[['Carline', 'Index (Model Type Index)', 'LineageID', 'BodyID']], \
        how='left', on = ['Carline', 'Index (Model Type Index)']).reset_index(drop=True)
    FE_output['LineageID'] = FE_output['LineageID'].astype(float).astype(int)
    FE_output['BodyID'] = FE_output['BodyID'].astype(float).astype(int)
    # FE_output = pd.concat([FE_output, matching_cyl_layout, matching_cyl_num, matching_eng_disp, matching_drvtrn_layout, \
    #                        matching_trns_numgears, matching_trns_category, matching_boost_category, matching_mfr_category, \
    #                        matching_fuel_category],axis=0)
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    FE_output.to_csv(output_path + '\\' + save_name + ' ' + date_and_time + '.csv', index=False)  # Output final FE data