import pandas as pd

from omega_effects_module.effects_code.general.general_functions import read_input_file


class VehicleAnnualData:

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

        key = pd.Series(zip(
            df['vehicle_id'],
            df['calendar_year']
        ))
        df.set_index(key, inplace=True)

        self._dict = df.to_dict('index')

    def get_vehicle_annual_data_by_calendar_year(self, calendar_year):

        return [v for k, v in self._dict.items() if k[1] == calendar_year]

    def get_vehicle_annual_data_by_vehicle_id(self, calendar_year, vehicle_id, *attribute_names):

        attribute_list = list()
        for attribute_name in attribute_names:
            attribute_list.append(self._dict[(vehicle_id, calendar_year)][attribute_name])
        if len(attribute_list) == 1:
            return attribute_list[0]

        return attribute_list


