import pandas as pd
from omega_preproc.alpha_package_costs.alpha_package_costs import InputSettings, Engine, AlphaData


class SelectICEforHEV:
    """

    Select ICE packages from ICE ALPHA files for "conversion" to HEV given specific selection parameters defined by the init.

    """
    def __init__(self, df):
        """

        Args:
            df: A DataFrame of ICE ALPHA packages.

        """
        self.df = df
        self.weight_reduction = 0
        self.aero = 20
        self.nonaero = 20
        self.startstop = 0

    def return_df(self):
        """

        Returns:
            A DataFrame of ICE packages as selected via the init args and those args defined within this function.

        """
        list_with_turb = list()
        for name in self.df['Engine']:
            turb, finj, atk, cegr = Engine().get_engine_techs(name)
            list_with_turb.append(turb)
        self.df.insert(0, 'turb', list_with_turb)
        if self.df.iloc[0]['Vehicle Type'] != 'Truck':
            return_df = pd.DataFrame(self.df.loc[self.df['turb'] == '', :])
        else:
            return_df = pd.DataFrame(self.df.loc[self.df['turb'] != '', :])
        return_df = pd.DataFrame(return_df.loc[return_df['Start Stop'] == self.startstop, :])
        return_df['Start Stop'] = 1 # HEVs have start-stop but we don't want to cost it since it's in the HEV cost - that's handled in alpha_package_costs.py
        return_df.drop(columns='turb', inplace=True)
        return_df.reset_index(drop=True, inplace=True)
        return return_df


def adjust_co2(metrics_dict, df, fuel_key):
    """

    Args:
        metrics_dict: Dictionary of HEV or PHEV metrics.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to electrified packages.
        fuel_key: String indicating whether the package is a PHEV or HEV ('phev' or 'hev').

    Returns:
        A DataFrame of packages with ICE-based CO2 values adjusted to reflect electrification.

    """
    factor = 1 - metrics_dict['co2_reduction_cycle'][fuel_key]
    factor_city = 1 - metrics_dict['co2_reduction_city'][fuel_key]
    factor_hwy = 1 - metrics_dict['co2_reduction_hwy'][fuel_key]

    df['EPA_FTP_1 gCO2e/mi'] = df['EPA_FTP_1 gCO2e/mi'] * factor_city
    df['EPA_FTP_2 gCO2e/mi'] = df['EPA_FTP_2 gCO2e/mi'] * factor_city
    df['EPA_FTP_3 gCO2e/mi'] = df['EPA_FTP_3 gCO2e/mi'] * factor_city
    df['EPA_HWFET gCO2e/mi'] = df['EPA_HWFET gCO2e/mi'] * factor_hwy
    df['Combined GHG gCO2e/mi'] = df['Combined GHG gCO2e/mi'] * factor
    return df


def add_kwh_per_mile(metrics_dict, df, fuel_key):
    """

    Args:
        metrics_dict: Dictionary of HEV or PHEV metrics.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to electrified packages.
        fuel_key: String indicating whether the package is a PHEV or HEV ('phev' or 'hev').

    Returns:
        A DataFrame of packages with ICE-based kWh values adjusted to reflect electrification.

    """
    factor = metrics_dict['co2_reduction_cycle'][fuel_key]
    factor_city = metrics_dict['co2_reduction_city'][fuel_key]
    factor_hwy = metrics_dict['co2_reduction_hwy'][fuel_key]

    kwh_per_mile_1 = pd.Series(df['EPA_FTP_1 Crankshaft Work kWh'] / df['EPA_FTP_1dist. mi'] * factor_city,
                               name='EPA_FTP_1_kWhr/100mi')
    kwh_per_mile_2 = pd.Series(df['EPA_FTP_2 Crankshaft Work kWh'] / df['EPA_FTP_2dist. mi'] * factor_city,
                               name='EPA_FTP_2_kWhr/100mi')
    kwh_per_mile_3 = pd.Series(df['EPA_FTP_3 Crankshaft Work kWh'] / df['EPA_FTP_3dist. mi'] * factor_city,
                               name='EPA_FTP_3_kWhr/100mi')
    kwh_per_mile_hwy = pd.Series(df['EPA_HWFET Crankshaft Work kWh'] / df['EPA_HWFETdist. mi'] * factor_hwy,
                                 name='EPA_HWFET_kWhr/100mi')
    combined = pd.Series(df['Combined FE CFR MPG'] * factor, name='Combined Consumption Rate')

    for s in [kwh_per_mile_1, kwh_per_mile_2, kwh_per_mile_3, kwh_per_mile_hwy, combined]:
        df = pd.concat([df, s], axis=1)

    return df


def add_battery(input_settings, df, curves_dict):
    """

    Args:
        input_settings: The InputSettings class of the alpha_package_costs module.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to HEV.
        curves_dict: Dictionary of HEV or PHEV curves.

    Returns:
        A DataFrame of packages with electrified vehicle battery details added.

    """
    df.insert(len(df.columns), 'battery_kwh_gross', 0)

    attribute = 'kWh_pack_per_kg_curbwt_curve'

    a = curves_dict[attribute]['x_cubed_factor']
    b = curves_dict[attribute]['x_squared_factor']
    c = curves_dict[attribute]['x_factor']
    d = curves_dict[attribute]['constant']

    curb_weight = (df['Test Weight lbs'] - 300)/input_settings.lbs_per_kg

    df['battery_kwh_gross'] = a * curb_weight ** 3 + b * curb_weight ** 2 + c * curb_weight + d

    return df


def add_motor(input_settings, df, curves_dict):
    """

    Args:
        input_settings: The InputSettings class of the alpha_package_costs module.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to HEV.
        curves_dict: Dictionary of HEV or PHEV curves.

    Returns:
        A DataFrame of packages with hybrid motor details added.

    """
    df.insert(len(df.columns), 'motor_kw', 0)

    attribute = 'kW_motor_per_kg_curbwt_curve'

    a = curves_dict[attribute]['x_cubed_factor']
    b = curves_dict[attribute]['x_squared_factor']
    c = curves_dict[attribute]['x_factor']
    d = curves_dict[attribute]['constant']

    curb_weight = (df['Test Weight lbs'] - 300)/input_settings.lbs_per_kg

    df['motor_kw'] = a * curb_weight ** 3 + b * curb_weight ** 2 + c * curb_weight + d

    return df


# def calc_size_scalers(settings):
#     """
#
#     Args:
#         settings: The SetInputs class of the alpha_package_costs module.
#
#     Returns:
#         A list of non-battery cost scalers based on entries in the SetInputs class.
#
#     """
#     bin_list = list(range(1, settings.hev_size_bins + 1))
#     list_of_scalers = list()
#     for idx, bin in enumerate(bin_list):
#         if bin <= settings.bin_with_scaler_equal_1:
#             list_of_scalers.append(1 - (settings.bin_with_scaler_equal_1 - bin) * settings.bin_size_scaling_interval)
#         if bin > settings.bin_with_scaler_equal_1:
#             list_of_scalers.append(1 + (bin - settings.bin_with_scaler_equal_1) * settings.bin_size_scaling_interval)
#     return list_of_scalers
#
#
# def add_size_scalers(settings, df):
#     """
#
#     Args:
#         settings: The SetInputs class of the alpha_package_costs module.
#         df: A DataFrame of ICE-based ALPHA packages that have been "converted" to HEV.
#
#     Returns:
#         A DataFrame of packages with non-battery size/cost scalers based on size class.
#
#     """
#     # get list_of_scalers
#     # list_of_scalers = calc_size_scalers(settings)
#     list_of_scalers = list(range(1, settings.hev_size_bins + 1))
#     scaler_series = pd.cut(df['Test Weight lbs'] - 300, settings.hev_size_bins, labels=list_of_scalers)
#     df.insert(len(df.columns), 'non_battery_size_scalers', scaler_series)
#     return df


def main():
    
    # what to make
    make_hev = False
    make_phev = True
    
    input_settings = InputSettings()
    ice_folder_path = input_settings.path_alpha_inputs / 'ICE'
    hev_folder_path = input_settings.path_alpha_inputs / 'HEV'
    hev_folder_path.mkdir(exist_ok=True)
    phev_folder_path = input_settings.path_alpha_inputs / 'PHEV'
    phev_folder_path.mkdir(exist_ok=True)    

    hev_packages_df = pd.DataFrame()
    phev_packages_df = pd.DataFrame()
    sub_header = pd.DataFrame()
    alpha_files = [file for file in ice_folder_path.iterdir() if file.name.__contains__('.csv')]

    for idx, alpha_file in enumerate(alpha_files):
        if idx == 0:
            alpha_file_df = pd.read_csv(alpha_file)
            sub_header = pd.DataFrame(alpha_file_df.iloc[0, :]).transpose()
            alpha_file_df = pd.read_csv(alpha_file, skiprows=range(1, 2))
        else: alpha_file_df = pd.read_csv(alpha_file, skiprows=range(1, 2))
        alpha_file_df = AlphaData().clean_alpha_data(alpha_file_df, 'Aero Improvement %', 'Crr Improvement %', 'Weight Reduction %')

        df = SelectICEforHEV(alpha_file_df).return_df()
        if make_hev:
            hev_packages_df = pd.concat([hev_packages_df, df], axis=0, ignore_index=True)
        if make_phev:
            phev_packages_df = pd.concat([phev_packages_df, df], axis=0, ignore_index=True)

    if make_hev:
        packages_df = hev_packages_df
        metrics_dict = input_settings.hev_metrics_dict
        curves_dict = input_settings.hev_curves_dict
        folder_path = hev_folder_path
        packages_df = add_battery(input_settings, packages_df, curves_dict)
        packages_df = add_motor(input_settings, packages_df, curves_dict)
        packages_df = adjust_co2(metrics_dict, packages_df, 'hev')
        # packages_df = add_size_scalers(input_settings, packages_df)
        packages_df = pd.concat([sub_header, packages_df], axis=0, ignore_index=True)
        packages_df.to_csv(folder_path / 'HEV.csv', index=False)
        print(f'HEV packages file is saved to {folder_path}')

    if make_phev:
        packages_df = phev_packages_df
        metrics_dict = input_settings.phev_metrics_dict
        curves_dict = input_settings.phev_curves_dict
        folder_path = phev_folder_path
        packages_df = add_battery(input_settings, packages_df, curves_dict)
        packages_df = add_motor(input_settings, packages_df, curves_dict)
        packages_df = adjust_co2(metrics_dict, packages_df, 'phev')
        packages_df = add_kwh_per_mile(metrics_dict, packages_df, 'phev')
        # packages_df = add_size_scalers(input_settings, packages_df)
        packages_df = pd.concat([sub_header, packages_df], axis=0, ignore_index=True)
        packages_df.to_csv(folder_path / 'PHEV.csv', index=False)
        print(f'PHEV packages file is saved to {folder_path}')


if __name__ == '__main__':
    main()
