"""

Contains functions used by the GUI.

"""

from PySide2.QtWidgets import QFileDialog
import yaml

import pandas
import matplotlib.pyplot as plt
from matplotlib import cm

import psutil
import os

# import pyqtgraph as pg


def open_file_action(filepath):
    """
    Loads a yaml formatted file and converts to a Python formatted dictionary.

    :param filepath: Full path of yaml source file
    :return: Python formatted dictionary
    """

    with open(filepath, "r") as file_descriptor:
        data = yaml.full_load(file_descriptor)
    return data


def save_file_action(filepath, data):
    """
    Dumps data to a yaml file.

    :param filepath: Full path to destination file
    :param data: Dictionary to save
    :return:
    """

    with open(filepath, "w") as file_descriptor:
        yaml.dump(data, file_descriptor)


def file_dialog_save(file_name, file_type, file_dialog_title):
    """

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
    :return: User selected file name, Echo file_type, Echo file_dialog_title
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
    :return: User selected directory name, Echo file_type, Echo file_dialog_title
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

    :param seconds: Seconds
    :return: Formatted xx hours  xx mins  xx seconds
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
    :return: Color for display
    """

    if g.find("Manufacturer=") != -1:
        g = "green"
    elif g.find("RROR") == -1 and g.find("rror") == -1 and g.find("###") == -1 and g.find("FAIL") == -1\
            and g.find("Fail") == -1:
        g = "black"
    else:
        g = "red"
    return g


def test_plot_2(plot_selection, scenario_selection, plot_select_directory_name, plot_select_directory):
    """
    Reads a csv file and plots selected graph.

    :param plot_selection:
    :param scenario_selection:
    :param plot_select_directory_name:
    :param plot_select_directory:
    :return:
    """

    from __init__ import gui_path

    import os
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep

    print('path = %s' % path)
    print('gui_path = %s' % gui_path)

    df = pandas.read_csv(path + 'omega_gui/elements/plot_definition.csv', index_col=0)

    if len(plot_selection) > 0:
        # print(plot_selection)
        # a = (df.loc[plot_selection, 'y_data_1'])
        x_data = (df.loc[plot_selection, 'x_data'])  # Column from spreadsheet for x axis
        # y_data = (df.loc[plot_selection, 'y_data_1'])  # Column from spreadsheet for y axis
        # file_name = (df.loc[plot_selection, 'plot_source'])  # Column from spreadsheet for file name
        file_name = plot_select_directory
        df1 = pandas.read_csv(file_name)  # Read source filename into dataframe
        df1 = df1.loc[df1['session_name'] == scenario_selection]  # Strip off all rows except selected scenario
        line_style = 'solid'  # Plot line style
        line_width = 2  # Plot line width
        marker_type = 'o'  # MatPlotLib marker style
        marker_size = 4  # Marker size
        x_label = (df.loc[plot_selection, 'x_label'])  # Label for x axis
        y_label = (df.loc[plot_selection, 'y_data_label'])  # Label for y axis
        # Plot title
        plot_title = plot_selection + '\n(' + scenario_selection + ')' + '\n(' + plot_select_directory_name + ')'

        cmap = cm.get_cmap('tab10')  # Color map

        # Define plot using dataframe formed from spreadsheet
        if str(df.loc[plot_selection, 'y_data_1']) != "nan":
            y_data = (df.loc[plot_selection, 'y_data_1'])  # Column from spreadsheet for y axis
            ax = df1.plot(x=x_data, y=y_data, linestyle=line_style, marker=marker_type,
                          linewidth=line_width, markersize=marker_size, xlabel=x_label, ylabel=y_label,
                          title=plot_title, color=cmap(0))

            data = ['y_data_2', 'y_data_3', 'y_data_4', 'y_data_5', 'y_data_6', 'y_data_7',
                    'y_data_8', 'y_data_9', 'y_data_10']  # Y data columns to search for data
            plot_color = 0
            for y_string in data:
                if str(df.loc[plot_selection, y_string]) != "nan":  # Check for empty cell in spreadsheet
                    plot_color = plot_color + 0.1  # Increment color
                    y_data = (df.loc[plot_selection, y_string])  # Column from spreadsheet for y axis
                    # Add data series to plot
                    df1.plot(x=x_data, y=y_data, ax=ax, linestyle=line_style, marker=marker_type, xlabel=x_label,
                             ylabel=y_label, linewidth=line_width, markersize=marker_size, color=cmap(plot_color))

            ax.grid()  # Show grid
            plt.show()  # Show plot


def is_running(script):
    """
    Checks to see if a Python script is running.

    :param script: Python script to check
    :return: True if script is running - False if script is not running
    """

    for q in psutil.process_iter():
        if q.name().startswith('python'):
            if len(q.cmdline())>1 and script in q.cmdline()[1] and q.pid !=os.getpid():
                print("'{}' Process is already running".format(script))
                return True

    return False

