import pandas as pd
from alpha_package_costs import SetInputs as settings, Engines, clean_alpha_data, add_elements_for_package_key, package_key


class SelectICEforHEV:
    def __init__(self, df):
        self.df = df
        self.weight_reduction = 0
        self.aero = 20
        self.nonaero = 20
        self.startstop = 0

    def return_df(self):
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
        # return_df = pd.DataFrame(self.df.loc[(self.df['Aero Improvement %'] == self.aero)
        #                                      & (self.df['Crr Improvement %'] == self.nonaero)
        #                                      & (self.df['Weight Reduction %'] == self.weight_reduction)
        #                                      & (self.df['Start Stop'] == self.startstop), :])
        return_df.drop(columns='turb', inplace=True)
        return_df.reset_index(drop=True, inplace=True)
        return return_df


def adjust_co2(settings, df):
    df['EPA_FTP_1 gCO2/mi'] = df['EPA_FTP_1 gCO2/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_city_hev']['value'])
    df['EPA_FTP_2 gCO2/mi'] = df['EPA_FTP_2 gCO2/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_city_hev']['value'])
    df['EPA_FTP_3 gCO2/mi'] = df['EPA_FTP_3 gCO2/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_city_hev']['value'])
    df['EPA_HWFET gCO2/mi'] = df['EPA_HWFET gCO2/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_hwy_hev']['value'])
    df['Combined GHG gCO2/mi'] = df['Combined GHG gCO2/mi'] * (1 - settings.hev_metrics_dict['co2_reduction_cycle_hev']['value'])
    return df


def add_battery(settings, df):
    df.insert(len(df.columns), 'battery_kwh_gross', 0)
    df['battery_kwh_gross'] \
        = settings.hev_curves_dict['x_cubed_factor']['kWh_pack_per_kg_curbwt_curve'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 3 \
          + settings.hev_curves_dict['x_squared_factor']['kWh_pack_per_kg_curbwt_curve'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 2 \
          + settings.hev_curves_dict['x_factor']['kWh_pack_per_kg_curbwt_curve'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) \
          + settings.hev_curves_dict['constant']['kWh_pack_per_kg_curbwt_curve']
    return df


def add_motor(settings, df):
    df.insert(len(df.columns), 'motor_kw', 0)
    df['motor_kw'] \
        = settings.hev_curves_dict['x_cubed_factor']['kW_motor_per_kg_curbwt_curve'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 3 \
          + settings.hev_curves_dict['x_squared_factor']['kW_motor_per_kg_curbwt_curve'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) ** 2 \
          + settings.hev_curves_dict['x_factor']['kW_motor_per_kg_curbwt_curve'] * ((df['Test Weight lbs'] - 300)/settings.lbs_per_kg) \
          + settings.hev_curves_dict['constant']['kW_motor_per_kg_curbwt_curve']
    return df


def main():
    # alpha_folder = settings.path_alpha_inputs / '2017_12_01 future RSE'
    alpha_folder = settings.path_alpha_inputs / 'ICE'
    hev_folder_path = settings.path_alpha_inputs / 'HEV'
    hev_folder_path.mkdir(exist_ok=True)

    hev_packages_df = pd.DataFrame()
    alpha_files = [file for file in alpha_folder.iterdir() if file.name.__contains__('.csv')]

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
    hev_packages_df = pd.concat([sub_header, hev_packages_df], axis=0, ignore_index=True)
    hev_packages_df.to_csv(hev_folder_path / 'HEV.csv', index=False)
    print(f'HEV packages file is saved to {hev_folder_path}')


if __name__ == '__main__':
    main()
