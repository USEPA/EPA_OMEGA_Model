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
       input_template_name:, ``[module_name]``, input_template_version:, 0.1

Sample Header
    .. csv-table::

       input_template_name:, policy.regulatory_classes, input_template_version:, 0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        reg_class_id,description,,
        car,“cars” as defined by the regulations,,
        truck,“trucks” as defined by the regulations,,

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
    _data = pd.DataFrame()
    reg_classes = None

    @staticmethod
    def get_vehicle_reg_class(vehicle):
        """
        Get vehicle regulatory class based on vehicle characteristics.

        Args:
            vehicle (VehicleFinal): the vehicle to determine the reg class of

        Returns:

            Vehicle reg class based on vehicle characteristics.

        """
        if vehicle.passenger_capacity > 5:
            reg_class_id = '1_reg_class'
        else:
            reg_class_id = '2_reg_class'
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

        if verbose:
            omega_log.logwrite('\nInitializing database from %s...' % filename)

        input_template_name = __name__
        input_template_version = 0.1
        input_template_columns = {'reg_class_id', 'description'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                RegulatoryClasses._data['reg_class_id'] = df['reg_class_id']
                RegulatoryClasses._data['description'] = df['description']

                RegulatoryClasses.reg_classes = OMEGAEnum(RegulatoryClasses._data['reg_class_id'].to_list())

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
        init_omega_db(omega_globals.options.verbose)
        omega_log.init_logfile()

        SQABase.metadata.create_all(omega_globals.engine)

        module_name = get_template_name(omega_globals.options.policy_reg_classes_file)
        omega_globals.options.RegulatoryClasses = importlib.import_module(module_name).RegulatoryClasses

        init_fail = []
        init_fail += omega_globals.options.RegulatoryClasses.init_from_file(omega_globals.options.policy_reg_classes_file,
                                                                            verbose=omega_globals.options.verbose)

        if not init_fail:
            file_io.validate_folder(omega_globals.options.database_dump_folder)
            omega_globals.options.RegulatoryClasses._data.to_csv(
                omega_globals.options.database_dump_folder + os.sep + 'reg_class_data.csv', index=False)

            print(omega_globals.options.RegulatoryClasses.reg_classes)

        else:
            print(init_fail)

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
