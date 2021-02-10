"""

# build usepa_omega2 package:
pyinstaller exe_entry.py --name omega2 --paths usepa_omega2 --add-data usepa_omega2/test_inputs;usepa_omega2/test_inputs --noconfirm

# build usepa_omega2_gui package:
pyinstaller exe_entry.py --name omega2 --paths usepa_omega2;usepa_omega2_gui --add-data usepa_omega2;usepa_omega2 --add-data usepa_omega2_gui;usepa_omega2_gui --noconfirm --onefile

"""

import usepa_omega2
import usepa_omega2_gui.omega_gui_batch

# usepa_omega2.run_omega(usepa_omega2.OMEGARuntimeOptions(), standalone_run=True)
usepa_omega2_gui.omega_gui_batch.run_gui()
