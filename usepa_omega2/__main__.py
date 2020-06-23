"""
__main__.py
===========

OMEGA2 top level code

"""

from usepa_omega2 import *

from manufacturers import *
from vehicles import *
from vehicle_annual_data import *
from GHG_standards import  *
from market_classes import *
from cost_curves import *
from fuels import *
from fuel_scenario_annual_data import *
from showroom_data import *
from showroom_annual_data import *


if __name__ == "__main__":

    print('OMEGA2 greeets you, version %s' % code_version)
    print('from %s with love' % fileio.get_filenameext(__file__))

    fileio.validate_folder(omega2_output_folder)

    session = Session(bind=engine)
    SQABase.metadata.create_all(engine)

    init_fail = Fuel.init_database('input_templates/fuels.csv', session, verbose=True)
