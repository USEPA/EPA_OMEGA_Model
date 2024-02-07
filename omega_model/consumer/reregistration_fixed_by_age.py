"""

Vehicle re-registration, fixed by age.

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents the re-registered proportion of vehicles by model year, age and market class.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:,consumer.reregistration_fixed_by_age,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        start_model_year,age,market_class_id,reregistered_proportion
        1970,0,non_hauling.BEV,1
        1970,1,non_hauling.BEV,0.987841531
        1970,2,non_hauling.BEV,0.976587217
        1970,0,hauling.ICE,1
        1970,1,hauling.ICE,0.977597055
        1970,2,hauling.ICE,0.962974697

Data Column Name and Description

:start_model_year:
    The start vehicle model year of the re-registration data, values apply until next available start year

:age:
    Vehicle age, in years

:market_class_id:
    Vehicle market class ID, e.g. 'hauling.ICE'

:reregistered_proportion:
    The fraction of vehicles re-registered, [0..1]

----

**CODE**


"""

from omega_model import *


class Reregistration(OMEGABase, ReregistrationBase):
    """
    **Load and provide access to vehicle re-registration data by model year, market class ID and age.**

    """
    _data = dict()

    @staticmethod
    def get_reregistered_proportion(model_year, market_class_id, age):
        """
        Get vehicle re-registered proportion [0..1] by market class and age.

        Args:
            model_year (int): the model year of the re-registration data
            market_class_id (str): market class id, e.g. 'hauling.ICE'
            age (int): vehicle age in years

        Returns:
            Re-registered proportion [0..1]

        """

        cache_key = (model_year, market_class_id, age)

        if cache_key not in Reregistration._data:
            start_years = Reregistration._data['start_model_year'][market_class_id].values

            max_age = int(max(Reregistration._data['age'][market_class_id].values))

            if age > max_age:
                Reregistration._data[cache_key] = 0
            elif len(start_years[start_years <= model_year]) > 0:
                year = max(start_years[start_years <= model_year])
                Reregistration._data[cache_key] = \
                    Reregistration._data[market_class_id, age, year]['reregistered_proportion']
            else:
                raise Exception('Missing registration fixed by age parameters for %s, %d or prior' %
                                (market_class_id, calendar_year))

        return Reregistration._data[cache_key]

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
        Reregistration._data.clear()

        if verbose:
            omega_log.logwrite(f'\nInitializing from {filename}...')

        input_template_name = __name__
        input_template_version = 0.2
        input_template_columns = {'start_model_year', 'age', 'market_class_id', 'reregistered_proportion'}

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
            # Reregistration._data = df.set_index(['market_class_id', 'age']).sort_index().to_dict(orient='index')

            # convert dataframe to dict keyed by market class ID, age, and start year
            Reregistration._data = df.set_index(['market_class_id', 'age', 'start_model_year']).\
                sort_index().to_dict(orient='index')
            # add 'start_year' key which returns start years by market class ID
            Reregistration._data.update(
                df[['market_class_id', 'age', 'start_model_year']].set_index('market_class_id').
                    to_dict(orient='series'))

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        import importlib

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

        init_fail += Reregistration.init_from_file(
            omega_globals.options.vehicle_reregistration_file, verbose=omega_globals.options.verbose)

        if not init_fail:
            pass
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
