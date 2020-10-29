"""
cost_clouds.py
==============


"""
print('importing %s' % __file__)

import o2  # import global variables
from usepa_omega2 import *

input_template_name = 'cost_clouds'

class CostCloud(SQABase, OMEGABase):
    # --- database table properties ---
    __tablename__ = 'cost_clouds'
    index = Column('index', Integer, primary_key=True)

    cost_curve_class = Column(String)
    model_year = Column(Numeric)
    new_vehicle_mfr_cost_dollars = Column(Float)
    cert_CO2_grams_per_mile = Column(Float)
    mfr_deemed_new_vehicle_generalized_cost_dollars = Column(Float)
    kwh_per_mile_cycle = Column(Float)

    @staticmethod
    def init_database_from_file(filename, verbose=False):
        import matplotlib.pyplot as plt
        import cost_curves

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.0004
        input_template_columns = {'cost_curve_class', 'model_year', 'cert_co2_grams_per_mile',
                                  'new_vehicle_mfr_cost_dollars', 'kWh_per_mile_cycle'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns,
                                                        verbose=verbose)

            if not template_errors:
                obj_list = []
                # load cloud data into database
                for i in df.index:
                    obj_list.append(CostCloud(
                        cost_curve_class=df.loc[i, 'cost_curve_class'],
                        model_year=df.loc[i, 'model_year'],
                        new_vehicle_mfr_cost_dollars=df.loc[i, 'new_vehicle_mfr_cost_dollars'],
                        cert_CO2_grams_per_mile=df.loc[i, 'cert_co2_grams_per_mile'],
                        kwh_per_mile_cycle=df.loc[i, 'kWh_per_mile_cycle'],
                    ))
                o2.session.add_all(obj_list)
                original_echo = o2.engine.echo
                o2.engine.echo = False  # cloud has a lot of points... turn off echo
                if verbose:
                    print('\nAdding cost cloud to database...')
                o2.session.flush()
                o2.engine.echo = original_echo

            # convert cost clouds into curves and set up cost_curves table...
            cost_curve_classes = df['cost_curve_class'].unique()
            # for each cost curve class
            for cost_curve_class in cost_curve_classes:
                if verbose:
                    print(cost_curve_class)
                class_cloud = df[df['cost_curve_class'] == cost_curve_class]
                cloud_model_years = class_cloud['model_year'].unique()
                # for each model year
                for model_year in cloud_model_years:
                    if verbose:
                        print(model_year)

                    cost_cloud = class_cloud[class_cloud['model_year'] == model_year]
                    frontier_df = CostCloud.calculate_frontier(cost_cloud, 'cert_co2_grams_per_mile',
                                                               'new_vehicle_mfr_cost_dollars')

                    if verbose and (model_year == cloud_model_years.min()):
                        import matplotlib.pyplot as plt
                        plt.figure()
                        plt.plot(cost_cloud['cert_co2_grams_per_mile'], cost_cloud['new_vehicle_mfr_cost_dollars'],
                                 '.')
                        plt.title('Cost versus CO2 %s' % cost_curve_class)
                        plt.xlabel('Combined GHG CO2 [g/mi]')
                        plt.ylabel('Combined GHG Cost [$]')
                        plt.plot(frontier_df['cert_co2_grams_per_mile'], frontier_df['new_vehicle_mfr_cost_dollars'],
                                 'r-')
                        plt.grid()
                        plt.savefig(o2.options.output_folder + 'Cost versus CO2 %s' % cost_curve_class)

                    cost_curves.CostCurve.init_database_from_lists(cost_curve_class, model_year,
                                                                   frontier_df['cert_co2_grams_per_mile'],
                                                                   frontier_df['new_vehicle_mfr_cost_dollars'])

            # plt.close()

        return template_errors

    @staticmethod
    def calculate_frontier(cloud, GHG_gpmi, GHG_cost):
        cloud = cloud.copy()

        result_df = pd.DataFrame()

        # find frontier starting point, lowest GHGs, and add to frontier
        result_df = result_df.append(cloud.loc[cloud[GHG_gpmi].idxmin()])

        # keep lower cost points
        cloud = cloud[cloud[GHG_cost] < result_df[GHG_cost].iloc[-1]]

        while len(cloud):
            # calculate frontier factor (more negative is more better) = slope of each point relative
            # to prior frontier point if frontier_social_affinity_factor = 1.0, else a "weighted" slope
            cloud['frontier_factor'] = (cloud[GHG_cost] - result_df[GHG_cost].iloc[-1]) \
                                       / (cloud[GHG_gpmi] - result_df[GHG_gpmi].iloc[-1]) \
                                       ** o2.options.cost_curve_frontier_affinity_factor

            # find next frontier point, lowest slope, and add to frontier lists
            result_df = result_df.append(cloud.loc[cloud['frontier_factor'].idxmin()])

            # keep lower cost points
            cloud = cloud[cloud[GHG_cost] < result_df[GHG_cost].iloc[-1]]

        result_df = result_df.drop('frontier_factor', axis=1)

        return result_df


    def calculate_generalized_cost(self, cost_curve_class):
        print(cost_curve_class)


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_log.init_logfile()
        o2.options.cost_file = 'input_samples/cost_clouds.csv'

        import cost_curves

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + CostCloud.init_database_from_file(o2.options.cost_file, verbose=True)

        if not init_fail:
            dump_omega_db_to_csv(o2.options.database_dump_folder)
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
