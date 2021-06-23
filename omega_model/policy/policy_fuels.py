"""

**Routines to load and provide access to policy-defined fuel attributes.**

The primary fuel attribute is CO2 grams per unit (i.e. g/gallon, g/kWh) when consumed, by policy year.

Used by ``policy_fuel_upstream`` functions.

See Also:

    ``policy_fuel_upstream`` module

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents fuel property data for compliance purposes, by policy year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,ghg_standards-fuels,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        fuel_id,start_year,cert_co2_grams_per_unit
        US electricity,2020,534
        gasoline,2020,8887

Data Column Name and Description

:fuel_id:
    The Fuel ID, as referenced by the ``policy_fuel_upstream`` module.

:start_year:
    Start year of fuel properties, properties apply until the next available start year

:cert_co2_grams_per_unit:
    CO2 emissions per unit when consumed, for compliance purposes

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

cache = dict()


class PolicyFuel(SQABase, OMEGABase):
    """
    **Provides methods to store and access policy fuel attributes.**

    """
    # --- database table properties ---
    __tablename__ = 'policy_fuels'
    index = Column('index', Integer, primary_key=True)  #: database index
    fuel_ID = Column('fuel_id', String)  #: fuel iD (e.g. 'gasoline', 'US electricity')
    calendar_year = Column(Numeric)  #: calendar year (or start year of fuel attributes)
    cert_co2_grams_per_unit = Column('cert_co2_grams_per_unit', Float)  #: emitted CO2 grams per unit when consumed

    @staticmethod
    def get_fuel_attributes(calendar_year, fuel_id, attribute_types):
        """
        Get fuel attributes for the given calendar year and fuel

        Args:
            calendar_year (numeric): calendar year to get properties in
            fuel_id (str): (e.g. 'gasoline', 'US electricity')
            attribute_types (str, [str]): name(s) of attributes to get, (e.g. 'cert_co2_grams_per_unit')

        Returns:
            Attribute value(s) as scalars or tuples if multiple ``attribute_types``.

        """
        start_years = cache[fuel_id]
        calendar_year = max(start_years[start_years <= calendar_year])

        cache_key = '%s_%s_%s' % (calendar_year, fuel_id, attribute_types)

        if cache_key not in cache:
            if type(attribute_types) is not list:
                attribute_types = [attribute_types]

            attrs = PolicyFuel.get_class_attributes(attribute_types)

            result = omega_globals.session.query(*attrs) \
                .filter(PolicyFuel.fuel_ID == fuel_id) \
                .filter(PolicyFuel.calendar_year == calendar_year) \
                .all()[0]

            if len(attribute_types) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'ghg_standards-fuels'
        input_template_version = 0.1
        input_template_columns = {'fuel_id', 'start_year', 'cert_co2_grams_per_unit'}

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
                    obj_list.append(PolicyFuel(
                        fuel_ID=df.loc[i, 'fuel_id'],
                        calendar_year=df.loc[i, 'start_year'],
                        cert_co2_grams_per_unit=df.loc[i, 'cert_co2_grams_per_unit'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                for fid in df['fuel_id'].unique():
                    cache[fid] = np.array(df['start_year'].loc[df['fuel_id'] == fid])

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += PolicyFuel.init_database_from_file(omega_globals.options.ghg_standards_fuels_file,
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
