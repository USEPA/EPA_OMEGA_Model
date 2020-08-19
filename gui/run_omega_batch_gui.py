"""
run_omega_batch_gui.py
===========

Calls run_omega_batch.py

"""
import sys
import os

if not len(sys.argv) > 1:
    print("Sound File Missing")
else:
    a = "python usepa_omega2/run_omega_batch.py " + (sys.argv[1])
    os.system(a)
