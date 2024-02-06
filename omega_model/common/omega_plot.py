"""

**Handy plotting functions for matplotlib plots.**

----

**CODE**

"""

print('importing %s' % __file__)
# see https://matplotlib.org/stable/tutorials/introductory/customizing.html#matplotlib-rcparams and
# https://matplotlib.org/stable/tutorials/introductory/customizing.html#the-matplotlibrc-file for more info
# on customizing matplotlib default settings
from matplotlib import rcParams
rcParams['figure.max_open_warning'] = -1  # disable max open figure warnings

import matplotlib.pyplot as plt


def label_xy(ax, x_label_str, y_label_str):
    """
    Label x-axis and y-axis.

    Args:
        ax (matplotlib.axes._subplots.AxesSubplot): the axis (plot) to label
        x_label_str (str): x-axis label
        y_label_str (str): y-axis label

    """
    ax.set_xlabel(x_label_str, fontsize=9)
    ax.set_ylabel(y_label_str, fontsize=9)


def label_xyt(ax, x_label_str, y_label_str, title_str):
    """
    Label x-axis, y-axis and set axis title.

    Args:
        ax (matplotlib.axes._subplots.AxesSubplot): the axis(plot) to label
        x_label_str (str): x-axis label
        y_label_str (str): y-axis label
        title_str (str): axis title

    Returns:

    """
    ax.set_xlabel(x_label_str, fontsize=9)
    ax.set_ylabel(y_label_str, fontsize=9)
    ax.set_title(title_str, fontsize=9)


def lineat(ax, y, *args, **kwargs):
    """
    Draw a horizontal line at a y-value.

    Args:
        ax (matplotlib.axes._subplots.AxesSubplot): the axis (plot) to draw on
        y (numeric): the vertical index of the line
        *args: optional positional arguments to pyplot.plot()
        **kwargs: optional keyword arguments to pyplot.plot()

    """
    xlim = ax.get_xlim()
    ax.plot(xlim, [y, y], *args, **kwargs)
    ax.set_xlim(xlim)


def vlineat(ax, x, *args, **kwargs):
    """
    Draw a vertical line at an x-value.

    Args:
        ax (matplotlib.axes._subplots.AxesSubplot): the axis to draw on
        x (numeric): the horizontal index of the line
        *args: optional positional arguments to pyplot.plot()
        **kwargs: optional keyword arguments to pyplot.plot()

    """
    ylim = ax.get_ylim()
    ax.plot([x, x], ylim, *args, **kwargs)
    ax.set_ylim(ylim)


def figure(reuse_figure=False):
    """
    Create a figure window with a single plot axis.

    Returns:
        2-tuple of figure and axis objects, respectively.

    """
    if reuse_figure:
        fig, ax1 = plt.subplots()
    else:
        fig, ax1 = plt.subplots(num=1, clear=True)

    ax1.grid(True, which='both')
    # fig.show()
    return fig, ax1


def fplothg(x, y, *args, reuse_figure=False, **kwargs):
    """
    Shortcut for figure, plot, hold on, grid on (based on Matlab plotting terminology)
    Creates a single axis plot, with grid.

    Args:
        x: x-values of data to plot
        y: y-values of data to plot
        *args: optional positional arguments to pyplot.plot()
        reuse_figure (bool): re-use figure window if ``True``
        **kwargs: optional keyword arguments to pyplot.plot()

    Returns:
        2-tuple of figure and axis objects, respectively.

    """
    if reuse_figure:
        fig, ax1 = plt.subplots()
    else:
        fig, ax1 = plt.subplots(num=1, clear=True)

    ax1.plot(x, y, *args, **kwargs)
    ax1.grid(True, which='both')
    # fig.show()
    return fig, ax1


def fplotyyhg(x, y, ylinespec, y2, y2linespec):
    """
    Shortcut for figure, plotyy, hold on, grid on (based on Matlab plotting terminology).
    Creates a plot with a double y-axis and grid.

    Args:
        x: x-values of data to plot
        y: y-values of data to plot on first y-axis
        ylinespec (str): line format string, e.g. 'b.-'
        y2: y-values of data to plot on second y-axis
        y2linespec (str): line format string, e.g. 'r.-'

    Returns:
        3-tuple of figure and two axis objects, respectively.

    """
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(x, y, ylinespec)
    ax2.plot(x, y2, y2linespec)
    ax1.grid(True)
    # ax2.grid(True)
    # fig.show()
    return fig, ax1, ax2


if __name__ == '__main__':
    import os, traceback

    try:
        fig, ax = fplothg([1, 2, 3], [4, 5, 6], 'r-')
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
