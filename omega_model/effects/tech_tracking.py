"""

Functions to track vehicle technology use.


----

**CODE**

"""


vehicle_info_dict = dict()
vehicle_tech_dict = dict()


def get_vehicle_info(vehicle_id, attribute_list):
    """

    Args:
        vehicle_id: The vehicle ID number from the VehicleFinal database table.
        attribute_list: The list of vehicle attributes for the vehicle_id vehicle for which vehicle information is needed.

    Returns:
        The attribute values associated with each element of attribute_list.

    """
    from producer.vehicles import VehicleFinal

    if vehicle_id not in vehicle_info_dict:
        vehicle_info_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)

    return vehicle_info_dict[vehicle_id]


def get_vehicle_tech_info(vehicle_id, attribute_list):
    """

    Args:
        vehicle_id: The vehicle ID number from the VehicleFinal database table.
        attribute_list: The list of vehicle attributes for the vehicle_id vehicle for which vehicle information is needed.

    Returns:
        The attribute values associated with each element of attribute_list.

    """
    from producer.vehicles import VehicleFinal

    if vehicle_id not in vehicle_tech_dict:
        vehicle_tech_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, attribute_list)

    return vehicle_tech_dict[vehicle_id]


def calc_tech_volumes(calendar_years): #physical_effects_dict):

    """

    Args:
        physical_effects_dict: A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the values are a
        dictionary of attributes and attribute value pairs.

    Returns:
        A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
        vehicle attributes (e.g., model_year, reg_class_id, in_use_fuel_id, etc.) and tech attributes (e.g., 'gdi', 'turb11', etc.) and their attribute values.

    """
    from producer.vehicle_annual_data import VehicleAnnualData
    from producer.vehicles import DecompositionAttributes

    tech_flag_list = DecompositionAttributes.other_values + DecompositionAttributes.offcycle_values
    id_attribute_list = ['manufacturer_id', 'model_year', 'base_year_reg_class_id', 'reg_class_id', 'in_use_fuel_id',
                         'non_responsive_market_group',]
    # attribute_list = id_attribute_list + tech_flag_list

    new_vehicle_tech_flag_dict = dict()
    tech_volumes_dict = dict()
    for calendar_year in calendar_years:
        vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

        for vad in vads:

            vehicle_id, age, registered_count = vad.vehicle_id, vad.age, vad.registered_count
            key = vehicle_id, int(calendar_year), int(age)

            mfr_id, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, non_responsive_market_group \
                = get_vehicle_info(vehicle_id, id_attribute_list)
            tech_volumes_dict[key] = {'manufacturer_id': mfr_id,
                                      'model_year': model_year,
                                      'base_year_reg_class_id': base_year_reg_class_id,
                                      'reg_class_id': reg_class_id,
                                      'in_use_fuel_id': in_use_fuel_id,
                                      'non_responsive_market_group': non_responsive_market_group,
                                      'registered_count': registered_count,
                                      }

            if vad.vehicle_id not in new_vehicle_tech_flag_dict:
                new_vehicle_tech_flag_dict[vehicle_id] = dict()
                tech_flag_values = get_vehicle_tech_info(vehicle_id, tech_flag_list)
                for idx, tech_flag in enumerate(tech_flag_list):
                    new_vehicle_tech_flag_dict[vehicle_id].update({tech_flag: tech_flag_values[idx]})

            for tech_flag, tech_flag_value in new_vehicle_tech_flag_dict[vehicle_id].items():
                if tech_flag_value is None:
                    tech_volumes_dict[key].update({tech_flag: tech_flag_value})
                elif tech_flag == 'curb_weight':
                    tech_volumes_dict[key].update({tech_flag: tech_flag_value})
                    tech_volumes_dict[key].update({'fleet_pounds': tech_flag_value * registered_count})
                elif tech_flag == 'weight_reduction':
                    tech_volumes_dict[key].update({tech_flag: tech_flag_value})
                else:
                    tech_volumes_dict[key].update({tech_flag: tech_flag_value * registered_count})

    return tech_volumes_dict

    # tech_flag_list = DecompositionAttributes.other_values + DecompositionAttributes.offcycle_values
    # new_vehicle_tech_flag_dict = dict()
    # tech_volumes_dict = dict()
    # for key in physical_effects_dict.keys():
    #     vehicle_id, calendar_year, age = key
    #     physical = physical_effects_dict[key]
    #
    #     tech_volumes_dict[key] = {'manufacturer_id': physical['manufacturer_id'],
    #                               'model_year': physical['model_year'],
    #                               'base_year_reg_class_id': physical['base_year_reg_class_id'],
    #                               'reg_class_id': physical['reg_class_id'],
    #                               'in_use_fuel_id': physical['in_use_fuel_id'],
    #                               'non_responsive_market_group': physical['non_responsive_market_group'],
    #                               'registered_count': physical['registered_count']
    #                               }
    #
    #     if vehicle_id not in new_vehicle_tech_flag_dict:
    #         new_vehicle_tech_flag_dict[vehicle_id] = dict()
    #         tech_flag_values = get_vehicle_info(vehicle_id, tech_flag_list)
    #         for idx, tech_flag in enumerate(tech_flag_list):
    #             new_vehicle_tech_flag_dict[vehicle_id].update({tech_flag: tech_flag_values[idx]})
    #
    #     for tech_flag, tech_flag_value in new_vehicle_tech_flag_dict[vehicle_id].items():
    #         if tech_flag == 'curb_weight':
    #             tech_volumes_dict[key].update({tech_flag: tech_flag_value})
    #             tech_volumes_dict[key].update({'fleet_pounds': tech_flag_value * physical['registered_count']})
    #         elif tech_flag == 'weight_reduction':
    #             tech_volumes_dict[key].update({tech_flag: tech_flag_value})
    #         else:
    #             tech_volumes_dict[key].update({tech_flag: tech_flag_value * physical['registered_count']})
    #
    # return tech_volumes_dict
