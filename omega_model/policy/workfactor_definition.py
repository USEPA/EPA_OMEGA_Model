"""

**Loads parameters and provides calculations for calculating the work factor.**

This is based on the current work factor based standards, with two liquid fuel types and with lifetime VMT and
parameter-based target calculations based on work factor with work factor defined in the work_factor_definition file.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represent the work factor calculation based on drive system (e.g., 2wd, 4wd) and weigh characteristics.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,workfactor_definition,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,drive_system,xwd,workfactor
        2014,2,0,(0.75) * (gvwr_lbs - curbweight_lbs + xwd) + 0.25 * (gcwr_lbs - gvwr_lbs)
        2014,4,500,(0.75) * (gvwr_lbs - curbweight_lbs + xwd) + 0.25 * (gcwr_lbs - gvwr_lbs)

Data Column Name and Description

:start_year:
    The start year of the standard, applies until the next available start year

:drive_system:
    2-wheel drive (2) or 4-wheel drive (4)

:xwd:
    The weight adjustment associated with drive system

:work_factor:
    The calculation for work factor

----

**CODE**

"""
import pandas as pd

print('importing %s' % __file__)

from omega_model import *


class WorkFactor(OMEGABase):
    """
    **Work factor definition and calculations.**

    """
    _cache = dict()  # the input file equations
    start_years = dict()
    _data = dict()  # private dict, work factors by year

    @staticmethod
    def calc_workfactor(model_year, curbweight_lbs, gvwr_lbs, gcwr_lbs, drive_system):
        """
        Calculate vehicle workfactor.

        Args:
            model_year (int): vehicle model year
            curbweight_lbs (float): vehicle curb weight in lbs
            gvwr_lbs (float): vehicle gross vehicle weight rating in lbs
            gcwr_lbs (float): vehicle combined weight rating in lbs
            drive_system (int): drive system, 2=two wheel drive, 4=four wheel drive, etc

        Returns:
            Vehicle workfactor.

        """
        cache_key = (model_year, drive_system)

        start_years = WorkFactor.start_years[drive_system]

        if len([yr for yr in start_years if yr <= model_year]) > 0:

            model_year = max([yr for yr in start_years if yr <= model_year])

            xwd = WorkFactor._cache[(model_year, drive_system)]['xwd']

            workfactor = eval(WorkFactor._cache[(model_year, drive_system)]['workfactor'], {'np': np}, locals())

        else:
            raise Exception(
                f'Missing workfactor calculation parameters for {model_year} or prior')

        return workfactor

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
        WorkFactor._cache.clear()
        WorkFactor.start_years.clear()
        WorkFactor._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'workfactor_definition'
        input_template_version = 0.1
        input_template_columns = {
            'start_year',
            'drive_system',
            'xwd',
            'workfactor',
        }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:

                df['workfactor'] = df['workfactor'] \
                    .apply(lambda x: str.replace(x, 'max(', 'np.maximum(').replace('min(', 'np.minimum('))

                cache_keys = zip(
                    df['start_year'],
                    df['drive_system'],
                )
                for cache_key in cache_keys:
                    WorkFactor._cache[cache_key] = dict()

                    start_year, drive_system = cache_key

                    workfactor_info = df[(df['start_year'] == start_year)
                                         & (df['drive_system'] == drive_system)].iloc[0]

                    xwd = workfactor_info['xwd']

                    WorkFactor._cache[cache_key] = {
                        'workfactor': dict(),
                        'xwd': xwd
                    }

                    WorkFactor._cache[cache_key]['workfactor'] \
                        = compile(str(workfactor_info['workfactor']), '<string>', 'eval')

                for drive_system in df['drive_system'].unique():
                    WorkFactor.start_years[drive_system] \
                        = [yr for yr in df.loc[df['drive_system'] == drive_system, 'start_year']]

        return template_errors
