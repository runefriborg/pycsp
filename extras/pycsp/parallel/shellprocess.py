"""
Shellprocess

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import subprocess
import sys
import os
import types
import uuid

from pycsp.parallel.channel import Channel
from pycsp.parallel.exceptions import *
from pycsp.parallel.const import *
from pycsp.parallel import serverresult

# Decorators
def shellprocess(func=None, pycsp_host='', pycsp_port=0, shell_python='python'):
    """ @shellprocess(pycsp_host='', pycsp_port=0, shell_python='python')

    ** MS windows not supported! **

    CSP process running in a new Python interpreter started from a new shell.
    
    This may be used to run processes in parallel using different interpreter versions
    in one CSP network.

    @shellprocess decorator for making a function into a CSP ShellProcess factory.

    All objects and variables provided to shellprocesses through the
    parameter list must support pickling.
   
    Usage:
      >>> @shellprocess
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)

      or
      >>> @shellprocess(pycsp_host="localhost", pycsp_port=9998, shell_python='python-2.6')
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)
      
    The CSP ShellProcess factory returned by the @shellprocess decorator:
      func(*args, **kwargs)
    """
    if func:
        def _call(*args, **kwargs):
            return ShellProcess(func, *args, **kwargs)
        _call.func_name = func.func_name
        return _call
    else:
        def wrap_process(func):
            def _call(*args, **kwargs):
                kwargs['pycsp_host']= pycsp_host
                kwargs['pycsp_port']= pycsp_port
                kwargs['shell_python']= shell_python
                return ShellProcess(func, *args, **kwargs)
            _call.func_name = func.func_name
            return _call
        return wrap_process


# Classes
class ShellProcess(object):
    """ ShellProcess(func, *args, **kwargs)

    ** MS windows not supported! **

    CSP process running in a new Python interpreter started from a new shell.

    It is recommended to use the @shellprocess decorator, to create ShellProcess instances.
    See help(pycsp.shellprocess)

    Usage:
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = ShellProcess(filter, A.reader(), B.writer(), "42", debug=True, shell_python='python-2.7') 

    ShellProcess(func, *args, **kwargs)
    func
      The function object to wrap and execute in the body of the process.
    args and kwargs
      are pickled and sent to the multiprocess where it is reassembled and
      passed to the execution of the function object.
    
    Public variables:
      ShellProcess.name       Unique name to identify the process
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
    
        diff= set(kwargs.keys()).difference(["pycsp_host", "pycsp_port", "shell_python"])
        if diff:
            raise InfoException("Parameters %s not valid for ShellProcess, use another process type or remove parameters." % (str(diff)))
        
        # Update values
        self.kwargs.update(kwargs)

        # Return updated process
        return self

    def start(self):

        # Host and Port address will be set in the new environment
        if self.kwargs.has_key("pycsp_host"):
            pycsp_host = self.kwargs.pop("pycsp_host")
        else:
            pycsp_host = ''
            
        if self.kwargs.has_key("pycsp_port"):
            pycsp_port = self.kwargs.pop("pycsp_port")
        else:
            pycsp_port = 0

        if self.kwargs.has_key("shell_python"):
            shell_python = self.kwargs.pop("shell_python")
        else:
            shell_python = "python"

        # Must be the script containing fn.
        self.scriptPath = self.fn.func_code.co_filename

        # Setup channel to communicate data to process
        self.channel = Channel(buffer=1)
        self.send = self.channel.writer()
       
        # Send arguments to new process
        self.send((self.args, self.kwargs))
        
        # Info is provided as arguments to the pycsp.parallel.server process.
        self.p = subprocess.Popen(["/usr/bin/env", 
                                   "PYCSP_HOST="+str(pycsp_host),
                                   "PYCSP_PORT="+str(pycsp_port),
                                   shell_python, "-m", "pycsp.parallel.server",
                                   os.getcwd(), self.channel.address[0], str(self.channel.address[1]), self.channel.name, self.scriptPath, self.fn.func_name], stdout=subprocess.PIPE)
        

    def join_report(self):
        # This method enables propagation of errors to parent processes and threads.
        # It also transfers the return value from function

        # Read value
        if self.p:
            val = serverresult.retrieve_value_from_stream(self.p.stdout)

            # Output the rest of stdout
            sys.stdout.write(self.p.stdout.read())
        else:
            val = None

        # Wait for process to finish
        if self.p:
            self.p.wait()

        # Return read value
        return val

    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        kwargs = self.__mul_channel_ends(self.kwargs)
        # Reset port number, as only one multiprocess may bind to the same interface
        kwargs['pycsp_port']=0
        return [self] + [ShellProcess(self.fn, *self.__mul_channel_ends(self.args), **kwargs) for i in range(multiplier - 1)]

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
                
