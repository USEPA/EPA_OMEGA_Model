"""
Variables shared across GUI submodules

"""

import os

gui_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + os.sep

print('GUI path = "%s"' % gui_path)
