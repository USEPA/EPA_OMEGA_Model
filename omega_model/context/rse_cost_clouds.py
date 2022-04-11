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


class CostCloud(OMEGABase, CostCloudBase):
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    _max_year = 0  # maximum year of cost cloud data (e.g. 2050), set by ``init_cost_clouds_from_file()``

    cost_cloud_data_columns = []

    # for reporting powertrain cost breakdowns
    cost_cloud_cost_columns = ['engine_cost', 'driveline_cost', 'emachine_cost', 'battery_cost',
                               'electrified_driveline_cost', 'glider_structure_cost', 'glider_non_structure_cost']

    cloud_non_numeric_columns = ['cost_curve_class', 'structure_material', 'vehicle_name']

    @staticmethod
    def eval_rse(powertrain_type, cost_curve_class, rse_name, rlhp20s, rlhp60s,
                 eng_rated_hps, etw_lbs, battery_kwhs, structure_masses_lbs, structure_materials, fooprint_ft2s):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            powertrain_type (str): e.g. 'ICE', 'BEV' ...
            cost_curve_class (str): name of the tech package, e.g. 'GDI_TRX12_SS0'
            rse_name (str): e.g. name of the drive cycle phase to calculate for
            rlhp20s (iterable): roadload horsepower at 20 MPH values
            rlhp60s (iterable): roadload horsepower at 60 MPH values
            eng_rated_hps (iterable): engine horsepowers
            etw_lbs (iterable): test weights, e.g. 3500 lbs
            battery_kwhs(iterable): battery capacities, kWh

        Returns:
            list of values evaluated by combining the terms

        """
        results = []
        eng_rated_hps_list = []
        etw_lbs_list = []
        battery_kwhs_list = []
        structure_masses_lbs_list = []
        structure_materials_list = []
        fooprint_ft2s_list = []

        for rlhp20 in rlhp20s:
            for rlhp60 in rlhp60s:
                for eng_rated_hp in eng_rated_hps:
                    for ETW, battery_kwh, structure_mass_lbs, structure_material, footprint_ft2\
                            in zip(etw_lbs, battery_kwhs, structure_masses_lbs, structure_materials, fooprint_ft2s):
                        RLHP20 = rlhp20 / ETW
                        RLHP60 = rlhp60 / ETW
                        HP_ETW = eng_rated_hp / ETW
                        results.append(eval(_cache[powertrain_type][cost_curve_class]['rse'][rse_name], {}, locals()))

                        eng_rated_hps_list.append(eng_rated_hp)
                        etw_lbs_list.append(ETW)
                        battery_kwhs_list.append(battery_kwh)
                        structure_masses_lbs_list.append(structure_mass_lbs)
                        structure_materials_list.append(structure_material)
                        fooprint_ft2s_list.append(footprint_ft2)

        return results, eng_rated_hps_list, etw_lbs_list, battery_kwhs_list, \
               structure_masses_lbs_list, structure_materials_list, fooprint_ft2s_list

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
        input_template_columns = {'cost_curve_class',
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

        CostCloud.cost_cloud_data_columns = list(CostCloud.cost_cloud_data_columns) + CostCloud.cost_cloud_cost_columns

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
        from context.powertrain_cost import PowertrainCost
        from context.glider_cost import GliderCost
        from producer.vehicles import VehicleAttributeCalculations, Vehicle
        import copy

        import time
        start_time = time.time()

        # print('Generating Cost Cloud for %s' % vehicle.name)

        vehicle_rlhp20 = \
            calc_roadload_hp(vehicle.target_coef_a, vehicle.target_coef_b, vehicle.target_coef_c, 20)

        vehicle_rlhp60 = \
            calc_roadload_hp(vehicle.target_coef_a, vehicle.target_coef_b, vehicle.target_coef_c, 60)

        # sweep vehicle params (for now, final ranges TBD)
        rlhp20s = [vehicle_rlhp20 * 0.95, vehicle_rlhp20, vehicle_rlhp20 * 1.05]
        rlhp60s = [vehicle_rlhp60 * 0.95, vehicle_rlhp60, vehicle_rlhp60 * 1.05]

        vehicle_footprints = [vehicle.footprint_ft2 * 0.95, vehicle.footprint_ft2, vehicle.footprint_ft2 * 1.05]

        cost_cloud = pd.DataFrame()

        cloud_points = []  # build a list of dicts that will be dumped into the cloud at the end
                           # (faster than sequentially appending Series objects)

        cost_curve_classes = _cache[vehicle.fueling_class]

        search_iterations = 0

        for ccc in cost_curve_classes:
            for structure_material in MassScaling.structure_materials:
                for footprint_ft2 in vehicle_footprints:
                    for rlhp20 in rlhp20s:
                        for rlhp60 in rlhp60s:
                            cloud_point = cost_curve_classes[ccc]['tech_flags'].to_dict()

                            # TODO: we need to deal with these properly, right now they are automatic in the powertrain cost...
                            cloud_point['ac_leakage'] = 1
                            cloud_point['ac_efficiency'] = 1

                            # ------------------------------------------------------------------------------------#
                            # size components ...
                            if vehicle.powertrain_type == 'ICE':
                                rated_hp = vehicle.eng_rated_hp
                            elif vehicle.powertrain_type == 'BEV':
                                rated_hp = vehicle.motor_kw * 1.34102
                            else:  # HEVs / PHEVs... what to do about sizing...?
                                rated_hp = vehicle.eng_rated_hp + vehicle.motor_kw * 1.34102

                            prior_powertrain_mass_lbs = 1
                            prior_rated_hp = 1
                            prior_battery_kwh = 1
                            convergence_tolerance = 0.01

                            battery_kwh = vehicle.battery_kwh  # for now...
                            motor_kw = vehicle.motor_kw  # for now...

                            converged = False
                            while not converged:
                                search_iterations += 1
                                # print('.')

                                # rated hp sizing --------------------------------------------------------------- #
                                structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, \
                                delta_glider_non_structure_mass_lbs, usable_battery_capacity_norm = \
                                    MassScaling.calc_mass_terms(vehicle, structure_material, rated_hp,
                                                                battery_kwh, footprint_ft2)

                                vehicle_curbweight_lbs = \
                                    vehicle.base_year_glider_non_structure_mass_lbs + \
                                    delta_glider_non_structure_mass_lbs + \
                                    powertrain_mass_lbs + \
                                    structure_mass_lbs + \
                                    battery_mass_lbs

                                rated_hp = vehicle_curbweight_lbs / vehicle.base_year_curbweight_lbs_to_hp

                                # set up RSE terms and run RSEs
                                ETW = vehicle_curbweight_lbs + DriveCycleBallast.get_ballast_lbs(vehicle)

                                RLHP20 = rlhp20 / ETW
                                RLHP60 = rlhp60 / ETW
                                HP_ETW = rated_hp / ETW

                                for rse_name in cost_curve_classes[ccc]['rse']:
                                    cloud_point[rse_name] = \
                                        eval(_cache[vehicle.fueling_class][ccc]['rse'][rse_name], {},
                                             {'ETW': ETW, 'RLHP20': RLHP20, 'RLHP60': RLHP60, 'HP_ETW': HP_ETW})

                                # battery sizing -------------------------------------------------------------------- #
                                if vehicle.powertrain_type != 'ICE':
                                    cloud_point = vehicle.calc_cert_values(cloud_point)  # TODO: should NOT pass in tech flags here... even though they get ignored...?

                                    # TODO: get rid of hard-coded 300:
                                    if cloud_point['cert_direct_oncycle_kwh_per_mile']:
                                        battery_kwh = 300 * cloud_point['onroad_direct_kwh_per_mile'] / usable_battery_capacity_norm

                                # determine convergence ------------------------------------------------------------- #
                                converged = abs(
                                    1 - powertrain_mass_lbs / prior_powertrain_mass_lbs) <= convergence_tolerance and \
                                            abs(1 - rated_hp / prior_rated_hp) <= convergence_tolerance

                                if vehicle.powertrain_type != 'ICE':
                                    converged = converged and \
                                            abs(1 - battery_kwh / prior_battery_kwh) < convergence_tolerance

                                # print(rated_hp, prior_rated_hp, rated_hp / prior_rated_hp)
                                # print(vehicle_curbweight_lbs, powertrain_mass_lbs, prior_powertrain_mass_lbs, powertrain_mass_lbs / prior_powertrain_mass_lbs)

                                prior_powertrain_mass_lbs = powertrain_mass_lbs
                                prior_rated_hp = rated_hp
                                prior_battery_kwh = battery_kwh

                                # ------------------------------------------------------------------------------------#

                            if vehicle.powertrain_type == 'ICE':
                                cloud_point = vehicle.calc_cert_values(cloud_point)

                            v = copy.copy(vehicle)
                            v.footprint_ft2 = footprint_ft2
                            v.set_target_co2e_grams_per_mile()
                            cloud_point['target_co2e_grams_per_mile'] = v.target_co2e_grams_per_mile

                            cloud_point['credits_co2e_grams_per_mile'] = \
                                cloud_point['cert_co2e_grams_per_mile'] - cloud_point['target_co2e_grams_per_mile']

                            # required cloud data for powertrain costing, etc:
                            cloud_point['cost_curve_class'] = ccc
                            cloud_point['curbweight_lbs'] = vehicle_curbweight_lbs
                            cloud_point['battery_kwh'] = battery_kwh
                            cloud_point['structure_mass_lbs'] = structure_mass_lbs
                            cloud_point['footprint_ft2'] = footprint_ft2
                            cloud_point['structure_material'] = structure_material
                            cloud_point['motor_kw'] = motor_kw

                            # informative data for troubleshooting:
                            if vehicle.model_year in omega_globals.options.log_vehicle_cloud_years or \
                                    omega_globals.options.log_vehicle_cloud_years == 'all':
                                cloud_point['vehicle_name'] = vehicle.name
                                cloud_point['model_year'] = vehicle.model_year
                                cloud_point['delta_glider_non_structure_mass_lbs'] = delta_glider_non_structure_mass_lbs
                                cloud_point['battery_mass_lbs']= battery_mass_lbs
                                cloud_point['powertrain_mass_lbs'] = powertrain_mass_lbs
                                cloud_point['etw_lbs'] = ETW
                                cloud_point['rated_hp'] = rated_hp
                                cloud_point['vehicle_eng_rated_hp'] = vehicle.eng_rated_hp
                                cloud_point['vehicle_mot_rated_kw'] = vehicle.motor_kw
                                cloud_point['rlhp20'] = rlhp20
                                cloud_point['rlhp60'] = rlhp60

                            cloud_points.append(cloud_point)

        cost_cloud = pd.DataFrame(cloud_points)

        powertrain_costs = PowertrainCost.calc_cost(vehicle, cost_cloud)  # includes battery cost
        powertrain_cost_terms = ['engine_cost', 'driveline_cost', 'emachine_cost', 'battery_cost',
                                 'electrified_driveline_cost']
        for idx, ct in enumerate(powertrain_cost_terms):
            cost_cloud[ct] = powertrain_costs[idx]

        glider_costs = GliderCost.calc_cost(vehicle, cost_cloud)  # includes structure_cost and glider_non_structure_cost
        glider_cost_terms = ['glider_structure_cost', 'glider_non_structure_cost']
        for idx, ct in enumerate(glider_cost_terms):
            cost_cloud[ct] = glider_costs[idx]

        cost_terms = powertrain_cost_terms + glider_cost_terms

        cost_cloud['new_vehicle_mfr_cost_dollars'] = \
            vehicle.base_year_glider_non_structure_cost_dollars + \
            cost_cloud[cost_terms].sum(axis=1)

        # calculate producer generalized cost
        cost_cloud = omega_globals.options.ProducerGeneralizedCost.\
            calc_generalized_cost(vehicle, cost_cloud, 'onroad_direct_co2e_grams_per_mile',
                                  'onroad_direct_kwh_per_mile', 'new_vehicle_mfr_cost_dollars')

        # print('done %.2f %d' % ((time.time() - start_time), search_iterations))
        # print('done %.2f' % (time.time() - start_time))

        if vehicle.model_year in omega_globals.options.log_vehicle_cloud_years or \
                omega_globals.options.log_vehicle_cloud_years == 'all':
            with open(omega_globals.options.output_folder + 'cost_clouds_%s.csv' % vehicle.powertrain_type, 'a') as f:
                cost_cloud.to_csv(f, mode='a', header=not f.tell(), columns=sorted(cost_cloud.columns), index=False)

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

