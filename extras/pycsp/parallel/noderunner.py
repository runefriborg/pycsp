"""
NodeRunner module

Requires the paramiko module.

Copyright (c) 2009 Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import sys
import threading


try:    
    import multiprocessing
    MULTIPROCESSING_ENABLED=1
except ImportError:
    MULTIPROCESSING_ENABLED=0

has_paramiko= False
try:
    import paramiko, select
    has_paramiko= True
except ImportError, e:
    # Ignore for now
    pass

from pycsp.parallel.channel import Channel
from pycsp.parallel.noderunner import *


class NodeRunnerThread(threading.Thread):
    def __init__(self, ssh_host, ssh_port, ssh_python, cwd, arg_chan_host, arg_chan_port, arg_chan_name):
        threading.Thread.__init__(self)

        self.ssh_host      = ssh_host
        self.ssh_port      = ssh_port
        self.ssh_python    = ssh_python
        self.ssh_user      = None
        self.ssh_password  = None
        self.cwd           = cwd
        self.arg_chan_host = arg_chan_host
        self.arg_chan_port = arg_chan_port
        self.arg_chan_name = arg_chan_name
    
    def run(self):

        try:

            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.set_missing_host_key_policy(paramiko.WarningPolicy())
    
            client.connect(self.ssh_host, port=self.ssh_port, username=self.ssh_user, password=self.ssh_password)

            command= " ".join(["/usr/bin/env", 
                               self.ssh_python, "-m", "pycsp.parallel.server",
                               self.cwd, self.arg_chan_host, self.arg_chan_port, self.arg_chan_name])

            transport = client.get_transport()
            session = transport.open_session()
            session.exec_command(command)

            while True:
                (r, w, e) = select.select([session], [], [], 10)
                if r:
                    got_data = False
                    if session.recv_ready():
                        data = r[0].recv(4096)
                        if data:
                            got_data = True
                            sys.stdout.write(data)
                    if session.recv_stderr_ready():
                        data = r[0].recv_stderr(4096)
                        if data:
                            got_data = True
                            sys.stderr.write(data)
                    if not got_data:
                        break


        finally:
            client.close()



class NodeRunner(object):
    """
    NodeRunner singleton
   
    Will be handling connections to remote hosts through ssh    
    """
    __condObj = threading.Condition() # lock object
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self, reset=False):
        pass

    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''

        #  Check that this is not a stale singleton from another interpreter. Using the multiprocessing
        #  module to create new subprocesses with individual interpreters, has such a side-effect.
        #  If the singleton is from another interpreter, then recreate a new singleton for this interpreter.

        # Critical section start
        cls.__condObj.acquire()

        try:
            if MULTIPROCESSING_ENABLED:                        
                if cls.__instance is not None:
                    subprocess = multiprocessing.current_process()
                    if cls.__instance.interpreter != subprocess:
                        del cls.__condObj
                        cls.__condObj = threading.Condition()
                        del cls.__instance
                        cls.__instance = None

            if cls.__instance is None:
                # Initialize **the unique** instance
                cls.__instance = object.__new__(cls)
                cls.__instance.condObj = cls.__condObj

                # Record interpreter subprocess if multiprocessing is available
                if MULTIPROCESSING_ENABLED:
                    cls.__instance.interpreter = multiprocessing.current_process()


                # Init ConnectionDict
                cls.__instance.connections = {}
                cls.__instance.running = {}
                cls.__instance.keys = {}
                cls.__instance.threads = {}
                                
        finally:
            #  Exit from critical section whatever happens
            cls.__condObj.release()
        # Critical section end

        return cls.__instance
    getInstance = classmethod(getInstance)

    def get_result(self, result_chan):
        
        # Fetch result
        cin = result_chan.reader()
        result = cin()

        self.condObj.acquire()
        key = self.keys.pop(result_chan)

        self.running[key].remove(result_chan)

        # If no more processes running at host, then poison
        if not self.running[key]:
            self.connections[key].reader().poison()
            
            del self.connections[key]
            del self.running[key]
            
            # join thread
            t = self.threads.pop(key)
            t.join()

        self.condObj.release()

        return result

        
    def run(self, ssh_host, ssh_port, ssh_python, cwd, pycsp_host, pycsp_port, script_path, func_name, func_args, func_kwargs, cluster_state = None):
        
        
        result_chan = Channel(buffer=1)

        key = (ssh_host, ssh_port, ssh_python, cwd)
        self.keys[result_chan] = key

        self.condObj.acquire()
        if key in self.connections:
            arg_chan = self.connections[key]
            running = self.running[key]
        else:
            # Setup channels to communicate data to process server.py
            arg_chan = Channel(buffer=1)
            running = []
            self.connections[key] = arg_chan
            self.running[key] = running
            
            # Start NodeRunnerThread
            t = NodeRunnerThread(ssh_host, ssh_port, ssh_python, cwd, str(arg_chan.address[0]), str(arg_chan.address[1]), arg_chan.name)
            t.start()
            self.threads[key] = t

        running.append(result_chan)
        
        self.condObj.release()

        cout = arg_chan.writer()

        if cluster_state:
            cout( (pycsp_host, pycsp_port, result_chan.name, script_path, func_name, func_args, func_kwargs, cluster_state) )
        else:
            cout( (pycsp_host, pycsp_port, result_chan.name, script_path, func_name, func_args, func_kwargs) )

        return result_chan
