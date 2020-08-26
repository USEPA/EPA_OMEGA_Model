"""
__main__.py
===========

OMEGA2 module-level run with default options

"""

from usepa_omega2 import *

if __name__ == "__main__":
    try:
        run_omega(OMEGARuntimeOptions())
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
