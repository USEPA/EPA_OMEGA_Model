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

print('importing %s' % __file__)

from omega_model import *


class OnroadFuel(OMEGABase):
    """
    **Loads and provides methods to access onroad fuel attribute data.**

    """

    _data = dict()  # private dict, in-use fuel properties

    fuel_ids = []  # list of known fuel ids

    # RV
    kilowatt_hours_per_gallon = 33.7  # for MPGe calcs from kWh/mi ...
    grams_co2e_per_gallon = 8887  # for MPG calcs from gCO2e/mi

    @staticmethod
    def get_fuel_attribute(calendar_year, in_use_fuel_id, attribute):
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

        if cache_key not in OnroadFuel._data:
            start_years = np.atleast_1d(OnroadFuel._data['start_year'][in_use_fuel_id])
            if len(start_years[start_years <= calendar_year]) > 0:
                year = max([yr for yr in start_years if yr <= calendar_year])

                OnroadFuel._data[cache_key] = OnroadFuel._data[in_use_fuel_id, year][attribute]
            else:
                raise Exception('Missing policy fuel values for %s, %d or prior' % (in_use_fuel_id, calendar_year))

        return OnroadFuel._data[cache_key]

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
        OnroadFuel._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'onroad-fuels'
        input_template_version = 0.1
        input_template_columns = {'fuel_id', 'start_year', 'unit', 'direct_co2e_grams_per_unit',
                                  'refuel_efficiency', 'transmission_efficiency'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'unit': ['gallon', 'kWh']}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            OnroadFuel._data = df.set_index(['fuel_id', 'start_year']).to_dict(orient='index')
            OnroadFuel._data.update(df[['start_year', 'fuel_id']].set_index('fuel_id').to_dict(orient='series'))
            OnroadFuel.fuel_ids = df['fuel_id'].unique()

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += \
            OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            print(OnroadFuel.get_fuel_attribute(2020, 'pump gasoline', 'direct_co2e_grams_per_unit'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
