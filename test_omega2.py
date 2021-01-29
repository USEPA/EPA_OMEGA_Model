test_omega2_output_folder = 'test_omega2_output'
test_omega2_results_file = '__test_omega2_results.txt'


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
            os.makedirs(dstfolder, exist_ok=True) # try create folder if necessary
        except:
            print("Couldn't access or create {}".format(dstfolder),file=sys.stderr)
            exit(-1)


def init_logfile():
    import os
    import time, datetime

    log = open(test_omega2_output_folder + os.sep + test_omega2_results_file, 'w')
    log.write('OMEGA2 test started at %s %s\n\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))
    log.close()


def logwrite(message):
    import os

    log = open(test_omega2_output_folder + os.sep + test_omega2_results_file, 'a')
    if type(message) is list:
        for m in message:
            log.write(m + '\n')
    else:
        log.write(message + '\n')

    print(message)
    log.close()


if __name__ == "__main__":
    import os, sys, subprocess
    import traceback

    validate_folder(test_omega2_output_folder)
    os.system('del %s\\*.* /Q' % test_omega2_output_folder)

    try:
        init_logfile()

        pythonpathstr = 'set PYTHONPATH=.;.\\usepa_omega2'
        pythoncommand = 'python -u'

        results = {'PASSED': [], 'FAILED': [], 'UNKNOWN': []}

        for source_folder in ['usepa_omega2', 'usepa_omega2\\consumer']:
            source_files = [fn for fn in os.listdir(source_folder) if '.py' in fn]
            for f in source_files:

                console_file_pathname = test_omega2_output_folder + os.sep + f.replace('.py', '') + '.txt'
                cmd_str = '%s & %s %s' % (pythonpathstr, pythoncommand, os.path.join(source_folder, f))
                cmd_opts = ''

                if f == 'run_omega_batch.py':
                    cmd_opts = '--batch_file usepa_omega2\\test_inputs\\single_session_batch.xlsx --verbose'

                cmd_str = cmd_str + ' %s > %s' % (cmd_opts, console_file_pathname)

                logwrite('TRYING %s' % cmd_str)
                r = os.system(cmd_str)

                if r == 0:
                    result_status = 'PASSED'
                elif r == -1:
                    result_status = 'FAILED'
                else:
                    result_status = 'UNKNOWN'

                results[result_status].append(cmd_str)
                logwrite('%s %s' % (cmd_str, result_status))
                os.system('RENAME %s %s_%s' % (console_file_pathname, result_status, f.replace('.py', '') + '.txt'))

                logwrite('')

    except Exception as e:
        logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())

    finally:
        logwrite('TEST SUMMARY')
        for k, v in results.items():
            logwrite('-'*20 + ' %d %s ' % (len(v), k) + '-'*20)
            for c in v:
                logwrite('%s %s' % (c, k))
