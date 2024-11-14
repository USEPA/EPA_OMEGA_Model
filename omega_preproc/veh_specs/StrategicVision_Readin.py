import pandas as pd
import numpy as np
import datetime

def StrategicVision_Readin(rawdata_input_path, run_input_path, input_filename, output_path, \
                        exceptions_table, bodyid_filename, matched_bodyid_filename, unit_change_table, \
                         year, ratedhp_filename, ftp_drivecycle_filename, hwfet_drivecycle_filename, lineageid_filename):

    raw_sv_file = pd.read_csv(rawdata_input_path+'\\'+input_filename)
    sv_modelyear = raw_sv_file[raw_sv_file['model_year'] == year].reset_index(drop=True)
    try:
        raw_sv_bodyid = pd.read_csv(rawdata_input_path+'\\'+matched_bodyid_filename, \
        converters = {'model_year':int, 'LineageID':int, 'BodyID':int, 'BodyID StartYear':int})
    except FileNotFoundError:
        raw_sv_lineageid = pd.read_csv(rawdata_input_path+'\\'+lineageid_filename, converters = \
            {'model_year':int, 'LineageID':int})
        raw_bodyid_table = pd.read_excel(run_input_path+'\\'+bodyid_filename)
        sv_lineageid = raw_sv_lineageid[(raw_sv_lineageid['model_year'] == year) & \
                                        (raw_sv_lineageid['LineageID'] != -9)].reset_index(drop=True)

        bodyid_table = raw_bodyid_table[(raw_bodyid_table['BodyID StartYear'] <= year) & \
                                        (raw_bodyid_table['BodyID EndYear'].astype(str) != 'xx')].reset_index(drop=True)
        bodyid_table_a = bodyid_table[~(bodyid_table['BodyID EndYear'].astype(str).str.contains('null'))].reset_index(drop=True)
        bodyid_table_a = bodyid_table_a[(bodyid_table_a['BodyID EndYear'].astype(int) >= year)].reset_index(drop=True)
        bodyid_table_b = bodyid_table[bodyid_table['BodyID EndYear'].astype(str) == 'null'].reset_index(drop=True)
        bodyid_table = pd.concat([bodyid_table_a, bodyid_table_b]).reset_index(drop=True)

        sv_bodyid = pd.merge_ordered(sv_lineageid, bodyid_table[['LineageID', 'BodyID', 'BodyID StartYear', 'BodyID EndYear', 'ref_Make', 'ref_Model', \
            'BodyDescription']], how='left', on='LineageID').reset_index(drop=True)
        try:
            sv_bodyid_int = pd.read_csv(output_path+'\\'+'StrategicVision_trimmissing_BodyID_int.csv')
            sv_bodyid = pd.merge_ordered(sv_bodyid, sv_bodyid_int[['trim_id_m', 'BodyID', 'USE_YN']], how='left', on=['trim_id_m', 'BodyID']).reset_index(drop=True)
        except FileNotFoundError:
            pass
        sv_bodyid.to_csv(output_path+'\\'+ 'MY' + str(year )+ '_StrategicVision_BodyID.csv',index=False)
    else:
        try:
            raw_sv_file['trim_id']
        except KeyError:
            trimid_key = 'trim_id_m'
        else:
            trimid_key = 'trim_id'
        sv_bodyid_modelyear = raw_sv_bodyid[(raw_sv_bodyid['model_year']==year) & (raw_sv_bodyid['USE_YN']=='y')].reset_index(drop=True)
        sv_output = pd.merge_ordered(sv_modelyear, sv_bodyid_modelyear[[trimid_key, 'LineageID', 'BodyID']], how='left', on=trimid_key).reset_index(drop=True)
        sv_output = sv_output[~pd.isnull(sv_output['LineageID'])].reset_index(drop=True)

        sv_output_nonflexfuel = sv_output[sv_output['fuel_type'] != 'flexible'].reset_index(drop=True)
        sv_output_flexfuel_gas = sv_output[sv_output['fuel_type'] == 'flexible'].reset_index(drop=True)
        sv_output_flexfuel_ethanol = sv_output[sv_output['fuel_type'] == 'flexible'].reset_index(drop=True)

        sv_output_flexfuel_gas['fuel_type'][sv_output_flexfuel_gas['fuel_type'] == 'flexible'] = 'gas'
        sv_output_flexfuel_ethanol['fuel_type'][sv_output_flexfuel_ethanol['fuel_type'] == 'flexible'] = 'ethanol'
        sv_output = pd.concat([sv_output_nonflexfuel, sv_output_flexfuel_gas, sv_output_flexfuel_ethanol])\
            .sort_values([trimid_key, 'fuel_type']).reset_index(drop=True)

        fuel_type = pd.Series(np.zeros(len(sv_output)), name = 'Fuel Type Category').replace(0,'G')
        fuel_type[sv_output['fuel_type']=='ethanol'] = 'Eth'
        fuel_type[sv_output['fuel_type'] == 'diesel'] = 'D'
        fuel_type[sv_output['fuel_type'].astype(str).str.contains('battery')] = 'E'
        fuel_type[sv_output['fuel_type'].astype(str).str.contains('hybrid')] = 'G'

        drv_sys = pd.Series(np.zeros(len(sv_output)), name = 'Drivetrain Layout Category').replace(0,'')
        drv_sys[sv_output['drive_type'] == 'RWD'] = '2WD'
        drv_sys[sv_output['drive_type'] == 'FWD'] = '2WD'
        drv_sys[sv_output['drive_type'] == 'AWD'] = '4WD'
        drv_sys[sv_output['drive_type'] == '4WD'] = '4WD'

        electrification_category = pd.Series(np.zeros(len(sv_output)), name = 'Electrification Category').replace(0,'N')
        electrification_category[sv_output['fuel_type'] == 'hybrid'] = 'HEV'
        electrification_category[sv_output['fuel_type'] == 'plug-in hybrid'] = 'REEV'
        electrification_category[sv_output['fuel_type'].astype(str).str.contains('battery')] = 'EV'
        try:
            # eng_layout = pd.Series(np.zeros(len(sv_output)), name = 'Cylinder Layout Category').replace(0,'ELE')
            # eng_layout[sv_output['cylinder_configuration'].str.contains('Inline')] = 'I'
            # eng_layout[sv_output['cylinder_configuration'].str.contains('H Block')] = 'H'
            # eng_layout[sv_output['cylinder_configuration'].str.contains('V')] = 'V'

            # num_cyls = pd.Series(np.zeros(len(sv_output)), name = 'Number of Cylinders Category').replace(0,'ELE')
            # num_cyls[sv_output['cylinder_configuration'].str[0]=='V'] = sv_output['cylinder_configuration'][sv_output['cylinder_configuration'].str[0]=='V']\
            #     .replace('V','', regex=True).str.strip().astype(float).astype(int)
            # num_cyls[sv_output['cylinder_configuration'].str.contains('Cylinder')] = sv_output['cylinder_configuration'][sv_output['cylinder_configuration'].str.contains('Cylinder')]\
            #     .str[-2:].replace('\)','',regex=True).str.strip().astype(int)
            # num_cyls[num_cyls != 'ELE'] = num_cyls[num_cyls != 'ELE'].astype(int)

            num_cyls = pd.Series(np.zeros(len(sv_output)), name = 'Number of Cylinders Category').replace(0,np.nan)
            num_cyls[sv_output['fuel_type']=='battery electric'] = 'ELE'
            num_cyls[sv_output['engine_cyl'].astype(str).str.contains('cylinder')] = \
                sv_output['engine_cyl'][sv_output['engine_cyl'].astype(str).str.contains('cylinder')].str.extract(
                '(\d+)')
            num_cyls[(num_cyls != 'ELE')&(~pd.isnull(num_cyls))]=num_cyls[(num_cyls != 'ELE')&(~pd.isnull(num_cyls))].astype(int)

            eng_disp = pd.Series(np.zeros(len(sv_output)), name = 'Engine Displacement Category')
            eng_disp[sv_output['engine_displacement'].astype(str).str.contains('Liter')] = \
                sv_output['engine_displacement'][sv_output['engine_displacement'].astype(str).str.contains('Liter')]\
                    .str[0:3].astype(float).round(1)

            num_gears = pd.Series(np.zeros(len(sv_output)), name = 'Number of Transmission Gears Category').replace(0,np.nan)
            num_gears[sv_output['transmission'].str.contains(' Speed')] = (sv_output['transmission'][sv_output['transmission'].str.contains(' Speed')].str[0])
            num_gears[sv_output['transmission'].str.contains('Continuous')] = 1
            num_gears[~pd.isnull(num_gears)] = num_gears[~pd.isnull(num_gears)].astype(int)

            trns_type = pd.Series(np.zeros(len(sv_output)), name = 'Transmission Type Category').replace(0,'A')
            trns_type[sv_output['transmission'].str.contains('Manual')] = 'M'
            trns_type[sv_output['transmission'].str.contains('With')] = 'AM'
            trns_type[sv_output['transmission'].str.contains('Continuously')] = '1ST'
            trns_type[num_gears==1] = '1ST'

            boost_type = pd.Series(np.zeros(len(sv_output)), name = 'Boost Type Category').replace(0,'N')
            boost_type[sv_output['compressor'].str.lower().str.contains('turbo')] = 'TC'
            boost_type[sv_output['compressor'].str.lower().str.contains('supercharger')] = 'SC'
            boost_type[(sv_output['compressor'].str.lower().str.contains('turbo'))\
                       &(sv_output['compressor'].str.lower().str.contains('supercharger'))] = 'TS'
            # sv_final_output = pd.concat(
            #     [pd.Series(range(len(sv_output)), name='SV_READIN_ID') + 1, sv_output, eng_layout, \
            #      num_cyls, eng_disp, drv_sys, trns_type, num_gears, boost_type, fuel_type, \
            #      electrification_category], axis=1).sort_values([trimid_key, 'fuel_type']).reset_index(drop=True)
            sv_final_output = pd.concat(
                [pd.Series(range(len(sv_output)), name='SV_READIN_ID') + 1, sv_output, \
                 num_cyls, eng_disp, drv_sys, trns_type, num_gears, boost_type, fuel_type, \
                 electrification_category], axis=1).sort_values([trimid_key, 'fuel_type']).reset_index(drop=True)

        except KeyError:
            sv_final_output = pd.concat(
                [pd.Series(range(len(sv_output)), name='SV_READIN_ID') + 1, sv_output, drv_sys, fuel_type, \
                 electrification_category], axis=1).sort_values([trimid_key, 'fuel_type']).reset_index(drop=True)


        sv_final_output['BodyID'] = sv_final_output['BodyID'].astype(int)
        sv_final_output['LineageID'] = sv_final_output['LineageID'].astype(int)
        sv_final_output.to_csv(output_path+'\\'+ 'MY' + str(year )+ '_StrategicVision_Readin.csv',index=False)
