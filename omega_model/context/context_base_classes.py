"""
    **Context base classes.**

    Currently just ``CostCloudBase``.

"""
print('importing %s' % __file__)

import inspect

from omega_model import *


class CostCloudBase:
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    @staticmethod
    def init_cost_clouds_from_files(ice_filename, bev_filename, phev_filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            ice_filename (str): name of ICE/HEV vehicle simulation data input file
            bev_filename (str): name of BEV vehicle simulation data input file
            phev_filename (str): name of PHEV vehicle simulation data input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        return ['**Attempt to call abstract method CostCloudBase.%s() without child class override**' %
                inspect.currentframe().f_code.co_name]

    @staticmethod
    def get_cloud(vehicle):
        """
        Retrieve cost cloud for the given vehicle.

        Args:
            vehicle (): the vehicle to get the cloud for

        Returns:
            Copy of the requested cost cload data.

        """
        raise Exception('**Attempt to call abstract method CostCloudBase.%s() without child class override**' %
                        inspect.currentframe().f_code.co_name)
