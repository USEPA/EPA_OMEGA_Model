"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents tailpipe emission rates by model year, age, reg-class and fuel type as estimated by EPA's MOVES model.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,emission_factors_vehicles,input_template_version:,0.1

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

    @staticmethod
    def get_emission_factors(model_year, age, reg_class_id, in_use_fuel_id, emission_factors):
        """

        Args:
            model_year (int): vehicle model year for which to get emission factors
            age (int): the vehicle age
            reg_class_id (str): the regulatory class, e.g., 'car' or 'truck'
            in_use_fuel_id (str): the liquid fuel ID, e.g., 'pump gasoline'
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """
        import pandas as pd

        cache_key = (model_year, age, reg_class_id, in_use_fuel_id, emission_factors)

        if cache_key not in EmissionFactorsVehicles._data:

            calendar_years = np.atleast_1d(EmissionFactorsVehicles._data['model_year'][in_use_fuel_id])
            ages = np.array(EmissionFactorsVehicles._data['age'][in_use_fuel_id])

            year = max([yr for yr in calendar_years if yr <= model_year])
            age_use = max([a for a in ages if a <= age])

            factors = []
            for ef in emission_factors:
                factors.append(EmissionFactorsVehicles._data[year, age_use, reg_class_id, in_use_fuel_id][ef])

            if len(emission_factors) == 1:
                EmissionFactorsVehicles._data[cache_key] = factors[0]
            else:
                EmissionFactorsVehicles._data[cache_key] = factors

        return EmissionFactorsVehicles._data[cache_key]

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

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'emission_factors_vehicles'
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

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

        if not template_errors:
            from context.onroad_fuels import OnroadFuel

            # validate columns
            validation_dict = {'in_use_fuel_id': OnroadFuel.fuel_ids,
                               'reg_class_id': list(legacy_reg_classes)}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            EmissionFactorsVehicles._data = \
                df.set_index(['model_year', 'age', 'reg_class_id', 'in_use_fuel_id']).sort_index()\
                    .to_dict(orient='index')
            EmissionFactorsVehicles._data.update(
                df[['model_year', 'age', 'in_use_fuel_id']].set_index('in_use_fuel_id').to_dict(orient='series'))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += EmissionFactorsVehicles.init_from_file(omega_globals.options.emission_factors_vehicles_file,
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
