"""

This code launches and controls the OMEGA GUI.
The GUI uses QT Designer for the layout and PySide2 as the Python interface.
The GUI has been tested to display properly up to 125% text size based on Windows 10 display settings.

"""

import os
import sys

path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(path, '..'))  # picks up omega_model
sys.path.insert(0, os.path.join(path, '../omega_model'))  # picks up omega_model sub-packages

if 'darwin' in sys.platform:
    os.environ['QT_MAC_WANTS_LAYER'] = '1'  # for Qt on MacOS

import psutil

import multitimer

from PySide2.QtGui import QIcon, QColor, QTextOption
from PySide2.QtWidgets import QWidget, QMessageBox
# from playsound import playsound

# PyCharm indicates the next statement is not used but is needed for the compile process to satisfy PySide2.QtUiTools.
import PySide2.QtXml
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication
from PySide2.QtCore import QFile, QObject

from datetime import datetime

# Import functions from other files
from omega_gui_functions import *
from omega_gui_stylesheets import *

path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep

# print('omega_gui.py path = %s' % path)
# print('SYS Path = %s' % sys.path)

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
run_button_image_disabled = path + "omega_gui/elements/play_button_gray_transparent.png"
run_button_image_enabled = path + "omega_gui/elements/play_button_green_transparent.png"
epa_button_image = path + "omega_gui/elements/epa_seal_large_trim.gif"
input_batch_file_button_image = path + "omega_gui/elements/file_select_white.png"
output_batch_directory_button_image = path + "omega_gui/elements/folder_select_white.png"


# Common spacer between events
event_separator = "----------"
# OMEGA 2 version
omega2_version = ""
# Log file for communication from other processes
# log_file = "comm_file.txt"
log_file_batch = "batch_logfile.txt"
log_file_session_prefix = "o2log_"
log_file_session_suffix = "_ReferencePolicy.txt"


class Form(QObject):
    """
    The main GUI Qt object

    """
    def __init__(self, ui_file, parent=None):
        """
        This function runs once during program start.
        Loads the gui along with defining all connections and element defaults.

        :param ui_file:
        :param parent:
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
        self.window.setWindowIcon(QIcon(path + "omega_gui/elements/icon_white.ico"))

        # Define gui connections to functions
        self.window.action_new_file.triggered.connect(self.new_file)
        self.window.action_open_configuration_file.triggered.connect(self.open_file)
        self.window.action_select_input_batch_file.triggered.connect(self.open_input_batch_file)
        self.window.action_select_output_batch_directory.triggered.connect(self.open_output_batch_directory)
        self.window.action_save_configuration_file.triggered.connect(self.save_file)
        self.window.action_exit.triggered.connect(self.exit_gui)
        self.window.select_input_batch_file_button.clicked.connect(self.open_input_batch_file)
        self.window.select_output_batch_directory_button.clicked.connect(self.open_output_batch_directory)
        # self.window.open_configuration_file_button.clicked.connect(self.open_file)
        # self.window.save_configuration_file_button.clicked.connect(self.save_file)
        # self.window.clear_event_monitor_button.clicked.connect(self.clear_event_monitor)
        self.window.run_model_button.clicked.connect(self.run_model)
        self.window.action_run_model.triggered.connect(self.run_model)
        self.window.action_documentation.triggered.connect(self.launch_documentation)
        self.window.epa_button.clicked.connect(self.launch_epa_website)
        self.window.action_about_omega.triggered.connect(self.launch_about)
        self.window.action_omega_support.triggered.connect(self.launch_support)
        # self.window.multiprocessor_help_button.clicked.connect(self.launch_about_multiprocessor)
        # self.window.multiprocessor_checkbox.clicked.connect(self.multiprocessor_mode)
        # self.window.open_plot_2.clicked.connect(self.open_plot_2)
        # self.window.select_plot_2.clicked.connect(self.select_plot_2)
        # self.window.select_plot_3.clicked.connect(self.select_plot_3)
        # Catch close event for clean exit
        app.aboutToQuit.connect(self.closeprogram)
        # Show gui
        self.window.show()

        # Initialize items
        # Select file path tab
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "intro_tab"))
        # Set status monitor window options
        self.window.event_monitor_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.event_monitor_result.setReadOnly(1)
        # Set input file directory window options
        self.window.input_batch_file_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.input_batch_file_1_result.setReadOnly(1)
        # Set configuration file window options
        # self.window.configuration_file_1_result.setWordWrapMode(QTextOption.NoWrap)
        # self.window.configuration_file_1_result.setReadOnly(1)
        # Set project directory window options
        self.window.output_batch_directory_1_result.setWordWrapMode(QTextOption.NoWrap)
        self.window.output_batch_directory_1_result.setReadOnly(1)
        # Set wizard window options
        # self.window.wizard_result.setReadOnly(1)
        # Disable run model button graphics
        # self.enable_run_button(False)
        self.window.select_input_batch_file_button.setIcon(QIcon(input_batch_file_button_image))
        self.window.select_output_batch_directory_button.setIcon(QIcon(output_batch_directory_button_image))
        # self.window.results_comment.setPlainText('Feature Under Development\n'
        #                                          'See Batch Output Directory Session Folders for Outputs')
        # self.window.results_comment.setStyleSheet(development_stylesheet())

        # Load stylesheet for tab control
        stylesheet = tab_stylesheet()
        # stylesheet = test1(stylesheet)
        self.window.tab_select.setStyleSheet(stylesheet)

        # Load stylesheet for background
        stylesheet = background_stylesheet()
        self.window.background_widget.setStyleSheet(stylesheet)

        # Load stylesheet for buttons
        stylesheet = button_stylesheet()
        # self.window.clear_event_monitor_button.setStyleSheet(stylesheet)
        # self.window.open_configuration_file_button.setStyleSheet(stylesheet)
        # self.window.save_configuration_file_button.setStyleSheet(stylesheet)
        self.window.select_input_batch_file_button.setStyleSheet(stylesheet)
        self.window.select_output_batch_directory_button.setStyleSheet(stylesheet)
        self.window.run_model_button.setStyleSheet(stylesheet)
        # self.window.open_plot_2.setStyleSheet(stylesheet)
        # self.window.select_plot_2.setStyleSheet(stylesheet)
        # self.window.select_plot_3.setStyleSheet(stylesheet)
        # self.window.multiprocessor_help_button.setStyleSheet(stylesheet)

        # Load stylesheet for text boxes
        stylesheet = textbox_stylesheet()
        # stylesheet = "border: 1px solid; border-radius:10px; background-color: palette(base); "
        self.window.event_monitor_result.setStyleSheet(stylesheet)
        self.window.input_batch_file_1_result.setStyleSheet(stylesheet)
        self.window.output_batch_directory_1_result.setStyleSheet(stylesheet)
        self.window.project_description.setStyleSheet(stylesheet)

        # Load stylesheet for list boxes
        stylesheet = listbox_stylesheet()
        # self.window.list_graphs_1.setStyleSheet(stylesheet)
        # self.window.list_graphs_2.setStyleSheet(stylesheet)

        # Load stylesheet for logo buttons
        stylesheet = logo_button_stylesheet()
        self.window.epa_button.setStyleSheet(stylesheet)

        # Load stylesheet for labels
        stylesheet = label_stylesheet()
        # self.window.configuration_file_1_label.setStyleSheet(stylesheet)
        self.window.input_batch_file_1_label.setStyleSheet(stylesheet)
        self.window.output_batch_directory_1_label.setStyleSheet(stylesheet)
        self.window.project_description_1_label.setStyleSheet(stylesheet)
        self.window.main_title_1_label.setStyleSheet(stylesheet)
        self.window.event_monitor_label.setStyleSheet(stylesheet)
        self.window.model_status_label.setStyleSheet(stylesheet)
        # self.window.available_plots_1_label_2.setStyleSheet(stylesheet)
        # self.window.available_plots_1_label_3.setStyleSheet(stylesheet)
        self.window.intro_label.setStyleSheet(stylesheet)

        # Load stylesheet for checkboxes
        stylesheet = checkbox_stylesheet()
        # self.window.multiprocessor_checkbox.setStyleSheet(stylesheet)

        # Timer start
        timer.start()
        # Setup the gui
        self.initialize_gui()

    def new_file(self):
        """
        Clears the gui and the input dictionary.

        :return:
        """

        self.clear_event_monitor()
        self.window.input_batch_file_1_result.setPlainText("")
        # self.window.configuration_file_1_result.setPlainText("")
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

        :return:
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
        temp2 = os.path.normpath(temp2) + os.sep
        # CU
        configuration_file = temp2 + temp1
        # Place path in gui
        # CU
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
            # self.window.input_batch_file_1_result.setPlainText(os.path.basename(input_batch_file))
            self.window.input_batch_file_1_result.setPlainText(input_batch_file)
            input_batch_file_valid = True
        else:
            # Display error message if invalid
            input_batch_file = item_value
            color = "red"
            self.window.input_batch_file_1_result.setTextColor(QColor(color))
            # self.window.input_batch_file_1_result.setPlainText(os.path.basename(input_batch_file))
            self.window.input_batch_file_1_result.setPlainText(input_batch_file)
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
            # CU
            self.window.output_batch_directory_1_result.setPlainText(output_batch_directory)
            output_batch_directory_valid = True
        else:
            # Display error message if invalid
            output_batch_directory = item_value
            color = "red"
            self.window.output_batch_directory_1_result.setTextColor(QColor(color))
            # CU
            self.window.output_batch_directory_1_result.setPlainText(output_batch_directory)
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
        # CU
        self.window.input_batch_file_1_result.setToolTip(os.path.basename(input_batch_file))
        self.window.output_batch_directory_1_result.setToolTip(os.path.basename(output_batch_directory))

    def save_file(self):
        """
        Opens a Windows dialog to save an OMEGA 2 (.om2) configuration file.

        When complete:
            Global variable "scenario_file" = user selected configuration file name.
            Global variable "working_directory" = User selected path to configuration file.

        :return:
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
        temp2 = os.path.normpath(temp2) + os.sep
        # CU
        configuration_file = temp2 + temp1
        # Place path in gui
        # CU
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

        :return:
        """

        global input_batch_file, scenario, configuration_file
        global configuration_file_valid, input_batch_file_valid, output_batch_directory_valid
        # self.window.statusBar().showMessage("Open File")
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "run_model_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA 2 Batch Files (*.xlsx *.csv)"
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
        temp2 = os.path.normpath(temp2) + os.sep
        # working_directory = temp2
        input_batch_file = temp2 + temp1
        # Update dictionary entry
        scenario['input_batch_file']['input_batch_file'] = input_batch_file
        # Place path in gui
        directory = input_batch_file
        # temp3 = '...' + directory[-40:]
        color = "green"
        self.window.input_batch_file_1_result.setTextColor(QColor(color))
        # self.window.input_batch_file_1_result.setPlainText(os.path.basename(input_batch_file))
        self.window.input_batch_file_1_result.setPlainText(input_batch_file)
        temp2 = "Input Batch File Loaded:\n    [" + directory + "]"
        self.event_monitor(temp2, color, 'dt')
        # Configuration has changed so blank out configuration file
        # self.window.configuration_file_1_result.setPlainText("")
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

        :return:
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
        temp2 = os.path.normpath(temp2) + os.sep
        # working_directory = temp2
        output_batch_directory = temp2 + temp1
        # Update dictionary entry
        scenario['output_batch_directory']['output_batch_directory'] = output_batch_directory
        # Place path in gui
        directory = output_batch_directory
        color = "green"
        self.window.output_batch_directory_1_result.setTextColor(QColor(color))
        # self.window.output_batch_directory_1_result.setPlainText(os.path.basename(output_batch_directory))
        self.window.output_batch_directory_1_result.setPlainText(output_batch_directory)
        temp2 = "Project Directory Loaded:\n    [" + directory + "]"
        self.event_monitor(temp2, color, 'dt')
        # Configuration has changed so blank out configuration file
        # self.window.configuration_file_1_result.setPlainText("")
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
        :return:
        """

        if timecode == 'dt':
            now = datetime.now()
            date_time = now.strftime("%m/%d/%Y %H:%M:%S")
            text = date_time + "  " + text
        # if color != 'black':
        self.window.event_monitor_result.setTextColor(QColor(color))
        self.window.event_monitor_result.append(text)

    def clear_event_monitor(self):
        """
        Clears the event monitor textbox.

        :return:
        """

        self.window.event_monitor_result.setPlainText("")

    # def wizard(self, text, color):
    # self.window.wizard_result.setTextColor(QColor(color))
    # self.window.wizard_result.append(text)

    # def clear_wizard(self):
    # self.window.wizard_result.setPlainText("")

    @staticmethod
    def launch_documentation():
        """
        Opens the OMEGA documentation website in browser.

        :return:
        """

        doc_link = 'https://omega2.readthedocs.io/en/2.1.0'

        if sys.platform.startswith('win'):
            os.system("start \"\" %s" % doc_link)
        else:
            os.system('open %s' % doc_link)

    @staticmethod
    def launch_epa_website():
        """
        Opens the EPA website in browser.

        :return:
        """

        epa_link = 'https://epa.gov'

        if sys.platform.startswith('win'):
            os.system("start \"\" %s" % epa_link)
        else:
            os.system('open %s' % epa_link)

    def launch_about(self):
        """
        Displays the OMEGA version in a popup box.

        :return:
        """

        global omega2_version
        message_title = "About OMEGA"
        message = "OMEGA Code Version = " + omega2_version
        self.showbox(message_title, message)

    def launch_support(self):
        """
        Displays the OMEGA support email address in a popup box.

        :return:
        """

        message_title = "OMEGA Support"
        message = "Contact omega_support@epa.gov if you have questions about setting up and running the OMEGA model."
        self.showbox(message_title, message)

    def launch_about_multiprocessor(self):
        """
        Displays help for multiprocessor in a popup box.

        :return:
        """

        global omega2_version
        message_title = "About Multiprocessor Mode"
        message = "To use Multiprocessor mode, a batch file customized to the configuration\n" \
                  "of this computer must be executed before the GUI is launched.\n\n" \
                  "For reference, there are " + str(os.cpu_count()) + " CPUs in this computer.\n\n" \
                  "Please see the documentation for further details."

        os.cpu_count()
        self.showbox(message_title, message)

    def wizard_logic(self):
        """
        Handles the gui logic to enable and disable various controls and launch event monitor messages.

        :return:
        """

        global configuration_file_valid
        if configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:

            temp2 = "Configuration File Loaded:\n    [" + configuration_file + "]"
            self.event_monitor(temp2, 'green', 'dt')

            temp1 = "Configuration Loaded.\n"
            temp1 = temp1 + "Model Run Enabled."
            self.event_monitor(temp1, 'black', '')
        elif not configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:
            # self.clear_wizard()
            temp1 = "Configuration has changed.  Save Configuration File if desired."
            self.event_monitor(temp1, 'black', '')
            temp1 = "Configuration Loaded.\n"
            temp1 = temp1 + "Model Run Enabled."
            self.event_monitor(temp1, 'black', '')
            configuration_file_valid = True
        elif not configuration_file_valid and (not input_batch_file_valid or not output_batch_directory_valid):
            # self.clear_wizard()
            temp1 = "Elements in the Configuration are invalid:"
            self.event_monitor(temp1, 'black', '')
            if not input_batch_file_valid:
                temp2 = "Input Batch File Invalid:\n    [" + input_batch_file + "]"
                self.event_monitor(temp2, 'red', 'dt')
            if not output_batch_directory_valid:
                temp2 = "Output Batch Directory Invalid:\n    [" + output_batch_directory + "]"
                self.event_monitor(temp2, 'red', 'dt')
        if configuration_file_valid and input_batch_file_valid and output_batch_directory_valid:
            self.enable_run_button(True)
        else:
            self.enable_run_button(False)

    def initialize_gui(self):
        """
        Initialize various gui program functions.

        :return:
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
                      " and optionally Save Configuration File\n" \
                      "----------"

        # Get OMEGA 2 version #.
        from omega_model import code_version as omega2_version

        # Prime the status monitor
        color = "black"
        message = "OMEGA Version " + omega2_version + " Ready"
        self.event_monitor(message, color, 'dt')
        self.event_monitor(event_separator, color, '')

        # Check if dispy is running.
        if is_running("dispynode.py"):
            self.window.multiprocessor_checkbox.setEnabled(1)  # Enable multiprocessor checkbox if running
            message = "Multiprocessor Mode Available\n" \
                "----------"
            # self.event_monitor(message, 'black', '')
        else:
            # self.window.multiprocessor_checkbox.setEnabled(0)  # Disable multiprocessor checkbox if not running
            message = "Multiprocessor Mode Not Available\n" \
                "----------"
            # self.event_monitor(message, 'black', '')

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
        # self.window.save_configuration_file_button.setEnabled(0)
        self.window.epa_button.setIcon(QIcon(epa_button_image))
        # self.window.configuration_file_check_button.setIcon(QIcon(red_x_image))
        # self.window.input_batch_file_check_button.setIcon(QIcon(red_x_image))
        # self.window.output_batch_directory_check_button.setIcon(QIcon(red_x_image))
        self.window.setWindowTitle("EPA OMEGA Model     Version: " + omega2_version)

        self.window.model_status_label.setText("Model Idle")
        # self.window.select_plot_3.setEnabled(0)

    def clear_entries(self):
        """
        Clears all fields in the gui.

        :return:
        """

        # self.window.configuration_file_1_result.setPlainText("")
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

        :return:
        """

        self.clear_event_monitor()
        elapsed_start = datetime.now()
        global status_bar_message
        global multiprocessor_mode_selected
        global output_batch_subdirectory
        # status_bar()
        self.window.repaint()

        model_error_count = 0

        # This call works but gui freezes until new process ends
        # os.system("python omega_model/__main__.py")
        # Open batch definition
        if '.xls' in input_batch_file:
            batch_definition_df = pandas.read_excel(input_batch_file, index_col=0, sheet_name='Sessions')
        else:
            batch_definition_df = pandas.read_csv(input_batch_file, index_col=0)
        # Create timestamp for batch filename
        batch_time_stamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        # Create path to batch log file
        output_batch_subdirectory = output_batch_directory + os.sep + batch_time_stamp + '_' + \
            batch_definition_df.loc['Batch Name', 'Value']

        # Play a model start sound
        # sound1 = subprocess.Popen(['python', os.path.realpath('gui/sound_gui.py'), model_sound_start], close_fds=True)

        # Prepare options for OMEGA 2 batch process
        command_line_dict = dict()
        command_line_dict['batch_file'] = input_batch_file
        command_line_dict['bundle_path'] = output_batch_directory
        command_line_dict['timestamp'] = batch_time_stamp
        command_line_dict['calc_effects'] = 'Physical and Costs'
        if multiprocessor_mode_selected:
            command_line_dict['dispy'] = True
            command_line_dict['local'] = True
            command_line_dict['dispy_exclusive'] = True
            command_line_dict['dispy_debug'] = True

        # Disable selected gui functions during model run
        self.enable_gui_run_functions(0)
        # Indicate model start to status bar
        self.event_monitor("Start Model Run", "black", 'dt')
        # Call OMEGA 2 batch as a subprocess with command line options from above
        status_bar_message = "Status = Model Running ..."

        # While the subprocess is running, output communication from the batch process to the event monitor
        # First find the log files
        log_file_array = []  # Clear log file array
        log_counter_array = []  # Clear counter array
        log_ident_array = []  # Clear log identifier array
        file_timer = 0  # Counter for file search timer
        file_timer1 = 0  # Counter for item output timer

        import omega_model.omega_batch as omega_batch
        import threading, time
        import multiprocessing
        # t = threading.Thread(target=omega_batch.run_omega_batch, kwargs=command_line_dict, daemon=False)
        t = multiprocessing.Process(target=omega_batch.run_omega_batch, kwargs=command_line_dict, daemon=False)
        t.name = input_batch_file
        t.start()

        # self.load_plots_2()
        # Keep looking for communication from other processes through the log files
        # while omega_batch.poll() is None:
        while t.is_alive():
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
            elapsed_time = "Model Running\n" + elapsed_time[:-4] + "\nError Count = " + str(model_error_count)
            self.window.model_status_label.setText(elapsed_time)

            # Look for new log files
            file_timer = file_timer + 1
            if file_timer > 20:  # Look for new files every 2 seconds to reduce overhead
                file_timer = 0
                directory = output_batch_subdirectory + "/"  # Define output directory to search
                for root, dirs, files in os.walk(directory):  # Search includes subdirectories
                    for file in files:  # Begin search
                        # Add if .txt file is found and it does not already exist in the log file array
                        if file.endswith('.txt') and 'log' in file and not any(file in x for x in log_file_array):
                            fullpath = os.path.join(root, file)  # Generate complete path of file
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
            file_timer1 = file_timer1 + 1
            if file_timer1 > 10:  # Check every 1 second to reduce overhead
                file_timer1 = 0
                for log_loop in range(0, len(log_file_array)):
                    if os.path.isfile(log_file_array[log_loop]):
                        log_lines = sum(1 for line in open(log_file_array[log_loop]))
                        log_status = 1
                    else:
                        log_lines = 0
                        log_status = 0

                    # Read and output all new lines from log files
                    while log_counter_array[log_loop] < log_lines and log_status == 1:
                        try:
                            f = open(log_file_array[log_loop])
                        except Exception as e:
                            print("%%%%% File Missing: ", e)
                            break
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
                        if color == "red":
                            model_error_count = model_error_count + 1
                            # print('***', model_error_count)
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

        # CU
        elapsed_time1 = str(elapsed_time)
        elapsed_time1 = "Model Run Completed\n" + elapsed_time1[:-4] + "\nError Count = " + str(model_error_count)
        self.window.model_status_label.setText(elapsed_time1)
        # CU
        # Enable selected gui functions disabled during model run
        self.enable_gui_run_functions(1)
        # CU

    @staticmethod
    def showbox(message_title, message):
        """
        Displays a popup message box.

        :param message_title: Title for message box
        :param message: Text for message box.
        :return:
        """

        msg = QMessageBox()
        msg.setWindowTitle(message_title)
        msg.setText(message)
        msg.exec()

    def exit_gui(self):
        """
        Runs when the user requests gui close.

        :return:
        """

        # Close the gui.
        self.window.close()

    @staticmethod
    def closeprogram():
        """
        Runs after the user closes the gui.
        Close any processes that are running outside the gui.

        :return:
        """

        # Message to the terminal.
        print("User Terminating Process")
        # Stop timer process
        timer.stop()

    def multiprocessor_mode(self):
        """
        Checks the status of the Multiprocessor checkbox.

        :return:
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

        :param enable: Boolean to enable or disable run model button and display appropriate button image
        :return:
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

        :param enable: Boolean to enable or disable selected gui functions during model run
        :return:
        """

        # self.window.open_configuration_file_button.setEnabled(enable)
        # self.window.save_configuration_file_button.setEnabled(enable)
        self.window.select_input_batch_file_button.setEnabled(enable)
        self.window.select_output_batch_directory_button.setEnabled(enable)
        self.window.action_new_file.setEnabled(enable)
        self.window.action_open_configuration_file.setEnabled(enable)
        self.window.action_save_configuration_file.setEnabled(enable)
        self.window.action_select_input_batch_file.setEnabled(enable)
        self.window.action_select_output_batch_directory.setEnabled(enable)
        self.window.action_run_model.setEnabled(enable)
        self.window.run_model_button.setEnabled(enable)
        # self.window.multiprocessor_checkbox.setEnabled(enable)
        # self.window.select_plot_3.setEnabled(enable)

        # if enable == 1:
            # Check if dispy is running.
        #     if is_running("dispynode.py"):
        #         self.window.multiprocessor_checkbox.setEnabled(1)  # Enable multiprocessor checkbox if running
        #     else:
        #         self.window.multiprocessor_checkbox.setEnabled(0)  # Disable multiprocessor checkbox if not running
        # else:
        #     self.window.multiprocessor_checkbox.setEnabled(0)

    def select_plot_2(self):
        """
        Opens a Windows dialog to select a previous model run for plotting.

        :return:
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
        input_file = path + 'omega_gui/elements/plot_definition.csv'
        plot_data_df = pandas.read_csv(input_file)
        for index, row in plot_data_df.iterrows():
            # print(row['plot_name'])
            self.window.list_graphs_1.addItem(row['plot_name'])

        self.window.list_graphs_2.clear()
        input_file = plot_select_directory_path + os.sep + plot_select_directory_name + '_summary_results.csv'
        plot_select_directory = input_file
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

        :return:
        """

        global plot_select_directory_name
        global plot_select_directory
        self.window.list_graphs_1.clear()
        input_file = path + 'omega_gui/elements/plot_definition.csv'
        plot_data_df = pandas.read_csv(input_file)
        for index, row in plot_data_df.iterrows():
            self.window.list_graphs_1.addItem(row['plot_name'])

        self.window.list_graphs_2.clear()
        plot_select_directory_path = output_batch_subdirectory
        plot_select_directory_name = os.path.basename(os.path.normpath(output_batch_subdirectory))
        input_file = plot_select_directory_path + os.sep + plot_select_directory_name + '_summary_results.csv'
        plot_select_directory = input_file
        if not os.path.exists(input_file):
            self.window.list_graphs_1.clear()
            self.window.list_graphs_2.clear()
            return()
        plot_data_df1 = pandas.read_csv(input_file)
        plot_data_df1.drop_duplicates(subset=['session_name'], inplace=True)
        for index, row in plot_data_df1.iterrows():
            self.window.list_graphs_2.addItem(row['session_name'])

    def open_plot_2(self):
        """
        Plots the selected data.

        :return:
        """

        global plot_select_directory_name
        global plot_select_directory
        # See if valid selections have been made
        if self.window.list_graphs_1.currentItem() is not None and self.window.list_graphs_2.currentItem() is not None:
            # Get plot selections
            a = self.window.list_graphs_1.selectedIndexes()[0]
            b = self.window.list_graphs_2.selectedIndexes()[0]
            # Send plot selections to plot function
            c = "Plotting Data: [" + b.data() + "] [" + a.data() + "] From: " + plot_select_directory_name
            self.event_monitor(c, "black", 'dt')
            test_plot_2(a.data(), b.data(), plot_select_directory_name, plot_select_directory)


def status_bar():
    """
    Called once per second to display the date, time, and global variable "status_bar_message" in the status bar.

    :return:
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
    """
    Run the OMEGA GUI.

    """
    global app
    global form

    app = QApplication(sys.argv)
    # Load the gui
    uifilename = path + 'omega_gui/elements/omega_gui_qt.ui'
    print('uifilename = %s' % uifilename)
    form = Form(uifilename)
    sys.exit(app.exec_())


if __name__ == '__main__':
    import platform
    if platform.system() == 'Darwin':
        # workaround for PySide2 on MacOS Big Sur
        import os
        os.environ['QT_MAC_WANTS_LAYER'] = '1'
    # ***** Added for new plot
    # import sys
    # if sys.flags.interactive != 1 or not hasattr(pg.QtCore, 'PYQT_VERSION'):
    #     pg.QtGui.QApplication.exec_()
    # if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
    #     QtGui.QApplication.instance().exec_()
    # *****
    run_gui()
