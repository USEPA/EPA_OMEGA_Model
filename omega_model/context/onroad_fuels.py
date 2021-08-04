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

Template Header
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

print('importing %s' % __file__)

from omega_model import *

cache = dict()


class OnroadFuel(OMEGABase):
    """
    **Loads and provides methods to access onroad fuel attribute data.**

    """

    @staticmethod
    def get_fuel_attribute(calendar_year, fuel_id, attribute):
        """

        Args:
            calendar_year (numeric): year to get fuel properties in
            fuel_id (str): e.g. 'pump gasoline')
            attribute (str): name of attribute to retrieve

        Returns:
            Fuel attribute value for the given year.

        Example:

            ::

                carbon_intensity_gasoline =
                    OnroadFuel.get_fuel_attribute(2020, 'pump gasoline', 'direct_co2e_grams_per_unit')

        """
        start_years = cache[fuel_id]['start_year']
        year = max(start_years[start_years <= calendar_year])

        return cache[fuel_id][year][attribute]

    @staticmethod
    def validate_fuel_id(fuel_id):
        """
        Validate fuel ID

        Args:
            fuel_id (str): e.g. 'pump gasoline')

        Returns:
            True if the fuel ID is valid, False otherwise

        """
        return fuel_id in cache['fuel_id']

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'onroad-fuels'
        input_template_version = 0.1
        input_template_columns = {'fuel_id', 'start_year', 'unit', 'direct_co2e_grams_per_unit',
                                  'refuel_efficiency', 'transmission_efficiency'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                for _, r in df.iterrows():
                    if r.fuel_id not in cache:
                        cache[r.fuel_id] = {'start_year': np.array(df['start_year'].loc[df['fuel_id'] == r.fuel_id])}
                    cache[r.fuel_id][r.start_year] = r.drop('start_year').to_dict()

                cache['fuel_id'] = np.array(list(df['fuel_id'].unique()))

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        init_fail = []
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            print(OnroadFuel.validate_fuel_id('pump gasoline'))
            print(OnroadFuel.get_fuel_attribute(2020, 'pump gasoline', 'direct_co2e_grams_per_unit'))
        else:
            print(init_fail)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
