"""

**Routines to load and provide access to policy-defined fuel attributes.**

The primary fuel attributes are CO2e grams per unit (i.e. g/gallon, g/kWh) when consumed, by policy year.


----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents fuel property data for compliance purposes, by policy year.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,policy-fuels,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        fuel_id,start_year,unit,direct_co2e_grams_per_unit,upstream_co2e_grams_per_unit,transmission_efficiency
        electricity,2020,kWh,0,534,0.935
        gasoline,2020,gallon,8887,2478,0
        diesel,2020,gallon,10180,2839,0

Data Column Name and Description

:fuel_id:
    The Fuel ID, as referenced by the ``policy_fuel_upstream`` module.

:start_year:
    Start year of fuel properties, properties apply until the next available start year

:unit:
    Fuel unit, e.g. 'gallon', 'kWh'

:direct_co2e_grams_per_unit:
    CO2e emissions per unit when consumed

:upstream_co2e_grams_per_unit:
    Upstream CO2e emissions per unit when consumed

:transmission_efficiency:
    Fuel transmission efficiency [0..1], e.g. electrical grid efficiency, may also be referred to as "grid loss"

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class PolicyFuel(OMEGABase):
    """
    **Loads and provides methods to access onroad fuel attribute data.**

    """

    _data = dict()  # private dict, policy fuel properties

    fuel_ids = []  # list of known fuel ids

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
                    PolicyFuel.get_fuel_attribute(2020, 'pump gasoline', 'direct_co2e_grams_per_unit')

        """
        cache_key = (calendar_year, fuel_id, attribute)

        if cache_key not in PolicyFuel._data:
            start_years = np.atleast_1d(PolicyFuel._data['start_year'][fuel_id])
            if len(start_years[start_years <= calendar_year]) > 0:
                year = max([yr for yr in start_years if yr <= calendar_year])

                PolicyFuel._data[cache_key] = PolicyFuel._data[fuel_id, year][attribute]
            else:
                raise Exception('Missing policy fuel values for %s, %d or prior' % (fuel_id, calendar_year))

        return PolicyFuel._data[cache_key]

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
        PolicyFuel._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'policy-fuels'
        input_template_version = 0.1
        input_template_columns = {'fuel_id', 'start_year', 'unit', 'direct_co2e_grams_per_unit',
                                  'upstream_co2e_grams_per_unit', 'transmission_efficiency'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'unit': ['gallon', 'kWh', 'kg']}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            PolicyFuel._data = df.set_index(['fuel_id', 'start_year']).to_dict(orient='index')
            PolicyFuel._data.update(df[['start_year', 'fuel_id']].set_index('fuel_id').to_dict(orient='series'))
            PolicyFuel.fuel_ids = df['fuel_id'].unique()

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
        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=omega_globals.options.verbose)

        if not init_fail:
            print(PolicyFuel.get_fuel_attribute(2020, 'gasoline', 'direct_co2e_grams_per_unit'))
            print(PolicyFuel.get_fuel_attribute(2020, 'electricity', 'transmission_efficiency'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
