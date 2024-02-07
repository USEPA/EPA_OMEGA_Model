"""

**Routines to implement producer generalized cost calculations.**

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows. The template header uses a dynamic format.

The data represents producer generalized cost parameters by market class ID.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,producer.producer_generalized_cost,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,fuel_years,annual_vmt
        non_hauling.BEV,5,15000
        hauling.ICE,5,15000

Data Column Name and Description

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:fuel_years:
    Number of years of fuel cost to include in producer generalized cost

:annual_vmt:
    Annual vehicle miles travelled for calculating producer generalized cost

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class ProducerGeneralizedCost(OMEGABase, ProducerGeneralizedCostBase):
    """
    Loads producer generalized cost data and provides cost calculation functionality.

    """

    _data = dict()

    @staticmethod
    def get_producer_generalized_cost_attributes(market_class_id, attribute_types):
        """
        Get one or more producer generalized cost attributes associated with the given market class ID.

        Args:
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            attribute_types (str, [strs]): name or list of generalized cost attribute(s), e.g.
                ``['producer_generalized_cost_fuel_years', 'producer_generalized_cost_annual_vmt']``

        Returns:
            The requested generalized cost attributes.

        """
        cache_key = (market_class_id, attribute_types)

        if cache_key not in ProducerGeneralizedCost._data:
            ProducerGeneralizedCost._data[cache_key] = \
                [ProducerGeneralizedCost._data[market_class_id][attr] for attr in attribute_types]

        return ProducerGeneralizedCost._data[cache_key]

    @staticmethod
    def calc_generalized_cost(vehicle, cost_cloud, co2_name, kwh_name, cost_name):
        """
        Calculate generalized cost (vehicle cost plus other costs such as fuel costs) for the given vehicle's
        cost cloud.

        Args:
            vehicle (Vehicle): the vehicle to calculate generalized costs for
            cost_cloud (DataFrame): vehicle cost cloud
            co2_name (str): CO2 column name, e.g. 'onroad_direct_co2e_grams_per_mile'
            kwh_name (str): kWh/mi column name, e.g. 'onroad_direct_kwh_per_mile'
            cost_name (str): vehicle cost column name, e.g. 'new_vehicle_mfr_cost_dollars'

        Returns:
            The vehicle's cost cloud with generalized cost column, e.g. 'new_vehicle_mfr_generalized_cost_dollars'

        """
        from context.price_modifications import PriceModifications
        from context.onroad_fuels import OnroadFuel
        from context.fuel_prices import FuelPrice

        producer_generalized_cost_fuel_years, producer_generalized_cost_annual_vmt = \
            ProducerGeneralizedCost. \
                get_producer_generalized_cost_attributes(vehicle.market_class_id, ('fuel_years', 'annual_vmt'))

        # cost_cloud = vehicle.cost_cloud
        vehicle_cost = cost_cloud[cost_name]
        vehicle_co2e_grams_per_mile = cost_cloud[co2_name]
        vehicle_direct_kwh_per_mile = cost_cloud[kwh_name] / OnroadFuel.get_fuel_attribute(vehicle.model_year,
                                                                                           'US electricity',
                                                                                           'refuel_efficiency')

        price_modification = \
            omega_globals.options.producer_price_modification_scaler * \
            PriceModifications.get_price_modification(vehicle.model_year, vehicle.market_class_id)

        grams_co2e_per_unit = vehicle.onroad_co2e_emissions_grams_per_unit()
        liquid_generalized_fuel_cost = 0
        electric_generalized_fuel_cost = 0

        if grams_co2e_per_unit > 0:
            liquid_generalized_fuel_cost = \
                (vehicle.retail_fuel_price_dollars_per_unit(vehicle.model_year) / grams_co2e_per_unit *
                 vehicle_co2e_grams_per_mile *
                 producer_generalized_cost_annual_vmt *
                 producer_generalized_cost_fuel_years)

        if any(vehicle_direct_kwh_per_mile > 0):
            electric_generalized_fuel_cost = (
                    vehicle_direct_kwh_per_mile *
                    omega_globals.options.ElectricityPrices.get_fuel_price(vehicle.model_year)
                    * producer_generalized_cost_annual_vmt * producer_generalized_cost_fuel_years
            )

        delta_footprint_ft2 = cost_cloud['footprint_ft2'] - vehicle.base_year_footprint_ft2
        footprint_wtp = delta_footprint_ft2 * omega_globals.options.producer_footprint_wtp

        generalized_fuel_cost = liquid_generalized_fuel_cost + electric_generalized_fuel_cost

        cost_cloud[cost_name.replace('mfr', 'mfr_generalized')] = (
                generalized_fuel_cost + vehicle_cost + price_modification - footprint_wtp
        )

        return cost_cloud

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
        ProducerGeneralizedCost._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'market_class_id', 'fuel_years', 'annual_vmt'}

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
            ProducerGeneralizedCost._data = df.set_index('market_class_id').to_dict(orient='index')

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

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        # pull in market classes before initializing classes that check market class validity
        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += ProducerGeneralizedCost.init_from_file(
            omega_globals.options.producer_generalized_cost_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
