"""
__main__.py
===========

OMEGA2 module-level run with default options

"""
print('importing %s' % __file__)

from usepa_omega2 import *

if __name__ == "__main__":
    try:
        run_omega(OMEGARuntimeOptions(), single_shot=True)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
