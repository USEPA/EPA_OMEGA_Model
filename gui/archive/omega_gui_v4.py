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

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog, QWidget, QListWidget, QListWidgetItem, \
    QTableWidgetItem
from PyQt5 import uic
from PyQt5.QtGui import QIcon

# Import functions from other files
from gui.omega_gui_setup3 import *
from gui.omega_gui_functions import *

atimer = 0
scenario_file = ""
working_directory = ""

Ui_MainWindow, QtBaseClass = uic.loadUiType('omega_gui_v4.ui')


def timer3():
    global atimer
    atimer = atimer + 1
    atimer
    if atimer == 5:
        window.ui.statusbar.showMessage("rrr")


    #else:
    #    window.ui.statusbar.showMessage("Hello")
    #    window.exit_gui()
    #    temp = MyApp()
    #    temp.exit_gui()
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

        self.ui.action_new_file.triggered.connect(self.new_file)
        self.ui.action_open_file.triggered.connect(self.open_file)
        self.ui.action_save_file.triggered.connect(self.save_file)
        self.ui.action_save_file_as.triggered.connect(self.save_file_as)
        self.ui.action_exit.triggered.connect(self.exit_gui)

        # Initialize items
        self.ui.tab_select.setCurrentWidget(self.ui.tab_select.findChild(QWidget, "intro_tab"))

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

        # Create library 'data' from YAML formatted scenario file
        filepath = working_directory + scenario_file
        data = open_file_action(filepath)

        # Read dictionary 'data' into tables in gui
        # Set row and column count
        self.ui.input_file_table.setRowCount(15)
        self.ui.input_file_table.setColumnCount(2)
        # Set header names
        self.ui.input_file_table.setHorizontalHeaderLabels(['File Type', 'File Name'])
        # Reset line counter
        a = 0
        # Read 'input_file' elements in dictionary 'data'
        parts = data.get('input_files')
        # Load name and value for each element into input file table
        for item_name, item_value in parts.items():
            self.ui.input_file_table.setItem(a, 0, QTableWidgetItem(str(item_name)))
            self.ui.input_file_table.setItem(a, 1, QTableWidgetItem(str(item_value)))
            a = a + 1
        # Autosize column widths
        self.ui.input_file_table.resizeColumnsToContents()

        # Read dictionary 'data' into tables in gui
        # Set row and column count
        self.ui.output_file_table.setRowCount(15)
        self.ui.output_file_table.setColumnCount(2)
        # Set header names
        self.ui.output_file_table.setHorizontalHeaderLabels(['File Type', 'File Name'])
        # Reset line counter
        a = 0
        # Read 'output_file' elements in dictionary 'data'
        parts = data.get('output_files')
        # Load name and value for each element into output file table
        for item_name, item_value in parts.items():
            self.ui.output_file_table.setItem(a, 0, QTableWidgetItem(str(item_name)))
            self.ui.output_file_table.setItem(a, 1, QTableWidgetItem(str(item_value)))
            a = a + 1
        # Autosize column widths
        self.ui.output_file_table.resizeColumnsToContents()

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

    def exit_gui(self):
        self.close()

    def closeEvent(self, event):
        print("End Program")
        # timer.stop()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()
    sys.exit(app.exec_())
