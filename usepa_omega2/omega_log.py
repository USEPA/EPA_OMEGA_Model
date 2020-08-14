"""
vehicle_annual_data.py
======================

Functions to log diagnostic data

"""

import o2  # import global variables


def init_logfile():
    import time, datetime
    import file_eye_oh as fileio
    from usepa_omega2 import code_version

    fileio.validate_folder(o2.options.output_folder)
    o2.options.logfilename = '%s%s.txt' % (o2.options.output_folder + o2.options.logfile_prefix, time.strftime('%Y%m%d_%H%M%S'))
    log = open(o2.options.logfilename, 'w')
    log.write('OMEGA2 %s run started at %s %s\n\n' % (code_version, datetime.date.today(), time.strftime('%H:%M:%S')))
    log.close()


def logwrite(message):
    log = open(o2.options.logfilename, 'a')
    if type(message) is list:
        for m in message:
            log.write(m + '\n')
    else:
        log.write(message + '\n')
    if o2.options.verbose:
        print(message)
    log.close()
