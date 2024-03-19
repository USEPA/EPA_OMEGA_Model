"""

Initiate OMEGA module-level run with default options

Can be used to test OMEGA installation


----

**CODE**

"""

print('importing %s' % __file__)

import os
import traceback

from omega_model import OMEGASessionSettings
from omega_model.omega import run_omega

if __name__ == "__main__":
    try:
        run_omega(OMEGASessionSettings(), standalone_run=True)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
