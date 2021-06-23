"""


----

**CODE**

"""

from omega_model import *

vehicles_cache = dict()


def get_vehicle_info(vehicle_ID):
    from producer.vehicles import VehicleFinal

    if vehicle_ID not in vehicles_cache:
        vehicles_cache[vehicle_ID] = VehicleFinal.get_vehicle_attributes(vehicle_ID, ['market_class_ID', 'model_year',
                                                                                      '_initial_registered_count'])

    return vehicles_cache[vehicle_ID]


def update_stock(calendar_year):
    """
    Deregister vehicles by calendar year, as a function of vehicle attributes (e.g. age, market class...)
    Update VMT
    :param calendar_year: calendar year
    :return: updates vehicle annual data table
    """

    from producer.vehicle_annual_data import VehicleAnnualData

    # pull in this year's vehicle ids:
    this_years_vehicle_annual_data = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

    omega_globals.session.add_all(this_years_vehicle_annual_data)
    # UPDATE vehicle annual data for this year's stock
    for vad in this_years_vehicle_annual_data:
        market_class_id, model_year, initial_registered_count = get_vehicle_info(vad.vehicle_ID)
        age = calendar_year - model_year # float(model_year)

        scrappage_factor = omega_globals.options.stock_scrappage.get_reregistered_proportion(market_class_id, age)

        annual_vmt = omega_globals.options.stock_vmt.get_vmt(market_class_id, age)

        registered_count = initial_registered_count * scrappage_factor

        vad.annual_vmt = annual_vmt
        vad.vmt = annual_vmt * registered_count

    prior_year_vehicle_ids = sql_unpack_result(VehicleAnnualData.get_vehicle_annual_data(calendar_year-1, 'vehicle_ID'))

    vad_list = []

    # CREATE vehicle annual data for last year's stock, now one year older:
    if prior_year_vehicle_ids:
        for vehicle_ID in prior_year_vehicle_ids:
            market_class_id, model_year, initial_registered_count = get_vehicle_info(vehicle_ID)
            age = calendar_year - model_year  # float(model_year)

            scrappage_factor = omega_globals.options.stock_scrappage.get_reregistered_proportion(market_class_id, age)

            annual_vmt = omega_globals.options.stock_vmt.get_vmt(market_class_id, age)

            registered_count = initial_registered_count * scrappage_factor

            vad_list.append(VehicleAnnualData(vehicle_ID=vehicle_ID,
                                              calendar_year=calendar_year,
                                              registered_count=registered_count,
                                              age=calendar_year-model_year,
                                              annual_vmt=annual_vmt,
                                              vmt=annual_vmt * registered_count)
                            )

    omega_globals.session.add_all(vad_list)


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
