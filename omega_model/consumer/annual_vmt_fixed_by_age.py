"""

**Routines to load and provide access to annual vehicle miles travelled (VMT) by market class and age.**

The data represents a fixed VMT schedule by age.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents the re-registered proportion of vehicles by calendar year, age and market class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

        input_template_name:,consumer.annual_vmt_fixed_by_age,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_year,age,market_class_id,annual_vmt
        2019,0,non_hauling.BEV,14699.55515
        2019,1,non_hauling.BEV,14251.70373
        2019,2,non_hauling.BEV,14025.35397
        2019,0,hauling.ICE,15973.88982
        2019,1,hauling.ICE,15404.1216
        2019,2,hauling.ICE,14840.93011

:start_year:
    Start year of annual VMT data, values apply until the next available start year

:age:
    Vehicle age, in years

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:annual_vmt:
    Vehicle miles travelled per year at the given age for the given market class ID

----

**CODE**

"""

from omega_model import *


class OnroadVMT(OMEGABase, AnnualVMTBase):
    """
    **Loads and provides access to annual Vehicle Miles Travelled by calendar year, market class, and age.**

    """

    _data = dict()  # private dict, on-road VMT by market class ID and age
    cumulative_vmt = dict()

    @staticmethod
    def get_vmt(calendar_year, market_class_id, age):
        """
        Get vehicle miles travelled by calendar year, market class and age.

        Args:
            calendar_year (int): calendar year of the VMT data
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            (float) Annual vehicle miles travelled.

        """
        cache_key = (calendar_year, market_class_id, age)

        if cache_key not in OnroadVMT._data:
            start_years = np.array(OnroadVMT._data['start_year'][market_class_id])

            if len(start_years[start_years <= calendar_year]) > 0:
                year = max(start_years[start_years <= calendar_year])
                OnroadVMT._data[cache_key] = OnroadVMT._data[market_class_id, age, year]['annual_vmt']
            else:
                raise Exception('Missing onroad VMT fixed by age parameters for %s, %d or prior' %
                                (market_class_id, calendar_year))

        return OnroadVMT._data[cache_key]

    @staticmethod
    def get_cumulative_vmt(market_class_id, age):
        """
        Get the cumulative VMT for the given market class and age

        Args:
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            The cumulative VMT for the given market class and age

        """
        if (market_class_id, age) in OnroadVMT.cumulative_vmt:
            return OnroadVMT.cumulative_vmt[market_class_id, age]
        else:
            cumulative_vmt = sum([v['annual_vmt'] for k, v in OnroadVMT._data.items()
                                  if k[0] == market_class_id
                                  and k[1] <= age]
                                 )
            OnroadVMT.cumulative_vmt[market_class_id, age] = cumulative_vmt

            return cumulative_vmt

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
        OnroadVMT._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing from {filename}...')

        input_template_name = __name__
        input_template_version = 0.2
        input_template_columns = {'start_year', 'age', 'market_class_id', 'annual_vmt'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                validation_dict = {'market_class_id': omega_globals.options.MarketClass.market_classes}

                template_errors += validate_dataframe_columns(df, validation_dict, filename)

            if not template_errors:
                # OnroadVMT._data = df.set_index(['market_class_id','age']).sort_index().to_dict(orient='index')

                # convert dataframe to dict keyed by market class ID, age, and start year
                OnroadVMT._data = df.set_index(['market_class_id', 'age', 'start_year']).sort_index().to_dict(
                    orient='index')
                # add 'start_year' key which returns start years by market class ID
                OnroadVMT._data.update(
                    df[['market_class_id', 'age', 'start_year']].set_index('market_class_id').to_dict(orient='dict'))

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

        # pull in reg classes before initializing classes that check reg class validity
        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(
            omega_globals.options.policy_reg_classes_file)

        # pull in market classes before initializing classes that check market class validity
        module_name = get_template_name(omega_globals.options.market_classes_file)
        omega_globals.options.MarketClass = importlib.import_module(module_name).MarketClass
        init_fail += omega_globals.options.MarketClass.init_from_file(omega_globals.options.market_classes_file,
                                                verbose=omega_globals.options.verbose)

        init_fail += OnroadVMT.init_from_file(omega_globals.options.onroad_vmt_file,
                                              verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
