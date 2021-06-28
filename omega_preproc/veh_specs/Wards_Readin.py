#def Wards_Readin(input_path, output_path, inputsheet_path, input_filename, bodyid_filename):
def Wards_Readin(rawdata_input_path, run_input_path, input_filename, output_path, exceptions_table, bodyid_filename, \
                 matched_bodyid_filename, unit_table, year, ftp_drivecycle_filename, hwfet_drivecycle_filename, \
                 ratedhp_filename, lineageid_filename):
    #Read in the Wards Auto Data File and compile the information within it in order to help create an
    # overall data sheet for the U.S. 2016 automotive vehicle fleet
    import pandas as pd
    import numpy as np
    import datetime
    #I:\Project\Midterm Review\Trends\Trends Data\Wards\U.S. Car and Light Truck Specifications and Prices
    save_name = 'Wards Readin MY' + str(year)

    if type(exceptions_table) != str:
        exceptions_table = exceptions_table.astype(str)
        exceptions_table_columns = exceptions_table[exceptions_table['Column Name Change?'] == 'y'].reset_index(drop=True)
        exceptions_table_makeseries = exceptions_table[exceptions_table['Column Name'] == 'MAKE & SERIES'].reset_index(drop=True)
        exceptions_table_other = exceptions_table[(exceptions_table['Column Name Change?'] != 'y') \
            & (exceptions_table['Column Name'] != 'MAKE & SERIES')].replace('"--"','--').reset_index(drop=True)
    if year < 2014:
        sheetname_vec = pd.Series(['Car', 'Light Truck', 'EV']) #Define Sheetnames
        electric_sheetname = 'EV'
    else:
        sheetname_vec = pd.Series(['Car', 'Light Truck', 'Electric']) #Define Sheetnames
        electric_sheetname = 'Electric'
    make_vec = pd.Series(['ACURA', 'ALFA ROMEO', 'AUDI', 'BENTLEY', 'BMW', 'BUICK', 'CADILLAC', 'CHEVROLET', 'CHRYSLER', \
                'CODA', 'DODGE', 'FIAT', 'FORD', 'GMC', 'HONDA', 'HYUNDAI', 'INFINITI', 'JAGUAR', 'JEEP', 'KIA', 'LAND ROVER', \
                'LEXUS', 'LINCOLN', 'MAZDA', 'MERCEDES-BENZ', 'MINI', 'MITSUBISHI', 'NISSAN', 'PORSCHE', 'RAM',\
                'ROLLS-ROYCE', 'SCION', 'SMART', 'SUBARU', 'SUZUKI', 'TESLA', 'TOYOTA', 'VOLKSWAGEN', 'VOLVO', 'WHEEGO']) #All Vehicle Makes
    mfr_vec = pd.Series(['Honda', 'FCA', 'Volkswagen', 'Volkswagen', 'BMW', 'GM', 'GM', 'GM', 'FCA', \
                'Coda', 'FCA', 'FCA', 'Ford', 'GM', 'Honda', 'Hyundai-Kia', 'Nissan', 'JLR', 'FCA', 'Hyundai-Kia', 'JLR', \
                'Toyota', 'Ford', 'Mazda', 'Mercedes-Benz', 'BMW', 'Mitsubishi', 'Nissan', 'Volkswagen', 'FCA', \
                 'BMW','Toyota', 'Mercedes-Benz', 'Subaru', 'Suzuki', 'Tesla', 'Toyota', 'Volkswagen', 'Volvo', 'Wheego']) #Corresponding Vehicle Manufacturers to Make Vec
    top_title_vec = pd.Series(['Wheel', 'Track', 'Overall Size', 'Curb', 'Box', 'Gross', 'Maximum']) #Category Title segments above Make & Series
    repeat_subtitle_vec = pd.Series(['RPM', 'Liter', 'Intake', 'Opt.', 'Volts', 'kWh', 'Km.']) #Category Title segments in line with Make & Series that are used in multiple categories
    for i in range (0,len(sheetname_vec)):
        readin_sheet = pd.read_excel(rawdata_input_path+'\\'+input_filename,sheetname=sheetname_vec[i]) #Read in worksheet
        readin_sheet = readin_sheet.dropna(axis=1, how='all').reset_index(drop=True).astype(str) #Drop clumns with no values
        readin_sheet[readin_sheet.select_dtypes(['object']).columns] = \
            readin_sheet.select_dtypes(['object']).apply(lambda x: x.str.strip()) #Apply str.strip to all entries
        readin_sheet[readin_sheet == 'nan'] = '' #Replace NaN blanks (blanks in original spreadsheet) with empty cells
        first_column = readin_sheet.ix[:,0] #Pull out first column
        makeseries_index = first_column[first_column == 'MAKE & SERIES'].index[0] #Find the 'MADE & SERIES' value in first column (reference point)
        sheet_colcount = readin_sheet.shape[1] #Number of columns
        colname_vec = pd.Series(np.zeros(sheet_colcount)) #Initialize names for specific worksheet output

        if sheetname_vec[i] == electric_sheetname:
            if year == 2013:
                datastart_index = int(first_column[first_column == 'CHEVROLET'].index[0]) #First make (for Electric only)
            else:
                datastart_index = int(first_column[first_column == 'BMW'].index[0])  # First make (for Electric only)
        else:
            datastart_index = int(first_column[first_column == 'ACURA'].index[0]) #First make

        dataend_index = int((first_column[first_column.str.contains('SPECIFICATIONS SHOWN')].index[0])-1) #Find end of range of actual data

        for j in range (0,sheet_colcount):
            iterative_col = readin_sheet.ix[:,j] #Desired column for a paricular name
            if str(iterative_col[makeseries_index-1]) == '' and str(iterative_col[makeseries_index]) == '':
                if repeat_subtitle_vec.isin([str(iterative_col[makeseries_index+1])]).sum() > 0 :
                    if str(iterative_col[makeseries_index+1]) == 'kWh':
                        colname_vec[j] = str(readin_sheet.ix[:, j-2][makeseries_index]) + ' (' + str(iterative_col[makeseries_index + 1])  + ')'# Obtain name of columns
                    else:
                        colname_vec[j] = str(readin_sheet.ix[:,j-1][makeseries_index]) + ' (' + str(iterative_col[makeseries_index + 1]) + ')' # Obtain name of columns
                        colname_vec[j-1] = str(readin_sheet.ix[:,j-1][makeseries_index]) + ' (' + str(readin_sheet.ix[:,j-1][makeseries_index + 1]) + ')' # Obtain name of columns
                else:
                    colname_vec[j] = str(iterative_col[makeseries_index+1]) #Obtain name of columns
            elif str(iterative_col[makeseries_index-1]) == '' and str(iterative_col[makeseries_index]) != '':
                if str(iterative_col[makeseries_index + 1]) == '':
                    colname_vec[j] = str(iterative_col[makeseries_index])#Obtain name of columns
                elif str(iterative_col[makeseries_index + 1]) == 'Std.':
                    colname_vec[j] = str(readin_sheet.ix[:, j][makeseries_index]) + ' (' + str(iterative_col[makeseries_index + 1]) + ')'
                elif str(iterative_col[makeseries_index + 1]) == '(ins.)': #Carry Over Subtitle
                    colname_vec[j] = colname_vec[j-1][0:colname_vec[j-1].find(' ')] + ' ' + str(iterative_col[makeseries_index]) + ' ' \
                                     + str(iterative_col[makeseries_index + 1])  # Obtain name of columns
                else:
                    colname_vec[j] = str(iterative_col[makeseries_index]) + ' ' \
                                     + str(iterative_col[makeseries_index + 1])  # Obtain name of columns
            else:
                if top_title_vec.isin([str(iterative_col[makeseries_index - 1])]).sum() > 0:
                    colname_vec[j] = str(iterative_col[makeseries_index - 1]) + ' ' + str(
                        iterative_col[makeseries_index]) + ' ' \
                                     + str(iterative_col[makeseries_index + 1])  # Obtain name of columns
                else:
                    colname_vec[j] = str(iterative_col[makeseries_index]) + ' ' \
                                     + str(iterative_col[makeseries_index + 1])  # Obtain name of columns
        colname_vec = colname_vec.replace('EPA MPGe City/Hwy','Est. MPG City/Hwy').str.strip().str.replace('  ', ' ')
        if type(exceptions_table) != str:
            exceptions_table_columns_sheetname = exceptions_table_columns[\
                exceptions_table_columns['Sheet Name'] == sheetname_vec[i]].reset_index(drop=True)
            for error_check_count in range(0,len(exceptions_table_columns_sheetname)):
                colname_vec = colname_vec.replace(str(exceptions_table_columns_sheetname['Old Value'][error_check_count]), \
                                                  str(exceptions_table_columns_sheetname['New Value'][error_check_count]))
        readin_sheet_data = readin_sheet.loc[datastart_index:dataend_index].reset_index(drop=True)
        readin_sheet_data.columns = colname_vec
        make_output_vec = pd.Series(np.zeros(len(readin_sheet_data)), name = 'Make')
        model_output_vec = pd.Series(np.zeros(len(readin_sheet_data)), name = 'Model')
        mfr_output_vec = pd.Series(np.zeros(len(readin_sheet_data)), name='Manufacturer')
        engine_notes = pd.Series(['']*len(readin_sheet_data), name='Engine Notes')
        makemodel_data = readin_sheet_data.ix[:,0]
        empty_check = readin_sheet_data.ix[:,2]
        empty_check = readin_sheet_data.ix[:,2]
        for j in range (0,len(readin_sheet_data)):
            if readin_sheet_data.ix[:,1][j] == '' and empty_check[j] == '--':
                empty_check[j] = ''
            if empty_check[j] == '': #Either make or model
                if j != len(readin_sheet_data)-1 and (make_vec == makemodel_data[j].strip().upper()).astype(int).astype(float).sum() > 0: #Make
                    current_make = makemodel_data[j].strip().upper()
                    current_mfr = mfr_vec[mfr_vec[make_vec == current_make].index[0]]
                elif j != len(readin_sheet_data)-1 and empty_check[j+1] != '': #Potential Model
                    if empty_check[j-1] == '' and makemodel_data[j-1] != current_make and (',' in makemodel_data[j-1]) == False: #Remove 'Over 8,500'-like labels
                        current_model = makemodel_data[j-1] + ' ' + makemodel_data[j]
                    else:
                        current_model = makemodel_data[j]
            make_output_vec[j] = current_make
            mfr_output_vec[j] = current_mfr
            if current_make != makemodel_data[j]:
                model_output_vec[j] = current_model
        if sheetname_vec[i] == electric_sheetname: #Engine Specific Details
            engine_data_col = readin_sheet_data['Electric Motor Type']
        else:
            engine_data_col = readin_sheet_data['Cyl & Type']
        makeseries_col = readin_sheet_data['MAKE & SERIES']
        readin_sheet_data_filtered = readin_sheet_data\
            [pd.isnull(engine_data_col)==False].reset_index(drop=True) #Significant data from readin sheet
        for j in range(0,len(colname_vec)): #Column index
            output_col = pd.Series(np.zeros(len(readin_sheet_data_filtered)), name = colname_vec[j]) #column for worksheet output
            data_col = readin_sheet_data_filtered.ix[:,j] #Desired data column
            for k in range (0,len(readin_sheet_data_filtered)): #Row index
                output_col[k] = data_col[k]
                # if colname_vec[j] == 'MAKE & SERIES':
                #     if (readin_sheet_data_filtered['Model'][k] in data_col[k] == False) : #Missing Overall Model Name
                #         output_col[k] = readin_sheet_data_filtered.ix[:,j-1][k] + ' ' + data_col[k]
                if data_col[k].find(' (1)') > 0: #Entry has footnotes from Wards datasheet
                    output_col[k] = (data_col[k][:data_col[k].find(' (1)')]).replace(',','')
                if ('Engine' in makeseries_col[k]) == True or ('Package' in makeseries_col[k]) == True:  #'Optional Engine' entry
                    if ('Engine' in makeseries_col[k-1]) == False and ('Package' in makeseries_col[k-1]) == False: #Previous item is the base model
                        base_model = makeseries_col[k-1]
                    if colname_vec[j] == 'MAKE & SERIES': #Update Model Name
                        output_col[k] = str(base_model + ' ' + data_col[k])
                    elif str(colname_vec[j]) == 'Track Front (ins.)' or str(colname_vec[j]) == 'Track Rear (ins.)' and data_col[k] == '':
                        output_col[k] = output_col[k-1]
                if ('--' in data_col[k]) == True and (sheetname_vec[i] == electric_sheetname or ('Engine' in makeseries_col[k]) == True or ('Package' in makeseries_col[k]) == True): #Similar series to a previous entry
                    if colname_vec[j] != 'Retail Price ($)' and colname_vec[j] != 'Transmission (Opt.)': #Don't carry over retail price or optional transmission from min entry
                        output_col[k] = str(output_col[k-1])
                elif colname_vec[j] == 'Cyl & Type': #Additional Engine Information (usually motors for hybrids)
                    if k != len(readin_sheet_data_filtered) -1 and makeseries_col[k+1] == '--':
                        engine_notes[k] = str(data_col[k+1]) #Add hybrid engine details
            if j == 0: #Create worksheet output
                Wards_readin_output = output_col
            else:
                Wards_readin_output = pd.concat([Wards_readin_output, output_col],axis=1)

        if sheetname_vec[i] != electric_sheetname: #Add in engine notes (not originally in Wards data)
            Wards_readin_output.insert(1+int(colname_vec[colname_vec == 'Cyl & Type'].index[0]), \
                                       'Engine Notes', engine_notes) #Add Engine Notes
        make_vec_filtered = make_output_vec[pd.isnull(engine_data_col) == False].reset_index(drop=True) #Add Make
        model_vec_filtered = model_output_vec[pd.isnull(engine_data_col)==False].reset_index(drop=True) #Add Model
        mfr_vec_filtered = mfr_output_vec[pd.isnull(engine_data_col) == False].reset_index(drop=True)  # Add Manufacturer
        sheet_type_vec = pd.Series([sheetname_vec[i]]*len(Wards_readin_output), name = 'Vehicle Type (Wards Sheet)') #Add car/truck/electric sheet type
        Wards_readin_output = pd.concat([sheet_type_vec,mfr_vec_filtered, make_vec_filtered, model_vec_filtered, \
                                         Wards_readin_output],axis=1)
        if type(exceptions_table) != str:
            exceptions_table_makeseries_sheetname = exceptions_table_makeseries[\
                exceptions_table_makeseries['Sheet Name'] == sheetname_vec[i]].reset_index(drop=True)
            exceptions_table_other_sheetname = exceptions_table_other[ \
                exceptions_table_other['Sheet Name'] == sheetname_vec[i]].reset_index(drop=True)
            for error_check_count in range (0,len(exceptions_table_makeseries_sheetname)):
                Wards_readin_output.loc[
                    (Wards_readin_output['Model'] == exceptions_table_makeseries_sheetname['Model'][error_check_count]) & \
                    (Wards_readin_output['MAKE & SERIES'] == exceptions_table_makeseries_sheetname['Make and Series'][error_check_count]) & \
                    (Wards_readin_output[exceptions_table_makeseries_sheetname['Column Name'][error_check_count]] ==
                     exceptions_table_makeseries_sheetname['Old Value'][error_check_count]), \
                    exceptions_table_makeseries_sheetname['Column Name'][error_check_count]] = \
                    exceptions_table_makeseries_sheetname['New Value'][error_check_count]
            for error_check_count in range(0, len(exceptions_table_other_sheetname)):
                Wards_readin_output.loc[
                    (Wards_readin_output['Model'] == exceptions_table_other_sheetname['Model'][
                        error_check_count]) & \
                    (Wards_readin_output['MAKE & SERIES'] ==
                     exceptions_table_other_sheetname['Make and Series'][error_check_count]) & \
                    (Wards_readin_output[exceptions_table_other_sheetname['Column Name'][error_check_count]] ==
                     exceptions_table_other_sheetname['Old Value'][error_check_count]), \
                    exceptions_table_other_sheetname['Column Name'][error_check_count]] = \
                    exceptions_table_other_sheetname['New Value'][error_check_count]

                    #& (Wards_readin_output[exceptions_table_makeseries_sheetname['Column Name'][error_check_count]] ==exceptions_table_makeseries_sheetname['Old Value'][error_check_count])]
            for error_check_count in range (0,len(exceptions_table_other_sheetname)):
                Wards_readin_output.loc[(Wards_readin_output['Model'] == exceptions_table_other_sheetname['Model'][error_check_count])& \
                    (Wards_readin_output['MAKE & SERIES'] == exceptions_table_other_sheetname['Make and Series'][error_check_count])\
                    ,exceptions_table_other_sheetname['Column Name'][error_check_count]] = exceptions_table_other_sheetname['New Value'][error_check_count]
        #Wards_readin_output = Wards_readin_output.replace([np.nan, str(np.nan)], '')
        Wards_readin_output = Wards_readin_output.dropna(axis=1,how='all')
        try:
            Wards_readin_output = Wards_readin_output.drop('280.0',axis=1)
            Wards_readin_output = Wards_readin_output.drop('', axis=1)
        except ValueError:
            pass
        Wards_readin_output = Wards_readin_output[~pd.isnull(Wards_readin_output['Drive Type'])].reset_index(drop=True)
        if sheetname_vec[i] != electric_sheetname:
            Wards_readin_output = Wards_readin_output[Wards_readin_output['Size (Liter)'] != ''].reset_index(drop=True)
        if sheetname_vec[i] != electric_sheetname: #Remove duplicate entries from Electric sheet
            Wards_readin_output = Wards_readin_output[(Wards_readin_output['MAKE & SERIES'] != '--') & (Wards_readin_output['MAKE & SERIES'] != '')].reset_index(drop=True)
        if i == 0: #Create final output array from worksheet outputs
            Wards_readin_final_output = Wards_readin_output
        else:
            merging_columns = pd.Series(list(set(Wards_readin_final_output.columns)-(set(Wards_readin_final_output.columns)-set(Wards_readin_output))))
            merging_columns = list(merging_columns[merging_columns != ''])
            Wards_readin_final_output = pd.merge_ordered(Wards_readin_final_output, Wards_readin_output, how='outer', \
                on=merging_columns)
            # concat_start = len(Wards_readin_final_output)
            # extension_array = pd.DataFrame(np.zeros([len(Wards_readin_output),Wards_readin_final_output.shape[1]]), columns = Wards_readin_final_output.columns)
            # Wards_readin_final_output = pd.concat([Wards_readin_final_output,extension_array]).reset_index(drop=True) #Extend final output
            # output_columns = pd.Series(Wards_readin_output.columns.values)
            # for k in range (0,Wards_readin_output.shape[1]):
            #     try:
            #         Wards_readin_final_output.loc[concat_start:, output_columns[k]] = pd.Series(Wards_readin_output[output_columns[k]]).tolist()
            #     except KeyError: #Add new columns in
            #         Wards_readin_final_output.insert(Wards_readin_final_output.shape[1],output_columns[k],Wards_readin_output[output_columns[k]])
            #         Wards_readin_final_output[output_columns[k]].loc[0:concat_start] = ''
            #         Wards_readin_final_output.loc[concat_start:, output_columns[k]] = pd.Series(Wards_readin_output[output_columns[k]]).tolist()
            #     Wards_readin_final_output = Wards_readin_final_output.reset_index(drop=True)
    #Separate data from estimated fuel economy and cylinder/cam data column in Wards
    cyltype_vec = Wards_readin_final_output['Cyl & Type'].astype(str)
    eng_arrange_vec = pd.Series(np.zeros(len(Wards_readin_final_output)), name = 'ENG_BLOCK_ARRANGEMENT_CD').astype(str)
    cyl_num_vec = pd.Series(np.zeros(len(Wards_readin_final_output)), name = 'NUM_CYLINDRS_ROTORS').astype(str)
    valve_vec = pd.Series(np.zeros(len(Wards_readin_final_output)), name = 'Valve Actuation').astype(str)
    city_est = pd.Series(np.zeros(len(Wards_readin_final_output)), name = 'Est. MPG City')
    hwy_est = pd.Series(np.zeros(len(Wards_readin_final_output)), name = 'Est. MPG Hwy')
    comb_est = pd.Series(np.zeros(len(Wards_readin_final_output)), name='Est. MPG Comb')
    city_hwy = pd.Series(Wards_readin_final_output['Est. MPG City/Hwy'])
    for i in range (0,len(Wards_readin_final_output)): #Cylinder/cam layout
        cyltype = str(cyltype_vec[i])
        space_index = cyltype.find(' ')
        dash_index = cyltype.find('-')
        if dash_index > 0:
            valve_vec[i] = cyltype[:space_index]
            eng_arrange_vec[i] = cyltype[space_index + 1:dash_index]
            cyl_num_vec[i] = cyltype[1 + dash_index:]
        else:
            valve_vec[i] = ''
            eng_arrange_vec[i] = ''
            cyl_num_vec[i] = ''
        city_est[i] = str(city_hwy[i])[:int(str(city_hwy[i]).find('/'))]  # City estimated MPG
        hwy_est[i] = str(city_hwy[i])[1 + int(str(city_hwy[i]).find('/')):]  # Hwy estimated MPG
        if str(city_est[i]).find('e') > 0:
            city_est[i] = city_hwy[i][:int(city_hwy[i].find('/'))-1]  # City estimated MPG
        if str(hwy_est[i]).find('e') > 0:
            hwy_est[i] = city_hwy[i][1 + int(city_hwy[i].find('/')):len(city_hwy[i])-1]  # Hwy estimated MPG
        try:
            comb_est[i] = round(((0.55/int(city_est[i]))+(0.45/int(hwy_est[i])))**-1,0)
        except ValueError:
            comb_est[i] = ''
    final_names = pd.Series(Wards_readin_final_output.columns) #Add in new separated columns after their original counterparts
    Wards_readin_final_output.insert(1+int(final_names[final_names == 'Est. MPG City/Hwy'].index[0]), 'Est. MPG City', city_est)
    Wards_readin_final_output.insert(2+int(final_names[final_names == 'Est. MPG City/Hwy'].index[0]), 'Est. MPG Hwy', hwy_est)
    Wards_readin_final_output.insert(3 + int(final_names[final_names == 'Est. MPG City/Hwy'].index[0]), 'Est. MPG Comb',comb_est)
    Wards_readin_final_output.insert(1+int(final_names[final_names == 'Cyl & Type'].index[0]), 'ENG_BLOCK_ARRANGEMENT_CD', eng_arrange_vec)
    Wards_readin_final_output.insert(2+int(final_names[final_names == 'Cyl & Type'].index[0]), 'NUM_CYLINDRS_ROTORS', cyl_num_vec)
    Wards_readin_final_output.insert(3+int(final_names[final_names == 'Cyl & Type'].index[0]), 'Valve Actuation',valve_vec)

    Wards_readin_final_output = Wards_readin_final_output[Wards_readin_final_output['Drive Type'] != '']\
        .replace(['     ','    ','   ', '  ','e/'], [' ',' ',' ',' ','/'], regex=True)\
        #.sort_values(['Manufacturer','Make', 'Model', 'MAKE & SERIES']).reset_index(drop=True) #Cleanup
    Wards_readin_final_output = Wards_readin_final_output.replace(['.', '0',0],['','','']) #Cleanup

    Wards_readin_final_output = Wards_readin_final_output.drop(['Est. MPG City/Hwy'],1) #Remove city/highway column (formattign errors in Excel)
    Wards_readin_final_output.columns = pd.Series(Wards_readin_final_output.columns.values).replace(['     ','    ','   ', '  '], ['','','',''], regex=True).reset_index(drop=True)
    #Wards_readin_final_output = pd.concat([pd.Series(range(len(Wards_readin_final_output)), name = 'Index (Wards)')+1,Wards_readin_final_output],axis=1) #Add numerical index for Wards
    Wards_readin_final_output['Size (Liter)'] = Wards_readin_final_output['Size (Liter)'].replace(['',np.nan,str(np.nan)],0)
    Wards_readin_final_output['Size (CC)']= Wards_readin_final_output['Size (CC)'].replace(['',np.nan,str(np.nan)],0)

    engine_info_datasheet = pd.Series(Wards_readin_final_output['ENG_BLOCK_ARRANGEMENT_CD'] + Wards_readin_final_output['NUM_CYLINDRS_ROTORS'] + '-' \
                            + (Wards_readin_final_output['Size (Liter)'].astype(float)).astype(str) + 'L' , name = 'Engine ID')
    engine_info_datasheet[Wards_readin_final_output['NUM_CYLINDRS_ROTORS']==''] = 'ELE'
    Wards_readin_final_output = Wards_readin_final_output.replace('  ', ' ')
    Wards_readin_final_output = pd.concat([Wards_readin_final_output, engine_info_datasheet], axis=1)

    #Add new entries for new transmission options
    extra_trans_array = Wards_readin_final_output[(Wards_readin_final_output['Transmission (Opt.)'] != '--')\
                                                  & (Wards_readin_final_output['Transmission (Opt.)'] != '')].reset_index(drop=True)
    extra_trans_array['Transmission (Std.)'] = pd.Series(extra_trans_array['Transmission (Opt.)'], name = 'Transmission (Std.)').reset_index(drop=True)
    Wards_readin_final_output = pd.concat([Wards_readin_final_output,extra_trans_array]).reset_index(drop=True)
    Wards_readin_final_output = Wards_readin_final_output.drop(['Transmission (Opt.)'],1)\
        .rename(index=str, columns={'Transmission (Std.)':'Transmission'})
    Wards_readin_final_output['Transmission'] = Wards_readin_final_output['Transmission'].replace('1', 'A1')

    # Add new entries for new fuel options
    Wards_readin_final_output['Fuel Type'][Wards_readin_final_output['Vehicle Type (Wards Sheet)'] == electric_sheetname] = 'Z'
    for split_type in ['/',',']:
        extra_fuel_array = Wards_readin_final_output[Wards_readin_final_output['Fuel Type'].str.contains(split_type)].reset_index(drop=True)
        split_list = extra_fuel_array['Fuel Type'].str.split(split_type)
        max_length = extra_fuel_array['Fuel Type'].str.count(split_type).max()+1
        if pd.isnull(max_length) != True:
            for fuel_count in range(0,int(max_length)):
                extra_fuel_array['Fuel Type'] = pd.Series([item[fuel_count].strip() for item in split_list], name = 'Fuel Type').str.strip().reset_index(drop=True)
                if fuel_count == 0:
                    extra_array = extra_fuel_array
                else:
                    extra_array = pd.concat([extra_array, extra_fuel_array]).reset_index(drop=True)
            full_fuel_array = pd.concat([Wards_readin_final_output[~(Wards_readin_final_output['Fuel Type'].str.contains('/'))\
                                                          & ~(Wards_readin_final_output['Fuel Type'].str.contains(','))], extra_array]).reset_index(drop=True)
            Wards_readin_final_output = full_fuel_array

    Wards_readin_final_output['Transmission'] = Wards_readin_final_output['Transmission'].str.replace('AMT','AM')
    Wards_readin_final_output = Wards_readin_final_output.sort_values(['Manufacturer','Make', 'Model', 'MAKE & SERIES', 'Transmission', 'Fuel Type']).reset_index(drop=True)
    Wards_readin_final_output = Wards_readin_final_output.drop([''], axis=1, errors='ignore')
    #Wards_readin_final_output.to_csv(output_path + '\\' + save_name, index=False)
    Wards_readin_final_output = Wards_readin_final_output.drop_duplicates(keep='first').reset_index(drop=True)
    Wards_readin_final_output = Wards_readin_final_output.replace('',np.nan).dropna(axis=1, how='all').replace(np.nan,'').reset_index(drop=True)
    Wards_readin_final_output = Wards_readin_final_output[Wards_readin_final_output['Transmission'] != ''].reset_index(drop=True)
    #Matching Categories
    # import Model_Matching
    # lineage_table = pd.read_excel('I:\Project\Midterm Review\Trends\Original Trends Team Data Gathering and Analysis\Lineage\Lineage Database Tables\BodyID.xlsx')
    # bodyid_file = pd.read_csv(run_input_path+'\\'+bodyid_filename, converters = {'LineageID':int, 'BodyID':int})
    matching_cyl_layout = pd.Series(Wards_readin_final_output['ENG_BLOCK_ARRANGEMENT_CD'], name='Cylinder Layout Category').replace(['',np.nan,str(np.nan)],'ELE')
    matching_cyl_num = pd.Series(Wards_readin_final_output['NUM_CYLINDRS_ROTORS'], name='Number of Cylinders Category').replace('', 0).astype(float).astype(int)
    matching_eng_disp = pd.Series(Wards_readin_final_output['Size (Liter)'], name='Engine Displacement Category').replace('',0).astype(float).round(1)
    matching_drvtrn_layout = pd.Series(Wards_readin_final_output['Drive Type'], name = 'Drivetrain Layout Category').astype(str).replace(['FWD', 'RWD'], '2WD').replace(['AWD', '4WD'], '4WD')
    matching_trns_numgears = pd.Series(Wards_readin_final_output['Transmission'].astype(str).str[-1], name='Number of Transmission Gears Category').replace(['T', 'V'],1)
    matching_trns_numgears[Wards_readin_final_output['Transmission'] == 'SCV'] = 1
    matching_trns_numgears[Wards_readin_final_output['Transmission'] == 'A6/HD'] = 6
    matching_trns_numgears = matching_trns_numgears.astype(int)
    matching_trns_category = pd.Series(Wards_readin_final_output['Transmission'].astype(str).str[:-1], name='Transmission Type Category').replace(['DCT', 'A1/A'],['AM', 'A']).replace(['CV', 'SC'],'CVT')
    matching_trns_category[Wards_readin_final_output['Transmission'] == 'A6/HD'] = 'A'
    matching_trns_category[matching_trns_numgears == 1] = '1ST'
    matching_boost_category = pd.Series(Wards_readin_final_output['Fuel Sys. (Intake)'], name='Boost Type Category').astype(str).str.upper().replace(['T', '2T'], 'TC').replace('S', 'SC').replace('T/S', 'TS').replace('', 'ELE')
    matching_mfr_category = pd.Series(Wards_readin_final_output['Make'], name='Make Category').astype(str).str.upper()
    matching_fuel_category = pd.Series(Wards_readin_final_output['Fuel Type'].astype(str).str[0], name='Fuel Type Category').replace(['E'], 'G').replace(['C'],'CNG').replace(['B'], 'D').replace('Z','E')
    Wards_readin_final_output['Fuel Type'] = Wards_readin_final_output['Fuel Type'].replace(['Z'], 'E')
    electrification_categrory = pd.Series(np.zeros(len(Wards_readin_final_output)), name = 'Electrification Category').replace(0,'N')
    electrification_categrory[Wards_readin_final_output['Vehicle Type (Wards Sheet)'] == electric_sheetname] = 'EV'
    electrification_categrory[(Wards_readin_final_output['Vehicle Type (Wards Sheet)'] != electric_sheetname) & (city_hwy.str.contains('e'))] = 'REEV'
    electrification_categrory[(electrification_categrory == 'N') & (Wards_readin_final_output['Engine Notes'] != '') \
                              & (Wards_readin_final_output['Engine Notes'] != '--')] = 'HEV'
    Wards_readin_final_output = pd.concat([Wards_readin_final_output, matching_cyl_layout, matching_cyl_num, \
                                           matching_eng_disp, matching_drvtrn_layout, matching_trns_category, \
                                           matching_trns_numgears, matching_boost_category, matching_mfr_category, \
                                           matching_fuel_category, electrification_categrory],axis=1)
    if matched_bodyid_filename == 'N':
        draft_lineageid_file = Wards_readin_final_output[['Manufacturer', 'Make', 'Model', 'MAKE & SERIES', 'Body Style', 'Wheel Base (ins.)', 'Transmission']]\
            .groupby(['Manufacturer', 'Make', 'Model', 'MAKE & SERIES', 'Body Style', 'Wheel Base (ins.)']).first().reset_index().drop('Transmission',axis=1)
        draft_lineageid_file.to_csv(output_path+'\\'+'Wards MY'+str(year)+' LineageID.csv', index=False)
    else:
        bodyid_file = pd.read_csv(run_input_path + '\\' + matched_bodyid_filename, converters={'LineageID': int, 'BodyID': int, 'Model Year':int})
        bodyid_file = bodyid_file.groupby(['Model Year', 'Manufacturer', 'Make', 'Model', 'MAKE & SERIES', 'Body Style', 'Wheel Base (ins.)']).first().reset_index()
        bodyid_file = bodyid_file[(bodyid_file['LineageID'] != -9) & (bodyid_file['Model Year'] == year)].reset_index(drop=True)
        body_id_table_readin = pd.read_csv(run_input_path + '\\' + bodyid_filename, \
                                             converters={'LineageID': int, 'BodyID': int})
        body_id_table_readin = body_id_table_readin[body_id_table_readin['EndYear'] != 'xx'].reset_index(drop=True)
        body_id_table_int = body_id_table_readin[(~pd.isnull(body_id_table_readin['EndYear'])) \
                                                 & (body_id_table_readin['StartYear'] <= year)].reset_index(drop=True)
        body_id_int_not_null_endyear = body_id_table_int[
            ~body_id_table_int['EndYear'].astype(str).str.contains('null')].reset_index(drop=True)
        body_id_int_not_null_endyear['EndYear'] = body_id_int_not_null_endyear['EndYear'].astype(float)
        body_id_table = pd.concat([body_id_int_not_null_endyear[body_id_int_not_null_endyear['EndYear'] >= year], \
                                   body_id_table_int[
                                       body_id_table_int['EndYear'].astype(str).str.contains('null')]]).reset_index(
            drop=True)
        body_id_table['LineageID'] = body_id_table['LineageID'].astype(int)
        body_id_table['BodyID'] = body_id_table['BodyID'].astype(int)
        if 'LineageID' in matched_bodyid_filename:
            draft_bodyid_table = pd.merge_ordered(bodyid_file, body_id_table[\
                ['BodyID', 'LineageID', 'BodyDescription', 'CabinID', 'StartYear', 'EndYear', 'ref_Make', 'ref_Model']], \
                how='left', on = 'LineageID').reset_index(drop=True)
            draft_bodyid_table.to_csv(output_path + '\\' + 'Wards MY' + str(year) + ' BodyID.csv', index=False)
        else:
            Wards_readin_final_output = pd.merge_ordered(Wards_readin_final_output, \
                    bodyid_file[['MAKE & SERIES', 'Body Style', 'Wheel Base (ins.)', 'BodyID','LineageID', 'USE_YN']],\
                    how='left', on=['MAKE & SERIES', 'Body Style', 'Wheel Base (ins.)']).reset_index(drop=True)

            Wards_data_cleaned = Wards_readin_final_output[Wards_readin_final_output['USE_YN'] == 'y']\
                .sort_values(['Manufacturer','Make', 'Model', 'MAKE & SERIES', 'Transmission', 'Fuel Type']).reset_index(drop=True)
            Wards_data_cleaned = pd.concat([pd.Series(range(len(Wards_data_cleaned)), name='WARDS_ID') + 1, Wards_data_cleaned],
                axis=1)
            Wards_data_cleaned['LineageID'] = Wards_data_cleaned['LineageID'].astype(float).astype(int)
            Wards_data_cleaned['BodyID'] = Wards_data_cleaned['BodyID'].astype(float).astype(int)
            # Wards_data_bodyid_single = Wards_readin_final_output[Wards_readin_final_output['BodyID'] != -9].reset_index(drop=True)
            # Wards_data_bodyid_many = Wards_readin_final_output[(Wards_readin_final_output['BodyID'] == -9) & \
            #                                                    (Wards_readin_final_output['LineageID'] != -9)].reset_index(drop=True)
            # Wards_data_bodyid_none = Wards_readin_final_output[Wards_readin_final_output['LineageID'] == -9].reset_index(drop=True)
            #
            # Wards_data_bodyid_many = Wards_data_bodyid_many.drop(['BodyID'],axis=1)
            #
            # Wards_data_bodyid_many_expanded = pd.merge_ordered(Wards_data_bodyid_many, body_id_table[['BodyID', 'LineageID']], how='left', on = 'LineageID')
            # Wards_data_cleaned = pd.concat([Wards_data_bodyid_single, Wards_data_bodyid_many_expanded, Wards_data_bodyid_none]).reset_index(drop=True)
            date_and_time = str(datetime.datetime.now())[:19].replace(':', '').replace('-', '')
            Wards_data_cleaned.to_csv(output_path + '\\' + save_name+ ' '+date_and_time+'.csv', index=False)  # Output final Wards data

