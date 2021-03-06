from distutils.dir_util import copy_tree

from PySide2.QtWidgets import QFileDialog
import yaml


def open_file_action(filepath):
    data = yaml_loader(filepath)
    return data


def yaml_loader(filepath):
    """
    Loads a yaml formatted file and converts to a Python formatted dictionary.

    :param filepath: Full path to yaml formatted source file

    :return: Python formatted dictionary
    """
    with open(filepath, "r") as file_descriptor:
        data = yaml.full_load(file_descriptor)
    return data


def yaml_dump(filepath, data):
    """
    Dumps data to a yaml file.

    :param filepath: Full path to destination file
    :param data: Dictionary to save

    :return: N/A
    """
    with open(filepath, "w") as file_descriptor:
        yaml.dump(data, file_descriptor)

        # yaml.dump(data)

    # print("Open File")


def save_file_action(filepath, data):
    yaml_dump(filepath, data)
    """
    Dumps data to a yaml file.

    :param filepath: Full path to destination file
    :param data: Dictionary to save
    
    :return: N/A
    """


def file_dialog_save(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a file with extension options.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box

    :return: User selected file name, Echo file_type, Echo file_dialog_title
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setAcceptMode(QFileDialog.AcceptSave)
    # dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    # temp = dialog.selectedFiles()
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title
    else:
        file_name = ""
        return file_name, file_type, file_dialog_title


def file_dialog(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a file with extension options.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box

    :return: User selected file name, echo file_type, echo file_dialog_title
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setFileMode(QFileDialog.ExistingFile)
    # dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    # temp = dialog.selectedFiles()
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title
    else:
        file_name = ""
        return file_name, file_type, file_dialog_title


def directory_dialog(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a directory.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box

    :return: User selected directory name, echo file_type, echo file_dialog_title
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setFileMode(QFileDialog.DirectoryOnly)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    # temp = dialog.selectedFiles()
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title
    else:
        file_name = ""
        return file_name, file_type, file_dialog_title


def copy_files(source, destination):
    copy_tree(source, destination)
