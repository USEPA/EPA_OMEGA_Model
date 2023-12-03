"""

**Routines to load and access electricity prices from the analysis context**

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent electricity charging costs per kWh and the share of charging at the given rate(s).

File Type
    comma-separated values (CSV)

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
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_column_names, read_input_file_template_info


class ElectricityPrices:
    """
    **Loads and provides access to fuel prices from the analysis context**

    """

    def __init__(self):
        self._data = {}
        self.df = pd.DataFrame()
        self.year_min = None
        self.year_max = None

    def init_from_file(self, filepath, batch_settings, effects_log, session_settings=None, context=False):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            batch_settings: an instance of the BatchSettings class.
            effects_log: an instance of the EffectsLog class.
            session_settings: an instance of the SessionSettings class.
            context (bool): whether context electricity prices (True) or session prices (False)

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

        if context is True or batch_settings.electricity_prices_source == 'AEO':
            df = df.loc[(df['context_id'] == batch_settings.context_name_liquid_fuel)
                        & (df['case_id'] == batch_settings.context_case_liquid_fuel), :]
        elif batch_settings.electricity_prices_source == 'IPM':
            if session_settings.session_policy == 'no_action':
                df = df.loc[df['case_id'] == 'no_action', :]
            else:
                df = df.loc[df['case_id'] != 'no_action', :]
        else:
            effects_log.logwrite(f'\nUnexpected setting for "Electricity Prices" may cause crash\n')

        dollar_basis = df['dollar_basis'].mean()
        cols_to_convert = [col for col in df.columns if 'dollars_per_unit' in col]

        deflators = batch_settings.ip_deflators._data

        adjustment_factor = deflators[batch_settings.analysis_dollar_basis]['price_deflator'] \
                            / deflators[dollar_basis]['price_deflator']

        for col in cols_to_convert:
            df[col] = df[col] * adjustment_factor

        df['dollar_basis'] = batch_settings.analysis_dollar_basis
        key = df['calendar_year']
        self._data = df.set_index(key).sort_index().to_dict(orient='index')

        self.year_min = df['calendar_year'].min()
        self.year_max = df['calendar_year'].max()

        self.df = self.interpolate_values(batch_settings, session_settings, df, cols_to_convert)
        self._data = self.df.sort_index().to_dict(orient='index')

    def interpolate_values(self, batch_settings, session_settings, df, args):
        """

        Parameters:
            batch_settings: an instance of the BatchSettings class.
            session_settings: an instance of the SessionSettings class.
            df (DataFrame): the input data to be interpolated.
            args (list): the arguments to interpolate.

        Returns:
             The passed DataFrame with interpolated values to fill in missing data.

        """
        years = df['calendar_year'].unique()
        fuel_id = df['fuel_id'].unique()[0]

        for idx, year in enumerate(years):
            if year < self.year_max:
                year1, year2 = year, years[idx + 1]
                dollar_basis = int(self._data[year]['dollar_basis'])

                for yr in range(year1 + 1, year2):
                    self._data.update({
                        yr: {
                            'context_id': batch_settings.electricity_prices_source,
                            'dollar_basis': dollar_basis,
                            'case_id': session_settings.session_policy,
                            'fuel_id': fuel_id,
                            'calendar_year': yr,
                            }
                    })

                    for arg in args:
                        arg_value1 = self._data[year1][arg]
                        arg_value2 = self._data[year2][arg]

                        m = (arg_value2 - arg_value1) / (year2 - year1)

                        arg_value = m * (yr - year1) + arg_value1
                        self._data[yr][arg] = arg_value

        df = pd.DataFrame(self._data).transpose().sort_index()

        return df

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
