"""


----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


cache = dict()


def upstream_zero(vehicle, co2_grams_per_mile, kwh_per_mile):
    return 0


def upstream_xev_ice_delta(vehicle, co2_grams_per_mile, kwh_per_mile):
    from policy.policy_fuel_upstream import PolicyFuelUpstream
    from policy.policy_fuels import PolicyFuel
    import numpy as np

    if vehicle.fueling_class == 'BEV':
        upstream_gco2_per_kwh = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year,
                                                                                    'US electricity')
        upstream_inefficiency = PolicyFuelUpstream.get_upstream_inefficiency(vehicle.model_year, 'US electricity')
        upstream_gco2_per_gal = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'pump gasoline')
        fuel_gco2_per_gal = PolicyFuel.get_fuel_attributes(vehicle.model_year, 'MTE gasoline',
                                                                 'cert_co2_grams_per_unit')

        upstream = np.maximum(0, kwh_per_mile * upstream_gco2_per_kwh / (1 - upstream_inefficiency) -
                              vehicle.cert_target_co2_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal)
    else:
        upstream = 0

    return upstream


def upstream_actual(vehicle, co2_grams_per_mile, kwh_per_mile):
    from policy.policy_fuel_upstream import PolicyFuelUpstream
    from policy.policy_fuels import PolicyFuel

    upstream_gco2_per_kwh = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'US electricity')
    upstream_inefficiency = PolicyFuelUpstream.get_upstream_inefficiency(vehicle.model_year, 'US electricity')
    upstream_gco2_per_gal = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'pump gasoline')
    fuel_gco2_per_gal = PolicyFuel.get_fuel_attributes(vehicle.model_year, 'MTE gasoline',
                                                             'cert_co2_grams_per_unit')

    # TODO: need "utility factor" or percentage of electric and gas miles to weight these terms
    upstream = kwh_per_mile * upstream_gco2_per_kwh / (1 - upstream_inefficiency) + \
                          co2_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal

    return upstream


upstream_method_dict = {'upstream_zero': upstream_zero, 'upstream_xev_ice_delta': upstream_xev_ice_delta,
                        'upstream_actual': upstream_actual}


class UpstreamMethods(OMEGABase):
    methods = pd.DataFrame()

    @staticmethod
    def get_upstream_method(calendar_year):

        start_years = cache['start_year']
        calendar_year = max(start_years[start_years <= calendar_year])

        method = UpstreamMethods.methods['upstream_calculation_method'].loc[
            UpstreamMethods.methods['start_year'] == calendar_year].item()

        return upstream_method_dict[method]

    @staticmethod
    def init_from_file(filename, verbose=False):

        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_fuel_upstream_methods'
        input_template_version = 0.2
        input_template_columns = {'start_year', 'upstream_calculation_method'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                UpstreamMethods.methods['start_year'] = df['start_year']
                UpstreamMethods.methods['upstream_calculation_method'] = df['upstream_calculation_method']

            cache['start_year'] = np.array(list(df['start_year']))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from context.onroad_fuels import OnroadFuel

        # set up global variables:
        omega_globals.options = OMEGARuntimeOptions()
        init_omega_db()
        omega_globals.engine.echo = omega_globals.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        init_fail = []
        init_fail += UpstreamMethods.init_from_file(omega_globals.options.fuel_upstream_methods_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            UpstreamMethods.methods.to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'policy_fuel_upstream_values.csv', index=False)

            print(UpstreamMethods.get_upstream_method(2020))
            print(UpstreamMethods.get_upstream_method(2027))
            print(UpstreamMethods.get_upstream_method(2050))
        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
