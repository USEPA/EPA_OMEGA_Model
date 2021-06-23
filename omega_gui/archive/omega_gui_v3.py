"""OMEGA GUI
   ---------

   This code controls the OMEGA GUI

       ::

        A highlighted literal section may also be added here if needed.

    """
import os
import sys
import multitimer
import time

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QWidget
from PyQt5 import uic
from PyQt5.QtGui import QIcon

# Import functions from other files
from omega_gui.omega_gui_setup3 import *
from omega_gui.omega_gui_functions import *

atimer = 0
scenario_file = ""
working_directory = ""

Ui_MainWindow, QtBaseClass = uic.loadUiType('omega_gui_v4.ui')


def timer3():
    global atimer
    atimer = atimer + 1
    print(atimer)


timer = multitimer.MultiTimer(interval=1, function=timer3)
# timer.start()


class MyApp(QMainWindow):
    # Initialize global variables
    # mass_iterations = 1
    # rolling_iterations = 1
    # aero_iterations = 1
    # engine_iterations = 1

    # Import setup values for gui
    # import gui.gui_setup3

    def __init__(self):
        # Required python stuff to activate the UI
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Set the window title
        self.setWindowTitle("EPA OMEGA Model")
        # Set the status bar
        self.statusBar().showMessage("Ready")
        # Set the window icon
        self.setWindowIcon(QIcon("images/omega2_icon.jpg"))

        # Sets an icon and messages in the system tray
        # icon = QIcon("images/alpha_logo.jpg")
        # self.tray = QSystemTrayIcon()
        # self.tray.setIcon(icon)
        # self.tray.show()
        # self.tray.setToolTip("ALPHA Command Generator")
        # self.tray.showMessage("ALPHA Command Generator", "Ready")
        # self.tray.showMessage("ALPHA Command Generator", "Idle")

        # Connect routines to events and any other needed initialization
        # self.ui.vehicle_type_select.currentIndexChanged.connect(self.displayvalue)
        # self.ui.validate_mass_reduction_button.clicked.connect(self.validate_mass_reduction)
        # self.ui.validate_rolling_reduction_button.clicked.connect(self.validate_rolling_reduction)
        # self.ui.validate_aero_reduction_button.clicked.connect(self.validate_aero_reduction)
        # self.ui.validate_engine_sizing_button.clicked.connect(self.validate_engine_sizing)
        # self.ui.calc_iterations_button.clicked.connect(self.calc_iterations)

        self.ui.action_new_file.triggered.connect(self.new_file)
        self.ui.action_open_file.triggered.connect(self.open_file)
        self.ui.action_save_file.triggered.connect(self.save_file)
        self.ui.action_save_file_as.triggered.connect(self.save_file_as)

        # Initialize items
        # Hide buttons not used for UI
        # self.ui.validate_mass_reduction_button.setVisible(0)
        # self.ui.validate_rolling_reduction_button.setVisible(0)
        # self.ui.validate_aero_reduction_button.setVisible(0)
        # self.ui.validate_engine_sizing_button.setVisible(0)
        # self.ui.calc_iterations_button.setVisible(0)

        # self.ui.number_of_iterations.setText(str(1))

        # Read input file labels
        # self.ui.file_1_label.setText(input_file_1_label)
        # self.ui.file_2_label.setText(input_file_2_label)
        # self.ui.file_3_label.setText(input_file_3_label)
        # self.ui.file_4_label.setText(input_file_4_label)
        # self.ui.file_5_label.setText(input_file_5_label)
        # self.ui.file_6_label.setText(input_file_6_label)

    def new_file(self):
        self.statusBar().showMessage("New File")
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
            self.ui.file_1_result.setPlainText(str(filenames))
        new_file_action(filenames, 234)

    def open_file(self):
        """
        Opens a Windows dialog to select an OMEGA2 (.om2) Scenario file.

        When complete:
            Global variable "scenario_file" = user selected scenario file name.
            Global variable "working_directory" = User selected path to scenario file name.
        """
        global scenario_file, working_directory
        self.statusBar().showMessage("Open File")
        # self.ui.tab_select.setCurrentIndex(1)
        self.ui.tab_select.setCurrentWidget(self.ui.tab_select.findChild(QWidget, "scenario_tab"))
        file_name = ""
        # file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_type = "OMEGA2 Scenario Files (*.om2)"
        # Add file dialog title
        file_dialog_title = "Open File"
        # Call file dialog function
        file_name, file_type, file_dialog_title = file_dialog(file_name, file_type, file_dialog_title)
        # Return if no file selected or dialog cancelled
        if file_name == "":
            return
        # Get name of selected file
        temp1 = os.path.basename(file_name)
        temp1 = os.path.normpath(temp1)
        scenario_file = temp1
        # Place name of selected file in gui
        self.ui.scenario_file_1_result.setPlainText(temp1)
        # Get path of selected file
        temp1 = os.path.dirname(file_name)
        temp1 = os.path.normpath(temp1) + '\\'
        working_directory = temp1
        # Place path in gui
        self.ui.working_directory_1_result.setPlainText(temp1)
        # Change status bar
        self.statusBar().showMessage("Ready")

        filepath = working_directory + scenario_file

        # temp1 = self.ui.working_directory_1_result.toPlainText()
        data = open_file_action(filepath)
        # print(data)

        parts = data.get('input_files')
        for item_name, item_value in parts.items():
            print(item_name, item_value)
        parts = data.get('output_files')
        for item_name, item_value in parts.items():
            print(item_name, item_value)

        # path = working_directory + scenario_file
        # f = open(path, "r")
        # if f.mode == 'r':
        #    contents = f.read()
        #    print(contents)

    def save_file(self):
        self.statusBar().showMessage("Save File")
        self.ui.tab_select.setCurrentIndex(2)
        # file_name = "666"
        file_name = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_name = save_file_action(file_name)
        print(file_name)

    def save_file_as(self):
        self.statusBar().showMessage("Save File As")
        self.ui.tab_select.setCurrentIndex(0)
        file_name = "eee.eee"
        file_type = "Image files (*.jpg *.gif);; All Files (*.*)"
        file_dialog_title = "Save As..."
        file_name, file_type, file_dialog_title = file_dialog(file_name, file_type, file_dialog_title)
        print(file_name)
        print(file_type)
        print(file_dialog_title)

    def closeEvent(self, event):
        print("End Program")
        # timer.stop()

    # def displayvalue(self):
    #    self.ui.textEdit.setText(self.ui.vehicle_type_select.currentText())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()

    # Initialize global variables
    # mass_iterations = 1
    # rolling_iterations = 1
    # aero_iterations = 1
    # engine_iterations = 1

    sys.exit(app.exec_())
