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

The data represents base-year (and eventually 'historic') vehicle attributes and sales.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,vehicles,input_template_version:,0.43

Sample Data Columns
    .. csv-table::
        :widths: auto

        vehicle_name,manufacturer_id,model_year,reg_class_id,context_size_class,electrification_class,cost_curve_class,in_use_fuel_id,cert_fuel_id,sales,cert_direct_oncycle_co2e_grams_per_mile,cert_direct_oncycle_kwh_per_mile,footprint_ft2,eng_rated_hp,tot_road_load_hp,etw_lbs,length_in,width_in,height_in,ground_clearance_in,wheelbase_in,interior_volume_cuft,msrp_dollars,passenger_capacity,payload_capacity_lbs,towing_capacity_lbs,unibody_structure,body_style,structure_material,drive_system,gvwr_lbs,gcwr_lbs,curbweight_lbs,eng_cyls_num,eng_disp_liters,high_eff_alternator,start_stop,hev,phev,bev,deac_pd,deac_fc,cegr,atk2,gdi,turb12,turb11,gas_fuel,diesel_fuel,target_coef_a,target_coef_b,target_coef_c
        COOPER HARDTOP 2 DOOR,BMX,2019,car,Subcompact,N,,{'pump gasoline':1.0},{'gasoline':1.0},4459,,,40,134,10.7,3000,153.5,,55.8,5.1,99.2,,23900,4.3,775,,0,sedan,steel,2,3680,,2743,3,1.5,0,0,0,0,0,0,0,0,0,1,1,0,1,0,27.6,0.156,0.01806
        Panamera 4 e-Hybrid,VGA,2019,car,Large,PHEV,,{'pump gasoline':1.0},{'gasoline':1.0},458,,,52.7,330,15.8,5500,200.8,,56.1,,118.1,,107783,4.3,,,0,sedan,steel,4,5860,,4547,6,2.9,0,1,0,1,0,0,0,0,0,1,1,0,1,0,51.706,0.39797,0.01863

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

    :cert_direct_oncycle_co2e_grams_per_mile:
        Vehicle direct oncycle emissions CO2e grams/mile

    :cert_direct_oncycle_kwh_per_mile:
        Vehicle direct oncycle electricity consumption kWh/mile

    :footprint_ft2:
        Vehicle footprint based on vehicle wheelbase and track (square feet)

    :eng_rated_hp:
        Vehicle engine rated power (horsepower)

    :tot_road_load_hp:
        Vehicle roadload power (horsepower) at a vehicle speed of 50 miles per hour

    :etw_lbs:
        Vehicle equivalent test weight (ETW) (pounds)

    :msrp_dollars:
        Vehicle manufacturer suggested retail price (MSRP)

    :unibody_structure:
        Vehicle body structure; 1 = unibody, 0 = body-on-frame

    :body_style:
        Vehicle body style; sedan, cuv_suv, pickup

    :structure_material:
        Primary material of the body structure; steel, aluminum

    :curbweight_lbs:
        Vehicle curb weight (pounds)

    :eng_cyls_num:
        Number of engine cylinders

    :eng_disp_liters:
        Engine displacement (liters)

    :high_eff_alternator:
        Technology flag for high efficiency alternator (1 = Equipped, 0 = Not equipped)

    :start_stop:
        Technology flag for engine start-stop system (1 = Equipped, 0 = Not equipped)

    :hev:
        Technology flag for non plug-in hybrid system (1 = Equipped, 0 = Not equipped)

    :phev:
        Technology flag for plug-in hybrid system (1 = Equipped, 0 = Not equipped)

    :bev:
        Technology flag for battery electric vehicle (1 = Equipped, 0 = Not equipped)

    :deac_pd:
        Technology flag for cylinder deactivation, discrete operation of partial number of cylinders (1 = Equipped, 0 = Not equipped)

    :deac_fc:
        Technology flag for cylinder deactivation, continuosly variable operation of full number of cylinders (1 = Equipped, 0 = Not equipped)

    :deac_fc:
        Technology flag for cooled exhaust gas recirculation (1 = Equipped, 0 = Not equipped)

    :atk2:
        Technology flag for high geometric compression ratio Atkinson cycle engine (1 = Equipped, 0 = Not equipped)

    :gdi:
        Technology flag for gasoline direct injection system (1 = Equipped, 0 = Not equipped)

    :turb12:
        Technology turbocharged engine, 18-21bar 2nd generation (1 = Equipped, 0 = Not equipped)

    :turb11:
        Technology turbocharged engine, 18-21bar 1st generation (1 = Equipped, 0 = Not equipped)

    :gas_fuel
        Technology gasoline-fueled engines (1 = Equipped, 0 = Not equipped)

    :diesel_fuel
        Technology diesel-fueled engines (1 = Equipped, 0 = Not equipped)

    :target_coef_a:
       Coast down target A coeffient (lbf)

    :target_coef_b:
       Coast down target B coeffient (lbf/mph)

    :target_coef_c:
       Coast down target C coeffient (lbf/mph**2)

    **OPTIONAL COLUMNS**
        These columns become object attributes that may be used to determine vehicle regulatory class
        (e.g. 'car','truck') based on the simulated policy, or they may be used for other purposes.

    :cert_co2e_grams_per_mile:
        Vehicle certification emissions CO2e grams/mile

    :cert_direct_kwh_per_mile:
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

    :gvwr_lbs:
       Gross Vehicle Weight Rating (pounds)

    :gcwr_lbs:
       Gross Combined Weight Rating (pounds)

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
        template_errors = []

        # DecompositionAttributes.init()   # offcycle_credits must be initalized first

        from producer.vehicles import Vehicle, VehicleFinal
        from context.new_vehicle_market import NewVehicleMarket
        from context.glider_cost import GliderCost
        from context.powertrain_cost import PowertrainCost
        from policy.workfactor_definition import WorkFactor

        omega_log.logwrite('\nAggregating vehicles from %s...' % filename)

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
                               'drive_system': [2, 4],  # for now, anyway... 1,2,3??
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
            df['ground_clearance_in'] = df['ground_clearance_in'].fillna(6.6) # dummy value, sales-weighted

            df['height_in'] = df['height_in'].fillna(62.4)  # dummy value, sales-weighted

            df['base_year_powertrain_type'] = df['electrification_class'].\
                replace({'N': 'ICE', 'EV': 'BEV', 'HEV': 'HEV', 'PHEV': 'PHEV', 'FCV': 'FCV'})

            # TODO: FCV battery size = 2?? Mirai=1.8
            df['battery_kwh'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 1, 'PHEV': 18, 'BEV': 60, 'FCV': 60, 'ICE': 0}})

            df['motor_kw'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 20,
                                             'PHEV': 50,
                                             'BEV': 150 + (100 * (df['drive_system'] == 4)),
                                             'FCV': 150 + (100 * (df['drive_system'] == 4)),
                                             'ICE': 0}})

            # TODO: FCV range = 0??
            df['charge_depleting_range_mi'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 0, 'PHEV': 50, 'BEV': 300, 'FCV': 300, 'ICE': 0}})

            # need to determine vehicle trans / techs
            df['engine_cylinders'] = df['eng_cyls_num']  # MIGHT NEED TO RENAME THESE, ONE PLACE OR ANOTHER
            df['engine_displacement_L'] = df['eng_disp_liters']  # MIGHT NEED TO RENAME THESE, ONE PLACE OR ANOTHER

            import time
            start_time = time.time()
            print('starting iterrows')

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
                    veh.base_year_powertrain_type = 'BEV'  # TODO: for costing purposes, for now

                veh.base_year_reg_class_id = row['reg_class_id']
                veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                row['market_class_id'] = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                veh.drive_system = row['drive_system']

                powertrain_cost = sum(PowertrainCost.calc_cost(veh, row, veh.base_year_powertrain_type))

                # powertrain_costs = PowertrainCost.calc_cost(veh, pd.DataFrame([row]))  # includes battery cost
                # powertrain_cost_terms = ['engine_cost', 'driveline_cost', 'emachine_cost', 'battery_cost',
                #                          'electrified_driveline_cost']
                # for i, ct in enumerate(powertrain_cost_terms):
                #     df.loc[idx, ct] = float(powertrain_costs[i])

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
                        = row['model_year'], row['curbweight_lbs'], row['gvwr_lbs'], row['gcwr_lbs'], row['drive_system']
                    workfactor = WorkFactor.calc_workfactor(model_year, curbweight_lbs, gvwr_lbs, gcwr_lbs, drive_system)
                df.at[idx, 'workfactor'] = workfactor
                veh.gvwr_lbs = row['gvwr_lbs']
                veh.gcwr_lbs = row['gcwr_lbs']
                veh.base_year_gvwr_lbs = row['gvwr_lbs']
                veh.base_year_gcwr_lbs = row['gcwr_lbs']

                # glider_costs = GliderCost.calc_cost(veh, pd.DataFrame([row]))  # includes structure_cost and glider_non_structure_cost
                # glider_cost_terms = ['structure_cost', 'glider_non_structure_cost']
                # for i, ct in enumerate(glider_cost_terms):
                #     df.loc[idx, ct] = [gc[i] for gc in glider_costs]

            df['glider_non_structure_mass_lbs'] = df['curbweight_lbs'] - df['powertrain_mass_lbs'] \
                                                  - df['structure_mass_lbs'] - df['battery_mass_lbs']

            print('done %.2f' % (time.time() - start_time))

            df.to_csv(omega_globals.options.output_folder + 'costed_vehicles.csv')

            # calculate weighted numeric values within the groups, and combined string values
            agg_df = df.groupby(aggregation_columns, as_index=False).apply(sales_weight_average_dataframe)
            agg_df['vehicle_name'] = agg_df[aggregation_columns].apply(lambda x: ':'.join(x.values.astype(str)), axis=1)

            if omega_globals.options.consolidate_manufacturers:
                agg_df['compliance_id'] = 'consolidated_OEM'
            else:
                agg_df['compliance_id'] = agg_df['manufacturer_id']

            agg_df.to_csv(omega_globals.options.output_folder + 'aggregated_vehicles.csv')

            agg_df['rated_hp'] = agg_df['eng_rated_hp']  # TODO: we need to figure out this 'engine' rated hp biz

            omega_globals.options.vehicles_df = agg_df

            omega_globals.options.SalesShare.calc_base_year_data(omega_globals.options.vehicles_df)

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib
        from omega import init_user_definable_submodules

        omega_globals.options = OMEGASessionSettings()

        init_fail = []
        init_fail += init_user_definable_submodules()

        # set up global variables:
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

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
