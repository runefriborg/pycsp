"""
ClusterProcess.

Requires the paramiko module.

Copyright (c) 2009 Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import os
import sys
import types
import uuid
import threading

has_paramiko= False
try:
    import paramiko, select
    has_paramiko= True
except ImportError, e:
    # Ignore for now
    pass

from pycsp.parallel.channel import Channel
from pycsp.parallel.exceptions import *
from pycsp.parallel.const import *
from pycsp.parallel.noderunner import *


# Decorators
def clusterprocess(func=None, cluster_nodefile="$PBS_NODEFILE", cluster_pin=None, cluster_hint='blocked', cluster_ssh_port=22, cluster_python='python'):
    """ @clusterprocess(cluster_nodefile="", cluster_pin=None, cluster_hint='blocked', cluster_ssh_port=22, cluster_python='python')

    This may be used to create a CSP network spanning remote hosts provided in a nodefile.

    Example of a 'nodefile':
    node1.host.org
    node1.host.org
    node2.host.org
    node2.host.org
    
    The location of this nodefile may then be provided using the Environment variable $PBS_NODEFILE.

    cluster_pin=X is used to pin a process to Xth entry in the nodefile.
    
    cluster_hint=[ 'blocked', 'strided', 'local' ] selects a distribution scheme for processes.

    All objects and variables provided to clusterprocesses through the
    parameter list must support pickling.
   
    Usage:
      >>> @clusterprocess
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)

      or
      >>> @clusterprocess(cluster_hint="local")
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)

      The cluster_* variables may overwritten in Parallel/Sequence/Spawn
      >>> Parallel(P, cluster_hint='blocked')
      
    The CSP ClusterProcess factory returned by the @clusterprocess decorator:
      func(*args, **kwargs)
    """
    if func:
        def _call(*args, **kwargs):
            return ClusterProcess(func, *args, **kwargs)
        _call.func_name = func.func_name
        return _call
    else:
        def wrap_process(func):
            def _call(*args, **kwargs):
                kwargs['cluster_nodefile'] = cluster_nodefile
                kwargs['cluster_pin']      = cluster_pin
                kwargs['cluster_hint']     = cluster_hint
                kwargs['cluster_ssh_port'] = cluster_ssh_port
                kwargs['cluster_python']   = cluster_python
                return ClusterProcess(func, *args, **kwargs)
            _call.func_name = func.func_name
            return _call
        return wrap_process


# Classes
class NodeGroup(object):
    def __init__(self, cond, nodefile, override=None):
        self.cond = cond
        self.nodefile = nodefile
        
        if override:
            self.nodes = override[0]
            self.next_index = override[1]
        else:
            realnodefile = nodefile
            # Lookup filename from environment
            if self.nodefile[0] == '$':
                try:
                    realnodefile = os.environ[nodefile[1:]]
                except KeyError:
                    raise InfoException("The provided cluster_nodefile='"+self.nodefile+"' does not exist. Please check the enviroment variable.")

            # read file
            fp = open(realnodefile)
            self.nodes=[l.strip() for l in fp.readlines()]
            fp.close()
            
        # Group state
        self.next_index = 0
        
    def get_node_from_index(self, index):
        return self.nodes[index % len(self.nodes)]

    def get_node_from_hint(self, hint='blocked'):
        """
          This function assumes that the nodefile is sorted, such
          that each entries translates to a cpu-core, and multiple
          cpu-cores on same node translates to multiple identical
          entries in the nodefile.
        """
        self.cond.acquire()
        node = None
        try:
            if hint == 'blocked':
                node = self.nodes[self.next_index]
                self.next_index = (self.next_index + 1) % len(self.nodes)

            elif hint == 'strided':
                previous_node = self.nodes[self.next_index - 1]
                start_index = self.next_index
                # Search for next node
                while (self.nodes[self.next_index] == previous_node):
                    # Skip next
                    self.next_index = (self.next_index + 1) % len(self.nodes)
                    
                    if self.next_index == start_index:
                        # All entries in nodefile is identical
                        break

                # Select node
                node = self.nodes[self.next_index]
                self.next_index = (self.next_index + 1) % len(self.nodes)
                
            #elif hint == 'auto':
            #    raise InfoException("The auto hint is not implemented yet. Use 'blocked', 'strided' or 'local'.")

            elif hint == 'local':
                node = 'localhost'

            else:
                raise InfoException("ClusterProcess does not support hint='"+hint+"'. Please replace with 'strided', 'blocked' or 'local'.")
        finally:
            self.cond.release()

        return node

    def get_state(self):
        return (self.nodes, self.next_index)
            

class NodePlacement(object):
    """ A special singleton class
    
    It reads the nodefile and based on the nodefile, it can provide placement strategies.
    """
    __cond = threading.Condition() # lock object
    __instance = None  # the unique instance
    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
        
    def getInstance(cls, *args, **kwargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''

        # Critical section start
        cls.__cond.acquire()
        try:
            if cls.__instance is None:
                # Initialize **the unique** instance
                cls.__instance = object.__new__(cls)
                cls.__instance.cond = cls.__cond
                cls.__instance.nodefiles= {}
        finally:
            #  Exit from critical section whatever happens
            cls.__cond.release()
        # Critical section end
        return cls.__instance
    getInstance = classmethod(getInstance)

    def set_nodegroup(self, nodefile, group_state):
        # Used by pycsp.parallel.server to enable the creation of new clusterprocesses from this node
        # using the original nodelist
        self.cond.acquire()
        if nodefile in self.nodefiles:
            # Ignore provided group_state
            group = self.nodefiles[nodefile]
        else:
            # Use provided group_state
            group = NodeGroup(self.cond, nodefile, override=group_state)
            self.nodefiles[nodefile] = group
        self.cond.release()
        return group
        

    def get_nodegroup(self, nodefile):
        self.cond.acquire()        
        if nodefile in self.nodefiles:
            group = self.nodefiles[nodefile]
        else:
            group = NodeGroup(self.cond, nodefile)
            self.nodefiles[nodefile] = group
        self.cond.release()
        return group


class ClusterProcess(object):
    """ ClusterProcess(func, *args, **kwargs)

    This may be used to create a CSP network spanning remote hosts.

    It is recommended to use the @clusterprocess decorator, to create ClusterProcess instances.
    See help(pycsp.clusterprocess)

    Usage:
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = ClusterProcess(filter, A.reader(), B.writer(), "42", debug=True, cluster_pin=1) 

    ClusterProcess(func, *args, **kwargs)
    func
      The function object to wrap and execute in the body of the process.
    args and kwargs
      are pickled and sent to the multiprocess where it is reassembled and
      passed to the execution of the function object.
    
    Public variables:
      ClusterProcess.name       Unique name to identify the process
    """
    def __init__(self, fn, *args, **kwargs):

        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        self.result_chan = None

        # This is not the real process, thus we use the id of the calling process.
        # The process started in method start, will have another new id.
        t, name = getThreadAndName()
        self.id = t.id

    def update(self, **kwargs):
        if self.result_chan:
            raise FatalException("Can not update process settings after it has been started")
 
        diff= set(kwargs.keys()).difference(["cluster_nodefile", "cluster_pin", "cluster_hint", "cluster_ssh_port", "cluster_python"])
        if diff:
            raise InfoException("Parameters %s not valid for ClusterProcess, use another process type or remove parameters." % (str(diff)))
        
        # Update values
        self.kwargs.update(kwargs)

        # Return updated process
        return self


    def start(self):

        if not has_paramiko:
            sys.stderr.write("The clusterprocess requires the Python paramiko module for SSH connections.\nSee https://pypi.python.org/pypi/paramiko/\n\n")
            raise ImportError("paramiko")

        if self.kwargs.has_key("cluster_nodefile"):
            cluster_nodefile = self.kwargs.pop("cluster_nodefile")
        else:
            cluster_nodefile = "$PBS_NODEFILE"
    
        group = NodePlacement().get_nodegroup(cluster_nodefile)

        if self.kwargs.has_key("cluster_pin"):
            cluster_pin = self.kwargs.pop("cluster_pin")
        else:
            cluster_pin = None

        if self.kwargs.has_key("cluster_hint"):
            cluster_hint = self.kwargs.pop("cluster_hint")
        else:
            cluster_hint = "blocked"

        if cluster_pin:
            nodehost = group.get_node_from_index(cluster_pin)
        else:
            nodehost = group.get_node_from_hint(cluster_hint)

        pycsp_host = ''
        if nodehost != 'localhost':
            # Set pycsp_host to enable using the correct network interfaces
            pycsp_host = nodehost

        # All cluster processes will find a new port for hosting channels automatically
        pycsp_port = 0

        
        if self.kwargs.has_key("cluster_ssh_port"):
            ssh_port = self.kwargs.pop("cluster_ssh_port")
        else:
            ssh_port = 22

        if self.kwargs.has_key("cluster_python"):
            ssh_python = self.kwargs.pop("cluster_python")
        else:
            ssh_python = "python"

        
        self.result_chan = NodeRunner().run(ssh_host      = nodehost,
                         ssh_port      = ssh_port,
                         ssh_python    = ssh_python,
                         cwd           = os.getcwd(),
                         pycsp_host    = pycsp_host,
                         pycsp_port    = pycsp_port,
                         script_path   = self.fn.func_code.co_filename,
                         func_name     = self.fn.func_name,
                         func_args     = self.args,
                         func_kwargs   = self.kwargs,
                         cluster_state = (cluster_nodefile, group.get_state()) )                         
                         

       
    def join_report(self):
        # This method enables propagation of errors to parent processes and threads.
        # It also transfers the return value from function

        result = NodeRunner().get_result(self.result_chan)
        return result

    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        kwargs = self.__mul_channel_ends(self.kwargs)        
        return [self] + [ClusterProcess(self.fn, *self.__mul_channel_ends(self.args), **kwargs) for i in range(multiplier - 1)]

    # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]
    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

    # Copy lists and dictionaries
    def __mul_channel_ends(self, args):
        if types.ListType == type(args) or types.TupleType == type(args):
            R = []
            for item in args:
                try:                    
                    if type(item.isReader) == types.UnboundMethodType and item.isReader():
                        R.append(item.channel.reader())
                    elif type(item.isWriter) == types.UnboundMethodType and item.isWriter():
                        R.append(item.channel.writer())
                except AttributeError:
                    if item == types.ListType or item == types.DictType or item == types.TupleType:
                        R.append(self.__mul_channel_ends(item))
                    else:
                        R.append(item)

            if types.TupleType == type(args):
                return tuple(R)
            else:
                return R
            
        elif types.DictType == type(args):
            R = {}
            for key in args:
                try:
                    if type(key.isReader) == types.UnboundMethodType and key.isReader():
                        R[key.channel.reader()] = args[key]
                    elif type(key.isWriter) == types.UnboundMethodType and key.isWriter():
                        R[key.channel.writer()] = args[key]
                    elif type(args[key].isReader) == types.UnboundMethodType and args[key].isReader():
                        R[key] = args[key].channel.reader()
                    elif type(args[key].isWriter) == types.UnboundMethodType and args[key].isWriter():
                        R[key] = args[key].channel.writer()
                except AttributeError:
                    if args[key] == types.ListType or args[key] == types.DictType or args[key] == types.TupleType:
                        R[key] = self.__mul_channel_ends(args[key])
                    else:
                        R[key] = args[key]
            return R
        return args
                
