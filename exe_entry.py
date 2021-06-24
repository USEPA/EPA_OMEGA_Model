"""

# build omega_model package:
pyinstaller exe_entry.py --name omega2 --paths omega_model --add-data omega_model/test_inputs;omega_model/test_inputs --noconfirm

# WINDOWS build omega_gui package:
pyinstaller exe_entry.py --name omega2 --paths omega_model;omega_gui --add-data omega_model;omega_model --add-data omega_gui;omega_gui --noconfirm --onefile

# *NIX build omega_gui package:
pyinstaller exe_entry.py --name omega2 --paths omega_model:omega_gui --add-data omega_model:omega_model --add-data omega_gui:omega_gui --noconfirm --onefile

"""

# import omega_model
import omega_gui.omega_gui_batch

# omega_model.run_omega(omega_model.OMEGARuntimeOptions(), standalone_run=True)
omega_gui.omega_gui_batch.run_gui()
