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
            validation_dict = {'share_id': ['onroad', 'cert', 'battery_sizing'],
                               'fueling_class': fueling_classes,
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
        cache_key = calendar_year, fueling_class, node_id, weighted

        if cache_key not in DriveCycleWeights._data:

            start_years = DriveCycleWeights._data[fueling_class]['start_year']
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])
                try:
                    eq_str = DriveCycleWeights._data[fueling_class][calendar_year].calc_value(cycle_values, node_id=node_id,
                                                                      weighted=weighted)[1]
                except:
                    print('drive cycle weights exception !!!')
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
        if fueling_class == 'PHEV':
            ftp_cd_uf, hwfet_cd_uf, us06_uf = \
                DriveCycleWeights.calc_phev_utility_factors(calendar_year, cycle_values)

            phev_cycle_values = cycle_values.copy()

            cd_ftp_1_co2e_grams_per_mile = cycle_values['cd_ftp_1:cert_direct_oncycle_co2e_grams_per_mile']
            cd_ftp_2_co2e_grams_per_mile = cycle_values['cd_ftp_2:cert_direct_oncycle_co2e_grams_per_mile']
            cd_ftp_3_co2e_grams_per_mile = cycle_values['cd_ftp_3:cert_direct_oncycle_co2e_grams_per_mile']
            cd_ftp_4_co2e_grams_per_mile = cycle_values['cd_ftp_4:cert_direct_oncycle_co2e_grams_per_mile']
            cd_hwfet_co2e_grams_per_mile = cycle_values['cd_hwfet:cert_direct_oncycle_co2e_grams_per_mile']
            cd_us06_1_co2e_grams_per_mile = cycle_values['cd_us06_1:cert_direct_oncycle_co2e_grams_per_mile']
            cd_us06_2_co2e_grams_per_mile = cycle_values['cd_us06_2:cert_direct_oncycle_co2e_grams_per_mile']

            cs_ftp_1_co2e_grams_per_mile = cycle_values['cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile']
            cs_ftp_2_co2e_grams_per_mile = cycle_values['cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile']
            cs_ftp_3_co2e_grams_per_mile = cycle_values['cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile']
            cs_ftp_4_co2e_grams_per_mile = cycle_values['cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile']
            cs_hwfet_co2e_grams_per_mile = cycle_values['cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile']
            cs_us06_1_co2e_grams_per_mile = cycle_values['cs_us06_1:cert_direct_oncycle_co2e_grams_per_mile']
            cs_us06_2_co2e_grams_per_mile = cycle_values['cs_us06_2:cert_direct_oncycle_co2e_grams_per_mile']

            phev_cycle_values['cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile'] = \
                ftp_cd_uf * cd_ftp_1_co2e_grams_per_mile + (1 - ftp_cd_uf) * cs_ftp_1_co2e_grams_per_mile
            phev_cycle_values['cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile'] = \
                ftp_cd_uf * cd_ftp_2_co2e_grams_per_mile + (1 - ftp_cd_uf) * cs_ftp_2_co2e_grams_per_mile
            phev_cycle_values['cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile'] = \
                ftp_cd_uf * cd_ftp_3_co2e_grams_per_mile + (1 - ftp_cd_uf) * cs_ftp_3_co2e_grams_per_mile
            phev_cycle_values['cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile'] = \
                ftp_cd_uf * cd_ftp_4_co2e_grams_per_mile + (1 - ftp_cd_uf) * cs_ftp_4_co2e_grams_per_mile
            phev_cycle_values['cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile'] = \
                hwfet_cd_uf * cd_hwfet_co2e_grams_per_mile + (1 - hwfet_cd_uf) * cs_hwfet_co2e_grams_per_mile
            phev_cycle_values['cs_us06_1:cert_direct_oncycle_co2e_grams_per_mile'] = \
                us06_uf * cd_us06_1_co2e_grams_per_mile + (1 - us06_uf) * cs_us06_1_co2e_grams_per_mile
            phev_cycle_values['cs_us06_2:cert_direct_oncycle_co2e_grams_per_mile'] = \
                us06_uf * cd_us06_2_co2e_grams_per_mile + (1 - us06_uf) * cs_us06_2_co2e_grams_per_mile

            cs_cert_direct_oncycle_co2e_grams_per_mile = \
                DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, phev_cycle_values,
                                                      'cs_cert_direct_oncycle_co2e_grams_per_mile', weighted=False)

            # cd_cert_direct_oncycle_co2e_grams_per_mile = \
            #     DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, phev_cycle_values,
            #                                           'cd_cert_direct_oncycle_co2e_grams_per_mile', weighted=False)

        else:
            cs_cert_direct_oncycle_co2e_grams_per_mile = \
                DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                         'cs_cert_direct_oncycle_co2e_grams_per_mile', weighted=False)

        return cs_cert_direct_oncycle_co2e_grams_per_mile

    @staticmethod
    def calc_cert_direct_oncycle_kwh_per_mile(calendar_year, fueling_class, cycle_values, charge_depleting_only=False):
        """
        Calculate cert direct on-cycle kWh/mi

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted
                (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)
            charge_depleting_only (Boolean): ``True`` if calculating charge-depleting kWh/mi, not cert

        Returns:
            A pandas ``Series`` object of the weighted results

        """

        utility_factor = 0

        if fueling_class == 'PHEV':
            ftp_cd_uf, hwfet_cd_uf, us06_uf = DriveCycleWeights.calc_phev_utility_factors(calendar_year, cycle_values)

            if charge_depleting_only:
                cd_cert_direct_oncycle_kwh_per_mile = \
                    DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                      'cd_cert_direct_oncycle_kwh_per_mile', weighted=False)
            else:
                phev_cycle_values = cycle_values.copy()

                cd_ftp_1_kwh_per_mile = cycle_values['cd_ftp_1:cert_direct_oncycle_kwh_per_mile']
                cd_ftp_2_kwh_per_mile = cycle_values['cd_ftp_2:cert_direct_oncycle_kwh_per_mile']
                cd_ftp_3_kwh_per_mile = cycle_values['cd_ftp_3:cert_direct_oncycle_kwh_per_mile']
                cd_ftp_4_kwh_per_mile = cycle_values['cd_ftp_4:cert_direct_oncycle_kwh_per_mile']
                cd_hwfet_kwh_per_mile = cycle_values['cd_hwfet:cert_direct_oncycle_kwh_per_mile']
                cd_us06_1_kwh_per_mile = cycle_values['cd_us06_1:cert_direct_oncycle_kwh_per_mile']
                cd_us06_2_kwh_per_mile = cycle_values['cd_us06_2:cert_direct_oncycle_kwh_per_mile']

                cs_ftp_1_kwh_per_mile = cycle_values['cs_ftp_1:cert_direct_oncycle_kwh_per_mile']
                cs_ftp_2_kwh_per_mile = cycle_values['cs_ftp_2:cert_direct_oncycle_kwh_per_mile']
                cs_ftp_3_kwh_per_mile = cycle_values['cs_ftp_3:cert_direct_oncycle_kwh_per_mile']
                cs_ftp_4_kwh_per_mile = cycle_values['cs_ftp_4:cert_direct_oncycle_kwh_per_mile']
                cs_hwfet_kwh_per_mile = cycle_values['cs_hwfet:cert_direct_oncycle_kwh_per_mile']
                cs_us06_1_kwh_per_mile = cycle_values['cs_us06_1:cert_direct_oncycle_kwh_per_mile']
                cs_us06_2_kwh_per_mile = cycle_values['cs_us06_2:cert_direct_oncycle_kwh_per_mile']

                phev_cycle_values['cs_ftp_1:cert_direct_oncycle_kwh_per_mile'] = \
                    ftp_cd_uf * cd_ftp_1_kwh_per_mile + (1 - ftp_cd_uf) * cs_ftp_1_kwh_per_mile
                phev_cycle_values['cs_ftp_2:cert_direct_oncycle_kwh_per_mile'] = \
                    ftp_cd_uf * cd_ftp_2_kwh_per_mile + (1 - ftp_cd_uf) * cs_ftp_2_kwh_per_mile
                phev_cycle_values['cs_ftp_3:cert_direct_oncycle_kwh_per_mile'] = \
                    ftp_cd_uf * cd_ftp_3_kwh_per_mile + (1 - ftp_cd_uf) * cs_ftp_3_kwh_per_mile
                phev_cycle_values['cs_ftp_4:cert_direct_oncycle_kwh_per_mile'] = \
                    ftp_cd_uf * cd_ftp_4_kwh_per_mile + (1 - ftp_cd_uf) * cs_ftp_4_kwh_per_mile
                phev_cycle_values['cs_hwfet:cert_direct_oncycle_kwh_per_mile'] = \
                    hwfet_cd_uf * cd_hwfet_kwh_per_mile + (1 - hwfet_cd_uf) * cs_hwfet_kwh_per_mile
                phev_cycle_values['cs_us06_1:cert_direct_oncycle_kwh_per_mile'] = \
                    us06_uf * cd_us06_1_kwh_per_mile + (1 - us06_uf) * cs_us06_1_kwh_per_mile
                phev_cycle_values['cs_us06_2:cert_direct_oncycle_kwh_per_mile'] = \
                    us06_uf * cd_us06_2_kwh_per_mile + (1 - us06_uf) * cs_us06_2_kwh_per_mile

                cs_cert_direct_oncycle_kwh_per_mile = \
                    DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, phev_cycle_values,
                                                          'cs_cert_direct_oncycle_kwh_per_mile', weighted=False)

                # calculate weighted utility factor
                cd_cert_direct_oncycle_kwh_per_mile = \
                    DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, phev_cycle_values,
                                                          'cd_cert_direct_oncycle_kwh_per_mile', weighted=False)

                utility_factor = cs_cert_direct_oncycle_kwh_per_mile / cd_cert_direct_oncycle_kwh_per_mile

        else:
            cd_cert_direct_oncycle_kwh_per_mile = \
                DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                  'cd_cert_direct_oncycle_kwh_per_mile', weighted=False)

        kwh_per_mile_scale = np.interp(calendar_year, omega_globals.options.kwh_per_mile_scale_years,
                                      omega_globals.options.kwh_per_mile_scale)

        return cd_cert_direct_oncycle_kwh_per_mile * kwh_per_mile_scale, utility_factor

    @staticmethod
    def calc_engine_on_distance_frac(calendar_year, fueling_class, cycle_values, utility_factor=1):
        """
        Calculate engine-on distance frac

        Args:
            calendar_year (numeric): calendar year to calculated weighted value in
            fueling_class (str): e.g. 'ICE', 'BEV', etc
            cycle_values (DataFrame): contains cycle values to be weighted
                (e.g. the simulated vehicles input data with results (columns) for each drive cycle phase)
            utility_factor (float): the utility factor for PHEVs

        Returns:
            The engine-on distance frac

        """

        if fueling_class == 'PHEV':
            cd_engine_on_distance_frac = \
                DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                      'cd_engine_on_distance_frac', weighted=False)

            cs_engine_on_distance_frac = \
                DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                      'cs_engine_on_distance_frac', weighted=False)

            engine_on_distance_frac = utility_factor * cd_engine_on_distance_frac + \
                                      (1 - utility_factor) * cs_engine_on_distance_frac

        else:
            engine_on_distance_frac = \
                DriveCycleWeights.calc_weighted_value(calendar_year, fueling_class, cycle_values,
                                                      'cs_engine_on_distance_frac', weighted=False)

        return engine_on_distance_frac

    @staticmethod
    def calc_phev_utility_factors(calendar_year, cycle_values):
        """
        Calculate PHEV utility factors

        Args:
            calendar_year (numeric): calendar year to utility factors in
            cycle_values (dict): holds charge-depleting and charge-sustaining cycle phase values

        Returns:
            tuple (FTP, HWFET, US06) utility factors
        """
        from policy.utility_factors import UtilityFactorMethods

        phev_batt_kwh = cycle_values['battery_kwh']
        usable_battery_capacity_norm = cycle_values['usable_battery_capacity_norm']
        phev_cd_battery_kwh = phev_batt_kwh * usable_battery_capacity_norm

        cd_ftp_kwh_per_mile = \
            DriveCycleWeights.calc_weighted_value(calendar_year, 'PHEV', cycle_values, 'cd_ftp_kwh', weighted=False)

        cd_hwfet_kwh_per_mile = cycle_values['cd_hwfet:cert_direct_oncycle_kwh_per_mile']

        cd_us06_1_kwh_per_mile = cycle_values['cd_us06_1:cert_direct_oncycle_kwh_per_mile']
        cd_us06_2_kwh_per_mile = cycle_values['cd_us06_2:cert_direct_oncycle_kwh_per_mile']

        cd_us06_kwh_per_mile = \
            1.772 / 8.007 * cd_us06_1_kwh_per_mile + 6.235 / 8.007 * cd_us06_2_kwh_per_mile

        if cd_ftp_kwh_per_mile > 0:
            cd_ftp_range_miles = max(0, phev_cd_battery_kwh / cd_ftp_kwh_per_mile)
        else:
            cd_ftp_range_miles = 0

        if cd_hwfet_kwh_per_mile > 0:
            cd_hwfet_range_miles = max(0, phev_cd_battery_kwh / cd_hwfet_kwh_per_mile)
        else:
            cd_hwfet_range_miles = 0

        if cd_us06_kwh_per_mile > 0:
            cd_us06_range_miles = max(0, phev_cd_battery_kwh / cd_us06_kwh_per_mile)
        else:
            cd_us06_range_miles = 0

        ftp_cd_uf = UtilityFactorMethods.calc_city_utility_factor(calendar_year, cd_ftp_range_miles)

        hwfet_cd_uf = UtilityFactorMethods.calc_highway_utility_factor(calendar_year, cd_hwfet_range_miles)

        us06_cd_uf = UtilityFactorMethods.calc_highway_utility_factor(calendar_year, cd_us06_range_miles)

        return ftp_cd_uf, hwfet_cd_uf, us06_cd_uf


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
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
