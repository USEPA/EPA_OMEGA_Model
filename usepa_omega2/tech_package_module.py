import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


compliance_start_year = 2020 # start year of modeling which would come from an input file or selection
compliance_end_year = 2050 # end year of modeling which would come from an input file or selection

PATH_PROJECT = Path.cwd()
PATH_INPUTS = PATH_PROJECT.joinpath('inputs')

GRAM_CO2_per_MJ_ice = 8887 / 131.76
GRAM_CO2_per_MJ_bev = 250 / 3.6

techcost_curves_file = pd.ExcelFile(PATH_INPUTS.joinpath('techcost_curves.xlsx'))
techcost_curves_roadload = pd.read_excel(techcost_curves_file, 'roadload')
techcost_curves_powertrain = pd.read_excel(techcost_curves_file, 'powertrain')

co2_perMJ_file = pd.ExcelFile(PATH_INPUTS.joinpath('co2_perMJ.xlsx'))
co2_perMJ_ice_df = pd.read_excel(co2_perMJ_file, 'ICE')
co2_perMJ_bev_df = pd.read_excel(co2_perMJ_file, 'BEV')


class TechCosts:
    def __init__(self, vehicle_classification, compliance_start_year, compliance_end_year):
        self.vehicle_classification = vehicle_classification
        self.compliance_start_year = compliance_start_year
        self.compliance_end_year = compliance_end_year

    def log_tech_cost(self, a_coeff, b_coeff, metric_value_min, metric_value_max):
        increment = self.get_increment(metric_value_min, metric_value_max)
        metric_values = range(int(metric_value_min * 1000), int(metric_value_max * 1000 + 1), int(increment * 1000))
        tech_cost = dict((metric_value / 1000, a_coeff * np.log((metric_value - metric_value_min * 1000) / 1000) + b_coeff) for metric_value in metric_values)
        return tech_cost

    def exponential_tech_cost(self, a_coeff, b_coeff, c_coeff, metric_value_min, metric_value_max):
        increment = self.get_increment(metric_value_min, metric_value_max)
        metric_values = range(int(metric_value_min * 1000), int(metric_value_max * 1000 + 1), int(increment * 1000))
        tech_cost = dict((metric_value / 1000, a_coeff * b_coeff ** (metric_value / 1000 - metric_value_min - metric_value_min) + c_coeff) for metric_value in metric_values)
        return tech_cost

    def learning_oem_planning(self, rate):
        calendar_years = range(compliance_start_year, compliance_end_year + 1)
        learning_factors = dict((calendar_year, rate * (calendar_year - compliance_start_year) + 1) for calendar_year in calendar_years)
        return learning_factors

    def get_increment(self, metric_value_min, metric_value_max):
        increments = int(round(20 * ((metric_value_max - metric_value_min) * 100) / 10, 0))
        increment = (metric_value_max - metric_value_min) / increments
        return increment


class PackageCosts:
    def __init__(self, vehicle_classification, powertrain, compliance_start_year, compliance_end_year):
        self.vehicle_classification = vehicle_classification
        self.powertrain = powertrain
        self.compliance_start_year = compliance_start_year
        self.compliance_end_year = compliance_end_year

    def create_packages(self, powertrain_costs, powertrain_learning_scalars, roadload_costs, roadload_learning_scalars, model_year):
        if self.powertrain == 'ice':
            co2_perMJ = co2_perMJ_ice
        elif self.powertrain == 'bev':
            co2_perMJ = co2_perMJ_bev
        else:
            co2_perMJ = dict()
        package_cost = dict()
        package_co2 = dict()
        for powertrain_metric in list(powertrain_costs.keys()):
            for roadload_metric in list(roadload_costs.keys()):
                package_cost[powertrain_metric, roadload_metric] = powertrain_costs[powertrain_metric] * powertrain_learning_scalars[model_year] \
                                                                   + roadload_costs[roadload_metric] * roadload_learning_scalars[model_year]
                package_co2[powertrain_metric, roadload_metric] = round(roadload_metric / powertrain_metric * co2_perMJ[model_year], 0)
        package_cost_df = pd.DataFrame().from_dict(package_cost, orient='index', columns=['cost'])
        package_cost_df.reset_index(drop=False, inplace=True)
        package_cost_df.rename(columns={'index': 'powertrain_roadload_metrics'}, inplace=True)
        package_co2_df = pd.DataFrame().from_dict(package_co2, orient='index', columns=['co2'])
        package_co2_df.reset_index(drop=False, inplace=True)
        package_co2_df.rename(columns={'index': 'powertrain_roadload_metrics'}, inplace=True)
        package_cost_co2 = pd.concat([package_cost_df, package_co2_df['co2']], axis=1, ignore_index=False)
        return package_cost_co2


def tech_package_module_line_charts(dictionaries, names, x_axis_name, y_axis_name):
    loop = 0
    for dictionary in dictionaries:
        plt.figure()
        plt.plot(*zip(*sorted(dictionary.items())))
        plt.title(names[loop])
        plt.xlabel(x_axis_name)
        plt.ylabel(y_axis_name)
        plt.grid()
        loop += 1
    return


def tech_package_module_scatter_chart(x_dictionary, y_dictionary, plot_title, x_axis_name, y_axis_name):
    plt.figure()
    plt.scatter(x_dictionary.values(), y_dictionary.values())
    plt.title(plot_title)
    plt.xlabel(x_axis_name)
    plt.ylabel(y_axis_name)
    plt.grid()
    return


def package_cost_co2_scatter_chart(pkg_cost_co2, model_year, vehicle_classification, x_axis_name, y_axis_name):
    plt.figure()
    plt.scatter(pkg_cost_co2['cost'], pkg_cost_co2['co2'])
    plt.title(vehicle_classification + '; ' + str(model_year))
    plt.xlabel(x_axis_name)
    plt.ylabel(y_axis_name)
    plt.grid()
    return


roadload_techcosts = dict()
roadload_learning = dict()
for index, row in techcost_curves_roadload.iterrows():
    vehicle_classification = row['vehicle_classification']
    cost_curve_function = row['cost_curve_function']
    a_coeff = row['a_coefficient']
    b_coeff = row['b_coefficient']
    c_coeff = row['c_coefficient']
    curve_metric = row['curve_metric']
    metric_value_min = row['metric_value_min']
    metric_value_max = row['metric_value_max']
    learning_rate = row['learning_rate_oem']

    if cost_curve_function == 'log':
        techcost = TechCosts(vehicle_classification, compliance_start_year, compliance_end_year).log_tech_cost(a_coeff, b_coeff, metric_value_min, metric_value_max)
    else:
        techcost = TechCosts(vehicle_classification, compliance_start_year, compliance_end_year).exponential_tech_cost(a_coeff, b_coeff, c_coeff, metric_value_min, metric_value_max)

    learning_curve = TechCosts(vehicle_classification, compliance_start_year, compliance_end_year).learning_oem_planning(learning_rate)

    roadload_techcosts[vehicle_classification] = techcost
    roadload_learning[vehicle_classification] = learning_curve

powertrain_techcosts = dict()
powertrain_learning = dict()
for index, row in techcost_curves_powertrain.iterrows():
    vehicle_classification = row['vehicle_classification']
    cost_curve_function = row['cost_curve_function']
    a_coeff = row['a_coefficient']
    b_coeff = row['b_coefficient']
    c_coeff = row['c_coefficient']
    curve_metric = row['curve_metric']
    metric_value_min = row['metric_value_min']
    metric_value_max = row['metric_value_max']
    learning_rate = row['learning_rate_oem']

    if cost_curve_function == 'log':
        techcost = TechCosts(vehicle_classification, compliance_start_year, compliance_end_year).log_tech_cost(a_coeff, b_coeff, metric_value_min, metric_value_max)
    else:
        techcost = TechCosts(vehicle_classification, compliance_start_year, compliance_end_year).exponential_tech_cost(a_coeff, b_coeff, c_coeff, metric_value_min, metric_value_max)

    learning_curve = TechCosts(vehicle_classification, compliance_start_year, compliance_end_year).learning_oem_planning(learning_rate)

    powertrain_techcosts[vehicle_classification] = techcost
    powertrain_learning[vehicle_classification] = learning_curve

# make dictionaries from the co2_perMJ DataFrames
co2_perMJ_ice = dict()
co2_perMJ_bev = dict()
for index, row in co2_perMJ_ice_df.iterrows():
    key = row['calendar_year']
    value = row['gramCO2/MJ']
    co2_perMJ_ice.update({key: value})

for index, row in co2_perMJ_bev_df.iterrows():
    key = row['calendar_year']
    value = row['gramCO2/MJ']
    co2_perMJ_bev.update({key: value})

package_costs_co2 = dict()
for index, row in techcost_curves_powertrain.iterrows():
    vehicle_classification = row['vehicle_classification']
    powertrain = row['powertrain']
    print('Creating packages for ' + vehicle_classification)
    for model_year in range(compliance_start_year, compliance_end_year + 1):
        package_costs_co2[vehicle_classification, model_year] = \
            PackageCosts(vehicle_classification, powertrain, compliance_start_year, compliance_end_year)\
                .create_packages(powertrain_techcosts[vehicle_classification], powertrain_learning[vehicle_classification], roadload_techcosts[vehicle_classification], roadload_learning[vehicle_classification], model_year)


# create lists for figures
# cost_dicts = [roadload_techcost_ice, roadload_techcost_bev, powertrain_techcost_ice, powertrain_techcost_bev]
# cost_dicts_names = ['Cost, Road load, ICE', 'Cost, Road load, BEV', 'Cost, Powertrain, ICE', 'Cost, Powertrain, BEV']

# cost_vs_efficiency_dicts = [powertrain_techcost_ice, powertrain_techcost_bev]
# cost_vs_energypermile_dicts = [roadload_techcost_ice, roadload_techcost_bev]
# cost_vs_efficiency_dicts_names = ['Cost, Powertrain, ICE', 'Cost, Powertrain, BEV']
# cost_vs_energypermile_dicts_names = ['Cost, Road load, ICE', 'Cost, Road load, BEV']
#
# learning_oem_dicts = [roadload_learning_oem_ice, roadload_learning_oem_bev, powertrain_learning_oem_ice, powertrain_learning_oem_bev]
# learning_oem_dicts_names = ['OEM learning, Road load, ICE', 'OEM learning, Road load, BEV', 'OEM learning, Powertrain, ICE', 'OEM learning, Powertrain, BEV']
#
# package_cost_dicts = [package_cost_ice, package_cost_bev]
# package_cost_dicts_names = ['Package costs, ICE', 'Package costs, BEV']
#
# package_co2_dicts = [package_co2_ice, package_co2_bev]
# package_co2_dicts_names = ['Package CO2, ICE', 'Package CO2, BEV']
#
# # create figures
# # tech_package_module_line_charts(cost_dicts, cost_dicts_names, 'Efficiency', 'Cost ($)')
# tech_package_module_line_charts(cost_vs_efficiency_dicts, cost_vs_efficiency_dicts_names, 'Efficiency', 'Cost ($)')
# tech_package_module_line_charts(cost_vs_energypermile_dicts, cost_vs_energypermile_dicts_names, 'MJ/mile', 'Cost ($)')
# tech_package_module_line_charts(learning_oem_dicts, learning_oem_dicts_names, 'Calendar year', 'Learning scalar')
#
# tech_package_module_scatter_chart(package_cost_ice, package_co2_ice, 'Package CO2 vs. Cost, ICE', 'Cost ($)', 'CO2 (g/mi)')
# tech_package_module_scatter_chart(package_cost_bev, package_co2_bev, 'Package CO2 vs. Cost, BEV', 'Cost ($)', 'CO2 (g/mi)')

