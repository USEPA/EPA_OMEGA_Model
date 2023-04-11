"""

**Routines to load and retrieve onroad (in-use) fuel attribute data**

Fuel data includes a name, units (e.g. gallons, kWh), CO2e g/unit, refuel_efficiency and transmission_efficiency.

See Also:

    ``vehicles`` and ``context_fuel_prices`` modules, and ``consumer`` subpackage

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents fuel property data for on-road/in-use purposes.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,onroad-fuels,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        fuel_id,start_year,unit,direct_co2e_grams_per_unit,refuel_efficiency,transmission_efficiency
        pump gasoline,2020,gallon,8887,1,1
        US electricity,2020,kWh,0,0.9,0.935

Data Column Name and Description

:fuel_id:
    The Fuel ID, as referenced by the ``vehicles`` and ``context_fuel_prices`` modules, and ``consumer`` subpackage.

:start_year:
    Start year of fuel properties, properties apply until the next available start year

:unit:
    Fuel unit, e.g. 'gallon', 'kWh'

:direct_co2e_grams_per_unit:
    CO2e emissions per unit when consumed

:refuel_efficiency:
    Refuel efficiency [0..1], e.g. electrical vehicle charging efficiency

:transmission_efficiency:
    Fuel transmission efficiency [0..1], e.g. electrical grid efficiency, may also be referred to as "grid loss"

----

**CODE**

"""
import numpy as np

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class OnroadFuel:
    """
    **Loads and provides methods to access onroad fuel attribute data.**

    """
    def __init__(self):
        self._data = dict()  # private dict, in-use fuel properties
        self.fuel_ids = []  # list of known fuel ids

        # RV
        self.kilowatt_hours_per_gallon = 33.7  # for MPGe calcs from kWh/mi ...
        self.grams_co2e_per_gallon = 8887  # for MPG calcs from gCO2e/mi

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        df = read_input_file(filepath, effects_log)

        input_template_name = 'onroad-fuels'
        input_template_version = 0.1
        input_template_columns = {
            'fuel_id',
            'start_year',
            'unit',
            'direct_co2e_grams_per_unit',
            'refuel_efficiency',
            'transmission_efficiency',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index(['fuel_id', 'start_year']).to_dict(orient='index')
        self._data.update(df[['start_year', 'fuel_id']].set_index('fuel_id').to_dict(orient='series'))
        self.fuel_ids = df['fuel_id'].unique()

    def get_fuel_attribute(self, calendar_year, in_use_fuel_id, attribute):
        """

        Args:
            calendar_year (numeric): year to get fuel properties in
            in_use_fuel_id (str): e.g. 'pump gasoline')
            attribute (str): name of attribute to retrieve

        Returns:
            Fuel attribute value for the given year.

        Example:

            ::

                carbon_intensity_gasoline =
                    OnroadFuel.get_fuel_attribute(2020, 'pump gasoline', 'direct_co2e_grams_per_unit')

        """
        cache_key = (calendar_year, in_use_fuel_id, attribute)

        if cache_key not in self._data:
            start_years = np.atleast_1d(self._data['start_year'][in_use_fuel_id])
            if len(start_years[start_years <= calendar_year]) > 0:
                year = max([yr for yr in start_years if yr <= calendar_year])

                self._data[cache_key] = self._data[in_use_fuel_id, year][attribute]
            else:
                raise Exception('Missing policy fuel values for %s, %d or prior' % (in_use_fuel_id, calendar_year))

        return self._data[cache_key]
