"""
**A set of base classes used to define the program interface(s) and to serve as templates for user-defined classes**

Ordinarily these classes might be implemented as Python abstract classes but abstract classes cause issues when
combined with SQLAlchemy base classes, so the implementation here is a workaround - if a child class fails to implement
one of the required methods, the class will throw a runtime Exception or return an error message.

"""

import inspect


class ReregistrationBase:
    """
    **Load and provide access to vehicle re-registration data.**

    """
    @staticmethod
    def get_reregistered_proportion(market_class_id, age):
        """
        Get vehicle re-registered proportion [0..1] by market class and age.

        Args:
            market_class_id (str): e.g. 'hauling.ICE'
            age (int): vehicle age

        Returns:
            Re-registered proportion [0..1]

        """
        raise Exception('**Attempt to call abstract method ReregistrationBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method ReregistrationBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class AnnualVMTBase:
    """
    Loads and provides access to annual Vehicle Miles Travelled by market class, age and potentially other factors.

    """

    @staticmethod
    def get_vmt(market_class_id, age, **kwargs):
        """
        Get vehicle miles travelled by market class and age.

        Args:
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            (float) Vehicle miles travelled.

        """
        raise Exception('**Attempt to call abstract method OnroadVMT.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method OnroadVMT.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class SalesShareBase:
    """
    Class to calculate absolute market shares by market class

    """

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
        raise Exception('**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

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
        return ['**Attempt to call abstract method SalesShareBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]