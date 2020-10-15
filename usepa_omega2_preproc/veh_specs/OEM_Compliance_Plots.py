import pandas as pd
import numpy as np
import heapq
import datetime
from matplotlib import pyplot as plt
from matplotlib import gridspec
import Powertrain_Array_Filter
def OEM_Compliance_Plots(input_path, output_path, query_filenames_list, footprint_plots, \
                            load_factor_plots, credit_integration, target_credit, credit_legend_category, \
                         credit_filenames_list, FTP_dist_mi, HWFET_dist_mi):
    from Unit_Conversion import gal2l, km2mi, mi2km, hp2mw
    from Table_Categories import car_table_categories, truck_table_categories, \
        overall_table_categories, tech_credits

    # table_pt2_categories = pd.Series(table_pt2_categories)
    # car_table_categories = pd.Series(car_table_categories)
    # truck_table_categories = pd.Series(truck_table_categories)
    # overall_table_categories = pd.Series(overall_table_categories)
    HV_Gasoline = 32.05239499
    numlabels = 5
    VMT_C= 195264
    VMT_T = 225865

    if ',' in query_filenames_list:
        filenames = pd.Series(list(query_filenames_list.split(','))).str.strip()
    else:
        filenames = pd.Series([query_filenames_list])
    if ',' in credit_filenames_list:
        credit_filenames = pd.Series(list(credit_filenames_list.split(','))).str.strip()
    else:
        credit_filenames = pd.Series([credit_filenames_list])

    for filename_count in range (0,len(filenames)):
        filename = filenames[filename_count]
        credit_filename = credit_filenames[filename_count]
        raw_powertrain_array = pd.read_csv(input_path+'\\'+filename)
        raw_powertrain_array['FOOTPRINT_SUBCONFIG_SALES'][pd.isnull(raw_powertrain_array['FOOTPRINT_SUBCONFIG_SALES'])] = 0
        sales_data = raw_powertrain_array[['CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD', 'FOOTPRINT_SUBCONFIG_SALES']]\
            .groupby(['CAFE_MFR_NM', 'COMPLIANCE_CATEGORY_CD']).sum().reset_index()
        Powertrain_Array_allentries = raw_powertrain_array
        model_year = int(Powertrain_Array_allentries['MODEL_YEAR'].value_counts().idxmax())
        sales_data.to_csv(output_path+'\\'+'Sales Data_MY'+str(model_year)+'.csv', index=False)
        credit_file = pd.read_csv(input_path+'\\'+credit_filename)
        ac_credits = credit_file
        if model_year < 2016:
            tech_credit_categories = tech_credits
            from Table_Categories import table_pt2_categories_pre2016 as table_pt2_categories
            from Table_Categories import all_table_categories_pre2016 as all_table_categories
        else:
            tech_credit_categories = pd.Series(tech_credits)[pd.Series(tech_credits) != 'FFV']
            from Table_Categories import table_pt2_categories_2016 as table_pt2_categories
            from Table_Categories import all_table_categories_2016 as all_table_categories
        Powertrain_Array_allentries['VMT'] = pd.Series(np.zeros(len(Powertrain_Array_allentries))).replace(0,VMT_C)
        Powertrain_Array_allentries['VMT'][Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD']=='LT'] = VMT_T
        for tech_credit in tech_credit_categories:
            Powertrain_Array_allentries[tech_credit + ' Credits (gCO2/mi)'] = pd.Series(np.zeros(len(Powertrain_Array_allentries)))
        for OEM_credit in credit_file['CAFE Manufacturer Name']:
            for cd in pd.Series(Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD']).unique():
                if cd == 'PV':
                    VMT = VMT_C
                elif cd == 'LT':
                    VMT = VMT_T
                try:
                    total_sales_credits = Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES'][(Powertrain_Array_allentries['CAFE_MFR_NM']==OEM_credit) & \
                        (Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == cd)].sum()
                    entry_number = len(Powertrain_Array_allentries[(Powertrain_Array_allentries['CAFE_MFR_NM']==OEM_credit) & \
                        (Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == cd)])
                    Powertrain_Array_allentries['A/C Credits (gCO2/mi)'][(Powertrain_Array_allentries['CAFE_MFR_NM']==OEM_credit) & \
                        (Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == cd)] = \
                        (1e6*(credit_file['A/C Efficiency Credits_Mg'+'_'+cd][credit_file['CAFE Manufacturer Name']==OEM_credit].sum() \
                        +credit_file['A/C Leakage Credits_Mg' + '_' + cd][credit_file['CAFE Manufacturer Name'] == OEM_credit].sum()) \
                        / (VMT*total_sales_credits))
                    Powertrain_Array_allentries['N2O-CH4 Credits (gCO2/mi)'][(Powertrain_Array_allentries['CAFE_MFR_NM']==OEM_credit) & \
                        (Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == cd)] = \
                        (1e6*(credit_file['N2O Credits_Mg'+'_'+cd][(credit_file['CAFE Manufacturer Name']==OEM_credit)].sum() \
                        +credit_file['CH4 Credits_Mg' + '_' + cd][(credit_file['CAFE Manufacturer Name'] == OEM_credit)].sum()) \
                        / (VMT*total_sales_credits))
                    Powertrain_Array_allentries['Off-Cycle Credits (gCO2/mi)'][(Powertrain_Array_allentries['CAFE_MFR_NM']==OEM_credit) & \
                        (Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == cd)] = \
                        (1e6*credit_file['Off-Cycle Credits_Mg'+'_'+cd][(credit_file['CAFE Manufacturer Name']==OEM_credit)].sum() \
                        / (VMT*total_sales_credits))
                    if model_year < 2016:
                        Powertrain_Array_allentries['FFV Credits (gCO2/mi)'][
                            (Powertrain_Array_allentries['CAFE_MFR_NM'] == OEM_credit) & \
                            (Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == cd)] = \
                            (credit_file['Overall per-Vehicle FFV Credits_gpmi' + '_' + cd][
                                (credit_file['CAFE Manufacturer Name'] == OEM_credit)].sum())
                except ZeroDivisionError:
                    pass
                Powertrain_Array_allentries['A/C Credits (g CO2)'] = Powertrain_Array_allentries['A/C Credits (gCO2/mi)'] \
                                                                     * Powertrain_Array_allentries['VMT'] * Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES']
                Powertrain_Array_allentries['N2O-CH4 Credits (g CO2)'] = Powertrain_Array_allentries['N2O-CH4 Credits (gCO2/mi)'] \
                                                                     * Powertrain_Array_allentries['VMT'] * Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES']
                Powertrain_Array_allentries['Off-Cycle Credits (g CO2)'] = Powertrain_Array_allentries['Off-Cycle Credits (gCO2/mi)'] \
                                                                     * Powertrain_Array_allentries['VMT'] * Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES']
                if model_year < 2016:
                    Powertrain_Array_allentries['FFV Credits (g CO2)'] = Powertrain_Array_allentries['FFV Credits (gCO2/mi)'] \
                                                                         * Powertrain_Array_allentries['VMT'] * Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES']
        OEM_unique_vec = pd.Series(Powertrain_Array_allentries['CAFE_MFR_NM'].unique())
        fleettype_vec_table = list(pd.Series(Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'].unique()).sort_values(ascending=False))+['All']
        OEM_PEV_Credits = pd.Series(np.zeros(len(OEM_unique_vec)))
        OEM_nonPEV_Credits = pd.Series(np.zeros(len(OEM_unique_vec)))

        Powertrain_Array_allentries['Pre-Tech CO2 Credits (g CO2)'] = \
            pd.Series((Powertrain_Array_allentries['CO2 Target_Master Index'] - \
                       Powertrain_Array_allentries['CO2 Tailpipe Emissions_Master Index']) * \
                      Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES'] * VMT_C)
        Powertrain_Array_allentries['Pre-Tech CO2 Credits (g CO2)'][Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD']=='LT'] = \
            pd.Series(Powertrain_Array_allentries['Pre-Tech CO2 Credits (g CO2)'] * VMT_T/VMT_C)

        Powertrain_Array_allentries['Stop-Start Tech Category'] = pd.Series(np.zeros(len(Powertrain_Array_allentries)))\
            .replace(0,'No S-S')
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Hybrid Check_Master Index'] == 'Y') & \
                                                                (Powertrain_Array_allentries['PEV Check_Master Index'] == 'Y')] = 'REEV-G'
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Hybrid Check_Master Index'] == 'Y') & \
                                                                (Powertrain_Array_allentries['PEV Check_Master Index'] == 'N')] = 'HEV'
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Hybrid Check_Master Index'] == 'N') & \
                                                                (Powertrain_Array_allentries['PEV Check_Master Index'] == 'Y')] = 'EV'
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Stop-Start Tech Category'] == 'No S-S') & \
                                                                (Powertrain_Array_allentries['Stop-Start_Master Index'] != 'N')] = 'S-S'
        #Temporary filter for error in 2016 Tesla Model X entries
        Powertrain_Array_allentries['Stop-Start Tech Category'][Powertrain_Array_allentries['CAFE_MFR_NM']=='Tesla, Inc.'] = 'EV'
        
        Powertrain_Array_allentries ['Post-Tech CO2 Credits (g CO2)'] = pd.Series(Powertrain_Array_allentries['Pre-Tech CO2 Credits (g CO2)'] + \
            Powertrain_Array_allentries['A/C Credits (g CO2)']+Powertrain_Array_allentries['Off-Cycle Credits (g CO2)'] \
            + Powertrain_Array_allentries['N2O-CH4 Credits (g CO2)'])
        Powertrain_Array_allentries['Post-Tech CO2 Credits (g/mi)'] = pd.Series(\
            Powertrain_Array_allentries['Post-Tech CO2 Credits (g CO2)'])/(Powertrain_Array_allentries['FOOTPRINT_SUBCONFIG_SALES']*VMT_C)
        Powertrain_Array_allentries['Post-Tech CO2 Credits (g/mi)'][Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == 'LT'] = \
        Powertrain_Array_allentries['Post-Tech CO2 Credits (g/mi)'][Powertrain_Array_allentries['COMPLIANCE_CATEGORY_CD'] == 'LT'] * VMT_C/VMT_T
        Powertrain_Array_allentries.to_csv(output_path+'\\'+'Temp Array.csv', index=False)
        # raise SystemExit
        if footprint_plots == 'y':
            x_plot_category = 'Footprint (ft2)'
            y_plot_category = 'Tailpipe CO2 Emissions (g/mi)'
            x_plot_label = 'Footprint (ft2)'
            y_plot_label = 'Tailpipe CO2 Emissions (g/mi)'
            axis_vec = [20,100,-100,700]
        elif load_factor_plots == 'y':
            x_plot_category = 'Combined Load Factor (%)'
            y_plot_category = 'Powertrain Efficiency'
            x_plot_label = 'Combined Load Factor (%)'
            y_plot_label = 'nonPEV Powertrain Efficiency'
            axis_vec = [0,12,10,41]
        else:
            x_plot_category = 'Tractive Energy Intensity'
            y_plot_category = 'Powertrain Efficiency'
            x_plot_label = 'Tractive Road Energy Intensity (MJ/km)'
            y_plot_label = 'nonPEV Powertrain Efficiency'
            axis_vec = [0,1.4,10,41]
        
        Powertrain_Array_allentries[x_plot_category] = pd.Series(Powertrain_Array_allentries[x_plot_category+'_Subconfig Data'])
        Powertrain_Array_allentries[x_plot_category][pd.isnull(Powertrain_Array_allentries[x_plot_category])] = Powertrain_Array_allentries[x_plot_category+'_Subconfig Data'+'_Max']
        Powertrain_Array_allentries[x_plot_category][pd.isnull(Powertrain_Array_allentries[x_plot_category])] = Powertrain_Array_allentries[x_plot_category + '_Test Car']
        Powertrain_Array_allentries[x_plot_category][pd.isnull(Powertrain_Array_allentries[x_plot_category])] = Powertrain_Array_allentries[x_plot_category + '_Test Car'+'_Max']
        
        Powertrain_Array_allentries[y_plot_category] = pd.Series(Powertrain_Array_allentries[y_plot_category+'_Subconfig Data'])
        Powertrain_Array_allentries[y_plot_category][pd.isnull(Powertrain_Array_allentries[y_plot_category])] = Powertrain_Array_allentries[y_plot_category+'_Subconfig Data'+'_Max']
        Powertrain_Array_allentries[y_plot_category][pd.isnull(Powertrain_Array_allentries[y_plot_category])] = Powertrain_Array_allentries[y_plot_category + '_Test Car']
        Powertrain_Array_allentries[y_plot_category][pd.isnull(Powertrain_Array_allentries[y_plot_category])] = Powertrain_Array_allentries[y_plot_category + '_Test Car'+'_Max']

        # if credit_integration == 'y' and target_credit != 'all':
        #     if target_credit.count(',') > 0:
        #         base_g = pd.Series((Powertrain_Array_allentries['Fleet Average Emissions (g/mi)'])\
        #                            *Powertrain_Array_allentries['VMT']*Powertrain_Array_allentries['Relevant Sales'], \
        #                                                                       name = 'Post-Tech CO2 Credits (g CO2)')
        #         iterative_target_credit = pd.Series(target_credit.split(',')).order().reset_index(drop=True)
        #         for credit_index in range (0,len(iterative_target_credit)):
        #             base_g += pd.Series((Powertrain_Array_allentries[iterative_target_credit[credit_index]])\
        #                            *Powertrain_Array_allentries['VMT']*Powertrain_Array_allentries['Relevant Sales'], \
        #                                                                       name = 'Post-Tech CO2 Credits (g CO2)')
        #         Powertrain_Array_allentries['Post-Tech CO2 Credits (g CO2)'] = base_g
        #     else:
        #         Powertrain_Array_allentries['Post-Tech CO2 Credits (g CO2)'] = pd.Series((Powertrain_Array_allentries['Fleet Average Emissions (g/mi)']\
        #         + Powertrain_Array_allentries[target_credit])*Powertrain_Array_allentries['VMT']*Powertrain_Array_allentries['Relevant Sales'], \
        #                                                                       name = 'Post-Tech CO2 Credits (g CO2)')
        #     Powertrain_Array_allentries.reset_index(drop=True)
        for i in range(0, len(OEM_unique_vec)):
            PEV_Credit_Array = Powertrain_Array_Filter.Powertrain_Array_Filter\
                (Powertrain_Array_allentries, 'Present', 'Sales','PEV', str(OEM_unique_vec[i]),'None', 'None', 'None')
            nonPEV_Credit_Array = Powertrain_Array_Filter.Powertrain_Array_Filter\
                (Powertrain_Array_allentries, 'Present', 'Sales','nonPEV', str(OEM_unique_vec[i]),'None', 'None', 'None')
            if credit_integration == 'y':
                OEM_PEV_Credits[i] = PEV_Credit_Array['Post-Tech CO2 Credits (g CO2)'].sum()
                OEM_nonPEV_Credits[i] = nonPEV_Credit_Array['Post-Tech CO2 Credits (g CO2)'].sum()

                OEM_PEV_Credits_nonintegrated = pd.Series(np.zeros(len(OEM_unique_vec)))
                OEM_nonPEV_Credits_nonintegrated = pd.Series(np.zeros(len(OEM_unique_vec)))

                OEM_PEV_Credits_nonintegrated[i] = PEV_Credit_Array['Pre-Tech CO2 Credits (g CO2)'].sum()
                OEM_nonPEV_Credits_nonintegrated[i] = nonPEV_Credit_Array['Pre-Tech CO2 Credits (g CO2)'].sum()
            else:
                OEM_PEV_Credits[i] = PEV_Credit_Array['Pre-Tech CO2 Credits (g CO2)'].sum()
                OEM_nonPEV_Credits[i] = nonPEV_Credit_Array['Pre-Tech CO2 Credits (g CO2)'].sum()
        normalized_footprint = 30
        Max_Credits = 1e12
        Max_Sales =  300000
        Max_Bubble_Size = 2000
        Max_Dot_Size = Max_Bubble_Size/5

        for i in range(0, len(OEM_unique_vec)):
            table_pt1 = pd.Series(np.zeros((len(table_pt2_categories) + 1)), name='')
            table_pt2 = pd.Series(np.zeros((len(table_pt2_categories) + 1)), name='Category')
            table_pt3 = pd.Series(np.zeros((len(table_pt2_categories) + 1)), name='g/mi')
            table_pt4 = pd.Series(np.zeros((len(table_pt2_categories) + 1)), name='Mg')

            OEM = str(OEM_unique_vec[i])
            print(OEM)
            OEM_Array_allentries = Powertrain_Array_Filter.Powertrain_Array_Filter\
                (Powertrain_Array_allentries, 'Present', 'Sales','None', str(OEM_unique_vec[i]),'None', 'None', 'None')
            if model_year >= 2016:
                tailpipe_error_g = (1e6*credit_file['Fleet Average Credits_Mg_PV'][\
                    credit_file['CAFE Manufacturer Name']==OEM].sum() + 1e6*credit_file['Fleet Average Credits_Mg_LT'][\
                    credit_file['CAFE Manufacturer Name']==OEM].sum()) - OEM_Array_allentries['Pre-Tech CO2 Credits (g CO2)'].sum()
            else:
                tailpipe_error_g = (1e6*credit_file['Fleet Average Credits_Mg_PV'][\
                    credit_file['CAFE Manufacturer Name']==OEM].sum() + 1e6*credit_file['Fleet Average Credits_Mg_LT'][\
                    credit_file['CAFE Manufacturer Name']==OEM].sum()) - OEM_Array_allentries['Pre-Tech CO2 Credits (g CO2)'].sum()\
                    - (credit_file['Overall per-Vehicle FFV Credits_gpmi_PV'][credit_file['CAFE Manufacturer Name']==OEM].sum()\
                    *VMT_C*credit_file['Total Production Volume_PV'][credit_file['CAFE Manufacturer Name']==OEM].sum()) \
                    - (credit_file['Overall per-Vehicle FFV Credits_gpmi_LT'][credit_file['CAFE Manufacturer Name'] == OEM].sum() \
                       * VMT_T * credit_file['Total Production Volume_LT'][credit_file['CAFE Manufacturer Name'] == OEM].sum())

            Array_Car = Powertrain_Array_Filter.Powertrain_Array_Filter\
                    (Powertrain_Array_allentries, 'Present', 'Sales','nonPEV', str(OEM_unique_vec[i]),'PV', x_plot_category, y_plot_category)
            Array_Truck = Powertrain_Array_Filter.Powertrain_Array_Filter\
                (Powertrain_Array_allentries, 'Present', 'Sales','nonPEV', str(OEM_unique_vec[i]),'LT', x_plot_category, y_plot_category)
            Array_Car_sales = Array_Car['FOOTPRINT_SUBCONFIG_SALES'].sum()
            Array_Truck_sales = Array_Truck['FOOTPRINT_SUBCONFIG_SALES'].sum()
            Car_SW_xcategory = 0
            Car_SW_ycategory = 0
            Truck_SW_xcategory = 0
            Truck_SW_ycategory = 0
            if Array_Car_sales > 0:
                Car_SW_ycategory=np.average(Array_Car[y_plot_category],weights=Array_Car['FOOTPRINT_SUBCONFIG_SALES'])
                Car_SW_xcategory=np.average(Array_Car[x_plot_category],weights=Array_Car['FOOTPRINT_SUBCONFIG_SALES'])
            if Array_Truck_sales > 0:
                Truck_SW_xcategory=np.average(Array_Truck[x_plot_category],weights=Array_Truck['FOOTPRINT_SUBCONFIG_SALES'])
                Truck_SW_ycategory=np.average(Array_Truck[y_plot_category],weights=Array_Truck['FOOTPRINT_SUBCONFIG_SALES'])
            # Car_SW_ycategory = (
            #     (Array_Car[y_plot_category].astype(float) * Array_Car['FOOTPRINT_SUBCONFIG_SALES'].astype(float)) \
            #     / Array_Car['FOOTPRINT_SUBCONFIG_SALES'].astype(float).sum()).sum()
            # Truck_SW_ycategory = (
            #     (Array_Truck[y_plot_category].astype(float) * Array_Truck['FOOTPRINT_SUBCONFIG_SALES'].astype(float)) \
            #     / Array_Truck['FOOTPRINT_SUBCONFIG_SALES'].astype(float).sum()).sum()
            # Car_SW_xcategory = ((Array_Car[x_plot_category].astype(float) *
            #                       Array_Car['FOOTPRINT_SUBCONFIG_SALES'].astype(float)) / Array_Car['FOOTPRINT_SUBCONFIG_SALES'].astype(float).sum()).sum()
            # Truck_SW_xcategory = ((Array_Truck[x_plot_category].astype(float) *
            #                         Array_Truck['FOOTPRINT_SUBCONFIG_SALES'].astype(float))/ Array_Truck['FOOTPRINT_SUBCONFIG_SALES'].astype(float).sum()).sum()

            Array_Car_All = Powertrain_Array_Filter.Powertrain_Array_Filter\
                (Powertrain_Array_allentries, 'Present', 'Sales','None', str(OEM_unique_vec[i]),'PV', 'CO2 Target_Master Index', 'None')
            Array_Truck_All = Powertrain_Array_Filter.Powertrain_Array_Filter\
                (Powertrain_Array_allentries, 'Present', 'Sales','None', str(OEM_unique_vec[i]),'LT', 'CO2 Target_Master Index', 'None')
            Array_Car_All_sales = Array_Car_All['FOOTPRINT_SUBCONFIG_SALES'].sum()
            Array_Truck_All_sales = Array_Truck_All['FOOTPRINT_SUBCONFIG_SALES'].sum()
            Car_SW_Target = 0
            Truck_SW_Target = 0
            if Array_Car_All_sales > 0:
                Car_SW_Target = np.average(Array_Car_All['CO2 Target_Master Index'],weights=Array_Car_All['FOOTPRINT_SUBCONFIG_SALES'])
            if Array_Truck_All_sales > 0:
                Truck_SW_Target = np.average(Array_Truck_All['CO2 Target_Master Index'],weights=Array_Truck_All['FOOTPRINT_SUBCONFIG_SALES'])
            Car_SW_FEI = (Car_SW_Target / 8887) * gal2l * km2mi * HV_Gasoline
            Truck_SW_FEI = (Truck_SW_Target / 8887) * gal2l * km2mi * HV_Gasoline

            del (Array_Car, Array_Truck, Array_Car_All, Array_Truck_All)

            print(str(model_year))
            #CO2_stats_array = pd.read_csv(output_path + '\\' + str(model_year) + ' - ' + 'CO2 Statistics.csv')
            # A_Car, B_Car, C_Car, D_Car = car_calculator_array[str(model_year)][0:4].reset_index(drop=True)
            # A_Truck, B_Truck, C_Truck, D_Truck = truck_calculator_array[str(model_year)][0:4].reset_index(drop=True)
            #OEM_Array = OEM_Array_allentries[OEM_Array_allentries[y_plot_category] > 0]
            OEM_Array_allentries_unique = OEM_Array_allentries.drop_duplicates(subset=[
            x_plot_category, y_plot_category], keep='first') \
            .reset_index(drop=True)
            OEM_Array_nonPEV = Powertrain_Array_Filter.Powertrain_Array_Filter\
            (Powertrain_Array_allentries, 'Present', 'Sales','nonPEV', str(OEM_unique_vec[i]),'None', 'None', 'None')
            Car_SW_y = Car_SW_ycategory
            Car_SW_x = Car_SW_xcategory
            Truck_SW_y = Truck_SW_ycategory
            Truck_SW_x = Truck_SW_xcategory
            Truck_SW_FEI = Truck_SW_FEI
            Truck_SW_Target = Truck_SW_Target
            save_year = model_year

            # OEM_Array_nonPEV = OEM_Array_nonPEV[OEM_Array_nonPEV[y_plot_category] > 0].reset_index(drop=True)
            OEM_Array_nonPEV_unique = OEM_Array_nonPEV.drop_duplicates(subset=[
                x_plot_category, y_plot_category], keep='first') \
                .reset_index(drop=True)

            save_string = output_path + '\\' + str(save_year) + ' ' + OEM
            if footprint_plots == 'y':
                save_string = save_string + '_footprint'
            if load_factor_plots == 'y':
                save_string = save_string + '_loadfactor'
            if credit_integration == 'y':
                save_string = save_string + '_integrated'
                if target_credit != 'all':
                    if len(target_credit.split(',')) > 1:
                        save_credit_iteration = pd.Series(credit_legend_category.split(',')).order().reset_index(drop=True)
                        for save_iteration in range (0,len(save_credit_iteration)):
                            save_string = save_string + '_' + str(save_credit_iteration[save_iteration])
                    else:
                        save_string = save_string + '_' + str(target_credit).rsplit(' ')[0]

            x_vec = OEM_Array_allentries_unique[x_plot_category]
            y_vec = OEM_Array_allentries_unique[y_plot_category]

            present_model_string_vec = pd.Series(np.zeros(len(x_vec)), name='Models')
            sales_vec = pd.Series(np.zeros(len(x_vec)), name='Sales')
            color_vec = pd.Series(np.zeros(len(x_vec)), name = 'Plot Color')
            if credit_integration == 'y':
                credit_vec = pd.Series(np.zeros(len(x_vec)), name='Post-Tech CO2 Credits (g CO2)')
                credit_vec_nonintegrated = pd.Series(np.zeros(len(x_vec)), name='Pre-Tech CO2 Credits (g CO2)')
                color_vec_nonintegrated = pd.Series(np.zeros(len(x_vec)), name='Pre-Tech Plot Color')
            else:
                credit_vec = pd.Series(np.zeros(len(x_vec)), name='Pre-Tech CO2 Credits (g CO2)')
            fleettype_vec = pd.Series(np.zeros(len(x_vec)), name='COMPLIANCE_CATEGORY_CD')
            SS_Tech_vec = pd.Series(np.zeros(len(x_vec)), name='Stop-Start Tech Category')
            for k in range(0, len(x_vec)):
                print(str(k+1) + ' out of ' + str(len(x_vec)))
                if pd.isnull(x_vec[k]):
                    int_array = OEM_Array_allentries[
                        (pd.isnull(OEM_Array_allentries[x_plot_category]))].reset_index(drop=True)
                else:
                    int_array = OEM_Array_allentries[
                        (OEM_Array_allentries[x_plot_category] == x_vec[k]) \
                        & (OEM_Array_allentries[y_plot_category] == y_vec[k])].reset_index(drop=True)
                sales_vec[k] = int_array['FOOTPRINT_SUBCONFIG_SALES'].sum()
                if credit_integration == 'y':
                    credit_vec[k] = int_array['Post-Tech CO2 Credits (g CO2)'].sum()
                    if credit_vec[k] > 0:
                        color_vec[k] = 'green'
                    else:
                        color_vec[k] = 'red'
                    credit_vec_nonintegrated[k] = int_array['Pre-Tech CO2 Credits (g CO2)'].sum()
                    if credit_vec_nonintegrated[k] > 0:
                        color_vec_nonintegrated[k] = 'green'
                    else:
                        color_vec_nonintegrated[k] = 'red'
                else:
                    credit_vec[k] = int_array['Pre-Tech CO2 Credits (g CO2)'].sum()
                    if credit_vec[k] > 0:
                        color_vec[k] = 'green'
                    else:
                        color_vec[k] = 'red'
                if len(int_array == 1):
                    fleettype_vec[k] = int_array['COMPLIANCE_CATEGORY_CD'][0]
                    SS_Tech_vec[k] = int_array['Stop-Start Tech Category'][0]
                else:
                    fleettype_vec[k] = int_array['COMPLIANCE_CATEGORY_CD'].value_counts().idxmax()
                    SS_Tech_vec[k] = int_array['Stop-Start Tech Category'].value_counts().idxmax()
                model_temp_vec = int_array['FOOTPRINT_CARLINE_NM'].unique()
                for l in range(0, len(model_temp_vec)):
                    if l == 0:
                        model_string = model_temp_vec[l]
                    else:
                        model_string = model_string + ', ' + model_temp_vec[l]
                present_model_string_vec[k] = model_string
            if credit_integration == 'y':
                OEM_Subarray_allentries_unique = pd.concat(
                    [present_model_string_vec, x_vec, y_vec, sales_vec, credit_vec, \
                     credit_vec_nonintegrated, fleettype_vec, SS_Tech_vec, color_vec, color_vec_nonintegrated], axis=1).reset_index(drop=True)
            else:
                OEM_Subarray_allentries_unique = pd.concat(
                    [present_model_string_vec, x_vec, y_vec, sales_vec, credit_vec, \
                     fleettype_vec, SS_Tech_vec, color_vec], axis=1).reset_index(drop=True)

            OEM_Subarray_allentries_unique_nonPEV = OEM_Subarray_allentries_unique[\
                ~pd.isnull(OEM_Subarray_allentries_unique[y_plot_category])].reset_index(drop=True)
            OEM_Subarray_allentries_unique_nonPEV[y_plot_category] = OEM_Subarray_allentries_unique_nonPEV[y_plot_category].astype(float)
            OEM_Subarray_allentries_unique_PEV = OEM_Subarray_allentries_unique[ \
                pd.isnull(OEM_Subarray_allentries_unique[y_plot_category])].reset_index(drop=True)
            OEM_Subarray_allentries_unique_nonPEV = OEM_Subarray_allentries_unique_nonPEV.sort(
                y_plot_category, ascending=True).reset_index(drop=True)
            if len(OEM_Subarray_allentries_unique_PEV) > 0:
                OEM_Subarray_allentries_unique = pd.concat\
                    ([OEM_Subarray_allentries_unique_nonPEV, OEM_Subarray_allentries_unique_PEV]).reset_index(drop=True)
            else:
                OEM_Subarray_allentries_unique = OEM_Subarray_allentries_unique_nonPEV.reset_index(drop=True)
            OEM_Subarray_allentries_unique = OEM_Subarray_allentries_unique[ \
                OEM_Subarray_allentries_unique[x_plot_category] > 0] \
                .reset_index(drop=True)
            # if OEM_unique_vec[i] == 'Hyundai/Kia':
            #     OEM_save_name = 'Hyundai-Kia'
            # else:
            #     OEM_save_name = str(OEM_unique_vec[i])

            Sales_Size_Normalized = (OEM_Subarray_allentries_unique['Sales'] / (Max_Sales)) * Max_Bubble_Size
            if credit_integration == 'y':
                Credits = OEM_Subarray_allentries_unique['Post-Tech CO2 Credits (g CO2)']
                Credits_nonintegrated = OEM_Subarray_allentries_unique['Pre-Tech CO2 Credits (g CO2)']
                Credits_Size_Normalized = (OEM_Subarray_allentries_unique['Post-Tech CO2 Credits (g CO2)'].abs()\
                                           / (Max_Credits)) * Max_Dot_Size
                Credits_Size_Normalized_nonintegrated = (OEM_Subarray_allentries_unique['Pre-Tech CO2 Credits (g CO2)'].abs()\
                                           / (Max_Credits)) * Max_Dot_Size
                OEM_Color_nonintegrated = OEM_Subarray_allentries_unique['Pre-Tech Plot Color']
                positive_color = 'green'
                negative_color = 'red'
            else:
                Credits = OEM_Subarray_allentries_unique['Pre-Tech CO2 Credits (g CO2)']
                Credits_Size_Normalized = (OEM_Subarray_allentries_unique['Pre-Tech CO2 Credits (g CO2)'].abs()\
                                           / (Max_Credits)) * Max_Dot_Size
                positive_color = 'green'
                negative_color = 'red'
            OEM_Color = OEM_Subarray_allentries_unique['Plot Color']
            AC_Credit_Size = Powertrain_Array_allentries['A/C Credits (g CO2)']\
                [Powertrain_Array_allentries['CAFE_MFR_NM']==OEM].sum() * Max_Dot_Size/Max_Credits
            Offcycle_Credit_Size = Powertrain_Array_allentries['Off-Cycle Credits (g CO2)']\
                [Powertrain_Array_allentries['CAFE_MFR_NM']==OEM].sum() * Max_Dot_Size/Max_Credits
            N2OCH4_Credit_Size = abs(Powertrain_Array_allentries['N2O-CH4 Credits (g CO2)']\
                [Powertrain_Array_allentries['CAFE_MFR_NM']==OEM].sum()) * Max_Dot_Size/Max_Credits
            if model_year < 2016:
                FFV_Credit_Size = ((credit_file['Overall per-Vehicle FFV Credits_gpmi_PV'][credit_file['CAFE Manufacturer Name']==OEM].sum()\
                        *VMT_C*credit_file['Total Production Volume_PV'][credit_file['CAFE Manufacturer Name']==OEM].sum()) \
                        + (credit_file['Overall per-Vehicle FFV Credits_gpmi_LT'][credit_file['CAFE Manufacturer Name'] == OEM].sum() \
                        * VMT_T * credit_file['Total Production Volume_LT'][credit_file['CAFE Manufacturer Name'] == OEM].sum())) \
                                  * Max_Dot_Size / Max_Credits
            Tailpipe_Error_Credit_Size = tailpipe_error_g * Max_Dot_Size/Max_Credits
            # Target_Error_Credit_Size = CO2_stats_array['Total Overall Target CO2 Credit Error (Mg)']\
            #                                  [CO2_stats_array['Total Overall Target CO2 Credit Error (Mg)'][\
            #     CO2_stats_array['CAFE_MFR_NM']==OEM].index[0]] * Max_Dot_Size*1e6/Max_Credits
            # FFV_Error_Credit_Size = CO2_stats_array['Total Overall FFV CO2 Credit Error (Mg)']\
            #                                  [CO2_stats_array['Total Overall FFV CO2 Credit Error (Mg)'][\
            #     CO2_stats_array['CAFE_MFR_NM']==OEM].index[0]] * Max_Dot_Size*1e6/Max_Credits
            if credit_integration == 'y':
                OEM_Array_Output = pd.concat([OEM_Subarray_allentries_unique, \
                                                  pd.Series(Sales_Size_Normalized, name='Sales Size'), \
                                                  pd.Series(Credits_Size_Normalized, name='Credits Size'), \
                                              pd.Series(Credits_Size_Normalized_nonintegrated, name='Nonintegrated Credits Size')], axis=1)
            else:
                OEM_Array_Output = pd.concat([OEM_Subarray_allentries_unique, \
                                                  pd.Series(Sales_Size_Normalized, name='Sales Size'), \
                                                  pd.Series(Credits_Size_Normalized, name='Credits Size')], axis=1)
            OEM_Array_Output.to_csv(save_string + '.csv',index=False)
            if len(OEM_Array_Output) > 0:
                OEM_Array_Output_Conventional = OEM_Array_Output[(OEM_Array_Output['Stop-Start Tech Category'] != 'EV') & \
                                                                   (OEM_Array_Output['Stop-Start Tech Category'] != 'REEV-G') & \
                                                                   (OEM_Array_Output['Stop-Start Tech Category'] != 'REEV-D') & \
                                                                   (OEM_Array_Output['Stop-Start Tech Category'] != 'REEV-E')].reset_index(drop=True)
            Credit_Plot = plt.figure('Credit Plot', (12, 8))
            Credit_Plot.suptitle(str(OEM_unique_vec[i]) + ', ' + str(save_year))

            if footprint_plots == 'y':
                Credit_Plot_Subplot = plt.subplot(1,1,1)
                Credit_Plot.subplots_adjust(hspace=0)
                Credit_Plot_Subplot.axis(axis_vec)
                Credit_Plot_Subplot.grid(True)
                Credit_Plot_Subplot.set_xlabel(x_plot_label)
                Credit_Plot_Subplot.set_ylabel(y_plot_label)
            elif load_factor_plots == 'y':
                gs = gridspec.GridSpec(2, 1, height_ratios=[0.25, 3.5])
                Credit_Plot_Subplot = plt.subplot(gs[1])
                Credit_Plot.subplots_adjust(hspace=0.05)
                Credit_Plot_Subplot.axis(axis_vec)
                Credit_Plot_Subplot.grid(True)
                Credit_Plot_Subplot.set_xlabel(x_plot_label)
                Credit_Plot_Subplot.set_ylabel(y_plot_label)
                Credit_Plot_Subplot2 = plt.subplot(gs[0])
                Credit_Plot_Subplot2.set_xlim(axis_vec[:2])
                Credit_Plot_Subplot2.set_ylim([-1, 2])
                Credit_Plot_Subplot2.set_yticks([0, 1])
                Credit_Plot_Subplot2.set_xticks([4, 8])
                plt.setp(Credit_Plot_Subplot2.get_xticklabels(), visible=False)
                Credit_Plot_Subplot2.set_yticklabels(['PHEV', 'BEV'], fontsize=10)
                Credit_Plot_Subplot2.set_xticklabels(['PHEV', 'BEV'], fontsize=10)
            else:
                gs = gridspec.GridSpec(2, 1, height_ratios=[0.25, 3.5])
                Credit_Plot_Subplot = plt.subplot(gs[1])
                Credit_Plot.subplots_adjust(hspace=0)
                Credit_Plot_Subplot.axis(axis_vec)
                Credit_Plot_Subplot.grid(True)
                Credit_Plot_Subplot.set_xlabel(x_plot_label)
                Credit_Plot_Subplot.set_ylabel(y_plot_label)
                Credit_Plot_Subplot2 = plt.subplot(gs[0], sharex=Credit_Plot_Subplot)
                Credit_Plot_Subplot2.set_xlim(axis_vec[:2])
                Credit_Plot_Subplot2.set_ylim([-1, 2])
                Credit_Plot_Subplot2.set_yticks([0, 1])
                plt.setp(Credit_Plot_Subplot2.get_xticklabels(), visible=False)
                Credit_Plot_Subplot2.set_yticklabels(['PHEV', 'BEV'], fontsize=10)
                Credit_Plot_Subplot2.xaxis.grid(True)

            l1 = Credit_Plot_Subplot.scatter([], [], edgecolor='black', linestyle='--', \
                                             facecolor='none', s=Max_Bubble_Size / 200)
            l2 = Credit_Plot_Subplot.scatter([], [], edgecolor='black', linestyle='--', \
                                             facecolor='none', s=Max_Bubble_Size / 20)
            l3 = Credit_Plot_Subplot.scatter([], [], edgecolor='black', linestyle='--', \
                                             facecolor='none', s=Max_Bubble_Size / 4)
            l4 = Credit_Plot_Subplot.scatter([], [], edgecolor='black', linestyle='--', \
                                             facecolor='none', s=Max_Bubble_Size / 2)
            l5 = Credit_Plot_Subplot.scatter([], [], edgecolor='black', linestyle='--', \
                                             facecolor='none', s=Max_Bubble_Size / 1)
            l_labels = [str(int(round((Max_Sales / 200),0))), str(int(round((Max_Sales / 20),0))), str(int(round((Max_Sales / 4),0))), \
                        str(int(round((Max_Sales / 2),0))),str(int(round((Max_Sales / 1),0))) ]
            leg = Credit_Plot_Subplot.legend([l1, l2, l3, l4, l5], l_labels, ncol=1, frameon=True,
                                             fontsize=6, handlelength=None, loc='upper right', borderpad=4.0,
                                             handletextpad=None, title='Sales', scatterpoints=1, labelspacing=6, \
                                             bbox_to_anchor=(1, 1)) #'Net'+'\n'+ 'g/mi'
            if footprint_plots == 'y':
                ax = Credit_Plot.gca().add_artist(leg)
            if Array_Car_sales > 0:
                Credit_Plot_Subplot.scatter([Car_SW_x], [Car_SW_y], \
                                            color='black', marker='*', s=10)
                Credit_Plot_Subplot.annotate('Car Actual', xy=(Car_SW_x, Car_SW_y), \
                                             xytext=(Car_SW_x + .02, Car_SW_y), fontsize=6)
            if Car_SW_FEI > 0:
                if footprint_plots == 'y':
                    pass
                    # Credit_Plot_Subplot.plot([axis_vec[0], ((A_Car - D_Car) / C_Car)], [A_Car, A_Car],
                    #                          linestyle='--', color='grey')
                    # Credit_Plot_Subplot.plot([((A_Car - D_Car) / C_Car), ((B_Car - D_Car) / C_Car)], \
                    #                          [A_Car, B_Car], linestyle='--', color='grey')
                    # Credit_Plot_Subplot.plot([((B_Car - D_Car) / C_Car), axis_vec[1]], \
                    #                          [B_Car, B_Car], linestyle='--', color='grey')
                    # Credit_Plot_Subplot.annotate('Car Target', xy=(axis_vec[0], A_Car), \
                    #                                      xytext=(axis_vec[0], A_Car), fontsize=7, \
                    #                              horizontalalignment='left')
                elif load_factor_plots != 'y':
                    Credit_Plot_Subplot.plot([0, 1.4], [0, 1.4 * 100 / Car_SW_FEI], linestyle='--', color='grey', \
                                             label='Car Target: ' + str(round(Car_SW_Target, 1)) + ' (g/mi)')
                    Credit_Plot_Subplot.annotate('Car Target', xy=(35 * Car_SW_FEI / 100, 35), \
                                                         xytext=(35 *Car_SW_FEI / 100, 35), fontsize=7, \
                                                 horizontalalignment='left')
                    Credit_Plot_Subplot.annotate('Car Target: ' + str(round(Car_SW_Target, 1)) + ' (g/mi)' \
                                                         , xy=(1.4,11.5), xytext=(1.4,11.5), fontsize=7, \
                                                 horizontalalignment = 'right')
            if len(OEM_Array_nonPEV) > 0 or (footprint_plots == 'y' and len(OEM_Array_allentries) > 0):
                for j in range(0, 2):
                    if j == 0 and (OEM_Color == negative_color).sum() != 0:
                        color = negative_color
                        if footprint_plots == 'y':
                            OEM_Array_unique_Plot = OEM_Subarray_allentries_unique[
                                (OEM_Color == negative_color)] \
                                .reset_index(drop=True)
                            sales_size = Sales_Size_Normalized[(OEM_Color == negative_color)].reset_index(drop=True)
                            credits_size = Credits_Size_Normalized[(OEM_Color == negative_color)].reset_index(drop=True)
                            if credit_integration == 'y':
                                credits_size_nonintegrated = Credits_Size_Normalized_nonintegrated[(OEM_Color == negative_color)].reset_index(drop=True)
                                colors_nonintegrated = OEM_Color_nonintegrated[(OEM_Color == negative_color)].reset_index(drop=True)
                        else:
                            OEM_Array_unique_Plot = OEM_Subarray_allentries_unique[
                                (OEM_Color == negative_color) & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                            sales_size = Sales_Size_Normalized[(OEM_Color == negative_color) & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                            credits_size = Credits_Size_Normalized[(OEM_Color == negative_color) & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                            if credit_integration == 'y':
                                credits_size_nonintegrated = Credits_Size_Normalized_nonintegrated[(OEM_Color == negative_color) & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                    .reset_index(drop=True)
                                colors_nonintegrated = OEM_Color_nonintegrated[(OEM_Color == negative_color) & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                    .reset_index(drop=True)
                    else:
                        color = positive_color
                        if footprint_plots == 'y':
                            OEM_Array_unique_Plot = OEM_Subarray_allentries_unique[
                                (OEM_Color == positive_color)] \
                                .reset_index(drop=True)
                            sales_size = Sales_Size_Normalized[(OEM_Color == positive_color)].reset_index(drop=True)
                            credits_size = Credits_Size_Normalized[(OEM_Color == positive_color)].reset_index(drop=True)
                            if credit_integration == 'y':
                                credits_size_nonintegrated = Credits_Size_Normalized_nonintegrated[(OEM_Color == positive_color)].reset_index(drop=True)
                                colors_nonintegrated = OEM_Color_nonintegrated[(OEM_Color == positive_color)].reset_index(drop=True)
                        else:
                            OEM_Array_unique_Plot = OEM_Subarray_allentries_unique[
                                (OEM_Color == positive_color) & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                            sales_size = Sales_Size_Normalized[(OEM_Color == positive_color) & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                               (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                            credits_size = Credits_Size_Normalized[(OEM_Color == positive_color) & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                                   (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                            if credit_integration == 'y':
                                credits_size_nonintegrated = Credits_Size_Normalized_nonintegrated[(OEM_Color == positive_color) & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                                                       (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                .reset_index(drop=True)
                                colors_nonintegrated = OEM_Color_nonintegrated[
                                    (OEM_Color == positive_color) & \
                                    (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'EV') & \
                                    (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-G') & \
                                    (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-D') & \
                                    (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'REEV-E')] \
                                    .reset_index(drop=True)
                    for o in range(0, 2):
                        if o == 0:
                            x_plot_vec = OEM_Array_unique_Plot[x_plot_category][OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                            y_plot_vec = OEM_Array_unique_Plot[y_plot_category][OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                            credit_plot_vec = credits_size[OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                            Credit_Plot_Subplot.scatter(x_plot_vec, y_plot_vec, facecolor=color, \
                                                                s=credit_plot_vec, \
                                                                edgecolor='none', alpha=0.5, linewidth=0) #color
                            if credit_integration == 'y':
                                x_plot_vec_nonintegrated = x_plot_vec
                                y_plot_vec_nonintegrated = y_plot_vec
                                credit_plot_vec_nonintegrated = credits_size_nonintegrated[OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                                color_plot_vec_nonintegrated = colors_nonintegrated[OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                                Credit_Plot_Subplot.scatter(x_plot_vec_nonintegrated, y_plot_vec_nonintegrated, facecolor = 'none', \
                                                            s=credit_plot_vec_nonintegrated, \
                                                            edgecolor=color_plot_vec_nonintegrated, alpha=1, linewidth=0.25, linestyle='-') #alpha_vec_nonintegrated_fleettype[w]
                        else:
                            x_plot_vec = OEM_Array_unique_Plot[x_plot_category][OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                            y_plot_vec = OEM_Array_unique_Plot[y_plot_category][OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                            credit_plot_vec = credits_size[OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                            Credit_Plot_Subplot.scatter(x_plot_vec, y_plot_vec, facecolor=color,s=credit_plot_vec, \
                                                                alpha=0.5, hatch='X', edgecolor='none', linewidth=0)
                            if credit_integration == 'y':
                                x_plot_vec_nonintegrated = OEM_Array_unique_Plot[x_plot_category][OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                y_plot_vec_nonintegrated = OEM_Array_unique_Plot[y_plot_category][OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                credit_plot_vec_nonintegrated = credits_size_nonintegrated[OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                color_plot_vec_nonintegrated = colors_nonintegrated[OEM_Array_unique_Plot['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                Credit_Plot_Subplot.scatter(x_plot_vec_nonintegrated, y_plot_vec_nonintegrated, facecolor='none',
                                                            s=credit_plot_vec_nonintegrated, \
                                                            alpha=1, edgecolor=color_plot_vec_nonintegrated, linewidth=0.25, linestyle='-') #alpha_vec_nonintegrated_fleettype[w]
                    Credit_Plot_Subplot.scatter(
                        OEM_Array_unique_Plot[x_plot_category], \
                        OEM_Array_unique_Plot[y_plot_category], facecolor='none', \
                        s=sales_size, edgecolor='black', linestyle='--', linewidth=0.25)  # linewidth = 0.25, dashes = (1,2)

                    l_a = Credit_Plot_Subplot.scatter([], [], edgecolor='green', \
                                                             facecolor='green', s=AC_Credit_Size, alpha=0.5)
                    l_b = Credit_Plot_Subplot.scatter([], [], edgecolor='green', \
                                                             facecolor='green', s=FFV_Credit_Size, alpha=0.5)
                    l_c = Credit_Plot_Subplot.scatter([], [], edgecolor='green', \
                                                             facecolor='green', s=Offcycle_Credit_Size, alpha=0.5)
                    l_d = Credit_Plot_Subplot.scatter([], [], edgecolor='red', \
                                                             facecolor='red', s=abs(N2OCH4_Credit_Size), alpha=0.5)
                    if Tailpipe_Error_Credit_Size < 0:
                        l_e = Credit_Plot_Subplot.scatter([], [], edgecolor='red', \
                                                                 facecolor='red', s=abs(Tailpipe_Error_Credit_Size), alpha=0.5)
                    else:
                        l_e = Credit_Plot_Subplot.scatter([], [], edgecolor='green', \
                                                                 facecolor='green', s=Tailpipe_Error_Credit_Size, alpha=0.5)
                    # if Target_Error_Credit_Size < 0:
                    #     l_f = Credit_Plot_Subplot.scatter([], [], edgecolor='red', \
                    #                                              facecolor='red', s=abs(Target_Error_Credit_Size), alpha=0.5)
                    # else:
                    #     l_f = Credit_Plot_Subplot.scatter([], [], edgecolor='green', \
                    #                                              facecolor='green', s=Target_Error_Credit_Size, alpha=0.5)
                    # if FFV_Error_Credit_Size < 0:
                    #     l_g = Credit_Plot_Subplot.scatter([], [], edgecolor='red', \
                    #                                              facecolor='red', s=abs(FFV_Error_Credit_Size), alpha=0.5)
                    # else:
                    #     l_g = Credit_Plot_Subplot.scatter([], [], edgecolor='green', \
                    #                                              facecolor='green', s=FFV_Error_Credit_Size, alpha=0.5)

                    if credit_integration == 'y':
                        pass
                        l_letter_labels = pd.Series(['Tailpipe Error'])
                        l_legend_categories = pd.Series([l_e])
                        # if target_credit  != 'all':
                        #     l_letter_labels_extended = pd.Series(['AC', 'FFV', 'Off-Cycle', 'N20-CH4'])
                        #     excluded_credit_categories = pd.Series(credit_legend_category.split(',')).order().reset_index(drop=True)
                        #     if len(excluded_credit_categories) > 1:
                        #         l_legend_categories_extended = pd.Series([l_a,l_c,l_d])
                        #         for legend_iteration in range (0,len(excluded_credit_categories)):
                        #             target_label_index = l_letter_labels_extended[l_letter_labels_extended == excluded_credit_categories[legend_iteration]].index[0]
                        #             l_letter_labels_extended = l_letter_labels_extended.drop(target_label_index).reset_index(drop=True)
                        #             l_legend_categories_extended = l_legend_categories_extended.drop(target_label_index).reset_index(drop=True)
                        #     else:
                        #         target_label_index = l_letter_labels_extended[l_letter_labels_extended == credit_legend_category].index[0]
                        #         l_letter_labels_extended = l_letter_labels_extended.drop(target_label_index).reset_index(drop=True)
                        #         l_legend_categories_extended = pd.Series([l_a,l_b,l_c,l_d]).drop(target_label_index).reset_index(drop=True)
                        #     l_letter_labels = pd.concat([l_letter_labels_extended,l_letter_labels]).reset_index(drop=True)
                        #     l_legend_categories = pd.concat([l_legend_categories_extended, l_legend_categories]).reset_index(drop=True)
                        if footprint_plots == 'y':
                            leg2 = Credit_Plot_Subplot.legend(l_legend_categories, l_letter_labels, ncol=len(l_legend_categories),
                                                               frameon=True,
                                                               fontsize=6, handlelength=None, loc='lower left',
                                                               handletextpad=None, \
                                                               scatterpoints=1, mode='expand', labelspacing=1.5, \
                                                               bbox_to_anchor=(0, 1, 1, 0.09))
                        else:
                            leg2 = Credit_Plot_Subplot2.legend(l_legend_categories, l_letter_labels, ncol=len(l_legend_categories),
                                                              frameon=True,
                                                              fontsize=6, handlelength=None, loc='lower left',
                                                              handletextpad=None, \
                                                              scatterpoints=1, mode='expand', labelspacing=1.5, \
                                                              bbox_to_anchor=(0, 1, 1, 0.09))
                    else:
                        l_letter_labels = pd.Series(['FFV', 'AC', 'Off-Cycle', 'N20-CH4', 'Tailpipe Error'])
                        if model_year >= 2016:
                            l_letter_labels = l_letter_labels[l_letter_labels != 'FFV'].reset_index(drop=True)
                        if footprint_plots == 'y': #CRITICAL CODE
                            #pass
                            leg2 = Credit_Plot_Subplot.legend([l_a, l_c, l_d, l_e], l_letter_labels, ncol=len(l_letter_labels), frameon=True,
                                                              fontsize=6, handlelength=None, loc='lower left',
                                                              handletextpad=None,\
                                                                 scatterpoints=1,mode='expand', labelspacing=1.5, \
                                                       bbox_to_anchor=(0,1, 1, 0.09))
                        else:
                            if model_year < 2016:
                                leg2 = Credit_Plot_Subplot2.legend([l_b, l_a, l_c, l_d, l_e], l_letter_labels, ncol=len(l_letter_labels), frameon=True,
                                                                  fontsize=6, handlelength=None, loc='lower left',
                                                                  handletextpad=None, \
                                                                     scatterpoints=1,mode='expand', labelspacing=1.5, \
                                                           bbox_to_anchor=(0,1, 1, 0.09))
                            else:
                                leg2 = Credit_Plot_Subplot2.legend([l_a, l_c, l_d, l_e], l_letter_labels, ncol=len(l_letter_labels), frameon=True,
                                                                  fontsize=6, handlelength=None, loc='lower left',
                                                                  handletextpad=None, \
                                                                     scatterpoints=1,mode='expand', labelspacing=1.5, \
                                                           bbox_to_anchor=(0,1, 1, 0.09))
                if len(OEM_Array_Output_Conventional) > 0 and OEM_Array_Output_Conventional['Sales'].sum()>0:
                    if len(OEM_Array_Output_Conventional) < numlabels:
                        numlabels_adj = len(OEM_Array_Output_Conventional)
                    else:
                        numlabels_adj = numlabels
                    top_sales_array = (OEM_Array_Output_Conventional[OEM_Array_Output_Conventional['Sales'] >= \
                                                                      heapq.nlargest(numlabels_adj,OEM_Array_Output_Conventional['Sales'])[-1]]).sort('Sales', ascending=True).reset_index(drop=True)
                    if credit_integration == 'y':
                        CO2_category = 'Post-Tech CO2 Credits (g CO2)'
                    else:
                        CO2_category = 'Pre-Tech CO2 Credits (g CO2)'
                    credit_generation_array = OEM_Array_Output_Conventional[OEM_Array_Output_Conventional[CO2_category] > 0].reset_index(drop=True)
                    if len(credit_generation_array) < numlabels_adj and len(credit_generation_array) > 0:
                        credit_gen_numlabels_adj = len(credit_generation_array)
                    elif len(credit_generation_array) != 0:
                        credit_gen_numlabels_adj = numlabels_adj
                    if len(credit_generation_array) > 0:
                        top_credits_array = (OEM_Array_Output_Conventional[OEM_Array_Output_Conventional[CO2_category] >= \
                                                                              heapq.nlargest(credit_gen_numlabels_adj,credit_generation_array[CO2_category])[-1]]).sort(CO2_category, ascending=True).reset_index(drop=True)
                    credit_deficit_array = OEM_Array_Output_Conventional[OEM_Array_Output_Conventional[CO2_category] < 0].reset_index(drop=True)
                    if len(credit_deficit_array) < numlabels_adj and len(credit_deficit_array) > 0:
                        credit_deficit_numlabels_adj = len(credit_deficit_array)
                    elif len(credit_deficit_array) != 0:
                        credit_deficit_numlabels_adj = numlabels_adj
                    bottom_credits_array = (OEM_Array_Output_Conventional[OEM_Array_Output_Conventional[CO2_category] <= \
                                                                          heapq.nsmallest(credit_deficit_numlabels_adj,credit_deficit_array[CO2_category])[-1]]).sort(CO2_category, ascending=False).reset_index(drop=True)
                    if len(credit_generation_array) == 0 and len(credit_deficit_array) > 0:
                        shift_array_int = pd.concat([top_sales_array, bottom_credits_array]).drop_duplicates(keep='first').reset_index(drop=True)
                    elif len(credit_generation_array) > 0 and len(credit_deficit_array) == 0:
                        shift_array_int = pd.concat([top_sales_array, top_credits_array]).drop_duplicates(keep='first').reset_index(drop=True)
                    else:
                        shift_array_int = pd.concat([top_sales_array, top_credits_array, bottom_credits_array]).drop_duplicates(keep='first').reset_index(drop=True)
                    sales_rank_vec = pd.Series(shift_array_int['Sales'].rank(method='dense', ascending=False).astype(int).reset_index(drop=True), name='Sales Rank')
                    top_credit_rank_vec = pd.Series(shift_array_int[CO2_category].rank(method='dense', ascending=False).astype(int).reset_index(drop=True), name = 'Top Credit Rank')
                    if credit_gen_numlabels_adj < numlabels_adj:
                        top_credit_rank_vec[top_credit_rank_vec > credit_gen_numlabels_adj] = ((3*numlabels)+1)
                    bottom_credit_rank_vec = pd.Series(shift_array_int[CO2_category].rank(method='dense', ascending=True).astype(int).reset_index(drop=True), name = 'Bottom Credit Rank')
                    if len(credit_generation_array) == 0:
                        credit_rank_vec = pd.Series(bottom_credit_rank_vec.astype(int), name = 'Credit Rank')
                    else:
                        credit_rank_vec = pd.Series(pd.concat([top_credit_rank_vec, bottom_credit_rank_vec],axis=1).min(axis=1).astype(int), name = 'Credit Rank')
                    shift_array_int2 = pd.concat([shift_array_int, sales_rank_vec, credit_rank_vec],axis=1).reset_index(drop=True)
                    if len(credit_generation_array) == 0:
                        shift_array_int2_deficit = shift_array_int2
                    else:
                        shift_array_int2_deficit = shift_array_int2[shift_array_int2[CO2_category] < 0].reset_index(drop=True)
                    if len(credit_generation_array) > 0:
                        shift_array_int2_generator = shift_array_int2[shift_array_int2[CO2_category] > 0].reset_index(drop=True)
                        shift_array_int3 = pd.concat([shift_array_int2[shift_array_int2['Sales Rank'] <= numlabels_adj], \
                                                       shift_array_int2_generator[shift_array_int2_generator['Credit Rank'] <= credit_gen_numlabels_adj], \
                                                      shift_array_int2_deficit[shift_array_int2_deficit['Credit Rank'] <= credit_deficit_numlabels_adj]]).drop_duplicates(keep='first').reset_index(drop=True)
                    else:
                        shift_array_int3 = pd.concat([shift_array_int2[shift_array_int2['Sales Rank'] <= numlabels_adj], \
                                                      shift_array_int2_deficit[shift_array_int2_deficit['Credit Rank'] <= credit_deficit_numlabels_adj]]).drop_duplicates(keep='first').reset_index(drop=True)
                    shift_array_int3['Sales Rank'][shift_array_int3['Sales Rank'] > numlabels_adj] = 0
                    shift_array_int3['Credit Rank'][shift_array_int3['Credit Rank'] > numlabels_adj] = 0
                    shift_array_int3['Plot Color'][(shift_array_int3['Sales Rank'] > 0) & (shift_array_int3['Credit Rank'] == 0)] = 'black'
                    model_shift_vec = shift_array_int3['Models']
                    sales_rank_vec = shift_array_int3['Sales Rank']
                    credit_rank_vec = shift_array_int3['Credit Rank']
                    label_shift_vec1 = pd.Series(np.zeros(len(shift_array_int3)), name='Label Pt1')
                    label_shift_vec2 = pd.Series(np.zeros(len(shift_array_int3)), name='Label Pt2')

                    for s in range(0, len(shift_array_int3)):
                        if sales_rank_vec[s] > 0 and credit_rank_vec[s] > 0:
                            label_shift_vec1[s] = '#' + str(int(credit_rank_vec[s])) + ', ' + str(model_shift_vec[s])
                            label_shift_vec2[s] = '(#' + str(int(sales_rank_vec[s])) + ' Sales)'
                            if (sales_rank_vec==sales_rank_vec[s]).sum() > 1:
                                label_shift_vec2[s] +=  ' Tie'
                        elif sales_rank_vec[s] > 0 and credit_rank_vec[s] == 0:
                            label_shift_vec1[s] = '#' + str(int(sales_rank_vec[s])) + ', Sales, ' + str(model_shift_vec[s])
                            label_shift_vec2[s] = ''
                            if (sales_rank_vec == sales_rank_vec[s]).sum() > 1:
                                label_shift_vec2[s] += ' Tie'
                        elif sales_rank_vec[s] == 0 and credit_rank_vec[s] > 0:
                            label_shift_vec1[s] = '#' + str(int(credit_rank_vec[s])) + ', ' + str(model_shift_vec[s])
                            label_shift_vec2[s] = ''
                    shift_array = pd.concat([shift_array_int3, label_shift_vec1, label_shift_vec2], axis=1) \
                        .sort(y_plot_category, ascending=True).reset_index(drop=True)
                    shift_array = shift_array[shift_array['Models'] != 0].reset_index(drop=True)
                    shift_array.to_csv(save_string + ' plot details.csv',index=False)
                    x_shift_vec = shift_array[x_plot_category]
                    y_shift_vec = shift_array[y_plot_category]
                    label_shift_vec1 = shift_array['Label Pt1']
                    label_shift_vec2 = shift_array['Label Pt2']
                    color_shift_vec = shift_array['Plot Color']
                    r1 = int(round(0.25 * len(x_shift_vec), 0))
                    r2 = int(round(0.75 * len(x_shift_vec), 0))
                    rmax = len(x_shift_vec)
                    label_shift_vec = label_shift_vec1 + label_shift_vec2
                    # bottom_loop_array = shift_array[:r1].sort('x',ascending=True).reset_index(drop=True)
                    try:
                        1/(OEM_Subarray_allentries_unique['Sales'].sum())
                    except ZeroDivisionError:
                        continue
                    else:
                        x_divide = (OEM_Subarray_allentries_unique[x_plot_category]*\
                                   OEM_Subarray_allentries_unique['Sales']).sum()/(OEM_Subarray_allentries_unique['Sales'].sum())
                    for r in range(0, len(x_shift_vec)):
                        if r < r1:
                            xytext_x =  (r/r1) # (r / r1) - .001 * r * len(label_shift_vec1[r])
                            xytext_y = (r/rmax)   #0.03 * (r + 1)
                            if r <= r1/2:
                                halign = 'left'
                            else:
                                halign = 'right'
                            valign='bottom'
                        elif r >= r1 and r <= r2:
                            if x_shift_vec[r] <= x_divide:
                                xytext_x = 0.05
                                halign = 'left'
                            else:
                                xytext_x = 1.15/1.4 #0.75 - .0025 * (r - r1) * len(label_shift_vec1[r])
                                halign = 'right'
                            xytext_y = (r/rmax) #0.03 * (r1 + 1) + 0.65 * (r / r2)
                            valign='None'
                        elif r > r2:
                            xytext_x = 0.05#(1/(2*(len(x_shift_vec)-r2)))*(len(x_shift_vec)-r)  # 0.4 - 0.4 * (r / len(x_shift_vec))
                            xytext_y = r/rmax  #1 - 0.05 * (len(x_shift_vec) - r)
                            halign='left'
                            valign='top'
                        #if footprint_plots == 'y':
                            #xy_shift_vec = x_shift_vec+y_shift_vec
                        # if ((shift_array['Label Pt1'] + shift_array['Label Pt2'])[:(r + 1)] == label_shift_vec[r]).sum() == 1:  # and (y_shift_vec[:(r + 1)] == y_shift_vec[r]).sum() == 1
                        Credit_Plot_Subplot.annotate(
                            str(shift_array['Label Pt1'][r]) + '\n' + str(shift_array['Label Pt2'][r]), \
                            xy=(shift_array[x_plot_category][r], shift_array[y_plot_category][r]),
                            xytext=(xytext_x, xytext_y), horizontalalignment = halign, verticalalignment=valign,  # xytext = (xytext_x,xytext_y)
                            textcoords='axes fraction', fontsize=6, xycoords='data', color=color_shift_vec[r],  # verticalalignment='bottom',\
                            arrowprops=dict(arrowstyle="-", shrinkA=0, linewidth=0.5, \
                                            shrinkB=0, connectionstyle="arc3", color=shift_array['Plot Color'][r]))
                    if Array_Truck_sales > 0:
                        Credit_Plot_Subplot.scatter([Truck_SW_x], [Truck_SW_y], \
                                                            color='black', marker='*', s=10)
                        Credit_Plot_Subplot.annotate('Truck Actual', xy=(Truck_SW_x, Truck_SW_y), \
                                                             xytext=(Truck_SW_x + .02, Truck_SW_y), fontsize=6)

                if Truck_SW_FEI > 0:
                    if footprint_plots == 'y':
                        pass
                        # Credit_Plot_Subplot.plot([axis_vec[0], ((A_Truck-D_Truck)/C_Truck)], [A_Truck, A_Truck], linestyle='--', color='grey' )
                        # Credit_Plot_Subplot.plot([((A_Truck - D_Truck) / C_Truck), ((B_Truck - D_Truck) / C_Truck)], \
                        #                          [A_Truck, B_Truck],linestyle='--', color='grey')
                        # Credit_Plot_Subplot.plot([((B_Truck - D_Truck) / C_Truck), axis_vec[1]], \
                        #                         [B_Truck, B_Truck], linestyle='--', color='grey')
                        # Credit_Plot_Subplot.annotate('Truck Target' , xy=(axis_vec[0], A_Truck), \
                        #                              xytext=(axis_vec[0], A_Truck),fontsize=7, \
                        #                              horizontalalignment='left')
                        # Credit_Plot_Subplot.annotate('Truck Target: ' + str(round(Truck_SW_Target, 1)) + ' (g/mi)'  , \
                        #     xy=(70, B_Truck), xytext=(70, B_Truck), fontsize=7, horizontalalignment='right')
                    elif load_factor_plots != 'y':
                        Credit_Plot_Subplot.plot([0, 1.4], [0, 1.4 * 100 / Truck_SW_FEI], linestyle='--', color='grey', \
                                                 label='Truck Target: ' + str(round(Truck_SW_Target, 1)) + ' (g/mi)')
                        Credit_Plot_Subplot.annotate('Truck Target' , xy=(35 * Truck_SW_FEI / 100, 35), \
                                                     xytext=(35 *Truck_SW_FEI / 100, 35),fontsize=7, \
                                                     horizontalalignment='left')
                        Credit_Plot_Subplot.annotate('Truck Target: ' + str(round(Truck_SW_Target, 1)) + ' (g/mi)'  , \
                            xy=(1.4, 10.5), xytext=(1.4,10.5), fontsize=7, horizontalalignment='right')
            if OEM_Array_Output['Sales'].sum() > 0:
                for fleettype_table_count in range(0, len(fleettype_vec_table)):
                    #car, truck or all
                    cd = fleettype_vec_table[fleettype_table_count]
                    if fleettype_table_count == 0:
                        table_categories = car_table_categories
                        VMT = VMT_C
                        reported_tailpipe_emissions = \
                            credit_file['Fleet Average Credits_Mg_PV'][credit_file['CAFE Manufacturer Name']==OEM].sum()
                    elif fleettype_table_count == 1:
                        table_categories = truck_table_categories
                        VMT = VMT_T
                        reported_tailpipe_emissions = \
                            credit_file['Fleet Average Credits_Mg_LT'][credit_file['CAFE Manufacturer Name']==OEM].sum()
                    elif fleettype_table_count == 2:
                        table_categories = overall_table_categories
                    for table_row_count in range(0, (len(table_pt2_categories) + 1)):
                        #row number for each table (car table, truck table, all table)
                        print(str(fleettype_table_count)+','+str(table_row_count))
                        if cd != 'All':
                            OEM_Array_VehicleType_allentries = OEM_Array_allentries[\
                                OEM_Array_allentries['COMPLIANCE_CATEGORY_CD']==cd].reset_index(drop=True)
                        else:
                            OEM_Array_VehicleType_allentries = OEM_Array_allentries
                        if table_row_count == 0: #'C','T'or'All'
                            table_pt1[table_row_count] = fleettype_vec_table[fleettype_table_count]
                        elif table_row_count == 1: #Sales Weighted Footprint
                            if len(OEM_Array_VehicleType_allentries) > 0:
                                OEM_Array_VehicleType_allentries = OEM_Array_VehicleType_allentries[\
                                    (~pd.isnull(OEM_Array_VehicleType_allentries['FOOTPRINT_SUBCONFIG_SALES'])) & \
                                     (~pd.isnull(OEM_Array_VehicleType_allentries['Footprint_Master Index']))]
                                table_pt1[table_row_count] = str(round(np.average(OEM_Array_VehicleType_allentries['Footprint_Master Index']\
                                    , weights = OEM_Array_VehicleType_allentries['FOOTPRINT_SUBCONFIG_SALES'] ),1)) + ' sqft'
                            else:
                                table_pt1[table_row_count] = '0 sqft'
                        elif table_row_count == 2: #Sales Percentage
                            target_sales = OEM_Array_VehicleType_allentries['FOOTPRINT_SUBCONFIG_SALES'].sum()
                            total_sales = OEM_Array_allentries['FOOTPRINT_SUBCONFIG_SALES'].sum()
                            if fleettype_table_count == 2: #'All'
                                table_pt1[table_row_count] = ''
                            else:
                                if total_sales > 0:
                                    table_pt1[table_row_count] = str(int(round(100 * target_sales / total_sales, 0))) + '%'
                                else:
                                    table_pt1[table_row_count] = str(0) + '%'
                        if table_row_count == len(table_pt2_categories): #Totaling Credits
                            if fleettype_table_count == 2:
                                table_pt2[table_row_count] = 'Total'
                            else:
                                table_pt2[table_row_count] = 'Subtotal'
                            table_pt3[table_row_count] = ''
                            table_pt4[table_row_count] = int(round(table_pt4[:table_row_count].astype(int).sum(), 0))
                            # table_pt4[u] = format(int(table_pt4[u]),',d')
                        else: #All other categories
                            table_pt2[table_row_count] = str(table_pt2_categories[table_row_count])
                            if fleettype_table_count == 2: #All
                                table_pt4[table_row_count] = int(round(plot_table['Mg'][table_row_count] + \
                                                         plot_table['Mg'][table_row_count + (len(table_pt2_categories) + 1)], 0))
                                OEM_Array_VehicleType_allentries = OEM_Array_VehicleType_allentries[ \
                                    (~pd.isnull(OEM_Array_VehicleType_allentries['CO2 Target_Master Index'])) & \
                                    (~pd.isnull(OEM_Array_VehicleType_allentries[
                                                    'CO2 Tailpipe Emissions_Master Index']))].reset_index(drop=True)
                                table_pt3[table_row_count] = int(round(plot_table['g/mi'][table_row_count]*.01*int(plot_table.ix[:,0][2][:-1]) + \
                                    plot_table['g/mi'][table_row_count + (len(table_pt2_categories) + 1)]*.01*\
                                    int(plot_table.ix[:,0][2+ len(table_pt2_categories) + 1][:-1]), 0))

                                        # if table_row_count < 2:
                                #     table_pt3[table_row_count] = int(round(np.average(pd.Series(OEM_Array_VehicleType_allentries[\
                                #         'CO2 Target_Master Index']-OEM_Array_VehicleType_allentries[\
                                #         'CO2 Tailpipe Emissions_Master Index']), \
                                #         weights = OEM_Array_VehicleType_allentries['FOOTPRINT_SUBCONFIG_SALES']),0))
                                # else:
                                #     table_pt3[table_row_count] = ''

                                # table_pt4[u] = format(int(table_pt4[u]), ',d')
                            else: #Car or Truck
                                if table_row_count < 2:
                                    if table_row_count == 0: #non-PEV vehicles
                                        OEM_Array_VehicleType_ss_allentries = Powertrain_Array_Filter.Powertrain_Array_Filter\
                                        (Powertrain_Array_allentries, 'Present', 'Sales','nonPEV', str(OEM_unique_vec[i]),cd, 'None', 'None')
                                    elif table_row_count == 1: #PEV vehicles
                                        OEM_Array_VehicleType_ss_allentries = Powertrain_Array_Filter.Powertrain_Array_Filter\
                                        (Powertrain_Array_allentries, 'Present', 'Sales','PEV', str(OEM_unique_vec[i]),cd, 'None', 'None')
                                    if len(OEM_Array_VehicleType_ss_allentries) > 0 and \
                                            OEM_Array_VehicleType_ss_allentries['FOOTPRINT_SUBCONFIG_SALES'].sum() > 0:
                                        table_pt4[table_row_count] = int(round(OEM_Array_VehicleType_ss_allentries['Pre-Tech CO2 Credits (g CO2)'].sum()*1e-6, 0))
                                        OEM_Array_VehicleType_ss_allentries = OEM_Array_VehicleType_ss_allentries[\
                                            (~pd.isnull(OEM_Array_VehicleType_ss_allentries['CO2 Target_Master Index'])) & \
                                            (~pd.isnull(OEM_Array_VehicleType_ss_allentries['CO2 Tailpipe Emissions_Master Index']))].reset_index(drop=True)
                                        table_pt3[table_row_count] = int(round(np.average(pd.Series(OEM_Array_VehicleType_ss_allentries[\
                                            'CO2 Target_Master Index']-OEM_Array_VehicleType_ss_allentries[\
                                            'CO2 Tailpipe Emissions_Master Index']), \
                                            weights = OEM_Array_VehicleType_ss_allentries['FOOTPRINT_SUBCONFIG_SALES']),0))
                                    else:
                                        table_pt3[table_row_count] = 0
                                        table_pt4[table_row_count] = 0
                                else:
                                    OEM_Array_VehicleType_ss_allentries = Powertrain_Array_Filter.Powertrain_Array_Filter \
                                        (Powertrain_Array_allentries, 'Present', 'Sales', 'None',str(OEM_unique_vec[i]), cd, 'None', 'None')
                                    category = all_table_categories[table_row_count]
                                    if category == 'Tailpipe Error (g CO2)':
                                        if target_sales > 0:
                                            if model_year >= 2016:
                                                table_pt4[table_row_count] = (reported_tailpipe_emissions) - (table_pt4[0:2].sum())
                                            else:
                                                table_pt4[table_row_count] = (reported_tailpipe_emissions) - (table_pt4[0:3].sum())
                                            table_pt3[table_row_count] = table_pt4[table_row_count]*1e6/(VMT*target_sales)
                                        else:
                                            table_pt3[table_row_count] = 0
                                            table_pt4[table_row_count] = 0
                                    elif target_sales > 0:
                                        table_pt4[table_row_count] = int(round(OEM_Array_VehicleType_ss_allentries[category].sum() * 1e-6,0))
                                        # OEM_Array_VehicleType_ss_allentries = OEM_Array_VehicleType_ss_allentries[ \
                                        #     (~pd.isnull(OEM_Array_VehicleType_ss_allentries['CO2 Target_Master Index'])) & \
                                        #     (~pd.isnull(OEM_Array_VehicleType_ss_allentries[
                                        #                     'CO2 Tailpipe Emissions_Master Index']))].reset_index(drop=True)
                                        table_pt3[table_row_count] = int(round(table_pt4[table_row_count]*1e6/(target_sales*VMT),0))
                                    else:
                                        table_pt3[table_row_count] = 0
                                        table_pt4[table_row_count] = 0
                                    # table_pt4[u] = format(int(table_pt4[u]), ',d')
                    table_pt1[table_pt1 == 0] = ''
                    plot_table_fleettype = pd.concat([table_pt1, table_pt2, table_pt3, table_pt4], axis=1)
                    if fleettype_table_count == 0:
                        plot_table = plot_table_fleettype.reset_index(drop=True)
                    else:
                        plot_table = pd.concat([plot_table, plot_table_fleettype]).reset_index(drop=True)
                for u in range(0, len(plot_table)):
                    if plot_table['g/mi'][u] != '':
                        try:
                            plot_table['g/mi'][u] = int(plot_table['g/mi'][u])
                        except ValueError:
                            pass
                    plot_table['Mg'][u] = format(int(plot_table['Mg'][u]), ',d')
            # #plot_table.to_csv(output_path + '\\' + str(model_year) + ' ' + OEM_save_name + ' plot table.csv',
            #                   index=False)
            color_pair = ['red', 'green']
            # if iterative_year == 0:
            #     OEM_Array_allentries_unique_sales = OEM_Array_allentries_unique['FOOTPRINT_SUBCONFIG_SALES']
            # else:
            #     OEM_Array_allentries_unique_sales = OEM_Array_allentries_unique['Projected Sales']
            if len(OEM_Array_allentries_unique) != len(OEM_Array_nonPEV_unique) and footprint_plots != 'y':
                for j in range(0, 2):
                    PEV_Array = OEM_Subarray_allentries_unique[
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'No S-S') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'S-S') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'MHEV') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'HEV') & \
                        (OEM_Color == color_pair[j])].reset_index(drop=True)
                    PEV_Sales_Size = Sales_Size_Normalized[
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'No S-S') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'S-S') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'MHEV') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'HEV') & \
                        (OEM_Color == color_pair[j])].reset_index(drop=True)
                    PEV_Credits_Size = Credits_Size_Normalized[
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'No S-S') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'S-S') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'MHEV') & \
                        (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'HEV') & \
                        (OEM_Color == color_pair[j])].reset_index(drop=True)
                    if credit_integration == 'y':
                        PEV_Credits_Size_nonintegrated = Credits_Size_Normalized_nonintegrated[
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'No S-S') & \
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'S-S') & \
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'MHEV') & \
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'HEV') & \
                            (OEM_Color == color_pair[j])].reset_index(drop=True)
                        PEV_Color_nonintegrated = OEM_Color_nonintegrated[
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'No S-S') & \
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'S-S') & \
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'MHEV') & \
                            (OEM_Subarray_allentries_unique['Stop-Start Tech Category'] != 'HEV') & \
                            (OEM_Color == color_pair[j])].reset_index(drop=True)

                    for o in range(0, 2):
                        if o == 0:
                            x_plot_vec = PEV_Array[x_plot_category][
                                PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                            y_plot_vec = 0 * PEV_Array[y_plot_category][
                                PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                            ss_car_vec = PEV_Array['Stop-Start Tech Category'][PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(
                                drop=True)
                            y_plot_vec[ss_car_vec != 'EV'] = 0
                            y_plot_vec[ss_car_vec == 'EV'] = 1
                            if load_factor_plots == 'y' and len(x_plot_vec)>0:
                                pev_credits_vec = PEV_Credits_Size[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                                pev_sales_vec = PEV_Sales_Size[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                                x_plot_vec[ss_car_vec != 'EV'] = 4
                                x_plot_vec[ss_car_vec == 'EV'] = 8
                                if len(x_plot_vec[ss_car_vec != 'EV']) > 0:
                                    Credit_Plot_Subplot2.scatter(x_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0], \
                                                                 y_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0], facecolor=color_pair[j], \
                                                                         s=pev_credits_vec[(ss_car_vec != 'EV')].sum(), \
                                                                         edgecolor='none', alpha=0.5)
                                    Credit_Plot_Subplot2.scatter(
                                        x_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0], \
                                        y_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0],
                                        facecolor='none', \
                                        s=pev_sales_vec[ss_car_vec != 'EV'].sum(), edgecolor='black', linestyle='--',
                                        linewidth=0.25)
                                if len(x_plot_vec[ss_car_vec == 'EV']) > 0:
                                    Credit_Plot_Subplot2.scatter(x_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[0], \
                                                                 y_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[0], facecolor=color_pair[j], \
                                                                 s=pev_credits_vec[(ss_car_vec == 'EV')].sum(), \
                                                                 edgecolor='none', alpha=0.5)
                                    Credit_Plot_Subplot2.scatter(
                                        x_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[0], \
                                        y_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[0],
                                        facecolor='none', \
                                        s=pev_sales_vec[ss_car_vec == 'EV'].sum(), edgecolor='black', linestyle='--',
                                        linewidth=0.25)
                            else:
                                Credit_Plot_Subplot2.scatter(x_plot_vec, y_plot_vec, facecolor=color_pair[j], \
                                                             s=PEV_Credits_Size[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'], \
                                                             edgecolor='none', alpha=0.5)
                            if credit_integration == 'y':
                                PEV_credit_plot_vec = PEV_Credits_Size_nonintegrated[
                                    PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                                PEV_color_plot_vec = PEV_Color_nonintegrated[
                                    PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'PV'].reset_index(drop=True)
                                for w in range (0,len(x_plot_vec)):
                                    if load_factor_plots == 'y' and len(x_plot_vec)>0:
                                        if len(x_plot_vec[ss_car_vec != 'EV']) > 0:
                                            Credit_Plot_Subplot2.scatter(x_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0], \
                                                                         y_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0], facecolor='none', \
                                                                         s=PEV_credit_plot_vec[ss_car_vec != 'EV'].sum(), \
                                                                         edgecolor=PEV_color_plot_vec[ss_car_vec != 'EV'].reset_index(drop=True)[0], alpha=1, \
                                                                         linewidth=0.25, linestyle='-')
                                        if len(x_plot_vec[ss_car_vec == 'EV']) > 0:
                                            Credit_Plot_Subplot2.scatter(x_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[0], \
                                                                         y_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[0],
                                                                         facecolor='none', \
                                                                         s=PEV_credit_plot_vec[ss_car_vec == 'EV'].sum(), \
                                                                         edgecolor=PEV_color_plot_vec[ss_car_vec == 'EV'].reset_index(drop=True)[
                                                                             0], alpha=1, \
                                                                         linewidth=0.25, linestyle='-')
                                    else:
                                        Credit_Plot_Subplot2.scatter(x_plot_vec[w], y_plot_vec[w], facecolor='none', \
                                                                     s=PEV_credit_plot_vec[w], \
                                                                     edgecolor=PEV_color_plot_vec[w], alpha=1, \
                                                                     linewidth=0.25, linestyle='-')
                        else: #truck
                            x_plot_vec = PEV_Array[x_plot_category][
                                PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                            y_plot_vec = 0 * PEV_Array[y_plot_category][
                                PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                            ss_truck_vec = PEV_Array['Stop-Start Tech Category'][
                                PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                            y_plot_vec[ss_truck_vec != 'EV'] = 0
                            y_plot_vec[ss_truck_vec == 'EV'] = 1
                            if load_factor_plots == 'y' and len(x_plot_vec)>0:
                                x_plot_vec[ss_truck_vec != 'EV'] = 4
                                x_plot_vec[ss_truck_vec == 'EV'] = 8
                                pev_credits_vec = PEV_Credits_Size[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                pev_sales_vec = PEV_Sales_Size[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                if len(x_plot_vec[ss_truck_vec != 'EV']) > 0:
                                    Credit_Plot_Subplot2.scatter(x_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0], \
                                                                 y_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0], facecolor=color_pair[j], \
                                                                 s=pev_credits_vec[(ss_truck_vec != 'EV')].sum(), \
                                                                 alpha=0.5, hatch='X', edgecolor='none')
                                    Credit_Plot_Subplot2.scatter(
                                        x_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0], \
                                        y_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0],
                                        facecolor='none', \
                                        s=pev_sales_vec[ss_truck_vec != 'EV'].sum(), edgecolor='black', linestyle='--',
                                        linewidth=0.25)
                                if len(x_plot_vec[ss_truck_vec == 'EV']) > 0:
                                    Credit_Plot_Subplot2.scatter(x_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0], \
                                                                 y_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0], facecolor=color_pair[j], \
                                                                 s=pev_credits_vec[(ss_truck_vec != 'EV')].sum(), \
                                                                 alpha=0.5, hatch='X', edgecolor='none')
                                    Credit_Plot_Subplot2.scatter(
                                        x_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0], \
                                        y_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0],
                                        facecolor='none', \
                                        s=pev_sales_vec[ss_truck_vec == 'EV'].sum(), edgecolor='black', linestyle='--',
                                        linewidth=0.25)
                            else:
                                Credit_Plot_Subplot2.scatter(x_plot_vec, y_plot_vec, facecolor=color_pair[j], \
                                                                 s=PEV_Credits_Size[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'], \
                                                                 alpha=0.5, hatch='X', edgecolor='none')
                            if credit_integration == 'y':
                                for w in range (0,len(x_plot_vec)):
                                    PEV_credit_plot_vec = PEV_Credits_Size_nonintegrated[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                    PEV_color_plot_vec = PEV_Color_nonintegrated[PEV_Array['COMPLIANCE_CATEGORY_CD'] == 'LT'].reset_index(drop=True)
                                    if load_factor_plots == 'y' and len(x_plot_vec)>0:
                                        if len(x_plot_vec[ss_truck_vec != 'EV']) > 0:
                                            Credit_Plot_Subplot2.scatter(x_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0], \
                                                                         y_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0], facecolor='none', \
                                                                         s=PEV_credit_plot_vec[ss_truck_vec != 'EV'].sum(), \
                                                                         edgecolor=PEV_color_plot_vec[ss_truck_vec != 'EV'].reset_index(drop=True)[0], alpha=1, \
                                                                         linewidth=0.25, linestyle='-')
                                        if len(x_plot_vec[ss_truck_vec == 'EV']) > 0:
                                            Credit_Plot_Subplot2.scatter(x_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0], \
                                                                         y_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0],
                                                                         facecolor='none', \
                                                                         s=PEV_credit_plot_vec[
                                                                             ss_truck_vec == 'EV'].sum(), \
                                                                         edgecolor=PEV_color_plot_vec[ss_truck_vec == 'EV'].reset_index(drop=True)[0], alpha=1, \
                                                                         linewidth=0.25, linestyle='-')
                                    else:
                                        Credit_Plot_Subplot2.scatter(x_plot_vec[w], y_plot_vec[w], facecolor='none', \
                                                                     s=PEV_credit_plot_vec[w], \
                                                                     edgecolor=PEV_color_plot_vec[w], alpha=1,\
                                                                     linewidth=0.25, linestyle='-')
                    PEV_Array[y_plot_category][PEV_Array['Stop-Start Tech Category'] == 'EV'] = 1
                    PEV_Array[y_plot_category][PEV_Array['Stop-Start Tech Category'] != 'EV'] = 0
                    if load_factor_plots == 'y' and len(PEV_Array[x_plot_category])>0:
                        PEV_Array[x_plot_category][PEV_Array['Stop-Start Tech Category'] == 'EV'] = 8
                        PEV_Array[x_plot_category][PEV_Array['Stop-Start Tech Category'] != 'EV'] = 4
                        if ((ss_car_vec != 'EV').sum() + (ss_truck_vec != 'EV').sum()) > 0:
                            Credit_Plot_Subplot2.annotate('PHEV', xy=(4,0), \
                                                         xytext=(4.25,0), fontsize=7, \
                                                         horizontalalignment='left')
                        if ((ss_car_vec == 'EV').sum() + (ss_truck_vec == 'EV').sum()) > 0:
                            Credit_Plot_Subplot2.annotate('BEV', xy=(8, 1), \
                                                         xytext=(8.25, 1), fontsize=7, \
                                                         horizontalalignment='left')
                    else:
                        Credit_Plot_Subplot2.scatter(PEV_Array[x_plot_category], \
                                                     PEV_Array[y_plot_category], facecolor='none', \
                                                     s=PEV_Sales_Size, edgecolor='black', linestyle='--',
                                                     linewidth=0.25)
            credits_table = Credit_Plot_Subplot.table(cellText=np.array(plot_table), colLabels=list(plot_table), \
                                                              loc='lower left', bbox=[1, 0, 0.35, 1],
                                                              colWidths=[0.5, 0.85, 0.75, 0.75])
            credits_table.auto_set_font_size(False)
            credits_table.set_fontsize(6)
            for key, cell in credits_table.get_celld().items():
                cell.set_linewidth(0)
            plt.subplots_adjust(left=0.1, right=0.75)

            plot_save_string = save_string + '_' + 'Credit Plot.png'
            Credit_Plot.savefig(plot_save_string,transparent=True, dpi=600)
            plt.close(Credit_Plot)
    return