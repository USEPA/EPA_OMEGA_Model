"""
emission_factors_vehicles.py
============================


"""

import o2  # import global variables
from usepa_omega2 import *

cache = dict()


class EmissionFactorsVehicles(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_vehicles'
    index = Column('index', Integer, primary_key=True)

    model_year = Column('model_year', Numeric)
    age = Column('age', Numeric)
    in_use_fuel_id = Column('in_use_fuel_id', String)
    reg_class_ID = Column('reg_class_id', String)
    voc_grams_per_mile = Column('voc_grams_per_mile', Float)
    co_grams_per_mile = Column('co_grams_per_mile', Float)
    nox_grams_per_mile = Column('nox_grams_per_mile', Float)
    pm25_grams_per_mile = Column('pm25_grams_per_mile', Float)
    sox_grams_per_gallon = Column('sox_grams_per_gallon', Float)
    benzene_grams_per_mile = Column('benzene_grams_per_mile', Float)
    butadiene13_grams_per_mile = Column('butadiene13_grams_per_mile', Float)
    formaldehyde_grams_per_mile = Column('formaldehyde_grams_per_mile', Float)
    acetaldehyde_grams_per_mile = Column('acetaldehyde_grams_per_mile', Float)
    acrolein_grams_per_mile = Column('acrolein_grams_per_mile', Float)
    ch4_grams_per_mile = Column('ch4_grams_per_mile', Float)
    n2o_grams_per_mile = Column('n2o_grams_per_mile', Float)

    @staticmethod
    def get_emission_factors(model_year, age, reg_class_id, emission_factors):
        """

        Args:
            model_year: vehicle model year to get emission factors for
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """
        cache_key = '%s_%s_%s_%s' % (model_year, age, reg_class_id, emission_factors)

        if cache_key not in cache:
            if type(emission_factors) is not list:
                cost_factors = [emission_factors]
            attrs = EmissionFactorsVehicles.get_class_attributes(emission_factors)

            result = o2.session.query(*attrs) \
                .filter(EmissionFactorsVehicles.model_year == model_year) \
                .filter(EmissionFactorsVehicles.age == age) \
                .filter(EmissionFactorsVehicles.reg_class_ID == reg_class_id) \
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
                        sox_grams_per_gallon=df.loc[i, 'sox_grams_per_gallon'],
                        benzene_grams_per_mile=df.loc[i, 'benzene_grams_per_mile'],
                        butadiene13_grams_per_mile=df.loc[i, 'butadiene13_grams_per_mile'],
                        formaldehyde_grams_per_mile=df.loc[i, 'formaldehyde_grams_per_mile'],
                        acetaldehyde_grams_per_mile=df.loc[i, 'acetaldehyde_grams_per_mile'],
                        acrolein_grams_per_mile=df.loc[i, 'acrolein_grams_per_mile'],
                        ch4_grams_per_mile=df.loc[i, 'ch4_grams_per_mile'],
                        n2o_grams_per_mile=df.loc[i, 'n2o_grams_per_mile'],
                    ))
                o2.session.add_all(obj_list)
                o2.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        from usepa_omega2.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        # init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
        #                                                             verbose=o2.options.verbose)

        init_fail = init_fail + EmissionFactorsVehicles.init_database_from_file(o2.options.emission_factors_vehicles_file,
                                                                                verbose=o2.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
