"""OMEGA GUI
   ---------

   This code controls the OMEGA GUI

       ::

        A highlighted literal section may also be added here if needed.

    """

import sys
import multitimer
import time

from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
from PyQt5 import uic
from PyQt5.QtGui import QIcon

# Import functions from other files
from gui.include1 import *

Ui_MainWindow, QtBaseClass = uic.loadUiType('OMEGA_GUI_V2.ui')

atimer = 0


def timer3():
    global atimer
    atimer = atimer + 1
    print(atimer)


timer = multitimer.MultiTimer(interval=1, function=timer3)
timer.start()


class MyApp(QMainWindow):
    # Initialize global variables
    # mass_iterations = 1
    # rolling_iterations = 1
    # aero_iterations = 1
    # engine_iterations = 1

def __init__():
    # Required python stuff to activate the UI
    super(MyApp).__init__()
    ui = Ui_MainWindow()
    ui.setupUi()

    mass_iterations = 1

    # Set the window title
    setWindowTitle("EPA OMEGA Model")
    # Set the status bar
    statusBar().showMessage(str(mass_iterations))
    # Set the window icon
    setWindowIcon(QIcon("images/omega2_icon.jpg"))


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


