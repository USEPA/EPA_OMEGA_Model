"""

**OMEGA file path handling.**

----

**CODE**

"""

from pathlib import Path
import shutil
import tkinter as tk
from tkinter import filedialog


class SetPaths:
    """

    The SetPaths class sets the paths and run_id info used by the tool.

    """
    def __init__(self):
        self.path_code = Path(__file__).parent
        self.path_module = self.path_code
        self.path_project = self.path_module.parent

    def files_in_code_folder(self):
        """

        Returns:
            A generator object.

        Note:
            This is just a generator that allows for copy/paste of tool code into a bundle of folders and files saved
            to the outputs folder.

        """
        files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())

        return files_in_path_code

    def copy_code_to_destination(self, destination):
        """

        Parameters:
            destination (path): the destination folder path; destination folder must exist prior to method call.

        Returns:
            Nothing, but copies contents of code folder to the destination.

        Note:
           This is just a generator that allows for copy/paste of tool code into a bundle of folders and files saved to
           the outputs folder.

        """
        # first copy files in the path_code folder
        if self.path_code.exists():
            files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())
            for file in files_in_path_code:
                shutil.copy2(file, destination / file.name)

            # now make subfolders in destination and copy files from path_code subfolders
            dirs_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_dir())
            for d in dirs_in_path_code:
                source_dir_name = Path(d).name
                destination_subdir = destination / source_dir_name
                destination_subdir.mkdir(exist_ok=False)
                files_in_source_dir = (entry for entry in d.iterdir() if entry.is_file())
                for file in files_in_source_dir:
                    shutil.copy2(file, destination_subdir / file.name)

    @staticmethod
    def run_id():
        """

        Returns:
            A console prompt to enter a run identifier; entering "test" sends outputs to a test folder; if left blank a
            default name is used.

        Note:
            This method allows for a user-interactive identifier (name) for the given run.

        """
        # set run id and files to generate
        run_folder_identifier = input('\nProvide a run identifier for your output folder name (press return to use the default name)\n')
        run_folder_identifier = run_folder_identifier if run_folder_identifier != '' else 'omega_effects'
        return run_folder_identifier

    @staticmethod
    def create_output_paths(path_name, batch_name, start_time_readable, run_id):
        """

        Parameters:
            path_name: save path set via batch settings file.
            batch_name (str): the batch name set via the runtime options input file.
            start_time_readable (str): the start time of the run, in text readable format.\n
            run_id (str): the run ID entered by the user or the default value if the user does not provide an ID.

        Returns:
            Output paths into which to save outputs of the given run.

        """
        path_name.mkdir(exist_ok=True)
        path_of_output_batch_folder = path_name / batch_name
        path_of_output_batch_folder.mkdir(exist_ok=True)
        path_of_run_folder = path_of_output_batch_folder / f'{start_time_readable}_{run_id}'
        path_of_run_folder.mkdir(exist_ok=False)
        path_of_code_folder = path_of_run_folder / 'code'
        path_of_code_folder.mkdir(exist_ok=False)

        return path_of_run_folder, path_of_code_folder

    @staticmethod
    def path_to_runtime_options_csv():
        """

        Returns:
            A console prompt to enter a run identifier; entering "test" sends outputs to a test folder; if left blank a
            default name is used.

        Note:
            This method allows for a user-interactive identifier (name) for the given run.

        """
        # set full path to the batch settings file
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()

        path_identifier = filedialog.askopenfilename(title='Select the runtime options CSV file')

        path_of_csv = Path(path_identifier)
        path_to_csv = path_of_csv.parent

        return path_of_csv, path_to_csv

    @staticmethod
    def path_of_batch_settings_csv():
        """

        Returns:
            An open-file dialog to select the batch settings file to use.

        Note:
            This method allows for a user-interactive means of selecting the desired batch settings file.

        """
        # set full path to the batch settings file
        root = tk.Tk()
        root.attributes("-topmost", True)
        root.withdraw()

        path_identifier = filedialog.askopenfilename(title='Select the batch settings CSV file')

        path_of_csv = Path(path_identifier)

        return path_of_csv
