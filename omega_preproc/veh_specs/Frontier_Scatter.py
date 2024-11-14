def cloud_plot():
    # !
    # Kevin Bolon 2017$
    # %matplotlib inline
    import pandas as pd
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1 import Grid

    def pareto_frontier(Xs, Ys, maxX=True, maxY=True):
        '''
        Method to take two equally-sized lists and return just the elements which lie
        on the Pareto frontier, sorted into order.
        Default behaviour is to find the maximum for both X and Y, but the option is
        available to specify maxX = False or maxY = False to find the minimum for either
        or both of the parameters.
        '''
        # Sort the list in either ascending or descending order of X
        myList = sorted([[Xs[i], Ys[i]] for i in range(len(Xs))], reverse=maxX)
        # Start the Pareto frontier with the first value in the sorted list
        p_front = [myList[0]]
        # Loop through the sorted list
        for pair in myList[1:]:
            if maxY:
                if pair[1] >= p_front[-1][1]:  # Look for higher values of Y…
                    p_front.append(pair)  # … and add them to the Pareto frontier
            else:
                if pair[1] <= p_front[-1][1]:  # Look for lower values of Y…
                    p_front.append(pair)  # … and add them to the Pareto frontier
        # Turn resulting pairs back into a list of Xs and Ys
        p_frontX = [pair[0] for pair in p_front]
        p_frontY = [pair[1] for pair in p_front]
        return p_frontX, p_frontY

    def plotcloud(p_front1, p_front2, p_front3, p_front4, x_vec, y_vec):
        fig = plt.figure(1)
        gridsize = (1, 1)
        grid = Grid(fig, rect=111, nrows_ncols=gridsize,
                    axes_pad=0.0, label_mode='L')
        fontscaler = 1
        ax = grid[0]
        ax.set_xlim(0, 1)
        ax.grid(True, which='major', color='grey', linewidth=0.1)
        ax.plot(p_front1[0], p_front1[1], color='r', linestyle='-', linewidth=0.5)
        ax.plot(p_front2[0], p_front2[1], color='b', linestyle='-', linewidth=0.5)
        ax.plot(p_front3[0], p_front3[1], color='k', linestyle='-', linewidth=0.5)
        ax.plot(p_front4[0], p_front4[1], color='g', linestyle='-', linewidth=0.5)
        ax.plot(x_vec, y_vec, marker='*',
                color='b', linestyle='', ms=10 * fontscaler, mew=1 * fontscaler,
                mec='k')
        # fig.savefig('C:/Users/KBolon/Desktop/cloudplot.png', dpi=600, transparent=True)  # rasterized image
        # fig.savefig()
        # fig.clf()

    # rootdir = 'C:/Users/KBolon/Desktop/'  # location of run controller file
    # df = pd.read_csv(rootdir + 'cloudpoints.txt',sep='\t',header = 0)
    def cloud_plot(x_vec, y_vec, OEM):
        if len(x_vec) > 0:
            p_front1 = pareto_frontier(x_vec, y_vec, True, False)
            p_front2 = pareto_frontier(x_vec, y_vec, False, False)
            p_front3 = pareto_frontier(x_vec, y_vec, False, True)
            p_front4 = pareto_frontier(x_vec, y_vec, True, True)

            # p_front = (p_front1[0]+p_front2[0]+p_front3[0]+p_front4[0][::-1],p_front1[1]+p_front2[1]+p_front3[1]+p_front4[1][::-1])
            p_front = (p_front1[0] + p_front2[0][::-1] + p_front3[0] + p_front4[0][::-1],
                       p_front1[1] + p_front2[1][::-1] + p_front3[1] + p_front4[1][::-1])

            # p_front4 = ([p_front3[0][-1], p_front1[0][0]], [p_front3[1][-1], p_front1[1][0]])
            # p_front_int = p_front1+p_front2+p_front3+p_front4
            #
            # p_front_x = [i for sub in p_front_int[::2] for i in sub]
            # p_front_y = [i for sub in p_front_int[1::2] for i in sub]
            #
            # return(p_front_x,p_front_y)

            return (p_front)
        else:
            return ([0], [0])
    return
def Frontier_Scatter(input_path, output_path, query_filenames_list, footprint_plots, \
                            load_factor_plots, credit_integration, target_credit, credit_legend_category, \
                         credit_filenames_list, sales_weighted, remove_scatter, FTP_time, HWFET_time, \
                     plot_color_filename, bool_max_peff):
    import matplotlib
    matplotlib.use("TKAgg")
    import matplotlib.pyplot as plt
    # from matplotlib import pyplot as plt
    import pylab
    import pandas as pd
    import numpy as np
    import math
    import datetime
    from collections import OrderedDict
    import cloud_plot
    from Unit_Conversion import hp2w, h2s
    # Plotting Parameters
    if ',' in query_filenames_list:
        filenames = pd.Series(list(query_filenames_list.split(','))).str.strip()
    else:
        filenames = pd.Series([query_filenames_list])

    TCG_vec = pd.Series(['TurbM_AdvT_No S-S', 'TurbM_AdvT_S-S', 'TurbM_ST_No S-S', 'TurbM_ST_S-S', \
                         'ATK_AdvT_No S-S', 'ATK_AdvT_S-S', 'ATK_ST_No S-S', 'ATK_ST_S-S', \
                         'Turb_AdvT_No S-S', 'Turb_AdvT_S-S', 'Turb_ST_No S-S', 'Turb_ST_S-S', \
                         'Deac_AdvT_No S-S', 'Deac_AdvT_S-S', 'Deac_ST_No S-S', 'Deac_ST_S-S', \
                         'NatAsp_AdvT_No S-S', 'NatAsp_AdvT_S-S', 'NatAsp_ST_No S-S', 'NatAsp_ST_S-S', \
                         'TurbM_AdvT_MHEV', 'TurbM_AdvT_HEV', 'TurbM_ST_MHEV', 'TurbM_ST_HEV', \
                         'ATK_AdvT_MHEV', 'ATK_AdvT_HEV', 'ATK_ST_MHEV', 'ATK_ST_HEV', \
                         'Turb_AdvT_MHEV', 'Turb_AdvT_HEV', 'Turb_ST_MHEV', 'Turb_ST_HEV', \
                         'Deac_AdvT_MHEV', 'Deac_AdvT_HEV', 'Deac_ST_MHEV', 'Deac_ST_HEV', \
                         'NatAsp_AdvT_MHEV', 'NatAsp_AdvT_HEV', 'NatAsp_ST_MHEV', 'NatAsp_ST_HEV'])

    Plot_vec = pd.Series(['Gas_No S-S', 'Gas_S-S', 'Gas_Conventional', 'Gas_Hybrid', \
                          'Diesel_No S-S', 'Diesel_S-S', 'Diesel_Conventional', 'Diesel_Hybrid', 'All non-PEV'])

    title_part1_vec = ['Combined Powertrain Efficiency', 'Combined Powertrain Efficiency',
                       'Tailpipe CO2 Emissions (g/mi)']
    title_part2_vec = ['Combined Load Factor (%)', 'Combined Tractive Road Energy Intensity (MJ/km)', \
                       'Combined Tractive Road Energy Intensity (MJ/km)']
    title_part1_vec = title_part1_vec[0:1]
    title_part2_vec = title_part2_vec[0:1]
    axis_tuple = ([0, 12, 5, 40], [0, 1.4, 5, 40], [0, 1.4, 100, 700])

    color_vec = ['darkblue', 'lightblue', 'darkred', 'yellow', 'darkviolet', \
                 'pink', 'darkgreen', 'lightgreen', 'black', 'gray', \
                 'darkblue', 'lightblue', 'darkred', 'yellow', 'darkviolet', \
                 'pink', 'darkgreen', 'lightgreen', 'black', 'gray']
    shape_vec = ['o', '*', '^', 'v']
    line_vec = ['-', ':', '-', '--']
    plot_color_array = pd.read_csv(input_path+'\\'+plot_color_filename)
    color_array_OEM = plot_color_array['OEM']
    OEM_color_vec = plot_color_array['Color']
    # OEM_color_vec_all = pd.Series(
    #     ['sienna', 'blue', 'green', 'red', 'cyan', 'magenta', 'goldenrod', 'cornflowerblue', 'palevioletred', \
    #      'orangered', 'grey', 'lime', 'darkviolet', 'mediumseagreen', 'darkred', 'orange', 'palevioletred', \
    #      'mediumorchid', 'midnightblue', 'tomato', 'plum', 'aquamarine', 'azure'])
    for filename in filenames:
        model_year = int(filename[0:4])
        Powertrain_Array_allentries = pd.read_csv(input_path+'\\'+filename).merge(plot_color_array, how='left', \
                    left_on = 'OEM_Master Index', right_on = 'OEM').reset_index(drop=True)
        # Filter Data Based on Controller Parameters

        Powertrain_Array_allentries['Stop-Start Tech Category'] = pd.Series(np.zeros(len(Powertrain_Array_allentries)))\
            .replace(0,'No S-S')
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Hybrid (y/n)_Master Index'] == 'Y') & \
                                                                (Powertrain_Array_allentries['Off-Board Charge Capability (y/n)_Master Index'] == 'Y')] = 'REEV'
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Hybrid (y/n)_Master Index'] == 'Y') & \
                                                                (Powertrain_Array_allentries['Off-Board Charge Capability (y/n)_Master Index'] == 'N')] = 'HEV'
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Hybrid (y/n)_Master Index'] == 'N') & \
                                                                (Powertrain_Array_allentries['Off-Board Charge Capability (y/n)_Master Index'] == 'Y')] = 'EV'
        Powertrain_Array_allentries['Stop-Start Tech Category'][(Powertrain_Array_allentries['Stop-Start Tech Category'] == 'No S-S') & \
                                                                (Powertrain_Array_allentries['Stop-Start System (y/n)_Master Index'] != 'N')] = 'S-S'

        Powertrain_Array_allentries['Advanced Transmission Category'] = pd.Series(np.zeros(len(Powertrain_Array_allentries)))\
            .replace(0,'ST')
        Powertrain_Array_allentries['Advanced Transmission Category'][(Powertrain_Array_allentries['Number of Transmission Gears_Master Index'] >= 8)] = 'AdvT'
        Powertrain_Array_allentries['Advanced Transmission Category'][(Powertrain_Array_allentries['Number of Transmission Gears_Master Index'] == 1)] = 'AdvT'

        Powertrain_Array_allentries['Engine Technology Category'] = pd.Series(np.zeros(len(Powertrain_Array_allentries)))\
            .replace(0,'NatAsp')
        Powertrain_Array_allentries['Engine Technology Category'][(Powertrain_Array_allentries['Cylinder Deactivation (y/n)_Master Index'] == 'Y')] = 'Deac'
        Powertrain_Array_allentries['Engine Technology Category'][~pd.isnull(Powertrain_Array_allentries['Air Aspiration_Master Index'])] = 'Turb'
        Powertrain_Array_allentries['Tech Combination Group'] = pd.Series(Powertrain_Array_allentries['Engine Technology Category'].astype(str)+'_'+ \
            Powertrain_Array_allentries['Advanced Transmission Category'].astype(str) + '_' + \
            Powertrain_Array_allentries['Stop-Start Tech Category'].astype(str))
        if bool_max_peff == 'n':
            Powertrain_Array_allentries['Combined Powertrain Efficiency'] = pd.Series(
                Powertrain_Array_allentries['Powertrain Efficiency' + '_Subconfig Data'])
            Powertrain_Array_allentries['Combined Powertrain Efficiency'][pd.isnull(Powertrain_Array_allentries['Combined Powertrain Efficiency'])] = \
            Powertrain_Array_allentries['Powertrain Efficiency' + '_Subconfig Data' + '_Max']
            Powertrain_Array_allentries['Combined Powertrain Efficiency'][pd.isnull(Powertrain_Array_allentries['Combined Powertrain Efficiency'])] = \
            Powertrain_Array_allentries['Powertrain Efficiency' + '_Test Car']
            Powertrain_Array_allentries['Combined Powertrain Efficiency'][pd.isnull(Powertrain_Array_allentries['Combined Powertrain Efficiency'])] = \
            Powertrain_Array_allentries['Powertrain Efficiency' + '_Test Car' + '_Max']

            Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'] = pd.Series(
                Powertrain_Array_allentries['FTP Tractive Energy' + '_Subconfig Data'])
            Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'][
                pd.isnull(Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'])] = \
                Powertrain_Array_allentries['FTP Tractive Energy' + '_Subconfig Data' + '_Max']
            Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'][
                pd.isnull(Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'])] = \
                Powertrain_Array_allentries['FTP Tractive Energy' + '_Test Car']
            Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'][
                pd.isnull(Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'])] = \
                Powertrain_Array_allentries['FTP Tractive Energy' + '_Test Car' + '_Max']

            Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'] = pd.Series(
                Powertrain_Array_allentries['HWFET Tractive Energy' + '_Subconfig Data'])
            Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'][
                pd.isnull(Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'])] = \
                Powertrain_Array_allentries['HWFET Tractive Energy' + '_Subconfig Data' + '_Max']
            Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'][
                pd.isnull(Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'])] = \
                Powertrain_Array_allentries['HWFET Tractive Energy' + '_Test Car']
            Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'][
                pd.isnull(Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'])] = \
                Powertrain_Array_allentries['HWFET Tractive Energy' + '_Test Car' + '_Max']

            Powertrain_Array_allentries['Rated Horsepower (hp)'] = pd.Series(
                Powertrain_Array_allentries['Rated Horsepower' + '_Master Index'])
            Powertrain_Array_allentries['Rated Horsepower (hp)'][
                pd.isnull(Powertrain_Array_allentries['Rated Horsepower (hp)'])] = \
                Powertrain_Array_allentries['Rated Horsepower' + '_Master Index' + '_Max']
            Powertrain_Array_allentries['Rated Horsepower (hp)'][
                pd.isnull(Powertrain_Array_allentries['Rated Horsepower (hp)'])] = \
                Powertrain_Array_allentries['Rated Horsepower' + '_Test Car']
            Powertrain_Array_allentries['Rated Horsepower (hp)'][
                pd.isnull(Powertrain_Array_allentries['Rated Horsepower (hp)'])] = \
                Powertrain_Array_allentries['Rated Horsepower' + '_Test Car' + '_Max']
        else:
            Powertrain_Array_allentries['Combined Powertrain Efficiency'] = Powertrain_Array_allentries[[\
                'Powertrain Efficiency' + '_Subconfig Data', 'Powertrain Efficiency' + '_Subconfig Data' + '_Max', \
                'Powertrain Efficiency' + '_Test Car', 'Powertrain Efficiency' + '_Test Car' + '_Max']].max(axis=1)
            target_column_suffixes = Powertrain_Array_allentries[[\
                'Powertrain Efficiency' + '_Subconfig Data', 'Powertrain Efficiency' + '_Subconfig Data' + '_Max', \
                'Powertrain Efficiency' + '_Test Car', 'Powertrain Efficiency' + '_Test Car' + '_Max']].idxmax(axis=1)\
            .str.replace('Powertrain Efficiency', '').str.strip()
            Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'] = pd.Series(np.zeros(len(target_column_suffixes)))
            Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'] = pd.Series(np.zeros(len(target_column_suffixes)))
            Powertrain_Array_allentries['Rated Horsepower (hp)'] = pd.Series(np.zeros(len(target_column_suffixes)))
            for suffix_count in range (0,len(target_column_suffixes)):
                suffix = target_column_suffixes[suffix_count]
                #print(suffix_count)
                if pd.isnull(suffix) == bool(False):
                    Powertrain_Array_allentries['FTP Tractive Energy (kWhr)'][suffix_count] = \
                        Powertrain_Array_allentries['FTP Tractive Energy' + suffix][suffix_count]
                    Powertrain_Array_allentries['HWFET Tractive Energy (kWhr)'][suffix_count] = \
                        Powertrain_Array_allentries['HWFET Tractive Energy' + suffix][suffix_count]
                    if "Test Car" in suffix:
                        Powertrain_Array_allentries['Rated Horsepower (hp)'][suffix_count] = \
                            Powertrain_Array_allentries['Rated Horsepower' + suffix][suffix_count]
                    else:
                        if "Max" in suffix:
                            Powertrain_Array_allentries['Rated Horsepower (hp)'][suffix_count] = \
                                Powertrain_Array_allentries['Rated Horsepower' + '_Master Index' + '_Max'][suffix_count]
                        else:
                            Powertrain_Array_allentries['Rated Horsepower (hp)'][suffix_count] = \
                                Powertrain_Array_allentries['Rated Horsepower' + '_Master Index'][suffix_count]
        Powertrain_Array_allentries['Rated Horsepower (hp)'] = Powertrain_Array_allentries[
            'Rated Horsepower (hp)'].replace([0, str(0)], np.nan)

        Powertrain_Array_nonBEV = Powertrain_Array_allentries[(Powertrain_Array_allentries['Stop-Start Tech Category'] != 'EV') & \
                                (Powertrain_Array_allentries['Stop-Start Tech Category'] != 'REEV')]\
                                .reset_index(drop=True)
        OEM_Unique_Vec = pd.Series(Powertrain_Array_nonBEV['OEM_Master Index'].unique())\
            .sort_values().reset_index(drop=True)
        # OEM_color_vec = OEM_color_vec_all[0:len(OEM_Unique_Vec)].reset_index(drop=True)
        # Separate out OEMs
        total_sales = 200000
        for i in range(0, len(Plot_vec)):  # For Each Fuel/Tech Category
            Tech_Type = str(Plot_vec[i])
            for j in range(0, len(title_part1_vec)):  # For Each Desired Plot/Bigplot
                if title_part2_vec[j] == 'Combined Load Factor (%)':
                    Powertrain_Array_nonBEV = Powertrain_Array_nonBEV[
                        (~pd.isnull(Powertrain_Array_nonBEV['FTP Tractive Energy (kWhr)'])) & \
                        (~pd.isnull(Powertrain_Array_nonBEV['HWFET Tractive Energy (kWhr)'])) & \
                        (~pd.isnull(Powertrain_Array_nonBEV['Rated Horsepower (hp)']))].reset_index(drop=True)
                    Powertrain_Array_nonBEV['Combined Load Factor (%)'] = 100*pd.Series(\
                        (0.55*Powertrain_Array_nonBEV['FTP Tractive Energy (kWhr)']\
                         +0.45*Powertrain_Array_nonBEV['HWFET Tractive Energy (kWhr)']) / \
                        ((0.55*Powertrain_Array_nonBEV['Rated Horsepower (hp)']*FTP_time*hp2w/(h2s*1000)) + \
                        (0.45*Powertrain_Array_nonBEV['Rated Horsepower (hp)']*HWFET_time*hp2w/(h2s*1000))))
                Powertrain_Array = Powertrain_Array_nonBEV[(~pd.isnull(Powertrain_Array_nonBEV[title_part1_vec[j]])) & \
                        (~pd.isnull(Powertrain_Array_nonBEV[title_part2_vec[j]]))].reset_index(drop=True)
                if j == 0:
                    load_factor_star = np.average(Powertrain_Array[title_part2_vec[j]],
                                                  weights=Powertrain_Array['FOOTPRINT_SUBCONFIG_SALES'])
                    peff_star = np.average(Powertrain_Array[title_part1_vec[j]],
                                           weights=Powertrain_Array['FOOTPRINT_SUBCONFIG_SALES'])
                # Create Bigmap
                Bigmap = plt.figure(Plot_vec[i] + '_' + title_part1_vec[j] + ' vs. ' + title_part2_vec[j],
                                    (18, 12))  # (26,7.5)
                plt.suptitle(Plot_vec[i] + '_' + title_part1_vec[j] + ' vs. ' + title_part2_vec[j])
                Bigmap1_axes1 = plt.subplot(121)
                plt.grid(True)
                Bigmap1_axes1.set_title(str(model_year))
                Bigmap1_axes1.set_xlabel(title_part2_vec[j].replace('Combined', '').strip())
                Bigmap1_axes1.set_ylabel(title_part1_vec[j].replace('Combined', '').strip())
                Bigmap1_axes1.axis(axis_tuple[j])
                Bigmap1_axes2 = plt.subplot(122)
                plt.grid(True)
                Bigmap1_axes2.set_title(str(model_year))
                Bigmap1_axes2.set_xlabel(title_part2_vec[j].replace('Combined', '').strip())
                Bigmap1_axes2.axis(axis_tuple[j])
                Bigmap1_axes2.legend(loc=2, prop={'size': 6}, numpoints=1,
                                    markerscale=20)
                Bigmap1_axes1.legend(loc=2, prop={'size': 6}, numpoints=1,
                                    markerscale=20)
                Bigmap2 = plt.figure(Plot_vec[i] + '_' + title_part1_vec[j] + ' vs. ' + title_part2_vec[j],
                                     (9, 12))  # (26,7.5)
                plt.suptitle(Plot_vec[i] + '_' + title_part1_vec[j] + ' vs. ' + title_part2_vec[j])
                Bigmap2_axes1 = plt.subplot(111)
                plt.grid(True)
                Bigmap2_axes1.set_title(str(model_year))
                Bigmap2_axes1.set_xlabel(title_part2_vec[j].replace('Combined', '').strip())
                Bigmap2_axes1.set_ylabel(title_part1_vec[j].replace('Combined', '').strip())
                Bigmap2_axes1.axis(axis_tuple[j])

                for k in range(0, len(OEM_Unique_Vec)):
                    OEM_Array_int = Powertrain_Array[Powertrain_Array['OEM_Master Index'] == OEM_Unique_Vec[k]].reset_index(
                        drop=True)
                    Tech_vec = pd.Series(OEM_Array_int['Stop-Start Tech Category'].unique()).sort_values().reset_index(drop=True)
                    OEM = str(OEM_Unique_Vec[k])
                    coloring = OEM_color_vec[OEM_color_vec[color_array_OEM == OEM].index[0]]
                    length_check = 0
                    title_part_1 = title_part1_vec[j].replace('(', '').replace(')', '').replace('/', ' per ')
                    title_part_2 = title_part2_vec[j].replace('(', '').replace(')', '').replace('%','').replace('/', ' per ')
                    bigmap_subtitle_1 = title_part_1 + ' vs'
                    bigmap_subtitle_2 = title_part_2 + ' ' + str(Plot_vec[i])
                    plot_subtitle_1 = str(OEM)
                    plot_subtitle_2 = bigmap_subtitle_1 + ' ' + bigmap_subtitle_2

                    map = plt.figure(plot_subtitle_1 + plot_subtitle_2, (14, 12))
                    map.suptitle(plot_subtitle_1 + '\n' + plot_subtitle_2)
                    ax = plt.subplot(int(111))
                    OEM_Array = OEM_Array_int[OEM_Array_int['FOOTPRINT_SUBCONFIG_SALES'] > 0].reset_index(drop=True)
                    sales_vector = OEM_Array['FOOTPRINT_SUBCONFIG_SALES']

                    if Tech_Type == 'Gas_No S-S':
                        Plot_Array = OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'G') & \
                                               (OEM_Array['Stop-Start Tech Category'] == 'No S-S')] \
                            .reset_index(drop=True)
                    elif Tech_Type == 'Gas_S-S':
                        Plot_Array = OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'G') & \
                                               (OEM_Array['Stop-Start Tech Category'] == 'S-S')] \
                            .reset_index(drop=True)
                    elif Tech_Type == 'Gas_Conventional':
                        Plot_Array = pd.concat([OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'G') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'No S-S')], \
                                                OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'G') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'S-S')]]) \
                            .reset_index(drop=True)
                        Plot_Array.columns = list(OEM_Array.columns.values)
                        if j == 0:
                            try:
                                Frontier_Array
                            except NameError:
                                Frontier_Array = pd.concat([Powertrain_Array[(Powertrain_Array['Fuel Type Category_Master Index'] == 'G') & \
                                                                  (Powertrain_Array['Stop-Start Tech Category'] == 'No S-S')], \
                                                            Powertrain_Array[(Powertrain_Array['Fuel Type Category_Master Index'] == 'G') & \
                                                                  (Powertrain_Array['Stop-Start Tech Category'] == 'S-S')]]) \
                                    .reset_index(drop=True)
                                Frontier_Array.columns = list(Powertrain_Array.columns.values)
                    elif Tech_Type == 'Gas_Hybrid':
                        Plot_Array = pd.concat([OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'G') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'MHEV')], \
                                                OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'G') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'HEV')]]) \
                            .reset_index(drop=True)
                        Plot_Array.columns = list(OEM_Array.columns.values)
                        Plot_Array.columns = list(OEM_Array.columns.values)
                    elif Tech_Type == 'Diesel_No S-S':
                        Plot_Array = OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'D') & \
                                               (OEM_Array['Stop-Start Tech Category'] == 'No S-S')] \
                            .reset_index(drop=True)
                    elif Tech_Type == 'Diesel_S-S':
                        Plot_Array = OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'D') & \
                                               (OEM_Array['Stop-Start Tech Category'] == 'S-S')] \
                            .reset_index(drop=True)
                    elif Tech_Type == 'Diesel_Conventional':
                        Plot_Array = pd.concat([OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'D') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'No S-S')], \
                                                OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'D') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'S-S')]]) \
                            .reset_index(drop=True)
                        Plot_Array.columns = list(OEM_Array.columns.values)
                    elif Tech_Type == 'Diesel_Hybrid':
                        Plot_Array = pd.concat([OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'D') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'MHEV')], \
                                                OEM_Array[(OEM_Array['Fuel Type Category_Master Index'] == 'D') & \
                                                          (OEM_Array['Stop-Start Tech Category'] == 'HEV')]]) \
                            .reset_index(drop=True)
                    elif Tech_Type == 'All non-PEV':
                        Plot_Array = OEM_Array

                    if sales_weighted == 'y':
                        size_int = (sales_vector / total_sales) ** 0.5
                        size_normalize = size_int.max()
                        size = (size_int / size_normalize) * 50  # 50
                    else:
                        size = 50  # 50

                    linewidth_curve = 3
                    line_width = 3

                    x_vector = Plot_Array[str(title_part2_vec[j])].astype(float)
                    y_vector = Plot_Array[str(title_part1_vec[j])].astype(float)
                    (p_front) = cloud_plot.cloud_plot(x_vector, y_vector, OEM)
                    ax.plot(p_front[0], p_front[1], color=coloring, linestyle=line_vec[i % 4], linewidth=1, \
                            label=OEM)
                    Bigmap1_axes1.plot(p_front[0], p_front[1], color=coloring, linestyle=line_vec[i % 4], \
                                        linewidth=linewidth_curve, label=OEM)
                    Bigmap1_axes1.legend(bbox_to_anchor=(1, 0.75), loc='right', title='Legend', shadow=True)
                    length_check += len(Plot_Array)
                    if Plot_vec[i] == 'Gas_Conventional':
                        p_front_0 = p_front[0]
                        p_front_1 = p_front[1]
                    ax.grid(True)
                    ax.set_xlabel(title_part2_vec[j])
                    ax.title.set_text(str(model_year))
                    ax.axis(axis_tuple[j])
                    if remove_scatter == 'n':
                        for m in range(0, len(TCG_vec)):
                            TCG = TCG_vec[m]
                            i_color = color_vec[math.floor(m / 2)]
                            i_fill = i_color
                            if m < (len(TCG_vec) / 2):
                                shape = shape_vec[(m % 2)]
                            else:
                                shape = shape_vec[2 + (m % 2)]
                            if len(x_vector[Plot_Array['Tech Combination Group'] == TCG]) > 0:
                                ax.scatter(x_vector[Plot_Array['Tech Combination Group'] == TCG], \
                                           y_vector[Plot_Array['Tech Combination Group'] == TCG], \
                                           edgecolor=i_color, facecolors=i_fill, marker=shape, s=size,
                                           linewidth=line_width, label=TCG)
                                ax.legend(bbox_to_anchor=(1, 0.75), loc='right', title='Legend', shadow=True)
                                Bigmap1_axes2.scatter(x_vector[Plot_Array['Tech Combination Group'] == TCG], \
                                           y_vector[Plot_Array['Tech Combination Group'] == TCG], \
                                           edgecolor=i_color, facecolors=i_fill, marker=shape, s=size,
                                           linewidth=line_width, label=TCG)

                                handles, labels = Bigmap1_axes2.get_legend_handles_labels()
                                by_label = OrderedDict(zip(labels, handles))
                                Bigmap1_axes2.legend(by_label.values(), by_label.keys(), \
                                               bbox_to_anchor=(1, 0.75), loc='right', title='Legend', shadow=True)
                        Bigmap2_axes1.scatter(x_vector, y_vector, \
                                              edgecolor=Plot_Array['Color'], facecolors=Plot_Array['Color'],
                                              marker='o', s=size,
                                              linewidth=line_width)

                    if length_check != 0:
                        map.savefig(
                            output_path + '\\' + str(model_year) + ' ' + plot_subtitle_1 + ' ' + str(Plot_vec[i]) + ' ' + str(j+1) + '.png',
                            transparent=True, dpi=600) #plot_subtutle_2
                    plt.close(map)
                Bigmap.savefig(
                    output_path + '\\' + str(model_year) + ' ' + str('All OEM') + ' ' +  \
                    str(Plot_vec[i]) + ' ' + str(j+1) + '.png', transparent=True, dpi=600) #bigmap_subtitle_2
                #plt.close(Bigmap)

        (p_front) = cloud_plot.cloud_plot(Frontier_Array[title_part2_vec[0]], \
                                          Frontier_Array[title_part1_vec[0]], OEM)
        print(load_factor_star)
        print(peff_star)
        Bigmap2_axes1.plot(p_front[0], p_front[1], color='k', linestyle=line_vec[i % 4], \
                           linewidth=linewidth_curve, label='Frontier')
        Bigmap2_axes1.scatter(load_factor_star, peff_star, color = 'k', marker = '*', s = 250)
        Bigmap2.savefig(
            output_path + '\\' + str(model_year)  + ' ' +  \
            '.png', transparent=True, dpi=600) #bigmap_subtitle_2
        #plt.close(Bigmap2)
    return
