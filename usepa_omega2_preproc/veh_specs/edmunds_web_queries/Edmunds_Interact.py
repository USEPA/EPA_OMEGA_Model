from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

import os
import time
import pandas as pd
# pd.options.mode.chained_assignment = None  # default='warn'
import math
from bs4 import BeautifulSoup
import numpy as np

# import signal

global super_trim_url_list
super_trim_url_list = []

class HTMLTableParser:
    def get_html_table(self, soup, trim_group, errorflag_1, errorflag_2, errorflag_3):
        full_dataframe_list = [self.parse_html_table(table, trim_group, errorflag_1, errorflag_2, errorflag_3) \
                               for table in soup.find_all('table') \
                               if len(table.find_all('tr')) > 1 and pd.Series(table.get('class')).str.cat(sep=' ') \
                               != 'features-table table-sm mt-lg-3 w-100-up-md']  # table['id']
        return full_dataframe_list

    def parse_html_table(self, table, trim_group, errorflag_1, errorflag_2, errorflag_3):
        n_columns = 0
        n_rows = 0
        column_names = []

        # Find number of rows and columns
        # we also find the column titles if we can
        for row in table.find_all('tr'):

            # Determine the number of rows in the table
            td_tags = row.find_all('td')
            if len(td_tags) > 0:
                n_rows += 1
                if n_columns == 0:
                    # Set the number of columns for our table
                    n_columns = len(td_tags)

            # Handle column names if we find them
            th_tags = row.find_all('th')
            if len(th_tags) > 0 and len(column_names) == 0:
                for th in th_tags:
                    column_names.append(th.get_text())

        # Safeguard on Column Titles
        column_names_length = len(column_names)
        if len(column_names) > 0 and column_names_length != n_columns:
            raise Exception("Column titles do not match the number of columns")

        columns = column_names if len(column_names) > 0 else range(0, n_columns)
        df = pd.DataFrame(columns=columns, index=range(0, n_rows))
        row_marker = 0
        for row in table.find_all('tr'):
            column_marker = 0
            columns = row.find_all('td')
            for column_count in range(0, len(columns)):
                column = columns[column_count]
                bool_check_true = column.find_all('span', {'class': 'feature-container bool-true'})
                bool_check_false = column.find_all('span', {'class': 'feature-container bool-false'})
                if len(bool_check_true) > 0:
                    df.iat[row_marker, column_marker] = bool(True)
                elif len(bool_check_false) > 0:
                    df.iat[row_marker, column_marker] = bool(False)
                else:
                    df.iat[row_marker, column_marker] = column.get_text().strip()
                column_marker += 1
            if len(columns) > 0:
                row_marker += 1

        return df

def merge_trim_options(tmp_raw_table0, _menu_columns, df_options, option_str):
    tmp_raw_table = tmp_raw_table0.copy(deep=True)
    _row_drop_start = 0
    _row_option_str_init = 0
    for k in range(len(df_options)):
        _row = df_options.index[k]
        _option_spec_str = tmp_raw_table['Specifications'][_row].split(' ' + option_str)
        _option_spec = _option_spec_str[0]
        if (_option_spec in ['All season', 'all season', 'painted alloy']) or len(_option_spec) == 0:
            continue
        else:
            if k == 0 or _row_option_str_init == 0:
                tmp_raw_table['Specifications'][_row] = option_str
                _option_str_row = _row
                if k>0 and _row_option_str_init == 0:
                    _row_drop_start = k
                    _row_option_str_init = k
                elif k == 0:
                    _row_option_str_init  = 1

            for _index_col in range(_menu_columns):
                trim_col = tmp_raw_table.columns[_index_col+2]
                ioption = str(tmp_raw_table[trim_col][_row])
                if ioption.lower() == 'yes':
                    tmp_raw_table[trim_col][_option_str_row] = _option_spec
                elif ioption.lower() == 'no' and tmp_raw_table[trim_col][_option_str_row] == 'no':
                    tmp_raw_table[trim_col][_option_str_row] = np.nan
                if k > _row_drop_start: tmp_raw_table[trim_col][_row] = np.nan
            # if k > _row_drop_start:
            #     # tmp_raw_table =[trim_col][_row] = ''
            #     tmp_raw_table = tmp_raw_table.drop(index=_row)

    return tmp_raw_table

def drop_merged_option(tmp_raw_table, _menu_columns):
    if _menu_columns == 1:
        tmp_raw_table = tmp_raw_table.dropna(how='all', subset=[tmp_raw_table.columns[2]])
    elif _menu_columns == 2:
        tmp_raw_table = tmp_raw_table.dropna(how='all', subset=[tmp_raw_table.columns[2], tmp_raw_table.columns[3]])
    elif _menu_columns == 3:
        tmp_raw_table = tmp_raw_table.dropna(how='all', subset=[tmp_raw_table.columns[2], tmp_raw_table.columns[3], tmp_raw_table.columns[4]])

    tmp_raw_table = tmp_raw_table.reset_index(drop=True)

    return tmp_raw_table


def Edmunds_Interact(url):
    max_attempts = 10
    max_time = 60
    _max_trim_groups_count = 20 # for 4K resolution monitor, set 10 for low resolution monitors like 1080K
    _max_trim_buttons =  60     # for 4K resolution monitor, set 33 (10 x 3 menu columns) for 1080K monitor

    trim_options = []
    trim_dropdown_buttons_xpath = "//button[@data-test='select-menu']"  # The xpath for the trim selection drop-down button, which is repeated in 1-3 columns and multiple rows for each table
    trim_select_buttons_xpath = "//div[@class='dropdown-menu show']//button[@class='dropdown-item']"

    for geturl_attempt in range(0, max_attempts):
        print('URL Attempt ' + str(geturl_attempt + 1))
        wait_time = 45
        chromedriver = 'chromedriver.exe'

        os.environ["webdriver.chrome.driver"] = chromedriver
        chromeOptions = Options()
        # caps = DesiredCapabilities().CHROME
        # caps["pageLoadStrategy"] = "none"
        # chromeOptions.add_argument("--kiosk")  # for Mac/Linux OS
        chromeOptions.add_argument("--start-maximized")
        # driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions, desired_capabilities=caps)
        driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
        try:
            driver.set_page_load_timeout(wait_time)
            driver.implicitly_wait(5)
            time.sleep(1)
            driver.get(url)
            # find and click main button to reveal drop-down menu
            menus = driver.find_elements_by_xpath(trim_dropdown_buttons_xpath)
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, trim_dropdown_buttons_xpath)))

            time.sleep(1.5)
            menus[0].click() # click the first dropdown menu button. Assumes all menus contain the same trim list.
            # find trim buttons in drop-down menu
            trim_buttons = driver.find_elements_by_xpath(trim_select_buttons_xpath)
            WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))

            _trim_start = 0
            _trim_buttons = len(trim_buttons)
            if _trim_buttons > _max_trim_buttons:
                _trim_buttons = _max_trim_buttons
                super_trim_url_list.append(url)

            for i, trim in zip(range(_trim_buttons), trim_buttons): trim_options.append(trim.text)
            menus[0].click()  # close the dropdown menu.
            break
        except (NoSuchElementException, TimeoutException, UnboundLocalError):
            driver.quit()
            pass

    try:
        total_trims = len(trim_buttons)
    except UnboundLocalError:
        if geturl_attempt + 1 == max_attempts:
            return ('N', 'READIN_ERROR')
    # trim_group_length = 1
    #
    # if total_trims >= 2:
    #     #menu2 = driver.find_elements_by_xpath(trim_dropdown_buttons_xpath)[1]
    #     # dropdown2 = Select(menu2)
    #     trim_group_length = 2
    # if total_trims >= 3:
    #     #menu3 = driver.find_elements_by_xpath(trim_dropdown_buttons_xpath)[2]
    #     # dropdown3 = Select(menu3)
    #     trim_group_length = 3

    trim_groups_count = math.ceil(total_trims / 3)  # Number of trim groups (in groups of 3, add one if only 1-2 trims left)
    last_group_count = total_trims % 3  # Length of last group
    readin_check = pd.Series(np.zeros(total_trims), name='Readin_Error').replace(0, '')
    if trim_groups_count > _max_trim_groups_count: trim_groups_count = _max_trim_groups_count
    for table_list_count in range(0, 1):
        if table_list_count == 0:
            save_name = 'pandas list.csv'
        else:
            save_name = 'soup list.csv'
        for trim_group in range(0, trim_groups_count):
            _index = trim_group
            errorflag_1 = 0
            errorflag_2 = 0
            errorflag_3 = 0
            trims_text = []
            try:
                del df_tmp  # important_tables
            except NameError:
                pass
            if trim_group == trim_groups_count - 1 and last_group_count != 0:  # Last (or only) trim group and less than 3 entries
                trims = pd.Series(range(last_group_count)) + trim_groups_count * trim_group
            else:
                trims = pd.Series(range(trim_groups_count)) + trim_groups_count * trim_group
            _menu_columns = len(trims)
            if _menu_columns < total_trims and trim_groups_count == 1: _menu_columns = total_trims
            if (_index < (trim_groups_count-1)) and total_trims >= 3:
                _menu_columns= 3
            else:
                _menu_columns = total_trims % 3
                if _menu_columns == 0: _menu_columns = 3

            if _menu_columns > 0:
                try:
                    for i in range(_menu_columns):
                        WebDriverWait(driver, 60).until(
                            EC.element_to_be_clickable((By.XPATH, trim_dropdown_buttons_xpath)))
                        time.sleep(2)
                        menus[i].click()
                        trims_text.append(trim_options[_index * 3 + i])
                        option_text = trims_text[i]
                        element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))
                        # dropdown_item = driver.find_element_by_xpath("//div[@class='dropdown-menu show']//button[text()='{}']".format(str(option_text)))
                        dropdown_item = driver.find_elements_by_xpath(trim_select_buttons_xpath)[_index * 3 + i]
                        actions = ActionChains(driver)
                        actions.move_to_element(dropdown_item).click().perform()
                        actions.reset_actions()
                except TimeoutException:
                    if i == 0: errorflag_1 = 1
                    if i == 1: errorflag_2 = 1
                    if i == 2: errorflag_3 = 1
                    readin_check[trims[i]] = 'READIN_ERROR'
            #     try:
            #         menus[0].click()
            #         # Choose first option
            #         element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))
            #         driver.find_elements_by_xpath(trim_select_buttons_xpath)[_index * 3 + 0].click()
            # #     except TimeoutException:
            #         errorflag_1 = 1
            #         readin_check[trims[0]] = 'READIN_ERROR'
            # if _menu_columns >= 2:  # Choose second option (if applicable)
            #     try:
            #         menus[1].click()
            #         # Choose second option
            #         element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))
            #         driver.find_elements_by_xpath(trim_select_buttons_xpath)[_index * 3 + 1].click()
            #     except TimeoutException:
            #         errorflag_2 = 1
            #         readin_check[trims[1]] = 'READIN_ERROR'
            # if _menu_columns >= 3:  # Choose third option (if applicable)
            #     try:
            #         menus[2].click()
            #         # Choose third option
            #         element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))
            #         driver.find_elements_by_xpath(trim_select_buttons_xpath)[_index * 3 + 2].click()
            #     except TimeoutException:
            #         errorflag_3 = 1
            #         readin_check[trims[2]] = 'READIN_ERROR'
            if table_list_count == 0:
                time.sleep(1)
                table_list = pd.read_html(driver.page_source, header=0)
            else:
                soup = BeautifulSoup(driver.page_source, "lxml")
                hp = HTMLTableParser()
                table_list = hp.get_html_table(soup, trim_group, errorflag_1, errorflag_2, errorflag_3)
            # table_list[16].to_csv(
            #     '/Users/Brandon/PycharmProjects/Web_Scraping' + '//' + str(trim_group) + ' ' + save_name, index=False)
            num_table_list = len(table_list)
            if len(table_list[num_table_list-1]) < 1:
                del table_list[num_table_list-1]
                num_table_list = num_table_list-1
            for table_count in range(0, len(table_list)):
                # if table_count == 12:
                #     print(raw_table)
                if table_list_count == 0 and len(table_list[table_count]) > 0:
                    table_check = 1
                    raw_table = table_list[table_count].reset_index(drop=True)
                elif table_list_count == 1:
                    table_check = 1
                    raw_table = table_list[table_count].reset_index(drop=True)
                else:
                    table_check = 0
                    pass
                if table_check == 1:
                    table_tag = raw_table.columns[0]

                    if len(raw_table) > 0 and isinstance(raw_table, pd.DataFrame) and \
                            not ("Highlights" in table_tag) \
                            and table_tag != 'OVERVIEW':
                        raw_table.columns = pd.Series(raw_table.columns).str.strip()

                        # for col_count in range(1, len(raw_table.columns)):
                        #     column = raw_table.columns[col_count]
                        #     msrp = column[column.find('$'):].strip()
                        #     # msrp=msrp.split(" ")[0]; msrp=msrp.strip('$'); msrp=msrp.replace(',', '')
                        #     raw_table = raw_table.rename \
                        #         (columns={column: column[column.rfind(')', 0, column.rfind(')')):column.rfind(')') + 1].strip().replace('  ', '').strip() + ' ' + msrp})
                        # raw_table.to_csv('/Users/Brandon/PycharmProjects/Web_Scraping/'+'Raw Table.csv')
                        if len(table_list[table_count].columns) > (1 + _menu_columns):
                            for i in range(len(table_list[table_count].columns)-1, _menu_columns, -1):
                                del_colname = table_list[table_count].columns[i]
                                table_list[table_count].drop(del_colname, axis=1, inplace=True)
                        try:
                            # important_tables = important_tables.loc[:, ~important_tables.columns.duplicated()]
                            # important_tables = pd.concat([important_tables, raw_table])
                            if table_count == 0: df_tmp = pd.concat([df_tmp, raw_table])
                            raw_table = raw_table.loc[:, ~raw_table.columns.duplicated()]
                            name_category = table_list[table_count].columns[0]
                            for i in range(_menu_columns):
                                table_list[table_count] = table_list[table_count].rename(columns={table_list[table_count].columns[1 + i]: trims_text[i]})
                            tmp_raw_table = table_list[table_count]
                            if tmp_raw_table.columns[0] != 'Category': tmp_raw_table.insert(0, 'Category', '')
                            tmp_raw_table.iloc[0, 0] = name_category
                            tmp_raw_table = tmp_raw_table.rename(columns={name_category: 'Specifications'})
                            front_headrests = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" front headrests")]
                            rear_headrests = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" rear headrests")]
                            months_of_provided_satellite_radio_service = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" Months of provided satellite radio service")]
                            watts_stereo_output = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" watts stereo output")]
                            total_speakers = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" total speakers")]
                            subwoofers = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" subwoofer")]
                            tires = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" tires")]
                            wheels = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" in. wheels")]
                            power_driver_seat = tmp_raw_table[tmp_raw_table["Specifications"].str.contains("power driver seat")]
                            power_passenger_seat = tmp_raw_table[tmp_raw_table["Specifications"].str.contains("power passenger seat")]
                            manual_driver_seat_adjustment = tmp_raw_table[tmp_raw_table["Specifications"].str.contains("manual driver seat adjustment")]
                            manual_passenger_seat_adjustment = tmp_raw_table[tmp_raw_table["Specifications"].str.contains(" manual passenger seat adjustment")]
                            if str(tmp_raw_table['Category'][0]).lower() == 'safety' and (len(front_headrests)  > 0 or len(rear_headrests)  > 0):
                                tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, front_headrests, 'front headrests')
                                tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, rear_headrests, 'rear headrests')
                                tmp_raw_table = drop_merged_option(tmp_raw_table, _menu_columns)
                            if str(tmp_raw_table['Category'][0]).lower() == 'in-car entertainment' and (len(subwoofers)  > 0 or len(total_speakers)  > 0 or len(months_of_provided_satellite_radio_service) > 0 or len(watts_stereo_output) > 0):
                                if len(subwoofers)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, subwoofers, 'subwoofer(s)')
                                if len(total_speakers)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, total_speakers, 'total speakers')
                                if len(months_of_provided_satellite_radio_service) > 0:
                                    tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, months_of_provided_satellite_radio_service, 'Months of provided satellite radio service')
                                if len(watts_stereo_output) > 0: merge_trim_options(tmp_raw_table, _menu_columns, watts_stereo_output, 'watts stereo output')
                                tmp_raw_table = drop_merged_option(tmp_raw_table, _menu_columns)
                            if str(tmp_raw_table['Category'][0]).lower() == 'tires & wheels' and (len(tires)  > 0 or len(wheels) > 0):
                                tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, tires, 'tires')
                                tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, wheels, 'wheels')
                                tmp_raw_table = drop_merged_option(tmp_raw_table, _menu_columns)
                            if str(tmp_raw_table['Category'][0]).lower() == 'front seats' and (len(power_driver_seat)  > 0 or len(power_passenger_seat)  > 0 or len(manual_driver_seat_adjustment) > 0 or len(manual_passenger_seat_adjustment) > 0):
                                if len(power_driver_seat)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, power_driver_seat, 'power driver seat')
                                if len(power_passenger_seat)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, power_passenger_seat, 'power passenger seat')
                                if len(manual_driver_seat_adjustment) > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, manual_driver_seat_adjustment, 'manual driver seat adjustment')
                                if len(manual_passenger_seat_adjustment) > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _menu_columns, manual_passenger_seat_adjustment, 'manual passenger seat adjustment')
                                tmp_raw_table = drop_merged_option(tmp_raw_table, _menu_columns)

                            df_tmp = df_tmp.append(tmp_raw_table, ignore_index=True)
                            df_tmp.fillna('', inplace=True)
                            if table_count == (num_table_list-1):
                                if trim_group == 0:
                                    df = df_tmp
                                else:
                                    df =  pd.merge(df, df_tmp, on=['Category', 'Specifications'])
                                    df = df.drop_duplicates(subset=['Specifications'])
                        except NameError:
                            # important_tables = raw_table
                            df_tmp = table_list[table_count]
                            name_category = table_list[table_count].columns[0]
                            if df_tmp.columns[0] != 'Category': df_tmp.insert(0, 'Category', '')
                            df_tmp.iloc[0, 0] = name_category
                            if df_tmp.columns[1] != 'Specifications': df_tmp = df_tmp.rename(
                                columns={df_tmp.columns[0]: 'Category', df_tmp.columns[1]: 'Specifications'})
                            for i in range(_menu_columns): df_tmp = df_tmp.rename(columns={df_tmp.columns[2 + i]: trims_text[i]})

            # important_array = important_array.replace(np.nan, '').astype(str).applymap(lambda x: x.strip()).reset_index(drop=True)
            # important_tables.to_csv('/Users/Brandon/PycharmProjects/Web_Scraping/' + 'Important Tables.csv')
            # for s in range(min(3, total_trims), important_tables.shape[1]):
            #     if s == min(3, total_trims):
            #         # category = important_tables.ix[:,s].astype(str)
            #         category = important_tables.iloc[:, s].astype(str)
            #     else:
            #         category = category.str.cat(important_tables.iloc[:, s], sep='')
            # category = pd.Series(category, name='Category')
            # important_array = pd.concat([important_tables.iloc[:, 0:min(3, total_trims)], category], axis=1).reset_index(drop=True)
            # if trim_group == 0:
            #     output_array = important_array
            # else:
            #     merge_array = pd.concat([important_array['Category'], important_array[important_array.columns.difference(output_array.columns)]], axis=1)
            #     output_array = pd.merge(output_array, merge_array, on='Category', how='outer')
    driver.close()
    # return (output_array, readin_check)
    return (df, readin_check)