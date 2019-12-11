from PyQt5.QtWidgets import QFileDialog


def new_file_action(var1, var2):
    """
    Doc Stub
    """
    print(var1, var2)


def open_file_action():
    print("Open File")


def save_file_action(file_name, file_type):
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter(file_type)
    dialog.setViewMode(QFileDialog.Detail)
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name, file_type


def save_file_as_action():
    print("Save File As")


def file_dialog(file_name):
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter("Image files (*.jpg *.gif);; All Files (*.*)")
    dialog.setViewMode(QFileDialog.Detail)
    if dialog.exec_():
        file_name = dialog.selectedFiles()
        file_name = str(file_name)[2:-2]
        return file_name

