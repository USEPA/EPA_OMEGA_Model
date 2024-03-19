"""

**Handy file system routines for general use**

Generally, user-friendly wrappers for functionality provided by the ``os`` and ``shutil`` packages.

----

**CODE**

"""

print('importing %s' % __file__)

import sys, os, shutil
from common import omega_log


def get_user_home():
    """
        Get user home directory, works cross-platform

    Returns:
        User home directory as a string

    """
    return os.path.expanduser('~')


def move_folder_contents(srcfolder, dstfolder):
    """
    Move files from the srcfolder to the dstfolder and delete the srcfolder

    Args:
        srcfolder (str): source folder path
        dstfolder (str): destination folder path

    """
    shutil.copytree(srcfolder, dstfolder, dirs_exist_ok=True)
    delete_folder(srcfolder)


def delete_folder(dstfolder):
    """
    Delete the dstfolder

    .. code-block:: python

        delete_folder('C:\\Users\\Temp')

    :param dstfolder: Path the folder to delete

    """
    shutil.rmtree(dstfolder, ignore_errors=True)


def validate_folder(dstfolder):
    """
    Verify the existence of dstfolder and try to create it if doesn't exist

    .. code-block:: python

        validate_folder('C:\\Users\\Temp')

    :param dstfolder: Path the folder to validate/create

    .. attention:: Exits app on failure
    """
    if not os.access(dstfolder, os.F_OK):
        try:
            os.makedirs(dstfolder, exist_ok=True)  # try create folder if necessary
        except:
            print("Couldn't access or create {}".format(dstfolder), file=sys.stderr)
            omega_log.logwrite("Error - Couldn't access or create {}".format(dstfolder))
            exit(-1)


def file_exists(filename):
    """
    Verify the existence of filename

    Args:
        filename: File pathname of the file to validate

    Returns:
        ``True`` if file is accessible (exists)

    """
    return os.access(filename, os.F_OK)


def validate_file(filename):
    """
    Verify the existence of filename

    :param filename: File pathname of the file to validate

    .. attention:: Exits app on failure
    """
    if not os.access(filename, os.F_OK):
        print("\n*** Couldn't access {}, check path and filename ***".format(filename), file=sys.stderr)
        omega_log.logwrite("\n*** Error - Couldn't access {}, check path and filename ***".format(filename))
        exit(-1)


def get_filepath(filename):
    """
    Returns path to file, e.g. /somepath/somefile.txt -> /somepath

    :param filename: file name, including path to file as required
    :return: file path, not including the file name
    """
    return os.path.split(filename)[0]


def get_filepathname(filename):
    """
    Returns file name without extension, including path, e.g. /somepath/somefile.txt -> /somepath/somefile

    :param filename: file name, including path to file as required
    :return: file name without extension, including path
    """
    return os.path.splitext(filename)[0]


def get_absolute_path(filename):
    """
    Get the full, absolute path of filename

    Args:
        filename (str): name of file available on the current path

    Returns:
        The full, absolute path of filename

    """
    return os.path.abspath(filename)


def get_basename(pathname):
    """
    Return the base name of pathname path. This is the second element of the pair returned by passing path to the
    function split(). Note that the result of this function is different from the Unix basename program; where basename
    for '/foo/bar/' returns 'bar', the basename() function returns an empty string ('').

    Args:
        pathname(str): the path to get the basename of

    Returns:
        The base name of pathname path.

    """
    return os.path.basename(pathname)


def get_filename(filename):
    """
    Returns file name without extension, e.g. /somepath/somefile.txt -> somefile

    :param filename: file name, including path to file as required
    :return: file name without extension
    """
    return os.path.split(get_filepathname(filename))[1]


def get_filenameext(filename):
    """
    Returns file name including extension, e.g. /somepath/somefile.txt -> somefile.txt

    :param filename: file name, including extension, including path to file as required
    :return: file name including extension
    """
    return os.path.split(filename)[1]


def get_parent_foldername(filepathnameext):
    """
    Returns the parent folder of the given file e.g. /apath/somepath/somefile.txt -> somepath

    :param filepathnameext: file name, including extension and path to file
    :return: parent folder of the given file
    """
    return get_filename(get_filepath(filepathnameext))


def network_copyfile(remote_path, srcfile):
    """
    Copy srcfile to remote_path

    :param remote_path: Path to file destination
    :param srcfile: source file name, including extension and path to file
    """
    dstfile = remote_path + os.sep + get_filenameext(srcfile)
    shutil.copyfile(srcfile, dstfile)


def relocate_file(remote_path, local_filename):
    """
    Move local_filename out to remote_path and return the filename in that remote context

    :param remote_path: Path to file destination
    :param local_filename: local source file name, including extension and path to file as required
    """
    network_copyfile(remote_path, local_filename)
    return get_filenameext(local_filename)


def sysprint(msg):
    """
    Performs ECHO command of str in CMD window

    :param msg: string to echo
    """
    os.system('echo {}'.format(msg))
