"""

**Routines to load and access fuel prices from the analysis context**

Context fuel price data includes retail and pre-tax costs in dollars per unit (e.g. $/gallon, $/kWh)

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents fuel prices by context case, fuel type, and calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_fuel_prices,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,dollar_basis,case_id,fuel_id,calendar_year,retail_dollars_per_unit,pretax_dollars_per_unit
        AEO2020,2019,Reference case,pump gasoline,2019,2.665601,2.10838
        AEO2020,2019,Reference case,US electricity,2019,0.12559407,0.10391058

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', etc

    :dollar_basis:
        The dollar basis of the fuel prices in the given AEO version. Note that this dollar basis is converted in-code to
        'analysis_dollar_basis' using the implicit_price_deflators input file.

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
from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class FuelPrice:
    """
    **Loads and provides access to fuel prices from the analysis context**

    """
    def __init__(self):
        self._data = dict()

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
        df = read_input_file(filepath, effects_log)

        input_template_name = 'context_fuel_prices'
        input_template_version = 0.2
        input_template_columns = {
            'context_id',
            'dollar_basis',
            'case_id',
            'fuel_id',
            'calendar_year',
            'retail_dollars_per_unit',
            'pretax_dollars_per_unit',
        }

        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)

        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[(df['context_id'] == batch_settings.context_name)
                    & (df['case_id'] == batch_settings.context_case), :]

        aeo_dollar_basis = df['dollar_basis'].mean()
        cols_to_convert = [col for col in df.columns if 'dollars_per_unit' in col]

        deflators = batch_settings.ip_deflators._data

        adjustment_factor = deflators[batch_settings.analysis_dollar_basis]['price_deflator'] \
                            / deflators[aeo_dollar_basis]['price_deflator']

        for col in cols_to_convert:
            df[col] = df[col] * adjustment_factor

        df['dollar_basis'] = batch_settings.analysis_dollar_basis

        self._data = df.set_index(['context_id', 'case_id', 'fuel_id', 'calendar_year']).sort_index()\
            .to_dict(orient='index')

        self._data['min_calendar_year'] = df['calendar_year'].min()
        self._data['max_calendar_year'] = df['calendar_year'].max()

    def get_fuel_prices(self, batch_settings, calendar_year, price_types, fuel_id):
        """
        Get fuel price data for fuel_id in calendar_year

        Args:
            batch_settings: an instance of the BatchSettings class.
            calendar_year (numeric): calendar year for which to get fuel prices.
            price_types (str, [str1, str2...]): ContextFuelPrices attributes to get
            fuel_id (str): fuel ID

        Returns:
            Fuel price or tuple of fuel prices if multiple attributes were requested

        Example:
            ::

                pretax_pump_gas_price_dollars_2030 =
                ContextFuelPrices.get_fuel_prices(2030, 'pretax_dollars_per_unit', 'pump gasoline')

                pump_gas_attributes_2030 =
                ContextFuelPrices.get_fuel_prices(2030, ['retail_dollars_per_unit', 'pretax_dollars_per_unit'], 'pump gasoline')

        """
        cache_key = (calendar_year, price_types, fuel_id)

        if cache_key not in self._data:

            calendar_year = max(self._data['min_calendar_year'], min(calendar_year, self._data['max_calendar_year']))

            if type(price_types) is not list:
                price_types = [price_types]

            prices = []
            for pt in price_types:
                prices.append(self._data[batch_settings.context_name,
                batch_settings.context_case,
                fuel_id,
                calendar_year][pt])

            if len(prices) == 1:
                self._data[cache_key] = prices[0]
            else:
                self._data[cache_key] = prices

        return self._data[cache_key]
