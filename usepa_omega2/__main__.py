"""
__main__.py
===========

OMEGA2 top level code

"""

from usepa_omega2 import *

from fuels import *
from fuel_scenarios import *
from fuel_scenario_annual_data import *
from market_classes import *
from cost_curves import *
from cost_clouds import *
from GHG_standards_flat import *
from demanded_sales_annual_data import *
from manufacturers import *
from vehicles import *
from vehicle_annual_data import *


if __name__ == "__main__":

    print('OMEGA2 greeets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    fileio.validate_folder(o2_options.output_folder)

    SQABase.metadata.create_all(engine)

    try:
        init_fail = []
        init_fail = init_fail + Fuel.init_database_from_file(o2_options.fuels_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + FuelScenario.init_database_from_file(o2_options.fuel_scenarios_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + FuelScenarioAnnualData.init_database_from_file(o2_options.fuel_scenario_annual_data_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2_options.market_classes_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + CostCurve.init_database_from_file(o2_options.cost_curves_file, session, verbose=o2_options.verbose)
        # init_fail = init_fail + CostCloud.init_database_from_file(o2_options.cost_clouds_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2_options.ghg_standards_file, session, verbose=o2_options.verbose)
        # init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2_options.ghg_standards_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + DemandedSalesAnnualData.init_database_from_file(o2_options.demanded_sales_annual_data_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + Vehicle.init_database_from_file(o2_options.vehicles_file, session, verbose=o2_options.verbose)

        # initial year = initial fleet model year (latest year of data)
        o2_options.analysis_initial_year = session.query(func.max(Vehicle.model_year)).scalar()
        # final year = last year of cost curve data
        o2_options.analysis_final_year = session.query(func.max(CostCurve.model_year)).scalar()

        if not init_fail:
            dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)
        else:
            omega_log.logwrite("\#FAIL")
    except:
        omega_log.logwrite("\n#FAIL")
