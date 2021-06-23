def Powertrain_Array_Filter(Powertrain_Array, year_filter, sales_filter, tech_filter, OEM_filter, \
                            fleettype_filter, nullfilter_1, nullfilter_2):
    import pandas as pd
    import numpy as np

    # if year_filter == 'Present':
    #     Powertrain_Array = Powertrain_Array[Powertrain_Array['Tech Package']=='TP00'].reset_index(drop=True)
    #     if sales_filter == 'Sales':
    #         Powertrain_Array = Powertrain_Array[Powertrain_Array['Present Sales']>0].reset_index(drop=True)
    # elif year_filter == 'Projected':
    #     Powertrain_Array = Powertrain_Array[Powertrain_Array['Tech Package']!='TP00'].reset_index(drop=True)
    #     if sales_filter == 'Sales':
    #         Powertrain_Array = Powertrain_Array[Powertrain_Array['Projected Sales']>0].reset_index(drop=True)

    if OEM_filter != 'None':
        Powertrain_Array = Powertrain_Array[Powertrain_Array['CAFE_MFR_NM'] == str(OEM_filter)].reset_index(drop=True)

    if tech_filter == 'nonPEV':
       Powertrain_Array = Powertrain_Array[
            (Powertrain_Array['Stop-Start Tech Category'] != 'REEV-G') & \
            (Powertrain_Array['Stop-Start Tech Category'] != 'REEV-D') & \
            (Powertrain_Array['Stop-Start Tech Category'] != 'REEV-E') & \
            (Powertrain_Array['Stop-Start Tech Category'] != 'EV')].reset_index(drop=True)
    elif tech_filter == 'PEV':
        Powertrain_Array = Powertrain_Array[
            (Powertrain_Array['Stop-Start Tech Category'] != 'No S-S') & \
            (Powertrain_Array['Stop-Start Tech Category'] != 'S-S') & \
            (Powertrain_Array['Stop-Start Tech Category'] != 'MHEV') & \
            (Powertrain_Array['Stop-Start Tech Category'] != 'HEV')].reset_index(drop=True)

    if fleettype_filter == 'PV':
        Powertrain_Array = Powertrain_Array[Powertrain_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
    elif fleettype_filter == 'LT':
        Powertrain_Array = Powertrain_Array[Powertrain_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)

    if nullfilter_1 != 'None':
        Powertrain_Array = Powertrain_Array[~pd.isnull(Powertrain_Array[nullfilter_1])]
    if nullfilter_2 != 'None':
        Powertrain_Array = Powertrain_Array[~pd.isnull(Powertrain_Array[nullfilter_2])]
    Filtered_Array = Powertrain_Array.reset_index(drop=True)
    return Filtered_Array