"""
__main__.py
===========

OMEGA2 top level code

"""

from usepa_omega2 import *

from manufacturers import *
from vehicles import *
from vehicle_annual_data import *
from GHG_standards_flat import  *
from market_classes import *
from cost_curves import *
from cost_clouds import *
from fuels import *
from fuel_scenario_annual_data import *
from showroom_data import *
from demanded_sales_annual_data import *


if __name__ == "__main__":

    print('OMEGA2 greeets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    fileio.validate_folder(o2_options.output_folder)

    SQABase.metadata.create_all(engine)

    # TODO: need to update self-test here:
    # init_fail = []
    # init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
