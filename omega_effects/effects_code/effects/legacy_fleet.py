"""

**Routines to load and access legacy fleet data for effects modeling**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent the legacy fleet that ages out as new vehicles enter the fleet.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,legacy_fleet,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        model_year,age,calendar_year,reg_class_id,body_style,market_class_id,in_use_fuel_id,registered_count,miles_per_gallon,horsepower,curbweight_lbs,fuel_capacity_gallons,kwh_per_mile,range_miles,transaction_price_dollars
        1981,39,2020,car,sedan,sedan_wagon.ICE,{'pump gasoline':1.0},7819790.332,21.41631,99,3076,15,,,24254.44782
        1982,38,2020,car,sedan,sedan_wagon.ICE,{'pump gasoline':1.0},7091909.547,22.21184,99,3053,16.1,,,25583.94377
        1983,37,2020,car,sedan,sedan_wagon.ICE,{'pump gasoline':1.0},7370905.119,22.09123,104,3112,15.9,,,26839.95207
        1984,36,2020,car,sedan,sedan_wagon.ICE,{'pump gasoline':1.0},10108067.31,22.4419,106,3101,15.2,,,26615.77742

Data Column Name and Description
    :model_year:
        The model year of vehicles represented by the data

    :age:
        The age of the vehicles represetned by the data

    :calendar_year:
        The calendar year for which the data apply

    :reg_class_id:
        The OMEGA reg_class_id (e.g., 'car', 'truck')

    :body_style:
        The OMEGA body_style (e.g., 'sedan', 'pickup')

    :market_class_id:
        The OMEGA market class id (e.g., 'sedan_wagon.BEV', 'pickup.ICE')

    :in_use_fuel_id:
        The OMEGA in use fuel id (e.g., 'pump gasoline', 'US electricity')

    :registered_count:
        The number of vehicles of the indicated model year sold as new (this is not the number of vehicles in the fleet
        in the indicated calendar year)

    :miles_per_gallon:
        The average 2-cycle fuel economy of the vehicles when sold as new

    :horsepower:
        The average horsepower of the vehicles when sold as new

    :curbweight_lbs:
        The average curb weight of the vehicles when sold as new

    :fuel_capacity_gallons:
        The average fuel capacity in gallons of the vehicles when sold as new

    :kwh_per_mile:
        The energy consumption in kilowatt hours of the vehicles when sold as new (electric-only)

    :range_miles:
        The range in miles of the vehicles when sold as new (electric only)

    :transaction_price_dollars:
        The average transaction price of the vehicles when sold as new

----

**CODE**

"""
import pandas as pd

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class LegacyFleet:
    """
    Legacy fleet class definition.

    """
    def __init__(self):
        """
        Loads and provides access to legacy fleet data by model year and age.

        """
        self._data = dict()  # private dict, the legacy_fleet_file data
        self._legacy_fleet = dict()  # the built legacy fleet for the analysis
        self.adjusted_legacy_fleet = dict()
        self.legacy_fleet_calendar_year_max = 0
        self.legacy_fleet_vehicle_id_start = pow(10, 6)

    def init_from_file(self, filepath, vehicles_base_year, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            vehicles_base_year (int): the model year of the input fleet - the legacy fleet
                calendar year will be adjusted
            if necessary for consistency with the analysis.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log)

        input_template_name = 'legacy_fleet'
        input_template_version = 0.1
        input_template_columns = [
            'model_year',
            'age',
            'calendar_year',
            'reg_class_id',
            'body_style',
            'market_class_id',
            'in_use_fuel_id',
            'registered_count',
            'miles_per_gallon',
            'horsepower',
            'curbweight_lbs',
            'fuel_capacity_gallons',
            'kwh_per_mile',
            'range_miles',
            'transaction_price_dollars',
        ]
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        df.fillna(0, inplace=True)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        # make adjustments to calendar year and model year for consistency with analysis_initial_year
        calendar_year_df = df['calendar_year'].unique()
        if len(calendar_year_df) > 1:
            effects_log.logwrite('\nLegacy fleet input file should have just one calendar year of data.')
        df['calendar_year'] = vehicles_base_year
        df['model_year'] = df['calendar_year'] - df['age']

        key = pd.Series(zip(
            df['age'],
            df['calendar_year'],
            df['reg_class_id'],
            df['market_class_id'],
            df['in_use_fuel_id'],
        ))
        # add attributes that are populated in build_legacy_fleet_for_analysis
        df.insert(0, 'vehicle_id', self.legacy_fleet_vehicle_id_start)
        df.insert(len(df.columns), 'annual_vmt', 0)
        df.insert(len(df.columns), 'odometer', 0)
        df.insert(len(df.columns), 'vmt', 0)
        self._data = df.set_index(key).to_dict(orient='index')

    def get_legacy_fleet_data(self, key, *args):
        """

        Args:
            key (tuple): the LegacyFleet._legacy_fleet key
            args (str, strs): name of attributes for which attribute values are sought

        Returns:
            A list of values associated with the key for each arg passed

        """
        return_values = list()
        for arg in args:
            return_values.append(self._legacy_fleet[key][arg])

        return return_values

    def update_legacy_fleet(self, key, update_dict):
        """

        Parameters:
            key: tuple; the LegacyFleet._legacy_fleet dict key
            update_dict: Dictionary; represents the attribute-value pairs to be updated

        Returns:
            Nothing, but updates the object dictionary with update_dict

        """
        if key in self._legacy_fleet:
            for attribute_name, attribute_value in update_dict.items():
                self._legacy_fleet[key][attribute_name] = attribute_value

        else:
            self._legacy_fleet.update({key: {}})
            for attribute_name, attribute_value in update_dict.items():
                self._legacy_fleet[key].update({attribute_name: attribute_value})

    def build_legacy_fleet_for_analysis(self, batch_settings):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.

        Returns:
            Nothing, but it builds and updates the instance dictionary.

        """

        vehicle_id_increment = 0
        for calendar_year in batch_settings.calendar_years:

            for key, nested_dict in self._data.items():

                last_age, last_calendar_year, reg_class_id, market_class_id, fuel_id = key
                model_year = nested_dict['model_year']
                new_age = calendar_year - model_year

                reregistered_proportion \
                    = batch_settings.reregistration.get_reregistered_proportion(model_year, market_class_id, new_age)
                new_registered_count = nested_dict['registered_count'] * reregistered_proportion
                if new_registered_count == 0 or new_age == 0:
                    pass

                else:
                    vehicle_id_increment += 1
                    annual_vmt = batch_settings.onroad_vmt.get_vmt(calendar_year, market_class_id, new_age)
                    if nested_dict['vehicle_id'] == self.legacy_fleet_vehicle_id_start:
                        self._data[key].update({'vehicle_id': nested_dict['vehicle_id'] + vehicle_id_increment})

                    update_dict = nested_dict.copy()
                    update_dict['age'] = new_age
                    update_dict['calendar_year'] = calendar_year
                    update_dict['registered_count'] = new_registered_count
                    update_dict['annual_vmt'] = annual_vmt
                    update_dict['odometer'] = batch_settings.onroad_vmt.get_cumulative_vmt(market_class_id, new_age)
                    update_dict['vmt'] = new_registered_count * annual_vmt
                    new_key = (update_dict['vehicle_id'], calendar_year, new_age)
                    self.update_legacy_fleet(new_key, update_dict)
                    self.legacy_fleet_calendar_year_max = max(self.legacy_fleet_calendar_year_max, calendar_year)

    def adjust_legacy_fleet_stock_and_vmt(self, batch_settings, vmt_adjustments_session):
        """

        Args:
            batch_settings: an instance of the BatchSettings class.
            vmt_adjustments_session: an instance of the AdjustmentsVMT class.

        Returns:
            The legacy fleet with adjusted VMT, registered count and odometer that adjust for context stock and VMT
            expectations.

        Note:
            There is no rebound VMT calculated for the legacy fleet.

        """
        self.adjusted_legacy_fleet = dict()

        calendar_years = batch_settings.calendar_years

        for key, nested_dict in self._legacy_fleet.items():

            vehicle_id, calendar_year, age = key

            registered_count = nested_dict['registered_count']

            # adjust vmt and legacy fleet stock
            calendar_year_vmt_adj = vmt_adjustments_session.get_vmt_adjustment(calendar_year)
            vmt_adjusted = nested_dict['vmt'] * calendar_year_vmt_adj

            calendar_year_stock_adj = vmt_adjustments_session.get_stock_adjustment(calendar_year)
            stock_adjusted = registered_count * calendar_year_stock_adj

            annual_vmt_adjusted = vmt_adjusted / stock_adjusted

            if nested_dict['calendar_year'] == calendar_years[0]:
                annual_vmt = nested_dict['annual_vmt']
                odometer = nested_dict['odometer']
                odometer_adjusted = odometer - annual_vmt + annual_vmt_adjusted
            else:
                odometer_last_year \
                    = self.adjusted_legacy_fleet[(vehicle_id, calendar_year - 1, age - 1)]['odometer']
                odometer_adjusted = odometer_last_year + annual_vmt_adjusted

            update_dict = {
                'age': age,
                'calendar_year': calendar_year,
                'registered_count': stock_adjusted,
                'context_vmt_adjustment': calendar_year_vmt_adj,
                'annual_vmt': annual_vmt_adjusted,
                'odometer': odometer_adjusted,
                'vmt': vmt_adjusted,
                'market_class_id': nested_dict['market_class_id'],
                'reg_class_id': nested_dict['reg_class_id'],
                'in_use_fuel_id': nested_dict['in_use_fuel_id'],
                'body_style': nested_dict['body_style'],
                'curbweight_lbs': nested_dict['curbweight_lbs'],
                'miles_per_gallon': nested_dict['miles_per_gallon'],
                'kwh_per_mile': nested_dict['kwh_per_mile'],
            }
            self.adjusted_legacy_fleet[key] = update_dict

            # else:
            #     legacy_fleet_extra_vehicles = \
            #         [k for k, v in self.adjusted_legacy_fleet.items() if k[1] == (calendar_year - 1)]
            #
            #     for key in legacy_fleet_extra_vehicles:
            #         vehicle_id, last_calendar_year, age_last_year = key
            #
            #         registered_count = self.adjusted_legacy_fleet[key]['registered_count']
            #
            #         # adjust vmt and legacy fleet stock
            #         calendar_year_vmt_adj = vmt_adjustments_session.get_vmt_adjustment(calendar_year)
            #         vmt_adjusted = self.adjusted_legacy_fleet[key]['vmt'] * calendar_year_vmt_adj
            #
            #         calendar_year_stock_adj = vmt_adjustments_session.get_stock_adjustment(calendar_year)
            #         stock_adjusted = registered_count * calendar_year_stock_adj
            #
            #         annual_vmt_adjusted = 0
            #         if stock_adjusted != 0:
            #             annual_vmt_adjusted = vmt_adjusted / stock_adjusted
            #
            #         odometer_last_year = self.adjusted_legacy_fleet[key]['odometer']
            #         odometer_adjusted = odometer_last_year + annual_vmt_adjusted
            #
            #         update_dict = {
            #             'age': age_last_year + 1,
            #             'calendar_year': calendar_year,
            #             'registered_count': stock_adjusted,
            #             'context_vmt_adjustment': calendar_year_vmt_adj,
            #             'annual_vmt': annual_vmt_adjusted,
            #             'odometer': odometer_adjusted,
            #             'vmt': vmt_adjusted,
            #             'market_class_id': self.adjusted_legacy_fleet[key]['market_class_id'],
            #             'reg_class_id': self.adjusted_legacy_fleet[key]['reg_class_id'],
            #             'in_use_fuel_id': self.adjusted_legacy_fleet[key]['in_use_fuel_id'],
            #             'body_style': self.adjusted_legacy_fleet[key]['body_style'],
            #             'curbweight_lbs': self.adjusted_legacy_fleet[key]['curbweight_lbs'],
            #         }
            #         key = vehicle_id, calendar_year, age_last_year + 1
            #         self.adjusted_legacy_fleet[key] = update_dict
