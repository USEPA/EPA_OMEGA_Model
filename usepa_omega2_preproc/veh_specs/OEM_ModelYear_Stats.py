import pandas as pd
import numpy as np
import datetime

def OEM_ModelYear_Stats(input_path, output_path, filenames_list, \
                        load_factor_plots, credit_integration, target_credit, credit_legend_category):
    VMT_C = 195264
    VMT_T = 225865
    if ',' in filenames_list:
        filenames = pd.Series(list(filenames_list.split(','))).str.strip()
    else:
        filenames = filenames_list.strip()
    sw_data_categories = pd.Series(['Powertrain Efficiency_Subconfig Data', 'Tractive Energy Intensity_Subconfig Data', \
        'CO2 Tailpipe Emissions_Master Index', 'CO2 Target_Master Index'])
    for filename in filenames:
        print(filename)
        file = pd.read_csv(input_path + '\\' + filename)
        try:
            combined_file = pd.concat([combined_file, file])
        except NameError:
            combined_file = file
        #Avg
        file['Total CO2 Tailpipe Emissions (Mg)'] = pd.Series(file['FOOTPRINT_SUBCONFIG_SALES']*\
                                                              file['CO2 Tailpipe Emissions_Master Index']*VMT_C*1e-6)
        file['Total CO2 Tailpipe Emissions (Mg)'][file['COMPLIANCE_CATEGORY_CD']=='LT'] \
            = pd.Series(file['Total CO2 Tailpipe Emissions (Mg)'][file['COMPLIANCE_CATEGORY_CD']=='LT']*(VMT_T/VMT_C))
        # #Max
        # file['Total CO2 Tailpipe Emissions (Mg)_Max'] = pd.Series(file['FOOTPRINT_SUBCONFIG_SALES']*\
        #                                                       file['CO2 Tailpipe Emissions_Master Index_Max']*VMT_C*1e-6)
        # file['Total CO2 Tailpipe Emissions (Mg)_Max'][file['COMPLIANCE_CATEGORY_CD']=='LT'] \
        #     = pd.Series(file['Total CO2 Tailpipe Emissions (Mg)_Max'][file['COMPLIANCE_CATEGORY_CD']=='LT']*(VMT_T/VMT_C))
        # #Min
        # file['Total CO2 Tailpipe Emissions (Mg)_Min'] = pd.Series(file['FOOTPRINT_SUBCONFIG_SALES']*\
        #                                                       file['CO2 Tailpipe Emissions_Master Index_Min']*VMT_C*1e-6)
        # file['Total CO2 Tailpipe Emissions (Mg)_Min'][file['COMPLIANCE_CATEGORY_CD']=='LT'] \
        #     = pd.Series(file['Total CO2 Tailpipe Emissions (Mg)_Min'][file['COMPLIANCE_CATEGORY_CD']=='LT']*(VMT_T/VMT_C))

        OEM_vehicletype_list = ['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']
        OEM_list = ['MODEL_YEAR', 'CAFE_MFR_NM']
        allOEM_vehicletype_list = ['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']
        allOEM_list = ['MODEL_YEAR']

        # BodyID count
        OEM_vehicletype_bodyidcount = file[list(OEM_vehicletype_list) + ['BodyID']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).size() \
            .reset_index(name = 'BodyID_Count')
        OEM_bodyidcount = file[list(OEM_list) + ['BodyID']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).size() \
            .reset_index(name = 'BodyID_Count')
        allOEM_vehicletype_bodyidcount = file[list(allOEM_vehicletype_list) + ['BodyID']] \
            .groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).size() \
            .reset_index(name = 'BodyID_Count')
        allOEM_bodyidcount = file[list(allOEM_list) + ['BodyID']] \
            .groupby(['MODEL_YEAR']).size() \
            .reset_index(name = 'BodyID_Count')
        # CabinID count
        OEM_vehicletype_cabinidcount = file[list(OEM_vehicletype_list) + ['CabinID']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).size() \
            .reset_index(name = 'CabinID_Count')
        OEM_cabinidcount = file[list(OEM_list) + ['CabinID']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).size() \
            .reset_index(name = 'CabinID_Count')
        allOEM_vehicletype_cabinidcount = file[list(allOEM_vehicletype_list) + ['CabinID']] \
            .groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).size() \
            .reset_index(name = 'CabinID_Count')
        allOEM_cabinidcount = file[list(allOEM_list) + ['CabinID']] \
            .groupby(['MODEL_YEAR']).size() \
            .reset_index(name = 'CabinID_Count').rename(columns={'CabinID': 'CabinID_Count'})


        # Sales Volume
        OEM_vehicletype_sales = file[list(OEM_vehicletype_list) + ['FOOTPRINT_SUBCONFIG_SALES']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).sum() \
            .reset_index()
        OEM_sales = file[list(OEM_list) + ['FOOTPRINT_SUBCONFIG_SALES']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).sum() \
            .reset_index()
        allOEM_vehicletype_sales = file[list(allOEM_vehicletype_list) + ['FOOTPRINT_SUBCONFIG_SALES']] \
            .groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).sum() \
            .reset_index()
        allOEM_sales = file[list(allOEM_list) + ['FOOTPRINT_SUBCONFIG_SALES']] \
            .groupby(['MODEL_YEAR']).sum() \
            .reset_index()
        #Total CO2 Emissiong (Mg)
        OEM_vehicletype_emissions = file[list(OEM_vehicletype_list) + ['Total CO2 Tailpipe Emissions (Mg)']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).sum() \
            .reset_index()
        OEM_emissions = file[list(OEM_list) + ['Total CO2 Tailpipe Emissions (Mg)']] \
            .groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).sum() \
            .reset_index()
        allOEM_vehicletype_emissions = file[list(allOEM_vehicletype_list) + ['Total CO2 Tailpipe Emissions (Mg)']] \
            .groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).sum() \
            .reset_index()
        allOEM_emissions = file[list(allOEM_list) + ['Total CO2 Tailpipe Emissions (Mg)']] \
            .groupby(['MODEL_YEAR']).sum() \
            .reset_index()

        file = file[~pd.isnull(file['Powertrain Efficiency_Subconfig Data'])].reset_index(drop=True)
        # Sales Weighted Average, Max and Min
        for sw_category in sw_data_categories:
            # Max
            OEM_vehicletype_sw_category_max = file[
                list(OEM_vehicletype_list) + [sw_category + '_Max']] \
                .groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).max() \
                .reset_index()
            OEM_sw_category_max = file[list(OEM_list) + [sw_category + '_Max']] \
                .groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).max() \
                .reset_index()
            allOEM_vehicletype_sw_category_max = file[list(allOEM_vehicletype_list) + [sw_category + '_Max']] \
                .groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).max() \
                .reset_index()
            allOEM_sw_category_max = file[list(allOEM_list) + [sw_category + '_Max']] \
                .groupby(['MODEL_YEAR']).max() \
                .reset_index()
            # Min
            OEM_vehicletype_sw_category_min = file[
                list(OEM_vehicletype_list) + [sw_category + '_Min']] \
                .groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).min() \
                .reset_index()
            OEM_sw_category_min = file[list(OEM_list) + [sw_category + '_Min']] \
                .groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).min() \
                .reset_index()
            allOEM_vehicletype_sw_category_min = file[list(allOEM_vehicletype_list) + [sw_category + '_Min']] \
                .groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).min() \
                .reset_index()
            allOEM_sw_category_min = file[list(allOEM_list) + [sw_category + '_Min']] \
                .groupby(['MODEL_YEAR']).min() \
                .reset_index()

            # Sales Weighted Average
            #Groupby Setup
            OEM_vehicletype_df = file[
                ['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD', 'FOOTPRINT_SUBCONFIG_SALES'] + [sw_category]]
            OEM_vehicletype_wm = lambda x: np.average(x, weights=OEM_vehicletype_df.loc[x.index, "FOOTPRINT_SUBCONFIG_SALES"])
            #OEM_vehicletype_f = {'FOOTPRINT_SUBCONFIG_SALES': ['sum'], sw_category: {sw_category: OEM_vehicletype_wm}}

            OEM_df = file[
                ['MODEL_YEAR', 'CAFE_MFR_NM', 'FOOTPRINT_SUBCONFIG_SALES'] + [sw_category]]
            OEM_wm = lambda x: np.average(x, weights=OEM_df.loc[x.index, "FOOTPRINT_SUBCONFIG_SALES"])
            #OEM_f = {'FOOTPRINT_SUBCONFIG_SALES': ['sum'], sw_category: {sw_category: OEM_wm}}

            allOEM_vehicletype_df = file[
                ['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD', 'FOOTPRINT_SUBCONFIG_SALES'] + [sw_category]]
            allOEM_vehicletype_wm = lambda x: np.average(x, weights=allOEM_vehicletype_df.loc[x.index, "FOOTPRINT_SUBCONFIG_SALES"])
            #allOEM_vehicletype_f = {'FOOTPRINT_SUBCONFIG_SALES': ['sum'], sw_category: {sw_category: allOEM_vehicletype_wm}}

            allOEM_df = file[
                ['MODEL_YEAR', 'FOOTPRINT_SUBCONFIG_SALES'] + [sw_category]]
            allOEM_wm = lambda x: np.average(x, weights=allOEM_df.loc[x.index, "FOOTPRINT_SUBCONFIG_SALES"])
            #allOEM_f = {'FOOTPRINT_SUBCONFIG_SALES': ['sum'], sw_category: {sw_category: allOEM_wm}}

            #Groupby
            OEM_vehicletype_sw_category = OEM_vehicletype_df.groupby(['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).agg(OEM_vehicletype_wm) \
                .reset_index()
            # OEM_vehicletype_sw_category.columns = ['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD', \
            #                                        sw_category, 'FOOTPRINT_SUBCONFIG_SALES']
            OEM_vehicletype_sw_category = OEM_vehicletype_sw_category.drop('FOOTPRINT_SUBCONFIG_SALES',axis=1)

            OEM_sw_category = OEM_df.groupby(['MODEL_YEAR', 'CAFE_MFR_NM']).agg(OEM_wm).reset_index()
            # OEM_sw_category.columns = ['MODEL_YEAR', 'CAFE_MFR_NM', sw_category, 'FOOTPRINT_SUBCONFIG_SALES']
            OEM_sw_category = OEM_sw_category.drop('FOOTPRINT_SUBCONFIG_SALES',axis=1)

            allOEM_vehicletype_sw_category = allOEM_vehicletype_df.groupby(['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).agg(allOEM_vehicletype_wm).reset_index()
            # allOEM_vehicletype_sw_category.columns = ['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD', sw_category, 'FOOTPRINT_SUBCONFIG_SALES']
            allOEM_vehicletype_sw_category = allOEM_vehicletype_sw_category.drop('FOOTPRINT_SUBCONFIG_SALES',axis=1)

            allOEM_sw_category = allOEM_df.groupby(['MODEL_YEAR']).agg(allOEM_wm).reset_index()
            # allOEM_sw_category.columns = ['MODEL_YEAR',sw_category, 'FOOTPRINT_SUBCONFIG_SALES']
            allOEM_sw_category = allOEM_sw_category.drop('FOOTPRINT_SUBCONFIG_SALES', axis=1)

            try:
                OEM_vehicletype_sw = OEM_vehicletype_sw.merge(OEM_vehicletype_sw_category, how='left', \
                                                              on=['MODEL_YEAR', 'CAFE_MFR_NM',
                                                                  'COMPLIANCE_CATEGORY_CD'])
                OEM_vehicletype_sw_max = OEM_vehicletype_sw_max.merge(OEM_vehicletype_sw_category_max, how='left', \
                                                                      on=['MODEL_YEAR', 'CAFE_MFR_NM',
                                                                          'COMPLIANCE_CATEGORY_CD'])
                OEM_vehicletype_sw_min = OEM_vehicletype_sw_min.merge(OEM_vehicletype_sw_category_min, how='left', \
                                                                      on=['MODEL_YEAR', 'CAFE_MFR_NM',
                                                                          'COMPLIANCE_CATEGORY_CD'])
                OEM_sw = OEM_sw.merge(OEM_sw_category, how='left', \
                                                  on=['MODEL_YEAR', 'CAFE_MFR_NM'])
                OEM_sw_max = OEM_sw_max.merge(OEM_sw_category_max, how='left', \
                                                          on=['MODEL_YEAR', 'CAFE_MFR_NM'])
                OEM_sw_min = OEM_sw_min.merge(OEM_sw_category_min, how='left', \
                                                          on=['MODEL_YEAR', 'CAFE_MFR_NM'])
                allOEM_vehicletype_sw = allOEM_vehicletype_sw.merge(allOEM_vehicletype_sw_category, how='left', \
                                                                    on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD'])
                allOEM_vehicletype_sw_max = allOEM_vehicletype_sw_max.merge(allOEM_vehicletype_sw_category_max,
                                                                            how='left', \
                                                                            on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD'])
                allOEM_vehicletype_sw_min = allOEM_vehicletype_sw_min.merge(allOEM_vehicletype_sw_category_min,
                                                                            how='left', \
                                                                            on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD'])
                allOEM_sw = allOEM_sw.merge(allOEM_sw_category, how='left', on=['MODEL_YEAR'])
                allOEM_sw_max = allOEM_sw_max.merge(allOEM_sw_category_max, how='left', on=['MODEL_YEAR'])
                allOEM_sw_min = allOEM_sw_min.merge(allOEM_sw_category_min, how='left', on=['MODEL_YEAR'])
            except NameError:
                OEM_vehicletype_sw = OEM_vehicletype_sw_category
                OEM_vehicletype_sw_max = OEM_vehicletype_sw_category_max
                OEM_vehicletype_sw_min = OEM_vehicletype_sw_category_min
                OEM_sw = OEM_sw_category
                OEM_sw_max = OEM_sw_category_max
                OEM_sw_min = OEM_sw_category_min
                allOEM_vehicletype_sw = allOEM_vehicletype_sw_category
                allOEM_vehicletype_sw_max = allOEM_vehicletype_sw_category_max
                allOEM_vehicletype_sw_min = allOEM_vehicletype_sw_category_min
                allOEM_sw = allOEM_sw_category
                allOEM_sw_max = allOEM_sw_category_max
                allOEM_sw_min = allOEM_sw_category_min

        OEM_vehicletype = OEM_vehicletype_bodyidcount.merge(OEM_vehicletype_cabinidcount, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM','COMPLIANCE_CATEGORY_CD']).merge(OEM_vehicletype_sales, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM','COMPLIANCE_CATEGORY_CD']).merge(OEM_vehicletype_emissions, \
            how='left', on = ['MODEL_YEAR', 'CAFE_MFR_NM','COMPLIANCE_CATEGORY_CD']).merge(OEM_vehicletype_sw,
            how='left', on=['MODEL_YEAR','CAFE_MFR_NM','COMPLIANCE_CATEGORY_CD']).merge(OEM_vehicletype_sw_max, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).merge(OEM_vehicletype_sw_min, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM','COMPLIANCE_CATEGORY_CD'])
        OEM = OEM_bodyidcount.merge(OEM_cabinidcount,\
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM']).merge(OEM_sales, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM']).merge(OEM_emissions, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM']).merge(OEM_sw, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM']).merge(OEM_sw_max, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM']).merge(OEM_sw_min, \
            how='left', on=['MODEL_YEAR', 'CAFE_MFR_NM'])
        allOEM_vehicletype = allOEM_vehicletype_bodyidcount.merge(allOEM_vehicletype_cabinidcount, \
            how='left', on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).merge(allOEM_vehicletype_sales, \
            how='left', on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).merge(allOEM_vehicletype_emissions, \
            how='left', on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).merge(allOEM_vehicletype_sw, \
            how='left', on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).merge(allOEM_vehicletype_sw_max, \
            how='left', on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD']).merge(allOEM_vehicletype_sw_min, \
            how='left', on=['MODEL_YEAR', 'COMPLIANCE_CATEGORY_CD'])
        allOEM = allOEM_bodyidcount.merge(allOEM_cabinidcount, \
            how='left', on=['MODEL_YEAR']).merge(allOEM_sales, \
            how='left', on=['MODEL_YEAR']).merge(allOEM_emissions, \
            how='left', on=['MODEL_YEAR']).merge(allOEM_sw, \
            how='left', on=['MODEL_YEAR']).merge(allOEM_sw_max, \
            how='left', on=['MODEL_YEAR']).merge(allOEM_sw_min, \
            how='left', on=['MODEL_YEAR'])
        OEM['COMPLIANCE_CATEGORY_CD'] = pd.Series(np.zeros(len(OEM))).replace(0,'')
        allOEM_vehicletype['CAFE_MFR_NM'] = pd.Series(np.zeros(len(allOEM_vehicletype))).replace(0, '')
        allOEM['COMPLIANCE_CATEGORY_CD'] = pd.Series(np.zeros(len(allOEM))).replace(0, '')
        allOEM['CAFE_MFR_NM'] = pd.Series(np.zeros(len(allOEM))).replace(0, '')
        del OEM_vehicletype_sw,OEM_vehicletype_sw_max,OEM_vehicletype_sw_min,OEM_sw,OEM_sw_max,OEM_sw_min,\
            allOEM_vehicletype_sw,allOEM_vehicletype_sw_max,allOEM_vehicletype_sw_min, allOEM_sw, allOEM_sw_max, \
            allOEM_sw_min

        data_array_fromfile = pd.concat([OEM_vehicletype, allOEM_vehicletype, OEM, allOEM]).reset_index(drop=True)
        try:
            data_array_output = pd.concat([data_array_output, data_array_fromfile]).reset_index(drop=True)
        except NameError:
            data_array_output = data_array_fromfile
        del OEM_vehicletype, OEM, allOEM_vehicletype, allOEM
    data_array_output_data_columns = sorted(list(set(data_array_output.columns).difference(set(list(OEM_vehicletype_list)))))
    data_array_output = data_array_output[list(OEM_vehicletype_list) + list(data_array_output_data_columns)]

    data_array_output['CAFE_MFR_NM'][data_array_output['CAFE_MFR_NM']==''] = 'All Manufacturers'
    data_array_output['COMPLIANCE_CATEGORY_CD'][data_array_output['COMPLIANCE_CATEGORY_CD'] == ''] = 'All'
    data_array_output['MODEL_YEAR'] = data_array_output['MODEL_YEAR'].astype(int)
    combined_file['CAFE_MFR_NM'] = combined_file['CAFE_MFR_NM'].replace('Volkswagen Group of America, Inc.', 'Volkswagen')
    data_array_output['CAFE_MFR_NM'] = data_array_output['CAFE_MFR_NM'].replace('Volkswagen Group of America, Inc.', 'Volkswagen')
    data_array_output['New BodyID Count'] = pd.Series(np.zeros(len(data_array_output))).replace(0,'NA')
    data_array_output['New CabinID Count'] = pd.Series(np.zeros(len(data_array_output))).replace(0,'NA')
    min_model_year = data_array_output['MODEL_YEAR'].min()
    for output_count in range (0,len(data_array_output)):
        model_year = data_array_output['MODEL_YEAR'][output_count]
        if model_year > min_model_year:
            OEM = data_array_output['CAFE_MFR_NM'][output_count]
            vehicle_type = data_array_output['COMPLIANCE_CATEGORY_CD'][output_count]
            present_model_year_combined_file = combined_file[combined_file['MODEL_YEAR']==model_year]
            past_model_year_combined_file = combined_file[combined_file['MODEL_YEAR'] == model_year-1]
            past_OEMs = past_model_year_combined_file['CAFE_MFR_NM']
            if model_year == 2013 and OEM == 'Jaguar Land Rover Limited':
                past_OEMs = past_OEMs.replace(['Jaguar Cars Limited', 'Land Rover'], 'Jaguar Land Rover Limited')
            if OEM == 'All Manufacturers' and vehicle_type == 'All':
                present_bodyids = present_model_year_combined_file['BodyID']
                past_bodyids = past_model_year_combined_file['BodyID']
                present_cabinids = present_model_year_combined_file['CabinID']
                past_cabinids = past_model_year_combined_file['CabinID']
            elif OEM == 'All Manufacturers' and vehicle_type != 'All':
                present_bodyids = present_model_year_combined_file['BodyID'][present_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type]
                past_bodyids = past_model_year_combined_file['BodyID'][past_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type]
                present_cabinids = present_model_year_combined_file['CabinID'][present_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type]
                past_cabinids = past_model_year_combined_file['CabinID'][past_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type]
            elif vehicle_type == 'All':
                present_bodyids = present_model_year_combined_file['BodyID'][present_model_year_combined_file['CAFE_MFR_NM'] == OEM]
                past_bodyids = past_model_year_combined_file['BodyID'][past_model_year_combined_file['CAFE_MFR_NM'] == OEM]
                present_cabinids = present_model_year_combined_file['CabinID'][present_model_year_combined_file['CAFE_MFR_NM'] == OEM]
                past_cabinids = past_model_year_combined_file['CabinID'][past_model_year_combined_file['CAFE_MFR_NM'] == OEM]
            else:
                present_bodyids = present_model_year_combined_file['BodyID'][(present_model_year_combined_file['CAFE_MFR_NM'] == OEM) & (present_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type)]
                past_bodyids = past_model_year_combined_file['BodyID'][(past_model_year_combined_file['CAFE_MFR_NM'] == OEM) & (past_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type)]
                present_cabinids = present_model_year_combined_file['CabinID'][(present_model_year_combined_file['CAFE_MFR_NM'] == OEM) & (present_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type)]
                past_cabinids = past_model_year_combined_file['CabinID'][(past_model_year_combined_file['CAFE_MFR_NM'] == OEM) & (past_model_year_combined_file['COMPLIANCE_CATEGORY_CD'] == vehicle_type)]
            if OEM == 'All Manufacturers' or sum(past_OEMs == OEM)>0:
                data_array_output['New BodyID Count'][output_count] = sum(~present_bodyids.isin(past_bodyids))
                data_array_output['New CabinID Count'][output_count] = sum(~present_cabinids.isin(past_cabinids))
    date_and_time = str(datetime.datetime.now())[:17].replace(':', '').replace('-', '')
    data_array_output.to_csv(output_path+'\\'+'OEM ModelYear Stats '+date_and_time+'.csv', index=False)
