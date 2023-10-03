"""
**A set of base classes used to define the program interface(s) and to serve as templates for user-defined classes**

Ordinarily these classes might be implemented as Python abstract classes but abstract classes cause issues when
combined with SQLAlchemy base classes, so the implementation here is a workaround - if a child class fails to implement
one of the required methods, the class will throw a runtime Exception or return an error message.

"""

import inspect


class RegulatoryClassesBase:
    """
    **Load and provides routines to access to regulatory class descriptive data**

    """

    @staticmethod
    def get_vehicle_reg_class(vehicle):
        """
        Get vehicle regulatory class based on vehicle characteristics.

        Args:
            vehicle (Vehicle): the vehicle to determine the reg class of

        Returns:

            Vehicle reg class based on vehicle characteristics.

        """
        raise Exception('**Attempt to call abstract method RegulatoryClassesBase.%s() without child class override**' %
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
        return ['**Attempt to call abstract method RegulatoryClassesBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class VehicleTargetsBase:
    """
    A base class representing the program interface for calculating vehicle CO g/mi targets.

    """
    @staticmethod
    def calc_target_co2e_gpmi(vehicle):
        """
        Calculate vehicle target CO2e g/mi.

        Args:
            vehicle (Vehicle): the vehicle to get the target for

        Returns:

            Vehicle target CO2e in g/mi.

        """
        raise Exception('**Attempt to call abstract method TargetsBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def calc_cert_lifetime_vmt(reg_class_id, model_year):
        """
        Get lifetime VMT as a function of regulatory class and model year.

        Args:
            reg_class_id (str): e.g. 'car','truck'
            model_year (numeric): model year

        Returns:

            Lifetime VMT for the regulatory class and model year.

        """
        raise Exception('**Attempt to call abstract method TargetsBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def calc_cert_useful_life_vmt(reg_class_id, model_year, cert_fuel_id):
        """
        Get lifetime VMT as a function of regulatory class and model year.

        Args:
            reg_class_id (str): e.g. 'car','truck'
            model_year (numeric): model year
            cert_fuel_id (str): certification fuel id, e.g. 'gasoline'

        Returns:

            Lifetime VMT for the regulatory class and model year.

        """
        raise Exception('**Attempt to call abstract method TargetsBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def calc_target_co2e_Mg(vehicle, sales_variants=None):
        """
        Calculate vehicle target CO2e Mg as a function of the vehicle, the standards and optional sales options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Target CO2e Mg value(s) for the given vehicle and/or sales variants.

        """
        raise Exception('**Attempt to call abstract method TargetsBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)

    @staticmethod
    def calc_cert_co2e_Mg(vehicle, co2_gpmi_variants=None, sales_variants=1):
        """
        Calculate vehicle cert CO2e Mg as a function of the vehicle, the standards, CO2e g/mi options and optional sales
        options.

        Includes the effect of production multipliers.

        See Also:

            GHG_standards_incentives.GHGStandardIncentives

        Args:
            vehicle (Vehicle): the vehicle
            co2_gpmi_variants (numeric list-like): optional co2 g/mi variants
            sales_variants (numeric list-like): optional sales variants

        Returns:

            Cert CO2e Mg value(s) for the given vehicle, CO2e g/mi variants and/or sales variants.

        """
        raise Exception('**Attempt to call abstract method TargetsBase.%s() without child class override**' %
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
        return ['**Attempt to call abstract method TargetsBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]


class OffCycleCreditsBase:
    """
    **Loads, stores and applies off-cycle credits to vehicle cost clouds**

    """

    offcycle_credit_names = []  #: list of credit names, populated during init, used to track credits across composition/decomposition, also used to check simulated vehicles for necessary columns

    @staticmethod
    def calc_off_cycle_credits(calendar_year, vehicle, cost_cloud):
        """
        Calculate vehicle off-cycle credits for the vehicle's cost cloud

        Args:
            calendar_year (int): the year to calculate credits for, usually the vehicle model year
            vehicle (Vehicle): the vehicle to apply off-cycle credits to
            cost_cloud (DataFrame): destination data set for off-cycle credits

        Returns:
            cost_cloud with off-cycle credits calculated

        """
        raise Exception('**Attempt to call abstract method OffCycleCreditsBase.%s() without child class override**' %
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
        return ['**Attempt to call abstract method OffCycleCreditsBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]
