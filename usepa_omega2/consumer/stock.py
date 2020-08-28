"""
stock.py
=============================

"""

from usepa_omega2 import *
from vehicles import Vehicle
from vehicle_annual_data import VehicleAnnualData


# def prior_year_stock_registered_count(calendar_year):
#
#     for year in range(o2.options.analysis_initial_year, calendar_year + 1):
#         # pull in last year's vehicles:
#         calendar_year_prior_vehicles = o2.session.query(VehicleAnnualData).\
#             filter(VehicleAnnualData.calendar_year == year - 1).all()
#
#         vehicle_IDs = []
#         for idx in range(0, len(calendar_year_prior_vehicles)):
#             vehicle_IDs.append(calendar_year_prior_vehicles[idx].vehicle_ID)
#
#         for idx, vehicle_ID in enumerate(vehicle_IDs):
#             # work on new stock count
#             vehicle_initial_sales = o2.session.query(VehicleAnnualData.registered_count).\
#                 filter(VehicleAnnualData.age==0).\
#                 filter(VehicleAnnualData.vehicle_ID==vehicle_ID).scalar()
#             veh_age = calendar_year_prior_vehicles[idx].age + 1
#             veh_market_class = o2.session.query(Vehicle.market_class_ID).filter(Vehicle.vehicle_ID == vehicle_ID)
#             scrappage_factor = o2.session.query(o2.options.stock_scrappage.reregistered_proportion).\
#                 filter(o2.options.stock_scrappage.market_class_ID == veh_market_class).\
#                 filter(o2.options.stock_scrappage.age == veh_age).scalar()
#             new_count = vehicle_initial_sales * scrappage_factor
#             VehicleAnnualData.update_registered_count(vehicle_ID, year, new_count)
#
#
# def prior_year_stock_vmt(calendar_year):
#
#     for year in range(o2.options.analysis_initial_year, calendar_year + 1):
#         # pull in last year's vehicles:
#         calendar_year_prior_vehicles = o2.session.query(VehicleAnnualData).\
#             filter(VehicleAnnualData.calendar_year == year - 1).all()
#
#         vehicle_IDs = []
#         for idx in range(0, len(calendar_year_prior_vehicles)):
#             vehicle_IDs.append(calendar_year_prior_vehicles[idx].vehicle_ID)
#
#         for idx, vehicle_ID in enumerate(vehicle_IDs):
#             veh_market_class = o2.session.query(Vehicle.market_class_ID).\
#                 filter(Vehicle.vehicle_ID == vehicle_ID)
#             veh_age = calendar_year_prior_vehicles[idx].age + 1
#             annual_vmt = o2.session.query(o2.options.stock_vmt.annual_vmt). \
#                 filter(o2.options.stock_vmt.market_class_ID == veh_market_class). \
#                 filter(o2.options.stock_vmt.age == veh_age).scalar()
#             VehicleAnnualData.insert_vmt(vehicle_ID, year, annual_vmt)
#
#
# def age0_stock_vmt(calendar_year):
#
#     for year in range(o2.options.analysis_initial_year, calendar_year + 1):
#         # pull in last year's vehicles:
#         age0_vehicles = o2.session.query(VehicleAnnualData).\
#             filter(VehicleAnnualData.calendar_year == year).\
#             filter(VehicleAnnualData.age==0).all()
#
#         vehicle_IDs = []
#         for idx in range(0, len(age0_vehicles)):
#             vehicle_IDs.append(age0_vehicles[idx].vehicle_ID)
#
#         for idx, vehicle_ID in enumerate(vehicle_IDs):
#             veh_market_class = o2.session.query(Vehicle.market_class_ID).\
#                 filter(Vehicle.vehicle_ID == vehicle_ID)
#             veh_age = 0
#             annual_vmt = o2.session.query(o2.options.stock_vmt.annual_vmt). \
#                 filter(o2.options.stock_vmt.market_class_ID == veh_market_class). \
#                 filter(o2.options.stock_vmt.age == veh_age).scalar()
#             VehicleAnnualData.insert_vmt(vehicle_ID, year, annual_vmt)

def prior_year_stock_registered_count(calendar_year):

    # pull in last year's vehicles:
    calendar_year_prior_vehicles = o2.session.query(VehicleAnnualData).\
        filter(VehicleAnnualData.calendar_year == calendar_year - 1).all()

    vehicle_IDs = []
    for idx in range(0, len(calendar_year_prior_vehicles)):
        vehicle_IDs.append(calendar_year_prior_vehicles[idx].vehicle_ID)

    for idx, vehicle_ID in enumerate(vehicle_IDs):
        # work on new stock count
        vehicle_initial_sales = o2.session.query(VehicleAnnualData.registered_count).\
            filter(VehicleAnnualData.age==0).\
            filter(VehicleAnnualData.vehicle_ID==vehicle_ID).scalar()
        veh_age = calendar_year_prior_vehicles[idx].age + 1
        veh_market_class = o2.session.query(Vehicle.market_class_ID).filter(Vehicle.vehicle_ID == vehicle_ID)
        scrappage_factor = o2.session.query(o2.options.stock_scrappage.reregistered_proportion).\
            filter(o2.options.stock_scrappage.market_class_ID == veh_market_class).\
            filter(o2.options.stock_scrappage.age == veh_age).scalar()
        new_count = vehicle_initial_sales * scrappage_factor
        vehicle = o2.session.query(Vehicle).filter(Vehicle.vehicle_ID == vehicle_ID)
        VehicleAnnualData.update_registered_count(vehicle, calendar_year, new_count)


def prior_year_stock_vmt(calendar_year):

    # pull in last year's vehicles:
    calendar_year_prior_vehicles = o2.session.query(VehicleAnnualData).\
        filter(VehicleAnnualData.calendar_year == calendar_year - 1).all()

    vehicle_IDs = []
    for idx in range(0, len(calendar_year_prior_vehicles)):
        vehicle_IDs.append(calendar_year_prior_vehicles[idx].vehicle_ID)

    for idx, vehicle_ID in enumerate(vehicle_IDs):
        veh_market_class = o2.session.query(Vehicle.market_class_ID).\
            filter(Vehicle.vehicle_ID == vehicle_ID)
        veh_age = calendar_year_prior_vehicles[idx].age + 1
        annual_vmt = o2.session.query(o2.options.stock_vmt.annual_vmt). \
            filter(o2.options.stock_vmt.market_class_ID == veh_market_class). \
            filter(o2.options.stock_vmt.age == veh_age).scalar()
        VehicleAnnualData.insert_vmt(vehicle_ID, calendar_year, annual_vmt)


def age0_stock_vmt(calendar_year):

    # pull in last year's vehicles:
    age0_vehicles = o2.session.query(VehicleAnnualData).\
        filter(VehicleAnnualData.calendar_year == calendar_year).\
        filter(VehicleAnnualData.age==0).all()

    vehicle_IDs = []
    for idx in range(0, len(age0_vehicles)):
        vehicle_IDs.append(age0_vehicles[idx].vehicle_ID)

    for idx, vehicle_ID in enumerate(vehicle_IDs):
        veh_market_class = o2.session.query(Vehicle.market_class_ID).\
            filter(Vehicle.vehicle_ID == vehicle_ID)
        veh_age = 0
        annual_vmt = o2.session.query(o2.options.stock_vmt.annual_vmt). \
            filter(o2.options.stock_vmt.market_class_ID == veh_market_class). \
            filter(o2.options.stock_vmt.age == veh_age).scalar()
        VehicleAnnualData.insert_vmt(vehicle_ID, calendar_year, annual_vmt)


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # from usepa_omega2 import *
        # from usepa_omega2.manufacturers import Manufacturer  # required by vehicles
        # from usepa_omega2.fuels import Fuel  # required by vehicles
        # from usepa_omega2.market_classes import MarketClass  # required by vehicles
        # # from vehicles import Vehicle  # for foreign key vehicle_ID
        #
        # fuels_file = 'EPA_OMEGA_MODEL/sample_inputs/fuels.csv'
        # self.manufacturers_file = 'sample_inputs/manufacturers.csv'
        # self.market_classes_file = 'sample_inputs/market_classes.csv'
        # self.vehicles_file = 'sample_inputs/vehicles.csv'
        #
        # # session = Session(bind=engine)
        # SQABase.metadata.create_all(engine)
        #
        # init_fail = []
        # init_fail = init_fail + MarketClass.init_database_from_file(o2_options.market_classes_file, session, verbose=o2_options.verbose)
        # init_fail = init_fail + Fuel.init_database_from_file(o2_options.fuels_file, session, verbose=o2_options.verbose)
        # init_fail = init_fail + Manufacturer.init_database_from_file(o2_options.manufacturers_file, session, verbose=o2_options.verbose)
        #
        # if not init_fail:
        #     for yr in (o2_options.analysis_initial_year, o2_options.analysis_final_year + 1):
        #         calc_stock_registered_count(session, yr)
        #     dump_database_to_csv(engine, o2_options.database_dump_folder, verbose=o2_options.verbose)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
