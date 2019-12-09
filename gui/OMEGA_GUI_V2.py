"""OMEGA GUI
   ---------

   This code controls the OMEGA GUI

       ::

        A highlighted literal section may also be added here if needed.

    """

import sys
from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QIcon

# Import functions from other files
from gui.include1 import *

Ui_MainWindow, QtBaseClass = uic.loadUiType('OMEGA_GUI_V2.ui')


class MyApp(QMainWindow):
    # Initialize global variables
    # mass_iterations = 1
    # rolling_iterations = 1
    # aero_iterations = 1
    # engine_iterations = 1

    def __init__(self):
        # Required python stuff to activate the UI
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        mass_iterations = 1

        # Set the window title
        self.setWindowTitle("EPA OMEGA Model")
        # Set the status bar
        self.statusBar().showMessage(str(mass_iterations))
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
        # self.ui.calculate_iterations_button.clicked.connect(self.calculate_iterations)

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
        # self.ui.calculate_iterations_button.setVisible(0)

        # self.ui.number_of_iterations.setText(str(1))

        self.ui.file_1_label.setText("Input File #1")
        self.ui.file_2_label.setText("Input File #2")
        self.ui.file_3_label.setText("Input File #3")
        self.ui.file_4_label.setText("Input File #4")
        self.ui.file_5_label.setText("Input File #5")
        self.ui.file_6_label.setText("Input File #6")

    def new_file(self):
        self.statusBar().showMessage("New File")
        self.ui.tab_select.setCurrentIndex(0)
        # Better file dialog
        dialog = QFileDialog(self)
        dialog.setFileMode(QFileDialog.AnyFile)
        dialog.setNameFilter("Image files (*.jpg *.gif);; All Files (*.*)")
        dialog.setViewMode(QFileDialog.Detail)
        if dialog.exec_():
            filenames = dialog.selectedFiles()
            filenames = str(filenames)[2:-2]
            print(filenames)
            self.ui.file_1_result.setPlainText(str(filenames))
        new_file_action(filenames, 234)

    def open_file(self):
        self.statusBar().showMessage("Open File")
        self.ui.tab_select.setCurrentIndex(1)
        # Open file with options
        title = "Open File"
        location = "c:\\"
        filetype = "Image files (*.jpg *.gif);; All Files (*.*)"
        fname = QFileDialog.getOpenFileName(self, title, location, filetype)
        # Open file without options
        # fname = QFileDialog.getOpenFileName()
        print(fname)
        open_file_action()

    def save_file(self):
        self.statusBar().showMessage("Save File")
        self.ui.tab_select.setCurrentIndex(2)
        save_file_action()

    def save_file_as(self):
        self.statusBar().showMessage("Save File As")
        self.ui.tab_select.setCurrentIndex(0)
        file_dialog()

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
