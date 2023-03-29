from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException, NoSuchElementException, TimeoutException

import os
import time
import pandas as pd
import math
from bs4 import BeautifulSoup
import numpy as np
from pathlib import *
max_URLs = 1000
_makers_no_models = ['BYTON', 'Lucid', 'Rivian']

chromedriver = 'chromedriver.exe'
os.environ["webdriver.chrome.driver"] = chromedriver
chromeOptions = Options()
chromeOptions.add_argument("--start-maximized")
wait_sec = 30
sleep_short = 0.1
sleep_long = 1.5

def reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, model_idx, xpath_year,
                        year_idx, xpath_go_button, url_list, working_directory):
    # make_idx, model_icx, year_idx == -1 no execution, == 0 no select_by_index() since a dropdown item starts from 1
    continue_flag = True
    driver.quit()
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
    time.sleep(sleep_short)
    driver.get(base_url)

    time.sleep(sleep_short)
    make_dropdown = Select(driver.find_element_by_xpath(xpath_make))
    if make_idx > 0 and make_idx < len(make_dropdown.options):
        time.sleep(sleep_short)
        make_dropdown.select_by_index(make_idx)
        # _maker = make_dropdown.options[make_idx].text
    xpath_text = xpath_make
    if model_idx >= 0:
        time.sleep(sleep_short)
        model_dropdown = Select(driver.find_element_by_xpath(xpath_model))
        if make_idx > 0: xpath_text = xpath_model
        if model_idx > 0 and model_idx < len(model_dropdown.options):
            time.sleep(sleep_short)
            model_dropdown.select_by_index(model_idx)
    if year_idx >= 0:
        time.sleep(sleep_short)
        year_dropdown = Select(driver.find_element_by_xpath(xpath_year))
        if year_idx > 0 and year_idx < len(year_dropdown.options):
            time.sleep(sleep_short)
            year_dropdown.select_by_index(year_idx)
            xpath_text = xpath_go_button
        else:
            xpath_text = xpath_year
            # print('year_idx = ', year_idx, ' max year_idx = ', len(year_dropdown.options))
    try:
        time.sleep(sleep_short)
        element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_text)))
        if year_idx > 0 and xpath_year != xpath_go_button:
            time.sleep(sleep_long)  # time.sleep(sleep_long)
            element.click()
        continue_flag = False
    except (NoSuchElementException, TimeoutException, UnboundLocalError):
        url_list_to_csv(url_list, make_idx, working_directory)

    return driver, continue_flag

def url_list_to_csv(url_list, make_idx, working_directory):
    model_year = url_list[0].replace('//', '/').split('/')[4]
    url_column_name = 'Link ' + str(model_year)
    url_list = pd.DataFrame(url_list, columns=[url_column_name])
    url_list.insert(0, 'Make', '')
    url_list.insert(1, 'Model', '')
    rows, cols = url_list.shape
    last_rows = 0
    for i in range(rows):
        url_str = url_list[url_column_name][i]
        if url_str == '':
            last_rows = i+1
            break
        str_make_model = url_str.replace('//', '/').split('/')
        url_list['Make'][i] = str_make_model[2].capitalize()
        url_list['Model'][i] = str_make_model[3].upper()
        if str_make_model[4].isnumeric() == False: url_str = url_str + str(model_year) + '/'
        if 'features-specs' not in str_make_model: url_str = url_str + 'features-specs/'
        url_list[url_column_name][i] = url_str

    num_csv_files = math.ceil(last_rows/max_URLs)
    timestr = time.strftime("%Y%m%d-%H%M%S")
    csv_fname_PART = working_directory + 'Edmunds URLs_' + str(model_year) + '_part.csv'
    for i in range(num_csv_files):
        if make_idx > 0:
            url_list.iloc[i*max_URLs:(i+1)*max_URLs,:].to_csv(csv_fname_PART, index=False)
        else:
            if os.path.exists(csv_fname_PART): os.remove(csv_fname_PART)
            url_list.iloc[i*max_URLs:(i+1)*max_URLs,:].to_csv(working_directory + 'Edmunds URLs_'+str(model_year) + '_'+ timestr + '.csv', index=False)

def Get_URLs_Edmunds(model_year):
    url_list = pd.Series(np.zeros(1000)).replace(0, '')
    url_list_count = 0
    working_directory = str(Path.home()) + '/Documents/Python/Edmunds_web_vehicle_specs/'
    base_url = 'https://www.edmunds.com/car-reviews/'
    chromedriver = 'chromedriver.exe'
    os.environ["webdriver.chrome.driver"] = chromedriver
    chromeOptions = Options()
    # caps = DesiredCapabilities().CHROME
    # caps["pageLoadStrategy"] = "none"
    # # chromeOptions.add_argument("--kiosk")
    chromeOptions.add_argument("--start-maximized")
    #prefs = {'profile.managed_default_content_settings.images':2}
    # prefs = {"plugins.plugins_disabled": ["Chrome PDF Viewer"]}
    #chromeOptions.add_experimental_option('prefs', prefs)
    #chromeOptions.add_argument("--disable-extensions")
    # driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions, desired_capabilities=caps)
    time.sleep(sleep_short)
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
    time.sleep(sleep_short)
    driver.get(base_url)

    # used_car_element = driver.find_element_by_xpath("//a[@data-tracking-id = 'nav_mmy_select_used_car']")
    # actions = ActionChains(driver)
    # actions.move_to_element(used_car_element)
    # actions.click()
    # raise SystemExit()
    xpath_make = "//select[@name = 'select-make']"
    xpath_model = "//select[@name = 'select-model']"
    xpath_year = "//select[@name = 'select-year']"
    xpath_go_button = "//button[@class = 'w-100 btn btn-success']"
    xpath_go_button = "//button[@class = 'mb-0_5 w-100 px-0 px-md-1_5 btn btn-success']"
    time.sleep(sleep_short)
    element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_make)))
    # time.sleep(sleep_short); element.click()
    make_dropdown = Select(driver.find_element_by_xpath(xpath_make))
    total_make_options = len(make_dropdown.options)
    for make_idx in range (1, total_make_options):
        try:
            time.sleep(sleep_short)
            make_dropdown.select_by_index(make_idx)
        except:
            [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, -1, xpath_year, -1,
                                                          xpath_go_button, url_list, working_directory)
            time.sleep(sleep_short)
            make_dropdown = Select(driver.find_element_by_xpath(xpath_make))
            if continue_flag: continue
        if make_dropdown.options[make_idx].text in _makers_no_models: continue
        try:
            time.sleep(sleep_short)
            element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_model)))
        except (NoSuchElementException, TimeoutException, UnboundLocalError):
            [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, 0, xpath_year, -1,
                                                          xpath_go_button, url_list, working_directory)
            if continue_flag: continue

            time.sleep(sleep_short)
            make_dropdown = Select(driver.find_element_by_xpath(xpath_make))
            make_dropdown.select_by_index(make_idx)
            try:
                time.sleep(sleep_short)
                element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_model)))
            except (NoSuchElementException, TimeoutException, UnboundLocalError):
                [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, 0, xpath_year, -1,
                                                              xpath_go_button, url_list, working_directory)
                if continue_flag: continue

        time.sleep(sleep_short)
        model_dropdown = Select(driver.find_element_by_xpath(xpath_model))
        total_model_options = len(model_dropdown.options)
        for model_idx in range(1, total_model_options):
            try:
                time.sleep(sleep_short)
                model_dropdown.select_by_index(model_idx)
            except:
                [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, model_idx,
                                                              xpath_year, -1, xpath_go_button, url_list, working_directory)
                if continue_flag: continue
            try:
                time.sleep(sleep_short)
                element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_year)))
            except (NoSuchElementException, TimeoutException, UnboundLocalError):
                [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, model_idx,
                                                              xpath_year, 0, xpath_go_button, url_list, working_directory)
                if continue_flag: continue

            time.sleep(sleep_short)
            year_dropdown = Select(driver.find_element_by_xpath(xpath_year))
            total_year_options = len(year_dropdown.options)
            for year_idx in range(1, total_year_options):
                if int(year_dropdown.options[1].text.strip()) < int(model_year): break
                if year_dropdown.options[year_idx].text == str(model_year):
                    time.sleep(sleep_short)
                    year_dropdown.select_by_index(year_idx)
                    time.sleep(sleep_short)
                    go_button = driver.find_element_by_xpath(xpath_go_button)
                    try:
                        time.sleep(sleep_long)  # time.sleep(sleep_long)
                        go_button.click()
                    except:
                        [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, model_idx,
                                                                      xpath_year, year_idx, xpath_go_button, url_list, working_directory)
                        if continue_flag: continue

                    if 'review' in str(driver.current_url):
                        url_list[url_list_count] = str(driver.current_url).replace('review', 'features-specs')
                    elif str(model_year) in str(driver.current_url):
                        url_list[url_list_count] = str(driver.current_url) + 'features-specs/'
                    else:
                        url_list[url_list_count] = str(driver.current_url) + str(model_year) + '/features-specs/'
                    print(url_list_count, make_idx, model_idx, url_list[url_list_count])
                    # if new_url[-1] == '\\':
                    #     url_list[url_list_count] = new_url + 'features-specs'
                    # else:
                    #     url_list[url_list_count] = new_url + '\\'+'features-specs'
                    url_list_count += 1
                    driver.get(base_url)
                    try:
                        time.sleep(sleep_short)
                        element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_make)))
                    except (NoSuchElementException, TimeoutException, UnboundLocalError):
                        [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, 0, xpath_model, -1,
                                                                      xpath_year, -1, xpath_go_button, url_list, working_directory)
                        if continue_flag: continue
                    time.sleep(sleep_short)
                    make_dropdown = Select(driver.find_element_by_xpath(xpath_make))
                    if make_dropdown.options[make_idx].text in _makers_no_models: break
                    time.sleep(sleep_short)
                    make_dropdown.select_by_index(make_idx)
                    try:
                        time.sleep(sleep_short)
                        element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, xpath_model)))
                    except (NoSuchElementException, TimeoutException, UnboundLocalError):
                        [driver, continue_flag] = reset_url_clickable(driver, base_url, xpath_make, make_idx, xpath_model, 0,
                                                                      xpath_year, -1, xpath_go_button, url_list, working_directory)
                        if continue_flag: continue
                    time.sleep(sleep_short)
                    model_dropdown = Select(driver.find_element_by_xpath(xpath_model))
                    break

    url_list_to_csv(url_list, -1, working_directory)
