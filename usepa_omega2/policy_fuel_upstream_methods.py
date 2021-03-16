"""
policy_fuel_upstream_methods.py
===============================


"""

print('importing %s' % __file__)

from usepa_omega2 import *


class PolicyFuelUpstreamMethods(OMEGABase):
    methods = pd.DataFrame()

    @staticmethod
    def get_upstream_method(calendar_year):
        return PolicyFuelUpstreamMethods.methods['upstream_calculation_method'].loc[
                  PolicyFuelUpstreamMethods.methods['calendar_year'] == calendar_year].item()

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_upstream_method'
        input_template_version = 0.1
        input_template_columns = {'calendar_year', 'upstream_calculation_method'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                PolicyFuelUpstreamMethods.methods['calendar_year'] = df['calendar_year']
                PolicyFuelUpstreamMethods.methods['upstream_calculation_method'] = df['upstream_calculation_method']

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        from fuels import Fuel

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = o2.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + PolicyFuelUpstreamMethods.init_from_file(o2.options.fuel_upstream_methods_file,
                                                                  verbose=o2.options.verbose)

        if not init_fail:
            PolicyFuelUpstreamMethods.methods.to_csv(
                o2.options.database_dump_folder + os.sep + 'policy_fuel_upstream_values.csv', index=False)

            print(PolicyFuelUpstreamMethods.get_upstream_method(2020))
            print(PolicyFuelUpstreamMethods.get_upstream_method(2027))
            print(PolicyFuelUpstreamMethods.get_upstream_method(2050))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
