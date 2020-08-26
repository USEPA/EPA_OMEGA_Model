"""
run_omega_batch.py
==================

example usage:

    python run_omega_batch.py --batch_file inputs\phase0_default_batch_file.xlsx

"""


class OMEGABatchObject(object):
    def __init__(self, name='', **kwargs):
        self.name = name
        self.output_path = ".\\"
        self.sessions = []
        self.dataframe = pd.DataFrame()

    def force_numeric_params(self):

        numeric_params = {
            'Cost Curve Frontier Affinity Factor',
            'Num Tech Options per Vehicle',
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
                       'CostClouds': 'clouds',
                       'CostCurves': 'curves',
                       'Flat': 'flat',
                       'Footprint': 'footprint',
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
                print('%s = %s' % (index_str, raw_param.__str__()))
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
                    fullfact_dimensions.append(param.__len__())
                else:
                    fullfact_dimensions.append(1)
            else:
                fullfact_dimensions.append(1)
        if verbose:
            print('fullfact dimensions = %s' % fullfact_dimensions)
        return fullfact_dimensions

    def parse_dataframe_params(self, verbose=False):
        fullfact_dimensions_vectors = []
        for column_index in range(0, self.dataframe.columns.__len__()):
            fullfact_dimensions_vectors.append(self.parse_column_params(column_index, verbose))
        return fullfact_dimensions_vectors

    def expand_dataframe(self, verbose=False):
        import pyDOE2 as doe

        acronyms_dict = {
            False: '0',
            True: '1',
            'Num Tech Options per Vehicle': 'NTO',
            'Allow Backsliding': 'ABS',
            'Cost Curve Frontier Affinity Factor': 'CFAF',
            'Verbose Output': 'VB',
            'GHG Standard Type': 'GHG',
        }

        fullfact_dimensions_vectors = self.parse_dataframe_params(verbose=verbose)

        dfx = pd.DataFrame()
        dfx['Parameters'] = self.dataframe.index
        dfx.set_index('Parameters', inplace=True)
        session_params_start_index = np.where(dfx.index == 'Enable Session')[0][0]

        dfx_column_index = 0
        # for each column in dataframe, copy or expand into dfx
        for df_column_index in range(0, self.dataframe.columns.__len__()):
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
                    num_params = dfx.index.__len__()
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
                                    # print(param_name + ' has ' + str(df_ff_dimensions_vector[param_index]) + ' values ')
                                    if acronyms_dict.__contains__(value):
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + \
                                                       acronyms_dict[value]
                                    else:
                                        session_name = session_name + '-' + acronyms_dict[param_name] + '=' + str(value)
                                    # print(session_name)
                    # dfx.loc['Session Name', dfx.columns[dfx_column]] = column_name
                    dfx.loc['Session Name', column_name] = session_name
                else:  # just copy column
                    dfx[column_name] = self.dataframe.iloc[:, df_column_index]
                dfx_column_index = dfx_column_index + 1
        # dfx.fillna('-----', inplace=True)
        self.dataframe = dfx

    def get_batch_settings(self):
        self.name = self.read_parameter('Batch Name')

    def num_sessions(self):
        return len(self.dataframe.columns)

    def add_sessions(self, verbose=True):
        if verbose:
            print()
            print("In Batch '{}':".format(self.name))
        for s in range(0, self.num_sessions()):
            self.sessions.append(OMEGASessionObject("session_{%d}" % s))
            self.sessions[s].parent = self
            self.sessions[s].get_session_settings(s)
            if verbose:
                print("Found Session %s:'%s'" % (s, batch.sessions[s].name))
        if verbose:
            print()


def validate_predefined_input(input_str, valid_inputs):
    if valid_inputs.__contains__(input_str):
        if type(valid_inputs) is dict:
            return valid_inputs[input_str]
        elif type(valid_inputs) is set:
            return True
        else:
            raise Exception(
                'validate_predefined_input(...,valid_inputs) error: valid_inputs must be a set or dictionary')
    else:
        raise Exception('Invalid input "%s", expecting %s' % (input_str, str(valid_inputs)))


class OMEGASessionObject(object):
    def __init__(self, name, **kwargs):
        self.parent = []
        self.name = name
        self.num = 0
        self.output_path = ".\\"
        self.enabled = False
        self.settings = []

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
        self.output_path = self.read_parameter('Session Output Folder Name')

    def get_io_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})
        print('Getting I/O settings...')
        self.settings = OMEGARuntimeOptions()

        # setup IOSettings
        if not options.dispy:
            self.settings.output_folder = self.output_path + "\\"
        else:
            self.settings.output_folder = self.output_path + "\\" + self.name

        self.settings.session_name = self.parent.name + '_' + self.name
        self.settings.database_dump_folder = self.read_parameter('Database Dump Folder Name',
                                                                 default_value=self.settings.database_dump_folder)
        self.settings.manufacturers_file = self.read_parameter('Manufacturers File')
        self.settings.market_classes_file = self.read_parameter('Market Classes File')
        self.settings.vehicles_file = self.read_parameter('Vehicles File')
        self.settings.demanded_shares_file = self.read_parameter('Demanded Shares File')
        self.settings.fuels_file = self.read_parameter('Fuels File')
        self.settings.fuel_scenarios_file = self.read_parameter('Fuel Scenarios File')
        self.settings.fuel_scenario_annual_data_file = self.read_parameter('Fuel Scenario Annual Data File')
        if validate_predefined_input(self.read_parameter('Cost File Type'), {'clouds', 'curves'}):
            self.settings.cost_file_type = self.read_parameter('Cost File Type')
        self.settings.cost_file = self.read_parameter('Cost File')
        self.settings.ghg_standards_file = self.read_parameter('GHG Standards File')
        if validate_predefined_input(self.read_parameter('GHG Standard Type'), {'flat', 'footprint'}):
            self.settings.GHG_standard = self.read_parameter('GHG Standard Type')
        self.settings.verbose = validate_predefined_input(self.read_parameter('Verbose Output'), true_false_dict)
        self.settings.slice_tech_combo_cloud_tables = validate_predefined_input(
            self.read_parameter('Slice Tech Combo Tables'), true_false_dict)

    def get_runtime_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        print('Getting Runtime Settings...')
        if not pd.isna(self.read_parameter('Num Tech Options per Vehicle')):
            self.settings.num_tech_options_per_vehicle = int(self.read_parameter('Num Tech Options per Vehicle'))
        self.settings.allow_backsliding = validate_predefined_input(self.read_parameter('Allow Backsliding'),
                                                                    true_false_dict)
        self.settings.cost_curve_frontier_affinity_factor = self.read_parameter('Cost Curve Frontier Affinity Factor')

    def get_postproc_settings(self):
        true_false_dict = dict({True: True, False: False, 'True': True, 'False': False, 'TRUE': True, 'FALSE': False})

        print('Getting Postproc Settings...')
        if validate_predefined_input(self.read_parameter('Stock Deregistration'), {'Fixed', 'Dynamic'}):
            self.settings.stock_scrappage = self.read_parameter('Stock Deregistration')
        if validate_predefined_input(self.read_parameter('Stock VMT'), {'Fixed', 'Dynamic'}):
            self.settings.stock_vmt = self.read_parameter('Stock VMT')


    def init(self, validate_only=False):
        if not validate_only:
            print("Starting Session '%s' -> %s" % (self.name, self.output_path))
        self.get_io_settings()
        self.get_runtime_settings()
        self.get_postproc_settings()

    def run(self):
        self.init()

        print("Starting Compliance Run...")
        run_omega(self.settings)
        # self.monitor()


def validate_file(filename):
    if not os.access(filename, os.F_OK):
        print("\n*** Couldn't access {}, check path and filename ***".format(filename), file=sys.stderr)
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        sys.exit(-1)


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


def get_basename(filename):
    return os.path.basename(filename)


# returns name of file including extension, e.g. /somepath/somefile.txt -> somefile.txt
def get_filenameext(filename):
    return os.path.split(filename)[1]


def network_copyfile(remote_path, srcfile):
    dstfile = remote_path + os.sep + get_basename(srcfile)
    shutil.copyfile(srcfile, dstfile)


# move file out to shared directory and return the filename in that remote context
def relocate_file(remote_path, local_filename):
    network_copyfile(remote_path, local_filename)
    return get_basename(local_filename)


def sysprint(str):
    import os
    os.system('echo {}'.format(str))


def dispy_node_setup():
    import socket
    sysprint('node {} standing by...'.format(socket.gethostbyname(socket.gethostname())))
    sysprint('.')
    return None


def restart_job(job):
    dispy_debug = options.dispy_debug

    job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
        job.id['session_num'])

    if retry_count.__contains__(str(job.id)):
        retry_count[str(job.id)] += 1
    else:
        retry_count[str(job.id)] = 0

    if retry_count[str(job.id)] <= 10:
        if dispy_debug:
            sysprint('#### Retrying job %s ####\n' % job_id_str)
        new_job = dispycluster.cluster.submit(job.id['batch_name'], job.id['batch_path'], job.id['batch_file'],
                                              job.id['session_num'], job.id['session_name'])
        if new_job is not None:
            new_job.id = job.id
            retry_count[str(job.id)] += 1
            if dispy_debug:
                sysprint('#### Terminated job restarted %s ####\n' % job_id_str)
    else:  # too many retries, abandon job
        if dispy_debug:
            sysprint('#### Cancelling job %s, too many retry attempts ####\n' % job_id_str)


def job_cb(job):  # gets called for: (DispyJob.Finished, DispyJob.Terminated, DispyJob.Abandoned)
    import dispy
    dispy_debug = options.dispy_debug

    if job is not None:
        job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
            job.id['session_num'])
    else:
        job_id_str = 'NONE'

    status = job.status

    if status == dispy.DispyJob.Finished:
        if dispy_debug:
            sysprint('---- Job Finished %s: %s\n' % (job_id_str, job.result))
        if job.result is False:
            restart_job(job)

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug:
            sysprint('---- Job Terminated %s \n' % str(job_id_str))
        restart_job(job)

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug:
            sysprint('---- Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        restart_job(job)

    else:
        if dispy_debug:
            sysprint('*** uncaught job callback %s %s ***\n' % (job_id_str, status))


# 'cluster_status' callback function. It is called by dispy (client)
# to indicate node / job status changes.
def status_cb(status, node, job):
    import dispy

    dispy_debug = options.dispy_debug

    # job comes in as an int before the job.id is initialized
    if job:
        try:
            job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + \
                         ': #' + str(job.id['session_num'])
        except:
            # sysprint('#### job_id object FAIL ### "%s"\n' % str(job)) # not really a fail
            job_id_str = str(job.id)
            pass
    else:
        job_id_str = 'NONE'

    if status == dispy.DispyJob.Created:
        if dispy_debug:
            sysprint('++++ Job Created, Job ID %s\n' % job_id_str)

    elif status == dispy.DispyJob.Running:
        if dispy_debug:
            sysprint('++++ Job Running, Job ID %s\n' % job_id_str)

    elif status == dispy.DispyJob.Finished:
        if dispy_debug:
            sysprint('++++ status_cb Job Finished %s: %s\n' % (job_id_str, job.result))
        return

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug:
            sysprint('++++ status_cb Job Terminated %s\n' % job_id_str)
        return

    elif status == dispy.DispyJob.Cancelled:
        if dispy_debug:
            sysprint('++++ Job Cancelled %s : Exception %s\n' % (job_id_str, job.exception))

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug:
            sysprint('++++ status_cb Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        return

    elif status == dispy.DispyJob.ProvisionalResult:
        return

    elif status == dispy.DispyNode.Initialized:
        if dispy_debug:
            sysprint('++++ Node %s with %s CPUs available\n' % (node.ip_addr, node.avail_cpus))

    elif status == dispy.DispyNode.Closed:
        if dispy_debug:
            sysprint('++++ Node Closed %s *** \n' % node.ip_addr)

    elif status == dispy.DispyNode.AvailInfo:
        if dispy_debug:
            sysprint('++++ Node Available %s *** \n' % node.ip_addr)

    else:
        if node is not None:
            if dispy_debug:
                sysprint('++++ uncaught node status %s %s ***\n' % (node.ip_addr, status))
        else:
            if dispy_debug:
                sysprint('++++ uncaught job status %s %s ***\n' % (job.id, status))


def dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=0):
    import sys, subprocess
    # call shell command
    pythonpath = sys.exec_prefix
    if 'env' in pythonpath:
        pythonpath = pythonpath + "\\scripts"
    cmd = '{}\\python "{}\\{}\\usepa_omega2\\run_omega_batch.py" --bundle_path "{}" \
            --batch_file "{}.csv" --session_num {} --no_validate --no_bundle'.format(
        pythonpath, network_batch_path_root, batch_name, network_batch_path_root, batch_file, session_num)
    sysprint('.')
    sysprint(cmd)
    sysprint('.')

    subprocess.call(cmd)

    summary_filename = os.path.join(network_batch_path_root, batch_name, session_name, 'output', 'o2log_%s_%s.txt' % (batch_name, session_name))
    sysprint('SFN=%s' % summary_filename)

    time.sleep(1)  # wait for summary file to finish writing?

    if os.path.exists(summary_filename) and os.path.getsize(summary_filename) > 0:
        f_read = open(summary_filename, "r")
        last_line = f_read.readlines()[-1]
        f_read.close()
        batch_path = os.path.join(network_batch_path_root, batch_name)
        if last_line.__contains__('Session Complete'):
            os.rename(os.path.join(batch_path, session_name), os.path.join(batch_path, '_' + session_name))
            sysprint('$$$ dispy_run_session Completed, Session %s $$$' % session_name)
            return True
        elif last_line.__contains__('Session Fail'):
            os.rename(os.path.join(batch_path, session_name), os.path.join(batch_path, '#FAIL_' + session_name))
            sysprint('?!? dispy_run_session Failed, Session %s ?!?' % session_name)
            return False
        else:
            sysprint('??? Weird Summary File for Session %s : last_line = "%s" ???' % (session_name, last_line))
            return False
    else:
        sysprint('??? No Summary File for Session %s, path_exists=%d, non_zero=%d ???' % (
            session_name, os.path.exists(summary_filename), os.path.getsize(summary_filename) > 0))
        if retry_count < 3:
            sysprint('@@@ Trying Session %s again (attempt %d)... @@@' % (session_name, retry_count + 1))
            dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name,
                              retry_count=retry_count + 1)
        else:
            sysprint('!!! Abandoning Session %s... !!!' % session_name)
        return False


class DispyCluster(object):
    def __init__(self, scheduler):
        import dispy
        self.master_ip = ''
        self.desired_node_list = []
        self.found_node_list = []
        self.sleep_time_secs = 3
        if scheduler is not None:
            self.scheduler_node = scheduler
        else:
            # self.scheduler_node = '204.47.182.182'
            self.scheduler_node = '204.47.184.69'
        if options.dispy_debug:
            self.loglevel = dispy.logger.DEBUG
        else:
            self.loglevel = dispy.logger.INFO
        self.total_cpus = 0
        self.cluster = None

    def find_nodes(self):
        import dispy, socket, time

        print("Finding dispynodes...")
        self.master_ip = socket.gethostbyname(socket.gethostname())
        if not options.local and (options.dispy_ping or options.network):
            self.desired_node_list = ['204.47.184.69', '204.47.184.60', '204.47.184.72', '204.47.184.63',
                                      '204.47.184.59']
        elif options.local:
            self.desired_node_list = self.master_ip  # for local run
        else:
            self.desired_node_list = []  # to auto-discover nodes, only seems to find the local node

        if options.dispy_exclusive:
            print('Starting JobCluster...')
            cluster = dispy.JobCluster(dispy_node_setup, nodes=self.desired_node_list,
                                       pulse_interval=60, reentrant=True,
                                       ping_interval=10, loglevel=self.loglevel, depends=[sysprint])

        else:
            print('Starting SharedJobCluster...')
            cluster = dispy.SharedJobCluster(dispy_node_setup, nodes=self.desired_node_list, ip_addr=self.master_ip,
                                             reentrant=True,
                                             loglevel=self.loglevel, depends=[sysprint],
                                             scheduler_node=self.scheduler_node)

        # need to wait for cluster to startup and transfer dependencies to nodes...
        t = 0
        while t < self.sleep_time_secs:
            print('t minus ' + str(self.sleep_time_secs - t))
            time.sleep(1)
            t = t + 1

        info_jobs = []
        self.found_node_list = []
        node_info = cluster.status()
        for node in node_info.nodes:
            self.total_cpus = self.total_cpus + node.cpus
            print('Submitting %s' % node.ip_addr)
            job = cluster.submit_node(node)
            if job is not None:
                job.id = node.ip_addr
                info_jobs.append(job)
                self.found_node_list.append(node.ip_addr)

        if self.found_node_list == []:
            print('No dispy nodes found, exiting...', file=sys.stderr)
            sys.exit(-1)  # exit, no nodes found

        print('Found Node List: %s' % self.found_node_list)
        print('Found %d cpus' % self.total_cpus)

        cluster.wait()
        cluster.print_status()
        cluster.shutdown()

    def submit_sessions(self, batch_name, batch_path, batch_file, session_list):
        import dispy, socket, time, usepa_omega2

        if options.dispy_exclusive:
            print('Starting JobCluster...')
            self.cluster = dispy.JobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip,
                                            pulse_interval=60, reentrant=True,
                                            ping_interval=10, loglevel=self.loglevel, depends=[sysprint],
                                            cluster_status=status_cb, callback=job_cb)
        else:
            print('Starting SharedJobCluster...')
            self.cluster = dispy.SharedJobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip,
                                                  reentrant=True,
                                                  loglevel=self.loglevel, depends=[sysprint],
                                                  scheduler_node=self.scheduler_node, cluster_status=status_cb,
                                                  callback=job_cb)

        time.sleep(self.sleep_time_secs)  # need to wait for cluster to startup and transfer dependencies to nodes...

        # process sessions:
        session_jobs = []
        for session_num in session_list:
            print("Processing Session %d: " % session_num, end='')
            if not batch.sessions[session_num].enabled:
                print("Skipping Disabled Session '%s'" % batch.sessions[session_num].name)
                # print('')
            else:
                print("Submitting Session '%s' to Cluster..." % batch.sessions[session_num].name)
                # print('')
                job = self.cluster.submit(batch_name, batch_path, batch_file, session_num,
                                          batch.sessions[session_num].name)
                if job is not None:
                    # job.id = (batch_name, batch_path, batch_file, session_num, batch.sessions[session_num].name)
                    job.id = dict({'batch_name': batch_name, 'batch_path': batch_path, 'batch_file': batch_file,
                                   'session_num': session_num, 'session_name': batch.sessions[session_num].name})
                    session_jobs.append(job)
                else:
                    print('*** Job Submit Failed %s ***' % str(job.id), file=sys.stderr)

        print('Waiting for cluster to run sessions...')

        self.cluster.wait()
        self.cluster.print_status()
        self.cluster.shutdown()


class runtime_options(object):
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
        self.session_num = []
        self.no_bundle = False
        self.verbose = False
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
        parser.add_argument('--dispy', action='store_true', help='True = run sessions on dispynode(s)')
        parser.add_argument('--dispy_ping', action='store_true', help='True = ping dispynode(s)')
        parser.add_argument('--dispy_debug', action='store_true', help='True = enable verbose dispy debug messages)')
        parser.add_argument('--dispy_exclusive', action='store_true', help='Run exclusive job, do not share dispynodes')
        parser.add_argument('--dispy_scheduler', type=str, help='Override default dispy scheduler IP address', default=None)

        group = parser.add_mutually_exclusive_group()
        group.add_argument('--local', action='store_true', help='Run only on local machine, no network nodes')
        group.add_argument('--network', action='store_true', help='Run on local machine and/or network nodes')

        args = parser.parse_args()

        options = runtime_options()
        options.validate_batch = not args.no_validate
        options.no_sim = args.no_sim
        options.bundle_path_root = args.bundle_path
        options.batch_file = args.batch_file
        options.session_num = args.session_num
        options.no_bundle = args.no_bundle # or args.dispy # or (options.bundle_path_root is not None)
        options.verbose = args.verbose
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
        from usepa_omega2.file_eye_oh import gui_comm

        # get batch info
        import socket, shutil
        import pandas as pd
        from datetime import datetime
        import numpy as np

        if options.dispy_ping:
            dispycluster = DispyCluster(options.dispy_scheduler)
            dispycluster.find_nodes()
            print("*** ping complete ***")
        else:
            batch = OMEGABatchObject()
            if options.batch_file.__contains__('.csv'):
                batch.dataframe = pd.read_csv(options.batch_file, index_col=0)
            else:
                batch.dataframe = pd.read_excel(options.batch_file, index_col=0, sheet_name="Sessions")
            batch.dataframe.replace(to_replace={'True': True, 'False': False, 'TRUE': True, 'FALSE': False}, inplace=True)
            batch.dataframe.drop('Type', axis=1, inplace=True,
                                 errors='ignore')  # drop Type column, no error if it's not there
            batch.expand_dataframe(verbose=options.verbose)
            batch.force_numeric_params()
            batch.get_batch_settings()
            batch.add_sessions(verbose=options.verbose)

            import copy

            expanded_batch = copy.deepcopy(batch)
            expanded_batch.name = os.path.splitext(os.path.basename(options.batch_file))[0] + '_expanded' + \
                os.path.splitext(options.batch_file)[1]

            if not options.no_bundle:
                batch.dataframe.loc['Batch Name'][0] = batch.name = datetime.now().strftime(
                    "%Y_%m_%d_%H_%M_%S_") + batch.name

            # validate session files
            validate_folder(options.bundle_path_root)
            options.batch_path = validate_folder(options.bundle_path_root, batch_name=batch.name)

            if options.validate_batch:
                # validate shared (batch) files
                validate_file(options.batch_file)

                sys.path.insert(0, os.getcwd())

                for s in range(0, batch.num_sessions()):
                    session = batch.sessions[s]
                    print("\nValidating Session %d ('%s') Files..." % (s, session.name))

                    # automatically validate files and folders based on parameter naming convention
                    for i in batch.dataframe.index:
                        if options.verbose and (str(i).endswith(' Folder Name') or str(i).endswith(' File')):
                            print('validating %s=%s' % (i, session.read_parameter(i)))
                        if str(i).endswith(' Folder Name'):
                            validate_folder(session.read_parameter(i))
                        elif str(i).endswith(' File'):
                            validate_file(session.read_parameter(i))

                    print('Validating Session %d Parameters...' % s)
                    session.init(validate_only=True)

            print("\n*** validation complete ***")

            # copy files to network_batch_path
            if not options.no_bundle:
                print('Bundling Source File...')
                # copy this file to batch folder
                # relocate_file(options.batch_path, __file__)

                source_files = [fn for fn in os.listdir('usepa_omega2') if '.py' in fn]
                validate_folder(options.batch_path + 'usepa_omega2/')
                for f in source_files:
                    relocate_file(options.batch_path + 'usepa_omega2/', 'usepa_omega2/' + f)

                source_files = [fn for fn in os.listdir('usepa_omega2/consumer') if '.py' in fn]
                validate_folder(options.batch_path + 'usepa_omega2/consumer/')
                for f in source_files:
                    relocate_file(options.batch_path + 'usepa_omega2/consumer/', 'usepa_omega2/consumer/' + f)

                # write a copy of the expanded, validated batch to the source batch_file directory:
                if options.batch_file.__contains__('.csv'):
                    expanded_batch.dataframe.to_csv(os.path.dirname(options.batch_file) + '\\' + expanded_batch.name)
                else:
                    expanded_batch.dataframe.to_excel(os.path.dirname(options.batch_file) + '\\' + expanded_batch.name,
                                                      "Sessions")

                # copy session inputs to session folder(s) for active session(s)
                for s in range(0, batch.num_sessions()):
                    if batch.sessions[s].enabled:
                        print('Bundling Session %d Files...' % s)
                        session = batch.sessions[s]
                        options.session_path = validate_folder(options.bundle_path_root, batch_name=batch.name,
                                                               session_name=session.name)

                        # indicate source batch
                        if ':' in args.batch_file:
                            # batch file path is absolute
                            batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % args.batch_file
                        else:
                            # batch file path is relative
                            batch.dataframe.loc['Batch Settings'][0] = 'FROM %s' % (os.getcwd() + os.sep + args.batch_file)

                        # automatically rename and relocate source files
                        for i in batch.dataframe.index:
                            if str(i).endswith(' Folder Name'):
                                if options.verbose:
                                    print('renaming %s to %s' % (batch.dataframe.loc[i][session.num],
                                                                 session.name + os.sep + batch.dataframe.loc[i][
                                                                     session.num]))
                                batch.dataframe.loc[i][session.num] = \
                                    session.name + os.sep + batch.dataframe.loc[i][session.num]
                            elif str(i).endswith(' File'):
                                if options.verbose:
                                    print('relocating %s to %s' % (batch.dataframe.loc[i][session.num],
                                                                   options.session_path + session.read_parameter(i)))
                                batch.dataframe.loc[i][session.num] = \
                                    session.name + os.sep + relocate_file(options.session_path, session.read_parameter(i))

            import time

            time.sleep(5)  # was 10, wait for files to fully transfer...

            os.chdir(options.batch_path)

            remote_batchfile = batch.name + '.csv'
            batch.dataframe.to_csv(remote_batchfile)

            print("Batch name = " + batch.name)

            if options.session_num is None:
                session_list = range(0, batch.num_sessions())
            else:
                session_list = [options.session_num]

            if not options.no_sim:
                if options.dispy:  # run remote job on cluster
                    retry_count = dict()  # track retry attempts for terminated or abandoned jobs

                    dispycluster = DispyCluster(options.dispy_scheduler)
                    dispycluster.find_nodes()
                    dispycluster.submit_sessions(batch.name, options.bundle_path_root, options.batch_path + batch.name,
                                                 session_list)
                    print("*** batch complete ***")
                else:  # run from here
                    batch = OMEGABatchObject()
                    print('REMOTE BATCHFILE = %s' % remote_batchfile)
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
                        print("Processing Session %d:" % s_index, end='')
                        gui_comm("Running Session " + str(s_index + 1) + ' of ' + str(batch.num_sessions()) + '...')

                        if not batch.sessions[s_index].enabled:
                            print("Skipping Disabled Session '%s'" % batch.sessions[s_index].name)
                            print('')
                        else:
                            batch.sessions[s_index].run()

    except:
        print("\n#RUNTIME FAIL\n%s\n" % traceback.format_exc())
        os._exit(-1)
