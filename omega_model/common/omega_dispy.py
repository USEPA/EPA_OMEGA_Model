"""

**Routines and data structures to support multi-processor / multi-machine OMEGA simulations via the dispy package.**

Generally speaking, running with ``dispy`` is a bit of an advanced topic, and is not required in order to run a
multi-session batch.  When getting started with ``dispy`` it's best to get started on a single machine before
working up to a multi-machine setup.

To run using ``dispy``, each machine must have a running instance of ``dispynode``, typically launched from a command
line script.  Also, each machine must have access to a shared folder where the source files for each
run will be staged.

Example:

    ::

        #! /bin/zsh

        PYTHONPATH="/Users/omega_user/Code/GitHub/USEPA_OMEGA2/venv3.8/bin"
        DISPYPATH="/Users/omega_user/Code/GitHub/USEPA_OMEGA2/venv3.8/lib/python3.8/site-packages/dispy"

        $PYTHONPATH/python3 $DISPYPATH/dispynode.py --clean --cpus=8 --client_shutdown --ping_interval=15 --daemon --zombie_interval=5


----

Since this is an advanced use case, EPA can provide limited support for its use.

**CODE**

"""

from common import omega_log

from omega_model import OMEGASessionSettings
bundle_output_folder_name = OMEGASessionSettings().output_folder
MsgTimeout = 120

print('importing %s' % __file__)


def sysprint(message):
    """
    Echo/print a message to the system standard output (i.e. the console)

    Args:
        message (str): the message to print

    """
    import os
    os.system('echo "%s"' % message)


def dispy_node_setup():
    """
    Prints a short hello message to the console, verifying that the dispynode is up and running (used during ping mode).

    """
    import socket
    sysprint('node %s standing by...' % str(socket.gethostbyname_ex(socket.gethostname())))
    sysprint('.')


_retry_count = dict()  # track retry attempts for terminated or abandoned jobs


def restart_job(job):
    """
    Restart an abandonded or failed DispyJob.

    Args:
        job (DispyJob): the job to restart

    """
    import os
    global dispycluster
    global dispy_debug

    job_id_str = job.id['batch_path'] + os.sep + job.id['batch_name'] + os.sep + job.id['session_name'] + ': #' + str(
        job.id['session_num'])

    if _retry_count.__contains__(str(job.id)):
        _retry_count[str(job.id)] += 1
    else:
        _retry_count[str(job.id)] = 0

    if _retry_count[str(job.id)] <= 10:
        if dispy_debug:
            sysprint('#### Retrying job %s ####\n' % job_id_str)
        new_job = dispycluster.cluster.submit(job.id['batch_name'], job.id['batch_path'], job.id['batch_file'],
                                              job.id['session_num'], job.id['session_name'])
        if new_job is not None:
            new_job.id = job.id
            _retry_count[str(job.id)] += 1
            if dispy_debug:
                sysprint('#### Terminated job restarted %s ####\n' % job_id_str)
    else:  # too many retries, abandon job
        if dispy_debug:
            sysprint('#### Cancelling job %s, too many retry attempts ####\n' % job_id_str)


def job_cb(job):  # gets called for: (DispyJob.Finished, DispyJob.Terminated, DispyJob.Abandoned)
    """
    Job callback function.  Gets called for: (DispyJob.Finished, DispyJob.Terminated, DispyJob.Abandoned)

    Args:
        job (DispyJob): the job associated with the callback

    """
    import os
    import dispy
    global dispy_debug

    if job is not None:
        job_id_str = job.id['batch_path'] + os.sep + job.id['batch_name'] + os.sep + job.id[
            'session_name'] + ': #' + str(
            job.id['session_num'])
    else:
        job_id_str = 'NONE'

    status = job.status

    if status == dispy.DispyJob.Finished:
        if dispy_debug:
            sysprint('---- Job Finished %s: %s\n' % (job_id_str, job.result))
        # if job.result is False:
        #     restart_job(job)

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug:
            sysprint('---- Job Terminated %s job exeption = %s\n' % (str(job_id_str), str(job.exception)))
        # restart_job(job)

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug:
            sysprint('---- Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        # restart_job(job)

    else:
        if dispy_debug:
            sysprint('*** uncaught job callback %s %s ***\n' % (job_id_str, status))

    return


def status_cb(status, node, job):
    """
    Cluster status callback function.  It is called by ``dispy`` (client) to indicate node / job status changes.

    Args:
        status: job status (e.g. dispy.DispyJob.Created, dispy.DispyJob.Running, etc)
        node (DispyNode, IP address, or host name): the node associated with the cluster
        job (DispyJob): the job associated with the callback

    """
    import os
    import dispy
    global dispy_debug

    # job comes in as an int before the job.id is initialized
    if job is not None:
        try:
            job_id_str = job.id['batch_path'] + os.sep + job.id['batch_name'] + os.sep + job.id[
                'session_name'] + ': #' + str(
                job.id['session_num'])
        except:
            job_id_str = str(job.id)
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
        # if dispy_debug: sysprint('++++ Node Available %s *** \n' % node.ip_addr)
        pass
    else:
        if node is not None:
            if dispy_debug:
                sysprint('++++ uncaught node status %s %s ***\n' % (node.ip_addr, status))
        else:
            if dispy_debug:
                sysprint('++++ uncaught job status %s %s ***\n' % (job.id, status))
    return


def dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=0):
    """
    Runs an OMEGA simulation session on a DispyNode.

    Args:
        batch_name (str): the name of the batch
        network_batch_path_root (str): name/path to a shared folder where the source files will be staged
        batch_file (str): path to the batch file being run
        session_num (int): the session number to be run
        session_name (str): the name of the session being run
        retry_count (int): retry count of the session

    """
    import sys, subprocess, os, time
    # build shell command
    cmd = '"{}" "{}/{}/omega_model/omega_batch.py" --bundle_path "{}" \
            --batch_file "{}.csv" --session_num {} --no_validate --no_bundle'.format(
        sys.executable, network_batch_path_root, batch_name, network_batch_path_root, batch_file, session_num,
        ).replace('/', os.sep)

    sysprint('.')
    sysprint(cmd)
    sysprint('.')

    # run shell command
    subprocess.call(cmd, shell=True)

    no_result_foldername = os.path.join(network_batch_path_root, batch_name, session_name)
    success_foldername = os.path.join(network_batch_path_root, batch_name, '_' + session_name)
    fail_foldername = os.path.join(network_batch_path_root, batch_name, '#FAIL_' + session_name)
    weird_foldername = os.path.join(network_batch_path_root, batch_name, '#WEIRD_' + session_name)

    time.sleep(1)  # wait for summary file to finish writing?

    if os.path.exists(success_foldername):
        sysprint('::: dispy_run_session Completed, Session "%s" :::' % session_name)
    elif os.path.exists(fail_foldername):
        sysprint('?!? dispy_run_session Failed, Session "%s" ?!?' % session_name)
    elif os.path.exists(weird_foldername):
        logfilename = os.path.join(weird_foldername, bundle_output_folder_name,
                                   'o2log_%s_%s.txt' % (batch_name, session_name))
        with open(logfilename, "r") as f_read:
            last_line = f_read.readlines()[-1]
        sysprint('??? Weird Log File for Session "%s" : last_line = "%s" ???' % (session_name, last_line))
    elif os.path.exists(no_result_foldername):
        if retry_count < 3:
            sysprint('@@@ Trying Session "%s" again (attempt %d)... @@@' % (session_name, retry_count + 1))
            dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name,
                              retry_count=retry_count + 1)
        else:
            sysprint('!!! Abandoning Session "%s"... !!!' % session_name)


dispy_debug = None
dispycluster = None


class DispyCluster(object):
    """
    Implements an object to run OMEGA sessions on dispy nodes.

    """
    def __init__(self, options):
        """
        Create a  DispyCluster object with the provided batch options.

        Args:
            options (OMEGABatchOptions): batch options, see ``omega_batch.py`` for more info

        """
        import dispy

        dispy.config.MsgTimeout = MsgTimeout

        self.master_ip = ''
        self.desired_node_list = []
        self.found_node_list = []
        self.sleep_time_secs = 3
        self.options = options

        if options.dispy_scheduler is not None:
            self.scheduler_node = options.dispy_scheduler
        else:
            # self.scheduler_node = '204.47.182.182'
            self.scheduler_node = '204.47.184.69'
        if self.options.dispy_debug:
            self.loglevel = dispy.logger.DEBUG
        else:
            self.loglevel = dispy.logger.INFO

        global dispy_debug
        dispy_debug = self.loglevel
        self.total_cpus = 0
        self.cluster = None

        global dispycluster
        dispycluster = self

    @staticmethod
    def get_ip_address():
        """
        Attempt to get "local" IP address(es)
        
        Example:

        ::
            
            >>> socket.gethostbyname_ex(socket.gethostname())
            ('mac-mini.local', [], ['127.0.0.1', '192.168.1.20'])
        
        Returns: list of local IP address(es)

        """
        import socket

        my_ip = []

        retries = 0
        ip_found = False
        while not ip_found and retries < 10:
            try:
                my_ip = socket.gethostbyname_ex(socket.gethostname())[2]
                ip_found = True
            except:
                retries += 1

        if not my_ip.count('127.0.0.1'):
            my_ip.append('127.0.0.1')  # Add support for local loopback interface

        return my_ip

    def find_nodes(self):
        """
        Look for available DispyNodes and update ``self.found_node_list`` with a list of the discovered nodes.

        """
        import dispy, time, sys

        print("Finding dispynodes...")
        self.master_ip = self.get_ip_address()
        print('Master IP = %s' % self.master_ip)
        if not self.options.local and (self.options.dispy_ping or self.options.network):
            self.desired_node_list = []
        elif self.options.local:
            self.desired_node_list = self.master_ip  # for local run
        else:
            self.desired_node_list = []  # to auto-discover nodes, only seems to find the local node

        if self.options.dispy_exclusive:
            print('Starting JobCluster...')
            cluster = dispy.JobCluster(dispy_node_setup, nodes=self.desired_node_list,
                                       pulse_interval=60, reentrant=True,
                                       ping_interval=10, loglevel=self.loglevel, depends=[sysprint])

        else:
            print('Starting SharedJobCluster...')
            if dispy.__version__ == '4.12.4':
                cluster = dispy.SharedJobCluster(dispy_node_setup, nodes=self.desired_node_list, client_port=0,
                                             reentrant=True,
                                             loglevel=self.loglevel, depends=[sysprint],
                                             scheduler_node=self.scheduler_node)
            else:
                cluster = dispy.SharedJobCluster(dispy_node_setup, nodes=self.desired_node_list, client_port=0,
                                             reentrant=True,
                                             loglevel=self.loglevel, depends=[sysprint],
                                             scheduler_host=self.scheduler_node)

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

        if not self.found_node_list:
            print('No dispy nodes found, exiting...', file=sys.stderr)
            omega_log.logwrite('ERROR - No Multiprocessor nodes found, exiting...')
            sys.exit(-1)  # exit, no nodes found

        print('Found Node List: %s' % self.found_node_list)
        print('Found %d cpus' % self.total_cpus)

        cluster.wait()
        cluster.print_status()
        cluster.shutdown()

    def submit_sessions(self, batch, batch_name, batch_path, batch_file, session_list):
        """
        Submit sessions to a DispyCluster.  Called from ``omega_batch.py``.

        Args:
            batch (OMEGABatchObject): the batch object, see ``omega_batch.py``
            batch_name (str): the name of the batch, e.g. '2021_06_29_13_34_44_multiple_session_batch'
            batch_path (str): the filesystem path to the bundle folder for the batch, e.g. '/Users/omega_user/bundle'
            batch_file (str): the filesystem path to the batch file to run (minus the '.csv' extension),
                e.g. '/Users/omega_user/bundle/2021_06_29_13_34_44_batch/2021_06_29_13_34_44_batch'
            session_list (iterable): a list or range of one or more sessions to run, by session number, e.g. range(1, 3)

        """
        import dispy, time, sys

        if self.options.dispy_exclusive:
            print('Starting JobCluster...')
            self.cluster = dispy.JobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip,
                                            pulse_interval=60, reentrant=True,
                                            ping_interval=10, loglevel=self.loglevel, depends=[sysprint],
                                            cluster_status=status_cb, callback=job_cb)
        else:
            print('Starting SharedJobCluster...')
            if dispy.__version__ == '4.12.4':
                self.cluster = dispy.SharedJobCluster(dispy_run_session, nodes=self.found_node_list, client_port=0,
                                                      reentrant=True,
                                                      loglevel=self.loglevel, depends=[sysprint],
                                                      scheduler_node=self.scheduler_node, cluster_status=status_cb,
                                                      callback=job_cb)
            else:
                self.cluster = dispy.SharedJobCluster(dispy_run_session, nodes=self.found_node_list, client_port=0,
                                                      reentrant=True,
                                                      loglevel=self.loglevel, depends=[sysprint],
                                                      scheduler_host=self.scheduler_node, cluster_status=status_cb,
                                                      job_status=job_cb)

        time.sleep(self.sleep_time_secs)  # need to wait for cluster to startup and transfer dependencies to nodes...

        # process sessions:
        session_jobs = []
        for session_num in session_list:
            print("Processing Session %d: " % session_num, end='')
            if not batch.sessions[session_num].enabled:
                print("Skipping Disabled Session '%s'" % batch.sessions[session_num].name)
            else:
                print("Submitting Session '%s' to Cluster..." % batch.sessions[session_num].name)
                job = self.cluster.submit(batch_name, batch_path, batch_file, session_num,
                                          batch.sessions[session_num].name)
                if job is not None:
                    job.id = dict({'batch_name': batch_name, 'batch_path': batch_path, 'batch_file': batch_file,
                                   'session_num': session_num, 'session_name': batch.sessions[session_num].name})
                    session_jobs.append(job)
                else:
                    print('*** Job Submit Failed %s ***' % str(job.id), file=sys.stderr)

        print('Waiting for cluster to run sessions...')

        self.cluster.wait()
        self.cluster.print_status()
        self.cluster.shutdown()
