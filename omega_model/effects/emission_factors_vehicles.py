"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents tailpipe emission rates by model year, age, reg-class and fuel type as estimated by EPA's MOVES model.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_emission_factors-vehicles,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        model_year,age,reg_class_id,in_use_fuel_id,voc_grams_per_mile,co_grams_per_mile,nox_grams_per_mile,pm25_grams_per_mile,sox_grams_per_gallon,benzene_grams_per_mile,butadiene13_grams_per_mile,formaldehyde_grams_per_mile,acetaldehyde_grams_per_mile,acrolein_grams_per_mile,co2_grams_per_mile,n2o_grams_per_mile,ch4_grams_per_mile
        2020,0,car,pump gasoline,0.038838978,0.934237929,0.041727278,0.001925829,0.001648851,0.001641638,0.0003004,0.000441563,0.000767683,4.91E-05,,0.004052681,0.005520596
        2020,0,truck,pump gasoline,0.035665375,1.068022441,0.054597497,0.002444363,0.002240974,0.001499163,0.000262733,0.000411881,0.000764069,4.45E-05,,0.005146965,0.007103921


Data Column Name and Description
    :model_year:
        The model year of vehicles, e.g. 2020

    :age:
        The age of vehicles

    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :voc_grams_per_mile:
        The vehicle emission factors follow the structure pollutant_units where units are grams per mile.

----

**CODE**

"""

from omega_model import *


class EmissionFactorsVehicles(OMEGABase):
    """
    Loads and provides access to vehicle emission factors by model year, age, legacy reg class ID and in-use fuel ID.

    """

    _data = dict()  # private dict, emission factors vehicles by model year, age, legacy reg class ID and in-use fuel ID
    _data_iufid_cy = dict()  # private dict, emissions factors vehicles in-use fuel id calendar years

    @staticmethod
    def get_emission_factors(model_year, age, reg_class_id, in_use_fuel_id, emission_factors):
        """

        Args:
            model_year: vehicle model year to get emission factors for
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """

        calendar_years = EmissionFactorsVehicles._data_iufid_cy['model_year'][in_use_fuel_id]
        year = max([yr for yr in calendar_years if yr <= model_year])

        factors = []
        for ef in emission_factors:
            factors.append(EmissionFactorsVehicles._data[year, age, reg_class_id, in_use_fuel_id][ef])

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
        EmissionFactorsVehicles._data.clear()
        EmissionFactorsVehicles._data_iufid_cy.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_emission_factors-vehicles'
        input_template_version = 0.1
        input_template_columns = {'model_year', 'age', 'reg_class_id', 'in_use_fuel_id',
                                  'voc_grams_per_mile', 'co_grams_per_mile', 'nox_grams_per_mile', 'pm25_grams_per_mile', 'sox_grams_per_gallon',
                                  'benzene_grams_per_mile', 'butadiene13_grams_per_mile', 'formaldehyde_grams_per_mile',
                                  'acetaldehyde_grams_per_mile', 'acrolein_grams_per_mile',
                                  'ch4_grams_per_mile', 'n2o_grams_per_mile'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                EmissionFactorsVehicles._data = \
                    df.set_index(['model_year', 'age', 'reg_class_id', 'in_use_fuel_id']).sort_index()\
                        .to_dict(orient='index')
                EmissionFactorsVehicles._data_iufid_cy = \
                    df[['model_year', 'in_use_fuel_id']].set_index('in_use_fuel_id').to_dict(orient='series')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        import importlib

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        # init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file,
        #                                                             verbose=o2.options.verbose)

        init_fail += EmissionFactorsVehicles.init_from_file(omega_globals.options.emission_factors_vehicles_file,
                                                            verbose=omega_globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
