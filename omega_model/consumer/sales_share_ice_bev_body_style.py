"""

**Implements a portion of the GCAM model related to the relative shares of ICE and BEV vehicles as a function
of relative generalized costs and assumptions about consumer acceptance over time (the S-shaped adoption curve).**

Relative shares are converted to absolute shares for use in the producer compliance search.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents GCAM consumer model input parameters.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,consumer.sales_share_ice_bev_body_style,input_template_version:,0.11

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,start_year,annual_vmt,price_amortization_period,share_weight,discount_rate,o_m_costs,average_occupancy,logit_exponent_mu
        sedan_wagon.BEV,2020,12000,5,0.142,0.1,1600,1.58,-8
        sedan_wagon.BEV,2021,12000,5,0.142,0.1,1600,1.58,-8
        sedan_wagon.BEV,2022,12000,5,0.168,0.1,1600,1.58,-8

Data Column Name and Description

:market_class_id:
    Vehicle market class ID, e.g. 'sedan_wagon.ICE'

:start_year:
    Start year of parameters, parameters apply until the next available start year

:annual_vmt:
    Vehicle miles travelled per year

:payback_years:
    Payback period, in years

:price_amortization_period:
    Price amorization period, in years

:share_weight:
    Share weight [0..1]

:discount_rate:
    Discount rate [0..1]

:o_m_costs:
    Operating and maintenance costs, dollars per year

:average_occupancy:
    Average vehicle occupancy, number of people

:logit_exponent_mu:
    Logit exponent, mu

----

**CODE**

"""
import numpy as np

print('importing %s' % __file__)

from omega_model import *
from context.new_vehicle_market import NewVehicleMarket
from context.fuel_prices import FuelPrice
from common.omega_functions import sales_weight_average_dataframe
from common import TRUE, FALSE

import math


class SalesShare(OMEGABase, SalesShareBase):
    """
    Loads and provides access to GCAM consumer response parameters.

    """
    _data = dict()
    _calibration_data = dict()

    prev_producer_decisions_and_responses = []

    @staticmethod
    def gcam_supports_market_class(market_class_id):
        """
        Determine if gcam supports the given market class ID.

        Args:
            market_class_id (str): market class id, e.g. 'hauling.ICE'

        Returns:
            ``True`` if gcam has parameters for the given market class ID
        """
        return market_class_id in SalesShare._data

    @staticmethod
    def get_gcam_params(calendar_year, market_class_id):
        """
        Get GCAM parameters for the given calendar year and market class.

        Args:
            calendar_year (int): the year to get parameters for
            market_class_id (str): market class id, e.g. 'hauling.ICE'

        Returns:
            GCAM parameters for the given calendar year and market class

        """
        cache_key = (calendar_year, market_class_id)

        if cache_key not in SalesShare._data:

            start_years = SalesShare._data[market_class_id]['start_year']
            if len(start_years[start_years <= calendar_year]) > 0:
                calendar_year = max(start_years[start_years <= calendar_year])

                SalesShare._data[cache_key] = SalesShare._data[market_class_id, calendar_year]
            else:
                raise Exception('Missing GCAM parameters for %s, %d or prior' % (market_class_id, calendar_year))

        return SalesShare._data[cache_key]

    @staticmethod
    def calc_consumer_generalized_cost(calendar_year, market_class_data, market_class_id, producer_decision):
        """

        Args:
            calendar_year (int): calendar year to calculate market shares in
            market_class_data (DataFrame): DataFrame with 'average_ALT_modified_cross_subsidized_price_MC' columns,
                where MC = market class ID
            market_class_id (str}: e.g. 'hauling.ICE'
            producer_decision (Series): selected producer compliance option with
                'average_ALT_retail_fuel_price_dollars_per_unit_MC',
                'average_ALT_onroad_direct_co2e_gpmi_MC', 'average_ALT_onroad_direct_kwh_pmi_MC' attributes,
                where MC = market class ID

        Returns:
            Consumer cost in $/mi

        """
        fuel_cost = producer_decision['average_ALT_retail_fuel_price_dollars_per_unit_%s' % market_class_id]
        gcam_data_cy = SalesShare.get_gcam_params(calendar_year, market_class_id)
        price_amortization_period = float(gcam_data_cy['price_amortization_period'])
        discount_rate = gcam_data_cy['discount_rate']
        annualization_factor = discount_rate + discount_rate / (
                ((1 + discount_rate) ** price_amortization_period) - 1)

        if type(market_class_data) is pd.DataFrame:
            total_capital_costs = market_class_data[
                'average_ALT_modified_cross_subsidized_price_%s' % market_class_id].values
        else:
            total_capital_costs = market_class_data[
                'average_ALT_modified_cross_subsidized_price_%s' % market_class_id]

        average_co2e_gpmi = producer_decision['average_ALT_onroad_direct_co2e_gpmi_%s' % market_class_id]
        average_kwh_pmi = producer_decision['average_ALT_onroad_direct_kwh_pmi_%s' % market_class_id]
        carbon_intensity_gasoline = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                  'direct_co2e_grams_per_unit')
        refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                          'refuel_efficiency')
        recharge_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'US electricity',
                                                            'refuel_efficiency')
        annual_o_m_costs = gcam_data_cy['o_m_costs']

        fuel_cost_per_VMT = \
            FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', 'US electricity') * \
            average_kwh_pmi / recharge_efficiency

        fuel_cost_per_VMT += fuel_cost * average_co2e_gpmi / carbon_intensity_gasoline / refuel_efficiency
        # consumer_generalized_cost_dollars = total_capital_costs
        annualized_capital_costs = annualization_factor * total_capital_costs
        annual_VMT = float(gcam_data_cy['annual_vmt'])
        total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / annual_VMT
        total_cost_w_fuel_per_VMT = total_non_fuel_costs_per_VMT + fuel_cost_per_VMT
        total_cost_w_fuel_per_PMT = total_cost_w_fuel_per_VMT / gcam_data_cy['average_occupancy']

        return total_cost_w_fuel_per_PMT

    @staticmethod
    def calc_shares_gcam(producer_decision, market_class_data, calendar_year,
                         parent_market_class, child_market_classes):
        """
        Determine consumer desired ICE/BEV market shares for the given vehicles, their costs, etc.
        Relative shares are calculated within the parent market class and then converted to absolute shares.

        Args:
            producer_decision (Series): selected producer compliance option with
                'average_ALT_retail_fuel_price_dollars_per_unit_MC',
                'average_ALT_onroad_direct_co2e_gpmi_MC', 'average_ALT_onroad_direct_kwh_pmi_MC' attributes,
                where MC = market class ID
            market_class_data (DataFrame): DataFrame with 'average_ALT_modified_cross_subsidized_price_MC' columns,
                where MC = market class ID
            calendar_year (int): calendar year to calculate market shares in
            parent_market_class (str): e.g. 'non_hauling'
            child_market_classes ([strs]): e.g. ['non_hauling.BEV', 'non_hauling.ICE']

        Returns:
            A copy of ``market_class_data`` with demanded ICE/BEV share columns by market class, e.g.
            'consumer_share_frac_MC', 'consumer_abs_share_frac_MC', and 'consumer_generalized_cost_dollars_MC' where
            MC = market class ID

        """
        from context.onroad_fuels import OnroadFuel

        if omega_globals.options.flat_context:
            calendar_year = omega_globals.options.flat_context_year

        sales_share_denominator = 0
        sales_share_numerator = dict()

        market_class_data['consumer_constrained_%s' % parent_market_class] = FALSE

        for pass_num in [0, 1]:
            for market_class_id in child_market_classes:
                if pass_num == 0:
                    total_cost_w_fuel_per_PMT = SalesShare.calc_consumer_generalized_cost(calendar_year,
                                                                                          market_class_data,
                                                                                          market_class_id,
                                                                                          producer_decision)

                    market_class_data['consumer_generalized_cost_dollars_%s' % market_class_id] = \
                        total_cost_w_fuel_per_PMT

                    gcam_data_cy = SalesShare.get_gcam_params(calendar_year, market_class_id)
                    logit_exponent_mu = gcam_data_cy['logit_exponent_mu']
                    sales_share_numerator[market_class_id] = gcam_data_cy['share_weight'] * (
                            total_cost_w_fuel_per_PMT ** logit_exponent_mu)

                    sales_share_denominator += sales_share_numerator[market_class_id]

                else:
                    min_constraints = omega_globals.constraints['min_constraints_%s' % parent_market_class]
                    max_constraints = omega_globals.constraints['max_constraints_%s' % parent_market_class]

                    demanded_share = sales_share_numerator[market_class_id] / sales_share_denominator

                    # constrain relative (and by extension, absolute) shares RV
                    share_name = market_class_id.replace(parent_market_class + '.', '')
                    demanded_share = np.minimum(np.maximum(min_constraints[share_name], demanded_share),
                                                max_constraints[share_name])

                    if all(demanded_share == max_constraints[share_name]):
                        market_class_data['consumer_constrained_%s' % parent_market_class] = TRUE

                    parent_share = market_class_data['consumer_abs_share_frac_%s' % parent_market_class].values

                    demanded_absolute_share = demanded_share * parent_share

                    market_class_data['consumer_share_frac_%s' % market_class_id] = demanded_share
                    market_class_data['consumer_abs_share_frac_%s' % market_class_id] = demanded_absolute_share

                    # distribute absolute shares to ALT / NO_ALT, NO_ALT first:
                    for alt in ['NO_ALT', 'ALT']:
                        share_id = 'consumer_abs_share_frac_%s.%s' % (market_class_id, alt)
                        if alt == 'NO_ALT':
                            market_class_data[share_id] = \
                                min_constraints[share_id.replace('consumer', 'producer')] * parent_share
                            demanded_absolute_share -= market_class_data[share_id]
                        else:
                            market_class_data[share_id] = demanded_absolute_share

        return market_class_data.copy()

    @staticmethod
    def calc_shares(calendar_year, compliance_id, producer_decision, market_class_data, mc_parent, mc_pair):
        """
        Determine consumer desired market shares for the given vehicles, their costs, etc.

        Args:
            calendar_year (int): calendar year to calculate market shares in
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            producer_decision (Series): selected producer compliance option with
                'average_retail_fuel_price_dollars_per_unit_MC',
                'average_onroad_direct_co2e_gpmi_MC', 'average_onroad_direct_kwh_pmi_MC' attributes,
                where MC = market category ID
                'average_ALT_retail_fuel_price_dollars_per_unit_MC',
                'average_ALT_onroad_direct_co2e_gpmi_MC', 'average_ALT_onroad_direct_kwh_pmi_MC' attributes,
                where MC = market class ID
            market_class_data (DataFrame): DataFrame with 'average_ALT_modified_cross_subsidized_price_MC' columns,
                where MC = market class ID
            mc_parent (str): e.g. '' for the total market, 'hauling' or 'non_hauling', etc
            mc_pair ([strs]): e.g. '['hauling', 'non_hauling'] or ['hauling.ICE', 'hauling.BEV'], etc

        Returns:
            A copy of ``market_class_data`` with demanded share columns by market class, e.g.
            'consumer_share_frac_MC', 'consumer_abs_share_frac_MC', and 'consumer_generalized_cost_dollars_MC' where
            MC = market class ID

        """

        # calculate the absolute market shares by traversing the market class tree and calling appropriate
        # share-calculation methods at each level

        # for the sake of the demo, the consumer hauling and non_hauling absolute shares are taken from the producer,
        # which gets them from the context size class projections and the makeup of the base year fleet.
        # If the hauling/non_hauling shares were responsive (endogenous), methods to calculate these values would
        # be called here.

        from producer.vehicles import Vehicle

        # if omega_globals.options.generate_context_calibration_files:
        context_total_sales = NewVehicleMarket.new_vehicle_data(calendar_year)

        if 'sedan_wagon' in Vehicle.mfr_base_year_share_data[compliance_id]:
            context_sedan_wagon_share = \
                (NewVehicleMarket.new_vehicle_data(calendar_year, context_body_style='sedan_wagon') /
                context_total_sales *
                Vehicle.mfr_base_year_share_data[compliance_id]['sedan_wagon'])
        else:
            context_sedan_wagon_share = 0

        if 'cuv_suv_van' in Vehicle.mfr_base_year_share_data[compliance_id]:
            context_cuv_suv_van_share = \
                (NewVehicleMarket.new_vehicle_data(calendar_year, context_body_style='cuv_suv_van') /
                context_total_sales *
                Vehicle.mfr_base_year_share_data[compliance_id]['cuv_suv_van'])
        else:
            context_cuv_suv_van_share = 0

        if 'pickup' in Vehicle.mfr_base_year_share_data[compliance_id]:
            context_pickup_share = \
                (NewVehicleMarket.new_vehicle_data(calendar_year, context_body_style='pickup') /
                 context_total_sales *
                 Vehicle.mfr_base_year_share_data[compliance_id]['pickup'])
        else:
            context_pickup_share = 0

        # renormalize shares
        denom = context_sedan_wagon_share + context_cuv_suv_van_share + context_pickup_share

        context_sedan_wagon_share /= denom
        context_cuv_suv_van_share /= denom
        context_pickup_share /= denom

        if len(market_class_data):
            market_class_data['consumer_abs_share_frac_sedan_wagon'] = context_sedan_wagon_share
        else:  # populate Series with at least one row
            market_class_data['consumer_abs_share_frac_sedan_wagon'] = [context_sedan_wagon_share]

        market_class_data['consumer_abs_share_frac_cuv_suv_van'] = context_cuv_suv_van_share
        market_class_data['consumer_abs_share_frac_pickup'] = context_pickup_share

        if all([SalesShare.gcam_supports_market_class(mc) for mc in mc_pair]):
            if len(mc_pair) > 1:
                # calculate desired ICE/BEV shares within hauling/non_hauling using methods based on the GCAM model:
                market_class_data = SalesShare.calc_shares_gcam(producer_decision, market_class_data, calendar_year,
                                                            mc_parent, mc_pair)
            else:
                # can't calculate ICE/BEV shares since there is only ICE or only BEV
                only_child = mc_pair[0]

                # populate fields that normally come from cross subsidy iteration
                market_class_data['average_ALT_cross_subsidized_price_%s' % only_child] = \
                    producer_decision['average_ALT_new_vehicle_mfr_cost_%s' % only_child]

                market_class_data['average_ALT_modified_cross_subsidized_price_%s' % only_child] = \
                    producer_decision['average_ALT_new_vehicle_mfr_cost_%s' % only_child]

                market_class_data['pricing_score'] = 0

                total_cost_w_fuel_per_PMT = SalesShare.calc_consumer_generalized_cost(calendar_year,
                                                                                      market_class_data,
                                                                                      only_child,
                                                                                      producer_decision)

                market_class_data['consumer_generalized_cost_dollars_%s' % only_child] = \
                    total_cost_w_fuel_per_PMT

                parent_share = market_class_data['consumer_abs_share_frac_%s' % mc_parent]

                market_class_data['consumer_share_frac_%s' % only_child] = 1.0
                market_class_data['consumer_abs_share_frac_%s' % only_child] = parent_share

                max_constraints = omega_globals.constraints['max_constraints_%s' % mc_parent]

                for alt in ['ALT', 'NO_ALT']:
                    only_child = mc_pair[0] + '.' + alt
                    market_class_data['consumer_share_frac_%s' % only_child] = \
                        1.0 * max_constraints['producer_abs_share_frac_%s' % only_child]
                    market_class_data['consumer_abs_share_frac_%s' % only_child] = \
                        parent_share * max_constraints['producer_abs_share_frac_%s' % only_child]

        return market_class_data

    @staticmethod
    def save_calibration(filename):
        """
            Save calibration data (if necessary) that aligns reference session market shares with context

        Args:
            filename (str): name of the calibration file

        """
        if omega_globals.options.standalone_run:
            filename = omega_globals.options.output_folder_base + filename

        calibration = pd.DataFrame.from_dict(SalesShare._calibration_data)

        calibration.to_csv(filename, columns=sorted(calibration.columns))

    @staticmethod
    def store_producer_decision_and_response(producer_decision_and_response):
        """
            Store producer decision and response (if necessary) for reference in future years

        Args:
            producer_decision_and_response (Series): producer decision and consumer response

        """
        SalesShare.prev_producer_decisions_and_responses.append(producer_decision_and_response)

    @staticmethod
    def calc_base_year_data(base_year_vehicles_df):
        """
            Calculate base year data (if necessary) such as sales-weighted curbweight, etc, if needed for reference
            in future years

        Args:
            base_year_vehicles_df (DataFrame): base year vehicle data

        """
        base_year = max(base_year_vehicles_df['model_year'].values)
        base_year_vehicles_df = base_year_vehicles_df[base_year_vehicles_df['model_year'] == base_year]

        base_year_reg_class_data = \
            base_year_vehicles_df.groupby(['reg_class_id']).apply(sales_weight_average_dataframe)

        # for rc in legacy_reg_classes:
        for rc in base_year_vehicles_df.reg_class_id.unique():
            for c in ['curbweight_lbs', 'rated_hp']:
                SalesShare._data['share_seed_data', base_year, rc, c] = base_year_reg_class_data[c][rc]

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

        # from producer.vehicles import Vehicle

        SalesShare._data.clear()
        SalesShare._calibration_data.clear()

        SalesShare.prev_producer_decisions_and_responses = []

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.11
        input_template_columns = {'market_class_id', 'start_year', 'annual_vmt',
                                  'price_amortization_period', 'share_weight', 'discount_rate',
                                  'o_m_costs', 'average_occupancy', 'logit_exponent_mu'
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            validation_dict = {'market_class_id': omega_globals.options.MarketClass.market_classes}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            SalesShare._data = df.set_index(['market_class_id', 'start_year']).sort_index().to_dict(orient='index')

            for mc in df['market_class_id'].unique():
                SalesShare._data[mc] = {'start_year': np.array(df['start_year'].loc[df['market_class_id'] == mc])}

            if omega_globals.options.generate_context_calibration_files:
                SalesShare._calibration_data = dict()

            else:
                SalesShare._calibration_data = \
                    pd.read_csv(omega_globals.options.sales_share_calibration_file).set_index('Unnamed: 0').to_dict()

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        from producer.manufacturers import Manufacturer
        from producer.vehicle_aggregation import VehicleAggregation
        from producer.vehicles import Vehicle, DecompositionAttributes

        from context.mass_scaling import MassScaling
        from context.body_styles import BodyStyles
        from context.glider_cost import GliderCost
        from context.fuel_prices import FuelPrice

        from policy.drive_cycles import DriveCycles
        from policy.policy_fuels import PolicyFuel
        from context.ip_deflators import ImplicitPriceDeflators

        from omega_model.omega import init_user_definable_decomposition_attributes, get_module

        init_fail = []

        # pull in reg classes before initializing classes that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=omega_globals.options.verbose)

        # pull in market classes before initializing classes that check market class validity
        omega_globals.options.market_classes_file = \
            omega_globals.options.omega_model_path + '/test_inputs/market_classes-body_style.csv'

        omega_globals.options.sales_share_file = \
            omega_globals.options.omega_model_path + '/test_inputs/sales_share_params_ice_bev_body_style.csv'

        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                                      verbose=omega_globals.options.verbose)

        module_name = get_template_name(omega_globals.options.offcycle_credits_file)
        omega_globals.options.OffCycleCredits = get_module(module_name).OffCycleCredits

        module_name = get_template_name(omega_globals.options.ice_vehicle_simulation_results_file)
        omega_globals.options.CostCloud = get_module(module_name).CostCloud

        module_name = get_template_name(omega_globals.options.sales_share_file)
        omega_globals.options.SalesShare = get_module(module_name).SalesShare

        module_name = get_template_name(omega_globals.options.powertrain_cost_input_file)
        omega_globals.options.PowertrainCost = get_module(module_name).PowertrainCost

        init_fail += init_user_definable_decomposition_attributes(omega_globals.options.verbose)

        init_fail += Manufacturer.init_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)

        from context.onroad_fuels import OnroadFuel  # needed for in-use fuel ID
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.SalesShare.init_from_file(omega_globals.options.sales_share_file,
                                                                     verbose=omega_globals.options.verbose)

        init_fail += BodyStyles.init_from_file(omega_globals.options.body_styles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += MassScaling.init_from_file(omega_globals.options.mass_scaling_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += NewVehicleMarket.init_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        # must come after NewVehicleMarket and OnroadFuel init for input validation
        init_fail += FuelPrice.init_from_file(omega_globals.options.context_fuel_prices_file,
                                              verbose=omega_globals.options.verbose)

        init_fail += ImplicitPriceDeflators.init_from_file(omega_globals.options.ip_deflators_file,
                                                          verbose=omega_globals.options.verbose)

        init_fail += GliderCost.init_from_file(omega_globals.options.glider_cost_input_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.PowertrainCost.init_from_file(omega_globals.options.powertrain_cost_input_file,
                                                   verbose=omega_globals.options.verbose)

        # init drive cycles PRIOR to CostCloud since CostCloud needs the drive cycle names for validation
        init_fail += DriveCycles.init_from_file(omega_globals.options.drive_cycles_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += omega_globals.options.CostCloud.\
            init_cost_clouds_from_files(omega_globals.options.ice_vehicle_simulation_results_file,
                                        omega_globals.options.bev_vehicle_simulation_results_file,
                                        omega_globals.options.phev_vehicle_simulation_results_file,
                                        verbose=omega_globals.options.verbose)

        init_fail += VehicleAggregation.init_from_file(omega_globals.options.vehicles_file,
                                                       verbose=omega_globals.options.verbose)

        init_fail += Vehicle.init_from_file(omega_globals.options.onroad_vehicle_calculations_file,
                                                 verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = 2021
            omega_globals.options.analysis_final_year = 2035

            # test market shares at different CO2e and price levels
            mcd = pd.DataFrame()
            for mc in omega_globals.options.MarketClass.market_classes:
                mcd['average_ALT_modified_cross_subsidized_price_%s' % mc] = [35000, 25000]
                mcd['average_ALT_onroad_direct_kwh_pmi_%s' % mc] = [.300, .300]
                mcd['average_onroad_direct_kwh_pmi_%s' % mc] = [0.250, 0.250]
                mcd['average_ALT_onroad_direct_co2e_gpmi_%s' % mc] = [125, 150]
                mcd['average_onroad_direct_co2e_gpmi_%s' % mc] = [125, 150]
                mcd['average_ALT_retail_fuel_price_dollars_per_unit_%s' % mc] = [2.75, 3.25]
                mcd['producer_abs_share_frac_%s' % mc] = [1/len(omega_globals.options.MarketClass.market_classes),
                                                          1/len(omega_globals.options.MarketClass.market_classes)]
                mcd['average_rated_hp_%s' % mc] = [250, 175]
                mcd['average_curbweight_lbs_%s' % mc] = [3500, 3750]

            for mcat in omega_globals.options.MarketClass.market_categories:
                mcd['average_new_vehicle_mfr_cost_%s' % mcat] = [35000, 25000]
                mcd['average_footprint_ft2_%s' % mcat] = [45, 45]

            share_demand = SalesShare.calc_shares(omega_globals.options.analysis_initial_year, 'Ford',
                                                  mcd.loc[0, :], mcd, 'sedan_wagon',
                                                  ['sedan_wagon.ICE', 'sedan_wagon.BEV'])

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
