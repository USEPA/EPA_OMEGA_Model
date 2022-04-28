"""

Functions to track vehicle technology use.


----

**CODE**

"""
from omega_model import *


class TechTracking(OMEGABase):

    def __init__(self):

        self._data = dict()
        self.new_vehicle_tech_flag_dict = dict()
        self.tech_flag_list = list()
        self.id_attribute_list = ['name', 'manufacturer_id', 'model_year', 'base_year_reg_class_id', 'reg_class_id',
                                  'in_use_fuel_id', 'target_co2e_grams_per_mile']

    def create_dict(self, calendar_years):
        """

        Args:
            calendar_years: The calendar years for which to generate tech tracking data.

        Returns:
            Creates a dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the
            value is a dictionary of key, value pairs providing vehicle attributes (e.g., model_year, reg_class_id,
            in_use_fuel_id, etc.) and tech attributes (e.g., 'gdi', 'turb11', etc.) and their attribute values.

        """
        from producer.vehicle_annual_data import VehicleAnnualData
        from producer.vehicles import VehicleFinal
        from producer.vehicles import DecompositionAttributes

        self._data.clear()
        self.tech_flag_list = [item for item in DecompositionAttributes.other_values if
                               'cost' not in item] + DecompositionAttributes.offcycle_values

        new_vehicle_info_dict = dict()
        for calendar_year in calendar_years:
            vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)

            for vad in vads:
                vehicle_id, age, registered_count = vad['vehicle_id'], vad['age'], vad['registered_count']
                key = vehicle_id, int(calendar_year), int(age)

                if vehicle_id not in new_vehicle_info_dict:
                    new_vehicle_info_dict[vehicle_id] \
                        = VehicleFinal.get_vehicle_attributes(vehicle_id, self.id_attribute_list)

                name, mfr_id, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, \
                target_co2e_grams_per_mile \
                    = new_vehicle_info_dict[vehicle_id]

                if target_co2e_grams_per_mile is not None:
                    self._data[key] = {'session_name': omega_globals.options.session_name,
                                       'calendar_year': int(calendar_year),
                                       'model_year': model_year,
                                       'age': int(age),
                                       'name': name,
                                       'manufacturer_id': mfr_id,
                                       'base_year_reg_class_id': base_year_reg_class_id,
                                       'reg_class_id': reg_class_id,
                                       'in_use_fuel_id': in_use_fuel_id,
                                       'registered_count': registered_count,
                                       }
                    for tech_flag in self.tech_flag_list:
                        update_dict = dict()
                        if tech_flag == 'curb_weight':
                            update_dict.update({f'{tech_flag}': 0,
                                               'fleet_pounds': 0})
                        elif tech_flag == 'weight_reduction':
                            update_dict.update({f'{tech_flag}': 0})
                        else:
                            update_dict.update({f'{tech_flag}_share': 0,
                                                f'{tech_flag}_volume': 0})
                        self.add_attributes_and_values(key, update_dict)

                    self.get_tech_flags(key)
                    self.calc_volumes_and_weight_flags(key)

    def add_attributes_and_values(self, key, update_dict):
        """

        Args:
            key: Tuple; the class key.
            update_dict: Dictionary; the key, value pairs to add to the class dictionary.

        Returns:
            Updates the class dictionary with data from update_dict.

        """
        for k, v in update_dict.items():
            self._data[key].update({k: v})

    def get_tech_flags(self, key):
        """

        Args:
            key: Tuple; the class key.

        Returns:
            Updates the class dictionary with tech flag data from VehicleFinal.

        """
        from producer.vehicles import VehicleFinal

        vehicle_id, calendar_year, age = key

        update_dict = dict()
        if vehicle_id not in self.new_vehicle_tech_flag_dict:
            self.new_vehicle_tech_flag_dict[vehicle_id] = dict()
            tech_flag_values = VehicleFinal.get_vehicle_attributes(vehicle_id, self.tech_flag_list)
            for idx, tech_flag in enumerate(self.tech_flag_list):
                self.new_vehicle_tech_flag_dict[vehicle_id].update({tech_flag: tech_flag_values[idx]})

        for tech_flag, tech_flag_value in self.new_vehicle_tech_flag_dict[vehicle_id].items():
            if tech_flag_value is None:
                update_dict.update({f'{tech_flag}_share': tech_flag_value})
            elif tech_flag == 'curb_weight':
                update_dict.update({f'{tech_flag}': tech_flag_value})
            elif tech_flag == 'weight_reduction':
                update_dict.update({f'{tech_flag}': tech_flag_value})
            else:
                update_dict.update({f'{tech_flag}_share': tech_flag_value})
        self.add_attributes_and_values(key, update_dict)

    def get_attribute_value(self, key, attribute_name):
        """

        Args:
            key: Tuple; the class key.
            attribute_name: String; the attribute name for which the value is sought.

        Returns:
            The value associated with attribute_name.

        """
        return self._data[key][attribute_name]

    def calc_volumes_and_weight_flags(self, key):
        """

        Args:
            key: Tuple; the class key.

        Returns:
            Updates the class dictionary with volume and weight, if applicable, data.

        """
        vehicle_id, calendar_year, age = key
        registered_count = self.get_attribute_value(key, 'registered_count')
        update_dict = dict()
        for tech_flag, tech_flag_value in self.new_vehicle_tech_flag_dict[vehicle_id].items():
            if tech_flag_value is None:
                update_dict.update({f'{tech_flag}_volume': tech_flag_value})
            elif tech_flag == 'curb_weight':
                # update_dict.update({tech_flag: tech_flag_value})
                update_dict.update({'fleet_pounds': tech_flag_value * registered_count})
            elif tech_flag == 'weight_reduction':
                pass
            else:
                update_dict.update({f'{tech_flag}_volume': tech_flag_value * registered_count})
        self.add_attributes_and_values(key, update_dict)



# def calc_tech_tracking(calendar_years):
# 
#     """
# 
#     Args:
#         calendar_years: The calendar years for which to generate tech tracking data.
# 
#     Returns:
#         A dictionary of key, value pairs where the key is a tuple (vehicle_id, calendar_year, age) and the value is a dictionary of key, value pairs providing
#         vehicle attributes (e.g., model_year, reg_class_id, in_use_fuel_id, etc.) and tech attributes (e.g., 'gdi', 'turb11', etc.) and their attribute values.
# 
#     """
#     from producer.vehicle_annual_data import VehicleAnnualData
#     from producer.vehicles import VehicleFinal
#     from producer.vehicles import DecompositionAttributes
# 
#     tech_flag_list = DecompositionAttributes.other_values + DecompositionAttributes.offcycle_values
#     id_attribute_list = ['name', 'manufacturer_id', 'model_year', 'base_year_reg_class_id', 'reg_class_id',
#                          'in_use_fuel_id', 'target_co2e_grams_per_mile']
# 
#     new_vehicle_info_dict = dict()
#     new_vehicle_tech_flag_dict = dict()
#     tech_tracking_dict = dict()
#     for calendar_year in calendar_years:
#         vads = VehicleAnnualData.get_vehicle_annual_data(calendar_year)
# 
#         for vad in vads:
# 
#             vehicle_id, age, registered_count = vad['vehicle_id'], vad['age'], vad['registered_count']
#             key = vehicle_id, int(calendar_year), int(age)
# 
#             if vehicle_id not in new_vehicle_info_dict:
#                 new_vehicle_info_dict[vehicle_id] = VehicleFinal.get_vehicle_attributes(vehicle_id, id_attribute_list)
# 
#             name, mfr_id, model_year, base_year_reg_class_id, reg_class_id, in_use_fuel_id, \
#             target_co2e_grams_per_mile \
#                 = new_vehicle_info_dict[vehicle_id]
# 
#             if target_co2e_grams_per_mile is not None:
# 
#                 tech_tracking_dict[key] = {'session_name': omega_globals.options.session_name,
#                                            'calendar_year': int(calendar_year),
#                                            'model_year': model_year,
#                                            'age': int(age),
#                                            'name': name,
#                                            'manufacturer_id': mfr_id,
#                                            'base_year_reg_class_id': base_year_reg_class_id,
#                                            'reg_class_id': reg_class_id,
#                                            'in_use_fuel_id': in_use_fuel_id,
#                                            'registered_count': registered_count,
#                                            }
# 
#                 if vehicle_id not in new_vehicle_tech_flag_dict:
#                     new_vehicle_tech_flag_dict[vehicle_id] = dict()
#                     tech_flag_values = VehicleFinal.get_vehicle_attributes(vehicle_id, tech_flag_list)
#                     for idx, tech_flag in enumerate(tech_flag_list):
#                         new_vehicle_tech_flag_dict[vehicle_id].update({tech_flag: tech_flag_values[idx]})
# 
#                 # calc volumes and weight flags
#                 for tech_flag, tech_flag_value in new_vehicle_tech_flag_dict[vehicle_id].items():
#                     if tech_flag_value is None:
#                         tech_tracking_dict[key].update({f'{tech_flag}_volume': tech_flag_value})
#                     elif tech_flag == 'curb_weight':
#                         tech_tracking_dict[key].update({tech_flag: tech_flag_value})
#                         tech_tracking_dict[key].update({'fleet_pounds': tech_flag_value * registered_count})
#                     elif tech_flag == 'weight_reduction':
#                         tech_tracking_dict[key].update({tech_flag: tech_flag_value})
#                     else:
#                         tech_tracking_dict[key].update({f'{tech_flag}_volume': tech_flag_value * registered_count})
# 
#                 # calc shares
#                 for tech_flag, tech_flag_value in new_vehicle_tech_flag_dict[vehicle_id].items():
#                     if tech_flag_value is None:
#                         tech_tracking_dict[key].update({f'{tech_flag}_share': tech_flag_value})
#                     elif tech_flag == 'curb_weight':
#                         pass
#                     elif tech_flag == 'weight_reduction':
#                         pass
#                     else:
#                         tech_tracking_dict[key].update({f'{tech_flag}_share': tech_flag_value})
#                     
#     return tech_tracking_dict
