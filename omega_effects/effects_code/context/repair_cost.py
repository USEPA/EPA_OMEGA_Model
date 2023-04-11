"""

**Routines to load Repair Cost Inputs.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in repair cost calculations.

File Type
    comma-separated values (CSV)

Sample Header
    .. csv-table::

       input_template_name:,repair_cost,input_template_version:,0.1

Sample Data Columns
    .. csv-table::
        :widths: auto

        item,value
        car_multiplier,1
        suv_multiplier,0.91
        truck_multiplier,0.7
        ICE_multiplier,1
        HEV_multiplier,0.91

Data Column Name and Description

:item:
    The repair cost curve attribute name.

:value:
    The attribute value.

**CODE**

"""
# reactivate these imports for QA/QC of this module
# from matplotlib import pyplot
from math import e

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import \
    validate_template_version_info, validate_template_column_names


class RepairCost:
    """
    **Loads and provides access to repair cost input values for repair cost calculations.**

    """
    def __init__(self):
        self._data = dict()

    def init_from_file(self, filepath, effects_log):
        """

        Initialize class data from input file.

        Args:
            filepath: the Path object to the file.
            effects_log: an instance of the EffectsLog class.

        Returns:
            Nothing, but reads the appropriate input file.

        """
        # don't forget to update the module docstring with changes here
        input_template_name = 'repair_cost'
        input_template_version = 0.1
        input_template_columns = {
            'item',
            'value',
        }

        df = read_input_file(filepath, effects_log)
        validate_template_version_info(df, input_template_name, input_template_version, effects_log)

        # read in the data portion of the input file
        df = read_input_file(filepath, effects_log, skiprows=1)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        self._data = df.set_index('item').to_dict(orient='index')

    def calc_repair_cost_per_mile(self, veh_cost, pt_type, repair_type, age):
        """

        Args:
            veh_cost: (Numeric) The value of the vehicle when sold as new
            pt_type: (str) The powertrain type (ICE, HEV, PHEV, BEV)
            repair_type: (str) The vehicle repair type (car, suv, truck)
            age: (int) The age of the vehicle where age=0 is year 1 in operation.

        Returns:
            A single repair cost per mile for the given vehicle at the given age.

        """
        veh_type_multiplier = self._data[f'{repair_type}_multiplier']['value']
        pt_multiplier = self._data[f'{pt_type}_multiplier']['value']
        if age <= 4:
            a_value = self._data[f'a_value_{age}']['value']
        else:
            a_value = self._data['a_value_4']['value'] \
                      + self._data['a_value_add']['value'] * (age - 4)
        b = self._data['b']['value']

        repair_cost_per_mile = veh_type_multiplier * pt_multiplier * a_value * e ** (veh_cost * b)

        return repair_cost_per_mile
