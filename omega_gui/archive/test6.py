"""OMEGA GUI
   ---------

   This code controls the OMEGA GUI

       ::

        A highlighted literal section may also be added here if needed.

    """
import os
import sys

import multitimer
from PySide2 import QtGui
from PySide2.QtGui import QIcon, QColor, QTextOption
from PySide2.QtWidgets import QWidget, QTableWidgetItem, QMessageBox

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject

from datetime import datetime, date

# Import functions from other files
from omega_gui.omega_gui_functions import *

# Initialize global variables
atimer = 0
configuration_file = ""
input_file_directory = ""
project_directory = ""
gui_loaded = 0
status_bar_message = "Ready"
date_time = ""
scenario = ""


class Form(QObject):
    # Initialize global variables
    # mass_iterations = 1
    # rolling_iterations = 1
    # aero_iterations = 1
    # engine_iterations = 1

    # Import setup values for gui
    # import gui.gui_setup3

    def __init__(self, ui_file, parent=None):
        super(Form, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)

        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # Set the window title
        self.window.setWindowTitle("EPA OMEGA Model")
        # Set the status bar
        # self.window.statusBar().showMessage("Ready")
        # Set the window icon
        self.window.setWindowIcon(QIcon("images/omega2_icon.jpg"))

        # Define gui connections to functions
        self.window.action_new_file.triggered.connect(self.new_file)
        self.window.action_open_configuration_file.triggered.connect(self.open_file)
        self.window.action_select_input_file_directory.triggered.connect(self.open_input_directory)
        self.window.action_select_project_directory.triggered.connect(self.open_project_directory)
        self.window.action_save_configuration_file.triggered.connect(self.save_file)
        # self.window.action_save_file_as.triggered.connect(self.save_file_as)
        self.window.action_exit.triggered.connect(self.exit_gui)
        self.window.select_input_directory_button.clicked.connect(self.open_input_directory)
        self.window.select_project_directory_button.clicked.connect(self.open_project_directory)
        self.window.open_configuration_file_button.clicked.connect(self.open_file)
        self.window.clear_status_monitor_button.clicked.connect(self.clear_status_monitor)
        # Catch close event for clean exit
        app.aboutToQuit.connect(self.closeprogram)
        # Show gui
        self.window.show()

        # Initialize items
        # Select intro tab
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "intro_tab"))
        # Set status monitor window options
        self.window.status_monitor_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.status_monitor_result.setReadOnly(1)
        # Set input file directory window options
        self.window.input_file_directory_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.input_file_directory_1_result.setReadOnly(1)
        # Set configuration file window options
        self.window.configuration_file_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.configuration_file_1_result.setReadOnly(1)
        # Set project directory window options
        self.window.project_directory_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.project_directory_1_result.setReadOnly(1)
        # Prime the status monitor
        self.status_monitor("Ready", "black")
        # Prime the wizard
        temp1 = "Open a valid Configuration File from the File Menu"
        self.wizard(temp1, "green")

        timer.start()
        global gui_loaded
        gui_loaded = 1

    def new_file(self):
        self.clear_status_monitor()
        self.window.input_file_directory_1_result.setPlainText("")
        self.window.configuration_file_1_result.setPlainText("")
        self.window.project_directory_1_result.setPlainText("")

    def open_file(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global configuration_file, scenario
        # self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA2 Configuration Files (*.om2)"
        # Add file dialog title
        file_dialog_title = "Open Configuration File"
        # Call file dialog function
        file_name, file_type, file_dialog_title = file_dialog(file_name, file_type, file_dialog_title)
        # Return if no file selected or dialog cancelled
        if file_name == "":
            return
        # Get name of selected file
        temp1 = os.path.basename(file_name)
        temp1 = os.path.normpath(temp1)
        # Get path of selected file
        temp2 = os.path.dirname(file_name)
        temp2 = os.path.normpath(temp2) + '\\'
        # working_directory = temp2
        configuration_file = temp2 + temp1
        # Place path in gui
        self.window.configuration_file_1_result.setPlainText(configuration_file)
        # Add to status monitor
        temp1 = "Configuration File Loaded [" + configuration_file + "]"
        self.status_monitor(temp1, "black")
        # Create python dictionary 'scenario' from YAML formatted configuration file
        filepath = configuration_file
        scenario = open_file_action(filepath)
        # Get input File Directory from dictionary
        item_value = scenario['input_file_directory']['Input_file_directory']
        # See if selected directory is valid
        if os.path.isdir(item_value):
            # Display in gui if valid
            directory = item_value
            color = "black"
            self.window.input_file_directory_1_result.setTextColor(QColor(color))
            self.window.input_file_directory_1_result.setPlainText(str(directory))
            # Add to status monitor
            temp2 = "Input File Directory Loaded [" + directory + "]"
            self.status_monitor(temp2, color)
        else:
            # Display error message if invalid
            directory = item_value
            color = "red"
            self.window.input_file_directory_1_result.setTextColor(QColor(color))
            self.window.input_file_directory_1_result.setPlainText(str(directory))
            # Add to status monitor
            temp2 = "Input File Directory Invalid [" + directory + "]"
            self.status_monitor(temp2, color)

        # Get output file directory from dictionary
        item_value = scenario['project_directory']['Project_directory']
        # See if selected directory is valid
        if os.path.isdir(item_value):
            # Display in gui if valid
            directory = item_value
            color = "black"
            self.window.project_directory_1_result.setTextColor(QColor(color))
            self.window.project_directory_1_result.setPlainText(str(directory))
            # Add to status monitor
            temp2 = "Project Directory Loaded [" + directory + "]"
            self.status_monitor(temp2, color)
        else:
            # Display error message if invalid
            directory = item_value
            color = "red"
            self.window.project_directory_1_result.setTextColor(QColor(color))
            self.window.project_directory_1_result.setPlainText(str(directory))
            # Add to status monitor
            temp2 = "Project Directory Invalid [" + directory + "]"
            self.status_monitor(temp2, color)
        temp2 = " "
        self.status_monitor(temp2, color)

    def save_file(self):
        """
        Opens a Windows dialog to save an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global configuration_file, scenario
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA2 Configuration Files (*.om2)"
        # Add file dialog title
        file_dialog_title = "Save Configuration File"
        # Call file dialog function
        file_name, file_type, file_dialog_title = file_dialog_save(file_name, file_type, file_dialog_title)
        # Return if no file selected or dialog cancelled
        if file_name == "":
            return
        # Get name of selected file
        temp1 = os.path.basename(file_name)
        temp1 = os.path.normpath(temp1)
        # Get path of selected file
        temp2 = os.path.dirname(file_name)
        temp2 = os.path.normpath(temp2) + '\\'
        # working_directory = temp2
        configuration_file = temp2 + temp1
        # Place path in gui
        self.window.configuration_file_1_result.setPlainText(configuration_file)
        temp1 = "Configuration File Saved [" + configuration_file + "]"
        self.status_monitor(temp1, "black")
        # Save YAML formatted configuration file from the 'scenario' dictionary
        filepath = configuration_file
        save_file_action(filepath, scenario)

        color = "black"
        temp2 = " "
        self.status_monitor(temp2, color)

    def open_input_directory(self):
        """
        Opens a Windows dialog to select an OMEGA2 input directory.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global input_file_directory, scenario
        self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA2 Configuration Files (*.om2)"
        # Add file dialog title
        file_dialog_title = "Select Input File Directory"
        # Call file dialog function
        file_name, file_type, file_dialog_title = directory_dialog(file_name, file_type, file_dialog_title)
        # Return if no file selected or dialog cancelled
        if file_name == "":
            return
        # Get name of selected directory
        temp1 = os.path.basename(file_name)
        temp1 = os.path.normpath(temp1)
        # Get path of selected directory
        temp2 = os.path.dirname(file_name)
        temp2 = os.path.normpath(temp2) + '\\'
        # working_directory = temp2
        input_file_directory = temp2 + temp1
        # Place path in gui
        directory = input_file_directory
        scenario['input_file_directory']['Input_file_directory'] = directory
        color = "black"
        self.window.input_file_directory_1_result.setTextColor(QColor(color))
        self.window.input_file_directory_1_result.setPlainText(str(directory))
        temp2 = "Input File Directory Loaded [" + directory + "]"
        self.status_monitor(temp2, color)

    def open_project_directory(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global project_directory, scenario
        self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA2 Configuration Files (*.om2)"
        # Add file dialog title
        file_dialog_title = "Select Project Directory"
        # Call file dialog function
        file_name, file_type, file_dialog_title = directory_dialog(file_name, file_type, file_dialog_title)
        # Return if no file selected or dialog cancelled
        if file_name == "":
            return
        # Get name of selected directory
        temp1 = os.path.basename(file_name)
        temp1 = os.path.normpath(temp1)
        # Get path of selected directory
        temp2 = os.path.dirname(file_name)
        temp2 = os.path.normpath(temp2) + '\\'
        # working_directory = temp2
        project_directory = temp2 + temp1
        # Place path in gui
        directory = project_directory
        scenario['project_directory']['Project_directory'] = directory
        color = "black"
        self.window.project_directory_1_result.setTextColor(QColor(color))
        self.window.project_directory_1_result.setPlainText(str(directory))
        temp2 = "Project Directory Loaded [" + directory + "]"
        self.status_monitor(temp2, color)

    def select_file_tab(self):
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))

    def status_monitor(self, text, color):
        text = date_time + " " + text
        self.window.status_monitor_result.setTextColor(QColor(color))
        self.window.status_monitor_result.append(text)

    def clear_status_monitor(self):
        self.window.status_monitor_result.setPlainText("")

    def wizard(self, text, color):
        self.window.wizard_result.setTextColor(QColor(color))
        self.window.wizard_result.append(text)

    def clear_wizard(self):
        self.window.wizard_result.setPlainText("")

    def exit_gui(self):
        self.window.close()

    def closeprogram(self):
        print("User Terminating Process")
        # Stop timer
        timer.stop()


def timer3():
    global status_bar_message, gui_loaded, date_time
    # Make sure gui is loaded before accessing it!
    if gui_loaded == 1:
        # Put date, time, and message on status bar
        time = datetime.now()
        t1 = time.strftime("%H:%M:%S")
        today = date.today()
        d1 = today.strftime("%B %d, %Y")
        d2 = today.strftime("%m/%d/%y")
        date_time = d2 + " " + t1
        form.window.statusBar().showMessage(d1 + "  " + t1 + "  " + status_bar_message)



# Run the function 'timer3' in 1 second intervals
timer = multitimer.MultiTimer(interval=1, function=timer3)
# Start timer
# timer.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form('omega_gui_v6.ui')
    # window = MyApp()
    # window.show()
    sys.exit(app.exec_())
