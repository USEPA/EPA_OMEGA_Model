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
aggregation_columns = ['context_size_class', 'body_style', 'electrification_class', 'unibody_structure',
                       'cert_fuel_id', 'reg_class_id', 'drive_system']


def weighted_average(df):
    import numpy as np

    numeric_columns = [c for c in df.columns if is_numeric_dtype(df[c])]
    non_numeric_columns = [c for c in df.columns if not is_numeric_dtype(df[c])]

    avg_df = pd.Series()

    for c in numeric_columns:
        if c != 'sales' and c != 'model_year':
            avg_df[c] = np.nansum(df[c] * df['sales']) / np.sum(df['sales'] * ~np.isnan(df[c]))
        elif c == 'sales':
            avg_df[c] = df[c].sum()

    for c in non_numeric_columns:
        avg_df[c] = ':'.join(df[c].unique())

    return avg_df


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

        if verbose:
            omega_log.logwrite('\nAggregating vehicles from %s...' % filename)

        input_template_name = 'vehicles'
        input_template_version = 0.46
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
            powertrain_type_dict = {'N': 'ICE', 'EV': 'BEV', 'HEV': 'HEV', 'PHEV': 'PHEV', 'FCV': 'BEV'}

            # new columns calculated here for every vehicle in vehicles.csv:
            df['structure_mass_lbs'] = 0
            df['battery_mass_lbs'] = 0
            df['powertrain_mass_lbs'] = 0
            df['glider_cost_dollars'] = 0
            df['structure_cost_dollars'] = 0
            df['glider_non_structure_cost_dollars'] = 0
            df['powertrain_cost_dollars'] = 0

            # fill in missing values
            for idx, row in df.iterrows():
                if pd.isna(row['ground_clearance_in']):
                    df.loc[idx, 'ground_clearance_in'] = 6.6  # dummy value, sales-weighted

                if pd.isna(row['height_in']):
                    df.loc[idx, 'height_in'] = 62.4  # dummy value, sales-weighted

                veh = Vehicle()
                veh.powertrain_type = powertrain_type_dict[row.electrification_class]
                df.loc[idx, 'battery_kwh'] = \
                    {'HEV': 1, 'PHEV': 18, 'BEV': 60, 'ICE': 0}[veh.powertrain_type]  # FOR NOW, NEED REAL NUMBERS

                df.loc[idx, 'motor_kw'] = \
                    {'HEV': 20, 'PHEV': 50, 'BEV': 150 + (100 * (row['drive_system'] == 4)), 'ICE': 0}[veh.powertrain_type]  # FOR NOW, NEED REAL NUMBERS

            for idx, row in df.iterrows():
                veh = Vehicle()
                veh.body_style = row.body_style
                veh.unibody_structure = row.unibody_structure
                veh.drive_system = row.drive_system
                veh.powertrain_type = powertrain_type_dict[row.electrification_class]

                structure_mass_lbs, battery_mass_lbs, powertrain_mass_lbs = \
                    MassScaling.calc_mass_terms(veh, row.structure_material, row.eng_rated_hp, row.battery_kwh, row.footprint_ft2)

                df.loc[idx, 'structure_mass_lbs'] = structure_mass_lbs
                df.loc[idx, 'battery_mass_lbs'] = battery_mass_lbs
                df.loc[idx, 'powertrain_mass_lbs'] = powertrain_mass_lbs

                # calc powertrain cost
                veh.model_year = row.model_year
                veh.electrification_class = row.electrification_class
                veh.market_class_id = omega_globals.options.MarketClass.get_vehicle_market_class(veh)
                row['cost_curve_class'] = 'TRX12'  # FOR NOW, NEED TO ADD TRX FLAGS TO THE VEHICLES.CSV
                row['engine_cylinders'] = row['eng_cyls_num']  # MIGHT NEED TO RENAME THESE, ONE PLACE OR ANOTHER
                row['engine_displacement_L'] = row['eng_disp_liters']  # MIGHT NEED TO RENAME THESE, ONE PLACE OR ANOTHER
                powertrain_cost = PowertrainCost.calc_cost(veh, pd.DataFrame([row]))[0]

                # don't think we need this, unless we want it for information purposes, veh.powertrain cost was only
                # calculated to get the glider_non_structure_cost
                # df.loc[idx, 'powertrain_cost_dollars'] = powertrain_cost

                # calc glider cost
                row['structure_mass_lbs'] = structure_mass_lbs
                veh.structure_material = row.structure_material
                veh.base_year_footprint_ft2 = row['footprint_ft2']
                veh.height_in = row['height_in']
                veh.ground_clearance_in = row['ground_clearance_in']
                veh.base_year_msrp_dollars = row['msrp_dollars']
                veh.base_year_structure_mass_lbs = structure_mass_lbs

                veh.base_year_glider_non_structure_cost_dollars = \
                    GliderCost.get_base_year_glider_non_structure_cost(veh, powertrain_cost)

                df.loc[idx, 'glider_cost_dollars'], df.loc[idx, 'structure_cost_dollars'], \
                    df.loc[idx, 'glider_non_structure_cost_dollars'] = GliderCost.calc_cost(veh, pd.DataFrame([row]))[0]

            df['glider_non_structure_mass_lbs'] = \
                df['curbweight_lbs'] - df['powertrain_mass_lbs'] - df['structure_mass_lbs'] - df['battery_mass_lbs']

            # calculate weighted numeric values within the groups, and combined string values
            agg_df = df.groupby(aggregation_columns, as_index=False).apply(weighted_average)
            agg_df['vehicle_name'] = agg_df[aggregation_columns].apply(lambda x: ':'.join(x.values.astype(str)), axis=1)
            agg_df['manufacturer_id'] = 'consolidated_OEM'
            agg_df['model_year'] = df['model_year'].iloc[0]
            agg_df.to_csv(omega_globals.options.output_folder + 'aggregated_vehicles.csv')

        omega_globals.options.vehicles_df = agg_df

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

        # from common.omega_functions import weighted_value
        #
        # from producer.manufacturers import Manufacturer  # needed for manufacturers table
        # from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        # from context.fuel_prices import FuelPrice  # needed for retail fuel price
        # from context.new_vehicle_market import NewVehicleMarket  # needed for context size class hauling info
        # from producer.vehicle_annual_data import VehicleAnnualData
        #
        # module_name = get_template_name(omega_globals.options.policy_targets_file)
        # omega_globals.options.VehicleTargets = importlib.import_module(module_name).VehicleTargets
        #
        # module_name = get_template_name(omega_globals.options.market_classes_file)
        # omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        #
        # from policy.policy_fuels import PolicyFuel
        #
        # # setup up dynamic attributes before metadata.create_all()
        # vehicle_columns = get_template_columns(omega_globals.options.vehicles_file)
        #
        # VehicleFinal.dynamic_columns = list(
        #     set.difference(set(vehicle_columns), VehicleFinal.base_input_template_columns))
        #
        # for vdc in VehicleFinal.dynamic_columns:
        #     VehicleFinal.dynamic_attributes.append(make_valid_python_identifier(vdc))
        #
        # for attribute in VehicleFinal.dynamic_attributes:
        #     if attribute not in VehicleFinal.__dict__:
        #         if int(sqlalchemy.__version__.split('.')[1]) > 3:
        #             sqlalchemy.ext.declarative.DeclarativeMeta.__setattr__(VehicleFinal, attribute, Column(attribute, Float))
        #         else:
        #             sqlalchemy.ext.declarative.api.DeclarativeMeta.__setattr__(VehicleFinal, attribute, Column(attribute, Float))
        #
        # SQABase.metadata.create_all(omega_globals.engine)
        #
        # init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
        #                                                   verbose=omega_globals.options.verbose)
        #
        # init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
        #                                         verbose=omega_globals.options.verbose)
        #
        # init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
        #                                        verbose=omega_globals.options.verbose)
        #
        # init_fail += FuelPrice.init_from_file(omega_globals.options.context_fuel_prices_file,
        #                                       verbose=omega_globals.options.verbose)
        #
        # init_fail += omega_globals.options.CostCloud.\
        #     init_cost_clouds_from_files(omega_globals.options.ice_vehicle_simulation_results_file,
        #                                 omega_globals.options.bev_vehicle_simulation_results_file,
        #                                 omega_globals.options.phev_vehicle_simulation_results_file,
        #                                 verbose=omega_globals.options.verbose)
        #
        # init_fail += omega_globals.options.VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
        #                                                                  verbose=omega_globals.options.verbose)
        #
        # init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
        #                                        verbose=omega_globals.options.verbose)
        #
        # init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
        #                                                   omega_globals.options.onroad_vehicle_calculations_file,
        #                                                   verbose=omega_globals.options.verbose)
        #
        if not init_fail:
            #     vehicle_list = VehicleFinal.get_compliance_vehicles(2019, 'OEM_A')
            #
            #     # update vehicle annual data, registered count must be update first:
            #     VehicleAnnualData.update_registered_count(vehicle_list[0], 2020, 54321)
            #
            #     # dump database with updated vehicle annual data
            #     dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
            #
            #     weighted_footprint = weighted_value(vehicle_list, 'initial_registered_count', 'footprint_ft2')
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        dump_omega_db_to_csv(omega_globals.options.database_dump_folder)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
