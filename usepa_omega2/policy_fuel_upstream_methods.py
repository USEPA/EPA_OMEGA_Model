"""
policy_fuel_upstream_methods.py
===============================


"""

print('importing %s' % __file__)

from usepa_omega2 import *


def upstream_zero(vehicle, co2_grams_per_mile, kwh_per_mile):
    return 0


def upstream_xev_ice_delta(vehicle, co2_grams_per_mile, kwh_per_mile):
    from policy_fuel_upstream import PolicyFuelUpstream
    from GHG_standards_fuels import GHGStandardFuels
    import numpy as np

    if vehicle.fueling_class == 'BEV':
        upstream_gco2_per_kwh = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'US electricity')
        upstream_inefficiency = PolicyFuelUpstream.get_upstream_inefficiency(vehicle.model_year, 'US electricity')
        upstream_gco2_per_gal = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'pump gasoline')
        fuel_gco2_per_gal = GHGStandardFuels.get_fuel_attributes('MTE gasoline', 'cert_co2_grams_per_unit')

        upstream = np.maximum(0, kwh_per_mile * upstream_gco2_per_kwh / (1 - upstream_inefficiency) -
                              vehicle.cert_target_co2_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal)
    else:
        upstream = 0

    return upstream


def upstream_actual(vehicle, co2_grams_per_mile, kwh_per_mile):
    from policy_fuel_upstream import PolicyFuelUpstream
    from GHG_standards_fuels import GHGStandardFuels

    upstream_gco2_per_kwh = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'US electricity')
    upstream_inefficiency = PolicyFuelUpstream.get_upstream_inefficiency(vehicle.model_year, 'US electricity')
    upstream_gco2_per_gal = PolicyFuelUpstream.get_upstream_co2e_grams_per_unit(vehicle.model_year, 'pump gasoline')
    fuel_gco2_per_gal = GHGStandardFuels.get_fuel_attributes('MTE gasoline', 'cert_co2_grams_per_unit')

    # TODO: need "utility factor" or percentage of electric and gas miles to weight these terms
    upstream = kwh_per_mile * upstream_gco2_per_kwh / (1 - upstream_inefficiency) + \
                          co2_grams_per_mile * upstream_gco2_per_gal / fuel_gco2_per_gal

    return upstream


upstream_method_dict = {'upstream_zero': upstream_zero, 'upstream_xev_ice_delta': upstream_xev_ice_delta,
                        'upstream_actual': upstream_actual}


class PolicyFuelUpstreamMethods(OMEGABase):
    methods = pd.DataFrame()

    @staticmethod
    def get_upstream_method(calendar_year):
        method = PolicyFuelUpstreamMethods.methods['upstream_calculation_method'].loc[
                PolicyFuelUpstreamMethods.methods['calendar_year'] == calendar_year].item()
        return upstream_method_dict[method]


    @staticmethod
    def init_from_file(filename, verbose=False):
        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'policy_fuel_upstream_methods'
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
            fileio.validate_folder(o2.options.database_dump_folder)
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
