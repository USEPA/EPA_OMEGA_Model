"""
vehicle_annual_data.py
======================

Functions to log diagnostic data

"""

import usepa_omega2
import file_eye_oh as fileio


def init_logfile(o2_options):
    import os
    import time, datetime

    fileio.validate_folder(o2_options.output_folder)
    o2_options.logfilename = '%s%s.txt' % (o2_options.logfile_prefix, time.strftime('%Y%m%d_%H%M%S'))
    log = open(o2_options.logfilename, 'w')
    log.write('OMEGA2 %s run started at %s %s\n\n' % (usepa_omega2.code_version, datetime.date.today(), time.strftime('%H:%M:%S')))
    log.close()


def logwrite(message):
    from usepa_omega2 import o2_options

    log = open(o2_options.logfilename, 'a')
    log.write(message + '\n')
    if o2_options.verbose:
        print(message)
    log.close()
