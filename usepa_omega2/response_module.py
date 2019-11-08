import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

start_year = 2019 # start year of modeling which would come from an input file or selection

def adoption_rate(L, k, x0, year):
    """

    :param L: The maximum value (a value of one denotes 100% adoption)
    :param k: The measure of steepness of the adoption where 2 would be steeper than 1, 0.5 less steep than 1
    :param x0: The x value relative to the start year where 50% adoption toward reaching L is achieved (x being the year in our case?)
    :param year: The year for which the adoption rate is being sought.
    :return: The adoption rate when x = year
    """
    adoption = L / (1 + np.exp(-k * (year - (start_year + x0))))
    return adoption


pen_rate = adoption_rate(1, 1, 5, 2025)
diffusion_curve_dict = dict()
# diffusion_curve_df = pd.DataFrame()
for year in range(start_year, 2031):
    L = 0.8
    k = 1
    x0 = 5
    diffusion_curve_dict[year] = adoption_rate(L, k, x0, year)

diffusion_curve_df = pd.DataFrame([diffusion_curve_dict])
diffusion_curve_df = diffusion_curve_df.transpose()
plt.figure()
x50 = x0 + start_year
# plt.title('L=%s, k=%s, x0=%s' % str(L) % str(k) % str(x50))
plt.plot(diffusion_curve_df.index, diffusion_curve_df[0])
plt.xlabel('Model Year')
plt.ylabel('Adoption Rate')
plt.grid()
