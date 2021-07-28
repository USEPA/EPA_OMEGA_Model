"""

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents electricity generating unit emission rates by calendar year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,context_emission_factors-powersector,input_template_version:,0.1

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

cache = dict()


class EmissionFactorsPowersector(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'emission_factors_powersector'
    index = Column(Integer, primary_key=True)

    calendar_year = Column(Numeric)
    voc_grams_per_kwh = Column(Float)
    co_grams_per_kwh = Column(Float)
    nox_grams_per_kwh = Column(Float)
    pm25_grams_per_kwh = Column(Float)
    sox_grams_per_kwh = Column(Float)
    benzene_grams_per_kwh = Column(Float)
    butadiene13_grams_per_kwh = Column(Float)
    formaldehyde_grams_per_kwh = Column(Float)
    acetaldehyde_grams_per_kwh = Column(Float)
    acrolein_grams_per_kwh = Column(Float)
    ch4_grams_per_kwh = Column(Float)
    n2o_grams_per_kwh = Column(Float)
    co2_grams_per_kwh = Column(Float)

    @staticmethod
    def get_emission_factors(calendar_year, emission_factors):
        """

        Args:
            calendar_year: calendar year to get emission factors for
            emission_factors: name of emission factor or list of emission factor attributes to get

        Returns: emission factor or list of emission factors

        """
        cache_key = '%s_%s' % (calendar_year, emission_factors)

        if cache_key not in cache:
            if type(emission_factors) is not list:
                cost_factors = [emission_factors]
            attrs = EmissionFactorsPowersector.get_class_attributes(emission_factors)

            result = omega_globals.session.query(*attrs).filter(EmissionFactorsPowersector.calendar_year == calendar_year).all()[0]

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

        input_template_name = 'context_emission_factors-powersector'
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

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(EmissionFactorsPowersector(
                        calendar_year=df.loc[i, 'calendar_year'],
                        voc_grams_per_kwh=df.loc[i, 'voc_grams_per_kwh'],
                        co_grams_per_kwh=df.loc[i, 'co_grams_per_kwh'],
                        nox_grams_per_kwh=df.loc[i, 'nox_grams_per_kwh'],
                        pm25_grams_per_kwh=df.loc[i, 'pm25_grams_per_kwh'],
                        sox_grams_per_kwh=df.loc[i, 'sox_grams_per_kwh'],
                        benzene_grams_per_kwh=df.loc[i, 'benzene_grams_per_kwh'],
                        butadiene13_grams_per_kwh=df.loc[i, 'butadiene13_grams_per_kwh'],
                        formaldehyde_grams_per_kwh=df.loc[i, 'formaldehyde_grams_per_kwh'],
                        acetaldehyde_grams_per_kwh=df.loc[i, 'acetaldehyde_grams_per_kwh'],
                        acrolein_grams_per_kwh=df.loc[i, 'acrolein_grams_per_kwh'],
                        ch4_grams_per_kwh=df.loc[i, 'ch4_grams_per_kwh'],
                        n2o_grams_per_kwh=df.loc[i, 'n2o_grams_per_kwh'],
                        co2_grams_per_kwh=df.loc[i, 'co2_grams_per_kwh'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        from omega_model.consumer.market_classes import MarketClass  # needed for market class ID

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        # init_fail += MarketClass.init_database_from_file(o2.options.market_classes_file,
        #                                                             verbose=o2.options.verbose)

        init_fail += EmissionFactorsPowersector.init_database_from_file(omega_globals.options.emission_factors_powersector_file,
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
