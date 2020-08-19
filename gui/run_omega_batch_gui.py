"""
run_omega_batch_gui.py
===========

Calls run_omega_batch.py

"""
import sys

if not len(sys.argv) > 1:
    print("Expecting link argument.")
else:
    print("in p1.py link is " + sys.argv[0])
    print(len(sys.argv))

# os.system('python usepa_omega2/run_omega_batch.py --batch_file inputs\phase0_default_batch_file.xlsx')
