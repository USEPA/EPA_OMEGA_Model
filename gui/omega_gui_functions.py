from PyQt5.QtWidgets import QFileDialog


def new_file_action(var1, var2):
    """
    Doc Stub
    """
    print(var1, var2)


# def open_file_action():
    # print("Open File")


def save_file_action(file_name):
    """
    Doc Stub
    """

    dialog = QFileDialog()
    dialog.selectFile("der.jpg")
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_name)
    dialog.setViewMode(QFileDialog.Detail)
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name


# def save_file_as_action(file_name, file_type):
    # print("Save File As")


def file_dialog(file_name, file_type, file_dialog_title):
    """
    Opens a file dialog to select a file with extension options.

    :param file_name: Default file name
    :param file_type: Specifies extension filter type
    :param file_dialog_title: Title for dialog box
    ...
    :return file_name: User selected file name
    :return file_type: Echo input param
    :return file_dialog_title: Echo input param
    """
    dialog = QFileDialog()
    dialog.selectFile(file_name)
    dialog.setWindowTitle(file_dialog_title)
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type, file_dialog_title



