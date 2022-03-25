"""

**Routines to create simulated vehicle data (vehicle energy/CO2e consumption, off-cycle tech application, and cost data)
and calculate frontiers from response surface equations fitted to vehicle simulation results**

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
rows.  The template header uses a dynamic format.

The data represents vehicle technology options and costs by simulation class (cost curve class) and model year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,0.3,dollar_basis:,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        TODO: add sample

Data Column Name and Description
    :package:
        Unique row identifier, specifies the powertrain package

    TODO: add the rest of the columns

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

    TODO: add the rest of the flags...

    :high_eff_alternator:
        = 1 if vehicle qualifies for the high efficiency alternator off-cycle credit, = 0 otherwise

    :start_stop:
        = 1 if vehicle qualifies for the engine start-stop off-cycle credit, = 0 otherwise

----

**CODE**

"""
import numpy as np
import pandas as pd

print('importing %s' % __file__)

from omega_model import *

_cache = dict()

# define list of non-numeric columns to ignore during frontier creation since they goof up pandas auto-typing of
# columns when switching between Series and DataFrame representations
cloud_non_numeric_columns = ['package']


class CostCloud(OMEGABase, CostCloudBase):
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    _max_year = 0  # maximum year of cost cloud data (e.g. 2050), set by ``init_cost_clouds_from_file()``

    cost_cloud_data_columns = []

    @staticmethod
    def eval_rse(powertrain_type, cost_curve_class, rse_name, rlhp20s, rlhp60s, etw_hps, etws):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            powertrain_type (str): e.g. 'ICE', 'BEV' ...
            cost_curve_class (str): name of the tech package, e.g. 'GDI_TRX12_SS0'
            rse_name (str): e.g. name of the drive cycle phase to calculate for
            rlhp20s (iterable): roadload horsepower at 20 MPH values
            rlhp60s (iterable): roadload horsepower at 60 MPH values
            etw_hps (iterable): weight to horsepower ratios
            etws (iterable): test weights, e.g. 3500 lbs

        Returns:
            list of values evaluated by combining the terms

        """
        results = []
        etw_lbs = []

        for RLHP20 in rlhp20s:
            for RLHP60 in rlhp60s:
                for ETW in etws:
                    for ETW_HP in etw_hps:
                        HP_ETW = 1 / ETW_HP
                        results.append(eval(_cache[powertrain_type][cost_curve_class]['rse'][rse_name], {}, locals()))
                        etw_lbs.append(ETW)

        return results, etw_lbs

    @staticmethod
    def init_from_ice_file(filename, powertrain_type='ICE', verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing CostCloud from %s...' % filename, echo_console=True)
        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'cost_curve_class','engine_displacement_L', 'engine_cylinders',
                                  'high_eff_alternator', 'start_stop', 'hev', 'hev_truck', 'deac_pd',
                                  'deac_fc', 'cegr', 'atk2', 'gdi', 'turb12', 'turb11', 'gas_fuel',
                                  'diesel_fuel'}

        # input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)
        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:
            # read in the data portion of the input file
            cost_clouds_template_info = pd.read_csv(filename, nrows=0)
            temp = [item for item in cost_clouds_template_info]

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            # validate drive cycle columns
            from policy.drive_cycles import DriveCycles
            drive_cycle_columns = set.difference(set(df.columns), input_template_columns)

            if not all([dc in DriveCycles.drive_cycle_names for dc in drive_cycle_columns]):
                template_errors.append('Invalid drive cycle column in %s' % filename)

            if not template_errors:
                # RSE columns are the drive cycle columns + the displacement and cylinder columns
                rse_columns = drive_cycle_columns
                rse_columns.update(['engine_displacement_L', 'engine_cylinders'])

                non_data_columns = list(rse_columns) + ['cost_curve_class']
                CostCloud.cost_cloud_data_columns = df.columns.drop(non_data_columns)

                _cache[powertrain_type] = dict()

                # convert cost clouds into curves and set up cost_curves table...
                cost_curve_classes = df['cost_curve_class'].unique()
                # for each cost curve class
                for cost_curve_class in cost_curve_classes:
                    class_cloud = df[df['cost_curve_class'] == cost_curve_class].iloc[0]
                    _cache[powertrain_type][cost_curve_class] = {'rse': dict(), 'tech_flags': pd.Series()}

                    for c in rse_columns:
                        _cache[powertrain_type][cost_curve_class]['rse'][c] = compile(class_cloud[c], '<string>', 'eval')

                    _cache[powertrain_type][cost_curve_class]['tech_flags'] = class_cloud[CostCloud.cost_cloud_data_columns]

        return template_errors

    def init_from_bev_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing CostCloud from %s...' % filename, echo_console=True)
        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'cost_curve_class'}

        # input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)
        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:
            # read in the data portion of the input file
            cost_clouds_template_info = pd.read_csv(filename, nrows=0)
            temp = [item for item in cost_clouds_template_info]

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            # validate drive cycle columns
            from policy.drive_cycles import DriveCycles
            drive_cycle_columns = set.difference(set(df.columns), input_template_columns)

            if not all([dc in DriveCycles.drive_cycle_names for dc in drive_cycle_columns]):
                template_errors.append('Invalid drive cycle column in %s' % filename)

            if not template_errors:
                # RSE columns are the drive cycle columns + the displacement and cylinder columns
                rse_columns = drive_cycle_columns

                non_data_columns = list(rse_columns) + ['cost_curve_class']
                CostCloud.cost_cloud_data_columns = df.columns.drop(non_data_columns)

                _cache['BEV'] = dict()

                # convert cost clouds into curves and set up cost_curves table...
                cost_curve_classes = df['cost_curve_class'].unique()
                # for each cost curve class
                for cost_curve_class in cost_curve_classes:
                    class_cloud = df[df['cost_curve_class'] == cost_curve_class].iloc[0]
                    _cache['BEV'][cost_curve_class] = {'rse': dict(), 'tech_flags': pd.Series()}

                    for c in rse_columns:
                        _cache['BEV'][cost_curve_class]['rse'][c] = compile(class_cloud[c], '<string>', 'eval')

                    _cache['BEV'][cost_curve_class]['tech_flags'] = class_cloud[CostCloud.cost_cloud_data_columns]

        return template_errors

    def init_from_phev_file(filename, verbose=False):
        # they're the same for now, so why reinvent the wheel?!
        return CostCloud.init_from_ice_file(filename, powertrain_type='PHEV', verbose=verbose)

    @staticmethod
    def init_cost_clouds_from_files(ice_filename, bev_filename, phev_filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            ice_filename (str): name of ICE/HEV vehicle simulation data input file
            bev_filename (str): name of BEV vehicle simulation data input file
            phev_filename (str): name of PHEV vehicle simulation data input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        _cache.clear()

        template_errors = []

        template_errors += CostCloud.init_from_ice_file(ice_filename, verbose=verbose)
        template_errors += CostCloud.init_from_bev_file(bev_filename, verbose=verbose)
        template_errors += CostCloud.init_from_phev_file(phev_filename, verbose=verbose)

        return template_errors

    @staticmethod
    def get_cloud(vehicle):
        """
        Retrieve cost cloud for the given vehicle.

        Args:
            vehicle (Vehicle): the vehicle to get the cloud for

        Returns:
            Copy of the requested cost cload data.

        """
        import numpy as np
        from context.mass_scaling import MassScaling
        from policy.drive_cycle_ballast import DriveCycleBallast

        cost_cloud = pd.DataFrame()

        # TODO: decide sweep ranges based on vehicle characteristics, for example, unibody v. body-on-frame or other
        # properties?

        vehicle_rlhp20 = calc_roadload_hp(vehicle.target_coef_a, vehicle.target_coef_b, vehicle.target_coef_c, 20)
        vehicle_rlhp60 = calc_roadload_hp(vehicle.target_coef_a, vehicle.target_coef_b, vehicle.target_coef_c, 60)

        # rlhp20s = [0.001, 0.00175, 0.0025]
        # rlhp60s = [0.003, 0.004, 0.006]

        # sweep vehicle params (for now, final ranges TBD)
        rlhp20s = [vehicle_rlhp20 * 0.95, vehicle_rlhp20, vehicle_rlhp20 * 1.05]
        rlhp60s = [vehicle_rlhp60 * 0.95, vehicle_rlhp60, vehicle_rlhp60 * 1.05]

        vehicle_curbweights_lbs = []
        for structure_material in ['steel', 'aluminum']:
            vehicle.structure_material = structure_material
            structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs = MassScaling.calc_mass_terms(vehicle)

            vehicle_curbweights_lbs.append(vehicle.glider_non_structure_mass_lbs + powertrain_mass_lbs + structure_mass_lbs + battery_mass_lbs)

        etws = np.array(vehicle_curbweights_lbs) + DriveCycleBallast.get_ballast_lbs(vehicle)  # TODO: get ballast from policy

        etw_hps = [vehicle.etw_lbs / vehicle.eng_rated_hp]

        # TODO: if vehicle up for redesign, query all classes, otherwise use same cost_curve class as prior year...?
        # TODO: need to assign cost curve class to vehicles from chosen tech package...?  Not sure how that will work
        # when interpolating along the frontier.......

        cost_curve_classes = _cache[vehicle.fueling_class]

        for cc in cost_curve_classes:
            # TODO: code here to decide if cost curve is applicable to vehicle (e.g. diesel for diesel, etc...)
            # print(cc)
            cc_cloud = pd.DataFrame()
            for r in cost_curve_classes[cc]['rse']:
                # print(r)
                cc_cloud[r], cc_cloud['etw_lbs'] = CostCloud.eval_rse(vehicle.fueling_class, cc, r, rlhp20s, rlhp60s, etw_hps, etws)
            cc_cloud['cost_curve_class'] = cc
            cc_cloud[cost_curve_classes[cc]['tech_flags'].keys()] = cost_curve_classes[cc]['tech_flags']
            cost_cloud = cost_cloud.append(cc_cloud)

        # TODO: calc vehicle mass(es) so they can be used to calc costs

        # TODO: calc costs!!

        return cost_cloud


if __name__ == '__main__':
    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from policy.drive_cycles import DriveCycles

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += CostCloud.\
            init_cost_clouds_from_files(omega_globals.options.ice_vehicle_simulation_results_file,
                                        omega_globals.options.bev_vehicle_simulation_results_file,
                                        omega_globals.options.phev_vehicle_simulation_results_file,
                                        verbose=True)

        if not init_fail:
            cost_curve_class = list(_cache['ICE'])[0]

            print(CostCloud.eval_rse('ICE', cost_curve_class, 'engine_cylinders_RSE',
                                     RLHP20=[0.001], RLHP60=[0.003], ETW_HP=[5], ETW=[2500]))

            print(CostCloud.eval_rse('ICE', cost_curve_class, DriveCycles.drive_cycle_names[0],
                                     RLHP20=[0.001], RLHP60=[0.003], ETW_HP=[5], ETW=[2500]))

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
