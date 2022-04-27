"""

**Routines to implement vehicle re-registration on an annual basis as a function of vehicle attributes.**

----

**CODE**

"""

from omega_model import *

vehicles_cache = dict()


def get_vehicle_info(vehicle_id):
    """
    Gets vehicle info for the given database vehicle ID

    Args:
        vehicle_id (int): the database vehicle ID (e.g. 1,2,3...)

    Returns:
        Vehicle market_class_id, model_year, initial_registered_count

    """
    from producer.vehicles import VehicleFinal

    if vehicle_id not in vehicles_cache:
        vehicles_cache[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, ['market_class_id', 'model_year',
                                                                                      '_initial_registered_count'])

    return vehicles_cache[vehicle_id]


def update_stock(calendar_year, compliance_id=None):
    """
    Re-register vehicles by calendar year, as a function of vehicle attributes (e.g. age, market class...)
    Also calculates vehicle miles travelled for each vehilce by market class and age.

    Args:
        compliance_id (str): optional argument, manufacturer name, or 'consolidated_OEM'
        calendar_year (int): calendar year to re-register vehicles in

    Returns:
        Nothing, updates VehicleAnnualData entries (``age``, ``registered_count``, ``annual_vmt``, ``vmt``).

    """
    from producer.vehicle_annual_data import VehicleAnnualData

    if calendar_year < omega_globals.options.analysis_initial_year:
        vehicles_cache.clear()

    # pull in this year's vehicle ids:
    this_years_vehicle_annual_data = VehicleAnnualData.get_vehicle_annual_data(calendar_year, compliance_id)

    last_years_vehicle_annual_data = VehicleAnnualData.get_vehicle_annual_data(calendar_year-1)

    # omega_globals.session.add_all(this_years_vehicle_annual_data)
    # UPDATE vehicle annual data for this year's stock
    for vad in this_years_vehicle_annual_data:
        market_class_id, model_year, initial_registered_count = get_vehicle_info(vad['vehicle_id'])
        age = calendar_year - model_year

        reregistration_factor = omega_globals.options.Reregistration.\
            get_reregistered_proportion(model_year, market_class_id, age)

        annual_vmt = omega_globals.options.OnroadVMT.get_vmt(calendar_year, market_class_id, age)

        if age == 0:
            odometer = annual_vmt
        else:
            odometer = max(0, odometer_data[odometer_data['vehicle_id'].values==vad.vehicle_id]['odometer'].values)
            odometer += annual_vmt

        if reregistration_factor > 0:
            registered_count = initial_registered_count * reregistration_factor
            vad['annual_vmt'] = annual_vmt
            vad['odometer'] = odometer
            vad['vmt'] = annual_vmt * registered_count

    if not last_years_vehicle_annual_data:
        prior_year_vehicle_data = []
    else:
        prior_year_vehicle_data = [(v['vehicle_id'], v['odometer']) for v in last_years_vehicle_annual_data]

    vad_list = []

    # CREATE vehicle annual data for last year's stock, now one year older:
    if prior_year_vehicle_data:
        for vehicle_id, prior_odometer in prior_year_vehicle_data:
            market_class_id, model_year, initial_registered_count = get_vehicle_info(vehicle_id)
            age = calendar_year - model_year

            reregistration_factor = omega_globals.options.Reregistration.\
                get_reregistered_proportion(model_year, market_class_id, age)

            if reregistration_factor > 0:
                annual_vmt = omega_globals.options.OnroadVMT.get_vmt(calendar_year, market_class_id, age)

                odometer = max(0, prior_odometer)
                odometer += annual_vmt

                registered_count = initial_registered_count * reregistration_factor

                vad_list.append(VehicleAnnualData.create(calendar_year=calendar_year,
                                  vehicle_id=int(vehicle_id),
                                  compliance_id=compliance_id,
                                  age=calendar_year - model_year,
                                  registered_count=registered_count,
                                  annual_vmt=annual_vmt,
                                  odometer=odometer,
                                  vmt=annual_vmt * registered_count))

        VehicleAnnualData.add_all(vad_list)


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
