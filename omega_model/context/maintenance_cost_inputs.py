"""

**Routines to load Maintenance Cost Inputs.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in effects calculations.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,maintenance_cost_inputs,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,miles_per_event_ice,miles_per_event_hev,miles_per_event_phev,miles_per_event_bev,USD_per_event,dollar_basis
        Engine Oil,7500,7500,9000,0,65,2019
        Oil Filter,7500,7500,9000,0,20,2019
        Tire Rotation,7500,7500,7500,7500,50,2019

Data Column Name and Description

:item:
    The maintenance attribute name.

:miles_per_event_ice:
    The attribute value for ICE vehicles.

:miles_per_event_hev:
    The attribute value for HEVs.

:miles_per_event_phev:
    The attribute value for PHEVs.

:miles_per_event_bev:
    The attribute value for BEVs.

:USD_per_event:
    The cost per maintenance event.

:dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

**CODE**

"""

print('importing %s' % __file__)

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class MaintenanceCostInputs(OMEGABase):
    """
    **Loads and provides access to maintenance cost input values for effects calculations.**

    """
    _data = dict()  # private dict of general input attributes and values

    @staticmethod
    def get_value(attribute, veh_type):
        """
        Get the attribute value for the given attribute.

        Args:
            attribute (str): the attribute(s) for which value(s) are sought.
            veh_type (str): the vehicle type (ICE, HEV, PHEV, BEV).

        Returns:
            The value of the given attribute for the given veh_type.

        """
        attribute_value = MaintenanceCostInputs._data[attribute][f'usd_per_mile_{veh_type}']

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
        # import numpy as np

        MaintenanceCostInputs._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'maintenance_cost_inputs'
        input_template_version = 0.1
        input_template_columns = {'item',
                                  'miles_per_event_ice',
                                  'miles_per_event_hev',
                                  'miles_per_event_phev',
                                  'miles_per_event_bev',
                                  'USD_per_event',
                                  'dollar_basis',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            cols_to_convert = [col for col in df.columns if 'USD_' in col]

            df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            if not template_errors:
                working_dict = df.set_index('item').to_dict(orient='index')
                working_dict = MaintenanceCostInputs.calc_maintenance_cost_per_mile(working_dict)
                MaintenanceCostInputs._data = working_dict

        return template_errors

    @staticmethod
    def calc_maintenance_cost_per_mile(input_dict):
        """

        Args:
            input_dict: Dictionary of the maintenance cost inputs.

        Returns:
            The input_dict with the total maintenance cost per mile added.

        """
        veh_types = ['ice', 'hev', 'phev', 'bev']

        # calc cost per mile for each maintenance event
        for key in input_dict.keys():
            cost_per_event = input_dict[key]['USD_per_event']
            for veh_type in veh_types:
                miles_per_event = input_dict[key][f'miles_per_event_{veh_type}']
                try: # protect against divide by zero
                    input_dict[key].update({f'cost_per_mile_{veh_type}': cost_per_event / miles_per_event})
                except:
                    input_dict[key].update({f'cost_per_mile_{veh_type}': 0})

        # calc total cost per mile for each veh_type, first add a new key and nested dict to hold totals
        input_dict.update({'total_maintenance': {}})
        for veh_type in veh_types:
            input_dict['total_maintenance'].update({f'cost_per_mile_{veh_type}': 0})

        for veh_type in veh_types:
            total = 0
            for key in input_dict.keys():
                total += input_dict[key][f'cost_per_mile_{veh_type}']
            input_dict['total_maintenance'].update({f'cost_per_mile_{veh_type}': total})

        return input_dict


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(file_io.get_filenameext(__file__))

        from context.onroad_fuels import OnroadFuel

        # set up global variables:
        omega_globals.options = OMEGASessionSettings()
        omega_log.init_logfile()

        init_fail = []

        init_fail += MaintenanceCostInputs.init_from_file(omega_globals.options.maintenance_cost_inputs_file,
                                                          verbose=omega_globals.options.verbose)

        if not init_fail:
            print(MaintenanceCostInputs.get_value('total_cost_per_mile', 'ice'))
            print(MaintenanceCostInputs.get_value('total_cost_per_mile', 'hev'))
            print(MaintenanceCostInputs.get_value('total_cost_per_mile', 'phev'))
            print(MaintenanceCostInputs.get_value('total_cost_per_mile', 'bev'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
