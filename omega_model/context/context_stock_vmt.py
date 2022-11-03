"""

**Routines to load and access stock vmt from the analysis context**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents stock vmt by context case, case id and calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_stock_vmt,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,calendar_year,case_id,miles,stock
        AEO2022,2021,Reference case,2.76E+12,260088654
        AEO2022,2022,Reference case,2.89E+12,261614075
        AEO2022,2023,Reference case,2.99E+12,263155182
        AEO2022,2024,Reference case,3.03E+12,264624603
        AEO2022,2025,Reference case,3.08E+12,266039459

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', etc

    :calendar_year:
        The calendar year of the fuel costs

    :miles:
        The vehicle miles traveled

    :stock:
        The vehicle stock

----

**CODE**

"""
print('importing %s' % __file__)

from omega_model import *


class ContextStockVMT(OMEGABase):
    """
    **Loads and provides access to stock vmt from the analysis context**

    """

    _data = dict()
    calendar_year_max = 0

    @staticmethod
    def get_context_stock_vmt(calendar_year):
        """

        Args:
            calendar_year (int): the calendar year for which stock vmt is sought

        Returns:
            The stock and vmt values for the passed calendar year

        """
        if calendar_year > ContextStockVMT.calendar_year_max:
            calendar_year = ContextStockVMT.calendar_year_max

        return ContextStockVMT._data[calendar_year]['stock'], ContextStockVMT._data[calendar_year]['miles']

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
        ContextStockVMT._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_stock_vmt'
        input_template_version = 0.1
        input_template_columns = {'context_id',
                                  'calendar_year',
                                  'case_id',
                                  'miles',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                df = df.loc[(df['context_id'] == omega_globals.options.context_id)
                            & (df['case_id'] == omega_globals.options.context_case_id),
                     :]

                ContextStockVMT.calendar_year_max = max(df['calendar_year'])

                key = df['calendar_year']

                ContextStockVMT._data = df.set_index(key).to_dict(orient='index')

        return template_errors
