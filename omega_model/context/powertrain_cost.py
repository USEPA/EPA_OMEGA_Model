"""

**Routines to powertrain cost.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,powertrain_cost,input_template_version:,0.1,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        powertrain_type,item,value,quantity,dollar_basis,notes
        ICE,dollars_per_cylinder,((-28.814) * CYL + 726.27) * CYL * MARKUP_ICE,,2019,
        ICE,dollars_per_liter,((400) * LITERS) * MARKUP_ICE,,2019,
        ICE,gdi,((43.237) * CYL + 97.35) * MARKUP_ICE,,2019,

----

**CODE**

"""
import pandas as pd
import numpy as np

print('importing %s' % __file__)

from omega_model import *
from effects.general_functions import dollar_adjustment_factor

_cache = dict()


class PowertrainCost(OMEGABase):
    """
    **Loads and provides access to powertrain cost data, provides methods to calculate powertrain costs.**

    """

    @staticmethod
    def calc_cost(vehicle, pkg_df):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            vehicle (Vehicle): the vehicle to calc costs for
            pkg_df (DataFrame): the necessary information for developing cost estimates.

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        powertrain_type, market_class_id, model_year = vehicle.powertrain_type, vehicle.market_class_id, vehicle.model_year

        locals_dict = locals()

        # markups and learning
        MARKUP_ICE = eval(_cache['ICE', 'markup']['value'], {}, locals_dict)
        MARKUP_HEV = eval(_cache['HEV', 'markup']['value'], {}, locals_dict)
        MARKUP_PHEV = eval(_cache['PHEV', 'markup']['value'], {}, locals_dict)
        MARKUP_BEV = eval(_cache['BEV', 'markup']['value'], {}, locals_dict)
        MARKUP_ALL = eval(_cache['ALL', 'markup']['value'], {}, locals_dict)

        learning_rate = eval(_cache['ALL', 'learning_rate']['value'], {}, locals_dict)
        learning_start = eval(_cache['ALL', 'learning_start']['value'], {}, locals_dict)
        legacy_sales_scaler_ice = eval(_cache['ICE', 'legacy_sales_learning_scaler']['value'], {}, locals_dict)
        legacy_sales_scaler_pev = eval(_cache['PEV', 'legacy_sales_learning_scaler']['value'], {}, locals_dict)
        sales_scaler_ice = eval(_cache['ICE', 'sales_scaler']['value'], {}, locals_dict)
        sales_scaler_pev = eval(_cache['PEV', 'sales_scaler']['value'], {}, locals_dict)
        cumulative_sales_ice = sales_scaler_ice * (model_year - learning_start)
        cumulative_sales_pev = sales_scaler_pev * (model_year - learning_start)
        learning_factor_ice = ((cumulative_sales_ice + legacy_sales_scaler_ice) / legacy_sales_scaler_ice) ** learning_rate
        learning_factor_pev = ((cumulative_sales_pev + legacy_sales_scaler_pev) / legacy_sales_scaler_pev) ** learning_rate

        weight_bins = (0, 3200, 3800, 4400, 5000, 5600, 6200, 14000)
        tractive_motor = 'dual'
        if (market_class_id.__contains__('non_hauling') and vehicle.drive_system < 4) or powertrain_type == 'HEV':
            tractive_motor = 'single'

        trans_cost = cyl_cost = liter_cost = 0
        high_eff_alt_cost = start_stop_cost = deac_pd_cost = deac_fc_cost = cegr_cost = atk2_cost = gdi_cost = 0
        turb12_cost = turb11_cost = 0
        twc_cost = gpf_cost = 0
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

        CURBWT = pkg_df['curbweight_lbs'].values

        # powertrain costs for anything with a liquid fueled engine
        if powertrain_type in ['ICE', 'HEV', 'PHEV']:

            pkg_df['trx_idx'] = pkg_df['cost_curve_class'].apply(lambda x: x.find('TRX'))
            pkg_df['trx_idx_end'] = pkg_df['trx_idx'].values + 5

            trans = pkg_df.apply(lambda x: x['cost_curve_class'][x['trx_idx']:x['trx_idx_end']], axis=1).values

            gasoline_flag = pkg_df['gas_fuel'].values
            diesel_flat = pkg_df['diesel_fuel'].values

            CYL = pkg_df['engine_cylinders'].values
            LITERS = pkg_df['engine_displacement_L'].values

            locals_dict = locals()

            # PGM costs and loadings
            PT_USD_PER_OZ = eval(_cache['ALL', 'pt_dollars_per_oz']['value'], {}, locals_dict)
            PD_USD_PER_OZ = eval(_cache['ALL', 'pd_dollars_per_oz']['value'], {}, locals_dict)
            RH_USD_PER_OZ = eval(_cache['ALL', 'rh_dollars_per_oz']['value'], {}, locals_dict)
            PT_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pt_grams_per_liter']['value'], {}, locals_dict)
            PD_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pd_grams_per_liter']['value'], {}, locals_dict)
            RH_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_rh_grams_per_liter']['value'], {}, locals_dict)
            PT_GRAMS_PER_LITER_GPF = eval(_cache['ALL', 'gpf_pt_grams_per_liter']['value'], {}, locals_dict)
            PD_GRAMS_PER_LITER_GPF = eval(_cache['ALL', 'gpf_pd_grams_per_liter']['value'], {}, locals_dict)
            RH_GRAMS_PER_LITER_GPF = eval(_cache['ALL', 'gpf_rh_grams_per_liter']['value'], {}, locals_dict)
            OZ_PER_GRAM = eval(_cache['ALL', 'troy_oz_per_gram']['value'], {}, locals_dict)  # note that these are Troy ounces

            turb_input_scaler = eval(_cache['ALL', 'turb_scaler']['value'], {}, locals_dict)

            # determine trans and calc cost
            adj_factor = np.array([_cache['ALL', t]['dollar_adjustment'] for t in trans])
            trans_cost = np.array([eval(_cache['ALL', t]['value'], {}, locals_dict) for t in trans]) \
                         * adj_factor * learning_factor_ice

            # cylinder cost
            adj_factor = _cache['ALL', 'dollars_per_cylinder']['dollar_adjustment']
            cyl_cost = eval(_cache['ALL', 'dollars_per_cylinder']['value'], {}, locals_dict) \
                       * adj_factor * learning_factor_ice

            # displacement cost
            adj_factor = _cache['ALL', 'dollars_per_liter']['dollar_adjustment']
            liter_cost = eval(_cache['ALL', 'dollars_per_liter']['value'], {}, locals_dict) \
                         * adj_factor * learning_factor_ice

            # high efficiency alternator cost
            adj_factor = _cache['ALL', 'high_eff_alternator']['dollar_adjustment']
            high_eff_alt_cost = eval(_cache['ALL', 'high_eff_alternator']['value'], {}, locals_dict) \
                                * adj_factor * learning_factor_ice * pkg_df['high_eff_alternator'].values

            # start_stop cost
            adj_factor = _cache['ALL', 'start_stop']['dollar_adjustment']
            start_stop_cost = eval(_cache['ALL', 'start_stop']['value'], {}, locals_dict) \
                              * adj_factor * learning_factor_ice * pkg_df['start_stop'].values

            # deac_pd cost
            adj_factor = _cache['ALL', 'deac_pd']['dollar_adjustment']
            deac_pd_cost = eval(_cache['ALL', 'deac_pd']['value'], {}, locals_dict) \
                           * adj_factor * learning_factor_ice * pkg_df['deac_pd'].values

            # deac_fc cost
            adj_factor = _cache['ALL', 'deac_fc']['dollar_adjustment']
            deac_fc_cost = eval(_cache['ALL', 'deac_fc']['value'], {}, locals_dict) \
                           * adj_factor * learning_factor_ice * pkg_df['deac_fc'].values

            # cegr cost
            adj_factor = _cache['ALL', 'cegr']['dollar_adjustment']
            cegr_cost = eval(_cache['ALL', 'cegr']['value'], {}, locals_dict) \
                           * adj_factor * learning_factor_ice * pkg_df['cegr'].values

            # atk2 cost
            adj_factor = _cache['ALL', 'atk2']['dollar_adjustment']
            atk2_cost = eval(_cache['ALL', 'atk2']['value'], {}, locals_dict) \
                        * adj_factor * learning_factor_ice * pkg_df['atk2'].values

            # gdi cost
            adj_factor = _cache['ALL', 'gdi']['dollar_adjustment']
            gdi_cost = eval(_cache['ALL', 'gdi']['value'], {}, locals_dict) \
                        * adj_factor * learning_factor_ice * pkg_df['gdi'].values

            # turb12 cost
            adj_factor = _cache['ALL', 'turb12']['dollar_adjustment']
            turb12_cost = eval(_cache['ALL', 'turb12']['value'], {}, locals_dict) \
                          * adj_factor * learning_factor_ice * pkg_df['turb12'].values

            # turb11 cost
            adj_factor = _cache['ALL', 'turb11']['dollar_adjustment']
            turb11_cost = eval(_cache['ALL', 'turb11']['value'], {}, locals_dict) \
                          * adj_factor * learning_factor_ice * pkg_df['turb11'].values

            turb_scaler += (turb_input_scaler - turb_scaler) * (pkg_df['turb11'].values | pkg_df['turb12'].values)

            # 3-way catalyst cost
            adj_factor_sub = _cache['ALL', 'twc_substrate']['dollar_adjustment']
            adj_factor_wash = _cache['ALL', 'twc_washcoat']['dollar_adjustment']
            adj_factor_can = _cache['ALL', 'twc_canning']['dollar_adjustment']
            TWC_SWEPT_VOLUME = eval(_cache['ALL', 'twc_swept_volume']['value'], {}, locals_dict)
            locals_dict = locals()
            substrate = eval(_cache['ALL', 'twc_substrate']['value'], {}, locals_dict) \
                        * adj_factor_sub * learning_factor_ice
            washcoat = eval(_cache['ALL', 'twc_washcoat']['value'], {}, locals_dict) \
                       * adj_factor_wash * learning_factor_ice
            canning = eval(_cache['ALL', 'twc_canning']['value'], {}, locals_dict) \
                      * adj_factor_can * learning_factor_ice
            pgm = eval(_cache['ALL', 'twc_pgm']['value'], {}, locals_dict)
            twc_cost = (substrate + washcoat + canning + pgm) * gasoline_flag

            # gpf cost
            adj_factor_sub = _cache['ALL', 'gpf_substrate']['dollar_adjustment']
            adj_factor_wash = _cache['ALL', 'gpf_washcoat']['dollar_adjustment']
            adj_factor_can = _cache['ALL', 'gpf_canning']['dollar_adjustment']
            GPF_SWEPT_VOLUME = eval(_cache['ALL', 'gpf_swept_volume']['value'], {}, locals_dict)
            locals_dict = locals()
            substrate = eval(_cache['ALL', 'gpf_substrate']['value'], {}, locals_dict) \
                        * adj_factor_sub * learning_factor_ice
            washcoat = eval(_cache['ALL', 'gpf_washcoat']['value'], {}, locals_dict) \
                       * adj_factor_wash * learning_factor_ice
            canning = eval(_cache['ALL', 'gpf_canning']['value'], {}, locals_dict) \
                      * adj_factor_can * learning_factor_ice
            pgm = eval(_cache['ALL', 'gpf_pgm']['value'], {}, locals_dict)
            gpf_cost = (substrate + washcoat + canning + pgm) * gasoline_flag

        if powertrain_type in ['HEV', 'PHEV', 'BEV']:

            if powertrain_type == 'HEV':
                learn = learning_factor_ice
            else:
                learn = learning_factor_pev

            KWH = pkg_df['battery_kwh'].values
            KW = pkg_df['motor_kw'].values

            if powertrain_type == 'HEV':
                obc_kw = 0
            elif powertrain_type == 'PHEV':
                obc_kw = 1.9 * np.ones_like(KWH)
                obc_kw[KWH < 10] = 1.1
                obc_kw[KWH < 7] = 0.7
            else:
                obc_kw = 19 * np.ones_like(KWH)
                obc_kw[KWH < 100] = 11
                obc_kw[KWH < 70] = 7

            dcdc_converter_kw = eval(_cache[powertrain_type, 'DCDC_converter_kW']['value'], {}, locals_dict)

            OBC_AND_DCDC_CONVERTER_KW = dcdc_converter_kw + obc_kw
            # VEHICLE_SIZE_CLASS = weight_bins.index(min([v for v in weight_bins if CURBWT < v])) # TODO where is this coming from, if we keep this?

            VEHICLE_SIZE_CLASS = np.array([weight_bins.index(min([v for v in weight_bins if cw < v])) for cw in CURBWT])

            locals_dict = locals()

            # battery cost
            adj_factor = _cache[powertrain_type, 'battery']['dollar_adjustment']
            battery_cost = eval(_cache[powertrain_type, 'battery']['value'], {}, locals_dict) \
                           * adj_factor * learn

            # electrified powertrain cost

            adj_factor = _cache[powertrain_type, f'motor_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'motor_{tractive_motor}']['quantity']
            motor_cost = eval(_cache[powertrain_type, f'motor_{tractive_motor}']['value'], {}, locals_dict) \
                         * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'inverter_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'inverter_{tractive_motor}']['quantity']
            inverter_cost = eval(_cache[powertrain_type, f'inverter_{tractive_motor}']['value'], {}, locals_dict) \
                            * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['quantity']
            induction_motor_cost = eval(_cache[powertrain_type, f'induction_motor_{tractive_motor}']['value'], {}, locals_dict) \
                                   * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['quantity']
            induction_inverter_cost = eval(_cache[powertrain_type, f'induction_inverter_{tractive_motor}']['value'], {}, locals_dict) \
                                      * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'OBC_and_DCDC_converter']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'OBC_and_DCDC_converter']['quantity']
            obc_and_dcdc_converter_cost = eval(_cache[powertrain_type, 'OBC_and_DCDC_converter']['value'], {}, locals_dict) \
                                          * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'HV_orange_cables']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'HV_orange_cables']['quantity']
            hv_orange_cables_cost = eval(_cache[powertrain_type, 'HV_orange_cables']['value'], {}, locals_dict) \
                                    * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'LV_battery']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'LV_battery']['quantity']
            lv_battery_cost = eval(_cache[powertrain_type, 'LV_battery']['value'], {}, locals_dict) \
                              * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'HVAC']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'HVAC']['quantity']
            hvac_cost = eval(_cache[powertrain_type, 'HVAC']['value'], {}, locals_dict) \
                        * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['quantity']
            single_speed_gearbox_cost = eval(_cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['value'], {}, locals_dict) \
                                        * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['quantity']
            powertrain_cooling_loop_cost = eval(_cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['value'], {}, locals_dict) \
                                           * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'charging_cord_kit']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'charging_cord_kit']['quantity']
            charging_cord_kit_cost = eval(_cache[powertrain_type, 'charging_cord_kit']['value'], {}, locals_dict) \
                                     * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'DC_fast_charge_circuitry']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'DC_fast_charge_circuitry']['quantity']
            dc_fast_charge_circuitry_cost = eval(_cache[powertrain_type, 'DC_fast_charge_circuitry']['value'], {}, locals_dict) \
                                            * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'power_management_and_distribution']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'power_management_and_distribution']['quantity']
            power_management_and_distribution_cost = eval(_cache[powertrain_type, 'power_management_and_distribution']['value'], {}, locals_dict) \
                                                     * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'brake_sensors_actuators']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'brake_sensors_actuators']['quantity']
            brake_sensors_actuators_cost = eval(_cache[powertrain_type, 'brake_sensors_actuators']['value'], {}, locals_dict) \
                                           * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['quantity']
            additional_pair_of_half_shafts_cost = eval(_cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['value'], {}, locals_dict) \
                                                  * adj_factor * learn * quantity

            emachine_cost = motor_cost + induction_motor_cost

            electrified_driveline_cost = inverter_cost + induction_inverter_cost \
                                          + obc_and_dcdc_converter_cost + hv_orange_cables_cost + lv_battery_cost \
                                          + hvac_cost + single_speed_gearbox_cost + powertrain_cooling_loop_cost \
                                          + charging_cord_kit_cost + dc_fast_charge_circuitry_cost \
                                          + power_management_and_distribution_cost + brake_sensors_actuators_cost \
                                          + additional_pair_of_half_shafts_cost

        # ac leakage cost
        adj_factor = _cache['ALL', 'ac_leakage']['dollar_adjustment']
        ac_leakage_cost = eval(_cache['ALL', 'ac_leakage']['value'], {}, locals_dict) \
                          * adj_factor * learning_factor_ice

        # ac efficiency cost
        adj_factor = _cache['ALL', 'ac_efficiency']['dollar_adjustment']
        ac_efficiency_cost = eval(_cache['ALL', 'ac_efficiency']['value'], {}, locals_dict) \
                             * adj_factor * learning_factor_ice

        engine_cost = (cyl_cost + liter_cost) * turb_scaler \
                          + deac_pd_cost + deac_fc_cost \
                          + cegr_cost + atk2_cost + gdi_cost \
                          + turb12_cost + turb11_cost \
                          + twc_cost + gpf_cost

        driveline_cost = trans_cost \
                          + high_eff_alt_cost + start_stop_cost \
                          + ac_leakage_cost + ac_efficiency_cost

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

        if verbose:
            omega_log.logwrite('\nInitializing PowertrainCost from %s...' % filename)
        input_template_name = 'powertrain_cost'
        input_template_version = 0.1
        input_template_columns = {'powertrain_type', 'item', 'value', 'quantity', 'dollar_basis', 'notes'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:

                cost_keys = zip(df['powertrain_type'], df['item'])

                for cost_key in cost_keys:

                    _cache[cost_key] = dict()
                    powertrain_type, item = cost_key

                    cost_info = df[(df['powertrain_type'] == powertrain_type) & (df['item'] == item)].iloc[0]

                    if cost_info['quantity'] >= 1:
                        quantity = cost_info['quantity']
                    else:
                        quantity = 0

                    _cache[cost_key] = {'value': dict(),
                                        'quantity': quantity,
                                        'dollar_adjustment': 1}

                    if cost_info['dollar_basis'] > 0:
                        adj_factor = dollar_adjustment_factor('ip_deflators', int(cost_info['dollar_basis']))
                        _cache[cost_key]['dollar_adjustment'] = adj_factor

                    _cache[cost_key]['value'] = compile(cost_info['value'], '<string>', 'eval')

        return template_errors
