"""

**Routines to load and provide access to 'incentives' such as production multipliers for battery-electric vehicles.**

Currently, only production multipliers are implemented here, but other incentives may be added later.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents production multiplier incentives as a function of vehicle attribute values.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,production_multipliers,input_template_version:,0.21

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,fueling_class:BEV
        2020, 2.0

Data Column Name and Description
    :start_year:
        Start year of incentive, incentive applies until the next available start year

    :dynamic column(s):
        Zero or more dynamic columns with the format
        ``{attribute_name}:{attribute_value}``

        Unspecified vehicle attribute-value pairs will have a production multiplier of 1.0, so only non-1.0
        multipliers need to be specified here.

        Example:
            ``fueling_class:BEV`` => ``if vehicle.fueling_class == 'BEV' then apply production multiplier``

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class Incentives(OMEGABase):
    """
    **Loads and provides access to GHG incentives.**

    """
    
    _data = dict()
    
    @staticmethod
    def get_production_multiplier(vehicle):
        """
        Get production multiplier (if any) for the given vehicle.

        Args:
            vehicle (Vehicle): the vehicle to get the multiplier for

        Returns:
            The production multiplier, if applicable, or 1.0

        """
        production_multiplier = 1

        start_years = Incentives._data['start_year']
        if len(start_years[start_years <= vehicle.model_year]) > 0:
            cache_key = max(start_years[start_years <= vehicle.model_year])

            if cache_key in Incentives._data:
                calcs = Incentives._data[cache_key]
                for calc, multiplier in calcs.items():
                    select_attribute, select_value = calc.split(':')
                    if vehicle.__getattribute__(select_attribute) == select_value:
                        production_multiplier = multiplier

        return production_multiplier

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
        Incentives._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        # don't forget to update the module docstring with changes hereƒß
        input_template_name = 'production_multipliers'
        input_template_version = 0.21
        input_template_columns = {'start_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                df = df.set_index('start_year')
                df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')

                Incentives._data = df.to_dict(orient='index')
                Incentives._data['start_year'] = np.array([*Incentives._data])  # CU

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += Incentives.init_from_file(omega_globals.options.production_multipliers_file,
                                               verbose=omega_globals.options.verbose)

        if not init_fail:
            class VehicleDummy:
                """
                Dummy Vehicle class.

                """
                model_year = 2020
                fueling_class = 'BEV'

            v = VehicleDummy()
            print(Incentives.get_production_multiplier(v))

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
