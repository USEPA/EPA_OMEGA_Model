"""

**INPUT FILE FORMAT**

The data represent options for what to include in the given run of the tool. The data also provide the path to the input
files and the name of the input_files file to use for the given run. The input_files file should reside in the same
path as the other input files. A project_name can also be set which will be included in the filenames of any output
files.

File Type
    comma-separated values (CSV)

Sample Data Columns
    .. csv-table::
        :widths: auto

        Parameter,Entry,Notes
        Batch Settings File,full path to file,"enter full path including drive id and filename extension"
        Save Path,full path to save folder,"enter full path including drive id but do not include unique run identifiers"
        Large Effects File Save Format,parquet,"enter 'csv' for large Excel-readable files; 'parquet' for compressed files usable in Pandas"

Data Column Name and Description
    :Parameter:
        The name of the runtime option; these should not be changed.

    :Entry:
        The Batch Settings File should be a CSV file; the Save Path should be a directory name or folder name; the
        Large Effects File Save Format can be "csv" or "parquet" where parquet files are usable in Pandas but not
        directly usable in Excel or a text reader.

    :Notes:
        Optional; ignored in-code.

----

**CODE**

"""
from pathlib import Path
import sys

from omega_effects.effects_code.general.general_functions import read_input_file
from omega_effects.effects_code.general.input_validation import validate_template_column_names


class RuntimeOptions:
    """

    The RuntimeOptions class reads the runtime_options file and provides methods to query its contents.

    """
    def __init__(self):
        self._dict = dict()
        self.batch_settings_file = None
        self.batch_settings_file_name = None
        self.file_format = None
        self.path_outputs = None
        self.save_context_fuel_cost_per_mile_file = None
        self.save_vehicle_safety_effects_files = None
        self.save_vehicle_physical_effects_files = None
        self.save_vehicle_cost_effects_files = None
        self.save_input_files = False

        self.true_false_dict = dict({
            True: True,
            False: False,
            'True': True,
            'False': False,
            'TRUE': True,
            'FALSE': False,
            'None': None,
            'Yes': True,
            'yes': True,
            'YES': True,
            'Y': True,
            'y': True,
            'No': False,
            'no': False,
            'NO': False,
            'N': False,
            'n': False,
        })

    def init_from_file(self, filepath, effects_log):
        """

        Parameters:
            filepath: Path to the specified file.
            effects_log: object; an object of the ToolLog class.

        Returns:
            Reads file at filepath; converts monetized values to analysis dollars (if applicable); creates a dictionary
            and other attributes specified in the class __init__.

        """
        # don't forget to update the module docstring with changes here
        input_template_columns = [
            'Parameters',
            'Entry',
        ]
        df = read_input_file(filepath, effects_log)
        validate_template_column_names(filepath, df, input_template_columns, effects_log)

        df.set_index('Parameters', inplace=True)

        self._dict = df.to_dict('index')

        input_file_path_string = self._dict['Batch Settings File']['Entry']

        self.batch_settings_file = Path(input_file_path_string)

        save_path_string = self._dict['Save Path']['Entry']

        self.path_outputs = Path(save_path_string)

        string_id = 'Save Context Fuel Cost per Mile File'
        self.save_context_fuel_cost_per_mile_file = self._dict[string_id]['Entry']
        if self.save_context_fuel_cost_per_mile_file in self.true_false_dict:
            self.save_context_fuel_cost_per_mile_file = self.true_false_dict[self.save_context_fuel_cost_per_mile_file]
            effects_log.logwrite(
                f'{string_id} is {self.save_context_fuel_cost_per_mile_file}\n')

        string_id = 'Save Vehicle-Level Safety Effects Files'
        self.save_vehicle_safety_effects_files = self._dict[string_id]['Entry']
        if self.save_vehicle_safety_effects_files in self.true_false_dict:
            self.save_vehicle_safety_effects_files = self.true_false_dict[self.save_vehicle_safety_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_safety_effects_files}\n')

        string_id = 'Save Vehicle-Level Physical Effects Files'
        self.save_vehicle_physical_effects_files = self._dict[string_id]['Entry']
        if self.save_vehicle_physical_effects_files in self.true_false_dict:
            self.save_vehicle_physical_effects_files = self.true_false_dict[self.save_vehicle_physical_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_physical_effects_files}\n')

        string_id = 'Save Vehicle-Level Cost Effects Files'
        self.save_vehicle_cost_effects_files = self._dict[string_id]['Entry']
        if self.save_vehicle_cost_effects_files in self.true_false_dict:
            self.save_vehicle_cost_effects_files = self.true_false_dict[self.save_vehicle_cost_effects_files]
            effects_log.logwrite(
                f'{string_id} is {self.save_vehicle_cost_effects_files}\n')

        try:
            self.batch_settings_file_name = self.batch_settings_file.name
        except Exception as e:
            effects_log.logwrite('\nBatch Settings File must be provided in runtime_settings.csv')
            effects_log.logwrite(e)
            sys.exit()

        try:
            # protect against NaN or empty string
            string_id = 'Format for Vehicle-Level Output Files'
            self.file_format = self._dict[string_id]['Entry'].lower()
            if self.save_vehicle_safety_effects_files \
                    or self.save_vehicle_physical_effects_files \
                    or self.save_vehicle_cost_effects_files:
                effects_log.logwrite(f'{string_id} is {self.file_format}\n')
        except Exception as e:
            effects_log.logwrite(
                '\nVehicle-Level Output File Save Format in runtime_settings.csv must be "csv" or "parquet"')
            effects_log.logwrite(e)
            sys.exit()

        if self.file_format not in ['csv', 'parquet']:
            # protect against improper save format
            effects_log.logwrite(
                '\nVehicle-Level Output File Save Format in runtime_settings.csv must be "csv" or "parquet"')
            sys.exit()

        string_id = 'Save Input Files'
        self.save_input_files = self._dict[string_id]['Entry']
        if self.save_input_files in self.true_false_dict:
            self.save_input_files = self.true_false_dict[self.save_input_files]
            effects_log.logwrite(f'{string_id} is {self.save_input_files}\n')
