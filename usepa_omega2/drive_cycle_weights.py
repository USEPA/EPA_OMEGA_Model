"""
drive_cycle_weights.py
======================

Example 55/45 Weighting:

::

    FTP1*0.55*0.43*3.591/7.4505 + FTP2*0.55*3.8595/7.4505 + FTP3*0.55*0.57*3.591/7.4505 + HWFET*0.45

    FTP1*0.11398852426011678 + FTP2*0.2849104086974029  + FTP3*0.15110106704248039 + HWFET*0.45 = 55/45 FTP/HWFET

Example 45/55 Weighting:

::

    FTP1*0.45*0.43*3.591/7.4505 + FTP2*0.45*3.8595/7.4505 + FTP3*0.45*0.57*3.591/7.4505 + HWFET*0.55

    FTP1*0.09326333803100464 + FTP2*0.23310851620696602  + FTP3*0.1236281457620294 + HWFET*0.55 = 55/45 FTP/HWFET


"""

print('importing %s' % __file__)

from usepa_omega2 import *


class DriveCycleWeights(OMEGABase):

    weights = pd.DataFrame()

    @staticmethod
    def get_drive_cycle_weight(calendar_year, drive_cycle_id):
        key = '%s:weight' % (drive_cycle_id)
        if key in DriveCycleWeights.weights:
            return DriveCycleWeights.weights[key].loc[
                  DriveCycleWeights.weights['calendar_year'] == calendar_year].item()
        else:
            return 0

    @staticmethod
    def calc_weighted_drive_cycle(calendar_year, df, weighted_value):
        from drive_cycles import DriveCycles

        weighted_result = 0

        for dc in DriveCycles.get_drive_cycles():
            key = '%s:%s' % (dc, weighted_value)
            if key in df:
                weighted_result += df[key] * DriveCycleWeights.get_drive_cycle_weight(calendar_year, dc)
            elif DriveCycleWeights.get_drive_cycle_weight(calendar_year, dc) > 0:
                # cycle has weighted value, but not present in df, that's an error
                raise Exception('*** Missing drive cycle "%s" in input to calc_weighted_drive_cycle() ***' % dc)

        return weighted_result

    @staticmethod
    def calc_weighted_drive_cycle_co2_grams_per_mile(calendar_year, df):
        return DriveCycleWeights.calc_weighted_drive_cycle(calendar_year, df, 'co2_grams_per_mile')

    @staticmethod
    def calc_weighted_drive_cycle_kWh_per_mile(calendar_year, df):
        return DriveCycleWeights.calc_weighted_drive_cycle(calendar_year, df, 'kWh_per_mile')

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
                from drive_cycles import DriveCycles

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

            print(DriveCycleWeights.get_drive_cycle_weight(2020, 'ftp_1'))
            print(DriveCycleWeights.get_drive_cycle_weight(2050, 'hwfet'))

            sample_cloud = {
                            'ftp_1:co2_grams_per_mile': 277.853416,
                            'ftp_2:co2_grams_per_mile': 272.779239,
                            'ftp_3:co2_grams_per_mile': 242.292152,
                            'hwfet:co2_grams_per_mile': 182.916104,
                            'ftp_1:kWh_per_mile': 0.26559971,
                            'ftp_2:kWh_per_mile': 0.2332757,
                            'ftp_3:kWh_per_mile': 0.25938633,
                            'hwfet:kWh_per_mile': 0.22907605,
            }
            print(DriveCycleWeights.calc_weighted_drive_cycle(2020, sample_cloud, 'co2_grams_per_mile'))
            print(DriveCycleWeights.calc_weighted_drive_cycle(2020, sample_cloud, 'kWh_per_mile'))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
