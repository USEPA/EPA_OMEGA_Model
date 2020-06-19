"""
__init.py__
===========

"""

from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session

import pandas as pd
pd.set_option('chained_assignment', 'raise')

import file_eye_oh as fileio

import matplotlib.pyplot as plt

# from copy import copy, deepcopy
# import numpy as np
# import networkx as nx
# import itertools
# import cProfile
# import time

# --- OMEGA2 globals ---
SQABase = declarative_base()
engine = create_engine('sqlite:///:memory:', echo=True)

# enumerated values
fueling_classes = ['BEV', 'ICE']
hauling_classes = ['hauling', 'non_hauling']
ownership_classes = ['shared', 'private']
reg_classes = ['car', 'truck']
fuel_units = ['gallon', 'kWh']

omega2_output_folder = 'output/'

# OMEGA2 code version number
code_version = "phase0.0.0"
# OMEGA2 input file format version number
input_format_version = '0.0'

print('loading usepa_omega2 version %s' % code_version)
