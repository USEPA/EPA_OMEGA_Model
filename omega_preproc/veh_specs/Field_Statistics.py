import pandas as pd
import numpy as np
import math
import datetime
from Unit_Conversion import mph2ftps, kgpm32slugpft3, in2mm, in2ft, n2lbf, in2m, mph2mps
def weighed_average(grp):
    weighting_field = 'FOOTPRINT_SUBCONFIG_VOLUMES'
    return grp._get_numeric_data().multiply(grp[weighting_field], axis=0).sum()/((~pd.isnull(grp)).multiply(grp[weighting_field],axis=0).sum())
def Field_Statistics(input_path, output_path, raw_data_filenames, footprint_plots, \
                     load_factor_plots, credit_integration, target_credit, credit_legend_category, credit_filenames, \
                     sales_weighted_bool, remove_scatter_bool, FTP_time, HWFET_time, color_array_filename, \
                      bool_max_peff, id_type, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                      aeroclass_table_filename, ALPHA_class_filename, OMEGA_index_filename, tire_dimension_filename, \
                     cd_grouping_category):
    try:
        baseline_query = pd.read_csv(input_path+'\\'+raw_data_filenames, converters = {'BodyID': int, \
        'FOOTPRINT_SUBCONFIG_VOLUMES':float})
    except UnicodeDecodeError:
        baseline_query = pd.read_csv(input_path+'\\'+raw_data_filenames, converters = {'BodyID': int, \
        'FOOTPRINT_SUBCONFIG_VOLUMES':float}, encoding = 'ISO-8859-1')
    aeroclass_table = pd.read_csv(input_path+'\\'+aeroclass_table_filename)
    model_year = baseline_query['CAFE_MODEL_YEAR'].mode()[0].astype(int)
    # baseline_columns = pd.Series(baseline_query.columns)
    # baseline_columns = baseline_columns[~baseline_columns.str.contains('_')].reset_index(drop=True)
    # baseline_query = baseline_query[['CALC_ID']+['FUEL_USAGE']+['FUEL_USAGE_DESC']+list(baseline_columns) + ['FOOTPRINT_SUBCONFIG_VOLUMES']]
    # model_year = int(raw_data_filenames[:len('2016')])

    baseline_query['Drive System Grouping'] = pd.Series(np.zeros(len(baseline_query))).replace(0,'4WD')
    baseline_query.ix[(baseline_query['DRV_SYS_DESC'].str.contains('2-Wheel Drive')), 'Drive System Grouping'] = '2WD'
    try:
        baseline_query[['TIRE_WIDTH_INS', 'FRONT_TIRE_RADIUS_IN', 'REAR_TIRE_RADIUS_IN']]
    except KeyError:
        baseline_query['TIRE_WIDTH_INS'] = pd.Series(baseline_query['FRONT_BASE_TIRE_CODE']).str.split('/').str.get(
            0).str.extract('(\d+)').astype(float) / in2mm
        baseline_query['FRONT_TIRE_RADIUS_IN'] = 0.5*pd.Series(baseline_query['FRONT_BASE_TIRE_CODE']).str.split('R').str.get(
            1).str.extract('(\d+)').astype(float)
        baseline_query['REAR_TIRE_RADIUS_IN'] = 0.5*pd.Series(baseline_query['REAR_BASE_TIRE_CODE']).str.split('R').str.get(
            1).str.extract('(\d+)').astype(float)
    for vehicle_dimension_category in ['Width', 'Height', 'Ground Clearance', 'TIRE_WIDTH_INS', \
        'FRONT_TIRE_RADIUS_IN', 'REAR_TIRE_RADIUS_IN']:
        baseline_query_with_aeroclass = pd.merge_ordered(baseline_query, aeroclass_table, how='left', \
            left_on = 'CARLINE_CLASS_DESC', right_on = 'CARLINE_CLASS_DESC').reset_index(drop=True)
        baseline_query_with_aeroclass_filtered = baseline_query_with_aeroclass[\
            ~pd.isnull(baseline_query_with_aeroclass[vehicle_dimension_category])].reset_index(drop=True)
        field_max = baseline_query_with_aeroclass_filtered[[vehicle_dimension_category, 'Drive System Grouping', 'AeroClass']]\
            .groupby(['Drive System Grouping', 'AeroClass']).max().reset_index().rename(\
            columns = {vehicle_dimension_category: vehicle_dimension_category + '_Max'})
        field_min = baseline_query_with_aeroclass_filtered[[vehicle_dimension_category, 'Drive System Grouping', 'AeroClass']]\
            .groupby(['Drive System Grouping', 'AeroClass']).min().reset_index().rename(\
            columns = {vehicle_dimension_category: vehicle_dimension_category + '_Min'})
        field_stdev = baseline_query_with_aeroclass_filtered[[vehicle_dimension_category, 'Drive System Grouping', 'AeroClass']]\
            .groupby(['Drive System Grouping', 'AeroClass']).std().reset_index().rename(\
            columns = {vehicle_dimension_category: vehicle_dimension_category + '_StDev'})
        field_count = baseline_query_with_aeroclass_filtered[[vehicle_dimension_category, 'Drive System Grouping', 'AeroClass']]\
            .groupby(['Drive System Grouping', 'AeroClass']).count().reset_index().rename(\
            columns = {vehicle_dimension_category: vehicle_dimension_category + '_Count'})
        field_swavg = baseline_query_with_aeroclass_filtered[\
            [vehicle_dimension_category, 'FOOTPRINT_SUBCONFIG_VOLUMES', 'Drive System Grouping', 'AeroClass']]\
            .groupby(['Drive System Grouping', 'AeroClass']).apply(weighed_average).drop('FOOTPRINT_SUBCONFIG_VOLUMES',axis=1)
        try:
            field_swavg = field_swavg.drop(['Drive System Grouping', 'AeroClass'],axis=1).reset_index()
        except KeyError:
            field_swavg = field_swavg.reset_index()
    
        field_table = baseline_query_with_aeroclass[['AeroClass', 'Drive System Grouping', 'FOOTPRINT_SUBCONFIG_VOLUMES']]\
            .groupby(['AeroClass', 'Drive System Grouping']).sum().reset_index().drop('FOOTPRINT_SUBCONFIG_VOLUMES',axis=1)\
            .merge(field_count, how='left', on=['Drive System Grouping', 'AeroClass']) \
            .merge(field_swavg, how='left', on=['Drive System Grouping', 'AeroClass']) \
            .merge(field_min, how='left', on=['Drive System Grouping', 'AeroClass'])\
            .merge(field_max, how='left', on=['Drive System Grouping', 'AeroClass']) \
            .merge(field_stdev, how='left', on=['Drive System Grouping', 'AeroClass'])
        try:
            field_table_output = pd.merge_ordered(field_table_output, field_table, how='left', \
                on=['Drive System Grouping', 'AeroClass']).reset_index(drop=True)
        except NameError:
            field_table_output = field_table
    field_table_output.to_csv(output_path+'\\'+ 'MY' + str(model_year) +' Vehicle Dimensions Table.csv', index=False)
    return field_table_output