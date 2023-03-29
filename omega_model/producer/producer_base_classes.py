"""
**A set of base classes used to define the program interface(s) and to serve as templates for user-defined classes**

Ordinarily these classes might be implemented as Python abstract classes but abstract classes cause issues when
combined with SQLAlchemy base classes, so the implementation here is a workaround - if a child class fails to implement
one of the required methods, the class will throw a runtime Exception or return an error message.

"""

import inspect


class ProducerGeneralizedCostBase:
    """
    Loads producer generalized cost data and provides cost calculation functionality.

    """

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
        raise Exception('**Attempt to call abstract method ProducerGeneralizedCostBase.%s() '
                        'without child class override**' % inspect.currentframe().f_code.co_name)

    @staticmethod
    def calc_generalized_cost(vehicle, cost_cloud, co2_name, kwh_name, cost_name):
        """
        Calculate generalized cost (vehicle cost plus other costs such as fuel costs) for the given vehicle's
        cost cloud.

        Args:
            vehicle (Vehicle): the vehicle to calculate generalized costs for
            cost_cloud (dataframe): the vehicle's cost cloud
            co2_name (str): CO2 column name, e.g. 'onroad_direct_co2e_grams_per_mile'
            kwh_name (str): kWh/mi column name, e.g. 'onroad_direct_kwh_per_mile'
            cost_name (str): vehicle cost column name, e.g. 'new_vehicle_mfr_cost_dollars'

        Returns:
            The vehicle's cost cloud with generalized cost column, e.g. 'new_vehicle_mfr_generalized_cost_dollars'

        """
        raise Exception('**Attempt to call abstract method ProducerGeneralizedCostBase.%s() '
                        'without child class override**' % inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method ProducerGeneralizedCostBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]
