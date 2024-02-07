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

       input_template_name:,vehicles,input_template_version:,0.50,notes:,20220926 Added fields for prior_redesign_year and redesign_interval to 20220819 ver from base_year_compilation_LD_2b3_20220926.xlsx

Sample Data Columns
    .. csv-table::
        :widths: auto

        vehicle_name,manufacturer_id,model_year,reg_class_id,context_size_class,electrification_class,cost_curve_class,in_use_fuel_id,cert_fuel_id,sales,cert_direct_oncycle_co2e_grams_per_mile,cert_direct_oncycle_kwh_per_mile,footprint_ft2,eng_rated_hp,tot_road_load_hp,etw_lbs,length_in,width_in,height_in,ground_clearance_in,wheelbase_in,interior_volume_cuft,msrp_dollars,passenger_capacity,payload_capacity_lbs,towing_capacity_lbs,unibody_structure,body_style,structure_material,prior_redesign_year,redesign_interval,drive_system,alvw_lbs,gvwr_lbs,gcwr_lbs,curbweight_lbs,dual_rear_wheel,long_bed_8ft,engine_cylinders,engine_displacement_liters,high_eff_alternator,start_stop,ice,hev,phev,bev,fcv,deac_pd,deac_fc,cegr,atk2,gdi,turb12,turb11,gas_fuel,diesel_fuel,awd,fwd,trx10,trx11,trx12,trx21,trx22,ecvt,target_coef_a,target_coef_b,target_coef_c
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
        ``class policy.policy_fuels.PolicyFuel``

    :sales:
        Number of vehicles sold in the ``model_year``

    :footprint_ft2:
        Vehicle footprint based on vehicle wheelbase and track (square feet)

    :eng_rated_hp:
        Vehicle engine rated power (horsepower)

    :unibody_structure:
        Vehicle body structure; 1 = unibody, 0 = body-on-frame

    :drive_system:
        Vehicle drive system, 'FWD', 'RWD', 'AWD'

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

    :engine_cylinders:
        Number of engine cylinders

    :engine_displacement_liters:
        Engine displacement (liters)

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
                       'prior_redesign_year', 'redesign_interval', 'cost_curve_class', 'structure_material',
                       'application_id', 'cert_fuel_id']


class VehicleAggregation(OMEGABase):
    """
    **Implements aggregation of detailed vehicle data into compliance vehicles.**

    """
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
        from producer.vehicles import Vehicle
        from context.new_vehicle_market import NewVehicleMarket
        from context.glider_cost import GliderCost
        from policy.workfactor_definition import WorkFactor
        from policy.policy_fuels import PolicyFuel

        # omega_log.logwrite('\nAggregating vehicles from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.51
        input_template_columns = Vehicle.mandatory_input_template_columns

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

            omega_globals.options.CostCloud.rse_names.update(['FCV'])  # RV FCV add 'FCV' RSE name for validation purposes for now

            validation_dict = {'manufacturer_id': Manufacturer.manufacturers,
                               'reg_class_id': list(legacy_reg_classes),
                               'context_size_class': NewVehicleMarket.context_size_classes,
                               'electrification_class': ['N', 'EV', 'HEV', 'PHEV', 'FCV'],
                               'cost_curve_class': omega_globals.options.CostCloud.rse_names,
                               'unibody_structure': [0, 1],
                               'body_style': BodyStyles.body_styles,
                               'structure_material': MassScaling.structure_materials,
                               'in_use_fuel_id': ["{'pump gasoline':1.0}", "{'pump diesel':1.0}", "{'hydrogen':1.0}",
                                                  "{'US electricity':1.0}"],
                               'cert_fuel_id': PolicyFuel.fuel_ids,
                               'drive_system': ['FWD', 'RWD', 'AWD'],
                               'dual_rear_wheel': [0, 1],
                               'application_id': ['SLA', 'HLA', 'MDV']
                               }

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:

            global aggregation_columns
            # if not omega_globals.options.consolidate_manufacturers:
            if 'manufacturer_id' not in aggregation_columns:
                aggregation_columns += ['manufacturer_id']

            omega_globals.manufacturer_aggregation = True

            # potentially drop low-volume vehicles
            df = df[df['sales'] >= omega_globals.options.base_year_min_sales]

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
            VehicleAggregation.weighted_fillna(df, 'ground_clearance_in')
            VehicleAggregation.weighted_fillna(df, 'height_in')

            df['gvwr_lbs'] = df['gvwr_lbs'].fillna(df['etw_lbs'] + 700)  # RV: placeholder BDE
            df['gcwr_lbs'] = df['gcwr_lbs'].fillna(10000)  # RV: placeholder BDE
            df['curbweight_lbs'] = df['curbweight_lbs'].fillna(df['etw_lbs'] - 300)  # RV: placeholder BDE
            df['dual_rear_wheel'] = df['dual_rear_wheel'].fillna(0)  # RV: placeholder BDE
            df['alvw_lbs'] = df['alvw_lbs'].fillna((df['etw_lbs'] + df['gvwr_lbs']) / 2)  # RV: placeholder BDE

            df['base_year_powertrain_type'] = df['electrification_class'].\
                replace({'N': 'ICE', 'EV': 'BEV', 'HEV': 'HEV', 'PHEV': 'PHEV', 'FCV': 'FCV'})

            # RV FCV
            df['battery_kwh'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': df['battery_gross_kwh'], 'PHEV': df['battery_gross_kwh'],
                                                       'BEV': df['battery_gross_kwh'],
                                                       'FCV': VehicleAggregation.weighted_fillna(
                                                           df[df['electrification_class'] == 'EV'], 'battery_gross_kwh',
                                                           update_df=False),
                                                       'ICE': 0}})

            df['battery_gross_kwh'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': df['battery_gross_kwh'], 'PHEV': df['battery_gross_kwh'],
                                                       'BEV': df['battery_gross_kwh'],
                                                       'FCV': VehicleAggregation.weighted_fillna(
                                                           df[df['electrification_class'] == 'EV'], 'battery_gross_kwh',
                                                           update_df=False),
                                                       'ICE': 0}})

            # RV FCV
            df['total_emachine_kw'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 20,
                                             'PHEV': df['total_emachine_kw'],
                                             'BEV': df['total_emachine_kw'],
                                             'FCV': 150 + (50 * (df['drive_system'] != 'FWD')),
                                             'ICE': 0}})

            # RV FCV
            df['onroad_charge_depleting_range_mi'] = df[['base_year_powertrain_type']].\
                replace({'base_year_powertrain_type': {'HEV': 0, 'PHEV': df['onroad_charge_depleting_range_mi'],
                                                       'BEV': df['onroad_charge_depleting_range_mi'],
                                                       'FCV': VehicleAggregation.weighted_fillna(
                                                           df[df['electrification_class'] == 'EV'], 'onroad_charge_depleting_range_mi',
                                                           update_df=False),
                                                       'ICE': 0}})

            # import time
            # start_time = time.time()
            # print('starting iterrows')

            df['base_year_footprint_ft2'] = df['footprint_ft2']

            df['base_year_curbweight_lbs'] = df['curbweight_lbs']

            df['powertrain_type'] = df['base_year_powertrain_type']  # required for mass_scaling calcs

            (df['structure_mass_lbs'], df['battery_mass_lbs'], df['powertrain_mass_lbs'],
             df['delta_glider_non_structure_mass_lbs'], df['usable_battery_capacity_norm']) = (
                MassScaling.calc_mass_terms(df, df['structure_material'], df['eng_rated_hp'], df['battery_kwh'],
                                            df['footprint_ft2']))

            df.insert(len(df.columns), 'workfactor', 0)

            if omega_globals.options.vehicles_file_base_year_offset is not None:
                df['prior_redesign_year'] += omega_globals.options.vehicles_file_base_year_offset
                df['model_year'] += omega_globals.options.vehicles_file_base_year_offset

            for idx, row in df.iterrows():
                # calc powertrain cost
                veh = Vehicle(row['manufacturer_id'])
                veh.model_year = row['model_year']
                veh.body_style = row['body_style']
                veh.drive_system = row['drive_system']

                if row['base_year_powertrain_type'] in ['BEV', 'FCV']:
                    df.loc[idx, 'rated_hp'] = row['total_emachine_kw'] / 0.746
                else:
                    df.loc[idx, 'rated_hp'] = row['eng_rated_hp']

                if row['base_year_powertrain_type'] == 'FCV':
                    # RV FCV map FCV to BEV for now
                    veh.base_year_powertrain_type = 'BEV'
                    veh.cost_curve_class = 'BEV_%s' % veh.drive_system
                else:
                    veh.base_year_powertrain_type = row['base_year_powertrain_type']
                    veh.cost_curve_class = row['cost_curve_class']

                veh.base_year_reg_class_id = row['reg_class_id']
                veh.base_year_cert_fuel_id = row['cert_fuel_id']
                veh.cert_fuel_id = row['cert_fuel_id']

                veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                row['market_class_id'] = omega_globals.options.MarketClass.get_vehicle_market_class(veh)

                veh.global_cumulative_battery_GWh = omega_globals.cumulative_battery_GWh

                veh.application_id = row['application_id']
                Vehicle.set_fueling_class(veh)

                # clear row tech flags:
                for tech_flag in omega_globals.options.CostCloud.tech_flags:
                    row[tech_flag] = 0

                # set row tech flags needed by powertrain cost:
                for tech_flag, value in omega_globals.options.CostCloud.get_tech_flags(veh).items():
                    row[tech_flag] = value

                powertrain_cost = sum(omega_globals.options.PowertrainCost.calc_cost(veh, veh.base_year_powertrain_type, row))

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

                glider_structure_cost_dollars, glider_non_structure_cost_dollars = \
                    GliderCost.calc_cost(veh, pd.DataFrame([row]))

                df.loc[idx, 'glider_structure_cost_dollars'] = \
                    float(glider_structure_cost_dollars)

                df.loc[idx, 'glider_non_structure_cost_dollars'] = \
                    float(glider_non_structure_cost_dollars)

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

            df.to_csv(omega_globals.options.output_folder + 'costed_vehicles.csv', columns=sorted(df.columns))

            # calculate weighted numeric values within the groups, and combined string values
            agg_df = df.groupby(aggregation_columns, as_index=False).apply(sales_weight_average_dataframe)
            agg_df['vehicle_name'] = agg_df[aggregation_columns].apply(lambda x: ':'.join(x.values.astype(str)), axis=1)

            if omega_globals.options.consolidate_manufacturers:
                agg_df['compliance_id'] = 'consolidated_OEM'
            else:
                agg_df['compliance_id'] = agg_df['manufacturer_id']

            agg_df.to_csv(omega_globals.options.output_folder + 'aggregated_vehicles.csv',
                          columns=sorted(agg_df.columns))

            omega_globals.options.vehicles_df = agg_df

            omega_globals.options.SalesShare.calc_base_year_data(omega_globals.options.vehicles_df)

        return template_errors

    @staticmethod
    def weighted_fillna(df, col, weight_by='sales', update_df=True):
        """
        Fill NaNs (if any) with weighted value

        Args:
            df (DataFrame): the dataframe to fill
            col (str): name of column to fill
            weight_by (str): name of the weighting column
            update_df (bool): if ``True`` then df will get updated values

        Returns:
            Nothing, modifies df[col] by filling NaNs with weighted value

        """
        fillval = 'NA'

        if not df.empty:
            notnans = df[col].notna()

            fillval = sum(df[col].loc[notnans] * df[weight_by].loc[notnans]) / df[weight_by].loc[notnans].sum()

            if update_df:
                df[col] = df[col].fillna(fillval)

        return fillval


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
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
