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
import pandas as pd
import math
from bs4 import BeautifulSoup
import numpy as np


def Get_URLs_Edmunds(model_year):
    url_list = pd.Series(np.zeros(1000)).replace(0,'')
    url_list_count = 0
    working_directory = 'C:/Users/KBolon/Documents/Python/Edmunds_web_vehicle_specs/'
    base_url = 'https://www.edmunds.com/car-reviews/'
    chromedriver = 'chromedriver.exe'
    os.environ["webdriver.chrome.driver"] = chromedriver
    chromeOptions = Options()
    caps = DesiredCapabilities().CHROME
    caps["pageLoadStrategy"] = "none"
    # chromeOptions.add_argument("--kiosk")
    chromeOptions.add_argument("--start-maximized")
    #prefs = {'profile.managed_default_content_settings.images':2}
    # prefs = {"plugins.plugins_disabled": ["Chrome PDF Viewer"]}
    #chromeOptions.add_experimental_option('prefs', prefs)
    #chromeOptions.add_argument("--disable-extensions")
    driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions, desired_capabilities=caps)
    driver.get(base_url)


    # used_car_element = driver.find_element_by_xpath("//a[@data-tracking-id = 'nav_mmy_select_used_car']")
    # actions = ActionChains(driver)
    # actions.move_to_element(used_car_element)
    # actions.click()
    # raise SystemExit()

    element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//select[@name = 'select-make']")))
    make_dropdown = Select(driver.find_element_by_xpath("//select[@name = 'select-make']"))
    total_make_options = len(make_dropdown.options)
    for make_idx in range(1, 3):
    # for make_idx in range (1,total_make_options):
            make_dropdown.select_by_index(make_idx)
            try:
                element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//select[@name = 'select-model']")))
            except (NoSuchElementException, TimeoutException, UnboundLocalError):
                continue
            model_dropdown = Select(driver.find_element_by_xpath("//select[@name = 'select-model']"))
            total_model_options = len(model_dropdown.options)
            for model_idx in range(1,total_model_options):
                model_dropdown.select_by_index(model_idx)
                element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//select[@name = 'select-year']")))
                year_dropdown = Select(driver.find_element_by_xpath("//select[@name = 'select-year']"))
                total_year_options = len(year_dropdown.options)
                for year_idx in range(1,total_year_options):
                    if year_dropdown.options[year_idx].text == str(model_year):
                        year_dropdown.select_by_index(year_idx)
                        # go_button = driver.find_element_by_class_name('w-100 btn btn-success')
                        go_button = driver.find_element_by_xpath("//button[@class = 'w-100 btn btn-success']")
                        go_button.click()
                        url_list[url_list_count] = str(driver.current_url).replace('review', 'features-specs')
                        # if new_url[-1] == '\\':
                        #     url_list[url_list_count] = new_url + 'features-specs'
                        # else:
                        #     url_list[url_list_count] = new_url + '\\'+'features-specs'
                        url_list_count += 1
                        # url_list.to_csv('/Users/Brandon/PycharmProjects/Web_Scraping/' + 'Edmunds URLs_' + str(model_year) + '.csv', index=False)
                        driver.get(base_url)
                        element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//select[@name = 'select-make']")))
                        make_dropdown = Select(driver.find_element_by_xpath("//select[@name = 'select-make']"))
                        make_dropdown.select_by_index(make_idx)
                        element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//select[@name = 'select-model']")))
                        model_dropdown = Select(driver.find_element_by_xpath("//select[@name = 'select-model']"))
                        model_dropdown.select_by_index(model_idx)
                        element = WebDriverWait(driver, 60).until(EC.element_to_be_clickable((By.XPATH, "//select[@name = 'select-year']")))
                        year_dropdown = Select(driver.find_element_by_xpath("//select[@name = 'select-year']"))

            # driver.get(base_url)
        # driver.get(base_url)

    url_list = url_list[url_list != ''].reset_index(drop=True)
    url_list.to_csv(working_directory + 'Edmunds URLs_'+str(model_year)+'.csv', index=False)