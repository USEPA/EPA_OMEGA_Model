"""

**Routines to calculate powertrain cost.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,powertrain_cost,input_template_version:,0.1,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        powertrain_type,item,value,quantity,dollar_basis,notes
        ALL,dollars_per_cylinder,((-28.814) * CYL + 726.27) * CYL * MARKUP_ICE,,2019,
        ALL,dollars_per_liter,((400) * LITERS) * MARKUP_ICE,,2019,
        ALL,gdi,((43.237) * CYL + 97.35) * MARKUP_ICE,,2019,
        BEV,battery_offset,{"dollars_per_kwh": {2023: -9, 2024: -18, 2025: -27, 2026: -36, 2027: -45, 2028: -45, 2029: -45, 2030: -33.75, 2031: -22.50, 2032: -11.25, 2033: -0}},,,

Data Column Name and Description

    :powertrain_type:
        Vehicle powertrain type, e.g. 'ICE', 'PHEV', etc

    :item:
        The name of the powertrain component associated with the cost value

    :value:
        The component cost value or equation to be evaulated

    :quantity:
        Component quantity per vehicle, if applicable

    :dollar_basis:
        The dollar basis year for the cost value, e.g. ``2020``

    :notes:
        Optional notes related to the data row

----

**CODE**

"""
print('importing %s' % __file__)
import pandas as pd

from common.omega_types import *
from common.input_validation import *
from context.ip_deflators import ImplicitPriceDeflators

_cache = {}


class PowertrainCost(OMEGABase):
    """
    **Loads and provides access to powertrain cost data, provides methods to calculate powertrain costs.**

    """
    cost_tracker = {}

    @staticmethod
    def calc_cost(vehicle, powertrain_type=None, pkg_info=None, update_tracker=False):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
            vehicle (Vehicle): the vehicle to calc costs for
            pkg_info (dict-like): the necessary information for developing cost estimates.
            update_tracker (bool): update cost tracking dict if ``True``

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        if pkg_info is None:
            pkg_info = omega_globals.options.CostCloud.get_tech_flags(vehicle)
            pkg_info['curbweight_lbs'] = vehicle.curbweight_lbs
            pkg_info['battery_kwh'] = vehicle.battery_kwh
            pkg_info['total_emachine_kw'] = vehicle.total_emachine_kw
            pkg_info['drive_system'] = vehicle.drive_system
            pkg_info['engine_cylinders'] = vehicle.engine_cylinders
            pkg_info['engine_displacement_liters'] = vehicle.engine_displacement_liters
            pkg_info['footprint_ft2'] = vehicle.footprint_ft2
            pkg_info['cost_curve_class'] = vehicle.cost_curve_class

        if powertrain_type is None:
            powertrain_type = omega_globals.options.CostCloud.get_powertrain_type(pkg_info)

        update_dict = None
        market_class_id, model_year, base_year_cert_fuel_id, reg_class_id, drive_system, body_style = \
            vehicle.market_class_id, vehicle.model_year, vehicle.base_year_cert_fuel_id, vehicle.reg_class_id, \
                vehicle.drive_system, vehicle.body_style

        locals_dict = locals()

        if model_year <= 2025 or vehicle.global_cumulative_battery_GWh['total'] == 0 \
                or vehicle.global_cumulative_battery_GWh[model_year - 1] == 0:
            learning_pev_battery_scaling_factor = 1
        else:
            if reg_class_id != 'mediumduty':
                locals_dict.update({'CUMULATIVE_GWH': vehicle.global_cumulative_battery_GWh[model_year - 1]})
                learning_pev_battery_scaling_factor = eval(_cache['PEV', 'battery_GWh_learning_curve']['value'],
                                                               {'np': np}, locals_dict)
                if learning_pev_battery_scaling_factor > 1:
                    gwh = vehicle.global_cumulative_battery_GWh[model_year - 2]
                    locals_dict.update({'CUMULATIVE_GWH': vehicle.global_cumulative_battery_GWh[model_year - 1] + gwh})
                    learning_pev_battery_scaling_factor = eval(_cache['PEV', 'battery_GWh_learning_curve']['value'],
                                                               {'np': np}, locals_dict)
            else:
                cumulative_GWh_ld_dict = \
                    eval(_cache['PEV', 'cumulative_GWh_LD_noIRA']['value'], {'np': np}, locals_dict)
                if model_year - 1 in cumulative_GWh_ld_dict['GWh']:
                    gwh = cumulative_GWh_ld_dict['GWh'][model_year - 1]
                    locals_dict.update({'CUMULATIVE_GWH': vehicle.global_cumulative_battery_GWh[model_year - 1] + gwh})
                    learning_pev_battery_scaling_factor = eval(_cache['PEV', 'battery_GWh_learning_curve']['value'],
                                                               {'np': np}, locals_dict)
                    if learning_pev_battery_scaling_factor > 1:
                        gwh += cumulative_GWh_ld_dict['GWh'][model_year - 2]
                        locals_dict.update(
                            {'CUMULATIVE_GWH': vehicle.global_cumulative_battery_GWh[model_year - 1] + gwh})
                        learning_pev_battery_scaling_factor = eval(_cache['PEV', 'battery_GWh_learning_curve']['value'],
                                                                   {'np': np}, locals_dict)
                else:
                    year = max(yr for yr in cumulative_GWh_ld_dict['GWh'])
                    gwh = cumulative_GWh_ld_dict['GWh'][year]
                    locals_dict.update({'CUMULATIVE_GWH': vehicle.global_cumulative_battery_GWh[model_year - 1] + gwh})
                    learning_pev_battery_scaling_factor = eval(_cache['PEV', 'battery_GWh_learning_curve']['value'],
                                                               {'np': np}, locals_dict)

        # markups and learning
        MARKUP_ICE = eval(_cache['ICE', 'markup']['value'], {'np': np}, locals_dict)
        MARKUP_HEV = eval(_cache['HEV', 'markup']['value'], {'np': np}, locals_dict)
        MARKUP_PHEV = eval(_cache['PHEV', 'markup']['value'], {'np': np}, locals_dict)
        MARKUP_BEV = eval(_cache['BEV', 'markup']['value'], {'np': np}, locals_dict)
        MARKUP_ALL = eval(_cache['ALL', 'markup']['value'], {'np': np}, locals_dict)

        learning_rate = eval(_cache['ALL', 'learning_rate']['value'], {'np': np}, locals_dict)
        learning_start = eval(_cache['ALL', 'learning_start']['value'], {'np': np}, locals_dict)
        legacy_sales_scaler_ice = eval(_cache['ICE', 'legacy_sales_learning_scaler']['value'], {'np': np}, locals_dict)
        legacy_sales_scaler_pev = eval(_cache['PEV', 'legacy_sales_learning_scaler']['value'], {'np': np}, locals_dict)
        sales_scaler_ice = eval(_cache['ICE', 'sales_scaler']['value'], {'np': np}, locals_dict)
        sales_scaler_pev = eval(_cache['PEV', 'sales_scaler']['value'], {'np': np}, locals_dict)
        cumulative_sales_ice = abs(sales_scaler_ice * (model_year - learning_start))
        cumulative_sales_pev = abs(sales_scaler_pev * (model_year - learning_start))
        learning_factor_ice = \
            ((cumulative_sales_ice + legacy_sales_scaler_ice) / legacy_sales_scaler_ice) ** learning_rate
        learning_factor_pev = \
            ((cumulative_sales_pev + legacy_sales_scaler_pev) / legacy_sales_scaler_pev) ** learning_rate
        if model_year < learning_start:
            learning_factor_ice = 1 / learning_factor_ice
            learning_factor_pev = 1 / learning_factor_pev

        weight_bins = (0, 3200, 3800, 4400, 5000, 5600, 6200, 14000)
        tractive_motor = 'dual'
        if (market_class_id.__contains__('non_hauling') and vehicle.drive_system != 'AWD') or powertrain_type == 'HEV':
            tractive_motor = 'single'

        drive_system_cost = trans_cost = cyl_cost = liter_cost = 0
        high_eff_alt_cost = start_stop_cost = deac_pd_cost = deac_fc_cost = cegr_cost = atk2_cost = gdi_cost = 0
        turb12_cost = turb11_cost = 0
        twc_cost = gpf_cost = diesel_eas_cost = 0
        ac_leakage_cost = ac_efficiency_cost = 0
        induction_inverter_cost = 0
        turb_scaler = 1  # default value adjusted below for turb packages

        battery_cost = electrified_driveline_cost = motor_cost = induction_motor_cost = inverter_cost = 0
        obc_and_dcdc_converter_cost = hv_orange_cables_cost = lv_battery_cost = 0
        hvac_cost = single_speed_gearbox_cost = powertrain_cooling_loop_cost = 0
        charging_cord_kit_cost = dc_fast_charge_circuitry_cost = 0
        power_management_and_distribution_cost = brake_sensors_actuators_cost = 0
        additional_pair_of_half_shafts_cost = 0
        emachine_cost = 0
        gasoline_flag = diesel_flag = 0

        KW = KWH = KW_OBC = obc_kw = KW_DU = KW_FDU = KW_RDU = KW_P2 = KW_P4 = 0
        trans = CYL = engine_config = LITERS = None
        twc_substrate = twc_washcoat = twc_canning = twc_pgm = twc_cost = gpf_cost = diesel_eas_cost = eas_cost = 0
        engine_cost = engine_block_cost = cegr_cost = gdi_cost = turb_cost = deac_pd_cost = deac_fc_cost = atk2_cost = 0
        fuel_storage_cost = non_eas_exhaust_cost = exhaust_cost = 0
        lv_battery_cost = start_stop_cost = trans_cost = high_eff_alt_cost = lv_harness_cost = 0
        powertrain_cooling_cost = hvac_cost = 0
        hv_harness_cost = dc_dc_converter_cost = charge_cord_cost = 0
        motor_cost = gearbox_cost = inverter_cost = battery_cost = battery_offset = 0
        ac_leakage_cost = ac_efficiency_cost = 0
        powertrain_cost = engine_cost = driveline_cost = e_machine_cost = electrified_driveline_cost = 0

        CURBWT = pkg_info['curbweight_lbs']
        VEHICLE_SIZE_CLASS = weight_bins.index(min([v for v in weight_bins if CURBWT < v]))
        locals_dict = locals()

        cost_curve_class = pkg_info['cost_curve_class']

        if drive_system != 'AWD':
            drive_system = '2WD'
            locals_dict = locals()

        # powertrain costs for anything with a liquid fueled engine
        if powertrain_type in ['ICE', 'HEV', 'PHEV', 'MHEV']:

            trans = get_trans(pkg_info)[0]

            gasoline_flag = True
            if 'diesel' in base_year_cert_fuel_id:
                diesel_flag = True
                gasoline_flag = False

            CYL = pkg_info['engine_cylinders']
            LITERS = pkg_info['engine_displacement_liters']

            locals_dict = locals()

            # PGM costs and loadings for gasoline
            if gasoline_flag:
                PT_USD_PER_OZ = eval(_cache['ALL', 'pt_dollars_per_oz']['value'], {'np': np}, locals_dict)
                PD_USD_PER_OZ = eval(_cache['ALL', 'pd_dollars_per_oz']['value'], {'np': np}, locals_dict)
                RH_USD_PER_OZ = eval(_cache['ALL', 'rh_dollars_per_oz']['value'], {'np': np}, locals_dict)
                PT_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pt_grams_per_liter']['value'], {'np': np}, locals_dict)
                PD_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pd_grams_per_liter']['value'], {'np': np}, locals_dict)
                RH_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_rh_grams_per_liter']['value'], {'np': np}, locals_dict)
                OZ_PER_GRAM = eval(_cache['ALL', 'troy_oz_per_gram']['value'], {'np': np}, locals_dict)

            turb_input_scaler = eval(_cache['ALL', 'turb_scaler']['value'], {'np': np}, locals_dict)

            learn = learning_factor_ice

            # determine trans and calc cost
            adj_factor = _cache['ALL', trans]['dollar_adjustment']
            trans_cost = eval(_cache['ALL', trans]['value'], {'np': np}, locals_dict) \
                         * adj_factor * learn

            # cylinder cost
            adj_factor = _cache['ALL', 'dollars_per_cylinder']['dollar_adjustment']
            cyl_cost = eval(_cache['ALL', 'dollars_per_cylinder']['value'], {'np': np}, locals_dict) \
                       * adj_factor * learn

            # displacement cost
            adj_factor = _cache['ALL', 'dollars_per_liter']['dollar_adjustment']
            liter_cost = eval(_cache['ALL', 'dollars_per_liter']['value'], {'np': np}, locals_dict) \
                         * adj_factor * learn

            # high efficiency alternator cost
            adj_factor = _cache['ALL', 'high_eff_alternator']['dollar_adjustment']
            high_eff_alt_cost = eval(_cache['ALL', 'high_eff_alternator']['value'], {'np': np}, locals_dict) \
                                * adj_factor * learn * pkg_info['high_eff_alternator']

            # start_stop cost
            adj_factor = _cache['ALL', 'start_stop']['dollar_adjustment']
            start_stop_cost = eval(_cache['ALL', 'start_stop']['value'], {'np': np}, locals_dict) \
                              * adj_factor * learn * pkg_info['start_stop']

            # deac_pd cost
            adj_factor = _cache['ALL', 'deac_pd']['dollar_adjustment']
            deac_pd_cost = eval(_cache['ALL', 'deac_pd']['value'], {'np': np}, locals_dict) \
                           * adj_factor * learn * pkg_info['deac_pd']

            # deac_fc cost
            adj_factor = _cache['ALL', 'deac_fc']['dollar_adjustment']
            deac_fc_cost = eval(_cache['ALL', 'deac_fc']['value'], {'np': np}, locals_dict) \
                           * adj_factor * learn * pkg_info['deac_fc']

            # cegr cost
            adj_factor = _cache['ALL', 'cegr']['dollar_adjustment']
            cegr_cost = eval(_cache['ALL', 'cegr']['value'], {'np': np}, locals_dict) \
                        * adj_factor * learn * pkg_info['cegr']

            # atk2 cost
            adj_factor = _cache['ALL', 'atk2']['dollar_adjustment']
            atk2_cost = eval(_cache['ALL', 'atk2']['value'], {'np': np}, locals_dict) \
                        * adj_factor * learn * pkg_info['atk2']

            # gdi cost
            adj_factor = _cache['ALL', 'gdi']['dollar_adjustment']
            gdi_cost = eval(_cache['ALL', 'gdi']['value'], {'np': np}, locals_dict) \
                       * adj_factor * learn * pkg_info['gdi']

            # turb12 cost
            adj_factor = _cache['ALL', 'turb12']['dollar_adjustment']
            turb12_cost = eval(_cache['ALL', 'turb12']['value'], {'np': np}, locals_dict) \
                          * adj_factor * learn * pkg_info['turb12']

            # turb11 cost
            adj_factor = _cache['ALL', 'turb11']['dollar_adjustment']
            turb11_cost = eval(_cache['ALL', 'turb11']['value'], {'np': np}, locals_dict) \
                          * adj_factor * learn * pkg_info['turb11']

            turb_scaler += (turb_input_scaler - turb_scaler) * (pkg_info['turb11'] | pkg_info['turb12'])

            # 3-way catalyst cost
            if gasoline_flag:
                adj_factor_sub = _cache['ALL', 'twc_substrate']['dollar_adjustment']
                adj_factor_wash = _cache['ALL', 'twc_washcoat']['dollar_adjustment']
                adj_factor_can = _cache['ALL', 'twc_canning']['dollar_adjustment']
                TWC_SWEPT_VOLUME = eval(_cache['ALL', 'twc_swept_volume']['value'], {'np': np}, locals_dict)
                locals_dict = locals()
                twc_substrate = eval(_cache['ALL', 'twc_substrate']['value'], {'np': np}, locals_dict) \
                                * adj_factor_sub * learn
                twc_washcoat = eval(_cache['ALL', 'twc_washcoat']['value'], {'np': np}, locals_dict) \
                               * adj_factor_wash * learn
                twc_canning = eval(_cache['ALL', 'twc_canning']['value'], {'np': np}, locals_dict) \
                              * adj_factor_can * learn
                twc_pgm = eval(_cache['ALL', 'twc_pgm']['value'], {'np': np}, locals_dict)
                twc_cost = (twc_substrate + twc_washcoat + twc_canning + twc_pgm)

                # gpf cost
                if omega_globals.options.powertrain_cost_with_gpf:
                    adj_factor_gpf = _cache['ALL', 'gpf_cost']['dollar_adjustment']
                    locals_dict = locals()
                    gpf_cost = eval(_cache['ALL', 'gpf_cost']['value'], {'np': np}, locals_dict) \
                               * adj_factor_gpf * learn

            # diesel exhaust aftertreatment cost
            elif diesel_flag:
                adj_factor_diesel_eas = _cache['ALL', 'diesel_aftertreatment_system']['dollar_adjustment']
                locals_dict = locals()
                diesel_eas_cost = \
                    eval(_cache['ALL', 'diesel_aftertreatment_system']['value'], {'np': np}, locals_dict) * \
                    adj_factor_diesel_eas * learn

            eas_cost = twc_cost + gpf_cost + diesel_eas_cost

        if powertrain_type in ['MHEV', 'HEV', 'PHEV', 'BEV']:

            if powertrain_type == 'PHEV' or powertrain_type == 'BEV':
                learn = learning_factor_pev

            KWH = pkg_info['battery_kwh']
            KW = pkg_info['total_emachine_kw']

            if powertrain_type == 'HEV':
                obc_kw = 0
            elif powertrain_type == 'MHEV':
                obc_kw = 0
            elif powertrain_type == 'PHEV':
                obc_kw = 1.9
                if KWH < 10:
                    obc_kw = 1.1
                elif KWH < 7:
                    obc_kw = 0.7
            else:
                obc_kw = 19
                if KWH < 100:
                    obc_kw = 11
                elif KWH < 70:
                    obc_kw = 7

            dcdc_converter_kw = eval(_cache[powertrain_type, 'DCDC_converter_kW']['value'], {'np': np}, locals_dict)

            OBC_AND_DCDC_CONVERTER_KW = dcdc_converter_kw + obc_kw

            locals_dict = locals()

            # battery cost
            if powertrain_type in ['MHEV', 'HEV', 'PHEV', 'BEV']:
                adj_factor = _cache[powertrain_type, 'battery']['dollar_adjustment']
                battery_cost = eval(_cache[powertrain_type, 'battery']['value'], {'np': np}, locals_dict) \
                               * adj_factor * learning_pev_battery_scaling_factor

            if powertrain_type in ['BEV', 'PHEV'] and KWH >= 7 and omega_globals.options.powertrain_cost_with_ira:
                battery_offset_dict = eval(_cache[powertrain_type, 'battery_offset']['value'], {'np': np}, locals_dict)
                battery_offset_min_year = min(battery_offset_dict['dollars_per_kwh'].keys())
                battery_offset_max_year = max(battery_offset_dict['dollars_per_kwh'].keys())
                if battery_offset_min_year <= model_year <= battery_offset_max_year:
                    battery_offset = battery_offset_dict['dollars_per_kwh'][model_year] * KWH
                    battery_cost += battery_offset

            # electrified powertrain cost
            adj_factor = _cache[powertrain_type, f'motor_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'motor_{tractive_motor}']['quantity']
            motor_cost = eval(_cache[powertrain_type, f'motor_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                         * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'inverter_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'inverter_{tractive_motor}']['quantity']
            inverter_cost = \
                eval(_cache[powertrain_type, f'inverter_{tractive_motor}']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['quantity']
            induction_motor_cost = \
                eval(_cache[powertrain_type, f'induction_motor_{tractive_motor}']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['quantity']
            induction_inverter_cost = \
                eval(_cache[powertrain_type, f'induction_inverter_{tractive_motor}']['value'],
                     {'np': np}, locals_dict) * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'OBC_and_DCDC_converter']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'OBC_and_DCDC_converter']['quantity']
            obc_and_dcdc_converter_cost = \
                eval(_cache[powertrain_type, 'OBC_and_DCDC_converter']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'HV_orange_cables']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'HV_orange_cables']['quantity']
            hv_orange_cables_cost = \
                eval(_cache[powertrain_type, 'HV_orange_cables']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['quantity']
            single_speed_gearbox_cost = \
                eval(_cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['value'],
                     {'np': np}, locals_dict) * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['quantity']
            powertrain_cooling_loop_cost = \
                eval(_cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['value'],
                     {'np': np}, locals_dict) * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'charging_cord_kit']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'charging_cord_kit']['quantity']
            charging_cord_kit_cost = \
                eval(_cache[powertrain_type, 'charging_cord_kit']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'DC_fast_charge_circuitry']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'DC_fast_charge_circuitry']['quantity']
            dc_fast_charge_circuitry_cost = \
                eval(_cache[powertrain_type, 'DC_fast_charge_circuitry']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'power_management_and_distribution']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'power_management_and_distribution']['quantity']
            power_management_and_distribution_cost = \
                eval(_cache[powertrain_type, 'power_management_and_distribution']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'brake_sensors_actuators']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'brake_sensors_actuators']['quantity']
            brake_sensors_actuators_cost = \
                eval(_cache[powertrain_type, 'brake_sensors_actuators']['value'], {'np': np}, locals_dict) *\
                adj_factor * learn * quantity

            adj_factor = \
                _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['quantity']
            additional_pair_of_half_shafts_cost = \
                eval(_cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['value'],
                     {'np': np}, locals_dict) * adj_factor * learn * quantity

            emachine_cost = motor_cost + induction_motor_cost

            electrified_driveline_cost = inverter_cost + induction_inverter_cost \
                                         + obc_and_dcdc_converter_cost + hv_orange_cables_cost \
                                         + single_speed_gearbox_cost \
                                         + charging_cord_kit_cost + dc_fast_charge_circuitry_cost \
                                         + power_management_and_distribution_cost + brake_sensors_actuators_cost \
                                         + additional_pair_of_half_shafts_cost

        # ac leakage cost
        adj_factor = _cache['ALL', 'ac_leakage']['dollar_adjustment']
        ac_leakage_cost = eval(_cache['ALL', 'ac_leakage']['value'], {'np': np}, locals_dict) \
                          * adj_factor * learning_factor_ice

        # ac efficiency cost
        adj_factor = _cache['ALL', 'ac_efficiency']['dollar_adjustment']
        ac_efficiency_cost = eval(_cache['ALL', 'ac_efficiency']['value'], {'np': np}, locals_dict) \
                             * adj_factor * learning_factor_ice

        # low voltage battery and hvac
        adj_factor = _cache[powertrain_type, 'LV_battery']['dollar_adjustment']
        quantity = _cache[powertrain_type, 'LV_battery']['quantity']
        lv_battery_cost = eval(_cache[powertrain_type, 'LV_battery']['value'], {'np': np}, locals_dict) \
                          * adj_factor * learning_factor_ice * quantity

        adj_factor = _cache[powertrain_type, 'HVAC']['dollar_adjustment']
        quantity = _cache[powertrain_type, 'HVAC']['quantity']
        hvac_cost = eval(_cache[powertrain_type, 'HVAC']['value'], {'np': np}, locals_dict) \
                    * adj_factor * learn * quantity

        if powertrain_type == 'BEV':
            adj_factor = _cache[powertrain_type, pkg_info['drive_system']]['dollar_adjustment']
            drive_system_cost = eval(_cache[powertrain_type, pkg_info['drive_system']]['value'], {'np': np},
                                     locals_dict) * adj_factor * learning_factor_ice
        else:
            adj_factor = _cache['ICE', pkg_info['drive_system']]['dollar_adjustment']
            drive_system_cost = eval(_cache['ICE', pkg_info['drive_system']]['value'], {'np': np},
                                     locals_dict) * adj_factor * learning_factor_ice

        diesel_engine_cost_scaler = 1
        if diesel_flag:
            diesel_engine_cost_scaler = \
                eval(_cache['ALL', 'diesel_engine_cost_scaler']['value'], {'np': np}, locals_dict)

        engine_cost = (cyl_cost + liter_cost) * turb_scaler * diesel_engine_cost_scaler \
                      + deac_pd_cost + deac_fc_cost \
                      + cegr_cost + atk2_cost + gdi_cost \
                      + turb12_cost + turb11_cost \
                      + twc_cost + gpf_cost + diesel_eas_cost

        driveline_cost = drive_system_cost + trans_cost \
                         + high_eff_alt_cost + start_stop_cost \
                         + ac_leakage_cost + ac_efficiency_cost \
                         + lv_battery_cost + powertrain_cooling_loop_cost + hvac_cost

        powertrain_cost = engine_cost + driveline_cost + emachine_cost + electrified_driveline_cost + battery_cost
        if omega_globals.options.powertrain_cost_tracker:
            update_dict = {
                'vehicle_id': vehicle.vehicle_id,
                'base_year_vehicle_id': vehicle.base_year_vehicle_id,
                'name': vehicle.name,
                'manufacturer_id': vehicle.manufacturer_id,
                'compliance_id': vehicle.compliance_id,
                'model_year': model_year,
                'reg_class_id': reg_class_id,
                'market_class_id': market_class_id,
                'base_year_cert_fuel_id': base_year_cert_fuel_id,
                'body_style': body_style,
                'drive_system': vehicle.drive_system,
                'powertrain_type': powertrain_type,
                'cost_curve_class': cost_curve_class,
                'onroad_charge_depleting_range_mi': vehicle.onroad_charge_depleting_range_mi,
                'footprint_ft2': pkg_info['footprint_ft2'],
                'learning_factor_ice': learning_factor_ice,
                'learning_factor_pev': learning_factor_pev,
                'learning_pev_battery_scaling_factor': learning_pev_battery_scaling_factor,
                'trans': trans,
                'CYL': CYL,
                'engine_config': 'n/a',
                'LITERS': LITERS,
                'twc_substrate': twc_substrate,
                'twc_washcoat': twc_washcoat,
                'twc_canning': twc_canning,
                'twc_pgm': twc_pgm,
                'twc_cost': twc_cost,
                'gpf_cost': gpf_cost,
                'diesel_eas_cost': diesel_eas_cost,
                'eas_cost': eas_cost,
                'engine_block_cost': (cyl_cost + liter_cost) * turb_scaler * diesel_engine_cost_scaler,
                'cegr_cost': cegr_cost,
                'gdi_cost': gdi_cost,
                'turb_cost': turb11_cost + turb12_cost,
                'deac_pd_cost': deac_pd_cost,
                'deac_fc_cost': deac_fc_cost,
                'atk2_cost': atk2_cost,
                'fuel_storage_cost': 'n/a',
                'non_eas_exhaust_cost': 'n/a',
                'exhaust_cost': 'n/a',
                'lv_battery_cost': lv_battery_cost,
                'start_stop_cost': start_stop_cost,
                'drive_system_cost': drive_system_cost,
                'trans_cost': trans_cost,
                'high_eff_alternator_cost': high_eff_alt_cost,
                'hvac_cost': hvac_cost,
                'powertrain_cooling_cost': powertrain_cooling_loop_cost,
                'lv_harness_cost': 'n/a',
                'hv_harness_cost': hv_orange_cables_cost,
                'DC_DC_converter_cost': obc_and_dcdc_converter_cost,
                'dc_fast_charge_circuitry_cost': dc_fast_charge_circuitry_cost,
                'external_charge_device': charging_cord_kit_cost,
                'kW_DU': KW,
                'kW_FDU': KW_FDU,
                'kW_RDU': KW_RDU,
                'kW_P2': KW_P2,
                'kW_P4': KW_P4,
                'kW_OBC': obc_kw,
                'kWh_battery': KWH,
                'e_motor_cost': motor_cost,
                'induction_motor_cost': induction_motor_cost,
                'gearbox_cost': single_speed_gearbox_cost,
                'inverter_cost': inverter_cost,
                'induction_inverter_cost': induction_inverter_cost,
                'power_management_and_distribution_cost': power_management_and_distribution_cost,
                'brake_sensors_actuators_cost': brake_sensors_actuators_cost,
                'additional_pair_of_half_shafts_cost': additional_pair_of_half_shafts_cost,
                'battery_cost': battery_cost,
                'battery_offset': battery_offset,
                'ac_leakage_cost': ac_leakage_cost,
                'ac_efficiency_cost': ac_efficiency_cost,
                'engine_cost': engine_cost,
                'driveline_cost': driveline_cost,
                'e_machine_cost': emachine_cost,
                'electrified_driveline_cost': electrified_driveline_cost,
                'powertrain_cost': powertrain_cost,
            }
            if update_tracker:
                PowertrainCost.cost_tracker[vehicle.vehicle_id, model_year] = update_dict

        return engine_cost, driveline_cost, emachine_cost, battery_cost, electrified_driveline_cost

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        _cache.clear()
        PowertrainCost.cost_tracker = {}

        if verbose:
            omega_log.logwrite('\nInitializing PowertrainCost from %s...' % filename)
        input_template_name = __name__

        input_template_version = 0.1
        input_template_columns = {
            'powertrain_type',
            'item',
            'value',
            'quantity',
            'dollar_basis',
        }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:

                df['value'] = df['value'] \
                    .apply(lambda x: str.replace(x, 'max(', 'np.maximum(').replace('min(', 'np.minimum('))

                cost_keys = zip(df['powertrain_type'], df['item'])

                for cost_key in cost_keys:

                    _cache[cost_key] = {}
                    powertrain_type, item = cost_key

                    cost_info = df[(df['powertrain_type'] == powertrain_type) & (df['item'] == item)].iloc[0]

                    if cost_info['quantity'] >= 1:
                        quantity = cost_info['quantity']
                    else:
                        quantity = 0

                    _cache[cost_key] = {'value': {},
                                        'quantity': quantity,
                                        'dollar_adjustment': 1}

                    if cost_info['dollar_basis'] > 0:
                        adj_factor = ImplicitPriceDeflators.dollar_adjustment_factor(int(cost_info['dollar_basis']))
                        _cache[cost_key]['dollar_adjustment'] = adj_factor

                    _cache[cost_key]['value'] = compile(str(cost_info['value']), '<string>', 'eval')

        return template_errors


def get_trans(pkg_info):
    """
    Get the transmission code for the given powertrain package.

    Args:
        pkg_info (Series): powertain package information

    Returns:
        The transmission code for the given data.

    """
    trans = ''
    flags = 0
    gears = 0

    if pkg_info['trx10']:
        trans = 'TRX10'
        flags += 1
        gears = 5
    elif pkg_info['trx11']:
        trans = 'TRX11'
        flags += 1
        gears = 6
    elif pkg_info['trx12']:
        trans = 'TRX12'
        flags += 1
        gears = 6
    elif pkg_info['trx21']:
        trans = 'TRX21'
        flags += 1
        gears = 8
    elif pkg_info['trx22']:
        trans = 'TRX22'
        flags += 1
        gears = 8
    elif pkg_info['ecvt']:
        trans = 'TRXCV'
        flags += 1

    if flags == 0:
        raise Exception('%s has no transmission tech flag' % pkg_info.vehicle_name)

    if flags > 1:
        raise Exception('%s has multiple transmission tech flags' % pkg_info.vehicle_name)

    return trans, gears
