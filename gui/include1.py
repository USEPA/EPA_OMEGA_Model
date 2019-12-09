from PyQt5.QtWidgets import QFileDialog


def new_file_action(var1, var2):
    """
    Doc Stub
    """
    print(var1, var2)


def open_file_action():
    print("Open File")


def save_file_action():
    print("Save File")


def save_file_as_action():
    print("Save File As")


def file_dialog():
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.AnyFile)
    dialog.setNameFilter("Image files (*.jpg *.gif);; All Files (*.*)")
    dialog.setViewMode(QFileDialog.Detail)
    if dialog.exec_():
        filenames = dialog.selectedFiles()
        filenames = str(filenames)[2:-2]
        print(filenames)
        return filenames

