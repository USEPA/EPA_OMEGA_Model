"""
production_constraints.py
=========================


"""

print('importing %s' % __file__)

from usepa_omega2 import *

min_share_units = 'minimum_share'
max_share_units = 'maximum_share'

class ProductionConstraints(OMEGABase):
    values = pd.DataFrame()

    @staticmethod
    def get_minimum_share(calendar_year, market_class_id):
        return ProductionConstraints.values['%s:%s' % (market_class_id, min_share_units)].loc[
            ProductionConstraints.values['calendar_year'] == calendar_year].item()

    @staticmethod
    def get_maximum_share(calendar_year, market_class_id):
        return ProductionConstraints.values['%s:%s' % (market_class_id, max_share_units)].loc[
            ProductionConstraints.values['calendar_year'] == calendar_year].item()

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'production_constraints'
        input_template_version = 0.1
        input_template_columns = {'calendar_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                from consumer.market_classes import MarketClass

                ProductionConstraints.values['calendar_year'] = df['calendar_year']

                share_columns = [c for c in df.columns if (min_share_units in c) or (max_share_units in c)]

                for sc in share_columns:
                    market_class = sc.split(':')[0]
                    if market_class in MarketClass.market_classes:
                        ProductionConstraints.values[sc] = df[sc]
                    else:
                        template_errors.append('*** Invalid Market Class "%s" in %s ***' % (market_class, filename))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        from consumer.market_classes import MarketClass

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = o2.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + MarketClass.init_database_from_file(o2.options.market_classes_file,
                                                                    verbose=o2.options.verbose)
        init_fail = init_fail + ProductionConstraints.init_from_file(o2.options.production_constraints_file,
                                                                     verbose=o2.options.verbose)

        if not init_fail:
            fileio.validate_folder(o2.options.database_dump_folder)
            ProductionConstraints.values.to_csv(
                o2.options.database_dump_folder + os.sep + 'production_constraints.csv', index=False)

            print(ProductionConstraints.get_minimum_share(2020, 'hauling.BEV'))
            print(ProductionConstraints.get_minimum_share(2020, 'non_hauling.BEV'))
            print(ProductionConstraints.get_maximum_share(2020, 'hauling.ICE'))
            print(ProductionConstraints.get_maximum_share(2020, 'non_hauling.ICE'))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
