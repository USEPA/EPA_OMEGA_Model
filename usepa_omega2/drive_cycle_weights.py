"""
drive_cycle_weights.py
======================

**Routines to load cycle weight values and perform tree-based drive cycle weighting (distance-share based)**

For vehicle certification purposes, vehicles are tested by driving several drive cycles and drive cycle phases.
The phases and cycles are weighted (by distance shares) and combined to arrive at a certification on-cycle test
result.  One way to represent the cycle weightings is the use of a tree, where the leaves are the drive cycle or
phase results, the nodes store the weight factors and the edges represent the relationships of phases to tests and
the tests to each other.

``class DriveCycleWeights`` loads the share tree input file, validates the leaves of the tree against known cycles
and provides methods to query the tree for weighted results.  Most of the heavy lifting is done by
``class WeightedTree``, see ``omega_trees.py``

Child share weights must add up to 1.0 at each node of the tree, with the exception of weights with the value ``None``,
these are used to ignore unused nodes (different vehicle types have different numbers of drive cycle phases but share
the same overall tree).

Drive cycles and weights may vary model year, depending on the policy being simulated, the share tree supports this.

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class DriveCycleWeights(OMEGABase):
    """
    **Loads a drive cycle share tree, validates cycle/phase names and provides methods to calculate weighted drive
    cycle results.**


    """

    @staticmethod
    def validate_drive_cycle_names(tree, filename):
        """
        Validate share tree input file leaf names against known drive cycles and phases.

        Args:
            tree (class WeightedTree): share tree with drive cycles/phases as leaves
            filename(str): name of input file being validated, for error messages

        Returns:
            List of cycle name errors, or empty list on success.

        """

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
        """

            Initialize class data from input file.  Validate drive cycle names and share weight sums.

            Args:
                filename (str): name of input file
                verbose (bool): enable additional console and logfile output if True

            Returns:
                List of template/input errors, else empty list on success

        """

        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'share_tree'
        input_template_version = 0.3
        input_template_columns = {'start_year', 'share_id', 'fueling_class'}

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
                for fc in fueling_classes:
                    for calendar_year in df['start_year']:
                        data = df.loc[(df['start_year'] == calendar_year) & (df['fueling_class'] == fc)]
                        if not data.empty:
                            tree = WeightedTree(df.loc[(df['start_year'] == calendar_year) & (df['fueling_class'] == fc)], verbose)
                            weight_errors += tree.validate_weights()
                            if weight_errors:
                                template_errors = ['weight error %s: %s' %
                                                   (calendar_year, error) for error in weight_errors]
                            else:
                                if not cache:
                                    # validate drive cycle names on first tree
                                    cycle_name_errors = DriveCycleWeights.validate_drive_cycle_names(tree, filename)
                                    if cycle_name_errors:
                                        template_errors = ['cyclename error %s' % error for error in cycle_name_errors]
                                if not cycle_name_errors:
                                    if fc not in cache:
                                        cache[fc] = dict()
                                    cache[fc][calendar_year] = tree

                    cache[fc]['start_year'] = np.array(list(cache[fc].keys()))

        return template_errors

    @staticmethod
    def calc_weighted_value(calendar_year, fueling_class, cycle_values, node_id=None, weighted=True):
        """
        Query the share tree for a value or weighted value.  A node's value is either a raw cycle result
        (for leaves) or the sum of the weighted values of its children.  A node's weighted value is it's value
        times its weight.

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)
            node_id (str): name of tree node at which to calculated weighted value, e.g. 'cs_cert_direct_oncycle_co2_grams_per_mile'
            weighted (bool): if True, return weighted value at node (node value * weight), else return node value (e.g. cycle result)

        Returns:
            A pandas ``Series`` object of the weighted results

        """
        start_years = cache[fueling_class]['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])
        return cache[fueling_class][calendar_year].calc_weighted_value(cycle_values, node_id=node_id,
                                                                       weighted=weighted)

    @staticmethod
    def calc_cert_direct_oncycle_co2_grams_per_mile(calendar_year, fueling_class, cycle_values):
        """
        Calculate cert direct on-cycle CO2 g/mi

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)

        Returns:
            A pandas ``Series`` object of the weighted results

        """
        return DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                     'cs_cert_direct_oncycle_co2_grams_per_mile', weighted=False)

    @staticmethod
    def calc_cert_direct_oncycle_kwh_per_mile(calendar_year, fueling_class, cycle_values):
        """
        Calculate cert direct on-cycle kWh/mi

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)

        Returns:
            A pandas ``Series`` object of the weighted results

        """
        return DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                     'cd_cert_direct_oncycle_kwh_per_mile', weighted=False)


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

        init_fail += DriveCycles.init_from_file(o2.options.drive_cycles_file,
                                                verbose=o2.options.verbose)

        init_fail += DriveCycleWeights.init_from_file(o2.options.drive_cycle_weights_file,
                                                      verbose=o2.options.verbose)

        if not init_fail:

            sample_cycle_results = {
                            'cs_ftp_1:cert_direct_oncycle_co2_grams_per_mile': 277.853416,
                            'cs_ftp_3:cert_direct_oncycle_co2_grams_per_mile': 272.779239,
                            'cs_ftp_3:cert_direct_oncycle_co2_grams_per_mile': 242.292152,
                            'cs_hwfet:cert_direct_oncycle_co2_grams_per_mile': 182.916104,
                            'ftp_1:cert_direct_kwh_per_mile': 0.26559971,
                            'ftp_2:cert_direct_kwh_per_mile': 0.2332757,
                            'ftp_3:cert_direct_kwh_per_mile': 0.25938633,
                            'hwfet:cert_direct_kwh_per_mile': 0.22907605,
            }
            print(DriveCycleWeights.calc_cert_direct_oncycle_co2_grams_per_mile(2020, sample_cycle_results))
            print(DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(2020, sample_cycle_results))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
