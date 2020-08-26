
import matplotlib.pyplot as plt


# label x-axis, y-axis and set axis title
def label_xy(ax, x_label_str, y_label_str):
    ax.set_xlabel(x_label_str, fontsize=9)
    ax.set_ylabel(y_label_str, fontsize=9)


# label x-axis, y-axis and set axis title
def label_xyt(ax, x_label_str, y_label_str, title_str):
    ax.set_xlabel(x_label_str, fontsize=9)
    ax.set_ylabel(y_label_str, fontsize=9)
    ax.set_title(title_str, fontsize=9)


# draw a horizontal line at:
def lineat(ax, y, *args, **kwargs):
    xlim = ax.get_xlim()
    ax.plot(xlim, [y, y], *args, **kwargs)
    ax.set_xlim(xlim)


# draw a vertical line at:
def vlineat(ax, x, *args, **kwargs):
    ylim = ax.get_ylim()
    ax.plot([x, x], ylim, *args, **kwargs)
    ax.set_ylim(ylim)


def figure():
    fig, ax1 = plt.subplots()
    ax1.grid(True, which='both')
    fig.show()
    return fig, ax1


def fplothg(x, y, *args, **kwargs):
    fig, ax1 = plt.subplots()
    ax1.plot(x, y, *args, **kwargs)
    ax1.grid(True, which='both')
    fig.show()
    return fig, ax1


def fplotyyhg(x, y, ylinespec, y2, y2linespec):
    fig, ax1 = plt.subplots()
    ax2 = ax1.twinx()
    ax1.plot(x, y, ylinespec)
    ax2.plot(x, y2, y2linespec)
    ax1.grid(True)
    # ax2.grid(True)
    fig.show()
    return fig, ax1, ax2


if __name__ == '__main__':
    import os, traceback

    try:
        fig, ax = fplothg([1, 2, 3], [4, 5, 6], 'r-')
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
