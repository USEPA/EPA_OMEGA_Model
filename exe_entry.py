"""

# build omega_model package:
pyinstaller exe_entry.py --name omega2 --paths omega_model --add-data omega_model/demo_inputs;omega_model/demo_inputs --noconfirm

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

# imports for pyinstaller to package user-definable classes...
import policy.regulatory_classes
import policy.targets_alternative
import policy.targets_footprint
import policy.offcycle_credits
import consumer.reregistration_fixed_by_age
import consumer.annual_vmt_fixed_by_age
import consumer.sales_share
import consumer.market_classes
import producer.producer_generalized_cost

# fix for for pyinstaller multiprocessing issue
multiprocessing.freeze_support()

# omega_model.run_omega(omega_model.OMEGARuntimeOptions(), standalone_run=True)
omega_gui.omega_gui.run_gui()
