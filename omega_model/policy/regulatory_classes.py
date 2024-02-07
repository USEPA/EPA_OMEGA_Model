"""

**Routines to load, validate, and provide access to regulatory class ("reg" class) definition data**

Reg classes are defined by a name, and a brief description.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.  The template header uses a dynamic format.

The data represents regulatory classes by name and a brief description.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

        input_template_name:,``[module_name]``,input_template_version:,``[template_version]``

Sample Header
    .. csv-table::

       input_template_name:, policy.regulatory_classes, input_template_version:, 0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,description
        car,'cars' as defined by the regulations
        truck,'trucks' as defined by the regulations
        mediumduty,'2b3' as defined by the regulations

Data Column Name and Description

:reg_class_id:
    Name of the regulatory class.

:description:
    A brief description of the regulatory class.

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class RegulatoryClasses(OMEGABase, RegulatoryClassesBase):
    """
    **Load and provides routines to access to regulatory class descriptive data**

    """
    reg_classes = None

    _data = dict()

    @staticmethod
    def get_vehicle_reg_class(vehicle):
        """
        Get vehicle regulatory class based on vehicle characteristics.

        Args:
            vehicle (Vehicle): the vehicle to determine the reg class of

        Returns:

            Vehicle reg class based on vehicle characteristics.


        """
        reg_class_id = vehicle.base_year_reg_class_id
        return reg_class_id

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
        RegulatoryClasses._data.clear()
        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'reg_class_id', 'description'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                RegulatoryClasses._data = df.set_index('reg_class_id').to_dict(orient='index')

                RegulatoryClasses.reg_classes = df['reg_class_id'].to_list()

        return template_errors


if __name__ == '__main__':

    __name__ = '%s.%s' % (file_io.get_parent_foldername(__file__), file_io.get_filename(__file__))

    try:
        import os
        import importlib

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses

        init_fail += \
            omega_globals.options.RegulatoryClasses.init_from_file(omega_globals.options.policy_reg_classes_file,
                                                                   verbose=omega_globals.options.verbose)

        if not init_fail:
            print(omega_globals.options.RegulatoryClasses.reg_classes)

        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
