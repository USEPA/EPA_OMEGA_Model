REM usage build_dist

cd ..

REM build executable

pyinstaller omega_effects/omega_effects_main.py ^
  --name OMEGA-effects-2.3.0-win.exe ^
  --paths omega_effects ^
  --noconfirm ^
  --onefile

REM cleanup

move /Y  *.spec versioning
rmdir /S /Q __pycache__
rmdir /S /Q build

cd versioning
