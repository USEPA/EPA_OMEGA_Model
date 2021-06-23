"""

**Routines to load and retrieve onroad (in-use) fuel attribute data**

Fuel data includes a name, units (e.g. gallons, kWh), energy density in MJ/unit and CO2 g/unit.

See Also:

    ``vehicles`` and ``context_fuel_prices`` modules, and ``consumer`` subpackage

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents fuel property data for on-road/in-use purposes.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,fuels,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        fuel_id,unit,energy_density_megajoules_per_unit,co2_tailpipe_emissions_grams_per_unit
        pump gasoline,gallon,129.46,8887
        US electricity,kWh,3.6,0

Data Column Name and Description

:fuel_id:
    The Fuel ID, as referenced by the ``vehicles`` and ``context_fuel_prices`` modules, and ``consumer`` subpackage.

:unit:
    Fuel unit, e.g. 'gallon', 'kWh'

:energy_density_megajoules_per_unit:
    Energy density (MJ/unit)

:co2_tailpipe_emissions_grams_per_unit:
    CO2 emissions per unit when consumed

----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class OnroadFuel(SQABase, OMEGABase):
    """
    **Loads and provides methods to access onroad fuel attribute data.**

    """

    # --- database table properties ---
    __tablename__ = 'onroad_fuels'
    fuel_ID = Column('fuel_id', String, primary_key=True)   #: name of fuel
    unit = Column(Enum(*fuel_units, validate_strings=True))  #: fuel units (e.g. gallon, kWh)
    energy_density_MJ_per_unit = Column('energy_density_megajoules_per_unit', Float)  #: fuel energy density
    co2_tailpipe_emissions_grams_per_unit = Column('co2_tailpipe_emissions_grams_per_unit', Float)  #: fuel carbon content when consumed

    @staticmethod
    def get_fuel_attributes(fuel_id, attribute_types):
        """

        Args:
            fuel_id (str): e.g. 'pump gasoline')
            attribute_types (str, [strs]): name of attribute to retrieve

        Returns:
            Attribute value or list of attribute values.

        Example:

            ::

                carbon_intensity_gasoline =
                    Fuel.get_fuel_attributes('pump gasoline', 'co2_tailpipe_emissions_grams_per_unit')

        """
        cache_key = '%s_%s' % (fuel_id, attribute_types)

        if cache_key not in cache:
            if type(attribute_types) is not list:
                attribute_types = [attribute_types]

            attrs = OnroadFuel.get_class_attributes(attribute_types)

            result = omega_globals.session.query(*attrs). \
                filter(OnroadFuel.fuel_ID == fuel_id).all()[0]

            if len(attribute_types) == 1:
                cache[cache_key] = result[0]
            else:
                cache[cache_key] = result

        return cache[cache_key]


    @staticmethod
    def validate_fuel_ID(fuel_id):
        """
        Validate fuel ID

        Args:
            fuel_id (str): e.g. 'pump gasoline')

        Returns:
            True if the fuel ID is valid, False otherwise

        """
        result = omega_globals.session.query(OnroadFuel.fuel_ID).filter(OnroadFuel.fuel_ID == fuel_id).all()
        if result:
            return True
        else:
            return False

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

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'fuels'
        input_template_version = 0.1
        input_template_columns = {'fuel_id', 'unit', 'energy_density_megajoules_per_unit',
                                  'co2_tailpipe_emissions_grams_per_unit'}

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
                    obj_list.append(OnroadFuel(
                        fuel_ID=df.loc[i, 'fuel_id'],
                        unit=df.loc[i, 'unit'],
                        energy_density_MJ_per_unit=df.loc[i, 'energy_density_megajoules_per_unit'],
                        co2_tailpipe_emissions_grams_per_unit=df.loc[i, 'co2_tailpipe_emissions_grams_per_unit'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_globals.engine.echo = omega_globals.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += OnroadFuel.init_database_from_file(omega_globals.options.fuels_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        else:
            print(init_fail)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
