"""
placeholder, for now, but the dispy stuff should not really be in the run_omega_batch.py...
"""


def sysprint(str):
    import os
    os.system('echo {}'.format(str))


def dispy_node_setup():
    import socket
    sysprint('node {} standing by...'.format(socket.gethostbyname(socket.gethostname())))
    sysprint('.')


retry_count = dict()    # track retry attempts for terminated or abandoned jobs


def restart_job(job):
    global options, dispycluster

    dispy_debug = options.dispy_debug

    job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
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
    import dispy
    dispy_debug = options.dispy_debug

    if job is not None:
        job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
            job.id['session_num'])
    else:
        job_id_str = 'NONE'

    status = job.status

    if status == dispy.DispyJob.Finished:
        if dispy_debug: sysprint('---- Job Finished %s: %s\n' % (job_id_str, job.result))
        if job.result is False:
            restart_job(job)

    elif status == dispy.DispyJob.Terminated:
        if dispy_debug: sysprint('---- Job Terminated %s \n' % str(job_id_str))
        restart_job(job)

    elif status == dispy.DispyJob.Abandoned:
        if dispy_debug: sysprint('---- Job Abandoned %s : Exception %s\n' % (job_id_str, job.exception))
        restart_job(job)

    else:
        if dispy_debug: sysprint('*** uncaught job callback %s %s ***\n' % (job_id_str, status))

    return


# 'cluster_status' callback function. It is called by dispy (client)
# to indicate node / job status changes.
def status_cb(status, node, job):
    # global sim_jobs, terminated_jobs, retry_count, config_case, minimum_batch_size, found_node_list, found_node_matlabs, dispy_debug
    import dispy

    dispy_debug = options.dispy_debug

    # SOMETIMES job comes in as an "int" instead of an object, then it throws an error here... not sure why!
    # SEEMS to be associated with those jobs that run fine but don't finish by adding the "_"
    # NOT all jobs have this problem... keep an eye on this and see if we have the same problem in the cluster...
    if job is not None:
        try:
            job_id_str = job.id['batch_path'] + '\\' + job.id['batch_name'] + '\\' + job.id['session_name'] + ': #' + str(
                job.id['session_num'])
        except:
            sysprint('#### job_id object FAIL ### "%s"\n' % str(job))
            job_id_str = str(job)
            pass
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
        if dispy_debug: sysprint('++++ Node Available %s *** \n' % node.ip_addr)

    else:
        if node is not None:
            if dispy_debug: sysprint('++++ uncaught node status %s %s ***\n' % (node.ip_addr, status))
        else:
            if dispy_debug: sysprint('++++ uncaught job status %s %s ***\n' % (job.id, status))
    return


def dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=0):
    import sys, subprocess
    #call shell command
    pythonpath = sys.exec_prefix
    if pythonpath.__contains__('envs'):
        pythonpath = pythonpath + "\\scripts"
    cmd = '{}\\python "{}\\{}\\run_dse2_batch.py" --bundle_path "{}" --batch_file "{}.csv" --session_num {} --no_validate'.format(pythonpath, network_batch_path_root, batch_name, network_batch_path_root, batch_file, session_num)
    sysprint('.')
    sysprint(cmd)
    sysprint('.')
    subprocess.call(cmd)
    # remove temporary dll folder for this session:
    dllpath = "C:\\Users\\Public\\temp\\%s\\" % (batch_name + '_' + session_name)
    sysprint('Removing ' + dllpath)
    shutil.rmtree(dllpath, ignore_errors=False)

    summary_filename = os.path.join(network_batch_path_root, batch_name, session_name, 'output\\logs\\Summary.txt')

    time.sleep(5) # wait for summary file to finish writing?

    if os.path.exists(summary_filename) and os.path.getsize(summary_filename) > 0:
        f_read = open(summary_filename, "r")
        last_line = f_read.readlines()[-1]
        f_read.close()
        batch_path = os.path.join(network_batch_path_root, batch_name)
        if last_line.__contains__("Standard Compliance Model Completed"):
            os.rename(os.path.join(batch_path, session_name), os.path.join(batch_path, '_' + session_name))
            sysprint('^^^ dispy_run_session Standard Compliance Model Completed, Session %s ^^^' % session_name)
            return True
        elif last_line.__contains__("Standard Compliance Model Stopped"):
            os.rename(os.path.join(batch_path, session_name), os.path.join(batch_path, '#FAIL_' + session_name))
            sysprint('???? Standard Compliance Model Stopped, Session %s ????' % session_name)
            return False
        else:
            sysprint('???? Weird Summary File for Session %s : last_line = "%s" ????' % (session_name, last_line))
            return False
    else:
        sysprint('???? No Summary File for Session %s, path_exists=%d, non_zero=%d ????' % (session_name, os.path.exists(summary_filename), os.path.getsize(summary_filename) > 0))
        if retry_count < 3:
            sysprint('???? Trying Session %s again (attempt %d)... ????' % (session_name, retry_count+1))
            dispy_run_session(batch_name, network_batch_path_root, batch_file, session_num, session_name, retry_count=retry_count+1)
        else:
            sysprint('???? Abandoning Session %s... ????' % session_name)
        return False


class DispyCluster(object):
    def __init__(self, scheduler):
        import dispy
        self.master_ip = ''
        self.desired_node_list = []
        self.found_node_list = []
        self.sleep_time_secs = 10
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
        if options.one_ping_only or options.network:
            # self.desired_node_list = ['204.47.182.182', '204.47.182.60', '204.47.185.53', '204.47.185.67',
            #                           '204.47.184.69', '204.47.184.60', '204.47.184.72', '204.47.184.63',
            #                           '204.47.184.59']
            # self.desired_node_list = ['204.47.182.182', '204.47.182.60', '204.47.185.53', '204.47.185.67']
            self.desired_node_list = ['204.47.184.69', '204.47.184.60', '204.47.184.72', '204.47.184.63',
                                      '204.47.184.59']
        elif options.local:
            self.desired_node_list = self.master_ip  # for local run
        elif options.mazer:
            self.desired_node_list = ['172.16.24.11']
        elif options.doorlag:
            self.desired_node_list = ['172.16.28.28']
        elif options.newman40:
            self.desired_node_list = ['172.16.24.12']
        elif options.dekraker:
            self.desired_node_list = ['172.16.24.10']
        else:
            self.desired_node_list = []  # to auto-discover nodes, only seems to find the local node

        if options.exclusive:
            print('Starting JobCluster...')
            cluster = dispy.JobCluster(dispy_node_setup, nodes=self.desired_node_list, ip_addr=self.master_ip, pulse_interval=60, reentrant=True,
                                   ping_interval=10, loglevel=self.loglevel, port=0, depends=[sysprint])
        else:
            print('Starting SharedJobCluster...')
            cluster = dispy.SharedJobCluster(dispy_node_setup, nodes=self.desired_node_list, ip_addr=self.master_ip, reentrant=True,
                                   loglevel=self.loglevel, depends=[sysprint], scheduler_node=self.scheduler_node, port=0)

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
            if (job is not None):
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
        cluster.close()

    def submit_sessions(self, batch_name, batch_path, batch_file, session_list):
        import dispy, socket, time

        if options.exclusive:
            print('Starting JobCluster...')
            self.cluster = dispy.JobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip, pulse_interval=60, reentrant=True,
                                   ping_interval=10, loglevel=self.loglevel, port=0, depends=[sysprint], cluster_status=status_cb, callback=job_cb)
        else:
            print('Starting SharedJobCluster...')
            self.cluster = dispy.SharedJobCluster(dispy_run_session, nodes=self.found_node_list, ip_addr=self.master_ip, reentrant=True,
                                   loglevel=self.loglevel, depends=[sysprint], scheduler_node=self.scheduler_node, port=0, cluster_status=status_cb, callback=job_cb)

        time.sleep(self.sleep_time_secs)  # need to wait for cluster to startup and transfer dependencies to nodes...

        # process sessions:
        session_jobs = []
        for session_num in session_list:
            print("Processing Session %d: " % session_num, end='')

            if not batch.sessions[session_num].enabled:
                print("Skipping Disabled Session '%s'" % batch.sessions[session_num].name)
                #print('')
            else:
                print("Submitting Session '%s' to Cluster..." % batch.sessions[session_num].name)
                #print('')
                job = self.cluster.submit(batch_name, batch_path, batch_file, session_num, batch.sessions[session_num].name)
                if (job != None):
                    # job.id = (batch_name, batch_path, batch_file, session_num, batch.sessions[session_num].name)
                    job.id = dict({'batch_name':batch_name, 'batch_path':batch_path, 'batch_file':batch_file, 'session_num':session_num, 'session_name':batch.sessions[session_num].name})
                    session_jobs.append(job)
                else:
                    print('*** Job Submit Failed %s ***' % str(job.id), file=sys.stderr)

        print('Waiting for cluster to run sessions...')

        self.cluster.wait()
        self.cluster.print_status()
        self.cluster.close()
