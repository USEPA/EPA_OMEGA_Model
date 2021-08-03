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


# TODO off-cycle values as cls attributes in DecompositionAttributes
def calc_tech_volumes(physical_effects_dict):

    """

    Args:
        physical_effects_dict: A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the values are a
        dictionary of attributes and attribute value pairs.

    Returns:
        A dictionary key, value pair where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
        vehicle attributes (model_year, reg_class_id, in_use_fuel_id) and inventory attributes (co2 tons, fuel consumed, etc.) and their attribute values.

    """
    from producer.vehicles import VehicleFinal, DecompositionAttributes
    # from effects.inventory import get_vehicle_info

    tech_flag_list = DecompositionAttributes.other_values
    new_vehicle_tech_flag_dict = dict()
    tech_volumes_dict = dict()
    for key in physical_effects_dict.keys():
        vehicle_id, calendar_year, age = key
        physical = physical_effects_dict[key]

        tech_volumes_dict[key] = {'model_year': physical['model_year'],
                                  'reg_class_id': physical['reg_class_id'],
                                  'in_use_fuel_id': physical['in_use_fuel_id'],
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
