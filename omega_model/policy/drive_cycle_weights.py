"""

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

Sample Drive Cycle Weight Tree
    ::

        1.0[weighted_combined]
        ├── 1[cd_cert_direct_oncycle_kwh_per_mile]
        │   ├── 0.55[cd_ftp_kwh]
        │   │   ├── 0.20726577181208053[cd_ftp_1:cert_direct_oncycle_kwh_per_mile]
        │   │   ├── 0.517986577181208[cd_ftp_2:cert_direct_oncycle_kwh_per_mile]
        │   │   ├── 0.2747476510067114[cd_ftp_3:cert_direct_oncycle_kwh_per_mile]
        │   │   └── None[cd_ftp_4:cert_direct_oncycle_kwh_per_mile]
        │   └── 0.45[cd_hwfet:cert_direct_oncycle_kwh_per_mile]
        └── 0[cs_cert_direct_oncycle_co2e_grams_per_mile]
            ├── 0.55[cs_ftp_co2]
            │   ├── 0.20726577181208053[cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile]
            │   ├── 0.517986577181208[cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile]
            │   ├── 0.2747476510067114[cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile]
            │   └── None[cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile]
            └── 0.45[cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile]

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The data header uses a dynamic column notation, as detailed below.

The data represents drive-cycle weighting factors (distance shares) in a hierarchical tree datastructure, by model year
and fueling class.  For details on how the header is parsed into a tree, see ``common.omega_trees.WeightedTree``.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,share_tree,input_template_version:,0.3

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,share_id,fueling_class,weighted_combined->cs_cert_direct_oncycle_co2e_grams_per_mile,weighted_combined->cd_cert_direct_oncycle_kwh_per_mile,cs_cert_direct_oncycle_co2e_grams_per_mile->cs_ftp_co2,cs_cert_direct_oncycle_co2e_grams_per_mile->cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_co2->cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_co2->cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_co2->cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_co2->cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile,cd_cert_direct_oncycle_kwh_per_mile->cd_ftp_kwh,cd_cert_direct_oncycle_kwh_per_mile->cd_hwfet:cert_direct_oncycle_kwh_per_mile,cd_ftp_kwh->cd_ftp_1:cert_direct_oncycle_kwh_per_mile,cd_ftp_kwh->cd_ftp_2:cert_direct_oncycle_kwh_per_mile,cd_ftp_kwh->cd_ftp_3:cert_direct_oncycle_kwh_per_mile,cd_ftp_kwh->cd_ftp_4:cert_direct_oncycle_kwh_per_mile
        2020,cert,ICE,1,0,0.55,0.45,0.43*3.591/7.45,3.859/7.45,0.57*3.591/7.45,None,0.55,0.45,0.43*3.591/7.45,3.859/7.45,0.57*3.591/7.45,None

Data Column Name and Description
    :start_year:
        The earliest model year that drive cycle weighting applies to

    :share_id:
        The type of the drive cycle weighting, e.g. 'cert'

    :fueling_class:
        The fueling class (general powertrain type) that the drive cycle weighting applies to, e.g. 'ICE', 'PHEV', etc

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
from policy.drive_cycles import DriveCycles


class DriveCycleWeights(OMEGABase):
    """
    **Loads a drive cycle share tree, validates cycle/phase names and provides methods to calculate weighted drive
    cycle results.**

    """
    
    _data = dict()  # private dict, drive cycle weights by fuel class and calendar year
    
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

        cycle_name_errors = []

        for leaf in tree.leaves():
            drive_cycle_id = leaf.identifier
            if not DriveCycles.validate_drive_cycle_id(drive_cycle_id):
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
        DriveCycleWeights._data.clear()

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

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'share_id': ['cert'],
                               'fueling_class': ['ICE', 'BEV', 'PHEV'],  # RV
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            from common.omega_trees import WeightedTree
            weight_errors = []
            cycle_name_errors = []
            for fc in fueling_classes:
                for calendar_year in df['start_year']:
                    data = df.loc[(df['start_year'] == calendar_year) & (df['fueling_class'] == fc)]
                    if not data.empty:
                        tree = WeightedTree(df.loc[(df['start_year'] == calendar_year) & (df['fueling_class'] == fc)],
                                            verbose=verbose)
                        weight_errors += tree.validate_weights()
                        if weight_errors:
                            template_errors = ['weight error %s: %s' %
                                               (calendar_year, error) for error in weight_errors]
                        else:
                            if not DriveCycleWeights._data:
                                # validate drive cycle names on first tree
                                cycle_name_errors = DriveCycleWeights.validate_drive_cycle_names(tree, filename)
                                if cycle_name_errors:
                                    template_errors = ['cyclename error %s' % error for error in cycle_name_errors]
                            if not cycle_name_errors:
                                if fc not in DriveCycleWeights._data:
                                    DriveCycleWeights._data[fc] = dict()
                                DriveCycleWeights._data[fc][calendar_year] = tree

                DriveCycleWeights._data[fc]['start_year'] = np.array([*DriveCycleWeights._data[fc]])  # CU

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
            cycle_values (DataFrame): contains cycle values to be weighted (e.g. the simulated vehicles input
                data with results (columns) for each drive cycle phase)
            node_id (str): name of tree node at which to calculated weighted value,
                e.g. 'cs_cert_direct_oncycle_co2e_grams_per_mile'
            weighted (bool): if True, return weighted value at node (node value * weight),
                else return node value (e.g. cycle result)

        Returns:
            A pandas ``Series`` object of the weighted results

        """
        cache_key = calendar_year, fueling_class

        if cache_key not in DriveCycleWeights._data:

            start_years = DriveCycleWeights._data[fueling_class]['start_year']
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])
                eq_str = DriveCycleWeights._data[fueling_class][calendar_year].calc_value(cycle_values, node_id=node_id,
                                                                      weighted=weighted)[1]
                DriveCycleWeights._data[cache_key] = eq_str
            else:
                raise Exception('Missing drive cycle weights for %s, %d or prior' % (fueling_class, calendar_year))

        return Eval.eval(DriveCycleWeights._data[cache_key], {}, {'results': cycle_values})

    @staticmethod
    def calc_cert_direct_oncycle_co2e_grams_per_mile(calendar_year, fueling_class, cycle_values):
        """
        Calculate cert direct on-cycle CO2e g/mi

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted
                (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)

        Returns:
            A pandas ``Series`` object of the weighted results

        """
        return DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                     'cs_cert_direct_oncycle_co2e_grams_per_mile', weighted=False)

    @staticmethod
    def calc_cert_direct_oncycle_kwh_per_mile(calendar_year, fueling_class, cycle_values):
        """
        Calculate cert direct on-cycle kWh/mi

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted
                (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)

        Returns:
            A pandas ``Series`` object of the weighted results

        """
        cd_cert_direct_oncycle_kwh_per_mile = \
            DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                  'cd_cert_direct_oncycle_kwh_per_mile', weighted=False)

        kwh_per_mile_scale = np.interp(calendar_year, omega_globals.options.kwh_per_mile_scale_years,
                                      omega_globals.options.kwh_per_mile_scale)

        return cd_cert_direct_oncycle_kwh_per_mile * kwh_per_mile_scale


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from drive_cycles import DriveCycles

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += DriveCycleWeights.init_from_file(omega_globals.options.drive_cycle_weights_file,
                                                      verbose=True)

        if not init_fail:

            sample_cycle_results = {
                            'cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile': 277.853416,
                            'cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile': 272.779239,
                            'cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile': 242.292152,
                            'cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile': 272.779239,
                            'cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile': 182.916104,
                            'cd_ftp_1:cert_direct_oncycle_kwh_per_mile': 0.26559971,
                            'cd_ftp_2:cert_direct_oncycle_kwh_per_mile': 0.2332757,
                            'cd_ftp_3:cert_direct_oncycle_kwh_per_mile': 0.25938633,
                            'cd_ftp_4:cert_direct_oncycle_kwh_per_mile': 0.2332757,
                            'cd_hwfet:cert_direct_oncycle_kwh_per_mile': 0.22907605,
            }

            print(DriveCycleWeights.calc_cert_direct_oncycle_co2e_grams_per_mile(2020, 'ICE', sample_cycle_results))
            # eq_str = DriveCycleWeights.calc_cert_direct_oncycle_co2e_grams_per_mile(2020, 'ICE', sample_cycle_results)[1]
            # print(eval(eq_str, {}, {'results': sample_cycle_results}))
            print(DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(2020, 'BEV', sample_cycle_results))
            # eq_str = DriveCycleWeights.calc_cert_direct_oncycle_kwh_per_mile(2020, 'BEV', sample_cycle_results)[1]
            # print(eval(eq_str, {}, {'results': sample_cycle_results}))

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
