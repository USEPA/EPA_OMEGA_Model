"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/mile cost estimates associated with congestion and noise associated with road travel.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,cost_factors_congestion_noise,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,dollar_basis,congestion_cost_dollars_per_mile,noise_cost_dollars_per_mile
        car,2018,0.063390239,0.000940863
        truck,2018,0.056598428,0.000940863

Data Column Name and Description
    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

    :congestion_cost_dollars_per_mile:
        The cost per vehicle mile traveled associated with congestion.

    :noise_cost_dollars_per_mile:
        The cost per vehicle mile traveled associated with noise.


----

**CODE**

"""
from omega_effects_module.effects_code.general.general_functions import read_input_file
from omega_effects_module.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names
from omega_effects_module.effects_code.general.general_functions import adjust_dollars


class CostFactorsCongestionNoise:
    """
    Loads and provides access to congestion and noise cost factors by legacy reg class id.

    """
    def __init__(self):
        self._data = dict()  # private dict, cost factor congestion and noise by legacy reg class id

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
        input_template_name = 'cost_factors_congestion_noise'
        input_template_version = 0.1
        input_template_columns = {
            'reg_class_id',
            'dollar_basis',
            'congestion_cost_dollars_per_mile',
            'noise_cost_dollars_per_mile',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df = df.loc[df['dollar_basis'] != 0, :]

        cols_to_convert = [col for col in df.columns if 'dollars_per_mile' in col]

        df = adjust_dollars(batch_settings, df, 'ip_deflators', effects_log, *cols_to_convert)

        self._data = df.set_index('reg_class_id').to_dict(orient='index')

    def get_cost_factors(self, reg_class_id, cost_factors):
        """

        Get cost factors by legacy reg class id

        Args:
            reg_class_id: reg class to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        cache_key = (reg_class_id, cost_factors)

        if cache_key not in self._data:

            factors = []
            for cf in cost_factors:
                factors.append(self._data[reg_class_id][cf])

            if len(cost_factors) == 1:
                self._data[cache_key] = factors[0]
            else:
                self._data[cache_key] = factors

        return self._data[cache_key]
