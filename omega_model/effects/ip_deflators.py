"""

**Routines to load Implicit Price (IP) deflators.**

Used to convert monetary inputs to a consistent dollar basis, e.g., in the ``cost_factors_congestion_noise`` module.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the price deflator by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_implicit_price_deflators,input_template_version:,0.22

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,price_deflator,,
        2001,79.79,,
        2002,81.052,,

Data Column Name and Description

:calendar_year:
    Calendar year of the price deflator

:price_deflator:
    Implicit price deflator

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class ImplictPriceDeflators(OMEGABase):
    """
    **Loads and provides access to implicit price deflators by calendar year.**

    """
    _data = dict()  # private dict, implicit price deflators by calendar year

    _cache = dict()

    @staticmethod
    def get_price_deflator(calendar_year):
        """
        Get the implicit price deflator for the given calendar year.

        Args:
            calendar_year (int): the calendar year to get the function for

        Returns:
            The implicit price deflator for the given calendar year.

        """
        cache_key = calendar_year

        if cache_key not in ImplictPriceDeflators._cache:

            calendar_years = pd.Series(ImplictPriceDeflators._data.keys())
            # calendar_years = np.array(list(ImplictPriceDeflators._data.keys()))
            # calendar_years = np.array([*ImplictPriceDeflators._data])
            if len(calendar_years[calendar_years <= calendar_year]) > 0:
                year = max(calendar_years[calendar_years <= calendar_year])

                ImplictPriceDeflators._cache[cache_key] = ImplictPriceDeflators._data[year]['price_deflator']
            else:
                raise Exception(f'Missing implicit price deflator for {calendar_year} or prior')

        return ImplictPriceDeflators._cache[cache_key]

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


        ImplictPriceDeflators._data.clear()

        ImplictPriceDeflators._cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'context_implicit_price_deflators'
        input_template_version = 0.22
        input_template_columns = {'calendar_year', 'price_deflator'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                ImplictPriceDeflators._data = df.set_index('calendar_year').to_dict(orient='index')

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

        init_fail += ImplictPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            print(ImplictPriceDeflators.get_price_deflator(2010))
            print(ImplictPriceDeflators.get_price_deflator(2020))
            print(ImplictPriceDeflators.get_price_deflator(2050))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
