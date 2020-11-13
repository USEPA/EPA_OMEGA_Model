"""
emission_factors_vehicles.py
============================


"""

import o2  # import global variables
from usepa_omega2 import *


class EmissionFactorsVehicles(SQABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_vehicles'
    index = Column('index', Integer, primary_key=True)

    model_year = Column('model_year', Numeric)
    age = Column('age', Numeric)
    in_use_fuel_id = Column('in_use_fuel_id', String)
    reg_class_id = Column('reg_class_id', String)
    voc_grams_per_mile = Column('voc_grams_per_mile', Numeric)
    co_grams_per_mile = Column('co_grams_per_mile', Numeric)
    nox_grams_per_mile = Column('nox_grams_per_mile', Numeric)
    pm25_grams_per_mile = Column('pm25_grams_per_mile', Numeric)
    sox_grams_per_gallon = Column('sox_grams_per_gallon', Numeric)
    benzene_grams_per_mile = Column('benzene_grams_per_mile', Numeric)
    butadiene_grams_per_mile = Column('13butadiene_grams_per_mile', Numeric)
    formaldehyde_grams_per_mile = Column('formaldehyde_grams_per_mile', Numeric)
    acetaldehyde_grams_per_mile = Column('acetaldehyde_grams_per_mile', Numeric)
    acrolein_grams_per_mile = Column('acrolein_grams_per_mile', Numeric)
    ch4_grams_per_mile = Column('ch4_grams_per_mile', Numeric)
    n2o_grams_per_mile = Column('n2o_grams_per_mile', Numeric)

    def __repr__(self):
        return f"<OMEGA2 {type(self).__name__} object at 0x{id(self)}>"

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite(f'\nInitializing database from {filename}...')

        input_template_name = 'context_emission_factors-vehicles'
        input_template_version = 0.1
        input_template_columns = {'model_year', 'age', 'reg_class_id', 'in_use_fuel_id',
                                  'voc_grams_per_mile', 'co_grams_per_mile', 'nox_grams_per_mile', 'pm25_grams_per_mile', 'sox_grams_per_gallon',
                                  'benzene_grams_per_mile', '13butadiene_grams_per_mile', 'formaldehyde_grams_per_mile',
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
                        reg_class_id=df.loc[i, 'reg_class_id'],
                        in_use_fuel_id=df.loc[i, 'in_use_fuel_id'],
                        voc_grams_per_mile=df.loc[i, 'voc_grams_per_mile'],
                        co_grams_per_mile=df.loc[i, 'co_grams_per_mile'],
                        nox_grams_per_mile=df.loc[i, 'nox_grams_per_mile'],
                        pm25_grams_per_mile=df.loc[i, 'pm25_grams_per_mile'],
                        sox_grams_per_gallon=df.loc[i, 'sox_grams_per_gallon'],
                        benzene_grams_per_mile=df.loc[i, 'benzene_grams_per_mile'],
                        butadiene_grams_per_mile=df.loc[i, '13butadiene_grams_per_mile'],
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
