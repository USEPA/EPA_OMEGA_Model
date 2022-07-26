"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents electricity generating unit emission rates by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,emission_rates_egu,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        case,rate_name,independent_variable,initial_year,equation_rate_id,equation_kwh
        low_bound,pm25_grams_per_kwh,(calendar_year - 2020),2020,((-0.00024125 * (calendar_year - 2020)) + 0.024254),((8215370000.0 * (calendar_year - 2020)) + 1420520000.0)
        low_bound,nox_grams_per_kwh,(calendar_year - 2020),2020,((-0.0027646 * (calendar_year - 2020)) + 0.28546),((8215370000.0 * (calendar_year - 2020)) + 1420520000.0)

Data Column Name and Description
    :case:
        The Integrated Planning Model electricity demand case.

    :rate_name:
        The emission rate providing the pollutant and units.

    :independent_variable:
        The independent variable used in calculating the emission rate.

    :initial_year:
        The calendar year from which the rate regression curves were generated.

    :equation_rate_id:
        The emission rate equation used to calculate an emission rate at the given independent variable.

    :equation_kwh:
        The kilowatt-hour demand equation used to calculate kwh demand in the specified case; the demands calculated using
        the kwh equations are used, along with the OMEGA kwh demand value to interpolate appropriate emission rates for
        the given OMEGA session.


----

**CODE**

"""

from omega_model import *


class EmissionRatesEGU(OMEGABase):
    """
    Loads and provides access to power sector emissions factors  by calendar year.

    """

    _data = dict()  # private dict, emissions factors power sector by calendar year
    _cases = None
    _cache = dict()
    calendar_year_max = 2050

    @staticmethod
    def get_emission_rate(calendar_year, kwh_demand, rate_names):
        """

        Get emission rates by calendar year

        Args:
            calendar_year (int): calendar year for which to get emission rates
            kwh_demand (numeric): the kWh demand to use (e.g., kwh_consumption or kwh_generation)
            rate_names (str, [strs]): name of emission rate(s) to get

        Returns:
            A list of emission rates for the given kwh_demand in the given calendar_year.

        """
        locals_dict = locals()
        return_rates = list()

        kwh_low = kwh_high = 0

        if calendar_year > EmissionRatesEGU.calendar_year_max:
            calendar_year = EmissionRatesEGU.calendar_year_max

        kwh_low = eval(EmissionRatesEGU._data['low_bound', rate_names[0]]['equation_kwh'], {}, locals_dict)
        kwh_high = eval(EmissionRatesEGU._data['high_bev', rate_names[0]]['equation_kwh'], {}, locals_dict)

        if kwh_high < kwh_demand:
            kwh_high = kwh_demand

        for rate_name in rate_names:
            rate_low = eval(EmissionRatesEGU._data['low_bound', rate_name]['equation_rate_id'], {}, locals_dict)
            rate_high = eval(EmissionRatesEGU._data['high_bev', rate_name]['equation_rate_id'], {}, locals_dict)

            # interpolate the rate for kwh_demand
            rate = rate_low - (kwh_low - kwh_demand) * (rate_low - rate_high) / (kwh_low - kwh_high)

            return_rates.append(rate)

        return return_rates

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
        EmissionRatesEGU._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'emission_rates_egu'
        input_template_version = 0.1
        input_template_columns = {
            'case',
            'rate_name',
            'equation_rate_id',
            'equation_kwh'
        }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:

                rate_keys = zip(
                    df['case'],
                    df['rate_name']
                )
                df.set_index(rate_keys, inplace=True)

                EmissionRatesEGU._cases = df['case'].unique()

                EmissionRatesEGU._data = df.to_dict('index')
                # EmissionRatesEGU._data = df.set_index('calendar_year').to_dict(orient='index')

                for rate_key in rate_keys:

                    rate_eq = EmissionRatesEGU._data[rate_key]['equation_rate_id']
                    kwh_eq = EmissionRatesEGU._data[rate_key]['equation_kwh']

                    EmissionRatesEGU._data[rate_key].update({'equation_rate_id': compile(rate_eq, '<string>', 'eval'),
                                                             'equation_kwh': compile(kwh_eq, '<string>', 'eval')})

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += \
            EmissionFactorsPowersector.init_from_file(omega_globals.options.emission_factors_powersector_file,
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
