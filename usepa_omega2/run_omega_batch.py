"""
run_omega_batch.py
==================

example usage:

    python run_omega_batch.py --batch_file inputs\phase0_default_batch_file.xlsx

"""
from usepa_omega2 import omega_log

print('importing %s' % __file__)

from file_eye_oh import validate_file, relocate_file


def validate_predefined_input(input_str, valid_inputs):
    if input_str in valid_inputs:
        if type(valid_inputs) is dict:
            return valid_inputs[input_str]
        elif type(valid_inputs) is set:
            return True
        else:
            raise Exception(
                'validate_predefined_input(...,valid_inputs) error: valid_inputs must be a set or dictionary')
    else:
        raise Exception('Invalid input "%s", expecting %s' % (input_str, str(valid_inputs)))


class OMEGABatchObject(object):
    def __init__(self, name='', **kwargs):
        self.name = name
        self.context_folder = ''
        self.context_id = ''
        self.context_case_id = ''
        self.output_path = ".\\"
        self.sessions = []
        self.dataframe = pd.DataFrame()

    def force_numeric_params(self):

        numeric_params = {
            'Cost Curve Frontier Affinity Factor',
            'First Pass Num Market Share Options',
            'First Pass Num Tech Options per ICE Vehicle',
            'First Pass Num Tech Options per BEV Vehicle',
            'Iteration Num Tech Options per ICE Vehicle',
            'Iteration Num Tech Options per BEV Vehicle',
            'New Vehicle Price Sales Response Elasticity',
        }

        for p in numeric_params:
            self.dataframe.loc[p] = pd.to_numeric(self.dataframe.loc[p])

    def read_parameter(self, index_str):
        return self.dataframe.loc[index_str][0]

    def parse_parameter(self, index_str, column_index, verbose=False):
        raw_param = self.dataframe.loc[index_str][column_index]
        params_dict = {'Y': 'Y',
                       'N': 'N',
                       'TRUE': True,
                       'FALSE': False,
                       }

        if type(raw_param) is str:
            if verbose:
                print('%s = "%s"' % (index_str, raw_param))
            try:
                param = eval(raw_param, {'__builtins__': None}, params_dict)
            except:
                param = raw_param
            return param
        else:
            if verbose:
                print('%s = %s' % (index_str, str(raw_param)))
            return raw_param

    def set_parameter(self, index_str, column_index, value):
        self.dataframe.loc[index_str][column_index] = value

    def parse_column_params(self, column_index, verbose=False):
        fullfact_dimensions = []
        for index_str in self.dataframe.index:
            if type(index_str) is str:
                param = self.parse_parameter(index_str, column_index)
                self.set_parameter(index_str, column_index, param)
                if type(param) is tuple:
                    if verbose:
                        print('found tuple')
                    fullfact_dimensions.append(len(param))
                else:
                    fullfact_dimensions.append(1)
            else:
                fullfact_dimensions.append(1)
        if verbose:
            print('fullfact dimensions = %s' % fullfact_dimensions)
        return fullfact_dimensions

    def parse_dataframe_params(self, verbose=False):
        fullfact_dimensions_vectors = []
        for column_index in range(0, len(self.dataframe.columns)):
            fullfact_dimensions_vectors.append(self.parse_column_params(column_index, verbose))
        return fullfact_dimensions_vectors

    def expand_dataframe(self, verbose=False):
        import pyDOE2 as doe

        acronyms_dict = {
            False: '0',
            True: '1',
            'First Pass Num Market Share Options': 'FPNMSO',
            'First Pass Num Tech Options per ICE Vehicle': 'FPNITO',
            'First Pass Num Tech Options per BEV Vehicle': 'FPNBTO',
            'Iteration Num Tech Options per ICE Vehicle': 'INITO',
            'Iteration Num Tech Options per BEV Vehicle': 'INBTO',
            'New Vehicle Price Sales Response Elasticity': 'NVPSRE',
            'Allow Backsliding': 'ABS',
            'Cost Curve Frontier Affinity Factor': 'CFAF',
            'Verbose Output': 'VB',
            'GHG Standard Type': 'GHG',
            'Iterate Producer-Consumer':'IPC',
        }

        fullfact_dimensions_vectors = self.parse_dataframe_params(verbose=verbose)

        dfx = pd.DataFrame()
        dfx['Parameters'] = self.dataframe.index
        dfx.set_index('Parameters', inplace=True)
        session_params_start_index = np.where(dfx.index == 'Enable Session')[0][0]

        dfx_column_index = 0
        # for each column in dataframe, copy or expand into dfx
        for df_column_index in range(0, len(self.dataframe.columns)):
            df_ff_dimensions_vector = fullfact_dimensions_vectors[df_column_index]
            df_ff_matrix = np.int_(doe.fullfact(df_ff_dimensions_vector))
            num_expanded_columns = np.product(df_ff_dimensions_vector)
            # expand variations and write to dfx
            for variation_index in range(0, num_expanded_columns):
                column_name = self.dataframe.loc['Session Name'][df_column_index]
                session_name = column_name
                if num_expanded_columns > 1:  # expand variations
                    column_name = column_name + '_%d' % variation_index
                    dfx[column_name] = np.nan  # add empty column to dfx
                    ff_param_indices = df_ff_matrix[variation_index]
                    num_params = len(dfx.index)
                    for param_index in range(0, num_params):
                        param_name = dfx.index[param_index]
                        if type(param_name) is str:  # if param_name is not blank (np.nan):
                            if (dfx_column_index == 0) or (param_index >= session_params_start_index):
                                # copy all data for df_column 0 (includes batchsettings) or just session settings for subsequent columns
                                if type(self.dataframe.loc[param_name][
                                            df_column_index]) == tuple:  # index tuple and get this variations element
                                    value = self.dataframe.loc[param_name][df_column_index][
                                        ff_param_indices[param_index]]
                                else:
                                    value = self.dataframe.loc[param_name][df_column_index]  # else copy source value
                                dfx.loc[param_name, dfx.columns[dfx_column_index]] = value
                                if df_ff_dimensions_vector[param_index] > 1:
                                    # omega_log.logwrite(param_name + ' has ' + str(df_ff_dimensions_vector[param_index]) + ' values ')
                                    if value in acronyms_dict:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + \
                                                       acronyms_dict[value]
                                    else:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + str(value)
                                    # omega_log.logwrite(session_name)
                    # dfx.loc['Session Name', dfx.columns[dfx_column]] = column_name
                    dfx.loc['Session Name', column_name] = session_name
                else:  # just copy column
                    dfx[column_name] = self.dataframe.iloc[:, df_column_index]
                dfx_column_index = dfx_column_index + 1
        # dfx.fillna('-----', inplace=True)
        self.dataframe = dfx

    def get_batch_settings(self):
        self.name = self.read_parameter('Batch Name')
        self.context_folder = self.read_parameter('Context Folder Name')
        self.context_id = self.read_parameter('Context Name')
        self.context_case_id = self.read_parameter('Context Case')

    def num_sessions(self):
        return len(self.dataframe.columns)

    def add_sessions(self, verbose=True):
        if verbose:
            omega_log.logwrite()
            omega_log.logwrite("In Batch '{}':".format(self.name))
        for s in range(0, self.num_sessions()):
            self.sessions.append(OMEGASessionObject("session_{%d}" % s))
            self.sessions[s].parent = self
            self.sessions[s].get_session_settings(s)
            if verbose:
                omega_log.logwrite("Found Session %s:'%s'" % (s, batch.sessions[s].name))
        if verbose:
            omega_log.logwrite()


class OMEGASessionObject(object):
    def __init__(self, name, **kwargs):
        self.parent = []
        self.name = name
        self.num = 0
        self.output_path = ".\\"
        self.enabled = False
        self.settings = OMEGARuntimeOptions()

    def read_parameter(self, index_str, default_value=None):
        try:
            param = self.parent.dataframe.loc[index_str][self.num]
        except:
            param = default_value
        finally:
            return param

    def get_session_settings(self, session_num):
        self.num = session_num
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        self.enabled = validate_predefined_input(self.read_parameter('Enable Session'), true_false_dict)
        self.name = self.read_parameter('Session Name')
        self.output_path = OMEGARuntimeOptions().output_folder  # self.read_parameter('Session Output Folder Name')

    def get_io_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        omega_log.logwrite('Getting Session I/O settings...')

        # setup IOSettings
        # if not options.dispy:
        #     self.settings.output_folder = self.output_path + "\\"
        # else:
        #     self.settings.output_folder = self.output_path + "\\" + self.name

        self.settings.session_name = self.name
        self.settings.session_unique_name = self.parent.name + '_' + self.name

        self.settings.output_folder = self.name + os.sep + self.settings.output_folder
        self.settings.database_dump_folder = self.name + os.sep + self.settings.database_dump_folder
        self.settings.context_folder = self.parent.context_folder
        self.settings.context_id = self.parent.context_id
        self.settings.context_case_id = self.parent.context_case_id

        self.settings.manufacturers_file = self.read_parameter('Manufacturers File')
        self.settings.market_classes_file = self.read_parameter('Market Classes File')
        self.settings.vehicles_file = self.read_parameter('Vehicles File')
        self.settings.demanded_shares_file = self.read_parameter('Demanded Shares File')
        self.settings.fuels_file = self.read_parameter('Fuels File')
        self.settings.fuel_scenarios_file = self.read_parameter('Fuel Scenarios File')
        self.settings.context_fuel_prices_file = self.read_parameter('Context Fuel Prices File')
        self.settings.context_fuel_upstream_file = self.read_parameter('Context Fuel Upstream File')
        self.settings.context_new_vehicle_market_file = self.read_parameter('Context New Vehicle Market File')
        self.settings.cost_file = self.read_parameter('Cost File')
        self.settings.ghg_standards_file = self.read_parameter('GHG Standards File')
        self.settings.ghg_standards_fuels_file = self.read_parameter('GHG Standards Fuels File')
        self.settings.required_zev_share_file = self.read_parameter('ZEV Requirement File')
        self.settings.verbose = validate_predefined_input(self.read_parameter('Verbose Output'), true_false_dict)
        self.settings.slice_tech_combo_cloud_tables = validate_predefined_input(
            self.read_parameter('Slice Tech Combo Tables'), true_false_dict)

    def get_runtime_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        omega_log.logwrite('Getting Runtime Settings...')

        if not pd.isna(self.read_parameter('First Pass Num Market Share Options')):
            self.settings.first_pass_num_market_share_options = int(
                self.read_parameter('First Pass Num Market Share Options'))

        if not pd.isna(self.read_parameter('First Pass Num Tech Options per ICE Vehicle')):
            self.settings.first_pass_num_tech_options_per_ice_vehicle = int(
                self.read_parameter('First Pass Num Tech Options per ICE Vehicle'))

        if not pd.isna(self.read_parameter('First Pass Num Tech Options per BEV Vehicle')):
            self.settings.first_pass_num_tech_options_per_bev_vehicle = int(
                self.read_parameter('First Pass Num Tech Options per BEV Vehicle'))

        if not pd.isna(self.read_parameter('Iteration Num Tech Options per ICE Vehicle')):
            self.settings.iteration_num_tech_options_per_ice_vehicle = int(
                self.read_parameter('Iteration Num Tech Options per ICE Vehicle'))

        if not pd.isna(self.read_parameter('Iteration Num Tech Options per BEV Vehicle')):
            self.settings.iteration_num_tech_options_per_bev_vehicle = int(
                self.read_parameter('Iteration Num Tech Options per BEV Vehicle'))

        if not pd.isna(self.read_parameter('New Vehicle Price Sales Response Elasticity')):
            self.settings.new_vehicle_sales_response_elasticity = \
                self.read_parameter('New Vehicle Price Sales Response Elasticity')

        self.settings.allow_backsliding = validate_predefined_input(self.read_parameter('Allow Backsliding'),
                                                                    true_false_dict)
        self.settings.cost_curve_frontier_affinity_factor = self.read_parameter('Cost Curve Frontier Affinity Factor')
        self.settings.iterate_producer_consumer = validate_predefined_input(
            self.read_parameter('Iterate Producer-Consumer'),
            true_false_dict)

    def get_postproc_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        omega_log.logwrite('Getting Postproc Settings...')
        if validate_predefined_input(self.read_parameter('Stock Deregistration'), {'fixed', 'dynamic'}):
            self.settings.stock_scrappage = self.read_parameter('Stock Deregistration')
        if validate_predefined_input(self.read_parameter('Stock VMT'), {'fixed', 'dynamic'}):
            self.settings.stock_vmt = self.read_parameter('Stock VMT')

    def init(self, validate_only=False):
        if not validate_only:
            omega_log.logwrite("Starting Session '%s' -> %s" % (self.name, self.output_path))
        self.get_io_settings()
        self.get_runtime_settings()
        self.get_postproc_settings()

    def run(self):
        self.init()

        omega_log.logwrite("Starting Compliance Run %s ..." % self.name)
        run_omega(self.settings)


def validate_folder(batch_root, batch_name='', session_name=''):
    dstfolder = batch_root + os.sep
    if not batch_name == '':
        dstfolder = dstfolder + batch_name + os.sep
    if not session_name == '':
        dstfolder = dstfolder + session_name + os.sep

    if not os.access(dstfolder, os.F_OK):
        try:
            os.makedirs(dstfolder, exist_ok=True)  # try create folder if necessary
        except:
            print("Couldn't access or create {}".format(dstfolder), file=sys.stderr)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    return dstfolder


class OMEGABatchOptions(object):
    def __init__(self):
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        self.validate_batch = True
        self.no_sim = False
        self.bundle_path_root = ''
        self.batch_file = ''
        self.batch_path = ''
        self.session_path = ''
        self.logfilename = 'batch_logfile.txt'
        self.session_num = []
        self.no_bundle = False
        self.verbose = False
        self.timestamp = None
        self.dispy = False
        self.dispy_ping = False
        self.dispy_debug = False
        self.dispy_exclusive = False
        self.dispy_scheduler = ip_address  # local ip_address by default
        self.local = True
        self.network = False


if __name__ == '__main__':
    try:
        import os, sys
        import argparse

        parser = argparse.ArgumentParser(
            description='Run an OMEGA compliance batch available on the network on one or more dispyNodes')
        parser.add_argument('--no_validate', action='store_true', help='Skip validating batch file')
        parser.add_argument('--no_sim', action='store_true', help='Skip running simulations')
        parser.add_argument('--bundle_path', type=str, help='Path to folder visible to all nodes',
                            default=os.getcwd() + os.sep + 'bundle')
        parser.add_argument('--batch_file', type=str, help='Path to session definitions visible to all nodes')
        parser.add_argument('--session_num', type=int, help='ID # of session to run from batch')
        parser.add_argument('--no_bundle', action='store_true',
                            help='Do NOT gather and copy all source files to bundle_path')
        parser.add_argument('--verbose', action='store_true', help='True = enable verbose omega_batch messages)')
        parser.add_argument('--timestamp', type=str,
                            help='Timestamp string, overrides creating timestamp from system clock', default=None)
        parser.add_argument('--dispy', action='store_true', help='True = run sessions on dispynode(s)')
        parser.add_argument('--dispy_ping', action='store_true', help='True = ping dispynode(s)')
        parser.add_argument('--dispy_debug', action='store_true', help='True = enable verbose dispy debug messages)')
        parser.add_argument('--dispy_exclusive', action='store_true', help='Run exclusive job, do not share dispynodes')
        parser.add_argument('--dispy_scheduler', type=str, help='Override default dispy scheduler IP address',
                            default=None)

        group = parser.add_mutually_exclusive_group()
        group.add_argument('--local', action='store_true', help='Run only on local machine, no network nodes')
        group.add_argument('--network', action='store_true', help='Run on local machine and/or network nodes')

        args = parser.parse_args()

        options = OMEGABatchOptions()
        options.validate_batch = not args.no_validate
        options.no_sim = args.no_sim
        options.bundle_path_root = args.bundle_path
        options.batch_file = args.batch_file
        options.session_num = args.session_num
        options.no_bundle = args.no_bundle  # or args.dispy # or (options.bundle_path_root is not None)
        options.verbose = args.verbose
        options.timestamp = args.timestamp
        options.dispy = args.dispy
        options.dispy_ping = args.dispy_ping
        options.dispy_debug = args.dispy_debug
        options.dispy_exclusive = args.dispy_exclusive
        if args.dispy_scheduler:
            options.dispy_scheduler = args.dispy_scheduler
        options.local = args.local
        options.network = args.network

        if options.no_bundle:
            batchfile_path = os.path.split(args.batch_file)[0]
            print('updating sys.path: %s' % [batchfile_path, batchfile_path + '\\usepa_omega2',
                                             batchfile_path + '\\usepa_omega2\\consumer'])
            sys.path.extend([batchfile_path, batchfile_path + '\\usepa_omega2',
                             batchfile_path + '\\usepa_omega2\\consumer'])

        from usepa_omega2 import *

        o2.options = options

        # get batch info
        import socket, shutil
        import pandas as pd
        from datetime import datetime
        import numpy as np

        from omega_dispy import DispyCluster

        if options.dispy_ping:
            dispycluster = DispyCluster(options)
            dispycluster.find_nodes()
            print("*** ping complete ***")
        else:
            batch = OMEGABatchObject()
            if '.csv' in options.batch_file:
                batch.dataframe = pd.read_csv(options.batch_file, index_col=0)
            else:
                batch.dataframe = pd.read_excel(options.batch_file, index_col=0, sheet_name="Sessions")

            batch.dataframe = batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
            batch.dataframe = batch.dataframe.drop('Type', axis=1, errors='ignore')  # drop Type column, no error if it's not there

            batch.expand_dataframe(verbose=options.verbose)
            batch.force_numeric_params()
            batch.get_batch_settings()
            batch.add_sessions(verbose=options.verbose)

            import copy

            expanded_batch = copy.deepcopy(batch)
            expanded_batch.name = os.path.splitext(os.path.basename(options.batch_file))[0] + '_expanded' + \
                                  os.path.splitext(options.batch_file)[1]

            if not options.no_bundle:
                if not options.timestamp:
                    options.timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                batch.dataframe.loc['Batch Name'][0] = batch.name = options.timestamp + '_' + batch.name

            # validate session files
            validate_folder(options.bundle_path_root)
            options.batch_path = validate_folder(options.bundle_path_root, batch_name=batch.name)

            options.logfilename = options.batch_path + options.logfilename

            if options.validate_batch:
                omega_log.logwrite('Validating batch definition source files...')
                # validate shared (batch) files
                validate_file(options.batch_file)

                sys.path.insert(0, os.getcwd())

                for s in range(0, batch.num_sessions()):
                    session = batch.sessions[s]
                    omega_log.logwrite("\nValidating Session %d ('%s') Files..." % (s, session.name))

                    # automatically validate files and folders based on parameter naming convention
                    for i in batch.dataframe.index:
                        # if options.verbose and (str(i).endswith(' Folder Name') or str(i).endswith(' File')):
                        #     omega_log.logwrite('validating %s=%s' % (i, session.read_parameter(i)))
                        # elif str(i).endswith(' Folder Name'):
                        #     validate_folder(session.read_parameter(i))
                        # elif str(i).endswith(' File'):
                        #     validate_file(session.read_parameter(i))
                        if options.verbose and (str(i).endswith(' File')):
                            omega_log.logwrite('validating %s=%s' % (i, session.read_parameter(i)))
                        elif str(i).endswith(' File'):
                            validate_file(session.read_parameter(i))

                    omega_log.logwrite('Validating Session %d Parameters...' % s)
                    session.init(validate_only=True)

            omega_log.logwrite("\n*** validation complete ***")

            # copy files to network_batch_path
            if not options.no_bundle:
                omega_log.logwrite('Bundling Source Files...')
                for source_folder in ['usepa_omega2\\', 'usepa_omega2\\consumer\\']:
                    source_files = [fn for fn in os.listdir(source_folder) if '.py' in fn]
                    validate_folder(options.batch_path + source_folder)
                    for f in source_files:
                        relocate_file(options.batch_path + source_folder, source_folder + f)

                # write a copy of the expanded, validated batch to the source batch_file directory:
                if '.csv' in options.batch_file:
                    expanded_batch.dataframe.to_csv(os.path.dirname(options.batch_file) + '\\' + expanded_batch.name)
                else:
                    expanded_batch.dataframe.to_excel(os.path.dirname(options.batch_file) + '\\' + expanded_batch.name,
                                                      "Sessions")

                # copy session inputs to session folder(s) for active session(s)
                for s in range(0, batch.num_sessions()):
                    if batch.sessions[s].enabled:
                        omega_log.logwrite('Bundling Session %d Files...' % s)
                        session = batch.sessions[s]
                        options.session_path = validate_folder(options.bundle_path_root, batch_name=batch.name,
                                                               session_name=session.name)

                        # indicate source batch
                        if ':' in args.batch_file:
                            # batch file path is absolute
                            batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % args.batch_file
                        else:
                            # batch file path is relative
                            batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % (
                                        os.getcwd() + os.sep + args.batch_file)

                        # automatically rename and relocate source files
                        for i in batch.dataframe.index:
                            # if str(i).endswith(' Folder Name'):
                            #     if options.verbose:
                            #         omega_log.logwrite('renaming %s to %s' % (batch.dataframe.loc[i][session.num],
                            #                                      session.name + os.sep + batch.dataframe.loc[i][
                            #                                          session.num]))
                            #     batch.dataframe.loc[i][session.num] = \
                            #         session.name + os.sep + batch.dataframe.loc[i][session.num]
                            if str(i).endswith(' File'):
                                if options.verbose:
                                    omega_log.logwrite('relocating %s to %s' % (batch.dataframe.loc[i][session.num],
                                                                   options.session_path + session.read_parameter(i)))
                                batch.dataframe.loc[i][session.num] = \
                                    session.name + os.sep + relocate_file(options.session_path,
                                                                          session.read_parameter(i))

            import time

            time.sleep(5)  # was 10, wait for files to fully transfer...

            os.chdir(options.batch_path)

            remote_batchfile = batch.name + '.csv'
            batch.dataframe.to_csv(remote_batchfile)

            # print("Batch name = " + batch.name)
            omega_log.logwrite("Batch name = " + batch.name)

            if options.session_num is None:
                session_list = range(0, batch.num_sessions())
            else:
                session_list = [options.session_num]

            if not options.no_sim:
                if options.dispy:  # run remote job on cluster
                    retry_count = dict()  # track retry attempts for terminated or abandoned jobs

                    dispycluster = DispyCluster(options)
                    dispycluster.find_nodes()
                    dispycluster.submit_sessions(batch, batch.name, options.bundle_path_root, options.batch_path + batch.name,
                                                 session_list)
                    omega_log.logwrite("*** batch complete ***")
                else:  # run from here
                    batch = OMEGABatchObject()
                    omega_log.logwrite('REMOTE BATCHFILE = %s' % remote_batchfile)
                    batch.dataframe = pd.read_csv(remote_batchfile, index_col=0)
                    batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False},
                                            inplace=True)
                    batch.dataframe.drop('Type', axis=1, inplace=True,
                                         errors='ignore')  # drop Type column, no error if it's not there
                    batch.force_numeric_params()
                    batch.get_batch_settings()
                    batch.add_sessions(verbose=False)

                    # process sessions:
                    for s_index in session_list:
                        omega_log.logwrite("Processing Session %d (%s):" % (s_index, batch.sessions[s_index].name))

                        if not batch.sessions[s_index].enabled:
                            omega_log.logwrite("Skipping Disabled Session '%s'" % batch.sessions[s_index].name)
                            omega_log.logwrite('')
                        else:
                            batch.sessions[s_index].run()
                        # omega_log.logwrite("*** batch complete ***")

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
