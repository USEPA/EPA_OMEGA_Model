import os
import pandas as pd
import numpy as np

Edmunds_Readin_LineageID = True
Footprint_LineageID = False

working_directory = 'C:/Users/slee02/Documents/Python/outputs/'

if Footprint_LineageID == True:
    Footprint_MY2019 = pd.read_csv(working_directory+'Footprint Lineage - MY2019'+'.csv', dtype=object, encoding = "ISO-8859-1")
    Edmunds_BodyID_MY2017 = pd.read_csv(working_directory+'Edmunds BodyID_MY2017'+'.csv', dtype=object, encoding = "ISO-8859-1")
    Edmunds_BodyID_MY2017 = Edmunds_BodyID_MY2017.rename(columns={Edmunds_BodyID_MY2017.columns[0]: 'Make'})
    Edmunds_MY2019 = pd.read_csv(working_directory+'Edmunds Readin_ MY2019 20210218 090517'+'.csv', dtype=object, encoding = "ISO-8859-1")

else:
    Edmunds_readin_base = pd.read_csv(working_directory+'Edmunds Readin_ MY2016 20171107 102744'+'.csv', dtype=object, encoding = "ISO-8859-1")
    Edmunds_readin_MY2019 = pd.read_csv(working_directory+'Edmunds Readin_ MY2019 20210218 090517'+'.csv', dtype=object, encoding = "ISO-8859-1")


# df = Footprint_MY2019[list(aggregating_columns) + [information_toget_source_column_name]]
                    # query_output_source = df.groupby(list(aggregating_columns))
                    #
if Footprint_LineageID == True:
    maker_MY2017 = Footprint_MY2019['FOOTPRINT_DIVISION_NM']
    model_MY2017 = Footprint_MY2019['FOOTPRINT_CARLINE_NM']
    model_desc_MY2017 = Footprint_MY2019['FOOTPRINT_DESC']
    lineage_MY2017 = Footprint_MY2019['LineageID']
    index_footprint_MY2017 = Footprint_MY2019['FOOTPRINT_INDEX']

    maker_MY2019 = Footprint_MY2019['FOOTPRINT_DIVISION_NM.1']
    model_MY2019 = Footprint_MY2019['FOOTPRINT_CARLINE_NM.1']
    model_desc_MY2019 = Footprint_MY2019['FOOTPRINT_DESC.1']
    lineage_MY2019 = Footprint_MY2019['LineageID.1']
    index_footprint_MY2019 = Footprint_MY2019['FOOTPRINT_INDEX.1']
    bodyID_MY2019 = pd.DataFrame({'BodyID': len(lineage_MY2019) * []})
    bodyID_MY2019 = lineage_MY2019.copy(deep=True)
    _rows, _cols = Footprint_MY2019.shape
elif Edmunds_Readin_LineageID == True:
    maker_base = Edmunds_readin_base['Make']
    model_base = Edmunds_readin_base['Model']
    model_desc_base = Edmunds_readin_base['Trims']
    lineageID_base = Edmunds_readin_base['LineageID']
    bodyID_base = Edmunds_readin_base['BodyID']

    maker_MY2019 = Edmunds_readin_MY2019['Make']
    model_MY2019 = Edmunds_readin_MY2019['Model']
    model_desc_MY2019 = Edmunds_readin_MY2019['Trims']
    lineageID_MY2019 = Edmunds_readin_MY2019['LineageID']
    bodyID_MY2019 = Edmunds_readin_MY2019['BodyID']
    _rows, _cols = Edmunds_readin_MY2019.shape

for i in range(_rows):
    _maker = maker_MY2019[i]
    _model = model_MY2019[i].lower()
    _trim = model_desc_MY2019[i].lower()
    _model0 = _model.split(' ')[0]
    
    maker_base = Edmunds_readin_base[Edmunds_readin_base['Make'] == _maker].reset_index()
    if len(maker_base) == 0:
        maker_base = Edmunds_readin_base[Edmunds_readin_base['Make'] == str(_maker).upper()].reset_index()
        # for j in range(len(maker_base)):
    #     if _model == maker_base.loc[j, 'FOOTPRINT_CARLINE_NM'] and lineage_MY2019[i] == '-9':
    #         lineage_MY2019[i] = maker_base.loc[j, 'LineageID']
    #         break

    for j in range(len(maker_base)):
        _model_base = maker_base.loc[j, 'Model'].lower()
        _model_base0 = str(_model_base).lower().split(' ')[0]
        # if 'Coupe' in _model_base: _model_base0 = _model_base + ' Coupe'
        # if 'Convertible' in _model_base: _model_base0 = _model_base + ' Convertible'

        if _model0 == _model_base0 and lineageID_MY2019[i] == '-9':
            lineageID_MY2019[i] = maker_base.loc[j, 'LineageID']
            bodyID_MY2019[i] = maker_base.loc[j, 'BodyID']
            break

Body_LineageIDs = [bodyID_MY2019, lineageID_MY2019]
bodyID_MY2019.to_csv(working_directory + 'edmundsBodyID-MY2019-step1.csv', index=False)
lineageID_MY2019.to_csv(working_directory + 'edmundsLineageID-MY2019-step1.csv', index=False)

# for i in range(_rows):
#     _maker = maker_MY2019[i]
#     _model = model_MY2019[i]
#     _trim = model_desc_MY2019[i]
#     _model0 = _model.split(' ')[0].lower()
#     _model_desc = model_desc_MY2019[i].lower()
#     _model_desc0 = _model_desc.split(' ')[0]
#
#     if lineage_MY2019[i] == '-9':
#         edmunds_base = Edmunds_BodyID_MY2017[Edmunds_BodyID_MY2017['Make'] == _maker].reset_index()
#         if len(edmunds_base) == 0:
#             edmunds_base = Edmunds_BodyID_MY2017[Edmunds_BodyID_MY2017['Make'] == _maker.upper()].reset_index()
#         for j in range(len(edmunds_base)):
#             _model_edmunds=edmunds_base.loc[j, 'Model'].split(' ')[0].lower()
#             # print(_model_edmunds)
#             if (_model0 == _model_edmunds) or (_model_desc0 == _model_edmunds) or (_model_edmunds in _model_desc):
#                 # print(edmunds_base.loc[j, 'LineageID'])
#                 lineage_MY2019[i] = edmunds_base.loc[j, 'LineageID']
#                 break
#         lineage_MY2019.to_csv(working_directory + 'LineageID-MY2019-step2.csv', index=False)

    #     maker_base = Footprint_MY2019[Footprint_MY2019['FOOTPRINT_DIVISION_NM'] == _maker].reset_index()
    #     if len(maker_base) == 0:
    #         maker_base = Footprint_MY2019[Footprint_MY2019['FOOTPRINT_DIVISION_NM'] == _maker.upper()].reset_index()
    #     # for j in range(len(maker_base)):
    #     #     if _model == maker_base.loc[j, 'FOOTPRINT_CARLINE_NM'] and lineage_MY2019[i] == '-9':
    #     #         lineage_MY2019[i] = maker_base.loc[j, 'LineageID']
    #     #         break
    #
    #     for j in range(len(maker_base)):
    #         _model_base0 = maker_base.loc[j, 'FOOTPRINT_CARLINE_NM'].split(' ')[0].lower()
    #         if _model0 == maker_base.loc[j, 'FOOTPRINT_CARLINE_NM'].lower().split(' ')[0] and lineage_MY2019[i] == '-9':
    #             lineage_MY2019[i] = maker_base.loc[j, 'LineageID']
    #             break
    # lineage_MY2019.to_csv(working_directory + 'LineageID-MY2019-step1.csv', index=False)
    #
    # for i in range(_rows):
    #     _maker = maker_MY2019[i]
    #     _model = model_MY2019[i]
    #     _trim = model_desc_MY2019[i]
    #     _model0 = _model.split(' ')[0].lower()
    #     _model_desc = model_desc_MY2019[i].lower()
    #     _model_desc0 = _model_desc.split(' ')[0]
    #
    #     if lineage_MY2019[i] == '-9':
    #         edmunds_base = Edmunds_BodyID_MY2017[Edmunds_BodyID_MY2017['Make'] == _maker].reset_index()
    #         if len(edmunds_base) == 0:
    #             edmunds_base = Edmunds_BodyID_MY2017[Edmunds_BodyID_MY2017['Make'] == _maker.upper()].reset_index()
    #         for j in range(len(edmunds_base)):
    #             _model_edmunds = edmunds_base.loc[j, 'Model'].split(' ')[0].lower()
    #             # print(_model_edmunds)
    #             if (_model0 == _model_edmunds) or (_model_desc0 == _model_edmunds) or (_model_edmunds in _model_desc):
    #                 # print(edmunds_base.loc[j, 'LineageID'])
    #                 lineage_MY2019[i] = edmunds_base.loc[j, 'LineageID']
    #                 break

    #     # _model_desc = _model
#     # if 'Regular Cab' in _trim: _model_desc = ' Regular Cab'
#     # if 'SUV' in _trim: _model_desc = _model + ' SUV'
    

# _rows, _cols = Edmunds_MY2019.shape
# _columns = Edmunds_MY2019.columns.to_list()
# maker = Edmunds_MY2019['Make']
# model = Edmunds_MY2019['Model']
# trims = Edmunds_MY2019['Trims']
# msrp = Edmunds_MY2019['MSRP']
# Edmunds_MY2019['Trims_desc'] = pd.DataFrame({'Trims_desc' : []})
# for i in range (_rows):
#     _model = Edmunds_MY2019.loc[i, 'Model']
#     _trim = Edmunds_MY2019.loc[i, 'Trims']
#     _model_desc = _model
#     if 'Regular Cab' in _trim: _model_desc = ' Regular Cab'
#     if 'SUV' in _trim: _model_desc = _model + ' SUV'
#     if 'Sedan' in _trim: _model_desc = _model + ' Sedan'
#     if 'Coupe' in _trim: _model_desc = _model + ' Coupe'
#     if 'Convertible' in _trim: _model_desc = _model + ' Convertible'
#     if 'Regular Cab' in _trim: _model_desc = _model + ' Regular Cab'

#     if 'AWD' in _trim: _model_desc = _model_desc + ' AWD'
#     if 'FWD' in _trim: _model_desc = _model_desc + ' FWD'
#     if '4WD' in _trim: _model_desc = _model_desc + ' 4WD'
#     if '2WD' in _trim: _model_desc = _model_desc + ' 2WD'

#     Edmunds_MY2019.loc[i, 'Trims_desc'] = _model_desc


#     final_table.to_csv(working_directory+output_name, index=False)
#     final_table['URL'] = final_table['URL'].str.upper()
#     final_table = final_table.sort_values('URL')
#
