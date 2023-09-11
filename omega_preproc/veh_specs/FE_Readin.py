def FE_Readin(input_path, run_input_path, input_filename, output_path, exceptions_table, bodyid_filename, \
              matched_bodyid_filename, unit_table, year, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
              ratedhp_filename, lineageid_filename):
    #Read in the FE Auto Data File and compile the information within it in order to help create an
    # overall data sheet for the U.S. 2016 automotive vehicle fleet
    import pandas as pd
    import numpy as np
    import re
    import datetime

    FE_Guide_BodyID_MY_BodyID_Matching = True

    #I:\Project\Midterm Review\Trends\Trends Data\FE\U.S. Car and Light Truck Specifications and Prices
    save_name = 'FE Readin'
    sheettype_vec = [] # pd.Series(['FEguide', 'PHEVs', 'EVs', 'FCVs']) #Define Sheetnames
    skiprows_vec = [0,4,7,3]

    if year == 2016:
        skiprows_vec = [0, 7, 8, 7]
    elif year == 2022:
        skiprows_vec = [0, 4, 7, 3]

    with pd.ExcelFile(input_path+'\\'+input_filename) as xlsx:
        sheetname_vec = [sheet for sheet in xlsx.sheet_names]
        # sheetname_vec = [sheet.lower() for sheet in xlsx.sheet_names]
        # If the sheet is not found, it will a ValueError exception
        # idx = sheets.index(sheet_name)
        # df = pd.read_excel(xlsx, sheet_name=idx)

    for i in range (0,len(sheetname_vec)):
        # readin_sheet = pd.read_excel(input_path+'\\'+input_filename,sheet_name=sheets[i], skiprows = skiprows_vec[i]) #Read in worksheet
        readin_sheet = pd.read_excel(input_path+'\\'+input_filename,sheet_name=sheetname_vec[i], skiprows = skiprows_vec[i]) #Read in worksheet
        readin_sheet = readin_sheet.dropna(axis=1, how='all').reset_index(drop=True).astype(str) #Drop clumns with no values
        readin_sheet[readin_sheet.select_dtypes(['object']).columns] = \
            readin_sheet.select_dtypes(['object']).apply(lambda x: x.str.strip()) #Apply str.strip to all entries
        readin_sheet[readin_sheet == 'nan'] = '' #Replace NaN blanks (blanks in original spreadsheet) with empty cells
        if (i == 0): sheettype_vec.append('FEguide')
        if i > 0:
            if (('EVs' in sheetname_vec[i]) and ('PHEVs' not in sheetname_vec[i]))or ('FCVs' in sheetname_vec[i]):
                if ('FCVs' not in sheetname_vec[i]):
                    sheettype_vec.append('EVs')
                else:
                    sheettype_vec.append('FCVs')

                readin_sheet = readin_sheet[readin_sheet["Carline"] != ''].reset_index(drop=True)
                readin_sheet = readin_sheet[readin_sheet['Fuel Unit - Conventional Fuel'] == 'MPG'].reset_index(drop=True)
                readin_sheet = readin_sheet.rename(columns={'Model Yr ': 'Model Year', 'Trans Lockup': 'Lockup Torque Converter', \
                             'Release Date (gold fill means release date is after 8/2/2012)': 'Release Date'})
            elif ('PHEVs' in sheetname_vec[i]):
                sheettype_vec.append('PHEVs')
                if year == 2016:
                    readin_sheet = readin_sheet[readin_sheet["Model Yr "] != ''].reset_index(drop=True)
                    readin_sheet = readin_sheet[readin_sheet["Carline"] != ''].reset_index(drop=True)
                    readin_sheet = readin_sheet.rename(columns={"Model Yr ": 'Model Year', 'Trans Lockup': 'Lockup Torque Converter',
                                                                "Release Date (gold fill means release date is after 8/2/2012)": "Release Date"})
                elif year == 2022:
                    readin_sheet = readin_sheet[readin_sheet["Model Yr  (gold fill means release date is after today's date)"] != ''].reset_index(drop=True)
                readin_sheet = readin_sheet[readin_sheet["Carline"] != ''].reset_index(drop=True)
                readin_sheet = readin_sheet.rename(columns={"Model Yr  (gold fill means release date is after today's date)": 'Model Year',
                                                            'Trans Lockup': 'Lockup Torque Converter',
                                                            "Release Date (gold fill means release date is after today's date)": "Release Date"})
            # else:
            #     readin_sheet = readin_sheet[readin_sheet['Model Year'] != ''].reset_index(drop=True)
            #     readin_sheet = readin_sheet.rename(columns={'Model Yr ':'Model Year', 'Trans Lockup':'Lockup Torque Converter',\
            #                                             'Release Date (gold fill means release date is after 8/2/2012)': 'Release Date'})
            #readin_sheet = readin_sheet[readin_sheet['Index (Model Type Index)'] != ''].reset_index(drop=True)
        readin_sheet = pd.concat([pd.Series(np.zeros(len(readin_sheet)),name = 'Sheet Type').replace(0,sheettype_vec[i]), readin_sheet],axis=1)
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
        FE_readin_final_output['Carline'][dash_output_index] = FE_readin_final_output['Carline'][dash_output_index][0:FE_readin_final_output['Carline'][dash_output_index].find('/')]
        if (' ' not in FE_readin_final_output['Carline'][dash_output_index]): continue
        last_space_index = [m.start() for m in re.finditer(' ', FE_readin_final_output['Carline'][dash_output_index])][-1]
        extra_carline_array['Carline'][i] = FE_readin_final_output['Carline'][dash_output_index].replace(FE_readin_final_output['Carline'][dash_output_index][1+last_space_index:],postdash_trim).strip()
    FE_readin_final_output = pd.concat([FE_readin_final_output, extra_carline_array])\
        .sort_values(['Mfr Name','Division', 'Carline', 'Index (Model Type Index)']).reset_index(drop=True)
    FE_readin_final_output['Model Year'] = FE_readin_final_output['Model Year'].replace('.0', '')
    # FE_readin_final_output['Model Year'] = FE_readin_final_output['Model Year'].replace('2016.0', '2016')
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
    if ('.csv' in bodyid_filename):
        body_id_table_readin = pd.read_csv(run_input_path + '\\' + bodyid_filename) #  , converters={'LineageID': int, 'BodyID': int})
        body_id_table_readin = body_id_table_readin.loc[pd.notnull(body_id_table_readin['BodyID']), :].reset_index(drop=True)
        # body_id_table_readin['BodyID'] = body_id_table_readin['BodyID'].astype(int)
        # body_id_table_readin['LineageID'] = body_id_table_readin['LineageID'].astype(int)
    else:
        body_id_table_readin = pd.read_excel(run_input_path + '\\' + bodyid_filename, converters={'LineageID': int, 'BodyID': int})
    body_id_table_readin = body_id_table_readin[body_id_table_readin['BodyID EndYear'] != 'xx'].reset_index(drop=True)
    body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['BodyID EndYear'])) \
                                             & (body_id_table_readin['BodyID StartYear'] <= year)].reset_index(drop=True)
    body_id_int_not_null_endyear = body_id_table_int[
        ~body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
    body_id_int_not_null_endyear['BodyID EndYear'] = body_id_int_not_null_endyear['BodyID EndYear'].astype(float)
    body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['BodyID EndYear'] >= year], \
                               body_id_table_int[
                                   body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')]]).reset_index(drop=True)
    body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
    body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)

    if (FE_Guide_BodyID_MY_BodyID_Matching == True):
        edmunds_bodyid_all = pd.read_csv(input_path + '\\' + 'edmunds-bodyid_ALL-20230818 001412.csv')
        edmunds_bodyid_all['ModelYear'] = edmunds_bodyid_all['ModelYear'].astype(int)
        edmunds_bodyid_all['BodyID'] = edmunds_bodyid_all['BodyID'].astype(int)
        edmunds_bodyid_all['LineageID'] = edmunds_bodyid_all['LineageID'].astype(int)

        edmunds_bodyid_my = edmunds_bodyid_all.loc[edmunds_bodyid_all['ModelYear'] == 2019, :].reset_index(drop=True)
        footprint_lineageid_bodyid = pd.read_csv(input_path + '\\' + 'footprint_lineageid_MY_2023_08_29_201935.csv')
        footprint_lineageid_bodyid['BodyID'] = footprint_lineageid_bodyid['LineageID'].copy()
        footprint_lineageid_bodyid['BodyID'] = np.nan
        footprint_lineageid_bodyid['LineageID'] = footprint_lineageid_bodyid['LineageID'].astype(int)
        footprint_lineageid_bodyid.drop(['PROD_VOL_GHG_STD_50_STATE'], axis=1, inplace=True)
        _lineageIDs = edmunds_bodyid_my['LineageID'].unique().tolist()
        for i in range(len(_lineageIDs)):
            _lineageid = _lineageIDs[i]
            _idx = edmunds_bodyid_my.loc[(edmunds_bodyid_my['LineageID'] == _lineageid), 'Model'].index
            _model = edmunds_bodyid_my.loc[_idx[0], 'Model']
            _bodyid = edmunds_bodyid_my.loc[_idx[0], 'BodyID']
            try:
                footprint_lineageid_bodyid.loc[(footprint_lineageid_bodyid['LineageID'] == _lineageid), 'BodyID'] = _bodyid
                                           # (footprint_lineageid_bodyid['FOOTPRINT_CARLINE_NM'].str.contains((_model), case=False, na=False)), 'BodyID'] = _bodyid
            except KeyError:
                print(_model, _lineageid)
                continue

        footprint_lineageid_bodyid.sort_values(by=['LineageID'], inplace=True, ascending=True)
        _lineageIDs = footprint_lineageid_bodyid.loc[(pd.isnull(footprint_lineageid_bodyid['BodyID'])) | (footprint_lineageid_bodyid['BodyID'] == -9), 'LineageID'].unique().tolist()

        _bodyid = footprint_lineageid_bodyid['BodyID'].max()
        for i in range(len(_lineageIDs)):
            _lineageid = _lineageIDs[i]
            _idx = footprint_lineageid_bodyid.loc[(footprint_lineageid_bodyid['LineageID'] == _lineageid), :].index
            _model = footprint_lineageid_bodyid.loc[_idx[0], 'FOOTPRINT_CARLINE_NM']
            _bodyid += 1
            try:
                footprint_lineageid_bodyid.loc[(footprint_lineageid_bodyid['LineageID'] == _lineageid), 'BodyID'] = _bodyid
            except KeyError:
                print(_model, _lineageid)
                continue

        footprint_lineageid_bodyid['BodyID'] = footprint_lineageid_bodyid['BodyID'].astype(int)
        # footprint_lineageid_bodyid.to_csv(output_path + '\\' + 'footprint_lineageid_bodyid' + '-MY' + str(year) + '.csv', index=False)
        edmunds_bodyid_all['WHEELBASE'] = edmunds_bodyid_all['WHEELBASE'].str.split(' ')
        edmunds_bodyid_my_base = edmunds_bodyid_all.loc[edmunds_bodyid_all['ModelYear'] == 2019, :].reset_index(drop=True)
        edmunds_bodyid_my = edmunds_bodyid_all.loc[edmunds_bodyid_all['ModelYear'] == year, :].reset_index(drop=True)
        edmunds_bodyid_my['BodyID'] = edmunds_bodyid_my['LineageID'] = np.nan
        for i in range(len(edmunds_bodyid_my_base)):
            edmunds_bodyid_my_base.loc[i, 'WHEELBASE'] = float(edmunds_bodyid_my_base.loc[i, 'WHEELBASE'][0])
        for i in range(len(edmunds_bodyid_my)):
            edmunds_bodyid_my.loc[i, 'WHEELBASE'] = float(edmunds_bodyid_my.loc[i, 'WHEELBASE'][0])

        _lineageIDs = edmunds_bodyid_my_base['LineageID'].unique().tolist()
        for i in range(len(_lineageIDs)):
            _lineageID = _lineageIDs[i]
            _idx = edmunds_bodyid_my_base.loc[edmunds_bodyid_my_base['LineageID'] == _lineageID, :].index
            _make = edmunds_bodyid_my_base.loc[_idx[0], 'Make']
            _model = edmunds_bodyid_my_base.loc[_idx[0], 'Model']
            _model_splitted = edmunds_bodyid_my_base.loc[_idx[0], 'Model'].split(' ')
            _trims = edmunds_bodyid_my_base.loc[_idx, 'Trims']
            _wheelbases = edmunds_bodyid_my_base.loc[_idx, 'WHEELBASE'].unique()

            print(_model, ', _lineageID = ', _lineageID, ', _wheelbases = ', _wheelbases)
            for j in range(len(_wheelbases)):
                _idx_bodyID_wheelbases = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'] == _make) & (edmunds_bodyid_my['Model'] == _model) &
                                                 (abs(edmunds_bodyid_my['WHEELBASE'] - _wheelbases[j]) <= 0.1)) &
                                                               (pd.isnull(edmunds_bodyid_my['BodyID'])), :].index
                if (len(_idx_bodyID_wheelbases) > 0):
                    _wheelbases_j = _wheelbases[j]
                    edmunds_bodyid_my.loc[_idx_bodyID_wheelbases, 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
                    edmunds_bodyid_my.loc[_idx_bodyID_wheelbases, 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']
                    print('_wheelbases_j = ', _wheelbases_j)
                    continue

            _idx_bodyID = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'] == _make) & (edmunds_bodyid_my['Model'] == _model)) &
                                                (pd.isnull(edmunds_bodyid_my['BodyID'])), :].index
            if (len(_wheelbases) == 1) and (len(_idx_bodyID) > 0):
                edmunds_bodyid_my.loc[_idx_bodyID, 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
                edmunds_bodyid_my.loc[_idx_bodyID, 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']
                continue

            _wheelbases0 = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'].str.contains((_make), case=False, na=False)) &
                                                 (edmunds_bodyid_my['Model'].str.contains((_model), case=False, na=False))) &
                                                 (pd.isnull(edmunds_bodyid_my['BodyID'])), 'WHEELBASE'].unique()
            for j in range(len(_wheelbases0)):
                _idx_bodyID_wheelbases0 = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'].str.contains((_make), case=False, na=False)) &
                                                                 (edmunds_bodyid_my['Model'].str.contains((_model), case=False, na=False)) &
                                                     (abs(edmunds_bodyid_my['WHEELBASE'] - _wheelbases0[j]) <= 0.1)), :].index
                if (len(_idx_bodyID_wheelbases0) > 0):
                    edmunds_bodyid_my.loc[_idx_bodyID_wheelbases0, 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
                    edmunds_bodyid_my.loc[_idx_bodyID_wheelbases0, 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']
                    _wheelbases0_j = _wheelbases0[j]
                    print('_wheelbases0_j = ', _wheelbases0_j)
                    continue

            _idx_bodyID0 = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'].str.contains((_make), case=False, na=False)) &
                                                 (edmunds_bodyid_my['Model'].str.contains((_model), case=False, na=False))) &
                                                 (pd.isnull(edmunds_bodyid_my['BodyID'])), :].index
            if (len(_wheelbases0) == 1) and (len(_idx_bodyID0) > 0):
                edmunds_bodyid_my.loc[_idx_bodyID0, 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
                edmunds_bodyid_my.loc[_idx_bodyID0, 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']

            print("# of Null BodyIDs = ", len(edmunds_bodyid_my.loc[edmunds_bodyid_my['BodyID'].astype(str) == 'nan', :]))
            edmunds_bodyid_my.to_csv(output_path + '\\' + 'edmunds_bodyid_my0' + '-MY' + str(year) + '.csv', index=False)

            edmunds_bodyid_my['BodyID'] = edmunds_bodyid_my['BodyID'].astype(int)
            edmunds_bodyid_my['LineageID'] = edmunds_bodyid_my['LineageID'].astype(int)
            df_nulls = edmunds_bodyid_my.loc[(edmunds_bodyid_my['BodyID'].astype(str) == 'nan') & (edmunds_bodyid_my['LineageID'].astype(str) == 'nan'), :] #  .unique().tolist()
            _idx_nulls = df_nulls.index
            _models = df_nulls['Model'].unique().tolist()
            for i in range(len(_models)):
                _model = _models[i]
                _idx_model = edmunds_bodyid_my.loc[edmunds_bodyid_my['Model'] == _model, :].index
                _make = edmunds_bodyid_my.loc[edmunds_bodyid_my['Model'] == _model, 'Make']
                _wheelbases = edmunds_bodyid_my.loc[edmunds_bodyid_my['Model'] == _model, 'WHEELBASE'].unique()
                df_footprint = footprint_lineageid_bodyid.loc[(footprint_lineageid_bodyid['FOOTPRINT_DIVISION_NM'].str.contains((_make[_idx_model[0]]), case=False, na=False)) &
                                                      (footprint_lineageid_bodyid['FOOTPRINT_CARLINE_NM'].str.contains((_model), case=False, na=False)), :]
                _idx_footprint = df_footprint.index
                if len(_idx_footprint) > 0:
                    _models_footprint = df_footprint.loc[_idx_footprint, 'FOOTPRINT_CARLINE_NM']
                    _wheelbase_inches = df_footprint.loc[_idx_footprint, 'WHEEL_BASE_INCHES'].unique()
                    if (len(_wheelbases) == 1) and (len(_wheelbase_inches) == 1):
                        edmunds_bodyid_my.loc[_idx_model, 'BodyID'] = df_footprint.loc[_idx_footprint[0], 'BodyID']
                        edmunds_bodyid_my.loc[_idx_model, 'LineageID'] = df_footprint.loc[_idx_footprint[0], 'LineageID']
                    else:
                        for j in range(len(_wheelbases)):
                            _wheelbases_j = _wheelbases[j]
                            for k in range(len(_wheelbase_inches)):
                                if abs(_wheelbases_j - _wheelbase_inches[k]) <= 0.1:
                                    _wheelbase_inches_k = _wheelbase_inches[k]
                                    _idx_k = df_footprint.loc[df_footprint['WHEEL_BASE_INCHES'] == _wheelbase_inches_k, :].index
                                    edmunds_bodyid_my.loc[_idx_model, 'BodyID'] = df_footprint.loc[_idx_k[0], 'BodyID']
                                    edmunds_bodyid_my.loc[_idx_model, 'LineageID'] = df_footprint.loc[_idx_k[0], 'LineageID']
                                    break
                                else:
                                    continue


                if ('-' in _model): _model = _model.split('-')[0]

                # print(_make, ', ', _model, ', _lineageID = ', _lineageID, ', _wheelbases = ', _wheelbases)
                # for j in range(len(_wheelbases)):
                #     _idx_bodyID_wheelbases = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'] == _division_id) & (
                #                 edmunds_bodyid_my['Model'] == _carline_nm) & (abs(edmunds_bodyid_my['WHEELBASE'] - _wheelbases[j]) <= 0.1)) &
                #                                                    (pd.isnull(edmunds_bodyid_my['BodyID'])), :].index
                #     if (len(_idx_bodyID_wheelbases) > 0):
                #         _wheelbases_j = _wheelbases[j]
                #         edmunds_bodyid_my.loc[_idx_bodyID_wheelbases, 'BodyID'] = footprint_lineageid_bodyid.loc[_idx[0], 'BodyID']
                #         edmunds_bodyid_my.loc[_idx_bodyID_wheelbases, 'LineageID'] = footprint_lineageid_bodyid.loc[_idx[0], 'LineageID']
                #         print('_wheelbases_j = ', _wheelbases_j)
                #         continue
                #
                # _idx_bodyID = edmunds_bodyid_my.loc[((edmunds_bodyid_my['Make'] == _division_id) & (edmunds_bodyid_my['Model'] == _carline_nm)) &
                #               (pd.isnull(edmunds_bodyid_my['BodyID'])), :].index
                # if (len(_wheelbases) == 1) and (len(_idx_bodyID) > 0):
                #     edmunds_bodyid_my.loc[_idx_bodyID, 'BodyID'] = footprint_lineageid_bodyid.loc[_idx[0], 'BodyID']
                #     edmunds_bodyid_my.loc[_idx_bodyID, 'LineageID'] = footprint_lineageid_bodyid.loc[_idx[0], 'LineageID']
                #     continue
                #
                # _wheelbases0 = edmunds_bodyid_my.loc[
                #     ((edmunds_bodyid_my['Make'].str.contains((_division_id), case=False, na=False)) & (edmunds_bodyid_my['Model'].str.contains((_carline_nm), case=False, na=False))) &
                #     (pd.isnull(edmunds_bodyid_my['BodyID'])), 'WHEELBASE'].unique()
                # for j in range(len(_wheelbases0)):
                #     _idx_bodyID_wheelbases0 = edmunds_bodyid_my.loc[
                #                               ((edmunds_bodyid_my['Make'].str.contains((_division_id), case=False, na=False)) &
                #                                (edmunds_bodyid_my['Model'].str.contains((_carline_nm), case=False, na=False)) &
                #                                (abs(edmunds_bodyid_my['WHEELBASE'] - _wheelbases0[j]) <= 0.1)), :].index
                #     if (len(_idx_bodyID_wheelbases0) > 0):
                #         edmunds_bodyid_my.loc[_idx_bodyID_wheelbases0, 'BodyID'] = footprint_lineageid_bodyid.loc[_idx[0], 'BodyID']
                #         edmunds_bodyid_my.loc[_idx_bodyID_wheelbases0, 'LineageID'] = footprint_lineageid_bodyid.loc[_idx[0], 'LineageID']
                #         _wheelbases0_j = _wheelbases0[j]
                #         print('_wheelbases0_j = ', _wheelbases0_j)
                #         continue
                #
                # _idx_bodyID0 = edmunds_bodyid_my.loc[
                #                ((edmunds_bodyid_my['Make'].str.contains((_division_id), case=False, na=False)) &
                #                 (edmunds_bodyid_my['Model'].str.contains((_carline_nm), case=False, na=False))) & (pd.isnull(edmunds_bodyid_my['BodyID'])), :].index
                # if (len(_wheelbases0) == 1) and (len(_idx_bodyID0) > 0):
                #     edmunds_bodyid_my.loc[_idx_bodyID0, 'BodyID'] = footprint_lineageid_bodyid.loc[_idx[0], 'BodyID']
                #     edmunds_bodyid_my.loc[_idx_bodyID0, 'LineageID'] = footprint_lineageid_bodyid.loc[_idx[0], 'LineageID']

            print("# of Null BodyIDs = ", len(edmunds_bodyid_my.loc[edmunds_bodyid_my['BodyID'].astype(str) == 'nan', :]))
            print("# of Null Models = ", len(edmunds_bodyid_my.loc[edmunds_bodyid_my['BodyID'].astype(str) == 'nan', 'Model'].unique()))
            edmunds_bodyid_my.to_csv(output_path + '\\' + 'edmunds_bodyid_my' + '-MY' + str(year) + '.csv', index=False)

            # _idx = footprint_lineageid_bodyid.loc[(footprint_lineageid_bodyid['FOOTPRINT_CARLINE_NM'] == _model) | ((footprint_lineageid_bodyid['FOOTPRINT_DIVISION_NM'].str.contains((_make), case=False, na=False)) &
            #                                          (footprint_lineageid_bodyid['FOOTPRINT_CARLINE_NM'].str.contains((_model_splitted[0]), case=False, na=False)) |
            #                                              (footprint_lineageid_bodyid['FOOTPRINT_DESC'].str.contains((_trims[0]), case=False, na=False))), 'BodyID'].index
            # if (len(_idx_bodyID_wheelbases) > 0):
            #     edmunds_bodyid_my.loc[_idx_bodyID_wheelbases & (pd.isnull(edmunds_bodyid_my['BodyID'])), 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
            #     edmunds_bodyid_my.loc[_idx_bodyID_wheelbases & (pd.isnull(edmunds_bodyid_my['LineageID'])), 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']
            # elif (len(_wheelbases) == 1) and (len(_idx_bodyID) > 0):
            #     edmunds_bodyid_my.loc[_idx_bodyID & (pd.isnull(edmunds_bodyid_my['BodyID'])), 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
            #     edmunds_bodyid_my.loc[_idx_bodyID & (pd.isnull(edmunds_bodyid_my['LineageID'])), 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']
            # elif (len(_idx_bodyID_wheelbases0) > 0):
            #     edmunds_bodyid_my.loc[_idx_bodyID_wheelbases0 & (pd.isnull(edmunds_bodyid_my['BodyID'])), 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
            #     edmunds_bodyid_my.loc[_idx_bodyID_wheelbases0 & (pd.isnull(edmunds_bodyid_my['LineageID'])), 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']
            # elif (len(_wheelbases0) == 1) and (len(_idx_bodyID0) > 0):
            #     edmunds_bodyid_my.loc[_idx_bodyID0 & (pd.isnull(edmunds_bodyid_my['BodyID'])), 'BodyID'] = edmunds_bodyid_my_base.loc[_idx[0], 'BodyID']
            #     edmunds_bodyid_my.loc[_idx_bodyID0 & (pd.isnull(edmunds_bodyid_my['LineageID'])), 'LineageID'] = edmunds_bodyid_my_base.loc[_idx[0], 'LineageID']


    # | ((edmunds_bodyid_my_base['Make'].str.contains((_make), case=False, na=False)) &
    #    (edmunds_bodyid_my_base['Model'].str.contains((_model_splitted[0]), case=False, na=False)))

# Output final FE data
    FE_matched_bodyid_file_raw = pd.read_csv(input_path + '\\' + matched_bodyid_filename)
    FE_matched_bodyid_file_raw.loc[pd.notnull(FE_matched_bodyid_file_raw['BodyID']), :].reset_index(drop=True, inplace=True)
    FE_matched_bodyid_file_raw['BodyID'] = FE_matched_bodyid_file_raw['BodyID'].astype(int)
    FE_matched_bodyid_file_raw['LineageID'] = FE_matched_bodyid_file_raw['LineageID'].astype(int)
    if ('Index (Model Type Index)' in FE_matched_bodyid_file_raw.columns):
        FE_matched_bodyid_file_raw['Index (Model Type Index)'] = FE_matched_bodyid_file_raw['Index (Model Type Index)'].astype(int)
    # converters={'FE_matched_bodyid_file_raw': int, 'BodyID': int, 'Index (Model Type Index)':int})
    FE_matched_bodyid_file_raw = FE_matched_bodyid_file_raw[FE_matched_bodyid_file_raw['LineageID'] != -9].reset_index(drop=True)
    FE_matched_bodyid_file_single = FE_matched_bodyid_file_raw[FE_matched_bodyid_file_raw['BodyID'] != -9].reset_index(drop=True)
    FE_matched_bodyid_file_many = FE_matched_bodyid_file_raw[FE_matched_bodyid_file_raw['BodyID'] == -9]\
        .drop('BodyID',axis=1).merge(body_id_table[['LineageID', 'BodyID']], how='left', on = 'LineageID').reset_index(drop=True)
    FE_matched_bodyid = pd.concat([FE_matched_bodyid_file_single, FE_matched_bodyid_file_many]).reset_index(drop=True)
    if ('Index (Model Type Index)' in FE_matched_bodyid_file_raw.columns):
        FE_output = FE_readin_final_output.merge(FE_matched_bodyid[['Carline', 'Index (Model Type Index)', 'LineageID', 'BodyID']], \
            how='left', on = ['Carline', 'Index (Model Type Index)']).reset_index(drop=True)
    else:
        FE_output = FE_readin_final_output.merge(FE_matched_bodyid[['Model', 'LineageID', 'BodyID']], \
            how='left', on = [['Carline', 'LineageID', 'BodyID']]).reset_index(drop=True)

    FE_output['MODEL_TYPE_INDEX'] = FE_output['Index (Model Type Index)'].copy()
    # FE_output = FE_output.rename({'Index (Model Type Index)': 'MODEL_TYPE_INDEX'}, axis=1)

    # FE_output['LineageID'] = FE_output['LineageID'].astype(float).astype(int)
    # FE_output['BodyID'] = FE_output['BodyID'].astype(float).astype(int)
    # # FE_output = pd.concat([FE_output, matching_cyl_layout, matching_cyl_num, matching_eng_disp, matching_drvtrn_layout, \
    # #                        matching_trns_numgears, matching_trns_category, matching_boost_category, matching_mfr_category, \
    # #                        matching_fuel_category],axis=0)
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    FE_output.to_csv(output_path + '\\' + save_name + '_MY' + str(year) + '-' + date_and_time + '.csv', index=False)  # Output final FE data