import pandas as pd
import numpy as np
import Edmunds_Interact
import os
import time
import math
from datetime import datetime
from pathlib import *

# pip install pandas numpy selenium beautifulsoup4 html5lib lxml
def movecol(df, cols_to_move=[], ref_cols='', place='After'):
    cols = df.columns.tolist()
    if ref_cols[0] in cols:
        ref_col = ref_cols[0]
    elif len(ref_cols) > 0:
        ref_col = ref_cols[1]

    if place == 'After':
        seg1 = cols[:list(cols).index(ref_col) + 1]
        seg2 = cols_to_move
    if place == 'Before':
        seg1 = cols[:list(cols).index(ref_col)]
        seg2 = cols_to_move + [ref_col]

    seg1 = [i for i in seg1 if i not in seg2]
    seg3 = [i for i in cols if i not in seg1 + seg2]

    return (df[seg1 + seg2 + seg3])

start_time = datetime.now()
working_directory = str(Path.home()) + '/Documents/Python/Edmunds_web_vehicle_specs/'
run_controller = pd.read_csv(working_directory+'Edmunds Run Controller-2021.csv')
start_count = 0 #Set to 0 when time permits
final_table_to_csv_inc = 20 # print final_table csv file at the final_table_to_csv_inc increments
# cols_safety = ["DUAL FRONT SIDE-MOUNTED AIRBAGS", "DUAL FRONT WITH HEAD PROTECTION CHAMBERS SIDE-MOUNTED AIRBAGS",
#                 "DUAL FRONT AND DUAL REAR SIDE-MOUNTED AIRBAGS",
#                 "DUAL FRONT AND DUAL REAR WITH HEAD PROTECTION CHAMBERS SIDE-MOUNTED AIRBAGS",
#                 "DRIVER ONLY WITH HEAD PROTECTION CHAMBER SIDE-MOUNTED AIRBAGS",
#                 "FRONT, REAR AND THIRD ROW HEAD AIRBAGS", "FRONT AND REAR HEAD AIRBAGS", "FRONT HEAD AIRBAGS",
#                 "STABILITY CONTROL", "TRACTION CONTROL", "TIRE PRESSURE MONITORING"]

for run_count in range (0,len(run_controller)):
    if run_count > 0: del final_table, reformatted_table
    continued_readin = str(run_controller['Continue Readin'][run_count])
    input_name = str(run_controller['URL Filename'][run_count])
    output_name = str(run_controller['Output Filename'][run_count])
    url_column_name = str(run_controller['URL Column Name'][run_count])
    model_year = str(run_controller['Model Year'][run_count])
    weberror = pd.Series(np.zeros(1), name = 'Website Errors').replace(0,'')
    edmunds_info = pd.read_csv(working_directory+input_name, encoding = "ISO-8859-1")
    edmunds_info.dropna(subset=[url_column_name], inplace=True)
    edmunds_makes = edmunds_info['Make']
    edmunds_models = edmunds_info['Model']
    url_list = edmunds_info[url_column_name]

    final_table_to_csv_list = [i*final_table_to_csv_inc for i in range(1, math.ceil(len(url_list)/final_table_to_csv_inc))] # print every final_table_to_csv_inc URLs
    if continued_readin == 'y':
        readin_table = pd.read_csv(working_directory+output_name, dtype=object, encoding = "ISO-8859-1")
        readin_error_models = pd.Series(readin_table['Model'][pd.isnull(readin_table['Readin_Error'])==False]\
            .unique()).reset_index(drop=True)
        final_table = readin_table
        for error_model in readin_error_models:
            print ('Removing ' + str(error_model))
            final_table = final_table[final_table['Model'] != error_model].reset_index(drop=True)
        # final_table.to_csv(working_directory + output_name + '_bkp', index=False)
    for url_count in range(start_count,len(url_list)):
        url = url_list[url_count]
        print(str(url_count) + ',' + str(url))
        if continued_readin == 'n' or (continued_readin == 'y' \
                and (final_table['URL']  == url.upper()).sum() == 0 and (final_table['URL']  == url).sum() == 0):
            model = edmunds_models[url_count]
            make = edmunds_makes[url_count]
            [original_output_table, readin_check, trim_text] = Edmunds_Interact.Edmunds_Interact(url)
            if type(original_output_table) == str:
                weberror[len(weberror)] = url
                weberror.to_csv(working_directory + 'Non-Functioning Websites_MY'+str(model_year)+'.csv',index=False)
                continue
            category_name = original_output_table['Category']
            specification_name = original_output_table['Specifications']
            output_table = original_output_table.drop(['Category', 'Specifications'], axis=1)
            # output_table = original_output_table.drop('Specifications',axis=1)
            # trims_msrp = output_table.columns.str.strip()
            # try:
            #     msrp = pd.Series(trims_msrp.str.rsplit('$').str[1].str.strip(), name = 'MSRP')
            #     tmp_str = original_output_table['Trim_x'].str.rsplit('$').str[1].str.strip()[0].split(' ')[0]
            # except AttributeError:
            #     msrp = pd.Series(np.zeros(len(trims_msrp)), name = 'MSRP').astype(str)
            trims = []; msrp = []
            for i in range(len(trim_text)):
                trims.append((trim_text[i].rsplit(' - ')[0].strip()))
                msrp.append((trim_text[i].rsplit('$')[1].strip()))

            trims = pd.Series(trims, name='Trims'); msrp = pd.Series(msrp, name='MSRP')
            # trims = pd.Series(trims.str.rsplit(' - ').str[0].str.strip(), name='Trims')
            new_output_table = output_table.T.reset_index(drop=True)
            new_output_table.columns = specification_name.str.upper()
            make_info = pd.Series(np.zeros(len(new_output_table)),name = 'Make').replace(0,make)
            model_info = pd.Series(np.zeros(len(new_output_table)),name = 'Model').replace(0,model)
            url_info = pd.Series(np.zeros(len(new_output_table)), name='URL').replace(0, url)
            reformatted_table = pd.concat([make_info, model_info, trims, msrp, url_info, new_output_table],axis=1).reset_index(drop=True)
            reformatted_table = pd.concat([readin_check,reformatted_table],axis=1)
            reformatted_table_T = reformatted_table.T
            reformatted_table_T2 = reformatted_table_T[~reformatted_table_T.index.duplicated(keep='first')]
            reformatted_table = reformatted_table_T2.T
            #Remove columns with duplicate names and non-duplicate values (They aren't reliable)
            # reformatted_table.to_csv('/Users/Brandon/Desktop/Individual Runs/' + url.replace('/','-')[url.find('.com')+len('.com'):url.find('features-specs')] + '.csv', index=False)
            for column in pd.Series(reformatted_table.columns).unique():
                if (pd.Series(reformatted_table.columns) == column).sum() > 1:
                    reformatted_table = reformatted_table.drop(column,axis=1)
            try:
                # non_merge_columns = list(reformatted_table.columns.difference(final_table.columns))
                # merge_columns = list(reformatted_table.columns.difference(non_merge_columns))
                reformatted_table = reformatted_table.loc[:, ~reformatted_table.columns.duplicated()]
                reformatted_table = reformatted_table.dropna(how='all', axis=1)
                final_table = final_table.loc[:, ~final_table.columns.duplicated()]
                if len(final_table) > 0:
                    final_table = final_table.merge(reformatted_table, how='outer').sort_values('URL')
                else:
                    final_table = reformatted_table
                # final_table = final_table.merge(reformatted_table, how='outer', on=specification_name).sort_values('URL')
                # final_table = final_table.dropna(how='all', axis=1)
            except NameError:
                reformatted_table = reformatted_table.dropna(how='all', axis=1)
                final_table = reformatted_table
            except TypeError:
                reformatted_table.to_csv(working_directory + 'Merge Error Table' + '.csv', index=False)
        # raise SystemExit
            final_table = final_table.dropna(how='all')
            if url_count in final_table_to_csv_list:
                final_table.to_csv(working_directory + output_name.split('.')[0] + '_' + str(url_count) + '.csv', index=False)
                if len(Edmunds_Interact.super_trim_url_list) > 0:
                    timestr = time.strftime("%Y%m%d-%H%M%S")
                    df_super_trim_url_list = pd.DataFrame(Edmunds_Interact.super_trim_url_list, columns=['URL'])
                    df_super_trim_url_list.to_csv(working_directory + output_name.split('.')[0] + '_high_options_url_' + timestr + '.csv' , index=False)
            # if url_count == 0:
            #     final_table_category_specs = pd.DataFrame([category_name, specification_name], columns=['Category', 'Specifications'])
            #     timestr = time.strftime("%Y%m%d-%H%M%S")
            #     final_table_category_specs.to_csv(
            #         working_directory + output_name.split('.')[0] + '_Category_Specifications_' + timestr + '.csv',
            #         index=False)

    # https: // towardsdatascience.com / reordering - pandas - dataframe - columns - thumbs - down - on - standard - solutions - 1ff0bc2941d5
    # my_list = df.columns.values.tolist() or my_list = list(df)
    # print (type(my_list))

    final_table['URL'] = final_table['URL'].str.upper()
    final_table = final_table.sort_values('URL')
    final_table = final_table.dropna(how='all', subset=['Make', 'Model'])
    final_table = final_table.fillna('')
    final_table = final_table.reset_index(drop=True)

    # cols_final_table = list(final_table)
    # _icols_safety = []
    # for i in range (len(cols_safety)):
    #     icol_safety = cols_safety[i]
    #     if icol_safety in cols_final_table:
    #         _icols_safety += [icol_safety]
    #         if len(final_table.loc[final_table[icol_safety] == '']) > 0:
    #             final_table[icol_safety] = final_table[icol_safety].replace('', 'null ')
    #
    # final_table = movecol(final_table, cols_to_move= _icols_safety, ref_cols = ['CAM TYPE', 'CYLINDER DEACTIVATION'], place='After')

    timestr = time.strftime("%Y%m%d-%H%M%S")
    final_table.to_csv(working_directory + output_name.split('.')[0] + '_' + timestr + '.csv', index=False)

    time_elapsed = datetime.now() - start_time
    print('Time elapsed (hh:mm:ss.ms) {}'.format(time_elapsed))

