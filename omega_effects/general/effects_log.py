"""

**OMEGA effects logging module.**

----

**CODE**

"""
import logging
from datetime import datetime


class EffectsLog:
    """
    Effects log class definition.

    """
    def __init__(self):
        self.logfile_name = None
        self.file_name = 'effects_messages.log'

    def init_logfile(self, path):
        """

        Args:
            path: the project Path object.

        """
        self.logfile_name = path / self.file_name
        logging.basicConfig(
            level=logging.DEBUG,
            filename=self.logfile_name,
            filemode='w',
        )

    def logwrite(self, message, echo_console=True, terminator='\n', stamp=False):
        """

        Args:
            message (str): message string to write.
            echo_console (bool): write message to console if True
            terminator (str): end of message terminator, default is newline
            stamp (bool): include date and time stamp True or False

        Returns:
            Nothing. Writes message to logfile and to console by default.

        """
        if stamp:
            t = datetime.now().strftime("%Y-%b-%d %H:%M:%S")
            message = f'\n{t}: {str(message)}'
        with open(self.logfile_name, 'a') as log:
            if type(message) is list:
                for m in message:
                    log.write(str(m) + terminator)
            else:
                log.write(str(message) + terminator)
            if echo_console:
                print(message)
