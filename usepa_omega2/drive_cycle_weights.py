"""
drive_cycle_weights.py
======================

Tree-based drive cycle weighting (distance-share based)

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class DriveCycleWeights(OMEGABase):

    @staticmethod
    def validate_drive_cycle_names(tree, filename):
        from drive_cycles import DriveCycles
        cycle_name_errors = []

        for leaf in tree.leaves():
            drive_cycle_id = leaf.identifier
            if not DriveCycles.validate_drive_cycle_ID(drive_cycle_id):
                cycle_name_errors.append(
                    '*** Invalid Policy Drive Cycle ID "%s" in %s ***' % (drive_cycle_id, filename))

        return cycle_name_errors

    @staticmethod
    def init_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'share_tree'
        input_template_version = 0.1
        input_template_columns = {'calendar_year', 'share_id'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                from omega_trees import WeightedTree
                weight_errors = []
                cycle_name_errors = []
                for calendar_year in df['calendar_year']:
                    tree = WeightedTree(df.loc[df['calendar_year'] == calendar_year], verbose)
                    weight_errors += tree.validate_weights()
                    if weight_errors:
                        template_errors = ['weight error %s: %s' %
                                           (calendar_year, error) for error in weight_errors]
                    else:
                        if not cache:
                            # validate drive cycle names on first tree
                            cycle_name_errors = DriveCycleWeights.validate_drive_cycle_names(tree, filename)
                            if cycle_name_errors:
                                template_errors =['cyclename error %s' % error for error in cycle_name_errors]
                        if not cycle_name_errors:
                            cache[calendar_year] = tree

        return template_errors

    @staticmethod
    def calculate_weighted_value(calendar_year, cycle_values_dict, node_id=None, weighted=True):
        return cache[calendar_year].calculate_weighted_value(cycle_values_dict, node_id=node_id,
                                                             weighted=weighted)

    @staticmethod
    def calc_weighted_drive_cycle_tailpipe_co2_grams_per_mile(calendar_year, df):
        return DriveCycleWeights.calculate_weighted_value(calendar_year, df, 'tailpipe_co2_grams_per_mile', weighted=False)

    @staticmethod
    def calc_weighted_drive_cycle_kWh_per_mile(calendar_year, df):
        return DriveCycleWeights.calculate_weighted_value(calendar_year, df, 'cert_kWh_per_mile', weighted=False)


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
            print(DriveCycleWeights.calc_weighted_drive_cycle_tailpipe_co2_grams_per_mile(2020, sample_cloud))
            print(DriveCycleWeights.calc_weighted_drive_cycle_kWh_per_mile(2020, sample_cloud))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
