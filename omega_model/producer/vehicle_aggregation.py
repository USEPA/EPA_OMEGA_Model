"""

**Routines to load base-year vehicle data, data structures to represent vehicles during compliance modeling
(transient or ephemeral vehicles), finalized vehicles (manufacturer-produced compliance vehicles), and composite
vehicles (used to group vehicles by various characteristics during compliance modeling).**

Classes are also implemented to handle composition and decomposition of vehicle attributes as part of the composite
vehicle workflow.  Some vehicle attributes are known and fixed in advance, others are created at runtime (e.g. off-cycle
credit attributes which may vary by policy).

**INPUT FILE FORMAT (Vehicles File)**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents base-year vehicle attributes and sales.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,vehicles,input_template_version:,0.49,notes:,20220926 Added fields for prior_redesign_year and redesign_interval to 20220819 ver from base_year_compilation_LD_2b3_20220926.xlsx

Sample Data Columns
    .. csv-table::
        :widths: auto

        vehicle_name,manufacturer_id,model_year,reg_class_id,context_size_class,electrification_class,cost_curve_class,in_use_fuel_id,cert_fuel_id,sales,cert_direct_oncycle_co2e_grams_per_mile,cert_direct_oncycle_kwh_per_mile,footprint_ft2,eng_rated_hp,tot_road_load_hp,etw_lbs,length_in,width_in,height_in,ground_clearance_in,wheelbase_in,interior_volume_cuft,msrp_dollars,passenger_capacity,payload_capacity_lbs,towing_capacity_lbs,unibody_structure,body_style,structure_material,prior_redesign_year,redesign_interval,drive_system,alvw_lbs,gvwr_lbs,gcwr_lbs,curbweight_lbs,dual_rear_wheel,long_bed_8ft,eng_cyls_num,eng_disp_liters,high_eff_alternator,start_stop,ice,hev,phev,bev,fcv,deac_pd,deac_fc,cegr,atk2,gdi,turb12,turb11,gas_fuel,diesel_fuel,awd,fwd,trx10,trx11,trx12,trx21,trx22,ecvt,target_coef_a,target_coef_b,target_coef_c
        DB11 V12,Aston Martin Lagonda,2019,car,Minicompact,N,TDS_TRX22_SS0,{'pump gasoline':1.0},{'gasoline':1.0},118,,,50,600,14.6,4500,186,77.26666667,50.53333333,3.5,110.4,81,311230,4,,,1,sedan,steel,2014,5,2,,,,3933,0,,12,5.2,0,0,1,0,0,0,0,1,0,0,0,0,1,0,1,0,,,,,,,,,40.94,0.0169,0.0271
        Grand Cherokee 4X4,FCA,2019,truck,Large Crossover,N,GDI_TRX22_SS1,{'pump gasoline':1.0},{'gasoline':1.0},155936,,,51.1,295,17.2,5000,189.8,76.5,68.82,8.6,114.71,140.5,43538.5,5,,,1,cuv_suv,steel,2014,5,4,5662.35,6500,,4824.7,0,,6,3.6,0,1,1,0,0,0,0,0,0,1,0,0,0,0,1,0,,,,,,,,,51.46511874,-0.260687329,0.036235437

Data Column Name and Description

    **REQUIRED COLUMNS**

    :vehicle_name:
        The vehicle name or description, e.g. 'ICE Small Utility truck', 'BEV Subcompact car', etc

    :manufacturer_id:
        Manufacturer name, must be consistent with the data loaded by ``class manufacturers.Manufacturer``

    :model_year:
        The model year of the vehicle data, e.g. 2020

    :reg_class_id:
        Vehicle regulatory class at the time of certification, e.g. 'car','truck'.  Reg class definitions may differ
        across years within the simulation based on policy changes. ``reg_class_id`` can be considered a 'historical'
        or 'legacy' reg class.

    :context_size_class:
        The context size class of the vehicle, for future sales mix projections.  Must be consistent with the context
        input file loaded by ``class context_new_vehicle_market.ContextNewVehicleMarket``

    :electrification_class:
        The electrification class of the vehicle, such as 'EV', 'HEV', (or 'N' for none - final format TBD)

    :cost_curve_class:
        The name of the cost curve class of the vehicle, used to determine which technology options and associated costs
        are available to be applied to this vehicle.  Must be consistent with the data loaded by
        ``class cost_clouds.CostCloud``

    :in_use_fuel_id:
        In-use fuel id, for use with context fuel prices, must be consistent with the context data read by
        ``class context_fuel_prices.ContextFuelPrices``

    :cert_fuel_id:
        Certification fuel id, for determining certification upstream CO2e grams/mile, must be in the table loaded by
        ``class fuels.Fuel``

    :sales:
        Number of vehicles sold in the ``model_year``

    :footprint_ft2:
        Vehicle footprint based on vehicle wheelbase and track (square feet)

    :eng_rated_hp:
        Vehicle engine rated power (horsepower)

    :unibody_structure:
        Vehicle body structure; 1 = unibody, 0 = body-on-frame

    :drive_system:
        Vehicle drive system, 2=FWD/RWD, 4=AWD

    :dual_rear_wheel:
        = 1 if vehicle has dual rear wheels, i.e. 'duallies', = 0 otherwise

    :curbweight_lbs:
        Vehicle curb weight (pounds)

    :gvwr_lbs:
       Gross Vehicle Weight Rating (pounds)

    :gcwr_lbs:
       Gross Combined Weight Rating (pounds)

    :target_coef_a:
       Coast down target A coefficient (lbf)

    :target_coef_b:
       Coast down target B coefficient (lbf/mph)

    :target_coef_c:
       Coast down target C coefficient (lbf/mph**2)

    :body_style:
        Vehicle body style; sedan, cuv_suv, pickup

    :msrp_dollars:
        Vehicle manufacturer suggested retail price (MSRP)

    :structure_material:
        Primary material of the body structure; steel, aluminum

    :prior_redesign_year:
        The vehicle's prior redesign year

    :redesign_interval:
        The vehicle's redesign interval, in years

    :eng_cyls_num:
        Number of engine cylinders

    :eng_disp_liters:
        Engine displacement (liters)

    :high_eff_alternator:
        Technology flag for high efficiency alternator (1 = Equipped, 0 = Not equipped)

    :start_stop:
        Technology flag for engine start-stop system (1 = Equipped, 0 = Not equipped)

    :ice:
        Technology flag for internal combustion engine (1 = Equipped, 0 = Not equipped)

    :hev:
        Technology flag for non plug-in hybrid system (1 = Equipped, 0 = Not equipped)

    :phev:
        Technology flag for plug-in hybrid system (1 = Equipped, 0 = Not equipped)

    :bev:
        Technology flag for battery electric vehicle (1 = Equipped, 0 = Not equipped)

    :deac_pd:
        Technology flag for cylinder deactivation, discrete operation of partial number of cylinders
        (1 = Equipped, 0 = Not equipped)

    :deac_fc:
        Technology flag for cylinder deactivation, continuosly variable operation of full number of cylinders
        (1 = Equipped, 0 = Not equipped)

    :cegr:
        Technology flag for cooled exhaust gas recirculation (1 = Equipped, 0 = Not equipped)

    :atk2:
        Technology flag for high geometric compression ratio Atkinson cycle engine (1 = Equipped, 0 = Not equipped)

    :gdi:
        Technology flag for gasoline direct injection system (1 = Equipped, 0 = Not equipped)

    :turb12:
        Technology flag for turbocharged engine, 18-21bar 2nd generation (1 = Equipped, 0 = Not equipped)

    :turb11:
        Technology flag for turbocharged engine, 18-21bar 1st generation (1 = Equipped, 0 = Not equipped)

    :gas_fuel:
        Technology flag for gasoline-fueled engine (1 = Equipped, 0 = Not equipped)

    :diesel_fuel:
        Technology flag for diesel-fueled engine (1 = Equipped, 0 = Not equipped)

    :awd:
        Technology flag for all-wheel drive (1 = Equipped, 0 = Not equipped)

    :fwd:
        Technology flag for front-wheel drive (1 = Equipped, 0 = Not equipped)

    :trx10:
        Technology flag for a baseline transmission (1 = Equipped, 0 = Not equipped)

    :trx11:
        Technology flag for an improved transmission (1 = Equipped, 0 = Not equipped)

    :trx12:
        Technology flag for an advanced transmission (1 = Equipped, 0 = Not equipped)

    :trx21:
        Technology flag for a high gear count transmission or equivalent (1 = Equipped, 0 = Not equipped)

    :trx22:
        Technology flag for an advanced high gear count transmission or equivalent (1 = Equipped, 0 = Not equipped)

    :ecvt:
        Technology flag for a powersplit-type hybrid vehicle transmission (1 = Equipped, 0 = Not equipped)

    **OPTIONAL COLUMNS**
        These columns become object attributes that may be used to determine vehicle regulatory class
        (e.g. 'car','truck') based on the simulated policy, or they may be used for other purposes.

    :tot_road_load_hp:
        Vehicle roadload power (horsepower) at a vehicle speed of 50 miles per hour

    :etw_lbs:
        Vehicle equivalent test weight (ETW) (pounds)

    :cert_direct_oncycle_co2e_grams_per_mile:
        Vehicle certification emissions CO2e grams/mile

    :cert_direct_oncycle_kwh_per_mile:
        Vehicle certification electricity consumption kWh/mile

    :length_in:
        Vehicle overall length (inches)

    :width_in:
        Vehicle overall width (inches)

    :height_in:
        Vehicle overall height (inches)

    :ground_clearance_in:
        Vehicle ground clearance (inches)

    :wheelbase_in:
        Vehicle wheelbase (inches)

    :interior_volume_cuft:
        Vehicle interior volume (cubic feet)

    :passenger_capacity:
        Vehicle passenger capacity (number of occupants)

    :payload_capacity_lbs:
        Vehicle payload capacity (pounds)

    :towing_capacity_lbs:
        Vehicle towing capacity (pounds)

    :alvw_lbs:
        Average loaded vehicle weight (pounds)

----

**CODE**

"""
import pandas as pd

print('importing %s' % __file__)

from omega_model import *

# for now, eventually need to be inputs somewhere:
# 'manufacturer_id' added if not consolidating manufacturers
aggregation_columns = ['context_size_class', 'body_style', 'base_year_powertrain_type', 'unibody_structure',
                       'cert_fuel_id', 'reg_class_id', 'drive_system', 'dual_rear_wheel', 'model_year',
                       'prior_redesign_year', 'redesign_interval', 'cost_curve_class', 'structure_material']


class VehicleAggregation(OMEGABase):
    """
    **Implements aggregation of detailed vehicle data into compliance vehicles.**

    """
    next_vehicle_id = 0

    def __init__(self):
        pass

    @staticmethod
    def init_from_file(filename, verbose=False):
        """
        Validate and read detailed vehicles.csv file

        Args:
            filename (str): the name of the base year vehicles file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        # See Also:
        #     ``DecompositionAttributes``

        """
        from producer.vehicles import Vehicle, VehicleFinal
        from context.new_vehicle_market import NewVehicleMarket
        from context.glider_cost import GliderCost
        from context.powertrain_cost import PowertrainCost
        from policy.workfactor_definition import WorkFactor

        # omega_log.logwrite('\nAggregating vehicles from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.49
        input_template_columns = VehicleFinal.mandatory_input_template_columns

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            from producer.manufacturers import Manufacturer
            from context.mass_scaling import MassScaling
            from context.body_styles import BodyStyles

            validation_dict = {'manufacturer_id': Manufacturer.manufacturers,
                               'reg_class_id': list(legacy_reg_classes),
                               'context_size_class': NewVehicleMarket.context_size_classes,
                               'electrification_class': ['N', 'EV', 'HEV', 'PHEV', 'FCV'],
                               'unibody_structure': [0, 1],
                               'body_style': BodyStyles.body_styles,
                               'structure_material': MassScaling.structure_materials,
                               'in_use_fuel_id': ["{'pump gasoline':1.0}", "{'pump diesel':1.0}", "{'hydrogen':1.0}",
                                                  "{'US electricity':1.0}"],
                               'cert_fuel_id': ["{'gasoline':1.0}", "{'diesel':1.0}", "{'hydrogen':1.0}",
                                                "{'electricity':1.0}"],
                               'drive_system': [2, 4],  # RV
                               'dual_rear_wheel': [0, 1],
                               'high_eff_alternator': [0, 1],
                               'start_stop': [0, 1],
                               'hev': [0, 1],
                               'phev': [0, 1],
                               'bev': [0, 1],
                               'deac_pd': [0, 1],
                               'deac_fc': [0, 1],
                               'cegr': [0, 1],
                               'atk2': [0, 1],
                               'gdi': [0, 1],
                               'turb12': [0, 1],
                               'turb11': [0, 1],
                               'gas_fuel': [0, 1],
                               'diesel_fuel': [0, 1],
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:

            global aggregation_columns
            # if not omega_globals.options.consolidate_manufacturers:
            aggregation_columns += ['manufacturer_id']
            omega_globals.manufacturer_aggregation = True

            # process manufacturer include/exclude lists
            if omega_globals.options.include_manufacturers_list != 'all':
                df = df[[mid in omega_globals.options.include_manufacturers_list
                                 for mid in df['manufacturer_id']]]

            if omega_globals.options.exclude_manufacturers_list != 'none':
                df = df[[mid not in omega_globals.options.exclude_manufacturers_list
                                 for mid in df['manufacturer_id']]]

            # new columns calculated here for every vehicle in vehicles.csv:
            df['glider_non_structure_cost_dollars'] = 0
            df['glider_non_structure_mass_lbs'] = 0

            # fill in missing values
            df['ground_clearance_in'] = df['ground_clearance_in'].fillna(6.6)  # RV

            df['height_in'] = df['height_in'].fillna(62.4)  # RV

            df['base_year_powertrain_type'] = df['electrification_class'].\
                replace({'N': 'ICE', 'EV': 'BEV', 'HEV': 'HEV', 'PHEV': 'PHEV', 'FCV': 'FCV'})

            # RV
            df['battery_kwh'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 1, 'PHEV': 18, 'BEV': 60, 'FCV': 60, 'ICE': 0}})

            # RV
            df['motor_kw'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 20,
                                             'PHEV': 50,
                                             'BEV': 150 + (100 * (df['drive_system'] == 4)),
                                             'FCV': 150 + (100 * (df['drive_system'] == 4)),
                                             'ICE': 0}})

            # RV
            df['charge_depleting_range_mi'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 0, 'PHEV': 50, 'BEV': 300, 'FCV': 300, 'ICE': 0}})

            # need to determine vehicle trans / techs
            df['engine_cylinders'] = df['eng_cyls_num']  # RV
            df['engine_displacement_L'] = df['eng_disp_liters']  # RV

            import time
            start_time = time.time()
            # print('starting iterrows')

            df['base_year_footprint_ft2'] = df['footprint_ft2']

            df['base_year_curbweight_lbs'] = df['curbweight_lbs']

            df['powertrain_type'] = df['base_year_powertrain_type']  # required for mass_scaling calcs

            df['structure_mass_lbs'], df['battery_mass_lbs'], df['powertrain_mass_lbs'], \
            df['delta_glider_non_structure_mass_lbs'], df['usable_battery_capacity_norm'] = \
                MassScaling.calc_mass_terms(df, df['structure_material'], df['eng_rated_hp'],
                                            df['battery_kwh'], df['footprint_ft2'])
            df.insert(len(df.columns), 'workfactor', 0)

            if omega_globals.options.vehicles_file_base_year is not None:
                model_year_delta = omega_globals.options.vehicles_file_base_year - df['model_year']
                df['prior_redesign_year'] += model_year_delta
                df['model_year'] += model_year_delta

            for idx, row in df.iterrows():
                # calc powertrain cost
                veh = Vehicle()
                veh.model_year = row['model_year']
                veh.base_year_powertrain_type = row['base_year_powertrain_type']
                veh.body_style = row['body_style']

                if veh.base_year_powertrain_type == 'FCV':
                    veh.base_year_powertrain_type = 'BEV'  # RV

                veh.base_year_reg_class_id = row['reg_class_id']
                veh.base_year_cert_fuel_id = row['cert_fuel_id']

                veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                row['market_class_id'] = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                veh.drive_system = row['drive_system']

                veh.global_cumulative_battery_GWh = omega_globals.cumulative_battery_GWh

                powertrain_cost = sum(PowertrainCost.calc_cost(veh, row, veh.base_year_powertrain_type))

                # calc glider cost
                veh.structure_material = row['structure_material']
                veh.height_in = row['height_in']
                veh.ground_clearance_in = row['ground_clearance_in']
                veh.base_year_msrp_dollars = row['msrp_dollars']
                row['base_year_msrp_dollars'] = row['msrp_dollars']

                veh.unibody_structure = row['unibody_structure']
                veh.body_style = row['body_style']

                veh.base_year_glider_non_structure_cost_dollars = \
                    GliderCost.get_base_year_glider_non_structure_cost(veh, row['structure_mass_lbs'], powertrain_cost)

                veh.base_year_footprint_ft2 = row['footprint_ft2']

                veh.base_year_curbweight_lbs = row['curbweight_lbs']

                df.loc[idx, 'glider_non_structure_cost_dollars'] = \
                    float(GliderCost.calc_cost(veh, pd.DataFrame([row]))[1])

                workfactor = 0
                if row['reg_class_id'] == 'mediumduty':
                    model_year, curbweight_lbs, gvwr_lbs, gcwr_lbs, drive_system \
                        = row['model_year'], row['curbweight_lbs'], row['gvwr_lbs'], row['gcwr_lbs'], \
                        row['drive_system']
                    workfactor = \
                        WorkFactor.calc_workfactor(model_year, curbweight_lbs, gvwr_lbs, gcwr_lbs, drive_system)
                df.at[idx, 'workfactor'] = workfactor
                veh.gvwr_lbs = row['gvwr_lbs']
                veh.gcwr_lbs = row['gcwr_lbs']
                veh.base_year_gvwr_lbs = row['gvwr_lbs']
                veh.base_year_gcwr_lbs = row['gcwr_lbs']

            df['glider_non_structure_mass_lbs'] = df['curbweight_lbs'] - df['powertrain_mass_lbs'] \
                                                  - df['structure_mass_lbs'] - df['battery_mass_lbs']

            # print('done %.2f' % (time.time() - start_time))

            df.to_csv(omega_globals.options.output_folder + 'costed_vehicles.csv')

            # calculate weighted numeric values within the groups, and combined string values
            agg_df = df.groupby(aggregation_columns, as_index=False).apply(sales_weight_average_dataframe)
            agg_df['vehicle_name'] = agg_df[aggregation_columns].apply(lambda x: ':'.join(x.values.astype(str)), axis=1)

            if omega_globals.options.consolidate_manufacturers:
                agg_df['compliance_id'] = 'consolidated_OEM'
            else:
                agg_df['compliance_id'] = agg_df['manufacturer_id']

            agg_df.to_csv(omega_globals.options.output_folder + 'aggregated_vehicles.csv')

            agg_df['rated_hp'] = agg_df['eng_rated_hp']  # RV

            omega_globals.options.vehicles_df = agg_df

            omega_globals.options.SalesShare.calc_base_year_data(omega_globals.options.vehicles_df)

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        init_fail = []

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
