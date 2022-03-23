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
SKIP_PRINTING_EXTERIOR_OPTIONS = True # skip printing tire brands, etc
SKIP_PRINTING_INTERIOR_OPTIONS = True
SKIP_PRINTING_COMFORT_CONVENIENCE = False # set false, for electric power steering
SKIP_PRINTING_PACKAGES = True
SKIP_IN_CAR_ENTERTAINMENT = True
SKIP_POWER_FEATURE = True
SKIP_PRINTING_COLORS = True # skip printingg interior and exterior colors
DELETE_DISCONTINUED_MODELS = False

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

def merge_trim_options(tmp_raw_table0, _num_menu_columns, df_options, _trim_str):
    tmp_raw_table = tmp_raw_table0.copy(deep=True)
    _row_drop_start = 0
    _row_trim_str_init = 0
    for k in range(len(df_options)):
        _row = df_options.index[k]
        _option_spec_str = tmp_raw_table['Specifications'][_row].split(' ' + _trim_str)
        _option_spec = _option_spec_str[0]
        _option_spec_no_spaces = _option_spec.replace(' ', '')
        # if (_option_spec in ['All season', 'all season', 'painted alloy', 'steel', 'Run flat', 'Performance']) or \
        if (_option_spec_no_spaces.isalpha() == True) or len(_option_spec) == 0:
            # print(_option_spec_no_spaces)
            continue
        else:
            if k == 0 or _row_trim_str_init == 0:
                tmp_raw_table['Specifications'][_row] = _trim_str
                _trim_str_row = _row
                if k>0 and _row_trim_str_init == 0:
                    _row_drop_start = k
                    _row_trim_str_init = k
                elif k == 0:
                    _row_trim_str_init  = 1

            for _index_col in range(_num_menu_columns):
                trim_col = tmp_raw_table.columns[_index_col+2]
                ioption = str(tmp_raw_table[trim_col][_row])
                if ioption.lower() == 'yes':
                    tmp_raw_table[trim_col][_trim_str_row] = _option_spec
                elif ioption.lower() == 'no' and tmp_raw_table[trim_col][_trim_str_row] == 'no':
                    tmp_raw_table[trim_col][_trim_str_row] = np.nan
                if k > _row_drop_start: tmp_raw_table[trim_col][_row] = np.nan
            # if k > _row_drop_start:
            #     # tmp_raw_table =[trim_col][_row] = ''
            #     tmp_raw_table = tmp_raw_table.drop(index=_row)

    return tmp_raw_table

def trim_tires_wheels(tmp_raw_table, _num_menu_columns):
    tmp_raw_table1 = tmp_raw_table.copy(deep=True)

    _index_all_season_tires = tmp_raw_table.index[tmp_raw_table['Specifications'].str.contains('All season tires')]
    wheels_index = tires_index = all_season_tires_index = run_flat_tires_index = performance_tires_index = all_terrain_tires_index = -1
    for _index in range(len(tmp_raw_table)):
        if tmp_raw_table['Specifications'][_index] == 'tires':
            tires_index = _index
            break
    for _index in range(len(tmp_raw_table)):
        if tmp_raw_table['Specifications'][_index] == 'wheels':
            wheels_index = _index
            break
    for _index in range(len(tmp_raw_table)):
        if str(tmp_raw_table['Specifications'][_index]).lower() == 'all season tires' or \
                tmp_raw_table['Specifications'][_index] == 'All season tires':
            all_season_tires_index = _index
            break
    for _index in range(len(tmp_raw_table)):
        if str(tmp_raw_table['Specifications'][_index]).lower() == 'performance tires' or \
                tmp_raw_table['Specifications'][_index] == 'Performance tires':
            performance_tires_index = _index
            break
    for _index in range(len(tmp_raw_table)):
        if str(tmp_raw_table['Specifications'][_index]).lower() == 'run flat tires' or \
                tmp_raw_table['Specifications'][_index] == 'Run flat tires':
            run_flat_tires_index = _index
            break
    for _index in range(len(tmp_raw_table)):
        if str(tmp_raw_table['Specifications'][_index]).lower() == 'all terrain tires' or \
                tmp_raw_table['Specifications'][_index] == 'All terrain tires':
            all_terrain_tires_index = _index
            break

    tmp_raw_table1.iloc[0, 1] = 'wheels'
    tmp_raw_table1.iloc[1, 1] = 'tires'
    tmp_raw_table1.iloc[2, 1] = 'tire types'
    for _jcol in range(_num_menu_columns):
        tmp_raw_table1.iloc[0, _jcol + 2] = tmp_raw_table.iloc[wheels_index, _jcol + 2]
        if tires_index < 0 or len(str(tmp_raw_table.iloc[tires_index, _jcol + 2])) == 0:
            tmp_raw_table1.iloc[1, _jcol + 2] = 'NA'
        else:
            tmp_raw_table1.iloc[1, _jcol + 2] = tmp_raw_table.iloc[tires_index, _jcol + 2]
        if wheels_index < 0 or len(str(tmp_raw_table.iloc[wheels_index, _jcol + 2])) == 0:
            tmp_raw_table1.iloc[0, _jcol + 2] = 'NA'
    for _jcol in range(_num_menu_columns):
        if all_season_tires_index >= 0:
            tmp_raw_table1.iloc[2, _jcol + 2] = 'All season tires'
        if run_flat_tires_index >= 0:
            tmp_raw_table1.iloc[2, _jcol + 2] = 'Run flat tires'
            if all_season_tires_index >= 0: tmp_raw_table1.iloc[2, _jcol + 2] = 'All season tires, Run flat tires'
        if all_terrain_tires_index >= 0:
            tmp_raw_table1.iloc[2, _jcol + 2] = 'All terrain tires'
            if all_season_tires_index >= 0: tmp_raw_table1.iloc[2, _jcol + 2] = 'All season tires, All terrain tires'
        if performance_tires_index >= 0:
            tmp_raw_table1.iloc[2, _jcol + 2] = 'Performance tires'
            if all_season_tires_index >= 0: tmp_raw_table1.iloc[2, _jcol + 2] = 'All season tires, Performance tires'
        if all_season_tires_index == -1 and performance_tires_index == -1 and run_flat_tires_index == -1 and all_terrain_tires_index == -1:
            tmp_raw_table1.iloc[2, _jcol + 2] = 'NA'

    tmp_raw_table = drop_merged_option(tmp_raw_table1, _num_menu_columns)
    tmp_raw_table = tmp_raw_table.drop_duplicates(subset=['Specifications']).reset_index(drop=True)

    return tmp_raw_table

def drop_merged_option(tmp_raw_table, _num_menu_columns):
    if _num_menu_columns == 1:
        tmp_raw_table = tmp_raw_table.dropna(how='all', subset=[tmp_raw_table.columns[2]])
    elif _num_menu_columns == 2:
        tmp_raw_table = tmp_raw_table.dropna(how='all', subset=[tmp_raw_table.columns[2], tmp_raw_table.columns[3]])
    elif _num_menu_columns == 3:
        tmp_raw_table = tmp_raw_table.dropna(how='all', subset=[tmp_raw_table.columns[2], tmp_raw_table.columns[3], tmp_raw_table.columns[4]])

    tmp_raw_table = tmp_raw_table.reset_index(drop=True)

    return tmp_raw_table

def update_raw_tables(tmp_raw_table0, _num_menu_columns):
    tmp_raw_table = tmp_raw_table0.copy(deep=True)
    _overview_list = ['Engine Type', 'Transmission', 'Drive Type', 'Combined MPG', 'Total Seating', 'Basic Warranty', 'Cylinders']
    _drivetrain_simple_list =['Drive type', 'Transmission']
    _drivetrain_list =['Drive type', 'Transmission', 'part time 4WD', 'on demand 4WD', 'automatic locking hubs', 'electronic hi-lo gear selection']
    _engine_list = ['Torque', 'Base engine size', 'Horsepower', 'Turning circle', 'Valves', 'direct injection', 'Base engine type', \
                    'Valve timing', 'Cam type', 'Cylinders', 'cylinder deactivation']
    _comfort_convenience_list = ['electric power steering', 'power steering']
    _measurements_list = ['Length', 'Maximum towing capacity', 'Wheel base', 'Width', 'Curb weight', 'Maximum payload', 'Gross weight', 'Height', \
                        'Ground clearance', 'Cargo capacity, all seats in place']
    _fuel_mpg_list = ['EPA mileage est. (cty/hwy)', 'Combined MPG', 'Fuel type', 'Fuel tank capacity', 'Range in miles (cty/hwy)']
    _PHEV_fuel_mpg_list = ['EPA Combined MPGe', 'Range in miles (cty/hwy)',  'EPA Time to charge battery (at 240v)', 'Fuel tank capacity', \
                           'Combined MPG', 'EPA kWh/100 mi', 'Fuel type', 'EPA Electricity Range']
    _BEV_fuel_mpg_list = ['EPA City MPGe', 'EPA Combined MPGe', 'EPA mileage est. (cty/hwy)', \
                          'Range in miles (cty/hwy)', 'EPA Time to charge battery (at 240v)', 'EPA Highway MPGe', \
                           'Combined MPG', 'EPA kWh/100 mi', 'Fuel type', 'EPA Electricity Range', 'Fuel tank capacity']
    _BEV_simple_fuel_mpg_list = ['Range in miles (cty/hwy)', 'Fuel type']
    _warrenty_list = ['Free maintenance', 'Basic', 'Drivetrain', 'Rust', 'Roadside', 'Hybrid Component', 'EV Battery']
    _no_to_nan_list =  ['MSRP', 'Torque', 'Cylinders', 'Total Seating', 'Basic Warranty', 'Horsepower', 'Turning circle', 'Valves' \
                        'Engine Type', 'Base engine size', 'EPA Time to charge battery (at 240v)', 'EPA Highway MPGe'] + \
                       _drivetrain_list + _fuel_mpg_list + _BEV_fuel_mpg_list + _measurements_list + _warrenty_list

    _num_specs_list = len(tmp_raw_table)
    _num_specs = len(tmp_raw_table0)
    _specs_list = []
    for i in range (_num_specs):
        _specs_list.append(tmp_raw_table0[tmp_raw_table0.columns[1]][i])

    _category = tmp_raw_table0[tmp_raw_table0.columns[0]][0]
    if _category == 'Overview': _new_specs_list = _overview_list
    if _category == 'Drivetrain': _new_specs_list = _drivetrain_simple_list
    if _category == 'Fuel & MPG':
        _new_specs_list = _fuel_mpg_list
        _fuel_list = list(tmp_raw_table0[tmp_raw_table0.columns[1]])
        if 'Fuel type' in _fuel_list:
            _row_fuel_type = _fuel_list.index('Fuel type')
            _fuel = tmp_raw_table0[tmp_raw_table0.columns[2]][_row_fuel_type]
            if _fuel == 'Electric fuel' and _num_specs_list > 8:
                _new_specs_list = _BEV_fuel_mpg_list
            elif _fuel == 'Electric fuel' and _num_specs_list == 2:
                _new_specs_list = _BEV_simple_fuel_mpg_list
            elif _num_specs_list > 5 and _num_specs_list <= 8:
                _new_specs_list = _PHEV_fuel_mpg_list
    if _category == 'Engine': _new_specs_list = _engine_list
    if _category == 'Comfort & Convenience':
        _new_specs_list = _comfort_convenience_list
    if _category == 'Measurements':
        _new_specs_list = _measurements_list
        if 'Maximum towing capacity'in _specs_list:
            _index_towing_capacity = _specs_list.index('Maximum towing capacity')
    if _category == 'Warranty': _new_specs_list = _warrenty_list

    _specs_seq = []
    _new_specs_pos = []
    _num_new_specs_inserted = 0
    _num_specs_skipped = 0
    _specs_skipped_pos = []

    for i in range(len(_new_specs_list)):
        _new_spec = _new_specs_list[i]
        if _new_spec in _specs_list:
            ispec_no = _specs_list.index(_new_spec)
            if ispec_no > i:
                _specs_skipped_pos.append('yes')
            else:
                _specs_skipped_pos.append('no')
            _specs_seq.append(str(ispec_no))
            _new_specs_pos.append('no')
        else:
            df1 = pd.DataFrame([[''] * len(tmp_raw_table.columns)], columns=tmp_raw_table.columns)
            df1["Category"][0] = _category
            df1['Specifications'][0] = _new_spec
            if i == 0:
                tmp_raw_table = pd.concat([df1, tmp_raw_table], ignore_index=True)
            else:
                tmp_raw_table = pd.concat([tmp_raw_table, df1], ignore_index=True)
            tmp_raw_table.reset_index()
            _new_specs_pos.append('yes')
            _specs_skipped_pos.append('no')
            _num_new_specs_inserted = _num_new_specs_inserted + 1
            _specs_seq.append(str('-1'))

    _num_specs_seq = len(_specs_seq)

    _num_new_specs_inserted = 0
    _num_specs_skipped = 0
    _new_spec_inserted = False
    _new_spec_skipped = False
    for i in range((_num_specs_seq)):
        _irow_adjusted = i
        ispec_no = int(_specs_seq[i])
        _irow = ispec_no = ispec_no
        if ispec_no >= 0:
            _specs = tmp_raw_table0[tmp_raw_table0.columns[1]][ispec_no]
        if _new_specs_pos[i] == 'yes' and ispec_no < 0:
            _new_specs_text = _new_specs_list[i]
            tmp_raw_table[tmp_raw_table.columns[1]][i] = _new_specs_text
            _num_new_specs_inserted = _num_new_specs_inserted + 1
            _irow = ispec_no + _num_new_specs_inserted
            for j in range (_num_menu_columns):
                tmp_raw_table[tmp_raw_table.columns[j+2]][i] = ''
                _new_spec_inserted = True
        elif _specs_skipped_pos[i] == 'yes':
            _num_specs_skipped = _num_specs_skipped + 1
            _new_spec_skipped = True
            _irow = ispec_no - _num_specs_skipped
            _irow_adjusted = i

        if ispec_no >= 0:
            _new_specs_text = tmp_raw_table0[tmp_raw_table0.columns[1]][ispec_no]
            if _new_specs_text == 'Maximum towing capacity': _index_towing_capacity = _irow
            tmp_raw_table[tmp_raw_table.columns[1]][_irow_adjusted] = _new_specs_text
            for j in range (_num_menu_columns):
                _item = tmp_raw_table0[tmp_raw_table0.columns[j + 2]][ispec_no]
                if _item == 'no' or _item == '' or  _item == np.nan:
                    if _specs in _no_to_nan_list: _item = ''
                tmp_raw_table[tmp_raw_table.columns[j+2]][_irow_adjusted] = _item

    return tmp_raw_table

def est_max_towing_capacity(df):
    _rows, _cols = df.shape
    _specs_list = df['Specifications'].tolist()

    _towing_cols = []
    _towing_missing_col = []
    _index_towing_capacity = _specs_list.index('Maximum towing capacity')
    _index_torque = _specs_list.index('Torque')
    _index_curb_weight = _specs_list.index('Curb weight')
    _index_gross_weight = _specs_list.index('Gross weight')
    _index_max_payload = _specs_list.index('Maximum payload')
    _num_menu_columns = _cols - 2

    for j in range(_num_menu_columns):
        max_payload = df.iloc[_index_max_payload, j+2]
        gross_weight = df.iloc[_index_gross_weight, j+2]
        curb_weight = df.iloc[_index_curb_weight, j+2]
        max_payload_str1 = gross_weight_str1 = ''
        if len(curb_weight) == 0 or (curb_weight == 'no' or curb_weight == '') and len(gross_weight) > 0 and len(max_payload) > 0:
            if 'lbs.' in max_payload:  max_payload_str1 = max_payload.split(' ')[0]
            if 'lbs.' in gross_weight:  gross_weight_str1 = gross_weight.split(' ')[0]
            if len(gross_weight_str1) > 0 and len(max_payload_str1) > 0:
                df.iloc[_index_curb_weight, j + 2] = str(float(gross_weight_str1) - float(max_payload_str1)) + ' lbs.'
    for j in range(_num_menu_columns):
        _item = df.iloc[_index_towing_capacity, j+2]
        if len(_item) > 0 and _item != 'no' and ('lbs.' in _item):
            _towing_cols.append(j)
        elif _item == 'no' or _item == '':
            df.iloc[_index_towing_capacity, j+2] = ''
            _towing_missing_col.append(j)
    _num_towing_cols = len(_towing_cols)
    _num_towing_missing_col = len(_towing_missing_col)
    if _num_towing_cols > 0 and _num_towing_missing_col > 0:
        _towing_est = 0
        _towing_capacity1_first = 0
        _towing_capacity2_first = 0
        if len(_towing_cols) < 4:
            num_sampling = 1
        else:
            num_sampling = 2
        for j in range (_num_towing_missing_col):
            _icol = int(_towing_missing_col[j])
            _towing_capacity1 = 0
            _towing_capacity = ''
            k = 0
            sampling_lower = []
            for _istart in range (_icol-1, 1, -1):
                if _istart in _towing_cols:
                    _item = df.iloc[_index_towing_capacity, _istart + 2]
                    _towing_capacity1 = _towing_capacity1 + float(_item.split(' ')[0])
                    if k == 0: _towing_capacity1_first = _towing_capacity1
                    k = k + 1
                    sampling_lower.append(_istart)
                    if k == num_sampling: break
            if k == 0 and _towing_capacity1 == 0:
                num_towing_capacity1 = 0
            else:
                num_towing_capacity1 = num_sampling

            _towing_capacity2 = 0
            k = 0
            sampling_upper = []
            for _iend in range (_icol+1, _cols):
                if _iend in _towing_cols:
                    _item = df.iloc[_index_towing_capacity, _iend + 2]
                    _towing_capacity2 = _towing_capacity2 + float(_item.split(' ')[0])
                    if k == 0: _towing_capacity2_first = _towing_capacity2
                    k = k + 1
                    sampling_upper.append(_iend)
                    if k == num_sampling: break
            if k == 0 and _towing_capacity2 == 0:
                num_towing_capacity2 = 0
            else:
                num_towing_capacity2 = num_sampling

            if num_towing_capacity1 > 0 or num_towing_capacity2 > 0:
                _towing_capacity = (_towing_capacity1 + _towing_capacity2)/(num_towing_capacity1 + num_towing_capacity2)

            if _towing_capacity != '':
                _towing_est = str(_towing_capacity) + ' lbs. (Estimated)'

            _towing_capacity_lower = 0
            _towing_capacity_upper = 0
            if len(sampling_lower) > 0:
                _item = df.iloc[_index_towing_capacity, sampling_lower[0] + 2]
                _towing_capacity_lower = float(_item.split(' ')[0])
            if len(sampling_upper) > 0:
                _item = df.iloc[_index_towing_capacity, sampling_upper[0] + 2]
                _towing_capacity_upper = float(_item.split(' ')[0])

            _towing_capacity_diff1 = _towing_capacity_diff2 = 0
            _towing_capacity_max = max(_towing_capacity_upper, _towing_capacity_lower)
            _towing_capacity_min = min(_towing_capacity_upper, _towing_capacity_lower)

            if _towing_capacity_min > 0:
                _towing_capacity_diff1 = abs(_towing_capacity - _towing_capacity_max) / _towing_capacity_max * 100
            if  _towing_capacity_min > 0:
                _towing_capacity_diff2 = abs(_towing_capacity - _towing_capacity_min) / _towing_capacity_min * 100
            if (_towing_capacity_diff1 > 10) or (_towing_capacity_diff2 > 10):
                curb_weight_lower = 0
                curb_weight_upper = 0
                curb_weight = 0
                curb_weight_max = 0
                if num_towing_capacity1 > 0 and (df.iloc[_index_curb_weight, sampling_lower[0] + 2] != 'no' and df.iloc[_index_curb_weight, sampling_lower[0] + 2] != '') \
                    and 'lbs.' in df.iloc[_index_curb_weight, sampling_lower[0] + 2] and len(sampling_lower) > 0:
                    curb_weight_lower = float(df.iloc[_index_curb_weight, sampling_lower[0] + 2].split(' ')[0])
                if num_towing_capacity2 > 0 and (df.iloc[_index_curb_weight, sampling_upper[0] + 2] != 'no' and df.iloc[_index_curb_weight, sampling_upper[0] + 2] != '') \
                        and 'lbs.' in df.iloc[_index_curb_weight, sampling_upper[0] + 2] and len(sampling_upper) > 0 and (sampling_upper[0] + 2) < _num_menu_columns:
                    curb_weight_upper = float(df.iloc[_index_curb_weight, sampling_upper[0] + 2].split(' ')[0])
                if curb_weight_upper > 0 or curb_weight_lower > 0:
                    curb_weight_max = max(curb_weight_lower, curb_weight_upper)
                if (df.iloc[_index_curb_weight, _icol + 2] != 'no' and df.iloc[_index_curb_weight, _icol + 2] != '') \
                    and 'lbs.' in df.iloc[_index_curb_weight, _icol + 2]:
                    curb_weight = float(df.iloc[_index_curb_weight, _icol + 2].split(' ')[0])

                torque = torque_lower = torque_upper = 0
                if num_towing_capacity1 > 0 and len(df.iloc[_index_torque, sampling_lower[0] + 2]) > 0:
                    torque_lower = float(df.iloc[_index_torque, sampling_lower[0] + 2].split(' ')[0])
                if num_towing_capacity2 > 0 and len(df.iloc[_index_torque, sampling_upper[0] + 2]) > 0:
                    torque_upper = float(df.iloc[_index_torque, sampling_upper[0] + 2].split(' ')[0])
                torque_max = max(torque_lower, torque_upper)
                if len(df.iloc[_index_torque, _icol + 2]) > 0 and 'libs.' in df.iloc[_index_torque, _icol + 2]:
                    torque = float(df.iloc[_index_torque, _icol + 2].split(' ')[0])

                curb_weight_diff1 = abs(curb_weight - curb_weight_lower)
                curb_weight_diff2 = abs(curb_weight - curb_weight_upper)
                torque_diff1 = abs(torque - torque_lower)
                torque_diff2 = abs(torque - torque_upper)

                if curb_weight > curb_weight_max and torque > torque_max:
                    _towing_est = _towing_capacity_max
                elif torque_diff1 < torque_diff2 and curb_weight_diff1 < curb_weight_diff2:
                    _towing_est = _towing_capacity_lower
                elif torque_diff1 > torque_diff2 and curb_weight_diff1 > curb_weight_diff2:
                    _towing_est = _towing_capacity_upper
                elif (curb_weight > 1.05*curb_weight_max and curb_weight_max > 0) or (torque > 1.1*torque_max and torque_max > 0):
                    _towing_est = _towing_capacity_max
                else:
                    _towing_est = _towing_capacity
                _towing_est = str(_towing_est) + ' lbs. (Estimated)'

            df.iloc[_index_towing_capacity, _icol+2] = _towing_est

    return df

def Edmunds_Interact(url):
    max_attempts = 10
    max_time = 30
    sleep_3sec = 3
    sleep_sec = 1
    wait_sec = 30
    _max_trim_groups_count = 20 # for 4K resolution monitor, set 10 for low resolution monitors like 1080K
    _max_trim_buttons =  60     # for 4K resolution monitor, set 33 (10 x 3 menu columns) for 1080K monitor
    _num_menu_columns = 1 # 3 trims were displayed in 2020, and changed the trim column to 1 in 2021
    trim_options = []
    num_column_shift = 2 #

    trim_dropdown_buttons_xpath = "//button[@data-test='select-menu']"  # The xpath for the trim selection drop-down button, which is repeated in 1-3 columns and multiple rows for each table
    trim_select_buttons_xpath = "//div[@class='dropdown-menu show']//button[@class='dropdown-item']"

    for geturl_attempt in range(0, max_attempts):
        print('URL Attempt ' + str(geturl_attempt + 1))
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
            driver.set_page_load_timeout(wait_sec)
            driver.implicitly_wait(5)
            time.sleep(sleep_sec)
            driver.get(url)
            # find and click main button to reveal drop-down menu
            menus = driver.find_elements_by_xpath(trim_dropdown_buttons_xpath)
            WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, trim_dropdown_buttons_xpath)))
            time.sleep(sleep_sec)
            menus[0].click() # click the first dropdown menu button. Assumes all menus contain the same trim list.
            # find trim buttons in drop-down menu
            trim_buttons = driver.find_elements_by_xpath(trim_select_buttons_xpath)
            WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))

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

    trim_groups_count = math.ceil(total_trims / _num_menu_columns)  # Number of trim groups (in groups of 3, add one if only 1-
    if _num_menu_columns == 1: trim_groups_count = 1
    last_group_count = total_trims % _num_menu_columns  # Length of last group
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
                df = []; df_tmp = []
                pass
            if trim_group == trim_groups_count - 1 and last_group_count != 0:  # Last (or only) trim group and less than 3 entries
                trims = pd.Series(range(last_group_count)) + trim_groups_count * trim_group
            elif _num_menu_columns == 1:
                trims = pd.Series(range(total_trims)) + trim_groups_count * trim_group
            else:
                trims = pd.Series(range(trim_groups_count)) + trim_groups_count * trim_group
            _num_trims_page = len(trims)
            if _num_menu_columns < total_trims and trim_groups_count == 1: _num_trims_page = total_trims
            if (_index < (trim_groups_count-1)) and total_trims >= _num_menu_columns and _num_menu_columns > 1:
                _num_trims_page=_num_menu_columns
            elif _num_menu_columns == 1:
                _num_trims_page = total_trims
            else:
                _num_trims_page = total_trims %_num_menu_columns
                if _num_menu_columns == 0: _num_trims_page = _num_menu_columns
            if _num_trims_page == 0: continue

            try:
                for i in range(_num_trims_page):
                    time.sleep(sleep_sec)
                    element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, trim_dropdown_buttons_xpath)))
                    time.sleep(sleep_3sec)
                    try:
                        if _num_menu_columns == 1:
                            element.click()
                        else:
                            menus[i].click()
                    except (NoSuchElementException, TimeoutException, UnboundLocalError):
                        driver.quit()
                        driver = webdriver.Chrome(executable_path=chromedriver, chrome_options=chromeOptions)
                        driver.get(url)
                        time.sleep(sleep_sec)
                        try:
                            element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, trim_dropdown_buttons_xpath)))
                            time.sleep(sleep_3sec)
                            if _num_menu_columns == 1:
                                element.click()
                            else:
                                menus = driver.find_elements_by_xpath(trim_dropdown_buttons_xpath)
                                menus[i].click()
                        except (NoSuchElementException, TimeoutException, UnboundLocalError):
                            print('element click Timeout')
                            continue
                    trims_text.append(trim_options[_index * _num_menu_columns + i])
                    element = WebDriverWait(driver, wait_sec).until(EC.element_to_be_clickable((By.XPATH, trim_select_buttons_xpath)))
                    dropdown_item = driver.find_elements_by_xpath(trim_select_buttons_xpath)[_index * _num_menu_columns + i]
                    actions = ActionChains(driver)
                    actions.move_to_element(dropdown_item).click().perform()
                    actions.reset_actions()

                    if table_list_count == 0:
                        time.sleep(sleep_sec)
                        table_list = pd.read_html(driver.page_source, header=0)
                    else:
                        soup = BeautifulSoup(driver.page_source, "lxml")
                        hp = HTMLTableParser()
                        table_list = hp.get_html_table(soup, trim_group, errorflag_1, errorflag_2, errorflag_3)
                    df_out = html_page_to_tables(table_list_count, table_list, _num_menu_columns, trims_text, i, trim_group, num_column_shift, df)
                    df = df_out

            except TimeoutException:
                if i == 0: errorflag_1 = 1
                if i == 1: errorflag_2 = 1
                if i == 2: errorflag_3 = 1
                readin_check[trims[i]] = 'READIN_ERROR'

    if DELETE_DISCONTINUED_MODELS == True:
        dfo = df.copy(deep=True)
        num_models = len(dfo.columns)
        for i in range(num_models - 1, 1, -1):  # deleted the "Discontinued' model
            _model_name = df.columns[i]
            print(i, _model_name)
            if 'Discontinued' in _model_name:
                df.drop(_model_name, axis=1, inplace=True)
                # df.drop(_model_name, axis=1, inplace=True)
        df.reset_index(drop=True, inplace=True)
    # df = est_max_towing_capacity(df)
    driver.close()
    return (df, readin_check)

def html_page_to_tables(table_list_count, table_list, _num_menu_columns, trims_text, i_trims_page, trim_group, num_column_shift, df):

    # if len(df_tmp) == 0: del df_tmp
    # if _num_menu_columns == 1:
    # try:
    #     del df_tmp  # important_tables
    # except NameError:
    #     pass

    num_table_list = len(table_list)
    if len(table_list[num_table_list-1]) < 1:
        del table_list[num_table_list-1]
        num_table_list = num_table_list - 1

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
        if table_check == 0: continue

        table_tag = raw_table.columns[0]
        if len(raw_table) > 0 and isinstance(raw_table, pd.DataFrame) and \
                not ("Highlights" in table_tag) \
                and table_tag != 'OVERVIEW':
            raw_table.columns = pd.Series(raw_table.columns).str.strip()

            if len(table_list[table_count].columns) > (1 + _num_menu_columns):
                for i in range(len(table_list[table_count].columns)-1, _num_menu_columns, -1):
                    del_colname = table_list[table_count].columns[i]
                    table_list[table_count].drop(del_colname, axis=1, inplace=True)
            try:
                # important_tables = important_tables.loc[:, ~important_tables.columns.duplicated()]
                # important_tables = pd.concat([important_tables, raw_table])
                if table_count == 0: df_tmp = pd.concat([df_tmp, raw_table])

                raw_table = raw_table.loc[:, ~raw_table.columns.duplicated()]
                name_category = table_list[table_count].columns[0]
                for i in range(_num_menu_columns):
                    table_list[table_count] = table_list[table_count].rename(columns={table_list[table_count].columns[1 + i]: trims_text[i_trims_page]})
                tmp_raw_table = table_list[table_count]
                if tmp_raw_table.columns[0] != 'Category': tmp_raw_table.insert(0, 'Category', '')
                tmp_raw_table['Category'] = name_category
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
                    tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, front_headrests, 'front headrests')
                    tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, rear_headrests, 'rear headrests')
                    tmp_raw_table = drop_merged_option(tmp_raw_table, _num_menu_columns)
                # elif str(tmp_raw_table['Category'][0]).lower() == 'in-car entertainment' and (len(subwoofers)  > 0 or len(total_speakers)  > 0 or len(months_of_provided_satellite_radio_service) > 0 or len(watts_stereo_output) > 0):
                #     if len(subwoofers)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table,_num_menu_columns, subwoofers, 'subwoofer(s)')
                #     if len(total_speakers)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table,_num_menu_columns, total_speakers, 'total speakers')
                #     if len(months_of_provided_satellite_radio_service) > 0:
                #         tmp_raw_table = merge_trim_options(tmp_raw_table,_num_menu_columns, months_of_provided_satellite_radio_service, 'Months of provided satellite radio service')
                #     if len(watts_stereo_output) > 0: tmp_raw_table = merge_trim_options(tmp_raw_table,_num_menu_columns, watts_stereo_output, 'watts stereo output')
                #     tmp_raw_table = drop_merged_option(tmp_raw_table,_num_menu_columns)
                elif str(tmp_raw_table['Category'][0]).lower() == 'tires & wheels' and (len(tires)  > 0 or len(wheels) > 0):
                    tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, tires, 'tires')
                    tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, wheels, 'wheels')
                    tmp_raw_table = trim_tires_wheels(tmp_raw_table, _num_menu_columns)
                    tmp_raw_table = drop_merged_option(tmp_raw_table, _num_menu_columns)
                elif str(tmp_raw_table['Category'][0]).lower() == 'front seats' and (len(power_driver_seat)  > 0 or len(power_passenger_seat)  > 0 or len(manual_driver_seat_adjustment) > 0 or len(manual_passenger_seat_adjustment) > 0):
                    if len(power_driver_seat)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, power_driver_seat, 'power driver seat')
                    if len(power_passenger_seat)  > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, power_passenger_seat, 'power passenger seat')
                    if len(manual_driver_seat_adjustment) > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, manual_driver_seat_adjustment, 'manual driver seat adjustment')
                    if len(manual_passenger_seat_adjustment) > 0: tmp_raw_table = merge_trim_options(tmp_raw_table, _num_menu_columns, manual_passenger_seat_adjustment, 'manual passenger seat adjustment')
                    tmp_raw_table = drop_merged_option(tmp_raw_table, _num_menu_columns)
                elif str(tmp_raw_table['Category'][0]).lower() == 'overview' or str(tmp_raw_table['Category'][0]).lower() == 'drivetrain' or \
                        str(tmp_raw_table['Category'][0]).lower() == 'fuel & mpg' or str(tmp_raw_table['Category'][0]).lower() == 'engine' or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'comfort & convenience' and SKIP_PRINTING_COMFORT_CONVENIENCE == False) or \
                    str(tmp_raw_table['Category'][0]).lower() == 'measurements' or str(tmp_raw_table['Category'][0]).lower() == 'warranty':
                    tmp_raw_table = update_raw_tables(tmp_raw_table, _num_menu_columns)
                    tmp_raw_table = drop_merged_option(tmp_raw_table, _num_menu_columns)

                if (str(tmp_raw_table['Category'][0]).lower() == 'colors' and SKIP_PRINTING_COLORS == True) or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'exterior options' and SKIP_PRINTING_EXTERIOR_OPTIONS == True) or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'comfort & convenience' and SKIP_PRINTING_COMFORT_CONVENIENCE == True) or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'packages' and SKIP_PRINTING_PACKAGES == True) or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'in-car entertainment' and SKIP_IN_CAR_ENTERTAINMENT == True) or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'power feature' and SKIP_POWER_FEATURE == True) or \
                        (str(tmp_raw_table['Category'][0]).lower() == 'interior options' and SKIP_PRINTING_INTERIOR_OPTIONS == True):
                    continue
                else:
                    df_tmp = df_tmp.append(tmp_raw_table, ignore_index=True)
                    df_tmp.fillna('', inplace=True)
                if table_count == (num_table_list-1):
                    if (trim_group == 0 and _num_menu_columns > 1) or (i_trims_page == 0):
                        df = df_tmp
                    else:
                        df =  pd.merge(df, df_tmp, on=['Category', 'Specifications'], how='inner')
                        df = df.drop_duplicates(subset=['Specifications'])
            except NameError:
                df_tmp = table_list[table_count]
                name_category = table_list[table_count].columns[0]
                if df_tmp.columns[0] != 'Category': df_tmp.insert(0, 'Category', '')
                df_tmp['Category'] = name_category
                if df_tmp.columns[1] != 'Specifications': df_tmp = df_tmp.rename(columns={df_tmp.columns[0]: 'Category', df_tmp.columns[1]: 'Specifications'})
                for i in range(_num_menu_columns): df_tmp = df_tmp.rename(columns={df_tmp.columns[num_column_shift + i]: trims_text[i_trims_page]})
                df_tmp = update_raw_tables(df_tmp, _num_menu_columns)
                df_tmp = drop_merged_option(df_tmp, _num_menu_columns)
    return df
