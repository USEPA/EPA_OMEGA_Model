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
from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class ContextStockVMT:
    """
    **Loads and provides access to stock vmt from the analysis context**

    """
    def __init__(self):
        self._data = dict()
        self.calendar_year_max = 0

    def init_from_file(self, filepath, batch_settings, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            batch_settings: an instance of the BatchSettings class.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log, index_col=0)

        input_template_name = 'context_stock_vmt'
        input_template_version = 0.1
        input_template_columns = {'context_id',
                                  'calendar_year',
                                  'case_id',
                                  'miles',
                                  }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        df.fillna(0, inplace=True)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[(df['context_id'] == batch_settings.context_name)
                    & (df['case_id'] == batch_settings.context_case), :]

        self.calendar_year_max = max(df['calendar_year'])

        key = df['calendar_year']

        self._data = df.set_index(key).to_dict(orient='index')

    def get_context_stock_vmt(self, calendar_year):
        """

        Args:
            calendar_year (int): the calendar year for which stock vmt is sought

        Returns:
            The stock and vmt values for the passed calendar year

        """
        if calendar_year > self.calendar_year_max:
            calendar_year = self.calendar_year_max

        return self._data[calendar_year]['stock'], self._data[calendar_year]['miles']
