import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
import datetime

def body_id_checks(Edmunds_Data, Edmunds_matched_bodyid_file_raw, year, base_year, _body_style_check, rawdata_input_path, run_input_path, matched_bodyid_filename):

    Edmunds_matched_bodyid_file_raw = Edmunds_matched_bodyid_file_raw.loc[:, ~Edmunds_matched_bodyid_file_raw.columns.str.contains('^Unnamed')]
    if len(Edmunds_matched_bodyid_file_raw['ModelYear'] == year) > 0:
        Edmunds_matched_bodyid_file_raw1 = Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == year, :].reset_index(drop=True)
    if _body_style_check != 1: return Edmunds_matched_bodyid_file_raw;

    if _body_style_check == 1 and len(Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == year, 'BodyID'] == -9) > 0:
        if year < 2019: base_year = year;
        Edmunds_matched_bodyid_file_raw0 = Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == base_year, :].reset_index(drop=True)

        Edmunds_matched_bodyid_file_raw0.loc[:, 'Powertrains'] = 'ICE';
        Edmunds_matched_bodyid_file_raw1.loc[:, 'Powertrains'] = 'ICE';
        Edmunds_matched_bodyid_file_raw1.loc[:, 'Matching'] = 0;
        _body_styles = ['Sedan', 'Truck', 'Hatchback', 'Coupe', 'Convertible', 'SUV', 'Wagon', 'Minivan', 'Van', 'Pickup', 'Crew Cab', 'Regular Cab', 'Double Cab', 'Extended Cab', 'SuperCab', 'King Cab', 'Quad Cab', 'Mega Cab', \
                        'SuperCrew', 'CrewMax', 'Access Cab']
        _powertrain_styles = ['electric DD', 'electric 2AM', 'fuel cell', 'hybrid', 'mild hybrid', 'plug-in']

        for j in range(len(_body_styles)):
            _body_style = _body_styles[j]
            Edmunds_matched_bodyid_file_raw0.loc[Edmunds_matched_bodyid_file_raw0['Trims'].str.contains(_body_style), 'BodyStyle'] = _body_style;
            Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['Trims'].str.contains(_body_style), 'BodyStyle'] = _body_style;

        for j in range(len(_powertrain_styles)):
            _powertrain_style = _powertrain_styles[j];
            Edmunds_matched_bodyid_file_raw0.loc[Edmunds_matched_bodyid_file_raw0['Trims'].str.contains(_powertrain_style), 'Powertrains'] = _powertrain_style;
            Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['Trims'].str.contains(_powertrain_style), 'Powertrains'] = _powertrain_style;

        Edmunds_matched_bodyid_null = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['BodyID'] == -9, :];
        _models_Edmunds_matched_bodyid_null = Edmunds_matched_bodyid_null['Model'].unique();
        for i in range (len(_models_Edmunds_matched_bodyid_null)):
            _model = _models_Edmunds_matched_bodyid_null[i]
            _model_org = _model;
            df_tmp = Edmunds_matched_bodyid_null.loc[(Edmunds_matched_bodyid_null['Model'] == _model_org), :].reset_index(drop=True)
            if len(df_tmp) == 0: continue;
            _wheelbase_df_tmp = [];
            _height_df_tmp = [];
            _length_df_tmp = [];
            for ik in range (len(df_tmp)):
                _wheelbase_tmp = float(df_tmp.loc[ik, 'WHEELBASE'].split(' ')[0])
                if isinstance(df_tmp.loc[ik, 'HEIGHT'], float):
                    # print(df_tmp.loc[ik, 'HEIGHT'])
                    tmp_str = Edmunds_Data.loc[(Edmunds_Data['Model'] == _model_org) & (Edmunds_Data['Trims'] == df_tmp.loc[ik, 'Trims']), 'HEIGHT'].reset_index(drop=True)
                    if isinstance(tmp_str, float) == False:
                        df_tmp.loc[ik, 'HEIGHT'] = tmp_str[0];
                        # Edmunds_matched_bodyid_null.loc[(Edmunds_matched_bodyid_null['Model'] == _model_org), :].reset_index(drop=True)
                _height_tmp = float(df_tmp.loc[ik, 'HEIGHT'].split(' ')[0]);
                _length_tmp = float(df_tmp.loc[ik, 'LENGTH'].split(' ')[0]);
                if _wheelbase_tmp not in _wheelbase_df_tmp:
                    _wheelbase_df_tmp.append(_wheelbase_tmp);
                    _height_df_tmp.append(_height_tmp);
                    _length_df_tmp.append(_length_tmp);
            df_wheelbase = pd.DataFrame({'HEIGHT': _height_df_tmp, 'LENGTH': _length_df_tmp, 'WHEELBASE': _wheelbase_df_tmp});

            _body_styles = df_tmp.loc[df_tmp['Model'] == _model_org, 'BodyStyle'].unique();
            for j in range (len(_body_styles)):
                _body_style = _body_styles[j];
                df_base = Edmunds_matched_bodyid_file_raw0.loc[(Edmunds_matched_bodyid_file_raw0['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw0['BodyStyle'] == _body_style), :].reset_index(drop=True)
                # if (_model_org == 'F-150') and (_body_style == 'SuperCab'): print(_model);

                if (len(df_base) == 0):
                    if (_model == 'SILVERADO-1500-LIMITED'): _model = 'SILVERADO-1500';
                    if (_model == 'SIERRA-1500-LIMITED'): _model = 'SIERRA-1500';
                    if (_model == 'ESCAPE-PLUG-IN-HYBRID'): _model = 'ESCAPE';
                    if (_model == 'CR-V-HYBRID'): _model = 'CR-V';
                    if (_model == 'SANTA-FE-HYBRID'): _model = 'SANTA-FE';
                    if (_model == 'SANTA-FE-PLUG-IN-HYBRID'): _model = 'SANTA-FE';
                    if (_model == 'TUCSON-PLUG-IN-HYBRID'): _model = 'TUCSON';
                    if (_model == 'SORENTO-HYBRID'): _model = 'SORENTO';
                    if (_model == 'SORENTO-PLUG-IN-HYBRID'): _model = 'SORENTO';
                    if (_model == 'COROLLA-HYBRID'): _model = 'COROLLA';

                    if (_model == 'ENCORE-GX'): _model = 'ENCORE';
                    if (_model == 'F-150-LIGHTNING'): _model = 'F-150';
                    if (_model == 'TRANSIT-CARGO-VAN'): _model = 'TRANSIT-VAN';
                    if (_model == 'TRANSIT-CONNECT-CARGO-VAN'): _model = 'TRANSIT-CONNECT';
                    if (_model == 'TRANSIT-CONNECT-PASSENGER-WAGON'): _model = 'TRANSIT-CONNECT';
                    if (_model == 'TRANSIT-CREW-VAN'): _model = 'TRANSIT-VAN';
                    if (_model == 'IONIQ-5'): _model = 'IONIQ';
                    if (_model == 'GRAND-CHEROKEE-L'): _model = 'GRAND-CHEROKEE';
                    if (_model == 'GRAND-CHEROKEE-WK'): _model = 'GRAND-CHEROKEE';
                    if (_model == 'GRAND-CHEROKEE-4XE'): _model = 'GRAND-CHEROKEE';
                    if (_model == 'RAV4-PRIME'): _model = 'RAV4';
                    if (_model == 'WRANGLER-4XE'): _model = 'WRANGLER';
                    if (_model == 'CAYENNE-COUPE'): _model = 'CAYENNE';
                    if (_model == 'MUSTANG-MACH-E'): _model = 'MUSTANG';
                    if (_model == 'CAYENNE-COUPE'): _model = 'CAYENNE';
                    if (_model == 'Q5-SPORTBACK'): _model = 'Q5';
                    if (_model == 'SQ5-SPORTBACK'): _model = 'SQ5';
                    if (_model == 'XC40-RECHARGE'): _model = 'XC40';
                    if (_model == 'A6-ALLROAD'): _model = 'A6';
                    if (_model == 'GHOST'): _model = 'GHOST-SERIES-II';
                    if (_model == 'E-TRANSIT-CARGO-VAN'): _model = 'TRANSIT-VAN';

                    df_base = Edmunds_matched_bodyid_file_raw0.loc[(Edmunds_matched_bodyid_file_raw0['Model'] == _model) & (Edmunds_matched_bodyid_file_raw0['BodyStyle'] == _body_style), :].reset_index(drop=True)

                if len(df_base) == 0: continue;
                _body_IDs_unique = df_base['BodyID'].unique();
                if (_body_IDs_unique[0] != -9):
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'BodyID'] = df_base.loc[0, 'BodyID'];
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'LineageID'] = df_base.loc[0, 'LineageID'];

                for k in range(1, len(_body_IDs_unique)):
                    _bodyID = _body_IDs_unique[k];
                    df_base1 = Edmunds_matched_bodyid_file_raw0.loc[(Edmunds_matched_bodyid_file_raw0['Model'] == _model) & (Edmunds_matched_bodyid_file_raw0['BodyStyle'] == _body_style) & \
                                                                   (Edmunds_matched_bodyid_file_raw0['BodyID'] == _bodyID), :].reset_index(drop=True)
                    if len(df_base1) == 0: continue;
                    _wheelbase_df_base1 = [];
                    for ik in range(len(df_base1)):
                        _wheelbase_tmp = float(df_base1.loc[ik, 'WHEELBASE'].split(' ')[0]);
                        if _wheelbase_tmp not in _wheelbase_df_base1:
                            _wheelbase_df_base1.append(_wheelbase_tmp);

                    _min_wheelbase = abs(_wheelbase_df_tmp[0] - _wheelbase_df_base1[0])
                    for l2 in range(0, len(_wheelbase_df_base1)):
                        df_sort = df_wheelbase.iloc[(df_wheelbase['WHEELBASE'] - _wheelbase_df_base1[l2]).abs().argsort()[:2]]
                        m2 = df_sort.index.tolist()[0];

                        if (m2 > 0):
                            Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                                                                         (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == str(_wheelbase_df_tmp[m2]) + ' in.'), 'BodyID'] = df_base1.loc[l2, 'BodyID'];
                            Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                                                                         (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == str(_wheelbase_df_tmp[m2]) + ' in.'), 'LineageID'] = df_base1.loc[l2, 'LineageID'];

                    del _wheelbase_df_base1;
            del _wheelbase_df_tmp;

        Edmunds_matched_bodyid_null = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['BodyID'] == -9, :];
        _models_Edmunds_matched_bodyid_null = Edmunds_matched_bodyid_null['Model'].unique();
        for i in range (len(_models_Edmunds_matched_bodyid_null)):
            _model = _models_Edmunds_matched_bodyid_null[i]
            df_tmp = Edmunds_matched_bodyid_null.loc[(Edmunds_matched_bodyid_null['Model'] == _model), :].reset_index(drop=True)
            if len(df_tmp) == 0: continue;
            for j in range (len(df_tmp)):
                _body_style = df_tmp.loc[j, 'BodyStyle'];
                if isinstance(df_tmp.loc[j, 'WHEELBASE'], float):
                    print(df_tmp.loc[j, 'WHEELBASE'])
                else:
                    _wheelbase = float(df_tmp.loc[j, 'WHEELBASE'].split(' ')[0]);
                df_base = Edmunds_matched_bodyid_file_raw0.loc[(Edmunds_matched_bodyid_file_raw0['Model'] == _model) & (Edmunds_matched_bodyid_file_raw0['BodyStyle'] == _body_style), :].reset_index(drop=True);
                if len(df_base) == 0: continue;
                _num_bodyIDs = len(df_base['BodyID'].unique());
                if (_num_bodyIDs == 1) and (df_base['BodyID'][0] != -9):
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'BodyID'] = df_base['BodyID'][0];
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'LineageID'] = df_base['LineageID'][0];
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'Matching'] = 1;
                else:
                    _wheelbases = df_base['WHEELBASE'].unique();
                    _k_matching = 0
                    _min_diff = 1000;
                    for k in range(len(_wheelbases)):
                        _wheelbases_k = float(df_base.loc[k, 'WHEELBASE'].split(' ')[0])
                        if (abs(_wheelbase - _wheelbases_k) < _min_diff):
                            _k_matching = k;
                            break;

                    _bodyID = df_base.loc[df_base['WHEELBASE'] == _wheelbases[_k_matching], 'BodyID'][0];
                    _lineageID = df_base.loc[df_base['WHEELBASE'] == _wheelbases[_k_matching], 'LineageID'][0];
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                            (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == df_tmp.loc[j, 'WHEELBASE']), 'BodyID'] = _bodyID;
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                            (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == df_tmp.loc[j, 'WHEELBASE']), 'LineageID'] = _lineageID;
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                        (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == df_tmp.loc[j, 'WHEELBASE']), 'Matching'] = 2;

    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    print('input_path: ', run_input_path)
    Edmunds_matched_bodyid_file_raw1.to_csv(run_input_path + '\\' + 'edmunds-bodyid-MY' + str(year) + '_' + date_and_time + '.csv', index=False)

    null_BodyID_models  = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['BodyID'] == -9, :]
    null_BodyID_models =  null_BodyID_models.drop_duplicates(subset=['Model']);
    null_BodyID_models = null_BodyID_models.drop(['Powertrains', 'Matching'], axis=1)

    null_BodyID_models.to_csv(run_input_path + '\\' + 'Null-BodyIDs-MY' + str(year) + '_' + date_and_time + '.csv', index=False)

    return Edmunds_matched_bodyid_file_raw1;
def Edmunds_Readin(rawdata_input_path, run_input_path, input_filename, output_path, exceptions_table, \
                   bodyid_filename, matched_bodyid_filename, unit_table, year, \
                   ftp_drivecycle_filename, hwfet_drivecycle_filename, ratedhp_filename, lineageid_filename):
    raw_Edmunds_data = pd.read_csv(rawdata_input_path+'\\'+input_filename, dtype=object, encoding="ISO-8859-1")
    Edmunds_Data = raw_Edmunds_data;
    if year >= 2022: Edmunds_Data.rename(columns={"RANGE IN MILES (CITY/HWY)": "RANGE IN MILES (CTY/HWY)"}, inplace=True)

    Edmunds_Data['Model'] = Edmunds_Data['Model'].astype(str)
    Edmunds_Data['ELECTRIC POWER STEERING'] = Edmunds_Data['ELECTRIC POWER STEERING'].replace([False,str(False).upper()], 'NOT EPS')\
        .replace([True,str(True).upper()], 'EPS')
    if type(exceptions_table) != str:
        for error_check_count in range(0, len(exceptions_table)):
            Edmunds_Data.loc[(Edmunds_Data['Model'] == exceptions_table['Model'][error_check_count]) & \
                (Edmunds_Data['Trims'] == exceptions_table['Trims'][error_check_count]), exceptions_table['Column Name'][error_check_count]] = \
            exceptions_table['New Value'][error_check_count]

    # run_input_path
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

    Edmunds_matched_bodyid_file_raw = pd.read_csv(run_input_path + '\\' + matched_bodyid_filename, converters={'LineageID': int, 'BodyID': int, 'Model':str})

    _body_style_check = 1;
    Edmunds_matched_bodyid_file_raw = body_id_checks(Edmunds_Data, Edmunds_matched_bodyid_file_raw, year, 2019, _body_style_check, rawdata_input_path, run_input_path, matched_bodyid_filename);

    Edmunds_matched_bodyid_file_notnone = Edmunds_matched_bodyid_file_raw[Edmunds_matched_bodyid_file_raw['LineageID'] != -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_none = Edmunds_matched_bodyid_file_raw[Edmunds_matched_bodyid_file_raw['LineageID'] == -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_single = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] != -9].reset_index(drop=True);
    Edmunds_matched_bodyid_file_many = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] == -9] \
        .drop('BodyID',axis=1).merge(body_id_table[['LineageID', 'BodyID']], how='left', on = 'LineageID').reset_index(drop=True)
    Edmunds_matched_bodyid = pd.concat([Edmunds_matched_bodyid_file_single, Edmunds_matched_bodyid_file_many, Edmunds_matched_bodyid_file_none]).reset_index(drop=True)
    if year < 2019:
        Edmunds_matched_bodyid['Model'] = Edmunds_matched_bodyid['Model'].str.upper();
        l_str = [' SEDAN', ' SUV', ' WAGON', ' CONVERTIBLE', ' COUPE', ' HATCHBACK', ' DIESEL', ' HYBRID', ' MINIVAN'];
        Edmunds_matched_bodyid['Model'] = Edmunds_matched_bodyid['Model'].str.replace('|'.join(l_str), '', regex=True).str.strip();
        # Edmunds_data_cleaned = Edmunds_Data.merge(Edmunds_matched_bodyid[['Make', 'Trims', 'LineageID', 'BodyID']], how='left', on=['Make', 'Trims']).reset_index(drop=True);
    Edmunds_data_cleaned = Edmunds_Data.merge(Edmunds_matched_bodyid[['Model', 'Trims', 'LineageID', 'BodyID']], how='left', on = ['Model', 'Trims']).reset_index(drop=True)
    # Edmunds_data_cleaned['BodyID'] = Edmunds_data_cleaned['BodyID'].astype(float)
    Edmunds_data_cleaned['BodyID'] = Edmunds_data_cleaned['BodyID'].replace(np.nan, 0).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].replace(np.nan, 0).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].replace(np.nan, 0)
    in_unit_columns=[]; ft_unit_columns = []; ft3_unit_columns = []; lbs_unit_columns = []
    degree_unit_columns=[]; gal_unit_columns = []; mpg_unit_columns = []; mpge_unit_columns = []; kwh_unit_columns = []; mi_unit_columns = []; hr_unit_columns = [];
    ncolumns = len(Edmunds_data_cleaned.columns)
    for i in range(ncolumns):
        cell_str = str(Edmunds_data_cleaned.iloc[:, i].to_list())
        if ' in.' in cell_str: in_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' ft.' in cell_str: ft_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' cu.ft.' in cell_str: ft3_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' lbs.' in cell_str: lbs_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' degrees' in cell_str: degree_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' gal.' in cell_str: gal_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' kwh' in cell_str: kwh_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if (' mi.' in cell_str) or (' mi' in cell_str): mi_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if (' hr.' in cell_str) or (' hr' in cell_str): hr_unit_columns.append(Edmunds_data_cleaned.columns[i])
        if ' mpge' in cell_str:
            mpge_unit_columns.append(Edmunds_data_cleaned.columns[i])
        elif ' mpg' in cell_str:
            mpg_unit_columns.append(Edmunds_data_cleaned.columns[i])

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
    for i in range(len(mpge_unit_columns)):
        Edmunds_data_cleaned[mpge_unit_columns[i]] = Edmunds_data_cleaned[mpge_unit_columns[i]].replace(np.nan, '').str.replace(' mpge', '').str.replace('no', '')
    for i in range(len(mpg_unit_columns)):
        Edmunds_data_cleaned[mpg_unit_columns[i]] = Edmunds_data_cleaned[mpg_unit_columns[i]].replace(np.nan, '').str.replace(' mpg', '').str.replace('no', '')
    for i in range(len(kwh_unit_columns)):
        Edmunds_data_cleaned[kwh_unit_columns[i]] = Edmunds_data_cleaned[kwh_unit_columns[i]].replace(np.nan, '').str.replace(' kwh', '').str.replace('no', '')
    for i in range(len(mi_unit_columns)):
        # if mi_unit_columns[i] == 'FREE MAINTENANCE': print(mi_unit_columns[i]);
        Edmunds_data_cleaned[mi_unit_columns[i]] = Edmunds_data_cleaned[mi_unit_columns[i]].replace(np.nan, '').str.replace(' mi.', '').str.replace('no', '')
    for i in range(len(hr_unit_columns)):
        Edmunds_data_cleaned[hr_unit_columns[i]] = Edmunds_data_cleaned[hr_unit_columns[i]].replace(np.nan, '').str.replace(' hr.', '').str.replace('no', '')

    # print(Edmunds_data_cleaned.loc[Edmunds_data_cleaned['TRANSMISSION'] == 'N/A', 'TRANSMISSION'])

    ncolumns = len(Edmunds_data_cleaned.columns)
    columns_duplicated = []
    for i in range(ncolumns):
        column_name = Edmunds_data_cleaned.columns[i]
        if ('EPA COMBINED MPGE') in column_name and len(column_name) > len('EPA COMBINED MPGE'):
            Edmunds_data_cleaned[column_name].fillna('', inplace=True)
            Edmunds_data_cleaned.loc[Edmunds_data_cleaned[column_name] != '', 'EPA COMBINED MPGE'] = Edmunds_data_cleaned[column_name]
            columns_duplicated.append(column_name)
        if ('EPA ELECTRICITY RANGE') in column_name and len(column_name) > len('EPA ELECTRICITY RANGE'):
            Edmunds_data_cleaned[column_name].fillna('', inplace=True)
            Edmunds_data_cleaned.loc[Edmunds_data_cleaned[column_name] != '', 'EPA ELECTRICITY RANGE'] = Edmunds_data_cleaned[column_name]
            columns_duplicated.append(column_name)
        if ('EPA TIME TO CHARGE BATTERY (AT 240V)') in column_name and len(column_name) > len('EPA TIME TO CHARGE BATTERY (AT 240V)'):
            Edmunds_data_cleaned[column_name].fillna('', inplace=True)
            Edmunds_data_cleaned.loc[Edmunds_data_cleaned[column_name] != '', 'EPA TIME TO CHARGE BATTERY (AT 240V)'] = Edmunds_data_cleaned[column_name]
            columns_duplicated.append(column_name)
        if ('EPA KWH/100 MI') in column_name and len(column_name) > len('EPA KWH/100 MI'):
            Edmunds_data_cleaned[column_name].fillna('', inplace=True)
            Edmunds_data_cleaned.loc[Edmunds_data_cleaned[column_name] != '', 'EPA KWH/100 MI'] = Edmunds_data_cleaned[column_name]
            columns_duplicated.append(column_name)

    for i in range (len(columns_duplicated)):
        Edmunds_data_cleaned.drop(columns_duplicated[i], inplace=True, axis=1)

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
        if tmp_trns_numgears[0] in ['C', 'E', 'n']: tmp_trns_numgears = 1;
        if tmp_trns_numgears == 'continuously variable':
            tmp_trns_numgears = 1;
        trns_numgears_list.append(tmp_trns_numgears)

    matching_trns_numgears = pd.Series(trns_numgears_list, name='Number of Transmission Gears Category').astype(int)
    # matching_trns_numgears = pd.Series(Edmunds_data_cleaned['TRANSMISSION'].str[0], name='Number of Transmission Gears Category').replace(['C', 'Co', 'E', 'n'], 1).astype(int)
    # matching_trns_numgears = pd.to_numeric(matching_trns_numgears, errors='coerce').astype(int)

    # matching_trns_numgears = pd.Series(Edmunds_data_cleaned['TRANSMISSION'].str[0], name='Number of Transmission Gears Category').replace('C',1).replace('E',1).astype(int)
    Edmunds_data_cleaned['TRANSMISSION'].fillna(' ', inplace=True)
    # print(Edmunds_data_cleaned.loc[Edmunds_data_cleaned['TRANSMISSION'] == 'N/A', 'TRANSMISSION'])
    matching_trns_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Transmission Type Category').replace(0,'A')
    matching_trns_category[matching_trns_numgears == 1] = '1ST'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('automated manual')] = 'AM'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('automatic')] = 'A'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('speed manual')] = 'M'
    matching_trns_category[Edmunds_data_cleaned['TRANSMISSION'].str.contains('continuous')] = '1ST'

    matching_boost_category = pd.Series(np.zeros(len(Edmunds_data_cleaned)), name = 'Boost Type Category').replace(0,'N')
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
    electrification_category[(Edmunds_data_cleaned['Trims'].str.contains('electric DD')) | (Edmunds_data_cleaned['Trims'].str.contains('electric 2AM'))] = 'EV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) != '0/0 mi.')] = 'HEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) == 'false (electric)')] = 'REEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) == '0/0 mi.') ] = 'PHEV'
    electrification_category[Edmunds_data_cleaned['Trims'].str.contains('plug-in')] = 'PHEV';
    electrification_category[Edmunds_data_cleaned['Trims'].str.contains('fuel cell')] = 'FCEV';

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
    if ('OVERALL WIDTH WITHOUT MIRRORS' in Edmunds_Final_Output.columns) and ('WIDTH' not in Edmunds_Final_Output.columns):
        # Edmunds_Final_Output.rename(columns={'OVERALL WIDTH WITHOUT MIRRORS': 'WIDTH'})
        Edmunds_Final_Output['WIDTH'] = Edmunds_Final_Output['OVERALL WIDTH WITHOUT MIRRORS'].copy()

    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    print('output_path: ', output_path)
    Edmunds_Final_Output.to_csv(output_path+'\\'+'Edmunds Readin'+'_ '+'MY'+str(year)+' '+date_and_time+'.csv', index=False)