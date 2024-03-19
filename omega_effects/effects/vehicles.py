"""

**OMEGA effects vehicles module.**

----

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.consumer import deregionalizer


class Vehicles:
    """
    The Vehicles class reads the vehicles file resulting from the OMEGA compliance run for a given session and provides
    methods to access the data.

    """
    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log, index_col='vehicle_id')

        df = deregionalizer.deregionalize_entries(df, 'market_class_id', 'r1nonzev', 'r2zev')
        df = deregionalizer.deregionalize_entries(df, 'body_style', 'r1nonzev', 'r2zev')

        df = deregionalizer.clean_body_styles(df)

        self._dict = df.to_dict('index')

    def get_vehicle_attributes(self, vehicle_id, *attribute_names):
        """
        Get vehicle attributes by vehicle id and attribute name(s).

        Args:
            vehicle_id: the vehicle id
            *attribute_names (strs): attributes to retrieve

        Returns:
            Vehicle attributes by vehicle id and attribute name(s).

        """
        attribute_list = []
        for attribute_name in attribute_names:
            if attribute_name == 'onroad_engine_on_distance_frac':
                if 'onroad_engine_on_distance_frac' not in self._dict[vehicle_id]:
                    attribute_list.append(1)  # this allows running of nprm files using updated effects calcs
                else:
                    attribute_list.append(self._dict[vehicle_id][attribute_name])
            elif attribute_name == 'onroad_charge_depleting_range_mi':
                if 'onroad_charge_depleting_range_mi' not in self._dict[vehicle_id]:
                    attribute_list.append(self._dict[vehicle_id]['charge_depleting_range_mi'])  # again, for nprm files
                else:
                    attribute_list.append(self._dict[vehicle_id][attribute_name])
            else:
                attribute_list.append(self._dict[vehicle_id][attribute_name])
        if len(attribute_list) == 1:
            return attribute_list[0]

        return attribute_list
