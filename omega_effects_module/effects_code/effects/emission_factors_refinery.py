"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents refinery emission rates by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,emission_factors_refinery,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,in_use_fuel_id,co_grams_per_gallon,voc_grams_per_gallon,nox_grams_per_gallon,sox_grams_per_gallon,pm25_grams_per_gallon,co2_grams_per_gallon,ch4_grams_per_gallon,n2o_grams_per_gallon,acetaldehyde_grams_per_gallon,acrolein_grams_per_gallon,benzene_grams_per_gallon,butadiene13_grams_per_gallon,formaldehyde_grams_per_gallon
        2017,pump gasoline,7.154547169,24.70656765,15.02737679,10.97287624,1.077573535,20321.29509,129.3687687,2.633447789,0.004753979,0.000652611,0.096633686,0.001043598,0.035749195

Data Column Name and Description
    :calendar_year:
        The calendar year for which $/gallon values are applicable.

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :co_grams_per_gallon:
        The refinery emission factors follow the structure pollutant_units where units are grams per gallon of liquid fuel.

----

**CODE**

"""
import numpy as np

from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class EmissionFactorsRefinery:
    """
    Loads and provides access to refinery emission factors by calendar year and in-use fuel id.

    """
    def __init__(self):
        self._data = dict()  # private dict, emissions factors refinery by calendar year and in-use fuel id

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_name = 'emission_factors_refinery'
        input_template_version = 0.2
        input_template_columns = {
            'calendar_year',
            'in_use_fuel_id',
            'voc_grams_per_gallon',
            'co_grams_per_gallon',
            'nox_grams_per_gallon',
            'pm25_grams_per_gallon',
            'sox_grams_per_gallon',
            'benzene_grams_per_gallon',
            'butadiene13_grams_per_gallon',
            'formaldehyde_grams_per_gallon',
            'acetaldehyde_grams_per_gallon',
            'acrolein_grams_per_gallon',
            'ch4_grams_per_gallon',
            'n2o_grams_per_gallon',
            'co2_grams_per_gallon',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = \
            df.set_index(['calendar_year', 'in_use_fuel_id']).sort_index().to_dict(orient='index')
        self._data.update(
            df[['calendar_year', 'in_use_fuel_id']].set_index('in_use_fuel_id').to_dict(orient='series'))

    def get_emission_factors(self, calendar_year, in_use_fuel_id, emission_factors):
        """

        Get emission factors by calendar year and in-use fuel ID

        Args:
            calendar_year (int): calendar year to get emission factors for
            in_use_fuel_id (str): the liquid fuel ID, e.g., 'pump gasoline'
            emission_factors (str, [strs]): name of emission factor or list of emission factor attributes to get

        Returns:
            Emission factor or list of emission factors

        """
        cache_key = (calendar_year, in_use_fuel_id, emission_factors)

        if cache_key not in self._data:

            calendar_years = np.atleast_1d(self._data['calendar_year'][in_use_fuel_id])
            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for ef in emission_factors:
                factors.append(self._data[year, in_use_fuel_id][ef])

            if len(emission_factors) == 1:
                self._data[cache_key] = factors[0]
            else:
                self._data[cache_key] = factors

        return self._data[cache_key]
