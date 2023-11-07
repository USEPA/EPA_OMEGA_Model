REM usage build_dist

cd ..

REM build executable

pyinstaller exe_entry.py ^
    --name OMEGA-2.2.0-win ^
    --paths omega_model;omega_gui ^
    --add-data omega_model;omega_model ^
    --add-data omega_gui/elements;omega_gui/elements ^
    --noconfirm ^
    --onefile

REM cleanup

move /Y  *.spec versioning
rmdir /S /Q __pycache__
rmdir /S /Q build

cd versioning
