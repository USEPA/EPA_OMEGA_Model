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

        model_year,age,reg_class_id,in_use_fuel_id,voc_grams_per_mile,co_grams_per_mile,nox_grams_per_mile,pm25_grams_per_mile,so2_grams_per_gallon,benzene_grams_per_mile,butadiene13_grams_per_mile,formaldehyde_grams_per_mile,acetaldehyde_grams_per_mile,acrolein_grams_per_mile,co2_grams_per_mile,n2o_grams_per_mile,ch4_grams_per_mile
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

----

**CODE**

"""

from omega_model import *

cache = dict()


class EmissionFactorsVehicles(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_vehicles'
    index = Column('index', Integer, primary_key=True)

    model_year = Column(Numeric)
    age = Column('age', Numeric)
    in_use_fuel_id = Column('in_use_fuel_id', String)
    reg_class_ID = Column('reg_class_id', String)
    voc_grams_per_mile = Column('voc_grams_per_mile', Float)
    co_grams_per_mile = Column('co_grams_per_mile', Float)
    nox_grams_per_mile = Column('nox_grams_per_mile', Float)
    pm25_grams_per_mile = Column('pm25_grams_per_mile', Float)
    so2_grams_per_gallon = Column('so2_grams_per_gallon', Float)
    benzene_grams_per_mile = Column('benzene_grams_per_mile', Float)
    butadiene13_grams_per_mile = Column('butadiene13_grams_per_mile', Float)
    formaldehyde_grams_per_mile = Column('formaldehyde_grams_per_mile', Float)
    acetaldehyde_grams_per_mile = Column('acetaldehyde_grams_per_mile', Float)
    acrolein_grams_per_mile = Column('acrolein_grams_per_mile', Float)
    ch4_grams_per_mile = Column('ch4_grams_per_mile', Float)
    n2o_grams_per_mile = Column('n2o_grams_per_mile', Float)

    @staticmethod
    def get_emission_factors(model_year, age, reg_class_id, in_use_fuel_id, emission_factors):
        """

        Args:
            model_year: vehicle model year to get emission factors for
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """
        cache_key = '%s_%s_%s_%s_%s' % (model_year, age, reg_class_id, in_use_fuel_id, emission_factors)

        if cache_key not in cache:
            if type(emission_factors) is not list:
                cost_factors = [emission_factors]
            attrs = EmissionFactorsVehicles.get_class_attributes(emission_factors)

            result = omega_globals.session.query(*attrs) \
                .filter(EmissionFactorsVehicles.model_year == model_year) \
                .filter(EmissionFactorsVehicles.age == age) \
                .filter(EmissionFactorsVehicles.reg_class_ID == reg_class_id) \
                .filter(EmissionFactorsVehicles.in_use_fuel_id == in_use_fuel_id) \
                .all()[0]

            if len(emission_factors) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]


    @staticmethod
    def init_database_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_emission_factors-vehicles'
        input_template_version = 0.1
        input_template_columns = {'model_year', 'age', 'reg_class_id', 'in_use_fuel_id',
                                  'voc_grams_per_mile', 'co_grams_per_mile', 'nox_grams_per_mile', 'pm25_grams_per_mile', 'so2_grams_per_gallon',
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
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(EmissionFactorsVehicles(
                        model_year=df.loc[i, 'model_year'],
                        age=df.loc[i, 'age'],
                        reg_class_ID=df.loc[i, 'reg_class_id'],
                        in_use_fuel_id=df.loc[i, 'in_use_fuel_id'],
                        voc_grams_per_mile=df.loc[i, 'voc_grams_per_mile'],
                        co_grams_per_mile=df.loc[i, 'co_grams_per_mile'],
                        nox_grams_per_mile=df.loc[i, 'nox_grams_per_mile'],
                        pm25_grams_per_mile=df.loc[i, 'pm25_grams_per_mile'],
                        so2_grams_per_gallon=df.loc[i, 'so2_grams_per_gallon'],
                        benzene_grams_per_mile=df.loc[i, 'benzene_grams_per_mile'],
                        butadiene13_grams_per_mile=df.loc[i, 'butadiene13_grams_per_mile'],
                        formaldehyde_grams_per_mile=df.loc[i, 'formaldehyde_grams_per_mile'],
                        acetaldehyde_grams_per_mile=df.loc[i, 'acetaldehyde_grams_per_mile'],
                        acrolein_grams_per_mile=df.loc[i, 'acrolein_grams_per_mile'],
                        ch4_grams_per_mile=df.loc[i, 'ch4_grams_per_mile'],
                        n2o_grams_per_mile=df.loc[i, 'n2o_grams_per_mile'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        from omega_model.consumer.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        # init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file,
        #                                                             verbose=o2.options.verbose)

        init_fail += EmissionFactorsVehicles.init_database_from_file(omega_globals.options.emission_factors_vehicles_file,
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
