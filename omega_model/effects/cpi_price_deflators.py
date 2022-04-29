"""

**Routines to load CPI price deflators.**

Used to convert monetary inputs to a consistent dollar basis, e.g., in the ``cost_factors_criteria`` module.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the price deflator by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_cpi_price_deflators,input_template_version:,0.22

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,price_deflator
        2010,218.056
        2011,224.939

Data Column Name and Description

:calendar_year:
    Calendar year of the price deflator

:price_deflator:
    CPI price deflator

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class CPIPriceDeflators(OMEGABase):
    """
    **Loads and provides access to CPI price deflators by calendar year.**

    """
    _data = dict()  # private dict, CPI price deflators by calendar year

    @staticmethod
    def get_price_deflator(calendar_year):
        """
        Get the CPI price deflator for the given calendar year.

        Args:
            calendar_year (int): the calendar year to get the function for

        Returns:
            The CPI price deflator for the given calendar year.

        """
        # import pandas as pd

        calendar_years = pd.Series(CPIPriceDeflators._data.keys())
        # calendar_years = np.array([*CPIPriceDeflators._data]) # np.array(list(CPIPriceDeflators._data.keys()))
        if len(calendar_years[calendar_years <= calendar_year]) > 0:
            year = max(calendar_years[calendar_years <= calendar_year])

            return CPIPriceDeflators._data[year]['price_deflator']
        else:
            raise Exception(f'Missing CPI price deflator for {calendar_year} or prior')

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


        CPIPriceDeflators._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'context_cpi_price_deflators'
        input_template_version = 0.22
        input_template_columns = {'calendar_year', 'price_deflator'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                CPIPriceDeflators._data = df.set_index('calendar_year').to_dict(orient='index')

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

        init_fail += CPIPriceDeflators.init_from_file(omega_globals.options.cpi_deflators_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            print(CPIPriceDeflators.get_price_deflator(2010))
            print(CPIPriceDeflators.get_price_deflator(2020))
            print(CPIPriceDeflators.get_price_deflator(2050))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
