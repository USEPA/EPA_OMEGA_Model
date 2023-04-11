"""

**OMEGA effects vehicles module.**

Reads omega session output vehicles file.

----

**INPUT FILE FORMAT**

The file format consists of a one-row data header and subsequent data rows.

The data represents the aggregated base year vehicles and vehicles produced during the analysis years of an
omega session.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        vehicle_id,from_vehicle_id,name,manufacturer_id,compliance_id,model_year,fueling_class,reg_class_id,context_size_class,target_co2e_grams_per_mile,lifetime_vmt,cert_co2e_megagrams,target_co2e_megagrams,in_use_fuel_id,cert_fuel_id,market_class_id,unibody_structure,drive_system,dual_rear_wheel,body_style,base_year_powertrain_type,charge_depleting_range_mi,prior_redesign_year,redesign_interval,in_production,price_modification_dollars,modified_cross_subsidized_price_dollars,price_dollars,market_class_cross_subsidy_multiplier,base_year_product,base_year_reg_class_id,base_year_vehicle_id,base_year_market_share,model_year_prevalence,base_year_glider_non_structure_mass_lbs,base_year_glider_non_structure_cost_dollars,base_year_footprint_ft2,base_year_curbweight_lbs,base_year_curbweight_lbs_to_hp,base_year_msrp_dollars,base_year_target_coef_a,base_year_target_coef_b,base_year_target_coef_c,base_year_workfactor,base_year_gvwr_lbs,base_year_gcwr_lbs,base_year_cert_fuel_id,cost_curve_class,structure_material,battery_kwh,motor_kw,curbweight_lbs,footprint_ft2,eng_rated_hp,workfactor,gvwr_lbs,gcwr_lbs,_initial_registered_count,projected_sales,credits_co2e_Mg_per_vehicle,target_co2e_Mg_per_vehicle,cert_co2e_Mg_per_vehicle,cert_co2e_grams_per_mile,new_vehicle_mfr_generalized_cost_dollars,new_vehicle_mfr_cost_dollars,cert_indirect_co2e_grams_per_mile,cert_direct_co2e_grams_per_mile,cert_direct_kwh_per_mile,onroad_direct_co2e_grams_per_mile,onroad_direct_kwh_per_mile,cert_direct_oncycle_kwh_per_mile,cert_direct_offcycle_kwh_per_mile,cert_direct_oncycle_co2e_grams_per_mile,cert_direct_offcycle_co2e_grams_per_mile,cert_indirect_offcycle_co2e_grams_per_mile,high_eff_alternator,start_stop,ac_efficiency,ac_leakage,bev,gdi,turb11,mhev,phev,turb12,trx22,hev_truck,deac_pd,trx12,structure_cost,trx21,atk2,driveline_cost,deac_fc,cegr,ice,electrified_driveline_cost,glider_non_structure_cost,emachine_cost,rated_hp,hev,fwd,fcv,awd,trx10,trx11,diesel_fuel,engine_cost,gas_fuel,battery_cost,unibody,ecvt,long_bed_8ft,eng_disp_liters,eng_cyls_num,ground_clearance_in,tot_road_load_hp,payload_capacity_lbs,width_in,height_in,passenger_capacity,etw_lbs,interior_volume_cuft,length_in,alvw_lbs,towing_capacity_lbs,wheelbase_in
        0,,Compact:sedan:BEV:1.0:{'electricity':1.0}:car:2.0:0.0:2021:2017.0:5.0:BEV:steel:VW:VW,VW,VW,2021,BEV,,Compact,,,,,{'US electricity':1.0},{'electricity':1.0},sedan_wagon.BEV,1.0,2.0,0.0,sedan,BEV,300.0,2017.0,5.0,1,,,,,1,car,0.0,0.000343788350714398,,1676.215369123688,11679.101593869393,43.2,3459.0,17.195865833470044,35395.0,36.65573488,0.074387598,0.020185903,0.0,4431.0,0.0,{'electricity':1.0},BEV,steel,60.0,150.0,3459.0,43.2,200.0,0.0,4431.0,0.0,5552.0,,,,,,,,,0.0,0.0,0.0,0.0,0.0,,0.0,,,0.0,0.0,,,1.0,0.0,0.0,,0.0,0.0,0.0,,0.0,0.0,,0.0,0.0,,0.0,0.0,0.0,,,,,0.0,0.0,0.0,0.0,0.0,0.0,0.0,,0.0,,,0.0,0.0,0.0,0.0,5.0,12.1,827.0,70.8,57.2,5.0,3750.0,116.3,168.1,3945.0,0.0,103.5
        156,,Large:sedan:ICE:1.0:{'gasoline':1.0}:car:4.0:0.0:2021:2021.0:5.0:TDS_TRX22_SS1:steel:BMW:BMW,BMW,BMW,2021,ICE,,Large,,,,,{'pump gasoline':1.0},{'gasoline':1.0},sedan_wagon.ICE,1.0,4.0,0.0,sedan,ICE,0.0,2021.0,5.0,1,,,,,1,car,156.0,1.634728468814861e-05,,3582.0903750330267,131105.9306533214,56.02272727,5128.0,8.532445923460898,156700.0,74.0,-0.616,0.02948,0.0,0.0,0.0,{'gasoline':1.0},TDS_TRX22_SS1,steel,0.0,0.0,5128.0,56.02272727,601.0,0.0,0.0,0.0,264.0,,,,,,,,,0.0,0.0,0.0,0.0,0.0,,0.0,,,0.0,1.0,,,0.0,1.0,0.0,,0.0,1.0,0.0,,0.0,0.0,,0.0,0.0,,0.0,0.0,1.0,,,,,0.0,0.0,0.0,0.0,0.0,0.0,0.0,,1.0,,,0.0,0.0,6.6,12.0,5.3,15.599999999999998,0.0,74.9,58.2,5.0,5500.0,0.0,206.6,0.0,0.0,126.39999999999999

Data Column Name and Description

:vehicle_id:
    The unique vehicle ID number

:from_vehicle_id:
    For internal use only, blank for base year vehicles

:name:
    The vehicle name, determined during vehicle aggregation and indicates the aggregation term values, colon-separated

:manufacturer_id:
    The name of the manufacturer

:compliance_id:
    The name of the manufacturer or 'consolidated_OEM' when consolidating manufacturers

:model_year:
    The vehicle model year

:fueling_class:
    Market class fueling class, e.g. 'BEV', 'ICE'

:reg_class_id:
    Name of the regulatory class, e.g. 'car', 'truck', etc, blank for base year vehicles

:context_size_class:
    The name of the vehicle size class, e.g. 'Minicompact', 'Large Utility', etc

:target_co2e_grams_per_mile:
    The vehicle target co2e g/mi, a function of vehicle attributes and the session policy

:lifetime_vmt:
    The vehicle lifetime VMT used for calculating lifetime megagrams of co2e emissions

:cert_co2e_megagrams:
    The vehicle model certification lifetime co2e emissions in megagrams, i.e. Mg/vehicle * sales

:target_co2e_megagrams:
    The vehicle model target lifetime co2e emissions in megagrams, i.e. Mg/vehicle * sales

:in_use_fuel_id:
    The OMEGA in-use fuel id and distance share as a python dict (e.g., ``{'pump gasoline':1.0}``)

:cert_fuel_id:
    The OMEGA certification fuel id and distance share as a python dict (e.g., ``{'gasoline':1.0}``)

:market_class_id:
    Vehicle market class ID, e.g. 'sedan_wagon.ICE'

:unibody_structure:
    Vehicle body structure; 1 = unibody, 0 = body-on-frame

:drive_system:
    Vehicle drive system, 2=FWD/RWD, 4=AWD

:dual_rear_wheel:
    Technology flag for dual rear wheels, i.e. 'duallies' (1 = Equipped, 0 = Not equipped)

:body_style:
    The name of the vehicle body style, e.g., 'sedan_wagon', 'cuv_suv_van', 'pickup'

:base_year_powertrain_type:
    The powertrain type of the original base-year vehicle, e.g. 'ICE', 'PHEV', 'BEV', etc

:charge_depleting_range_mi:
    The vehicle charge depleting range, if applicable, zero otherwise

:prior_redesign_year:
    The vehicle's prior redesign year

:redesign_interval:
    The vehicle redesign interval in years

:in_production:
    = 1 if the vehicle is in production, 0 otherwise.  Alternative powertrain vehicles are carried forward in the output
    file even if they aren't in production yet, due to redesign constraints

:price_modification_dollars:
    The vehicle price modification in dollars.  Negative values represent 'rebates' or other incentives

:modified_cross_subsidized_price_dollars:
    The vehicle price, including rebates and cross-subsidy multipliers
    ``modified_cross_subsidized_price_dollars = price_dollars + price_modification_dollars``

:price_dollars:
    The vehicle price, without price modifiers, includes cross-subsidy multipliers.
    ``price_dollars = new_vehicle_mfr_cost_dollars * market_class_cross_subsidy_multiplier``

:market_class_cross_subsidy_multiplier:
    The markup or markdown multiplier applied to the ``new_vehicle_mfr_cost_dollars`` as a result of the cross-subsidy
    search and producer-consumer iteration

:base_year_product:
    = 1 if vehicle is a non-alternative-powertrain vehicle (e.g. was available in the base year), = 0 otherwise

:base_year_reg_class_id:
    The base year source vehicle's regulatory class id, i.e. legacy regulatory class id

:base_year_vehicle_id:
    The id number of the base year vehicle the current vehicle is based on.  Comes from the ``aggregated_vehicles.csv``
    in the session output folder.  Shared by alternative and non-alternative vehicles

:base_year_market_share:
    The base year vehicle's share of the total vehicle market

:model_year_prevalence:
    *unused*

:base_year_glider_non_structure_mass_lbs:
    The base year source vehicle's glider non-structure mass (pounds)

:base_year_glider_non_structure_cost_dollars:
    The base year source vehicle's glider non-structure cost (dollars)

:base_year_footprint_ft2:
    The base year source vehicle's footprint (square feet)

:base_year_curbweight_lbs:
    The base year source vehicle's curb weight (pounds)

:base_year_curbweight_lbs_to_hp:
    The base year source vehicle's weight-to-power ratio (pounds per horsepower)

:base_year_msrp_dollars:
    The base year source vehicle's manufacturer suggested retail price (MSRP) (dollars)

:base_year_target_coef_a:
    The base year source vehicle's coast down target A coefficient (lbf)

:base_year_target_coef_b:
    The base year source vehicle's coast down target B coefficient (lbf/mph)

:base_year_target_coef_c:
    The base year source vehicle's coast down target C coefficient (lbf/mph**2)

:base_year_workfactor:
    The base year source vehicle's workfactor, if applicable, zero otherwise

:base_year_gvwr_lbs:
    The base year source vehicle's gross vehicle weight rating (pounds)

:base_year_gcwr_lbs:
    The base year source vehicle's gross combined weight rating (pounds)

:base_year_cert_fuel_id:
    The base year source vehicle's OMEGA certification fuel id and distance share as a python dict
    (e.g., ``{'gasoline':1.0}``)

:cost_curve_class:
    The name of the cost curve class of the vehicle, used to determine which technology options and associated costs
    are available to be applied to this vehicle.

:structure_material:
    Primary material of the vehicle body structure, e.g. 'steel', 'aluminum'

:battery_kwh:
    The vehicle's battery pack capacity (kilowatt-hours), if applicable, zero otherwise

:motor_kw:
    The vehicle's drive motor power rating (kilowatts), if applicable, zero otherwise

:curbweight_lbs:
    The vehicle's curb weight (pounds)

:footprint_ft2:
    The vehicle's footprint (square feet)

:eng_rated_hp:
    The vehicle's engine power rating (horsepower) if applicable, zero otherwise

:workfactor:
    The vehicle's workfactor, if applicable, zero otherwise

:gvwr_lbs:
    The vehicle's gross vehicle weight rating (pounds)

:gcwr_lbs:
    The vehicle's gross combined weight rating (pounds)

:_initial_registered_count:
    The vehicle's initial registered count, i.e. sales in the given model year

:projected_sales:
    *unused*

:credits_co2e_Mg_per_vehicle:
    The co2e credits earned by the vehicle on a per-vehicle basis (co2e megagrams).  Positive values indicate
    over-compliance with vehicle standards, negative values indicated under-compliance

:target_co2e_Mg_per_vehicle:
    The per-vehicle target lifetime co2e emissions in megagrams

:cert_co2e_Mg_per_vehicle:
    The per-vehicle model certification lifetime co2e emissions in megagrams

:cert_co2e_grams_per_mile:
    The vehicle's certification co2e emissions (grams per mile), including offcycle credits, etc.
    ``cert_co2e_grams_per_miles = cert_direct_co2e_grams_per_mile + cert_indirect_co2e_grams_per_mile -
    cert_indirect_offcycle_co2e_grams_per_mile``

:new_vehicle_mfr_generalized_cost_dollars:
    The vehicle's manufacturer generalized cost (dollars).
    Includes manufacturing cost plus some years of fuel costs, etc

:new_vehicle_mfr_cost_dollars:
    The vehicle's manufacturing cost (dollars)

:cert_indirect_co2e_grams_per_mile:
    The vehicle's indirect certification co2e emissions (grams per mile), e.g. upstream emissions

:cert_direct_co2e_grams_per_mile:
    The vehicle's direct (i.e. tailpipe) certification co2e emissions (grams per mile)
    ``cert_direct_co2e_grams_per_mile = cert_direct_oncycle_co2e_grams_per_mile -
    cert_direct_offcycle_co2e_grams_per_mile``

:cert_direct_kwh_per_mile:
    The vehicle's direct (i.e. in-vehicle) certification energy consumption (kilowatt-hours per mile),
    ``cert_direct_kwh_per_mile = cert_direct_oncycle_kwh_per_mile - cert_direct_offcycle_kwh_per_mile``

:onroad_direct_co2e_grams_per_mile:
    The vehicle's direct (i.e. tailpipe) on-road co2e emissions (grams per mile)

:onroad_direct_kwh_per_mile:
    The vehicle's direct (i.e. in-vehicle) on-road energy consumption (kilowatt-hours per mile)

:cert_direct_oncycle_kwh_per_mile:
    The vehicle's direct (i.e. in-vehicle) on-cycle energy consumption (kilowatt-hours per mile)

:cert_direct_offcycle_kwh_per_mile:
    The vehicle's direct (i.e. in-vehicle) off-cycle (credits) energy consumption (kilowatt-hours per mile)

:cert_direct_oncycle_co2e_grams_per_mile:
    The vehicle's direct (i.e. tailpipe) on-cycle co2e emissions (grams per mile)

:cert_direct_offcycle_co2e_grams_per_mile:
    The vehicle's direct (i.e. tailpipe) off-cycle (credits) co2e emissions (grams per mile)

:cert_indirect_offcycle_co2e_grams_per_mile:
    The vehicle's indirect (i.e. non-tailpipe) off-cycle (credits) co2e emissions (grams per mile),
    e.g. AC leakage credits

:high_eff_alternator:
    Technology flag for high efficiency alternator (1 = Equipped, 0 = Not equipped)

:start_stop:
    Technology flag for engine start-stop system (1 = Equipped, 0 = Not equipped)

:ac_efficiency:
    = 1 if the vehicle qualifies for the AC efficiency off-cycle credit, = 0 otherwise

:ac_leakage:
    = 1 if the vehicle qualifies for the AC leakage off-cycle credit, = 0 otherwise

:bev:
    Technology flag for battery electric vehicle (1 = Equipped, 0 = Not equipped)

:gdi:
    Technology flag for gasoline direct injection system (1 = Equipped, 0 = Not equipped)

:turb11:
    Technology flag for turbocharged engine, 18-21bar 1st generation (1 = Equipped, 0 = Not equipped)

:mhev:
    Technology flag for a mild hybrid vehicle, e.g. 48V start-stop, etc (1 = Equipped, 0 = Not equipped)

:phev:
    Technology flag for a plug-in hybrid system (1 = Equipped, 0 = Not equipped)

:turb12:
    Technology flag for turbocharged engine, 18-21bar 2nd generation (1 = Equipped, 0 = Not equipped)

:trx22:
    Technology flag for an advanced high gear count transmission or equivalent (1 = Equipped, 0 = Not equipped)

:hev_truck:
    Technology flag for a hybrid truck (1 = Equipped, 0 = Not equipped)

:deac_pd:
    Technology flag for cylinder deactivation, discrete operation of partial number of cylinders
    (1 = Equipped, 0 = Not equipped)

:trx12:
    Technology flag for an advanced transmission (1 = Equipped, 0 = Not equipped)

:structure_cost:
    The vehicle's structure cost (dollars).  Structure = body-in-white + closures

:trx21:
    Technology flag for a high gear count transmission or equivalent (1 = Equipped, 0 = Not equipped)

:atk2:
    Technology flag for high geometric compression ratio Atkinson cycle engine (1 = Equipped, 0 = Not equipped)

:driveline_cost:
    The vehicle's driveline cost (dollars)
    ``driveline_cost = trans_cost + high_eff_alt_cost + start_stop_cost + ac_leakage_cost + ac_efficiency_cost
    + lv_battery_cost + hvac_cost``

:deac_fc:
    Technology flag for cylinder deactivation, continuosly variable operation of full number of cylinders
    (1 = Equipped, 0 = Not equipped)

:cegr:
    Technology flag for cooled exhaust gas recirculation (1 = Equipped, 0 = Not equipped)

:ice:
    Technology flag for internal combustion engine (1 = Equipped, 0 = Not equipped)

:electrified_driveline_cost:
    The vehicle's electrified driveline cost (dollars)
    ``electrified_driveline_cost = inverter_cost + induction_inverter_cost + obc_and_dcdc_converter_cost
    + hv_orange_cables_cost + single_speed_gearbox_cost + powertrain_cooling_loop_cost + charging_cord_kit_cost +
    dc_fast_charge_circuitry_cost + power_management_and_distribution_cost + brake_sensors_actuators_cost +
    additional_pair_of_half_shafts_cost``

:glider_non_structure_cost:
    The vehicle's glider non-structure cost (dollars)

:emachine_cost:
    The vehicle's electric machine cost (dollars)

:rated_hp:
    The vehicle's rated horsepower (whether ICE or BEV)

:hev:
    Technology flag for non plug-in hybrid system (1 = Equipped, 0 = Not equipped)

:fwd:
    Technology flag for front-wheel drive (1 = Equipped, 0 = Not equipped)

:fcv:
    Technology flag for a fuel cell vehicle (1 = Equipped, 0 = Not equipped)

:awd:
    Technology flag for all-wheel drive (1 = Equipped, 0 = Not equipped)

:trx10:
    Technology flag for a baseline transmission (1 = Equipped, 0 = Not equipped)

:trx11:
    Technology flag for an improved transmission (1 = Equipped, 0 = Not equipped)

:diesel_fuel:
    Technology flag for diesel-fueled engine (1 = Equipped, 0 = Not equipped)

:engine_cost:
    The vehicle's internal combustion engine cost, if applicable, = 0 otherwise

:gas_fuel:
    Technology flag for gasoline-fueled engine (1 = Equipped, 0 = Not equipped)

:battery_cost:
    The vehicle's battery cost, if applicable, = 0 otherwise

:unibody:
    Technology flag for unibody vehicle structure (1 = Equipped, 0 = Not equipped)

:ecvt:
    Technology flag for a powersplit-type hybrid vehicle transmission (1 = Equipped, 0 = Not equipped)

:long_bed_8ft:
    Technology flag for a pickup with an 8-foot long bed (1 = Equipped, 0 = Not equipped)

:eng_disp_liters:
    The vehicle's engine displacement (liters), if applicable, = 0 otherwise

:eng_cyls_num:
    The vehicle's number of engine cylinders, if applicable, = 0 otherwise

:ground_clearance_in:
    The vehicle's ground clearance (inches)

:tot_road_load_hp:
    The vehicle's roadload power (horsepower) at a vehicle speed of 50 miles per hour

:payload_capacity_lbs:
    The vehicle's payload capacity (pounds)

:width_in:
    The vehicle's overall width (inches)

:height_in:
    The vehicle's overall height (inches)

:passenger_capacity:
    The vehicle's passenger capacity (number of occupants)

:etw_lbs:
    The vehicle's equivalent test weight (ETW) (pounds)

:interior_volume_cuft:
    The vehicle's interior volume (cubic feet)

:length_in:
    The vehicle's overall length (inches)

:alvw_lbs:
    The vehicle's average loaded vehicle weight (pounds)

:towing_capacity_lbs:
    The vehicle's towing capacity (pounds)

:wheelbase_in:
    The vehicle's wheelbase (inches)

----

**CODE**

"""

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.consumer import deregionalizer


class Vehicles:
    """
    Vehicles class definition.

    """
    def __init__(self):
        self._dict = dict()

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        df = read_input_file(filepath, effects_log, index_col=0)

        df = deregionalizer.deregionalize_entries(df, 'market_class_id', 'r1nonzev', 'r2zev')
        df = deregionalizer.deregionalize_entries(df, 'body_style', 'r1nonzev', 'r2zev')

        df = deregionalizer.clean_body_styles(df)

        self._dict = df.to_dict('index')

    def get_vehicle_attributes(self, vehicle_id, *attribute_names):
        """
        Get vehicle attributes by vehicle id and attribute name(s).

        Args:
            vehicle_id: the vehicle id
            *attribute_names: attributes to retrieve

        Returns:
            Vehicle attributes by vehicle id and attribute name(s).

        """
        attribute_list = list()
        for attribute_name in attribute_names:
            attribute_list.append(self._dict[vehicle_id][attribute_name])
        if len(attribute_list) == 1:
            return attribute_list[0]

        return attribute_list
