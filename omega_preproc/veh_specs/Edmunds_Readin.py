import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'
import numpy as np
import datetime

cols_safety = ["DUAL FRONT SIDE-MOUNTED AIRBAGS", "DUAL FRONT WITH HEAD PROTECTION CHAMBERS SIDE-MOUNTED AIRBAGS",
               "DUAL FRONT AND DUAL REAR SIDE-MOUNTED AIRBAGS",
               "DUAL FRONT AND DUAL REAR WITH HEAD PROTECTION CHAMBERS SIDE-MOUNTED AIRBAGS",
               "DRIVER ONLY WITH HEAD PROTECTION CHAMBER SIDE-MOUNTED AIRBAGS",
               "FRONT, REAR AND THIRD ROW HEAD AIRBAGS", "FRONT AND REAR HEAD AIRBAGS", "FRONT HEAD AIRBAGS",
               "FRONT, REAR, THIRD AND FOURTH ROW HEAD AIRBAGS",
               "STABILITY CONTROL", "TRACTION CONTROL", "TIRE PRESSURE MONITORING"]
_body_style_check = False
edmunds_bodyid_to_edmunds_bodyid_match = True
footprint_lineageid_to_edmunds_lineageid_match = True

def check_footprint_lineageIDs(Edmunds_matched_bodyid_file_raw1, Edmunds_matched_bodyid_file_raw, footprint_lineageid_flag, year, _matching_ID_cname, run_input_path, date_and_time):

    if footprint_lineageid_flag == True:
        _modelyear_cname = 'MODEL_YEAR'
        _make_cname = 'FOOTPRINT_DIVISION_NM'
        _model_cname = 'FOOTPRINT_CARLINE_NM'
        _trims_cname = 'FOOTPRINT_DESC'
        _bodyid_cname = 'FOOTPRINT_CARLINE_CD'
    else:
        _modelyear_cname = 'ModelYear'
        _make_cname = 'Make'
        _model_cname = 'Model'
        _trims_cname = 'Trims'
        _bodyid_cname = 'BodyID'

    # _matching_ID_cname = 'LineageID'
    _makers = pd.DataFrame(Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] == -9), 'Make'].unique().tolist(), columns=['Make']).sort_values(by=['Make']).reset_index(drop=True)
    _lineagdID_max = Edmunds_matched_bodyid_file_raw1[_matching_ID_cname].max()
    for kk in range(len(_makers)):
        _models = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Make'] == _makers.loc[kk, 'Make']) & (Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] == -9), 'Model'].unique()
        for i in range(len(_models)):
            # if (_models[i] == 'TRANSIT-CONNECT-PASSENGER-WAGON'):
            #     print(_models[i])
            _model_splitted = _models[i].split('-')
            _model = _model_splitted[0]
            if (len(_model_splitted) > 1):
                if ((_model == 'F') and ((_model_splitted[1] != 'PACE') and (_model_splitted[1] != 'TYPE')))  or (_model == 'SILVERADO') or (_model == 'SIERRA') or (_model == 'MODEL') or \
                    (_models[i] == 'C-HR') or (_models[i] == 'CR-V') or (_models[i] == 'HR-V') or (_models[i] == 'F-PACE') or (_models[i] == 'F-TYPE') or (_model_splitted[1] == 'SERIES') or (_model == 'RS') \
                        or (_model == 'SANTA')  or (_model == 'GRAND') or (_model == 'ES') or (_model == 'MX') or (_model == 'CX') or (_model == 'GR') or (_model_splitted[1] == 'CLASS'):
                    _model = _model_splitted[0] + '-' + _model_splitted[1]

            _trims = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _models[i]) & (Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] == -9), 'Trims']
            _index = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _models[i]) & (Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] == -9), 'Trims'].index
            for j in range(len(_index)):
                _drivetrain = ''
                _doorstyle = ''
                _roofstyle = ''
                _vanstyle = ''
                _make = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Make']
                _trim = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Trims']
                _wheelbase = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'WHEELBASE']
                _bodystyle = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyStyle']
                _trim_splitted = _trim.split(' ')
                for kk in range(len(_trim_splitted)):
                    if 'dr' in _trim_splitted[kk]: _doorstyle = _trim_splitted[kk]
                    if 'WD' in _trim_splitted[kk]: _drivetrain = _trim_splitted[kk]
                    if 'Roof' in _trim_splitted[kk]: _roofstyle = _trim_splitted[kk-1] + ' ' + _trim_splitted[kk]

                    if ('Van' in _trim_splitted[kk]) and (_bodystyle == "Van"):
                        _vanstyle = _trim_splitted[kk]
                        if (_trim_splitted[kk-1] == "Ext"): _vanstyle = _bodystyle = "Ext Van"
                        if (_trim_splitted[kk-1] == "Cargo"): _vanstyle = _bodystyle = "Cargo Van"
                        if (_trim_splitted[kk-1] == "Passenger"): _vanstyle = _bodystyle = "Passenger Van"

                _trim0 = _trim_splitted[0]
                if footprint_lineageid_flag == True:
                    if ('F-250' in _models[i]) or ('F-350' in _models[i]) or ('F-450' in _models[i]): continue
                    if ('2500' in _models[i]) or ('3500' in _models[i]) or ('4500' in _models[i]): continue

                    if _model == 'F-150':
                        _model = 'F150'
                    elif ('SILVERADO-1500' in _model) and ('2500' not in _models[i]) and ('3500' not in _models[i]):
                        _model = 'SILVERADO'
                    elif (('TRANSIT' in _models[i]) or ('E-TRANSIT' in _models[i])) and ('TRANSIT-CONNECT' not in _models[i]):
                        _model = 'TRANSIT T150 WAGON'
                    elif ('TRANSIT-CONNECT' in _models[i]):
                        _model = 'TRANSIT CONNECT'
                    elif (_model == 'SIERRA-1500') and ('2500' not in _models[i]) and ('3500' not in _models[i]):
                        _model = 'SIERRA'
                    elif ('MUSTANG-MACH-E' in _models[i]):
                        _model = 'MUSTANG MACH-E'
                    elif ('SHELBY-GT500' in _models[i]):
                        _model = 'FORD GT'
                    elif ('GR-SUPRA' in _models[i]):
                        if ('2.0' in _trim): _model = 'Supra 2.0'
                        if ('3.0' in _trim): _model = 'Supra 3.0'
                    elif ('E-TRON' in _models[i]):
                        if ('Q4-SPORTBACK-E-TRON' in _models[i]):
                            _model = 'Q4 e-tron Sportback'
                        elif len(_model_splitted) >= 2:
                            _model = 'E-TRON' + ' ' + _model_splitted[2]
                        else:
                            _model = 'E-TRON'
                    elif ('C-HR' in _models[i]) or ('CR-V' in _models[i]) or ('E-PACE' in _models[i]) or ('F-PACE' in _models[i])  or ('I-PACE' in _models[i])  or ('F-TYPE' in _models[i]) \
                            or ('CX-3' in _models[i])  or ('CX-30' in _models[i]) or ('CX-5' in _models[i]) or ('CX-7' in _models[i]) or ('CX-9' in _models[i]) or ('E-GOLF' in _models[i]) \
                            or ('MV-1' in _models[i]) or ('MX-5' in _models[i]) or ('MX-30' in _models[i]) or ('FR-S' in _models[i]) or ('9-4X' in _models[i]) \
                            or ('GLB-CLASS' in _models[i]) or ('GOLF-R' in _models[i]) or ('HR-V' in _models[i]) or ('Q4 E-TRON' in _models[i]):
                        _model = _model_splitted[0] + '-' + _model_splitted[1]
                    else:
                        _model = _model.replace("-", " ")

                    if ('Rolls-Royce' in _make) or ('Mercedes-Benz' in _make):
                        pass
                    else:
                        _make = _make.replace("-", " ")

                    _idx = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_drivetrain), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_vanstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_bodystyle), case=False, na=False)) &
                                                               (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :].index
                    if len(_idx) == 0:
                        _idx = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_drivetrain), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :].index
                    if len(_idx) == 0:
                        _idx = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :].index
                    if len(_idx) == 0:
                        _idx = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :].index
                else:
                    _idx = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_trim0), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_drivetrain), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_doorstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_roofstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_vanstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_bodystyle), case=False, na=False)) & (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :].index
                if len(_idx) > 0:
                    if footprint_lineageid_flag == True:
                        _yr = year
                        _bodyids = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_drivetrain), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_roofstyle), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_vanstyle), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_bodystyle), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_modelyear_cname] == _yr) & (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :]
                        if len(_bodyids) == 0:
                            _bodyids = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                                           (Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_drivetrain), case=False, na=False)) &
                                                                           (Edmunds_matched_bodyid_file_raw[_modelyear_cname] == _yr) &
                                                                       (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :]

                        if len(_bodyids) == 0:
                            _bodyids = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_modelyear_cname] == _yr) &
                                                                       (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :]
                        if len(_bodyids) == 0:
                            _bodyids = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                       (Edmunds_matched_bodyid_file_raw[_modelyear_cname] == _yr) &
                                                                       (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :]

                    else:
                        _yr = Edmunds_matched_bodyid_file_raw.loc[_idx, 'ModelYear'].max()
                        _bodyids = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw[_model_cname].str.contains((_model), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_make_cname].str.contains((_make), case=False,na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_trim0), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_drivetrain), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_doorstyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_roofstyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_vanstyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_trims_cname].str.contains((_bodystyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw[_modelyear_cname] == _yr) & (Edmunds_matched_bodyid_file_raw[_matching_ID_cname] != -9), :]

                    if (len(_bodyids) == 1) or (len(_bodyids) >= 1 and footprint_lineageid_flag == True):
                        # Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyID'] = _bodyids.loc[_bodyids.index[0], 'BodyID']
                        Edmunds_matched_bodyid_file_raw1.loc[_index[j], _matching_ID_cname] = _bodyids.loc[_bodyids.index[0], _matching_ID_cname]
                        if (footprint_lineageid_flag != True):
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Matching'] = 3
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'] = str(_bodyids.loc[_bodyids.index[0], _modelyear_cname]) + ', ' + _models[i] + ', ' + _trim
                        # print(_trim, Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'])
                    elif (len(_bodyids) > 1):
                        _idx_wheelbase_matched_yr = 0
                        _wheelbase_diff = 999*np.ones(len(_bodyids))
                        for k in range(len(_bodyids)):
                            _wheelbase_yr = _bodyids.loc[_bodyids.index[k], 'WHEELBASE']
                            _wheelbase_diff[k] = abs(float(_wheelbase.split(' ')[0]) - float(_wheelbase_yr.split(' ')[0]))
                            if (_wheelbase == _wheelbase_yr) or (_wheelbase_diff[k] <= 0.1):
                                _idx_wheelbase_matched_yr = _bodyids.index[k]
                                break;
                        if _idx_wheelbase_matched_yr != 0:
                            # Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyID'] = _bodyids.loc[_idx_wheelbase_matched_yr, 'BodyID']
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], _matching_ID_cname] = _bodyids.loc[_idx_wheelbase_matched_yr, _matching_ID_cname]
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Matching'] = 3
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'] = str(_bodyids.loc[_idx_wheelbase_matched_yr, 'ModelYear']) + ', ' + _models[i] + ', ' + _trim
                            # print(_trim, Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'])
                        else:
                            _idx_wheelbase_diff_min = 0
                            _wheelbase_diff_min = 999
                            for kk in range(len(_wheelbase_diff)):
                                if _wheelbase_diff[kk] < _wheelbase_diff_min:
                                    _wheelbase_diff_min = _wheelbase_diff[kk]
                                    _idx_wheelbase_diff_min = kk
                                    break
                            # Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyID'] = _bodyids.loc[_bodyids.index[_idx_wheelbase_diff_min], 'BodyID']
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], _matching_ID_cname] = _bodyids.loc[_bodyids.index[_idx_wheelbase_diff_min], _matching_ID_cname]
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Matching'] = 4
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'] = str(_bodyids.loc[_bodyids.index[_idx_wheelbase_diff_min], 'ModelYear']) + ', ' + _models[i] + ', ' + _trim
                            # print(_trim, Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'])

    Edmunds_matched_bodyid_file_raw1.to_csv(run_input_path + '\\' + 'footprint1-edmunds-bodyid-MY' + str(year) + '-' + date_and_time + '.csv', index=False)

    if (footprint_lineageid_flag == True):
        _models = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] == -9), 'Model'].unique()
        for i in range(len(_models)):
            _model = _models[i]
            _model_splitted = _models[i].split("-")
            if ('F-250' in _models[i]) or ('F-350' in _models[i]) or ('F-450' in _models[i]): continue
            if ('2500' in _models[i]) or ('3500' in _models[i]) or ('4500' in _models[i]): continue

            if (('F' in _model) and ('PACE' not in _model) and ('FACE' not in _model) and ('TYPE' not in _model)) or ('SILVERADO' in _model) or \
                    ('TRANSIT-CONNECT' in _model):
                _model = _model_splitted[0] + '-' + _model_splitted[1]
            elif ('MUSTANG-MACH-E' in _models[i]):
                _model = 'MUSTANG-MACH-E'
            elif (('TRANSIT' in _models[i]) or ('E-TRANSIT' in _models[i])) and ('TRANSIT-CONNECT' not in _models[i]):
                _model = 'TRANSIT-VAN'
            elif ('TRANSIT-CONNECT' in _models[i]):
                _model = 'TRANSIT-CONNECT'
            elif ('E-TRON' in _models[i]):
                if len(_model_splitted) >= 2: _model = 'E-TRON' + '-' + _model_splitted[2]
                if len(_model_splitted) < 2: _model = 'E-TRON'
            elif ('C-HR' in _models[i]) or ('CR-V' in _models[i]) or ('E-PACE' in _models[i]) or ('F-PACE' in _models[i])  or ('I-PACE' in _models[i])  or ('F-TYPE' in _models[i]) \
                            or ('CX-3' in _models[i])  or ('CX-30' in _models[i]) or ('CX-5' in _models[i]) or ('CX-7' in _models[i]) or ('CX-9' in _models[i]) or ('E-GOLF' in _models[i]) \
                            or ('MV-1' in _models[i]) or ('MX-5' in _models[i]) or ('MX-30' in _models[i]) or ('FR-S' in _models[i]) or ('9-4X' in _models[i]) \
                            or ('GLB-CLASS' in _models[i]) or ('GOLF-R' in _models[i]) or ('HR-V' in _models[i]) or ('Q4 E-TRON' in _models[i]) or (_model == 'SILVERADO') or \
                    (_model == 'SIERRA') or (_model == 'F'):
                _model = _model_splitted[0] + '-' + _model_splitted[1]
            else:
                _model = _model_splitted[0]

            _idx_nulls = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'].str.contains((_model), case=False, na=False)) & (Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] == -9), 'Model'].index
            _idx = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'].str.contains((_model), case=False, na=False)) & (Edmunds_matched_bodyid_file_raw1[_matching_ID_cname] != -9), :].index
            if len(_idx) > 0:
                Edmunds_matched_bodyid_file_raw1.loc[_idx_nulls, _matching_ID_cname] = Edmunds_matched_bodyid_file_raw1.loc[_idx[0], _matching_ID_cname]

    Edmunds_matched_bodyid_file_raw1.to_csv(run_input_path + '\\' + 'footprint2-edmunds-bodyid-MY' + str(year) + '-' + date_and_time + '.csv', index=False)

    return Edmunds_matched_bodyid_file_raw1

def body_id_checks(Edmunds_Data, Edmunds_matched_bodyid_file_raw, year, base_year, rawdata_input_path, run_input_path, matched_bodyid_filename, lineageid_filename):

    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    Edmunds_matched_bodyid_file_raw = Edmunds_matched_bodyid_file_raw.loc[:, ~Edmunds_matched_bodyid_file_raw.columns.str.contains('^Unnamed')]
    if len(Edmunds_matched_bodyid_file_raw['ModelYear'] == year) > 0:
        Edmunds_matched_bodyid_file_raw1 = Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == year, :].reset_index(drop=True)
    if _body_style_check != 1: return Edmunds_matched_bodyid_file_raw;

    if _body_style_check == 1 and len(Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == year, 'BodyID'] == -9) > 0:
        if year < 2019: base_year = year;
        Edmunds_matched_bodyid_file_raw0 = Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == base_year, :].reset_index(drop=True)
        _idx_blanks = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['Model'].str.contains(' '), :].index
        if (len(_idx_blanks) == 0):
            Edmunds_matched_bodyid_file_raw0.loc[Edmunds_matched_bodyid_file_raw0['Model'].str.contains(' '), 'Model'].str.replace(' ', '-')

        Edmunds_matched_bodyid_file_raw0.loc[:, 'Powertrains'] = 'ICE';
        Edmunds_matched_bodyid_file_raw1.loc[:, 'Powertrains'] = 'ICE';
        Edmunds_matched_bodyid_file_raw1.loc[:, 'Matching'] = 0;
        Edmunds_matched_bodyid_file_raw1.loc[:, 'BodyStyle'] = '';
        Edmunds_matched_bodyid_file_raw1.loc[:, 'Source'] = '';
        _body_styles = ['Sedan', 'Truck', 'Hatchback', 'Coupe', 'Convertible', 'SUV', 'Wagon', 'Minivan', 'Cargo Van', 'Ext Van', 'Van', 'Pickup', 'Crew Cab', 'Regular Cab', 'Double Cab', 'Extended Cab', 'SuperCab', 'King Cab', 'Quad Cab', 'Mega Cab', \
                        'SuperCrew', 'CrewMax', 'Access Cab']
        _powertrain_styles = ['electric DD', 'electric 2AM', 'fuel cell', 'hybrid', 'mild hybrid', 'plug-in']

        if edmunds_bodyid_to_edmunds_bodyid_match:
            Edmunds_matched_bodyid_file_base = pd.read_csv(run_input_path + '\\' + 'edmunds-bodyid_197eea9a_20230913.csv')
            if footprint_lineageid_to_edmunds_lineageid_match == True:
                footprint_lineageid_file_raw = pd.read_csv(run_input_path + '\\' + lineageid_filename)
                footprint_lineageid_flag = True
                Edmunds_matched_bodyid_file_raw1 = check_footprint_lineageIDs(Edmunds_matched_bodyid_file_raw1, footprint_lineageid_file_raw, footprint_lineageid_flag, year, 'LineageID',
                                                                              run_input_path, date_and_time)

                _idx_null_lineageIDs = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['LineageID'] == -9, :].index
                _makers_null = Edmunds_matched_bodyid_file_raw1.loc[_idx_null_lineageIDs, 'Make'].unique()
                _models_null = Edmunds_matched_bodyid_file_raw1.loc[_idx_null_lineageIDs, 'Model'].unique()
                _lineagdID = footprint_lineageid_file_raw['LineageID'].max()
                for i in range(len(_models_null)):
                    _idx = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _models_null[i]) & (Edmunds_matched_bodyid_file_raw1['LineageID'] == -9), 'LineageID'].index
                    _lineagdID += 1
                    Edmunds_matched_bodyid_file_raw1.loc[_idx, 'LineageID'] = _lineagdID
            Edmunds_matched_bodyid_file_raw1.to_csv(run_input_path + '\\' + 'footprint3-edmunds-bodyid-MY' + str(year) + '-' + date_and_time + '.csv', index=False)

            Edmunds_matched_bodyid_file_base = Edmunds_matched_bodyid_file_base.loc[Edmunds_matched_bodyid_file_base['ModelYear'] == 2019, :].reset_index(drop=True)

            _idx_spaces = Edmunds_matched_bodyid_file_base.loc[Edmunds_matched_bodyid_file_base['Model'].str.contains(' '), :].index
            if len(_idx_spaces) > 0:
                Edmunds_matched_bodyid_file_base.loc[_idx_spaces, 'Model'] = Edmunds_matched_bodyid_file_base.loc[_idx_spaces, 'Model'].str.replace(" ", "-")

            _models = Edmunds_matched_bodyid_file_raw1['Model'].unique()
            for i in range(len(_models)):
                _model = _models[i]
                _trims = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['Model'] == _model, 'Trims'].unique()
                for j in range(len(_trims)):
                    _trim = _trims[j]
                    # if _trim == 'Sport Hybrid SH-AWD 4dr Sedan AWD w/Technology Package (3.5L 6cyl gas/electric hybrid 7AM)':
                        # print(_model)_model
                    _idx_base = Edmunds_matched_bodyid_file_base.loc[(Edmunds_matched_bodyid_file_base['Model'] == _model) & (Edmunds_matched_bodyid_file_base['Trims'] == _trim), :].index
                    if len(_idx_base > 0):
                        Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['Trims'] == _trim), 'BodyID'] = Edmunds_matched_bodyid_file_base.loc[_idx_base[0], 'BodyID']
                        # Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['Trims'] == _trim), 'LineageID'] = Edmunds_matched_bodyid_file_base.loc[_idx_base[0], 'LineageID']

            _models = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['BodyID'] == -9 , 'Model'].unique()
            for i in range(len(_models)):
                _model = _models[i]
                _idx_nulls = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyID'] == -9), :].index
                # if 30 in _idx_nulls:
                #     print(_idx_nulls)
                _idx_lineageid = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyID'] != -9), :].index
                if len(_idx_lineageid) == 0: continue
                _bodyids = Edmunds_matched_bodyid_file_raw1.loc[_idx_lineageid, 'BodyID'].unique()
                if (len(_bodyids) == 1):
                    Edmunds_matched_bodyid_file_raw1.loc[_idx_nulls, 'BodyID'] = _bodyids[0]
                    # Edmunds_matched_bodyid_file_raw1.loc[_idx_nulls, 'LineageID'] = Edmunds_matched_bodyid_file_raw1.loc[_idx_lineageid[0], 'LineageID']
                else:
                    for j in range(len(_bodyids)):
                        _bodyid = _bodyids[j]
                        _wheelbases =  Edmunds_matched_bodyid_file_base.loc[(Edmunds_matched_bodyid_file_base['Model'] == _model) & (Edmunds_matched_bodyid_file_base['BodyID'] == _bodyid), 'WHEELBASE'].unique()
                        for k in range(len(_wheelbases)):
                            _idx_base = Edmunds_matched_bodyid_file_base.loc[(Edmunds_matched_bodyid_file_base['Model'] == _model) & (Edmunds_matched_bodyid_file_base['BodyID'] == _bodyid) &
                            (Edmunds_matched_bodyid_file_base['WHEELBASE'] == _wheelbases[k]), :].index

                            Edmunds_matched_bodyid_file_raw1.loc[(_idx_nulls) & (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == _wheelbases[k]), 'BodyID'] = Edmunds_matched_bodyid_file_base.loc[_idx_base[0], 'BodyID']
                            # Edmunds_matched_bodyid_file_raw1.loc[(_idx_nulls) & (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == _wheelbases[k]), 'LineageID'] = Edmunds_matched_bodyid_file_base.loc[_idx_base[0], 'LineageID']

            # Edmunds_matched_bodyid_file_raw1.to_csv(run_input_path + '\\' + matched_bodyid_filename.split('.csv')[0] + '-MY' + str(year) + '.csv', index=False)

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
                if (isinstance(df_tmp.loc[ik, 'WHEELBASE'], str) == True) and (df_tmp.loc[ik, 'WHEELBASE'] != str(np.nan)):
                    _wheelbase_tmp = float(df_tmp.loc[ik, 'WHEELBASE'].split(' ')[0])
                else:
                    _wheelbase_tmp = ''
                if (isinstance(df_tmp.loc[ik, 'LENGTH'], str) == True) and (df_tmp.loc[ik, 'LENGTH'] != str(np.nan)):
                    _length_tmp = float(df_tmp.loc[ik, 'LENGTH'].split(' ')[0]);
                else:
                    _length_tmp = ''
                if (isinstance(df_tmp.loc[ik, 'HEIGHT'], str) == True) and (df_tmp.loc[ik, 'HEIGHT'] != str(np.nan)):
                    _height_tmp = float(df_tmp.loc[ik, 'HEIGHT'].split(' ')[0]);
                else:
                    _height_tmp = ''

                if _wheelbase_tmp not in _wheelbase_df_tmp:
                    _wheelbase_df_tmp.append(_wheelbase_tmp);
                    _height_df_tmp.append(_height_tmp);
                    _length_df_tmp.append(_length_tmp);
            df_wheelbase = pd.DataFrame({'HEIGHT': _height_df_tmp, 'LENGTH': _length_df_tmp, 'WHEELBASE': _wheelbase_df_tmp});

            _body_styles = df_tmp.loc[df_tmp['Model'] == _model_org, 'BodyStyle'].unique();
            for j in range (len(_body_styles)):
                _body_style = _body_styles[j];
                df_base = Edmunds_matched_bodyid_file_raw0.loc[(Edmunds_matched_bodyid_file_raw0['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw0['BodyStyle'] == _body_style), :].reset_index(drop=True)

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
                    # Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'LineageID'] = df_base.loc[0, 'LineageID'];

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
                            # Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model_org) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                            #                                              (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == str(_wheelbase_df_tmp[m2]) + ' in.'), 'LineageID'] = df_base1.loc[l2, 'LineageID'];

                    del _wheelbase_df_base1;
            if len(_wheelbase_df_tmp) > 0: del _wheelbase_df_tmp;

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
                    # Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'LineageID'] = df_base['LineageID'][0];
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style), 'Matching'] = 1;
                else:
                    _wheelbases = df_base['WHEELBASE'].unique();
                    _k_matching = 0
                    _min_diff = 1000;
                    for k in range(len(_wheelbases)):
                        if (isinstance(df_base.loc[k, 'WHEELBASE'], float)) or (df_base.loc[k, 'WHEELBASE'] == str(np.nan)): continue
                        _wheelbases_k = float(df_base.loc[k, 'WHEELBASE'].split(' ')[0])
                        if (abs(_wheelbase - _wheelbases_k) < _min_diff):
                            _k_matching = k;
                            break;

                    _bodyID = df_base.loc[df_base['WHEELBASE'] == _wheelbases[_k_matching], 'BodyID'][0];
                    # _lineageID = df_base.loc[df_base['WHEELBASE'] == _wheelbases[_k_matching], 'LineageID'][0];
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                            (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == df_tmp.loc[j, 'WHEELBASE']), 'BodyID'] = _bodyID;
                    # Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                    #         (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == df_tmp.loc[j, 'WHEELBASE']), 'LineageID'] = _lineageID;
                    Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _model) & (Edmunds_matched_bodyid_file_raw1['BodyStyle'] == _body_style) & \
                        (Edmunds_matched_bodyid_file_raw1['WHEELBASE'] == df_tmp.loc[j, 'WHEELBASE']), 'Matching'] = 2;

    _makers = pd.DataFrame(Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['BodyID'] == -9), 'Make'].unique().tolist(), columns=['Make']).sort_values(by=['Make']).reset_index(drop=True)
    for kk in range(len(_makers)):
        _models = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Make'] == _makers.loc[kk, 'Make']) & (Edmunds_matched_bodyid_file_raw1['BodyID'] == -9), 'Model'].unique()
        for i in range(len(_models)):
            # if (_models[i] == 'F-250-SUPER-DUTY'): #   or (_models[i] == 'COLORADO'):
            #     print(_models[i])
            _model_splitted = _models[i].split('-')
            _model = _model_splitted[0]
            if (len(_model_splitted) > 1):
                if ((_model == 'F') and ((_model_splitted[1] != 'PACE') and (_model_splitted[1] != 'TYPE')))  or (_model == 'SILVERADO') or (_model == 'SIERRA') or (_model == 'MODEL') or \
                    (_models[i] == 'C-HR') or (_models[i] == 'CR-V') or (_models[i] == 'F-PACE') or (_models[i] == 'F-TYPE') or (_model_splitted[1] == 'SERIES') or (_model == 'RS') \
                        or (_model == 'SANTA')  or (_model == 'GRAND') or (_model == 'ES') or (_model == 'MX') or (_model == 'CX') or (_model == 'GR') or (_model_splitted[1] == 'CLASS'):
                    _model = _model_splitted[0] + '-' + _model_splitted[1]

            _trims = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _models[i]) & (Edmunds_matched_bodyid_file_raw1['BodyID'] == -9), 'Trims']
            _index = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _models[i]) & (Edmunds_matched_bodyid_file_raw1['BodyID'] == -9), 'Trims'].index
            for j in range(len(_index)):
                _drivetrain = ''
                _doorstyle = ''
                _roofstyle = ''
                _vanstyle = ''
                _make = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Make']
                _trim = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Trims']
                _wheelbase = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'WHEELBASE']
                _bodystyle = Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyStyle']
                _trim_splitted = _trim.split(' ')
                for kk in range(len(_trim_splitted)):
                    if 'dr' in _trim_splitted[kk]: _doorstyle = _trim_splitted[kk]
                    if 'WD' in _trim_splitted[kk]: _drivetrain = _trim_splitted[kk]
                    if 'Roof' in _trim_splitted[kk]: _roofstyle = _trim_splitted[kk-1] + ' ' + _trim_splitted[kk]

                    if ('Van' in _trim_splitted[kk]) and (_bodystyle == "Van"):
                        _vanstyle = _trim_splitted[kk]
                        if (_trim_splitted[kk-1] == "Ext"): _vanstyle = _bodystyle = "Ext Van"
                        if (_trim_splitted[kk-1] == "Cargo"): _vanstyle = _bodystyle = "Cargo Van"
                        if (_trim_splitted[kk-1] == "Passenger"): _vanstyle = _bodystyle = "Passenger Van"

                _trim0 = _trim_splitted[0]
                _idx = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw['Model'].str.contains((_model), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Make'].str.contains((_make), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_trim0), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_drivetrain), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_doorstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_roofstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_vanstyle), case=False, na=False)) &
                                                           (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_bodystyle), case=False, na=False)) & (Edmunds_matched_bodyid_file_raw['BodyID'] != -9), :].index
                if len(_idx) > 0:
                    _yr = Edmunds_matched_bodyid_file_raw.loc[_idx, 'ModelYear'].max()
                    _bodyids = Edmunds_matched_bodyid_file_raw.loc[(Edmunds_matched_bodyid_file_raw['Model'].str.contains((_model), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Make'].str.contains((_make), case=False,na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_trim0), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_drivetrain), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_doorstyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_roofstyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_vanstyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['Trims'].str.contains((_bodystyle), case=False, na=False)) &
                                                                   (Edmunds_matched_bodyid_file_raw['ModelYear'] == _yr) & (Edmunds_matched_bodyid_file_raw['BodyID'] != -9), :]

                    if len(_bodyids) == 1:
                        Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyID'] = _bodyids.loc[_bodyids.index[0], 'BodyID']
                        # Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'LineageID'] = _bodyids.loc[_bodyids.index[0], 'LineageID']
                        Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Matching'] = 3
                        Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'] = str(_bodyids.loc[_bodyids.index[0], 'ModelYear']) + ', ' + _models[i] + ', ' + _trim
                        # print(_trim, Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'])
                    else:
                        _idx_wheelbase_matched_yr = 0
                        _wheelbase_diff = 999*np.ones(len(_bodyids))
                        for k in range(len(_bodyids)):
                            _wheelbase_yr = _bodyids.loc[_bodyids.index[k], 'WHEELBASE']
                            _wheelbase_diff[k] = abs(float(_wheelbase.split(' ')[0]) - float(_wheelbase_yr.split(' ')[0]))
                            if (_wheelbase == _wheelbase_yr) or (_wheelbase_diff[k] <= 0.1):
                                _idx_wheelbase_matched_yr = _bodyids.index[k]
                                break;
                        if _idx_wheelbase_matched_yr != 0:
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyID'] = _bodyids.loc[_idx_wheelbase_matched_yr, 'BodyID']
                            # Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'LineageID'] = _bodyids.loc[_idx_wheelbase_matched_yr, 'LineageID']
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Matching'] = 3
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'] = str(_bodyids.loc[_idx_wheelbase_matched_yr, 'ModelYear']) + ', ' + _models[i] + ', ' + _trim
                            # print(_trim, Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'])
                        else:
                            _idx_wheelbase_diff_min = 0
                            _wheelbase_diff_min = 999
                            for kk in range(len(_wheelbase_diff)):
                                if _wheelbase_diff[kk] < _wheelbase_diff_min:
                                    _wheelbase_diff_min = _wheelbase_diff[kk]
                                    _idx_wheelbase_diff_min = kk
                                    break
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'BodyID'] = _bodyids.loc[_bodyids.index[_idx_wheelbase_diff_min], 'BodyID']
                            # Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'LineageID'] = _bodyids.loc[_bodyids.index[_idx_wheelbase_diff_min], 'LineageID']
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Matching'] = 4
                            Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'] = str(_bodyids.loc[_bodyids.index[_idx_wheelbase_diff_min], 'ModelYear']) + ', ' + _models[i] + ', ' + _trim
                            # print(_trim, Edmunds_matched_bodyid_file_raw1.loc[_index[j], 'Source'])

    _idx_null_bodyIDs = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['BodyID'] == -9, :].index
    _makers_null = Edmunds_matched_bodyid_file_raw1.loc[_idx_null_bodyIDs, 'Make'].unique()
    _models_null = Edmunds_matched_bodyid_file_raw1.loc[_idx_null_bodyIDs, 'Model'].unique()
    _bodyID = Edmunds_matched_bodyid_file_raw1['BodyID'].max()
    for i in range(len(_models_null)):
        _idx = Edmunds_matched_bodyid_file_raw1.loc[(Edmunds_matched_bodyid_file_raw1['Model'] == _models_null[i]) &
                                                            (Edmunds_matched_bodyid_file_raw1['BodyID'] == -9), 'BodyID'].index
        _bodyID += 1
        Edmunds_matched_bodyid_file_raw1.loc[_idx, 'BodyID'] = _bodyID

    _idx_MY_drop = Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['ModelYear'] == year, 'ModelYear'].index
    Edmunds_matched_bodyid_file_raw = Edmunds_matched_bodyid_file_raw.drop(index=_idx_MY_drop).reset_index(drop=True)
    _columns_edmunds_bodyIDs = ['ModelYear', 'Make', 'Model', 'Trims', 'HEIGHT', 'LENGTH', 'WHEELBASE', 'BodyID', 'LineageID']
    Edmunds_matched_bodyid_file_raw = pd.concat([Edmunds_matched_bodyid_file_raw, Edmunds_matched_bodyid_file_raw1[_columns_edmunds_bodyIDs]], axis=0, ignore_index=True)
    Edmunds_matched_bodyid_file_raw.sort_values(by=['ModelYear'], ascending=True, inplace=True)
    Edmunds_matched_bodyid_file_raw['Model'] = Edmunds_matched_bodyid_file_raw['Model'].apply(str.upper)
    Edmunds_matched_bodyid_file_raw1['Model'] = Edmunds_matched_bodyid_file_raw1['Model'].apply(str.upper)

    # date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    print('input_path: ', run_input_path)
    Edmunds_matched_bodyid_file_raw1.to_csv(run_input_path + '\\' + 'edmunds-bodyid-MY' + str(year) + '-' + date_and_time + '.csv', index=False)
    Edmunds_matched_bodyid_file_raw.to_csv(run_input_path + '\\' + matched_bodyid_filename.split('.csv')[0] + date_and_time + '.csv', index=False)
    # run_input_path + '\\' + matched_bodyid_filename.split('.csv')[0] + '-MY' + str(year) + '.csv', index = False)
    # null_BodyID_models  = Edmunds_matched_bodyid_file_raw1.loc[Edmunds_matched_bodyid_file_raw1['BodyID'] == -9, :]
    # if len(null_BodyID_models) > 0:
    #     null_BodyID_models = null_BodyID_models.drop_duplicates(subset=['Model']);
    #     null_BodyID_models = null_BodyID_models.drop(['Powertrains', 'Matching'], axis=1).reset_index(drop=True)
    #     null_BodyID_models.to_csv(run_input_path + '\\' + 'Null-BodyIDs-MY' + str(year) + '_' + date_and_time + '.csv', index=False)

    return Edmunds_matched_bodyid_file_raw1;
def Edmunds_Readin(rawdata_input_path, run_input_path, input_filename, output_path, exceptions_table, \
                   bodyid_filename, matched_bodyid_filename, unit_table, year, \
                   ftp_drivecycle_filename, hwfet_drivecycle_filename, ratedhp_filename, lineageid_filename, skiprows_vec):
    raw_Edmunds_data = pd.read_csv(rawdata_input_path+'\\'+input_filename, dtype=object, encoding="ISO-8859-1")
    Edmunds_Data = raw_Edmunds_data;
    if ('RANGE IN MILES (CTY/HWY)' not in Edmunds_Data.columns) and ('RANGE IN MILES (CITY/HWY)' in Edmunds_Data.columns):
        Edmunds_Data.rename(columns={'RANGE IN MILES (CITY/HWY)': 'RANGE IN MILES (CTY/HWY)'}, inplace=True)
    Edmunds_Data.loc[(Edmunds_Data['BASE ENGINE TYPE'].str.lower() == 'electric') & (Edmunds_Data['RANGE IN MILES (CTY/HWY)'].astype(str) != 'nan'), 'RANGE IN MILES (CTY/HWY)'] = '0/0 mi.'

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

    Edmunds_matched_bodyid_file_raw = pd.read_csv(run_input_path + '\\' + matched_bodyid_filename)
    Edmunds_matched_bodyid_file_raw.dropna(subset=['ModelYear', 'Make'], how='any', inplace=True)
    Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['LineageID'].astype(str) == str(np.nan), 'LineageID'] = -9
    Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['BodyID'].astype(str) == str(np.nan), 'BodyID'] = -9
    Edmunds_matched_bodyid_file_raw.loc[Edmunds_matched_bodyid_file_raw['BodyID'].astype(str) == str(np.nan), 'BodyID'] = -9
    Edmunds_matched_bodyid_file_raw['BodyID'] = Edmunds_matched_bodyid_file_raw['BodyID'].astype(int)
    Edmunds_matched_bodyid_file_raw['ModelYear'] = Edmunds_matched_bodyid_file_raw['ModelYear'].astype(int)
    Edmunds_matched_bodyid_file_raw['Model'] = Edmunds_matched_bodyid_file_raw['Model'].astype(str)

    if _body_style_check == True:
        Edmunds_matched_bodyid_file_raw = body_id_checks(Edmunds_Data, Edmunds_matched_bodyid_file_raw, year, 2019, rawdata_input_path, run_input_path, matched_bodyid_filename, lineageid_filename);

    Edmunds_matched_bodyid_file_notnone = Edmunds_matched_bodyid_file_raw[Edmunds_matched_bodyid_file_raw['LineageID'] != -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_none = Edmunds_matched_bodyid_file_raw[Edmunds_matched_bodyid_file_raw['LineageID'] == -9].reset_index(drop=True)
    Edmunds_matched_bodyid_file_single = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] != -9].reset_index(drop=True);
    Edmunds_matched_bodyid_file_many = Edmunds_matched_bodyid_file_notnone[Edmunds_matched_bodyid_file_notnone['BodyID'] == -9] \
        .drop('BodyID',axis=1).merge(body_id_table[['LineageID', 'BodyID']], how='left', on = 'LineageID').reset_index(drop=True)
    Edmunds_matched_bodyid = pd.concat([Edmunds_matched_bodyid_file_single, Edmunds_matched_bodyid_file_many, Edmunds_matched_bodyid_file_none]).reset_index(drop=True)
    # if year < 2019:
    #     Edmunds_matched_bodyid['Model'] = Edmunds_matched_bodyid['Model'].str.upper();
    #     l_str = [' SEDAN', ' SUV', ' WAGON', ' CONVERTIBLE', ' COUPE', ' HATCHBACK', ' DIESEL', ' HYBRID', ' MINIVAN'];
    #     Edmunds_matched_bodyid['Model'] = Edmunds_matched_bodyid['Model'].str.replace('|'.join(l_str), '', regex=True).str.strip();
        # Edmunds_data_cleaned = Edmunds_Data.merge(Edmunds_matched_bodyid[['Make', 'Trims', 'LineageID', 'BodyID']], how='left', on=['Make', 'Trims']).reset_index(drop=True);
    Edmunds_data_cleaned = Edmunds_Data.merge(Edmunds_matched_bodyid[['Model', 'Trims', 'LineageID', 'BodyID']], how='left', on = ['Model', 'Trims']).reset_index(drop=True)
    # Edmunds_data_cleaned = Edmunds_data_cleaned.merge(Edmunds_matched_bodyid[['Make', 'Model', 'Trims', 'LineageID', 'BodyID']], how='left', on = ['Make', 'Model']).reset_index(drop=True)
    if ('Trims_y' in Edmunds_data_cleaned.columns):
        Edmunds_data_cleaned.drop(['Trims_y'], axis=1, inplace=True)
        Edmunds_data_cleaned.rename({'Trims_x': 'Trims'}, axis=1, inplace=True)
    if ('BodyID_x' in Edmunds_data_cleaned.columns):
        Edmunds_data_cleaned.drop(['BodyID_x'], axis=1, inplace=True)
        Edmunds_data_cleaned.rename({'BodyID_y': 'BodyID'}, axis=1, inplace=True)
    if ('LineageID_x' in Edmunds_data_cleaned.columns):
        Edmunds_data_cleaned.drop(['LineageID_x'], axis=1, inplace=True)
        Edmunds_data_cleaned.rename({'LineageID_y':'LineageID'}, axis=1, inplace=True)
    Edmunds_data_cleaned['BodyID'] = Edmunds_data_cleaned['BodyID'].replace(np.nan, 0).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].replace(np.nan, 0).astype(int)
    Edmunds_data_cleaned['LineageID'] = Edmunds_data_cleaned['LineageID'].replace(np.nan, 0)

    _idx_blanks = Edmunds_matched_bodyid.loc[Edmunds_matched_bodyid['Model'].str.contains(' '), :].index
    _extra_str = ['-VAN', '-WAGON', '-CONVERTIBLE']
    if (len(_idx_blanks) > 0):
        for i in range(len(_extra_str)):
            Edmunds_data_cleaned.loc[Edmunds_data_cleaned['Model'].str.contains(_extra_str[i]), 'Model'].str.replace(_extra_str[i], '')
        # else:
        #     Edmunds_data_cleaned.loc[Edmunds_data_cleaned['Model'].str.contains_extra_str[i]), 'Model'].str.replace(
        #         _extra_str[i], '')
    # Edmunds_data_cleaned['Model'].str.replace('-', ' ')
    _models_null = Edmunds_data_cleaned.loc[(Edmunds_data_cleaned['LineageID'] == 0), 'Model'].unique()

    for i in range(len(_models_null)):
        _model_null = _models_null[i]
        _model0_null = _model_null.split(' ')[0]
        _idx = Edmunds_matched_bodyid.loc[(Edmunds_matched_bodyid['Model'] == _model_null) & (Edmunds_matched_bodyid['LineageID'] != -9), :].index
        _idx_null = Edmunds_data_cleaned.loc[(Edmunds_data_cleaned['Model'] == _model_null) & (Edmunds_data_cleaned['LineageID'] == 0), :].index
        # if (len(_idx_null) > 0) and (len(_idx) == 0):
        #     _idx = Edmunds_matched_bodyid.loc[(Edmunds_matched_bodyid['Model'].str.contains((_model_null[0]), case=False, na=False)) & (Edmunds_matched_bodyid['LineageID'] != -9), :].index
        if (len(_idx) > 0) and (len(_idx_null) > 0):
            Edmunds_data_cleaned.loc[_idx_null, 'LineageID'] = Edmunds_matched_bodyid.loc[_idx[0], 'LineageID']
            Edmunds_data_cleaned.loc[_idx_null, 'BodyID'] = Edmunds_matched_bodyid.loc[_idx[0], 'BodyID']

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
        try:
            Edmunds_data_cleaned[hr_unit_columns[i]] = Edmunds_data_cleaned[hr_unit_columns[i]].replace(np.nan, '').str.replace(' hr.', '').str.replace('no', '')
        except KeyError:
            print(Edmunds_data_cleaned[hr_unit_columns[i]])
            continue

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

    # Edmunds_data_cleaned[~Edmunds_data_cleaned['DRIVE TYPE'].str.contains(('wheel drive'), case=False, na=False)] = 'Front wheel drive'
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
    try:
        electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) != '0/0 mi.')] = 'HEV'
    except KeyError:
        print(Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'])
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) == 'false (electric)')] = 'PHEV'
    electrification_category[(Edmunds_data_cleaned['BASE ENGINE TYPE'].str.lower() == 'hybrid') & (Edmunds_data_cleaned['RANGE IN MILES (CTY/HWY)'].astype(str) == '0/0 mi.') ] = 'PHEV'
    electrification_category[Edmunds_data_cleaned['Trims'].str.contains('plug-in')] = 'PHEV'
    electrification_category[Edmunds_data_cleaned['Trims'].str.contains('fuel cell')] = 'FCV'

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
    _column_insert_pos = len(Edmunds_Final_Output.columns);
    for i in range(len(cols_safety)):
        if (cols_safety[i] not in Edmunds_Final_Output.columns):
            Edmunds_Final_Output.insert(_column_insert_pos, cols_safety[i], '')
            _column_insert_pos += 1
    if ('OVERALL WIDTH WITHOUT MIRRORS' in Edmunds_Final_Output.columns) and ('WIDTH' not in Edmunds_Final_Output.columns):
        # Edmunds_Final_Output.rename(columns={'OVERALL WIDTH WITHOUT MIRRORS': 'WIDTH'})
        Edmunds_Final_Output['WIDTH'] = Edmunds_Final_Output['OVERALL WIDTH WITHOUT MIRRORS'].copy()
    Edmunds_Final_Output = Edmunds_Final_Output.loc[:, ~Edmunds_Final_Output.columns.duplicated()]
    Edmunds_Final_Output = Edmunds_Final_Output.drop_duplicates().reset_index()

    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    print('output_path: ', output_path)
    Edmunds_Final_Output.to_csv(output_path+'\\'+'Edmunds Readin'+'_ '+'MY'+str(year)+' '+date_and_time+'.csv', index=False)