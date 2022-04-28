"""

**Routines to load General Inputs for Effects.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in effects calculations.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,general_inputs_for_effects,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,value,notes
        gal_per_bbl,42,gallons per barrel of oil
        imported_oil_share,0.91,estimated oil import reduction as percent of total oil demand reduction
        grams_per_uston,907185,

Data Column Name and Description

:item:
    The attribute name.

:value:
    The attribute value

:notes:
    Descriptive information regarding the attribute name and/or value.

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *


class GeneralInputsForEffects(OMEGABase):
    """
    **Loads and provides access to general input values for effects calculations.**

    """
    _data = dict()  # private dict of general input attributes and values

    @staticmethod
    def get_value(attribute):
        """
        Get the attribute value for the given attribute.

        Args:
            attribute (str): the attribute(s) for which value(s) are sought.

        Returns:
            The value of the given attribute.

        """
        attribute_value = GeneralInputsForEffects._data[attribute]['value']

        return attribute_value


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
        GeneralInputsForEffects._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'general_inputs_for_effects'
        input_template_version = 0.1
        input_template_columns = {'item', 'value', 'notes'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                GeneralInputsForEffects._data = df.set_index('item').to_dict(orient='index')

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from context.onroad_fuels import OnroadFuel

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += GeneralInputsForEffects.init_from_file(omega_globals.options.general_inputs_for_effects_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            print(GeneralInputsForEffects.get_value('gal_per_bbl'))
            print(GeneralInputsForEffects.get_value('imported_oil_share'))
            print(GeneralInputsForEffects.get_value('grams_per_uston'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
