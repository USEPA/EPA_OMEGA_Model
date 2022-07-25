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
        change_above = SafetyValues._data[body_style]['change_ per_100_lbs_at_or_above_threshold']

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
            'change_ per_100_lbs_at_or_above_threshold',
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
