import pandas as pd
import numpy as np
import datetime
from Unit_Conversion import in32l

def TrendsReadin_2008to2016(rawdata_input_path, run_input_path, input_filename, output_path, \
                        exceptions_table, bodyid_filename, matched_bodyid_filename, unit_change_table, \
                         year, ratedhp_filename, ftp_drivecycle_filename, hwfet_drivecycle_filename, lineageid_filename):
    raw_trends_file = pd.read_csv(rawdata_input_path + '\\' + input_filename, converters = {'Index':int})
    trends_file_modelyear = raw_trends_file[raw_trends_file['MODEL_YEAR']==year].reset_index(drop=True)

    trends_file_modelyear['TRANS_TYPE'] = trends_file_modelyear['Transmission'].astype(str).str[0].replace(['C', 'L'], ['CVT', 'A'])
    trends_file_modelyear['TOTAL_NUM_TRANS_GEARS'] = trends_file_modelyear['Transmission'].astype(str).str[1]
    trends_file_modelyear['TOTAL_NUM_TRANS_GEARS'] = trends_file_modelyear['TOTAL_NUM_TRANS_GEARS'].replace('V',1)
    trends_file_modelyear['TOTAL_NUM_TRANS_GEARS'] = trends_file_modelyear['TOTAL_NUM_TRANS_GEARS'].astype(float).astype(int)

    trends_file_modelyear['ENG_DISPL'] = pd.Series(np.zeros(len(trends_file_modelyear)))
    trends_file_modelyear['ENG_DISPL'][trends_file_modelyear['ECID'].astype(str) == 'NA'] = 'null'
    trends_file_modelyear['ENG_DISPL'][trends_file_modelyear['ECID'].astype(str) == str(np.nan)] = 'null'
    trends_file_modelyear['ENG_DISPL'][trends_file_modelyear['ECID'].astype(str) != 'NA'] = \
        (trends_file_modelyear['ECID'][trends_file_modelyear['ECID'].astype(str) != 'NA'].astype(float)*in32l).round(1)

    trends_file_modelyear['AIR_ASP_DESC'] = pd.Series(np.zeros(len(trends_file_modelyear))).replace(0,'Naturally Aspirated')
    trends_file_modelyear['AIR_ASP_DESC'][trends_file_modelyear['AIR_ASPIRATION_METH'] == 'TC'] = 'Turbocharged'
    trends_file_modelyear['AIR_ASP_DESC'][trends_file_modelyear['AIR_ASPIRATION_METH'] == 'SC'] = 'Supercharged'
    trends_file_modelyear['AIR_ASP_DESC'][trends_file_modelyear['AIR_ASPIRATION_METH'] == 'TS'] = 'Turbocharged + Supercharged'
    trends_file_modelyear['AIR_ASP_DESC'][trends_file_modelyear['FuelDelivery'] == 'Electric'] = 'null'

    trends_file_modelyear['FUEL_USAGE_GROUP']= trends_file_modelyear['PowerCategory'].str[0].replace(['F', 'H', 'P'], ['H', 'G', 'G'])

    trends_file_modelyear['OFF_BOARD_CHARGE_CAPABLE_YN'] = pd.Series(np.zeros(len(trends_file_modelyear))).replace(0,'N')
    trends_file_modelyear['OFF_BOARD_CHARGE_CAPABLE_YN'][trends_file_modelyear['PowerCategory'] == 'Electric'] = 'Y'
    trends_file_modelyear['OFF_BOARD_CHARGE_CAPABLE_YN'][trends_file_modelyear['PowerCategory'] == 'PHEV'] = 'Y'

    trends_file_modelyear = trends_file_modelyear\
        .rename(columns={'TrendsManf': 'CARLINE_MFR_NAME', 'NCYL': 'NUM_CYLINDRS_ROTORS', 'DRIVE_SYSTEM':'DRV_SYS', \
                         'CYLNDR_DEACTIVATION_YN': 'CYL_DEACT', 'HP':'ENG_RATED_HP'})
    raw_bodyid_file = pd.read_excel(run_input_path + '\\' + bodyid_filename,
                                    converters={'LineageID': int, 'BodyID': int})
    bodyid_file = raw_bodyid_file[raw_bodyid_file['BodyID EndYear'].astype(str) != 'xx'].reset_index(drop=True)
    bodyid_file['BodyID EndYear'] = bodyid_file['BodyID EndYear'].replace('null', 9999)
    bodyid_file = bodyid_file[
        (bodyid_file['BodyID StartYear'] <= year) & (bodyid_file['BodyID EndYear'] >= year)].reset_index(drop=True)
    bodyid_file['BodyID EndYear'] = bodyid_file['BodyID EndYear'].replace(9999, 'null')

    try:
        trends_file_modelyear_bodyid = pd.read_csv(rawdata_input_path+'\\'+matched_bodyid_filename)
        trends_file_bodyid_expanded = pd.merge_ordered(trends_file_modelyear, trends_file_modelyear_bodyid, how='left', \
        on=list(set(trends_file_modelyear_bodyid.columns)-(set(trends_file_modelyear_bodyid)-set(trends_file_modelyear.columns))))
        trends_file_bodyid_expanded = pd.merge_ordered(trends_file_bodyid_expanded, \
            bodyid_file[['BodyID']+list(set(bodyid_file.columns)-set(trends_file_bodyid_expanded.columns))], how='left', on='BodyID')
        trends_file_bodyid_expanded = trends_file_bodyid_expanded[trends_file_bodyid_expanded['USE_YN'] == 'y'].sort_values('Index').reset_index(drop=True)
        trends_file_bodyid_expanded['Distributed FEProd'] = pd.Series(\
            trends_file_bodyid_expanded['FEProd'] / trends_file_bodyid_expanded.groupby('Index')['FEProd'].transform(len))
        try:
            trends_file_bodyid_expanded = trends_file_bodyid_expanded.drop('FOOTPRINT_SUBCONFIG_VOLUMES',axis=1)
        except KeyError:
            pass
        trends_file_bodyid_expanded.to_csv(output_path+'\\'+str(year)+ '_TrendsReportReadin.csv', index=False)
    except FileNotFoundError:
        raise SystemExit()
        trends_file_lineageid = pd.read_csv(rawdata_input_path+'\\'+lineageid_filename, converters = {'LineageID':int})
        trends_file_bodyid_yn = pd.merge_ordered(pd.merge_ordered(\
            trends_file_modelyear, trends_file_lineageid[['Index', 'LineageID']], how='left', on='Index'), \
            bodyid_file[['LineageID', 'BodyID', 'ref_Model', 'BodyDescription']], how='left', on='LineageID')
        trends_file_bodyid_yn_output = trends_file_bodyid_yn[trends_file_bodyid_yn['LineageID'] != -9].drop_duplicates(['Index', 'BodyID'],keep='first').reset_index(drop=True)
        trends_file_bodyid_yn_output.to_csv(rawdata_input_path + '\\' +str(year)+ '_TrendsReportReadin_BodyID.csv', index=False)
        try:
            trends_file_bodyid_yn_compiled = pd.read_csv(rawdata_input_path+'\\' +'TrendsReportReadin_BodyID.csv', converters={'Index':int, 'LineageID':int})
            trends_file_bodyid_yn_compiled = pd.concat([trends_file_bodyid_yn_compiled, trends_file_bodyid_yn_output]).reset_index(drop=True)
            try:
                trends_file_bodyid_yn_compiled_int = pd.read_csv(rawdata_input_path+'\\'+'TrendsReportReadin_BodyID_int.csv', \
                    converters = {'Index':int,'LineageID':int, 'BodyID':int}).drop_duplicates(['Index', 'BodyID'],keep='first')
                trends_file_bodyid_yn_compiled_int.to_csv(rawdata_input_path+'\\'+'TrendsReportReadin_BodyID_int.csv', index=False)
                trends_file_bodyid_yn_compiled = trends_file_bodyid_yn_compiled.drop('USE_YN',axis=1)
                trends_file_bodyid_yn_compiled = pd.merge_ordered(trends_file_bodyid_yn_compiled, \
                    trends_file_bodyid_yn_compiled_int[['Index', 'BodyID', 'USE_YN']], how='left', on=['Index', 'BodyID'])\
                    .drop_duplicates(['Index', 'BodyID'],keep='first').reset_index(drop=True)
                trends_file_bodyid_yn_compiled[list(trends_file_bodyid_yn_compiled_int.columns)].to_csv(rawdata_input_path + '\\' + 'TrendsReportReadin_BodyID.csv',index=False)
            except FileNotFoundError:
                trends_file_bodyid_yn_compiled.to_csv(rawdata_input_path+'\\'+'TrendsReportReadin_BodyID.csv', index=False)
        except FileNotFoundError:
            trends_file_bodyid_yn_compiled = pd.concat([trends_file_bodyid_yn_output, \
                pd.Series(np.zeros(len(trends_file_bodyid_yn_output)), name = 'USE_YN').replace(0,np.nan)],axis=1)
            trends_file_bodyid_yn_compiled.to_csv(rawdata_input_path + '\\' + 'TrendsReportReadin_BodyID.csv',index=False)