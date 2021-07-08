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
        The calendar year for which $/ton values are applicable.

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

----

**CODE**

"""

from omega_model import *

cache = dict()


class EmissionFactorsRefinery(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_refinery'
    index = Column('index', Integer, primary_key=True)

    calendar_year = Column(Numeric)
    in_use_fuel_id = Column('in_use_fuel_id', String)
    voc_grams_per_gallon = Column('voc_grams_per_gallon', Float)
    co_grams_per_gallon = Column('co_grams_per_gallon', Float)
    nox_grams_per_gallon = Column('nox_grams_per_gallon', Float)
    pm25_grams_per_gallon = Column('pm25_grams_per_gallon', Float)
    sox_grams_per_gallon = Column('sox_grams_per_gallon', Float)
    benzene_grams_per_gallon = Column('benzene_grams_per_gallon', Float)
    butadiene13_grams_per_gallon = Column('butadiene13_grams_per_gallon', Float)
    formaldehyde_grams_per_gallon = Column('formaldehyde_grams_per_gallon', Float)
    acetaldehyde_grams_per_gallon = Column('acetaldehyde_grams_per_gallon', Float)
    acrolein_grams_per_gallon = Column('acrolein_grams_per_gallon', Float)
    co2_grams_per_gallon = Column('co2_grams_per_gallon', Float)
    ch4_grams_per_gallon = Column('ch4_grams_per_gallon', Float)
    n2o_grams_per_gallon = Column('n2o_grams_per_gallon', Float)

    @staticmethod
    def get_emission_factors(calendar_year, fuel, emission_factors):
        """

        Args:
            calendar_year: calendar year to get emission factors for
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """
        calendar_years = pd.Series(sql_unpack_result(omega_globals.session.query(EmissionFactorsRefinery.calendar_year).all())).unique()
        year = max([yr for yr in calendar_years if yr <= calendar_year])

        cache_key = '%s_%s_%s' % (year, fuel, emission_factors)

        if cache_key not in cache:
            if type(emission_factors) is not list:
                emission_factors = [emission_factors]
            attrs = EmissionFactorsRefinery.get_class_attributes(emission_factors)

            result = omega_globals.session.query(*attrs) \
                .filter(EmissionFactorsRefinery.calendar_year == year) \
                .filter(EmissionFactorsRefinery.in_use_fuel_id == fuel).all()[0]

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

        input_template_name = 'context_emission_factors-refinery'
        input_template_version = 0.2
        input_template_columns = {'calendar_year', 'in_use_fuel_id',
                                  'voc_grams_per_gallon', 'co_grams_per_gallon', 'nox_grams_per_gallon', 'pm25_grams_per_gallon', 'sox_grams_per_gallon',
                                  'benzene_grams_per_gallon', 'butadiene13_grams_per_gallon', 'formaldehyde_grams_per_gallon',
                                  'acetaldehyde_grams_per_gallon', 'acrolein_grams_per_gallon',
                                  'ch4_grams_per_gallon', 'n2o_grams_per_gallon', 'co2_grams_per_gallon'}

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
                    obj_list.append(EmissionFactorsRefinery(
                        calendar_year=df.loc[i, 'calendar_year'],
                        in_use_fuel_id=df.loc[i, 'in_use_fuel_id'],
                        voc_grams_per_gallon=df.loc[i, 'voc_grams_per_gallon'],
                        co_grams_per_gallon=df.loc[i, 'co_grams_per_gallon'],
                        nox_grams_per_gallon=df.loc[i, 'nox_grams_per_gallon'],
                        pm25_grams_per_gallon=df.loc[i, 'pm25_grams_per_gallon'],
                        sox_grams_per_gallon=df.loc[i, 'sox_grams_per_gallon'],
                        benzene_grams_per_gallon=df.loc[i, 'benzene_grams_per_gallon'],
                        butadiene13_grams_per_gallon=df.loc[i, 'butadiene13_grams_per_gallon'],
                        formaldehyde_grams_per_gallon=df.loc[i, 'formaldehyde_grams_per_gallon'],
                        acetaldehyde_grams_per_gallon=df.loc[i, 'acetaldehyde_grams_per_gallon'],
                        acrolein_grams_per_gallon=df.loc[i, 'acrolein_grams_per_gallon'],
                        co2_grams_per_gallon=df.loc[i, 'co2_grams_per_gallon'],
                        ch4_grams_per_gallon=df.loc[i, 'ch4_grams_per_gallon'],
                        n2o_grams_per_gallon=df.loc[i, 'n2o_grams_per_gallon'],
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

        init_fail += EmissionFactorsRefinery.init_database_from_file(omega_globals.options.emission_factors_refinery_file,
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
