"""

**Routines to load simulated vehicle data (vehicle energy/CO2e consumption, off-cycle tech application, and cost data)
and calculate frontiers from "clouds" of points**

Also contains a function to plot frontiers for troubleshooting purposes

Cost cloud frontiers are at the heart of OMEGA's optimization and compliance processes.  For every set of points
represented in $/CO2e_g/mi (or Y versus X in general) there is a set of points that represent the lowest cost for each
CO2e level, this is referred to as the frontier of the cloud.  Each point in the cloud (and on the frontier) can store
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

       input_template_name:,simulated_vehicle_results_and_costs,input_template_version:,0.22,dollar_basis:,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        simulated_vehicle_id,model_year,cost_curve_class,ac_efficiency,ac_leakage,high_eff_alternator,start_stop,cd_ftp_1:cert_direct_oncycle_kwh_per_mile,cd_ftp_2:cert_direct_oncycle_kwh_per_mile,cd_ftp_3:cert_direct_oncycle_kwh_per_mile,cd_ftp_4:cert_direct_oncycle_kwh_per_mile,cd_hwfet:cert_direct_oncycle_kwh_per_mile,new_vehicle_mfr_cost_dollars,cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile,cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile
        bev_1,2020,bev_LPW_LRL,1,1,1,1,0.12992078,0.10534883,0.1247339,0.10534883,0.13151191,29559.4800439885,0,0,0,0,0
        ice_9086,2021,ice_MPW_HRL,1,1,1,0,0,0,0,0,0,31012.5039133722,285.798112,269.100823,246.852389,269.100823,191.235952

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
        The manufacturer cost associated with the simulation results, based on vehicle technology content and model year.Note that the
         costs are converted in-code to 'analysis_dollar_basis' using the implicit_price_deflators input file.

    CHARGE-SUSTAINING SIMULATION RESULTS
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile

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

from omega_model import *

cache = dict()

# define list of non-numeric columns to ignore during frontier creation since they goof up pandas auto-typing of
# columns when switching between Series and DataFrame representations
cloud_non_numeric_columns = ['simulated_vehicle_id']


class CostCloud(OMEGABase):
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    _max_year = 0  # maximum year of cost cloud data (e.g. 2050), set by ``init_cost_clouds_from_file()``

    cost_cloud_data_columns = []

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

        input_template_name = 'simulated_vehicle_results_and_costs'
        input_template_version = 0.22
        input_template_columns = {'simulated_vehicle_id', 'model_year', 'cost_curve_class',
                                  'new_vehicle_mfr_cost_dollars'}
        input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            cost_clouds_template_info = pd.read_csv(filename, nrows=0)
            temp = [item for item in cost_clouds_template_info]
            dollar_basis_template = int(temp[temp.index('dollar_basis:') + 1])

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            deflators = pd.read_csv(omega_globals.options.ip_deflators_file, skiprows=1, index_col=0).to_dict('index')

            adjustment_factor = deflators[omega_globals.options.analysis_dollar_basis]['price_deflator'] \
                                / deflators[dollar_basis_template]['price_deflator']

            df['new_vehicle_mfr_cost_dollars'] = df['new_vehicle_mfr_cost_dollars'] * adjustment_factor

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

                CostCloud.cost_cloud_data_columns = df.columns.drop(['simulated_vehicle_id', 'model_year',
                                                                     'cost_curve_class'])

        return template_errors

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


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        init_fail = []
        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.vehicle_simulation_results_and_costs_file, verbose=True)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
