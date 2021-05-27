"""
GHG_standards_sales_incentives.py
=================================


"""

print('importing %s' % __file__)

from usepa_omega2 import *

input_template_name = 'incentive_sales_multipliers'

cache = dict()


class GHGStandardIncentives(OMEGABase):
    # --- database table properties ---

    @staticmethod
    def get_sales_incentive(vehicle):
        incentive_sales_multiplier = 1

        start_years = cache['start_year']
        if start_years[start_years <= vehicle.model_year]:
            cache_key = max(start_years[start_years <= vehicle.model_year])

            if cache_key in cache:
                calcs = cache[cache_key]
                for calc, multiplier in calcs.items():
                    select_attribute, select_value = calc.split(':')
                    if vehicle.__getattribute__(select_attribute) == select_value:
                        incentive_sales_multiplier = multiplier

        return incentive_sales_multiplier

    @staticmethod
    def init_from_file(filename, verbose=False):
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_version = 0.2
        input_template_columns = {'start_year'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                df = df.set_index('start_year')
                df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')

                for idx, r in df.iterrows():
                    if idx not in cache:
                        cache[idx] = dict()

                    cache[idx] = r.to_dict()

                cache['start_year'] = np.array(list(cache.keys()))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()

        init_omega_db()
        omega_log.init_logfile()

        init_fail = []
        init_fail = init_fail + GHGStandardIncentives.init_from_file(o2.options.ghg_standards_sales_incentives_file,
                                                                             verbose=o2.options.verbose)

        if not init_fail:
            class dummyVehicle:
                model_year = 2020
                fueling_class = 'BEV'

            v = dummyVehicle()
            print(GHGStandardIncentives.get_sales_incentives(v, 1.0))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)