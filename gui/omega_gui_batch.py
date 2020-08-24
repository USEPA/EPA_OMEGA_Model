"""OMEGA GUI
   ---------

   This code controls the OMEGA2 GUI

       ::

        A highlighted literal section may also be added here if needed.

    """
import os
import sys
import subprocess

import multitimer
import time

from PySide2.QtGui import QIcon, QColor, QTextOption
from PySide2.QtWidgets import QWidget, QMessageBox

# PyCharm indicates the next statement is not used but is needed for the compile to satisfy PySide2.QtUiTools.
import PySide2.QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject

from datetime import datetime

# Import functions from other files
from omega_gui_functions import *
from omega_gui_stylesheets import *

# from external_functions import *

# Initialize global variables
# Contains the complete path (including filename) to the configuration file
configuration_file = ""
# Contains the directory path to the input file directory
input_batch_file = ""
# Contains the directory path to the project directory
output_batch_directory = ""
# Output to the status bar every timer cycle
status_bar_message = "Ready"
# Python dictionary containing contents of the configuration file
scenario = ""
# Logic elements for program control
configuration_file_valid = False
input_batch_file_valid = False
output_batch_directory_valid = False
# Images for model run button
run_button_image_disabled = "gui/elements/green_car_1.jpg"
run_button_image_enabled = "gui/elements/green_car_1.jpg"
# Common spacer between events
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
        self.window.setWindowIcon(QIcon("gui/elements/omega2_icon.jpg"))

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
        self.window.action_about_omega.triggered.connect(self.launch_about)
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

        # Timer start
        timer.start()
        # Setup the gui
        self.initialize_gui()

    def new_file(self):
        """
            Clears the gui and the input dictionary.

            :return: N/A
        """
        self.clear_event_monitor()
        self.window.input_batch_file_1_result.setPlainText("")
        self.window.configuration_file_1_result.setPlainText("")
        self.window.output_batch_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.initialize_gui()
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        self.enable_run_button(False)

    def open_file(self):
        """
            Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

            When complete:
                Global variable "scenario_file" = user selected scenario file name.

            :return: N/A
        """
        global configuration_file, scenario, configuration_file_valid, input_batch_file_valid
        global output_batch_directory_valid, input_batch_file, output_batch_directory
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
            self.window.input_batch_file_1_result.setPlainText(str(input_batch_file))
            input_batch_file_valid = True
        else:
            # Display error message if invalid
            input_batch_file = item_value
            color = "red"
            self.window.input_batch_file_1_result.setTextColor(QColor(color))
            self.window.input_batch_file_1_result.setPlainText(str(input_batch_file))
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
            self.window.output_batch_directory_1_result.setPlainText(str(output_batch_directory))
            output_batch_directory_valid = True
        else:
            # Display error message if invalid
            output_batch_directory = item_value
            color = "red"
            self.window.output_batch_directory_1_result.setTextColor(QColor(color))
            self.window.output_batch_directory_1_result.setPlainText(str(output_batch_directory))
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

    def save_file(self):
        """
            Opens a Windows dialog to save an OMEGA2 (.om2) Scenario file.

            When complete:
                Global variable "scenario_file" = user selected scenario file name.
                Global variable "working_directory" = User selected path to scenario file name.

            :return: N/A
        """
        global configuration_file, scenario, input_batch_file, output_batch_directory
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

    def open_input_batch_file(self):
        """
            Opens a Windows dialog to select an OMEGA2 input directory.

            When complete:
                Global variable "input_batch_file" = user selected input file directory.

            :return: N/A
        """
        global input_batch_file, scenario, configuration_file
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
        # self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "file_path_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA2 Batch Files (*.xlsx)"
        # Add file dialog title
        file_dialog_title = "Select OMEGA2 Batch File"
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
        color = "green"
        self.window.input_batch_file_1_result.setTextColor(QColor(color))
        self.window.input_batch_file_1_result.setPlainText(str(directory))
        temp2 = "Input File Directory Loaded:\n    [" + directory + "]"
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
            Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

            When complete:
                Global variable "output_batch_directory" = user selected project directory.

            :return: N/A
        """
        global output_batch_directory, scenario, configuration_file
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
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
        output_batch_directory = temp2 + temp1
        # Update dictionary entry
        scenario['output_batch_directory']['output_batch_directory'] = output_batch_directory
        # Place path in gui
        directory = output_batch_directory
        color = "green"
        self.window.output_batch_directory_1_result.setTextColor(QColor(color))
        self.window.output_batch_directory_1_result.setPlainText(str(directory))
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

        :param text: Text to append to event monitor window
        :param color: Color to display text
        :param timecode: 'dt' will display current date and time before text
        :return: N/A
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

        :return: N/A
        """
        self.window.event_monitor_result.setPlainText("")

    # def wizard(self, text, color):
    # self.window.wizard_result.setTextColor(QColor(color))
    # self.window.wizard_result.append(text)

    # def clear_wizard(self):
    # self.window.wizard_result.setPlainText("")

    def launch_documentation(self):
        """
        Opens the OMEGA documentation website in browser window.

        :return: N/A
        """
        os.system("start \"\" https://omega2.readthedocs.io/en/latest/index.html")

    def launch_about(self):
        """
        Displays the OMEGA version in a popup box.

        :return: N/A
        """
        message_title = "About OMEGA"
        message = "OMEGA Version 10.1.2"
        self.showbox(message_title, message)

    def wizard_logic(self):
        """
        Handles the gui logic to enable and disable various controls and launch event monitor messages.

        :return: N/A
        """
        if configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:

            temp2 = "Configuration File Loaded:\n    [" + configuration_file + "]"
            self.event_monitor(temp2, 'green', 'dt')

            temp1 = "Configuration Loaded.\n"
            temp1 = temp1 + "Punch It Chewie!"
            self.event_monitor(temp1, 'black', '')

            self.window.save_configuration_file_button.setEnabled(1)

        elif not configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:
            # self.clear_wizard()
            temp1 = "Configuration has changed.  Save Configuration File to continue."
            self.event_monitor(temp1, 'black', '')
            self.window.save_configuration_file_button.setEnabled(1)
        elif not configuration_file_valid and (not input_batch_file_valid or not output_batch_directory_valid):
            # self.clear_wizard()
            temp1 = "Elements in the Configuration are invalid:"
            self.event_monitor(temp1, 'black', '')
            self.window.save_configuration_file_button.setEnabled(0)
            if not input_batch_file_valid:
                temp2 = "Input Directory Invalid:\n    [" + input_batch_file + "]"
                self.event_monitor(temp2, 'red', 'dt')
            if not output_batch_directory_valid:
                temp2 = "Project Directory Invalid:\n    [" + output_batch_directory + "]"
                self.event_monitor(temp2, 'red', 'dt')
        if configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:
            self.enable_run_button(True)
        else:
            self.enable_run_button(False)

    def initialize_gui(self):
        """
        Initialize various program functions.

        :return: N/A
        """
        global scenario, status_bar_message
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
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
        scenario = {'input_batch_file': {'input_batch_file': 'null'},
                    'output_batch_directory': {'output_batch_directory': 'null'},
                    'project_description': {'Project_description': 'null'}}
        configuration_file_valid = False
        input_batch_file_valid = False
        output_batch_directory_valid = False
        status_bar_message = "Ready"
        self.enable_run_button(False)
        self.window.save_configuration_file_button.setEnabled(0)

    def clear_entries(self):
        """
        Clears all fields in the gui.

        :return: N/A
        """
        self.window.configuration_file_1_result.setPlainText("")
        self.window.input_batch_file_1_result.setPlainText("")
        self.window.output_batch_directory_1_result.setPlainText("")
        self.window.project_description.setPlainText("")
        self.clear_event_monitor()

    def run_model(self):
        """
        Copies all files from the input directory to the project directory.

        :return: N/A
        """
        model_sound_start = 'gui/elements/model_start.mp3'
        model_sound_stop = 'gui/elements/model_stop.mp3'
        global status_bar_message
        # self.event_monitor("Start Model Run ...", "black", 'dt')
        status_bar_message = "Model Running ..."
        status_bar()
        self.window.progress_bar.setValue(0)
        self.window.progress_bar.setValue(50)
        self.window.repaint()
        # Copy all files from the input directory to the project directory.
        # color = "green"
        # temp = "[" + input_batch_file + "]" + " to [" + output_batch_directory + "]"
        # self.event_monitor("Copying Files ...\n    " + temp, color, 'dt')
        # self.window.repaint()
        # copy_files(input_batch_file, output_batch_directory)
        # self.window.progress_bar.setValue(50)
        # copy_files(input_batch_file, output_batch_directory)
        # self.event_monitor("Copying Files Complete\n    " + temp, color, 'dt')

        # This call works but gui freezes until new process ends
        # os.system("python usepa_omega2/__main__.py")

        # Delete contents of comm_file.txt used to communicate with other processes
        file1 = open(output_batch_directory + "/comm_file.txt", "a")  # append mode
        file1.write("Today \n")
        file1.close()
        file = open(output_batch_directory + "/comm_file.txt", "r+")
        file.truncate(0)
        file.close()
        file1 = open(output_batch_directory + "/comm_file.txt", "a")  # append mode
        file1.write("Start Model Run \n")
        file1.close()

        # sound1 = subprocess.Popen(['python', os.path.realpath('gui/sound_gui.py'), model_sound_start], close_fds=True)

        # This call works and runs a completely separate process
        # omega2 = subprocess.Popen(['python', os.path.realpath('usepa_omega2/__main__.py'), 'Test333'], close_fds=True)
        # omega2.terminate()
        a = '--batch_file ' + '"' + input_batch_file + '"'
        b = ' --bundle_path ' + '"' + output_batch_directory + '"'
        c = a + b

        omega_batch = subprocess.Popen(['python', os.path.realpath('gui/run_omega_batch_gui.py'),
                                        c], close_fds=True)

        line_counter = 0
        status_file = output_batch_directory + '/comm_file.txt'
        poll = None
        while poll is None:
            time.sleep(1)
            poll = omega_batch.poll()
            # print('****** Running', poll)
            num_lines = sum(1 for line in open(status_file))

            while line_counter < num_lines:
                f = open(status_file)
                lines = f.readlines()
                f.close()
                g = lines[line_counter]
                g = g.rstrip("\n")
                # print(g)
                self.event_monitor(g, "black", 'dt')
                # self.window.repaint()
                line_counter = line_counter + 1
                # print('*****', line_counter, num_lines)
                # self.window.repaint()
                app.processEvents()


            #  with open(status_file) as f:
            #      if '5' in f.read():
            #          print('***** Found')

        print('****** Complete', poll)

        # a = 0
        # while a == 0:
        #     time.sleep(1)
        #     with open('gui/comm_file.txt') as f:
        #         if 'end_model_run' in f.read():
        #             a = 1

        # sound2 = subprocess.Popen(['python', os.path.realpath('gui/sound_gui.py'), model_sound_stop], close_fds=True)
        # time.sleep(2)
        # sound1.terminate()

        self.event_monitor("End Model Run", "black", 'dt')
        self.event_monitor(event_separator, "black", '')
        status_bar_message = "Ready"
        status_bar()
        self.window.progress_bar.setValue(100)

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
            self.window.action_run_model.setEnabled(1)
        else:
            self.window.run_model_button.setIcon(QIcon(run_button_image_disabled))
            self.window.run_model_button.setEnabled(0)
            self.window.action_run_model.setEnabled(0)


def status_bar():
    """
    Called once per second to display the date, time, and global variable "status_bar_message" in the status bar.

    :return: N/A
    """
    global status_bar_message
    # Put date, time, and message on status bar
    now = datetime.now()
    date_time = now.strftime("%B %d, %Y  %H:%M:%S")
    try:
        form.window.statusBar().showMessage(date_time + "  " + status_bar_message)
    except NameError:
        return


# Run the function 'timer3' in 1 second intervals
timer = multitimer.MultiTimer(interval=1, function=status_bar)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form('gui/elements/omega_gui_v15.ui')
    sys.exit(app.exec_())
