REM usage build_dist

cd ..

# pyinstaller exe_entry.py --name omega2 --paths omega_model;omega_gui --add-data omega_model;omega_model --add-data omega_gui;omega_gui --noconfirm --onefile
`
REM build executable
pyinstaller exe_entry.py ^
    --name OMEGA-1.9.0 ^
    --paths omega_model;omega_gui ^
    --add-data omega_model;omega_model ^
    --add-data omega_gui;omega_gui ^
    --noconfirm ^
    --onefile

cd versioning
