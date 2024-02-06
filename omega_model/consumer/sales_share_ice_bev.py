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

       input_template_name:,consumer.sales_share_ice_bev,input_template_version:,0.13

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,start_year,annual_vmt,price_amortization_period,share_weight,discount_rate,o_m_costs,average_occupancy,logit_exponent_mu
        hauling.BEV,2020,12000,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2021,12000,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2022,12000,5,0.168,0.1,1600,1.58,-8

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

print('importing %s' % __file__)

from omega_model import *
from context.fuel_prices import FuelPrice
from context.new_vehicle_market import NewVehicleMarket


class SalesShare(OMEGABase, SalesShareBase):
    """
    Loads and provides access to GCAM consumer response parameters.

    """
    _data = dict()
    _calibration_data = dict()

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
            producer_decision (Series): selected producer compliance option
            market_class_data (DataFrame): DataFrame with 'average_ALT_fuel_price_MC',
                'average_ALT_modified_cross_subsidized_price_MC', 'average_ALT_co2e_gpmi_MC', 'average_ALT_kwh_pmi_MC'
                columns, where MC = market class ID
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
                    fuel_cost = producer_decision['average_ALT_retail_fuel_price_dollars_per_unit_%s' % market_class_id]

                    gcam_data_cy = SalesShare.get_gcam_params(calendar_year, market_class_id)

                    logit_exponent_mu = gcam_data_cy['logit_exponent_mu']

                    price_amortization_period = float(gcam_data_cy['price_amortization_period'])
                    discount_rate = gcam_data_cy['discount_rate']
                    annualization_factor = discount_rate + discount_rate / (
                            ((1 + discount_rate) ** price_amortization_period) - 1)

                    total_capital_costs = market_class_data[
                        'average_ALT_modified_cross_subsidized_price_%s' % market_class_id].values
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
                        omega_globals.options.ElectricityPrices.get_fuel_price(calendar_year) * \
                        average_kwh_pmi / recharge_efficiency

                    fuel_cost_per_VMT += fuel_cost * average_co2e_gpmi / carbon_intensity_gasoline / refuel_efficiency

                    # consumer_generalized_cost_dollars = total_capital_costs
                    annualized_capital_costs = annualization_factor * total_capital_costs
                    annual_VMT = float(gcam_data_cy['annual_vmt'])

                    total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / annual_VMT
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
    def calc_shares(calendar_year, compliance_id, producer_decision, market_class_data, mc_parent, mc_pair):
        """
        Determine consumer desired market shares for the given vehicles, their costs, etc.

        Args:
            calendar_year (int): calendar year to calculate market shares in
            compliance_id (str): manufacturer name, or 'consolidated_OEM'
            producer_decision (Series): selected producer compliance option
            market_class_data (DataFrame): DataFrame with 'average_ALT_fuel_price_MC',
                'average_ALT_modified_cross_subsidized_price_MC', 'average_ALT_co2e_gpmi_MC', 'average_ALT_kwh_pmi_MC'
                columns, where MC = market class ID
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

        market_class_data['consumer_abs_share_frac_hauling'] = \
            producer_decision['producer_abs_share_frac_hauling']

        market_class_data['consumer_abs_share_frac_non_hauling'] = \
            producer_decision['producer_abs_share_frac_non_hauling']

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
        pass

    @staticmethod
    def store_producer_decision_and_response(producer_decision_and_response):
        """
            Store producer decision and response (if necessary) for reference in future years

        Args:
            producer_decision_and_response (Series): producer decision and consumer response

        """
        pass

    @staticmethod
    def calc_base_year_data(base_year_vehicles_df):
        """
            Calculate base year data (if necessary) such as sales-weighted curbweight, etc, if needed for reference
            in future years

        Args:
            base_year_vehicles_df (DataFrame): base year vehicle data

        """
        pass

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
        SalesShare._calibration_data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.13
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

        from policy.policy_fuels import PolicyFuel
        from omega_model.omega import get_module

        # pull in reg classes before initializing classes that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        init_fail += PolicyFuel.init_from_file(omega_globals.options.policy_fuels_file,
                                               verbose=omega_globals.options.verbose)

        omega_globals.options.market_classes_file = \
            omega_globals.options.omega_model_path + '/test_inputs/market_classes.csv'

        # pull in market classes before initializing classes that check market class validity
        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                                      verbose=omega_globals.options.verbose)

        from context.onroad_fuels import OnroadFuel  # needed for in-use fuel ID
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)

        init_fail += NewVehicleMarket.init_from_file(
            omega_globals.options.context_new_vehicle_market_file, verbose=omega_globals.options.verbose)

        module_name = get_template_name(omega_globals.options.context_electricity_prices_file)
        omega_globals.options.ElectricityPrices = get_module(module_name).ElectricityPrices

        init_fail += omega_globals.options.ElectricityPrices.init_from_file(
            omega_globals.options.context_electricity_prices_file, verbose=omega_globals.options.verbose
        )

        # must come after NewVehicleMarket and OnroadFuel init for input validation
        from context.fuel_prices import FuelPrice
        init_fail += FuelPrice.init_from_file(omega_globals.options.context_fuel_prices_file,
                                              verbose=omega_globals.options.verbose)

        omega_globals.options.sales_share_file = \
            omega_globals.options.omega_model_path + '/test_inputs/sales_share_params.csv'

        init_fail += SalesShare.init_from_file(omega_globals.options.sales_share_file,
                                               verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = 2021
            omega_globals.options.analysis_final_year = 2035

            # test market shares at different CO2e and price levels
            mcd = pd.DataFrame()
            for mc in omega_globals.options.MarketClass.market_classes:
                mcd['average_ALT_modified_cross_subsidized_price_%s' % mc] = [35000, 25000]
                mcd['average_ALT_onroad_direct_kwh_pmi_%s' % mc] = [0, 0]
                mcd['average_ALT_onroad_direct_co2e_gpmi_%s' % mc] = [125, 150]
                mcd['average_ALT_retail_fuel_price_dollars_per_unit_%s' % mc] = [2.75, 3.25]
                mcd['producer_abs_share_frac_non_hauling'] = [0.8, 0.85]
                mcd['producer_abs_share_frac_hauling'] = [0.2, 0.15]

            share_demand = SalesShare.calc_shares(omega_globals.options.analysis_initial_year, 'consolidated_OEM',
                                                  mcd, mcd, 'hauling', ['hauling.ICE', 'hauling.BEV'])

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
