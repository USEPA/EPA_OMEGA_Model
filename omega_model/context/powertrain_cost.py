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

        if omega_globals.options.powertrain_cost_fev:
            return PowertrainCost.calc_cost_fev(vehicle, pkg_info, powertrain_type, update_tracker)

        else:
            return PowertrainCost.calc_cost_nprm(vehicle, pkg_info, powertrain_type, update_tracker)

    @staticmethod
    def calc_cost_nprm(vehicle, pkg_info, powertrain_type, update_tracker=False):
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
        if (market_class_id.__contains__('non_hauling') and vehicle.drive_system < 4) or powertrain_type == 'HEV':
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
    def calc_cost_fev(vehicle, pkg_info, powertrain_type, update_tracker=False):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
            vehicle (Vehicle): the Vehicle for which to calculate costs
            pkg_info (Series): the necessary information for developing cost estimates.
            update_tracker (bool): update cost tracking dict if ``True``

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        update_dict = {}
        locals_dict = locals()

        market_class_id, model_year, base_year_cert_fuel_id, reg_class_id, drive_system, body_style = \
            vehicle.market_class_id, vehicle.model_year, vehicle.base_year_cert_fuel_id, vehicle.reg_class_id, \
                vehicle.drive_system, vehicle.body_style

        learning_pev_battery_scaling_factor, learning_factor_ice, learning_factor_pev, locals_dict = \
            get_learning_factors(vehicle, locals_dict)

        KWH = KW = KW_OBC = KW_DU = KW_FDU = KW_RDU = KW_P2 = KW_P4 = 0
        trans = CYL = engine_config = LITERS = powertrain_subtype = None
        twc_substrate= twc_washcoat = twc_canning = twc_pgm = twc_cost = gpf_cost = diesel_eas_cost = eas_cost = 0
        engine_cost = engine_block_cost = cegr_cost = gdi_cost = turb_cost = deac_pd_cost = deac_fc_cost = atk2_cost = 0
        fuel_storage_cost = non_eas_exhaust_cost = exhaust_cost = 0
        lv_battery_cost = start_stop_cost = trans_cost = high_eff_alt_cost = lv_harness_cost = 0
        powertrain_cooling_cost = hvac_cost = 0
        hv_harness_cost = dc_dc_converter_cost = charge_cord_cost = 0
        motor_cost = gearbox_cost = inverter_cost = battery_cost = battery_offset = 0
        ac_leakage_cost = ac_efficiency_cost = 0
        powertrain_cost = engine_cost = driveline_cost = e_machine_cost = electrified_driveline_cost = 0

        cost_curve_class = pkg_info['cost_curve_class']
        if powertrain_type in ['MHEV', 'HEV', 'PHEV']:
            powertrain_subtype = get_powertrain_subtype(cost_curve_class)

        if powertrain_type in ['BEV', 'MHEV', 'HEV', 'PHEV']:
            KW_OBC = get_obc_power(pkg_info, powertrain_type)
            KWH = pkg_info['battery_kwh']
            KW, KW_DU, KW_FDU, KW_RDU, KW_P0, KW_P2, KW_P4 = get_motor_power(
                locals_dict, pkg_info, powertrain_type, powertrain_subtype, drive_system
            )

        MARKUP_ICE, MARKUP_HEV, MARKUP_PHEV, MARKUP_BEV = get_markups(locals_dict)

        locals_dict = locals()

        gasoline_flag = diesel_flag = False
        if powertrain_type in ['ICE', 'MHEV', 'HEV', 'PHEV']:

            # set some needed attributes
            gasoline_flag = True
            if 'diesel' in base_year_cert_fuel_id:
                diesel_flag, gasoline_flag = True, False
            trans, GEARS = get_trans(pkg_info)
            CYL, LITERS, engine_config = get_engine_deets(pkg_info)

            locals_dict = locals()

            # Engine System Costs ______________________________________________________________________________________
            # exhaust and exhaust aftertreatment system (eas)
            eas_cost = 0
            if gasoline_flag:
                twc_substrate, twc_washcoat, twc_canning, twc_pgm, twc_cost, gpf_cost = \
                    calc_gasoline_eas_cost(locals_dict, learning_factor_ice)
                eas_cost = twc_cost + gpf_cost
            elif diesel_flag:
                diesel_eas_cost = calc_diesel_eas_cost(locals_dict, learning_factor_ice)
                eas_cost = diesel_eas_cost

            non_eas_exhaust_cost = \
                calc_non_eas_exhaust_cost(locals_dict, learning_factor_ice, powertrain_type, engine_config, body_style)

            exhaust_cost = eas_cost + non_eas_exhaust_cost

            locals_dict = locals()

            # engine block and tech
            engine_block_cost, cegr_cost, gdi_cost, turb_cost, deac_pd_cost, deac_fc_cost, atk2_cost = \
                calc_engine_cost(
                    locals_dict, learning_factor_ice, pkg_info, powertrain_type, engine_config, body_style, diesel_flag
                )

            # fuel storage
            fuel_storage_cost = calc_fuel_storage_cost(locals_dict, learning_factor_ice, powertrain_type, body_style)

            # Driveline System Costs ___________________________________________________________________________________
            trans_cost = calc_trans_cost(
                locals_dict, learning_factor_ice, powertrain_type, powertrain_subtype, drive_system, body_style
            )

            inverter_cost = 0
            if powertrain_type in ['MHEV', 'HEV', 'PHEV'] and drive_system == 'AWD':
                inverter_cost = calc_inverter_cost(
                    locals_dict, learning_factor_pev, powertrain_type, powertrain_subtype=powertrain_subtype
                )
            gearbox_cost = 0
            if powertrain_type in ['MHEV', 'HEV', 'PHEV'] and drive_system == 'AWD':
                gearbox_cost = calc_gearbox_cost(
                    locals_dict, learning_factor_pev, powertrain_type, body_style, powertrain_subtype=powertrain_subtype
                )

            lv_battery_cost = calc_lv_battery_cost(locals_dict, learning_factor_ice, powertrain_type)

            start_stop_cost = high_eff_alt_cost = 0
            if powertrain_type == 'ICE':
                start_stop_cost = calc_start_stop_cost(locals_dict, learning_factor_ice, pkg_info)
                high_eff_alt_cost = calc_high_efficiency_alternator(locals_dict, learning_factor_ice, pkg_info)

            powertrain_cooling_cost = calc_powertrain_cooling_cost(
                locals_dict, learning_factor_ice, powertrain_type, drive_system, engine_config, body_style
            )
            hvac_cost = calc_hvac_cost(locals_dict, learning_factor_ice, powertrain_type)

            ac_leakage_cost, ac_efficiency_cost = calc_air_conditioning_costs(locals_dict, learning_factor_ice)

            lv_harness_cost = \
                calc_lv_harness_cost(locals_dict, learning_factor_ice, powertrain_type, drive_system, body_style)

            hv_harness_cost = dc_dc_converter_cost = 0
            if powertrain_type in ['MHEV', 'HEV', 'PHEV']:
                hv_harness_cost = \
                    calc_hv_harness_cost(locals_dict, learning_factor_pev, powertrain_type, drive_system, body_style)
                dc_dc_converter_cost = calc_dc_dc_converter_cost(locals_dict, learning_factor_pev, powertrain_type)

            charge_cord_cost = 0
            if powertrain_type == 'PHEV':
                charge_cord_cost = calc_charge_cord_cost(locals_dict, learning_factor_pev, powertrain_type)

            battery_cost = battery_offset = 0
            if powertrain_type in ['MHEV', 'HEV', 'PHEV']:
                battery_cost = calc_battery_cost(locals_dict, learning_pev_battery_scaling_factor, powertrain_type)

                if powertrain_type == 'PHEV' and omega_globals.options.powertrain_cost_with_ira:
                    battery_offset = calc_battery_offset(locals_dict, vehicle, powertrain_type, KWH)

            battery_cost += battery_offset

            engine_cost = sum([
                exhaust_cost, engine_block_cost, cegr_cost, gdi_cost, turb_cost, deac_pd_cost, deac_fc_cost, atk2_cost,
                fuel_storage_cost
            ])

            driveline_cost = \
                lv_battery_cost + lv_harness_cost + \
                trans_cost + start_stop_cost + high_eff_alt_cost + \
                powertrain_cooling_cost + hvac_cost + ac_leakage_cost + ac_efficiency_cost

            e_machine_cost = motor_cost

            electrified_driveline_cost = dc_dc_converter_cost + hv_harness_cost + charge_cord_cost + \
                                         inverter_cost + gearbox_cost

        if powertrain_type == 'BEV':

            engine_cost = 0

            locals_dict = locals()

            # Driveline System Costs ___________________________________________________________________________________
            motor_cost = 0
            motor_cost = calc_motor_cost(
                locals_dict, learning_factor_pev, powertrain_type, drive_system=drive_system
            )
            inverter_cost = calc_inverter_cost(
                locals_dict, learning_factor_pev, powertrain_type, drive_system=drive_system
            )
            gearbox_cost = calc_gearbox_cost(
                locals_dict, learning_factor_pev, powertrain_type, body_style, drive_system=drive_system
            )
            lv_battery_cost = calc_lv_battery_cost(locals_dict, learning_factor_ice, powertrain_type)

            powertrain_cooling_cost = calc_powertrain_cooling_cost(
                locals_dict, learning_factor_ice, powertrain_type, drive_system, '-', body_style
            )
            hvac_cost = calc_hvac_cost(locals_dict, learning_factor_ice, powertrain_type)

            ac_leakage_cost, ac_efficiency_cost = calc_air_conditioning_costs(locals_dict, learning_factor_ice)

            lv_harness_cost = \
                calc_lv_harness_cost(locals_dict, learning_factor_ice, powertrain_type, drive_system, body_style)

            hv_harness_cost = dc_dc_converter_cost = 0
            hv_harness_cost = \
                calc_hv_harness_cost(locals_dict, learning_factor_pev, powertrain_type, drive_system, body_style)
            dc_dc_converter_cost = calc_dc_dc_converter_cost(locals_dict, learning_factor_pev, powertrain_type)

            charge_cord_cost = calc_charge_cord_cost(locals_dict, learning_factor_pev, powertrain_type)

            battery_cost = calc_battery_cost(locals_dict, learning_pev_battery_scaling_factor, powertrain_type)

            battery_offset = 0
            if omega_globals.options.powertrain_cost_with_ira:
                battery_offset = calc_battery_offset(locals_dict, vehicle, powertrain_type, KWH)

            battery_cost += battery_offset

            driveline_cost = \
                lv_battery_cost + lv_harness_cost + \
                powertrain_cooling_cost + hvac_cost + ac_leakage_cost + ac_efficiency_cost

            e_machine_cost = motor_cost

            electrified_driveline_cost = dc_dc_converter_cost + hv_harness_cost + charge_cord_cost + \
                                         inverter_cost + gearbox_cost

        powertrain_cost = engine_cost + driveline_cost + e_machine_cost + electrified_driveline_cost + battery_cost

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
                'engine_config': engine_config,
                'LITERS': LITERS,
                'twc_substrate': twc_substrate,
                'twc_washcoat': twc_washcoat,
                'twc_canning': twc_canning,
                'twc_pgm': twc_pgm,
                'twc_cost': twc_cost,
                'gpf_cost': gpf_cost,
                'diesel_eas_cost': diesel_eas_cost,
                'eas_cost': eas_cost,
                'engine_block_cost': engine_block_cost,
                'cegr_cost': cegr_cost,
                'gdi_cost': gdi_cost,
                'turb_cost': turb_cost,
                'deac_pd_cost': deac_pd_cost,
                'deac_fc_cost': deac_fc_cost,
                'atk2_cost': atk2_cost,
                'fuel_storage_cost': fuel_storage_cost,
                'non_eas_exhaust_cost': non_eas_exhaust_cost,
                'exhaust_cost': exhaust_cost,
                'lv_battery_cost': lv_battery_cost,
                'drive_system_cost': 'n/a',
                'start_stop_cost': start_stop_cost,
                'trans_cost': trans_cost,
                'high_eff_alternator_cost': high_eff_alt_cost,
                'hvac_cost': hvac_cost,
                'powertrain_cooling_cost': powertrain_cooling_cost,
                'lv_harness_cost': lv_harness_cost,
                'hv_harness_cost': hv_harness_cost,
                'DC_DC_converter_cost': dc_dc_converter_cost,
                'dc_fast_charge_circuitry_cost': 'n/a',
                'external_charge_device': charge_cord_cost,
                'kW_total': KW,
                'kW_DU': KW_DU,
                'kW_FDU': KW_FDU,
                'kW_RDU': KW_RDU,
                'kW_P2': KW_P2,
                'kW_P4': KW_P4,
                'kW_OBC': KW_OBC,
                'kWh_battery': KWH,
                'e_motor_cost': motor_cost,
                'induction_motor_cost': 'n/a',
                'gearbox_cost': gearbox_cost,
                'inverter_cost': inverter_cost,
                'induction_inverter_cost': 'n/a',
                'power_management_and_distribution_cost': 'n/a',
                'brake_sensors_actuators_cost': 'n/a',
                'additional_pair_of_half_shafts_cost': 'n/a',
                'battery_cost': battery_cost,
                'battery_offset': battery_offset,
                'ac_leakage_cost': ac_leakage_cost,
                'ac_efficiency_cost': ac_efficiency_cost,
                'engine_cost': engine_cost,
                'driveline_cost': driveline_cost,
                'e_machine_cost': e_machine_cost,
                'electrified_driveline_cost': electrified_driveline_cost,
                'powertrain_cost': powertrain_cost,
            }
            if update_tracker:
                PowertrainCost.cost_tracker[vehicle.vehicle_id, model_year] = update_dict

        return engine_cost, driveline_cost, e_machine_cost, battery_cost, electrified_driveline_cost

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
        input_template_name = 'powertrain_cost'

        if omega_globals.options.powertrain_cost_fev:
            input_template_version = 0.21
            input_template_columns = {
                'powertrain_type',
                'powertrain_subtype',
                'system',
                'subsystem',
                'drive_system',
                'engine_configuration',
                'body_style',
                'value',
                'dollar_basis',
            }
        else:
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

                if omega_globals.options.powertrain_cost_fev:
                    cost_keys = pd.Series(zip(
                        df['powertrain_type'],
                        df['powertrain_subtype'],
                        df['system'],
                        df['subsystem'],
                        df['drive_system'],
                        df['engine_configuration'],
                        df['body_style'],
                    ))
                    df.insert(0, 'cost_key', cost_keys)

                    for cost_key in cost_keys:
                        _cache[cost_key] = {}
                        cost_info = df[df['cost_key'] == cost_key].iloc[0]

                        _cache[cost_key] = {'value': {},
                                            'dollar_adjustment': 1}

                        if cost_info['dollar_basis'] > 0:
                            adj_factor = ImplicitPriceDeflators.dollar_adjustment_factor(int(cost_info['dollar_basis']))
                            _cache[cost_key]['dollar_adjustment'] = adj_factor

                        _cache[cost_key]['value'] = compile(str(cost_info['value']), '<string>', 'eval')

                else:

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


def get_learning_factors(v, locals_dict):
    """
    Get learning factors for use in estimating powertrain costs.

    Args:
        v (Vehicle): the Vehicle object
        locals_dict (dict): local attributes

    Returns:
        Learning factors for ICE, PEV, and high-voltage batteries for use in calculating powertrain costs; locals_dict
        is also returned with updated local attributes.

    """
    if v.model_year <= 2025 or v.global_cumulative_battery_GWh['total'] == 0 \
            or v.global_cumulative_battery_GWh[v.model_year - 1] == 0:
        learning_pev_battery_scaling_factor = 1
    else:
        cost_key = ('PEV', '-', 'battery_GWh_learning_curve', '-', '-', '-', '-')
        if v.reg_class_id != 'mediumduty':
            cumulative_gwh = v.global_cumulative_battery_GWh[v.model_year - 1]
            locals_dict.update({'CUMULATIVE_GWH': cumulative_gwh})
            learning_pev_battery_scaling_factor = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)

            while learning_pev_battery_scaling_factor > 1:
                cumulative_gwh *= 1.1
                locals_dict.update({'CUMULATIVE_GWH': cumulative_gwh})
                learning_pev_battery_scaling_factor = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)

        else:
            ld_dict_key = ('PEV', '-', 'cumulative_GWh_LD_noIRA', '-', '-', '-', '-')
            cumulative_GWh_ld_dict = eval(_cache[ld_dict_key]['value'], {'np': np}, locals_dict)

            if v.model_year - 1 in cumulative_GWh_ld_dict['GWh']:
                gwh = cumulative_GWh_ld_dict['GWh'][v.model_year - 1]
                cumulative_gwh = v.global_cumulative_battery_GWh[v.model_year - 1]
                locals_dict.update({'CUMULATIVE_GWH': cumulative_gwh + gwh})
                learning_pev_battery_scaling_factor = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)

                while learning_pev_battery_scaling_factor > 1:
                    cumulative_gwh *= 1.1
                    locals_dict.update({'CUMULATIVE_GWH': cumulative_gwh})
                    learning_pev_battery_scaling_factor = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)

            else:
                year = max(yr for yr in cumulative_GWh_ld_dict['GWh'])
                gwh = cumulative_GWh_ld_dict['GWh'][year]
                cumulative_gwh = v.global_cumulative_battery_GWh[v.model_year - 1]
                locals_dict.update({'CUMULATIVE_GWH': cumulative_gwh + gwh})
                learning_pev_battery_scaling_factor = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)

    # non-battery learning
    learning_rate = eval(_cache['ALL', '-', 'learning_rate', '-', '-', '-', '-']['value'], {'np': np}, locals_dict)
    learning_start = eval(_cache['ALL', '-', 'learning_start', '-', '-', '-', '-']['value'], {'np': np}, locals_dict)
    legacy_sales_scaler_ice = \
        eval(_cache['ICE', '-', 'legacy_sales_learning_scaler', '-', '-', '-', '-']['value'], {'np': np}, locals_dict)
    legacy_sales_scaler_pev = \
        eval(_cache['PEV', '-', 'legacy_sales_learning_scaler', '-', '-', '-', '-']['value'], {'np': np}, locals_dict)
    sales_scaler_ice = eval(_cache['ICE', '-', 'sales_scaler', '-', '-', '-', '-']['value'], {'np': np}, locals_dict)
    sales_scaler_pev = eval(_cache['PEV', '-', 'sales_scaler', '-', '-', '-', '-']['value'], {'np': np}, locals_dict)
    cumulative_sales_ice = abs(sales_scaler_ice * (v.model_year - learning_start))
    cumulative_sales_pev = abs(sales_scaler_pev * (v.model_year - learning_start))
    learning_factor_ice = \
        ((cumulative_sales_ice + legacy_sales_scaler_ice) / legacy_sales_scaler_ice) ** learning_rate
    learning_factor_pev = \
        ((cumulative_sales_pev + legacy_sales_scaler_pev) / legacy_sales_scaler_pev) ** learning_rate
    if v.model_year < learning_start:
        learning_factor_ice = 1 / learning_factor_ice
        learning_factor_pev = 1 / learning_factor_pev

    return learning_pev_battery_scaling_factor, learning_factor_ice, learning_factor_pev, locals_dict


def get_markups(locals_dict):
    """
    Get markups for estimating indirect costs.

    Args:
        locals_dict (dict): local attributes

    Returns:
        A list of markup factors for use with ICE, MHEV, HEV, PHEV and BEV technologies

    """
    markup_list = []
    for ptrain in ['ICE', 'HEV', 'PHEV', 'BEV']:
        markup_list.append(eval(_cache[ptrain, '-', 'markup', '-', '-', '-', '-']['value'], {'np': np}, locals_dict))

    return markup_list


def get_obc_power(pkg_info, powertrain_type):
    """
    Get the charging power of the onboard charger, if equipped.

    Args:
        pkg_info (Series): the necessary information for developing cost estimates
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'

    Returns:
        The charging power of the onboard charger

    """
    kw_obc = 0
    kwh = pkg_info['battery_kwh']
    if powertrain_type in ['BEV', 'PHEV']:
        kw_obc = 19
        if kwh < 100:
            kw_obc = 11

    return kw_obc


def get_motor_power(locals_dict, pkg_info, powertrain_type, powertrain_subtype, drive_system):
    """
    Get the electric drive motor-power, if equipped, of the given package.

    Args:
        locals_dict (dict): local attributes
        pkg_info (Series): the necessary information for developing cost estimates
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        powertrain_subtype (str): e.g., 'P0', 'P2', 'PS'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive

    Returns:
        The motive power of the electric drive motor(s) whether it be the primary drive unit, the front and rear drive
        units or the P2 and P4 drive units, depending on the package architecture

    """
    kw = pkg_info['total_emachine_kw']
    kw_fdu = kw_rdu = kw_du = kw_p0 = kw_p2 = kw_p4 = 0

    if powertrain_type == 'BEV':
        if drive_system == 'AWD':
            share_key = (powertrain_type, '-', 'KW_RDU_share', 'E_Motor', '-', '-', '-')
            share = eval(_cache[share_key]['value'], {'np': np}, locals_dict)
            kw_fdu, kw_rdu = (1 - share) * kw, share * kw
        else:
            kw_du = kw
    elif powertrain_subtype in ['P2', 'PS']:
        if drive_system == 'AWD':
            share_key = (powertrain_type, '-', 'KW_P2_share', 'E_Motor', '-', '-', '-')
            share = eval(_cache[share_key]['value'], {'np': np}, locals_dict)
            kw_p4, kw_p2 = (1 - share) * kw, share * kw
        else:
            kw_p2 = kw
    elif powertrain_subtype == 'P0':
        if drive_system == 'AWD':
            share_key = (powertrain_type, '-', 'KW_P0_share', 'E_Motor', '-', '-', '-')
            share = eval(_cache[share_key]['value'], {'np': np}, locals_dict)
            kw_p4, kw_p0 = (1 - share) * kw, share * kw
        else:
            kw_p0 = kw
    else:
        pass

    return kw, kw_du, kw_fdu, kw_rdu, kw_p0, kw_p2, kw_p4


def get_powertrain_subtype(cost_curve_class):
    """

    Args:
        cost_curve_class (str): the cost curve class of the package

    Returns:
        The powertrain subtype, if applicable

    """
    if 'P0_' in cost_curve_class:
        return 'P0'
    elif 'P2_' in cost_curve_class:
        return 'P2'
    elif 'PS_' in cost_curve_class:
        return 'PS'
    else:
        return '-'


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


def get_engine_deets(pkg_info):
    """
    Get engine details, if equipped, for the given powertrain package.

    Args:
        pkg_info (Series): powertain package information

    Returns:
        The number of cylinders, the displacement (liters) and 'I' or 'V' configuration of the engine block.

    """
    CYL = pkg_info['engine_cylinders']
    engine_config = 'I'
    if pkg_info['engine_cylinders'] > 5:
        engine_config = 'V'
    LITERS = pkg_info['engine_displacement_liters']

    return CYL, LITERS, engine_config


def calc_gasoline_eas_cost(locals_dict, learning_factor):
    """
    Calculate exhaust aftertreatment system (eas) costs for gasoline-fueled engines.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use

    Returns:
        The three-way catalyst (twc) substrate, washcoat, canning, platinum group metal (pgm) and total costs along with
        the gasoline particulate filter (gpf) cost

    """
    pt_cost_key = ('ALL', '-', 'Exhaust', 'pt_dollars_per_oz', '-', '-', '-')
    pd_cost_key = ('ALL', '-', 'Exhaust', 'pd_dollars_per_oz', '-', '-', '-')
    rh_cost_key = ('ALL', '-', 'Exhaust', 'rh_dollars_per_oz', '-', '-', '-')
    pt_load_key = ('ALL', '-', 'Exhaust', 'twc_pt_grams_per_liter', '-', '-', '-')
    pd_load_key = ('ALL', '-', 'Exhaust', 'twc_pd_grams_per_liter', '-', '-', '-')
    rh_load_key = ('ALL', '-', 'Exhaust', 'twc_rh_grams_per_liter', '-', '-', '-')
    PT_USD_PER_OZ = eval(_cache[pt_cost_key]['value'], {'np': np}, locals_dict)
    PD_USD_PER_OZ = eval(_cache[pd_cost_key]['value'], {'np': np}, locals_dict)
    RH_USD_PER_OZ = eval(_cache[rh_cost_key]['value'], {'np': np}, locals_dict)
    PT_GRAMS_PER_LITER_TWC = eval(_cache[pt_load_key]['value'], {'np': np}, locals_dict)
    PD_GRAMS_PER_LITER_TWC = eval(_cache[pd_load_key]['value'], {'np': np}, locals_dict)
    RH_GRAMS_PER_LITER_TWC = eval(_cache[rh_load_key]['value'], {'np': np}, locals_dict)
    OZ_PER_GRAM = \
        eval(_cache['ALL', '-', 'Exhaust', 'troy_oz_per_gram', '-', '-', '-']['value'], {'np': np}, locals_dict)

    adj_factor_sub = _cache['ALL', '-', 'Exhaust', 'twc_substrate', '-', '-', '-']['dollar_adjustment']
    adj_factor_wash = _cache['ALL', '-', 'Exhaust', 'twc_substrate', '-', '-', '-']['dollar_adjustment']
    adj_factor_can = _cache['ALL', '-', 'Exhaust', 'twc_canning', '-', '-', '-']['dollar_adjustment']
    TWC_SWEPT_VOLUME = \
        eval(_cache['ALL', '-', 'Exhaust', 'twc_swept_volume', '-', '-', '-']['value'], {'np': np}, locals_dict)

    locals_dict.update(locals())

    twc_substrate = \
        eval(_cache['ALL', '-', 'Exhaust', 'twc_substrate', '-', '-', '-']['value'], {'np': np}, locals_dict) \
        * adj_factor_sub * learning_factor
    twc_washcoat = \
        eval(_cache['ALL', '-', 'Exhaust', 'twc_washcoat', '-', '-', '-']['value'], {'np': np}, locals_dict) \
        * adj_factor_wash * learning_factor
    twc_canning = \
        eval(_cache['ALL', '-', 'Exhaust', 'twc_canning', '-', '-', '-']['value'], {'np': np}, locals_dict) \
        * adj_factor_can * learning_factor
    twc_pgm = eval(_cache['ALL', '-', 'Exhaust', 'twc_pgm', '-', '-', '-']['value'], {'np': np}, locals_dict)
    twc_cost = (twc_substrate + twc_washcoat + twc_canning + twc_pgm)

    # gpf cost
    gpf_cost = 0
    if omega_globals.options.powertrain_cost_with_gpf:
        cost_key = ('ALL', '-', 'Exhaust', 'gpf', '-', '-', '-')
        adj_factor_gpf = _cache[cost_key]['dollar_adjustment']
        gpf_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) \
                   * adj_factor_gpf * learning_factor

    return twc_substrate, twc_washcoat, twc_canning, twc_pgm, twc_cost, gpf_cost


def calc_diesel_eas_cost(locals_dict, learning_factor):
    """
    Calculate exhaust aftertreatment system (eas) cost for diesel-fueled engines.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use

    Returns:
        The diesel exhaust aftertreatment system cost

    """
    cost_key = ('ALL', '-', 'Exhaust', 'diesel_aftertreatment_system', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    diesel_eas_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * \
                      adj_factor * learning_factor

    return diesel_eas_cost


def calc_non_eas_exhaust_cost(locals_dict, learning_factor, powertrain_type, engine_config, body_style):
    """
    Calculate non-eas exhaust system cost for all liquid-fueled engines.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        engine_config (str): e.g., 'I' or 'V' configuration of the engine block
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The exhaust system cost excluding the exhaust aftertreatment system (eas)

    """
    cost_key = (powertrain_type, '-', 'Exhaust', 'Non-EAS', '-', engine_config, body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    non_eas_exhaust_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) \
                           * adj_factor * learning_factor

    return non_eas_exhaust_cost


def calc_engine_cost(locals_dict, learning_factor, pkg_info, powertrain_type, engine_config, body_style,
                     diesel_flag=False):
    """
    Calculate the cost of the engine, if equipped, including technologies included on the engine, if equipped
    (e.g., GDI, EGR, etc.).

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        pkg_info (Series): powertain package information
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        engine_config (str): e.g., 'I' or 'V' configuration of the engine block
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'
        diesel_flag (bool): True for diesel engines (default is False)

    Returns:
        The engine block cost, cooled EGR cost, GDI cost, turbocharger cost, cylinder deactivation cost, and
        Atkinson-specific cost, all where applicable; costs are $0 where not applicable

    """
    # engine block
    cost_key = (powertrain_type, '-', 'Engine', 'ALL', '-', engine_config, body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    engine_block_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    if diesel_flag:
        cost_key = ('ALL', '-', 'Engine', 'diesel_engine_cost_scaler', '-', '-', '-')
        diesel_scaler = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)
        engine_block_cost *= diesel_scaler

    # vvt (included on all liquid-fueled engines)
    cost_key = (powertrain_type, '-', 'Engine', 'VVT', '-', engine_config, body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    engine_block_cost += eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    # cegr cost
    cost_key = (powertrain_type, '-', 'Engine', 'EGR', '-', '-', body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    cegr_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                pkg_info['cegr']

    # gdi cost
    cost_key = (powertrain_type, '-', 'Engine', 'DI', '-', engine_config, body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    gdi_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
               pkg_info['gdi']

    # turb cost
    cost_key = (powertrain_type, '-', 'Engine', 'Turbo Charger', '-', engine_config, body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    turb_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                (pkg_info['turb11'] + pkg_info['turb12'])

    # deac_pd cost
    cost_key = ('ALL', '-', 'Engine', 'deac_pd', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    deac_pd_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                   pkg_info['deac_pd']

    # deac_fc cost
    cost_key = ('ICE', '-', 'Engine', 'deac_fc', '-', engine_config, body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    deac_fc_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                   pkg_info['deac_fc']

    # atk2 cost
    cost_key = ('ALL', '-', 'Engine', 'atk2', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    atk2_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                pkg_info['atk2']

    return engine_block_cost, cegr_cost, gdi_cost, turb_cost, deac_pd_cost, deac_fc_cost, atk2_cost


def calc_fuel_storage_cost(locals_dict, learning_factor, powertrain_type, body_style):
    """
    Calculate the cost of the liquid-fuel storage on liquid-fueled vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The fuel storage system cost for liquid-fueled vehicles

    """
    cost_key = (powertrain_type, '-', 'Fuel', 'Storage', '-', '-', body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    fuel_storage_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return fuel_storage_cost


def calc_lv_battery_cost(locals_dict, learning_factor, powertrain_type):
    """
    Calculate the low voltage battery cost for all vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'

    Returns:
        The low voltage battery cost

    """
    cost_key = (powertrain_type, '-', 'Driveline', 'LV_Battery_Less_Than_Equalto_48V', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    lv_battery_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return lv_battery_cost


def calc_start_stop_cost(locals_dict, learning_factor, pkg_info):
    """
    Calculate the start-stop system cost, if equipped.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        pkg_info (Series): powertain package information

    Returns:
        The start-stop system cost

    """
    cost_key = ('ICE', '-', 'Driveline', 'start_stop', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    start_stop_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                      pkg_info['start_stop']

    return start_stop_cost


def calc_trans_cost(locals_dict, learning_factor, powertrain_type, powertrain_subtype, drive_system, body_style):
    """
    Calculate the transmission cost, if equipped, of the given package.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        powertrain_subtype (str): e.g., 'P0', 'P2', 'PS', 'ALL'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive
        body_style (str): e.g., 'sedan', 'cuv_suv', 'pickup'

    Returns:
        The transmission cost for the given package

    Notes:
        Start-stop for non-electrified ICE is included in calc_start_stop_cost

    """
    if powertrain_type == 'ICE':
        if drive_system == 'AWD':
            cost_key = (powertrain_type, '-', 'Transmission', 'AT', drive_system, '-', body_style)
        else:
            cost_key = (powertrain_type, '-', 'Transmission', 'AT', drive_system, '-', '-')
    elif powertrain_type != 'ICE' and locals_dict['GEARS'] != 0:
        cost_key = (powertrain_type, powertrain_subtype, 'Transmission', 'AT', drive_system, '-', '-')
    else:
        cost_key = (powertrain_type, powertrain_subtype, 'Transmission', 'eCVT', drive_system, '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']

    trans_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return trans_cost


def calc_motor_cost(locals_dict, learning_factor, powertrain_type, drive_system, body_style='-'):
    """
    Calculate the electric drive motor cost, if equipped.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV', 'HEV'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The electric drive motor cost, including all drive motors

    """
    cost_key = (powertrain_type, '-', 'Drive_Unit', 'E_Motor', drive_system, '-', body_style)

    adj_factor = _cache[cost_key]['dollar_adjustment']
    motor_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return motor_cost


def calc_high_efficiency_alternator(locals_dict, learning_factor, pkg_info):
    """
    Calculate the cost of the high efficiency alternator, if equipped.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        pkg_info (Series): powertain package information

    Returns:
        The high efficiency alternator cost

    """
    cost_key = ('ICE', '-', 'Driveline', 'high_eff_alternator', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    high_eff_alt_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor * \
                        pkg_info['high_eff_alternator']

    return high_eff_alt_cost


def calc_powertrain_cooling_cost(locals_dict, learning_factor, powertrain_type, drive_system, engine_config, body_style):
    """
    Calculate the powertrain thermal control system cost for all vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive
        engine_config (str): e.g., 'I' or 'V' configuration of the engine block
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The powertrain thermal control system cost

    """
    cost_key = (powertrain_type, '-', 'Thermal', 'Coolant_Circuit_Cooling_Heating', '-', engine_config, body_style)
    if powertrain_type == 'BEV':
        cost_key = (powertrain_type, '-', 'Thermal', 'Coolant_Circuit_Cooling_Heating', drive_system, '-', body_style)

    adj_factor = _cache[cost_key]['dollar_adjustment']
    powertrain_cooling_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return powertrain_cooling_cost


def calc_hvac_cost(locals_dict, learning_factor, powertrain_type):
    """
    Calculate the powertrain thermal control system cost for all vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'

    Returns:
        The HVAC system cost

    """
    cost_key = (powertrain_type, '-', 'Thermal', 'HVAC', '-', '-', '-')

    adj_factor = _cache[cost_key]['dollar_adjustment']
    hvac_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return hvac_cost


def calc_air_conditioning_costs(locals_dict, learning_factor):
    """
    Calculate the air conditioning (ac) system costs for all vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use

    Returns:
        The ac-leakage and ac-efficiency costs

    """
    cost_key = ('ALL', '-', 'Driveline', 'ac_leakage', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    ac_leakage_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    cost_key = ('ALL', '-', 'Driveline', 'ac_efficiency', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    ac_efficiency_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return ac_leakage_cost, ac_efficiency_cost


def calc_lv_harness_cost(locals_dict, learning_factor, powertrain_type, drive_system, body_style):
    """
    Calculate the low voltage harness cost for all vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'ICE', 'BEV', 'PHEV', 'HEV', 'MHEV'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The low voltage harness cost

    """
    cost_key = \
        (powertrain_type, '-', 'Elect._Distribution_and_Electronic_Controls', 'Harness_Low_Voltage_LV', drive_system,
         '-', body_style
         )
    adj_factor = _cache[cost_key]['dollar_adjustment']
    lv_harness_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return lv_harness_cost


def calc_hv_harness_cost(locals_dict, learning_factor, powertrain_type, drive_system, body_style):
    """
    Calculate the high voltage harness cost, if equipped.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV', 'HEV', 'MHEV'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The high voltage harness cost

    """
    cost_key = \
        (powertrain_type, '-', 'Elect._Distribution_and_Electronic_Controls', 'Harness_High_Voltage_HV', drive_system,
         '-', body_style
         )
    adj_factor = _cache[cost_key]['dollar_adjustment']
    hv_harness_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return hv_harness_cost


def calc_dc_dc_converter_cost(locals_dict, learning_factor, powertrain_type):
    """
    Calculate the DC-to-DC converter cost, if equipped.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV', 'HEV', 'MHEV'

    Returns:
        The DC-to-DC converter cost

    Notes:
        The OBC kW is determined in the get_obc_power function.

    """
    cost_key = (powertrain_type, '-', 'Electrical_Power_Supply', 'DC_DC_Converter', '-', '-', '-')
    if powertrain_type in ['BEV', 'PHEV']:
        cost_key = (powertrain_type, '-', 'Electrical_Power_Supply', 'DC_DC_Converter + OBC', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    dc_dc_converter_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return dc_dc_converter_cost


def calc_charge_cord_cost(locals_dict, learning_factor, powertrain_type):
    """
    Calculate the external charging device cost, if equipped.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV'

    Returns:
        The external charging device cost

    """
    cost_key = (powertrain_type, '-', 'Electrical_Power_Supply', 'External_Battery_Charge_Device', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    charge_cord_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) * adj_factor * learning_factor

    return charge_cord_cost


def calc_inverter_cost(
        locals_dict, learning_factor, powertrain_type, powertrain_subtype='-', drive_system='AWD', body_style='-'):
    """
    Calculate the costs for inverters on BEVs and on electrified AWD.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV', 'HEV', 'MHEV'
        powertrain_subtype (str): e.g., 'P0', 'P2', 'PS'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD'
        body_style (str): e.g., 'P0', 'P2', 'PS'

    Returns:
        The inverter cost(s)

    """
    cost_key = (powertrain_type, powertrain_subtype, 'Drive_Unit', 'Inverter', drive_system, '-', body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    inverter_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) \
                    * adj_factor * learning_factor

    return inverter_cost


def calc_gearbox_cost(
        locals_dict, learning_factor, powertrain_type, body_style, powertrain_subtype='-', drive_system='AWD'):
    """
    Calculate the costs for gearboxes on BEVs.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV', 'HEV', 'MHEV'
        powertrain_subtype (str): e.g., 'P0', 'P2', 'PS'
        drive_system (str): e.g., 'FWD', 'RWD', 'AWD' denoting front/rear/all wheel drive
        body_style (str): e.g., 'sedan', 'cuv_suv' or 'pickup'

    Returns:
        The gearbox(es) cost

    """
    cost_key = (powertrain_type, powertrain_subtype, 'Drive_Unit', 'Gearbox', drive_system, '-', body_style)
    adj_factor = _cache[cost_key]['dollar_adjustment']
    gearbox_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) \
                   * adj_factor * learning_factor

    return gearbox_cost


def calc_battery_cost(locals_dict, learning_factor, powertrain_type):
    """
    Calculate the high voltage battery pack cost on electrified vehicles.

    Args:
        locals_dict (dict): local attributes
        learning_factor (float): the learning factor to use
        powertrain_type (str): e.g., 'BEV', 'PHEV', 'HEV', 'MHEV'

    Returns:
        The high voltage battery pack cost

    """
    cost_key = (powertrain_type, '-', 'Electrical_Power_Supply', 'HV_Battery', '-', '-', '-')
    adj_factor = _cache[cost_key]['dollar_adjustment']
    battery_cost = eval(_cache[cost_key]['value'], {'np': np}, locals_dict) \
                   * adj_factor * learning_factor

    return battery_cost


def calc_battery_offset(locals_dict, v, powertrain_type, battery_kwh):
    """
    Calculate the high voltage battery pack cost offset, where applicable (e.g., pursuant to the
    Inflation Reduction Act).

    Args:
        locals_dict (dict): local attributes
        v (Vehicle): the Vehicle object
        powertrain_type (str): e.g., 'BEV', 'PHEV'

    Returns:
        The high voltage battery pack cost offset

    """
    battery_offset = 0
    if battery_kwh >= 7:
        cost_key = (powertrain_type, '-', 'battery_offset', '-', '-', '-', '-')
        battery_offset_dict = eval(_cache[cost_key]['value'], {'np': np}, locals_dict)
        battery_offset_min_year = min(battery_offset_dict['dollars_per_kwh'])
        battery_offset_max_year = max(battery_offset_dict['dollars_per_kwh'])
        if battery_offset_min_year <= v.model_year <= battery_offset_max_year:
            battery_offset = battery_offset_dict['dollars_per_kwh'][v.model_year] * battery_kwh

    return battery_offset
