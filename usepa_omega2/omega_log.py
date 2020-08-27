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
    o2.options.logfilename = '%s%s.txt' % (
        o2.options.output_folder + o2.options.logfile_prefix, o2.options.session_name)
    log = open(o2.options.logfilename, 'w')
    log.write('OMEGA2 %s session %s started at %s %s\n\n' % (
        code_version, o2.options.session_name, datetime.date.today(), time.strftime('%H:%M:%S')))
    log.close()


def end_logfile(message):
    import time
    o2.options.end_time = time.time()
    elapsed_time = (o2.options.end_time - o2.options.start_time)
    import datetime
    logwrite('Session ended at %s %s\n\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))
    logwrite('\nElapsed Time %.2f Seconds' % elapsed_time)
    logwrite(message, terminator='')


def logwrite(message, terminator='\n'):
    log = open(o2.options.logfilename, 'a')
    if type(message) is list:
        for m in message:
            log.write(m + terminator)
    else:
        log.write(message + terminator)
    if o2.options.verbose:
        print(message)
    log.close()