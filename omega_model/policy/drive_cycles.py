"""

**Routines to load, validate, and provide access to drive cycle definition data**

Drive cycles and cycle phasese are defined by a name, a distance and a brief description.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents drive cycles by name/phase, a distance and a brief description.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,drive_cycles,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        drive_cycle_id,drive_cycle_distance_miles,description,
        cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile,3.591,Charge Sustaining EPA UDDS cycle phase 1 CO2e g/mi,
        cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile,10.26,Charge Sustaining EPA HWFET cycle CO2e g/mi,

Data Column Name and Description

:drive_cycle_id:
    Name of the drive cycle or drive cycle phase.  This must be consistent the leaves of the drive cycle weights tree,
    see also ``drive_cycle_weights.DriveCycleWeights``.

:drive_cycle_distance_miles:
    Drive cycle/phase distances (miles).

:description:
    A brief description of the drive cycle/phase.

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class DriveCycles(OMEGABase):
    """
    **Load and provides routines to access drive cycle descriptive data**

    """

    _data = pd.DataFrame()

    @staticmethod
    def validate_drive_cycle_id(drive_cycle_id):
        """
        Validate drive cycle name.

        Args:
            drive_cycle_id(str): drive cycle name to validate e.g. 'cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile'

        Returns:
            True if drive cycle name is in the list of known drive cycles.

        """
        return drive_cycle_id in DriveCycles._data['drive_cycle_id'].values

    @staticmethod
    def get_drive_cycles():
        """
        Get list of known drive cycle names

        Returns:
            List of known drive cycle names

        """
        return DriveCycles._data['drive_cycle_id'].to_list()

    @staticmethod
    def get_drive_cycle_distance_miles(drive_cycle_id):
        """
        Get the target driven distance (in miles) of a drive cycle

        Args:
            drive_cycle_id(str): drive cycle name

        Returns:
            Drive cycle distance in miles

        """
        return DriveCycles._data['drive_cycle_distance_miles'].loc[DriveCycles._data['drive_cycle_id'] == drive_cycle_id].item()

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

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'drive_cycles'
        input_template_version = 0.2
        input_template_columns = {'drive_cycle_id', 'drive_cycle_distance_miles', 'description'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                DriveCycles._data['drive_cycle_id'] = df['drive_cycle_id']
                DriveCycles._data['drive_cycle_distance_miles'] = df['drive_cycle_distance_miles']
                DriveCycles._data['description'] = df['description']

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            DriveCycles._data.to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'drive_cycle_data.csv', index=False)

            print(DriveCycles.validate_drive_cycle_id('cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile'))
            print(DriveCycles.validate_drive_cycle_id('cd_hwfet:cert_direct_oncycle_kwh_per_mile'))
            print(DriveCycles.get_drive_cycle_distance_miles('cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile'))

            print(DriveCycles.get_drive_cycles())

        else:
            print(init_fail)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
