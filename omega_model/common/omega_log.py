"""

**Functions to manage batch and session log files.**

----

**CODE**

"""

print('importing %s' % __file__)

from common import omega_globals  # import global variables
from common.omega_types import OMEGABase


class IterationLog(OMEGABase):
    """
    Handles creation and writing of a dataframe to a .csv file, possibly multiple times via appending.
    Used to log producer-consumer iteration, but could be used to log any dataframe.

    """
    def __init__(self, logfilename):
        """
        Create IterationLog object

        Args:
            logfilename: name of file to create, '.csv' extension added if not provided.

        """
        self.create_file = True
        self.logfilename = logfilename

        if not self.logfilename.endswith('.csv'):
            self.logfilename += '.csv'

    def write(self, dataframe):
        """
        Write dataframe to a .csv file, file is created on first write, subsequent writes append.

        Args:
            dataframe (DataFrame): dataframe to write to file


        """
        if self.create_file:
            dataframe.to_csv(self.logfilename, mode='w', columns=sorted(dataframe.columns))
            self.create_file = False
        else:
            dataframe.to_csv(self.logfilename, mode='a', header=False, columns=sorted(dataframe.columns))


class OMEGABatchLog(OMEGABase):
    """
    Handles logfile creation at the batch level.

    """
    def __init__(self, o2_options, verbose=True):
        """
        Create OMEGABatchLog object

        Args:
            o2_options (OMEGABatchOptions): provides the logfile name
            verbose (bool): if True enables optional output to console as well as logfile

        """
        import datetime, time
        from omega_model import code_version

        self.logfilename = o2_options.logfilename
        self.verbose = verbose
        self.start_time = time.time()

        with open(self.logfilename, 'w') as log:
            log.write('OMEGA %s batch started at %s %s\n\n' %
                      (code_version, datetime.date.today(), time.strftime('%H:%M:%S')))

    def logwrite(self, message, terminator='\n'):
        """
        Write a message to a logfile (and console if verbose)

        Args:
            message (str): message string to write
            terminator (str): end of message terminator, default is newline (``\\n``)

        """
        with open(self.logfilename, 'a') as log:
            if type(message) is list:
                for m in message:
                    log.write(m + terminator)
            else:
                log.write(message + terminator)
            if self.verbose:
                print(message)

    def end_logfile(self, message):
        """
        End logfile with closing message, record elapsed time.

        Args:
            message (str): message string to write

        """
        import time
        elapsed_time = (time.time() - self.start_time)
        import datetime

        for msg in ('\nOMEGA batch ended at %s %s' % (datetime.date.today(), time.strftime('%H:%M:%S')),
                    'OMEGA batch elapsed time %.2f seconds\n' % elapsed_time):
            self.logwrite(msg)
            if self.verbose:
                print(msg)

        self.logwrite(message, terminator='')


def init_logfile(compliance_id=None):
    """
    Create a session logfile.

    Args:
        compliance_id (str): added to log file name if provided

    """
    import time, datetime
    import common.file_io as file_io
    from omega_model import code_version

    file_io.validate_folder(omega_globals.options.output_folder)

    if compliance_id:
        omega_globals.options.logfilename = '%s%s_%s.txt' % (
            omega_globals.options.output_folder + omega_globals.options.logfile_prefix,
            omega_globals.options.session_unique_name, compliance_id)
    else:
        omega_globals.options.logfilename = '%s%s.txt' % (
            omega_globals.options.output_folder + omega_globals.options.logfile_prefix,
            omega_globals.options.session_unique_name)

    with open(omega_globals.options.logfilename, 'w') as log:
        log.write('OMEGA %s session %s started at %s %s\n\n' % (
            code_version, omega_globals.options.session_name, datetime.date.today(), time.strftime('%H:%M:%S')))


def end_logfile(message):
    """
    End logfile with closing message, record elapsed time.

    Args:
        message (str): message string to write

    """
    import time
    omega_globals.options.end_time = time.time()
    elapsed_time = (omega_globals.options.end_time - omega_globals.options.start_time)
    import datetime
    logwrite('\nSession ended at %s %s' % (datetime.date.today(), time.strftime('%H:%M:%S')))
    logwrite('Session elapsed time %.2f seconds\n' % elapsed_time)
    logwrite(message, terminator='')


def logwrite(message, echo_console=True, terminator='\n'):
    """
    Write message to logfile.

    Args:
        message (str or [strs]): message string or list of strings to write
        echo_console (bool): write message to console if True
        terminator (str): end of message terminator, default is newline (``\\n``)

    """
    with open(omega_globals.options.logfilename, 'a') as log:
        if type(message) is list:
            for m in message:
                log.write(m + terminator)
        else:
            log.write(message + terminator)
        if omega_globals.options.verbose or echo_console:
            print(message)
