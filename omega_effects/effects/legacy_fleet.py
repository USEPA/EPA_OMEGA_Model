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
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class LegacyFleet:
    """
    Legacy fleet class definition.

    """
    def __init__(self):
        """
        Loads and provides access to legacy fleet data by model year and age.

        """
        self._data = {}  # the legacy_fleet_file data
        self._legacy_fleet = {}  # the built legacy fleet for the analysis
        self.adjusted_legacy_fleet = {}
        self.legacy_fleet_calendar_year_max = 0
        self.legacy_fleet_vehicle_id_start = pow(10, 6)

    def init_from_file(self, filepath, vehicles_base_year, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            vehicles_base_year (int): the model year of the input fleet - the legacy fleet calendar year will be
            adjusted if necessary for consistency with the analysis.
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
            'curbweight_lbs',
            'kwh_per_mile',
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

        # add attributes that are populated in build_legacy_fleet_for_analysis
        df.insert(0, 'vehicle_id', self.legacy_fleet_vehicle_id_start)
        df.insert(len(df.columns), 'annual_vmt', 0)
        df.insert(len(df.columns), 'odometer', 0)
        df.insert(len(df.columns), 'vmt', 0)
        self._data = df.to_dict(orient='index')

    def update_legacy_fleet(self, vehicle_id, calendar_year, update_dict):
        """

        Parameters:
            vehicle_id (int): the vehicle_id.
            calendar_year (int): the calendar year.
            update_dict: Dictionary; represents the attribute-value pairs to be updated.

        Returns:
            Nothing, but updates the object dictionary with update_dict

        """
        key = (vehicle_id, calendar_year)
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

            for k, v in self._data.items():

                last_age, last_calendar_year, model_year = v['age'], v['calendar_year'], v['model_year']
                reg_class_id, market_class_id, fuel_id = v['reg_class_id'], v['market_class_id'], v['in_use_fuel_id']
                new_age = calendar_year - model_year

                reregistered_proportion \
                    = batch_settings.reregistration.get_reregistered_proportion(model_year, market_class_id, new_age)
                new_registered_count = v['registered_count'] * reregistered_proportion
                if new_registered_count == 0 or new_age == 0:
                    pass

                else:
                    vehicle_id_increment += 1
                    annual_vmt = batch_settings.onroad_vmt.get_vmt(calendar_year, market_class_id, new_age)
                    if v['vehicle_id'] == self.legacy_fleet_vehicle_id_start:
                        self._data[k].update({'vehicle_id': v['vehicle_id'] + vehicle_id_increment})

                    update_dict = v.copy()
                    update_dict['age'] = new_age
                    update_dict['calendar_year'] = calendar_year
                    update_dict['registered_count'] = new_registered_count
                    update_dict['annual_vmt'] = annual_vmt
                    update_dict['odometer'] = batch_settings.onroad_vmt.get_cumulative_vmt(market_class_id, new_age)
                    update_dict['vmt'] = new_registered_count * annual_vmt

                    self.update_legacy_fleet(update_dict['vehicle_id'], calendar_year, update_dict)
                    self.legacy_fleet_calendar_year_max = max(self.legacy_fleet_calendar_year_max, calendar_year)

    def get_legacy_fleet_price(self, vehicle_id, calendar_year):
        """

        Args:
            vehicle_id (int): the vehicle id.
            calendar_year (int): the calendar year.

        Returns:

        """
        price = [v['transaction_price_dollars'] for v in self._legacy_fleet.values()
                 if v['vehicle_id'] == vehicle_id
                 and v['calendar_year'] == calendar_year][0]

        return price

    def get_adjusted_legacy_fleet_odometer(self, vehicle_id, calendar_year):
        """

        Args:
            vehicle_id (int): the vehicle_id number.
            calendar_year (int): the calendar year for which the vehicle's odometer value is sought.

        Returns:

        """
        odometer = [v['odometer'] for v in self.adjusted_legacy_fleet.values()
                    if v['vehicle_id'] == vehicle_id
                    and v['calendar_year'] == calendar_year][0]

        return odometer

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
        for v in self._legacy_fleet.values():

            # adjust vmt and legacy fleet stock
            context_vmt_adjustment = vmt_adjustments_session.get_vmt_adjustment(v['calendar_year'])
            vmt_adjusted = v['vmt'] * context_vmt_adjustment

            context_stock_adj = vmt_adjustments_session.get_stock_adjustment(v['calendar_year'])
            adjusted_registered_count = v['registered_count'] * context_stock_adj

            annual_vmt_adjusted = vmt_adjusted / adjusted_registered_count

            if v['calendar_year'] == batch_settings.analysis_initial_year:
                annual_vmt = v['annual_vmt']
                odometer = v['odometer']
                odometer_adjusted = odometer - annual_vmt + annual_vmt_adjusted
            else:
                odometer_last_year = self.get_adjusted_legacy_fleet_odometer(v['vehicle_id'], v['calendar_year'] - 1)
                odometer_adjusted = odometer_last_year + annual_vmt_adjusted

            update_dict = {
                'vehicle_id': v['vehicle_id'],
                'age': v['age'],
                'calendar_year': v['calendar_year'],
                'registered_count': adjusted_registered_count,
                'context_vmt_adjustment': context_vmt_adjustment,
                'annual_vmt': annual_vmt_adjusted,
                'odometer': odometer_adjusted,
                'vmt': vmt_adjusted,
                'market_class_id': v['market_class_id'],
                'reg_class_id': v['reg_class_id'],
                'in_use_fuel_id': v['in_use_fuel_id'],
                'body_style': v['body_style'],
                'curbweight_lbs': v['curbweight_lbs'],
                'miles_per_gallon': v['miles_per_gallon'],
                'kwh_per_mile': v['kwh_per_mile'],
            }
            self.adjusted_legacy_fleet[(v['vehicle_id'], v['calendar_year'])] = update_dict

    @staticmethod
    def set_legacy_fleet_name(vehicle_id, market_class_id, fueling_class):
        """

        Args:
            vehicle_id (int): the vehicle id number
            market_class_id (str): the legacy fleet market class id
            fueling_class (str): 'BEV', 'ICE', 'PHEV'

        Returns:
            A name for the vehicle primarily for use in cost_effects, repair cost calculations which looks for
            'car' or 'Pickup' in the name attribute

        Note:
            This method is called in safety_effects.calc_legacy_fleet_safety_effects

        """
        if 'sedan' in market_class_id:
            _name = f'car:{fueling_class}:{vehicle_id}'
        elif 'pickup' in market_class_id:
            _name = f'Pickup:{fueling_class}:{vehicle_id}'
        else:
            _name = f'cuv_suv:{fueling_class}:{vehicle_id}'

        return _name
