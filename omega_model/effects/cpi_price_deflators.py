"""

**Routines to load CPI price deflators.**

Used to discount costs in the ``cost_factors_criteria`` module.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the price deflator by start year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_cpi_price_deflators,input_template_version:,0.21

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,price_deflator
        2010,218.056
        2011,224.939

Data Column Name and Description

:start_year:
    Start year of the price deflator, applies until the next available start year

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
        import pandas as pd

        start_years = pd.Series(CPIPriceDeflators._data.keys())
        if len(start_years[start_years <= calendar_year]) > 0:
            year = max(start_years[start_years <= calendar_year])

            return CPIPriceDeflators._data[year]['price_deflator']
        else:
            raise Exception('Missing CPI price deflator for %d or prior' % calendar_year)

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

        CPIPriceDeflators._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'context_cpi_price_deflators'
        input_template_version = 0.21
        input_template_columns = {'start_year', 'price_deflator'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                CPIPriceDeflators._data = df.set_index('start_year').to_dict(orient='index')

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
