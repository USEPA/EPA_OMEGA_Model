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
            dataframe.to_csv(self.logfilename, mode='w')
            self.create_file = False
        else:
            dataframe.to_csv(self.logfilename, mode='a', header=False)


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

        self.logfilename = o2_options.logfilename
        self.verbose = verbose
        self.start_time = time.time()

        with open(self.logfilename, 'w') as log:
            log.write('OMEGA batch log started at %s %s\n\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))

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

        for msg in ('\nOMEGA log ended at %s %s\n' % (datetime.date.today(), time.strftime('%H:%M:%S')),
                    'Elapsed Time %.2f Seconds\n' % elapsed_time):
            self.logwrite(msg)
            if self.verbose:
                print(msg)

        self.logwrite(message, terminator='')


def init_logfile():
    """
    Create a session logfile.

    """
    import time, datetime
    import common.file_io as file_io
    from omega_model import code_version

    file_io.validate_folder(omega_globals.options.output_folder)
    omega_globals.options.logfilename = '%s%s.txt' % (
        omega_globals.options.output_folder + omega_globals.options.logfile_prefix, omega_globals.options.session_unique_name)
    with open(omega_globals.options.logfilename, 'w') as log:
        log.write('OMEGA2 %s session %s started at %s %s\n\n' % (
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
    logwrite('\nSession ended at %s %s\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))
    logwrite('Elapsed Time %.2f Seconds\n' % elapsed_time)
    print('Elapsed Time %.2f Seconds\n' % elapsed_time)
    logwrite(message, terminator='')


def logwrite(message, echo_console=False, terminator='\n'):
    """
    Write message to logfile.

    Args:
        message (str): message string to write
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
