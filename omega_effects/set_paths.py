"""

**OMEGA file path handling.**

----

**CODE**

"""
from pathlib import Path
import shutil


class SetPaths:
    """

    The SetPaths class sets the paths and run_id info used by the omega effects package.

    """
    def __init__(self):
        self.path_code = Path(__file__).parent
        self.path_module = self.path_code
        self.path_project = self.path_module.parent

        # output paths
        self.path_of_run_folder = None
        self.path_of_run_inputs_folder = None
        self.path_of_run_results_folder = None
        self.path_of_modified_inputs_folder = None
        self.path_of_code_folder = None

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

    def copy_code_to_destination(self):
        """

        Returns:
            Nothing, but copies contents of code folder to the destination.

        Note:
           This is just a generator that allows for copy/paste of omega effects package code into a bundle of folders
           and files saved to the outputs folder.

        """
        # first copy files in the path_code folder
        files_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_file())
        for file in files_in_path_code:
            shutil.copy2(file, self.path_of_code_folder / file.name)

        # now make subfolders in destination and copy files from path_code subfolders
        dirs_in_path_code = (entry for entry in self.path_code.iterdir() if entry.is_dir())
        for d in dirs_in_path_code:
            source_dir_name = Path(d).name
            destination_subdir = self.path_of_code_folder / source_dir_name
            destination_subdir.mkdir(exist_ok=False)
            files_in_source_dir = (entry for entry in d.iterdir() if entry.is_file())
            for file in files_in_source_dir:
                shutil.copy2(file, destination_subdir / file.name)

        shutil.copy2(self.path_project / 'requirements.txt', self.path_of_run_folder / 'requirements.txt')
        self.path_code = self.path_of_code_folder

    def create_output_paths(self, path_name, batch_name, start_time_readable, run_id):
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
        self.path_of_run_folder = path_of_output_batch_folder / f'{start_time_readable}_{run_id}'
        self.path_of_run_folder.mkdir(exist_ok=False)
        self.path_of_code_folder = self.path_of_run_folder / 'code'
        self.path_of_code_folder.mkdir(exist_ok=False)
        self.path_of_modified_inputs_folder = self.path_of_run_folder / 'modified_inputs'
        self.path_of_modified_inputs_folder.mkdir(exist_ok=False)
