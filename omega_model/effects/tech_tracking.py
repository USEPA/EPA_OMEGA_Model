"""

**Functions to track vehicle technology use.**


----

**CODE**

"""


vehicles_dict = dict()


def get_vehicle_info(vehicle_id, attribute_list):
    """

    Args:
        vehicle_id: The vehicle ID number from the VehicleFinal database table.
        attribute_list: The list of vehicle attributes for the vehicle_id vehicle for which vehicle information is needed.

    Returns:
        The attribute values associated with each element of attribute_list.

    """
    from producer.vehicles import VehicleFinal

    if vehicle_id not in vehicles_dict:
        vehicles_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)

    return vehicles_dict[vehicle_id]

# TODO need to track both base year reg class and reg class all the time
def calc_tech_volumes(physical_effects_dict):

    """

    Args:
        physical_effects_dict: A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the values are a
        dictionary of attributes and attribute value pairs.

    Returns:
        A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
        vehicle attributes (e.g., model_year, reg_class_id, in_use_fuel_id, etc.) and tech attributes (e.g., 'gdi', 'turb11', etc.) and their attribute values.

    """
    from producer.vehicles import VehicleFinal, DecompositionAttributes

    tech_flag_list = DecompositionAttributes.other_values + DecompositionAttributes.offcycle_values
    new_vehicle_tech_flag_dict = dict()
    tech_volumes_dict = dict()
    for key in physical_effects_dict.keys():
        vehicle_id, calendar_year, age = key
        physical = physical_effects_dict[key]

        tech_volumes_dict[key] = {'manufacturer_id': physical['manufacturer_id'],
                                  'model_year': physical['model_year'],
                                  'base_year_reg_class_id': physical['base_year_reg_class_id'],
                                  'reg_class_id': physical['reg_class_id'],
                                  'in_use_fuel_id': physical['in_use_fuel_id'],
                                  'non_responsive_market_group': physical['non_responsive_market_group'],
                                  'registered_count': physical['registered_count']
                                  }

        if vehicle_id not in new_vehicle_tech_flag_dict:
            new_vehicle_tech_flag_dict[vehicle_id] = dict()
            tech_flag_values = get_vehicle_info(vehicle_id, tech_flag_list)
            for idx, tech_flag in enumerate(tech_flag_list):
                new_vehicle_tech_flag_dict[vehicle_id].update({tech_flag: tech_flag_values[idx]})

        for tech_flag, tech_flag_value in new_vehicle_tech_flag_dict[vehicle_id].items():
            # if tech_flag == 'curb_weight':
            #     tech_volumes_dict[key].update({tech_flag: tech_flag_value})
            # else:
            tech_volumes_dict[key].update({tech_flag: tech_flag_value * physical['registered_count']})

    return tech_volumes_dict
