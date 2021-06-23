"""

**Routines to load simulated vehicle data (vehicle energy/CO2 consumption, off-cycle tech application, and cost data)
and calculate frontiers from "clouds" of points**

Also contains a function to plot frontiers for troubleshooting purposes

Cost cloud frontiers are at the heart of OMEGA's optimization and compliance processes.  For every set of points
represented in $/CO2_g/mi (or Y versus X in general) there is a set of points that represent the lowest cost for each
CO2 level, this is referred to as the frontier of the cloud.  Each point in the cloud (and on the frontier) can store
multiple parameters, implemented as rows in a pandas DataFrame where each row can have multiple columns of data.

Each manufacturer vehicle, in each model year, gets its own frontier.  The frontiers are combined in a sales-weighted
fashion to create composite frontiers for groups of vehicles that can be considered simultaneously for compliance
purposes.  These groups of vehicles are called composite vehicles (*see also vehicles.py, class CompositeVehicle*).
The points of the composite frontiers are in turn combined and sales-weighted in various combinations during
manufacturer compliance search iteration.

Frontiers can hew closely to the points of the source cloud or can cut through a range of representative points
depending on the value of ``o2.options.cost_curve_frontier_affinity_factor``.  Higher values pick up more points, lower
values are a looser fit.  The default value provides a good compromise between number of points and accuracy of fit.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents vehicle technology options and costs by simulation class (cost curve class) and model year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,simulated_vehicles,input_template_version:,0.2,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        simulated_vehicle_id,model_year,cost_curve_class,cd_ftp_1:cert_direct_oncycle_kwh_per_mile,cd_ftp_2:cert_direct_oncycle_kwh_per_mile,cd_ftp_3:cert_direct_oncycle_kwh_per_mile,cd_ftp_4:cert_direct_oncycle_kwh_per_mile,cd_hwfet:cert_direct_oncycle_kwh_per_mile,new_vehicle_mfr_cost_dollars,cs_ftp_1:cert_direct_oncycle_co2_grams_per_mile,cs_ftp_2:cert_direct_oncycle_co2_grams_per_mile,cs_ftp_3:cert_direct_oncycle_co2_grams_per_mile,cs_ftp_4:cert_direct_oncycle_co2_grams_per_mile,cs_hwfet:cert_direct_oncycle_co2_grams_per_mile,ac_efficiency,ac_leakage,high_eff_alternator,start_stop
        1_bev,2020,bev_LPW_LRL,0.12992078,0.10534883,0.1247339,0.10534883,0.13151191,30837.9095774431,0,0,0,0,0,1,0,0,0
        9086_ice,2031,ice_MPW_HRL,0,0,0,0,0,28995.8504073507,285.798112,269.100823,246.852389,269.100823,191.235952,1,1,1,1

Data Column Name and Description
    :simulated_vehicle_id:
        Unique row identifier, unused otherwise

    :model_year:
        The model year of the data (particularly for ``new_vehicle_mfr_cost_dollars``)

    :cost_curve_class:
        The name of the cost curve class, e.g. 'bev_LPW_LRL', 'ice_MPW_HRL', etc

    CHARGE-DEPLETING SIMULATION RESULTS
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cd_ftp_1:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_2:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_3:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_4:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_hwfet:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile

    :new_vehicle_mfr_cost_dollars:
        The manufacturer cost associated with the simulation results, based on vehicle technology content and model year

    CHARGE-SUSTAINING SIMULATION RESULTS
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cs_ftp_1:cert_direct_oncycle_co2_grams_per_mile: simulation result, CO2 grams/mile
        :cs_ftp_2:cert_direct_oncycle_co2_grams_per_mile: simulation result, CO2 grams/mile
        :cs_ftp_3:cert_direct_oncycle_co2_grams_per_mile: simulation result, CO2 grams/mile
        :cs_ftp_4:cert_direct_oncycle_co2_grams_per_mile: simulation result, CO2 grams/mile
        :cs_hwfet:cert_direct_oncycle_co2_grams_per_mile: simulation result, CO2 grams/mile

    :ac_efficiency:
        = 1 if vehicle qualifies for the AC efficiency off-cycle credit, = 0 otherwise

    :ac_leakage:
        = 1 if vehicle qualifies for the AC leakage off-cycle credit, = 0 otherwise

    :high_eff_alternator:
        = 1 if vehicle qualifies for the high efficiency alternator off-cycle credit, = 0 otherwise

    :start_stop:
        = 1 if vehicle qualifies for the engine start-stop off-cycle credit, = 0 otherwise

----

**CODE**

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()

# define list of non-numeric columns to ignore during frontier creation since they goof up pandas auto-typing of
# columns when switching between Series and DataFrame representations
cloud_non_numeric_columns = ['simulated_vehicle_id']


class CostCloud(OMEGABase):
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    _max_year = 0  # maximum year of cost cloud data (e.g. 2050), set by ``init_cost_clouds_from_file()``

    @staticmethod
    def init_cost_clouds_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """

        from policy.offcycle_credits import OffCycleCredits  # offcycle_credits must be initalized first

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'simulated_vehicles'
        input_template_version = 0.2
        input_template_columns = {'simulated_vehicle_id', 'model_year', 'cost_curve_class',
                                  'new_vehicle_mfr_cost_dollars'}
        input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            # TODO: validate manufacturer, reg classes, fuel ids, etc, etc....

            if not template_errors:
                # convert cost clouds into curves and set up cost_curves table...
                cost_curve_classes = df['cost_curve_class'].unique()
                # for each cost curve class
                for cost_curve_class in cost_curve_classes:
                    class_cloud = df[df['cost_curve_class'] == cost_curve_class]
                    cloud_model_years = class_cloud['model_year'].unique()
                    # for each model year
                    cache[cost_curve_class] = dict()
                    for model_year in cloud_model_years:
                        cache[cost_curve_class][model_year] = class_cloud[class_cloud['model_year'] == model_year].copy()
                        CostCloud._max_year = max(CostCloud._max_year, model_year)

        return template_errors

    @staticmethod
    def plot_frontier(cost_cloud, cost_curve_name, frontier_df, x_key, y_key):
        """
        Plot a cloud and its frontier.  Saves plot to ``o2.options.output_folder``.

        Args:
            cost_cloud (DataFrame): set of points to plot
            cost_curve_name (str): name of  plot
            frontier_df (DataFrame): set of points on the frontier
            x_key (str): column name of x-value
            y_key (str): columns name of y-value

        Example:

            ::

                # from create_frontier_df() in vehicles.py
                CostCloud.plot_frontier(self.cost_cloud, '', cost_curve, 'cert_co2_grams_per_mile', 'new_vehicle_mfr_cost_dollars')

        """
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(cost_cloud[x_key], cost_cloud[y_key],
                 '.')
        plt.title('Cost versus %s %s' % (x_key, cost_curve_name))
        plt.xlabel('%s' % x_key)
        plt.ylabel('%s' % y_key)
        plt.plot(frontier_df[x_key], frontier_df[y_key],
                 'r-')
        plt.grid()
        plt.savefig(globals.options.output_folder + '%s versus %s %s.png' % (y_key, x_key, cost_curve_name))

    @staticmethod
    def calc_frontier(cloud, x_key, y_key, allow_upslope=False):
        """
        Calculate the frontier of a cloud.

        Args:
            cloud (DataFrame): a set of points to find the frontier of
            x_key (str): name of the column holding x-axis data
            y_key (str): name of the column holding y-axis data
            allow_upslope (bool): allow U-shaped frontier

        Returns:
            DataFrame containing the frontier points

        .. figure:: _static/code_figures/cost_cloud_ice_Truck_allow_upslope_frontier_affinity_factor_0.75.png
            :scale: 75 %
            :align: center

            Cost cloud and frontier, ``o2.options.cost_curve_frontier_affinity_factor=0.75`` ``allow_upslope=True``
            These are the default settings

        .. figure:: _static/code_figures/cost_cloud_ice_Truck_allow_upslope_frontier_affinity_factor_10.png
            :scale: 75 %
            :align: center

            Cost cloud and frontier, ``o2.options.cost_curve_frontier_affinity_factor=10`` ``allow_upslope=True``
            Higher affinity factor follows cloud points more closely

        .. figure:: _static/code_figures/cost_cloud_ice_Truck_no_upslope_frontier_affinity_factor_0.75.png
            :scale: 75 %
            :align: center

            Cost cloud and frontier, ``o2.options.cost_curve_frontier_affinity_factor=0.75`` ``allow_upslope=False``
            Default affinity factor, no up-slope

        """

        import numpy as np

        if len(cloud) > 1:
            frontier_pts = []

            # drop non-numeric columns so dtypes don't become "object"
            cloud = cloud.drop(columns=cloud_non_numeric_columns, errors='ignore')

            # normalize data (helps with up-slope frontier)
            cloud['y_norm'] = (cloud[y_key] - cloud[y_key].min()) / (cloud[y_key].max() - cloud[y_key].min())
            cloud['x_norm'] = (cloud[x_key] - cloud[x_key].min()) / (cloud[x_key].max() - cloud[x_key].min())

            x_key = 'x_norm'
            y_key = 'y_norm'

            # find frontier starting point, lowest x-value, and add to frontier
            idxmin = cloud[x_key].idxmin()
            frontier_pts.append(cloud.loc[idxmin])
            min_frontier_factor = 0

            if cloud[x_key].min() != cloud[x_key].max():
                while pd.notna(idxmin) and (min_frontier_factor <= 0 or allow_upslope) \
                        and not np.isinf(min_frontier_factor) and not cloud.empty:
                    # calculate frontier factor (more negative is more better) = slope of each point relative
                    # to prior frontier point if frontier_social_affinity_factor = 1.0, else a "weighted" slope
                    cloud = cloud.loc[cloud[x_key] > frontier_pts[-1][x_key]].copy()
                    cloud['frontier_factor'] = (cloud[y_key] - frontier_pts[-1][y_key]) / \
                                               (cloud[x_key] - frontier_pts[-1][x_key]) \
                                               ** globals.options.cost_curve_frontier_affinity_factor
                    # find next frontier point (lowest slope), if there is one, and add to frontier list
                    min_frontier_factor = cloud['frontier_factor'].min()

                    if min_frontier_factor > 0 and allow_upslope:
                        # frontier factor is different for up-slope (swap x & y and invert "y")
                        cloud['frontier_factor'] = (frontier_pts[-1][x_key] - cloud[x_key]) / \
                                                   (cloud[y_key] - frontier_pts[-1][y_key]) \
                                                   ** globals.options.cost_curve_frontier_affinity_factor
                        min_frontier_factor = cloud['frontier_factor'].min()

                    if not cloud.empty:
                        if not np.isinf(min_frontier_factor):
                            if len(cloud[cloud['frontier_factor'] == min_frontier_factor]) > 1:
                                # if multiple points with the same slope, take the one with the highest x-value
                                idxmin = cloud[cloud['frontier_factor'] == min_frontier_factor][x_key].idxmax()
                            else:
                                idxmin = cloud['frontier_factor'].idxmin()
                        else:
                            idxmin = cloud['frontier_factor'].idxmax()

                        if pd.notna(idxmin) and (allow_upslope or min_frontier_factor <= 0):
                            frontier_pts.append(cloud.loc[idxmin])

            frontier_df = pd.concat(frontier_pts, axis=1)
            frontier_df = frontier_df.transpose()
            frontier_df['frontier_factor'] = 0
        else:
            frontier_df = cloud
            frontier_df['frontier_factor'] = 0

        return frontier_df.copy()

    @staticmethod
    def get_cloud(model_year, cost_curve_class):
        """
        Retrieve cost cloud for the given model year and cost curve class.

        Args:
            model_year (numeric): model year
            cost_curve_class (str): name of cost curve class (e.g. 'ice_MPW_LRL')

        Returns:
            Copy of the requested cost cload data.

        """
        return cache[cost_curve_class][model_year].copy()

    @staticmethod
    def get_max_year():
        """
        Get maximum year of cost cloud data.

        Returns:
            CostCloud.max_year

        """
        return CostCloud._max_year


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()
        globals.options.cost_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'test_inputs/cost_clouds.csv'

        init_fail = []
        init_fail += CostCloud.init_cost_clouds_from_file(globals.options.cost_file, verbose=True)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
