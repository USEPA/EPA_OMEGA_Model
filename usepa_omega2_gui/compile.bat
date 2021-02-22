# pyinstaller --windowed --onefile omega_gui_batch.py
# pyinstaller --windowed omega_gui_batch.py
pyinstaller exe_entry.py --name omega2 --paths usepa_omega2;usepa_omega2_gui --add-data usepa_omega2;usepa_omega2 --add-data usepa_omega2_gui;usepa_omega2_gui --noconfirm --onefile