"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent fatality rates (fatalities per billion miles) for the fleet.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,fatality_rates,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        model_year,calendar_year,age,average_fatality_rate,
        1996,1996,0,8.487042,
        1996,1997,1,8.364596,
        1996,1998,2,8.342017,

Data Column Name and Description
    :model_year:
        The model year of a given vehicle

    :calendar_year:
        The calendar year

    :age:
        The vehicle age

    :average_fatality_rate:
        The fatality rate in fatalities per billions miles travelled where "average" denotes the average effectiveness
        of passenger safety technology on vehicles.

----

**CODE**

"""
from omega_model import *


class FatalityRates(OMEGABase):
    """
    Loads and provides access to fatality rates by calendar year and vehicle age.

    """

    _data = dict()  # private dict
    model_year_max = None

    @staticmethod
    def get_fatality_rate(model_year, age):
        """

        Args:
            model_year (int): the model year for which a fatality rate is needed.

        Returns:
            The average fatality rate for vehicles of a specific model year and age.

        """
        year = model_year
        if model_year > FatalityRates.model_year_max:
            year = FatalityRates.model_year_max

        return FatalityRates._data[year, age]['average_fatality_rate']

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
        FatalityRates._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'fatality_rates'
        input_template_version = 0.1
        input_template_columns = {
            'model_year',
            'age',
            'average_fatality_rate',
        }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:

                model_year_max = max(df['model_year'])
                key = pd.Series(zip(
                    df['model_year'],
                    df['age']
                ))
                df.insert(0, 'key', key)
                FatalityRates._data = df.set_index(key).to_dict(orient='index')
                FatalityRates.model_year_max = model_year_max

        return template_errors
