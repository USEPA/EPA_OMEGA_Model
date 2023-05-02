#! /bin/zsh

cd ..

# build executable

pyinstaller omega_effects/omega_effects_main.py \
  --name OMEGA-effects-2.1.0-mac.command \
  --paths omega_effects \
  --noconfirm \
  --onefile

# cleanup

mv *.spec versioning
rm -R __pycache__
rm -R build

cd versioning
