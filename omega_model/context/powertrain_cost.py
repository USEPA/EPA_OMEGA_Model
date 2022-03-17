"""

**Routines to powertrain cost.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents vehicle technology options and costs by simulation class (cost curve class) and model year.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,0.3,dollar_basis:,``{optional_source_data_comment}``

Sample Data Columns
    .. csv-table::
        :widths: auto

        TODO: add sample

Data Column Name and Description
    :package:
        Unique row identifier, specifies the powertrain package

    TODO: add the rest of the columns

    CHARGE-DEPLETING SIMULATION RESULTS
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cd_ftp_1:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_2:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_3:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_ftp_4:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile
        :cd_hwfet:cert_direct_oncycle_kwh_per_mile: simulation result, kWh/mile

    :new_vehicle_mfr_cost_dollars:
        The manufacturer cost associated with the simulation results, based on vehicle technology content and model year.Note that the
         costs are converted in-code to 'analysis_dollar_basis' using the implicit_price_deflators input file.

    CHARGE-SUSTAINING SIMULATION RESULTS
        Column names must be consistent with the input data loaded by ``class drive_cycles.DriveCycles``

        :cs_ftp_1:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_ftp_2:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_ftp_3:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_ftp_4:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile
        :cs_hwfet:cert_direct_oncycle_co2e_grams_per_mile: simulation result, CO2e grams/mile

    TODO: add the rest of the flags...

    :high_eff_alternator:
        = 1 if vehicle qualifies for the high efficiency alternator off-cycle credit, = 0 otherwise

    :start_stop:
        = 1 if vehicle qualifies for the engine start-stop off-cycle credit, = 0 otherwise

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

    _max_year = 0  # maximum year of cost cloud data (e.g. 2050), set by ``init_cost_clouds_from_file()``

    @staticmethod
    def calc_cost(pkg_df, powertrain_type, model_year):
        """
        Calculate the value of the response surface equation for the given powertrain type, cost curve class (tech
        package) for the full factorial combination of the iterable terms.

        Args:
            pkg_df (DataFrame): the necessary information for developing cost estimates.
            powertrain_type (str): e.g. 'ICE', 'BEV' ...
            model_year (int): the model_year of the passed packages for which costs are needed

        Returns:
            A list of cost values indexed the same as pkg_df.

        """
        results = []

        # markup and learning
        MARKUP = eval(_cache[powertrain_type, 'markup']['value'], {}, locals())

        learning_rate = eval(_cache['ALL', 'learning_rate']['value'], {}, locals())
        learning_start = eval(_cache['ALL', 'learning_start']['value'], {}, locals())
        legacy_sales_scaler = eval(_cache[powertrain_type, 'legacy_sales_learning_scaler']['value'], {}, locals())
        sales_scaler = eval(_cache[powertrain_type, 'sales_scaler']['value'], {}, locals())
        cumulative_sales = sales_scaler * (model_year - learning_start)
        learning_factor = ((cumulative_sales + legacy_sales_scaler) / legacy_sales_scaler) ** learning_rate

        turb_input_scaler = eval(_cache[powertrain_type, 'turb_scaler']['value'], {}, locals())

        PT_USD_PER_OZ = eval(_cache[powertrain_type, 'pt_dollars_per_oz']['value'], {}, locals())
        PD_USD_PER_OZ = eval(_cache[powertrain_type, 'pd_dollars_per_oz']['value'], {}, locals())
        RH_USD_PER_OZ = eval(_cache[powertrain_type, 'rh_dollars_per_oz']['value'], {}, locals())
        PT_GRAMS_PER_LITER_TWC = eval(_cache[powertrain_type, 'twc_pt_grams_per_liter']['value'], {}, locals())
        PD_GRAMS_PER_LITER_TWC = eval(_cache[powertrain_type, 'twc_pd_grams_per_liter']['value'], {}, locals())
        RH_GRAMS_PER_LITER_TWC = eval(_cache[powertrain_type, 'twc_rh_grams_per_liter']['value'], {}, locals())
        PT_GRAMS_PER_LITER_GPF = eval(_cache[powertrain_type, 'gpf_pt_grams_per_liter']['value'], {}, locals())
        PD_GRAMS_PER_LITER_GPF = eval(_cache[powertrain_type, 'gpf_pd_grams_per_liter']['value'], {}, locals())
        RH_GRAMS_PER_LITER_GPF = eval(_cache[powertrain_type, 'gpf_rh_grams_per_liter']['value'], {}, locals())
        OZ_PER_GRAM = eval(_cache[powertrain_type, 'troy_oz_per_gram']['value'], {}, locals()) # note that these are Troy ounces

        if powertrain_type == 'ICE' or 'HEV' or 'PHEV':

            for idx, row in pkg_df.iterrows():

                high_eff_alt_cost = start_stop_cost = deac_pd_cost = deac_fc_cost = cegr_cost = atk2_cost = gdi_cost = 0
                turb12_cost = turb11_cost = 0
                twc_cost = gpf_cost = 0
                ac_leakage_cost = ac_efficiency_cost = 0
                turb_scaler = 1 # default value adjusted below for turb packages

                gasoline_flag = row['gas_fuel']
                diesel_flat = row['diesel_fuel']

                # determine trans and calc cost
                trx_idx = row['cost_curve_class'].find('TRX')
                trans = row['cost_curve_class'][trx_idx:trx_idx+5]
                adj_factor = _cache[powertrain_type, trans]['dollar_adjustment']
                trans_cost = eval(_cache[powertrain_type, trans]['value'], {}, locals()) \
                             * adj_factor * learning_factor

                # cylinder cost
                CYL = row['engine_cylinders']
                adj_factor = _cache[powertrain_type, 'dollars_per_cylinder']['dollar_adjustment']
                cyl_cost = eval(_cache[powertrain_type, 'dollars_per_cylinder']['value'], {}, locals()) \
                           * adj_factor * learning_factor

                # displacement cost
                LITERS = row['engine_displacement_L']
                adj_factor = _cache[powertrain_type, 'dollars_per_liter']['dollar_adjustment']
                liter_cost = eval(_cache[powertrain_type, 'dollars_per_liter']['value'], {}, locals()) \
                             * adj_factor * learning_factor

                # high efficiency alternator cost
                flag = row['high_eff_alternator']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'high_eff_alternator']['dollar_adjustment']
                    high_eff_alt_cost = eval(_cache[powertrain_type, 'high_eff_alternator']['value'], {}, locals()) \
                                        * adj_factor * learning_factor

                # start_stop cost
                flag = row['start_stop']
                if flag == 1:
                    CURBWT = row['etw_lbs'] - 300
                    adj_factor = _cache[powertrain_type, 'start_stop']['dollar_adjustment']
                    start_stop_cost = eval(_cache[powertrain_type, 'start_stop']['value'], {}, locals()) \
                                      * adj_factor * learning_factor

                # deac_pd cost
                flag = row['deac_pd']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'deac_pd']['dollar_adjustment']
                    deac_pd_cost = eval(_cache[powertrain_type, 'deac_pd']['value'], {}, locals()) \
                                   * adj_factor * learning_factor

                # deac_fc cost
                flag = row['deac_fc']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'deac_fc']['dollar_adjustment']
                    deac_fc_cost = eval(_cache[powertrain_type, 'deac_fc']['value'], {}, locals()) \
                                   * adj_factor * learning_factor

                # cegr cost
                flag = row['cegr']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'cegr']['dollar_adjustment']
                    cegr_cost = eval(_cache[powertrain_type, 'cegr']['value'], {}, locals()) \
                                   * adj_factor * learning_factor

                # atk2 cost
                flag = row['atk2']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'atk2']['dollar_adjustment']
                    atk2_cost = eval(_cache[powertrain_type, 'atk2']['value'], {}, locals()) \
                                * adj_factor * learning_factor

                # gdi cost
                flag = row['gdi']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'gdi']['dollar_adjustment']
                    gdi_cost = eval(_cache[powertrain_type, 'gdi']['value'], {}, locals()) \
                                * adj_factor * learning_factor

                # turb12 cost
                flag = row['turb12']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'turb12']['dollar_adjustment']
                    turb12_cost = eval(_cache[powertrain_type, 'turb12']['value'], {}, locals()) \
                                  * adj_factor * learning_factor
                    turb_scaler = turb_input_scaler

                # turb11 cost
                flag = row['turb11']
                if flag == 1:
                    adj_factor = _cache[powertrain_type, 'turb11']['dollar_adjustment']
                    turb11_cost = eval(_cache[powertrain_type, 'turb11']['value'], {}, locals()) \
                                  * adj_factor * learning_factor
                    turb_scaler = turb_input_scaler

                # 3-way catalyst cost
                if powertrain_type == 'ICE' or 'HEV' or 'PHEV' and gasoline_flag == 1:
                    adj_factor_sub = _cache[powertrain_type, 'twc_substrate']['dollar_adjustment']
                    adj_factor_wash = _cache[powertrain_type, 'twc_washcoat']['dollar_adjustment']
                    adj_factor_can = _cache[powertrain_type, 'twc_canning']['dollar_adjustment']
                    TWC_SWEPT_VOLUME = eval(_cache[powertrain_type, 'twc_swept_volume']['value'], {}, locals())
                    substrate = eval(_cache[powertrain_type, 'twc_substrate']['value'], {}, locals()) \
                                * adj_factor_sub * learning_factor
                    washcoat = eval(_cache[powertrain_type, 'twc_washcoat']['value'], {}, locals()) \
                               * adj_factor_wash * learning_factor
                    canning = eval(_cache[powertrain_type, 'twc_canning']['value'], {}, locals()) \
                              * adj_factor_can * learning_factor
                    pgm = eval(_cache[powertrain_type, 'twc_pgm']['value'], {}, locals())
                    twc_cost = substrate + washcoat + canning + pgm

                # gpf cost
                if powertrain_type == 'ICE' or 'HEV' or 'PHEV' and gasoline_flag == 1:
                    adj_factor_sub = _cache[powertrain_type, 'gpf_substrate']['dollar_adjustment']
                    adj_factor_wash = _cache[powertrain_type, 'gpf_washcoat']['dollar_adjustment']
                    adj_factor_can = _cache[powertrain_type, 'gpf_canning']['dollar_adjustment']
                    GPF_SWEPT_VOLUME = eval(_cache[powertrain_type, 'gpf_swept_volume']['value'], {}, locals())
                    substrate = eval(_cache[powertrain_type, 'gpf_substrate']['value'], {}, locals()) \
                                * adj_factor_sub * learning_factor
                    washcoat = eval(_cache[powertrain_type, 'gpf_washcoat']['value'], {}, locals()) \
                               * adj_factor_wash * learning_factor
                    canning = eval(_cache[powertrain_type, 'gpf_canning']['value'], {}, locals()) \
                              * adj_factor_can * learning_factor
                    pgm = eval(_cache[powertrain_type, 'gpf_pgm']['value'], {}, locals())
                    gpf_cost = substrate + washcoat + canning + pgm

                # ac leakage cost
                adj_factor = _cache['ALL', 'ac_leakage']['dollar_adjustment']
                ac_leakage_cost = eval(_cache['ALL', 'ac_leakage']['value'], {}, locals()) \
                                  * adj_factor * learning_factor

                # ac efficiency cost
                adj_factor = _cache['ALL', 'ac_efficiency']['dollar_adjustment']
                ac_efficiency_cost = eval(_cache['ALL', 'ac_efficiency']['value'], {}, locals()) \
                                     * adj_factor * learning_factor

                powertrain_cost = trans_cost + (cyl_cost + liter_cost) * turb_scaler + high_eff_alt_cost + start_stop_cost \
                                  + deac_pd_cost + deac_fc_cost + cegr_cost + atk2_cost + gdi_cost + turb12_cost + turb11_cost \
                                  + twc_cost + gpf_cost \
                                  + ac_leakage_cost + ac_efficiency_cost

                results.append(powertrain_cost)

        return results

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing PowertrainCost from %s...' % filename, echo_console=True)
        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'powertrain_type', 'item', 'value', 'dollar_basis', 'notes'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)
        if not template_errors:

            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:

                powertrain_type_item_pairs = zip(df['powertrain_type'], df['item'])

                for powertrain_type_item_pair in powertrain_type_item_pairs:
                        _cache[powertrain_type_item_pair] = dict()
                        powertrain_type, item = powertrain_type_item_pair

                        cost_info = df[(df['powertrain_type'] == powertrain_type) & (df['item'] == item)].iloc[0]

                        _cache[powertrain_type_item_pair] = {'value': dict(), 'dollar_adjustment': 1}

                        if cost_info['dollar_basis'] > 0:
                            adj_factor = dollar_adjustment_factor('ip_deflators', int(cost_info['dollar_basis']))
                            _cache[powertrain_type_item_pair]['dollar_adjustment'] = adj_factor

                        _cache[powertrain_type_item_pair]['value'] = compile(cost_info['value'], '<string>', 'eval')

        return template_errors
