#! /bin/zsh

cd ..

# build executable

pyinstaller exe_entry.py \
    --name OMEGA-2.1.0-mac.command \
    --paths omega_model:omega_gui \
    --add-data omega_model:omega_model \
    --add-data omega_gui/elements:omega_gui/elements \
    --noconfirm \
    --onefile

# cleanup

mv *.spec versioning
rm -R __pycache__
rm -R build

cd versioning
