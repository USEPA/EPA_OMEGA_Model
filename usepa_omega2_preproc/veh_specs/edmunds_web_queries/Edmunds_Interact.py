from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains

import os
import pandas as pd
import math
from bs4 import BeautifulSoup
import numpy as np
# import signal

class HTMLTableParser:
    def get_html_table(self, soup, trim_group, errorflag_1, errorflag_2, errorflag_3):
        full_dataframe_list =  [self.parse_html_table(table, trim_group, errorflag_1, errorflag_2, errorflag_3) \
                                for table in soup.find_all('table') \
                                if len(table.find_all('tr')) > 1 and pd.Series(table.get('class')).str.cat(sep=' ') \
                                != 'features-table table-sm mt-lg-3 w-100-up-md'] #table['id']
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
            for column_count in range (0,len(columns)):
                column = columns[column_count]
                bool_check_true = column.find_all('span', {'class':'feature-container bool-true'})
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

def Edmunds_Interact(url):
    max_attempts = 10
    max_time = 60
    for geturl_attempt in range (0,max_attempts):
        print('URL Attempt '+str(geturl_attempt+1))
        # time = (max_time)*(0.125 + ((geturl_attempt+1)/max_attempts))
        time  = 45
        chromedriver = 'chromedriver.exe'
        os.environ["webdriver.chrome.driver"] = chromedriver
        chromeOptions = Options()
        #chromeOptions.add_argument("--kiosk")
        chromeOptions.add_argument("--start-maximized")
        driver = webdriver.Chrome(chromedriver, chrome_options=chromeOptions)
        try:
            driver.set_page_load_timeout(time)
            driver.get(url)
            # find and click main button to reveal drop-down menu
            menu1 = driver.find_elements_by_xpath("//button[@data-test='select-menu']")[0]
            menu1.click()
            # find trim buttons in drop-down menu
            trim_buttons = driver.find_elements_by_xpath("//div[@class='dropdown-menu show']//button[@class='dropdown-item']")
            # collapse drop-down menu
            menu1.click()
            break
        except (NoSuchElementException, TimeoutException, UnboundLocalError):
            driver.quit()
            pass

    try:
        total_trims = len(trim_buttons)
    except UnboundLocalError:
        if geturl_attempt + 1 == max_attempts:
            return ('N', 'READIN_ERROR')
    trim_group_length = 1

    if total_trims >= 2:
        menu2 = driver.find_elements_by_xpath("//button[@data-test='select-menu']")[1]
        # dropdown2 = Select(menu2)
        trim_group_length = 2
    if total_trims >= 3:
        menu3 = driver.find_elements_by_xpath("//button[@data-test='select-menu']")[2]
        # dropdown3 = Select(menu3)
        trim_group_length = 3

    trim_groups_count = math.ceil(total_trims / 3) #Number of trim groups (in groups of 3, add one if only 1-2 trims left)
    last_group_count = total_trims % 3 #Length of last group
    readin_check = pd.Series(np.zeros(total_trims), name = 'Readin_Error').replace(0,'')
    for table_list_count in range(0, 1):
        if table_list_count == 0:
            save_name = 'pandas list.csv'
        else:
            save_name = 'soup list.csv'
        for trim_group in range(0,trim_groups_count):
            errorflag_1 = 0
            errorflag_2 = 0
            errorflag_3 = 0
            try:
                del important_tables
            except NameError:
                pass
            if trim_group == trim_groups_count - 1 and last_group_count != 0: #Last (or only) trim group and less than 3 entries
                trims = pd.Series(range(last_group_count)) + trim_group_length*trim_group
            else:
                trims = pd.Series(range(trim_group_length)) + trim_group_length*trim_group
            if len(trims) >= 1:
                try:
                    menu1.click()
                    #Choose first option
                    driver.find_elements_by_xpath("//div[@class='dropdown-menu show']//button[@class='dropdown-item']")[0].click()
                    # dropdown1.select_by_index(trims[0]) #Choose first option
                    # element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.LINK_TEXT, (dropdown1.options)[trims[0]].text)))
                except TimeoutException:
                    errorflag_1 = 1
                    readin_check[trims[0]] = 'READIN_ERROR'
            if len(trims) >= 2: #Choose second option (if applicable)
                try:
                    menu2.click()
                    # Choose second option
                    driver.find_elements_by_xpath("//div[@class='dropdown-menu show']//button[@class='dropdown-item']")[1].click()
                    # dropdown2.select_by_index(trims[1])
                    # element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.LINK_TEXT, (dropdown2.options)[trims[1]].text)))
                except TimeoutException:
                    errorflag_2 = 1
                    readin_check[trims[1]] = 'READIN_ERROR'
            if len(trims) >= 3: #Choose third option (if applicable)
                try:
                    menu3.click()
                    # Choose third option
                    driver.find_elements_by_xpath("//div[@class='dropdown-menu show']//button[@class='dropdown-item']")[2].click()
                    # dropdown3.select_by_index(trims[2])
                    # element = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.LINK_TEXT, (dropdown3.options)[trims[2]].text)))
                except TimeoutException:
                    errorflag_3 = 1
                    readin_check[trims[2]] = 'READIN_ERROR'
            if table_list_count == 0:
                table_list = pd.read_html(driver.page_source, header=0)
            else:
                soup = BeautifulSoup(driver.page_source, "lxml")
                hp = HTMLTableParser()
                table_list = hp.get_html_table(soup, trim_group, errorflag_1, errorflag_2, errorflag_3)
            # table_list[16].to_csv(
            #     '/Users/Brandon/PycharmProjects/Web_Scraping' + '//' + str(trim_group) + ' ' + save_name,
            #     index=False)
            for table_count in range(0,len(table_list)):
                if table_list_count == 0 and len(table_list[table_count]) > 3:
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
                            not("Highlights" in table_tag)  \
                            and table_tag != 'OVERVIEW':
                        raw_table.columns = pd.Series(raw_table.columns).str.strip()
                        for col_count in range(1,len(raw_table.columns)):
                            column = raw_table.columns[col_count]
                            msrp = column[column.find('$'):].strip()
                            raw_table = raw_table.rename\
                                (columns = {column:column[column.rfind(')',0,column.rfind(')')):column.rfind(')')+1].strip()\
                                 .replace('  ','').strip() + ' ' + msrp})
                        # raw_table.to_csv('/Users/Brandon/PycharmProjects/Web_Scraping/'+'Raw Table.csv')
                        try:
                            important_tables = pd.concat([important_tables, raw_table])
                        except NameError:
                            important_tables = raw_table
            important_tables = important_tables.replace(np.nan, '').astype(str).applymap(lambda x:x.strip()).reset_index(drop=True)
            # important_tables.to_csv('/Users/Brandon/PycharmProjects/Web_Scraping/' + 'Important Tables.csv')
            for s in range (min(3,total_trims),important_tables.shape[1]):
                if s == min(3,total_trims):
                    category = important_tables.ix[:,s].astype(str)
                else:
                    category = category.str.cat(important_tables.ix[:,s],sep='')
            category = pd.Series(category, name = 'Category')
            important_array = pd.concat([important_tables.ix[:,0:min(3, total_trims)],category],axis=1)\
                .reset_index(drop=True)
            if trim_group == 0:
                output_array = important_array
            else:
                merge_array = pd.concat([important_array['Category'], \
                                         important_array[important_array.columns.difference(output_array.columns)]],axis=1)
                output_array = pd.merge(output_array, merge_array, on='Category', how='outer')

    driver.close()
    return (output_array, readin_check)