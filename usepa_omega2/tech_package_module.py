import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


compliance_start_year = 2020 # start year of modeling which would come from an input file or selection
compliance_end_year = 2050 # end year of modeling which would come from an input file or selection
compliance_year = 2025 # calendar year being analyzed, this would be passed to this module

GRAM_CO2_per_MJ_ice = 8887 / 131.76
GRAM_CO2_per_MJ_bev = 250 / 3.6


def log_tech_cost(a_coeff, b_coeff, x_value_min, x_value_max):
    increment = get_increment(x_value_min, x_value_max)
    x_values = range(int(x_value_min * 1000), int(x_value_max * 1000 + 1), int(increment * 1000))
    tech_cost = dict((x_value / 1000, a_coeff * np.log((x_value - x_value_min * 1000) / 1000) + b_coeff) for x_value in x_values)
    return tech_cost


def exponential_tech_cost(a_coeff, b_coeff, c_coeff, x_value_min, x_value_max):
    increment = get_increment(x_value_min, x_value_max)
    x_values = range(int(x_value_min * 1000), int(x_value_max * 1000 + 1), int(increment * 1000))
    tech_cost = dict((x_value / 1000, a_coeff * b_coeff ** (x_value / 1000 - x_value_min - x_value_min) + c_coeff) for x_value in x_values)
    return tech_cost


def learning_oem_planning(rate):
    calendar_years = range(compliance_start_year, compliance_end_year + 1)
    learning_factors = dict((calendar_year, rate * (calendar_year - compliance_start_year) + 1) for calendar_year in calendar_years)
    return learning_factors


def create_packages(compliance_start_year, compliance_end_year, powertrain_costs, powertrain_learning, roadload_costs, roadload_learning, gram_co2pMJ):
    package_cost = dict()
    package_co2 = dict()
    for model_year in range(compliance_start_year, compliance_end_year + 1):
        for powertrain_efficiency in list(powertrain_costs.keys()):
            for roadload_efficiency in list(roadload_costs.keys()):
                package_cost[model_year, powertrain_efficiency, roadload_efficiency] = powertrain_costs[powertrain_efficiency] * powertrain_learning[model_year] \
                                                                                       + roadload_costs[roadload_efficiency] * roadload_learning[model_year]
                package_co2[model_year, powertrain_efficiency, roadload_efficiency] = round(roadload_efficiency / powertrain_efficiency * gram_co2pMJ, 0)
    return package_cost, package_co2


def get_increment(x_value_min, x_value_max):
    increments = int(round(20 * ((x_value_max - x_value_min) * 100) / 10, 0))
    increment = (x_value_max - x_value_min) / increments
    return increment


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


# create cost dictionaries
roadload_techcost_ice = log_tech_cost(-1000, 100, .6, 1)
roadload_techcost_bev = log_tech_cost(-1000, 100, .6, 1)

powertrain_techcost_ice = exponential_tech_cost(1000, 1000, 400, 0.2, 0.4)
powertrain_techcost_bev = exponential_tech_cost(10000, 2, 0, .8, .95)

roadload_learning_oem_ice = learning_oem_planning(-0.01)
roadload_learning_oem_bev = learning_oem_planning(-0.01)

powertrain_learning_oem_ice = learning_oem_planning(-0.005)
powertrain_learning_oem_bev = learning_oem_planning(-0.02)

# create package dictionaries
package_cost_ice, package_co2_ice = create_packages(compliance_start_year, compliance_end_year, powertrain_techcost_ice, powertrain_learning_oem_ice, roadload_techcost_ice, roadload_learning_oem_ice, GRAM_CO2_per_MJ_ice)
package_cost_bev, package_co2_bev = create_packages(compliance_start_year, compliance_end_year, powertrain_techcost_bev, powertrain_learning_oem_bev, roadload_techcost_bev, roadload_learning_oem_bev, GRAM_CO2_per_MJ_bev)

# create lists for figures
cost_dicts = [roadload_techcost_ice, roadload_techcost_bev, powertrain_techcost_ice, powertrain_techcost_bev]
cost_dicts_names = ['Cost, Road load, ICE', 'Cost, Road load, BEV', 'Cost, Powertrain, ICE', 'Cost, Powertrain, BEV']

learning_oem_dicts = [roadload_learning_oem_ice, roadload_learning_oem_bev, powertrain_learning_oem_ice, powertrain_learning_oem_bev]
learning_oem_dicts_names = ['OEM learning, Road load, ICE', 'OEM learning, Road load, BEV', 'OEM learning, Powertrain, ICE', 'OEM learning, Powertrain, BEV']

package_cost_dicts = [package_cost_ice, package_cost_bev]
package_cost_dicts_names = ['Package costs, ICE', 'Package costs, BEV']

package_co2_dicts = [package_co2_ice, package_co2_bev]
package_co2_dicts_names = ['Package CO2, ICE', 'Package CO2, BEV']

# create figures
tech_package_module_line_charts(cost_dicts, cost_dicts_names, 'Efficiency', 'Cost ($)')
tech_package_module_line_charts(learning_oem_dicts, learning_oem_dicts_names, 'Calendar year', 'Learning scalar')

tech_package_module_scatter_chart(package_cost_ice, package_co2_ice, 'Package CO2 vs. Cost, ICE', 'Cost ($)', 'CO2 (g/mi)')
tech_package_module_scatter_chart(package_cost_bev, package_co2_bev, 'Package CO2 vs. Cost, BEV', 'Cost ($)', 'CO2 (g/mi)')

# min(package_co2_bev, key=package_co2_bev.get) # returns key at min CO2 value where key, right now, is a tuple of (MY, PTeff, RLeff)
# min(package_cost_bev, key=package_cost_bev.get) # returns key at min cost value where key, right now, is a tuple of (MY, PTeff, RLeff)

# # create cost figures
# loop = 0
# for cost_dict in cost_dicts:
#     plt.figure()
#     plt.plot(*zip(*sorted(cost_dict.items())))
#     plt.title(cost_dicts_names[loop])
#     plt.xlabel('Efficiency')
#     plt.ylabel('Cost ($)')
#     plt.grid()
#     loop += 1
#
# # create learning figures
# loop = 0
# for learning_oem_dict in learning_oem_dicts:
#     plt.figure()
#     plt.plot(*zip(*sorted(learning_oem_dict.items())))
#     plt.title(learning_oem_dicts_names[loop])
#     plt.xlabel('Calendar year')
#     plt.ylabel('Learning scalar')
#     plt.grid()
#     loop += 1
