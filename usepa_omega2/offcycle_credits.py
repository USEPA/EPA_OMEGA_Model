"""
offycle_credits.py
==================

**Routines to load and access offcycle credit values**

Off-cycle credits represent GHG benefits of technologies that have no or limited on-cycle benefits.

For example, LED headlights have a real-world ("off-cycle") benefit but are not represented during certification
testing (tests are performed with headlights off).

As another example, engine Stop-Start has an on-cycle benefit but the vehicle idle duration during testing may
under-represent vehicle idle duration in real-world driving so there may be some additional benefit available.


"""

print('importing %s' % __file__)

from usepa_omega2 import *


class OffcycleCredits(OMEGABase):
    values = dict()

    @staticmethod
    def init_from_file(filename, verbose=False):
        import numpy as np

        if verbose:
            omega_log.logwrite('\nInitializing data from %s...' % filename)

        input_template_name = 'offcycle_credits'
        input_template_version = 0.1
        input_template_columns = {'start_year', 'credit_name', 'credit_group', 'credit_destination'}

        template_errors = validate_template_version_info(filename, input_template_name, input_template_version,
                                                         verbose=verbose)

        if not template_errors:
            # read in the data portion of the input file
            df = pd.read_csv(filename, skiprows=1)

            template_errors = validate_template_columns(filename, input_template_columns, df.columns, verbose=verbose)

            if not template_errors:
                OffcycleCredits.values['start_year'] = np.array(df['start_year'])
                OffcycleCredits.values['data'] = df

                credit_columns = [c for c in df.columns if ('reg_class_id:' in c)]

                for cc in credit_columns:
                    reg_class_id = cc.split(':')[1]
                    if not reg_class_id in reg_classes:
                        template_errors.append('*** Invalid Reg Class ID "%s" in %s ***' % (reg_class_id, filename))

        return template_errors


if __name__ == '__main__':
    try:
        if '__file__' in locals():
            print(fileio.get_filenameext(__file__))

        # set up global variables:
        o2.options = OMEGARuntimeOptions()
        init_omega_db()
        o2.engine.echo = o2.options.verbose
        omega_log.init_logfile()

        SQABase.metadata.create_all(o2.engine)

        init_fail = []
        init_fail = init_fail + OffcycleCredits.init_from_file(o2.options.offcycle_credits_file,
                                                                verbose=o2.options.verbose)

        if not init_fail:
            fileio.validate_folder(o2.options.database_dump_folder)
            OffcycleCredits.values['data'].to_csv(
                o2.options.database_dump_folder + os.sep + 'required_zev_shares.csv', index=False)

        else:
            print(init_fail)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            os._exit(-1)
    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
