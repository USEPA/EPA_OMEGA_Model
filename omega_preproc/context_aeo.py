"""
context_aeo.py
==============

"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil



def read_table(path, table_name, skiprows=4):
    """

    :param path: The path to input files.
    :param table_name: The AEO table to read.
    :param skiprows: The number of rows to be skipped when reading the AEO table.
    :return: A DataFrame of the table_name.

    """
    return pd.read_csv(path / table_name, skiprows=skiprows, error_bad_lines=False).dropna()


def return_df(table, col_id, string_id):
    """

    :param table: A DataFrame of the table_name passed thru the read_table function.
    :param col_id: The column identifier where string_id data can be found.
    :param string_id: The string identifier (e.g., the string_id such as Reference case, High Oil Price, etc.).
    :return: A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed from the 'full name' column entries.
    
    """
    df_return = pd.DataFrame(table.loc[table[col_id].str.endswith(f'{string_id}'), :]).reset_index(drop=True)
    df_return.replace({col_id: f': {string_id}'}, {col_id: ''}, regex=True, inplace=True)
    return df_return


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


def save_template(settings, df, path_to_save, template_name):
    """

    :param df: The DataFrame containing data to save to the template.
    :param settings: The SetInputs class.
    :param path_to_save: Path to the save folder.
    :param template_name: Name of template.
    :return: Confirmation message that the template has been saved and to where.

    """
    shutil.copy2(settings.path_input_templates / f'{template_name}', path_to_save / f'{template_name}')

    # open the input template into which results will be placed.
    template_info = pd.read_csv(path_to_save / f'{template_name}', 'b', nrows=0)
    temp = ' '.join((item for item in template_info))
    temp2 = temp.split(',')
    template_info_df = pd.DataFrame(columns=temp2)
    template_info_df.to_csv(path_to_save / f'{template_name}', index=False)

    with open(path_to_save / f'{template_name}', 'a', newline='') as template_file:
        df.to_csv(template_file, index=False)
    return print(f'\n{template_name} saved to {path_to_save}')


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


class GetContext:
    def __init__(self, table):
        """

        :param table: A DataFrame of the table being worked on.
        """
        self.table = table

    def aeo_year(self):
        """

        :return: The year of the report, e.g., 'AEO2020'.
        """
        a_loc = self.table.at[0, 'api key'].find('A')
        return self.table.at[0, 'api key'][a_loc: a_loc + 7]

    def aeo_dollars(self):
        """

        :return: The dollar basis of the AEO report.
        """
        usd_loc = self.table.at[0, 'units'].find(' $')
        return int(self.table.at[0, 'units'][0: usd_loc])

    def select_table_rows(self, col_id, arg, replace=None):
        """

        :param arg: The identifying string used to determine what rows to be included in the returned DataFrame.
        :param replace: Any string elements that are to be removed from the entries containing 'metric'.
        :return: A DataFrame of those AEO table rows containing 'metric' within the 'full name' column.
        """
        df_rows = pd.DataFrame()
        df_rows = pd.concat([df_rows, self.table.loc[self.table[col_id].str.contains(arg), :]],
                            ignore_index=True)
        if replace:
            df_rows.replace({col_id: replace}, {col_id: ''}, regex=True, inplace=True)
        df_rows = df_rows.iloc[:, :-1]
        return df_rows


class SetInputs:
    aeo_version = '2021'
    path_cwd = Path.cwd()
    path_aeo_inputs = path_cwd / f'usepa_omega2_preproc/aeo_tables/AEO{aeo_version}'
    path_bea_inputs = path_cwd / f'usepa_omega2_preproc/bea_tables/BEA{aeo_version}'
    path_outputs = path_cwd / 'usepa_omega2_preproc/output_context_aeo'
    path_outputs.mkdir(exist_ok=True)
    path_input_templates = path_cwd / 'usepa_omega2/test_inputs'

    vehicles_context_template = 'context_new_vehicle_market.csv'
    fuels_context_template = 'context_fuel_prices.csv'
    price_deflators_template = 'implicit_price_deflators.csv'
    cpiu_deflators_template = 'cpi_price_deflators.csv'

    aeo_cases = ['Reference case', 'High oil price', 'Low oil price']
    gasoline_upstream = 2478  # 77 FR 63181
    electricity_upstream = 534  # 77 FR 63182

    # name the aeo table(s) being used
    aeo_class_attributes_table_file = 'Table_42._Summary_of_New_Light-Duty_Vehicle_Size_Class_Attributes.csv'
    aeo_sales_table_file = 'Table_38._Light-Duty_Vehicle_Sales_by_Technology_Type.csv'
    if aeo_version == '2020':
        aeo_petroleum_fuel_prices_table_file = 'Table_58._Components_of_Selected_Petroleum_Product_Prices.csv'
    elif aeo_version == '2021':
        aeo_petroleum_fuel_prices_table_file = 'Table_57._Components_of_Selected_Petroleum_Product_Prices.csv'
    else:
        print('Error finding AEO fuel prices table.')
    aeo_electricity_fuel_prices_table_file = 'Table_8._Electricity_Supply_Disposition_Prices_and_Emissions.csv'
    aeo_vehicle_prices_table_file = 'Table_52._New_Light-Duty_Vehicle_Prices.csv'

    # and the bea table(s) being used
    deflators_table_file = 'Table_1.1.9_ImplicitPriceDeflators.csv'
    cpiu_table_file = 'SeriesReport.csv'


def main():

    settings = SetInputs()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

    # read files as DataFrames
    aeo_class_attributes_table = read_table(settings.path_aeo_inputs, settings.aeo_class_attributes_table_file)
    aeo_sales_table = read_table(settings.path_aeo_inputs, settings.aeo_sales_table_file)
    aeo_petroleum_fuel_prices_table = read_table(settings.path_aeo_inputs, settings.aeo_petroleum_fuel_prices_table_file)
    aeo_electricity_fuel_prices_table = read_table(settings.path_aeo_inputs, settings.aeo_electricity_fuel_prices_table_file)
    aeo_vehicle_prices_table = read_table(settings.path_aeo_inputs, settings.aeo_vehicle_prices_table_file)
    deflators_table = read_table(settings.path_bea_inputs, settings.deflators_table_file)
    cpi_table = pd.read_csv(settings.path_bea_inputs / settings.cpiu_table_file, skiprows=11, usecols=[0, 1])

    # first work on class attributes by looping thru the aeo cases
    fleet_context_df = pd.DataFrame()
    for aeo_case in settings.aeo_cases:
        print(f'Working on market context vehicle attributes for the AEO {aeo_case}')
        attribute = dict()
        attributes_df = return_df(aeo_class_attributes_table, 'full name', aeo_case)
        aeo_table_obj = GetContext(attributes_df)
        attribute['HP'] = aeo_table_obj.select_table_rows('full name', 'Horsepower', replace='New Vehicle Attributes: Horsepower: Conventional ')
        attribute['lb'] = aeo_table_obj.select_table_rows('full name', 'Weight', replace='New Vehicle Attributes: Weight: Conventional ')
        attribute['percent'] = aeo_table_obj.select_table_rows('full name', 'Sales Shares', replace='New Vehicle Attributes: Sales Shares: ')
        attribute['mpg_conventional'] = aeo_table_obj.select_table_rows('full name', 'EPA Efficiency', replace='New Vehicle Attributes: EPA Efficiency: Conventional ')
        attribute['mpg_alternative'] = aeo_table_obj.select_table_rows('full name', 'Fuel Efficiency', replace='New Vehicle Attributes: Fuel Efficiency: Alternative-Fuel ')
        attribute['ratio'] = aeo_table_obj.select_table_rows('full name', 'Degradation Factors', replace='New Vehicle Attributes: Degradation Factors: ')

        # merge things together; start with shares since that metric excludes any averages which makes for a better merge
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
        sales_df = return_df(aeo_sales_table, 'full name', aeo_case)
        aeo_table_obj = GetContext(sales_df)
        print(f'Working on market context vehicle sales for the AEO {aeo_case}')
        sales_fleet = aeo_table_obj.select_table_rows('full name', 'Light-Duty Vehicle Sales: Total Vehicles Sales')
        sales_car = aeo_table_obj.select_table_rows('full name', 'Light-Duty Vehicle Sales: Total New Car')
        sales_truck = aeo_table_obj.select_table_rows('full name', 'Light-Duty Vehicle Sales: Total New Truck')

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
        case_dict = dict()
        case_df = pd.DataFrame()
        for year in range(aeo_veh_context['calendar_year'].min(), aeo_veh_context['calendar_year'].max() + 1):
            sales_df = pd.DataFrame(sales.loc[sales['calendar_year'] == year, :])
            sales_df.reset_index(drop=True, inplace=True)
            car_sales = sales_df.at[0, 'sales_car']
            truck_sales = sales_df.at[0, 'sales_truck']
            fleet_sales = sales_df.at[0, 'sales_fleet']

            case_dict[year, 'car'] = pd.DataFrame(aeo_veh_context.loc[(aeo_veh_context['calendar_year'] == year) & (aeo_veh_context['reg_class_id'] == 'car'), :])
            case_dict[year, 'car']['sales'] = (case_dict[year, 'car']['sales_share_of_regclass'] / 100) * car_sales
            case_dict[year, 'car']['sales_share_of_total'] = (case_dict[year, 'car']['sales'] / fleet_sales) * 100

            case_dict[year, 'truck'] = pd.DataFrame(aeo_veh_context.loc[(aeo_veh_context['calendar_year'] == year) & (aeo_veh_context['reg_class_id'] == 'truck'), :])
            case_dict[year, 'truck']['sales'] = (case_dict[year, 'truck']['sales_share_of_regclass'] / 100) * truck_sales
            case_dict[year, 'truck']['sales_share_of_total'] = (case_dict[year, 'truck']['sales'] / fleet_sales) * 100
            case_df = pd.concat([case_df, case_dict[year, 'car'], case_dict[year, 'truck']], axis=0, ignore_index=True)

        # work on vehicle prices
        prices_df = return_df(aeo_vehicle_prices_table, 'full name', aeo_case)
        aeo_table_obj = GetContext(prices_df)
        print(f'Working on market context vehicle prices for the AEO {aeo_case}')
        vehicle_prices = dict()
        vehicle_prices['gasoline'] = aeo_table_obj.select_table_rows('full name', 'Gasoline: ', replace='New Light-Duty Vehicle Prices: Gasoline: ')
        vehicle_prices['electric'] = aeo_table_obj.select_table_rows('full name', '300 Mile Electric Vehicle: ', replace='New Light-Duty Vehicle Prices: 300 Mile Electric Vehicle: ')

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
        case_df.replace({'full name': r'Cars: '}, {'full name': ''}, regex=True, inplace=True)
        case_df.replace({'full name': r'Light Trucks: '}, {'full name': ''}, regex=True, inplace=True)

        case_df = case_df.merge(vehicle_prices_df, on=['full name', 'calendar_year', 'reg_class_id'], how='left')
        case_df.rename(columns={'full name': 'context_size_class'}, inplace=True)

        # lastly, round all the sales shares and force sum to 100
        for yr in range(case_df['calendar_year'].min(), case_df['calendar_year'].max() + 1):
            shares = pd.Series(case_df.loc[case_df['calendar_year'] == yr, 'sales_share_of_total']).tolist()
            new_shares = round_floats_to_100(shares, 2)
            case_df.loc[case_df['calendar_year'] == yr, 'sales_share_of_total'] = new_shares
            for reg_class in ['car', 'truck']:
                shares = pd.Series(case_df.loc[(case_df['calendar_year'] == yr) & (case_df['reg_class_id'] == reg_class), 'sales_share_of_regclass']).tolist()
                new_shares = round_floats_to_100(shares, 2)
                case_df.loc[(case_df['calendar_year'] == yr) & (case_df['reg_class_id'] == reg_class), 'sales_share_of_regclass'] = new_shares

        fleet_context_df = pd.concat([fleet_context_df, case_df], axis=0, ignore_index=True)

    # work on fuel prices
    fuel_context_df = pd.DataFrame()
    for aeo_case in settings.aeo_cases:
        print(f'Working on context gasoline prices for the AEO {aeo_case}')
        case_df = return_df(aeo_petroleum_fuel_prices_table, 'full name', aeo_case)
        aeo_table_obj = GetContext(case_df)
        gasoline_retail_prices = aeo_table_obj.select_table_rows('full name', 'Price Components: Motor Gasoline: End-User Price')
        # the above selects all rows but all we want is the true end user price row, so now get that alone
        gasoline_retail_prices = gasoline_retail_prices.loc[gasoline_retail_prices['full name'] == 'Price Components: Motor Gasoline: End-User Price', :]
    
        gasoline_distribution = aeo_table_obj.select_table_rows('full name', 'Price Components: Motor Gasoline: End-User Price: Distribution Costs')
    
        gasoline_wholesale = aeo_table_obj.select_table_rows('full name', 'Price Components: Motor Gasoline: End-User Price: Wholesale Price')
    
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
        case_df = return_df(aeo_electricity_fuel_prices_table, 'full name', aeo_case)
        aeo_table_obj = GetContext(case_df)
        electricity_prices_residential = aeo_table_obj.select_table_rows('full name', 'Electricity: End-Use Prices: Residential')
        electricity_prices_allsecavg = aeo_table_obj.select_table_rows('full name', 'Electricity: End-Use Prices: All Sectors Average')
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

        case_prices = pd.concat([gasoline_prices, electricity_prices], axis=0, ignore_index=True)
        # concatenate the fuel prices into one DF
        fuel_context_df = pd.concat([fuel_context_df, case_prices], ignore_index=True, axis=0)

    # work on deflators
    print('Working on GDP price deflators.')
    deflators = return_df(deflators_table, 'Unnamed: 1', 'Gross domestic product')
    deflators = melt_df(deflators, 'Unnamed: 1', 'price_deflator', 'Unnamed: 1')
    deflators['price_deflator'] = deflators['price_deflator'].astype(float)
    basis_factor_df = pd.DataFrame(deflators.loc[deflators['calendar_year'] == usd_basis, 'price_deflator']).reset_index(drop=True)
    basis_factor = basis_factor_df.at[0, 'price_deflator']
    deflators.insert(len(deflators.columns),
                     'adjustment_factor',
                     basis_factor / deflators['price_deflator'])

    print('Working on CPIU price deflators.')
    cpi_table.rename(columns={'Year': 'calendar_year', 'Annual': 'price_deflator'}, inplace=True)
    basis_factor_df = pd.DataFrame(cpi_table.loc[cpi_table['calendar_year'] == usd_basis, 'price_deflator']).reset_index(drop=True)
    basis_factor = basis_factor_df.at[0, 'price_deflator']
    cpi_table.insert(len(cpi_table.columns),
                     'adjustment_factor',
                     basis_factor / cpi_table['price_deflator'])

    # print to output files
    path_of_run_folder = settings.path_outputs / f'{start_time_readable}_run'
    path_of_run_folder.mkdir(exist_ok=False)
    print(f'Saving output files to {path_of_run_folder}')

    fleet_context_df.to_csv(path_of_run_folder / settings.vehicles_context_template, index=False)
    fuel_context_df.to_csv(path_of_run_folder / settings.fuels_context_template, index=False)
    deflators.to_csv(path_of_run_folder / settings.price_deflators_template, index=False)
    deflators.to_csv(settings.path_cwd / f'usepa_omega2_preproc/bea_tables/implicit_price_deflators_{usd_basis}.csv', index=False)
    cpi_table.to_csv(path_of_run_folder / settings.cpiu_deflators_template, index=False)


if __name__ == '__main__':
    main()
