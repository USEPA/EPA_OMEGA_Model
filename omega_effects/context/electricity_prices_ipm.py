"""

**Routines to load and access electricity prices from the analysis context and the sessions**

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represent electricity charging costs per kWh.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        context_id,dollar_basis,case_id,fuel_id,calendar_year,retail_dollars_per_unit,pretax_dollars_per_unit
        IPM,2022,action,US electricity,2020,0.11635031,0.109908833
        IPM,2022,action,US electricity,2028,0.118313045,0.111762906

Data Column Name and Description
    :context_id:
        The name of the context source, e.g. 'AEO2020', 'AEO2021', 'IPM', etc

    :dollar_basis:
        The dollar basis of the fuel prices. Note that this dollar basis is converted in-code to 'analysis_dollar_basis'
         using the implicit_price_deflators input file.

    :case_id:
        The name of the case within the context, e.g. 'Reference Case', 'High oil price', for AEO; 'action' or
        'no_action' for IPM

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
        self.context_id = None
        self.case_id = None

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
        self.context_id = df['context_id'].unique()[0]
        self.case_id = df['case_id'].unique()[0]

        self.df = self.interpolate_values(df, cols_to_convert)
        self._data = self.df.sort_index().to_dict(orient='index')

    def interpolate_values(self, df, args):
        """

        Parameters:
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
                            'context_id': self.context_id,
                            'dollar_basis': dollar_basis,
                            'case_id': self.case_id,
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
            price_types (str or strs): the price types sought (e.g., retail, pretax)

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
