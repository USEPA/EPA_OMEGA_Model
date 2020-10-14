"""
context_aeo.py

"""

import pandas as pd
from pathlib import Path

path_cwd = Path.cwd()
path_inputs = path_cwd / 'usepa_omega2_preproc/aeo_tables'
path_outputs = path_cwd / 'usepa_omega2_preproc/output_context_aeo'
path_outputs.mkdir(exist_ok=True)
path_input_templates = path_cwd / 'input_templates'

vehicles_context_filename = 'new_vehicle_sales_context-aeo.csv'
fuels_context_filename = 'fuels_context-aeo.csv'

# from somewhere, e.g., the top/general section of the batch file, the aeo_case has to be set; this is a placeholder
aeo_case = 'Reference case'
# aeo = aeo_case.replace(' ', '')
gasoline_upstream = 2478 # 77 FR 63181
electricity_upstream = 534 # 77 FR 63182


def melt_df(df, value_name, drop_col=None):
    """
    Melt the passed DataFrame from short-and-wide to long-and-narrow.
    :param df: The passed DataFrame.
    :param value_name: The name for the resultant data column.
    :param drop_col: The name of any columns to be dropped after melt.
    :return: The melted DataFrame with a column of data named value_name.
    """
    df = pd.melt(df, id_vars=['full name'], value_vars=[col for col in df.columns if '20' in col], var_name='calendar_year', value_name=value_name)
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


class GetAEO:
    def __init__(self, table_name, aeo_case, skiprows=4):
        """

        :param table_name: The AEO table to read.
        :param aeo_case: The aeo case (e.g., Reference case, High Oil Price, etc.)
        :param skiprows: The number of rows to be skipped when reading the AEO table.
        """
        self.table_name = table_name
        self.aeo_case = aeo_case
        self.skiprows = skiprows

    def __repr__(self):
        return f'Reading {self.table_name} for AEO {self.aeo_case}'

    def read_aeo_table(self):
        return pd.read_csv(path_inputs / self.table_name, skiprows=self.skiprows, error_bad_lines=False).dropna()

    def return_aeo_case_df(self):
        """

        :return: A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed from the 'full name' column entries.
        """
        df_return = pd.DataFrame(self.read_aeo_table().loc[self.read_aeo_table()['full name'].str.endswith(f'{self.aeo_case}'), :])
        df_return.replace({'full name': f': {self.aeo_case}'}, {'full name': ''}, regex=True, inplace=True)
        return df_return

    def aeo_year(self):
        """

        :return: The year of the AEO report, e.g., 'AEO2020'.
        """
        a_loc = self.read_aeo_table().at[self.skiprows, 'api key'].find('A')
        return self.read_aeo_table().at[self.skiprows, 'api key'][a_loc: a_loc + 7]

    def select_aeo_table_rows(self, metric, replace=None):
        """

        :param metric: The identifying string used to determine what rows to be included in the returned DataFrame.
        :param replace: Any string elements that are to be removed from the entries containing 'metric'.
        :return: A DataFrame of those AEO table rows containing 'metric' within the 'full name' column.
        """
        df_rows = pd.DataFrame()
        df_rows = pd.concat([df_rows, self.return_aeo_case_df().loc[self.return_aeo_case_df()['full name'].str.contains(metric), :]],
                            ignore_index=True)
        if replace:
            df_rows.replace({'full name': replace}, {'full name': ''}, regex=True, inplace=True)
        df_rows = df_rows.iloc[:, :-1]
        return df_rows


def main():
    # name the aeo tables being used
    aeo_class_attributes_table = 'Table_42._Summary_of_New_Light-Duty_Vehicle_Size_Class_Attributes.csv'
    aeo_sales_table = 'Table_38._Light-Duty_Vehicle_Sales_by_Technology_Type.csv'
    aeo_petroleum_fuel_prices_table = 'Table_58._Components_of_Selected_Petroleum_Product_Prices.csv'
    aeo_electricity_fuel_prices_table = 'Table_8._Electricity_Supply_Disposition_Prices_and_Emissions.csv'
    aeo_vehicle_prices_table = 'Table_52._New_Light-Duty_Vehicle_Prices.csv'

    # first work on class attributes
    attribute = dict()
    aeo_table_obj = GetAEO(aeo_class_attributes_table, aeo_case)
    print(aeo_table_obj)
    attribute['HP'] = aeo_table_obj.select_aeo_table_rows('Horsepower', replace='New Vehicle Attributes: Horsepower: Conventional ')
    attribute['lb'] = aeo_table_obj.select_aeo_table_rows('Weight', replace='New Vehicle Attributes: Weight: Conventional ')
    attribute['percent'] = aeo_table_obj.select_aeo_table_rows('Sales Shares', replace='New Vehicle Attributes: Sales Shares: ')
    attribute['mpg_conventional'] = aeo_table_obj.select_aeo_table_rows('EPA Efficiency', replace='New Vehicle Attributes: EPA Efficiency: Conventional ')
    attribute['mpg_alternative'] = aeo_table_obj.select_aeo_table_rows('Fuel Efficiency', replace='New Vehicle Attributes: Fuel Efficiency: Alternative-Fuel ')
    attribute['ratio'] = aeo_table_obj.select_aeo_table_rows('Degradation Factors', replace='New Vehicle Attributes: Degradation Factors: ')

    # merge things together; start with shares since that metric excludes any averages which makes for a better merge
    aeo_veh_context = pd.DataFrame()
    aeo_veh_context = melt_df(attribute['percent'], 'sales_share_of_regclass')
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['lb'], 'weight_lbs'), on=['full name', 'calendar_year'])
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['HP'], 'hp'), on=['full name', 'calendar_year'])
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['mpg_conventional'], 'mpg_conventional'), on=['full name', 'calendar_year'])
    aeo_veh_context = aeo_veh_context.merge(melt_df(attribute['mpg_alternative'], 'mpg_alternative'), on=['full name', 'calendar_year'])

    # define reg_class in aeo_veh_context and ratio DFs and then merge ratio in
    ratio_df = melt_df(attribute['ratio'], 'onroad_to_cycle_mpg_ratio')
    for df in [aeo_veh_context, ratio_df]:
        df.insert(df.columns.get_loc('calendar_year') + 1, 'reg_class', '')
        df = new_metric(df, 'full name', 'reg_class', 'car', 'Car')
        df = new_metric(df, 'full name', 'reg_class', 'truck', 'Truck')
    ratio_df.drop(columns='full name', inplace=True)
    aeo_veh_context = aeo_veh_context.merge(ratio_df, on=['reg_class', 'calendar_year'])

    # calculate some new metrics
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('hp') + 1,
                           'hp_to_weight',
                           aeo_veh_context['hp'] / aeo_veh_context['weight_lbs'])
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('mpg_conventional') + 1,
                           'mpg_conventional_onroad',
                           aeo_veh_context[['mpg_conventional', 'onroad_to_cycle_mpg_ratio']].product(axis=1))
    aeo_veh_context.insert(aeo_veh_context.columns.get_loc('mpg_alternative') + 1,
                           'mpg_alternative_onroad',
                           aeo_veh_context[['mpg_alternative', 'onroad_to_cycle_mpg_ratio']].product(axis=1))
    aeo_veh_context.insert(0, 'aeo_case_id', f'{aeo_case}')
    aeo_veh_context.insert(0, 'aeo_context_id', aeo_table_obj.aeo_year())

    # work on sales
    aeo_table_obj = GetAEO(aeo_sales_table, aeo_case)
    print(aeo_table_obj)
    sales_fleet = aeo_table_obj.select_aeo_table_rows('Light-Duty Vehicle Sales: Total Vehicles Sales')
    sales_car = aeo_table_obj.select_aeo_table_rows('Light-Duty Vehicle Sales: Total New Car')
    sales_truck = aeo_table_obj.select_aeo_table_rows('Light-Duty Vehicle Sales: Total New Truck')

    # merge individual sales into a new DF
    sales = melt_df(sales_fleet, 'sales_fleet')\
        .merge(melt_df(sales_car, 'sales_car', 'full name'), on='calendar_year')\
        .merge(melt_df(sales_truck, 'sales_truck', 'full name'), on='calendar_year')
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

        fleet_dict[year, 'car'] = pd.DataFrame(aeo_veh_context.loc[(aeo_veh_context['calendar_year'] == year) & (aeo_veh_context['reg_class'] == 'car'), :])
        fleet_dict[year, 'car']['sales'] = (fleet_dict[year, 'car']['sales_share_of_regclass'] / 100) * car_sales
        fleet_dict[year, 'car']['sales_share_of_total'] = (fleet_dict[year, 'car']['sales'] / fleet_sales) * 100

        fleet_dict[year, 'truck'] = pd.DataFrame(aeo_veh_context.loc[(aeo_veh_context['calendar_year'] == year) & (aeo_veh_context['reg_class'] == 'truck'), :])
        fleet_dict[year, 'truck']['sales'] = (fleet_dict[year, 'truck']['sales_share_of_regclass'] / 100) * truck_sales
        fleet_dict[year, 'truck']['sales_share_of_total'] = (fleet_dict[year, 'truck']['sales'] / fleet_sales) * 100
        fleet_context_df = pd.concat([fleet_context_df, fleet_dict[year, 'car'], fleet_dict[year, 'truck']], axis=0, ignore_index=True)

    # work on vehicle prices
    vehicle_prices = dict()
    aeo_table_obj = GetAEO(aeo_vehicle_prices_table, aeo_case)
    print(aeo_table_obj)
    vehicle_prices['gasoline'] = aeo_table_obj.select_aeo_table_rows('Gasoline: ', replace='New Light-Duty Vehicle Prices: Gasoline: ')
    vehicle_prices['electric'] = aeo_table_obj.select_aeo_table_rows('300 Mile Electric Vehicle: ', replace='New Light-Duty Vehicle Prices: 300 Mile Electric Vehicle: ')

    vehicle_prices['gasoline'] = melt_df(vehicle_prices['gasoline'], 'ice_price_dollars')
    vehicle_prices['electric'] = melt_df(vehicle_prices['electric'], 'bev_price_dollars')
    vehicle_prices['gasoline']['ice_price_dollars'] = vehicle_prices['gasoline']['ice_price_dollars'] * 1000
    vehicle_prices['electric']['bev_price_dollars'] = vehicle_prices['electric']['bev_price_dollars'] * 1000

    # clean up vehicle_prices for merging
    for df in [vehicle_prices['gasoline'], vehicle_prices['electric']]:
        df.insert(df.columns.get_loc('calendar_year') + 1, 'reg_class', '')
        df = new_metric(df, 'full name', 'reg_class', 'car', 'full name', 'Car')
        df = new_metric(df, 'full name', 'reg_class', 'truck', 'Truck')
        df = new_metric(df, 'full name', 'reg_class', 'truck', 'Pickup')
        df = new_metric(df, 'full name', 'reg_class', 'truck', 'Van')
        df = new_metric(df, 'full name', 'reg_class', 'truck', 'Utility')
        df.replace({'full name': r' Car'}, {'full name': ''}, regex=True, inplace=True)
        df.replace({'full name': r'Mini-compact'}, {'full name': 'Minicompact'}, regex=True, inplace=True)
        df.replace({'full name': r' Light Truck'}, {'full name': ''}, regex=True, inplace=True)
    vehicle_prices_df = vehicle_prices['gasoline'].merge(vehicle_prices['electric'], on=['full name', 'calendar_year', 'reg_class'])

    # merge prices into larger context DF, but first make the "full name" columns consistent
    fleet_context_df.replace({'full name': r'Cars: '}, {'full name': ''}, regex=True, inplace=True)
    fleet_context_df.replace({'full name': r'Light Trucks: '}, {'full name': ''}, regex=True, inplace=True)

    fleet_context_df = fleet_context_df.merge(vehicle_prices_df, on=['full name', 'calendar_year', 'reg_class'], how='left')
    fleet_context_df.rename(columns={'full name': 'aeo_size_class'}, inplace=True)


    # work on fuel prices
    aeo_table_obj = GetAEO(aeo_petroleum_fuel_prices_table, aeo_case)
    print(aeo_table_obj)
    gasoline_retail_prices = aeo_table_obj.select_aeo_table_rows('Price Components: Motor Gasoline: End-User Price')
    # the above selects all rows but all we want is the true end user price row, so now get that alone
    gasoline_retail_prices = gasoline_retail_prices.loc[gasoline_retail_prices['full name'] == 'Price Components: Motor Gasoline: End-User Price', :]

    gasoline_distribution = aeo_table_obj.select_aeo_table_rows('Price Components: Motor Gasoline: End-User Price: Distribution Costs')

    gasoline_wholesale = aeo_table_obj.select_aeo_table_rows('Price Components: Motor Gasoline: End-User Price: Wholesale Price')

    gasoline_retail_prices = melt_df(gasoline_retail_prices, 'cost_dollars_per_unit', 'full name')
    gasoline_retail_prices.insert(0, 'fuel_id', 'pump gasoline retail')
    gasoline_retail_prices.insert(0, 'aeo_case_id', f'{aeo_case}')
    gasoline_retail_prices.insert(0, 'aeo_context_id', aeo_table_obj.aeo_year())

    gasoline_distribution = melt_df(gasoline_distribution, 'gasoline_distribution', 'full name')
    gasoline_wholesale = melt_df(gasoline_wholesale, 'gasoline_wholesale', 'full name')

    gasoline_prices_pretax = gasoline_retail_prices.copy()
    gasoline_prices_pretax['cost_dollars_per_unit'] = gasoline_distribution['gasoline_distribution'] \
                                                      + gasoline_wholesale['gasoline_wholesale']
    gasoline_prices_pretax['fuel_id'] = 'pump gasoline pretax'

    # electricity prices
    aeo_table_obj = GetAEO(aeo_electricity_fuel_prices_table, aeo_case)
    print(aeo_table_obj)
    electricity_prices_residential = aeo_table_obj.select_aeo_table_rows('Electricity: End-Use Prices: Residential')
    electricity_prices_allsecavg = aeo_table_obj.select_aeo_table_rows('Electricity: End-Use Prices: All Sectors Average')
    # the above gets prices in constant and nominal cents so nominal need to be removed
    electricity_prices_residential = electricity_prices_residential.loc[~electricity_prices_residential['units'].str.contains('nom'), :]
    electricity_prices_allsecavg = electricity_prices_allsecavg.loc[~electricity_prices_allsecavg['units'].str.contains('nom'), :]

    electricity_prices_residential = melt_df(electricity_prices_residential, 'cost_dollars_per_unit', 'full name')
    electricity_prices_allsecavg = melt_df(electricity_prices_allsecavg, 'cost_dollars_per_unit', 'full name')

    electricity_prices_residential['cost_dollars_per_unit'] = electricity_prices_residential['cost_dollars_per_unit'] / 100
    electricity_prices_allsecavg['cost_dollars_per_unit'] = electricity_prices_allsecavg['cost_dollars_per_unit'] / 100

    electricity_prices_residential.insert(0, 'fuel_id', 'US electricity residential')
    electricity_prices_allsecavg.insert(0, 'fuel_id', 'US electricity all sectors average')

    for df in [electricity_prices_residential, electricity_prices_allsecavg]:
        df.insert(0, 'aeo_case_id', f'{aeo_case}')
        df.insert(0, 'aeo_context_id', aeo_table_obj.aeo_year())

    # concatenate the fuel prices into one DF
    aeo_fuel_context = pd.concat([gasoline_retail_prices, gasoline_prices_pretax,
                                  electricity_prices_residential, electricity_prices_allsecavg], ignore_index=True, axis=0)

    # print to output files
    print(f'Saving output files to {path_outputs}')
    fleet_context_df.to_csv(path_outputs / vehicles_context_filename, index=False)
    aeo_fuel_context.to_csv(path_outputs / fuels_context_filename, index=False)


if __name__ == '__main__':
    main()
