import pandas as pd
import glob
import os

# location of components files
maindir = 'I:/Project/Midterm Review/Trends/Trends Data/A2MAC1/AutoReverse Raw Data/CSV_Components'
outputdir = 'C:/Users/KBolon/Documents'

# location of product description file
productdescriptionsfile = 'I:/Project/Midterm Review/Trends/Original Trends Team Data Gathering and Analysis/Lineage/Lineage Database Tables/A2macID.csv'

components_files = os.path.join(maindir, '*Components.csv')
components_files = glob.glob(components_files)
drop_columns_pre_run = []
drop_columns_post_run = []
keep_fields = []
productdescriptionsfields = ['vehicle_yrmkmdl', 'Weight', 'BodyStyle', 'Doorsnumber', 'SeatingCapacity', 'Fueltype', 'EngineCapacity(cm3)', 'NumberofCylinders', 'Boost', 'HorsePower', 'Drivetrain', 'GearBoxSpeeds', 'Width(mm)', 'Overallwidthwithmirror(mm)', 'Height(mm)', 'Wheelbase(mm)']

df_all = pd.DataFrame()

for components_file in components_files:
    df_components = pd.read_csv(components_file)
    df_components['vehicle_yrmkmdl'] = components_file.replace(maindir+'\\', '').replace(' Components.csv','')
    df_components = df_components.drop(columns=drop_columns_pre_run,
                                   errors='ignore')  # reduce script memory requirements, and output file size, drop unnecessary fields

    if df_all.empty:
        df_all = df_components
    else:
        df_all = pd.concat([df_all, df_components], ignore_index=True)

df_all = df_all.drop(columns=drop_columns_post_run) # reduce output file size, drop intermediate calculation fields

# merge product description key fields
df_productdescriptions = pd.read_csv(productdescriptionsfile)
df_productdescriptions = df_productdescriptions[productdescriptionsfields]

df_all = df_all.merge(df_productdescriptions,
                              how='left', on=['vehicle_yrmkmdl'])

df_all.to_csv(os.path.join(outputdir, 'combined_components.csv')