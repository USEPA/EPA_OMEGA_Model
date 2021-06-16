"""
GHG_standards_incentives.py
===========================

**Routines to load and provide access to 'incentives' such as production multipliers for battery-electric vehicles.**

Currently, only production multipliers are implemented here, but other incentives may be added later.


Input File Format
-----------------

The input file format uses a flexible column header notation, as detailed below.

Column Name and Description
    :start_year:
        Start year of incentive, incentive applies until the next available start year

    :dynamic column(s):
        One or more dynamic columns with the format
        ``{attribute_name}:{attribute_value}``

        Example:
            ``fueling_class:BEV`` => ``if vehicle.fueling_class == 'BEV' then apply incentive``

"""

print('importing %s' % __file__)

from usepa_omega2 import *

cache = dict()


class GHGStandardIncentives(OMEGABase):
    """
    **Loads and provides access to GHG incentives.**

    """
    @staticmethod
    def get_production_multiplier(vehicle):
        """
        Get production multiplier (if any) for the given vehicle.

        Args:
            vehicle (Vehicle): the vehicle to get the multiplier for

        Returns:

            The production multiplier, if applicable, or 1.0

        """
        production_multiplier = 1

        start_years = cache['start_year']
        if start_years[start_years <= vehicle.model_year]:
            cache_key = max(start_years[start_years <= vehicle.model_year])

            if cache_key in cache:
                calcs = cache[cache_key]
                for calc, multiplier in calcs.items():
                    select_attribute, select_value = calc.split(':')
                    if vehicle.__getattribute__(select_attribute) == select_value:
                        production_multiplier = multiplier

        return production_multiplier

    @staticmethod
    def init_from_file(filename, verbose=False):
        """

        Initialize class data from input file.

        Args:
            filename (str): name of input file
            verbose (bool): enable additional console and logfile output if True

        Returns:
            List of template/input errors, else empty list on success

        """
        import numpy as np

        cache.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'production_multipliers'
        input_template_version = 0.21
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
        init_fail += GHGStandardIncentives.init_from_file(o2.options.production_multipliers_file,
                                                                     verbose=o2.options.verbose)

        if not init_fail:
            class dummyVehicle:
                model_year = 2020
                fueling_class = 'BEV'

            v = dummyVehicle()
            print(GHGStandardIncentives.get_production_multipliers(v, 1.0))

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)