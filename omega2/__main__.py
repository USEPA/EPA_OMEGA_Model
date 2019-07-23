"""
__main__.py
===========

OMEGA2 top level code

"""

import os

import omega2

if __name__ == "__main__":

    print('OMEGA2 greeets you, version %s' % omega2.__version__)
    print('from %s with love' % omega2.get_filenameext(os.path.abspath(__file__)))
