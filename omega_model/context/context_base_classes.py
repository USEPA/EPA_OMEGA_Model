
print('importing %s' % __file__)

import inspect

from omega_model import *


class CostCloudBase():
    """
    **Loads and provides access to simulated vehicle data, provides methods to calculate and plot frontiers.**

    """

    # @staticmethod
    # def init_cost_clouds_from_file(filename, verbose=False):
    #     """
    #
    #     Initialize class data from input file.
    #
    #     Args:
    #         filename (str): name of input file
    #         verbose (bool): enable additional console and logfile output if True
    #
    #     Returns:
    #         List of template/input errors, else empty list on success
    #
    #     """
    #     from policy.offcycle_credits import OffCycleCredits  # offcycle_credits must be initalized first
    #
    #     _cache.clear()
    #
    #     if verbose:
    #         omega_log.logwrite('\nInitializing database from %s...' % filename)
    #
    #     input_template_name = __name__
    #     input_template_version = 0.3
    #     input_template_columns = {'simulated_vehicle_id', 'model_year', 'cost_curve_class',
    #                               'new_vehicle_mfr_cost_dollars'}
    #     input_template_columns = input_template_columns.union(OffCycleCredits.offcycle_credit_names)
    #
    #     template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
    #                                                      verbose=verbose)
    #
    #     if not template_errors:
    #         # read in the data portion of the input file
    #         cost_clouds_template_info = pd.read_csv(filename, nrows=0)
    #         temp = [item for item in cost_clouds_template_info]
    #         dollar_basis_template = int(temp[temp.index('dollar_basis:') + 1])
    #
    #         df = pd.read_csv(filename, skiprows=1)
    #
    #         template_errors = validate_template_columns(filename, input_template_columns, df.columns,
    #                                                     verbose=verbose)
    #
    #         deflators = pd.read_csv(omega_globals.options.ip_deflators_file, skiprows=1, index_col=0).to_dict('index')
    #
    #         adjustment_factor = deflators[omega_globals.options.analysis_dollar_basis]['price_deflator'] \
    #                             / deflators[dollar_basis_template]['price_deflator']
    #
    #         df['new_vehicle_mfr_cost_dollars'] = df['new_vehicle_mfr_cost_dollars'] * adjustment_factor
    #
    #         # TODO: validate manufacturer, reg classes, fuel ids, etc, etc....
    #
    #         if not template_errors:
    #
    #             # convert cost clouds into curves and set up cost_curves table...
    #             cost_curve_classes = df['cost_curve_class'].unique()
    #             # for each cost curve class
    #             for cost_curve_class in cost_curve_classes:
    #                 class_cloud = df[df['cost_curve_class'] == cost_curve_class]
    #                 cloud_model_years = class_cloud['model_year'].unique()
    #                 # for each model year
    #                 _cache[cost_curve_class] = dict()
    #                 for model_year in cloud_model_years:
    #                     _cache[cost_curve_class][model_year] = class_cloud[class_cloud['model_year'] == model_year].copy()
    #                     CostCloud._max_year = max(CostCloud._max_year, model_year)
    #
    #             CostCloud.cost_cloud_data_columns = df.columns.drop(['simulated_vehicle_id', 'model_year',
    #                                                                  'cost_curve_class'])
    #
    #     return template_errors

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
