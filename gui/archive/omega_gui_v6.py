"""OMEGA GUI
   ---------

   This code controls the OMEGA2 GUI

       ::

        A highlighted literal section may also be added here if needed.

    """
import os
import sys

import multitimer
from PySide2.QtGui import QIcon, QColor, QTextOption
from PySide2.QtWidgets import QWidget

from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject

from datetime import datetime, date

# Import functions from other files
from gui.omega_gui_functions import *

# Initialize global variables
atimer = 0
configuration_file = ""
input_file_directory = ""
project_directory = ""
gui_loaded = 0
date_time = ""
status_bar_message = "Ready"
scenario = ""
configuration_file_valid = False
input_directory_valid = False
project_directory_valid = False
wizard_init = ""


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
        self.window.save_configuration_file_button.clicked.connect(self.save_file)
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
        # Set wizard window options
        self.window.wizard_result.setReadOnly(1)

        # self.initialize_gui()

        timer.start()
        # time.sleep(5)
        global gui_loaded
        gui_loaded = 1
        self.initialize_gui()

    def new_file(self):
        self.clear_status_monitor()
        self.window.input_file_directory_1_result.setPlainText("")
        self.window.configuration_file_1_result.setPlainText("")
        self.window.project_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.initialize_gui()

    def open_file(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
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
        self.window.configuration_file_1_result.setPlainText(configuration_file)
        # Add to status monitor
        # temp1 = "Configuration File Loaded [" + configuration_file + "]"
        # self.status_monitor(temp1, "black")
        # Create python dictionary 'scenario' from YAML formatted configuration file
        filepath = configuration_file
        scenario = open_file_action(filepath)
        # Get input File Directory from dictionary
        item_value = ""
        # Make sure the dictionary entry exists
        try:
            item_value = scenario['input_file_directory']['Input_file_directory']
        # Add entry to dictionary if missing from file
        except KeyError:
            scenario.update({'input_file_directory': {'Input_file_directory': 'null'}})
        configuration_file_valid = True
        # See if selected directory is valid
        if os.path.isdir(item_value):
            # Display in gui if valid
            input_file_directory = item_value
            color = "black"
            self.window.input_file_directory_1_result.setTextColor(QColor(color))
            self.window.input_file_directory_1_result.setPlainText(str(input_file_directory))
            # Add to status monitor
            # temp2 = "Input File Directory Loaded [" + directory + "]"
            # self.status_monitor(temp2, color)
            input_directory_valid = True
        else:
            # Display error message if invalid
            input_file_directory = item_value
            color = "red"
            self.window.input_file_directory_1_result.setTextColor(QColor(color))
            self.window.input_file_directory_1_result.setPlainText(str(input_file_directory))
            # Add to status monitor
            # temp2 = "Input File Directory Invalid [" + directory + "]"
            # self.status_monitor(temp2, color)
            input_directory_valid = False
            configuration_file_valid = False

        # Get output file directory from dictionary
        item_value = ""
        # Make sure the dictionary entry exists
        try:
            item_value = scenario['project_directory']['Project_directory']
        # Add entry to dictionary if missing from file
        except KeyError:
            scenario.update({'project_directory': {'Project_directory': 'null'}})
        # See if selected directory is valid
        if os.path.isdir(item_value):
            # Display in gui if valid
            project_directory = item_value
            color = "black"
            self.window.project_directory_1_result.setTextColor(QColor(color))
            self.window.project_directory_1_result.setPlainText(str(project_directory))
            # Add to status monitor
            # temp2 = "Project Directory Loaded [" + directory + "]"
            # self.status_monitor(temp2, color)
            project_directory_valid = True
        else:
            # Display error message if invalid
            project_directory = item_value
            color = "red"
            self.window.project_directory_1_result.setTextColor(QColor(color))
            self.window.project_directory_1_result.setPlainText(str(project_directory))
            # Add to status monitor
            # temp2 = "Project Directory Invalid [" + directory + "]"
            # self.status_monitor(temp2, color)
            project_directory_valid = False
            configuration_file_valid = False

        # Display project description from configuration file
        item_value = ""
        try:
            item_value = scenario['project_description']['Project_description']
            # Trap, add element, and display if project description element missing from file
        except KeyError:
            scenario.update({'project_description': {'Project_description': 'null'}})
            temp2 = "Warning - No project description in configuration file"
            self.status_monitor(temp2, 'red')
            self.window.project_description.setPlainText(str(item_value))
        self.wizard_logic()
        temp2 = " "
        self.status_monitor(temp2, color)

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
        self.window.configuration_file_1_result.setPlainText(configuration_file)
        temp1 = "Configuration File Saved [" + configuration_file + "]"
        self.status_monitor(temp1, "black")
        # Save text from Project Description window to dictionary
        temp1 = self.window.project_description.toPlainText()
        scenario['project_description']['Project_description'] = temp1
        # Save YAML formatted configuration file
        filepath = configuration_file
        save_file_action(filepath, scenario)

        configuration_file_valid = True
        self.wizard_logic()
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
        color = "black"
        self.window.input_file_directory_1_result.setTextColor(QColor(color))
        self.window.input_file_directory_1_result.setPlainText(str(directory))
        temp2 = "Input File Directory Loaded [" + directory + "]"
        self.status_monitor(temp2, color)
        # Configuration has changed so blank out configuration file
        self.window.configuration_file_1_result.setPlainText("")
        configuration_file = ""
        configuration_file_valid = False
        input_directory_valid = True
        # User instructions to wizard
        self.wizard_logic()

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
        color = "black"
        self.window.project_directory_1_result.setTextColor(QColor(color))
        self.window.project_directory_1_result.setPlainText(str(directory))
        temp2 = "Project Directory Loaded [" + directory + "]"
        self.status_monitor(temp2, color)
        # Configuration has changed so blank out configuration file
        self.window.configuration_file_1_result.setPlainText("")
        configuration_file = ""
        configuration_file_valid = False
        project_directory_valid = True
        # User instructions to wizard
        self.wizard_logic()

    def status_monitor(self, text, color):
        global date_time
        time1 = datetime.now()
        t1 = time1.strftime("%H:%M:%S")
        today = date.today()
        d2 = today.strftime("%m/%d/%y")
        date_time = d2 + " " + t1
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

    def wizard_logic(self):
        if configuration_file_valid and input_directory_valid and project_directory_valid:
            self.clear_wizard()
            temp1 = "Configuration Loaded."
            self.wizard(temp1, "green")
            temp2 = "Configuration File Loaded [" + configuration_file + "]"
            self.status_monitor(temp2, 'black')
        elif not configuration_file_valid and input_directory_valid and project_directory_valid:
            self.clear_wizard()
            temp1 = "Configuration has changed.  Save Configuration File to continue."
            self.wizard(temp1, "red")
        elif not configuration_file_valid and (not input_directory_valid or not project_directory_valid):
            self.clear_wizard()
            temp1 = "Elements in the Configuration are invalid.  See the Status Monitor for details."
            self.wizard(temp1, "red")
            if not input_directory_valid:
                temp2 = "Input Directory Invalid [" + input_file_directory + "]"
                self.status_monitor(temp2, 'red')
            if not project_directory_valid:
                temp2 = "Project Directory Invalid [" + project_directory + "]"
                self.status_monitor(temp2, 'red')

    def initialize_gui(self):
        global scenario, wizard_init
        global configuration_file_valid, input_directory_valid, project_directory_valid
        wizard_init = "Open a valid Configuration File or:\n" \
                      "  1) Select New Input Directory\n" \
                      "  2) Select New Project Directory\n" \
                      "  3) Save Configuration File\n"
        # Prime the status monitor
        self.status_monitor("Ready", "black")
        # Prime the wizard
        self.clear_wizard()
        self.wizard(wizard_init, "green")
        # Create 'scenario' dictionary for later reference
        scenario = {'input_file_directory': {'Input_file_directory': 'null'},
                    'project_directory': {'Project_directory': 'null'},
                    'project_description': {'Project_description': 'null'}}
        configuration_file_valid = False
        input_directory_valid = False
        project_directory_valid = False

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
        time1 = datetime.now()
        t1 = time1.strftime("%H:%M:%S")
        today = date.today()
        d1 = today.strftime("%B %d, %Y")
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
