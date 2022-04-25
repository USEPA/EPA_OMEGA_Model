"""

**Routines to load Maintenance Cost Inputs.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in maintenance cost calculations.

File Type
    comma-separated values (CSV)

Template Header
    .. csv-table::

       input_template_name:,maintenance_cost,input_template_version:,0.2

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,miles_per_event_ICE,miles_per_event_HEV,miles_per_event_PHEV,miles_per_event_BEV,dollars_per_event,dollar_basis
        Engine Oil,7500,7500,9000,,65,2019
        Oil Filter,7500,7500,9000,,20,2019
        Tire Rotation,7500,7500,7500,7500,50,2019

Data Column Name and Description

:item:
    The maintenance attribute name.

:miles_per_event_ICE:
    The attribute value for ICE vehicles.

:miles_per_event_HEV:
    The attribute value for HEVs.

:miles_per_event_PHEV:
    The attribute value for PHEVs.

:miles_per_event_BEV:
    The attribute value for BEVs.

:dollars_per_event:
    The cost in US dollars per maintenance event.

:dollar_basis:
        The dollar basis of values within the table. Values are converted in-code to 'analysis_dollar_basis' using the
        implicit_price_deflators input file.

**CODE**

"""

print('importing %s' % __file__)

# reactivate these imports for QA/QC of this module
# from scipy.optimize import curve_fit
# from matplotlib import pyplot

from omega_model import *
import omega_model.effects.general_functions as gen_fxns


class MaintenanceCost(OMEGABase):
    """
    **Loads and provides access to maintenance cost input values for effects calculations.**

    """
    _data = dict()  # private dict of general input attributes and values

    @staticmethod
    def get_maintenance_cost_curve_coefficients(veh_type):
        """

        Args:
            veh_type (string): The type of powertrain in the vehicle, e.g., 'ICE', 'BEV', 'HEV', 'PHEV'

        Returns:
            The maintenance cost curve coefficients for the given veh_type.

        """

        return MaintenanceCost._data[veh_type]

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
        MaintenanceCost._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'maintenance_cost'
        input_template_version = 0.2
        input_template_columns = {'item',
                                  'miles_per_event_ICE',
                                  'miles_per_event_HEV',
                                  'miles_per_event_PHEV',
                                  'miles_per_event_BEV',
                                  'dollars_per_event',
                                  'dollar_basis',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)
            df = df.loc[df['dollar_basis'] != 0, :]

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            cols_to_convert = [col for col in df.columns if 'dollars_per_event' in col]

            df = gen_fxns.adjust_dollars(df, 'ip_deflators', omega_globals.options.analysis_dollar_basis, *cols_to_convert)

            maintenance_cost_curve_dict = MaintenanceCost.calc_maintenance_cost_per_mile_curve(df)

            if not template_errors:
                MaintenanceCost._data = maintenance_cost_curve_dict.copy()

        return template_errors

    @staticmethod
    def calc_maintenance_cost_per_mile_curve(input_df):
        """

        Args:
            input_df: DataFrame reflecting the maintenance_cost_inputs.csv file with costs updated to analysis_basis_dollars.

        Returns:
            A dictionary of maintenance cost curve coefficients (slope with intercept=0) having keys of 'ICE', 'HEV', 'PHEV', 'BEV'.

        Notes:
            Dividing the cumulative_cost by miles gives a constant cost/mile for every mile. However, costs/mile should
            be lower early and higher later, so this method determines a triangular area that equates to the cumulative
            cost. With the slope of that triangular area, a cost/mile at any odometer value can be calculated and the
            cost of maintenance in any year can then be calculated as that cost/mile multiplied by miles driven in that
            year.

        """
        # create a dictionary in which to place curve coefficients
        veh_types = ['ICE', 'HEV', 'PHEV', 'BEV']
        nested_dict = {'slope': 0, 'intercept': 0}
        maint_cost_curve_dict = dict.fromkeys(veh_types, nested_dict)

        # determine the max odometer included in the input table
        max_series = input_df[[col for col in input_df.columns if 'miles' in col]].max()
        max_value = 0
        for max in max_series:
            if max > max_value:
                max_value = int(max)

        # generate curve coefficients for each of the veh_types in a for loop and store in maint_cost_curve_dict
        for veh_type in veh_types:
            df = pd.DataFrame()
            df.insert(0, 'miles', pd.Series(range(0, max_value + 1, 100)))
            intervals = input_df[f'miles_per_event_{veh_type}'].dropna().unique()
            for interval in intervals:
                cost_at_interval = input_df.loc[input_df[f'miles_per_event_{veh_type}'] == interval, 'dollars_per_event'].sum()
                df.insert(1, f'cost_for_{int(interval)}', 0)

                # determine miles for all events in this interval series (%1=0 divides by 1 and looks for a remainder of 0)
                events = [odo[1] for odo in df['miles'].iteritems() if odo[1] != 0 and odo[1] / interval % 1 == 0]

                for event in events:
                    df.loc[df['miles'] == event, f'cost_for_{int(interval)}'] = cost_at_interval

            cols = df.columns[1:]
            df.insert(0, f'rollup', df[cols].sum(axis=1))
            df.insert(0, f'rollup_cumulative', df['rollup'].cumsum(axis=0))

            cumulative_cost = df['rollup_cumulative'].values.max()
            max_miles = df['miles'].values.max()

            # calc cost/mile at max miles to that gives a triangular area equal to cumulative costs
            cost_per_mile_at_max_miles = cumulative_cost / (0.5 * max_miles)
            cost_per_mile_slope = cost_per_mile_at_max_miles / max_miles

            maint_cost_curve_dict[veh_type] = {'slope': cost_per_mile_slope,
                                               'intercept': 0}

            # plot the curve (uncomment lines to see plots for QA/QC of rollup_cumulative)
            # x, y = df['miles'], df['rollup_cumulative']
            #
            # def objective1(x, a, b):
            #     return a * x + b * x ** 2
            #
            # popt, _ = curve_fit(objective1, x, y)
            # miles_factor, miles_squared_factor = popt

            # pyplot.scatter(x, y)
            # x_line = x
            # y_line = objective(x, a, b)
            # pyplot.title(veh_type)
            # pyplot.plot(x_line, y_line, '--', color='red')
            # pyplot.show()

        return maint_cost_curve_dict

    @staticmethod
    def calc_maintenance_cost_per_mile(input_dict):
        """

        Args:
            input_dict: Dictionary of the maintenance cost inputs.

        Returns:
            The input_dict with the total maintenance cost per mile added; this cost per mile would be a constant for all
            miles.

        Notes:
            This method is not being used currently in favor of the calc_maintenance_cost_per_mile_curve method within
            the class.

        """
        veh_types = ['ICE', 'HEV', 'PHEV', 'BEV']

        # calc cost per mile for each maintenance event
        for key in input_dict.keys():
            cost_per_event = input_dict[key]['dollars_per_event']
            for veh_type in veh_types:
                miles_per_event = input_dict[key][f'miles_per_event_{veh_type}']
                try: # protect against divide by zero
                    input_dict[key].update({f'dollars_per_mile_{veh_type}': cost_per_event / miles_per_event})
                finally:
                    input_dict[key].update({f'dollars_per_mile_{veh_type}': 0})

        # calc total cost per mile for each veh_type, first add a new key and nested dict to hold totals
        input_dict.update({'total_maintenance': {}})
        for veh_type in veh_types:
            input_dict['total_maintenance'].update({f'dollars_per_mile_{veh_type}': 0})

        for veh_type in veh_types:
            total = 0
            for key in input_dict.keys():
                total += input_dict[key][f'dollars_per_mile_{veh_type}']
            input_dict['total_maintenance'].update({f'dollars_per_mile_{veh_type}': total})

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

        init_fail += MaintenanceCost.init_from_file(omega_globals.options.maintenance_cost_inputs_file,
                                                    verbose=omega_globals.options.verbose)

        if not init_fail:
            print(MaintenanceCost.get_maintenance_cost_curve_coefficients('ICE'))
            print(MaintenanceCost.get_maintenance_cost_curve_coefficients('HEV'))
            print(MaintenanceCost.get_maintenance_cost_curve_coefficients('PHEV'))
            print(MaintenanceCost.get_maintenance_cost_curve_coefficients('BEV'))
        else:
            print(init_fail)
            print("\n#INIT FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
