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
        results = []

        elec_class, market_class_id, model_year = vehicle.electrification_class, vehicle.market_class_id, vehicle.model_year
        ec_dict = {'N': 'ICE', 'EV': 'BEV', 'HEV': 'HEV', 'PHEV': 'PHEV', 'FCV': 'BEV'}
        powertrain_type = ec_dict[elec_class]

        # markups and learning
        MARKUP_ICE = eval(_cache['ICE', 'markup']['value'], {}, locals())
        MARKUP_HEV = eval(_cache['HEV', 'markup']['value'], {}, locals())
        MARKUP_PHEV = eval(_cache['PHEV', 'markup']['value'], {}, locals())
        MARKUP_BEV = eval(_cache['BEV', 'markup']['value'], {}, locals())
        MARKUP_ALL = eval(_cache['ALL', 'markup']['value'], {}, locals())

        learning_rate = eval(_cache['ALL', 'learning_rate']['value'], {}, locals())
        learning_start = eval(_cache['ALL', 'learning_start']['value'], {}, locals())
        legacy_sales_scaler_ice = eval(_cache['ICE', 'legacy_sales_learning_scaler']['value'], {}, locals())
        legacy_sales_scaler_pev = eval(_cache['PEV', 'legacy_sales_learning_scaler']['value'], {}, locals())
        sales_scaler_ice = eval(_cache['ICE', 'sales_scaler']['value'], {}, locals())
        sales_scaler_pev = eval(_cache['PEV', 'sales_scaler']['value'], {}, locals())
        cumulative_sales_ice = sales_scaler_ice * (model_year - learning_start)
        cumulative_sales_pev = sales_scaler_pev * (model_year - learning_start)
        learning_factor_ice = ((cumulative_sales_ice + legacy_sales_scaler_ice) / legacy_sales_scaler_ice) ** learning_rate
        learning_factor_pev = ((cumulative_sales_pev + legacy_sales_scaler_pev) / legacy_sales_scaler_pev) ** learning_rate

        weight_bins = [0, 3200, 3800, 4400, 5000, 5600, 6200, 14000]
        tractive_motor = 'dual'
        if market_class_id.__contains__('non_hauling') or powertrain_type == 'HEV':
            tractive_motor = 'single'

        for idx, row in pkg_df.iterrows():

            trans_cost = cyl_cost = liter_cost = 0
            high_eff_alt_cost = start_stop_cost = deac_pd_cost = deac_fc_cost = cegr_cost = atk2_cost = gdi_cost = 0
            turb12_cost = turb11_cost = 0
            twc_cost = gpf_cost = 0
            ac_leakage_cost = ac_efficiency_cost = 0
            battery_cost = electrified_powertrain_cost = 0
            turb_scaler = 1 # default value adjusted below for turb packages

            # powertrain costs for anything with a liquid fueled engine
            if powertrain_type == 'ICE' or powertrain_type == 'HEV' or powertrain_type == 'PHEV':

                # PGM costs and loadings
                PT_USD_PER_OZ = eval(_cache['ALL', 'pt_dollars_per_oz']['value'], {}, locals())
                PD_USD_PER_OZ = eval(_cache['ALL', 'pd_dollars_per_oz']['value'], {}, locals())
                RH_USD_PER_OZ = eval(_cache['ALL', 'rh_dollars_per_oz']['value'], {}, locals())
                PT_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pt_grams_per_liter']['value'], {}, locals())
                PD_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_pd_grams_per_liter']['value'], {}, locals())
                RH_GRAMS_PER_LITER_TWC = eval(_cache['ALL', 'twc_rh_grams_per_liter']['value'], {}, locals())
                PT_GRAMS_PER_LITER_GPF = eval(_cache['ALL', 'gpf_pt_grams_per_liter']['value'], {}, locals())
                PD_GRAMS_PER_LITER_GPF = eval(_cache['ALL', 'gpf_pd_grams_per_liter']['value'], {}, locals())
                RH_GRAMS_PER_LITER_GPF = eval(_cache['ALL', 'gpf_rh_grams_per_liter']['value'], {}, locals())
                OZ_PER_GRAM = eval(_cache['ALL', 'troy_oz_per_gram']['value'], {}, locals())  # note that these are Troy ounces

                turb_input_scaler = eval(_cache['ALL', 'turb_scaler']['value'], {}, locals())
                gasoline_flag = row['gas_fuel']
                diesel_flat = row['diesel_fuel']

                # determine trans and calc cost
                trx_idx = row['cost_curve_class'].find('TRX')
                trans = row['cost_curve_class'][trx_idx:trx_idx+5]
                adj_factor = _cache['ALL', trans]['dollar_adjustment']
                trans_cost = eval(_cache['ALL', trans]['value'], {}, locals()) \
                             * adj_factor * learning_factor_ice

                # cylinder cost
                CYL = row['engine_cylinders']
                adj_factor = _cache['ALL', 'dollars_per_cylinder']['dollar_adjustment']
                cyl_cost = eval(_cache['ALL', 'dollars_per_cylinder']['value'], {}, locals()) \
                           * adj_factor * learning_factor_ice

                # displacement cost
                LITERS = row['engine_displacement_L']
                adj_factor = _cache['ALL', 'dollars_per_liter']['dollar_adjustment']
                liter_cost = eval(_cache['ALL', 'dollars_per_liter']['value'], {}, locals()) \
                             * adj_factor * learning_factor_ice

                # high efficiency alternator cost
                flag = row['high_eff_alternator']
                if flag == 1:
                    adj_factor = _cache['ALL', 'high_eff_alternator']['dollar_adjustment']
                    high_eff_alt_cost = eval(_cache['ALL', 'high_eff_alternator']['value'], {}, locals()) \
                                        * adj_factor * learning_factor_ice

                # start_stop cost
                flag = row['start_stop']
                if flag == 1:
                    CURBWT = row['etw_lbs'] - 300
                    adj_factor = _cache['ALL', 'start_stop']['dollar_adjustment']
                    start_stop_cost = eval(_cache['ALL', 'start_stop']['value'], {}, locals()) \
                                      * adj_factor * learning_factor_ice

                # deac_pd cost
                flag = row['deac_pd']
                if flag == 1:
                    adj_factor = _cache['ALL', 'deac_pd']['dollar_adjustment']
                    deac_pd_cost = eval(_cache['ALL', 'deac_pd']['value'], {}, locals()) \
                                   * adj_factor * learning_factor_ice

                # deac_fc cost
                flag = row['deac_fc']
                if flag == 1:
                    adj_factor = _cache['ALL', 'deac_fc']['dollar_adjustment']
                    deac_fc_cost = eval(_cache['ALL', 'deac_fc']['value'], {}, locals()) \
                                   * adj_factor * learning_factor_ice

                # cegr cost
                flag = row['cegr']
                if flag == 1:
                    adj_factor = _cache['ALL', 'cegr']['dollar_adjustment']
                    cegr_cost = eval(_cache['ALL', 'cegr']['value'], {}, locals()) \
                                   * adj_factor * learning_factor_ice

                # atk2 cost
                flag = row['atk2']
                if flag == 1:
                    adj_factor = _cache['ALL', 'atk2']['dollar_adjustment']
                    atk2_cost = eval(_cache['ALL', 'atk2']['value'], {}, locals()) \
                                * adj_factor * learning_factor_ice

                # gdi cost
                flag = row['gdi']
                if flag == 1:
                    adj_factor = _cache['ALL', 'gdi']['dollar_adjustment']
                    gdi_cost = eval(_cache['ALL', 'gdi']['value'], {}, locals()) \
                                * adj_factor * learning_factor_ice

                # turb12 cost
                flag = row['turb12']
                if flag == 1:
                    adj_factor = _cache['ALL', 'turb12']['dollar_adjustment']
                    turb12_cost = eval(_cache['ALL', 'turb12']['value'], {}, locals()) \
                                  * adj_factor * learning_factor_ice
                    turb_scaler = turb_input_scaler

                # turb11 cost
                flag = row['turb11']
                if flag == 1:
                    adj_factor = _cache['ALL', 'turb11']['dollar_adjustment']
                    turb11_cost = eval(_cache['ALL', 'turb11']['value'], {}, locals()) \
                                  * adj_factor * learning_factor_ice
                    turb_scaler = turb_input_scaler

                # 3-way catalyst cost
                if gasoline_flag == 1:
                    adj_factor_sub = _cache['ALL', 'twc_substrate']['dollar_adjustment']
                    adj_factor_wash = _cache['ALL', 'twc_washcoat']['dollar_adjustment']
                    adj_factor_can = _cache['ALL', 'twc_canning']['dollar_adjustment']
                    TWC_SWEPT_VOLUME = eval(_cache['ALL', 'twc_swept_volume']['value'], {}, locals())
                    substrate = eval(_cache['ALL', 'twc_substrate']['value'], {}, locals()) \
                                * adj_factor_sub * learning_factor_ice
                    washcoat = eval(_cache['ALL', 'twc_washcoat']['value'], {}, locals()) \
                               * adj_factor_wash * learning_factor_ice
                    canning = eval(_cache['ALL', 'twc_canning']['value'], {}, locals()) \
                              * adj_factor_can * learning_factor_ice
                    pgm = eval(_cache['ALL', 'twc_pgm']['value'], {}, locals())
                    twc_cost = substrate + washcoat + canning + pgm

                # gpf cost
                flag = 1
                if flag == 1 and gasoline_flag == 1:
                    adj_factor_sub = _cache['ALL', 'gpf_substrate']['dollar_adjustment']
                    adj_factor_wash = _cache['ALL', 'gpf_washcoat']['dollar_adjustment']
                    adj_factor_can = _cache['ALL', 'gpf_canning']['dollar_adjustment']
                    GPF_SWEPT_VOLUME = eval(_cache['ALL', 'gpf_swept_volume']['value'], {}, locals())
                    substrate = eval(_cache['ALL', 'gpf_substrate']['value'], {}, locals()) \
                                * adj_factor_sub * learning_factor_ice
                    washcoat = eval(_cache['ALL', 'gpf_washcoat']['value'], {}, locals()) \
                               * adj_factor_wash * learning_factor_ice
                    canning = eval(_cache['ALL', 'gpf_canning']['value'], {}, locals()) \
                              * adj_factor_can * learning_factor_ice
                    pgm = eval(_cache['ALL', 'gpf_pgm']['value'], {}, locals())
                    gpf_cost = substrate + washcoat + canning + pgm

            if powertrain_type == 'HEV' or powertrain_type == 'PHEV' or powertrain_type == 'BEV':

                if powertrain_type == 'HEV':
                    learn = learning_factor_ice
                else:
                    learn = learning_factor_pev

                # battery cost
                KWH = row['battery_kwh']
                adj_factor = _cache[powertrain_type, 'battery']['dollar_adjustment']
                battery_cost = eval(_cache[powertrain_type, 'battery']['value'], {}, locals()) \
                               * adj_factor * learn

                # electrified powertrain cost
                KW = row['motor_kw'] # what will this be called in the passed df?

                adj_factor = _cache[powertrain_type, f'motor_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'motor_{tractive_motor}']['quantity']
                motor_cost = eval(_cache[powertrain_type, f'motor_{tractive_motor}']['value'], {}, locals()) \
                             * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, f'inverter_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'inverter_{tractive_motor}']['quantity']
                inverter_cost = eval(_cache[powertrain_type, f'inverter_{tractive_motor}']['value'], {}, locals()) \
                                * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'induction_motor_{tractive_motor}']['quantity']
                induction_motor_cost = eval(_cache[powertrain_type, f'induction_motor_{tractive_motor}']['value'], {}, locals()) \
                                       * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'induction_inverter_{tractive_motor}']['quantity']
                induction_inverter_cost = eval(_cache[powertrain_type, f'induction_inverter_{tractive_motor}']['value'], {}, locals()) \
                                          * adj_factor * learn * quantity

                dcdc_converter_kw = eval(_cache[powertrain_type, 'DCDC_converter_kW']['value'], {}, locals())
                if powertrain_type == 'HEV':
                    obc_kw = 0
                elif powertrain_type == 'PHEV':
                    if KWH < 7:
                        obc_kw = 0.7
                    elif KWH < 10:
                        obc_kw = 1.1
                    else:
                        obc_kw = 1.9
                else:
                    if KWH < 70:
                        obc_kw = 7
                    elif KWH < 100:
                        obc_kw = 11
                    else:
                        obc_kw = 19
                OBC_AND_DCDC_CONVERTER_KW = dcdc_converter_kw + obc_kw
                adj_factor = _cache[powertrain_type, 'OBC_and_DCDC_converter']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'OBC_and_DCDC_converter']['quantity']
                obc_and_dcdc_converter_cost = eval(_cache[powertrain_type, 'OBC_and_DCDC_converter']['value'], {}, locals()) \
                                              * adj_factor * learn * quantity

                CURBWT = row['etw_lbs'] - 300
                VEHICLE_SIZE_CLASS = weight_bins.index(min([v for v in weight_bins if CURBWT < v])) # TODO where is this coming from, if we keep this?
                adj_factor = _cache[powertrain_type, 'HV_orange_cables']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'HV_orange_cables']['quantity']
                hv_orange_cables_cost = eval(_cache[powertrain_type, 'HV_orange_cables']['value'], {}, locals()) \
                                        * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, 'LV_battery']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'LV_battery']['quantity']
                lv_battery_cost = eval(_cache[powertrain_type, 'LV_battery']['value'], {}, locals()) \
                                  * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, 'HVAC']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'HVAC']['quantity']
                hvac_cost = eval(_cache[powertrain_type, 'HVAC']['value'], {}, locals()) \
                            * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['quantity']
                single_speed_gearbox_cost = eval(_cache[powertrain_type, f'single_speed_gearbox_{tractive_motor}']['value'], {}, locals()) \
                                            * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['quantity']
                powertrain_cooling_loop_cost = eval(_cache[powertrain_type, f'powertrain_cooling_loop_{tractive_motor}']['value'], {}, locals()) \
                                               * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, 'charging_cord_kit']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'charging_cord_kit']['quantity']
                charging_cord_kit_cost = eval(_cache[powertrain_type, 'charging_cord_kit']['value'], {}, locals()) \
                                         * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, 'DC_fast_charge_circuitry']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'DC_fast_charge_circuitry']['quantity']
                dc_fast_charge_circuitry_cost = eval(_cache[powertrain_type, 'DC_fast_charge_circuitry']['value'], {}, locals()) \
                                                * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, 'power_management_and_distribution']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'power_management_and_distribution']['quantity']
                power_management_and_distribution_cost = eval(_cache[powertrain_type, 'power_management_and_distribution']['value'], {}, locals()) \
                                                         * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, 'brake_sensors_actuators']['dollar_adjustment']
                quantity = _cache[powertrain_type, 'brake_sensors_actuators']['quantity']
                brake_sensors_actuators_cost = eval(_cache[powertrain_type, 'brake_sensors_actuators']['value'], {}, locals()) \
                                               * adj_factor * learn * quantity

                adj_factor = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['dollar_adjustment']
                quantity = _cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['quantity']
                additional_pair_of_half_shafts_cost = eval(_cache[powertrain_type, f'additional_pair_of_half_shafts_{tractive_motor}']['value'], {}, locals()) \
                                                      * adj_factor * learn * quantity

                electrified_powertrain_cost = battery_cost + motor_cost + inverter_cost \
                                              + induction_motor_cost + induction_inverter_cost \
                                              + obc_and_dcdc_converter_cost + hv_orange_cables_cost + lv_battery_cost \
                                              + hvac_cost + single_speed_gearbox_cost + powertrain_cooling_loop_cost \
                                              + charging_cord_kit_cost + dc_fast_charge_circuitry_cost \
                                              + power_management_and_distribution_cost + brake_sensors_actuators_cost \
                                              + additional_pair_of_half_shafts_cost

            # ac leakage cost
            flag = 1
            if flag == 1:
                adj_factor = _cache['ALL', 'ac_leakage']['dollar_adjustment']
                ac_leakage_cost = eval(_cache['ALL', 'ac_leakage']['value'], {}, locals()) \
                                  * adj_factor * learning_factor_ice

            # ac efficiency cost
            flag = 1
            if flag == 1:
                adj_factor = _cache['ALL', 'ac_efficiency']['dollar_adjustment']
                ac_efficiency_cost = eval(_cache['ALL', 'ac_efficiency']['value'], {}, locals()) \
                                     * adj_factor * learning_factor_ice

            powertrain_cost = trans_cost \
                              + (cyl_cost + liter_cost) * turb_scaler \
                              + high_eff_alt_cost + start_stop_cost \
                              + deac_pd_cost + deac_fc_cost \
                              + cegr_cost + atk2_cost + gdi_cost \
                              + turb12_cost + turb11_cost \
                              + twc_cost + gpf_cost \
                              + ac_leakage_cost + ac_efficiency_cost\
                              + electrified_powertrain_cost

            results.append(powertrain_cost)

        return results

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
            omega_log.logwrite('\nInitializing PowertrainCost from %s...' % filename, echo_console=True)
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
