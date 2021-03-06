import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

start_year = 2020 # start year of modeling which would come from an input file or selection
end_year = 2050 # end year of modeling which would come from an input file or selection
compliance_year = 2025 # calendar year being analyzed, this would be passed to this module

ice_cost_scalar = 1
bev_cost_scalar = 1
base_cost = 30000
ice_costs = dict()
bev_costs = dict()
for year in range(start_year, end_year + 1):
    ice_costs.update({year: 500 * (1 + .05) ** (year - start_year) * ice_cost_scalar})
    bev_costs.update({year: 12000 * (1 - .07) ** (year - start_year) * bev_cost_scalar})


def ice_cost_per_mile(compliance_year, dollars_per_gal_start, dollars_per_gallon_increase, base_mpg, mpg_increase):
    """
    This is just a function to generate some cpm metrics for testing, this won't be used in final code
    :param start_year:
    :param compliance_year:
    :param dollars_per_gal_start:
    :param dollars_per_gallon_increase:
    :param base_mpg:
    :param mpg_increase: 1.5% per year would be passed as 0.015
    :return: cost per mile in the compliance year
    """
    ice_cpm = pd.DataFrame({'compliance_year': range(start_year, end_year + 1), 'cpm': ''})
    ice_cpm['cpm'] = (dollars_per_gal_start + dollars_per_gallon_increase * (ice_cpm['compliance_year'] - start_year)) / \
                     (1 / ((1 / base_mpg)*(1 - mpg_increase) ** (ice_cpm['compliance_year'] - start_year)))
    ice_cpm.set_index('compliance_year', inplace=True)
    ice_cpm_compliance_year = ice_cpm.at[compliance_year, 'cpm']
    return ice_cpm_compliance_year


def bev_cost_per_mile(compliance_year, dollars_per_mile_start, kWh_per_mile_decrease):
    """
    This is just a function to generate some cpm metrics for testing, this won't be used in final code
    :param start_year:
    :param compliance_year:
    :param dollars_per_kWh:
    :param kWh_per_mile_decrease: 1% decrease in consumption would be entered as 0.01
    :return: cost per mile in the compliance year
    """
    bev_cpm = pd.DataFrame({'compliance_year': range(start_year, end_year + 1), 'cpm': ''})
    bev_cpm['cpm'] = dollars_per_mile_start * (1 - kWh_per_mile_decrease) ** (compliance_year - start_year)
    bev_cpm.set_index('compliance_year', inplace=True)
    bev_cpm_compliance_year = bev_cpm.at[compliance_year, 'cpm']
    return bev_cpm_compliance_year


def logistic_function(L, k, t_halfway, year):
    """
    Adapted from https://en.wikipedia.org/wiki/Logistic_function
    :param L: The maximum value (a value of one denotes 100% adoption).
    :param k: The measure of steepness of the adoption where 2 would be steeper than 1, 0.5 less steep than 1.
    :param t_halfway: The time value relative to the start year where 50% adoption toward reaching L is achieved.
    :param year: The year for which the adoption rate is being sought.
    :return: The adoption rate when time, relative to the start year, equals year.
    """
    adoption = L / (1 + np.exp(-k * (year - (start_year + t_halfway))))
    return adoption


def steepness_of_adoption(ice_metric1, ice_metric2, bev_metric1, bev_metric2, weight_metric1, weight_metric2, miles):
    """
    :param ice_metric1: Right now this is new vehicle cost
    :param ice_metric2: Right now this is cost per mile
    :param bev_metric1: Right now this is new vehicle cost
    :param bev_metric2: Right now this is cost per mile
    :param weight_metric1: Weighting factor for new vehicle purchase
    :param weight_metric2: Weighting factor for fuel costs
    :param miles: Number of miles considered for fuel costs (not actual VMT, but what's the person considering when buying)
    :return: The steepness of adoption for use in the adoption rate calculation for the given compliance year.
    """
    score = (bev_metric1 - ice_metric1) * weight_metric1 + (bev_metric2 - ice_metric2) * weight_metric2 * miles
    if score > 0:
        steepness = 0.5 + 100 / score
    else:
        steepness = 1
    return steepness


def year_to_halfway(ice_costs, bev_costs, base_cost, scalar):
    """

    :param ice_costs:
    :param bev_costs:
    :param base_cost:
    :param scalar: BEV costs must be within the ice_costs multiplied by the scalar to reach the halfway point to max_adoption (and/or adjusted max_adoption)
    :return: The year in which the BEV costs are within the scalar range of ICE costs to suggest equivalency in consumer purchase decisions.
    """
    for yr in range(start_year, end_year + 1):
        if bev_costs[yr] + base_cost <= (ice_costs[yr] + base_cost) * scalar: # if cost ratio <= scalar
            year_to_halfway = yr
            break
        else:
            year_to_halfway = 2050
    return year_to_halfway


def max_adoption_adjustment(ice_costs, bev_costs, base_cost, year, ratio_100, ratio_3):
    """

    :param ice_costs:
    :param bev_costs:
    :param base_cost:
    :param year: The year for which there would be no adjustment to the max_adoption rate (i.e., 2050 or some out-year)
    :param ratio_100: The ratio of BEV to ICE costs that would result in the max_adoption rate.
    :param ratio_3: The ratio of BEV to ICE costs that results in a 3% adoption rate (i.e., ~today's adoption rate)
    :return: The percentage adjustment to be applied to the max_adoption rate to get the adjusted adoption rate.
    """
    if ratio_100 < 1:
        cost_ratio = (bev_costs[year] + base_cost) / (ice_costs[year] + base_cost) # this is my x value in mx + b
        relationship_slope = (1 - 0.03) / (ratio_100 - ratio_3)
        pct_intercept = - ratio_100 * relationship_slope + 1
        percent_of_max_adoption = relationship_slope * cost_ratio + pct_intercept
    else:
        percent_of_max_adoption = 1
    return percent_of_max_adoption


ice_metric1 = ice_costs[compliance_year] + base_cost
bev_metric1 = bev_costs[compliance_year] + base_cost
ice_metric2 = ice_cost_per_mile(compliance_year, 3, 0.1, 30, 0.015)
bev_metric2 = bev_cost_per_mile(compliance_year, 0.04, 0.005)
k = steepness_of_adoption(ice_metric1, ice_metric2, bev_metric1, bev_metric2, .75, .25, 30000)
t_halfway = year_to_halfway(ice_costs, bev_costs, base_cost, 1.2) - start_year
max_adoption = .8
L = max_adoption * max_adoption_adjustment(ice_costs, bev_costs, base_cost, 2050, .5, 60000/30000)

# what all the fuss is about
compliance_year_cap = round(logistic_function(L, k, t_halfway, compliance_year), 2)

# draw a chart
logistic_curve_dict = dict()
plt.figure()
for year in range(start_year, end_year + 1):
    logistic_curve_dict[year] = logistic_function(L, k, t_halfway, year)
plt.plot(*zip(*sorted(logistic_curve_dict.items())))
plt.xlabel('Model Year')
plt.ylabel('Adoption Rate')
k_round = round(k, 2)
L_round = round(L, 2)
plt.title('Adoption adj_max=' + str(L_round) + '; k=' + str(k_round) + '; BEV cap=' + str(compliance_year_cap) + ' in compliance year=' + str(compliance_year))
plt.grid()



# def shifted_gompertz_dist(p, q, year):
#     """
#     Adapted from https://en.wikipedia.org/wiki/Shifted_Gompertz_distribution
#     :param p: The coefficient of innovation where p = 0 reflects zero innovation.
#     :param q: The coefficient of imitation where q = 0 reflects zero imitation.
#     :param year: The year for which the adoption rate is being sought.
#     :return: The cumulative distribution rate when time, relative to the start year, equals year.
#     """
#     cdf = (1 - np.exp(-(p + q) * (year - start_year))) / (1 + q/p) ** (np.exp(-(p + q) * (year - start_year))) # cumulative distribution function
#     return cdf
#
#
# def bass_diffusion(p, q, year):
#     """
#     Adapted from https://en.wikipedia.org/wiki/Bass_diffusion_model
#     :param p: The coefficient of innovation where p = 0 reflects zero innovation.
#     :param q: The coefficient of imitation where q = 0 reflects zero imitation.
#     :param year: The year for which the adoption rate is being sought.
#     :return: The installed base rate when time, relative to the start year, equals year.
#     """
#     ibf = (1 - np.exp(-(p + q) * (year - start_year))) / (1 + q/p * np.exp(-(p + q) * (year - start_year))) # installed base fraction
#     return ibf

# pen_rate_logistic = logistic_function(1, 1, 5, 2025)
# pen_rate_gompertz = shifted_gompertz_dist(.000018, .3999, 2025)
#
# logistic_curve_dict = dict()
# gompertz_curve_dict = dict()
# bass_curve_dict = dict()
#
# for steepness in range(25, 125, 25):
#     plt.figure()
#     L = 0.8
#     k = steepness / 100
#     for t_halfway in range(8, 15, 1):
#         logistic_curve_dict = dict()
#         for year in range(start_year, 2050):
#             # t_halfway = halfway
#             logistic_curve_dict[year] = logistic_function(L, k, t_halfway, year)
#             logistic_curve_df = pd.DataFrame([logistic_curve_dict])
#             logistic_curve_df = logistic_curve_df.transpose()
#             plt.plot(logistic_curve_df.index, logistic_curve_df[0])
#     plt.xlabel('Model Year')
#     plt.ylabel('Adoption Rate')
#     plt.title('Logistic, k=' + str(k))
#     plt.grid()
#
#
# plt.figure()
# for num in range(10, 61, 10):
#     p = .0001
#     q = num/100
#     gompertz_curve_dict = dict()
#     for year in range(start_year, 2051):
#         gompertz_curve_dict[year] = shifted_gompertz_dist(p, q, year)
#         gompertz_curve_df = pd.DataFrame([gompertz_curve_dict])
#         gompertz_curve_df = gompertz_curve_df.transpose()
#         plt.plot(gompertz_curve_df.index, gompertz_curve_df[0])
#         # plt.legend('p=' + str(p), 'q=' + str(q))
# plt.xlabel('Model Year')
# plt.ylabel('Adoption Rate')
# plt.title('Gompertz')
# plt.grid()
#
# plt.figure()
# for num in range(30, 81, 10):
#     p = .0001
#     q = num/100
#     bass_curve_dict = dict()
#     for year in range(start_year, 2051):
#         bass_curve_dict[year] = bass_diffusion(p, q, year)
#         bass_curve_df = pd.DataFrame([bass_curve_dict])
#         bass_curve_df = bass_curve_df.transpose()
#         plt.plot(bass_curve_df.index, bass_curve_df[0])
#         # plt.legend('p=' + str(p), 'q=' + str(q))
# plt.xlabel('Model Year')
# plt.ylabel('Adoption Rate')
# plt.title('Bass')
# plt.grid()
#
# logistic_curve_df = pd.DataFrame([logistic_curve_dict])
# logistic_curve_df = logistic_curve_df.transpose()
# plt.figure()
# plt.plot(logistic_curve_df.index, logistic_curve_df[0])
# plt.xlabel('Model Year')
# plt.ylabel('Adoption Rate')
# plt.title('Logistic')
# plt.grid()
#
# gompertz_curve_df = pd.DataFrame([gompertz_curve_dict])
# gompertz_curve_df = gompertz_curve_df.transpose()
# plt.figure()
# plt.plot(gompertz_curve_df.index, gompertz_curve_df[0])
# plt.xlabel('Model Year')
# plt.ylabel('Adoption Rate')
# plt.grid()
