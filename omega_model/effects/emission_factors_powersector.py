"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents electricity generating unit emission rates by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,emission_factors_powersector,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        calendar_year,voc_grams_per_kwh,co_grams_per_kwh,nox_grams_per_kwh,pm25_grams_per_kwh,sox_grams_per_kwh,benzene_grams_per_kwh,butadiene13_grams_per_kwh,formaldehyde_grams_per_kwh,acetaldehyde_grams_per_kwh,acrolein_grams_per_kwh,co2_grams_per_kwh,n2o_grams_per_kwh,ch4_grams_per_kwh
        2020,0.055181393,0.338895846,0.240906423,0.070888642,0.236594079,0.001536237,0,3.79E-05,6.40E-05,5.95E-05,479.8,0.007436538,3.322482776

Data Column Name and Description
    :calendar_year:
        The calendar year for which $/kWh values are applicable.

    :voc_grams_per_kwh:
        The electric generating unit emission factors follow the structure pollutant_units where units are grams per kWh of electricity.

----

**CODE**

"""

from omega_model import *


class EmissionFactorsPowersector(OMEGABase):
    """
    Loads and provides access to power sector emissions factors  by calendar year.

    """

    _data = dict()  # private dict, emissions factors power sector by calendar year

    @staticmethod
    def get_emission_factors(calendar_year, emission_factors):
        """

        Get emission factors by calendar year

        Args:
            calendar_year (int): calendar year to get emission factors for
            emission_factors (str, [strs]): name of emission factor or list of emission factor attributes to get

        Returns:
            Emission factor or list of emission factors

        """
        calendar_years = EmissionFactorsPowersector._data.keys()
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        factors = []
        for ef in emission_factors:
            factors.append(EmissionFactorsPowersector._data[year][ef])

        if len(emission_factors) == 1:
            return factors[0]
        else:
            return factors

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
        EmissionFactorsPowersector._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'emission_factors_powersector'
        input_template_version = 0.1
        input_template_columns = {'calendar_year',
                                  'voc_grams_per_kwh', 'co_grams_per_kwh', 'nox_grams_per_kwh', 'pm25_grams_per_kwh', 'sox_grams_per_kwh',
                                  'benzene_grams_per_kwh', 'butadiene13_grams_per_kwh', 'formaldehyde_grams_per_kwh',
                                  'acetaldehyde_grams_per_kwh', 'acrolein_grams_per_kwh',
                                  'ch4_grams_per_kwh', 'n2o_grams_per_kwh', 'co2_grams_per_kwh'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                EmissionFactorsPowersector._data = df.set_index('calendar_year').to_dict(orient='index')

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
