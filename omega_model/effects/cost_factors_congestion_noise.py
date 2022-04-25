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

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class CostFactorsCongestionNoise(OMEGABase):
    """
    Loads and provides access to congestion and noise cost factors by legacy reg class id.

    """

    _data = dict()  # private dict, cost factor congestion and noise by legacy reg class id

    @staticmethod
    def get_cost_factors(reg_class_id, cost_factors):
        """

        Get cost factors by legacy reg class id

        Args:
            reg_class_id: reg class to get cost factors for
            cost_factors: name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        cache_key = (reg_class_id, cost_factors)

        if cache_key not in CostFactorsCongestionNoise._data:

            factors = []
            for cf in cost_factors:
                factors.append(CostFactorsCongestionNoise._data[reg_class_id][cf])

            if len(cost_factors) == 1:
                CostFactorsCongestionNoise._data[cache_key] = factors[0]
            else:
                CostFactorsCongestionNoise._data[cache_key] = factors

        return CostFactorsCongestionNoise._data[cache_key]

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
        CostFactorsCongestionNoise._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'cost_factors_congestion_noise'
        input_template_version = 0.1
        input_template_columns = {'reg_class_id',
                                  'dollar_basis',
                                  'congestion_cost_dollars_per_mile',
                                  'noise_cost_dollars_per_mile',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

        if not template_errors:
            validation_dict = {'reg_class_id': list(legacy_reg_classes)}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            cols_to_convert = [col for col in df.columns if 'dollars_per_mile' in col]

            df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            if not template_errors:
                CostFactorsCongestionNoise._data = df.set_index('reg_class_id').to_dict(orient='index')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        from effects.ip_deflators import ImplictPriceDeflators
        init_fail += ImplictPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += \
            CostFactorsCongestionNoise.init_from_file(omega_globals.options.congestion_noise_cost_factors_file,
                                                      verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
