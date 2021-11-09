test_omega2_output_folder = 'out'
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
    """
    Initialize test_omega2 log file

    """
    import os
    import time, datetime

    log = open(test_omega2_output_folder + os.sep + test_omega2_results_file, 'w')
    log.write('OMEGA2 test started at %s %s\n\n' % (datetime.date.today(), time.strftime('%H:%M:%S')))
    log.close()


def logwrite(message):
    """
    Write ``message`` to the test_omega2 log file

    Args:
        message (str): the message to write

    """
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
    if 'darwin' in sys.platform:
        os.system('rm %s/*.*' % test_omega2_output_folder)
    else:
        os.system('del %s\\*.* /Q' % test_omega2_output_folder)

    try:
        init_logfile()

        path = os.path.dirname(os.path.abspath(__file__)) + os.sep + '..'

        if 'darwin' in sys.platform:
            pythonpathstr = 'export PYTHONPATH=%s:%s/omega_model' % (path, path)
        else:
            pythonpathstr = 'set PYTHONPATH=.;..;..\\omega_model'
        pythoncommand = 'python -u'

        results = dict() # {'PASSED': [], 'FAILED': [], 'UNKNOWN': []}

        package_folder = '%s/omega_model' % path
        subpackage_list = [package_folder + os.sep + d for d in os.listdir(package_folder)
                           if os.path.isdir(package_folder + os.sep + d)
                           and '__init__.py' in os.listdir('%s%s%s' % (package_folder, os.sep, d))]

        subpackage_list.append(package_folder)

        for source_folder in subpackage_list:
            source_files = [fn for fn in os.listdir(source_folder) if '.py' in fn]
            for f in source_files:

                console_file_pathname = test_omega2_output_folder + os.sep + os.path.split(source_folder)[1] + '_' + f.replace('.py', '') + '.txt'

                if 'darwin' in sys.platform:
                    cmd_str = '%s; %s %s' % (pythonpathstr, pythoncommand, os.path.join(source_folder, f))
                else:
                    cmd_str = '%s & %s %s' % (pythonpathstr, pythoncommand, os.path.join(source_folder, f))

                cmd_opts = ''

                if f == 'omega_batch.py':
                    cmd_opts = '--batch_file omega_model/test_inputs/test_batch.csv --verbose --session_num 0 --analysis_final_year 2020'

                cmd_str = cmd_str + ' %s > %s' % (cmd_opts, console_file_pathname)

                logwrite('TRYING %s' % cmd_str)
                r = os.system(cmd_str)

                if r == 0:
                    result_status = 'PASSED'
                elif r == -1:
                    result_status = 'FAILED'
                else:
                    result_status = 'UNKNOWN_%s' % r

                if result_status not in results:
                    results[result_status] = []

                results[result_status].append(cmd_str)
                logwrite('%s %s' % (cmd_str, result_status))

                if 'darwin' in sys.platform:
                    os.system('mv %s %s/%s_%s' % (console_file_pathname, test_omega2_output_folder, result_status, os.path.split(source_folder)[1] + '_' + f.replace('.py', '') + '.txt'))
                else:
                    os.system('RENAME %s %s_%s' % (console_file_pathname, result_status, os.path.split(source_folder)[1] + '_' + f.replace('.py', '') + '.txt'))

                logwrite('')

    except Exception as e:
        logwrite("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())

    finally:
        logwrite('TEST SUMMARY')
        for k, v in results.items():
            logwrite('-'*20 + ' %d %s ' % (len(v), k) + '-'*20)
            for c in v:
                logwrite('%s %s' % (c, k))
