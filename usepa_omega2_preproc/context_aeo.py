"""
context_aeo.py
==============

"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil

path_cwd = Path.cwd()
path_aeo_inputs = path_cwd / 'usepa_omega2_preproc/aeo_tables'
path_bea_inputs = path_cwd / 'usepa_omega2_preproc/bea_tables'
path_outputs = path_cwd / 'usepa_omega2_preproc/output_context_aeo'
path_outputs.mkdir(exist_ok=True)
path_input_templates = path_cwd / 'input_samples'

vehicles_context_template = 'context_new_vehicle_market.csv'
fuels_context_template = 'context_fuel_prices.csv'
price_deflators_template = 'context_implicit_price_deflators.csv'
cpiu_deflators_template = 'context_cpiu_price_deflators.csv'

# from somewhere, e.g., the top/general section of the batch file, the string_id has to be set; this is a placeholder
aeo_case = 'Reference case'
# aeo = string_id.replace(' ', '')
gasoline_upstream = 2478 # 77 FR 63181
electricity_upstream = 534 # 77 FR 63182


def melt_df(df, id_col, value_name, drop_col=None):
    """
    Melt the passed DataFrame from short-and-wide to long-and-narrow.
    :param df: The passed DataFrame.
    :param value_name: The name for the resultant data column.
    :param drop_col: The name of any columns to be dropped after melt.
    :return: The melted DataFrame with a column of data named value_name.
    """
    df = pd.melt(df, id_vars=[id_col], value_vars=[col for col in df.columns if '20' in col], var_name='calendar_year', value_name=value_name)
    df['calendar_year'] = df['calendar_year'].astype(int)
    if drop_col:
        df.drop(columns=drop_col, inplace=True)
    return df


def new_metric(df, id_column, new_metric, new_metric_entry, *id_words):
    """

    :param df: DataFrame in which new entries (new_metric_entry) are needed for a new_metric.
    :param id_column: The column of data that contains necessary data to determine the new_metric_entry.
    :param new_metric: The name of the new_metric that is to be populated.
    :param new_metric_entry: The new entry to be populated into the new_metric column.
    :param id_words: The words to look for in the id_column to determine what the new_metric_entry should be.
    :return: The passed DataFrame with the new_metric column populated with the new_metric_entries
    """
    for index, row in df.iterrows():
        for id_word in id_words:
            name = row[f'{id_column}']
            if name.__contains__(f'{id_word}'):
                df.at[index, f'{new_metric}'] = f'{new_metric_entry}'
            else:
                pass
    return df


def save_template(df, path_to_template, path_to_save, template_name):
    """

    :param df: The DataFrame containing data to save to the template.
    :param path_to_template: Path to the input template.
    :param path_to_save: Path to the save folder.
    :param template_name: Name of template.
    :return: Confirmation message that the template has been saved and to where.
    """
    shutil.copy2(path_to_template / f'{template_name}', path_to_save / f'{template_name}')

    # open the input template into which results will be placed.
    template_info = pd.read_csv(path_to_save / f'{template_name}', 'b', nrows=0)
    temp = ' '.join((item for item in template_info))
    temp2 = temp.split(',')
    template_info_df = pd.DataFrame(columns=temp2)
    template_info_df.to_csv(path_to_save / f'{template_name}', index=False)

    with open(path_to_save / f'{template_name}', 'a', newline='') as template_file:
        df.to_csv(template_file, index=False)
    return print(f'\n{template_name} saved to {path_to_save}')


class GetContext:
    def __init__(self, path, table_name, string_id, col_id, skiprows=4):
        """

        :param path: The path to input files.
        :param table_name: The AEO table to read.
        :param string_id: The string identifier (e.g., the string_id such as Reference case, High Oil Price, etc.).
        :param col_id: The column identifier where string_id data can be found.
        :param skiprows: The number of rows to be skipped when reading the AEO table.
        """
        self.path = path
        self.table_name = table_name
        self.string_id = string_id
        self.col_id = col_id
        self.skiprows = skiprows

    def __repr__(self):
        return f'Reading {self.table_name}'

    def read_table(self):
        return pd.read_csv(self.path / self.table_name, skiprows=self.skiprows, error_bad_lines=False).dropna()

    def return_case_df(self):
        """

        :return: A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed from the 'full name' column entries.
        """
        df_return = pd.DataFrame(self.read_table().loc[self.read_table()[self.col_id].str.endswith(f'{self.string_id}'), :]).reset_index(drop=True)
        df_return.replace({self.col_id: f': {self.string_id}'}, {self.col_id: ''}, regex=True, inplace=True)
        return df_return

    def aeo_year(self):
        """

        :return: The year of the AEO report, e.g., 'AEO2020'.
        """
        a_loc = self.return_case_df().at[0, 'api key'].find('A')
        return self.return_case_df().at[0, 'api key'][a_loc: a_loc + 7]

    def aeo_dollars(self):
        """

        :return: The dollar basis of the AEO report.
        """
        usd_loc = self.return_case_df().at[0, 'units'].find(' $')
        return int(self.return_case_df().at[0, 'units'][0: usd_loc])

    def select_table_rows(self, metric, replace=None):
        """

        :param metric: The identifying string used to determine what rows to be included in the returned DataFrame.
        :param replace: Any string elements that are to be removed from the entries containing 'metric'.
        :return: A DataFrame of those AEO table rows containing 'metric' within the 'full name' column.
        """
        df_rows = pd.DataFrame()
        df_rows = pd.concat([df_rows, self.return_case_df().loc[self.return_case_df()[self.col_id].str.contains(metric), :]],
                            ignore_index=True)
        if replace:
            df_rows.replace({self.col_id: replace}, {self.col_id: ''}, regex=True, inplace=True)
        df_rows = df_rows.iloc[:, :-1]
        return df_rows


def error_gen(actual, rounded):
    divisor = np.sqrt(1.0 if actual < 1.0 else actual)
    return abs(rounded - actual) ** 2 / divisor


def round_to_100(percents):
    """

    :param percents: A list of percentages to be rounded.
    :return: A list of percents rounded to integers and summing to 100.
    """
    if not np.isclose(sum(percents), 100):
        raise ValueError
    n = len(percents)
    rounded = [int(x) for x in percents]
    up_count = 100 - sum(rounded)
    errors = [(error_gen(percents[i], rounded[i] + 1) - error_gen(percents[i], rounded[i]), i) for i in range(n)]
    rank = sorted(errors)
    for i in range(up_count):
        rounded[rank[i][1]] += 1
    return rounded


def round_floats_to_100(percents, decimals):
    """

    :param percents: A list of percentages to be rounded.
    :param decimals: The number of decimal places in rounded values.
    :return: A list of percents rounded to 'decimals' number of decimal places and summing to 100.
    """
    if not np.isclose(sum(percents), 100):
        raise ValueError
    n = len(percents)
    scaler = 10 ** decimals
    rounded = [int(x * scaler) for x in percents]
    up_count = int(100 * scaler - sum(rounded)) if int(100 * scaler - sum(rounded)) != 0 else 1
    add = round((100 * scaler - sum(rounded)) / up_count, decimals)
    errors = [(error_gen(percents[i] * scaler, rounded[i] + 1 * scaler) - error_gen(percents[i] * scaler, rounded[i]), i) for i in range(n)]
    rank = sorted(errors)
    for i in range(up_count):
        rounded[rank[i][1]] += add
    rounded = [rounded[x] / scaler for x in range(len(rounded))]
    return rounded


def main():
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

    # name the aeo table(s) being used
    aeo_class_attributes_table = 'Table_42._Summary_of_New_Light-Duty_Vehicle_Size_Class_Attributes.csv'
    aeo_sales_table = 'Table_38._Light-Duty_Vehicle_Sales_by_Technology_Type.csv'
    aeo_petroleum_fuel_prices_table = 'Table_58._Components_of_Selected_Petroleum_Product_Prices.csv'
    aeo_electricity_fuel_prices_table = 'Table_8._Electricity_Supply_Disposition_Prices_and_Emissions.csv'
    aeo_vehicle_prices_table = 'Table_52._New_Light-Duty_Vehicle_Prices.csv'

    # and the bea table(s) being used
    deflators_table = 'Table_1.1.9_ImplicitPriceDeflators.csv'
    cpiu_table = 'SeriesReport.csv'

    # first work on class attributes
    attribute = dict()
    aeo_table_obj = GetContext(path_aeo_inputs, aeo_class_attributes_table, aeo_case, 'full name')
    print(aeo_table_obj)
    attribute['HP'] = aeo_table_obj.select_table_rows('Horsepower', replace='New Vehicle Attributes: Horsepower: Conventional ')
    attribute['lb'] = aeo_table_obj.select_table_rows('Weight', replace='New Vehicle Attributes: Weight: Conventional ')
    attribute['percent'] = aeo_table_obj.select_table_rows('Sales Shares', replace='New Vehicle Attributes: Sales Shares: ')
    attribute['mpg_conventional'] = aeo_table_obj.select_table_rows('EPA Efficiency', replace='New Vehicle Attributes: EPA Efficiency: Conventional ')
    attribute['mpg_alternative'] = aeo_table_obj.select_table_rows('Fuel Efficiency', replace='New Vehicle Attributes: Fuel Efficiency: Alternative-Fuel ')
    attribute['ratio'] = aeo_table_obj.select_table_rows('Degradation Factors', replace='New Vehicle Attributes: Degradation Factors: ')

    # merge things together; start with shares since that metric excludes any averages which makes for a better merge
    aeo_veh_context = pd.DataFrame()
    aeo_veh_context = melt_df(attribute['percent'], 'full name', 'sales_share_of_regclass')
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['lb'], 'full name', 'weight_lbs'), on=['full name', 'calendar_year'])
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['HP'], 'full name', 'horsepower'), on=['full name', 'calendar_year'])
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['mpg_conventional'], 'full name', 'mpg_conventional'), on=['full name', 'calendar_year'])
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['mpg_alternative'], 'full name', 'mpg_alternative'), on=['full name', 'calendar_year'])

    # define reg_class in aeo_veh_context and ratio DFs and then merge ratio in
    ratio_df = melt_df(attribute['ratio'], 'full name', 'onroad_to_cycle_mpg_ratio')
    for df in [aeo_veh_context, ratio_df]:
        df.insert(df.columns.get_loc('calendar_year') + 1, 'reg_class_id', '')
        df = new_metric(df, 'full name', 'reg_class_id', 'car', 'Car')
        df = new_metric(df, 'full name', 'reg_class_id', 'truck', 'Truck')
    ratio_df.drop(columns='full name', inplace=True)
    aeo_veh_context = aeo_veh_context.merge(ratio_df, on=['reg_class_id', 'calendar_year'])

    # calculate some new metrics
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('horsepower') + 1,
                           'horsepower_to_weight_ratio',
                           aeo_veh_context['horsepower'] / aeo_veh_context['weight_lbs'])
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('mpg_conventional') + 1,
                           'mpg_conventional_onroad',
                           aeo_veh_context[['mpg_conventional', 'onroad_to_cycle_mpg_ratio']].product(axis=1))
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('mpg_alternative') + 1,
                           'mpg_alternative_onroad',
                           aeo_veh_context[['mpg_alternative', 'onroad_to_cycle_mpg_ratio']].product(axis=1))
    aeo_veh_context.insert(0, 'case_id', f'{aeo_case}')
    aeo_veh_context.insert(0, 'context_id', aeo_table_obj.aeo_year())

    # work on sales
    aeo_table_obj = GetContext(path_aeo_inputs, aeo_sales_table, aeo_case, 'full name')
    print(aeo_table_obj)
    sales_fleet = aeo_table_obj.select_table_rows('Light-Duty Vehicle Sales: Total Vehicles Sales')
    sales_car = aeo_table_obj.select_table_rows('Light-Duty Vehicle Sales: Total New Car')
    sales_truck = aeo_table_obj.select_table_rows('Light-Duty Vehicle Sales: Total New Truck')

    # merge individual sales into a new DF
    sales = melt_df(sales_fleet, 'full name', 'sales_fleet')\
        .merge(melt_df(sales_car, 'full name', 'sales_car', 'full name'), on='calendar_year')\
        .merge(melt_df(sales_truck, 'full name', 'sales_truck', 'full name'), on='calendar_year')
    sales_cols = [col for col in sales if 'sales' in col]
    sales[sales_cols] = sales[sales_cols] * 1000

    # insert share of fleet data into aeo_class_attributes
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('sales_share_of_regclass') + 1,
                           'sales_share_of_total',
                           0)
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('sales_share_of_total') + 1,
                           'sales',
                           0)
    # calc some new metrics
    fleet_dict = dict()
    fleet_context_df = pd.DataFrame()
    for year in range(aeo_veh_context['calendar_year'].min(), aeo_veh_context['calendar_year'].max() + 1):
        sales_df = pd.DataFrame(sales.loc[sales['calendar_year'] == year, :])
        sales_df.reset_index(drop=True, inplace=True)
        car_sales = sales_df.at[0, 'sales_car']
        truck_sales = sales_df.at[0, 'sales_truck']
        fleet_sales = sales_df.at[0, 'sales_fleet']

        fleet_dict[year, 'car'] = pd.DataFrame(aeo_veh_context.loc[(aeo_veh_context['calendar_year'] == year) & (aeo_veh_context['reg_class_id'] == 'car'), :])
        fleet_dict[year, 'car']['sales'] = (fleet_dict[year, 'car']['sales_share_of_regclass'] / 100) * car_sales
        fleet_dict[year, 'car']['sales_share_of_total'] = (fleet_dict[year, 'car']['sales'] / fleet_sales) * 100

        fleet_dict[year, 'truck'] = pd.DataFrame(aeo_veh_context.loc[(aeo_veh_context['calendar_year'] == year) & (aeo_veh_context['reg_class_id'] == 'truck'), :])
        fleet_dict[year, 'truck']['sales'] = (fleet_dict[year, 'truck']['sales_share_of_regclass'] / 100) * truck_sales
        fleet_dict[year, 'truck']['sales_share_of_total'] = (fleet_dict[year, 'truck']['sales'] / fleet_sales) * 100
        fleet_context_df = pd.concat([fleet_context_df, fleet_dict[year, 'car'], fleet_dict[year, 'truck']], axis=0, ignore_index=True)

    # work on vehicle prices
    vehicle_prices = dict()
    aeo_table_obj = GetContext(path_aeo_inputs, aeo_vehicle_prices_table, aeo_case, 'full name')
    print(aeo_table_obj)
    vehicle_prices['gasoline'] = aeo_table_obj.select_table_rows('Gasoline: ', replace='New Light-Duty Vehicle Prices: Gasoline: ')
    vehicle_prices['electric'] = aeo_table_obj.select_table_rows('300 Mile Electric Vehicle: ', replace='New Light-Duty Vehicle Prices: 300 Mile Electric Vehicle: ')

    vehicle_prices['gasoline'] = melt_df(vehicle_prices['gasoline'], 'full name', 'ice_price_dollars')
    vehicle_prices['electric'] = melt_df(vehicle_prices['electric'], 'full name', 'bev_price_dollars')
    vehicle_prices['gasoline']['ice_price_dollars'] = vehicle_prices['gasoline']['ice_price_dollars'] * 1000
    vehicle_prices['electric']['bev_price_dollars'] = vehicle_prices['electric']['bev_price_dollars'] * 1000

    # clean up vehicle_prices for merging
    for df in [vehicle_prices['gasoline'], vehicle_prices['electric']]:
        df.insert(df.columns.get_loc('calendar_year') + 1, 'reg_class_id', '')
        df = new_metric(df, 'full name', 'reg_class_id', 'car', 'full name', 'Car')
        df = new_metric(df, 'full name', 'reg_class_id', 'truck', 'Truck')
        df = new_metric(df, 'full name', 'reg_class_id', 'truck', 'Pickup')
        df = new_metric(df, 'full name', 'reg_class_id', 'truck', 'Van')
        df = new_metric(df, 'full name', 'reg_class_id', 'truck', 'Utility')
        df.replace({'full name': r' Car'}, {'full name': ''}, regex=True, inplace=True)
        df.replace({'full name': r'Mini-compact'}, {'full name': 'Minicompact'}, regex=True, inplace=True)
        df.replace({'full name': r' Light Truck'}, {'full name': ''}, regex=True, inplace=True)
    vehicle_prices_df = vehicle_prices['gasoline'].merge(vehicle_prices['electric'], on=['full name', 'calendar_year', 'reg_class_id'])

    # merge prices into larger context DF, but first make the "full name" columns consistent
    fleet_context_df.replace({'full name': r'Cars: '}, {'full name': ''}, regex=True, inplace=True)
    fleet_context_df.replace({'full name': r'Light Trucks: '}, {'full name': ''}, regex=True, inplace=True)

    fleet_context_df = fleet_context_df.merge(vehicle_prices_df, on=['full name', 'calendar_year', 'reg_class_id'], how='left')
    fleet_context_df.rename(columns={'full name': 'context_size_class'}, inplace=True)

    # lastly, round all the sales shares and force sum to 100
    for yr in range(fleet_context_df['calendar_year'].min(), fleet_context_df['calendar_year'].max() + 1):
        shares = pd.Series(fleet_context_df.loc[fleet_context_df['calendar_year'] == yr, 'sales_share_of_total']).tolist()
        new_shares = round_floats_to_100(shares, 2)
        fleet_context_df.loc[fleet_context_df['calendar_year'] == yr, 'sales_share_of_total'] = new_shares
        for reg_class in ['car', 'truck']:
            shares = pd.Series(fleet_context_df.loc[(fleet_context_df['calendar_year'] == yr) & (fleet_context_df['reg_class_id'] == reg_class), 'sales_share_of_regclass']).tolist()
            new_shares = round_floats_to_100(shares, 2)
            fleet_context_df.loc[(fleet_context_df['calendar_year'] == yr) & (fleet_context_df['reg_class_id'] == reg_class), 'sales_share_of_regclass'] = new_shares

    # work on fuel prices
    aeo_table_obj = GetContext(path_aeo_inputs, aeo_petroleum_fuel_prices_table, aeo_case, 'full name')
    print(aeo_table_obj)
    gasoline_retail_prices = aeo_table_obj.select_table_rows('Price Components: Motor Gasoline: End-User Price')
    # the above selects all rows but all we want is the true end user price row, so now get that alone
    gasoline_retail_prices = gasoline_retail_prices.loc[gasoline_retail_prices['full name'] == 'Price Components: Motor Gasoline: End-User Price', :]

    gasoline_distribution = aeo_table_obj.select_table_rows('Price Components: Motor Gasoline: End-User Price: Distribution Costs')

    gasoline_wholesale = aeo_table_obj.select_table_rows('Price Components: Motor Gasoline: End-User Price: Wholesale Price')

    gasoline_retail_prices = melt_df(gasoline_retail_prices, 'full name', 'retail_dollars_per_unit', 'full name')
    gasoline_retail_prices.insert(0, 'fuel_id', 'pump gasoline')
    gasoline_retail_prices.insert(0, 'case_id', f'{aeo_case}')
    gasoline_retail_prices.insert(0, 'context_id', aeo_table_obj.aeo_year())

    gasoline_distribution = melt_df(gasoline_distribution, 'full name', 'gasoline_distribution', 'full name')
    gasoline_wholesale = melt_df(gasoline_wholesale, 'full name', 'gasoline_wholesale', 'full name')

    gasoline_pretax_prices = gasoline_retail_prices.copy()
    gasoline_pretax_prices['pretax_dollars_per_unit'] = gasoline_distribution['gasoline_distribution'] \
                                                      + gasoline_wholesale['gasoline_wholesale']
    gasoline_pretax_prices['fuel_id'] = 'pump gasoline'

    gasoline_prices = gasoline_retail_prices.join(gasoline_pretax_prices[['pretax_dollars_per_unit']])

    usd_basis = aeo_table_obj.aeo_dollars()

    # electricity prices
    aeo_table_obj = GetContext(path_aeo_inputs, aeo_electricity_fuel_prices_table, aeo_case, 'full name')
    print(aeo_table_obj)
    electricity_prices_residential = aeo_table_obj.select_table_rows('Electricity: End-Use Prices: Residential')
    electricity_prices_allsecavg = aeo_table_obj.select_table_rows('Electricity: End-Use Prices: All Sectors Average')
    # the above gets prices in constant and nominal cents so nominal need to be removed
    electricity_prices_residential = electricity_prices_residential.loc[~electricity_prices_residential['units'].str.contains('nom'), :]
    electricity_prices_allsecavg = electricity_prices_allsecavg.loc[~electricity_prices_allsecavg['units'].str.contains('nom'), :]

    electricity_prices_residential = melt_df(electricity_prices_residential, 'full name', 'retail_dollars_per_unit', 'full name')
    electricity_prices_allsecavg = melt_df(electricity_prices_allsecavg, 'full name', 'pretax_dollars_per_unit', 'full name')

    electricity_prices_residential['retail_dollars_per_unit'] = electricity_prices_residential['retail_dollars_per_unit'] / 100
    electricity_prices_allsecavg['pretax_dollars_per_unit'] = electricity_prices_allsecavg['pretax_dollars_per_unit'] / 100

    electricity_prices_residential.insert(0, 'fuel_id', 'US electricity')
    electricity_prices_allsecavg.insert(0, 'fuel_id', 'US electricity')

    for df in [electricity_prices_residential, electricity_prices_allsecavg]:
        df.insert(0, 'case_id', f'{aeo_case}')
        df.insert(0, 'context_id', aeo_table_obj.aeo_year())

    electricity_prices = electricity_prices_residential.join(electricity_prices_allsecavg[['pretax_dollars_per_unit']])

    # concatenate the fuel prices into one DF
    aeo_fuel_context = pd.concat([gasoline_prices, electricity_prices], ignore_index=True, axis=0)

    # work on deflators
    bea_table_obj = GetContext(path_bea_inputs, deflators_table, 'Gross domestic product', 'Unnamed: 1')
    print(bea_table_obj)
    deflators = bea_table_obj.return_case_df()
    deflators = melt_df(deflators, 'Unnamed: 1', 'price_deflator', 'Unnamed: 1')
    deflators['price_deflator'] = deflators['price_deflator'].astype(float)
    basis_factor_df = pd.DataFrame(deflators.loc[deflators['calendar_year'] == usd_basis, 'price_deflator']).reset_index(drop=True)
    basis_factor = basis_factor_df.at[0, 'price_deflator']
    deflators.insert(len(deflators.columns),
                     'adjustment_factor',
                     basis_factor / deflators['price_deflator'])

    cpi = pd.read_csv(path_bea_inputs / cpiu_table, skiprows=11, usecols=[0, 1])
    cpi.rename(columns={'Year': 'calendar_year', 'Annual': 'price_deflator'}, inplace=True)
    basis_factor_df = pd.DataFrame(cpi.loc[cpi['calendar_year'] == usd_basis, 'price_deflator']).reset_index(drop=True)
    basis_factor = basis_factor_df.at[0, 'price_deflator']
    cpi.insert(len(cpi.columns),
               'adjustment_factor',
               basis_factor / cpi['price_deflator'])

    # print to output files
    print(f'Saving output files to {path_outputs}')
    path_of_run_folder = path_outputs / f'{start_time_readable}_run'
    path_of_run_folder.mkdir(exist_ok=False)

    save_template(fleet_context_df, path_input_templates, path_of_run_folder, vehicles_context_template)
    save_template(aeo_fuel_context, path_input_templates, path_of_run_folder, fuels_context_template)
    save_template(deflators, path_input_templates, path_of_run_folder, price_deflators_template)
    save_template(cpi, path_input_templates, path_of_run_folder, cpiu_deflators_template)


if __name__ == '__main__':
    main()
