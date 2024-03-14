"""

**Routines to load and access electricity prices from the analysis context**

AEO electricity price data include retail and pre-tax costs in dollars per unit (e.g. $/kWh)

NOTE: This module is not active - electricity_prices.py is used

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents electricity prices by context case and calendar year.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,context.electricity_prices_aeo,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,dollar_basis,case_id,fuel_id,calendar_year,retail_dollars_per_unit,pretax_dollars_per_unit
        AEO2020,2019,Reference case,US electricity,2019,0.12559407,0.10391058
        AEO2020,2019,Reference case,US electricity,2020,0.1239522,0.10212733

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :dollar_basis:
        The dollar basis of the fuel prices in the given AEO version. Note that this dollar basis is
        converted in-code to 'analysis_dollar_basis' using the implicit_price_deflators input file.

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', etc

    :fuel_id:
        The name of the vehicle in-use fuel, must be in the table loaded by ``class fuels.Fuel`` and consistent with
        the base year vehicles file (column ``in_use_fuel_id``) loaded by ``class vehicles.VehicleFinal``

    :calendar_year:
        The calendar year of the fuel costs

    :retail_dollars_per_unit:
        Retail dollars per unit

    :pretax_dollars_per_unit:
        Pre-tax dollars per unit

----

**CODE**

"""
from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_column_names


class ElectricityPrices:
    """
    **Loads and provides access to fuel prices from the analysis context**

    """

    def __init__(self):
        self._data = {}
        self.year_min = None
        self.year_max = None

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
        # don't forget to update the module docstring with changes here
        input_template_columns = {
            'context_id',
            'dollar_basis',
            'case_id',
            'fuel_id',
            'calendar_year',
            'retail_dollars_per_unit',
            'pretax_dollars_per_unit',
        }
        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[(df['context_id'] == batch_settings.context_name_liquid_fuel)
                    & (df['case_id'] == batch_settings.context_case_liquid_fuel), :]

        aeo_dollar_basis = df['dollar_basis'].mean()
        cols_to_convert = [col for col in df.columns if 'dollars_per_unit' in col]

        deflators = batch_settings.ip_deflators._data

        adjustment_factor = deflators[batch_settings.analysis_dollar_basis]['price_deflator'] \
                            / deflators[aeo_dollar_basis]['price_deflator']

        for col in cols_to_convert:
            df[col] = df[col] * adjustment_factor

        df['dollar_basis'] = batch_settings.analysis_dollar_basis

        self._data = df.set_index('calendar_year').sort_index().to_dict(orient='index')

        self.year_min = df['calendar_year'].min()
        self.year_max = df['calendar_year'].max()

    def get_fuel_price(self, calendar_year, *price_types):
        """
        Get fuel price data in calendar_year

        Args:
            calendar_year (numeric): calendar year for which to get fuel prices.
            price_types (str): the price types sought (e.g., retail, pretax)

        Returns:
            Fuel price or list of fuel prices if multiple attributes were requested

        """
        prices = []
        if calendar_year not in self._data:
            calendar_year = max(self.year_min, min(calendar_year, self.year_max))

        for price_type in price_types:
            prices.append(self._data[calendar_year][price_type])

        if len(prices) == 1:
            return prices[0]
        else:
            return prices
