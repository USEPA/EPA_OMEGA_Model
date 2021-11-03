"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents refinery emission rates by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_emission_factors-refinery,input_template_version:,0.2

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

from omega_model import *


class EmissionFactorsRefinery(OMEGABase):
    """
    Loads and provides access to refinery emission factors by calendar year and in-use fuel id.

    """

    _data = dict()  # private dict, emissions factors refinery by calendar year and in-use fuel id
    _data_iufid_cy = dict()  # private dict, emissions factors refinery in-use fuel id calendar years

    @staticmethod
    def get_emission_factors(calendar_year, in_use_fuel_id, emission_factors):
        """

        Get emission factors by calendar year and in-use fuel ID

        Args:
            calendar_year (int): calendar year to get emission factors for
            emission_factors (str, [strs]): name of emission factor or list of emission factor attributes to get

        Returns:
            Emission factor or list of emission factors

        """
        calendar_years = EmissionFactorsRefinery._data_iufid_cy['calendar_year'][in_use_fuel_id]
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        factors = []
        for ef in emission_factors:
            factors.append(EmissionFactorsRefinery._data[year, in_use_fuel_id][ef])

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
        EmissionFactorsRefinery._data.clear()
        EmissionFactorsRefinery._data_iufid_cy.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_emission_factors-refinery'
        input_template_version = 0.2
        input_template_columns = {'calendar_year', 'in_use_fuel_id',
                                  'voc_grams_per_gallon', 'co_grams_per_gallon', 'nox_grams_per_gallon',
                                  'pm25_grams_per_gallon', 'sox_grams_per_gallon', 'benzene_grams_per_gallon',
                                  'butadiene13_grams_per_gallon', 'formaldehyde_grams_per_gallon',
                                  'acetaldehyde_grams_per_gallon', 'acrolein_grams_per_gallon',
                                  'ch4_grams_per_gallon', 'n2o_grams_per_gallon', 'co2_grams_per_gallon'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                EmissionFactorsRefinery._data = \
                    df.set_index(['calendar_year', 'in_use_fuel_id']).sort_index().to_dict(orient='index')
                EmissionFactorsRefinery._data_iufid_cy = \
                    df[['calendar_year', 'in_use_fuel_id']].set_index('in_use_fuel_id').to_dict(orient='series')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += EmissionFactorsRefinery.init_from_file(omega_globals.options.emission_factors_refinery_file,
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
