REM usage build_dist

cd ..

REM build executable

pyinstaller omega_effects/omega_effects_main.py ^
  --name OMEGA-effects-2.5.0-win.exe ^
  --paths omega_effects ^
  --add-data "./*.txt;./" ^
  --add-data "./omega_effects/*.py;./omega_effects/" ^
  --add-data "./omega_effects/consumer/*.py;./omega_effects/consumer/" ^
  --add-data "./omega_effects/context/*.py;./omega_effects/context/" ^
  --add-data "./omega_effects/effects/*.py;./omega_effects/effects/" ^
  --add-data "./omega_effects/general/*.py;./omega_effects/general/" ^
  --add-data "./omega_effects/test_inputs/*.csv;./omega_effects/test_inputs/" ^
  --noconfirm ^
  --onefile

REM cleanup

move /Y  *.spec versioning
rmdir /S /Q __pycache__
rmdir /S /Q build

cd versioning
