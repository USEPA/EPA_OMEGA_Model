#! /bin/zsh

cd ..

# build executable

pyinstaller omega_effects/omega_effects_main.py \
  --name OMEGA-effects-2.3.0-mac.command \
  --paths omega_effects \
  --add-data "./*.txt;./" \
  --add-data "./omega_effects/*.py:./omega_effects/" \
  --add-data "./omega_effects/consumer/*.py:./omega_effects/consumer/" \
  --add-data "./omega_effects/context/*.py:./omega_effects/context/" \
  --add-data "./omega_effects/effects/*.py:./omega_effects/effects/" \
  --add-data "./omega_effects/general/*.py:./omega_effects/general/" \
  --add-data "./omega_effects/test_inputs/*.csv:./omega_effects/test_inputs/" \
  --noconfirm \
  --onefile

# cleanup

mv *.spec versioning
rm -R __pycache__
rm -R build

cd versioning
