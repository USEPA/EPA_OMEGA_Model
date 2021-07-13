#! /bin/zsh

PATH=./venv:./venv/Scripts:$PATH
PYTHONPATH=.:./omega_model

python test_omega2.py

cd test_omega2_output

ls

