from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains

import os
import pandas as pd
import math
from bs4 import BeautifulSoup
import numpy as np


def Get_URLs_Edmunds(model_year):
    url_list = pd.Series(np.zeros(1000)).replace(0,'')
    url_list_count = 0
    working_directory = 'C:/Users/KBolon/Documents/Python/Edmunds_web_ vehicle_specs/'
    base_url = 'https://www.edmunds.com/'
    chromedriver = 'chromedriver.exe'
    os.environ["webdriver.chrome.driver"] = chromedriver
    chromeOptions = Options()
    chromeOptions.add_argument("--kiosk")
    #prefs = {'profile.managed_default_content_settings.images':2}
    # prefs = {"plugins.plugins_disabled": ["Chrome PDF Viewer"]}
    #chromeOptions.add_experimental_option('prefs', prefs)
    #chromeOptions.add_argument("--disable-extensions")
    driver = webdriver.Chrome(chromedriver, chrome_options=chromeOptions)
    driver.get(base_url)

    used_car_element = driver.find_element_by_xpath("//a[@data-tracking-id = 'nav_mmy_select_used_car']")
    actions = ActionChains(driver)
    actions.move_to_element(used_car_element)
    actions.click()
    raise SystemExit()
    # make_dropdown = Select(driver.find_element_by_xpath("//select[@class = 'mmy-select js-makes-select w-100 btn btn-sm btn-secondary']"))
    # total_make_options = len(make_dropdown.options)
    # for total_make_count in range (1,total_make_options):
    #     model_dropdown = Select(driver.find_element_by_xpath("//select[@class = 'mmy-select js-models-select w-100 btn btn-sm btn-secondary']"))
    #     total_model_options = len(model_dropdown.options)
    #     for total_model_count in range(1,total_model_options):
    #         model_dropdown.select_by_index(total_model_count)
    #         year_dropdown = Select(driver.find_element_by_xpath("//select[@class = 'mmy-select js-years-select w-100 btn btn-sm btn-secondary']"))
    #         total_year_options = len(year_dropdown.options)
    #         for year_count in range(1,total_year_options):
    #             current_year = year_dropdown.select_by_index(year_count)
    #             if current_year.text.upper() == str(model_year):
    #                 go_button = driver.find_element_by_class_name('btn btn-success px-1 py-0_5 js-go-btn')
    #                 go_button.click()
    #                 new_url = str(driver.current_url)
    #                 if new_url[-1] == '\\':
    #                     url_list[url_list_count] = new_url + 'features-specs'
    #                 else:
    #                     url_list[url_list_count] = new_url + '\\'+'features-specs'
    #                 url_list_count += 1
    #                 url_list.to_csv(
    #                     '/Users/Brandon/PycharmProjects/Web_Scraping/' + 'Edmunds URLs_' + str(model_year) + '.csv',
    #                     index=False)
    #                 driver.get(base_url)
    #                 make_dropdown.select_by_index(total_make_count)
    #                 model_dropdown.select_by_index(total_model_count)
    #         driver.get(base_url)
    #         make_dropdown.select_by_index(total_make_count)
    #     driver.get(base_url)
    url_list = url_list[url_list != ''].reset_index(drop=True)
    url_list.to_csv(working_directory + 'Edmunds URLs_'+str(model_year)+'.csv', index=False)