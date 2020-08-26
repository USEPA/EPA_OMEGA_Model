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
    import os, sys
    import traceback

    sys.path.extend(['\\usepa_omega2', '\\usepa_omega2\\consumer'])
    validate_folder(test_omega2_output_folder)
    os.system('del %s\\*.* /Q' % test_omega2_output_folder)

    try:
        init_logfile()

        passed = []
        failed = []
        unknown = []

        for source_folder in ['usepa_omega2', 'usepa_omega2\\consumer']:
            source_files = [fn for fn in os.listdir(source_folder) if '.py' in fn]
            for f in source_files:
                console_file = test_omega2_output_folder + os.sep + f.replace('.py', '') + '.txt'

                if f == 'run_omega_batch.py':
                    cmd_str = 'python %s\\%s --batch_file inputs\phase0_default_batch_file.xlsx --verbose > %s' % \
                              (source_folder, f, console_file)
                else:
                    cmd_str = 'python %s\\%s > %s' % (source_folder, f, console_file)

                logwrite('TRYING %s' % cmd_str)
                r = os.system(cmd_str)
                if r == 0:
                    passed.append(cmd_str)
                    logwrite('%s PASSED' % cmd_str)
                    os.system('RENAME %s PASSED_%s' % (console_file, f.replace('.py', '') + '.txt'))
                elif r == -1:
                    failed.append(cmd_str)
                    logwrite('%s FAILED' % cmd_str)
                    os.system('RENAME %s FAILED_%s' % (console_file, f.replace('.py', '') + '.txt'))
                else:
                    unknown.append(cmd_str)
                    logwrite('%s UNKNOWN' % cmd_str)
                    os.system('RENAME %s UNKNOWN_%s' % (console_file, f.replace('.py', '') + '.txt'))
                logwrite('')

    except Exception as e:
        logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())

        logwrite('### test_omega2.py runtime fail ###')

    finally:
        logwrite('TEST SUMMARY')
        logwrite('-'*20 + '%d PASSED ' % len(passed) + '-'*21)
        for c in passed:
            logwrite('%s PASSED' % c)

        logwrite('-'*20 + '%d UNKNOWN ' % len(unknown) + '-'*20)
        for c in unknown:
            logwrite('%s UNKNOWN' % c)

        logwrite('-'*20 + '%d FAILED ' % len(failed) + '-'*21)
        for c in failed:
            logwrite('%s FAILED' % c)
