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

       input_template_name:,``[module_name]``,input_template_version:,0.12

Sample Header
    .. csv-table::

       input_template_name:,consumer.sales_share,input_template_version:,0.12

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,start_year,annual_vmt,payback_years,price_amortization_period,share_weight,discount_rate,o_m_costs,average_occupancy,logit_exponent_mu
        hauling.BEV,2020,12000,5,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2021,12000,5,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2022,12000,5,5,0.168,0.1,1600,1.58,-8

Data Column Name and Description

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

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

import math

sedan_wagon_constants = {'Constant': 0.654042341423643,
                 'Xprice': -0.0180171809091689,
                 'Xcpm': -0.461372743184231,
                 'Xfoot': 0.557877300321091,
                 'Xhpwt': 0.00920608496452878,
                 'y_lag': 0.76336704353215,
                 'inc_growth': -0.663778795048909,
                 'y_hat_historic': 2.599148

                 }

cuv_suv_van_constants = {'Constant': -0.855185491214764,
                 'Xprice': -0.0180171809091689,
                 'Xcpm': -0.107849853426846,
                 'Xfoot': 0.188693199606348,
                 'Xhpwt': 0.104957947064753,
                 'y_lag': 0.814995420534703,
                 'inc_growth': 0.878066934600003,
                 'y_hat_historic': 3.035549
                 }

pickup_constants = {'Constant': -0.220428824716918,
                 'Xprice': -0.0180171809091689,
                 'Xcpm': -0.747888235402595,
                 'Xfoot': 0.188693199606348,
                 'Xhpwt': 0.103118883181103,
                 'y_lag': 0.863491530280403,
                 'inc_growth': -0.319399443869625,
                 'y_hat_historic': 1.893975
                 }

class SalesShare(OMEGABase, SalesShareBase):
    """
    Loads and provides access to GCAM consumer response parameters.

    """
    _data = dict()

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
    def calc_shares_gcam(producer_decision, market_class_data, calendar_year,
                         parent_market_class, child_market_classes):
        """
        Determine consumer desired ICE/BEV market shares for the given vehicles, their costs, etc.
        Relative shares are calculated within the parent market class and then converted to absolute shares.

        Args:
            producer_decision (Series): selected producer compliance option with
                'average_retail_fuel_price_dollars_per_unit_MC',
                'average_onroad_direct_co2e_gpmi_MC', 'average_onroad_direct_kwh_pmi_MC' attributes,
                where MC = market class ID
            market_class_data (DataFrame): DataFrame with 'average_modified_cross_subsidized_price_MC' columns,
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

        for pass_num in [0, 1]:
            for market_class_id in child_market_classes:
                if pass_num == 0:
                    fuel_cost = producer_decision['average_retail_fuel_price_dollars_per_unit_%s' % market_class_id]

                    gcam_data_cy = SalesShare.get_gcam_params(calendar_year, market_class_id)

                    logit_exponent_mu = gcam_data_cy['logit_exponent_mu']

                    price_amortization_period = float(gcam_data_cy['price_amortization_period'])
                    discount_rate = gcam_data_cy['discount_rate']
                    annualization_factor = discount_rate + discount_rate / (
                            ((1 + discount_rate) ** price_amortization_period) - 1)

                    total_capital_costs = market_class_data[
                        'average_modified_cross_subsidized_price_%s' % market_class_id].values
                    average_co2e_gpmi = producer_decision['average_onroad_direct_co2e_gpmi_%s' % market_class_id]
                    average_kwh_pmi = producer_decision['average_onroad_direct_kwh_pmi_%s' % market_class_id]

                    carbon_intensity_gasoline = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                              'direct_co2e_grams_per_unit')

                    refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                      'refuel_efficiency')

                    recharge_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'US electricity',
                                                                        'refuel_efficiency')

                    annual_o_m_costs = gcam_data_cy['o_m_costs']

                    # TODO: will eventually need utility factor for PHEVs here
                    fuel_cost_per_VMT = fuel_cost * average_kwh_pmi / recharge_efficiency
                    fuel_cost_per_VMT += fuel_cost * average_co2e_gpmi / carbon_intensity_gasoline / refuel_efficiency

                    # consumer_generalized_cost_dollars = total_capital_costs
                    annualized_capital_costs = annualization_factor * total_capital_costs
                    annual_VMT = float(gcam_data_cy['annual_vmt'])

                    total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / 1.383 / annual_VMT
                    total_cost_w_fuel_per_VMT = total_non_fuel_costs_per_VMT + fuel_cost_per_VMT
                    total_cost_w_fuel_per_PMT = total_cost_w_fuel_per_VMT / gcam_data_cy['average_occupancy']
                    sales_share_numerator[market_class_id] = gcam_data_cy['share_weight'] * (
                            total_cost_w_fuel_per_PMT ** logit_exponent_mu)

                    market_class_data[
                        'consumer_generalized_cost_dollars_%s' % market_class_id] = total_cost_w_fuel_per_PMT

                    sales_share_denominator += sales_share_numerator[market_class_id]

                else:
                    demanded_share = sales_share_numerator[market_class_id] / sales_share_denominator
                    demanded_absolute_share = \
                        demanded_share * market_class_data['consumer_abs_share_frac_%s' % parent_market_class].values

                    market_class_data['consumer_share_frac_%s' % market_class_id] = demanded_share
                    market_class_data['consumer_abs_share_frac_%s' % market_class_id] = demanded_absolute_share

        return market_class_data.copy()

    @staticmethod
    def calc_shares_body_style_helper(calendar_year, producer_decision, body_style):
        """

        Args:
            calendar_year (int):
            prev_producer_decision_and_response1:
            market_class (str): e.g. 'hauling' or 'non_hauling'

        Returns:
            Non-normalized fleet share for the given vehicle class

        """

        dfs_coeffs = pd.Series({'sedan_wagon': sedan_wagon_constants, 'cuv_suv_van': cuv_suv_van_constants,
                                'pickup': pickup_constants}[body_style])

        if 'y_hat_sedan_wagon_%s' % (calendar_year - 1) not in SalesShare._data:
            # no prior year analysis, use base year, historic value
            SalesShare._data['y_hat_sedan_wagon_%s' % (calendar_year - 1)] = sedan_wagon_constants['y_hat_historic']
            SalesShare._data['y_hat_cuv_suv_van_%s' % (calendar_year - 1)] = cuv_suv_van_constants['y_hat_historic']
            SalesShare._data['y_hat_pickup_%s' % (calendar_year - 1)] = pickup_constants['y_hat_historic']

        y_hat_prior = SalesShare._data['y_hat_%s_%s' % (body_style, calendar_year - 1)]
        price = producer_decision['average_new_vehicle_mfr_cost_%s' % body_style]
        footprint = producer_decision['average_footprint_ft2_%s' % body_style]
        gasoline_dollars_per_gallon = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', 'pump gasoline')
        electricity_dollars_per_kwh = FuelPrice.get_fuel_prices(calendar_year, 'retail_dollars_per_unit', 'US electricity')
        carbon_intensity_gasoline = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline', 'direct_co2e_grams_per_unit')
        gasoline_cpm = gasoline_dollars_per_gallon * producer_decision['average_onroad_direct_co2e_gpmi_%s' % body_style + '.ICE'] / carbon_intensity_gasoline
        electricity_cpm = electricity_dollars_per_kwh * producer_decision['average_onroad_direct_kwh_pmi_%s' % body_style + '.BEV']
        cpm = gasoline_cpm + electricity_cpm # only includes ICE vehicle cpm, consistent with original regression
        hpwt = producer_decision['average_rated_hp_%s' % body_style + '.ICE'] / producer_decision['average_curbweight_lbs_%s' % body_style + '.ICE'] # ICE only. BEV hp values would be needed for meaningful power-to-weight values over all vehicles

        gasoline_cpm_sedan_wagon = gasoline_dollars_per_gallon * producer_decision['average_onroad_direct_co2e_gpmi_sedan_wagon.ICE'] / carbon_intensity_gasoline
        electricity_cpm_sedan_wagon = electricity_dollars_per_kwh * producer_decision['average_onroad_direct_kwh_pmi_sedan_wagon.BEV']
        cpm_sedan_wagon = gasoline_cpm_sedan_wagon + electricity_cpm_sedan_wagon # only includes ICE vehicle cpm, consistent with original regression
        hpwt_sedan_wagon = producer_decision['average_rated_hp_sedan_wagon.ICE'] / producer_decision['average_curbweight_lbs_sedan_wagon.ICE'] # ICE only. BEV hp values would be needed for meaningful power-to-weight values over all vehicles

        gasoline_cpm_cuv_suv_van = gasoline_dollars_per_gallon * producer_decision['average_onroad_direct_co2e_gpmi_cuv_suv_van.ICE'] / carbon_intensity_gasoline
        electricity_cpm_cuv_suv_van = electricity_dollars_per_kwh * producer_decision['average_onroad_direct_kwh_pmi_cuv_suv_van.BEV']
        cpm_cuv_suv_van = gasoline_cpm_cuv_suv_van + electricity_cpm_cuv_suv_van # only includes ICE vehicle cpm, consistent with original regression
        hpwt_cuv_suv_van = producer_decision['average_rated_hp_cuv_suv_van.ICE'] / producer_decision['average_curbweight_lbs_cuv_suv_van.ICE'] # ICE only. BEV hp values would be needed for meaningful power-to-weight values over all vehicles

        gasoline_cpm_pickup = gasoline_dollars_per_gallon * producer_decision['average_onroad_direct_co2e_gpmi_pickup.ICE'] / carbon_intensity_gasoline
        electricity_cpm_pickup = electricity_dollars_per_kwh * producer_decision['average_onroad_direct_kwh_pmi_pickup.BEV']
        cpm_pickup = gasoline_cpm_pickup + electricity_cpm_pickup # only includes ICE vehicle cpm, consistent with original regression
        hpwt_pickup = producer_decision['average_rated_hp_pickup.ICE'] / producer_decision['average_curbweight_lbs_pickup.ICE'] # ICE only. BEV hp values would be needed for meaningful power-to-weight values over all vehicles

        geometric_mean_price = np.exp(np.average([math.log(producer_decision['average_new_vehicle_mfr_cost_sedan_wagon']), math.log(producer_decision['average_new_vehicle_mfr_cost_cuv_suv_van']), math.log(producer_decision['average_new_vehicle_mfr_cost_pickup'])]))
        geometric_mean_footprint = np.exp(np.average([math.log(producer_decision['average_footprint_ft2_sedan_wagon']), math.log(producer_decision['average_footprint_ft2_cuv_suv_van']), math.log(producer_decision['average_footprint_ft2_pickup'])]))
        geometric_mean_cpm = np.exp(np.average([math.log(cpm_sedan_wagon), math.log(cpm_cuv_suv_van), math.log(cpm_pickup)]))
        geometric_mean_hpwt = np.exp(np.average([math.log(hpwt_sedan_wagon), math.log(hpwt_cuv_suv_van), math.log(hpwt_pickup)]))

        y_hat = (dfs_coeffs.Constant +
                 dfs_coeffs.Xprice * math.log(price / geometric_mean_price) +
                 dfs_coeffs.Xfoot * math.log(footprint / geometric_mean_footprint) +
                 dfs_coeffs.Xcpm * math.log(cpm / geometric_mean_cpm) +
                 dfs_coeffs.Xhpwt * math.log(hpwt / geometric_mean_hpwt) +
                 dfs_coeffs.inc_growth * 1.02 +
                 dfs_coeffs.y_lag * y_hat_prior)

        # save y_hat value for the next analysis year's prior value
        SalesShare._data['y_hat_%s_%s' % (body_style, calendar_year)] = y_hat

        return y_hat

    @staticmethod
    def calc_shares_body_style(calendar_year, producer_decision):
        """

        Args:
            calendar_year:
            producer_decision:

        Returns:

        """
        y_hat_sedan_wagon = SalesShare.calc_shares_body_style_helper(calendar_year, producer_decision, 'sedan_wagon')
        y_hat_cuv_suv_van = SalesShare.calc_shares_body_style_helper(calendar_year, producer_decision, 'cuv_suv_van')
        y_hat_pickup = SalesShare.calc_shares_body_style_helper(calendar_year, producer_decision, 'pickup')

        denom = math.exp(y_hat_sedan_wagon) + math.exp(y_hat_cuv_suv_van) + math.exp(y_hat_pickup)

        sedan_wagon_share = math.exp(y_hat_sedan_wagon) / denom
        cuv_suv_van_share = math.exp(y_hat_cuv_suv_van) / denom
        pickup_share = math.exp(y_hat_pickup) / denom

        return sedan_wagon_share, cuv_suv_van_share, pickup_share

    @staticmethod
    def calc_shares(calendar_year, producer_decision, market_class_data, mc_parent, mc_pair):
        """
        Determine consumer desired market shares for the given vehicles, their costs, etc.

        Args:
            calendar_year (int): calendar year to calculate market shares in
            producer_decision (Series): selected producer compliance option with
                'average_retail_fuel_price_dollars_per_unit_MC',
                'average_onroad_direct_co2e_gpmi_MC', 'average_onroad_direct_kwh_pmi_MC' attributes,
                where MC = market class ID
            market_class_data (DataFrame): DataFrame with 'average_modified_cross_subsidized_price_MC' columns,
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

        analysis_sedan_wagon_share, analysis_cuv_suv_van_share, analysis_pickup_share = \
            SalesShare.calc_shares_body_style(calendar_year, producer_decision)

        if omega_globals.options.generate_context_calibration_files:

            context_sedan_wagon_share = \
                NewVehicleMarket.new_vehicle_data(calendar_year, context_body_style='sedan_wagon',
                                            value='sales_share_of_total') / 100

            context_cuv_suv_van_share = \
                NewVehicleMarket.new_vehicle_data(calendar_year, context_body_style='cuv_suv_van',
                                            value='sales_share_of_total') / 100

            context_pickup_share = \
                NewVehicleMarket.new_vehicle_data(calendar_year, context_body_style='pickup',
                                            value='sales_share_of_total') / 100

            SalesShare._data['sedan_wagon_calibration'][calendar_year] = \
                context_sedan_wagon_share / analysis_sedan_wagon_share

            SalesShare._data['cuv_suv_van_calibration'][calendar_year] = \
                context_cuv_suv_van_share / analysis_cuv_suv_van_share

            SalesShare._data['pickup_calibration'][calendar_year] = \
                context_pickup_share / analysis_pickup_share

        analysis_sedan_wagon_share *= SalesShare._data['sedan_wagon_calibration'][calendar_year]
        analysis_cuv_suv_van_share *= SalesShare._data['cuv_suv_van_calibration'][calendar_year]
        analysis_pickup_share *= SalesShare._data['pickup_calibration'][calendar_year]

        total_corrected_share = analysis_sedan_wagon_share + analysis_cuv_suv_van_share + analysis_pickup_share

        analysis_sedan_wagon_share /= total_corrected_share
        analysis_cuv_suv_van_share /= total_corrected_share
        analysis_pickup_share /= total_corrected_share

        market_class_data['consumer_abs_share_frac_sedan_wagon'] = analysis_sedan_wagon_share
        market_class_data['consumer_abs_share_frac_cuv_suv_van'] = analysis_cuv_suv_van_share
        market_class_data['consumer_abs_share_frac_pickup'] = analysis_pickup_share

        if all([SalesShare.gcam_supports_market_class(mc) for mc in mc_pair]):
            # calculate desired ICE/BEV shares within hauling/non_hauling using methods based on the GCAM model:
            market_class_data = SalesShare.calc_shares_gcam(producer_decision, market_class_data, calendar_year,
                                                        mc_parent, mc_pair)

        return market_class_data

    @staticmethod
    def save_calibration(filename):
        """
            Save calibration data (if necessary) that aligns reference session market shares with context

        Args:
            filename (str): name of the calibration file

        """
        if omega_globals.options.standalone_run:
            filename = omega_globals.options.output_folder + filename

        calibration = pd.DataFrame.from_dict({'sedan_wagon_calibration' : SalesShare._data['sedan_wagon_calibration'],
                                              'cuv_suv_van_calibration' : SalesShare._data['cuv_suv_van_calibration'],
                                              'pickup_calibration' : SalesShare._data['pickup_calibration']})
        calibration.to_csv(filename)

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

        for rc in legacy_reg_classes:
            for c in ['curbweight_lbs', 'rated_hp']:  # TODO: add 'onroad_mpg' ...
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


        SalesShare._data.clear()

        SalesShare.prev_producer_decisions_and_responses = []

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'market_class_id', 'start_year', 'annual_vmt', 'payback_years',
                                  'price_amortization_period', 'share_weight', 'discount_rate',
                                  'o_m_costs', 'average_occupancy', 'logit_exponent_mu'
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

        if not template_errors:
            validation_dict = {'market_class_id': omega_globals.options.MarketClass.market_classes}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            SalesShare._data = df.set_index(['market_class_id', 'start_year']).sort_index().to_dict(orient='index')

            for mc in df['market_class_id'].unique():
                SalesShare._data[mc] = {'start_year': np.array(df['start_year'].loc[df['market_class_id'] == mc])}

            if omega_globals.options.generate_context_calibration_files:
                SalesShare._data['sedan_wagon_calibration'] = dict()
                SalesShare._data['cuv_suv_van_calibration'] = dict()
                SalesShare._data['pickup_calibration'] = dict()
            else:
                SalesShare._data['sedan_wagon_calibration'] = \
                    pd.read_csv(omega_globals.options.sales_share_calibration_file). \
                        set_index('Unnamed: 0').to_dict()['sedan_wagon_calibration']
                SalesShare._data['cuv_suv_van_calibration'] = \
                    pd.read_csv(omega_globals.options.sales_share_calibration_file). \
                        set_index('Unnamed: 0').to_dict()['cuv_suv_van_calibration']
                SalesShare._data['pickup_calibration'] = \
                    pd.read_csv(omega_globals.options.sales_share_calibration_file). \
                        set_index('Unnamed: 0').to_dict()['pickup_calibration']

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

        init_fail = []

        # pull in reg classes before initializing classes that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        # pull in market classes before initializing classes that check market class validity
        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                                      verbose=omega_globals.options.verbose)

        from context.onroad_fuels import OnroadFuel  # needed for in-use fuel ID
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += SalesShare.init_from_file(omega_globals.options.sales_share_file,
                                               verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = 2021
            omega_globals.options.analysis_final_year = 2035

            # test market shares at different CO2e and price levels
            mcd = pd.DataFrame()
            for mc in omega_globals.options.MarketClass.market_classes:
                mcd['average_modified_cross_subsidized_price_%s' % mc] = [35000, 25000]
                mcd['average_onroad_direct_kwh_pmi_%s' % mc] = [0, 0]
                mcd['average_onroad_direct_co2e_gpmi_%s' % mc] = [125, 150]
                mcd['average_retail_fuel_price_dollars_per_unit_%s' % mc] = [2.75, 3.25]
                mcd['producer_abs_share_frac_non_hauling'] = [0.8, 0.85]
                mcd['producer_abs_share_frac_hauling'] = [0.2, 0.15]

            share_demand = SalesShare.calc_shares(omega_globals.options.analysis_initial_year, mcd, 'hauling',
                                                  ['hauling.ICE', 'hauling.BEV'])

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
