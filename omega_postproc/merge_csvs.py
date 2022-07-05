import pandas as pd
import glob
import os

maindir = 'C:/Users/KBolon/Documents/OMEGA_runs/2022June/'
runname = '2022_06_29_16_48_36_Gap_compare_trial'
sessionnames = ['_Flatter_2', '_Gap+10', '_Gap+20', '_Gap+40', '_Gap-20', 'NoGap', '_SAFE'] #, '_NTR+OCC', '_Steep']

df = pd.DataFrame()
for sessionname in sessionnames:
    # list of merged files returned
    files = os.path.join(maindir + '/' + runname + '/' + sessionname + '/out/' + '*cost_cloud.csv')
    files = glob.glob(files)
    for file in files:
        dftmp = pd.read_csv(file)
        dftmp.columns = dftmp.columns.str.replace('veh_....._', '',regex=True)
        dftmp.columns = dftmp.columns.str.replace('veh_...._', '', regex=True)
        dftmp['run_name'] = runname
        dftmp['session_name'] = sessionname
        if df.empty:
            df = dftmp
        else:
            df = pd.concat([df, dftmp], ignore_index=True)
df.to_csv(maindir + '/' + runname + '/' + 'combined_cost_cloud.csv')
