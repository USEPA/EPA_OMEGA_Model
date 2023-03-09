from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.consumer import deregionalizer


class Vehicles:

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
        df = read_input_file(filepath, effects_log, index_col=0)

        df = deregionalizer.deregionalize_entries(df, 'market_class_id', 'r1nonzev', 'r2zev')
        df = deregionalizer.deregionalize_entries(df, 'body_style', 'r1nonzev', 'r2zev')

        df = deregionalizer.clean_body_styles(df)

        self._dict = df.to_dict('index')

    def get_vehicle_attributes(self, vehicle_id, *attribute_names):

        attribute_list = list()
        for attribute_name in attribute_names:
            attribute_list.append(self._dict[vehicle_id][attribute_name])
        if len(attribute_list) == 1:
            return attribute_list[0]

        return attribute_list


