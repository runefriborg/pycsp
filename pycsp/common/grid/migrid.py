"""
This file has been based on work created by Morten A. Bentsen on 2008-10-26.

Copyright (C) 2010 Rune M. Friborg <runef@diku.dk>
"""
import os, shutil, subprocess
import time

TEMPDIR = "/tmp"

# Controls the output of debug information
PRINT_DEBUG = True
LOG_STATS = True

# can be used to configure a new location for the mig scripts.
# if this is None, we will assume that the scripts are located on the path.
SCRIPT_PATH = os.path.dirname(__file__) + "/mig-scripts"

# can be used to configure a new location for the mig configuration file
MIG_USER_CONF = None


def execute_test(session):
    exec_file = os.path.dirname(__file__) + "/exec.py"
    print session.package_file
    print exec_file
    
    shutil.copy(exec_file, TEMPDIR + "/exec.py")

    cmd = ['/usr/bin/env', 'python', 'exec.py', session.ID]
    p = subprocess.Popen(cmd, cwd=TEMPDIR)
    p.wait()


def print_debug(text, job=None):
	if PRINT_DEBUG:
		message = text
		if job != None:
			message = '[' + job.job_uid + '] ' + message
		print message	


# =======================================
# = MiG user script wrappers coming up! =
# =======================================
def __execute_mig_script(script, args,check_exitcode=False, check_nonempty=False):
	command = 'python '
	
	if SCRIPT_PATH != None:
		command += SCRIPT_PATH + '/'
		
	command += script
	
	if MIG_USER_CONF != None:
		command += ' -c ' + MIG_USER_CONF
	
	for arg in args:
		command += ' ' + arg
		
	proc = subprocess.Popen(command, shell = True, stdout = subprocess.PIPE)
	output = proc.communicate()[0]
	
	if check_exitcode:
		if output.find('Exit code:') < 0:
			print_debug('No exit_code from ' + script + ': ' + output)
		elif output.find('Exit code: 0') < 0:
			print_debug('Bad exit code from ' + script + ': ' + output)
		
	if check_nonempty and len(output) > 0:
	   print_debug('Got non-empty output from '+ script + ': ' + output)
	
	return output

# ============================
# = Wrapper for migsubmit.py =
# ============================
def migsubmit(jobfile):
	return __execute_mig_script('migsubmit.py',[jobfile])


# =========================
# = Wrapper for migput.py =
# =========================
def migput(local_src, MiG_dest):
	__execute_mig_script('migput.py',[local_src, MiG_dest],check_nonempty=True)
	
# =========================
# = Wrapper for migget.py =
# =========================
def migget(MiG_src, local_dest):
	__execute_mig_script('migget.py',[MiG_src, local_dest],check_nonempty=True)

# ============================
# = Wrapper for migstatus.py =
# ============================
def migstatus(jobid):
	return __execute_mig_script('migstatus.py',[jobid],check_exitcode=True)

# =========================
# = Wrapper for migrim.py =
# =========================
def migrm(file, recursive=False):
	args = []
	if recursive:
		args = ['-r',file]
	else:
		args = [file]
	__execute_mig_script('migrm.py',args,check_exitcode=True)

# ===========================
# = Wrapper for migmkdir.py =
# ===========================
def migmkdir(folder):
	__execute_mig_script('migmkdir.py',[folder],check_exitcode=True)	

# =========================
# = Wrapper for migcat.py =
# =========================
def migcat(file):
	return __execute_mig_script('migcat.py',[file],check_exitcode=True)

# ========================
# = Wrapper for migls.py =
# ========================
def migls(file):
	return __execute_mig_script('migls.py',[file],check_exitcode=True)


# ===========================
# = Wrapper for migtouch.py =
# ===========================
def migtouch(file):
	__execute_mig_script('migtouch.py',[file],check_exitcode=True)	

# ============================
# = Jobstate enum-like class =
# ============================
class Jobstate:
	queued, executing, finished, retry, canceled, other, failed, expired = range(8)
	def getname(state):
		if state == Jobstate.queued:
			return 'Queued'
		elif state == Jobstate.executing:
			return 'Executing'
		elif state == Jobstate.finished:
			return 'Finished'
		elif state == Jobstate.retry:
			return 'Retry'
		elif state == Jobstate.canceled:
			return 'Canceled'
		elif state == Jobstate.other:
			return 'Other'
		elif state == Jobstate.failed:
			return 'Failed'
		elif state == Jobstate.expired:
			return 'Expired'
		else:
			return 'Unknown'
	getname = staticmethod(getname)
# ============================================================
# = Class Migjob. Capable of submitting and waiting for jobs =
# ============================================================
class Migjob:
	
	# TODO throw exception if job isn't submitted.
	# TODO add support for input files and output files for the job.
	def __init__(self, command, vgrid, job_uid, temp_folder):
		self.command = command
		# TODO check for trailing '/'
		self.job_uid = job_uid
		self.job_filename = job_uid + '.mRSL'
		self.temp_folder = temp_folder
		self.vgrid = vgrid
		self.MiG_jobid = None
		self.input_files = []
		self.output_files = []
		self.env_vars = []
		self.runtime_envs =[]
		self.job_file_created = False
		self.job_submitted = False
		self.cpu_time = -1
		self.cpu_count = -1
		self.node_count = -1
		self.memory = -1
		self.disk = -1
		self.arch = None
                self.resources = None
		self.log = {}		
	
	# TODO handle file exception
	def __create_jobfile(self):
		file_contents = '::EXECUTE::\n'
		file_contents += self.command + '\n\n'
	
		file_contents += '::INPUTFILES::\n'
		for MiG_path in self.input_files:
			file_contents += MiG_path +'\n'
		file_contents += '\n'
		
		file_contents += '::OUTPUTFILES::\n'
		for MiG_path in self.output_files:
			file_contents += MiG_path + '\n'
		file_contents += '\n'
		
		file_contents += '::RUNTIMEENVIRONMENT::\n'
		for run_env in self.runtime_envs:
			file_contents += run_env + '\n'
		file_contents += '\n'
		
		file_contents += '::ENVIRONMENT::\n'
		for name,value in self.env_vars:
			file_contents += name + '=' + value + '\n'
		file_contents += '\n'
				
		file_contents += '::VGRID::\n'+self.vgrid+'\n\n'		
			
		if self.cpu_time > 0:
			file_contents += '::CPUTIME::\n' + str(self.cpu_time) + '\n\n'	

		if self.cpu_count > 0:
			file_contents += '::CPUCOUNT::\n' + str(self.cpu_count) + '\n\n'	

		if self.node_count > 0:
			file_contents += '::NODECOUNT::\n' + str(self.node_count) + '\n\n'	
			
		if self.memory > 0:
			file_contents += '::MEMORY::\n' + str(self.memory) + '\n\n'	

		if self.disk > 0:
			file_contents += '::DISK::\n' + str(self.disk) + '\n\n'	

		if self.arch != None:
			file_contents += '::ARCHITECTURE::\n' + self.arch + '\n\n'	

		if self.resources != None:
			file_contents += '::RESOURCE::\n' + self.resources + '\n\n'	
			
                

		
		job_file = open(self.temp_folder + '/' + self.job_filename,'w')
		job_file.write(file_contents)
		job_file.close()
		self.job_file_created = True


	# Submits a job to MiG using the migsubmit.py script
	# Checks if the first line of the output is 0
	# and then extracts the job-id as the first
	# chunk of non-whitespace chars of the second line.
	# TODO: Handle errors better
	def submit(self):
		print_debug('Submitting MiG job to vgrid ' + self.vgrid, self)
		self.__create_jobfile()
		submit_output = migsubmit(self.temp_folder + '/' + self.job_filename)
		self.job_submitted = True
		# Check that we got the right output
		lines = submit_output.splitlines()
		if (lines[0] == '0') and (len(lines) > 1):
			job_id_line = lines[1].split(' ')
			if(len(job_id_line) > 0):
				self.MiG_jobid = job_id_line[0]
				print_debug('Job submitted with MiG id: '+self.MiG_jobid, self)
				if LOG_STATS:
					self.log['mig_id'] = self.MiG_jobid
					self.log['local_id'] = self.job_uid
		
		if self.MiG_jobid == None:
			if PRINT_DEBUG:
				print_debug('An error occurred when submitting the job: ' + submit_output,self)	
	
	# add input file
	def add_input_file(self,relative_MiG_path):
		print_debug('Adding input file: '+relative_MiG_path, self)
		if relative_MiG_path.find('/') == 0:
			print_debug('Only relative paths are allowed', self)
		self.input_files.append(relative_MiG_path)
	
		
	
	# add output file
	def add_output_file(self,relative_MiG_path):
		print_debug('Adding output file: '+relative_MiG_path,self)
		if relative_MiG_path.find('/') == 0:
			print_debug('Only relative paths are allowed', self)
		self.output_files.append(relative_MiG_path)

	
	def add_env_var(self, name, value):
		"""Add an environment variable"""
		self.env_vars.append((name,value))
		
	# TODO CpuTime, Memory, Disk, CpuCount, NodeCount, Archictecture - dropdown?
	def add_runtime_env(self, run_env):
		self.runtime_envs.append(run_env)
		
	def set_cpu_time(self, cpu_time):
		self.cpu_time = cpu_time
	
	def set_memory(self,memory):
		self.memory = memory

	def set_disk(self,disk):
		self.disk = disk

	def set_cpu_count(self,cpu_count):
		self.cpu_count = cpu_count
		
	def set_node_count(self, node_count):
                self.node_count = node_count

        def set_resources(self, resources):
                self.resources = resources

	def set_architecture(self, arch):
		self.arch = arch
	
	def __log_finish_data(self,status_output):
		lines = status_output.splitlines()
		for line in lines:
			if line.find('Received:') == 0:
				before, sep, after = line.partition('Received:')
				self.log['received'] = after.strip()
			elif line.find('Queued:') == 0:
				before, sep, after = line.partition('Queued:')
				self.log['queued'] = after.strip()				
			elif line.find('Executing:') == 0:
				before, sep, after = line.partition('Executing:')
				self.log['executing'] = after.strip()				
			elif line.find('Finished:') == 0:
				before, sep, after = line.partition('Finished:')
				self.log['finished'] = after.strip()

	
	def poll_job(self):
		status_output = migstatus(self.MiG_jobid)
		lines = status_output.splitlines()
		status_chunk = 'Status:'
		for line in lines:
			if line.find(status_chunk) == 0:
				before, sep, after = line.partition('Status:')
				status = after.strip()
				if status == 'QUEUED':
					return Jobstate.queued
				elif status == 'EXECUTING':
					return Jobstate.executing
				elif status == 'FINISHED':
					if LOG_STATS:
						self.__log_finish_data(status_output)
					return Jobstate.finished
				elif status == 'CANCELED':
					return Jobstate.canceled
				elif status == 'FAILED':
					return Jobstate.failed
				elif status == 'EXPIRED':
					return Jobstate.expired
		
		return Jobstate.other


	
	def dump_output(self):
		print_debug('MiG stdout\n' + migcat('job_output/' + self.MiG_jobid + '/' + self.MiG_jobid + '.stdout'))
		print_debug('MiG stderr\n' + migcat('job_output/' + self.MiG_jobid + '/' + self.MiG_jobid + '.stderr'))
		print_debug('MiG status\n' + migcat('job_output/' + self.MiG_jobid + '/' + self.MiG_jobid + '.status'))
		
	
	def cleanup(self):
		print_debug('Cleaning up',self)

		# delete job file on MiG
		if self.job_submitted:
			migrm(self.job_filename)
		
		# dumping output files if we're debugging
		#if PRINT_DEBUG:
		#	self.dump_output()
	
	# blocks until job is finished and then returns the result.
	def wait(self,poll_interval=10):
		print_debug('Waiting for result. Checking status every %d seconds.' % poll_interval,self)
		job_status = Jobstate.other
		while ( job_status != Jobstate.finished and job_status != Jobstate.canceled and 
				job_status != Jobstate.failed and job_status != Jobstate.expired) :
			time.sleep(poll_interval)
			new_status = self.poll_job()
			if new_status != job_status:
				# status changed.
				if job_status == Jobstate.executing and new_status != Jobstate.finished:
					print_debug('{WARNING} Unexpected status: '+ Jobstate.getname(new_status), self)
				else:
					print_debug('New Status: '+ Jobstate.getname(new_status), self)
				job_status = new_status


		if job_status == Jobstate.finished:			
			return True
		else:
			print_debug('Job not finished. An error occurred. State: ' + Jobstate.getname(job_status), self)
			return False
	
