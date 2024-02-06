"""

**Drive cycle ballast module.**

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents the additional weight present during certification drive cycle testing, in pounds.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,drive_cycle_ballast,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,reg_class_id,ballast_lbs,
        1974,car,300,
        1974,truck,300,
        1974,mediumduty,(vehicle.gvwr_lbs + vehicle.curbweight_lbs)/2,

Data Column Name and Description

:start_year:
    Start year of parameters, parameters apply until the next available start year

:reg_class_id:
    Name of the regulatory class, e.g. 'car', 'truck', etc

:ballast_lbs:
    The drive cycle test weight ballast in pounds, scalar value or expression to be evaluated

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class DriveCycleBallast(OMEGABase):
    """
    Loads and provides access to drive cycle ballast data.

    """
    _data = dict()

    @staticmethod
    def get_ballast_lbs(vehicle):
        """
        Get drive cycle ballast for the given vehicle.

        Args:
            vehicle (Vehicle): the vehicle to get drive cycle ballast for

        Returns:
            Drive cycle ballast in pounds

        """

        cache_key = (vehicle.reg_class_id, vehicle.model_year)

        if True or cache_key not in DriveCycleBallast._data:

            start_years = DriveCycleBallast._data[vehicle.reg_class_id]['start_year']
            if len(start_years[start_years <= vehicle.model_year]) > 0:
                calendar_year = max(start_years[start_years <= vehicle.model_year])

                DriveCycleBallast._data[cache_key] = \
                    Eval.eval(DriveCycleBallast._data[vehicle.reg_class_id, calendar_year]['ballast_lbs'], {},
                              {'vehicle': vehicle})
            else:
                raise Exception('Missing drive cycle ballast parameters for %s, %d or prior' %
                                (vehicle.reg_class_id, vehicle.model_year))

        return DriveCycleBallast._data[cache_key]

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
        DriveCycleBallast._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'drive_cycle_ballast'
        input_template_version = 0.1
        input_template_columns = {'start_year', 'reg_class_id', 'ballast_lbs'
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')

            validation_dict = {'reg_class_id': list(legacy_reg_classes)}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            DriveCycleBallast._data = df.set_index(['reg_class_id', 'start_year']).sort_index().to_dict(orient='index')

            for rc in df['reg_class_id'].unique():
                DriveCycleBallast._data[rc] = {'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += DriveCycleBallast.init_from_file(omega_globals.options.drive_cycle_ballast_file,
                                                      verbose=omega_globals.options.verbose)

        if not init_fail:
            class Vehicle:
                """
                Dummy Vehicle class.

                """
                model_year = 2020
                reg_class_id = list(legacy_reg_classes)[0]

            print(DriveCycleBallast.get_ballast_lbs(Vehicle))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
