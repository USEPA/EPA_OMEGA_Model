"""
omega_batch.py
==================

example usage:

    python omega_batch.py --batch_file inputs\phase0_default_batch_file.xlsx

"""

print('importing %s' % __file__)

import os, sys

# make sure top-level project folder is on the path (i.e. folder that contains usepa_omega2)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# print('usepa_omega2 omega_batch.py path = %s' %  os.path.abspath(__file__))
# print('SYS Path = %s' % sys.path)

from o2 import OMEGABase
from usepa_omega2 import OMEGARuntimeOptions
from file_eye_oh import validate_file, relocate_file

bundle_input_folder_name = 'in'
bundle_output_folder_name = OMEGARuntimeOptions().output_folder


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


def is_absolute_path(source_file_path):
    """

    Args:
        source_file_path: file path

    Returns: True if file path is absolute

    """
    # return source_file_path.startswith('/') or source_file_path.startswith('\\') or (source_file_path[1] == ':')
    import os
    return os.path.isabs(source_file_path)


class OMEGABatchObject(OMEGABase):
    def __init__(self, name='', **kwargs):
        import pandas as pd

        self.batch_definition_path = ''
        self.name = name
        self.context_folder = ''
        self.context_id = ''
        self.context_case_id = ''
        self.context_new_vehicle_prices_file = ''
        self.generate_context_new_vehicle_prices_file = False
        self.output_path = "." + os.sep
        self.sessions = []
        self.dataframe = pd.DataFrame()
        self.batch_log = None
        self.auto_close_figures = True

    def force_numeric_params(self):
        import pandas as pd

        numeric_params = {
            'Cost Curve Frontier Affinity Factor',
            'Num Market Share Options',
            'Num Tech Options per ICE Vehicle',
            'Num Tech Options per BEV Vehicle',
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
        import pandas as pd
        import numpy as np

        acronyms_dict = {
            False: '0',
            True: '1',
            'Num Market Share Options': 'NMSO',
            'Num Tech Options per ICE Vehicle': 'NITO',
            'Num Tech Options per BEV Vehicle': 'NBTO',
            'New Vehicle Price Sales Response Elasticity': 'NVPSRE',
            'Consumer Pricing Multiplier Min': 'CPMMIN',
            'Consumer Pricing Multiplier Max': 'CPMMAX',
            'Allow Backsliding': 'BS',
            'Cost Curve Frontier Affinity Factor': 'CFAF',
            'Verbose Output': 'VB',
            'GHG Standard Type': 'GHG',
            'Iterate Producer-Consumer': 'IPC',
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
                                    # batch_log.logwrite(param_name + ' has ' + str(df_ff_dimensions_vector[param_index]) + ' values ')
                                    if value in acronyms_dict:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + \
                                                       acronyms_dict[value]
                                    else:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + str(value)
                                    # batch_log.logwrite(session_name)
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
        self.context_new_vehicle_prices_file = self.read_parameter('Context New Vehicle Prices File').replace('\\', os.sep)
        # context_new_vehicle_prices_file can be one of:
        # relative path, absolute path, 'GENERATE' or 'GENERATE filename' where filename can be an absolute or relative path
        # if 'GENERATE' then the default file name will be batch_definition_path + 'context_new_vehicle_prices.csv'
        if self.context_new_vehicle_prices_file.startswith('GENERATE'):
            self.generate_context_new_vehicle_prices_file = True
            self.context_new_vehicle_prices_file = \
                self.context_new_vehicle_prices_file.replace('GENERATE', '').strip()
            if not self.context_new_vehicle_prices_file:
                self.context_new_vehicle_prices_file = 'context_new_vehicle_prices.csv'

    def num_sessions(self):
        return len(self.dataframe.columns)

    def add_sessions(self, verbose=True):
        if verbose:
            self.batch_log.logwrite('')
            self.batch_log.logwrite("In Batch '{}':".format(self.name))
        for s in range(0, self.num_sessions()):
            self.sessions.append(OMEGASessionObject("session_{%d}" % s))
            self.sessions[s].parent = self
            self.sessions[s].get_session_settings(s)
            if verbose:
                self.batch_log.logwrite("Found Session %s:'%s'" % (s, self.sessions[s].name))
        if verbose:
            self.batch_log.logwrite('')


class OMEGASessionObject(OMEGABase):
    def __init__(self, name, **kwargs):
        from omega2 import OMEGARuntimeOptions

        self.parent = []
        self.name = name
        self.num = 0
        self.output_path = "." + os.sep
        self.enabled = False
        self.settings = OMEGARuntimeOptions()
        self.result = []

    def read_parameter(self, index_str, default_value=None):
        try:
            param = self.parent.dataframe.loc[index_str][self.num]
        except:
            param = default_value
        finally:
            return param

    def get_session_settings(self, session_num):
        from omega2 import OMEGARuntimeOptions

        self.num = session_num
        self.settings.session_is_reference = self.num == 0
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        self.enabled = validate_predefined_input(self.read_parameter('Enable Session'), true_false_dict)
        self.name = self.read_parameter('Session Name')
        self.output_path = OMEGARuntimeOptions().output_folder  # self.read_parameter('Session Output Folder Name')

    def get_io_settings(self, remote=False):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        self.parent.batch_log.logwrite('Getting Session I/O settings...')

        self.settings.session_name = self.name
        self.settings.session_unique_name = self.parent.name + '_' + self.name
        self.settings.auto_close_figures = self.parent.auto_close_figures
        self.settings.output_folder = self.name + os.sep + self.settings.output_folder
        self.settings.database_dump_folder = self.name + os.sep + self.settings.database_dump_folder
        self.settings.context_folder = self.parent.context_folder
        self.settings.context_id = self.parent.context_id
        self.settings.context_case_id = self.parent.context_case_id

        if self.num > 0:
            self.settings.generate_context_new_vehicle_prices_file = False
        else:
            self.settings.generate_context_new_vehicle_prices_file = self.parent.generate_context_new_vehicle_prices_file

        if remote and self.num > 0:
            self.settings.context_new_vehicle_prices_file = self.read_parameter('Context New Vehicle Prices File').replace('\\', os.sep)
        else: # local or self.num==0 (reference case)
            self.settings.context_new_vehicle_prices_file = self.parent.context_new_vehicle_prices_file

        self.settings.manufacturers_file = self.read_parameter('Manufacturers File')
        self.settings.market_classes_file = self.read_parameter('Market Classes File')
        self.settings.vehicles_file = self.read_parameter('Vehicles File')
        self.settings.demanded_shares_file = self.read_parameter('Demanded Shares File')
        self.settings.fuels_file = self.read_parameter('Fuels File')
        self.settings.fuel_scenarios_file = self.read_parameter('Fuel Scenarios File')
        self.settings.context_fuel_prices_file = self.read_parameter('Context Fuel Prices File')
        self.settings.context_new_vehicle_market_file = self.read_parameter('Context New Vehicle Market File')
        self.settings.cost_file = self.read_parameter('Cost File')
        self.settings.ghg_standards_file = self.read_parameter('GHG Standards File')
        self.settings.ghg_standards_fuels_file = self.read_parameter('GHG Standards Fuels File')
        self.settings.ghg_credits_file = self.read_parameter('GHG Credits File')
        self.settings.required_zev_share_file = self.read_parameter('ZEV Requirement File')
        self.settings.reregistration_fixed_by_age_file = self.read_parameter('Stock Deregistration File')
        self.settings.annual_vmt_fixed_by_age_file = self.read_parameter('Stock VMT File')
        self.settings.verbose = validate_predefined_input(self.read_parameter('Verbose Output'), true_false_dict)
        self.settings.slice_tech_combo_cloud_tables = validate_predefined_input(
            self.read_parameter('Slice Tech Combo Tables'), true_false_dict)

    def get_runtime_settings(self):
        import pandas as pd

        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        self.parent.batch_log.logwrite('Getting Runtime Settings...')

        if not pd.isna(self.read_parameter('Num Market Share Options')):
            self.settings.producer_num_market_share_options = int(
                self.read_parameter('Num Market Share Options'))

        if not pd.isna(self.read_parameter('Num Tech Options per ICE Vehicle')):
            self.settings.producer_num_tech_options_per_ice_vehicle = int(
                self.read_parameter('Num Tech Options per ICE Vehicle'))

        if not pd.isna(self.read_parameter('Num Tech Options per BEV Vehicle')):
            self.settings.producer_num_tech_options_per_bev_vehicle = int(
                self.read_parameter('Num Tech Options per BEV Vehicle'))

        if not pd.isna(self.read_parameter('New Vehicle Price Sales Response Elasticity')):
            self.settings.new_vehicle_sales_response_elasticity = \
                self.read_parameter('New Vehicle Price Sales Response Elasticity')

        if not pd.isna(self.read_parameter('Consumer Pricing Multiplier Min')):
            self.settings.consumer_pricing_multiplier_min = float(
                self.read_parameter('Consumer Pricing Multiplier Min'))

        if not pd.isna(self.read_parameter('Consumer Pricing Multiplier Max')):
            self.settings.consumer_pricing_multiplier_max = float(
                self.read_parameter('Consumer Pricing Multiplier Max'))

        self.settings.allow_backsliding = validate_predefined_input(self.read_parameter('Allow Backsliding'),
                                                                    true_false_dict)
        self.settings.cost_curve_frontier_affinity_factor = self.read_parameter('Cost Curve Frontier Affinity Factor')
        self.settings.iterate_producer_consumer = validate_predefined_input(
            self.read_parameter('Iterate Producer-Consumer'),
            true_false_dict)

    def get_postproc_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        self.parent.batch_log.logwrite('Getting Postproc Settings...')
        self.settings.criteria_cost_factors_file = self.read_parameter('Context Criteria Cost Factors File')
        self.settings.scc_cost_factors_file = self.read_parameter('Context SCC Cost Factors File')
        self.settings.energysecurity_cost_factors_file = self.read_parameter('Context Energy Security Cost Factors File')
        self.settings.congestion_noise_cost_factors_file = self.read_parameter('Context Congestion-Noise Cost Factors File')
        self.settings.emission_factors_powersector_file = self.read_parameter('Context Powersector Emission Factors File')
        self.settings.emission_factors_refinery_file = self.read_parameter('Context Refinery Emission Factors File')
        self.settings.emission_factors_vehicles_file = self.read_parameter('Context Vehicle Emission Factors File')
        self.settings.ip_deflators_file = self.read_parameter('Context Implicit Price Deflators File')
        self.settings.cpi_deflators_file = self.read_parameter('Context Consumer Price Index File')

    def init(self, validate_only=False, remote=False):
        if not validate_only:
            self.parent.batch_log.logwrite("Starting Session '%s' -> %s" % (self.name, self.output_path))
        self.get_io_settings(remote=remote)
        self.get_runtime_settings()
        self.get_postproc_settings()

    def run(self, remote=False):
        from omega2 import run_omega

        self.init(remote=remote)

        self.parent.batch_log.logwrite("Starting Compliance Run %s ..." % self.name)
        result = run_omega(self.settings)
        return result


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
            import traceback

            print('Couldn''t access or create {"%s"}' % (dstfolder), file=sys.stderr)
            print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
            sys.exit(-1)
    return dstfolder


class OMEGABatchOptions(OMEGABase):
    def __init__(self):
        import time
        import socket
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)

        self.start_time = time.time()
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
        self.auto_close_figures = True
        self.dispy = False
        self.dispy_ping = False
        self.dispy_debug = False
        self.dispy_exclusive = False
        self.dispy_scheduler = ip_address  # local ip_address by default
        self.local = True
        self.network = False


def run_bundled_sessions(batch, options, remote_batchfile, session_list):
    import pandas as pd
    from omega_log import OMEGALog
    import time

    batch = OMEGABatchObject()
    batch.batch_definition_path = options.batch_path
    batch.batch_log = OMEGALog(options)
    batch.batch_log.logwrite('REMOTE BATCHFILE = %s' % remote_batchfile)
    batch.dataframe = pd.read_csv(remote_batchfile, index_col=0)
    batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False},
                            inplace=True)
    batch.dataframe.drop('Type', axis=1, inplace=True,
                         errors='ignore')  # drop Type column, no error if it's not there
    batch.force_numeric_params()
    batch.get_batch_settings()
    batch.auto_close_figures = options.auto_close_figures
    batch.add_sessions(verbose=False)
    # process sessions:
    for s_index in session_list:
        batch.batch_log.logwrite("\nProcessing Session %d (%s):" % (s_index, batch.sessions[s_index].name))

        if not batch.sessions[s_index].enabled:
            batch.batch_log.logwrite("Skipping Disabled Session '%s'" % batch.sessions[s_index].name)
            batch.batch_log.logwrite('')
        else:
            batch.sessions[s_index].result = batch.sessions[s_index].run(remote=True)

            if not batch.sessions[s_index].result:
                # normal run, no failures
                time.sleep(1)  # wait for files to close
                summary_filename = os.path.join(options.bundle_path_root, batch.name,
                                                batch.sessions[s_index].name, bundle_output_folder_name,
                                                'o2log_%s_%s.txt' % (
                                                    batch.name, batch.sessions[s_index].name))

                # check session completion status and add status prefix to session folder
                if os.path.exists(summary_filename) and os.path.getsize(summary_filename) > 0:
                    with open(summary_filename, "r") as f_read:
                        last_line = f_read.readlines()[-1]
                    batch_path = os.path.join(options.bundle_path_root, batch.name)
                    if 'Session Complete' in last_line:
                        completion_prefix = '_'
                        batch.batch_log.logwrite('$$$ Session Completed, Session "%s" $$$' %
                                                 batch.sessions[s_index].name)
                    elif 'Session Fail' in last_line:
                        completion_prefix = '#FAIL_'
                        batch.batch_log.logwrite(
                            '*** Session Failed, Session "%s" ***' % batch.sessions[s_index].name)
                    else:
                        completion_prefix = '#WEIRD_'
                        batch.batch_log.logwrite('??? Weird Summary File for Session "%s" : last_line = "%s" ???' % (
                            batch.sessions[s_index].name, last_line))

                    os.rename(os.path.join(batch_path, batch.sessions[s_index].name),
                              os.path.join(batch_path, completion_prefix + batch.sessions[s_index].name))
            else:
                # abnormal run, display fault
                batch.batch_log.logwrite(
                    '\n*** Session Failed, Session "%s" ***' % batch.sessions[s_index].name)
                for idx, r in enumerate(batch.sessions[s_index].result):
                    if idx == 0:
                        # strip leading '\n'
                        r = r[1:]
                    batch.batch_log.logwrite(r)

    batch.batch_log.end_logfile("$$$ batch complete $$$")
    return batch


def run_omega_batch(no_validate=False, no_sim=False, bundle_path=os.getcwd() + os.sep + 'bundle', batch_file='',
                    session_num=None, no_bundle=False, verbose=False, timestamp=None, show_figures=False, dispy=False,
                    dispy_ping=False, dispy_debug=False, dispy_exclusive=False, dispy_scheduler=None, local=False,
                    network=False):

    import sys

    # print('run_omega_batch sys.path = %s' % sys.path)
    import o2

    options = OMEGABatchOptions()
    options.validate_batch = not no_validate
    options.no_sim = no_sim
    options.bundle_path_root = bundle_path
    options.batch_file = batch_file
    options.session_num = session_num
    options.no_bundle = no_bundle  # or args.dispy # or (options.bundle_path_root is not None)
    options.verbose = verbose
    options.timestamp = timestamp
    options.auto_close_figures = not show_figures
    options.dispy = dispy
    options.dispy_ping = dispy_ping
    options.dispy_debug = dispy_debug
    options.dispy_exclusive = dispy_exclusive
    if dispy_scheduler:
        options.dispy_scheduler = dispy_scheduler
    options.local = local
    options.network = network

    if options.no_bundle:
        batchfile_path = os.path.split(args.batch_file)[0]

        package_folder = batchfile_path + os.sep + 'usepa_omega2'

        subpackage_list = [package_folder + os.sep + d for d in os.listdir(package_folder)
                           if os.path.isdir(package_folder + os.sep + d)
                           and '__init__.py' in os.listdir('%s%s%s' % (package_folder, os.sep, d))]

        sys.path.extend([batchfile_path, batchfile_path + os.sep + package_folder] + subpackage_list)

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
        batch.batch_definition_path = os.path.dirname(os.path.abspath(options.batch_file)) + os.sep

        if '.csv' in options.batch_file:
            batch.dataframe = pd.read_csv(options.batch_file, index_col=0)
        else:
            batch.dataframe = pd.read_excel(options.batch_file, index_col=0, sheet_name="Sessions")

        batch.dataframe = batch.dataframe.replace(
            to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        batch.dataframe = batch.dataframe.drop('Type', axis=1,
                                               errors='ignore')  # drop Type column, no error if it's not there

        batch.expand_dataframe(verbose=options.verbose)
        batch.force_numeric_params()
        batch.get_batch_settings()

        if not options.no_bundle:
            if not options.timestamp:
                options.timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            batch.dataframe.loc['Batch Name'][0] = batch.name = options.timestamp + '_' + batch.name

        # validate session files
        validate_folder(options.bundle_path_root)
        options.batch_path = validate_folder(options.bundle_path_root, batch_name=batch.name)

        options.logfilename = options.batch_path + options.logfilename

        from omega_log import OMEGALog
        batch.batch_log = OMEGALog(options)

        batch.add_sessions(verbose=options.verbose)

        import copy

        expanded_batch = copy.deepcopy(batch)
        expanded_batch.name = os.path.splitext(os.path.basename(options.batch_file))[0] + '_expanded' + \
                              os.path.splitext(options.batch_file)[1]

        if options.validate_batch:
            batch.batch_log.logwrite('Validating batch definition source files...')
            # validate shared (batch) files
            validate_file(options.batch_file)

            sys.path.insert(0, os.getcwd())

            print('\nbatch_definition_path = %s\n' % batch.batch_definition_path)

            for s in range(0, batch.num_sessions()):
                session = batch.sessions[s]
                batch.batch_log.logwrite("\nValidating Session %d ('%s') Files..." % (s, session.name))

                # automatically validate files and folders based on parameter naming convention
                for i in batch.dataframe.index:
                    # if options.verbose and (str(i).endswith(' Folder Name') or str(i).endswith(' File')):
                    #     batch.batch_log.logwrite('validating %s=%s' % (i, session.read_parameter(i)))
                    # elif str(i).endswith(' Folder Name'):
                    #     validate_folder(session.read_parameter(i))
                    # elif str(i).endswith(' File'):
                    #     validate_file(session.read_parameter(i))
                    if str(i).endswith(' File'):
                        source_file_path = session.read_parameter(i)
                        if type(source_file_path) is str:
                            source_file_path = source_file_path.replace('\\', os.sep)
                        if (i != 'Context New Vehicle Prices File') or \
                                ( (s == 0) and (i == 'Context New Vehicle Prices File') and
                                 not batch.generate_context_new_vehicle_prices_file):
                            if is_absolute_path(source_file_path):
                                if options.verbose: batch.batch_log.logwrite('validating %s=%s' % (i, source_file_path))
                                validate_file(source_file_path)
                            else:
                                if options.verbose: batch.batch_log.logwrite(
                                    'validating %s=%s' % (i, batch.batch_definition_path + source_file_path))
                                validate_file(batch.batch_definition_path + source_file_path)

                batch.batch_log.logwrite('Validating Session %d Parameters...' % s)
                session.init(validate_only=True)

        batch.batch_log.logwrite("\n*** validation complete ***")

        # copy files to network_batch_path
        if not options.no_bundle:
            batch.batch_log.logwrite('Bundling Source Files...')

            # go to project top level so we can copy source files
            os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

            package_folder = 'usepa_omega2'
            subpackage_list = [package_folder + os.sep + d for d in os.listdir(package_folder)
                               if os.path.isdir(package_folder + os.sep + d)
                               and '__init__.py' in os.listdir('%s%s%s' % (package_folder, os.sep, d))]

            for source_folder in [package_folder] + subpackage_list:
                source_files = [fn for fn in os.listdir(source_folder) if '.py' in fn]
                validate_folder(options.batch_path + source_folder)
                for f in source_files:
                    relocate_file(options.batch_path + source_folder, source_folder + os.sep + f)

            # write a copy of the original batch definition file to the bundle
            relocate_file(options.batch_path, options.batch_file)

            # write a copy of the expanded, validated batch to the source batch_file directory:
            if '.csv' in options.batch_file:
                expanded_batch.dataframe.to_csv(os.path.dirname(options.batch_file) + os.sep + expanded_batch.name)
            else:
                expanded_batch.dataframe.to_excel(os.path.dirname(options.batch_file) + os.sep + expanded_batch.name,
                                                  "Sessions")

            # copy session inputs to session folder(s) for active session(s)
            for s in range(0, batch.num_sessions()):
                if batch.sessions[s].enabled:
                    batch.batch_log.logwrite('Bundling Session %d Files...' % s)
                    session = batch.sessions[s]
                    options.session_path = validate_folder(options.bundle_path_root, batch_name=batch.name,
                                                           session_name=session.name)
                    validate_folder(options.bundle_path_root, batch_name=batch.name,
                                    session_name=session.name + os.sep + bundle_input_folder_name)
                    # indicate source batch
                    if is_absolute_path(options.batch_file):
                        # batch file path is absolute
                        batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % options.batch_file
                    else:
                        # batch file path is relative
                        batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % (
                                os.getcwd() + os.sep + options.batch_file)

                    # automatically rename and relocate source files
                    for i in batch.dataframe.index:
                        # if str(i).endswith(' Folder Name'):
                        #     if options.verbose:
                        #         batch.batch_log.logwrite('renaming %s to %s' % (batch.dataframe.loc[i][session.num],
                        #                                      session.name + os.sep + batch.dataframe.loc[i][
                        #                                          session.num]))
                        #     batch.dataframe.loc[i][session.num] = \
                        #         session.name + os.sep + batch.dataframe.loc[i][session.num]
                        if str(i).endswith(' File'):
                            if (i != 'Context New Vehicle Prices File') or \
                                    ((i == 'Context New Vehicle Prices File') and
                                     not batch.generate_context_new_vehicle_prices_file):
                                if i != 'Context New Vehicle Prices File':
                                    source_file_path = batch.dataframe.loc[i][session.num]
                                else:
                                    source_file_path = batch.context_new_vehicle_prices_file

                                if type(source_file_path) is str:
                                    # fix path separators, if necessary
                                    source_file_path = source_file_path.replace('\\', os.sep)

                                if is_absolute_path(source_file_path):
                                    import file_eye_oh as fileio
                                    # file_path is absolute path
                                    if options.verbose:
                                        batch.batch_log.logwrite('relocating %s to %s' % (
                                        source_file_path, options.session_path + fileio.get_filenameext(source_file_path)))
                                    batch.dataframe.loc[i][session.num] = session.name + os.sep + bundle_input_folder_name + os.sep + relocate_file(
                                        options.session_path + bundle_input_folder_name, source_file_path)
                                else:
                                    # file_path is relative path
                                    if options.verbose:
                                        batch.batch_log.logwrite('relocating %s to %s' % (
                                            batch.batch_definition_path + batch.dataframe.loc[i][session.num],
                                            options.session_path + source_file_path))
                                    batch.dataframe.loc[i][session.num] = session.name + os.sep + bundle_input_folder_name + os.sep + relocate_file(
                                        options.session_path + bundle_input_folder_name, batch.batch_definition_path + source_file_path)
                            else:
                                # handle 'Context New Vehicle Prices File' when generating
                                if session.num == 0:
                                    batch.dataframe.loc[i][session.num] = batch.dataframe.loc[i][session.num]
                                else:
                                    batch.dataframe.loc[i][session.num] = batch.context_new_vehicle_prices_file

        import time

        time.sleep(5)  # was 10, wait for files to fully transfer...

        os.chdir(options.batch_path)

        remote_batchfile = batch.name + '.csv'
        batch.dataframe.to_csv(remote_batchfile)

        # print("Batch name = " + batch.name)
        batch.batch_log.logwrite("Batch name = " + batch.name)

        if options.session_num is None:
            session_list = range(0, batch.num_sessions())
        else:
            session_list = [options.session_num]

        if not options.no_sim:
            if options.dispy:  # run remote job on cluster, except for first job if generating context vehicle prices
                dispy_session_list = session_list
                if batch.generate_context_new_vehicle_prices_file:
                    import copy
                    # run reference case to generate vehicle prices then dispy the rest
                    run_bundled_sessions(copy.copy(batch), options, remote_batchfile, [0])
                    dispy_session_list = dispy_session_list[1:]

                if dispy_session_list:
                    retry_count = dict()  # track retry attempts for terminated or abandoned jobs

                    dispycluster = DispyCluster(options)
                    dispycluster.find_nodes()
                    dispycluster.submit_sessions(batch, batch.name, options.bundle_path_root,
                                                 options.batch_path + batch.name,
                                                 dispy_session_list)
                    batch.batch_log.end_logfile("*** dispy batch complete ***")
            else:  # run from here
                batch = run_bundled_sessions(batch, options, remote_batchfile, session_list)

            batch_summary_filename = ''
            # if not running a session inside a dispy batch (i.e. we are the top-level batch):
            if options.session_num is None:
                # post-process sessions (collate summary files)
                for idx, s_index in enumerate(session_list):
                    if not batch.sessions[s_index].result or options.dispy:
                        batch.batch_log.logwrite("\nPost-Processing Session %d (%s):" % (s_index, batch.sessions[s_index].name))
                        session_summary_filename = options.batch_path + '_' + batch.sessions[
                            s_index].settings.output_folder + batch.sessions[
                                                       s_index].settings.session_unique_name + '_summary_results.csv'
                        batch_summary_filename = batch.name + '_summary_results.csv'
                        if os.access(session_summary_filename, os.F_OK):
                            if idx == 0:
                                # copy the first summary verbatim to create batch summary
                                shutil.copyfile(session_summary_filename, batch_summary_filename)
                            else:
                                # add subsequent sessions to batch summary
                                df = pd.read_csv(session_summary_filename)
                                df.to_csv(batch_summary_filename, header=False, index=False, mode='a')

                # perform batch post-process, if possible
                if os.access(batch_summary_filename, os.F_OK):
                    import postproc_batch
                    postproc_batch.run_postproc(batch.batch_log, batch_summary_filename)


if __name__ == '__main__':
    try:
        import os, sys, time
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
        parser.add_argument('--verbose', action='store_true', help='Enable verbose omega_batch messages)')
        parser.add_argument('--timestamp', type=str,
                            help='Timestamp string, overrides creating timestamp from system clock', default=None)
        parser.add_argument('--show_figures', action='store_true', help='Display figure windows (no auto-close)')
        parser.add_argument('--dispy', action='store_true', help='Run sessions on dispynode(s)')
        parser.add_argument('--dispy_ping', action='store_true', help='Ping dispynode(s)')
        parser.add_argument('--dispy_debug', action='store_true', help='Enable verbose dispy debug messages)')
        parser.add_argument('--dispy_exclusive', action='store_true', help='Run exclusive job, do not share dispynodes')
        parser.add_argument('--dispy_scheduler', type=str, help='Override default dispy scheduler IP address',
                            default=None)

        group = parser.add_mutually_exclusive_group()
        group.add_argument('--local', action='store_true', help='Run only on local machine, no network nodes')
        group.add_argument('--network', action='store_true', help='Run on local machine and/or network nodes')

        args = parser.parse_args()

        run_omega_batch(no_validate=args.no_validate, no_sim=args.no_sim, bundle_path=args.bundle_path,
                        batch_file=args.batch_file, session_num=args.session_num, no_bundle=args.no_bundle,
                        verbose=args.verbose, timestamp=args.timestamp, show_figures=args.show_figures,
                        dispy=args.dispy, dispy_ping=args.dispy_ping, dispy_debug=args.dispy_debug,
                        dispy_exclusive=args.dispy_exclusive, dispy_scheduler=args.dispy_scheduler, local=args.local,
                        network=args.network)

    except:
        import traceback

        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
