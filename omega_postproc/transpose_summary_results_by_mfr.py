import pandas as pd
import os

maindir = 'C:/Users/KBOLON/OMEGA'
runname = '2023_01_06_13_35_41_ldv_sensitivity_AEOlow_20230105'

summary_file = os.path.join(maindir, runname, runname + '_summary_results.csv')
df_summary = pd.read_csv(summary_file)
mfrnames = list(df_summary.filter(regex='_sales_total').columns.str.replace('_sales_total', ''))
df_all = pd.DataFrame()

for mfrname in mfrnames:
    df_mfr = df_summary[['calendar_year', 'session_name', mfrname + '_sales_total', mfrname + '_target_co2e_Mg', mfrname + '_calendar_year_cert_co2e_Mg', mfrname + '_model_year_cert_co2e_Mg']]
    df_mfr.columns = df_mfr.columns.str.replace(mfrname + "_", "")
    df_mfr['manufacturer_name'] = mfrname

    if df_all.empty:
        df_all = df_mfr
    else:
        df_all = pd.concat([df_all, df_mfr], ignore_index=True)

df_all.to_csv(os.path.join(maindir, runname, runname + '_summary_results_w_mfr_transposed.csv'))