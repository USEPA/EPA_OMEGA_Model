"""

**Routines to load Repair Cost Inputs.**

----

**INPUT FILE FORMAT**

The file format consists of a one-row template header followed by a one-row data header and subsequent data
rows.

The data represent various inputs for use in repair cost calculations.

File Type
    comma-separated values (CSV)

Template Header
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

print('importing %s' % __file__)

# reactivate these imports for QA/QC of this module
# from matplotlib import pyplot
from math import e

from omega_model import *


class RepairCost(OMEGABase):
    """
    **Loads and provides access to repair cost input values for repair cost calculations.**

    """
    _data = dict()  # private dict of general input attributes and values

    @staticmethod
    def calc_repair_cost_per_mile(veh_cost, pt_type, repair_type, age):
        """

        Args:
            veh_cost: (Numeric) The value of the vehicle when sold as new
            pt_type: (String) The powertrain type (ICE, HEV, PHEV, BEV)
            repair_type: (String) The vehicle repair type (car, suv, truck)
            age: (Integer) The age of the vehicle where age=0 is year 1 in operation.

        Returns:
            A single repair cost per mile for the given vehicle at the given age.

        """
        veh_type_multiplier = RepairCost._data[f'{repair_type}_multiplier']['value']
        pt_multiplier = RepairCost._data[f'{pt_type}_multiplier']['value']
        if age <= 4:
            a_value = RepairCost._data[f'a_value_{age}']['value']
        else:
            a_value = RepairCost._data['a_value_4']['value'] \
                      + RepairCost._data['a_value_add']['value'] * (age - 4)
        b = RepairCost._data['b']['value']

        repair_cost_per_mile = veh_type_multiplier * pt_multiplier * a_value * e ** (veh_cost * b)

        return repair_cost_per_mile

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
        RepairCost._data.clear()

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'repair_cost'
        input_template_version = 0.1
        input_template_columns = {'item',
                                  'value',
                                  }

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_column_names(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                RepairCost._data = df.set_index('item').to_dict(orient='index')

        return template_errors
