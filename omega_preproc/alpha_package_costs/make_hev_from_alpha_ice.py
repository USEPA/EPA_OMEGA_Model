import pandas as pd
from omega_preproc.alpha_package_costs.alpha_package_costs import SetInputs as settings, Engines, clean_alpha_data


class SelectICEforHEV:
    """

    Select ICE packges from ICE ALPHA files for "conversion" to HEV given specific selection parameters defined by the init.

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
            turb, finj, atk, cegr = Engines().get_techs(name)
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


def adjust_co2(settings, df):
    """

    Args:
        settings: The SetInputs class of the alpha_package_costs module.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to HEV.

    Returns:
        A DataFrame of HEV packages with ICE-based CO2 values adjusted to reflect hybridization.

    """
    df['EPA_FTP_1 gCO2e/mi'] = df['EPA_FTP_1 gCO2e/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_city_hev']['value'])
    df['EPA_FTP_2 gCO2e/mi'] = df['EPA_FTP_2 gCO2e/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_city_hev']['value'])
    df['EPA_FTP_3 gCO2e/mi'] = df['EPA_FTP_3 gCO2e/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_city_hev']['value'])
    df['EPA_HWFET gCO2e/mi'] = df['EPA_HWFET gCO2e/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_hwy_hev']['value'])
    df['Combined GHG gCO2e/mi'] = df['Combined GHG gCO2e/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_cycle_hev']['value'])
    return df


def add_battery(settings, df):
    """

    Args:
        settings: The SetInputs class of the alpha_package_costs module.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to HEV.

    Returns:
        A DataFrame of packages with hybrid battery details added.

    """
    df.insert(len(df.columns), 'battery_kwh_gross', 0)
    df['battery_kwh_gross'] \
        = settings.hev_curves_dict['kWh_pack_per_kg_curbwt_curve']['x_cubed_factor'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 3 \
          + settings.hev_curves_dict['kWh_pack_per_kg_curbwt_curve']['x_squared_factor'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 2 \
          + settings.hev_curves_dict['kWh_pack_per_kg_curbwt_curve']['x_factor'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) \
          + settings.hev_curves_dict['kWh_pack_per_kg_curbwt_curve']['constant']
    return df


def add_motor(settings, df):
    """

    Args:
        settings: The SetInputs class of the alpha_package_costs module.
        df: A DataFrame of ICE-based ALPHA packages that are being "converted" to HEV.

    Returns:
        A DataFrame of packages with hybrid motor details added.

    """
    df.insert(len(df.columns), 'motor_kw', 0)
    df['motor_kw'] \
        = settings.hev_curves_dict['kW_motor_per_kg_curbwt_curve']['x_cubed_factor'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 3 \
          + settings.hev_curves_dict['kW_motor_per_kg_curbwt_curve']['x_squared_factor'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 2 \
          + settings.hev_curves_dict['kW_motor_per_kg_curbwt_curve']['x_factor'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) \
          + settings.hev_curves_dict['kW_motor_per_kg_curbwt_curve']['constant']
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
    ice_folder_path = settings.path_alpha_inputs / 'ICE'
    hev_folder_path = settings.path_alpha_inputs / 'HEV'
    hev_folder_path.mkdir(exist_ok=True)

    hev_packages_df = pd.DataFrame()
    sub_header = pd.DataFrame()
    alpha_files = [file for file in ice_folder_path.iterdir() if file.name.__contains__('.csv')]

    for idx, alpha_file in enumerate(alpha_files):
        if idx == 0:
            alpha_file_df = pd.read_csv(alpha_file)
            sub_header = pd.DataFrame(alpha_file_df.iloc[0, :]).transpose()
            alpha_file_df = pd.read_csv(alpha_file, skiprows=range(1, 2))
        else: alpha_file_df = pd.read_csv(alpha_file, skiprows=range(1, 2))
        alpha_file_df = clean_alpha_data(alpha_file_df, 'Aero Improvement %', 'Crr Improvement %', 'Weight Reduction %')
        df = SelectICEforHEV(alpha_file_df).return_df()
        hev_packages_df = pd.concat([hev_packages_df, df], axis=0, ignore_index=True)

    hev_packages_df = add_battery(settings, hev_packages_df)
    hev_packages_df = add_motor(settings, hev_packages_df)
    hev_packages_df = adjust_co2(settings, hev_packages_df)
    # hev_packages_df = add_size_scalers(settings, hev_packages_df)
    hev_packages_df = pd.concat([sub_header, hev_packages_df], axis=0, ignore_index=True)
    hev_packages_df.to_csv(hev_folder_path / 'HEV.csv', index=False)
    print(f'HEV packages file is saved to {hev_folder_path}')


if __name__ == '__main__':
    main()
