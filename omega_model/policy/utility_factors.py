"""

**Routines to load and apply utility factor calculation methods.**

Calculate utility factor based on PHEV charge-depleting range

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
from common.omega_functions import ASTM_round


def labelUF(miles, norm_dist=400):
    """
    Calculate "label" PHEV individual vehicle utility factor, from SAEJ2841 SEP2010.
    https://www.sae.org/standards/content/j2841_201009/

    Args:
        miles: distance travelled in charge-depleting driving, scalar or pandas Series
        norm_dist: distance normalizing denominator in miles

    Returns:
        Utility factor from SAEJ2841 SEP2010, Table 2 (Multi-day utility factor Fit)

    """
    miles_norm = min(2.0, miles/norm_dist)

    return ASTM_round(1-np.exp(-(
                        1.31e+01 * miles_norm +
                        -1.87e+01 * miles_norm ** 2 +
                        5.22e+00 * miles_norm ** 3 +
                        8.15e+00 * miles_norm ** 4 +
                        3.53e+00 * miles_norm ** 5 +
                        -1.34e+00 * miles_norm ** 6 +
                        -4.01e+00 * miles_norm ** 7 +
                        -3.90e+00 * miles_norm ** 8 +
                        -1.15e+00 * miles_norm ** 9 +
                        3.88e+00 * miles_norm ** 10
    )), 3)


def cityFUF(miles, norm_dist=399):
    """
    Calculate "city" PHEV fleet utility factor, from SAEJ2841 SEP2010.
    https://www.sae.org/standards/content/j2841_201009/

    Args:
        miles: distance travelled in "city" charge-depleting driving, scalar or pandas Series
        norm_dist: distance normalizing denominator in miles

    Returns:
        City utility factor from SAEJ2841 SEP2010, Table 5 (55/45 city/highway split)

    """
    miles_norm = min(2.0, miles/norm_dist)

    return ASTM_round(1-np.exp(-(
                        1.486e+01 * miles_norm +
                        2.965e+00 * miles_norm ** 2 +
                        -8.405e+01 * miles_norm ** 3 +
                        1.537e+02 * miles_norm ** 4 +
                        -4.359e+01 * miles_norm ** 5 +
                        -9.694e+01 * miles_norm ** 6 +
                        1.447e+01 * miles_norm ** 7 +
                        9.170e+01 * miles_norm ** 8 +
                        -4.636e+01 * miles_norm ** 9
    )), 3)


def highwayFUF(miles, norm_dist=399):
    """
    Calculate "highway" PHEV fleet utility factor, from SAEJ2841 SEP2010.
    https://www.sae.org/standards/content/j2841_201009/

    Args:
        miles: distance travelled in "highway" charge-depleting driving, scalar or pandas Series
        norm_dist: distance normalizing denominator in miles

    Returns:
        Highway utility factor from SAEJ2841 SEP2010, Table 5 (55/45 city/highway split)

    """
    miles_norm = min(2.0, miles/norm_dist)

    return ASTM_round(1-np.exp(-(
                        4.8e+00 * miles_norm +
                        1.3e+01 * miles_norm ** 2 +
                        -6.5e+01 * miles_norm ** 3 +
                        1.2e+02 * miles_norm ** 4 +
                        -1.0e+02 * miles_norm ** 5 +
                        3.1e+01 * miles_norm ** 6
    )), 3)


def FUF(miles, norm_dist=399):
    """
    Calculate PHEV fleet utility factor, from SAEJ2841 SEP2010.
    https://www.sae.org/standards/content/j2841_201009/

    Args:
        miles: distance travelled in charge-depleting driving, scalar or pandas Series
        norm_dist: distance normalizing denominator in miles

    Returns:
        Fleet Utility Factor from SAEJ2841 SEP2010, Table 2

    """
    miles_norm = min(2.0, miles/norm_dist)

    return ASTM_round(1-np.exp(-(
                        10.52 * miles_norm +
                        -7.282 * miles_norm ** 2 +
                        -26.37 * miles_norm ** 3 +
                        79.08 * miles_norm ** 4 +
                        -77.36 * miles_norm ** 5 +
                        26.07 * miles_norm ** 6
    )), 3)


utility_factor_methods_dict = {'cityFUF': cityFUF, 'highwayFUF': highwayFUF, 'FUF': FUF, 'labelUF': labelUF}


class UtilityFactorMethods(OMEGABase):
    """
    **Loads and provides access to upstream calculation methods by start year.**

    """

    _data = pd.DataFrame()  # private Dataframe, upstream methods by start year

    _cache = dict()

    @staticmethod
    def calc_city_utility_factor(calendar_year, miles):
        """
        Calculate "city" PHEV fleet utility factor

        Args:
            calendar_year (int): the calendar year to get the function for
            miles: distance travelled in charge-depleting driving, scalar or pandas Series

        Returns:
            A callable python function used to calculate upstream cert emissions for the given calendar year

        """

        cache_key = str(calendar_year)

        if cache_key not in UtilityFactorMethods._cache:

            start_years = np.atleast_1d(UtilityFactorMethods._data['start_year'])
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                method = UtilityFactorMethods._data['city_method'].loc[
                    UtilityFactorMethods._data['start_year'] == calendar_year].item()

                norm_dist = UtilityFactorMethods._data['city_norm_dist'].loc[
                    UtilityFactorMethods._data['start_year'] == calendar_year].item()

                UtilityFactorMethods._cache[cache_key + '_method'] = utility_factor_methods_dict[method]
                UtilityFactorMethods._cache[cache_key + '_norm_dist'] = norm_dist
            else:
                raise Exception('Missing utility factor calculation method for %d or prior' % calendar_year)

        method = UtilityFactorMethods._cache[cache_key + '_method']
        norm_dist = UtilityFactorMethods._cache[cache_key + '_norm_dist']

        try:
            return method(miles, norm_dist)
        except:
            # extreme cases may blow up, return 0 for now
            return 0

    @staticmethod
    def calc_highway_utility_factor(calendar_year, miles):
        """
        Calculate "highway" PHEV fleet utility factor

        Args:
            calendar_year (int): the calendar year to get the function for
            miles: distance travelled in charge-depleting driving, scalar or pandas Series

        Returns:
            A callable python function used to calculate upstream cert emissions for the given calendar year

        """

        cache_key = str(calendar_year)

        if cache_key not in UtilityFactorMethods._cache:

            start_years = np.atleast_1d(UtilityFactorMethods._data['start_year'])
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                method = UtilityFactorMethods._data['highway_method'].loc[
                    UtilityFactorMethods._data['start_year'] == calendar_year].item()

                norm_dist = UtilityFactorMethods._data['highway_norm_dist'].loc[
                    UtilityFactorMethods._data['start_year'] == calendar_year].item()

                UtilityFactorMethods._cache[cache_key + '_method'] = utility_factor_methods_dict[method]
                UtilityFactorMethods._cache[cache_key + '_norm_dist'] = norm_dist
            else:
                raise Exception('Missing utility factor calculation method for %d or prior' % calendar_year)

        method = UtilityFactorMethods._cache[cache_key + '_method']
        norm_dist = UtilityFactorMethods._cache[cache_key + '_norm_dist']

        return method(miles, norm_dist)

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

        UtilityFactorMethods._data = pd.DataFrame()

        UtilityFactorMethods._cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'utility_factor_methods'
        input_template_version = 0.1
        input_template_columns = {'start_year', 'city_method', 'city_norm_dist', 'highway_method', 'highway_norm_dist'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                UtilityFactorMethods._data = df

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

        init_fail += UtilityFactorMethods.init_from_file(omega_globals.options.utility_factor_methods_file,
                                                         verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.output_folder)
            UtilityFactorMethods._data.to_csv(
                omega_globals.options.output_folder + os.sep + 'policy_upstream_method.csv', index=False)

            print(UtilityFactorMethods.calc_city_utility_factor(2020, 50))
            print(UtilityFactorMethods.calc_city_utility_factor(2027, 50))
            print(UtilityFactorMethods.calc_highway_utility_factor(2020, 50))
            print(UtilityFactorMethods.calc_highway_utility_factor(2027, 50))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
