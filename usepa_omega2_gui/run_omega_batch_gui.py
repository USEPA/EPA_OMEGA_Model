"""
run_omega_batch_gui.py
======================

Calls omega_batch.py

"""
import sys
import os

print('\n*** running run_omega_batch_gui.py... ***\n')

if not len(sys.argv) > 1:
    print("Batch Directives Missing")
else:
    path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    pythonpathstr = "set PYTHONPATH=%s" % path

    a = '%s & python -u "%s/usepa_omega2/omega_batch.py" %s' % (pythonpathstr, path,  sys.argv[1])
    print(a)
    os.system(a)
