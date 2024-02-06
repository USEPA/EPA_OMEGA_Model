"""

**Routines to implement vehicle re-registration on an annual basis as a function of vehicle attributes.**

----

**CODE**

"""

from omega_model import *

vehicles_cache = dict()


def get_vehicle_info(vehicle_id):
    """
    Gets vehicle info for the given vehicle ID

    Args:
        vehicle_id (str): the vehicle ID (e.g. 'OEM_42')

    Returns:
        Vehicle market_class_id, model_year, initial_registered_count

    """
    # from producer.vehicles import Vehicle

    if vehicle_id not in vehicles_cache:
        try:
            vehicles_cache[vehicle_id] = [(v.market_class_id, v.model_year, v.initial_registered_count, v.reg_class_id)
                                      for v in omega_globals.finalized_vehicles if v.vehicle_id == vehicle_id][0]
        except:
            print('stock.py exception !!!')

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

    last_years_vehicle_annual_data = VehicleAnnualData.get_vehicle_annual_data(calendar_year-1, compliance_id)

    # omega_globals.session.add_all(this_years_vehicle_annual_data)
    # UPDATE vehicle annual data for this year's stock
    for vad in this_years_vehicle_annual_data:
        market_class_id, model_year, initial_registered_count, reg_class_id = get_vehicle_info(vad['vehicle_id'])
        age = calendar_year - model_year

        reregistration_factor = omega_globals.options.Reregistration.\
            get_reregistered_proportion(model_year, market_class_id, age)

        if initial_registered_count > 0:
            annual_vmt = omega_globals.options.OnroadVMT.get_vmt(calendar_year, market_class_id, age)
        else:
            annual_vmt = 0

        if age == 0:
            odometer = annual_vmt
        else:
            odometer = max(0, vad['odometer'])
            odometer += annual_vmt

        if reregistration_factor > 0:
            registered_count = initial_registered_count * reregistration_factor
            vad['annual_vmt'] = annual_vmt
            vad['odometer'] = odometer
            vad['vmt'] = annual_vmt * registered_count
            vad['reg_class_id'] = reg_class_id

    if not last_years_vehicle_annual_data:
        prior_year_vehicle_data = []
    else:
        prior_year_vehicle_data = [(v['vehicle_id'], v['odometer']) for v in last_years_vehicle_annual_data]

    vad_list = []

    # CREATE vehicle annual data for last year's stock, now one year older:
    if prior_year_vehicle_data:
        for vehicle_id, prior_odometer in prior_year_vehicle_data:
            market_class_id, model_year, initial_registered_count, reg_class_id = get_vehicle_info(vehicle_id)
            age = int(calendar_year - model_year)

            reregistration_factor = omega_globals.options.Reregistration.\
                get_reregistered_proportion(model_year, market_class_id, age)

            registered_count = initial_registered_count * reregistration_factor

            if reregistration_factor > 0:
                if initial_registered_count > 0:
                    annual_vmt = omega_globals.options.OnroadVMT.get_vmt(calendar_year, market_class_id, age)
                else:
                    annual_vmt = 0

                odometer = max(0, prior_odometer)
                odometer += annual_vmt

                vad_list.append(VehicleAnnualData.create(calendar_year=calendar_year,
                                  vehicle_id=vehicle_id,
                                  compliance_id=compliance_id,
                                  age=age,
                                  registered_count=registered_count,
                                  reg_class_id=reg_class_id,
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
        sys.exit(-1)
