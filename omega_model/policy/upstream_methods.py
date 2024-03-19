"""

**Routines to load and apply upstream calculation methods.**

Upstream calculation methods calculate cert CO2e g/mi from kWh/mi.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the calculation method(s) to apply by start year.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,policy_fuel_upstream_methods,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,upstream_calculation_method
        2020,upstream_xev_ice_delta
        2025,upstream_actual

Data Column Name and Description

:start_year:
    Start year of the upstream calculation method, method applies until the next available start year

:upstream_calculation_method:
    The name of the function to call within ``upstream_methods.py``

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
from policy.policy_fuels import PolicyFuel


def upstream_zero(vehicle, co2_grams_per_mile, kwh_per_mile):
    """
    Calculate upstream cert emissions under a "zero-upstream" policy.

    Args:
        vehicle (Vehicle): *unused*
        co2_grams_per_mile (numeric value or array-like): *unused*
        kwh_per_mile (numeric value or array-like): *unused*

    Returns:
        Returns ``0``

    """
    return 0


def upstream_xev_ice_delta(vehicle, co2_grams_per_mile, kwh_per_mile):
    """
    Calculate upstream cert emissions based on cert direct kWh/mi relative to an ICE vehicle with the same target
    emissions.  Upstream emissions cannot be negative.

    upstream_co2e_g/mi = max(0, kwh_per_mile * upstream_gco2_per_kwh / upstream_efficiency -
    vehicle.target_co2e_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal)

    Args:
        vehicle (Vehicle): The vehicle to calculate upstream emissions for
        co2_grams_per_mile (numeric value or array-like): vehicle cert direct CO2e g/mi
        kwh_per_mile (numeric value or array-like): vehicle cert direct kWh/mi

    Returns:
        Upstream cert emissions based on kWh/mi relative to an ICE vehicle with the same target emissions

    """
    if vehicle.fueling_class == 'BEV':
        upstream_gco2_per_kwh = \
            PolicyFuel.get_fuel_attribute(vehicle.model_year, 'electricity', 'upstream_co2e_grams_per_unit')

        upstream_efficiency = \
            PolicyFuel.get_fuel_attribute(vehicle.model_year, 'electricity', 'transmission_efficiency')

        upstream_gco2_per_gal = \
            PolicyFuel.get_fuel_attribute(vehicle.model_year, 'gasoline', 'upstream_co2e_grams_per_unit')

        fuel_gco2_per_gal = \
            PolicyFuel.get_fuel_attribute(vehicle.model_year, 'gasoline', 'direct_co2e_grams_per_unit')

        upstream = np.maximum(0, kwh_per_mile * upstream_gco2_per_kwh / upstream_efficiency -
                              vehicle.target_co2e_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal)
    else:
        upstream = 0

    return upstream


def upstream_actual(vehicle, co2_grams_per_mile, kwh_per_mile):
    """
    Calculate upstream cert emissions based on cert direct kWh/mi and CO2e g/mi.

    upstream_co2e_g/mi = kwh_per_mile * upstream_gco2_per_kwh / upstream_efficiency +
    co2_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal

    Args:
        vehicle (Vehicle): The vehicle to calculate upstream emissions for
        co2_grams_per_mile (numeric value or array-like): vehicle cert direct CO2e g/mi
        kwh_per_mile (numeric value or array-like): vehicle cert direct kWh/mi

    Returns:
        Upstream cert emissions based on cert direct kWh/mi and CO2e g/mi

    """
    upstream_gco2_per_kwh = \
        PolicyFuel.get_fuel_attribute(vehicle.model_year, 'electricity', 'upstream_co2e_grams_per_unit')

    upstream_efficiency = \
        PolicyFuel.get_fuel_attribute(vehicle.model_year, 'electricity', 'transmission_efficiency')

    upstream_gco2_per_gal = \
        PolicyFuel.get_fuel_attribute(vehicle.model_year, 'gasoline', 'upstream_co2e_grams_per_unit')

    fuel_gco2_per_gal = \
        PolicyFuel.get_fuel_attribute(vehicle.model_year, 'gasoline', 'direct_co2e_grams_per_unit')

    # TODO: need "utility factor" or percentage of electric and gas miles to weight these terms
    upstream = kwh_per_mile * upstream_gco2_per_kwh / upstream_efficiency + \
               co2_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal

    return upstream


upstream_method_dict = {'upstream_zero': upstream_zero, 'upstream_xev_ice_delta': upstream_xev_ice_delta,
                        'upstream_actual': upstream_actual}


class UpstreamMethods(OMEGABase):
    """
    **Loads and provides access to upstream calculation methods by start year.**

    """

    _data = pd.DataFrame()  # private Dataframe, upstream methods by start year

    _cache = dict()

    @staticmethod
    def get_upstream_method(calendar_year):
        """
        Get the cert upstream calculation function for the given calendar year.

        Args:
            calendar_year (int): the calendar year to get the function for

        Returns:
            A callable python function used to calculate upstream cert emissions for the given calendar year

        """

        cache_key = calendar_year

        if cache_key not in UpstreamMethods._cache:

            start_years = np.atleast_1d(UpstreamMethods._data['start_year'])
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                method = UpstreamMethods._data['upstream_calculation_method'].loc[
                    UpstreamMethods._data['start_year'] == calendar_year].item()

                UpstreamMethods._cache[cache_key] = upstream_method_dict[method]
            else:
                raise Exception('Missing upstream calculation method for %d or prior' % calendar_year)

        return UpstreamMethods._cache[cache_key]

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
        import pandas as pd

        UpstreamMethods._data = pd.DataFrame()

        UpstreamMethods._cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_fuel_upstream_methods'
        input_template_version = 0.2
        input_template_columns = {'start_year', 'upstream_calculation_method'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                UpstreamMethods._data = df

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from context.onroad_fuels import OnroadFuel

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += UpstreamMethods.init_from_file(omega_globals.options.fuel_upstream_methods_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.output_folder)
            UpstreamMethods._data.to_csv(
                omega_globals.options.output_folder + os.sep + 'policy_fuel_upstream_values.csv', index=False)

            print(UpstreamMethods.get_upstream_method(2020))
            print(UpstreamMethods.get_upstream_method(2027))
            print(UpstreamMethods.get_upstream_method(2050))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
