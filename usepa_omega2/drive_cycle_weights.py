"""
drive_cycle_weights.py
======================


"""

print('importing %s' % __file__)

from usepa_omega2 import *


class DriveCycleWeights(OMEGABase):
    weights = pd.DataFrame()

    @staticmethod
    def get_drive_cycle_weight(calendar_year, drive_cycle_id):
        return DriveCycleWeights.weights['%s:weight' % (drive_cycle_id)].loc[
                  DriveCycleWeights.weights['calendar_year'] == calendar_year].item()

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'drive_cycle_weights'
        input_template_version = 0.1
        input_template_columns = {'calendar_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                DriveCycleWeights.weights['calendar_year'] = df['calendar_year']

                weight_columns = [c for c in df.columns if 'weight' in c]

                for wc in weight_columns:
                    drive_cycle_id = wc.split(':')[0]
                    if DriveCycles.validate_drive_cycle_ID(drive_cycle_id):
                        DriveCycleWeights.weights[wc] = df[wc]
                    else:
                        template_errors.append('*** Invalid Policy Drive Cycle ID "%s" in %s ***' % (drive_cycle_id, filename))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        from drive_cycles import DriveCycles

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = o2.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + DriveCycles.init_from_file(o2.options.drive_cycles_file,
                                                           verbose=o2.options.verbose)
        init_fail = init_fail + DriveCycleWeights.init_from_file(o2.options.drive_cycle_weights_file,
                                                                  verbose=o2.options.verbose)

        if not init_fail:
            fileio.validate_folder(o2.options.database_dump_folder)
            DriveCycleWeights.weights.to_csv(
                o2.options.database_dump_folder + os.sep + 'drive_cycle_weights.csv', index=False)

            print(DriveCycleWeights.get_drive_cycle_weight(2020, 'CS_EPA_FTP'))
            print(DriveCycleWeights.get_drive_cycle_weight(2050, 'CS_EPA_FTP'))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
