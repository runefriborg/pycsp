"""
SSHProcess.

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
    import paramiko
    has_paramiko= True
except ImportError, e:
    # Ignore for now
    pass

from pycsp.parallel.channel import Channel
from pycsp.parallel.exceptions import *
from pycsp.parallel.const import *
from pycsp.parallel.noderunner import *

# Decorators
def sshprocess(func=None, pycsp_host='', pycsp_port=0, ssh_host='localhost', ssh_port=22, ssh_user=None, ssh_password=None, ssh_python='python'):
    """ @sshprocess(pycsp_host='', pycsp_port=0, ssh_host='localhost', ssh_port=22, ssh_user=None, ssh_password=None, ssh_python='python')

    This may be used to create a CSP network spanning remote hosts.
    Create CSP processes running in a new Python interpreter started on a remote host using the
    SSH2 protocol (paramiko module)

    It is not recommended to use the password argument. Instead, setup the remote host
    for a passwordless login using private/public key authorisation.


    @sshprocess decorator for making a function into a CSP SSHProcess factory.

    All objects and variables provided to sshprocesses through the
    parameter list must support pickling.
   
    Usage:
      >>> @sshprocess(ssh_host="10.22.32.10")
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)

      or
      >>> @sshprocess(ssh_host="10.0.10.1", ssh_user="guest", ssh_password="42", ssh_python='python-2.6')
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)
      
    The CSP SSHProcess factory returned by the @sshprocess decorator:
      func(*args, **kwargs)
    """
    if func:
        def _call(*args, **kwargs):
            return SSHProcess(func, *args, **kwargs)
        _call.func_name = func.func_name
        return _call
    else:
        def wrap_process(func):
            def _call(*args, **kwargs):
                kwargs['pycsp_host']= pycsp_host
                kwargs['pycsp_port']= pycsp_port
                kwargs['ssh_host']= ssh_host
                kwargs['ssh_port']= ssh_port
                kwargs['ssh_user']= ssh_user
                kwargs['ssh_password']= ssh_password
                kwargs['ssh_python']= ssh_python
                return SSHProcess(func, *args, **kwargs)
            _call.func_name = func.func_name
            return _call
        return wrap_process


# Classes
class SSHProcess(object):
    """ SSHProcess(func, *args, **kwargs)

    This may be used to create a CSP network spanning remote hosts.
    Create CSP processes running in a new Python interpreter started on a remote host using the
    SSH2 protocol (paramiko module)

    It is recommended to use the @sshprocess decorator, to create SSHProcess instances.
    See help(pycsp.sshprocess)

    Usage:
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = SSHProcess(filter, A.reader(), B.writer(), "42", debug=True, ssh_host='10.0.0.2', ssh_python='python-2.7') 

    SSHProcess(func, *args, **kwargs)
    func
      The function object to wrap and execute in the body of the process.
    args and kwargs
      are pickled and sent to the multiprocess where it is reassembled and
      passed to the execution of the function object.
    
    Public variables:
      SSHProcess.name       Unique name to identify the process
    """
    def __init__(self, fn, *args, **kwargs):

        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.p = None

        # This is not the real process, thus we use the id of the calling process.
        # The process started in method start, will have another new id.
        t, name = getThreadAndName()
        self.id = t.id

    def update(self, **kwargs):
        if self.p:
            raise FatalException("Can not update process settings after it has been started")
    
        diff= set(kwargs.keys()).difference(["pycsp_host", "pycsp_port", "ssh_host", "ssh_port", "ssh_user", "ssh_password", "ssh_python"])
        if diff:
            raise InfoException("Parameters %s not valid for SSHProcess, use another process type or remove parameters." % (str(diff)))
        
        # Update values
        self.kwargs.update(kwargs)

        # Return updated process
        return self


    def start(self):

        if not has_paramiko:
            sys.stderr.write("The sshprocess requires the Python paramiko module for SSH connections.\nSee https://pypi.python.org/pypi/paramiko/\n\n")
            raise ImportError("paramiko")

        # Host and Port address will be set in the new environment
        if self.kwargs.has_key("pycsp_host"):
            pycsp_host = self.kwargs.pop("pycsp_host")
        else:
            pycsp_host = ''
            
        if self.kwargs.has_key("pycsp_port"):
            pycsp_port = self.kwargs.pop("pycsp_port")
        else:
            pycsp_port = 0

        if self.kwargs.has_key("ssh_host"):
            ssh_host = self.kwargs.pop("ssh_host")
        else:
            ssh_host = "localhost"

        if self.kwargs.has_key("ssh_port"):
            ssh_port = self.kwargs.pop("ssh_port")
        else:
            ssh_port = 22

        if self.kwargs.has_key("ssh_user"):
            ssh_user = self.kwargs.pop("ssh_user")
        else:
            ssh_user = None

        if self.kwargs.has_key("ssh_password"):
            ssh_password = self.kwargs.pop("ssh_password")
        else:
            ssh_password = None

        if self.kwargs.has_key("ssh_python"):
            ssh_python = self.kwargs.pop("ssh_python")
        else:
            ssh_python = "python"


        
        self.result_chan = NodeRunner().run(ssh_host      = ssh_host,
                         ssh_port      = ssh_port,
                         ssh_python    = ssh_python,
                         cwd           = os.getcwd(),
                         pycsp_host    = pycsp_host,
                         pycsp_port    = pycsp_port,
                         script_path   = self.fn.func_code.co_filename,
                         func_name     = self.fn.func_name,
                         func_args     = self.args,
                         func_kwargs   = self.kwargs,
                         cluster_state = None )                         
                         

       
    def join_report(self):
        # This method enables propagation of errors to parent processes and threads.
        # It also transfers the return value from function

        result = NodeRunner().get_result(self.result_chan)
        return result


    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        kwargs = self.__mul_channel_ends(self.kwargs)        
        return [self] + [SSHProcess(self.fn, *self.__mul_channel_ends(self.args), **kwargs) for i in range(multiplier - 1)]

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
                
