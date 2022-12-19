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

Template Header
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

_cache = dict()  # the input file equations
start_years = dict()
_data = dict()  # private dict, work factors by year


class WorkFactor(OMEGABase):
    """
    **Work factor definition and calculations.**

    """
    # _cache = dict()  # the input file equations
    # start_years = dict()
    # _data = dict()  # private dict, work factors by year

    @staticmethod
    def calc_workfactor(year, curbwt, gvwr, gcwr, drive):
        """
        Calculate vehicle workfactor.

        Args:
            vehicle (Vehicle): the vehicle for which to calculate the workfactor

        Returns:
            Vehicle workfactor.

        """
        cache_key = (year, drive)

        locals_dict = locals()

        # if cache_key not in WorkFactor._data:

        # start_years = WorkFactor.start_years[drive]
        start_yrs = start_years[drive]

        if len([yr for yr in start_yrs if yr <= year]) > 0:

            model_year = max([yr for yr in start_yrs if yr <= year])

            gvwr_lbs, gcwr_lbs, curbweight_lbs = gvwr, gcwr, curbwt

            # xwd = WorkFactor._cache[(model_year, drive)]['xwd']
            xwd = _cache[(model_year, drive)]['xwd']

            # workfactor = eval(WorkFactor._cache[(model_year, drive)]['workfactor'], {}, locals_dict)
            workfactor = eval(_cache[(model_year, drive)]['workfactor'], {}, locals_dict)

            # WorkFactor._data[cache_key] = workfactor

        else:
            raise Exception(
                f'Missing workfactor calculation parameters for {year} or prior')

        return workfactor # WorkFactor._data[cache_key]
    # @staticmethod
    # def calc_workfactor(vehicle):
    #     """
    #     Calculate vehicle workfactor.
    #
    #     Args:
    #         vehicle (Vehicle): the vehicle for which to calculate the workfactor
    #
    #     Returns:
    #         Vehicle workfactor.
    #
    #     """
    #     cache_key = (vehicle.model_year, vehicle.drive_system)
    #
    #     locals_dict = locals()
    #
    #     if cache_key not in WorkFactor._data:
    #
    #         start_years = WorkFactor.start_years[vehicle.drive_system]
    #
    #         if len([yr for yr in start_years if yr <= vehicle.model_year]) > 0:
    #
    #             model_year = max([yr for yr in start_years if yr <= vehicle.model_year])
    #
    #             gvwr_lbs, gcwr_lbs, curbweight_lbs = vehicle.gvwr_lbs, vehicle.gcwr_lbs, vehicle.curbweight_lbs
    #
    #             xwd = WorkFactor._cache[(model_year, vehicle.drive_system)]['xwd']
    #
    #             workfactor = eval(WorkFactor._cache[(model_year, vehicle.drive_system)]['workfactor'], {}, locals_dict)
    #
    #             WorkFactor._data[cache_key] = workfactor
    #
    #         else:
    #             raise Exception(f'Missing workfactor calculation parameters for {vehicle.reg_class_id}, {vehicle.model_year} or prior')
    #
    #     return WorkFactor._data[cache_key]

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
        # WorkFactor._cache.clear()
        #
        # WorkFactor._data.clear()
        _cache.clear()

        _data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

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
                cache_keys = zip(
                    df['start_year'],
                    df['drive_system'],
                )
                for cache_key in cache_keys:
                    _cache[cache_key] = dict()

                    start_year, drive_system = cache_key

                    workfactor_info = df[(df['start_year'] == start_year)
                                         & (df['drive_system'] == drive_system)].iloc[0]

                    xwd = workfactor_info['xwd']

                    _cache[cache_key] = {
                        'workfactor': dict(),
                        'xwd': xwd
                    }

                    _cache[cache_key]['workfactor'] \
                        = compile(workfactor_info['workfactor'], '<string>', 'eval')

                for drive_system in df['drive_system'].unique():
                    start_years[drive_system] \
                        = [yr for yr in df.loc[df['drive_system'] == drive_system, 'start_year']]

        return template_errors
