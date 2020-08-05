"""
__main__.py
===========

OMEGA2 top level code

"""

import traceback

from usepa_omega2 import *

from fuels import Fuel
from fuel_scenarios import FuelScenario
from fuel_scenario_annual_data import FuelScenarioAnnualData
from market_classes import MarketClass
from cost_curves import CostCurve
from cost_clouds import CostCloud
from demanded_sales_annual_data import DemandedSalesAnnualData
from manufacturers import Manufacturer
from manufacturer_annual_data import ManufacturerAnnualData
from vehicles import Vehicle
from vehicle_annual_data import VehicleAnnualData
from consumer.reregistration_fixed_by_age import ReregistrationFixedByAge
from consumer.annual_vmt_fixed_by_age import AnnualVMTFixedByAge
import consumer.sales as consumer
import producer

if __name__ == "__main__":

    print('OMEGA2 greets you, version %s' % code_version)
    if '__file__' in locals():
        print('from %s with love' % fileio.get_filenameext(__file__))

    fileio.validate_folder(o2_options.output_folder)

    if o2_options.GHG_standard == 'flat':
        from GHG_standards_flat import GHGStandardFlat
    else:
        from GHG_standards_footprint import GHGStandardFootprint

    o2_options.producer_calculate_generalized_cost = producer.calculate_generalized_cost
    o2_options.consumer_calculate_generalized_cost = consumer.calculate_generalized_cost

    SQABase.metadata.create_all(engine)

    try:
        init_fail = []
        init_fail = init_fail + Fuel.init_database_from_file(o2_options.fuels_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + FuelScenario.init_database_from_file(o2_options.fuel_scenarios_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + FuelScenarioAnnualData.init_database_from_file(o2_options.fuel_scenario_annual_data_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + MarketClass.init_database_from_file(o2_options.market_classes_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + CostCurve.init_database_from_file(o2_options.cost_curves_file, session, verbose=o2_options.verbose)
        # init_fail = init_fail + CostCloud.init_database_from_file(o2_options.cost_clouds_file, session, verbose=o2_options.verbose)

        if o2_options.GHG_standard == 'flat':
            init_fail = init_fail + GHGStandardFlat.init_database_from_file(o2_options.ghg_standards_file, session, verbose=o2_options.verbose)
            o2_options.GHG_standard = GHGStandardFlat
        else:
            init_fail = init_fail + GHGStandardFootprint.init_database_from_file(o2_options.ghg_standards_file, session, verbose=o2_options.verbose)
            o2_options.GHG_standard = GHGStandardFootprint

        init_fail = init_fail + DemandedSalesAnnualData.init_database_from_file(o2_options.demanded_sales_annual_data_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + Vehicle.init_database_from_file(o2_options.vehicles_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + ReregistrationFixedByAge.init_database_from_file(o2_options.reregistration_fixed_by_age_file, session, verbose=o2_options.verbose)
        init_fail = init_fail + AnnualVMTFixedByAge.init_database_from_file(o2_options.annual_vmt_fixed_by_age_file, session, verbose=o2_options.verbose)

        # initial year = initial fleet model year (latest year of data)
        o2_options.analysis_initial_year = int(session.query(func.max(Vehicle.model_year)).scalar()) + 1
        # final year = last year of cost curve data
        o2_options.analysis_final_year = int(session.query(func.max(CostCurve.model_year)).scalar())

        if not init_fail:
            # dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=False)
            producer.run_compliance_model(session)
            dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=False)
        else:
            omega_log.logwrite("\#INIT FAIL")
    except Exception as e:
        if init_fail:
            omega_log.logwrite("\#INIT FAIL")
        omega_log.logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())

# from sqlalchemy.sql import text
# sel = Vehicle.__table__.select().where(text('model_year==2020 AND manufacturer_id=="USA Motors"'))
# ins = Vehicle.__table__.insert().from_select(Vehicle.__table__.columns, sel)
# print(ins)
# engine.execute(ins)
# session.execute('INSERT INTO vehicles (name, manufacturer_id, model_year) SELECT vehicles.name, vehicles.manufacturer_id, vehicles.model_year FROM vehicles WHERE model_year==2020 AND manufacturer_id=="USA Motors"')
# session.execute('INSERT INTO vehicles SELECT * FROM vehicles WHERE model_year==2020 AND manufacturer_id=="USA Motors"')
