"""

**INPUT FILE FORMAT**

The file consists of several Worksheets within an Excel Workbook and should be saved in a folder named
"inputs" within the omega_preproc/alpha_package_costs Python package. Note that throughout the input file cost values must be entered with
a "dollar_basis" term which denotes the dollar-year for the cost estimate (i.e., is the cost in 2012 dollars? 2018 dollars?).

The individual Worksheets and their contents are:

inputs_code
    :run_ID:
        A user defined ID for the given run of the alpha_package_costs module. This run_ID will be included in the output filename.
    :optional_run_description:
        An optional description for the run. This is not used other than here.
    :dollar_basis_for_output_file:
        The dollar basis desired for the module output file(s). Note that this dollar basis will be converted within OMEGA (if necessary) for consistency with the OMEGA run.
    :start_year:
        The start year for cost calculations and the year from which learning effects will occur.
    :end_year:
        The last year for cost calculations.
    :learning_rate_weight:
        The year-over-year learning rate to be applied to weight-related technologies.
    :learning_rate_ice_powertrain:
        The year-over-year learning rate to be applied to ICE and HEV powertrain technologies.
    :learning_rate_roadload:
        The year-over-year learning rate to be applied to roadload related technologies.
    :learning_rate_bev:
        The year-over-year learning rate to be applied to BEV related technologies (battery/motor).
    :learning_rate_phev:
        The year-over-year learning rate to be applied to PHEV related technologies (battery/motor).
    :boost_multiplier:
        The cost multiplier to be applied to ICE engine cylinder and displacement costs to reflect the extra costs associated with boost.

inputs_workbook
    :Markup:
        The indirect cost markup factor to use within the workbook.
    :AWD_scaler:
        The multiplier to be applied to transmission costs for any vehicle with AWD.

electrified_metrics
    :usable_soc:
        The usable state-of-charge for a BEV/PHEV/HEV battery.
    :gap:
        The on-road "gap" for a BEV/PHEV/HEV.
    :electrification_markup:
        The indirect cost multiplier to be used for BEV/PHEV/HEV related costs (battery/motor)
    :co2_reduction_cycle_hev:
        The 2-cycle CO2 reduction provided by adding electrification tech.
    :co2_reduction_city_hev:
        The city-cycle CO2 reduction provided by adding electrification tech.
    :co2_reduction_hwy_hev:
        The highway-cycle CO2 reduction provided by adding electrification tech.

bev_curves, phev_curves and hev_curves

    These entries are curves according to the equation (Ax^3 +Bx^2 + Cx + D), where the capital letters are the entries in the worksheet and x is the attribute.

    :kWh_pack_per_kg_curbwt_curve:
        The gross energy content per kilogram of curb weight.
    :kW_motor_per_kg_curbwt_curve:
        The motor power per kilogram of curb weight.
    :dollars_per_kWh_curve:
        The battery cost per kWh.
    :kWh_pack_per_kg_pack_curve:
        The energy density of the battery pack.

bev_nonbattery_single, bev_nonbattery_dual, phev_nonbattery_single, phev_nonbattery_dual, and hev_nonbattery

    The quantity, cost curve slopes and intercepts, the cost scalers (e.g., vehicle/motor power, vehicle size) and dollar-basis can be
    set for each of the following "non-battery" components

    :motor:

    :inverter:

    :induction_motor:

    :induction_inverter:

    :kW_DCDC_converter:
        DC to DC converter power in kW.

    :OBC_and_DCDC_converter:

    :HV_orange_cables:

    :LV_battery:

    :HVAC:

    :single_speed_gearbox:

    :powertrain_cooling_loop:

    :charging_cord_kit:

    :DC_fast_charge_circuitry:

    :power_management_and_distribution:

    :brake_sensors_actuators:

    :additional_pair_of_half_shafts:

price_class
    A concept that would allow for different cost scalers depending on the luxury/economy/etc. class of a vehicle package. This is not being used.

engine
    Cost entries for engine-related technologies (e.g., dollars per cylinder, dollars per liter, direct injection, turbocharging, etc.).

trans
    Cost entries for transmissions.

accessory
    Cost entries for accessory technologies (e.g., electric power steering).

start-stop
    Cost entries for start-stop technology; these vary by curb weight.

weight_ice and weight_bev
    Cost entries associated with weight for ICE/PHEV/HEV and for BEV; these vary by ladder-frame vs. unibody.

aero and nonaero
    Cost entries for roadload aero and nonaero tech, respectively; these vary by ladder-frame and unibody.

ac
    Cost entries air conditioning related tech needed to earn the full AC credit (both leakage and efficiency).

et_dmc
    Cost entries for individual techs; some of these costs are pulled into the sheets above for calculations.
    These costs are from EPA's past GHG work.

----

**CODE**

"""


import pandas as pd
import numpy as np
from datetime import datetime
import shutil
import matplotlib.pyplot as plt
from pathlib import Path

from omega_preproc.context_aeo import SetInputs as context_aeo_inputs


weight_cost_cache = dict()


class RuntimeSettings:
    """

    The RuntimeSettings class determines what costs to calculate and what, if any, simulated_vehicles files to generate by setting entries
    equal to True or False.

    """
    def __init__(self):
        """

        Make runtime selections.

        """
        # set what to run (i.e., what outputs to generate)
        self.run_ice = True
        self.run_bev = True
        self.run_phev = False
        self.run_hev = True
        self.generate_simulated_vehicles_file = True
        self.generate_simulated_vehicles_verbose_file = False

        # set tech to track via tech flags
        self.set_tech_tracking_flags = True


class InputSettings:
    """

    The InputSettings class sets input values for this module as well as reading the input file and creating dictionaries for use throughout the module.

    """
    def __init__(self):
        """

        Read input files and convert monetized values to a consistent dollar basis.

        """
        self.path_to_file = Path(__file__).parent
        self.path_preproc = self.path_to_file.parent
        self.path_project = self.path_preproc.parent
        self.path_inputs = self.path_to_file / 'inputs'
        self.path_outputs = self.path_to_file / 'outputs'
        self.path_alpha_inputs = self.path_to_file / 'ALPHA'
        self.path_input_templates = self.path_project / 'omega_model/test_inputs'

        self.tech_flag_tracking = ['ac_leakage', 'ac_efficiency', 'high_eff_alternator', 'start_stop', 'hev', 'hev_truck', 'phev', 'bev',
                                   'weight_reduction', 'curb_weight', 'deac_pd', 'deac_fc', 'cegr', 'atk2', 'gdi', 'turb12', 'turb11',
                                   ]

        self.start_time_readable = datetime.now().strftime('%Y%m%d-%H%M%S')

        # set input filenames
        self.gdp_deflators_file = self.path_input_templates / 'implicit_price_deflators.csv'
        self.techcosts_file = pd.ExcelFile(self.path_inputs / 'alpha_package_costs_module_inputs.xlsx')

        try:
            self.gdp_deflators = pd.read_csv(self.gdp_deflators_file, skiprows=1, index_col=0).to_dict('index')
            # set inputs
            self.inputs_code = pd.read_excel(self.techcosts_file, 'inputs_code', index_col=0).to_dict('index')
            self.dollar_basis_for_output_file = int(self.inputs_code['dollar_basis_for_output_file']['value'])
            self.start_year = int(self.inputs_code['start_year']['value'])
            self.end_year = int(self.inputs_code['end_year']['value'])
            self.years = range(self.start_year, self.end_year + 1)
            self.learning_dict = {'learning_rate': self.inputs_code['learning_rate']['value'],
                                  'weight_scaler': self.inputs_code['weight_scaler']['value'],
                                  'roadload_scaler': self.inputs_code['roadload_scaler']['value'],
                                  'ice_scaler': self.inputs_code['ice_scaler']['value'],
                                  'pev_scaler': self.inputs_code['pev_scaler']['value'],
                                  'weight_sales_scaler': self.inputs_code['weight_sales_scaler']['value'],
                                  'roadload_sales_scaler': self.inputs_code['roadload_sales_scaler']['value'],
                                  'ice_sales_scaler': self.inputs_code['ice_sales_scaler']['value'],
                                  'pev_sales_scaler': self.inputs_code['pev_sales_scaler']['value'],
                                  }
            # self.learning_rate_weight = self.inputs_code['learning_rate_weight']['value']
            # self.learning_rate_ice_powertrain = self.inputs_code['learning_rate_ice_powertrain']['value']
            # self.learning_rate_roadload = self.inputs_code['learning_rate_roadload']['value']
            # self.learning_rate_bev = self.inputs_code['learning_rate_bev']['value']
            # self.learning_rate_phev = self.inputs_code['learning_rate_phev']['value']
            # self.learning_rate_aftertreatment = self.inputs_code['learning_rate_aftertreatment']['value']
            self.pt_dollars_per_troy_oz = self.inputs_code['Pt_dollars_per_troy_oz']['value']
            self.pd_dollars_per_troy_oz = self.inputs_code['Pd_dollars_per_troy_oz']['value']
            self.rh_dollars_per_troy_oz = self.inputs_code['Rh_dollars_per_troy_oz']['value']
            self.boost_multiplier = self.inputs_code['boost_multiplier']['value']
            self.run_id = self.inputs_code['run_ID']['value']
            if self.run_id != 0:
                self.name_id = f'{self.run_id}_{self.start_time_readable}'
            else:
                self.name_id = self.start_time_readable

            # read cost sheets from the tech costs input file, convert dollar values to consistent dollar basis, and create dictionaries
            self.price_class_dict \
                = pd.read_excel(self.techcosts_file, 'price_class', index_col=0).to_dict('index')
            self.engine_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'engine', 'item_cost', 'dmc').to_dict('index')
            self.trans_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'trans', 'item_cost', 'dmc', 'dmc_increment').to_dict('index')
            self.accessories_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'accessories', 'item_cost', 'dmc').to_dict('index')
            self.startstop_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'start-stop', 'item_cost', 'dmc').to_dict('index')
            self.weight_cost_ice_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'weight_ice', 'item_cost', 'dmc_per_pound').to_dict('index')
            self.weight_cost_bev_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'weight_bev', 'item_cost', 'dmc_per_pound').to_dict('index')
            self.aero_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'aero', 'item_cost', 'dmc').to_dict('index')
            self.nonaero_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'nonaero', 'item_cost', 'dmc').to_dict('index')
            self.ac_cost_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'ac', 'item_cost', 'dmc').to_dict('index')

            self.bev_curves_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'bev_curves', 'x_cubed_factor',
                                                                 'x_squared_factor',
                                                                 'x_factor', 'constant').to_dict('index')
            self.phev_curves_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'phev_curves', 'x_cubed_factor',
                                                                 'x_squared_factor',
                                                                 'x_factor', 'constant').to_dict('index')
            self.hev_curves_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'hev_curves', 'x_cubed_factor',
                                                                 'x_squared_factor',
                                                                 'x_factor', 'constant').to_dict('index')

            self.bev_nonbattery_single_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'bev_nonbattery_single',
                                                                 'slope', 'intercept').to_dict('index')
            self.bev_nonbattery_dual_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'bev_nonbattery_dual',
                                                                 'slope', 'intercept').to_dict('index')
            self.phev_nonbattery_single_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'phev_nonbattery_single',
                                                                 'slope', 'intercept').to_dict('index')
            self.phev_nonbattery_dual_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'phev_nonbattery_dual',
                                                                 'slope', 'intercept').to_dict('index')
            self.hev_nonbattery_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'hev_nonbattery',
                                                                 'slope', 'intercept').to_dict('index')

            self.electrified_metrics_dict = pd.read_excel(self.techcosts_file, sheet_name='electrified_metrics', index_col=0).to_dict('index')

            self.aftertreatment_dict \
                = self.create_cost_df_in_consistent_dollar_basis(self.gdp_deflators,
                                                                 self.dollar_basis_for_output_file,
                                                                 self.techcosts_file,
                                                                 'aftertreatment',
                                                                 'dmc_slope', 'dmc_intercept').to_dict('index')

            self.ice_glider_share = 0.85
            self.bev_glider_share = 1

            # for now, set a BEV range and motor power here
            self.onroad_bev_range_miles = 300
            self.bev_motor_power = 150
            self.bev_weight_reduction = 0

            self.onroad_phev_range_miles = 40
            # self.phev_weight_reduction = 0

            self.pev_size_bins = 7
            # for now, set HEV size bins here
            self.hev_size_bins = 7
            self.bin_size_scaling_interval = 0.05 # not being used
            self.bin_with_scaler_equal_1 = 3 # not being used

            # set constants
            self.lbs_per_kg = 2.2
            self.grams_per_troy_oz = 31.1

        except:
            import traceback
            print(traceback.format_exc())

    def create_cost_df_in_consistent_dollar_basis(self, deflators, dollar_basis, file, sheet_name, *args, index_col=0):
        """

        Args:
            deflators: A dictionary of GDP deflators with years as the keys.
            dollar_basis: The dollar basis to which all monetized values are to be converted.
            file: The file containing monetized values to be converted into dollar_basis dollars.
            sheet_name: The specific worksheet within file for which monetized values are to be converted.
            args: The arguments to be converted.

        Returns:
             A DataFrame of monetized values in a consistent dollar_basis valuation.

        """
        df = pd.read_excel(file, sheet_name, index_col=index_col)
        df = self.convert_dollars_to_analysis_basis(df, deflators, dollar_basis, *args)
        return df

    def convert_dollars_to_analysis_basis(self, df, deflators, dollar_basis_year, *args):
        """

        Args:
            df: The DataFrame of values to be converted to a consistent dollar basis.
            deflators: A dictionary of price deflators.
            dollar_basis_year: An integer representing the desired dollar basis for the return DataFrame.
            args: The attributes to be converted to a consistent dollar basis.

        Returns:
            The passed DataFrame with args expressed in a consistent dollar basis.

        """
        basis_years = pd.Series(df.loc[df['dollar_basis'] > 0, 'dollar_basis']).unique()
        adj_factor_numerator = deflators[dollar_basis_year]['price_deflator']
        df_return = df.copy()
        for basis_year in basis_years:
            adj_factor = adj_factor_numerator / deflators[basis_year]['price_deflator']
            for arg in args:
                df_return.loc[df_return['dollar_basis'] == basis_year, arg] = df_return[arg] * adj_factor
        df_return['dollar_basis'] = dollar_basis_year
        return df_return


class AlphaData:
    """

    The AlphaData class reads an ALPHA file, cleans data and adds elements used in the Package Key that uniquely identifies every package in
    the simulated_vehicles.csv file.

    """

    @staticmethod
    def read_alpha_file(alpha_file):
        return pd.read_csv(alpha_file, skiprows=range(1, 2))

    @staticmethod
    def clean_alpha_data(df, *args):
        """

        Args:
            input_df: A DataFrame based on a single ALPHA file is which some data is to be cleaned.
            args: The arguments for which cleaning is to be done.

        Returns:
            The passed DataFrame with data cleaned (text values converted to integers, % signs removed, etc.).

        """
        # clean data with percent signs
        df_clean = df.copy()
        df_clean = pd.DataFrame(df_clean.loc[df_clean['Engine'] != 'engine_future_Ricardo_EGRB_1L0_Tier2', :])
        args_to_clean = [arg for arg in df_clean.columns.tolist() if arg in args]
        for arg in args_to_clean:
            df_clean = df_clean.join(df_clean[arg].str.split('.', expand=True))
            df_clean.drop(columns=[arg, 1], inplace=True)
            df_clean.rename(columns={0: arg}, inplace=True)
            df_clean[arg] = pd.to_numeric(df_clean[arg])

        return df_clean

    @staticmethod
    def add_elements_for_package_key(df):
        """

        Args:
            df: A DataFrame of ALPHA packages for which columns are to be created for use in the package key.

        Returns:
            The passed DataFrame with additional columns for use in the package key.

        """
        df_return = df.copy().fillna(0)
        df_return = pd.DataFrame(df_return.loc[df_return['Vehicle Type'] != 0, :]).reset_index(drop=True)
        df_return.insert(0, 'Structure Class', 'unibody')
        for index, row in df_return.iterrows():
            if row['Vehicle Type'] == 'Truck':
                df_return.loc[index, 'Structure Class'] = 'ladder'
            else:
                pass

        df_return.insert(df_return.columns.get_loc('Key'), 'Price Class', 1)

        return df_return

    @staticmethod
    def create_package_dict(input_settings, input_df, fuel_key):
        """

        Args:
            input_settings: The InputSettings class.
            input_df (DataFrame): ALPHA packages having the passed fuel_id (i.e., 'ice', 'bev', 'hev').
            fuel_key (string): The fuel ID (i.e., 'ice', 'bev', 'hev').

        Returns:
            The passed DataFrame converted to a dictionary having method-created package_keys as the dictionary keys.

        """
        key_methods = PackageKeyMethods()
        df = input_df.copy().fillna(0)
        alpha_keys = pd.Series(df['Key']) # directly from the ALPHA file
        fuel_keys = pd.Series([fuel_key] * len(df))
        structure_keys = pd.Series(df['Structure Class']) # added via the add_elements_for_package_key method
        price_keys = pd.Series(df['Price Class']) # added via the add_elements_for_package_key method
        alpha_class_keys = pd.Series(df['Vehicle Type']) # directly from the ALPHA file

        # create engine_keys
        if fuel_key != 'bev':
            engine_keys = pd.Series(zip(df['Engine'], df['Engine Displacement L'], df['Engine Cylinders'].astype(int),
                                        df['DEAC D Cyl.'].astype(int), df['DEAC C Cyl.'].astype(int), df['Start Stop']))
        else:
            engine_keys = pd.Series([0] * len(df))

        # create pev_keys and hev_keys
        if fuel_key == 'ice':
            hev_keys = pd.Series([0] * len(df))
            pev_keys = pd.Series([0] * len(df))

        if fuel_key == 'bev':
            hev_keys = pd.Series([0] * len(df))
            battery_kwh_gross_list = key_methods.calc_battery_kwh_gross(input_settings, df, fuel_key)
            # determine onboard charger specs
            onboard_charger_kw_list = list()
            for battery_kwh_gross in battery_kwh_gross_list:
                if battery_kwh_gross < 70:
                    onboard_charger_kw_list.append(7)
                elif 70 <= battery_kwh_gross < 100:
                    onboard_charger_kw_list.append(11)
                else:
                    onboard_charger_kw_list.append(19)
            # determine single or dual motor bev
            number_of_motors_list = list()
            for structure_class in structure_keys:
                if structure_class == 'unibody':
                    number_of_motors_list.append('single')
                else:
                    number_of_motors_list.append('dual')

            # add size scaler to key where size scaler is based on curb weight and scales non-battery costs for PEV and HEV packages
            size_scaler_list = pd.cut(df['Test Weight lbs'] - 300, input_settings.pev_size_bins,
                                      labels=list(range(1, input_settings.pev_size_bins + 1)))

            range_list = [input_settings.onroad_bev_range_miles] * len(df)
            usable_soc_list = [input_settings.electrified_metrics_dict['usable_soc'][fuel_key]] * len(df)
            gap_list = [input_settings.electrified_metrics_dict['gap'][fuel_key]] * len(df)
            motor_power_list = [input_settings.bev_motor_power] * len(df)
            pev_keys = pd.Series(zip(range_list,
                                     df['Combined Consumption Rate'] / 100,
                                     usable_soc_list,
                                     gap_list,
                                     battery_kwh_gross_list,
                                     motor_power_list,
                                     number_of_motors_list,
                                     onboard_charger_kw_list,
                                     size_scaler_list))

        if fuel_key == 'hev':
            pev_keys = pd.Series([0] * len(df))
            battery_kwh_gross_list = df['battery_kwh_gross']
            motor_kw_list = df['motor_kw']

            # add size scaler to key where size scaler is based on curb weight and scales non-battery costs for PEV and HEV packages
            size_scaler_list = pd.cut(df['Test Weight lbs'] - 300, input_settings.hev_size_bins,
                                      labels=list(range(1, input_settings.hev_size_bins + 1)))

            usable_soc_list = [input_settings.electrified_metrics_dict['usable_soc'][fuel_key]] * len(df)
            gap_list = [input_settings.electrified_metrics_dict['gap'][fuel_key]] * len(df)
            hev_keys = pd.Series(zip(usable_soc_list,
                                     gap_list,
                                     battery_kwh_gross_list,
                                     motor_kw_list,
                                     size_scaler_list))

        if fuel_key == 'phev':
            hev_keys = pd.Series([0] * len(df))
            battery_kwh_gross_list = df['battery_kwh_gross']
            motor_kw_list = df['motor_kw']
            # determine onboard charger specs
            onboard_charger_kw_list = list()
            for battery_kwh_gross in battery_kwh_gross_list:
                if battery_kwh_gross < 7:
                    onboard_charger_kw_list.append(.7)
                elif 7 <= battery_kwh_gross < 10:
                    onboard_charger_kw_list.append(1.1)
                else:
                    onboard_charger_kw_list.append(1.9)
            # determine single or dual motor bev
            number_of_motors_list = list()
            for structure_class in structure_keys:
                if structure_class == 'unibody':
                    number_of_motors_list.append('single')
                else:
                    number_of_motors_list.append('dual')

            # add size scaler to key where size scaler is based on curb weight and scales non-battery costs for PEV and HEV packages
            size_scaler_list = pd.cut(df['Test Weight lbs'] - 300, input_settings.pev_size_bins,
                                      labels=list(range(1, input_settings.pev_size_bins + 1)))

            range_list = [input_settings.onroad_phev_range_miles] * len(df)
            usable_soc_list = [input_settings.electrified_metrics_dict['usable_soc'][fuel_key]] * len(df)
            gap_list = [input_settings.electrified_metrics_dict['gap'][fuel_key]] * len(df)
            pev_keys = pd.Series(zip(range_list,
                                     df['Combined Consumption Rate'] / 100,
                                     usable_soc_list,
                                     gap_list,
                                     battery_kwh_gross_list,
                                     motor_kw_list,
                                     number_of_motors_list,
                                     onboard_charger_kw_list,
                                     size_scaler_list))

        # create trans_keys
        if fuel_key != 'bev':
            trans_keys = pd.Series(df['Transmission'])
        else:
            trans_keys = pd.Series([0] * len(df))

        # create accessory_keys
        if fuel_key != 'bev':
            accessory_keys = pd.Series(df['Accessory'])
        else:
            accessory_keys = pd.Series(['REGEN'] * len(df))

        # create aero_keys
        if fuel_key != 'bev':
            aero_keys = pd.Series(df['Aero Improvement %'])
        else:
            aero_keys = pd.Series([20] * len(df))

        # create nonaero_keys
        if fuel_key != 'bev':
            nonaero_keys = pd.Series(df['Crr Improvement %'])
        else:
            nonaero_keys = pd.Series([20] * len(df))

        # create weight_keys
        curb_weights_series = pd.Series(df['Test Weight lbs'] - 300)

        if fuel_key == 'ice':
            battery_weight_list = pd.Series([0] * len(df))
            glider_weight_list = key_methods.calc_glider_weight(fuel_key, input_settings, battery_weight_list, curb_weights_series)
            weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, df['Weight Reduction %']))
        if fuel_key == 'bev':
            battery_weight_list = key_methods.calc_battery_weight(input_settings, battery_kwh_gross_list, input_settings.bev_curves_dict)
            glider_weight_list = key_methods.calc_glider_weight(fuel_key, input_settings, battery_weight_list, curb_weights_series)
            weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list,
                                        [input_settings.bev_weight_reduction] * len(df)))
        if fuel_key == 'phev':
            battery_weight_list = key_methods.calc_battery_weight(input_settings, battery_kwh_gross_list, input_settings.phev_curves_dict)
            glider_weight_list = key_methods.calc_glider_weight(fuel_key, input_settings, battery_weight_list, curb_weights_series)
            weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, df['Weight Reduction %']))
        if fuel_key == 'hev':
            battery_weight_list = key_methods.calc_battery_weight(input_settings, battery_kwh_gross_list, input_settings.hev_curves_dict)
            glider_weight_list = key_methods.calc_glider_weight(fuel_key, input_settings, battery_weight_list, curb_weights_series)
            weight_keys = pd.Series(zip(curb_weights_series, glider_weight_list, battery_weight_list, df['Weight Reduction %']))

        else:
            pass

        # create cost_keys
        cost_keys = pd.Series(zip(fuel_keys, structure_keys, price_keys, alpha_class_keys,
                                  engine_keys, hev_keys, pev_keys,
                                  trans_keys, accessory_keys, aero_keys, nonaero_keys, weight_keys))

        # create dict_keys
        keys = pd.Series(zip(alpha_keys, cost_keys))

        # add keys to df
        df.insert(0, 'cost_key', cost_keys)
        df.insert(0, 'alpha_key', alpha_keys)
        df.insert(0, 'key', keys)

        # create dict
        df.set_index('key', inplace=True)
        df_dict = df.to_dict('index')
        
        return df_dict


class PackageKeyMethods:

    @staticmethod
    def calc_battery_kwh_gross(input_settings, input_df, fuel_key):
        """

        The calc_battery_kwy_gross method is used by the package dict function to create needed battery characteristics from the ALPHA file.

        Args:
            input_settings: The InputSettings class.
            input_df: A DataFrame of plug-in vehicles for which battery gross kWh is to be calculated based on values set in the module's input file.
            fuel_key: A string designating whether the package is ICE/HEV/PHEV/BEV.

        Returns:
            A list of gross kWh values indexed exactly as the input_df.

        """
        onroad_range = input_settings.onroad_bev_range_miles
        usable_soc = input_settings.electrified_metrics_dict['usable_soc'][fuel_key]
        gap = input_settings.electrified_metrics_dict['gap'][fuel_key]
        battery_kwh_list = list()

        for kwh_per_100_miles in input_df['Combined Consumption Rate']:
            battery_kwh = (onroad_range / usable_soc) * (kwh_per_100_miles / 100) / (1 - gap)
            battery_kwh_list.append(battery_kwh)

        return battery_kwh_list

    @staticmethod
    def calc_battery_weight(input_settings, battery_kwh_list, curves_dict):
        """

        The calc_battery_weight method is used by the package dict function to create needed battery characteristics from the ALPHA file.

        Args:
            input_settings: The InputSettings class.
            battery_kwh_list: A list of gross battery kWh values for which battery weights are to be calculated.
            curves_dict: A dictionary of battery metrics including kWh_pack_per_kg_pack_curve.

        Returns:
            A list of battery weights for each of the batteries in the passed battery_kwh_list.

        """
        attribute = 'kWh_pack_per_kg_pack_curve'

        battery_weight_list = list()
        a = curves_dict[attribute]['x_cubed_factor']
        b = curves_dict[attribute]['x_squared_factor']
        c = curves_dict[attribute]['x_factor']
        d = curves_dict[attribute]['constant']

        for battery_kwh in battery_kwh_list:
            battery_weight = input_settings.lbs_per_kg * battery_kwh \
                             / (a * battery_kwh ** 3 + b * battery_kwh ** 2 + c * battery_kwh + d)
            battery_weight_list.append(battery_weight)

        return battery_weight_list

    @staticmethod
    def calc_glider_weight(fuel_key, input_settings, battery_weight_list, curb_weight_series):
        """
        Args:
            fuel_key: A string indicating whether the package is ICE/HEV/PHEV/BEV.
            input_settings: The InputSettings class.
            battery_weight_list: A list of battery weights.
            curb_weight_series: A Series of curb weights.

        Returns:
            A list of glider weights for fuel_id vehicles having the curb weights and battery weights according to the passed lists.

        """
        glider_weight_list = list()

        if fuel_key == 'bev':
            glider_share = input_settings.bev_glider_share
        else:
            glider_share = input_settings.ice_glider_share

        for idx, battery_weight in enumerate(battery_weight_list):
            glider_wt = curb_weight_series[idx] * glider_share - battery_weight
            glider_weight_list.append(glider_wt)

        return glider_weight_list


class Engine:
    """

    The Engine class defines specific technologies on each ALPHA engine benchmarked by EPA and calculates the cost of the engine.

    """
    def __init__(self, key=None):
        if key:
            self.engine_key, self.weight_key, self.fuel_key = PackageCost(key).get_object_attributes(['engine_key', 'weight_key', 'fuel_key'])
        self._engines = {'engine_2013_GM_Ecotec_LCV_2L5_PFI_Tier3': {'turb': '',
                                                                     'finj': 'PFI',
                                                                     'atk': '',
                                                                     'cegr': '',
                                                                     },
                         'engine_2013_GM_Ecotec_LCV_2L5_Tier3': {'turb': '',
                                                                 'finj': 'DI',
                                                                 'atk': '',
                                                                 'cegr': '',
                                                                 },
                         'engine_2014_GM_EcoTec3_LV3_4L3_Tier2_PFI_no_deac': {'turb': '',
                                                                              'finj': 'PFI',
                                                                              'atk': '',
                                                                              'cegr': '',
                                                                              },
                         'engine_2014_GM_EcoTec3_LV3_4L3_Tier2_no_deac': {'turb': '',
                                                                          'finj': 'DI',
                                                                          'atk': '',
                                                                          'cegr': '',
                                                                          },
                         'engine_2015_Ford_EcoBoost_2L7_Tier2': {'turb': 'TURB11',
                                                                 'finj': 'DI',
                                                                 'atk': '',
                                                                 'cegr': '',
                                                                 },
                         'engine_2013_Ford_EcoBoost_1L6_Tier2': {'turb': 'TURB11',
                                                                 'finj': 'DI',
                                                                 'atk': '',
                                                                 'cegr': '',
                                                                 },
                         'engine_2016_Honda_L15B7_1L5_Tier2': {'turb': 'TURB12',
                                                               'finj': 'DI',
                                                               'atk': '',
                                                               'cegr': 'CEGR',
                                                               },
                         'engine_2014_Mazda_Skyactiv_US_2L0_Tier2': {'turb': '',
                                                                     'finj': 'DI',
                                                                     'atk': 'ATK2',
                                                                     'cegr': '',
                                                                     },
                         'engine_2016_toyota_TNGA_2L5_paper_image': {'turb': '',
                                                                     'finj': 'DI',
                                                                     'atk': 'ATK2',
                                                                     'cegr': 'CEGR',
                                                                     },
                         'engine_future_EPA_Atkinson_r2_2L5': {'turb': '',
                                                               'finj': 'DI',
                                                               'atk': 'ATK2',
                                                               'cegr': 'CEGR',
                                                               },
                         'engine_future_Ricardo_EGRB_1L0_Tier2': {'turb': 'TURB12',
                                                                  'finj': 'DI',
                                                                  'atk': '',
                                                                  'cegr': 'CEGR',
                                                                  },
                         }

    def get_engine_techs(self, name=None):
        """

        Args:
            name (string): Optional engine_name, used for the make_hev_from_alpha_ice module.
        Returns:
            The technology cost codes for specific engine technologies.

        """
        if name:
            engine_name = name
        else:
            engine_name = self.engine_key[0]
        turb, finj, atk, cegr = self._engines.get(engine_name).values()

        return turb, finj, atk, cegr

    def calc_engine_cost(self, input_settings):
        """

        Args:
            input_settings: The InputSettings class.
            key (Tuple): The full package key.

        Returns:
            A numeric value representing the cost of the given engine.

        """
        # parse data from keys
        engine_name, disp, cyl, deacpd, deacfc, startstop = self.engine_key
        turb, finj, atk, cegr = self.get_engine_techs()
        curb_wt, glider_weight, battery_weight, weight_rdxn = self.weight_key

        # sum the costs for each tech
        cost = disp * input_settings.engine_cost_dict['dollars_per_liter']['item_cost']
        cost += cyl * input_settings.engine_cost_dict[f'dollars_per_cyl_{cyl}']['item_cost']
        # if turbo, apply boost multiplier to disp and cyl costs, then add the turbo cost
        if turb: cost += cost * (input_settings.boost_multiplier - 1) + input_settings.engine_cost_dict[f'{turb}_{cyl}']['item_cost']
        if cegr: cost += input_settings.engine_cost_dict['CEGR']['item_cost']
        if finj: cost += input_settings.engine_cost_dict[f'DI_{cyl}']['item_cost']
        if deacpd != 0: cost += input_settings.engine_cost_dict[f'DeacPD_{cyl}']['item_cost']
        if deacfc != 0: cost += input_settings.engine_cost_dict[f'DeacFC']['item_cost']
        if atk: cost += input_settings.engine_cost_dict[f'ATK2_{cyl}']['item_cost']
        # reminder that ss_cost is included in HEV costs so not double counted here (PHEV?)
        ss_cost = 0
        if startstop == 1 and self.fuel_key == 'ice':
            for ss_key in input_settings.startstop_cost_dict.keys():
                if input_settings.startstop_cost_dict[ss_key]['curb_weight_min'] < curb_wt <= input_settings.startstop_cost_dict[ss_key]['curb_weight_max']:
                    ss_cost = input_settings.startstop_cost_dict[ss_key]['item_cost']
                else:
                    pass
            cost += ss_cost

        return cost


class Battery:

    def __init__(self, key):
        self.hev_key, self.pev_key, self.fuel_key = PackageCost(key).get_object_attributes(['hev_key', 'pev_key', 'fuel_key'])

    def calc_battery_cost(self, input_settings):
        """
        The calc_battery_cost method calculates the cost of the battery associated with electrification/hybridization.

        Args:
            input_settings: The InputSettings class.

        Returns:
            The battery cost for the given package.

        """
        battery_kwh_gross, markup = 0, 0
        curves_dict = dict()
        if self.fuel_key == 'bev':
            range, energy_rate, soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = self.pev_key
            curves_dict = input_settings.bev_curves_dict
            markup = input_settings.electrified_metrics_dict['electrification_markup'][self.fuel_key]

        if self.fuel_key == 'phev':
            range, energy_rate, soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = self.pev_key
            curves_dict = input_settings.phev_curves_dict
            markup = input_settings.electrified_metrics_dict['electrification_markup'][self.fuel_key]

        elif self.fuel_key == 'hev':
            soc, gap, battery_kwh_gross, motor_power, size_scaler = self.hev_key
            curves_dict = input_settings.hev_curves_dict
            markup = input_settings.electrified_metrics_dict['electrification_markup'][self.fuel_key]

        attribute = 'dollars_per_kWh_curve'
        a = curves_dict[attribute]['x_cubed_factor']
        b = curves_dict[attribute]['x_squared_factor']
        c = curves_dict[attribute]['x_factor']
        d = curves_dict[attribute]['constant']

        battery_cost = battery_kwh_gross \
                       * (a * battery_kwh_gross ** 3 + b * battery_kwh_gross ** 2 + c * battery_kwh_gross + d)
        battery_cost = battery_cost * markup

        return battery_cost


class NonBattery:

    def __init__(self, key):
        self.hev_key, self.pev_key, self.fuel_key = PackageCost(key).get_object_attributes(['hev_key', 'pev_key', 'fuel_key'])

    def calc_nonbattery_cost(self, input_settings):
        """
        The calc_motor_cost method calculates the cost of non-battery components of electrification/hybridization.

        Args:
            input_settings: The InputSettings class.

        Returns:
            The non-battery electrification cost (motors, inverters, etc.) for the given package.

        """
        motor_power = motor_power_divisor = dcdc_converter_plus_obc = size_scaler = markup = 0
        if self.fuel_key == 'bev':
            range, energy_rate, soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = self.pev_key
            if number_of_motors == 'single':
                nonbattery_dict = input_settings.bev_nonbattery_single_dict
                motor_power_divisor = 1
            else:
                nonbattery_dict = input_settings.bev_nonbattery_dual_dict
                motor_power_divisor = 2
            markup = input_settings.electrified_metrics_dict['electrification_markup'][self.fuel_key]
            dcdc_converter_plus_obc = nonbattery_dict['kW_DCDC_converter']['intercept'] + onboard_charger_kw

        elif self.fuel_key == 'phev':
            range, energy_rate, soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = self.pev_key
            if number_of_motors == 'single':
                nonbattery_dict = input_settings.phev_nonbattery_single_dict
                motor_power_divisor = 1
            else:
                nonbattery_dict = input_settings.phev_nonbattery_dual_dict
                motor_power_divisor = 2
            markup = input_settings.electrified_metrics_dict['electrification_markup'][self.fuel_key]
            dcdc_converter_plus_obc = nonbattery_dict['kW_DCDC_converter']['intercept'] + onboard_charger_kw

        elif self.fuel_key == 'hev':
            soc, gap, battery_kwh_gross, motor_power, size_scaler = self.hev_key
            nonbattery_dict = input_settings.hev_nonbattery_dict
            markup = input_settings.electrified_metrics_dict['electrification_markup'][self.fuel_key]
            onboard_charger_kw = 0
            motor_power_divisor = 1
            dcdc_converter_plus_obc = nonbattery_dict['kW_DCDC_converter']['intercept'] + onboard_charger_kw

        # get quantity, slope and intercept values from nonbattery_dict
        motor_quantity, inverter_quantity, induction_motor_quantity, induction_inverter_quantity, obc_and_dcdc_converter_quantity, \
        hv_orange_cables_quantity, lv_battery_quantity, hvac_quantity, single_speed_gearbox_quantity, powertrain_cooling_loop_quantity, \
        charging_cord_kit_quantity, dc_fast_charge_circuitry_quantity, power_management_and_distribution_quantity, \
        additional_pair_of_half_shafts_quantity, brake_sensors_actuators_quantity \
            = self.get_attribute_values(nonbattery_dict, 'quantity')

        motor_slope, inverter_slope, induction_motor_slope, induction_inverter_slope, obc_and_dcdc_converter_slope, \
        hv_orange_cables_slope, lv_battery_slope, hvac_slope, single_speed_gearbox_slope, powertrain_cooling_loop_slope, \
        charging_cord_kit_slope, dc_fast_charge_circuitry_slope, power_management_and_distribution_slope, \
        additional_pair_of_half_shafts_slope, brake_sensors_actuators_slope \
            = self.get_attribute_values(nonbattery_dict, 'slope')

        motor_intercept, inverter_intercept, induction_motor_intercept, induction_inverter_intercept, obc_and_dcdc_converter_intercept, \
        hv_orange_cables_intercept, lv_battery_intercept, hvac_intercept, single_speed_gearbox_intercept, powertrain_cooling_loop_intercept, \
        charging_cord_kit_intercept, dc_fast_charge_circuitry_intercept, power_management_and_distribution_intercept, \
        additional_pair_of_half_shafts_intercept, brake_sensors_actuators_intercept \
            = self.get_attribute_values(nonbattery_dict, 'intercept')
        
        motor_cost = motor_quantity * (motor_slope * motor_power / motor_power_divisor + motor_intercept)
        inverter_cost = inverter_quantity * (inverter_slope * motor_power / motor_power_divisor + inverter_intercept)
        induction_motor_cost = induction_motor_quantity * induction_motor_slope * motor_power / motor_power_divisor
        induction_inverter_cost = induction_inverter_quantity * induction_motor_slope * motor_power / motor_power_divisor
        obc_and_dcdc_converter_cost = obc_and_dcdc_converter_quantity * obc_and_dcdc_converter_slope * dcdc_converter_plus_obc
        hv_orange_cables_cost = hv_orange_cables_quantity * hv_orange_cables_slope * size_scaler + hv_orange_cables_intercept
        lv_battery_cost = lv_battery_quantity * lv_battery_slope * size_scaler + lv_battery_intercept
        hvac_cost = hvac_quantity * hvac_slope * size_scaler + hvac_intercept
        single_speed_gearbox_cost = single_speed_gearbox_quantity * single_speed_gearbox_intercept
        powertrain_cooling_loop_cost = powertrain_cooling_loop_quantity * powertrain_cooling_loop_intercept
        charging_cord_kit_cost = charging_cord_kit_quantity * charging_cord_kit_intercept
        dc_fast_charge_circuitry_cost = dc_fast_charge_circuitry_quantity * dc_fast_charge_circuitry_intercept
        power_management_and_distribution_cost = power_management_and_distribution_quantity * power_management_and_distribution_intercept
        additional_pair_of_half_shafts_cost = additional_pair_of_half_shafts_quantity * additional_pair_of_half_shafts_intercept
        brake_sensors_actuators_cost = brake_sensors_actuators_quantity * brake_sensors_actuators_intercept

        non_battery_cost = motor_cost + inverter_cost + induction_motor_cost + induction_inverter_cost \
                           + obc_and_dcdc_converter_cost + hv_orange_cables_cost + lv_battery_cost + hvac_cost \
                           + single_speed_gearbox_cost + powertrain_cooling_loop_cost + charging_cord_kit_cost \
                           + dc_fast_charge_circuitry_cost + power_management_and_distribution_cost \
                           + additional_pair_of_half_shafts_cost + brake_sensors_actuators_cost
        non_battery_cost = non_battery_cost * markup

        return non_battery_cost
    
    @staticmethod
    def get_attribute_values(nonbattery_dict, attribute):
        """

        Args:
            nonbattery_dict: Dictionary of non-battery curves.
            attribute: A string ('quantity', 'slope' or 'intercept')

        Returns:
            The attribute values of the requested attribute.
            
        """
        motor = nonbattery_dict['motor'][attribute]
        inverter = nonbattery_dict['inverter'][attribute]
        induction_motor = nonbattery_dict['induction_motor'][attribute]
        induction_inverter = nonbattery_dict['induction_inverter'][attribute]
        obc_and_dcdc_converter = nonbattery_dict['OBC_and_DCDC_converter'][attribute]
        hv_orange_cables = nonbattery_dict['HV_orange_cables'][attribute]
        lv_battery = nonbattery_dict['LV_battery'][attribute]
        hvac = nonbattery_dict['HVAC'][attribute]
        single_speed_gearbox = nonbattery_dict['single_speed_gearbox'][attribute]
        powertrain_cooling_loop = nonbattery_dict['powertrain_cooling_loop'][attribute]
        charging_cord_kit = nonbattery_dict['charging_cord_kit'][attribute]
        dc_fast_charge_circuitry = nonbattery_dict['DC_fast_charge_circuitry'][attribute]
        power_management_and_distribution = nonbattery_dict['power_management_and_distribution'][attribute]
        additional_pair_of_half_shafts = nonbattery_dict['additional_pair_of_half_shafts'][attribute]
        brake_sensors_actuators = nonbattery_dict['brake_sensors_actuators'][attribute]
        
        return motor, inverter, induction_motor, induction_inverter, obc_and_dcdc_converter, hv_orange_cables, lv_battery, \
               hvac, single_speed_gearbox, powertrain_cooling_loop, charging_cord_kit, dc_fast_charge_circuitry, \
               power_management_and_distribution, additional_pair_of_half_shafts, brake_sensors_actuators 
    

class Weight:

    def __init__(self, key):
        self.weight_key, self.fuel_key, self.price_key, self.structure_key \
            = PackageCost(key).get_object_attributes(['weight_key', 'fuel_key', 'price_key', 'structure_key'])

    def calc_weight_cost(self, input_settings):
        """

        Weight costs are calculated as an absolute cost associated with the curb weight of the vehicle and are then adjusted according to the weight reduction.

        Args:
            input_settings: The InputSettings class.

        Returns:
            The cost associated with the steel, aluminum, plastic, etc., of the given vehicle package.

        """
        curb_wt, glider_weight, battery_weight, weight_rdxn = self.weight_key
        weight_rdxn = weight_rdxn / 100
        weight_cost_cache_key = (self.weight_key, self.price_key, self.structure_key, self.fuel_key)
        if weight_cost_cache_key in weight_cost_cache.keys():
            cost = weight_cost_cache[weight_cost_cache_key]
        else:
            weight_removed = glider_weight / (1 - weight_rdxn) - glider_weight
            base_wt = glider_weight + weight_removed

            if self.fuel_key != 'bev':
                weight_cost_dict = input_settings.weight_cost_ice_dict
            else:
                weight_cost_dict = input_settings.weight_cost_bev_dict

            base_weight_cost_per_lb = weight_cost_dict[self.structure_key]['item_cost'] \
                                      * input_settings.price_class_dict[self.price_key]['scaler']
            dmc_ln_coeff = weight_cost_dict[self.structure_key]['DMC_ln_coefficient']
            dmc_constant = weight_cost_dict[self.structure_key]['DMC_constant']
            ic_slope = weight_cost_dict[self.structure_key]['IC_slope']

            cost = base_wt * base_weight_cost_per_lb

            if weight_rdxn != 0:
                cost += ((dmc_ln_coeff * np.log(weight_rdxn) + dmc_constant) + (ic_slope * weight_rdxn)) * weight_removed

            weight_cost_cache[weight_cost_cache_key] = cost

        return cost


class Aftertreatment:

    def __init__(self, key):
        self.engine_key, self.fuel_key = PackageCost(key).get_object_attributes(['engine_key', 'fuel_key'])

    def calc_aftertreatment_cost(self, input_settings, device):
        """

        Args:
            input_settings: The InputSettings class.
            device: String designating the device for which costs are calculated (e.g., 'twc', 'gpf')

        Returns:
            The aftertreatment cost (TWC system or GPF system) for the given package.

        """
        disp = self.engine_key[1]
        swept_volume = input_settings.aftertreatment_dict[f'swept_volume_{device}']['value']
        twc_volume = disp * swept_volume
        factor = twc_volume / input_settings.grams_per_troy_oz

        pt_cost = factor * input_settings.pt_dollars_per_troy_oz * input_settings.aftertreatment_dict[f'Pt_grams_per_liter_{device}']['value']
        pd_cost = factor * input_settings.pd_dollars_per_troy_oz * input_settings.aftertreatment_dict[f'Pd_grams_per_liter_{device}']['value']
        rh_cost = factor * input_settings.rh_dollars_per_troy_oz * input_settings.aftertreatment_dict[f'Rh_grams_per_liter_{device}']['value']

        substrate = twc_volume * input_settings.aftertreatment_dict[f'substrate_{device}']['dmc_slope'] \
                    + input_settings.aftertreatment_dict[f'substrate_{device}']['dmc_intercept']
        washcoat = twc_volume * input_settings.aftertreatment_dict[f'washcoat_{device}']['dmc_slope'] \
                   + input_settings.aftertreatment_dict[f'washcoat_{device}']['dmc_intercept']
        canning = twc_volume * input_settings.aftertreatment_dict[f'canning_{device}']['dmc_slope'] \
                  + input_settings.aftertreatment_dict[f'canning_{device}']['dmc_intercept']

        cost = pt_cost + pd_cost + rh_cost + substrate + washcoat + canning

        cost = input_settings.aftertreatment_dict[f'markup_{device}']['value'] * cost

        return cost


class PackageCost:
    """

    The PackageCost class calculates the cost of the passed package based on the package cost key.

    """
    def __init__(self, key):
        self.key = key
        self.alpha_key, self.cost_key = self.key
        self.fuel_key, self.structure_key, self.price_key, self.alpha_class_key, self.engine_key, self.hev_key, self.pev_key, \
        self.trans_key, self.accessory_key, self.aero_key, self.nonaero_key, self.weight_key = self.cost_key

    def get_object_attributes(self, attribute_list):
        """

        Args:
            self: the object to get attributes from
            attribute_list: a list of attribute names

        Returns:
            A list containing the values of the requested attributes

        """
        return [self.__getattribute__(attr) for attr in attribute_list]

    def calc_trans_cost(self, input_settings):
        """

        Args:
            input_settings: The InputSettings class.

        Returns:
            The transmission cost for the given package based on its trans_key.

        """
        return input_settings.trans_cost_dict[self.trans_key]['item_cost']

    def calc_accessories_cost(self, input_settings):
        """

        Args:
            input_settings: The InputSettings class.

        Returns:
            The accessory cost for the given package based on its accessory_key.

        """
        return input_settings.accessories_cost_dict[self.accessory_key]['item_cost']

    def calc_aero_cost(self, input_settings):
        """

        Args:
            input_settings: The InputSettings class.

        Returns:
            The aero cost for the given package based on its aero_key.

        """
        tech_class = f'{self.structure_key}_{self.aero_key}'
        return input_settings.aero_cost_dict[tech_class]['item_cost']

    def calc_nonaero_cost(self, input_settings):
        """

        Args:
            input_settings: The InputSettings class.

        Returns:
            The aero cost for the given package based on its aero_key.

        """
        tech_class = f'{self.structure_key}_{self.nonaero_key}'
        return input_settings.nonaero_cost_dict[tech_class]['item_cost']

    def calc_ac_cost(self, input_settings):
        """

        Args:
            input_settings: The InputSettings class.

        Returns:
            The ac cost for the given package based on its structure_key.

        """
        return input_settings.ac_cost_dict[self.structure_key]['item_cost']

    def ice_package_costs(self, runtime_settings, input_settings, alpha_file_dict, alpha_file_name):
        """

        This function generates costs, etc., of ICE packages or ICE elements of electrified packages.

        Args:
            runtime_settings: The RuntimeSettings class.
            input_settings: The InputSettings class.
            alpha_file_dict: A dictionary of ALPHA packages created by the create_package_dict function.
            alpha_file_name: The name of the file from which the ALPHA packages are derived.

        Returns:
            A single row DataFrame containing necessary cycle results, credit flags, and first year costs of the given package.

        """
        print(self.cost_key)

        ftp1_co2, ftp2_co2, ftp3_co2, hwy_co2, combined_co2 = alpha_file_dict[self.key]['EPA_FTP_1 gCO2e/mi'], \
                                                              alpha_file_dict[self.key]['EPA_FTP_2 gCO2e/mi'], \
                                                              alpha_file_dict[self.key]['EPA_FTP_3 gCO2e/mi'], \
                                                              alpha_file_dict[self.key]['EPA_HWFET gCO2e/mi'], \
                                                              alpha_file_dict[self.key]['Combined GHG gCO2e/mi']
        trans_cost = self.calc_trans_cost(input_settings)
        accessories_cost = self.calc_accessories_cost(input_settings)
        ac_cost = self.calc_ac_cost(input_settings)
        aero_cost = self.calc_aero_cost(input_settings)
        nonaero_cost = self.calc_nonaero_cost(input_settings)
        roadload_cost = aero_cost + nonaero_cost
        roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[self.alpha_key])

        engine_cost = Engine(self.key).calc_engine_cost(input_settings)

        twc_cost = Aftertreatment(self.key).calc_aftertreatment_cost(input_settings, 'twc')
        gpf_cost = Aftertreatment(self.key).calc_aftertreatment_cost(input_settings, 'gpf')
        aftertreatment_cost = twc_cost + gpf_cost

        if self.fuel_key == 'hev':
            battery_cost = Battery(self.key).calc_battery_cost(input_settings)
            non_battery_cost = NonBattery(self.key).calc_nonbattery_cost(input_settings)
            hev_cost = battery_cost + non_battery_cost
        else:
            hev_cost = 0
        
        ice_powertrain_cost = engine_cost + trans_cost + accessories_cost + ac_cost
        ice_powertrain_cost_df = pd.DataFrame(ice_powertrain_cost, columns=['ice_powertrain'], index=[self.alpha_key])

        aftertreatment_cost_df = pd.DataFrame(aftertreatment_cost, columns=['aftertreatment'], index=[self.alpha_key])

        electrification_cost = hev_cost
        electrification_cost_df = pd.DataFrame(electrification_cost, columns=['hev_powertrain'], index=[self.alpha_key])

        weight_cost = Weight(self.key).calc_weight_cost(input_settings)
        body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[self.alpha_key])

        package_cost_df = ice_powertrain_cost_df.join(aftertreatment_cost_df).join(electrification_cost_df).join(roadload_cost_df).join(body_cost_df)
        
        package_cost_df.insert(0, 'cs_cert_direct_oncycle_co2e_grams_per_mile', combined_co2)
        package_cost_df.insert(0, 'cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile', hwy_co2)
        package_cost_df.insert(0, 'cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile', ftp2_co2)  ## FOR NOW ONLY!!! -KNew
        package_cost_df.insert(0, 'cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile', ftp3_co2)
        package_cost_df.insert(0, 'cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile', ftp2_co2)
        package_cost_df.insert(0, 'cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile', ftp1_co2)
        
        if runtime_settings.set_tech_tracking_flags:
            package_cost_df = create_tech_flags_from_cost_key(package_cost_df, self.key)

        package_cost_df.insert(0, 'dollar_basis', input_settings.dollar_basis_for_output_file)
        package_cost_df.insert(0, 'cost_curve_class', f'ice_{self.alpha_class_key}')
        package_cost_df.insert(0, 'cost_key', str(self.cost_key))
        package_cost_df.insert(0, 'alpha_filename', alpha_file_name)

        return package_cost_df

    def pev_package_costs(self, runtime_settings, input_settings, alpha_file_dict, alpha_file_name):
        """

        This function generates costs, etc., of BEV packages or plug-in electric elements of electrified packages.

        Args:
            runtime_settings: The RuntimeSettings class.
            input_settings: The InputSettings class.
            alpha_file_dict: A dictionary of ALPHA packages created by the create_package_dict function.
            alpha_file_name: The name of the file from which the ALPHA packages are derived.

        Returns:
            A single row DataFrame containing necessary cycle results, credit flags, and first year costs of the given package.

        """
        print(self.cost_key)

        onroad_range, oncycle_kwh_per_mile, usable_soc, gap, battery_kwh_gross, motor_power, number_of_motors, onboard_charger_kw, size_scaler = self.pev_key

        ftp1_kwh, ftp2_kwh, ftp3_kwh, hwy_kwh, combined_kwh = alpha_file_dict[self.key]['EPA_FTP_1_kWhr/100mi'] / 100, \
                                                              alpha_file_dict[self.key]['EPA_FTP_2_kWhr/100mi'] / 100, \
                                                              alpha_file_dict[self.key]['EPA_FTP_3_kWhr/100mi'] / 100, \
                                                              alpha_file_dict[self.key]['EPA_HWFET_kWhr/100mi'] / 100, \
                                                              oncycle_kwh_per_mile
        if self.fuel_key == 'phev':
            ftp1_co2, ftp2_co2, ftp3_co2, hwy_co2, combined_co2 = alpha_file_dict[self.key]['EPA_FTP_1 gCO2e/mi'], \
                                                                  alpha_file_dict[self.key]['EPA_FTP_2 gCO2e/mi'], \
                                                                  alpha_file_dict[self.key]['EPA_FTP_3 gCO2e/mi'], \
                                                                  alpha_file_dict[self.key]['EPA_HWFET gCO2e/mi'], \
                                                                  alpha_file_dict[self.key]['Combined GHG gCO2e/mi']
        ac_cost = self.calc_ac_cost(input_settings)
        aero_cost = self.calc_aero_cost(input_settings)
        nonaero_cost = self.calc_nonaero_cost(input_settings)
        roadload_cost = aero_cost + nonaero_cost
        roadload_cost_df = pd.DataFrame(roadload_cost, columns=['roadload'], index=[self.alpha_key])

        if self.fuel_key == 'phev':
            engine_cost = Engine(self.key).calc_engine_cost(input_settings)
            trans_cost = self.calc_trans_cost(input_settings)
            accessories_cost = self.calc_accessories_cost(input_settings)
            twc_cost = Aftertreatment(self.key).calc_aftertreatment_cost(input_settings, 'twc')
            gpf_cost = Aftertreatment(self.key).calc_aftertreatment_cost(input_settings, 'gpf')
            aftertreatment_cost = twc_cost + gpf_cost
            ice_powertrain_cost = engine_cost + trans_cost + accessories_cost + ac_cost
            battery_cost = Battery(self.key).calc_battery_cost(input_settings)
            non_battery_cost = NonBattery(self.key).calc_nonbattery_cost(input_settings)
            electrification_cost = battery_cost + non_battery_cost
        else:
            engine_cost = 0
            trans_cost = 0
            accessories_cost = 0
            aftertreatment_cost = 0
            ice_powertrain_cost = engine_cost + trans_cost + accessories_cost
            battery_cost = Battery(self.key).calc_battery_cost(input_settings)
            non_battery_cost = NonBattery(self.key).calc_nonbattery_cost(input_settings)
            electrification_cost = battery_cost + non_battery_cost + ac_cost

        ice_powertrain_cost_df = pd.DataFrame(ice_powertrain_cost, columns=['ice_powertrain'], index=[self.alpha_key])

        aftertreatment_cost_df = pd.DataFrame(aftertreatment_cost, columns=['aftertreatment'], index=[self.alpha_key])

        electrification_cost_df = pd.DataFrame({'pev_battery': battery_cost, 'pev_nonbattery': non_battery_cost, 'pev_powertrain': electrification_cost}, index=[self.alpha_key])

        weight_cost = Weight(self.key).calc_weight_cost(input_settings)
        body_cost_df = pd.DataFrame(weight_cost, columns=['body'], index=[self.alpha_key])

        package_cost_df = ice_powertrain_cost_df.join(aftertreatment_cost_df).join(electrification_cost_df).join(roadload_cost_df).join(body_cost_df)

        package_cost_df.insert(0, 'cd_cert_direct_oncycle_kwh_per_mile', combined_kwh)
        package_cost_df.insert(0, 'cd_hwfet:cert_direct_oncycle_kwh_per_mile', hwy_kwh)
        package_cost_df.insert(0, 'cd_ftp_4:cert_direct_oncycle_kwh_per_mile', ftp2_kwh)  ## FOR NOW ONLY!!! -KNew
        package_cost_df.insert(0, 'cd_ftp_3:cert_direct_oncycle_kwh_per_mile', ftp3_kwh)
        package_cost_df.insert(0, 'cd_ftp_2:cert_direct_oncycle_kwh_per_mile', ftp2_kwh)
        package_cost_df.insert(0, 'cd_ftp_1:cert_direct_oncycle_kwh_per_mile', ftp1_kwh)

        if self.fuel_key == 'phev':
            package_cost_df.insert(0, 'cs_cert_direct_oncycle_co2e_grams_per_mile', combined_co2)
            package_cost_df.insert(0, 'cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile', hwy_co2)
            package_cost_df.insert(0, 'cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile', ftp2_co2)  ## FOR NOW ONLY!!! -KNew
            package_cost_df.insert(0, 'cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile', ftp3_co2)
            package_cost_df.insert(0, 'cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile', ftp2_co2)
            package_cost_df.insert(0, 'cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile', ftp1_co2)

        if runtime_settings.set_tech_tracking_flags:
            package_cost_df = create_tech_flags_from_cost_key(package_cost_df, self.key)
        package_cost_df.insert(0, 'battery_kwh_gross', battery_kwh_gross)
        package_cost_df.insert(0, 'dollar_basis', input_settings.dollar_basis_for_output_file)
        package_cost_df.insert(0, 'cost_curve_class', f'{self.fuel_key}_{self.alpha_class_key}')
        package_cost_df.insert(0, 'cost_key', str(self.cost_key))
        package_cost_df.insert(0, 'alpha_filename', alpha_file_name)

        return package_cost_df


def alpha_file_name_becomes_dict(input_settings, alpha_file_name, fuel_key):
    """
    Read ALPHA file, clean data if necessary, add elements for keys, create dictionary.

    Args:
        input_settings: THe InputSettings class.
        alpha_file_name: The name of the ALPHA file.
        fuel_key: The fuel_id ('ice', 'bev', 'hev', 'phev')

    Returns:
        A dictionary of the ALPHA file data.

    """
    alpha_file_df = AlphaData().read_alpha_file(alpha_file_name)
    if fuel_key == 'ice':
        alpha_file_df = AlphaData().clean_alpha_data(alpha_file_df, 'Aero Improvement %', 'Crr Improvement %', 'Weight Reduction %')
    alpha_file_df = AlphaData().add_elements_for_package_key(alpha_file_df)
    alpha_file_dict = AlphaData().create_package_dict(input_settings, alpha_file_df, fuel_key)

    return alpha_file_dict


def create_tech_flags_from_cost_key(df, key):
    """

    Args:
        df: A DataFrame of simulated vehicle packages.
        key: The alpha_dict_key

    Return:
        The passed DataFrame with tech flags (0, 1, etc.) added.

    """
    alpha_class_key, engine_key, weight_key, accessory_key, fuel_key \
        = PackageCost(key).get_object_attributes(['alpha_class_key', 'engine_key', 'weight_key', 'accessory_key', 'fuel_key'])

    # set tech flags to 0, indicating that the tech is not present on the package
    turb11_value = turb12_value = di_value = atk2_value = 0
    cegr_value = deacpd_value = deacfc_value = accessory_value = 0
    startstop = hev_value = hev_truck_value = bev_value = phev_value = 0

    # set tech flags to 1 where applicable
    curb_weight, glider_weight, battery_weight, weight_rdxn = weight_key
    if accessory_key.__contains__('REGEN'): accessory_value = 1

    if fuel_key != 'bev':
        engine_name, disp, cyl, deacpd, deacfc, startstop = engine_key
        turb, finj, atk, cegr = Engine(key).get_engine_techs()
        if turb == 'TURB11': turb11_value = 1
        if turb == 'TURB12': turb12_value = 1
        if finj == 'DI': di_value = 1
        if atk == 'ATK2': atk2_value = 1
        if cegr == 'CEGR': cegr_value = 1
        if deacpd != 0: deacpd_value = 1
        if deacfc != 0: deacfc_value = 1

    if fuel_key == 'bev':
        bev_value = 1

    if fuel_key == 'hev':
        hev_value = 1
        if alpha_class_key == 'Truck': hev_truck_value = 1

    if fuel_key == 'phev':
        phev_value = 1

    df.insert(0, 'ac_leakage', 1)
    df.insert(0, 'ac_efficiency', 1)
    df.insert(0, 'high_eff_alternator', accessory_value)
    df.insert(0, 'bev', bev_value)
    df.insert(0, 'phev', phev_value)
    df.insert(0, 'hev', hev_value)
    df.insert(0, 'hev_truck', hev_truck_value)
    df.insert(0, 'start_stop', startstop)
    df.insert(0, 'curb_weight', curb_weight)
    df.insert(0, 'weight_reduction', weight_rdxn / 100)
    df.insert(0, 'deac_fc', deacfc_value)
    df.insert(0, 'deac_pd', deacpd_value)
    df.insert(0, 'cegr', cegr_value)
    df.insert(0, 'atk2', atk2_value)
    df.insert(0, 'gdi', di_value)
    df.insert(0, 'turb12', turb12_value)
    df.insert(0, 'turb11', turb11_value)

    return df


def cost_vs_plot(input_settings, df, path, *years):
    """

    Args:
        input_settings: The InputSettings class.
        df: A DataFrame cost cloud consisting of ICE, BEV and HEV packages.
        path: The path for saving the plot.
        years: The years for which cost cloud plots are to be generated and saved.

    Returns:
        Nothing, but plots for the given years will be saved to the passed path.

    """
    ice_classes = [x for x in df['cost_curve_class'].unique() if 'ice' in x]
    bev_classes = [x for x in df['cost_curve_class'].unique() if 'bev' in x]
    phev_classes = [x for x in df['cost_curve_class'].unique() if 'phev' in x]
    hev_classes = [x for x in df['cost_curve_class'].unique() if 'hev' in x and 'phev' not in x]
    for year in years:
        ice_data = dict()
        ice_plot = list()
        ice_legends = list()
        bev_data = dict()
        bev_plot = list()
        bev_legends = list()
        phev_data_co2 = dict()
        phev_data_kwh = dict()
        phev_plot_co2 = list()
        phev_plot_kwh = list()
        phev_legends_co2 = list()
        phev_legends_kwh = list()
        hev_data = dict()
        hev_plot = list()
        hev_legends = list()
        for cost_curve_class in ice_classes:
            ice_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cs_cert_direct_oncycle_co2e_grams_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            ice_plot.append(ice_data[cost_curve_class])
            ice_legends.append(cost_curve_class)
        for cost_curve_class in bev_classes:
            bev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cd_cert_direct_oncycle_kwh_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            bev_plot.append(bev_data[cost_curve_class])
            bev_legends.append(cost_curve_class)
        for cost_curve_class in phev_classes:
            phev_data_kwh[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cd_cert_direct_oncycle_kwh_per_mile'],
                                               df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            phev_plot_kwh.append(phev_data_kwh[cost_curve_class])
            phev_legends_kwh.append(cost_curve_class)
        for cost_curve_class in phev_classes:
            phev_data_co2[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cs_cert_direct_oncycle_co2e_grams_per_mile'],
                                               df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            phev_plot_co2.append(phev_data_co2[cost_curve_class])
            phev_legends_co2.append(cost_curve_class)
        for cost_curve_class in hev_classes:
            hev_data[cost_curve_class] = (df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'cs_cert_direct_oncycle_co2e_grams_per_mile'],
                                          df.loc[(df['model_year'] == year) & (df['cost_curve_class'] == cost_curve_class), 'new_vehicle_mfr_cost_dollars'])
            hev_plot.append(hev_data[cost_curve_class])
            hev_legends.append(cost_curve_class)

        ice_plot = tuple(ice_plot)
        ice_legends = tuple(ice_legends)
        bev_plot = tuple(bev_plot)
        bev_legends = tuple(bev_legends)
        phev_plot_kwh = tuple(phev_plot_kwh)
        phev_legends_kwh = tuple(phev_legends_kwh)
        phev_plot_co2 = tuple(phev_plot_co2)
        phev_legends_co2 = tuple(phev_legends_co2)
        hev_plot = tuple(hev_plot)
        hev_legends = tuple(hev_legends)

        # create ice plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for ice_plot, ice_legends in zip(ice_plot, ice_legends):
            x, y = ice_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=ice_legends)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            ax.set_ylabel(f'{input_settings.dollar_basis_for_output_file} dollars', fontsize=9)
            plt.legend(loc=2)
            plt.title(f'ice_{year}')
            plt.savefig(path / f'ice_{year}_{input_settings.name_id}.png')

        # create bev plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for bev_plot, bev_legends in zip(bev_plot, bev_legends):
            x, y = bev_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=bev_legends)
            ax.set(xlim=(0, 0.5), ylim=(10000, 60000))
            ax.set_ylabel(f'{input_settings.dollar_basis_for_output_file} dollars', fontsize=9)
            plt.legend(loc=4)
            plt.title(f'bev_{year}')
            plt.savefig(path / f'bev_{year}_{input_settings.name_id}.png')

        # create phev plot kwh
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for phev_plot_kwh, phev_legends_kwh in zip(phev_plot_kwh, phev_legends_kwh):
            x, y = phev_plot_kwh
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=phev_legends_kwh)
            ax.set(xlim=(0, 0.5), ylim=(10000, 60000))
            ax.set_ylabel(f'{input_settings.dollar_basis_for_output_file} dollars', fontsize=9)
            plt.legend(loc=4)
            plt.title(f'phev_kwh_{year}')
            plt.savefig(path / f'phev_kwh_{year}_{input_settings.name_id}.png')

        # create phev plot co2
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for phev_plot_co2, phev_legends_co2 in zip(phev_plot_co2, phev_legends_co2):
            x, y = phev_plot_co2
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=phev_legends_co2)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            ax.set_ylabel(f'{input_settings.dollar_basis_for_output_file} dollars', fontsize=9)
            plt.legend(loc=4)
            plt.title(f'phev_co2_{year}')
            plt.savefig(path / f'phev_co2_{year}_{input_settings.name_id}.png')

        # create hev plot
        fig = plt.figure()
        ax = fig.add_subplot(1, 1, 1)
        ax.grid(True)
        for hev_plot, hev_legends in zip(hev_plot, hev_legends):
            x, y = hev_plot
            ax.scatter(x, y, alpha=0.8, edgecolors='none', s=30, label=hev_legends)
            ax.set(xlim=(0, 500), ylim=(10000, 60000))
            ax.set_ylabel(f'{input_settings.dollar_basis_for_output_file} dollars', fontsize=9)
            plt.legend(loc=2)
            plt.title(f'hev_{year}')
            plt.savefig(path / f'hev_{year}_{input_settings.name_id}.png')


def calc_year_over_year_costs(input_settings, df, arg, learning_type):
    """

    Args:
        input_settings: The InputSettings class.
        df: A DataFrame of ALPHA packages with costs for a single start year.
        arg (string): The argument for which year-over-year costs are to be calculated.
        learning_type (string): The learning type to apply (e.g., powertrain, bev, roadload).

    Returns:
        A DataFrame of ALPHA packages with costs for all years.

    """
    df_return = df.copy()
    arg_dict = dict()
    learn_rate = input_settings.learning_dict['learning_rate']
    years = input_settings.years
    for year in years:
        legacy_sales_scaler = input_settings.learning_dict[f'{learning_type}_scaler']
        sales_scaler = input_settings.learning_dict[f'{learning_type}_sales_scaler']
        cumulative_sales = sales_scaler * (year - years[0])
        arg_dict[year] = pd.Series(df[arg]
                                   * ((cumulative_sales + legacy_sales_scaler) / legacy_sales_scaler) ** learn_rate,
                                   name=f'{arg}_{year}')
    for year in years:
        df_return = pd.concat([df_return, arg_dict[year]], axis=1)
    return df_return


def sum_vehicle_parts(df, years, new_arg, *args):
    """

    Args:
        df: A DataFrame of ALPHA packages with year-over-year costs for all years.
        years: The years for which new_arg year-over-year costs are to be calculated.
        args: The arguments to sum into a single new_arg value for each of the passed years.

    Returns:
        A DataFrame of year-over-year costs that now includes summed args expressed as the new_arg.

    """
    for year in years:
        df.insert(len(df.columns), f'{new_arg}_{year}', 0)
        for arg in args:
            df[f'{new_arg}_{year}'] += df[f'{arg}_{year}']
    return df


def reshape_df_for_cloud_file(runtime_settings, input_settings, df_source, *id_args):
    """

    Args:
        runtime_settings: The RuntimeSettings class.
        input_settings: The InputSettings class.
        df_source: A DataFrame of ALPHA packages containing year-over-year costs to be reshaped into the cost cloud.
        id_args: The arguments to use as ID variables in the reshaped DataFrame (pd.melt).

    Return:
        A DataFrame in the desired shape of the cost cloud file.

    """
    df_return = pd.DataFrame()
    id_variables = [id_arg for id_arg in id_args]

    tech_flag_list = input_settings.tech_flag_tracking

    for tech in tech_flag_list:
        id_variables.append(tech)
    if runtime_settings.run_bev or runtime_settings.run_phev:
        for arg in df_source.columns:
            if arg.__contains__('kwh_per_mile'):
                id_variables.append(arg)
    if runtime_settings.run_ice or runtime_settings.run_hev or runtime_settings.run_phev:
        for arg in df_source.columns:
            if arg.__contains__('grams_per_mile'):
                id_variables.append(arg)
    source_args = id_variables.copy()
    for year in input_settings.years:
        source_args.append(f'new_vehicle_mfr_cost_dollars_{year}')
    for year in input_settings.years:
        temp = pd.melt(df_source[source_args], id_vars=id_variables, value_vars=f'new_vehicle_mfr_cost_dollars_{year}', value_name='new_vehicle_mfr_cost_dollars')
        temp.insert(1, 'model_year', year)
        temp.drop(columns='variable', inplace=True)
        df_return = pd.concat([df_return, temp], ignore_index=True, axis=0)
    return df_return


def drop_columns(df, *args):
    """

    Args:
        df: A DataFrame in which a column is to be dropped.
        args: The column names to be dropped.

    Returns:
        A DataFrame without columns=args.

    """
    cols_to_drop = list()
    for arg in args:
        if arg in df.columns:
            cols_to_drop.append(arg)
        else:
            pass
    df.drop(columns=cols_to_drop, inplace=True)
    return df


def main():

    runtime_settings = RuntimeSettings()
    input_settings = InputSettings()

    ice_packages_df, bev_packages_df, hev_packages_df, phev_packages_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    if runtime_settings.run_bev:
        fuel_key = 'bev'
        alpha_folder = input_settings.path_alpha_inputs / 'BEV'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = alpha_file_name_becomes_dict(input_settings, alpha_file_name, fuel_key)
            for key in alpha_file_dict.keys():
                package_result = PackageCost(key).pev_package_costs(runtime_settings, input_settings, alpha_file_dict, alpha_file_name)
                bev_packages_df = pd.concat([bev_packages_df, package_result], axis=0, ignore_index=False)

    if runtime_settings.run_phev:
        fuel_key = 'phev'
        alpha_folder = input_settings.path_alpha_inputs / 'PHEV'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = alpha_file_name_becomes_dict(input_settings, alpha_file_name, fuel_key)
            for key in alpha_file_dict.keys():
                package_result = PackageCost(key).pev_package_costs(runtime_settings, input_settings, alpha_file_dict, alpha_file_name)
                phev_packages_df = pd.concat([phev_packages_df, package_result], axis=0, ignore_index=False)

    if runtime_settings.run_hev:
        fuel_key = 'hev'
        alpha_folder = input_settings.path_alpha_inputs / 'HEV'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = alpha_file_name_becomes_dict(input_settings, alpha_file_name, fuel_key)
            for key in alpha_file_dict.keys():
                package_result = PackageCost(key).ice_package_costs(runtime_settings, input_settings, alpha_file_dict, alpha_file_name)
                hev_packages_df = pd.concat([hev_packages_df, package_result], axis=0, ignore_index=False)

    if runtime_settings.run_ice:
        fuel_key = 'ice'
        alpha_folder = input_settings.path_alpha_inputs / 'ICE'
        alpha_file_names = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]
        for idx, alpha_file_name in enumerate(alpha_file_names):
            alpha_file_dict = alpha_file_name_becomes_dict(input_settings, alpha_file_name, fuel_key)
            for key in alpha_file_dict.keys():
                package_result = PackageCost(key).ice_package_costs(runtime_settings, input_settings, alpha_file_dict, alpha_file_name)
                ice_packages_df = pd.concat([ice_packages_df, package_result], axis=0, ignore_index=False)

    # calculate YoY bev costs with learning
    if runtime_settings.run_bev:
        bev_packages_df = calc_year_over_year_costs(input_settings, bev_packages_df, 'pev_battery', 'pev')
        bev_packages_df = calc_year_over_year_costs(input_settings, bev_packages_df, 'pev_nonbattery', 'pev')
        bev_packages_df = calc_year_over_year_costs(input_settings, bev_packages_df, 'pev_powertrain', 'pev')
        bev_packages_df = calc_year_over_year_costs(input_settings, bev_packages_df, 'roadload', 'roadload')
        bev_packages_df = calc_year_over_year_costs(input_settings, bev_packages_df, 'body', 'weight')
        bev_packages_df.reset_index(drop=False, inplace=True)
        bev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'bev_{idx}' for idx in range(1, len(bev_packages_df) + 1)]
        bev_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        bev_packages_df = sum_vehicle_parts(bev_packages_df, input_settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'pev_powertrain', 'roadload', 'body')

    # calculate YoY phev costs with learning
    if runtime_settings.run_phev:
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'ice_powertrain', 'ice')
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'aftertreatment', 'ice')
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'pev_battery', 'pev')
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'pev_nonbattery', 'pev')
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'pev_powertrain', 'pev')
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'roadload', 'roadload')
        phev_packages_df = calc_year_over_year_costs(input_settings, phev_packages_df, 'body', 'weight')
        phev_packages_df.reset_index(drop=False, inplace=True)
        phev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'phev_{idx}' for idx in range(1, len(phev_packages_df) + 1)]
        phev_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        phev_packages_df = sum_vehicle_parts(phev_packages_df, input_settings.years,
                                             'new_vehicle_mfr_cost_dollars',
                                             'ice_powertrain', 'aftertreatment', 'pev_powertrain', 'roadload', 'body')

    # calculate YoY hev costs with learning
    if runtime_settings.run_hev:
        hev_packages_df = calc_year_over_year_costs(input_settings, hev_packages_df, 'ice_powertrain', 'ice')
        hev_packages_df = calc_year_over_year_costs(input_settings, hev_packages_df, 'aftertreatment', 'ice')
        hev_packages_df = calc_year_over_year_costs(input_settings, hev_packages_df, 'hev_powertrain', 'ice')
        hev_packages_df = calc_year_over_year_costs(input_settings, hev_packages_df, 'roadload', 'roadload')
        hev_packages_df = calc_year_over_year_costs(input_settings, hev_packages_df, 'body', 'weight')
        hev_packages_df.reset_index(drop=False, inplace=True)
        hev_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'hev_{idx}' for idx in range(1, len(hev_packages_df) + 1)]
        hev_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        hev_packages_df = sum_vehicle_parts(hev_packages_df, input_settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'aftertreatment', 'hev_powertrain', 'roadload', 'body')

    # calculate YoY ice costs with learning
    if runtime_settings.run_ice:
        ice_packages_df = calc_year_over_year_costs(input_settings, ice_packages_df, 'ice_powertrain', 'ice')
        ice_packages_df = calc_year_over_year_costs(input_settings, ice_packages_df, 'aftertreatment', 'ice')
        ice_packages_df = calc_year_over_year_costs(input_settings, ice_packages_df, 'roadload', 'roadload')
        ice_packages_df = calc_year_over_year_costs(input_settings, ice_packages_df, 'body', 'weight')
        ice_packages_df.reset_index(drop=False, inplace=True)
        ice_packages_df.rename(columns={'index': 'alpha_key'}, inplace=True)
        simulated_vehicle_id = [f'ice_{idx}' for idx in range(1, len(ice_packages_df) + 1)]
        ice_packages_df.insert(0, 'simulated_vehicle_id', simulated_vehicle_id)
        ice_packages_df = sum_vehicle_parts(ice_packages_df, input_settings.years,
                                            'new_vehicle_mfr_cost_dollars',
                                            'ice_powertrain', 'aftertreatment', 'roadload', 'body')

    input_settings.path_outputs.mkdir(exist_ok=True)
    input_settings.path_of_run_folder = input_settings.path_outputs / f'{input_settings.name_id}'
    input_settings.path_of_run_folder.mkdir(exist_ok=False)

    cost_cloud, cost_cloud_bev, cost_cloud_phev, cost_cloud_hev, cost_cloud_ice \
        = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    
    if runtime_settings.run_bev:
        cost_cloud_bev = reshape_df_for_cloud_file(runtime_settings, input_settings, bev_packages_df,
                                                   'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')
    if runtime_settings.run_phev:
        cost_cloud_phev = reshape_df_for_cloud_file(runtime_settings, input_settings, phev_packages_df,
                                                    'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')
    if runtime_settings.run_hev:
        cost_cloud_hev = reshape_df_for_cloud_file(runtime_settings, input_settings, hev_packages_df,
                                                   'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')
    if runtime_settings.run_ice:
        cost_cloud_ice = reshape_df_for_cloud_file(runtime_settings, input_settings, ice_packages_df,
                                                   'simulated_vehicle_id', 'cost_curve_class', 'alpha_key', 'alpha_filename')

    cost_cloud = pd.concat([cost_cloud_bev, cost_cloud_phev, cost_cloud_hev, cost_cloud_ice], axis=0, ignore_index=True)

    cost_cloud_verbose = cost_cloud.copy()
    cost_cloud.fillna(0, inplace=True)

    cost_vs_plot(input_settings, cost_cloud, input_settings.path_of_run_folder, 2020, 2030, 2040)

    bev_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_bev_{input_settings.name_id}.csv', index=False)
    ice_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_ice_{input_settings.name_id}.csv', index=False)
    hev_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_hev_{input_settings.name_id}.csv', index=False)
    phev_packages_df.to_csv(input_settings.path_of_run_folder / f'detailed_costs_phev_{input_settings.name_id}.csv', index=False)

    if runtime_settings.generate_simulated_vehicles_file:
        cost_cloud = drop_columns(cost_cloud, 'cert_co2e_grams_per_mile', 'cert_kWh_per_mile', 'alpha_key',
                                  'alpha_filename', 'cs_cert_direct_oncycle_co2e_grams_per_mile',
                                  'cd_cert_direct_oncycle_kwh_per_mile')
        # open the 'simulated_vehicles.csv' input template into which results will be placed.
        cost_clouds_template_info = pd.read_csv(input_settings.path_input_templates.joinpath('simulated_vehicles.csv'), nrows=0, usecols=[0, 1, 2, 3, 4])
        temp = [item for item in cost_clouds_template_info]
        temp.append(f'{input_settings.dollar_basis_for_output_file}')
        temp.append(f'{input_settings.name_id}')
        df = pd.DataFrame(columns=temp)
        df.to_csv(input_settings.path_of_run_folder.joinpath('simulated_vehicles.csv'), index=False)

        with open(input_settings.path_of_run_folder.joinpath('simulated_vehicles.csv'), 'a', newline='') as cloud_file:
            cost_cloud.to_csv(cloud_file, index=False)

    if runtime_settings.generate_simulated_vehicles_verbose_file:
        df.to_csv(input_settings.path_of_run_folder.joinpath('simulated_vehicles_verbose.csv'), index=False)

        with open(input_settings.path_of_run_folder.joinpath('simulated_vehicles_verbose.csv'), 'a', newline='') as cloud_file:
            cost_cloud_verbose.to_csv(cloud_file, index=False)

    # save additional outputs
    modified_costs = pd.ExcelWriter(input_settings.path_of_run_folder.joinpath(f'techcosts_in_{input_settings.dollar_basis_for_output_file}_dollars.xlsx'))
    pd.DataFrame(input_settings.engine_cost_dict).transpose().to_excel(modified_costs, sheet_name='engine', index=True)
    pd.DataFrame(input_settings.trans_cost_dict).transpose().to_excel(modified_costs, sheet_name='trans', index=True)
    pd.DataFrame(input_settings.startstop_cost_dict).transpose().to_excel(modified_costs, sheet_name='start-stop', index=False)
    pd.DataFrame(input_settings.accessories_cost_dict).transpose().to_excel(modified_costs, sheet_name='accessories', index=True)
    pd.DataFrame(input_settings.aero_cost_dict).transpose().to_excel(modified_costs, sheet_name='aero', index=False)
    pd.DataFrame(input_settings.nonaero_cost_dict).transpose().to_excel(modified_costs, sheet_name='nonaero', index=False)
    pd.DataFrame(input_settings.weight_cost_ice_dict).transpose().to_excel(modified_costs, sheet_name='weight_ice', index=True)
    pd.DataFrame(input_settings.weight_cost_bev_dict).transpose().to_excel(modified_costs, sheet_name='weight_bev', index=True)
    pd.DataFrame(input_settings.ac_cost_dict).transpose().to_excel(modified_costs, sheet_name='ac', index=True)
    pd.DataFrame(input_settings.bev_curves_dict).transpose().to_excel(modified_costs, sheet_name='bev_curves', index=True)
    pd.DataFrame(input_settings.phev_curves_dict).transpose().to_excel(modified_costs, sheet_name='phev_curves', index=True)
    pd.DataFrame(input_settings.hev_curves_dict).transpose().to_excel(modified_costs, sheet_name='hev_curves', index=True)
    modified_costs.save()

    # copy input files into the output folder
    input_files_list = [input_settings.techcosts_file]
    filename_list = [Path(path).name for path in input_files_list]
    for file in filename_list:
        path_source = input_settings.path_inputs.joinpath(file)
        path_destination = input_settings.path_of_run_folder.joinpath(file)
        shutil.copy2(path_source, path_destination)  # copy2 should maintain date/timestamps

    print(f'\nOutput files have been saved to {input_settings.path_of_run_folder}')


if __name__ == '__main__':
    import os, traceback

    try:
        main()
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
