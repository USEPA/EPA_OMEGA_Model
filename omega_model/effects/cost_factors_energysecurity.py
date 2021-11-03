"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents $/gallon cost estimates associated with energy security.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_cost_factors-energysecurity,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,dollar_basis,dollars_per_gallon,foreign_oil_fraction
        2020,2018,0.081357143,0.9

Data Column Name and Description
    :calendar_year:
        The calendar year for which $/gallon values are applicable.

    :dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

    :dollars_per_gallon:
        The cost (in US dollars) per gallon of liquid fuel associated with energy security.

    :foreign_oil_fraction:
        A legacy parameter that is not used currently.

----

**CODE**

"""

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class CostFactorsEnergySecurity(OMEGABase):
    """
    Loads and provides access to energy security cost factors by calendar year.

    """
    _data = dict()

    @staticmethod
    def get_cost_factors(calendar_year, cost_factors):
        """

        Get cost factors by calendar year

        Args:
            calendar_year (int): calendar year to get cost factors for
            cost_factors (str, [strs]): name of cost factor or list of cost factor attributes to get

        Returns:
            Cost factor or list of cost factors

        """
        calendar_years = CostFactorsEnergySecurity._data.keys()
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        factors = []
        for cf in cost_factors:
            factors.append(CostFactorsEnergySecurity._data[year][cf])

        if len(cost_factors) == 1:
            return factors[0]
        else:
            return factors

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        CostFactorsEnergySecurity._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_cost_factors-energysecurity'
        input_template_version = 0.2
        input_template_columns = {'calendar_year',
                                  'dollar_basis',
                                  'dollars_per_gallon',
                                  'foreign_oil_fraction',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis,
                                             'dollars_per_gallon')

                CostFactorsEnergySecurity._data = df.set_index('calendar_year').to_dict(orient='index')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from effects.ip_deflators import ImplictPriceDeflators

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += ImplictPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += CostFactorsEnergySecurity.init_database_from_file(omega_globals.options.energysecurity_cost_factors_file,
                                                                       verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
