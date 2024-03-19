"""

# build omega_model package:
pyinstaller exe_entry.py --name omega2 --paths omega_model --add-data omega_model/test_inputs;omega_model/test_inputs --noconfirm

# WINDOWS build omega_gui package:
pyinstaller exe_entry.py --name omega2 --paths omega_model;omega_gui --add-data omega_model;omega_model --add-data omega_gui;omega_gui --noconfirm --onefile
pyinstaller exe_entry.py --name omega2 --paths omega_model;omega_gui --add-data omega_model;omega_model --add-data omega_gui;omega_gui --noconfirm

# *NIX build omega_gui package:
pyinstaller exe_entry.py --name omega2 --paths omega_model:omega_gui --add-data omega_model:omega_model --add-data omega_gui:omega_gui --noconfirm --onefile
pyinstaller exe_entry.py --name omega2 --paths omega_model:omega_gui --add-data omega_model:omega_model --add-data omega_gui:omega_gui --noconfirm

"""
import multiprocessing

# import omega_model
import omega_gui.omega_gui

# fix for for pyinstaller multiprocessing issue
multiprocessing.freeze_support()

# omega_model.run_omega(omega_model.OMEGASessionSettings(), standalone_run=True)
omega_gui.omega_gui.run_gui()
