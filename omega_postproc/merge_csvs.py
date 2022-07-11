import pandas as pd
import glob
import os

maindir = 'C:/Users/KBolon/Documents/OMEGA_runs/2022July/'
runname = '2022_07_10_22_19_33_testcycles_20220710c'
sessionnames = ['_Flatter-5545', '_Flatter-plus40pct-ftpus06'] # , '_NTR+OCC', '_Negative', '_Flat', , '_NTR+OCC', '_Steep', , 'SAFE', '_Steep']
model_year = 2030

drop_columns_pre_run = ['cd_ftp_1:cert_direct_oncycle_kwh_per_mile', 'cd_ftp_2:cert_direct_oncycle_kwh_per_mile',
    'cd_ftp_3:cert_direct_oncycle_kwh_per_mile', 'cd_ftp_4:cert_direct_oncycle_kwh_per_mile',
    'cd_hwfet:cert_direct_oncycle_kwh_per_mile', 'cd_us06_1:cert_direct_oncycle_kwh_per_mile',
    'cd_us06_2:cert_direct_oncycle_kwh_per_mile', 'cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile',
    'cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile', 'cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile',
    'cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile', 'cs_us06_1:cert_direct_oncycle_co2e_grams_per_mile',
    'cs_us06_2:cert_direct_oncycle_co2e_grams_per_mile']

drop_columns_post_run = ['new_vehicle_mfr_generalized_cost_dollars_at_min_footprint',
    'credits_co2e_Mg_per_vehicle_at_min_footprint', 'new_vehicle_mfr_generalized_cost_dollars_at_max_footprint',
    'credits_co2e_Mg_per_vehicle_at_max_footprint']

keep_fields_small_output_version = ['cost_curve_class', 'etw_lbs', 'onroad_direct_oncycle_co2e_grams_per_mile',
    'onroad_direct_oncycle_kwh_per_mile', 'rlhp20', 'rlhp60', 'battery_cost', 'cert_co2e_grams_per_mile',
    'credits_co2e_Mg_per_vehicle', 'curbweight_lbs', 'footprint_ft2', 'new_vehicle_mfr_cost_dollars',
    'new_vehicle_mfr_generalized_cost_dollars', 'onroad_direct_co2e_grams_per_mile', 'onroad_direct_kwh_per_mile',
    'target_co2e_Mg_per_vehicle', 'base_year_vehicle_id', 'run_name', 'session_name', 'rlhp20_level', 'rlhp60_level',
    'footprint_level', 'credits_co2e_Mg_per_vehicle_per_new_vehicle_mfr_generalized_cost_dollars', 'unibody',
    'context_size_class', 'body_style', 'base_year_reg_class', 'drive_system', 'apportioned_initial_registered_count']

keep_fields_very_small_output_version = ['cost_curve_class', 'credits_co2e_Mg_per_vehicle', 'footprint_ft2',
    'new_vehicle_mfr_cost_dollars', 'new_vehicle_mfr_generalized_cost_dollars', 'base_year_vehicle_id', 'run_name',
    'session_name', 'rlhp20_level', 'rlhp60_level', 'footprint_level',
    'credits_co2e_Mg_per_vehicle_per_new_vehicle_mfr_generalized_cost_dollars', 'body_style', 'base_year_reg_class',
    'apportioned_initial_registered_count']

df_all = pd.DataFrame()

for sessionname in sessionnames:
    df_session = pd.DataFrame()
    # loop through cloud files
    cloud_files = os.path.join(maindir, runname, sessionname, 'out', '*cost_cloud.csv')
    cloud_files = glob.glob(cloud_files)
    for cloud_file in cloud_files:
        df_vehcloud = pd.read_csv(cloud_file)
        df_vehcloud = df_vehcloud.drop(columns=drop_columns_pre_run, errors='ignore') # reduce script memory requirements, and output file size, drop unnecessary fields
        df_vehcloud.columns = df_vehcloud.columns.str.replace('veh_....._', '', regex=True)
        df_vehcloud.columns = df_vehcloud.columns.str.replace('veh_...._', '', regex=True)
        df_vehcloud['run_name'] = runname
        df_vehcloud['session_name'] = sessionname
        df_vehcloud['rlhp20_level'] = 'mid'
        df_vehcloud['rlhp60_level'] = 'mid'
        df_vehcloud['footprint_level'] = 'mid'
        df_vehcloud['apportioned_share'] = 0
        techpkg_fields = ['cost_curve_class','structure_material','rlhp20_level','rlhp60_level']

        footprint_min_of_package = df_vehcloud.groupby(techpkg_fields)[
            'footprint_ft2'].transform('min')
        footprint_max_of_package = df_vehcloud.groupby(techpkg_fields)[
            'footprint_ft2'].transform('max')

        rlhp20_min_of_package = df_vehcloud.groupby(techpkg_fields)[
            'rlhp20'].transform('min')
        rlhp20_max_of_package = df_vehcloud.groupby(techpkg_fields)[
            'rlhp20'].transform('max')
        rlhp60_min_of_package = df_vehcloud.groupby(techpkg_fields)[
            'rlhp60'].transform('min')
        rlhp60_max_of_package = df_vehcloud.groupby(techpkg_fields)[
            'rlhp60'].transform('max')

        df_vehcloud['footprint_level'].loc[df_vehcloud['footprint_ft2'] == footprint_min_of_package] = 'min'
        df_vehcloud['footprint_level'].loc[df_vehcloud['footprint_ft2'] == footprint_max_of_package] = 'max'
        df_vehcloud['rlhp20_level'].loc[df_vehcloud['rlhp20'] == rlhp20_min_of_package] = 'min'
        df_vehcloud['rlhp20_level'].loc[df_vehcloud['rlhp20'] == rlhp20_max_of_package] = 'max'
        df_vehcloud['rlhp60_level'].loc[df_vehcloud['rlhp60'] == rlhp60_min_of_package] = 'min'
        df_vehcloud['rlhp60_level'].loc[df_vehcloud['rlhp60'] == rlhp60_max_of_package] = 'max'

        df_packages_for_min_footprints = df_vehcloud[techpkg_fields + ['new_vehicle_mfr_generalized_cost_dollars', 'credits_co2e_Mg_per_vehicle']][df_vehcloud['footprint_ft2'] == footprint_min_of_package]
        df_packages_for_min_footprints = df_packages_for_min_footprints.rename(columns={
            'new_vehicle_mfr_generalized_cost_dollars': 'new_vehicle_mfr_generalized_cost_dollars_at_min_footprint',
            'credits_co2e_Mg_per_vehicle': 'credits_co2e_Mg_per_vehicle_at_min_footprint'})
        df_packages_for_max_footprints = df_vehcloud[techpkg_fields + ['new_vehicle_mfr_generalized_cost_dollars', 'credits_co2e_Mg_per_vehicle']][df_vehcloud['footprint_ft2'] == footprint_max_of_package]
        df_packages_for_max_footprints = df_packages_for_max_footprints.rename(columns={
            'new_vehicle_mfr_generalized_cost_dollars': 'new_vehicle_mfr_generalized_cost_dollars_at_max_footprint',
            'credits_co2e_Mg_per_vehicle': 'credits_co2e_Mg_per_vehicle_at_max_footprint'})
        df_vehcloud = df_vehcloud.merge(df_packages_for_min_footprints, on=techpkg_fields)
        df_vehcloud = df_vehcloud.merge(df_packages_for_max_footprints, on=techpkg_fields)


        df_vehcloud['credits_co2e_Mg_per_vehicle_per_new_vehicle_mfr_generalized_cost_dollars'] = (
                                                                                                          df_vehcloud['credits_co2e_Mg_per_vehicle_at_max_footprint'] - df_vehcloud['credits_co2e_Mg_per_vehicle_at_min_footprint']) / (
                                                                                                          df_vehcloud['new_vehicle_mfr_generalized_cost_dollars_at_max_footprint'] - df_vehcloud['new_vehicle_mfr_generalized_cost_dollars_at_min_footprint'])
        # dftmp.groupby(['vehicle_name', 'structure_material', 'rlhp20', 'rlhp60'])['a'] = dftmp.groupby(['vehicle_name', 'structure_material', 'rlhp20', 'rlhp60']).apply(lambda x: x['footprint_min_of_package_flag'] == True])['new_vehicle_mfr_generalized_cost_dollars'].transform

        df_vehcloud = df_vehcloud.rename(columns={'vehicle_base_year_id': 'base_year_vehicle_id'})

        if df_session.empty:
            df_session = df_vehcloud
        else:
            df_session = pd.concat([df_session, df_vehcloud], ignore_index=True)

    # get vehicle sales, by package
    vehicles_file = os.path.join(maindir, runname, sessionname, 'out', runname + sessionname + '_vehicles.csv')
    dfvehtmp = pd.read_csv(vehicles_file)
    dfvehtmp = dfvehtmp[dfvehtmp['model_year'] == model_year]
    dfvehtmp = dfvehtmp[['name', 'model_year', 'base_year_vehicle_id', 'cost_curve_class', 'structure_material', '_initial_registered_count']]

    if dfvehtmp['cost_curve_class'].str.split(':', expand=True).shape[1] == 2:
        dfvehtmp[['cost_curve_class_1', 'cost_curve_class_2']] = dfvehtmp['cost_curve_class'].str.split(':', expand=True)
        dfvehtmp[['cost_curve_class_1', 'cost_curve_class_1_share']] = dfvehtmp['cost_curve_class_1'].str.replace(')', ''). \
            str.split('\s\(', expand=True).fillna(1)  # first package, default share of 1 unless otherwise specified
        dfvehtmp[['cost_curve_class_2', 'cost_curve_class_2_share']] = dfvehtmp['cost_curve_class_2'].str.replace(')', ''). \
            str.split('\s\(', expand=True).fillna(0)  # second package, default share of 0 unless otherwise specified
    else:
        emptydf = pd.DataFrame(columns=['empty1', 'empty2', 'empty3'], index=dfvehtmp.index)
        dfvehtmp[['cost_curve_class_1', 'cost_curve_class_1_share', 'cost_curve_class_2', 'cost_curve_class_2_share']] = pd.concat([dfvehtmp['cost_curve_class'], emptydf.empty1.fillna(1), emptydf.empty2, emptydf.empty3], axis=1)

    if dfvehtmp['structure_material'].str.split(':', expand=True).shape[1] == 2:
        dfvehtmp[['structure_material_1', 'structure_material_2']] = dfvehtmp['structure_material'].str.split(':', expand=True)
        dfvehtmp[['structure_material_1', 'structure_material_1_share']] = dfvehtmp['structure_material_1'].\
            str.replace(')', '').str.split('\s\(', expand=True).fillna(1)  # first package, default share of 1 unless otherwise specified
        dfvehtmp[['structure_material_2', 'structure_material_2_share']] = dfvehtmp['structure_material_2'].\
            str.replace(')','').str.split('\s\(', expand=True).fillna(0)  # second package, default share of 0 unless otherwise specified
    else:
        emptydf = pd.DataFrame(columns=['empty1','empty2','empty3'], index=dfvehtmp.index)
        dfvehtmp[['structure_material_1', 'structure_material_1_share', 'structure_material_2', 'structure_material_2_share']] = pd.concat([dfvehtmp['structure_material'], emptydf.empty1.fillna(1), emptydf.empty2, emptydf.empty3], axis=1)

    dfvehtmp = dfvehtmp.drop(columns=['name', 'cost_curve_class', 'structure_material'], errors='ignore')

    # merge in sub share fields one at a time
    df_session = df_session.merge(dfvehtmp[['model_year', 'base_year_vehicle_id', '_initial_registered_count']].
                                  drop_duplicates(['model_year', 'base_year_vehicle_id']),
                                  how='left', on=['model_year', 'base_year_vehicle_id'])

    # each combination of cost_curve_class_1 and 2, and structure_material_1 and 2
    df_session = df_session.merge(dfvehtmp[['model_year', 'base_year_vehicle_id', 'cost_curve_class_1', 'cost_curve_class_1_share', 'structure_material_1', 'structure_material_1_share']].
                                  drop_duplicates(['model_year', 'base_year_vehicle_id', 'cost_curve_class_1', 'cost_curve_class_1_share', 'structure_material_1', 'structure_material_1_share']),
                                  how='left', left_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class', 'structure_material'],
                                  right_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class_1', 'structure_material_1'])
    df_session['apportioned_share'] = df_session['apportioned_share'] + df_session['cost_curve_class_1_share'].fillna(0).astype(float) * df_session['structure_material_1_share'].fillna(0).astype(float)
    df_session = df_session.drop(columns=['cost_curve_class_1', 'cost_curve_class_1_share', 'structure_material_1', 'structure_material_1_share'], errors='ignore')

    df_session = df_session.merge(dfvehtmp[['model_year', 'base_year_vehicle_id', 'cost_curve_class_2', 'cost_curve_class_2_share', 'structure_material_2', 'structure_material_2_share']].
                                  drop_duplicates(['model_year', 'base_year_vehicle_id', 'cost_curve_class_2', 'cost_curve_class_2_share', 'structure_material_2', 'structure_material_2_share']),
                                  how='left', left_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class', 'structure_material'],
                                  right_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class_2', 'structure_material_2'])
    df_session['apportioned_share'] = df_session['apportioned_share'] + df_session['cost_curve_class_2_share'].fillna(0).astype(float) * df_session['structure_material_2_share'].fillna(0).astype(float)
    df_session = df_session.drop(columns=['cost_curve_class_2', 'cost_curve_class_2_share', 'structure_material_2', 'structure_material_2_share'], errors='ignore')

    df_session = df_session.merge(dfvehtmp[['model_year', 'base_year_vehicle_id', 'cost_curve_class_1', 'cost_curve_class_1_share', 'structure_material_2', 'structure_material_2_share']].
                                  drop_duplicates(['model_year', 'base_year_vehicle_id', 'cost_curve_class_1', 'cost_curve_class_1_share', 'structure_material_2', 'structure_material_2_share']),
                                  how='left', left_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class', 'structure_material'],
                                  right_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class_1', 'structure_material_2'])
    df_session['apportioned_share'] = df_session['apportioned_share'] + df_session['cost_curve_class_1_share'].fillna(0).astype(float) * df_session['structure_material_2_share'].fillna(0).astype(float)
    df_session = df_session.drop(columns=['cost_curve_class_1', 'cost_curve_class_1_share', 'structure_material_2', 'structure_material_2_share'], errors='ignore')

    df_session = df_session.merge(dfvehtmp[['model_year', 'base_year_vehicle_id', 'cost_curve_class_2', 'cost_curve_class_2_share', 'structure_material_1', 'structure_material_1_share']].
                                  drop_duplicates(['model_year', 'base_year_vehicle_id', 'cost_curve_class_2', 'cost_curve_class_2_share', 'structure_material_1', 'structure_material_1_share']),
                                  how='left', left_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class', 'structure_material'],
                                  right_on=['model_year', 'base_year_vehicle_id', 'cost_curve_class_2', 'structure_material_1'])
    df_session['apportioned_share'] = df_session['apportioned_share'] + df_session['cost_curve_class_2_share'].fillna(0).astype(float) * df_session['structure_material_1_share'].fillna(0).astype(float)
    df_session = df_session.drop(columns=['cost_curve_class_2', 'cost_curve_class_2_share', 'structure_material_1', 'structure_material_1_share'], errors='ignore')

    df_session['apportioned_initial_registered_count'] = df_session['apportioned_share'] * df_session['_initial_registered_count']

    if df_all.empty:
        df_all = df_session
    else:
        df_all = pd.concat([df_all, df_session], ignore_index=True)

df_all['vehicle_name'] = df_all['vehicle_name'].str.replace('BEV of ', '').str.replace('\'', '').str.replace('ICE of ', '').str.replace('{', '').str.replace('}', '') # prepare vehicle_name field for delimited split
df_all[['context_size_class', 'body_style', 'base_year_electrification_class', 'unibody', 'base_year_fuel', 'base_year_fuel_share', 'base_year_reg_class', 'drive_system']] = df_all['vehicle_name'].str.split(':', expand=True)
df_all = df_all.drop(columns=['vehicle_name'])
df_all = df_all.drop(columns=drop_columns_post_run) # reduce output file size, drop intermediate calculation fields

#df_all.to_csv(os.path.join(maindir, runname, 'combined_cost_cloud.csv'))
df_all[keep_fields_small_output_version].to_csv(os.path.join(maindir, runname, 'combined_cost_cloud_small.csv'))
#df_all[keep_fields_very_small_output_version].to_csv(os.path.join(maindir, runname, 'combined_cost_cloud_very_small.csv'))