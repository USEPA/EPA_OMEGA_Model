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

        calendar_year,dollar_basis,base_rate_dollars_per_kwh,marginal_public_level2_dollars_per_kwh,marginal_public_level3_dollars_per_kwh,share_base_rate,share_public_level2,share_public_level3
        2027,2022,0.1,0.05,0.08,0.6,0.3,0.1
        2030,2022,0.11,0.05,0.08,0.57,0.31,0.12
        2035,2022,0.12,0.05,0.08,0.54,0.32,0.14
        2040,2022,0.13,0.05,0.08,0.51,0.33,0.16
        2045,2022,0.14,0.05,0.08,0.48,0.34,0.18
        2050,2022,0.15,0.05,0.08,0.45,0.35,0.2

Data Column Name and Description
    :calendar_year:
        The calendar year for which the indicated price is valid.

    :dollar_basis:
        The dollar value of the associated price; prices are converted to analysis dollars in code.

    :base_rate_dollars_per_kwh:
        The base rate cost per kWh for all charging.

    :marginal_public_level2_dollars_per_kwh:
        The marginal cost per kWh for level 2 charging; this is added to the base rate.

    :marginal_public_level3_dollars_per_kwh:
        The marginal cost per kWh for level 2 charging; this is added to the base rate.

    :share_base_rate:
        The share of charging at the base rate.

    :share_public_level2:
        The share of charging at the public level 2 rate.

    :share_public_level3:
        The share of charging at the public level 3 rate.

----

**CODE**

"""
print('importing %s' % __file__)

from omega_model import *


class ElectricityPrices(OMEGABase):
    """
    **Loads and provides access to fuel prices from the analysis context**

    """
    _data = {}
    year_max = None
    year_min = None

    @staticmethod
    def interpolate_values(df, args):
        """

        Parameters:
            df (DataFrame): the input data to be interpolated.
            args (list): the arguments to interpolate.

        Returns:
             The passed DataFrame with interpolated values to fill in missing data.

        """
        years = df['calendar_year'].unique()
        ElectricityPrices.year_max = df['calendar_year'].max()
        ElectricityPrices.year_min = df['calendar_year'].min()

        for idx, year in enumerate(years):
            if year < ElectricityPrices.year_max:
                year1, year2 = year, years[idx + 1]
                dollar_basis = int(ElectricityPrices._data[year]['dollar_basis'])

                for yr in range(year1 + 1, year2):
                    ElectricityPrices._data.update({yr: {'dollar_basis': dollar_basis}})

                    for arg in args:
                        arg_value1 = ElectricityPrices._data[year1][arg]
                        arg_value2 = ElectricityPrices._data[year2][arg]

                        m = (arg_value2 - arg_value1) / (year2 - year1)

                        arg_value = m * (yr - year1) + arg_value1
                        ElectricityPrices._data[yr][arg] = arg_value

        df = pd.DataFrame(ElectricityPrices._data).transpose().sort_index()

        return df

    @staticmethod
    def get_fuel_price(calendar_year):
        """

        Parameters:
            calendar_year (int): the year for which price(s) is sought

        Returns:
            The price data for the given calendar year.

        """
        if calendar_year < ElectricityPrices.year_min:
            calendar_year = ElectricityPrices.year_min
        elif calendar_year > ElectricityPrices.year_max:
            calendar_year = ElectricityPrices.year_max

        return ElectricityPrices._data[calendar_year]['retail_dollars_per_unit']

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
        ElectricityPrices._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        # don't forget to update the module docstring with changes here
        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {
            'calendar_year',
            'dollar_basis',
            'base_rate_dollars_per_kwh',
            'marginal_public_level2_dollars_per_kwh',
            'marginal_public_level3_dollars_per_kwh',
            'share_base_rate',
            'share_public_level2_rate',
            'share_public_level3_rate',
        }
        template_errors = validate_template_version_info(
            filename, input_template_name, input_template_version, verbose=verbose
        )
        df = pd.DataFrame()
        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(
                filename, input_template_columns, df.columns, verbose=verbose
            )

        if not template_errors:
            dollar_basis = df['dollar_basis'].mean()
            cols_to_convert = [col for col in df.columns if 'dollars_per_kwh' in col]

            deflators = pd.read_csv(omega_globals.options.ip_deflators_file, skiprows=1, index_col=0).to_dict('index')

            adjustment_factor = (deflators[omega_globals.options.analysis_dollar_basis]['price_deflator'] /
                                 deflators[dollar_basis]['price_deflator']
                                 )

            for col in cols_to_convert:
                df[col] = df[col] * adjustment_factor

            df['dollar_basis'] = omega_globals.options.analysis_dollar_basis

            df.insert(
                len(df.columns),
                'retail_dollars_per_unit',
                df['base_rate_dollars_per_kwh'] * df['share_base_rate']
                + (df['base_rate_dollars_per_kwh'] + df['marginal_public_level2_dollars_per_kwh']) *
                df['share_public_level2_rate']
                + (df['base_rate_dollars_per_kwh'] + df['marginal_public_level3_dollars_per_kwh']) *
                df['share_public_level3_rate']
            )
            args = [col for col in df.columns if 'calendar_year' not in col and 'dollar_basis' not in col]

            ElectricityPrices._data = df.set_index('calendar_year').sort_index().to_dict(orient='index')

            df = ElectricityPrices.interpolate_values(df, args)
            ElectricityPrices._data = df.sort_index().to_dict(orient='index')

        return template_errors
