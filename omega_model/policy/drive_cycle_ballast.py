"""

**Implements a portion of the GCAM model related to the relative shares of ICE and BEV vehicles as a function
of relative generalized costs and assumptions about consumer acceptance over time (the S-shaped adoption curve).**

Relative shares are converted to absolute shares for use in the producer compliance search.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents GCAM consumer model input parameters.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,``[module_name]``,input_template_version:,0.12

Sample Header
    .. csv-table::

       input_template_name:,consumer.sales_share,input_template_version:,0.12

Sample Data Columns
    .. csv-table::
        :widths: auto

        market_class_id,start_year,annual_vmt,payback_years,price_amortization_period,share_weight,discount_rate,o_m_costs,average_occupancy,logit_exponent_mu
        hauling.BEV,2020,12000,5,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2021,12000,5,5,0.142,0.1,1600,1.58,-8
        hauling.BEV,2022,12000,5,5,0.168,0.1,1600,1.58,-8

Data Column Name and Description

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:start_year:
    Start year of parameters, parameters apply until the next available start year

:annual_vmt:
    Vehicle miles travelled per year

:payback_years:
    Payback period, in years

:price_amortization_period:
    Price amorization period, in years

:share_weight:
    Share weight [0..1]

:discount_rate:
    Discount rate [0..1]

:o_m_costs:
    Operating and maintenance costs, dollars per year

:average_occupancy:
    Average vehicle occupancy, number of people

:logit_exponent_mu:
    Logit exponent, mu

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class DriveCycleBallast(OMEGABase):
    """
    Loads and provides access to drive cycle ballast data.

    """
    _data = dict()

    @staticmethod
    def get_ballast_lbs(vehicle):
        """
        Get drive cycle ballast for the given vehicle.

        Args:
            vehicle (Vehicle): the vehicle to get drive cycle ballast for

        Returns:
            Drive cycle ballast in pounds

        """

        cache_key = (vehicle.reg_class_id, vehicle.model_year)

        if cache_key not in DriveCycleBallast._data:

            start_years = DriveCycleBallast._data[vehicle.reg_class_id]['start_year']
            if len(start_years[start_years <= vehicle.model_year]) > 0:
                calendar_year = max(start_years[start_years <= vehicle.model_year])

                DriveCycleBallast._data[cache_key] = \
                    Eval.eval(DriveCycleBallast._data[vehicle.reg_class_id, calendar_year]['ballast_lbs'], {},
                              {'vehicle': vehicle})
            else:
                raise Exception('Missing drive cycle ballast parameters for %s, %d or prior' %
                                (vehicle.reg_class_id, vehicle.model_year))

        return DriveCycleBallast._data[cache_key]

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


        DriveCycleBallast._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = 'drive_cycle_ballast'
        input_template_version = 0.1
        input_template_columns = {'start_year', 'reg_class_id', 'ballast_lbs'
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

        if not template_errors:
            df = df.drop([c for c in df.columns if 'Unnamed' in c], axis='columns')

            validation_dict = {'reg_class_id': list(legacy_reg_classes)}

            template_errors += validate_dataframe_columns(df, validation_dict, filename)

        if not template_errors:
            DriveCycleBallast._data = df.set_index(['reg_class_id', 'start_year']).sort_index().to_dict(orient='index')

            for rc in df['reg_class_id'].unique():
                DriveCycleBallast._data[rc] = {'start_year': np.array(df['start_year'].loc[df['reg_class_id'] == rc])}

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += DriveCycleBallast.init_from_file(omega_globals.options.drive_cycle_ballast_file,
                                                      verbose=omega_globals.options.verbose)

        if not init_fail:
            class Vehicle:
                model_year = 2020
                reg_class_id = list(legacy_reg_classes)[0]

            print(DriveCycleBallast.get_ballast_lbs(Vehicle))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
