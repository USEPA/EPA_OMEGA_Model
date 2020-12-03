"""
vehicle_annual_data.py
======================
Functions to log diagnostic data
"""

print('importing %s' % __file__)

import o2  # import global variables
from o2 import OMEGABase

class IterationLog():
    def __init__(self, logfilename):
        self.init = True
        self.logfilename = logfilename

        if not self.logfilename.endswith('.csv'):
            self.logfilename += '.csv'

    def write(self, dataframe):
        import os
        if self.init:
            dataframe.to_csv(self.logfilename, mode='w')
            self.init = False
        else:
            dataframe.to_csv(self.logfilename, mode='a', header=False)


class OMEGALog(OMEGABase):
    def __init__(self, o2_options, verbose=True):
        import datetime, time

        self.logfilename = o2_options.logfilename
        self.verbose = verbose
        self.start_time = time.time()

        with open(self.logfilename, 'w') as log:
            log.write('OMEGA log started at %s %s\n\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))

    def logwrite(self, message, terminator='\n'):
        with open(self.logfilename, 'a') as log:
            if type(message) is list:
                for m in message:
                    log.write(m + terminator)
            else:
                log.write(message + terminator)
            if self.verbose:
                print(message)

    def end_logfile(self, message, echo_console=True):
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
    import time, datetime
    import file_eye_oh as fileio
    from usepa_omega2 import code_version

    fileio.validate_folder(o2.options.output_folder)
    o2.options.logfilename = '%s%s.txt' % (
        o2.options.output_folder + o2.options.logfile_prefix, o2.options.session_unique_name)
    with open(o2.options.logfilename, 'w') as log:
        log.write('OMEGA2 %s session %s started at %s %s\n\n' % (
            code_version, o2.options.session_name, datetime.date.today(), time.strftime('%H:%M:%S')))


def end_logfile(message):
    import time
    o2.options.end_time = time.time()
    elapsed_time = (o2.options.end_time - o2.options.start_time)
    import datetime
    logwrite('\nSession ended at %s %s\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))
    logwrite('Elapsed Time %.2f Seconds\n' % elapsed_time)
    print('Elapsed Time %.2f Seconds\n' % elapsed_time)
    logwrite(message, terminator='')


def logwrite(message, echo_console=False, terminator='\n'):
    with open(o2.options.logfilename, 'a') as log:
        if type(message) is list:
            for m in message:
                log.write(m + terminator)
        else:
            log.write(message + terminator)
        if o2.options.verbose or echo_console:
            print(message)
