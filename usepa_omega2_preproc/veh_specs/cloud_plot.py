#!
# Kevin Bolon 2017$
#%matplotlib inline

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import Grid


def pareto_frontier(Xs, Ys, maxX = True, maxY = True):
    '''
    Method to take two equally-sized lists and return just the elements which lie
    on the Pareto frontier, sorted into order.
    Default behaviour is to find the maximum for both X and Y, but the option is
    available to specify maxX = False or maxY = False to find the minimum for either
    or both of the parameters.
    '''
    # Sort the list in either ascending or descending order of X
    myList = sorted([[Xs[i], Ys[i]] for i in range(len(Xs))], reverse=maxX)
    # Start the Pareto frontier with the first value in the sorted list
    p_front = [myList[0]]
    # Loop through the sorted list
    for pair in myList[1:]:
        if maxY:
            if pair[1] >= p_front[-1][1]: # Look for higher values of Y…
                p_front.append(pair) # … and add them to the Pareto frontier
        else:
            if pair[1] <= p_front[-1][1]: # Look for lower values of Y…
                p_front.append(pair) # … and add them to the Pareto frontier
    # Turn resulting pairs back into a list of Xs and Ys
    p_frontX = [pair[0] for pair in p_front]
    p_frontY = [pair[1] for pair in p_front]
    return p_frontX, p_frontY

def plotcloud(p_front1,p_front2,p_front3,p_front4,x_vec, y_vec):
    fig = plt.figure(1)
    gridsize = (1 , 1)
    grid = Grid(fig, rect=111, nrows_ncols=gridsize,
                axes_pad=0.0, label_mode='L')
    fontscaler = 1
    ax = grid[0]
    ax.set_xlim(0, 1)
    ax.grid(True, which='major', color='grey', linewidth=0.1)
    ax.plot(p_front1[0], p_front1[1], color='r', linestyle='-', linewidth=0.5)
    ax.plot(p_front2[0], p_front2[1], color='b', linestyle='-', linewidth=0.5)
    ax.plot(p_front3[0], p_front3[1], color='k', linestyle='-', linewidth=0.5)
    ax.plot(p_front4[0], p_front4[1], color='g', linestyle='-', linewidth=0.5)
    ax.plot(x_vec, y_vec, marker='*',
        color='b', linestyle='', ms=10 * fontscaler, mew=1 * fontscaler,
        mec='k')
    #fig.savefig('C:/Users/KBolon/Desktop/cloudplot.png', dpi=600, transparent=True)  # rasterized image
    #fig.savefig()
    #fig.clf()

#rootdir = 'C:/Users/KBolon/Desktop/'  # location of run controller file
#df = pd.read_csv(rootdir + 'cloudpoints.txt',sep='\t',header = 0)
def cloud_plot(x_vec, y_vec, OEM):
    if len(x_vec) > 0:
        p_front1 = pareto_frontier(x_vec, y_vec,True, False)
        p_front2 = pareto_frontier(x_vec, y_vec,False, False)
        p_front3 = pareto_frontier(x_vec, y_vec,False, True)
        p_front4 = pareto_frontier(x_vec, y_vec,True, True)

        #p_front = (p_front1[0]+p_front2[0]+p_front3[0]+p_front4[0][::-1],p_front1[1]+p_front2[1]+p_front3[1]+p_front4[1][::-1])
        p_front = (p_front1[0] + p_front2[0][::-1] + p_front3[0] + p_front4[0][::-1],
                   p_front1[1] + p_front2[1][::-1] + p_front3[1] + p_front4[1][::-1])

        #p_front4 = ([p_front3[0][-1], p_front1[0][0]], [p_front3[1][-1], p_front1[1][0]])
        # p_front_int = p_front1+p_front2+p_front3+p_front4
        #
        # p_front_x = [i for sub in p_front_int[::2] for i in sub]
        # p_front_y = [i for sub in p_front_int[1::2] for i in sub]
        #
        # return(p_front_x,p_front_y)

        return(p_front)
    else:
        return([0],[0])