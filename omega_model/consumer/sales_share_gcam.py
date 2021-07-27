"""

**Implements a portion of the GCAM model related to the relative shares of ICE and BEV vehicles as a function
of relative generalized costs and assumptions about consumer acceptance over time (the S-shaped adoption curve).**

Relative shares are converted to absolute shares for use in the producer compliance search.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents GCAM consumer model input parameters.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,demanded_shares_gcam,input_template_version:,0.12

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

print('importing %s' % __file__)

from omega_model import *

cache = dict()


class SalesShare(OMEGABase, SQABase, SalesShareBase):
    """
    Loads and provides access to GCAM consumer response parameters.

    """
    # --- database table properties ---
    __tablename__ = 'demanded_shares_gcam'
    index = Column(Integer, primary_key=True)  #: database table index

    market_class_id = Column('market_class_id', String, ForeignKey('market_classes.market_class_id'))  #: market class ID
    annual_VMT = Column('annual_vmt', Float)  #: annual vehicle miles travelled
    calendar_year = Column(Numeric)  #: the calendar year of the parameters
    payback_years = Column(Numeric)  #: payback period, in years
    price_amortization_period = Column(Numeric)  #: price amorization period, in years
    discount_rate = Column(Float)  #: discount rate [0..1], e.g. 0.1
    share_weight = Column(Float)  #: share weight [0..1]
    o_m_costs = Column(Float)  #: operating and maintenance costs, in dollars
    average_occupancy = Column(Float)  #: average vehicle occupancy, number of people
    logit_exponent_mu = Column(Float)  #: logit exponent, mu

    @staticmethod
    def get_gcam_params(calendar_year, market_class_id):
        """
        Get GCAM parameters for the given calendar year and market class.

        Args:
            calendar_year (int): the year to get parameters for
            market_class_id (str): market class id, e.g. 'non_hauling.BEV'

        Returns:
            GCAM parameters for the given calendar year and market class

        """
        start_years = cache[market_class_id]['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        key = '%s_%s' % (calendar_year, market_class_id)
        if not key in cache:
            cache[key] = omega_globals.session.query(SalesShare). \
                filter(SalesShare.calendar_year == calendar_year). \
                filter(SalesShare.market_class_id == market_class_id).one()

        return cache[key]

    def calc_shares(market_class_data, calendar_year):
        """
        Determine consumer desired market shares for the given vehicles, their costs, etc.  Relative shares are first
        calculated within non-responsive market categories then converted to absolute shares.

        Args:
            market_class_data (DataFrame): DataFrame with 'average_fuel_price_MC',
                'average_modified_cross_subsidized_price_MC', 'average_co2e_gpmi_MC', 'average_kwh_pmi_MC'
                columns, where MC = market class ID
            calendar_year (int): calendar year to calculate market shares in

        Returns:
            A copy of ``market_class_data`` with demanded ICE/BEV share columns by market class, e.g.
            'consumer_share_frac_MC', 'consumer_abs_share_frac_MC', and 'consumer_generalized_cost_dollars_MC' where
            MC = market class ID

        """
        from consumer.market_classes import MarketClass
        from context.onroad_fuels import OnroadFuel

        if omega_globals.options.flat_context:
            calendar_year = omega_globals.options.flat_context_year

        #  PHASE0: hauling/non, EV/ICE, with hauling/non share fixed. We don't need shared/private for beta

        sales_share_denominator_all_hauling = 0
        sales_share_denominator_all_nonhauling = 0

        sales_share_numerator = dict()

        for pass_num in [0, 1]:
            for market_class_id in MarketClass.market_classes:
                if pass_num == 0:
                    fuel_cost = market_class_data['average_fuel_price_%s' % market_class_id]

                    gcam_data_cy = SalesShare.get_gcam_params(calendar_year, market_class_id)

                    logit_exponent_mu = gcam_data_cy.logit_exponent_mu

                    price_amortization_period = float(gcam_data_cy.price_amortization_period)
                    discount_rate = gcam_data_cy.discount_rate
                    annualization_factor = discount_rate + discount_rate / (
                            ((1 + discount_rate) ** price_amortization_period) - 1)

                    total_capital_costs = market_class_data[
                        'average_modified_cross_subsidized_price_%s' % market_class_id]
                    average_co2e_gpmi = market_class_data['average_co2e_gpmi_%s' % market_class_id]
                    average_kwh_pmi = market_class_data['average_kwh_pmi_%s' % market_class_id]

                    carbon_intensity_gasoline = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                              'direct_co2e_grams_per_unit')

                    refuel_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'pump gasoline',
                                                                      'refuel_efficiency')

                    recharge_efficiency = OnroadFuel.get_fuel_attribute(calendar_year, 'US electricity',
                                                                        'refuel_efficiency')

                    annual_o_m_costs = gcam_data_cy.o_m_costs

                    # TODO: will eventually need utility factor for PHEVs here
                    fuel_cost_per_VMT = fuel_cost * average_kwh_pmi / recharge_efficiency
                    fuel_cost_per_VMT += fuel_cost * average_co2e_gpmi / carbon_intensity_gasoline / refuel_efficiency

                    # consumer_generalized_cost_dollars = total_capital_costs
                    annualized_capital_costs = annualization_factor * total_capital_costs
                    annual_VMT = float(gcam_data_cy.annual_VMT)

                    total_non_fuel_costs_per_VMT = (annualized_capital_costs + annual_o_m_costs) / 1.383 / annual_VMT
                    total_cost_w_fuel_per_VMT = total_non_fuel_costs_per_VMT + fuel_cost_per_VMT
                    total_cost_w_fuel_per_PMT = total_cost_w_fuel_per_VMT / gcam_data_cy.average_occupancy
                    sales_share_numerator[market_class_id] = gcam_data_cy.share_weight * (
                            total_cost_w_fuel_per_PMT ** logit_exponent_mu)

                    market_class_data[
                        'consumer_generalized_cost_dollars_%s' % market_class_id] = total_cost_w_fuel_per_PMT

                    if 'non_hauling' in market_class_id.split('.'):
                        sales_share_denominator_all_nonhauling += sales_share_numerator[market_class_id]
                    else:
                        sales_share_denominator_all_hauling += sales_share_numerator[market_class_id]
                else:
                    if 'non_hauling' in market_class_id.split('.'):
                        demanded_share = sales_share_numerator[market_class_id] / sales_share_denominator_all_nonhauling
                        demanded_absolute_share = demanded_share * market_class_data[
                            'producer_abs_share_frac_non_hauling']
                    else:
                        demanded_share = sales_share_numerator[market_class_id] / sales_share_denominator_all_hauling
                        demanded_absolute_share = demanded_share * market_class_data['producer_abs_share_frac_hauling']

                    market_class_data['consumer_share_frac_%s' % market_class_id] = demanded_share
                    market_class_data['consumer_abs_share_frac_%s' % market_class_id] = demanded_absolute_share

        return market_class_data.copy()

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
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.12
        input_template_columns = {'market_class_id', 'start_year', 'annual_vmt', 'payback_years',
                                  'price_amortization_period', 'share_weight', 'discount_rate',
                                  'o_m_costs', 'average_occupancy', 'logit_exponent_mu'
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                obj_list = []
                # load data into database
                for i in df.index:
                    obj_list.append(SalesShare(
                        market_class_id=df.loc[i, 'market_class_id'],
                        calendar_year=df.loc[i, 'start_year'],
                        annual_VMT=df.loc[i, 'annual_vmt'],
                        payback_years=df.loc[i, 'payback_years'],
                        price_amortization_period=df.loc[i, 'price_amortization_period'],
                        discount_rate=df.loc[i, 'discount_rate'],
                        share_weight=df.loc[i, 'share_weight'],
                        o_m_costs=df.loc[i, 'o_m_costs'],
                        average_occupancy=df.loc[i, 'average_occupancy'],
                        logit_exponent_mu=df.loc[i, 'logit_exponent_mu'],
                    ))
                omega_globals.session.add_all(obj_list)
                omega_globals.session.flush()

                for mc in df['market_class_id'].unique():
                    cache[mc] = {'start_year': np.array(df['start_year'].loc[df['market_class_id'] == mc])}

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        init_fail = []

        # pull in reg classes before building database tables (declaring classes) that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        from producer.manufacturers import Manufacturer  # needed for manufacturers table
        from consumer.market_classes import MarketClass  # needed for market class ID
        from context.onroad_fuels import OnroadFuel  # needed for showroom fuel ID
        from policy.targets_footprint import VehicleTargets
        from context.cost_clouds import CostCloud

        omega_globals.options.VehicleTargets = VehicleTargets

        from producer.vehicles import VehicleFinal
        from producer.vehicle_annual_data import VehicleAnnualData

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail += Manufacturer.init_database_from_file(omega_globals.options.manufacturers_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)
        init_fail += SalesShare.init_from_file(omega_globals.options.sales_share_file,
                                               verbose=omega_globals.options.verbose)
        init_fail += CostCloud.init_cost_clouds_from_file(omega_globals.options.vehicle_simulation_results_and_costs_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += VehicleTargets.init_from_file(omega_globals.options.policy_targets_file,
                                                          verbose=omega_globals.options.verbose)
        init_fail += OnroadFuel.init_from_file(omega_globals.options.onroad_fuels_file,
                                               verbose=omega_globals.options.verbose)
        init_fail += VehicleFinal.init_database_from_file(omega_globals.options.vehicles_file,
                                                          omega_globals.options.onroad_vehicle_calculations_file,
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:
            omega_globals.options.analysis_initial_year = 2021
            omega_globals.options.analysis_final_year = 2035
            omega_globals.options.database_dump_folder = '__dump'

            dump_omega_db_to_csv(omega_globals.options.database_dump_folder)

            # test market shares at different CO2e and price levels
            mcd = pd.DataFrame()
            for mc in MarketClass.market_classes:
                mcd['average_modified_cross_subsidized_price_%s' % mc] = [35000, 25000]
                mcd['average_kwh_pmi_%s' % mc] = [0, 0]
                mcd['average_co2e_gpmi_%s' % mc] = [125, 150]
                mcd['average_fuel_price_%s' % mc] = [2.75, 3.25]
                mcd['producer_abs_share_frac_non_hauling'] = [0.8, 0.85]
                mcd['producer_abs_share_frac_hauling'] = [0.2, 0.15]

            share_demand = SalesShare.calc_shares(mcd, omega_globals.options.analysis_initial_year)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
