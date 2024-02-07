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

       input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::
        :widths: auto

        input_template_name:,context.rse_cost_clouds,input_template_version:,0.21

Sample Data Columns
    .. csv-table::
        :widths: auto

        cost_curve_class,cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile,cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile,cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile,cs_us06_1:cert_direct_oncycle_co2e_grams_per_mile,cs_us06_2:cert_direct_oncycle_co2e_grams_per_mile,engine_displacement_liters,engine_cylinders,hev_motor_kw,hev_batt_kwh,unibody,high_eff_alternator,start_stop,mhev,hev,hev_truck,deac_pd,deac_fc,cegr,atk2,gdi,turb12,turb11,gas_fuel,diesel_fuel,awd,fwd,trx10,trx11,trx12,trx21,trx22,ecvt,ice,fcv,phev
        GDI_TRX10_SS0,(18.5453154586108 + RLHP20 * -3982.40242855764 + RLHP60 * -2817.56800285645 + HP_ETW * 137.278361090642 + ETW * 3.32340903920597E-02 + RLHP20 * RLHP60 * 110807.33630121 + RLHP20 * HP_ETW * -4627.4326168311 + RLHP20 * ETW * 6.70966614616728 + RLHP60 * HP_ETW * -30332.4612603004 + RLHP60 * ETW * 5.00876531603704 + HP_ETW * ETW * 0.294125190164327 + RLHP20 * RLHP20 * 1256197.72766571 + RLHP60 * RLHP60 * 481695.350341595 + HP_ETW * HP_ETW * 1609.12975282719 + ETW * ETW * -8.29944026819907E-08),(9.5791054371677 + RLHP20 * -3590.79375495996 + RLHP60 * 50.6722067942342 + HP_ETW * 347.705321630021 + ETW * 3.48152635650444E-02 + RLHP20 * RLHP60 * 149496.500686564 + RLHP20 * HP_ETW * -2223.94352321471 + RLHP20 * ETW * 9.48200087525242 + RLHP60 * HP_ETW * 2351.5654615553 + RLHP60 * ETW * 0.461922645205613 + HP_ETW * ETW * 0.471412910808918 + RLHP20 * RLHP20 * 1436117.83181053 + RLHP60 * RLHP60 * 39270.700829774 + HP_ETW * HP_ETW * 406.447384354043 + ETW * ETW * -7.71706080556899E-08),(16.90268475641 + RLHP20 * -3242.90634919696 + RLHP60 * -2629.28146207688 + HP_ETW * 118.975915082563 + ETW * 2.89017033343035E-02 + RLHP20 * RLHP60 * 92250.9850799915 + RLHP20 * HP_ETW * -4113.71943103567 + RLHP20 * ETW * 5.80112048232174 + RLHP60 * HP_ETW * -26327.5543378143 + RLHP60 * ETW * 4.36516119956593 + HP_ETW * ETW * 0.257209252731031 + RLHP20 * RLHP20 * 1079137.01783225 + RLHP60 * RLHP60 * 434252.441619121 + HP_ETW * HP_ETW * 1393.97146449451 + ETW * ETW * -7.30125392390274E-08),(17.9637457539001 + RLHP20 * -3472.62459269551 + RLHP60 * -4398.38499132763 + HP_ETW * 215.768640351807 + ETW * 8.51144457518359E-03 + RLHP20 * RLHP60 * 149970.005773222 + RLHP20 * HP_ETW * -21981.6870797447 + RLHP20 * ETW * 3.63778043662855 + RLHP60 * HP_ETW * -59423.2422059756 + RLHP60 * ETW * 8.04728064311791 + HP_ETW * ETW * 7.86039589271401E-02 + RLHP20 * RLHP20 * 848749.589907981 + RLHP60 * RLHP60 * 616072.465286428 + HP_ETW * HP_ETW * 2979.55595160764 + ETW * ETW * -1.4351363539333E-08),(9.56569818390454 + RLHP20 * 6596.09179395163 + RLHP60 * -613.085872919802 + HP_ETW * -318.90997967565 + ETW * 0.101983529095103 + RLHP20 * RLHP60 * 2170002.03346542 + RLHP20 * HP_ETW * -64249.5598973361 + RLHP20 * ETW * 2.75914558215585 + RLHP60 * HP_ETW * -44733.8189080356 + RLHP60 * ETW * 4.62964787308715 + HP_ETW * ETW * -3.71755481566662E-02 + RLHP20 * RLHP20 * -2853471.14537167 + RLHP60 * RLHP60 * 128583.11933152 + HP_ETW * HP_ETW * 7854.33640825238 + ETW * ETW * 1.26205572300569E-07),(41.1164896514876 + RLHP20 * 2234.44390496137 + RLHP60 * -22070.3587003615 + HP_ETW * 610.147530710725 + ETW * 1.28797324323515E-02 + RLHP20 * RLHP60 * -728006.913610047 + RLHP20 * HP_ETW * 46152.9690756253 + RLHP20 * ETW * -2.88589393142033 + RLHP60 * HP_ETW * -118593.147293144 + RLHP60 * ETW * 15.9274202719561 + HP_ETW * ETW * -3.60173610138859E-02 + RLHP20 * RLHP20 * -309499.872474524 + RLHP60 * RLHP60 * 2587604.52877069 + HP_ETW * HP_ETW * 1551.30184056957 + ETW * ETW * 5.53256211916988E-08),(9.42426552897976E-02 + RLHP20 * -8.67753548243127 + RLHP60 * -1.25433074169979 + HP_ETW * 2.36155977722839 + ETW * -5.02570130409737E-05 + RLHP20 * RLHP60 * -1346.72585688432 + RLHP20 * HP_ETW * -2.01875340702074 + RLHP20 * ETW * -2.86900770294598E-04 + RLHP60 * HP_ETW * -9.79248304114116 + RLHP60 * ETW * -8.02462001216872E-04 + HP_ETW * ETW * 1.31800222688058E-02 + RLHP20 * RLHP20 * 4522.82437754836 + RLHP60 * RLHP60 * 862.766253485694 + HP_ETW * HP_ETW * -14.9086015192973 + ETW * ETW * 4.04706726926766E-09),(-4.82637156703734 + RLHP20 * -105.074481298302 + RLHP60 * 54.2696982370053 + HP_ETW * 151.462510854908 + ETW * 0.00130625681466241 + RLHP20 * RLHP60 * -10076.0711025307 + RLHP20 * HP_ETW * 261.577105272997 + RLHP20 * ETW * -0.010298721021474 + RLHP60 * HP_ETW * -4.07581237442843 + RLHP60 * ETW * -0.0209676757797716 + HP_ETW * ETW * -0.00296283965731266 + RLHP20 * RLHP20 * 47916.0507236993 + RLHP60 * RLHP60 * 6235.77804094256 + HP_ETW * HP_ETW * -581.199529326768 + ETW * ETW * -4.05477867514449E-08),0,0,1,0,0,0,0,0,0,0,0,0,1,0,0,1,0,0,1,1,0,0,0,0,0,1,0,0
        GDI_TRX10_SS1,(17.3945556524814 + RLHP20 * -3678.93129741256 + RLHP60 * -3049.38693353786 + HP_ETW * 67.2832031730545 + ETW * 3.28941003129913E-02 + RLHP20 * RLHP60 * 109636.473272387 + RLHP20 * HP_ETW * -5729.03684895062 + RLHP20 * ETW * 6.69010202922273 + RLHP60 * HP_ETW * -30027.6511414333 + RLHP60 * ETW * 5.03102604096674 + HP_ETW * ETW * 0.253718771476502 + RLHP20 * RLHP20 * 1204537.81741955 + RLHP60 * RLHP60 * 493584.495898655 + HP_ETW * HP_ETW * 1931.96067256056 + ETW * ETW * -8.00143560878314E-08),(6.09111677491136 + RLHP20 * -3081.94312700559 + RLHP60 * -26.3676295610723 + HP_ETW * 237.351389156045 + ETW * 3.45305581858264E-02 + RLHP20 * RLHP60 * 198197.59303984 + RLHP20 * HP_ETW * -4158.45730287789 + RLHP20 * ETW * 9.43126927729562 + RLHP60 * HP_ETW * 2678.06741551965 + RLHP60 * ETW * 0.472345818320218 + HP_ETW * ETW * 0.405183157861073 + RLHP20 * RLHP20 * 1270438.81851366 + RLHP60 * RLHP60 * 33613.6602886178 + HP_ETW * HP_ETW * 1029.38089977022 + ETW * ETW * -8.55268065109595E-08),(15.2414651650666 + RLHP20 * -3140.68640670414 + RLHP60 * -2688.84923545992 + HP_ETW * 42.788916424425 + ETW * 2.85968485885624E-02 + RLHP20 * RLHP60 * 102784.268828302 + RLHP20 * HP_ETW * -5382.85950863125 + RLHP20 * ETW * 5.78794685887964 + RLHP60 * HP_ETW * -26055.7046118476 + RLHP60 * ETW * 4.38225109623388 + HP_ETW * ETW * 0.212795915443702 + RLHP20 * RLHP20 * 1051240.4750741 + RLHP60 * RLHP60 * 430073.482368004 + HP_ETW * HP_ETW * 1758.43536857247 + ETW * ETW * -7.31926954156259E-08),(18.0397672059242 + RLHP20 * -3458.63617341381 + RLHP60 * -4434.1760180141 + HP_ETW * 214.730811606447 + ETW * 8.48047223497087E-03 + RLHP20 * RLHP60 * 141263.645257291 + RLHP20 * HP_ETW * -21996.5452273929 + RLHP20 * ETW * 3.63944777094314 + RLHP60 * HP_ETW * -59401.3965935959 + RLHP60 * ETW * 8.04977129035753 + HP_ETW * ETW * 7.80462608067639E-02 + RLHP20 * RLHP20 * 852336.376483536 + RLHP60 * RLHP60 * 620251.888348202 + HP_ETW * HP_ETW * 2990.11761798953 + ETW * ETW * -1.29685668562444E-08),(17.229281279127 + RLHP20 * 3281.19554853941 + RLHP60 * -1093.11929055584 + HP_ETW * -354.773649847422 + ETW * 0.100820983700518 + RLHP20 * RLHP60 * 2093639.2063385 + RLHP20 * HP_ETW * -60792.7239868145 + RLHP20 * ETW * 3.03448556782973 + RLHP60 * HP_ETW * -43345.0109706843 + RLHP60 * ETW * 4.59964822522492 + HP_ETW * ETW * -3.43748579282498E-02 + RLHP20 * RLHP20 * -2233008.51113499 + RLHP60 * RLHP60 * 193707.967212162 + HP_ETW * HP_ETW * 7894.44336508737 + ETW * ETW * 1.77071424573799E-07),(51.9652982605103 + RLHP20 * 8112.63624490393 + RLHP60 * -29719.291811228 + HP_ETW * 670.791208277599 + ETW * 1.19964142403331E-02 + RLHP20 * RLHP60 * 1760214.52993652 + RLHP20 * HP_ETW * 48884.7464586267 + RLHP20 * ETW * -3.0468747508932 + RLHP60 * HP_ETW * -134151.498433435 + RLHP60 * ETW * 16.5196056612086 + HP_ETW * ETW * -5.00780312010795E-02 + RLHP20 * RLHP20 * -5174881.07759553 + RLHP60 * RLHP60 * 2847380.89699544 + HP_ETW * HP_ETW * 1933.97839645941 + ETW * ETW * 2.49944257702617E-08),(9.42426552897976E-02 + RLHP20 * -8.67753548243127 + RLHP60 * -1.25433074169979 + HP_ETW * 2.36155977722839 + ETW * -5.02570130409737E-05 + RLHP20 * RLHP60 * -1346.72585688432 + RLHP20 * HP_ETW * -2.01875340702074 + RLHP20 * ETW * -2.86900770294598E-04 + RLHP60 * HP_ETW * -9.79248304114116 + RLHP60 * ETW * -8.02462001216872E-04 + HP_ETW * ETW * 1.31800222688058E-02 + RLHP20 * RLHP20 * 4522.82437754836 + RLHP60 * RLHP60 * 862.766253485694 + HP_ETW * HP_ETW * -14.9086015192973 + ETW * ETW * 4.04706726926766E-09),(-4.82637156703734 + RLHP20 * -105.074481298302 + RLHP60 * 54.2696982370053 + HP_ETW * 151.462510854908 + ETW * 0.00130625681466241 + RLHP20 * RLHP60 * -10076.0711025307 + RLHP20 * HP_ETW * 261.577105272997 + RLHP20 * ETW * -0.010298721021474 + RLHP60 * HP_ETW * -4.07581237442843 + RLHP60 * ETW * -0.0209676757797716 + HP_ETW * ETW * -0.00296283965731266 + RLHP20 * RLHP20 * 47916.0507236993 + RLHP60 * RLHP60 * 6235.77804094256 + HP_ETW * HP_ETW * -581.199529326768 + ETW * ETW * -4.05477867514449E-08),0,0,1,0,1,0,0,0,0,0,0,0,1,0,0,1,0,0,1,1,0,0,0,0,0,1,0,0


Data Column Name and Description
    :cost_curve_class:
        Unique row identifier, specifies the powertrain package

    CHARGE-SUSTAINING SIMULATION RESULTS (example)
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile: response surface equation, CO2e grams/mile
        :cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile: response surface equation, CO2e grams/mile
        :cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile: response surface equation, CO2e grams/mile
        :cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile: response surface equation, CO2e grams/mile

    CHARGE-DEPLETING SIMULATION RESULTS (example)
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cd_ftp_1:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_2:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_3:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_hwfet:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile

    :engine_displacement_liters:
        Response surface equation for engine displacement in Liters, if applicable

    :engine_cylinders:
        Response surface equation for number of engine cylinders, if applicable

    :hev_motor_kw:
        Response surface equation or scalar value for hybrid electric vehicle motor power rating in kW

    :hev_batt_kwh:
        Response surface equation or scalar value for hybrid electric vehicle battery capacity rating in kWh

    :unibody:
        = 1 if powertrain package is associated with a unibody vehicle

    :high_eff_alternator:
        = 1 if powertrain package qualifies for the high efficiency alternator off-cycle credit, = 0 otherwise

    :start_stop:
        = 1 if powertrain package qualifies for the engine start-stop off-cycle credit, = 0 otherwise

    :mhev:
        = 1 if powertrain package represents a mild hybrid vehicle, e.g. 48V start-stop, etc, = 0 otherwise

    :hev:
        = 1 if powertrain package represents a strong hybrid vehicle, e.g. a powersplit hybrid, = 0 otherwise

    :hev_truck:
        = 1 if powertrain package represents a hybrid truck, = 0 otherwise

    :deac_pd:
        = 1 if powertrain package includes partial discrete cylinder deactivation, = 0 otherwise

    :deac_fc:
        = 1 if powertrain package includes full continuous cylinder deactivation, = 0 otherwise

    :cegr:
        = 1 if powertrain package includes cooled exhaust gas recirculation, = 0 otherwise

    :atk2:
        = 1 if powertrain package includes an high geometric compression ratio Atkinson cycle engine, = 0 otherwise

    :gdi:
        = 1 if powertrain package includes a gasoline direct injection engine, = 0 otherwise

    :turb12:
        = 1 if powertrain package includes an advanced turbo charger, = 0 otherwise

    :turb11:
        = 1 if powertrain package includes a convenvtional turbo charger, = 0 otherwise

    :cert_fuel_id:
        = cert fuel id, e.g. 'gasoline'

    :trx10:
        = 1 if powertrain package includes a baseline transmission, = 0 otherwise

    :trx11:
        = 1 if powertrain package includes an improved transmission, = 0 otherwise

    :trx12:
        = 1 if powertrain package includes an advanced transmission, = 0 otherwise

    :trx21:
        = 1 if powertrain package includes a high gear count transmission or equivalent, = 0 otherwise

    :trx22:
        = 1 if powertrain package includes an advanced high gear count transmission or equivalent, = 0 otherwise

    :ecvt:
        = 1 if powertrain package includes an powersplit-type hybrid vehicle transmission, = 0 otherwise

    :ice:
        = 1 if powertrain package is associated with an internal combustion engine, = 0 otherwise

    :fcv:
        = 1 if powertrain package is associated with a fuel cell vehicle, = 0 otherwise

    :phev:
        = 1 if powertrain package is associated with a plug-in hybrid vehicle, = 0 otherwise

    :bev:
        = 1 if powertrain package is associated with a battery-electric vehicle, = 0 otherwise

    :drive_system:
        = drive system, e.g. 'FWD', 'RWD', 'AWD'

    :application_id:
        = high-load application = 'HLA', standard-load application = 'SLA', medium-duty application = 'MDV'

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

from context.mass_scaling import MassScaling
from context.glider_cost import GliderCost

from policy.drive_cycle_ballast import DriveCycleBallast

from producer.vehicles import VehicleOnroadCalculations, Vehicle, is_up_for_redesign

_cache = dict()

# define list of non-numeric columns to ignore during frontier creation since they goof up pandas auto-typing of
# columns when switching between Series and DataFrame representations


class CostCloud(OMEGABase, CostCloudBase):
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    _max_year = 0  # maximum year of cost cloud data (e.g. 2050), set by ``init_cost_clouds_from_file()``

    cost_cloud_data_columns = set()

    # numeric columns generated by ``get_cloud()`` that we want to track and interpolate along the cost curve
    cost_cloud_generated_columns = ['curbweight_lbs', 'rated_hp', 'battery_kwh', 'total_emachine_kw',
                                    'ac_efficiency', 'ac_leakage', 'footprint_ft2', 'etw_lbs',
                                    'cert_utility_factor', 'onroad_utility_factor',
                                    'battery_sizing_onroad_direct_kwh_per_mile', 'tractive_motor_kw',
                                    'cert_engine_on_distance_frac', 'onroad_engine_on_distance_frac',
                                    'battery_mass_lbs', 'powertrain_mass_lbs', 'delta_glider_non_structure_mass_lbs',
                                    'glider_non_structure_mass_lbs', 'structure_mass_lbs']

    # for reporting powertrain cost breakdowns
    cost_cloud_cost_columns = ['engine_cost', 'driveline_cost', 'emachine_cost', 'battery_cost',
                               'electrified_driveline_cost', 'structure_cost', 'glider_non_structure_cost']

    cloud_non_numeric_columns = ['cost_curve_class', 'structure_material', 'powertrain_type', 'vehicle_name',
                                 'drive_system', 'application_id', 'cert_fuel_id']

    cloud_non_numeric_data_columns = ['cost_curve_class', 'structure_material', 'powertrain_type']

    tech_flags = set()
    rse_names = set()

    @staticmethod
    def init_from_ice_file(filename, powertrain_type='ICE', verbose=False):
        """
        Init ``CostCloud`` from ICE RSE data.

        Args:
            filename (str): the pathname of the file to load
            powertrain_type (str): e.g. 'ICE'
            verbose (bool): enhanced console output if ``True``

        Returns:
            list of encountered errors, if any

        """
        if verbose:
            omega_log.logwrite('\nInitializing CostCloud from %s...' % filename)
        input_template_name = __name__
        # TODO: move phev flag to phev rse only when it gets its own init:

        input_template_version = 0.22
        input_template_columns = {'cost_curve_class', 'engine_displacement_liters', 'engine_cylinders', 'hev_motor_kw',
                                  'hev_batt_kwh', 'high_eff_alternator', 'start_stop', 'mhev', 'hev',
                                  'hev_truck', 'deac_pd', 'deac_fc', 'cegr', 'atk2', 'gdi', 'turb12', 'turb11',
                                  'cert_fuel_id', 'trx10', 'trx11', 'trx12', 'trx21', 'trx22',
                                  'ecvt', 'ice', 'fcv', 'phev', 'drive_system', 'application_id'}

        # input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)
        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            # validate drive cycle columns
            from policy.drive_cycles import DriveCycles
            drive_cycle_columns = set.difference(set(df.columns), input_template_columns)

            if not all([dc in DriveCycles.drive_cycle_names for dc in drive_cycle_columns]):
                template_errors.append('Invalid drive cycle column in %s' % filename)

            if not template_errors:
                # RSE columns are the drive cycle columns + the displacement, cylinder count,
                # hev motor kW and hev battery kWh columns
                rse_columns = drive_cycle_columns
                rse_columns.update(['engine_displacement_liters', 'engine_cylinders', 'hev_motor_kw', 'hev_batt_kwh'])

                non_data_columns = list(rse_columns) + ['cost_curve_class', 'drive_system', 'application_id',
                                                        'cert_fuel_id']

                tech_flags = list(df.columns.drop(non_data_columns))
                CostCloud.cost_cloud_data_columns.update(tech_flags + ['engine_displacement_liters', 'engine_cylinders'])

                # convert cost clouds into curves and set up cost_curves table...
                cost_curve_classes = df['cost_curve_class'].unique()
                drive_systems = df['drive_system'].unique()
                application_ids = df['application_id'].unique()
                cert_fuel_ids = df['cert_fuel_id'].unique()

                # for each cost curve class
                for cost_curve_class in cost_curve_classes:
                    CostCloud.rse_names.update([cost_curve_class])

                    for cert_fuel_id in cert_fuel_ids:
                        for application_id in application_ids:
                            for drive_system in drive_systems:
                                cache_key = \
                                    '%s_%s_%s_%s' % (powertrain_type, cert_fuel_id, application_id, drive_system)

                                if cache_key not in _cache:
                                    _cache[cache_key] = dict()

                                rse_condition = (df['cost_curve_class'] == cost_curve_class) & \
                                                (df['cert_fuel_id'] == cert_fuel_id) & \
                                                (df['drive_system'] == drive_system) & \
                                                (df['application_id'] == application_id)

                                if any(rse_condition):

                                    class_cloud = df[rse_condition].iloc[0]

                                    _cache[cache_key][cost_curve_class] = \
                                        {'rse': dict(), 'tech_flags': pd.Series(dtype='float64')}

                                    for c in rse_columns:
                                        _cache[cache_key][cost_curve_class]['rse'][c] = \
                                            compile(str(class_cloud[c]), '<string>', 'eval')

                                    rse_tuple = (sorted(rse_columns), tuple(class_cloud[sorted(rse_columns)]))

                                    _cache[cache_key][cost_curve_class]['rse_names'] = rse_tuple[0]

                                    _cache[cache_key][cost_curve_class]['rse_tuple'] = \
                                        str(rse_tuple[1]).replace("'", '')

                                    _cache[cache_key][cost_curve_class]['tech_flags'] = class_cloud[tech_flags]

                                    CostCloud.tech_flags.update(tech_flags)

        return template_errors

    @staticmethod
    def init_from_bev_file(filename, verbose=False):
        """
        Init ``CostCloud`` from BEV RSE data.

        Args:
            filename (str): the pathname of the file to load
            verbose (bool): enhanced console output if ``True``

        Returns:
            list of encountered errors, if any

        """
        if verbose:
            omega_log.logwrite('\nInitializing CostCloud from %s...' % filename)
        input_template_name = __name__
        input_template_version = 0.13
        input_template_columns = {'cost_curve_class', 'bev_motor_kw', 'bev', 'drive_system', 'cert_fuel_id',
                                  }
        powertrain_type = 'BEV'

        # input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)
        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:
            # read in the data portion of the input file
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
                rse_columns.update(['bev_motor_kw'])

                non_data_columns = list(rse_columns) + ['cost_curve_class', 'drive_system', 'cert_fuel_id']  # , 'application_id'] eventually?
                tech_flags = list(df.columns.drop(non_data_columns))
                CostCloud.cost_cloud_data_columns.update(tech_flags)

                # convert cost clouds into curves and set up cost_curves table...
                cost_curve_classes = df['cost_curve_class'].unique()
                drive_systems = df['drive_system'].unique()
                cert_fuel_ids = df['cert_fuel_id'].unique()

                # for each cost curve class
                for cost_curve_class in cost_curve_classes:
                    CostCloud.rse_names.update([cost_curve_class])

                    for cert_fuel_id in cert_fuel_ids:
                        for drive_system in drive_systems:

                            cache_key = '%s_%s_%s' % (powertrain_type, cert_fuel_id, drive_system)

                            if cache_key not in _cache:
                                _cache[cache_key] = dict()

                            rse_condition = (df['cost_curve_class'] == cost_curve_class) & \
                                            (df['drive_system'] == drive_system)

                            if any(rse_condition):

                                class_cloud = df[rse_condition].iloc[0]

                                _cache[cache_key][cost_curve_class] = \
                                    {'rse': dict(), 'tech_flags': pd.Series(dtype='float64')}

                                for c in rse_columns:
                                    _cache[cache_key][cost_curve_class]['rse'][c] = \
                                        compile(str(class_cloud[c]), '<string>', 'eval')

                                rse_tuple = (sorted(rse_columns), tuple(class_cloud[sorted(rse_columns)]))

                                _cache[cache_key][cost_curve_class]['rse_names'] = rse_tuple[0]

                                _cache[cache_key][cost_curve_class]['rse_tuple'] = \
                                    str(rse_tuple[1]).replace("'", '')

                                _cache[cache_key][cost_curve_class]['tech_flags'] = class_cloud[tech_flags]

                                CostCloud.tech_flags.update(tech_flags)

        return template_errors

    @staticmethod
    def init_from_phev_file(filename, verbose=False):
        """
        Init ``CostCloud`` from PHEV RSE data.

        Args:
            filename (str): the pathname of the file to load
            verbose (bool): enhanced console output if ``True``

        Returns:
            list of encountered errors, if any

        """
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

        CostCloud.tech_flags = set()
        CostCloud.cost_cloud_data_columns = set()

        template_errors = []

        template_errors += CostCloud.init_from_ice_file(ice_filename, verbose=verbose)
        template_errors += CostCloud.init_from_bev_file(bev_filename, verbose=verbose)
        template_errors += CostCloud.init_from_phev_file(phev_filename, verbose=verbose)

        CostCloud.cost_cloud_data_columns = list(CostCloud.cost_cloud_data_columns) + \
                                            CostCloud.cost_cloud_cost_columns + \
                                            CostCloud.cost_cloud_generated_columns

        return template_errors

    @staticmethod
    def get_cloud(vehicle):
        """
        Retrieve cost cloud for the given vehicle.

        Args:
            vehicle (Vehicle): the vehicle to get the cloud for

        Returns:
            Copy of the requested cost cloud data.

        """

        # print(vehicle.name)

        sweep_precision = 10

        vehicle_rlhp20 = \
            ASTM_round(calc_roadload_hp(vehicle.base_year_target_coef_a, vehicle.base_year_target_coef_b,
                             vehicle.base_year_target_coef_c, 20), sweep_precision)

        if 'BEV of' in vehicle.name:
            rlhp60_scaler = omega_globals.options.bev_of_ice_rlhp60_scaler
        else:
            rlhp60_scaler = 1.0

        vehicle_rlhp60 = rlhp60_scaler * \
            ASTM_round(calc_roadload_hp(vehicle.base_year_target_coef_a, vehicle.base_year_target_coef_b,
                             vehicle.base_year_target_coef_c, 60), sweep_precision)

        rse_group_key = CostCloud.get_rse_group_key(vehicle)

        if is_up_for_redesign(vehicle):
            # sweep vehicle params
            rlhp20s = np.unique((ASTM_round(vehicle_rlhp20 * omega_globals.options.rlhp20_min_scaler, sweep_precision),
                                 vehicle_rlhp20,
                                 ASTM_round(vehicle_rlhp20 * omega_globals.options.rlhp20_max_scaler, sweep_precision)))

            rlhp60s = np.unique((ASTM_round(vehicle_rlhp60 * omega_globals.options.rlhp60_min_scaler, sweep_precision),
                                 vehicle_rlhp60,
                                 ASTM_round(vehicle_rlhp60 * omega_globals.options.rlhp60_max_scaler, sweep_precision)))

            vehicle_footprints = \
                np.unique((ASTM_round(vehicle.base_year_footprint_ft2 * omega_globals.options.footprint_min_scaler, sweep_precision),
                           ASTM_round(vehicle.base_year_footprint_ft2, sweep_precision),
                           ASTM_round(vehicle.base_year_footprint_ft2 * omega_globals.options.footprint_max_scaler, sweep_precision)))

            structure_materials = MassScaling.structure_materials

            cost_curve_classes = _cache[rse_group_key]

            vehicle.prior_redesign_year = vehicle.model_year
        else:
            # maintain vehicle params
            rlhp20s = [vehicle_rlhp20]
            rlhp60s = [vehicle_rlhp60]
            vehicle_footprints = [vehicle.footprint_ft2]
            structure_materials = [vehicle.structure_material]

            cost_curve_classes = {vehicle.cost_curve_class: _cache[rse_group_key][vehicle.cost_curve_class]}

        # convergence terms init
        convergence_tolerance = 0.01
        battery_kwh = 1

        # build a list of dicts that will be dumped into the cloud at the end faster than sequentially
        # appending Series objects)
        cloud_points = []

        for ccc in cost_curve_classes:
            tech_flags = cost_curve_classes[ccc]['tech_flags'].to_dict()
            # RV
            tech_flags['ac_leakage'] = 1
            tech_flags['ac_efficiency'] = 1
            tech_flags['other_oc_menu_tech'] = 1

            # clear all tech flags
            for tf in CostCloud.tech_flags:
                vehicle.__setattr__(tf, 0)

            # set tech flags in vehicle temporarily
            for tf in tech_flags:
                vehicle.__setattr__(tf, tech_flags[tf])

            vehicle.powertrain_type = CostCloud.get_powertrain_type(tech_flags)

            if vehicle.prior_redesign_year == vehicle.model_year:
                # update charge depleting range if it's a redesign year
                if vehicle.powertrain_type == 'PHEV':
                    vehicle.onroad_charge_depleting_range_mi = omega_globals.options.phev_range_mi
                elif vehicle.powertrain_type == 'BEV':
                    if vehicle.reg_class_id == 'mediumduty' and vehicle.body_style == 'cuv_suv':
                        vehicle.onroad_charge_depleting_range_mi = omega_globals.options.bev_mdv_van_range_mi
                    else:
                        vehicle.onroad_charge_depleting_range_mi = omega_globals.options.bev_range_mi

            for structure_material in structure_materials:
                for footprint_ft2 in vehicle_footprints:
                    for rlhp20 in rlhp20s:
                        for rlhp60 in rlhp60s:
                            cloud_point = copy.copy(tech_flags)  # cost_curve_classes[ccc]['tech_flags'].to_dict()

                            cloud_point['powertrain_type'] = vehicle.powertrain_type
                            cloud_point['drive_system'] = vehicle.drive_system
                            cloud_point['application_id'] = vehicle.application_id

                            # ------------------------------------------------------------------------------------#
                            rated_hp = 1
                            prior_rated_hp = 1
                            prior_battery_kwh = 1
                            prior_powertrain_mass_lbs = 1

                            converged = False
                            while not converged:
                                # rated hp sizing --------------------------------------------------------------- #
                                structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs, \
                                 delta_glider_non_structure_mass_lbs, usable_battery_capacity_norm = \
                                    MassScaling.calc_mass_terms(vehicle, structure_material, rated_hp,
                                                                battery_kwh, footprint_ft2)

                                # update curbweight in case it's needed by DriveCycleBallast (medium-duty)
                                vehicle.curbweight_lbs = sum((vehicle.base_year_glider_non_structure_mass_lbs,
                                                             delta_glider_non_structure_mass_lbs,
                                                             powertrain_mass_lbs, structure_mass_lbs, battery_mass_lbs))

                                # vehicle ballast is f(curbweight_lbs) for medium-duty:
                                vehicle_ballast = DriveCycleBallast.get_ballast_lbs(vehicle)

                                rated_hp = min(1000, vehicle.curbweight_lbs / vehicle.base_year_curbweight_lbs_to_hp)

                                # set up RSE terms and run RSEs
                                ETW = vehicle.curbweight_lbs + vehicle_ballast

                                RLHP20 = rlhp20 / ETW
                                RLHP60 = rlhp60 / ETW
                                HP_ETW = rated_hp / ETW

                                cloud_point.update(zip(_cache[rse_group_key][ccc]['rse_names'],
                                                       Eval.eval(_cache[rse_group_key][ccc]['rse_tuple'], {},
                                                                 {'ETW': ETW, 'RLHP20': RLHP20, 'RLHP60': RLHP60,
                                                                  'HP_ETW': HP_ETW})))

                                # battery sizing -------------------------------------------------------------------- #
                                if vehicle.powertrain_type == 'BEV' or vehicle.powertrain_type == 'PHEV':
                                    cloud_point['battery_kwh'] = battery_kwh
                                    cloud_point['usable_battery_capacity_norm'] = usable_battery_capacity_norm

                                    cloud_point = vehicle.calc_battery_sizing_onroad_direct_kWh_per_mile(cloud_point)

                                    if vehicle.powertrain_type == 'PHEV' and \
                                            (omega_globals.options.phev_battery_kwh == 'RSE' or
                                             cloud_point['battery_sizing_onroad_direct_kwh_per_mile'] == 0):
                                        # use nominal size from RSE
                                        battery_kwh = cloud_point['hev_batt_kwh']
                                    elif vehicle.powertrain_type == 'PHEV' and \
                                            omega_globals.options.phev_battery_kwh is not None:
                                        # override battery size by kWh
                                        battery_kwh = omega_globals.options.phev_battery_kwh
                                    else:
                                        # BEVs and range-sized PHEVs
                                        battery_kwh = vehicle.onroad_charge_depleting_range_mi * \
                                                      cloud_point['battery_sizing_onroad_direct_kwh_per_mile'] / \
                                                      usable_battery_capacity_norm

                                # determine convergence ------------------------------------------------------------- #
                                converged = abs(
                                    1 - powertrain_mass_lbs / prior_powertrain_mass_lbs) <= convergence_tolerance and \
                                            abs(1 - rated_hp / prior_rated_hp) <= convergence_tolerance

                                if vehicle.powertrain_type == 'BEV' or vehicle.powertrain_type == 'PHEV':
                                    converged = converged and \
                                            abs(1 - battery_kwh / prior_battery_kwh) < convergence_tolerance

                                prior_powertrain_mass_lbs = powertrain_mass_lbs
                                prior_rated_hp = rated_hp
                                prior_battery_kwh = battery_kwh

                                # ------------------------------------------------------------------------------------#

                            # update battery and motor data prior to calc_cert_values (for PHEV, primarily)
                            if vehicle.powertrain_type != 'BEV' and vehicle.powertrain_type != 'PHEV':
                                # battery size and total motor/generator power come from RSEs for ICE/HEV
                                cloud_point['battery_kwh'] = cloud_point['hev_batt_kwh']
                                cloud_point['total_emachine_kw'] = cloud_point['hev_motor_kw']
                                cloud_point['tractive_motor_kw'] = 0
                            elif vehicle.powertrain_type == 'PHEV':
                                # PHEV battery size and motor power determined by vehicle and iterative range calculation
                                cloud_point['battery_kwh'] = battery_kwh
                                cloud_point['total_emachine_kw'] = cloud_point['hev_motor_kw']
                                cloud_point['tractive_motor_kw'] = 0
                            else:
                                # BEV battery size and motor power determined by vehicle and iterative range calculation
                                cloud_point['battery_kwh'] = battery_kwh
                                cloud_point['total_emachine_kw'] = rated_hp * 0.746
                                cloud_point['tractive_motor_kw'] = \
                                    cloud_point['total_emachine_kw'] * vehicle.base_year_tractive_motor_kw / \
                                    vehicle.base_year_total_emachine_kw

                            cloud_point = vehicle.calc_cert_and_onroad_values(cloud_point)

                            if rlhp20 == vehicle_rlhp20 and \
                                    rlhp60 == vehicle_rlhp60 and \
                                    footprint_ft2 == ASTM_round(vehicle.base_year_footprint_ft2, sweep_precision) and \
                                    structure_material == vehicle.structure_material and \
                                    ccc == vehicle.cost_curve_class and vehicle.fueling_class != 'BEV':
                                vehicle.onroad_direct_oncycle_co2e_grams_per_mile = \
                                    cloud_point['onroad_direct_oncycle_co2e_grams_per_mile']
                                if vehicle.model_year == omega_globals.options.analysis_initial_year:
                                    vehicle.base_year_cert_direct_oncycle_co2e_grams_per_mile = \
                                        cloud_point['cert_direct_oncycle_co2e_grams_per_mile']
                                    vehicle.base_year_onroad_direct_oncycle_co2e_grams_per_mile = \
                                        cloud_point['onroad_direct_oncycle_co2e_grams_per_mile']

                            elif rlhp20 == vehicle_rlhp20 and \
                                    rlhp60 == vehicle_rlhp60 and \
                                    footprint_ft2 == ASTM_round(vehicle.base_year_footprint_ft2, sweep_precision) and \
                                    structure_material == vehicle.structure_material and \
                                    ccc == vehicle.cost_curve_class and vehicle.fueling_class == 'BEV':
                                vehicle.onroad_direct_oncycle_kwh_per_mile = \
                                    cloud_point['onroad_direct_oncycle_kwh_per_mile']
                                if vehicle.model_year == omega_globals.options.analysis_initial_year:
                                    vehicle.base_year_cert_direct_oncycle_kwh_per_mile = \
                                        cloud_point['cert_direct_oncycle_kwh_per_mile']
                                    vehicle.base_year_onroad_direct_oncycle_kwh_per_mile = \
                                        cloud_point['onroad_direct_oncycle_kwh_per_mile']

                            v = copy.copy(vehicle)
                            v.footprint_ft2 = footprint_ft2
                            cloud_point['target_co2e_Mg_per_vehicle'] = \
                                omega_globals.options.VehicleTargets.calc_target_co2e_Mg(v, sales_variants=1)

                            cloud_point['cert_co2e_Mg_per_vehicle'] = \
                                omega_globals.options.VehicleTargets.\
                                    calc_cert_co2e_Mg(v, co2_gpmi_variants=cloud_point['cert_co2e_grams_per_mile'],
                                                      sales_variants=1)

                            cloud_point['credits_co2e_Mg_per_vehicle'] = \
                                cloud_point['target_co2e_Mg_per_vehicle'] - cloud_point['cert_co2e_Mg_per_vehicle']

                            # required cloud data for powertrain costing, etc:
                            cloud_point['cost_curve_class'] = ccc
                            cloud_point['structure_mass_lbs'] = structure_mass_lbs
                            cloud_point['footprint_ft2'] = footprint_ft2
                            cloud_point['structure_material'] = structure_material
                            cloud_point['curbweight_lbs'] = vehicle.curbweight_lbs
                            cloud_point['etw_lbs'] = ETW
                            cloud_point['rated_hp'] = rated_hp
                            cloud_point['battery_mass_lbs'] = battery_mass_lbs
                            cloud_point['powertrain_mass_lbs'] = powertrain_mass_lbs
                            cloud_point['delta_glider_non_structure_mass_lbs'] = \
                                delta_glider_non_structure_mass_lbs
                            cloud_point['glider_non_structure_mass_lbs'] = \
                                vehicle.base_year_glider_non_structure_mass_lbs + \
                                delta_glider_non_structure_mass_lbs

                            # informative data for troubleshooting:
                            if omega_globals.options.log_vehicle_cloud_years == 'all' or \
                                    vehicle.model_year in omega_globals.options.log_vehicle_cloud_years or \
                                    vehicle.base_year_vehicle_id == omega_globals.options.canary_byvid:
                                cloud_point['vehicle_id'] = vehicle.vehicle_id
                                cloud_point['vehicle_base_year_id'] = vehicle.base_year_vehicle_id
                                cloud_point['vehicle_name'] = vehicle.name
                                cloud_point['model_year'] = vehicle.model_year
                                cloud_point['vehicle_base_year_eng_rated_hp'] = vehicle.base_year_eng_rated_hp
                                cloud_point['vehicle_mot_rated_kw'] = vehicle.total_emachine_kw
                                cloud_point['rlhp20'] = rlhp20
                                cloud_point['rlhp60'] = rlhp60
                                cloud_point['hp_etw'] = HP_ETW

                            # add powertrain costs
                            powertrain_costs = \
                                omega_globals.options.PowertrainCost.calc_cost(vehicle, cloud_point['powertrain_type'],
                                                         cloud_point)  # includes battery cost

                            powertrain_cost_terms = ['engine_cost', 'driveline_cost', 'emachine_cost', 'battery_cost',
                                                     'electrified_driveline_cost']

                            for idx, ct in enumerate(powertrain_cost_terms):
                                cloud_point[ct] = powertrain_costs[idx]

                            cloud_points.append(cloud_point)

        cost_cloud = pd.DataFrame(cloud_points)

        if len(cost_cloud) > 1:
            if omega_globals.options.no_backsliding and vehicle.fueling_class != 'BEV' and \
                    vehicle.cost_curve_class is not None:
                cost_cloud = cost_cloud[cost_cloud['onroad_direct_oncycle_co2e_grams_per_mile'] <=
                                        vehicle.onroad_direct_oncycle_co2e_grams_per_mile]
            elif omega_globals.options.no_backsliding and vehicle.fueling_class == 'BEV' and \
                    vehicle.cost_curve_class is not None:
                cost_cloud = cost_cloud[cost_cloud['onroad_direct_oncycle_kwh_per_mile'] <=
                                        vehicle.onroad_direct_oncycle_kwh_per_mile]
        glider_costs = \
            GliderCost.calc_cost(vehicle, cost_cloud)  # includes structure_cost and glider_non_structure_cost

        glider_cost_terms = ['structure_cost', 'glider_non_structure_cost']
        for idx, ct in enumerate(glider_cost_terms):
            cost_cloud[ct] = glider_costs[idx]

        cost_terms = powertrain_cost_terms + glider_cost_terms

        cost_cloud['new_vehicle_mfr_cost_dollars'] = cost_cloud[cost_terms].sum(axis=1)

        powertrain_cost_terms.remove('battery_cost')
        cost_cloud['powertrain_cost'] = cost_cloud[powertrain_cost_terms].sum(axis=1)

        # calculate producer generalized cost
        cost_cloud = omega_globals.options.ProducerGeneralizedCost.\
            calc_generalized_cost(vehicle, cost_cloud, 'onroad_direct_co2e_grams_per_mile',
                                  'onroad_direct_kwh_per_mile', 'new_vehicle_mfr_cost_dollars')

        if omega_globals.options.log_vehicle_cloud_years == 'all' or \
                vehicle.model_year in omega_globals.options.log_vehicle_cloud_years:
            with open(omega_globals.options.output_folder + '%d_cost_clouds_%s_%s.csv' %
                      (vehicle.model_year, vehicle.compliance_id, vehicle.base_year_powertrain_type), 'a') as f:
                cost_cloud.to_csv(f, mode='a', header=not f.tell(), columns=sorted(cost_cloud.columns), index=False)

        # clear all tech flags
        for tf in CostCloud.tech_flags:
            vehicle.__setattr__(tf, 0)

        return cost_cloud

    @staticmethod
    def get_rse_group_key(vehicle):
        """
        Get RSE group key for the given vehicle

        Args:
            vehicle (Vehicle): the vehicle

        Returns:
            The RSE group key

        """
        if vehicle.fueling_class == 'BEV':
            # ** no application ids for BEV yet, one size fits all **
            rse_group_key = '%s_%s_%s' % (vehicle.fueling_class, vehicle.cert_fuel_id, vehicle.drive_system)
        else:
            rse_group_key = '%s_%s_%s_%s' % \
                            (vehicle.fueling_class, vehicle.cert_fuel_id, vehicle.application_id, vehicle.drive_system)

        return rse_group_key

    @staticmethod
    def get_tech_flags(vehicle):
        """
        Get tech flags associated with the vehicle cost curve class

        Args:
            vehicle (Vehicle): the vehicle

        Returns:
            Pandas Series of tech flags and values associated with the vehicle cost curve class

        """
        rse_group_key = CostCloud.get_rse_group_key(vehicle)

        try:
            tech_flags = _cache[rse_group_key][vehicle.cost_curve_class]['tech_flags'].to_dict()
        except:
            raise Exception('Unknown cost curve class "%s" in RSE group "%s"' % (vehicle.cost_curve_class, rse_group_key))

        return tech_flags

    @staticmethod
    def get_powertrain_type(tech_flags):
        """
        Determine powertrain type based on tech flags

        Args:
            tech_flags (dict-like):  tech flags and values

        Returns:
            Powertrain type based on tech flags

        """

        if 'bev' in tech_flags and tech_flags['bev']:
            powertrain_type = 'BEV'
        elif ('hev' in tech_flags and tech_flags['hev']) or ('mhev' in tech_flags and tech_flags['mhev']):  # mhev/hev have same mass calcs for now
            powertrain_type = 'HEV'
        elif 'phev' in tech_flags and tech_flags['phev']:
            powertrain_type = 'PHEV'
        # elif 'fcv' in tech_flags and tech_flags['fcv']:
        #     powertrain_type = 'FCV'
        else:
            powertrain_type = 'ICE'

        return powertrain_type


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
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)            
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
