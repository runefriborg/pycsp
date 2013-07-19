"""
Multiprocess

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import types
import uuid
import threading
import os

import multiprocessing

from pycsp.parallel.dispatch import SocketDispatcher
from pycsp.parallel.protocol import RemoteLock
from pycsp.parallel.const import *
from pycsp.parallel.configuration import *
from pycsp.parallel.exceptions import *
        
conf = Configuration()

# Decorators
def multiprocess(func=None, pycsp_host='', pycsp_port=None):
    """ @multiprocess(pycsp_host='', pycsp_port=None)

    @multiprocess decorator for making a function into a CSP MultiProcess factory.
    Each generated CSP process is implemented as a single OS process.

    All objects and variables provided to multiprocesses through the
    parameter list must support pickling.
   
    Usage:
      >>> @multiprocess
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)

      or
      >>> @multiprocess(pycsp_host="localhost", pycsp_port=9998)
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)
      
    The CSP MultiProcess factory returned by the @multiprocess decorator:
      func(*args, **kwargs)
    """
    if func:
        def _call(*args, **kwargs):
            return MultiProcess(func, *args, **kwargs)
        _call.func_name = func.func_name
        return _call
    else:
        def wrap_process(func):
            def _call(*args, **kwargs):
                kwargs['pycsp_host']= pycsp_host
                kwargs['pycsp_port']= pycsp_port
                return MultiProcess(func, *args, **kwargs)
            _call.func_name = func.func_name
            return _call
        return wrap_process



# Classes
class MultiProcess(multiprocessing.Process):
    """ MultiProcess(func, *args, **kwargs)

    CSP process implemented as a single OS process.

    It is recommended to use the @multiprocess decorator, to create MultiProcess instances.
    See help(pycsp.multiprocess)

    Usage:
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = MultiProcess(filter, A.reader(), B.writer(), "42", debug=True, pycsp_host='localhost') 

    MultiProcess(func, *args, **kwargs)
    func
      The function object to wrap and execute in the body of the process.
    args and kwargs
      are pickled and sent to the multiprocess where it is reassembled and
      passed to the execution of the function object.
    
    Public variables:
      MultiProcess.name       Unique name to identify the process
    """
    def __init__(self, fn, *args, **kwargs):
        multiprocessing.Process.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        
        # Create return pipe for return value
        self.return_pipe = multiprocessing.Pipe()

        # Create 64 byte unique id based on network address, sequence number and time sample.
        self.id = uuid.uuid1().hex + "." + fn.func_name[:31]

        # Channel request state
        self.cond = None
        self.chan_moved_to = None
        self.state = FAIL
        self.result_ch_idx = None
        self.result_msg = None
        
        # Used to wait for acknowledgements from the RemoteLock
        self.ack = False

        # Used to ensure the validity of the remote answers
        self.sequence_number = 1

        # Protect against early termination of mother-processes leavings childs in an invalid state
        self.spawned = []

        # Protect against early termination of channelhomes leaving processes in an invalid state
        self.registeredChanDict = {}

        # Protect against early termination of processes leaving channelhomes in an invalid state
        self.activeChanList = []
        self.closedChanList = []

        # Identify this as a wrapped pycsp process, which must not be terminated by shutdown
        self.maintained= True

        # report execution error
        self._error = multiprocessing.RawValue('i', 0)

    def update(self, **kwargs):
        if self.cond:
            raise FatalException("Can not update process settings after it has been started")
    
        diff= set(kwargs.keys()).difference(["pycsp_host", "pycsp_port"])
        if diff:
            raise InfoException("Parameters %s not valid for MultiProcess, use another process type or remove parameters." % (str(diff)))
        
        # Update values
        self.kwargs.update(kwargs)

        # Return updated process
        return self

    def wait_ack(self):
        self.cond.acquire()
        while not self.ack:
            self.cond.wait()
        # Got ack, resetting
        self.ack= False
        self.cond.release()

    def wait(self):
        self.cond.acquire()
        while self.state == READY:
            self.cond.wait()
        self.cond.release()

    def join_report(self):
        # This method enables propagation of errors to parent processes and threads.
        # It also transfers the return value from function

        # Receive value while process is running, since send may block until read
        val= self.return_pipe[0].recv()
        
        # Wait for process to finish
        self.join()

        # 1001 = Socket bind error
        if self._error.value == 1001:          
            raise ChannelBindException(None, 'Could not bind to address in multiprocess')

        # Return read value
        return val


    def run(self):
        
        # Multiprocessing inherits global objects like singletons. Thus we must reset!
        # Reset SocketDispatcher Singleton object to force the creation of a new
        # SocketDispatcher

        # Host and Port address will be set for the SocketDispatcher (one per interpreter/multiprocess)
        if self.kwargs.has_key("pycsp_host"):
            self.host = self.kwargs.pop("pycsp_host")
        else:
            self.host = ''
            
        if self.kwargs.has_key("pycsp_port"):
            self.port = self.kwargs.pop("pycsp_port")
        else:
            self.port = 0

        if self.host != '':
            conf.set(PYCSP_HOST, self.host)

        # Set a new port, to overwrite PYCSP_PORT as that is already taken by the mother process.
        conf.set(PYCSP_PORT, self.port)

        # Also clear PYCSP_PORT environment variable 
        if os.environ.has_key("PYCSP_PORT"):
            del os.environ["PYCSP_PORT"]


        try:            
            SocketDispatcher(reset=True)
        except SocketBindException as e:
            self._error.value = 1001
            self.return_pipe[1].send(None)
            return

        # Create remote lock
        self.cond = threading.Condition()        
        dispatch = SocketDispatcher().getThread()
        self.addr = dispatch.server_addr
        dispatch.registerProcess(self.id, RemoteLock(self))

        return_value = None
        try:
            return_value = self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException as e:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(self.kwargs.values())
        except ChannelRetireException as e:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())
        finally:
            self.return_pipe[1].send(return_value)

        # Join spawned processes
        for p in self.spawned:
            p.join_report()

        # Initiate clean up and waiting for channels to finish outstanding operations.
        for channel in self.activeChanList:
            channel._CM.leave(channel, self)

        # Wait for channels        
        self.cond.acquire()
        X = len(self.activeChanList)
        while len(self.closedChanList) < X:
            self.cond.wait()
        self.cond.release()

        dispatch.deregisterProcess(self.id)

        # Deregister namespace references
        for chan in self.registeredChanDict:
            address = self.registeredChanDict[chan]
            chan._deregister(other_address=address)

        for chan in self.registeredChanDict:
            chan._threadjoin()

        # Wait for sub-processes as these may not yet have quit.
        for processchild in multiprocessing.active_children():
            processchild.join()

        # Wait for sub-threads as these may not yet have quit. When threads are run in multiprocesses (daemon setting is ignored)
        skip = threading.currentThread()
        for threadchild in threading.enumerate():
            if not threadchild == skip:
                threadchild.join()

    def __check_poison(self, args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_poison(arg)
                elif types.DictType == type(arg):
                    self.__check_poison(arg.keys())
                    self.__check_poison(arg.values())
                elif type(arg.poison) == types.UnboundMethodType:
                    arg.poison()
            except AttributeError:
                pass

    def __check_retire(self, args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_retire(arg)
                elif types.DictType == type(arg):
                    self.__check_retire(arg.keys())
                    self.__check_retire(arg.values())
                elif type(arg.retire) == types.UnboundMethodType:
                    # Ignore if try to retire an already retired channel end.
                    try:
                        arg.retire()
                    except ChannelRetireException:
                        pass
            except AttributeError:
                pass

    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        kwargs = self.__mul_channel_ends(self.kwargs)
        # Reset port number, as only one multiprocess may bind to the same interface
        kwargs['pycsp_port']=0
        return [self] + [MultiProcess(self.fn, *self.__mul_channel_ends(self.args), **kwargs) for i in range(multiplier - 1)]

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
                
