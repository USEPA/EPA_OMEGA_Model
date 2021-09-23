REM usage build_dist

cd ..

REM build executable
pyinstaller exe_entry.py ^
    --name OMEGA-0.9.1 ^
    --paths omega_model;omega_gui ^
    --add-data omega_model;omega_model ^
    --add-data omega_gui\elements;omega_gui\elements ^
    --noconfirm ^
    --onefile

cd versioning
