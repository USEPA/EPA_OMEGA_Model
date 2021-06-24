"""

Initiate OMEGA module-level run with default options

Can be used to test OMEGA installation


----

**CODE**

"""

print('importing %s' % __file__)

import os
import traceback

from omega_model import run_omega, OMEGARuntimeOptions

if __name__ == "__main__":
    try:
        run_omega(OMEGARuntimeOptions(), standalone_run=True)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
