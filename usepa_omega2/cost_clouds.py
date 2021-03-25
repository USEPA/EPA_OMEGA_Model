"""
cost_clouds.py
==============


"""
print('importing %s' % __file__)

from usepa_omega2 import *

input_template_name = 'cost_clouds'

cache = dict()


class CostCloud(OMEGABase):

    max_year = 0

    @staticmethod
    def init_cost_clouds_from_file(filename, verbose=False):
        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.1
        input_template_columns = {'cost_curve_class', 'model_year', 'cert_co2_grams_per_mile',
                                  'new_vehicle_mfr_cost_dollars', 'cert_kWh_per_mile'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:
                # convert cost clouds into curves and set up cost_curves table...
                cost_curve_classes = df['cost_curve_class'].unique()
                # for each cost curve class
                for cost_curve_class in cost_curve_classes:
                    class_cloud = df[df['cost_curve_class'] == cost_curve_class]
                    cloud_model_years = class_cloud['model_year'].unique()
                    # for each model year
                    cache[cost_curve_class] = dict()
                    for model_year in cloud_model_years:
                        cache[cost_curve_class][model_year] = class_cloud[class_cloud['model_year'] == model_year].copy()
                        CostCloud.max_year = max(CostCloud.max_year, model_year)

        return template_errors

    @staticmethod
    def plot_frontier(cost_cloud, cost_curve_class, frontier_df, value_column):
            import matplotlib.pyplot as plt
            plt.figure()
            plt.plot(cost_cloud[value_column], cost_cloud['new_vehicle_mfr_cost_dollars'],
                     '.')
            plt.title('Cost versus %s %s' % (value_column, cost_curve_class))
            plt.xlabel('%s' % value_column)
            plt.ylabel('Combined GHG Cost [$]')
            plt.plot(frontier_df[value_column], frontier_df['new_vehicle_mfr_cost_dollars'],
                     'r-')
            plt.grid()
            plt.savefig(o2.options.output_folder + 'Cost versus %s %s' % (value_column, cost_curve_class))

    @staticmethod
    def calculate_frontier(cloud, x_key, y_key):
        """
        Args:
            cloud (DataFrame): a set of points to find the frontier of
            x_key (str): name of the column holding x-axis data
            y_key (str): name of the column holding y-axis data

        Returns:
            DataFrame containing the frontier points

        """

        frontier_pts = []

        # find frontier starting point, lowest GHGs, and add to frontier
        idxmin = cloud[x_key].idxmin()
        frontier_pts.append(cloud.loc[idxmin])

        if cloud[x_key].min() != cloud[x_key].max():
            while pd.notna(idxmin):
                # calculate frontier factor (more negative is more better) = slope of each point relative
                # to prior frontier point if frontier_social_affinity_factor = 1.0, else a "weighted" slope
                cloud['frontier_factor'] = (cloud[y_key] - frontier_pts[-1][y_key]) \
                                           / (cloud[x_key] - frontier_pts[-1][x_key]) \
                                           ** o2.options.cost_curve_frontier_affinity_factor

                # find next frontier point (lowest slope), if there is one, and add to frontier list
                min = cloud['frontier_factor'].min()

                if min > 0:
                    # frontier factor is different for up-slope
                    cloud['frontier_factor'] = (cloud[y_key] - frontier_pts[-1][y_key]) / \
                                               (cloud[x_key] - frontier_pts[-1][x_key]) \
                                               ** (1 + 1 - o2.options.cost_curve_frontier_affinity_factor)
                    min = cloud['frontier_factor'].min()

                if len(cloud[cloud['frontier_factor'] == min]) > 1:
                    # if multiple points with the same slope, take the one with the highest index (highest x-value)
                    idxmin = cloud[cloud['frontier_factor'] == min].index.max()
                else:
                    idxmin = cloud['frontier_factor'].idxmin()
                if pd.notna(idxmin):
                    frontier_pts.append(cloud.loc[idxmin])

        frontier_df = pd.concat(frontier_pts, axis=1)
        frontier_df = frontier_df.transpose()
        frontier_df['frontier_factor'] = 0

        return frontier_df.copy()

    @staticmethod
    def get_cloud(model_year, cost_curve_class):
        return cache[cost_curve_class][model_year].copy()

    @staticmethod
    def get_max_year():
        return CostCloud.max_year

    # def calculate_generalized_cost(self, cost_curve_class):
    #     print(cost_curve_class)


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()
        o2.options.cost_file = os.path.dirname(os.path.abspath(__file__)) + os.sep + 'test_inputs/cost_clouds.csv'

        init_fail = []
        init_fail = init_fail + CostCloud.init_cost_clouds_from_file(o2.options.cost_file, verbose=True)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
