"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/uston benefits estimates associated with reductions in criteria air pollutants. The data should
be left blank to avoid calculating health effects (criteria air pollution effects) using $/uston values.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,cost_factors_criteria,input_template_version:,0.5

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,source_id,rate,study,pm25,sox,nox
        2020,2020,car pump gasoline,0.03,Wu,0,0,0
        2025,2020,car pump gasoline,0.03,Wu,709156.4844,127863.083,7233.620573
        2030,2020,car pump gasoline,0.03,Wu,813628.2611,146570.4771,8157.897937
        2035,2020,car pump gasoline,0.03,Wu,938850.3917,169075.4785,9195.259845
        2040,2020,car pump gasoline,0.03,Wu,1060686.72,191135.9472,10073.96999
        2045,2020,car pump gasoline,0.03,Wu,1171439.061,211302.6049,10731.06062
        2050,2020,car pump gasoline,0.03,Wu,1268468.809,229133.7696,11165.95105

Data Column Name and Description

    :calendar_year:
        The calendar year for which specific cost factors are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        cpi_price_deflators input file.

    :source_id:
        The source of the pollutant, whether it be a gasoline car or an EGU or refinery.

    :rate:
        The discount rate used in generating the $/ton benefits values.

    :study:
        The study from which the values are sourced.

    :pm25:
        The dollar per US ton of PM2.5.

    :sox:
        The dollar per US ton of SOx.

    :nox:
        The dollar per US tons of NOx.

----

**CODE**

"""
import pandas as pd

from omega_effects.general.general_functions import read_input_file
from omega_effects.general.input_validation import validate_template_version_info, validate_template_column_names


class CostFactorsCriteria:
    """
    Loads and provides access to criteria emissions cost factors by calendar year.

    """
    def __init__(self):
        self._dict = {}
        self._cache = {}
        self.calc_health_effects = True
        self.df = pd.DataFrame()
        self.criteria_rates_as_strings = []
        self.criteria_rates = []
        self.pollutants = []
        self.source_ids = []
        self.studies = []

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
        input_template_name = 'cost_factors_criteria'
        input_template_version = 0.5
        input_template_columns = [
            'calendar_year',
            'dollar_basis',
            'source_id',
            'rate',
            'study',
        ]

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(
            df, input_template_version, input_template_name=input_template_name, effects_log=effects_log
        )

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self.pollutants = [col for col in df.columns if col not in input_template_columns]
        self.criteria_rates_as_strings = df['rate'].astype('string').unique()
        for item in self.criteria_rates_as_strings:
            if len(item) > 5:
                n = pd.to_numeric(item[:-3])
            else:
                n = pd.to_numeric(item)
            self.criteria_rates.append(n)
        self.criteria_rates = sorted(set(self.criteria_rates))
        self.source_ids = df['source_id'].unique()
        self.studies = df['study'].unique()

        if not sum(df['calendar_year']) == 0:

            df = df.loc[df['dollar_basis'] != 0, :]

            df = batch_settings.cpi_deflators.adjust_dollars(batch_settings, df, effects_log, *self.pollutants)

            key = zip(
                df['calendar_year'],
                df['source_id'],
                df['study'],
                df['rate'].astype('string'),
            )
            self._dict = df.set_index(key).to_dict(orient='index')
            self.df = df.copy()

        else:
            self.calc_health_effects = False

    def get_cost_factors(self, calendar_year, source_id, cost_factors):
        """

        Get cost factors by calendar year

        Args:
            calendar_year (int): calendar year to get cost factors for
            source_id: (str): the pollutant source, e.g., 'car pump gasoline', 'egu', 'refinery'
            cost_factors (str, [strs]): name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        cache_key = (calendar_year, source_id, cost_factors)

        if cache_key not in self._cache:

            calendar_years \
                = [v['calendar_year'] for k, v in self._dict.items() if v['source_id'] == source_id]

            year = max([yr for yr in calendar_years if yr <= calendar_year])

            factors = []
            for cost_factor in cost_factors:
                pollutant_id, study, criteria_rate = (
                    cost_factor.split('_')[0], cost_factor.split('_')[1], cost_factor.split('_')[2]
                )
                factors.append(self._dict[year, source_id, study, criteria_rate][pollutant_id])

            if len(cost_factors) == 1:
                self._cache[cache_key] = factors[0]
            else:
                self._cache[cache_key] = factors

        return self._cache[cache_key]
