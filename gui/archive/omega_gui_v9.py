"""OMEGA GUI
   ---------

   This code controls the OMEGA2 GUI

       ::

        A highlighted literal section may also be added here if needed.

    """
import os
import sys
from distutils.dir_util import copy_tree

import multitimer

from PySide2.QtGui import QIcon, QColor, QTextOption, QPalette
from PySide2.QtWidgets import QWidget, QMessageBox

# PyCharm indicates the next statement is not used but is needed for the compile to satisfy PySide2.QtUiTools.
import PySide2.QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject

from datetime import datetime, date

# Import functions from other files
from omega_gui_functions import *

# Initialize global variables
# Contains the complete path (including filename) to the configuration file
configuration_file = ""
# Contains the directory path to the input file directory
input_file_directory = ""
# Contains the directory path to the project directory
project_directory = ""
# Output to the status bar every timer cycle
status_bar_message = "Ready"
# Python dictionary containing contents of the configuration file
scenario = ""
# Logic elements for program control
configuration_file_valid = False
input_directory_valid = False
project_directory_valid = False
run_button_image_disabled = ""
run_button_image_enabled = "elements/green_car_1"
event_separator = "----------"


class Form(QObject):

    def __init__(self, ui_file, parent=None):
        """
        This function runs once upon program start.
        Loads the gui and defines all connections and element defaults.
        """
        # Load the gui.
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
        self.window.setWindowIcon(QIcon("elements/omega2_icon.jpg"))

        # Define gui connections to functions
        self.window.action_new_file.triggered.connect(self.new_file)
        self.window.action_open_configuration_file.triggered.connect(self.open_file)
        self.window.action_select_input_file_directory.triggered.connect(self.open_input_directory)
        self.window.action_select_project_directory.triggered.connect(self.open_project_directory)
        self.window.action_save_configuration_file.triggered.connect(self.save_file)
        self.window.action_exit.triggered.connect(self.exit_gui)
        self.window.select_input_directory_button.clicked.connect(self.open_input_directory)
        self.window.select_project_directory_button.clicked.connect(self.open_project_directory)
        self.window.open_configuration_file_button.clicked.connect(self.open_file)
        self.window.save_configuration_file_button.clicked.connect(self.save_file)
        self.window.clear_event_monitor_button.clicked.connect(self.clear_event_monitor)
        self.window.run_model_button.clicked.connect(self.run_model)
        # Catch close event for clean exit
        app.aboutToQuit.connect(self.closeprogram)
        # Show gui
        self.window.show()

        # Initialize items
        # Select file path tab
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        # Set status monitor window options
        self.window.event_monitor_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.event_monitor_result.setReadOnly(1)
        # Set input file directory window options
        self.window.input_file_directory_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.input_file_directory_1_result.setReadOnly(1)
        # Set configuration file window options
        self.window.configuration_file_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.configuration_file_1_result.setReadOnly(1)
        # Set project directory window options
        self.window.project_directory_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.project_directory_1_result.setReadOnly(1)
        # Set wizard window options
        # self.window.wizard_result.setReadOnly(1)
        # Disable run model button
        self.enable_run_button(False)

        self.window.tab_select.setStyleSheet("QTabBar::tab { height: 30px; width: 125px; background: 'lightgreen'}")
        # self.window.tab_select.setBackgroundRole(QPalette.base)
        # self.window.tab_select.setStyleSheet("QTabBar::tab { background: 'green'}")
        # self.window.tab_select.setStyleSheet("QTabBar::tab { foreground: 'lightgreen'}")

        # Timer start
        timer.start()
        # Setup the gui
        self.initialize_gui()

    def new_file(self):
        """
        Clears the gui and the input dictionary

        """
        self.clear_event_monitor()
        self.window.input_file_directory_1_result.setPlainText("")
        self.window.configuration_file_1_result.setPlainText("")
        self.window.project_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.initialize_gui()
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        self.enable_run_button(False)

    def open_file(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.

        """

        global configuration_file, scenario, configuration_file_valid, input_directory_valid
        global project_directory_valid, input_file_directory, project_directory
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
        color = "green"
        self.window.configuration_file_1_result.setTextColor(QColor(color))
        self.window.configuration_file_1_result.setPlainText(configuration_file)
        # Create python dictionary 'scenario' from YAML formatted configuration file
        filepath = configuration_file
        scenario = open_file_action(filepath)
        # Get input File Directory from dictionary
        item_value = ""
        # Make sure the dictionary entry exists
        try:
            item_value = scenario['input_file_directory']['Input_file_directory']
        # Add entry to dictionary if missing from file
        except (KeyError, TypeError):
            try:
                # Try to add replacement dictionary element
                scenario.update({'input_file_directory': {'Input_file_directory': 'null'}})
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
        if os.path.isdir(item_value):
            # Display in gui if valid
            input_file_directory = item_value
            color = "green"
            self.window.input_file_directory_1_result.setTextColor(QColor(color))
            self.window.input_file_directory_1_result.setPlainText(str(input_file_directory))
            input_directory_valid = True
        else:
            # Display error message if invalid
            input_file_directory = item_value
            color = "red"
            self.window.input_file_directory_1_result.setTextColor(QColor(color))
            self.window.input_file_directory_1_result.setPlainText(str(input_file_directory))
            input_directory_valid = False
            configuration_file_valid = False

        # Get output file directory from dictionary
        item_value = ""
        # Make sure the dictionary entry exists
        try:
            item_value = scenario['project_directory']['Project_directory']
        # Add entry to dictionary if missing from file
        except (KeyError, TypeError):
            scenario.update({'project_directory': {'Project_directory': 'null'}})
        # See if selected directory is valid
        if os.path.isdir(item_value):
            # Display in gui if valid
            project_directory = item_value
            color = "green"
            self.window.project_directory_1_result.setTextColor(QColor(color))
            self.window.project_directory_1_result.setPlainText(str(project_directory))
            project_directory_valid = True
        else:
            # Display error message if invalid
            project_directory = item_value
            color = "red"
            self.window.project_directory_1_result.setTextColor(QColor(color))
            self.window.project_directory_1_result.setPlainText(str(project_directory))
            project_directory_valid = False
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

    def save_file(self):
        """
        Opens a Windows dialog to save an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global configuration_file, scenario, input_file_directory, project_directory
        global configuration_file_valid
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
        color = "green"
        self.window.configuration_file_1_result.setTextColor(QColor(color))
        self.window.configuration_file_1_result.setPlainText(configuration_file)
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

    def open_input_directory(self):
        """
        Opens a Windows dialog to select an OMEGA2 input directory.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global input_file_directory, scenario, configuration_file
        global configuration_file_valid, input_directory_valid, project_directory_valid
        # self.window.statusBar().showMessage("Open File")
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
        # Update dictionary entry
        scenario['input_file_directory']['Input_file_directory'] = input_file_directory
        # Place path in gui
        directory = input_file_directory
        color = "green"
        self.window.input_file_directory_1_result.setTextColor(QColor(color))
        self.window.input_file_directory_1_result.setPlainText(str(directory))
        temp2 = "Input File Directory Loaded:\n    [" + directory + "]"
        self.event_monitor(temp2, color, 'dt')
        # Configuration has changed so blank out configuration file
        self.window.configuration_file_1_result.setPlainText("")
        configuration_file = ""
        configuration_file_valid = False
        input_directory_valid = True
        # User instructions to wizard
        self.wizard_logic()
        color = "black"
        self.event_monitor(event_separator, color, '')

    def open_project_directory(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global project_directory, scenario, configuration_file
        global configuration_file_valid, input_directory_valid, project_directory_valid
        # self.window.statusBar().showMessage("Open File")
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
        # Update dictionary entry
        scenario['project_directory']['Project_directory'] = project_directory
        # Place path in gui
        directory = project_directory
        color = "green"
        self.window.project_directory_1_result.setTextColor(QColor(color))
        self.window.project_directory_1_result.setPlainText(str(directory))
        temp2 = "Project Directory Loaded:\n    [" + directory + "]"
        self.event_monitor(temp2, color, 'dt')
        # Configuration has changed so blank out configuration file
        self.window.configuration_file_1_result.setPlainText("")
        configuration_file = ""
        configuration_file_valid = False
        project_directory_valid = True
        # User instructions to wizard
        self.wizard_logic()
        color = "black"
        self.event_monitor(event_separator, color, '')

    def event_monitor(self, text, color, timecode):
        if timecode == 'dt':
            time1 = datetime.now()
            t1 = time1.strftime("%H:%M:%S")
            today = date.today()
            d2 = today.strftime("%m/%d/%Y")
            text = d2 + " " + t1 + " " + text
        self.window.event_monitor_result.setTextColor(QColor(color))
        self.window.event_monitor_result.append(text)

    def clear_event_monitor(self):
        self.window.event_monitor_result.setPlainText("")

    # def wizard(self, text, color):
        # self.window.wizard_result.setTextColor(QColor(color))
        # self.window.wizard_result.append(text)

    # def clear_wizard(self):
        # self.window.wizard_result.setPlainText("")

    def wizard_logic(self):
        if configuration_file_valid and input_directory_valid and project_directory_valid:
            # self.clear_wizard()
            # temp1 = "Configuration Loaded.\n\n"
            # temp1 = temp1 + "Atomic Batteries to Power - Turbines to Speed!\n\n"
            # temp1 = temp1 + "Warp Factor Number Five Mr. Sulu\n\n"
            # temp1 = temp1 + "Punch It Chewie!"
            # self.wizard(temp1, "green")

            temp2 = "Configuration File Loaded:\n    [" + configuration_file + "]"
            self.event_monitor(temp2, 'green', 'dt')

            temp1 = "Configuration Loaded.\n"
            temp1 = temp1 + "Punch It Chewie!"
            self.event_monitor(temp1, 'black', '')

        elif not configuration_file_valid and input_directory_valid and project_directory_valid:
            # self.clear_wizard()
            temp1 = "Configuration has changed.  Save Configuration File to continue."
            self.event_monitor(temp1, 'black', '')
        elif not configuration_file_valid and (not input_directory_valid or not project_directory_valid):
            # self.clear_wizard()
            temp1 = "Elements in the Configuration are invalid:"
            self.event_monitor(temp1, 'black', '')
            if not input_directory_valid:
                temp2 = "Input Directory Invalid:\n    [" + input_file_directory + "]"
                self.event_monitor(temp2, 'red', 'dt')
            if not project_directory_valid:
                temp2 = "Project Directory Invalid:\n    [" + project_directory + "]"
                self.event_monitor(temp2, 'red', 'dt')
        if configuration_file_valid and input_directory_valid and project_directory_valid:
            self.enable_run_button(True)
        else:
            self.enable_run_button(False)

    def initialize_gui(self):
        global scenario, status_bar_message
        global configuration_file_valid, input_directory_valid, project_directory_valid
        wizard_init = "Open a valid Configuration File or:\n" \
                      "    Select New Input Directory," \
                      " Select New Project Directory," \
                      " and Save Configuration File\n" \
                      "----------"
        # Prime the status monitor
        color = "black"
        self.event_monitor("Ready", color, 'dt')
        self.event_monitor(event_separator, color, '')
        # Prime the wizard
        # self.clear_wizard()
        self.event_monitor(wizard_init, 'black', '')
        # Create 'scenario' dictionary for later reference
        scenario = {'input_file_directory': {'Input_file_directory': 'null'},
                    'project_directory': {'Project_directory': 'null'},
                    'project_description': {'Project_description': 'null'}}
        configuration_file_valid = False
        input_directory_valid = False
        project_directory_valid = False
        status_bar_message = "Ready"

    def clear_entries(self):
        """
            Clears all fields in the gui.

            :return: N/A
            """
        self.window.configuration_file_1_result.setPlainText("")
        self.window.input_file_directory_1_result.setPlainText("")
        self.window.project_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.clear_event_monitor()

    def run_model(self):
        """
        Copies all files from the input directory to the project directory.

        :return: N/A
        """
        self.event_monitor("Start Model Run ...", "black", 'dt')
        # Copy all files from the input directory to the project directory.
        color = "green"
        temp = "[" + input_file_directory + "]" + " to [" + project_directory + "]"
        self.event_monitor("Copying Files ...\n    " + temp, color, 'dt')
        self.window.repaint()
        copy_files(input_file_directory, project_directory)
        self.event_monitor("Copying Files Complete\n    " + temp, color, 'dt')
        self.event_monitor("End Model Run", "black", 'dt')
        self.event_monitor(event_separator, "black", '')

    def showbox(self, message_title, message):
        """
        Displays a popup message box.

        :param message_title: Title for message box
        :param message: Text for message box.
        :return: N/A
        """
        msg = QMessageBox()
        msg.setWindowTitle(message_title)
        msg.setText(message)
        msg.exec()

    def exit_gui(self):
        """
        Runs when the user requests gui close.
        """
        # Close the gui.
        self.window.close()

    def closeprogram(self):
        """
        Runs after the user closes the gui.
        Close any processes that are running outside the gui.
        """
        # Message to the terminal.
        print("User Terminating Process")
        # Stop timer process
        timer.stop()

    def enable_run_button(self, enable):
        """
        Enables and disables the run model button.

        :param enable: Boolean to enable or disable run model button and display appropriate button image
        :return: N/A
        """
        if enable:
            self.window.run_model_button.setIcon(QIcon(run_button_image_enabled))
            self.window.run_model_button.setEnabled(1)
        else:
            self.window.run_model_button.setIcon(QIcon(run_button_image_disabled))
            self.window.run_model_button.setEnabled(0)




def timer3():
    global status_bar_message
    # Put date, time, and message on status bar
    time1 = datetime.now()
    t1 = time1.strftime("%H:%M:%S")
    today = date.today()
    d1 = today.strftime("%m/%d/%Y")
    # If the form is not loaded, return
    try:
        form.window.statusBar().showMessage(d1 + "  " + t1 + "  " + status_bar_message)
    except NameError:
        return


# Run the function 'timer3' in 1 second intervals
timer = multitimer.MultiTimer(interval=1, function=timer3)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form('elements/omega_gui_v10.ui')
    sys.exit(app.exec_())
