"""
omega_gui_batch.py
==================

This code launches and controls the OMEGA GUI.
The GUI uses QT Designer for the layout and PySide2 as the Python interface.

"""

import os
import sys
import subprocess

import pandas
import psutil

import multitimer
import time

from PySide2.QtGui import QIcon, QColor, QTextOption
from PySide2.QtWidgets import QWidget, QMessageBox
from playsound import playsound

# PyCharm indicates the next statement is not used but is needed for the compile to satisfy PySide2.QtUiTools.
import PySide2.QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject

from datetime import datetime

from plyer import notification

# Import functions from other files
from usepa_omega2_gui.omega_gui_functions import *
from usepa_omega2_gui.omega_gui_stylesheets import *

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep

print('omega_gui_batch.py path = %s' % path)
print('SYS Path = %s' % sys.path)

# Initialize global variables
# Contains the complete path (including filename) to the configuration file
configuration_file = ""
# Contains the directory path to the input file directory
input_batch_file = ""
# Contains the directory path to the project directory
output_batch_directory = ""
# Contains the directory path to the project subdirectory
output_batch_subdirectory = ""
# Output to the status bar every timer cycle
status_bar_message = "Status = Ready"
# Python dictionary containing contents of the configuration file
scenario = ""
plot_select_directory = ""
plot_select_directory_name = ""
# Multiprocessor flag
multiprocessor_mode_selected = False
# Logic elements for program control
configuration_file_valid = False
input_batch_file_valid = False
output_batch_directory_valid = False
# Images for model run button
run_button_image_disabled = path + "usepa_omega2_gui/elements/green_car_1.jpg"
run_button_image_enabled = path + "usepa_omega2_gui/elements/green_car_1.jpg"
epa_button_image = path + "usepa_omega2_gui/elements/epa_seal_large_trim.gif"
green_check_image = path + "usepa_omega2_gui/elements/green_check.png"
red_x_image = path + "usepa_omega2_gui/elements/red_x.png"
# Common spacer between events
event_separator = "----------"
# OMEGA 2 version
omega2_version = ""
# Log file for communication from other processes
# log_file = "comm_file.txt"
log_file_batch = "batch_logfile.txt"
log_file_session_prefix = "o2log_"
log_file_session_suffix = "_ReferencePolicy.txt"
button_click_sound = path + 'usepa_omega2_gui/elements/click.mp3'


class Form(QObject):

    def __init__(self, ui_file, parent=None):
        """
        This function runs once during program start.
        Loads the gui along with defining all connections and element defaults.

        Args:
            N/A

        Returns:
            N/A
        """
        # Load the gui.
        super(Form, self).__init__(parent)
        ui_file = QFile(ui_file)
        ui_file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.window = loader.load(ui_file)
        ui_file.close()

        # Set the window title
        self.window.setWindowTitle("EPA OMEGA 2 Model")
        # Set the status bar
        # self.window.statusBar().showMessage("Ready")
        # Set the window icon
        self.window.setWindowIcon(QIcon(path + "usepa_omega2_gui/elements/omega2_icon.jpg"))

        # Define gui connections to functions
        self.window.action_new_file.triggered.connect(self.new_file)
        self.window.action_open_configuration_file.triggered.connect(self.open_file)
        self.window.action_select_input_batch_file.triggered.connect(self.open_input_batch_file)
        self.window.action_select_output_batch_directory.triggered.connect(self.open_output_batch_directory)
        self.window.action_save_configuration_file.triggered.connect(self.save_file)
        self.window.action_exit.triggered.connect(self.exit_gui)
        self.window.select_input_batch_file_button.clicked.connect(self.open_input_batch_file)
        self.window.select_output_batch_directory_button.clicked.connect(self.open_output_batch_directory)
        self.window.open_configuration_file_button.clicked.connect(self.open_file)
        self.window.save_configuration_file_button.clicked.connect(self.save_file)
        self.window.clear_event_monitor_button.clicked.connect(self.clear_event_monitor)
        self.window.run_model_button.clicked.connect(self.run_model)
        self.window.action_run_model.triggered.connect(self.run_model)
        self.window.action_documentation.triggered.connect(self.launch_documentation)
        self.window.epa_button.clicked.connect(self.launch_epa_website)
        self.window.action_about_omega.triggered.connect(self.launch_about)
        self.window.multiprocessor_checkbox.clicked.connect(self.multiprocessor_mode)
        self.window.open_plot_2.clicked.connect(self.open_plot_2)
        self.window.select_plot_2.clicked.connect(self.select_plot_2)
        self.window.select_plot_3.clicked.connect(self.select_plot_3)
        # Catch close event for clean exit
        app.aboutToQuit.connect(self.closeprogram)
        # Show gui
        self.window.show()

        # Initialize items
        # Select file path tab
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        # Set status monitor window options
        self.window.event_monitor_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.event_monitor_result.setReadOnly(1)
        # Set input file directory window options
        self.window.input_batch_file_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.input_batch_file_1_result.setReadOnly(1)
        # Set configuration file window options
        self.window.configuration_file_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.configuration_file_1_result.setReadOnly(1)
        # Set project directory window options
        self.window.output_batch_directory_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.output_batch_directory_1_result.setReadOnly(1)
        # Set wizard window options
        # self.window.wizard_result.setReadOnly(1)
        # Disable run model button
        # self.enable_run_button(False)

        # Load stylesheet for tab control
        stylesheet = ""
        stylesheet = tab_stylesheet(stylesheet)
        # stylesheet = test1(stylesheet)
        self.window.tab_select.setStyleSheet(stylesheet)

        # Load stylesheet for background
        stylesheet = ""
        stylesheet = background_stylesheet(stylesheet)
        self.window.background_widget.setStyleSheet(stylesheet)

        # Load stylesheet for buttons
        stylesheet = ""
        stylesheet = button_stylesheet(stylesheet)
        self.window.clear_event_monitor_button.setStyleSheet(stylesheet)
        self.window.open_configuration_file_button.setStyleSheet(stylesheet)
        self.window.save_configuration_file_button.setStyleSheet(stylesheet)
        self.window.select_input_batch_file_button.setStyleSheet(stylesheet)
        self.window.select_output_batch_directory_button.setStyleSheet(stylesheet)
        self.window.run_model_button.setStyleSheet(stylesheet)
        self.window.open_plot_2.setStyleSheet(stylesheet)
        self.window.select_plot_2.setStyleSheet(stylesheet)
        self.window.select_plot_3.setStyleSheet(stylesheet)

        # Load stylesheet for logo buttons
        stylesheet = ""
        stylesheet = logo_button_stylesheet(stylesheet)
        self.window.epa_button.setStyleSheet(stylesheet)

        # Load stylesheet for labels
        stylesheet = ""
        stylesheet = label_stylesheet(stylesheet)
        self.window.configuration_file_1_label.setStyleSheet(stylesheet)
        self.window.input_batch_file_1_label.setStyleSheet(stylesheet)
        self.window.output_batch_directory_1_label.setStyleSheet(stylesheet)
        self.window.project_description_1_label.setStyleSheet(stylesheet)
        self.window.main_title_1_label.setStyleSheet(stylesheet)
        self.window.event_monitor_label.setStyleSheet(stylesheet)
        self.window.model_status_label.setStyleSheet(stylesheet)
        self.window.available_plots_1_label_2.setStyleSheet(stylesheet)
        self.window.available_plots_1_label_3.setStyleSheet(stylesheet)
        self.window.intro_label.setStyleSheet(stylesheet)

        # Load stylesheet for checkboxes
        stylesheet = ""
        stylesheet = checkbox_stylesheet(stylesheet)
        self.window.multiprocessor_checkbox.setStyleSheet(stylesheet)

        # Timer start
        timer.start()
        # Setup the gui
        self.initialize_gui()

    def new_file(self):
        """
        Clears the gui and the input dictionary.

        Args:
            N/A

        Returns:
            N/A
         """
        self.clear_event_monitor()
        self.window.input_batch_file_1_result.setPlainText("")
        self.window.configuration_file_1_result.setPlainText("")
        self.window.output_batch_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.initialize_gui()
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        self.enable_run_button(False)

    def open_file(self):
        """
        Opens a Windows dialog to select an OMEGA 2 (.om2) configuration file.

        When complete:
            Global variable "scenario_file" = user selected configuration file name.

        Args:
            N/A

        Returns:
            N/A
        """
        # playsound(button_click_sound)
        global configuration_file, scenario, configuration_file_valid, input_batch_file_valid
        global output_batch_directory_valid, input_batch_file, output_batch_directory
        # self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA 2 Configuration Files (*.om2)"
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
        color = "green"
        self.window.configuration_file_1_result.setTextColor(QColor(color))
        self.window.configuration_file_1_result.setPlainText(os.path.basename(configuration_file))
        # Create python dictionary 'scenario' from YAML formatted configuration file
        filepath = configuration_file
        scenario = open_file_action(filepath)
        # Get input File Directory from dictionary
        item_value = ""
        # Make sure the dictionary entry exists
        try:
            item_value = scenario['input_batch_file']['input_batch_file']
        # Add entry to dictionary if missing from file
        except (KeyError, TypeError):
            try:
                # Try to add replacement dictionary element
                scenario.update({'input_batch_file': {'input_batch_file': 'null'}})
            # If unable to add element, file is corrupt so clear everything and start over
            except AttributeError:
                self.initialize_gui()
                self.clear_entries()
                message_title = "OMEGA 2 Warning Message"
                message = "Configuration File Corrupt:\n    [" + configuration_file + "]"
                self.showbox(message_title, message)
                temp2 = message
                self.event_monitor(temp2, 'red', 'dt')
                self.event_monitor(event_separator, 'red', "")
                return
        configuration_file_valid = True
        # See if selected directory is valid
        if os.path.isfile(item_value):
            # Display in gui if valid
            input_batch_file = item_value
            color = "green"
            self.window.input_batch_file_1_result.setTextColor(QColor(color))
            self.window.input_batch_file_1_result.setPlainText(os.path.basename(input_batch_file))
            input_batch_file_valid = True
        else:
            # Display error message if invalid
            input_batch_file = item_value
            color = "red"
            self.window.input_batch_file_1_result.setTextColor(QColor(color))
            self.window.input_batch_file_1_result.setPlainText(os.path.basename(input_batch_file))
            input_batch_file_valid = False
            configuration_file_valid = False

        # Get output file directory from dictionary
        item_value = ""
        # Make sure the dictionary entry exists
        try:
            item_value = scenario['output_batch_directory']['output_batch_directory']
        # Add entry to dictionary if missing from file
        except (KeyError, TypeError):
            scenario.update({'output_batch_directory': {'output_batch_directory': 'null'}})
        # See if selected directory is valid
        if os.path.isdir(item_value):
            # Display in gui if valid
            output_batch_directory = item_value
            color = "green"
            self.window.output_batch_directory_1_result.setTextColor(QColor(color))
            # path = pathlib.PurePath(output_batch_directory)
            self.window.output_batch_directory_1_result.setPlainText(os.path.basename(output_batch_directory))
            output_batch_directory_valid = True
        else:
            # Display error message if invalid
            output_batch_directory = item_value
            color = "red"
            self.window.output_batch_directory_1_result.setTextColor(QColor(color))
            self.window.output_batch_directory_1_result.setPlainText(os.path.basename(output_batch_directory))
            output_batch_directory_valid = False
            configuration_file_valid = False

        # Display project description from configuration file
        try:
            item_value = scenario['project_description']['Project_description']
            # Trap, add element, and display if project description element missing from file
        except (KeyError, TypeError):
            scenario.update({'project_description': {'Project_description': ''}})
            item_value = scenario['project_description']['Project_description']

        if item_value == "":
            temp2 = "Warning - No project description in configuration file"
            self.event_monitor(temp2, 'orange', 'dt')

        self.window.project_description.setPlainText(str(item_value))
        self.wizard_logic()
        self.event_monitor(event_separator, "black", "")
        self.window.configuration_file_1_result.setToolTip(configuration_file)
        self.window.input_batch_file_1_result.setToolTip(input_batch_file)
        self.window.output_batch_directory_1_result.setToolTip(output_batch_directory)

    def save_file(self):
        """
        Opens a Windows dialog to save an OMEGA 2 (.om2) configuration file.

        When complete:
            Global variable "scenario_file" = user selected configuration file name.
            Global variable "working_directory" = User selected path to configuration file.

        Args:
            N/A

        Returns:
            N/A
        """
        global configuration_file, scenario, input_batch_file, output_batch_directory
        global configuration_file_valid
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA 2 Configuration Files (*.om2)"
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
        color = "green"
        self.window.configuration_file_1_result.setTextColor(QColor(color))
        self.window.configuration_file_1_result.setPlainText(os.path.basename(configuration_file))
        temp1 = "Configuration File Saved:\n    [" + configuration_file + "]"
        self.event_monitor(temp1, "green", 'dt')
        # Save text from Project Description window to dictionary
        temp1 = self.window.project_description.toPlainText()
        scenario['project_description']['Project_description'] = temp1
        # Save YAML formatted configuration file
        filepath = configuration_file
        save_file_action(filepath, scenario)

        configuration_file_valid = True
        self.wizard_logic()
        color = "black"
        self.event_monitor(event_separator, color, '')

    def open_input_batch_file(self):
        """
        Opens a Windows dialog to select an OMEGA 2 input directory.

        When complete:
            Global variable "input_batch_file" = user selected input batch file.

        Args:
            N/A

        Returns:
            N/A
        """
        global input_batch_file, scenario, configuration_file
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
        # self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA 2 Batch Files (*.xlsx)"
        # Add file dialog title
        file_dialog_title = "Select Input Batch File"
        # Call file dialog function
        file_name, file_type, file_dialog_title = file_dialog(file_name, file_type, file_dialog_title)
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
        input_batch_file = temp2 + temp1
        # Update dictionary entry
        scenario['input_batch_file']['input_batch_file'] = input_batch_file
        # Place path in gui
        directory = input_batch_file
        # temp3 = '...' + directory[-40:]
        color = "green"
        self.window.input_batch_file_1_result.setTextColor(QColor(color))
        self.window.input_batch_file_1_result.setPlainText(os.path.basename(input_batch_file))
        temp2 = "Input Batch File Loaded:\n    [" + directory + "]"
        self.event_monitor(temp2, color, 'dt')
        # Configuration has changed so blank out configuration file
        self.window.configuration_file_1_result.setPlainText("")
        configuration_file = ""
        configuration_file_valid = False
        input_batch_file_valid = True
        # User instructions to wizard
        self.wizard_logic()
        color = "black"
        self.event_monitor(event_separator, color, '')

    def open_output_batch_directory(self):
        """
        Opens a Windows dialog to select an OMEGA 2 (.om2) Scenario file.

        When complete:
            Global variable "output_batch_directory" = user selected output batch directory.

        Args:
            N/A

        Returns:
            N/A
        """
        global output_batch_directory, scenario, configuration_file
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
        # self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA 2 Configuration Files (*.om2)"
        # Add file dialog title
        file_dialog_title = "Select Output Batch Directory"
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
        output_batch_directory = temp2 + temp1
        # Update dictionary entry
        scenario['output_batch_directory']['output_batch_directory'] = output_batch_directory
        # Place path in gui
        directory = output_batch_directory
        color = "green"
        self.window.output_batch_directory_1_result.setTextColor(QColor(color))
        self.window.output_batch_directory_1_result.setPlainText(os.path.basename(output_batch_directory))
        temp2 = "Project Directory Loaded:\n    [" + directory + "]"
        self.event_monitor(temp2, color, 'dt')
        # Configuration has changed so blank out configuration file
        self.window.configuration_file_1_result.setPlainText("")
        configuration_file = ""
        configuration_file_valid = False
        output_batch_directory_valid = True
        # User instructions to wizard
        self.wizard_logic()
        color = "black"
        self.event_monitor(event_separator, color, '')

    def event_monitor(self, text, color, timecode):
        """
        Appends text to event monitor window.

        Args:
            text: Text to append to event monitor window
            color: Color to display text
            timecode: 'dt' will display current date and time before text

        Returns:
            N/A
        """
        if timecode == 'dt':
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y %H:%M:%S")
            text = date_time + "  " + text
        self.window.event_monitor_result.setTextColor(QColor(color))
        self.window.event_monitor_result.append(text)

    def clear_event_monitor(self):
        """
        Clears the event monitor textbox.

        Args:
            N/A

        Returns:
            N/A
        """
        self.window.event_monitor_result.setPlainText("")

    # def wizard(self, text, color):
    # self.window.wizard_result.setTextColor(QColor(color))
    # self.window.wizard_result.append(text)

    # def clear_wizard(self):
    # self.window.wizard_result.setPlainText("")

    def launch_documentation(self):
        """
        Opens the OMEGA documentation website in browser.

        Args:
            N/A

        Returns:
            N/A
        """
        os.system("start \"\" https://omega2.readthedocs.io/en/latest/index.html")

    def launch_epa_website(self):
        """
        Opens the EPA website in browser.

        Args:
            N/A

        Returns:
            N/A
        """
        os.system("start \"\" https://epa.gov")

    def launch_about(self):
        """
        Displays the OMEGA version in a popup box.

        Args:
            N/A

        Returns:
            N/A
        """
        global omega2_version, button_click_sound
        message_title = "About OMEGA"
        message = "OMEGA Code Version = " + omega2_version
        self.showbox(message_title, message)

    def wizard_logic(self):
        """
        Handles the gui logic to enable and disable various controls and launch event monitor messages.

        Args:
            N/A

        Returns:
            N/A
        """
        if configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:

            temp2 = "Configuration File Loaded:\n    [" + configuration_file + "]"
            self.event_monitor(temp2, 'green', 'dt')

            temp1 = "Configuration Loaded.\n"
            temp1 = temp1 + "Model Run Enabled.\n"
            temp1 = temp1 + "Punch It Chewie!"
            self.event_monitor(temp1, 'black', '')

            self.window.save_configuration_file_button.setEnabled(1)
            self.window.configuration_file_check_button.setIcon(QIcon(green_check_image))
            self.window.input_batch_file_check_button.setIcon(QIcon(green_check_image))
            self.window.output_batch_directory_check_button.setIcon(QIcon(green_check_image))

        elif not configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:
            # self.clear_wizard()
            temp1 = "Configuration has changed.  Save Configuration File to continue."
            self.event_monitor(temp1, 'black', '')
            self.window.save_configuration_file_button.setEnabled(1)
            self.window.configuration_file_check_button.setIcon(QIcon(red_x_image))
            self.window.input_batch_file_check_button.setIcon(QIcon(green_check_image))
            self.window.output_batch_directory_check_button.setIcon(QIcon(green_check_image))
        elif not configuration_file_valid and (not input_batch_file_valid or not output_batch_directory_valid):
            # self.clear_wizard()
            temp1 = "Elements in the Configuration are invalid:"
            self.event_monitor(temp1, 'black', '')
            self.window.save_configuration_file_button.setEnabled(0)
            self.window.configuration_file_check_button.setIcon(QIcon(red_x_image))
            self.window.input_batch_file_check_button.setIcon(QIcon(green_check_image))
            self.window.output_batch_directory_check_button.setIcon(QIcon(green_check_image))
            if not input_batch_file_valid:
                temp2 = "Input Batch File Invalid:\n    [" + input_batch_file + "]"
                self.event_monitor(temp2, 'red', 'dt')
                self.window.input_batch_file_check_button.setIcon(QIcon(red_x_image))
            if not output_batch_directory_valid:
                temp2 = "Output Batch Directory Invalid:\n    [" + output_batch_directory + "]"
                self.event_monitor(temp2, 'red', 'dt')
                self.window.output_batch_directory_check_button.setIcon(QIcon(red_x_image))
        if configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:
            self.enable_run_button(True)
            self.window.configuration_file_check_button.setIcon(QIcon(green_check_image))
            self.window.input_batch_file_check_button.setIcon(QIcon(green_check_image))
            self.window.output_batch_directory_check_button.setIcon(QIcon(green_check_image))
        else:
            self.enable_run_button(False)

    def initialize_gui(self):
        """
        Initialize various gui program functions.

        Args:
            N/A

        Returns:
            N/A
        """
        global scenario, status_bar_message, omega2_version
        global configuration_file, input_batch_file, output_batch_directory, output_batch_subdirectory
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
        configuration_file = ""
        input_batch_file = ""
        output_batch_directory = ""
        output_batch_subdirectory = ""
        wizard_init = "Open a valid Configuration File or:\n" \
                      "    Select New Input Batch File," \
                      " Select New Output Batch Directory," \
                      " and Save Configuration File\n" \
                      "----------"

        # Get OMEGA 2 version #.
        from usepa_omega2 import code_version as omega2_version

        # Prime the status monitor
        color = "black"
        message = "OMEGA Version " + omega2_version + " Ready"
        self.event_monitor(message, color, 'dt')
        self.event_monitor(event_separator, color, '')
        # Prime the wizard
        # self.clear_wizard()
        self.event_monitor(wizard_init, 'black', '')
        # Create 'scenario' dictionary for later reference
        scenario = {'input_batch_file': {'input_batch_file': 'null'},
                    'output_batch_directory': {'output_batch_directory': 'null'},
                    'project_description': {'Project_description': 'null'}}
        configuration_file_valid = False
        input_batch_file_valid = False
        output_batch_directory_valid = False
        status_bar_message = "Status = Ready"
        self.enable_run_button(False)
        self.window.save_configuration_file_button.setEnabled(0)
        self.window.epa_button.setIcon(QIcon(epa_button_image))
        self.window.configuration_file_check_button.setIcon(QIcon(red_x_image))
        self.window.input_batch_file_check_button.setIcon(QIcon(red_x_image))
        self.window.output_batch_directory_check_button.setIcon(QIcon(red_x_image))
        self.window.setWindowTitle("EPA OMEGA Model     Version: " + omega2_version)

        self.window.model_status_label.setText("Model Idle")
        self.window.select_plot_3.setEnabled(0)

    def clear_entries(self):
        """
        Clears all fields in the gui.

        Args:
            N/A

        Returns:
            N/A
        """
        self.window.configuration_file_1_result.setPlainText("")
        self.window.input_batch_file_1_result.setPlainText("")
        self.window.output_batch_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.clear_event_monitor()

    def run_model(self):
        """
        Calls the OMEGA 2 main program with selected options.
        Options for single processor mode:
        --batch_file [user selected batch file] --bundle_path [user selected output directory]
        --timestamp [current date and time]

        Options for multiprocessor mode:
        --batch_file [user selected batch file] --bundle_path [user selected output directory]
        --dispy --local --dispy_exclusive --dispy_debug
        --timestamp [current date and time]

        Args:
            N/A

        Returns:
            N/A
        """
        elapsed_start = datetime.now()
        # model_sound_start = 'gui/elements/click.mp3'
        # model_sound_stop = 'gui/elements/model_stop.mp3'
        global status_bar_message
        global multiprocessor_mode_selected
        global output_batch_subdirectory
        # status_bar()
        self.window.repaint()

        # This call works but gui freezes until new process ends
        # os.system("python usepa_omega2/__main__.py")
        # Open batch excel spreadsheet
        excel_data_df = pandas.read_excel(input_batch_file, index_col=0, sheet_name='Sessions')
        # Create timestamp for batch filename
        batch_time_stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        # Create path to batch log file
        output_batch_subdirectory = output_batch_directory + "/" + batch_time_stamp + '_' + \
            excel_data_df.loc['Batch Name', 'Value']
        # Create path to session log file
        output_session_subdirectory = output_batch_subdirectory + "/ReferencePolicy/output"
        # print('*****', output_session_subdirectory)

        # Delete contents of comm_file.txt used to communicate with other processes
        # and place the first line 'Start Model Run'
        # path = output_batch_subdirectory
        # os.mkdir(path)
        # file1 = open(output_batch_subdirectory + "/" + log_file_batch, "a")  # append mode
        # file1.write("Today \n")
        # file1.close()
        # file = open(output_batch_subdirectory + "/" + log_file_batch, "r+")
        # file.truncate(0)
        # file.close()
        # file1 = open(output_batch_subdirectory + "/" + log_file_batch, "a")  # append mode
        # file1.write("Start Model Run \n")
        # file1.close()

        # Play a model start sound
        # sound1 = subprocess.Popen(['python', os.path.realpath('gui/sound_gui.py'), model_sound_start], close_fds=True)

        # This call works and runs a completely separate process
        # omega2 = subprocess.Popen(['python', os.path.realpath('usepa_omega2/__main__.py'), 'Test333'], close_fds=True)
        # omega2.terminate()

        # Prepare command line options for OMEGA 2 batch process
        # batch_time_stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        a = '--batch_file ' + '"' + input_batch_file + '"'
        b = ' --bundle_path ' + '"' + output_batch_directory + '"'

        if multiprocessor_mode_selected:
            # Add command line options for multiprocessor mode
            c = ' --dispy --local --dispy_exclusive --dispy_debug'
        else:
            # No multiprocessor
            c = ''
        # Add timestamp option so program can track comm_file
        d = ' --timestamp ' + batch_time_stamp

        # Combine command line options
        x = a + b + c + d

        # Disable selected gui functions during model run
        self.enable_gui_run_functions(0)
        # Indicate model start to status bar
        self.event_monitor("Start Model Run", "black", 'dt')
        # Call OMEGA 2 batch as a subprocess with command line options from above
        status_bar_message = "Status = Model Running ..."

        # # Send notification to Windows
        # notification.notify(
        #     title="OMEGA Notification",
        #     message="Model Run Started\n" + "Input File =\n" + "  " + os.path.basename(input_batch_file),
        #     # app_icon=path + "usepa_omega2_gui/elements/omega2_icon.ico",
        #     timeout=5
        # )

        print('sys.executable = %s' % sys.executable)
        print('Popen(%s)' % ['python', os.path.realpath(path + 'usepa_omega2_gui/run_omega_batch_gui.py'), x])

        omega_batch = subprocess.Popen(['python', os.path.realpath(path + 'usepa_omega2_gui/run_omega_batch_gui.py'),
                                         x], close_fds=True)

        # While the subprocess is running, output communication from the batch process to the event monitor
        # First find the log files
        log_file_array = []  # Clear log file array
        log_counter_array = []  # Clear counter array
        log_ident_array = []  # Clear log identifier array
        file_timer = 0  # Counter for file search timer

        # self.load_plots_2()
        # Keep looking for communication from other processes through the log files
        while omega_batch.poll() is None:
            # This command allows the GUI to catch up and repaint itself
            app.processEvents()
            # Keep the overhead low and only update the event file at 10 hz
            time.sleep(0.1)
            # Update model run time
            elapsed_end = datetime.now()
            elapsed_time = elapsed_end - elapsed_start
            elapsed_time = sec_to_hours(elapsed_time.seconds)
            # elapsed_time = str(elapsed_time)
            # elapsed_time = "Model Running\n" + elapsed_time[:-7]
            elapsed_time = "Model Running\n" + elapsed_time[:-4]
            self.window.model_status_label.setText(elapsed_time)

            # Look for new log files
            file_timer = file_timer + 1
            if file_timer > 20:  # Look for new files every 2 seconds
                file_timer = 0
                directory = output_batch_subdirectory + "/"  # Define output directory to search
                for root, dirs, files in os.walk(directory):  # Search includes subdirectories
                    for file in files:  # Begin search
                        if file.endswith('.txt'):  # Process if .txt file is found
                            fullpath = os.path.join(root, file)  # Generate complete path of file
                            # log_file_array.append(fullpath)
                            # log_counter_array.append(0)
                            try:
                                log_file_array.index(fullpath)  # See if found .txt file already in log file
                            except ValueError:
                                log_file_array.append(fullpath)  # Append filename to log file array
                                log_counter_array.append(0)  # Add another log counter for new file
                                f = open(fullpath)  # Get identifier for status output
                                lines = f.readlines()  # Read file
                                f.close()  # Close file
                                j = lines[0]  # Get first line
                                # h = j.find('session')  # Look for 'session'
                                if j.find('session') > -1:  # See if 'session' found
                                    l = j.find('session') + 8
                                    i = j.find(' ', l)  # Find the end of the next word after 'session'
                                    k = j[l:i]  # Save the next word
                                elif j.find('batch') > -1:  # See if 'batch' found:
                                    k = 'Batch'  # Save the word for output
                                else:
                                    k = ""  # Not recognized
                                log_ident_array.append(k)

            # Get number of lines in the log files if they exist
            for log_loop in range(0, len(log_file_array)):
                if os.path.isfile(log_file_array[log_loop]):
                    log_lines = sum(1 for line in open(log_file_array[log_loop]))
                    log_status = 1
                else:
                    log_lines = 0
                    log_status = 0

                # Read and output all new lines from log files
                while log_counter_array[log_loop] < log_lines and log_status == 1:
                    f = open(log_file_array[log_loop])
                    lines = f.readlines()
                    f.close()

                    # j = lines[0]  # Get first line
                    # h = j.find('session')
                    # l = h + 8
                    # i = j.find(' ', 21)
                    # k = j[l:i]
                    # print('&&&', j, h, i, k)

                    g = lines[log_counter_array[log_loop]]
                    g = g.rstrip("\n")
                    g = '[' + log_ident_array[log_loop] + '] ' + g
                    # Select output color
                    color = status_output_color(g)
                    # Output to event monitor
                    self.event_monitor(g, color, 'dt')
                    # Increment total number of read lines in log file counter
                    log_counter_array[log_loop] = log_counter_array[log_loop] + 1

        # Play a model end sound
        # sound2 = subprocess.Popen(['python', os.path.realpath('gui/sound_gui.py'), model_sound_stop], close_fds=True)
        # sound1.terminate()

        # process has ended - update items in GUI
        # Send elapsed time to event monitor.
        elapsed_end = datetime.now()
        elapsed_time = elapsed_end - elapsed_start
        elapsed_time = sec_to_hours(elapsed_time.seconds)
        self.event_monitor("Model Run Time = " + str(elapsed_time), "black", "dt")

        # Update event monitor and status bar for end of model run
        self.event_monitor("End Model Run", "black", 'dt')
        self.event_monitor(event_separator, "black", '')
        status_bar_message = "Status = Ready"

        # elapsed_end = datetime.now()
        elapsed_time1 = elapsed_end - elapsed_start
        elapsed_time1 = str(elapsed_time)
        elapsed_time1 = "Model Run Completed\n" + elapsed_time1[:-4]
        self.window.model_status_label.setText(elapsed_time1)
        # self.window.model_status_label.setText("Model Run Completed")
        # Enable selected gui functions disabled during model run
        self.enable_gui_run_functions(1)
        # self.load_plots_2()

        # Send Notification to Windows
        # notification.notify(
        #     title="OMEGA Notification",
        #     message="Model Run Completed\n" + str(elapsed_time) + "\n" + "Output Directory =\n" +
        #             "  " + os.path.basename(output_batch_directory),
        #     # app_icon= path + "usepa_omega2_gui/elements/omega2_icon.ico",
        #     timeout=5
        # )

    def showbox(self, message_title, message):
        """
        Displays a popup message box.

        Args:
            message_title: Title for message box
            message: Text for message box.

        Returns:
            N/A
        """
        msg = QMessageBox()
        msg.setWindowTitle(message_title)
        msg.setText(message)
        msg.exec()

    def exit_gui(self):
        """
        Runs when the user requests gui close.

        Args:
            N/A

        Returns:
            N/A
        """
        # Close the gui.
        self.window.close()

    def closeprogram(self):
        """
        Runs after the user closes the gui.
        Close any processes that are running outside the gui.

        Args:
            N/A

        Returns:
            N/A
        """
        # Message to the terminal.
        print("User Terminating Process")
        # Stop timer process
        timer.stop()

    def multiprocessor_mode(self):
        """
        Checks the status of the Multiprocessor checkbox

        Args:
            N/A

        Returns:
            N/A
        """
        global multiprocessor_mode_selected
        if self.window.multiprocessor_checkbox.isChecked():
            self.event_monitor("Multi Processor Mode Selected", "black", 'dt')
            multiprocessor_mode_selected = True
        else:
            self.event_monitor("Single Processor Mode Selected", "black", 'dt')
            multiprocessor_mode_selected = False

    def enable_run_button(self, enable):
        """
        Enables and disables the run model button.

        Args:
            enable: Boolean to enable or disable run model button and display appropriate button image

        Returns:
            N/A
        """
        if enable:
            self.window.run_model_button.setIcon(QIcon(run_button_image_enabled))
            self.window.run_model_button.setEnabled(1)
            self.window.action_run_model.setEnabled(1)
            self.window.model_status_label.setText("Model Ready")
        else:
            self.window.run_model_button.setIcon(QIcon(run_button_image_disabled))
            self.window.run_model_button.setEnabled(0)
            self.window.action_run_model.setEnabled(0)
            self.window.model_status_label.setText("Model Idle")

    def enable_gui_run_functions(self, enable):
        """
        Enables and disables various gui functions during model run.

        Args:
            enable: Boolean to enable or disable selected gui functions during model run

        Returns:
            N/A
        """
        self.window.open_configuration_file_button.setEnabled(enable)
        self.window.save_configuration_file_button.setEnabled(enable)
        self.window.select_input_batch_file_button.setEnabled(enable)
        self.window.select_output_batch_directory_button.setEnabled(enable)
        self.window.action_new_file.setEnabled(enable)
        self.window.action_open_configuration_file.setEnabled(enable)
        self.window.action_save_configuration_file.setEnabled(enable)
        self.window.action_select_input_batch_file.setEnabled(enable)
        self.window.action_select_output_batch_directory.setEnabled(enable)
        self.window.action_run_model.setEnabled(enable)
        self.window.run_model_button.setEnabled(enable)
        self.window.multiprocessor_checkbox.setEnabled(enable)
        self.window.select_plot_3.setEnabled(enable)

    def select_plot_2(self):
        """
        Opens a Windows dialog to select a previous model run for plotting.

        Args:
            N/A

        Returns:
            N/A
        """
        global plot_select_directory
        global plot_select_directory_name
        file_name = ""
        file_type = ""
        file_dialog_title = 'Select Run Directory'
        file_name, file_type, file_dialog_title = directory_dialog(file_name, file_type, file_dialog_title)
        if file_name == "":
            self.window.list_graphs_1.clear()
            self.window.list_graphs_2.clear()
            return()

        plot_select_directory_path = file_name
        plot_select_directory_name = os.path.basename(os.path.normpath(file_name))
        # print(plot_select_directory_name)

        self.window.list_graphs_1.clear()
        input_file = path + 'usepa_omega2_gui/elements/plot_definition.xlsx'
        plot_data_df = pandas.read_excel(input_file)
        # df = pandas.read_csv('usepa_omega2_gui/elements/summary_results.csv')
        for index, row in plot_data_df.iterrows():
            # print(row['plot_name'])
            self.window.list_graphs_1.addItem(row['plot_name'])

        self.window.list_graphs_2.clear()
        # input_file = 'usepa_omega2_gui/elements/summary_results.csv'
        input_file = plot_select_directory_path + '/' + plot_select_directory_name + '_summary_results.csv'
        if not os.path.exists(input_file):
            self.window.list_graphs_1.clear()
            self.window.list_graphs_2.clear()
            return()
        plot_data_df1 = pandas.read_csv(input_file)
        plot_data_df1.drop_duplicates(subset=['session_name'], inplace=True)
        for index, row in plot_data_df1.iterrows():
            # print(row['plot_name'])
            self.window.list_graphs_2.addItem(row['session_name'])

    def select_plot_3(self):
        """
        Opens the current model run for plotting.

        Args:
            N/A

        Returns:
            N/A
        """
        global plot_select_directory_name
        self.window.list_graphs_1.clear()
        input_file = path + 'usepa_omega2_gui/elements/plot_definition.xlsx'
        plot_data_df = pandas.read_excel(input_file)
        # df = pandas.read_csv('usepa_omega2_gui/elements/summary_results.csv')
        for index, row in plot_data_df.iterrows():
            # print(row['plot_name'])
            self.window.list_graphs_1.addItem(row['plot_name'])

        self.window.list_graphs_2.clear()
        plot_select_directory_path = output_batch_subdirectory
        plot_select_directory_name = os.path.basename(os.path.normpath(output_batch_subdirectory))
        input_file = plot_select_directory_path + '/' + plot_select_directory_name + '_summary_results.csv'
        if not os.path.exists(input_file):
            self.window.list_graphs_1.clear()
            self.window.list_graphs_2.clear()
            return()
        # print(input_file)
        # input_file = 'usepa_omega2_gui/elements/summary_results.csv'
        plot_data_df1 = pandas.read_csv(input_file)
        plot_data_df1.drop_duplicates(subset=['session_name'], inplace=True)
        for index, row in plot_data_df1.iterrows():
            # print(row['plot_name'])
            self.window.list_graphs_2.addItem(row['session_name'])

    def open_plot_2(self):
        """
        Plots the selected data.

        Args:
            N/A

        Returns:
            N/A
        """
        global plot_select_directory_name
        # See if valid selections have been made
        if self.window.list_graphs_1.currentItem() is not None and self.window.list_graphs_2.currentItem() is not None:
            # Get plot selections
            a = self.window.list_graphs_1.selectedIndexes()[0]
            b = self.window.list_graphs_2.selectedIndexes()[0]
            # Send plot selections to plot function
            test_plot_2(a.data(), b.data(), plot_select_directory_name)


def status_bar():
    """
    Called once per second to display the date, time, and global variable "status_bar_message" in the status bar.

    Args:
        N/A

    Returns:
        N/A
    """
    global status_bar_message
    # Put date, time, and message on status bar
    now = datetime.now()
    date_time = now.strftime("%B %d, %Y  %H:%M:%S")
    # Get CPU usage
    cpu = psutil.cpu_percent()
    cpu = int(cpu / 5)
    cpu = "{" + "|" * cpu + "                      "
    cpu = "CPU Load=" + cpu[0:21] + "}"
    # Get memory used
    mem = psutil.virtual_memory().percent
    mem = int(mem/5)
    mem = "{" + "|" * mem + "                      "
    mem = "Memory Load=" + mem[0:21] + "}"
    try:
        form.window.statusBar().showMessage(date_time + "  " + status_bar_message + "     " + cpu + "   " + mem)
    except NameError:
        return


# Run the function 'status_bar' in 1 second intervals
timer = multitimer.MultiTimer(interval=1, function=status_bar)

def run_gui():
    global app
    global form

    app = QApplication(sys.argv)
    # Load the gui
    uifilename = path + 'usepa_omega2_gui/elements/omega_gui_v22.ui'
    print('uifilename = %s' % uifilename)
    form = Form(uifilename)
    sys.exit(app.exec_())


if __name__ == '__main__':
    run_gui()
