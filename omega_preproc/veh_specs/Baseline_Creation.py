import pandas as pd
import numpy as np
import math
import datetime
from Unit_Conversion import mph2ftps, kgpm32slugpft3, in2mm, in2ft, n2lbf, in2m, mph2mps, hp2lbfmph
def Get_Percentiles(table, data_colname, weights_colname, percentile_colname):
    aggregated_data_raw = pd.concat([table[data_colname], table[weights_colname]],axis=1)
    aggregated_data_notnull = aggregated_data_raw[~pd.isnull(aggregated_data_raw[data_colname])].reset_index(drop=True)
    del aggregated_data_raw
    aggregated_data = aggregated_data_notnull.groupby(data_colname).sum().reset_index().sort_values(data_colname,ascending=True)
    del aggregated_data_notnull
    aggregated_data[percentile_colname] = pd.Series(np.zeros(len(aggregated_data)))
    weights_total = aggregated_data[weights_colname].sum()
    for percentile_count in range (1,len(aggregated_data)):
        aggregated_data[percentile_colname][percentile_count] = 100*aggregated_data[weights_colname][:1+percentile_count].sum()/weights_total
    table_with_percentiles = pd.merge_ordered(table, aggregated_data, how='left', on = data_colname)
    return table_with_percentiles
def weighed_average(grp):
    weighting_field = 'FOOTPRINT_SUBCONFIG_VOLUMES'
    return grp._get_numeric_data().multiply(grp[weighting_field], axis=0).sum()/((~pd.isnull(grp)).multiply(grp[weighting_field],axis=0).sum())

def Baseline_Creation(input_path, output_path, raw_data_filenames, footprint_plots, \
                     load_factor_plots, credit_integration, target_credit, credit_legend_category, credit_filenames, \
                     sales_weighted_bool, remove_scatter_bool, FTP_time, HWFET_time, color_array_filename, \
                      bool_max_peff, id_type, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                      aeroclass_table_filename, ALPHA_class_filename, OMEGA_index_filename, tire_dimension_filename, \
                      cd_grouping_category):
    try:
        raw_baseline_query = pd.read_csv(input_path+'\\'+raw_data_filenames, converters = {'BodyID': int, \
            'FOOTPRINT_SUBCONFIG_VOLUMES':float})
    except UnicodeDecodeError:
        raw_baseline_query = pd.read_csv(input_path+'\\'+raw_data_filenames, converters = {'BodyID': int, \
            'FOOTPRINT_SUBCONFIG_VOLUMES':float}, encoding = 'ISO-8859-1')
    # baseline_query['Roadload Horsepower'][~pd.isnull(baseline_query['Roadload Horsepower'])] \
    #     = baseline_query['Roadload Horsepower'][~pd.isnull(baseline_query['Roadload Horsepower'])].round(1)
    raw_baseline_query['CALC_ID'] = raw_baseline_query['CALC_ID'].astype(float).astype(int)
    raw_baseline_query['ENG_DISPL'][~pd.isnull(raw_baseline_query['ENG_DISPL'])] \
        = raw_baseline_query['ENG_DISPL'][~pd.isnull(raw_baseline_query['ENG_DISPL'])].round(1)
    original_baseline_query = raw_baseline_query[raw_baseline_query['FUEL_USAGE'] != 'E'].reset_index(drop=True)

    model_year = int(raw_data_filenames[:len('2016')])
    drivetrain_score = 3 #3
    transmission_score= 2 #2
    rlhp_score = 0.1 #0.1
    rlhp_category = 'TOT_ROAD_LOAD_HP' #RLHP_FROM_RLCOEFFS or TOT_ROAD_LOAD_HP
    if OMEGA_index_filename != 'N':
        OMEGA_index_file = pd.read_csv(input_path+'\\'+OMEGA_index_filename, converters = {'Index':int}).rename(columns = {\
            'Index':'OMEGA_INDEX'})
        baseline_query = pd.merge_ordered(original_baseline_query, OMEGA_index_file, how='left', on='CALC_ID').reset_index(drop=True)
    else:
        baseline_query = original_baseline_query
    if ALPHA_class_filename != 'N':
        ALPHAclass_table = pd.read_csv(input_path + '\\' + ALPHA_class_filename)
        baseline_query = pd.merge_ordered(baseline_query,ALPHAclass_table,how='left',on ='CALC_ID').reset_index(drop=True)
    baseline_file = baseline_query
    v_aero_mph = 45
    v_roadload = 50
    air_density = 1.17*kgpm32slugpft3

    # baseline_file['TIRE_WIDTH_INS'] = pd.Series(baseline_file['FRONT_BASE_TIRE_CODE']).str.split('/').str.get(0).str.extract('(\d+)').astype(float)/in2mm
    # baseline_file['FRONT_TIRE_RADIUS_IN'] = 0.5*pd.Series(baseline_file['FRONT_BASE_TIRE_CODE']).str.split('R').str.get(1).str.extract('(\d+)').astype(float)
    # baseline_file['REAR_TIRE_RADIUS_IN'] = 0.5*pd.Series(baseline_file['REAR_BASE_TIRE_CODE']).str.split('R').str.get(1).str.extract('(\d+)').astype(float)

    import Field_Statistics
    vehicle_dimensions_table = Field_Statistics.Field_Statistics(input_path, output_path, raw_data_filenames, footprint_plots, \
                    load_factor_plots, credit_integration, target_credit, credit_legend_category, credit_filenames, \
                    sales_weighted_bool, remove_scatter_bool, FTP_time, HWFET_time, color_array_filename, \
                    bool_max_peff, id_type, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                    aeroclass_table_filename, ALPHA_class_filename, OMEGA_index_filename, tire_dimension_filename, \
                    cd_grouping_category)
    aeroclass_table = pd.read_csv(input_path + '\\' + aeroclass_table_filename)
    aeroclass_tire_table = pd.read_csv(input_path + '\\' + tire_dimension_filename)
    baseline_file['Drive System Grouping'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'4WD')
    baseline_file.ix[(baseline_file['DRV_SYS_DESC'].str.contains('2-Wheel Drive')), 'Drive System Grouping'] = '2WD'
    baseline_file = pd.merge_ordered(baseline_file, aeroclass_table, how='left', \
        left_on='CARLINE_CLASS_DESC', right_on='CARLINE_CLASS_DESC').reset_index(drop=True)
    for vehicle_dimension_category in pd.Series(['Width', 'Height', 'Ground Clearance', 'TIRE_WIDTH_INS', \
        'FRONT_TIRE_RADIUS_IN', 'REAR_TIRE_RADIUS_IN']):
        vehicle_dimensions_table = vehicle_dimensions_table.rename(
            columns={vehicle_dimension_category:vehicle_dimension_category+' by Grouping'})
        baseline_file = pd.merge_ordered(baseline_file, \
            vehicle_dimensions_table[['Drive System Grouping', 'AeroClass', vehicle_dimension_category + ' by Grouping']],
            how='left',on=['AeroClass', 'Drive System Grouping'])
        baseline_file['REPORTED_'+vehicle_dimension_category+'_YN'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'N')
        baseline_file['REPORTED_'+vehicle_dimension_category+'_YN'][~pd.isnull(baseline_file[vehicle_dimension_category])] = 'Y'
        baseline_file[vehicle_dimension_category + '_SOURCE'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'')
        baseline_file[vehicle_dimension_category + '_SOURCE'][~pd.isnull(baseline_file[vehicle_dimension_category])] = 'Reported'
        baseline_file[vehicle_dimension_category][pd.isnull(baseline_file[vehicle_dimension_category])] = \
            baseline_file[vehicle_dimension_category + ' by Grouping'][pd.isnull(baseline_file[vehicle_dimension_category])]
        baseline_file[vehicle_dimension_category + '_SOURCE'][(baseline_file[vehicle_dimension_category + '_SOURCE'] == '') & \
            (baseline_file[vehicle_dimension_category] == baseline_file[vehicle_dimension_category + ' by Grouping'])] = 'MY Grouping'
        if 'TIRE' in vehicle_dimension_category and model_year != 2016:
            vehicle_dimensions_table = aeroclass_tire_table.rename(
                columns={vehicle_dimension_category: vehicle_dimension_category + ' by MY2016 Grouping'})
            baseline_file = pd.merge_ordered(baseline_file, vehicle_dimensions_table[['Drive System Grouping', 'AeroClass',
                vehicle_dimension_category + ' by MY2016 Grouping']],how='left', on=['AeroClass', 'Drive System Grouping'])
            baseline_file[vehicle_dimension_category][pd.isnull(baseline_file[vehicle_dimension_category])] = \
                baseline_file[vehicle_dimension_category + ' by MY2016 Grouping'][pd.isnull(baseline_file[vehicle_dimension_category])]
            baseline_file[vehicle_dimension_category + '_SOURCE'][(baseline_file[vehicle_dimension_category + '_SOURCE'] != 'MY Grouping')& \
                (baseline_file[vehicle_dimension_category] == baseline_file[vehicle_dimension_category + ' by MY2016 Grouping'])] = 'MY2016 Grouping'
        try:
            baseline_file[vehicle_dimension_category+'_min'][pd.isnull(baseline_file[vehicle_dimension_category+'_min'])] = \
                baseline_file[vehicle_dimension_category][pd.isnull(baseline_file[vehicle_dimension_category + '_min'])]
            baseline_file[vehicle_dimension_category+'_max'][pd.isnull(baseline_file[vehicle_dimension_category+'_max'])] = \
                baseline_file[vehicle_dimension_category][pd.isnull(baseline_file[vehicle_dimension_category + '_max'])]
        except KeyError:
            pass

    baseline_file['Frontal Area'] = pd.Series((baseline_file['Width']*baseline_file['Height']) - baseline_file[\
        'Ground Clearance']*(baseline_file['FRONT_TRACK_WIDTH_INCHES']-baseline_file['TIRE_WIDTH_INS']))*(in2ft**2)
    baseline_file['Frontal Area_min'] = pd.Series((baseline_file['Width_min']*baseline_file['Height_min']) - baseline_file[\
        'Ground Clearance_max']*(baseline_file['FRONT_TRACK_WIDTH_INCHES_max']-baseline_file['TIRE_WIDTH_INS_min']))*(in2ft**2)
    baseline_file['Frontal Area_max'] = pd.Series((baseline_file['Width_max']*baseline_file['Height_max']) - baseline_file[\
        'Ground Clearance_min']*(baseline_file['FRONT_TRACK_WIDTH_INCHES_min']-baseline_file['TIRE_WIDTH_INS_max']))*(in2ft**2)

    baseline_file['CD_FROM_RLCOEFFS'] = baseline_file['CDA_FROM_RLCOEFFS']/baseline_file['Frontal Area']
    baseline_file['CD_FROM_RLCOEFFS_min'] = baseline_file['CDA_FROM_RLCOEFFS_min'] / baseline_file['Frontal Area_max']
    baseline_file['CD_FROM_RLCOEFFS_max'] = baseline_file['CDA_FROM_RLCOEFFS_max'] / baseline_file['Frontal Area_min']

    baseline_file['CD_ASGN_SCORE'] = pd.Series(np.zeros(len(baseline_file)))
    baseline_file['CD_ASGN_SCORE'][baseline_file['DRV_SYS_DESC'].str.contains('2-Wheel Drive')] += drivetrain_score
    baseline_file['CD_ASGN_SCORE'][baseline_file['TRANS_TYPE'] != 'M'] += transmission_score
    #baseline_file['CD_ASGN_SCORE'][baseline_file['Air Aspiration Description'] == 'Naturally Aspirated'] += 3

    baseline_file_initial_maxscore = baseline_file[[cd_grouping_category, 'CD_ASGN_SCORE']].groupby(cd_grouping_category).max().reset_index()\
        .rename(columns = {'CD_ASGN_SCORE':'max_CD_ASGN_SCORE'})
    baseline_file = pd.merge_ordered(baseline_file, baseline_file_initial_maxscore, how='left', on = cd_grouping_category)
    baseline_file['CD_FRONTRUNNER_YN'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'N')
    baseline_file['CD_FRONTRUNNER_YN'][baseline_file['CD_ASGN_SCORE']==baseline_file['max_CD_ASGN_SCORE']] = 'Y'
    baseline_file_tiebreaker = baseline_file[baseline_file['CD_FRONTRUNNER_YN']=='Y'].reset_index(drop=True)
    baseline_file_minmaxscoring = baseline_file_tiebreaker[[cd_grouping_category, rlhp_category]].groupby(cd_grouping_category).min().reset_index() \
        .rename(columns={rlhp_category:'Min_'+rlhp_category+'_FROM_RLCOEFFS_by'+cd_grouping_category})
    baseline_file = pd.merge_ordered(baseline_file, baseline_file_minmaxscoring[[cd_grouping_category, \
        'Min_'+rlhp_category+'_FROM_RLCOEFFS_by'+cd_grouping_category]], how='left', on = cd_grouping_category).reset_index(drop=True)
    # baseline_file['CD_ASGN_SCORE'][baseline_file['ETW'] == baseline_file['Min_ETW_by'+cd_grouping_category]] += 0.2
    baseline_file['CD_ASGN_SCORE'][baseline_file[rlhp_category] == baseline_file['Min_'+rlhp_category+'_FROM_RLCOEFFS_by'+cd_grouping_category]] += rlhp_score
    baseline_file_highestscore = baseline_file[[cd_grouping_category, 'CD_ASGN_SCORE']][~pd.isnull(baseline_file['CD_FROM_RLCOEFFS'])].reset_index(drop=True)\
        .groupby(cd_grouping_category).max().reset_index()
    baseline_file_highestscore = pd.merge_ordered(baseline_file_highestscore, \
        baseline_file[[cd_grouping_category, 'CD_ASGN_SCORE', 'CD_FROM_RLCOEFFS']], how='left', on=[cd_grouping_category, 'CD_ASGN_SCORE']).rename(columns={'CD_FROM_RLCOEFFS': 'Cd'})\
        .drop('CD_ASGN_SCORE',axis=1).groupby(cd_grouping_category).min().reset_index()
    baseline_file = pd.merge_ordered(baseline_file, baseline_file_highestscore[[cd_grouping_category, 'Cd']], how='left', on=cd_grouping_category).reset_index(drop=True)
    baseline_file = baseline_file.drop(['CD_ASGN_SCORE', 'max_CD_ASGN_SCORE', 'CD_FRONTRUNNER_YN', 'Min_'+rlhp_category+'_FROM_RLCOEFFS_by'+cd_grouping_category],axis=1)\
        .sort_values('CALC_ID').reset_index(drop=True)
    baseline_file['CDA'] = pd.Series(baseline_file['Cd'] * baseline_file['Frontal Area'])
    baseline_file['GROUP_CD_ENTRY_YN'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'N')
    baseline_file['GROUP_CD_ENTRY_YN'][baseline_file['CD_FROM_RLCOEFFS']==baseline_file['Cd']] = 'Y'
    baseline_file['GROUP_CD_ENTRY_YN'][pd.isnull(baseline_file['Cd'])] = 'N'

    F_brake = 2*(0.4/(baseline_file['FRONT_TIRE_RADIUS_IN']*in2m))*n2lbf + 2*(0.4/(baseline_file['REAR_TIRE_RADIUS_IN']*in2m))*n2lbf
    rpm_front = v_roadload \
                * mph2mps * (1 / (baseline_file['FRONT_TIRE_RADIUS_IN'] * in2m)) * (60 / (2 * math.pi))
    rpm_rear = v_roadload \
               * mph2mps * (1 / (baseline_file['REAR_TIRE_RADIUS_IN'] * in2m)) * (60 / (2 * math.pi))
    F_hub = 2 * ((((-2e-6 * rpm_front ** 2) + (.0023 * rpm_front) + 1.2157) \
        / (baseline_file['FRONT_TIRE_RADIUS_IN']* in2m)) * n2lbf) + 2 * ((((-2e-6 * rpm_rear ** 2) \
        + (.0023 * rpm_rear) + 1.2157) / (baseline_file['REAR_TIRE_RADIUS_IN']* in2m)) * n2lbf)
    F_drivetrain = 20 * n2lbf

    for stat_group in pd.Series(['min', 'avg', 'max']):
        for roadload_group in ['TOT_ROAD_LOAD_HP', 'RLHP_FROM_RLCOEFFS']:
            if stat_group == 'avg':
                total_road_load_force = pd.Series(baseline_file[roadload_group]*hp2lbfmph*(1/v_roadload))
            else:
                total_road_load_force = pd.Series(baseline_file[roadload_group+'_'+stat_group]*hp2lbfmph*(1/v_roadload))
            baseline_file['Non Aero Drag Force'+'_'+ stat_group.upper() +'_'+roadload_group.upper()] = \
                total_road_load_force - 0.5*air_density*baseline_file['Cd']*baseline_file['Frontal Area']*((v_roadload*mph2ftps)**2)
            baseline_file['Non Aero Drag Force' + '_' + 'ROUNDED' + '_' + stat_group.upper() +'_'+roadload_group.upper()] = \
                baseline_file['Non Aero Drag Force'+'_'+ stat_group.upper() +'_'+roadload_group.upper()].round(2)
            rolling_force= pd.Series(baseline_file['Non Aero Drag Force'+'_'+ stat_group.upper() +'_'+roadload_group.upper()] - F_brake - F_hub - F_drivetrain)
            baseline_file['RRC'+'_'+ stat_group.upper() +'_'+roadload_group.upper()] = 1000*rolling_force/baseline_file['ETW']
            baseline_file['RRC' + '_' + 'ROUNDED' + '_'+ stat_group.upper() +'_'+roadload_group.upper()] = \
                baseline_file['RRC'+'_'+ stat_group.upper() +'_'+roadload_group.upper()].round(2)
            baseline_file['Non Aero Drag Force'+'_'+ stat_group.upper() +'_'+roadload_group.upper()+'_'+'NORMALIZED_BY_ETW'] = \
                100*baseline_file['Non Aero Drag Force' + '_' + stat_group.upper() + '_' + roadload_group.upper()]/baseline_file['ETW']

    baseline_file['Transmission Short Name'] = pd.Series(baseline_file['TRANS_TYPE'] + \
        baseline_file['TOTAL_NUM_TRANS_GEARS'].astype(str)).replace('CVT1','CVT')

    baseline_file['RLHP_min_ROUNDED']=pd.Series(np.zeros(len(baseline_file)))
    baseline_file['RLHP_ROUNDED']=pd.Series(np.zeros(len(baseline_file)))
    baseline_file['RLHP_max_ROUNDED']=pd.Series(np.zeros(len(baseline_file)))

    baseline_file['RLHP_min_ROUNDED'][~pd.isnull(baseline_file['TOT_ROAD_LOAD_HP_min'])] = baseline_file['TOT_ROAD_LOAD_HP_min'][~pd.isnull(baseline_file['TOT_ROAD_LOAD_HP_min'])].round(1)
    baseline_file['RLHP_ROUNDED'][~pd.isnull(baseline_file['TOT_ROAD_LOAD_HP'])] = baseline_file['TOT_ROAD_LOAD_HP'][~pd.isnull(baseline_file['TOT_ROAD_LOAD_HP'])].round(1)
    baseline_file['RLHP_max_ROUNDED'][~pd.isnull(baseline_file['TOT_ROAD_LOAD_HP_max'])] = baseline_file['TOT_ROAD_LOAD_HP_max'][~pd.isnull(baseline_file['TOT_ROAD_LOAD_HP_max'])].round(1)

    baseline_file['CD_FROM_RLCOEFFS_ROUNDED'] = baseline_file['CD_FROM_RLCOEFFS'].round(2)
    baseline_file['CD_FROM_RLCOEFFS_ROUNDED_min'] = baseline_file['CD_FROM_RLCOEFFS_min'].round(2)
    baseline_file['CD_FROM_RLCOEFFS_ROUNDED_max'] = baseline_file['CD_FROM_RLCOEFFS_max'].round(2)

    baseline_file['ROAD_LOAD_LABEL'] = pd.Series(baseline_file['CALC_ID'].astype(str)+'_'\
        +baseline_file['FOOTPRINT_CARLINE_NM']+'_'+baseline_file['BodyID'].astype(str)+'_'\
        +baseline_file['ENG_DISPL'].astype(str)+'_'+baseline_file['Transmission Short Name']+'_'+\
        \
        'Axle Ratio:(' + baseline_file['AXLE_RATIO_min'].round(2).replace(np.nan,'na').astype(str)+'-'+ \
        baseline_file['AXLE_RATIO'].round(2).replace(np.nan, 'na').astype(str)+'-'+ \
        baseline_file['AXLE_RATIO_max'].round(2).replace(np.nan,'na').astype(str)+')'+'_'+
        \
        'RLHP:(' + baseline_file['RLHP_min_ROUNDED'].replace(np.nan,'na').astype(str)+'-'+\
        baseline_file['RLHP_ROUNDED'].replace(np.nan,'na').astype(str)+'-'+\
        baseline_file['RLHP_max_ROUNDED'].replace(np.nan,'na').astype(str)+')'+'_'+\
        \
        'CD:(' + baseline_file['CD_FROM_RLCOEFFS'+'_ROUNDED_'+'min'].astype(str)+'-'+\
        baseline_file['CD_FROM_RLCOEFFS'+'_ROUNDED'].astype(str) + '-'+\
        baseline_file['CD_FROM_RLCOEFFS'+'_ROUNDED_'+'max'].astype(str)+'|'+ \
        baseline_file['Cd'].round(2).astype(str)+ ')'+'_'+ \
        \
        'Non-Aero:(' + baseline_file['Non Aero Drag Force'+'_ROUNDED_'+'MIN_TOT_ROAD_LOAD_HP'].astype(str)+'-'+\
        baseline_file['Non Aero Drag Force'+'_ROUNDED_'+'AVG_TOT_ROAD_LOAD_HP'].astype(str) + '-' + \
        baseline_file['Non Aero Drag Force'+'_ROUNDED_'+'MAX_TOT_ROAD_LOAD_HP'].astype(str) + ')'+'_'+\
        \
        'RRC:(' + baseline_file['RRC'+'_ROUNDED_'+'MIN_TOT_ROAD_LOAD_HP'].astype(str)+'-'+\
        baseline_file['RRC'+'_ROUNDED_'+'AVG_TOT_ROAD_LOAD_HP'].astype(str) + '-'+\
        baseline_file['RRC'+'_ROUNDED_'+'MAX_TOT_ROAD_LOAD_HP'].astype(str)+')'+'_'+\
        \
        baseline_file['FRONT_BASE_TIRE_CODE']+'_'+\
        baseline_file['ETW'].replace(np.nan,0).astype(float).round(0).astype(int).replace(0,'na').astype(str))

    #ETW_Normalized Non-Aero Drag Force Percentiles
    if ALPHA_class_filename != 'N':
        bin_size = 100
        baseline_file['ALPHA Class for Non-Aero Percentiles'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'OTHER')
        baseline_file['ALPHA Class for Non-Aero Percentiles'][baseline_file['ALPHA Class'] == 'PEV'] = 'PEV'
        baseline_file['ALPHA Class for Non-Aero Percentiles'][baseline_file['ALPHA Class'] == 'Truck'] = 'TRUCK'
        baseline_file['ALPHA Class for Non-Aero Percentiles'][baseline_file['ALPHA Class'] == 'HPW'] = 'HPW'
        baseline_file['Drive System Class for Non-Aero Percentiles'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'4WD')
        baseline_file['Drive System Class for Non-Aero Percentiles'][baseline_file['DRV_SYS_DESC'] == '2-Wheel Drive, Front'] = 'FWD'
        baseline_file['Drive System Class for Non-Aero Percentiles'][baseline_file['DRV_SYS_DESC'] == '2-Wheel Drive, Rear']  ='RWD'
        baseline_file['Drive System Class for Non-Aero Percentiles'][baseline_file['DRV_SYS_DESC'] == 'All Wheel Drive'] = 'AWD'

        baseline_file['Binned Rated Horsepower'] = pd.Series((bin_size/2)+bin_size*np.floor(baseline_file['ENG_RATED_HP']/bin_size))
        baseline_file['Binned Rated Horsepower'][~pd.isnull(baseline_file['Binned Rated Horsepower'])] = \
            baseline_file['Binned Rated Horsepower'][~pd.isnull(baseline_file['Binned Rated Horsepower'])].astype(int)
        baseline_file['Transmission Type for Non-Aero Percentiles'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'Automatic')
        baseline_file['Transmission Type for Non-Aero Percentiles'][baseline_file['TRANS_TYPE'].str.contains('AM')] = 'Automated Manual'
        baseline_file['Transmission Type for Non-Aero Percentiles'][baseline_file['TRANS_TYPE'].str.contains('CV')] = 'Continuously Variable'
        baseline_file['Transmission Type for Non-Aero Percentiles'][baseline_file['TRANS_TYPE']=='M']='Manual'
        # baseline_file['Binned NV Ratio'] = pd.Series(np.zeros(len(baseline_file))).replace(0,'Bin2')
        # baseline_file['Binned NV Ratio'][baseline_file['NV Ratio'] <= 26.4] = 'Bin1'
        # baseline_file['Binned NV Ratio'][baseline_file['NV Ratio'] > 29.6] = 'Bin3'

        baseline_file['Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_NORMALIZED_BY_ETW_GROUP'] = pd.Series(baseline_file['Drive System Class for Non-Aero Percentiles']+'-'+\
            baseline_file['ALPHA Class for Non-Aero Percentiles']+'-'+baseline_file['Binned Rated Horsepower'].astype(str)+'-'\
            +baseline_file['Transmission Type for Non-Aero Percentiles'])
        for percentile_count in range(0,2):
            if percentile_count == 0:
                binning_column = 'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_NORMALIZED_BY_ETW_GROUP'
                data_column = 'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_NORMALIZED_BY_ETW'
            else:
                binning_column = 'AeroClass'
                data_column = 'Cd'
            binning_groups = baseline_file.groupby([binning_column]).groups.keys()
            percentile_column = binning_column+'_PERCENTILE'
            quartile_column = binning_column+'_QUARTILE'
            for binning_group in binning_groups:
                baseline_subfile = baseline_file[(baseline_file[binning_column] == binning_group) & \
                    (~pd.isnull(baseline_file[data_column]))]\
                    .reset_index(drop=True)
                print(binning_group+ ' '+str(len(baseline_subfile)))
                baseline_subfile_with_percentiles = Get_Percentiles(baseline_subfile,data_column,\
                    'FOOTPRINT_SUBCONFIG_VOLUMES', percentile_column)
                baseline_subfile_with_percentiles[quartile_column] = pd.Series(np.ceil(baseline_subfile_with_percentiles[\
                    binning_column+'_PERCENTILE']/25)).replace([5,0],[4,1])
                try:
                    baseline_file_with_percentiles_columns = list(baseline_file_with_percentiles.columns)
                    baseline_file_with_percentiles = pd.concat([baseline_file_with_percentiles, \
                        baseline_subfile_with_percentiles]).sort_values(['CALC_ID', 'BodyID']).reset_index(drop=True)
                    baseline_file_with_percentiles = baseline_file_with_percentiles[baseline_file_with_percentiles_columns]
                except NameError:
                    baseline_file_with_percentiles = baseline_subfile_with_percentiles
            baseline_file = pd.merge_ordered(baseline_file, baseline_file_with_percentiles[\
                ['CALC_ID', 'BodyID', 'FUEL_USAGE', 'FUEL_USAGE_DESC', percentile_column, quartile_column]], \
                how='left', on = ['CALC_ID', 'BodyID', 'FUEL_USAGE', 'FUEL_USAGE_DESC']).reset_index(drop=True)
            del baseline_file_with_percentiles

        baseline_file_grouped = baseline_file[['Drive System Class for Non-Aero Percentiles', 'ALPHA Class for Non-Aero Percentiles',\
            'Binned Rated Horsepower', 'Transmission Type for Non-Aero Percentiles', \
            'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_NORMALIZED_BY_ETW_GROUP_QUARTILE', 'OMEGA_INDEX','FOOTPRINT_CARLINE_NM']]\
            .groupby(['Drive System Class for Non-Aero Percentiles', 'ALPHA Class for Non-Aero Percentiles',\
            'Binned Rated Horsepower', 'Transmission Type for Non-Aero Percentiles',\
            'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_NORMALIZED_BY_ETW_GROUP_QUARTILE']).agg({'FOOTPRINT_CARLINE_NM':lambda x: ','.join(x), \
            'OMEGA_INDEX': lambda x: ','.join(map(str,x))}).reset_index()
        baseline_file_grouped['OMEGA_INDEX'] = baseline_file_grouped['OMEGA_INDEX']
        baseline_file_grouped[~pd.isnull(baseline_file_grouped['Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_NORMALIZED_BY_ETW_GROUP_QUARTILE'])].reset_index(drop=True)
        baseline_file_grouped.to_csv(output_path + '\\' + ' MY' + str(model_year) + ' Non-Aero Baseline Quartiles.csv', index=False)

    #Final Edits and Output
    baseline_file_columns = pd.Series(baseline_file.columns)
    baseline_file_columns = baseline_file_columns[(~baseline_file_columns.str.contains('Master Index')) & \
        (~baseline_file_columns.str.contains('Subconfig Data')) & \
        (~baseline_file_columns.str.contains('Edmunds')) & (~baseline_file_columns.str.contains('Test Car')) & \
        (~baseline_file_columns.str.contains('FEGuide')) & (~baseline_file_columns.str.contains('Wards')) & \
        (~baseline_file_columns.str.contains('AllData'))].reset_index(drop=True)
    baseline_file = baseline_file[baseline_file_columns]
    baseline_file = baseline_file.replace([',', np.nan, str(np.nan), 'inconclusive'],'', regex=True) #For Colliderscope
    baseline_file = baseline_file.replace('',np.nan)
    baseline_file.columns = pd.Series(baseline_file.columns).str.replace(',','')
    baseline_final_columns = pd.Series(baseline_file.columns)
    baseline_final_columns = baseline_final_columns[~baseline_final_columns.str.contains('_ROUNDED_')]
    baseline_file = baseline_file[baseline_final_columns]

    #cabinid_start_year_array = original_baseline_query[['CabinID', 'BodyID StartYear']].groupby(
    #    'CabinID').min().reset_index() \
    #    .rename(columns={'BodyID StartYear': 'CabinID StartYear'})
    #baseline_file = pd.merge_ordered(baseline_file, cabinid_start_year_array, how='left',
    #                                         on='CabinID').reset_index(drop=True).sort_values(['CALC_ID', 'BodyID'])
    date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
    baseline_file.to_csv(output_path+'\\'+ date_and_time + ' MY' + str(model_year) +  ' Baseline.csv', index=False)

    #Baseline File by Calc ID
    minmax_categories_old = ['EPA_CAFE_MT_CALC_COMB_FE_4', 'ENG_RATED_HP', 'Curb Weight', 'Width', 'Height', \
                      'Ground Clearance', 'ROUNDED_CARGO_CARRYING_VOL', 'Wheelbase', 'ETW', 'Turning Circle', 'Interior Volume',\
                         'TOT_ROAD_LOAD_HP', 'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', 'TESTCAR_Set Coef A', 'TESTCAR_Set Coef B', \
                         'TESTCAR_Set Coef C', 'FUEL_NET_HEATING_VALUE', 'NV_RATIO', 'AXLE_RATIO',\
                         'FUEL_BLND_CARBON_WT', 'FUEL_GRAVITY', 'FRONT_TRACK_WIDTH_INCHES', 'REAR_TRACK_WIDTH_INCHES', \
                         'TIRE_WIDTH_INS', 'FRONT_TIRE_RADIUS_IN', 'REAR_TIRE_RADIUS_IN','EPA_TARGET_FE_VALUE', \
                         'EPA_TARGET_GHG_RND_GPM_1', 'APPROACH_ANGLE', 'BREAKOVER_ANGLE', 'DEPARTURE_ANGLE', \
                         'PTEFF_FROM_RLCOEFFS', 'RLHP_FROM_RLCOEFFS', 'CDA_FROM_RLCOEFFS', 'FOOTPRINT', 'Combined Tractive Road Energy Intensity (MJ/km)', 'MSRP']
    minmax_categories_new = ['Cd', 'CD_FROM_RLCOEFFS', 'Frontal Area', 'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP', 'RRC_AVG_TOT_ROAD_LOAD_HP']
    minmax_categories = minmax_categories_old+minmax_categories_new
    bounded_minmax_categories = ['EPA_CAFE_MT_CALC_COMB_FE_4', 'ETW', 'NV_RATIO', 'AXLE_RATIO', \
                         'TARGET_COEF_A', 'TARGET_COEF_B', 'TARGET_COEF_C', 'TESTCAR_Set Coef A', 'TESTCAR_Set Coef B', \
                         'TESTCAR_Set Coef C', 'FUEL_NET_HEATING_VALUE', \
                         'FUEL_BLND_CARBON_WT', 'FUEL_GRAVITY', 'EPA_TARGET_FE_VALUE', \
                         'EPA_TARGET_GHG_RND_GPM_1', 'PTEFF_FROM_RLCOEFFS', 'Combined Tractive Road Energy Intensity (MJ/km)']
    min_aggregation = baseline_file[['CALC_ID']+list(minmax_categories)].replace('',np.nan).groupby('CALC_ID').min().reset_index()
    min_aggregation.columns = pd.Series((pd.Series(min_aggregation.columns).str.cat(list(pd.Series(np.zeros(len(min_aggregation.columns))).replace(0,'min')), sep='_')))\
        .replace('CALC_ID_min','CALC_ID')
    max_aggregation = baseline_file[['CALC_ID'] + list(minmax_categories)].replace('', np.nan).groupby('CALC_ID').max().reset_index()
    max_aggregation.columns = pd.Series((pd.Series(max_aggregation.columns).str.cat(list(pd.Series(np.zeros(len(max_aggregation.columns))).replace(0,'max')), sep='_')))\
        .replace('CALC_ID_max','CALC_ID')
    avg_aggregation = baseline_file[['CALC_ID'] + ['FOOTPRINT_SUBCONFIG_VOLUMES'] + list(minmax_categories_new)]\
        .replace('', np.nan).groupby('CALC_ID').apply(weighed_average).drop('FOOTPRINT_SUBCONFIG_VOLUMES',axis=1).replace(0,np.nan).reset_index(drop=True)
    all_bodyids = baseline_file[['CALC_ID', 'BodyID']].groupby('CALC_ID')['BodyID'].apply(lambda x: '|'.join(map(str,x))).reset_index()
    all_cabinids = baseline_file[['CALC_ID', 'CabinID']].groupby('CALC_ID')['CabinID'].apply(lambda x: '|'.join(map(str, x))).reset_index()
    max_rlhp_aggregation = baseline_file[['CALC_ID', 'TOT_ROAD_LOAD_HP']].groupby('CALC_ID').max().reset_index().rename(columns={'TOT_ROAD_LOAD_HP': 'MaxRLHP'}).replace('',np.nan)
    max_rlhp_aggregation = pd.merge_ordered(max_rlhp_aggregation, baseline_file[['CALC_ID']+['TOT_ROAD_LOAD_HP']+list(bounded_minmax_categories)], how='left', \
        left_on= ['CALC_ID', 'MaxRLHP'], right_on=['CALC_ID', 'TOT_ROAD_LOAD_HP']).groupby('CALC_ID').mean().reset_index().drop('MaxRLHP',axis=1)
    max_rlhp_aggregation.columns = pd.Series((pd.Series(max_rlhp_aggregation.columns).str.cat(\
        list(pd.Series(np.zeros(len(max_rlhp_aggregation.columns))).replace(0,'atmaxTOT_ROAD_LOAD_HP')), sep='_')))\
        .replace('CALC_ID_atmaxTOT_ROAD_LOAD_HP','CALC_ID')
    min_rlhp_aggregation = baseline_file[['CALC_ID', 'TOT_ROAD_LOAD_HP']].groupby('CALC_ID').min().reset_index().rename(columns={'TOT_ROAD_LOAD_HP': 'MinRLHP'}).replace('',np.nan)
    min_rlhp_aggregation = pd.merge_ordered(min_rlhp_aggregation, baseline_file[['CALC_ID']+['TOT_ROAD_LOAD_HP']+list(bounded_minmax_categories)], how='left', \
        left_on= ['CALC_ID', 'MinRLHP'], right_on=['CALC_ID', 'TOT_ROAD_LOAD_HP']).groupby('CALC_ID').mean().reset_index().drop('MinRLHP',axis=1)
    min_rlhp_aggregation.columns = pd.Series((pd.Series(min_rlhp_aggregation.columns).str.cat(\
        list(pd.Series(np.zeros(len(min_rlhp_aggregation.columns))).replace(0,'atminTOT_ROAD_LOAD_HP')), sep='_')))\
        .replace('CALC_ID_atminTOT_ROAD_LOAD_HP','CALC_ID')
    volumes_bycalcid = baseline_file[['CALC_ID', 'FOOTPRINT_SUBCONFIG_VOLUMES', 'PROD_VOL_GHG_STD_50_STATE', \
        'PROD_VOL_GHG_TLAAS_50_STATE', 'PROD_VOL_GHG_TOTAL_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE', 'PRODUCTION_VOLUME_FE_50_STATE']].groupby('CALC_ID').sum().reset_index()
    # new_columns = baseline_file[['CALC_ID', 'Cd', 'Frontal Area', 'Non Aero Drag Force_avg_RLHP', 'RRC_avg_RLHP']]
    baseline_file_byCalcID_int = original_baseline_query.drop(['BodyID', 'FOOTPRINT_SUBCONFIG_VOLUMES', 'PROD_VOL_GHG_STD_50_STATE', \
        'PROD_VOL_GHG_TLAAS_50_STATE', 'PROD_VOL_GHG_TOTAL_50_STATE', 'PRODUCTION_VOLUME_GHG_50_STATE', 'PRODUCTION_VOLUME_FE_50_STATE'],axis=1).groupby('CALC_ID').first().reset_index()
    baseline_file_byCalcID_int_columns = pd.Series(baseline_file_byCalcID_int.columns)
    baseline_file_byCalcID_int_columns = baseline_file_byCalcID_int_columns[(~baseline_file_byCalcID_int_columns.str.contains('_min')) \
        & (~baseline_file_byCalcID_int_columns.str.contains('_max')) & \
        (~baseline_file_byCalcID_int_columns.str.contains('_atminTOT_ROAD_LOAD_HP')) & \
        (~baseline_file_byCalcID_int_columns.str.contains('_atmaxTOT_ROAD_LOAD_HP'))].reset_index(drop=True)
    baseline_file_byCalcID_int_columns = baseline_file_byCalcID_int_columns[baseline_file_byCalcID_int_columns != 'NON_AERO_DRAG_FORCE_FROM_RLCOEFFS'].reset_index(drop=True)
    baseline_file_byCalcID_int = baseline_file_byCalcID_int[list(baseline_file_byCalcID_int_columns) + \
        ['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS_atminTOT_ROAD_LOAD_HP']+['NON_AERO_DRAG_FORCE_FROM_RLCOEFFS_atmaxTOT_ROAD_LOAD_HP']]
    #baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, cabinid_start_year_array, how='left', on='CabinID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, min_aggregation, how='left', \
                                                   on = 'CALC_ID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, max_aggregation, how='left',
                                                   on='CALC_ID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, avg_aggregation, how='left',
                                                   on='CALC_ID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, min_rlhp_aggregation, how='left',
                                                   on='CALC_ID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, max_rlhp_aggregation, how='left',
                                                   on='CALC_ID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, volumes_bycalcid, how='left',
                                                   on='CALC_ID').reset_index(drop=True)
    baseline_file_byCalcID_int = pd.merge_ordered(baseline_file_byCalcID_int, all_bodyids, how='left', on='CALC_ID').drop('CabinID',axis=1)
    baseline_file_byCalcID = pd.merge_ordered(baseline_file_byCalcID_int, all_cabinids, how='left', on='CALC_ID')

    baseline_file_byCalcID_columns = pd.Series(original_baseline_query.columns)
    baseline_file_byCalcID_columns = baseline_file_byCalcID_columns[(~baseline_file_byCalcID_columns.str.contains('Master Index')) & \
        (~baseline_file_byCalcID_columns.str.contains('Subconfig Data')) & \
        (~baseline_file_byCalcID_columns.str.contains('Edmunds')) & (~baseline_file_byCalcID_columns.str.contains('Test Car')) & \
        (~baseline_file_byCalcID_columns.str.contains('FEGuide')) & (~baseline_file_byCalcID_columns.str.contains('Wards')) & \
        (~baseline_file_byCalcID_columns.str.contains('AllData'))].reset_index(drop=True)
    baseline_file_byCalcID_columns = list(baseline_file_byCalcID_columns) + ['Cd', 'Frontal Area', 'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP', 'RRC_AVG_TOT_ROAD_LOAD_HP'] \
        + ['Cd_min', 'Frontal Area_min', 'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_min', 'RRC_AVG_TOT_ROAD_LOAD_HP_min'] + \
        ['Cd_max', 'Frontal Area_max', 'Non Aero Drag Force_AVG_TOT_ROAD_LOAD_HP_max','RRC_AVG_TOT_ROAD_LOAD_HP_max']
    baseline_file_byCalcID = baseline_file_byCalcID[baseline_file_byCalcID_columns]
    baseline_file_byCalcID = baseline_file_byCalcID.loc[:,~baseline_file_byCalcID.columns.duplicated()]
    for cabinid_count in range(0,len(baseline_file_byCalcID)):
        baseline_file_byCalcID['CabinID'][cabinid_count] = \
            '|'.join(list(pd.Series(baseline_file_byCalcID['CabinID'][cabinid_count].split('|')).unique()))
    try:
        baseline_file_byCalcID = baseline_file_byCalcID.drop(['TIRE_WIDTH_INS', 'FRONT_TIRE_RADIUS_IN', \
            'REAR_TIRE_RADIUS_IN', 'Drive System Grouping'],axis=1)
    except ValueError:
        pass
    baseline_file_byCalcID = baseline_file_byCalcID.drop('Cd',axis=1).rename(columns = {'Cd_min':'Cd'})
    baseline_file_byCalcID = baseline_file_byCalcID.drop(['Cd_max'],axis=1)
    baseline_file_byCalcID.to_csv(output_path + '\\' + date_and_time + ' MY' + str(model_year) + ' Baseline_byCalcID.csv', index=False)
