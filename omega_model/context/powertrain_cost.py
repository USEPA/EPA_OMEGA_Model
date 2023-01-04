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

print('importing %s' % __file__)

from omega_model import *
from effects.general_functions import dollar_adjustment_factor

_cache = dict()


def get_trans(x):
    trans = ''
    flags = 0

    if x['trx10']:
        trans = 'TRX10'
        flags += 1
    elif x['trx11']:
        trans = 'TRX11'
        flags += 1
    elif x['trx12']:
        trans = 'TRX12'
        flags += 1
    elif x['trx21']:
        trans = 'TRX21'
        flags += 1
    elif x['trx22']:
        trans = 'TRX22'
        flags += 1
    elif x['ecvt']:
        trans = 'TRXCV'
        flags += 1

    if flags == 0:
        raise Exception('%s has no transmission tech flag' % x.vehicle_name)

    if flags > 1:
        raise Exception('%s has multiple transmission tech flags' % x.vehicle_name)

    return trans


class PowertrainCost(OMEGABase):
    """
    **Loads and provides access to powertrain cost data, provides methods to calculate powertrain costs.**

    """
    battery_cost_scalers = dict()

    @staticmethod
    def calc_cost(vehicle, pkg_info, powertrain_type):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            powertrain_type:
            vehicle (Vehicle): the vehicle to calc costs for
            pkg_info (dict-like): the necessary information for developing cost estimates.

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        market_class_id, model_year = vehicle.market_class_id, vehicle.model_year

        locals_dict = locals()

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
        learning_factor_ice = ((cumulative_sales_ice + legacy_sales_scaler_ice) / legacy_sales_scaler_ice) ** learning_rate
        learning_factor_pev = ((cumulative_sales_pev + legacy_sales_scaler_pev) / legacy_sales_scaler_pev) ** learning_rate
        if model_year < learning_start:
            learning_factor_ice = 1 / learning_factor_ice
            learning_factor_pev = 1 / learning_factor_pev

        weight_bins = (0, 3200, 3800, 4400, 5000, 5600, 6200, 14000)
        tractive_motor = 'dual'
        if (market_class_id.__contains__('non_hauling') and vehicle.drive_system < 4) or powertrain_type == 'HEV':
            tractive_motor = 'single'

        trans_cost = cyl_cost = liter_cost = 0
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

        CURBWT = pkg_info['curbweight_lbs']
        # VEHICLE_SIZE_CLASS = np.array([weight_bins.index(min([v for v in weight_bins if cw < v])) for cw in CURBWT])
        VEHICLE_SIZE_CLASS = weight_bins.index(min([v for v in weight_bins if CURBWT < v]))

        # powertrain costs for anything with a liquid fueled engine
        if powertrain_type in ['ICE', 'HEV', 'PHEV', 'MHEV']:

            trans = get_trans(pkg_info)

            gasoline_flag = pkg_info['gas_fuel']

            diesel_flag = pkg_info['diesel_fuel']

            CYL = pkg_info['engine_cylinders']
            LITERS = pkg_info['engine_displacement_L']

            locals_dict = locals()

            # PGM costs and loadings
            PT_USD_PER_OZ = eval(_cache['ALL', 'pt_dollars_per_oz']['value'], {'np': np}, locals_dict)
            PD_USD_PER_OZ = eval(_cache['ALL', 'pd_dollars_per_oz']['value'], {'np': np}, locals_dict)
            RH_USD_PER_OZ = eval(_cache['ALL', 'rh_dollars_per_oz']['value'], {'np': np}, locals_dict)
            PT_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pt_grams_per_liter']['value'], {'np': np}, locals_dict)
            PD_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pd_grams_per_liter']['value'], {'np': np}, locals_dict)
            RH_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_rh_grams_per_liter']['value'], {'np': np}, locals_dict)
            OZ_PER_GRAM = eval(_cache['ALL', 'troy_oz_per_gram']['value'], {'np': np}, locals_dict)  # note that these are Troy ounces

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
            if gasoline_flag == 1:
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
                adj_factor_gpf = _cache['ALL', 'gpf_cost']['dollar_adjustment']
                locals_dict = locals()
                gpf_cost = eval(_cache['ALL', 'gpf_cost']['value'], {'np': np}, locals_dict) \
                           * adj_factor_gpf * learn

            # diesel exhaust aftertreatment cost
            elif diesel_flag == 1:
                adj_factor_diesel_eas = _cache['ALL', 'diesel_aftertreatment_system']['dollar_adjustment']
                locals_dict = locals()
                diesel_eas_cost = eval(_cache['ALL', 'diesel_aftertreatment_system']['value'], {'np': np}, locals_dict) \
                                  * adj_factor_diesel_eas * learn

        if powertrain_type in ['MHEV', 'HEV', 'PHEV', 'BEV']:

            if powertrain_type == 'PHEV' or powertrain_type == 'BEV':
                learn = learning_factor_pev

            KWH = pkg_info['battery_kwh']
            KW = pkg_info['motor_kw']

            if powertrain_type == 'HEV':
                obc_kw = 0
            elif powertrain_type == 'MHEV':
                obc_kw = 0
            elif powertrain_type == 'PHEV':
                obc_kw = 1.9 # * np.ones_like(KWH)
                if KWH < 10:
                    obc_kw = 1.1
                elif KWH < 7:
                    obc_kw = 0.7
                # obc_kw[KWH < 10] = 1.1
                # obc_kw[KWH < 7] = 0.7
            else:
                obc_kw = 19 # * np.ones_like(KWH)
                if KWH < 100:
                    obc_kw = 11
                elif KWH < 70:
                    obc_kw = 7
                # obc_kw[KWH < 100] = 11
                # obc_kw[KWH < 70] = 7

            dcdc_converter_kw = eval(_cache[powertrain_type, 'DCDC_converter_kW']['value'], {'np': np}, locals_dict)

            OBC_AND_DCDC_CONVERTER_KW = dcdc_converter_kw + obc_kw

            locals_dict = locals()

            # battery cost
            if powertrain_type in ['MHEV', 'HEV', 'PHEV', 'BEV']:
                battery_cost_scaler_dict \
                    = eval(_cache['ALL', 'battery_cost_scalers']['value'], {'np': np}, locals_dict)

                if model_year in battery_cost_scaler_dict['scaler'].keys():
                    cost_scaler = battery_cost_scaler_dict['scaler'][model_year]
                elif model_year in PowertrainCost.battery_cost_scalers:
                    cost_scaler = PowertrainCost.battery_cost_scalers[model_year]
                else:
                    min_year = max([yr for yr in battery_cost_scaler_dict['scaler'].keys() if yr < model_year])
                    max_year = min([yr for yr in battery_cost_scaler_dict['scaler'].keys() if yr > model_year])
                    min_year_scaler = battery_cost_scaler_dict['scaler'][min_year]
                    max_year_scaler = battery_cost_scaler_dict['scaler'][max_year]

                    m = (max_year_scaler - min_year_scaler) / (max_year - min_year)
                    cost_scaler = m * (model_year - min_year) + min_year_scaler

                    PowertrainCost.battery_cost_scalers[model_year] = cost_scaler

                adj_factor = _cache[powertrain_type, 'battery']['dollar_adjustment']
                battery_cost = eval(_cache[powertrain_type, 'battery']['value'], {'np': np}, locals_dict) \
                               * adj_factor * cost_scaler

            if powertrain_type == 'BEV':
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
            inverter_cost = eval(_cache[powertrain_type, f'inverter_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                            * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['quantity']
            induction_motor_cost = eval(_cache[powertrain_type, f'induction_motor_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                                   * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['quantity']
            induction_inverter_cost = eval(_cache[powertrain_type, f'induction_inverter_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                                      * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'OBC_and_DCDC_converter']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'OBC_and_DCDC_converter']['quantity']
            obc_and_dcdc_converter_cost = eval(_cache[powertrain_type, 'OBC_and_DCDC_converter']['value'], {'np': np}, locals_dict) \
                                          * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'HV_orange_cables']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'HV_orange_cables']['quantity']
            hv_orange_cables_cost = eval(_cache[powertrain_type, 'HV_orange_cables']['value'], {'np': np}, locals_dict) \
                                    * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['quantity']
            single_speed_gearbox_cost = eval(_cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                                        * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['quantity']
            powertrain_cooling_loop_cost = eval(_cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                                           * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'charging_cord_kit']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'charging_cord_kit']['quantity']
            charging_cord_kit_cost = eval(_cache[powertrain_type, 'charging_cord_kit']['value'], {'np': np}, locals_dict) \
                                     * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'DC_fast_charge_circuitry']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'DC_fast_charge_circuitry']['quantity']
            dc_fast_charge_circuitry_cost = eval(_cache[powertrain_type, 'DC_fast_charge_circuitry']['value'], {'np': np}, locals_dict) \
                                            * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'power_management_and_distribution']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'power_management_and_distribution']['quantity']
            power_management_and_distribution_cost = eval(_cache[powertrain_type, 'power_management_and_distribution']['value'], {'np': np}, locals_dict) \
                                                     * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, 'brake_sensors_actuators']['dollar_adjustment']
            quantity = _cache[powertrain_type, 'brake_sensors_actuators']['quantity']
            brake_sensors_actuators_cost = eval(_cache[powertrain_type, 'brake_sensors_actuators']['value'], {'np': np}, locals_dict) \
                                           * adj_factor * learn * quantity

            adj_factor = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['dollar_adjustment']
            quantity = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['quantity']
            additional_pair_of_half_shafts_cost = eval(_cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['value'], {'np': np}, locals_dict) \
                                                  * adj_factor * learn * quantity

            emachine_cost = motor_cost + induction_motor_cost

            electrified_driveline_cost = inverter_cost + induction_inverter_cost \
                                         + obc_and_dcdc_converter_cost + hv_orange_cables_cost \
                                         + single_speed_gearbox_cost + powertrain_cooling_loop_cost \
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
                          * adj_factor * learn * quantity

        adj_factor = _cache[powertrain_type, 'HVAC']['dollar_adjustment']
        quantity = _cache[powertrain_type, 'HVAC']['quantity']
        hvac_cost = eval(_cache[powertrain_type, 'HVAC']['value'], {'np': np}, locals_dict) \
                    * adj_factor * learn * quantity

        diesel_engine_cost_scaler = 1
        if diesel_flag == 1:
            diesel_engine_cost_scaler = eval(_cache['ALL', 'diesel_engine_cost_scaler']['value'], {'np': np}, locals_dict)

        engine_cost = (cyl_cost + liter_cost) * turb_scaler * diesel_engine_cost_scaler \
                      + deac_pd_cost + deac_fc_cost \
                      + cegr_cost + atk2_cost + gdi_cost \
                      + turb12_cost + turb11_cost \
                      + twc_cost + gpf_cost + diesel_eas_cost

        driveline_cost = trans_cost \
                         + high_eff_alt_cost + start_stop_cost \
                         + ac_leakage_cost + ac_efficiency_cost \
                         + lv_battery_cost + hvac_cost

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

                df['value'] = df['value'] \
                    .apply(lambda x: str.replace(x, 'max(', 'np.maximum(').replace('min(', 'np.minimum('))

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
