"""
omega_gui_functions
===================

"""

# from distutils.dir_util import copy_tree

from PySide2.QtWidgets import QFileDialog
import yaml

import pandas
import matplotlib.pyplot as plt
from matplotlib import cm


def open_file_action(filepath):
    data = yaml_loader(filepath)
    return data


def yaml_loader(filepath):
    """
    Loads a yaml formatted file and converts to a Python formatted dictionary.

    :param filepath: Full path to yaml formatted source file

    :return: Python formatted dictionary
    """
    with open(filepath, "r") as file_descriptor:
        data = yaml.full_load(file_descriptor)
    return data


def yaml_dump(filepath, data):
    """
    Dumps data to a yaml file.

    :param filepath: Full path to destination file
    :param data: Dictionary to save

    :return: N/A
    """
    with open(filepath, "w") as file_descriptor:
        yaml.dump(data, file_descriptor)

        # yaml.dump(data)

    # print("Open File")


def save_file_action(filepath, data):
    yaml_dump(filepath, data)
    """
    Dumps data to a yaml file.

    :param filepath: Full path to destination file
    :param data: Dictionary to save
    
    :return: N/A
    """


def file_dialog_save(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a file with extension options.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box

    :return: User selected file name, Echo file_type, Echo file_dialog_title
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    # dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    # temp = dialog.selectedFiles()
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title
    else:
        file_name = ""
        return file_name, file_type, file_dialog_title


def file_dialog(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a file with extension options.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box

    :return: User selected file name, echo file_type, echo file_dialog_title
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setFileMode(QFileDialog.ExistingFile)
    # dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    # temp = dialog.selectedFiles()
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title
    else:
        file_name = ""
        return file_name, file_type, file_dialog_title


def directory_dialog(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a directory.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box

    :return: User selected directory name, echo file_type, echo file_dialog_title
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setFileMode(QFileDialog.DirectoryOnly)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    # temp = dialog.selectedFiles()
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title
    else:
        file_name = ""
        return file_name, file_type, file_dialog_title


# def copy_files(source, destination):
#     copy_tree(source, destination)


def sec_to_hours(seconds):
    """
    Converts seconds to hours, minutes, and seconds.

    :param seconds: seconds

    :return: formatted xx hours  xx mins  xx seconds
    """
    a = str(seconds//3600)
    b = str((seconds % 3600)//60)
    c = str((seconds % 3600) % 60)
    d = "{} hours {} mins {} seconds".format(a, b, c)
    return d


def status_output_color(g):
    """
    Examines strings for specific cases to change the color for display.

    :param g: input string

    :return: color for display
    """
    if g.find("Manufacturer=") != -1:
        g = "green"
    elif g.find("RROR") == -1 and g.find("rror") == -1 and g.find("###") == -1 and g.find("FAIL") == -1\
            and g.find("Fail") == -1:
        g = "black"
    else:
        g = "red"
    return g


def test_plot_1(y_axis):
    """
    Reads a csv file and plots selected graph.

    :param y-axis: column to plot

    :return: N/A
    """
    df = pandas.read_csv('usepa_omega2_gui/elements/summary_results.csv')

    if len(y_axis) > 0:
        # print(y_axis)
        x_data = 'calendar_year'  # Column from spreadsheet for x axis
        y_data = y_axis  # Column from spreadsheet for y axis
        line_color = 'green'  # Plot line color
        line_style = 'solid'  # Plot line style
        line_width = 2  # Plot line width
        marker_type = 'o'  # MatPlotLib marker style
        marker_size = 4  # Marker size
        x_label = 'Calendar Year'  # Label for x axis
        y_label = y_axis  # Label for y axis
        plot_title = 'OMEGA Results'  # Plot title

        cmap = cm.get_cmap('tab10')  # Color map

        # Define plot using dataframe formed from spreadsheet
        ax = df.plot(x=x_data, y=y_data, linestyle=line_style, marker=marker_type,
                     linewidth=line_width, markersize=marker_size, xlabel=x_label, ylabel=y_label,
                     title=plot_title, color=cmap(0))
        # ax = df.plot(x=x_data, y=y_axis, color=line_color, linestyle=line_style, marker=marker_type,
        #              linewidth=line_width, markersize=marker_size, xlabel=x_label, ylabel=y_label,
        #              title=plot_title)
        # Add more series in same plot
        # df.plot(x=x_data, y="bev_non_hauling_share_frac", ax=ax, color=cmap(.1))
        # df.plot(x=x_data, y="bev_hauling_share_frac", ax=ax, color=cmap(.2))

        ax.grid()  # Show grid
        plt.show()  # Show plot
