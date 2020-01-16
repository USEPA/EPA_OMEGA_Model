"""OMEGA GUI
   ---------

   This code controls the OMEGA GUI

       ::

        A highlighted literal section may also be added here if needed.

    """
import os
import sys

import multitimer
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QWidget, QTableWidgetItem

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
status_bar_message = "Ready"


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
        global gui_loaded
        gui_loaded = 1

        # Set the window title
        self.window.setWindowTitle("EPA OMEGA Model")
        # Set the status bar
        self.window.statusBar().showMessage("Ready")
        # Set the window icon
        self.window.setWindowIcon(QIcon("images/omega2_icon.jpg"))

        # Define gui connections to functions
        self.window.action_new_file.triggered.connect(self.new_file)
        self.window.action_open_configuration_file.triggered.connect(self.open_file)
        self.window.action_save_file.triggered.connect(self.save_file)
        self.window.action_save_file_as.triggered.connect(self.save_file_as)
        self.window.action_exit.triggered.connect(self.exit_gui)
        self.window.select_input_directory_button.clicked.connect(self.open_input_directory)
        self.window.select_project_directory_button.clicked.connect(self.open_project_directory)
        # Catch close event for clean exit
        app.aboutToQuit.connect(self.closeprogram)
        # Show gui
        self.window.show()

        # Initialize items
        # Select intro tab
        self.window.tab_select.setCurrentWidget(self.window.tab_select.findChild(QWidget, "intro_tab"))

    def new_file(self):
        self.window.statusBar().showMessage("New File")
        # self.ui.tab_select.setCurrentIndex(0)
        # Better file dialog
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter("Image files (*.jpg *.gif);; All Files (*.*)")
        dialog.setViewMode(QFileDialog.Detail)
        filenames = ""
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            filenames = str(filenames)[2:-2]
            print(filenames)
            self.window.file_1_result.setPlainText(str(filenames))
        new_file_action(filenames, 234)

    def open_file(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global configuration_file
        self.window.statusBar().showMessage("Open File")
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
        # Change status bar

        # Create python dictionary 'scenario' from YAML formatted configuration file
        filepath = configuration_file
        scenario = open_file_action(filepath)

        # Get input File Directory
        parts = scenario.get('input_file_directory')
        for item_name, item_value in parts.items():
            self.window.input_file_directory_1_result.setPlainText(str(item_value))
        # Get output file directory
        parts = scenario.get('project_directory')
        for item_name, item_value in parts.items():
            self.window.project_directory_1_result.setPlainText(str(item_value))

    def open_input_directory(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global input_file_directory
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
        self.window.input_file_directory_1_result.setPlainText(input_file_directory)

    def open_project_directory(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global project_directory
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
        self.window.project_directory_1_result.setPlainText(project_directory)



    def save_file(self):
        self.window.statusBar().showMessage("Save File")
        self.window.tab_select.setCurrentIndex(2)
        # file_name = "666"
        file_name = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_name = save_file_action(file_name)
        print(file_name)

    def save_file_as(self):
        self.window.statusBar().showMessage("Save File As")
        self.window.tab_select.setCurrentIndex(0)
        file_name = "eee.eee"
        file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_dialog_title = "Save As..."
        file_name, file_type, file_dialog_title = file_dialog(file_name, file_type, file_dialog_title)
        print(file_name)
        print(file_type)
        print(file_dialog_title)

    def exit_gui(self):
        self.window.close()

    def closeprogram(self):
        print("User Terminating Process")
        # Stop timer
        timer.stop()


def timer3():
    # Make sure gui is loaded before accessing it!
    if gui_loaded == 1:
        # Put date, time, and message on status bar
        time = datetime.now()
        t1 = time.strftime("%H:%M:%S")
        today = date.today()
        d1 = today.strftime("%B %d, %Y")
        form.window.statusBar().showMessage(d1 + "  " + t1 + "  " + status_bar_message)


# Run the function 'timer3' in 1 second intervals
timer = multitimer.MultiTimer(interval=1, function=timer3)
# Start timer
timer.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form('omega_gui_v5.ui')
    # window = MyApp()
    # window.show()
    sys.exit(app.exec_())
