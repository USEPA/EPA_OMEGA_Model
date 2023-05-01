REM usage build_dist

cd ..

REM build executable

pynstaller omega_effects/omega_effects_main.py ^
  --name omega-effects-win.command ^
  --paths omega_effects ^
  --noconfirm ^
  --onefile

REM cleanup

move /Y  *.spec versioning
rmdir /S /Q __pycache__
rmdir /S /Q build

cd versioning
