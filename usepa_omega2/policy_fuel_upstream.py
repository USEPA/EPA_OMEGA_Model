"""
policy_fuel_upstream.py
=======================


"""

print('importing %s' % __file__)

from usepa_omega2 import *

co2_units = 'co2e_grams_per_unit'

class PolicyFuelUpstream(OMEGABase):
    values = pd.DataFrame()

    @staticmethod
    def get_upstream_co2e_grams_per_unit(calendar_year, fuel_ID):
        return PolicyFuelUpstream.values['%s:%s' % (fuel_ID, co2_units)].loc[
                  PolicyFuelUpstream.values['calendar_year'] == calendar_year].item()

    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_fuel_upstream'
        input_template_version = 0.1
        input_template_columns = {'calendar_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                from fuels import Fuel

                PolicyFuelUpstream.values['calendar_year'] = df['calendar_year']

                fuel_columns = [c for c in df.columns if co2_units in c]

                for fc in fuel_columns:
                    fuel = fc.split(':')[0]
                    if Fuel.validate_fuel_ID(fuel):
                        PolicyFuelUpstream.values[fc] = df[fc]
                    else:
                        template_errors.append('*** Invalid Policy Upstream fuel ID "%s" in %s ***' % (fuel, filename))

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
        init_fail = init_fail + Fuel.init_database_from_file(o2.options.fuels_file, verbose=o2.options.verbose)
        init_fail = init_fail + PolicyFuelUpstream.init_from_file(o2.options.fuel_upstream_file,
                                                                  verbose=o2.options.verbose)

        if not init_fail:
            fileio.validate_folder(o2.options.database_dump_folder)
            PolicyFuelUpstream.values.to_csv(
                o2.options.database_dump_folder + os.sep + 'policy_fuel_upstream_values.csv', index=False)

            print(PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(2020, 'pump gasoline'))
            print(PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(2021, 'US electricity'))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
