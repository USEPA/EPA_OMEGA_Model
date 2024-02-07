"""

**Routines to load, validate, and provide access to body style definition data**

Body styles defined by a name and a brief description.

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represents body style names and a brief description.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,body_styles,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        body_style_id,description
        sedan,Non-pickup / non-crossover / non-sport-utility vehicle
        pickup,Pickup truck / body-on-frame vehicle
        cuv_suv,Crossover / sport-utility vehicle

Data Column Name and Description

:body_style_id:
    Name of the body style

:description:
    A brief description of the body style

----

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class BodyStyles(OMEGABase):
    """
    **Load and provides routines to access drive cycle descriptive data**

    """

    body_styles = []  #: list of available body styles

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
        BodyStyles.body_styles = []

        if verbose:
            omega_log.logwrite('\nInitializing from %s...' % filename)

        input_template_name = 'body_styles'
        input_template_version = 0.1
        input_template_columns = {'body_style_id', 'description'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns,
                                                             verbose=verbose)

            if not template_errors:
                BodyStyles.body_styles = df['body_style_id'].unique()

        return template_errors


if __name__ == '__main__':
    try:
        import os

        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += BodyStyles.init_from_file(omega_globals.options.body_styles_file,
                                                verbose=omega_globals.options.verbose)

        if not init_fail:
            print(BodyStyles.body_styles)
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)
