"""
Variables shared across GUI submodules

----

**CODE**

"""

import os

gui_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep

print('\nOMEGA exectuable launching, this may take a few moments\n')

print('GUI path = "%s"' % gui_path)
