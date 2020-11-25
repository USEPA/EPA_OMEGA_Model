"""
stock.py
========

"""

from usepa_omega2 import *


def prior_year_stock_registered_count_slow(calendar_year):
    """
    Deregister vehicles by calendar year, as a function of vehicle attributes (e.g. age, market class...)

    :param calendar_year: calendar year
    :return: updates vehicle annual data table
    """

    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData

    # pull in last year's set of vehicle IDs (gets bigger every year!):
    calendar_year_prior_vehicle_IDs = sql_unpack_result(o2.session.query(VehicleAnnualData.vehicle_ID). \
                                                        filter(VehicleAnnualData.calendar_year == calendar_year - 1).all())

    for vehicle_ID in calendar_year_prior_vehicle_IDs:
        vehicle = o2.session.query(VehicleFinal).filter(VehicleFinal.vehicle_ID == vehicle_ID).one()

        scrappage_factor = float(o2.session.query(o2.options.stock_scrappage.reregistered_proportion). \
                                 filter(o2.options.stock_scrappage.market_class_ID == vehicle.market_class_ID). \
                                 filter(o2.options.stock_scrappage.age == ((calendar_year - vehicle.model_year) + 1)).
                                 scalar())

        VehicleAnnualData.update_registered_count(vehicle, calendar_year,
                                                  vehicle.initial_registered_count * scrappage_factor)

    o2.session.flush()


def prior_year_stock_registered_count(calendar_year):
    """
    Deregister vehicles by calendar year, as a function of vehicle attributes (e.g. age, market class...)

    :param calendar_year: calendar year
    :return: updates vehicle annual data table
    """

    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData

    # pull in last year's set of vehicle IDs (gets bigger every year!):
    calendar_year_prior_vehicle_IDs = sql_unpack_result(o2.session.query(VehicleAnnualData.vehicle_ID). \
                                                        filter(VehicleAnnualData.calendar_year == calendar_year - 1).all())

    vad_list = []
    for vehicle_ID in calendar_year_prior_vehicle_IDs:
        vehicle = get_vehicle(vehicle_ID)

        scrappage_factor = get_scrappage_factor(calendar_year, vehicle)

        vad_list.append(VehicleAnnualData(vehicle_ID=vehicle.vehicle_ID,
                                         calendar_year=calendar_year,
                                         registered_count=vehicle.initial_registered_count * scrappage_factor,
                                         age=(calendar_year - vehicle.model_year) + 1))

    o2.session.add_all(vad_list)
    o2.session.flush()


def update_vad(vehicle, calendar_year, scrappage_factor):
    from vehicle_annual_data import VehicleAnnualData
    VehicleAnnualData.update_registered_count(vehicle, calendar_year,
                                              vehicle.initial_registered_count * scrappage_factor)


scrappage_dict = dict()
def get_scrappage_factor(calendar_year, vehicle):
    # get scrappage factor
    age = ((calendar_year - vehicle.model_year) + 1)

    scrappage_factor_id = '%s_%s' % (vehicle.market_class_ID, age)
    if scrappage_factor_id in scrappage_dict:
        scrappage_factor = scrappage_dict[scrappage_factor_id]
    else:
        scrappage_factor = float(o2.session.query(o2.options.stock_scrappage.reregistered_proportion). \
                                filter(o2.options.stock_scrappage.market_class_ID == vehicle.market_class_ID). \
                                filter(o2.options.stock_scrappage.age == age).scalar())
        scrappage_dict[scrappage_factor_id] = scrappage_factor

    return scrappage_factor


vehicles_dict = dict()
def get_vehicle(vehicle_ID):
    from vehicles import VehicleFinal

    if vehicle_ID in vehicles_dict:
        vehicle = vehicles_dict[vehicle_ID]
    else:
        vehicle = o2.session.query(VehicleFinal).filter(VehicleFinal.vehicle_ID == vehicle_ID).one()
        vehicles_dict[vehicle_ID] = vehicle

    return vehicle


def prior_year_stock_vmt(calendar_year):
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData

    # pull in last year's vehicles:
    calendar_year_prior_vehicles = o2.session.query(VehicleAnnualData).\
        filter(VehicleAnnualData.calendar_year == calendar_year - 1).all()

    vehicle_IDs = []
    for idx in range(0, len(calendar_year_prior_vehicles)):
        vehicle_IDs.append(calendar_year_prior_vehicles[idx].vehicle_ID)

    for idx, vehicle_ID in enumerate(vehicle_IDs):
        veh_market_class = o2.session.query(VehicleFinal.market_class_ID).\
            filter(VehicleFinal.vehicle_ID == vehicle_ID)
        veh_age = calendar_year_prior_vehicles[idx].age + 1
        annual_vmt = o2.session.query(o2.options.stock_vmt.annual_vmt). \
            filter(o2.options.stock_vmt.market_class_ID == veh_market_class). \
            filter(o2.options.stock_vmt.age == veh_age).scalar()
        VehicleAnnualData.insert_vmt(vehicle_ID, calendar_year, annual_vmt)


def age0_stock_vmt(calendar_year):
    from vehicles import VehicleFinal
    from vehicle_annual_data import VehicleAnnualData

    # pull in last year's vehicles:
    age0_vehicles = o2.session.query(VehicleAnnualData).\
        filter(VehicleAnnualData.calendar_year == calendar_year).\
        filter(VehicleAnnualData.age==0).all()

    vehicle_IDs = []
    for idx in range(0, len(age0_vehicles)):
        vehicle_IDs.append(age0_vehicles[idx].vehicle_ID)

    for idx, vehicle_ID in enumerate(vehicle_IDs):
        veh_market_class = o2.session.query(VehicleFinal.market_class_ID).\
            filter(VehicleFinal.vehicle_ID == vehicle_ID)
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
        # fuels_file = 'EPA_OMEGA_MODEL/input_samples/fuels.csv'
        # self.manufacturers_file = 'input_samples/manufacturers.csv'
        # self.market_classes_file = 'input_samples/market_classes.csv'
        # self.vehicles_file = 'input_samples/vehicles.csv'
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
