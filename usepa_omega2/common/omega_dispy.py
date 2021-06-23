"""

placeholder, for now, but the dispy stuff should not really be in the omega_batch.py...


----

**CODE**

"""

from common import omega_log

from usepa_omega2 import OMEGARuntimeOptions
bundle_output_folder_name = OMEGARuntimeOptions().output_folder

print('importing %s' % __file__)


def sysprint(str):
    import os
    os.system('echo {}'.format(str))


def dispy_node_setup():
    import socket
    sysprint('node "%s" standing by...' % str(socket.gethostbyname_ex(socket.gethostname())))
    sysprint('.')


retry_count = dict()  # track retry attempts for terminated or abandoned jobs


def restart_job(job):
    import os
    global dispycluster
    global dispy_debug

    job_id_str = job.id['batch_path'] + os.sep + job.id['batch_name'] + os.sep + job.id['session_name'] + ': #' + str(
        job.id['session_num'])

    if retry_count.__contains__(str(job.id)):
        retry_count[str(job.id)] += 1
    else:
        retry_count[str(job.id)] = 0

    if retry_count[str(job.id)] <= 10:
        if dispy_debug: sysprint('#### Retrying job %s ####\n' % job_id_str)
        new_job = dispycluster.cluster.submit(job.id['batch_name'], job.id['batch_path'], job.id['batch_file'],
                                              job.id['session_num'], job.id['session_name'])
        if new_job is not None:
            new_job.id = job.id
            retry_count[str(job.id)] += 1
            if dispy_debug: sysprint('#### Terminated job restarted %s ####\n' % job_id_str)
    else:  # too many retries, abandon job
        if dispy_debug: sysprint('#### Cancelling job %s, too many retry attempts ####\n' % job_id_str)


def job_cb(job):  # gets called for: (DispyJob.Finished, DispyJob.Terminated, DispyJob.Abandoned)
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
        if dispy_debug: sysprint('---- Job Finished %s: %s\n' % (job_id_str, job.result))
        # if job.result is False:
        #     restart_job(job)

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug: sysprint('---- Job Terminated %s job exeption = %s\n' % (str(job_id_str), str(job.exception)))
        # restart_job(job)

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug: sysprint('---- Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        # restart_job(job)

    else:
        if dispy_debug: sysprint('*** uncaught job callback %s %s ***\n' % (job_id_str, status))

    return


# 'cluster_status' callback function. It is called by dispy (client)
# to indicate node / job status changes.
def status_cb(status, node, job):
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
        if dispy_debug: sysprint('++++ Job Created, Job ID %s\n' % job_id_str)

    elif status == dispy.DispyJob.Running:
        if dispy_debug: sysprint('++++ Job Running, Job ID %s\n' % job_id_str)

    elif status == dispy.DispyJob.Finished:
        if dispy_debug: sysprint('++++ status_cb Job Finished %s: %s\n' % (job_id_str, job.result))
        return

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug: sysprint('++++ status_cb Job Terminated %s\n' % job_id_str)
        return

    elif status == dispy.DispyJob.Cancelled:
        if dispy_debug: sysprint('++++ Job Cancelled %s : Exception %s\n' % (job_id_str, job.exception))

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug: sysprint('++++ status_cb Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        return

    elif status == dispy.DispyJob.ProvisionalResult:
        return

    elif status == dispy.DispyNode.Initialized:
        if dispy_debug: sysprint('++++ Node %s with %s CPUs available\n' % (node.ip_addr, node.avail_cpus))

    elif status == dispy.DispyNode.Closed:
        if dispy_debug: sysprint('++++ Node Closed %s *** \n' % node.ip_addr)

    elif status == dispy.DispyNode.AvailInfo:
        # if dispy_debug: sysprint('++++ Node Available %s *** \n' % node.ip_addr)
        pass
    else:
        if node is not None:
            if dispy_debug: sysprint('++++ uncaught node status %s %s ***\n' % (node.ip_addr, status))
        else:
            if dispy_debug: sysprint('++++ uncaught job status %s %s ***\n' % (job.id, status))
    return


def dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=0):
    import sys, subprocess, os, time
    # build shell command
    cmd = '"{}" "{}/{}/usepa_omega2/omega_batch.py" --bundle_path "{}" \
            --batch_file "{}.csv" --session_num {} --no_validate --no_bundle'.format(
        sys.executable, network_batch_path_root, batch_name, network_batch_path_root, batch_file, session_num).replace(
        '/', os.sep)

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

    return True


dispy_debug = None
dispycluster = None


class DispyCluster(object):
    def __init__(self, options):
        import dispy
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

    def get_ip_address(self):
        """
        Attempt to get "local" IP address(es)
        
        Example:

        ::
            
            >>> socket.gethostbyname_ex(socket.gethostname())
            ('kevins-mac-mini.local', [], ['127.0.0.1', '192.168.1.20'])
        
        Returns: list of local IP address(es)

        """
        import socket
        # socket.gethostbyname(socket.gethostname())
        # return socket.gethostbyname_ex(socket.gethostname())[2][-1]
        return socket.gethostbyname_ex(socket.gethostname())[2]

    def find_nodes(self):
        import dispy, time, sys

        print("Finding dispynodes...")
        self.master_ip = self.get_ip_address()
        print('Master IP = %s' % self.master_ip)
        if not self.options.local and (self.options.dispy_ping or self.options.network):
            self.desired_node_list = []  # ['204.47.184.69', '204.47.184.60', '204.47.184.72', '204.47.184.63', '204.47.184.59']
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
        import dispy, time, sys

        if self.options.dispy_exclusive:
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
