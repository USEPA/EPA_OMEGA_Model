import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
import datetime
def Edmunds_Readin(rawdata_input_path, run_input_path, input_filename, output_path, exceptions_table, \
                   bodyid_filename, matched_bodyid_filename, unit_table, year, \
                   ftp_drivecycle_filename, hwfet_drivecycle_filename, ratedhp_filename, lineageid_filename):
    raw_Edmunds_data = pd.read_csv(rawdata_input_path+'\\'+input_filename, dtype=object, encoding="ISO-8859-1")
    Edmunds_Data = raw_Edmunds_data
    Edmunds_Data['Model'] = Edmunds_Data['Model'].astype(str)
    Edmunds_Data['ELECTRIC POWER STEERING'] = Edmunds_Data['ELECTRIC POWER STEERING'].replace([False,str(False).upper()], 'NOT EPS')\
        .replace([True,str(True).upper()], 'EPS')
    if type(exceptions_table) != str:
        for error_check_count in range(0, len(exceptions_table)):
            Edmunds_Data.loc[(Edmunds_Data['Model'] == exceptions_table['Model'][error_check_count]) & \
                (Edmunds_Data['Trims'] == exceptions_table['Trims'][error_check_count]), exceptions_table['Column Name'][error_check_count]] = \
            exceptions_table['New Value'][error_check_count]

    body_id_table_readin = pd.read_csv(run_input_path + '\\' + bodyid_filename, low_memory=False)
    body_id_table_readin.dropna(subset=['BodyID', 'LineageID'], how='any', inplace=True)
    body_id_table_readin.reset_index(drop=True, inplace=True)
    body_id_table_readin[['BodyID', 'LineageID']].astype(int)

    body_id_table_readin = body_id_table_readin[body_id_table_readin['BodyID EndYear'] != 'xx'].reset_index(drop=True)
    body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['BodyID EndYear'])) \
                                             & (body_id_table_readin['BodyID StartYear'] <= year)].reset_index(drop=True)
    body_id_int_not_null_endyear = body_id_table_int[
        ~body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
    body_id_int_not_null_endyear['BodyID EndYear'] = body_id_int_not_null_endyear['BodyID EndYear'].astype(float)
    body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['BodyID EndYear'] >= year], \
                               body_id_table_int[body_id_table_int['BodyID EndYear'].astype(str).str.contains('null')]]).reset_index(drop=True)
    body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
    body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)

    Edmunds_matched_bodyid_file_raw = pd.read_csv(rawdata_input_path + '\\' + matched_bodyid_filename, converters={'LineageID': int, 'BodyID': int, 'Model':str})
    Edmunds_matched_bodyid_file_notnone = Edmunds_matched_bodyid_file_raw[Edmunds_matched_bodyid_file_raw['LineageID'] != -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_none = Edmunds_matched_bodyid_file_raw[
        Edmunds_matched_bodyid_file_raw['LineageID'] == -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_single = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] != -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_many = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] == -9] \
        .drop('BodyID',axis=1).merge(body_id_table[['LineageID', 'BodyID']], how='left', on = 'LineageID').reset_index(drop=True)
    Edmunds_matched_bodyid = pd.concat([Edmunds_matched_bodyid_file_single, Edmunds_matched_bodyid_file_many, Edmunds_matched_bodyid_file_none]).reset_index(drop=True)
    Edmunds_data_cleaned = Edmunds_Data.merge(Edmunds_matched_bodyid[['Model', 'Trims', 'LineageID', 'BodyID']], how='left', on = ['Model', 'Trims']).reset_index(drop=True)
    # Edmunds_data_cleaned['BodyID'] = Edmunds_data_cleaned['BodyID'].astype(float)
    Edmunds_data_cleaned['BodyID'] = Edmunds_data_cleaned['BodyID'].replace(np.nan, 0).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].replace(np.nan, 0).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].replace(np.nan, 0)
    in_unit_columns=[]; ft_unit_columns = []; ft3_unit_columns = []; lbs_unit_columns = []
    degree_unit_columns=[]; gal_unit_columns = []; mpg_unit_columns = [];
    ncolumns = len(Edmunds_data_cleaned.columns)
    for i in range(ncolumns):
        cell_str = str(Edmunds_data_cleaned.iloc[:, i].to_list())
        if ' in.' in cell_str: in_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' ft.' in cell_str: ft_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' cu.ft.' in cell_str: ft3_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' lbs.' in cell_str: lbs_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' degrees' in cell_str: degree_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' gal.' in cell_str: gal_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' mpg' in cell_str: mpg_unit_columns.append(Edmunds_data_cleaned.columns[i])

    for i in range(len(in_unit_columns)):
        Edmunds_data_cleaned[in_unit_columns[i]] = Edmunds_data_cleaned[in_unit_columns[i]].replace(np.nan, '').str.replace(' in.', '').str.replace('no', '')
    for i in range(len(ft_unit_columns)):
        Edmunds_data_cleaned[ft_unit_columns[i]] = Edmunds_data_cleaned[ft_unit_columns[i]].replace(np.nan, '').str.replace(' ft.', '').str.replace('no', '')
    for i in range(len(ft3_unit_columns)):
        Edmunds_data_cleaned[ft3_unit_columns[i]] = Edmunds_data_cleaned[ft3_unit_columns[i]].replace(np.nan, '').str.replace(' cu.ft.', '').str.replace('no', '')
    for i in range(len(lbs_unit_columns)):
        Edmunds_data_cleaned[lbs_unit_columns[i]] = Edmunds_data_cleaned[lbs_unit_columns[i]].replace(np.nan, '').str.replace(' lbs.', '').str.replace('no', '')
    for i in range(len(degree_unit_columns)):
        Edmunds_data_cleaned[degree_unit_columns[i]] = Edmunds_data_cleaned[degree_unit_columns[i]].replace(np.nan, '').str.replace(' degrees', '').str.replace('no', '')
    for i in range(len(gal_unit_columns)):
        Edmunds_data_cleaned[gal_unit_columns[i]] = Edmunds_data_cleaned[gal_unit_columns[i]].replace(np.nan, '').str.replace(' gal.', '').str.replace('no', '')
    for i in range(len(mpg_unit_columns)):
        Edmunds_data_cleaned[mpg_unit_columns[i]] = Edmunds_data_cleaned[mpg_unit_columns[i]].replace(np.nan, '').str.replace(' mpg', '').str.replace('no', '')

    Edmunds_data_cleaned['CURB WEIGHT'] = Edmunds_data_cleaned['CURB WEIGHT'].str.replace(',', '') #.str.replace(' (Most Popular)', '').str.replace(' (Discontinued)', '')
    Edmunds_data_cleaned['GROSS WEIGHT'] = Edmunds_data_cleaned['GROSS WEIGHT'].str.replace(',', '') #.str.replace(' (Most Popular)', '').str.replace(' (Discontinued)', '')
    Edmunds_data_cleaned['CURB WEIGHT'] = Edmunds_data_cleaned['CURB WEIGHT'].str.replace('no', '') #.str.replace(' (Most Popular)', '').str.replace(' (Discontinued)', '')
    Edmunds_data_cleaned['GROSS WEIGHT'] = Edmunds_data_cleaned['GROSS WEIGHT'].str.replace('no', '') #.str.replace(' (Most Popular)', '').str.replace(' (Discontinued)', '')
    Edmunds_data_cleaned['MAXIMUM PAYLOAD'] = Edmunds_data_cleaned['MAXIMUM PAYLOAD'].str.replace('no', '') #.str.replace(' (Most Popular)', '').str.replace(' (Discontinued)', '')
    Edmunds_data_cleaned['MSRP'] = Edmunds_data_cleaned['MSRP'].str.replace(',', '') #.str.replace(' (Most Popular)', '').str.replace(' (Discontinued)', '')
    Edmunds_data_cleaned['MSRP'] = Edmunds_data_cleaned['MSRP'].str.rstrip(' (Most Popular)')
    Edmunds_data_cleaned['MSRP'] = Edmunds_data_cleaned['MSRP'].str.rstrip(' (Discontinued)')
    Edmunds_data_cleaned['MAXIMUM TOWING CAPACITY'] = Edmunds_data_cleaned['MAXIMUM TOWING CAPACITY'].str.rstrip(' (Estimated)')

    Edmunds_data_cleaned['Drivetrain Layout Category'] = Edmunds_data_cleaned['DRIVE TYPE'].copy()
    matching_drvtype = Edmunds_data_cleaned['DRIVE TYPE']
    matching_drvtype[matching_drvtype.str.contains('Front')] = 'F'
    matching_drvtype[matching_drvtype.str.contains('Four')] = '4'
    matching_drvtype[matching_drvtype.str.contains('All')] = 'A'
    matching_drvtype[matching_drvtype.str.contains('Rear')] = 'R'

    Edmunds_data_cleaned['CYLINDERS'] = Edmunds_data_cleaned['CYLINDERS'].str.replace('Inline ','I').str.replace('Flat ', 'H').replace([np.nan, str(np.nan), 'FALSE', 'false', 'False', 'No', 'no'], 'ELE')
    matching_cyl_layout = pd.Series(Edmunds_data_cleaned['CYLINDERS'].astype(str).str[0], name = 'Cylinder Layout Category').replace('E','ELE').astype(str)
    matching_cyl_num = pd.Series(Edmunds_data_cleaned['CYLINDERS'].astype(str).str[1:], name='Number of Cylinders Category').replace(['LE', 'ALSE', str(np.nan)[1:]], 0)
    # matching_cyl_num = pd.Series(Edmunds_data_cleaned['CYLINDERS'].astype(str).str[1:], name='Number of Cylinders Category').replace(['LE', 'ALSE', str(np.nan)[1:]], 0).astype(float).astype(int)
    matching_eng_disp = pd.Series(Edmunds_data_cleaned['BASE ENGINE SIZE'].str.replace(' L', '').str.replace(' l', '').str.strip(), name='Engine Displacement Category')\
        .replace(['',' ', np.nan,str(np.nan), 'FALSE', 'False', 'no', 'No'], 0).astype(float).round(1)
    # matching_eng_disp = pd.to_numeric(matching_eng_disp, errors='coerce').round(1)
    matching_drvtrn_layout = Edmunds_data_cleaned['Drivetrain Layout Category']
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('Front')] = '2WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('Four')] = '4WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('All')] = '4WD'
    matching_drvtrn_layout[matching_drvtrn_layout.str.contains('Rear')] = '2WD'

    trns_numgears_list = []
    for i in range (len(Edmunds_data_cleaned['TRANSMISSION'])):
        tmp_trns_numgears = str(Edmunds_data_cleaned.loc[i, 'TRANSMISSION']).split('-')[0]
        if tmp_trns_numgears[0] in ['C', 'E', 'n']: tmp_trns_numgears = 1
        trns_numgears_list.append(tmp_trns_numgears)

    matching_trns_numgears = pd.Series(trns_numgears_list, name='Number of Transmission Gears Category').astype(int)
    # matching_trns_numgears = pd.Series(Edmunds_data_cleaned['TRANSMISSION'].str[0], name='Number of Transmission Gears Category').replace(['C', 'Co', 'E', 'n'], 1).astype(int)
    # matching_trns_numgears = pd.to_numeric(matching_trns_numgears, errors='coerce').astype(int)

    # matching_trns_numgears = pd.Series(Edmunds_data_cleaned['TRANSMISSION'].str[0], name='Number of Transmission Gears Category').replace('C',1).replace('E',1).astype(int)
    matching_trns_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Transmission Type Category').replace(0,'A')
    matching_trns_category[matching_trns_numgears == 1] = '1ST'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('automated manual')] = 'AM'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('automatic')] = 'A'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('speed manual')] = 'M'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('continuous')] = '1ST'

    matching_boost_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Boost Type Category').replace(0,'N')
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('Turbo')] = 'TC'
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('Turbodiesel')] = 'TC'
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('Twincharger')] = 'TS'
    matching_boost_category[Edmunds_data_cleaned['Trims'].str.contains('S/C')] = 'SC'
    matching_boost_category[matching_cyl_layout == 'ELE'] = 'ELE'
    matching_mfr_category = pd.Series(Edmunds_data_cleaned['Make'], name='Make Category').astype(str).replace('ROLLS ROYCE', 'ROLLS-ROYCE')

    matching_fuel_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Fuel Type Category').replace(0,'G')
    Edmunds_data_cleaned['FUEL TYPE'][matching_cyl_layout == 'ELE'] = 'Electric fuel'
    Edmunds_data_cleaned['FUEL TYPE'][pd.isnull(Edmunds_data_cleaned['FUEL TYPE'])] = 'gas'
    matching_fuel_category[Edmunds_data_cleaned['FUEL TYPE'].str.contains('Flex')] = 'FFV'
    matching_fuel_category[Edmunds_data_cleaned['FUEL TYPE'].str.contains('Diesel')] = 'D'
    matching_fuel_category[matching_cyl_layout == 'ELE'] = 'E'

    electrification_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Electrification Category').replace(0,'N')
    electrification_category[Edmunds_data_cleaned['FUEL TYPE'] == 'Electric fuel'] = 'EV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) != '0/0 mi.')] = 'HEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) == '0/0 mi.') ] = 'PHEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) == 'false (electric)')] = 'REEV'

    Edmunds_data_cleaned['CAM TYPE SHORT NAME'] = pd.Series(np.zeros(len(Edmunds_data_cleaned))).replace(0,'')
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('DOHC')] = 'DOHC'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('OHV')] = 'OHV'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('SOHC')] = 'SOHC'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('dohc')] = 'DOHC'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('ohv')] = 'OHV'
    Edmunds_data_cleaned['CAM TYPE SHORT NAME'][Edmunds_data_cleaned['CAM TYPE'].astype(str).str.contains('sohc')] = 'SOHC'

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
    # tire_categories_raw = pd.Series(initial_columns[(initial_columns.str.contains('TIRES'))].str.strip().unique())
    tire_sizes = Edmunds_data_cleaned['TIRES']
    tire_types = Edmunds_data_cleaned['TIRE TYPES']
    i = 0
    for tire_type, tire_size in zip(tire_types, tire_sizes):
        if tire_size == '': tire_size = 'NA'
        tire_codes[i] = str(tire_type) + '|' + str(tire_size)
        i += 1
        # if tire_category.find(' ') == -2: #!= -1
        #     for tire_trim in tire_trims:
        #         tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] = \
        #             tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] + '|' + tire_category[:tire_category.find(' ')]
        #         tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes == '')] = tire_category[:tire_category.find(' ')]
    #     else:
    #         for tire_trim in tire_trims:
    #             tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] = \
    #                 tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes != '')] + '|' + tire_category
    #             tire_codes[(Edmunds_data_cleaned['Trims'] == tire_trim) & (tire_codes == '')] = tire_category

    Edmunds_Final_Output = pd.concat([Edmunds_data_cleaned, matching_cyl_layout, matching_cyl_num, \
                                           matching_eng_disp, matching_drvtrn_layout, matching_trns_category, \
                                           matching_trns_numgears, matching_boost_category, matching_mfr_category, \
                                           matching_fuel_category, electrification_category, tire_codes],axis=1)
    Edmunds_Final_Output.rename(columns={'WHEEL BASE':'WHEEL_BASE_INCHES'})
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    print('output_path: ', output_path)
    Edmunds_Final_Output.to_csv(output_path+'\\'+'Edmunds Readin'+'_ '+'MY'+str(year)+' '+date_and_time+'.csv', index=False)