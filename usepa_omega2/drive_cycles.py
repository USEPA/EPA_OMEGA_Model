"""
drive_cycles.py
===============


"""

print('importing %s' % __file__)

from usepa_omega2 import *


class DriveCycles(OMEGABase):
    data = pd.DataFrame()

    @staticmethod
    def validate_drive_cycle_ID(drive_cycle_id):
        return drive_cycle_id in DriveCycles.data['drive_cycle_id'].values

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'drive_cycles'
        input_template_version = 0.1
        input_template_columns = {'drive_cycle_id', 'description'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                DriveCycles.data['drive_cycle_id'] = df['drive_cycle_id']
                DriveCycles.data['description'] = df['description']

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = o2.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + DriveCycles.init_from_file(o2.options.drive_cycles_file,
                                                           verbose=o2.options.verbose)

        if not init_fail:
            fileio.validate_folder(o2.options.database_dump_folder)
            DriveCycles.data.to_csv(
                o2.options.database_dump_folder + os.sep + 'drive_cycle_data.csv', index=False)

            print(DriveCycles.validate_drive_cycle_ID('CS_EPA_FTP'))
            print(DriveCycles.validate_drive_cycle_ID('CS_EPA_FPT'))

        else:
            print(init_fail)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
