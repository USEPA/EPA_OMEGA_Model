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

    Args:
        path: The path to input files.
        table_name: The AEO table to read.
        skiprows: The number of rows to be skipped when reading the AEO table.
    
    Returns:
        A DataFrame of the table_name.
        
    """
    # Note that "error_bad_lines" is deprecated in newer pandas versions; change to "on_bad_lines='skip'" with newer pandas
    # return pd.read_csv(path / table_name, skiprows=skiprows, error_bad_lines=False).dropna()
    return pd.read_csv(path / table_name, skiprows=skiprows, on_bad_lines='skip').dropna()


def return_df(table, col_id, case_id, version_id):
    """
    
    Args:
        table: A DataFrame of the table_name passed thru the read_table function.
        col_id (string): The column identifier where case_id data can be found.
        case_id (string): The string identifier (e.g., the string_id such as Reference case, High Oil Price, etc.).
        version_id (string): The AEO version info that might need to be scrubbed from col_id data (e.g., 'AEO2022').
    
    Returns:
        A DataFrame consisting of only the data for the given AEO case; the name of the AEO case is also removed from the 'full name' column entries.
        
    """
    table[col_id].replace(f'{version_id} {case_id}', case_id, regex=True, inplace=True)
    df_return = pd.DataFrame(table.loc[table[col_id].str.endswith(f'{case_id}'), :]).reset_index(drop=True)
    df_return.replace({col_id: f': {case_id}'}, {col_id: ''}, regex=True, inplace=True)
    return df_return


def melt_df(df, id_col, value_name, drop_col=None):
    """
    
    A function to melt the passed DataFrame from short-and-wide (data for each year in separate columns) to long-and-narrow (data for each year
    in a single column).
    
    Args:
        df: The passed DataFrame.
        id_col: The identifying column of data around which values will be melted.
        value_name: The name for the resultant data column.
        drop_col: The name of any columns to be dropped after melt.
    
    Returns:
        The melted DataFrame with a column of data named value_name.
        
    """
    df = pd.melt(df, id_vars=[id_col], value_vars=[col for col in df.columns if '20' in col], var_name='calendar_year', value_name=value_name)
    df['calendar_year'] = df['calendar_year'].astype(int)
    if drop_col:
        df.drop(columns=drop_col, inplace=True)
    return df


def new_metric(df, id_column, new_metric, new_metric_entry, *id_words):
    """
    
    Args:
        df: DataFrame in which new entries (new_metric_entry) are needed for a new_metric.
        id_column: The column of data that contains necessary data to determine the new_metric_entry.
        new_metric: The name of the new_metric that is to be populated.
        new_metric_entry: The new entry value to be populated into the new_metric column.
        id_words: The words to look for in the id_column to determine what the new_metric_entry should be.
    
    Returns:
        The passed DataFrame with the new_metric column populated with the new_metric_entries.
        
    """
    for index, row in df.iterrows():
        for id_word in id_words:
            name = row[f'{id_column}']
            if name.__contains__(f'{id_word}'):
                df.at[index, f'{new_metric}'] = f'{new_metric_entry}'
            else:
                pass
    return df


def error_gen(actual, rounded):
    """

    Args:
        actual:
        rounded:

    Returns:

    """
    divisor = np.sqrt(1.0 if actual < 1.0 else actual)
    return abs(rounded - actual) ** 2 / divisor


def round_to_100(percents):
    """

    This function is not being used and has not been tested.

    Args:
        percents: A list of percentages to be rounded.

    Returns:
        A list of percents rounded to integers and summing to 100.

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

    Args:
        percents: A list of percentages to be rounded.
        decimals: The number of decimal places in rounded values.

    Returns:
        A list of percents rounded to 'decimals' number of decimal places and summing to 100.

    """
    # if not np.isclose(sum(percents), 100):
    #     raise ValueError
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
    """

    A class to extract specific data values from AEO tables.

    """
    def __init__(self, table):
        """

        Args:
            table: A DataFrame of the table being worked on.

        """
        self.table = table

    def aeo_year(self):
        """

        Returns:
            The year of the report, e.g., 'AEO2020'.

        """
        a_loc = self.table.at[0, 'api key'].find('A')
        return self.table.at[0, 'api key'][a_loc: a_loc + 7]

    def aeo_dollars(self):
        """

        Return:
            The dollar basis of the AEO report.

        """
        usd_loc = self.table.at[0, 'units'].find(' $')
        return int(self.table.at[0, 'units'][0: usd_loc])

    def select_table_rows(self, col_id, arg, desired_final_year, replace=None):
        """

        Args:
            col_id: The column of data in which to look for arg.
            arg: The identifying string used to determine what rows to be included in the returned DataFrame.
            desired_final_year: The value of the create_results_thru variable in the SetInputs class.
            replace: Any string elements that are to be removed from the entries containing 'metric'.

        Returns:
            A DataFrame of those AEO table rows containing arg within the col_id column.
        """
        df_rows = pd.DataFrame()
        df_rows = pd.concat([df_rows, self.table.loc[self.table[col_id].str.contains(arg), :]],
                            ignore_index=True)
        if replace:
            df_rows.replace({col_id: replace}, {col_id: ''}, regex=True, inplace=True)
        df_rows = df_rows.iloc[:, :-1]

        # get growth in case results are needed for years > aeo table max years
        # growth_col_name = df_rows.columns.tolist()[-1]
        # df_rows.rename(columns={growth_col_name: 'growth_rate'}, inplace=True)

        # clean data so that growth rates are floats
        # df_rows['growth_rate'].replace({'- -': '0%'}, inplace=True)
        # df_rows = df_rows.join(df_rows['growth_rate'].str.split('%', expand=True))
        # df_rows.drop(columns=['growth_rate', 1], inplace=True)
        # df_rows.rename(columns={0: 'growth_rate'}, inplace=True)
        # df_rows['growth_rate'] = pd.to_numeric(df_rows['growth_rate'])

        # growth_df = df_rows.iloc[:, -1:]
        final_aeo_year = int(df_rows.columns.tolist()[-1])

        # grow results if necessary
        # if desired_final_year > final_aeo_year:
        #     for yr in range(final_aeo_year + 1, desired_final_year + 1):
        #         prior_yr = yr - 1
        #         df_rows.insert(len(df_rows.columns), f'{yr}', (df_rows['growth_rate'] / 100) * df_rows[f'{prior_yr}'] + df_rows[f'{prior_yr}'])

        if desired_final_year > final_aeo_year:
            for yr in range(final_aeo_year + 1, desired_final_year + 1):
                prior_yr, two_prior_yr = yr - 1, yr - 2
                df_rows.insert(len(df_rows.columns), f'{yr}', ((df_rows[f'{prior_yr}'] - df_rows[f'{two_prior_yr}']) / df_rows[f'{two_prior_yr}']) * df_rows[f'{prior_yr}'] + df_rows[f'{prior_yr}'])

        # df_rows.drop(columns=['growth_rate'], inplace=True)

        return df_rows


def add_body_style(df):

    body_style_dict = {
        'Minicompact': 'sedan_wagon',
        'Subcompact': 'sedan_wagon',
        'Compact': 'sedan_wagon',
        'Midsize': 'sedan_wagon',
        'Large': 'sedan_wagon',
        'Two Seater': 'sedan_wagon',
        'Small Crossover': 'cuv_suv_van',
        'Large Crossover': 'cuv_suv_van',
        'Small Van': 'cuv_suv_van',
        'Large Van': 'cuv_suv_van',
        'Small Utility': 'cuv_suv_van',
        'Large Utility': 'cuv_suv_van',
        'Small Pickup': 'pickup',
        'Large Pickup': 'pickup',
    }
    df.insert(df.columns.get_loc('context_size_class') + 1, 'body_style', '')
    context_size_classes = pd.Series(df['context_size_class'].unique())
    for context_size_class in context_size_classes:
        df.loc[df['context_size_class'] == context_size_class, 'body_style'] = body_style_dict[context_size_class]

    return df


def calc_sales_share_of_body_style(df):

    body_styles = pd.Series(df['body_style'].unique())
    calendar_years = pd.Series(df['calendar_year'].unique())
    df.insert(df.columns.get_loc('sales_share_of_regclass'), 'sales_share_of_body_style', 0)
    for calendar_year in calendar_years:
        for body_style in body_styles:
            body_style_sales = df.loc[(df['body_style'] == body_style) & (df['calendar_year'] == calendar_year), 'sales'].sum()
            df.loc[(df['body_style'] == body_style) & (df['calendar_year'] == calendar_year), 'sales_share_of_body_style'] \
                = df.loc[(df['body_style'] == body_style) & (df['calendar_year'] == calendar_year), 'sales'] / body_style_sales

    df['sales_share_of_body_style'] = df['sales_share_of_body_style'] * 100

    return df


class SetInputs:

    def __init__(self):

        # set paths
        self.path_preproc = Path(__file__).parent
        self.path_project = self.path_preproc.parent
        self.path_aeo_tables = self.path_preproc / 'aeo_tables'
        self.path_bea_tables = self.path_preproc / 'bea_tables'
        self.path_outputs = self.path_preproc / 'output_context_aeo'
        try:
            self.path_outputs.mkdir(exist_ok=True)
        except:
            pass
        self.path_input_templates = self.path_project / 'omega_model/test_inputs'

        # specify templates to use
        self.vehicles_context_template = 'context_new_vehicle_market.csv'
        self.fuels_context_template = 'context_fuel_prices.csv'
        self.price_deflators_template = 'implicit_price_deflators.csv'
        self.cpiu_deflators_template = 'cpi_price_deflators.csv'

        # some run settings
        self.create_results_thru = 2060
        self.aeo_cases = ['Reference case', 'High oil price', 'Low oil price']
        self.gasoline_upstream = 2478  # 77 FR 63181
        self.electricity_upstream = 534  # 77 FR 63182

        # name the aeo table(s) being used
        self.aeo_class_attributes_table_file = 'Summary_of_New_Light-Duty_Vehicle_Size_Class_Attributes.csv'
        self.aeo_sales_table_file = 'Light-Duty_Vehicle_Sales_by_Technology_Type.csv'
        self.aeo_petroleum_fuel_prices_table_file = 'Components_of_Selected_Petroleum_Product_Prices.csv'
        self.aeo_electricity_fuel_prices_table_file = 'Electricity_Supply_Disposition_Prices_and_Emissions.csv'
        self.aeo_vehicle_prices_table_file = 'New_Light-Duty_Vehicle_Prices.csv'

        # and the bea table(s) being used
        self.deflators_table_file = 'Table_1.1.9_ImplicitPriceDeflators.csv'
        self.cpiu_table_file = 'SeriesReport.csv'


def main():

    settings = SetInputs()
    start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

    deflators_table = read_table(settings.path_bea_tables, settings.deflators_table_file)
    cpi_table = pd.read_csv(settings.path_bea_tables / settings.cpiu_table_file, skiprows=11, usecols=[0, 1])

    fleet_context_df = pd.DataFrame()
    fuel_context_df = pd.DataFrame()

    for path_aeo_version in settings.path_aeo_tables.iterdir():

        aeo_version = path_aeo_version.stem
        # read files as DataFrames
        aeo_class_attributes_table = read_table(path_aeo_version, settings.aeo_class_attributes_table_file)
        aeo_sales_table = read_table(path_aeo_version, settings.aeo_sales_table_file)
        aeo_petroleum_fuel_prices_table = read_table(path_aeo_version, settings.aeo_petroleum_fuel_prices_table_file)
        aeo_electricity_fuel_prices_table = read_table(path_aeo_version, settings.aeo_electricity_fuel_prices_table_file)
        aeo_vehicle_prices_table = read_table(path_aeo_version, settings.aeo_vehicle_prices_table_file)

        # work on fuel prices
        for aeo_case in settings.aeo_cases:
            # print(f'Working on context gasoline prices for the AEO {aeo_case}')
            case_df = return_df(aeo_petroleum_fuel_prices_table, 'full name', aeo_case, aeo_version)
            aeo_table_obj = GetContext(case_df)

            usd_basis = aeo_table_obj.aeo_dollars()

            aeo_to_omega_dict = {'Motor Gasoline': 'pump gasoline',
                                 'Diesel': 'pump diesel'}
            case_prices = pd.DataFrame()
            for liquid_fuel in ['Motor Gasoline', 'Diesel']:
                print(f'Working on {liquid_fuel} prices for the AEO {aeo_case}')

                omega_fuel_id = aeo_to_omega_dict[liquid_fuel]
                retail_prices = aeo_table_obj.select_table_rows('full name', f'Price Components: {liquid_fuel}: End-User Price', settings.create_results_thru)
                retail_prices = retail_prices.loc[retail_prices['full name'] == f'Price Components: {liquid_fuel}: End-User Price', :]

                distribution = aeo_table_obj.select_table_rows('full name', f'Price Components: {liquid_fuel}: End-User Price: Distribution Costs', settings.create_results_thru)
                wholesale = aeo_table_obj.select_table_rows('full name', f'Price Components: {liquid_fuel}: End-User Price: Wholesale Price', settings.create_results_thru)

                retail_prices = melt_df(retail_prices, 'full name', 'retail_dollars_per_unit', 'full name')
                retail_prices.insert(0, 'fuel_id', omega_fuel_id)
                retail_prices.insert(0, 'case_id', f'{aeo_case}')
                retail_prices.insert(0, 'dollar_basis', f'{usd_basis}')
                retail_prices.insert(0, 'context_id', aeo_table_obj.aeo_year())

                distribution = melt_df(distribution, 'full name', 'distribution', 'full name')
                wholesale = melt_df(wholesale, 'full name', 'wholesale', 'full name')

                pretax_prices = retail_prices.copy()
                pretax_prices['pretax_dollars_per_unit'] = distribution['distribution'] + wholesale['wholesale']
                pretax_prices['fuel_id'] = omega_fuel_id

                prices = retail_prices.join(pretax_prices[['pretax_dollars_per_unit']])

                case_prices = pd.concat([case_prices, prices], axis=0, ignore_index=True)

            # gasoline_retail_prices = aeo_table_obj.select_table_rows('full name', 'Price Components: Motor Gasoline: End-User Price', settings.create_results_thru)
            # # the above selects all rows but all we want is the true end user price row, so now get that alone
            # gasoline_retail_prices = gasoline_retail_prices.loc[gasoline_retail_prices['full name'] == 'Price Components: Motor Gasoline: End-User Price', :]
            #
            # gasoline_distribution = aeo_table_obj.select_table_rows('full name', 'Price Components: Motor Gasoline: End-User Price: Distribution Costs', settings.create_results_thru)
            #
            # gasoline_wholesale = aeo_table_obj.select_table_rows('full name', 'Price Components: Motor Gasoline: End-User Price: Wholesale Price', settings.create_results_thru)
            #
            # gasoline_retail_prices = melt_df(gasoline_retail_prices, 'full name', 'retail_dollars_per_unit', 'full name')
            # gasoline_retail_prices.insert(0, 'fuel_id', 'pump gasoline')
            # gasoline_retail_prices.insert(0, 'case_id', f'{aeo_case}')
            # gasoline_retail_prices.insert(0, 'dollar_basis', f'{usd_basis}')
            # gasoline_retail_prices.insert(0, 'context_id', aeo_table_obj.aeo_year())
            #
            # gasoline_distribution = melt_df(gasoline_distribution, 'full name', 'gasoline_distribution', 'full name')
            # gasoline_wholesale = melt_df(gasoline_wholesale, 'full name', 'gasoline_wholesale', 'full name')
            #
            # gasoline_pretax_prices = gasoline_retail_prices.copy()
            # gasoline_pretax_prices['pretax_dollars_per_unit'] = gasoline_distribution['gasoline_distribution'] \
            #                                                     + gasoline_wholesale['gasoline_wholesale']
            # gasoline_pretax_prices['fuel_id'] = 'pump gasoline'
            #
            # gasoline_prices = gasoline_retail_prices.join(gasoline_pretax_prices[['pretax_dollars_per_unit']])

            # electricity prices
            case_df = return_df(aeo_electricity_fuel_prices_table, 'full name', aeo_case, aeo_version)
            aeo_table_obj = GetContext(case_df)
            electricity_prices_residential = aeo_table_obj.select_table_rows('full name', 'Electricity: End-Use Prices: Residential', settings.create_results_thru)
            electricity_prices_allsecavg = aeo_table_obj.select_table_rows('full name', 'Electricity: End-Use Prices: All Sectors Average', settings.create_results_thru)
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
                df.insert(0, 'dollar_basis', f'{usd_basis}')
                df.insert(0, 'context_id', aeo_table_obj.aeo_year())

            electricity_prices = electricity_prices_residential.join(electricity_prices_allsecavg[['pretax_dollars_per_unit']])

            case_prices = pd.concat([case_prices, electricity_prices], axis=0, ignore_index=True)
            # case_prices = pd.concat([gasoline_prices, electricity_prices], axis=0, ignore_index=True)
            # concatenate the fuel prices into one DF
            fuel_context_df = pd.concat([fuel_context_df, case_prices], ignore_index=True, axis=0)

            print(f'Working on market context vehicle attributes for the AEO {aeo_case}')
            attribute = dict()
            attributes_df = return_df(aeo_class_attributes_table, 'full name', aeo_case, aeo_version)
            aeo_table_obj = GetContext(attributes_df)

            attribute['HP'] = aeo_table_obj.select_table_rows('full name', 'Horsepower', settings.create_results_thru, replace='New Vehicle Attributes: Horsepower: Conventional ')
            attribute['lb'] = aeo_table_obj.select_table_rows('full name', 'Weight', settings.create_results_thru, replace='New Vehicle Attributes: Weight: Conventional ')
            attribute['percent'] = aeo_table_obj.select_table_rows('full name', 'Sales Shares', settings.create_results_thru, replace='New Vehicle Attributes: Sales Shares: ')
            attribute['mpg_conventional'] = aeo_table_obj.select_table_rows('full name', 'EPA Efficiency', settings.create_results_thru, replace='New Vehicle Attributes: EPA Efficiency: Conventional ')
            attribute['mpg_alternative'] = aeo_table_obj.select_table_rows('full name', 'Fuel Efficiency', settings.create_results_thru, replace='New Vehicle Attributes: Fuel Efficiency: Alternative-Fuel ')
            attribute['ratio'] = aeo_table_obj.select_table_rows('full name', 'Degradation Factors', settings.create_results_thru, replace='New Vehicle Attributes: Degradation Factors: ')

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
            aeo_veh_context.insert(0, 'dollar_basis', f'{usd_basis}')
            aeo_veh_context.insert(0, 'context_id', aeo_table_obj.aeo_year())

            # work on sales
            sales_df = return_df(aeo_sales_table, 'full name', aeo_case, aeo_version)
            aeo_table_obj = GetContext(sales_df)
            print(f'Working on market context vehicle sales for the AEO {aeo_case}')
            sales_fleet = aeo_table_obj.select_table_rows('full name', 'Light-Duty Vehicle Sales: Total Vehicles Sales', settings.create_results_thru)
            sales_car = aeo_table_obj.select_table_rows('full name', 'Light-Duty Vehicle Sales: Total New Car', settings.create_results_thru)
            sales_truck = aeo_table_obj.select_table_rows('full name', 'Light-Duty Vehicle Sales: Total New Truck', settings.create_results_thru)

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
            for year in range(aeo_veh_context['calendar_year'].values.min(), aeo_veh_context['calendar_year'].values.max() + 1):
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
            prices_df = return_df(aeo_vehicle_prices_table, 'full name', aeo_case, aeo_version)
            aeo_table_obj = GetContext(prices_df)
            print(f'Working on market context vehicle prices for the AEO {aeo_case}')
            vehicle_prices = dict()
            vehicle_prices['gasoline'] = aeo_table_obj.select_table_rows('full name', 'Gasoline: ', settings.create_results_thru, replace='New Light-Duty Vehicle Prices: Gasoline: ')
            vehicle_prices['electric'] = aeo_table_obj.select_table_rows('full name', '300 Mile Electric Vehicle: ', settings.create_results_thru, replace='New Light-Duty Vehicle Prices: 300 Mile Electric Vehicle: ')

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

            case_df = add_body_style(case_df)
            calc_sales_share_of_body_style(case_df)

            # lastly, round all the sales shares and force sum to 100
            for yr in range(case_df['calendar_year'].values.min(), case_df['calendar_year'].values.max() + 1):
                shares = pd.Series(case_df.loc[case_df['calendar_year'] == yr, 'sales_share_of_total']).tolist()
                new_shares = round_floats_to_100(shares, 2)
                case_df.loc[case_df['calendar_year'] == yr, 'sales_share_of_total'] = new_shares
                for reg_class in ['car', 'truck']:
                    shares = pd.Series(case_df.loc[(case_df['calendar_year'] == yr) & (case_df['reg_class_id'] == reg_class), 'sales_share_of_regclass']).tolist()
                    new_shares = round_floats_to_100(shares, 2)
                    case_df.loc[(case_df['calendar_year'] == yr) & (case_df['reg_class_id'] == reg_class), 'sales_share_of_regclass'] = new_shares
                for body_style in ['sedan_wagon', 'cuv_suv_van', 'pickup']:
                    shares = pd.Series(case_df.loc[(case_df['calendar_year'] == yr) & (
                                case_df['body_style'] == body_style), 'sales_share_of_body_style']).tolist()
                    new_shares = round_floats_to_100(shares, 2)
                    case_df.loc[(case_df['calendar_year'] == yr) & (
                                case_df['body_style'] == body_style), 'sales_share_of_body_style'] = new_shares

            fleet_context_df = pd.concat([fleet_context_df, case_df], axis=0, ignore_index=True)

    # work on deflators
    print('Working on GDP price deflators.')
    deflators = return_df(deflators_table, 'Unnamed: 1', 'Gross domestic product', aeo_version)
    deflators = melt_df(deflators, 'Unnamed: 1', 'price_deflator', 'Unnamed: 1')
    deflators['price_deflator'] = deflators['price_deflator'].astype(float)
    # basis_factor_df = pd.DataFrame(deflators.loc[deflators['calendar_year'] == usd_basis, 'price_deflator']).reset_index(drop=True)
    # basis_factor = basis_factor_df.at[0, 'price_deflator']
    # deflators.insert(len(deflators.columns),
    #                  'adjustment_factor',
    #                  basis_factor / deflators['price_deflator'])

    print('Working on CPIU price deflators.')
    cpi_table.rename(columns={'Year': 'calendar_year', 'Annual': 'price_deflator'}, inplace=True)
    # basis_factor_df = pd.DataFrame(cpi_table.loc[cpi_table['calendar_year'] == usd_basis, 'price_deflator']).reset_index(drop=True)
    # basis_factor = basis_factor_df.at[0, 'price_deflator']
    # cpi_table.insert(len(cpi_table.columns),
    #                  'adjustment_factor',
    #                  basis_factor / cpi_table['price_deflator'])

    # print to output files
    path_of_run_folder = settings.path_outputs / f'{start_time_readable}_run'
    path_of_run_folder.mkdir(exist_ok=False)
    print(f'Saving output files to {path_of_run_folder}')

    fleet_context_df.to_csv(path_of_run_folder / settings.vehicles_context_template, index=False)
    fuel_context_df.to_csv(path_of_run_folder / settings.fuels_context_template, index=False)
    deflators.to_csv(path_of_run_folder / settings.price_deflators_template, index=False)
    cpi_table.to_csv(path_of_run_folder / settings.cpiu_deflators_template, index=False)


if __name__ == '__main__':
    main()
