"""ALPHA GUI
   ---------

   This code controls the ALPHA GUI

       ::

        A highlighted literal section may also be added here if needed.

    """

import sys
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5 import uic
from PyQt5.QtGui import QIcon

# Import functions from other files
# from include1 import *

Ui_MainWindow, QtBaseClass = uic.loadUiType('OMEGA_GUI_V1.ui')


# def test_routine():
#    print("Test Routine")


class MyApp(QMainWindow):
    # Define global variables
    mass_iterations = 1
    rolling_iterations = 1
    aero_iterations = 1
    engine_iterations = 1

    def __init__(self):
        super(MyApp, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Sets the window title
        self.setWindowTitle("EPA ALPHA Model REVS3 Command File Generator")
        # Sets the status bar
        self.statusBar().showMessage("Ready")
        # Sets the window icon
        self.setWindowIcon(QIcon("images/alpha_logo.jpg"))

        # Sets an icon and messages in the system tray
        # icon = QIcon("images/alpha_logo.jpg")
        # self.tray = QSystemTrayIcon()
        # self.tray.setIcon(icon)
        # self.tray.show()
        # self.tray.setToolTip("ALPHA Command Generator")
        # self.tray.showMessage("ALPHA Command Generator", "Ready")
        # self.tray.showMessage("ALPHA Command Generator", "Idle")

        # Connect routines to events and any other needed initialization
        self.ui.vehicle_type_select.currentIndexChanged.connect(self.displayvalue)
        self.ui.validate_mass_reduction_button.clicked.connect(self.validate_mass_reduction)
        self.ui.validate_rolling_reduction_button.clicked.connect(self.validate_rolling_reduction)
        self.ui.validate_aero_reduction_button.clicked.connect(self.validate_aero_reduction)
        self.ui.validate_engine_sizing_button.clicked.connect(self.validate_engine_sizing)
        self.ui.calculate_iterations_button.clicked.connect(self.calculate_iterations)

        # Initialize items
        # Hide buttons not used for UI
        self.ui.validate_mass_reduction_button.setVisible(0)
        self.ui.validate_rolling_reduction_button.setVisible(0)
        self.ui.validate_aero_reduction_button.setVisible(0)
        self.ui.validate_engine_sizing_button.setVisible(0)
        self.ui.calculate_iterations_button.setVisible(0)

        self.ui.number_of_iterations.setText(str(1))

    def displayvalue(self):
        self.ui.textEdit.setText(self.ui.vehicle_type_select.currentText())

    # This function prevents invalid user selections on the Road Load UI page and then calculates
    # the possible step values given the valid max and min selections
    def validate_mass_reduction(self):
        # Mass Reduction
        # Get selection range from ui
        selection_range = self.ui.mass_reduction_max_select.value() - self.ui.mass_reduction_min_select.value()
        # Clear the step selector on ui
        self.ui.mass_reduction_step_select.clear()
        # Force selection ranges to be valid
        if self.ui.mass_reduction_max_select.value() < self.ui.mass_reduction_min_select.value():
            selection_range = 0
            self.ui.mass_reduction_min_select.setValue(self.ui.mass_reduction_max_select.value())
        #  Determine what step values are possible given the max and min selections in the ui
        for a in range(1, selection_range + 1):
            if selection_range / a == int(selection_range / a):
                self.ui.mass_reduction_step_select.addItem(str(a))
        if selection_range == 0:
            self.ui.mass_reduction_step_select.clear()
            self.ui.mass_reduction_step_select.addItem("0")

        self.calculate_iterations()

    def validate_rolling_reduction(self):
        # Rolling Reduction
        # Get selection range from ui
        selection_range = self.ui.rolling_reduction_max_select.value() - self.ui.rolling_reduction_min_select.value()
        # Clear the step selector on ui
        self.ui.rolling_reduction_step_select.clear()
        # Force selection ranges to be valid
        if self.ui.rolling_reduction_max_select.value() < self.ui.rolling_reduction_min_select.value():
            selection_range = 0
            self.ui.rolling_reduction_min_select.setValue(self.ui.rolling_reduction_max_select.value())
        #  Determine what step values are possible given the max and min selections in the ui
        for a in range(1, selection_range + 1):
            if selection_range / a == int(selection_range / a):
                self.ui.rolling_reduction_step_select.addItem(str(a))
        if selection_range == 0:
            self.ui.rolling_reduction_step_select.clear()
            self.ui.rolling_reduction_step_select.addItem("0")

        self.calculate_iterations()

    def validate_aero_reduction(self):
        # Aero Reduction
        # Get selection range from ui
        selection_range = self.ui.aero_reduction_max_select.value() - self.ui.aero_reduction_min_select.value()
        # Clear the step selector on ui
        self.ui.aero_reduction_step_select.clear()
        # Force selection ranges to be valid
        if self.ui.aero_reduction_max_select.value() < self.ui.aero_reduction_min_select.value():
            selection_range = 0
            self.ui.aero_reduction_min_select.setValue(self.ui.aero_reduction_max_select.value())
        #  Determine what step values are possible given the max and min selections in the ui
        for a in range(1, selection_range + 1):
            if selection_range / a == int(selection_range / a):
                self.ui.aero_reduction_step_select.addItem(str(a))
        if selection_range == 0:
            self.ui.aero_reduction_step_select.clear()
            self.ui.aero_reduction_step_select.addItem("0")

        self.calculate_iterations()

    def validate_engine_sizing(self):
        # Engine Sizing
        # Get selection range from ui
        selection_range = self.ui.engine_sizing_max_select.value() - self.ui.engine_sizing_min_select.value()
        # Clear the step selector on ui
        self.ui.engine_sizing_step_select.clear()
        # Force selection ranges to be valid
        if self.ui.engine_sizing_max_select.value() < self.ui.engine_sizing_min_select.value():
            selection_range = 0
            self.ui.engine_sizing_min_select.setValue(self.ui.engine_sizing_max_select.value())
        #  Determine what step values are possible given the max and min selections in the ui
        for a in range(1, selection_range + 1):
            if selection_range / a == int(selection_range / a):
                self.ui.engine_sizing_step_select.addItem(str(a))
        if selection_range == 0:
            self.ui.engine_sizing_step_select.clear()
            self.ui.engine_sizing_step_select.addItem("0")

        self.calculate_iterations()

        # test_routine()
        # test_routine1()

    def calculate_iterations(self):

        global mass_iterations
        mass_iterations = int(self.ui.mass_reduction_max_select.value())
        mass_iterations = mass_iterations - int(self.ui.mass_reduction_min_select.value())
        if int(self.ui.mass_reduction_step_select.currentText()) > 0:
            mass_iterations = mass_iterations / int(self.ui.mass_reduction_step_select.currentText())
        mass_iterations = mass_iterations + 1

        global rolling_iterations
        rolling_iterations = int(self.ui.rolling_reduction_max_select.value())
        rolling_iterations = rolling_iterations - int(self.ui.rolling_reduction_min_select.value())
        if int(self.ui.rolling_reduction_step_select.currentText()) > 0:
            rolling_iterations = rolling_iterations / int(self.ui.rolling_reduction_step_select.currentText())
        rolling_iterations = rolling_iterations + 1

        global aero_iterations
        aero_iterations = int(self.ui.aero_reduction_max_select.value())
        aero_iterations = aero_iterations - int(self.ui.aero_reduction_min_select.value())
        if int(self.ui.aero_reduction_step_select.currentText()) > 0:
            aero_iterations = aero_iterations / int(self.ui.aero_reduction_step_select.currentText())
        aero_iterations = aero_iterations + 1

        global engine_iterations
        engine_iterations = int(self.ui.engine_sizing_max_select.value())
        engine_iterations = engine_iterations - int(self.ui.engine_sizing_min_select.value())
        if int(self.ui.engine_sizing_step_select.currentText()) > 0:
            engine_iterations = engine_iterations / int(self.ui.engine_sizing_step_select.currentText())
        engine_iterations = engine_iterations + 1

        iterations = mass_iterations * rolling_iterations * aero_iterations * engine_iterations
        self.ui.number_of_iterations.setText(str(iterations))
        calculation = iterations * 15
        self.ui.calculation_time.setText(str(calculation))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyApp()
    window.show()

    # Initialize global variables
    mass_iterations = 1
    rolling_iterations = 1
    aero_iterations = 1
    engine_iterations = 1

    sys.exit(app.exec_())
