"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent safety values associated with mass reduction in the fleet.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,safety_values,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        body_style,nhtsa_safety_class,threshold_lbs,change_per_100_lbs_below_threshold,change_per_100_lbs_at_or_above_threshold
        sedan,PC,3201,0.012,0.0042
        pickup,LT/SUV,5014,0.0031,-0.0061
        cuv_suv,CUV/Minivan,3872,-0.0025,-0.0025

Data Column Name and Description
    :body_style:
        The OMEGA body_style (e.g., sedan, pickup, cuv_suv)

    :nhtsa_safety_class:
        The NHTSA safety class (e.g., PC, LT/SUV, CUV/Minivan)

    :threshold_lbs:
        The curb weight, in pounds, above and below which safety values may change.

    :change_per_100_lbs_below_threshold:
        A percentage change in the fatality rate associated with reductions in curb weight below the associated curb
        weight threshold; a positive value denotes an increase in fatality rate associated with a reduced curb weight
        while a negative value denotes a decrease in fatality rate associated with a reduced curb weight; increased
        curb weights would have the opposite effect on fatality rate.

    :change_per_100_lbs_at_or_above_threshold:
        A percentage change in the fatality rate associated with reductions in curb weight above the associated curb
        weight threshold; a positive value denotes an increase in fatality rate associated with a reduced curb weight
        while a negative value denotes a decrease in fatality rate associated with a reduced curb weight; increased
        curb weights would have the opposite effect on fatality rate.

----

**CODE**

"""
from omega_model import *


class SafetyValues(OMEGABase):
    """
    Loads and provides access to safety values by body style.

    """

    _data = dict()  # private dict

    @staticmethod
    def get_safety_values(body_style):
        """

        Get safety values by body style.

        Args:
            body_style (str): the OMEGA body style (e.g., sedan, cuv_suv, pickup)

        Returns:
            The curb weight threshold and percentage changes in fatality rates for weight changes above and below
            that threshold.

        """
        threshold = SafetyValues._data[body_style]['threshold_lbs']
        change_below = SafetyValues._data[body_style]['change_per_100_lbs_below_threshold']
        change_above = SafetyValues._data[body_style]['change_per_100_lbs_at_or_above_threshold']

        return threshold, change_below, change_above

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
        SafetyValues._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'safety_values'
        input_template_version = 0.1
        input_template_columns = {
            'body_style',
            'nhtsa_safety_class',
            'threshold_lbs',
            'change_per_100_lbs_below_threshold',
            'change_per_100_lbs_at_or_above_threshold',
        }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                SafetyValues._data = df.set_index('body_style').to_dict(orient='index')

        return template_errors
