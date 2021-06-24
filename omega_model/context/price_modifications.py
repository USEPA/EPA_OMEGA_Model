"""


----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *

price_modification = 'price_modification_dollars'

class PriceModifications(OMEGABase):
    values = pd.DataFrame()

    @staticmethod
    def get_price_modification(calendar_year, market_class_id):
        start_years = PriceModifications.values['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        mod_key = '%s:%s' % (market_class_id, price_modification)
        if mod_key in PriceModifications.values:
            return PriceModifications.values['%s:%s' % (market_class_id, price_modification)].loc[
                PriceModifications.values['start_year'] == calendar_year].item()
        else:
            return 0

    @staticmethod
    def init_from_file(filename, verbose=False):
        import numpy as np

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_price_modifications'
        input_template_version = 0.2
        input_template_columns = {'start_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                from consumer.market_classes import MarketClass

                PriceModifications.values['start_year'] = np.array(df['start_year'])

                share_columns = [c for c in df.columns if (price_modification in c)]

                for sc in share_columns:
                    market_class = sc.split(':')[0]
                    if market_class in MarketClass.market_classes:
                        PriceModifications.values[sc] = df[sc]
                    else:
                        template_errors.append('*** Invalid Market Class "%s" in %s ***' % (market_class, filename))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from consumer.market_classes import MarketClass

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_globals.engine.echo = omega_globals.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += MarketClass.init_database_from_file(omega_globals.options.market_classes_file,
                                                         verbose=omega_globals.options.verbose)
        init_fail += PriceModifications.init_from_file(omega_globals.options.price_modifications_file,
                                                       verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            PriceModifications.values.to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'policy_price_modifications.csv', index=False)

            print(PriceModifications.get_price_modification(2020, 'hauling.BEV'))
            print(PriceModifications.get_price_modification(2020, 'non_hauling.BEV'))
            print(PriceModifications.get_price_modification(2020, 'hauling.ICE'))
            print(PriceModifications.get_price_modification(2020, 'non_hauling.ICE'))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)