"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:
  
The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.  THE
SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

# Imports
import types
import uuid
import threading

from pycsp.parallel.dispatch import SocketDispatcher
from pycsp.parallel.protocol import RemoteLock, ChannelMessenger
from pycsp.parallel.channel import Channel, ChannelEndRead, ChannelEndWrite
from pycsp.parallel.const import *
from pycsp.parallel.exceptions import *

# Decorators
def process(func):
    """
    @process decorator for making a function into a CSP Process factory.
    Each generated CSP process is implemented as a single OS thread.

    Usage:
      >>> @process
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = filter(A.reader(), B.writer(), "42", debug=True)

    The CSP Process factory returned by the @process decorator:
      func(*args, **kwargs)
    """
    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call



# Classes
class Process(threading.Thread):
    """ Process(func, *args, **kwargs)

    CSP process implemented as a single OS thread.

    It is recommended to use the @process decorator, to create Process instances.
    See help(pycsp.process)

    Usage:
      >>> def filter(dataIn, dataOut, tag, debug=False):
      >>>   pass # perform filtering
      >>>
      >>> P = Process(filter, A.reader(), B.writer(), "42", debug=True) 

    Process(func, *args, **kwargs)
    func
      The function object to wrap and execute in the body of the process.
    args and kwargs are passed directly to the execution of the function object.
    
    Public variables:
      Process.name       Unique name to identify the process
    """
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        # Create 64 byte unique id based on network address, sequence number and time sample.
        self.id = uuid.uuid1().hex + "." + fn.func_name[:31]
        
        # Channel request state
        self.state = FAIL
        self.result_ch_idx = None
        self.result_msg = None
        
        # Used to ensure the validity of the remote answers
        self.sequence_number = 1

        # Protect against early termination of mother-processes leaving childs in an invalid state
        self.spawned = []

        # Protect against early termination of channelhomes leaving channel references in an invalid state
        self.registeredChanHomeList = []
        self.registeredChanConnectList = []

        # Protect against early termination of processes leaving channelhomes in an invalid state
        self.activeChanList = []
        self.closedChanList = []

        # Identify this as a wrapped pycsp process, which must not be terminated by shutdown
        self.maintained= True

    def wait(self):
        self.cond.acquire()
        if self.state == READY:
            self.cond.wait()
        self.cond.release()

    def run(self):
        
        # Create remote lock
        self.cond = threading.Condition()        
        dispatch = SocketDispatcher().getThread()
        self.addr = dispatch.server_addr
        dispatch.registerProcess(self.id, RemoteLock(self))

        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException as e:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(self.kwargs.values())
        except ChannelRetireException as e:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())

        # Join spawned processes
        for p in self.spawned:
            p.join()

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

        # Deregister channel references
        for chan in self.registeredChanConnectList:
            chan._deregister()
        for chan in self.registeredChanHomeList:
            chan._deregister()

        for chan in self.registeredChanHomeList:
            chan._threadjoin()

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
        return [self] + [Process(self.fn, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

    # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]
    def __rmul__(self, multiplier):
        return [self] + [Process(self.fn, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

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
                
# Functions
def Parallel(*plist):
    """ Parallel(P1, [P2, .. ,PN])

    Performs concurrent synchronous execution of the supplied CSP processes. 
    
    Blocks until all processes have exited.
  
    Usage:
      >>> @process
      ... def P1(cout):
      ...     for i in range(10):
      ...         cout(i)
      ...     retire(cout)

      >>> @process
      ... def P2(cin):
      ...     while True:
      ...         cin()
    
      >>> C = Channel()  
      >>> Parallel(P1(C.writer()), P2(C.reader()))
    """
    _parallel(plist, True)

def Spawn(*plist):
    """ Spawn(P1, [P2, .. ,PN])

    Performs concurrent asynchronous execution of the supplied CSP processes. 
  
    Usage:
      >>> @process
      ... def P1(cout):
      ...     for i in range(10):
      ...         cout(i)
      ...     retire(cout)
    
      >>> C = Channel()  
      >>> Parallel(P1(C.writer()))

      >>> cin = C.reader()
      ... try:
      ...     while True:
      ...         cin()
    """
    _parallel(plist, False)

def _parallel(plist, block = True):
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    for p in processes:
        p.start()

    if block:
        for p in processes:
            p.join()
    else:
        p,_ = getThreadAndName()
        p.spawned.extend(processes)
    
def Sequence(*plist):
    """ Sequence(P1, [P2, .. ,PN])

    Performs synchronous execution of the supplied CSP processes. 
    
    The supplied processes are executed in order.

    Blocks until the last process has exited.
  
    Usage:
      >>> @process
      ... def P1(id):
      ...     print(id)

      >>> L = [P1(i) for i in range(10)]
      >>> Sequence(L)
    """
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    # For every process we simulate a new process_id.
    t, name = getThreadAndName()

    t_original_id = t.id
    for p in processes:
        t.id = p.id

        # Call Run directly instead of start() and join() 
        p.run()
    t.id = t_original_id


def current_process_id():
    """
    Returns the id of the executing CSP process.
    """
    t, name = getThreadAndName()

    if name == 'MainThread':
        try:
            return MAINTHREAD_ID
        except NameError:            
            return '__main__'
    return t.id


# Update Main Thread/Process with necessary state variables
# All channel communications require the active process to have a running
# LockThread and have the necessary state variables initialised
#
# To accomondate channel communications made from the main thread, the following
# code initialises state variables and creates a LockThread.
#
init_procs = []

# Enable the main thread to function as a process
def init():
    """
    Initialising state variables for channel communication made from an uninitialized thread/process (__main__).

    This function is invoked from const.getThreadAndName to initialise the current NON-CSP! process when necessary.
    """
    global init_procs
    try:
        # compatible with Python 2.6+
        current_proc = threading.current_thread()
    except AttributeError:
        # compatible with Python 2.5- 
        current_proc = threading.currentThread()        

    run = True
    try:
        if current_proc.id != None:
            run = False
    except AttributeError:
        pass

    if run:
        if not current_proc in init_procs:
            init_procs.append(current_proc)

        current_proc.id = uuid.uuid1().hex + ".__INIT__"
        current_proc.fn = None
        current_proc.state = FAIL
        current_proc.result_ch_idx = None
        current_proc.result_msg = None
        current_proc.sequence_number = 1

        # Protect against early termination of mother-processes leaving childs in an invalid state
        current_proc.spawned = []

        # Protect against early termination of channelhomes leaving channel references in an invalid state
        current_proc.registeredChanHomeList = []
        current_proc.registeredChanConnectList = []

        # Protect against early termination of processes leaving channelhomes in an invalid state
        current_proc.activeChanList = []
        current_proc.closedChanList = []

        current_proc.cond = threading.Condition()
        dispatch = SocketDispatcher().getThread()
        current_proc.addr = dispatch.server_addr
        dispatch.registerProcess(current_proc.id, RemoteLock(current_proc))

        def wait():
            current_proc.cond.acquire()
            if current_proc.state == READY:
                current_proc.cond.wait()
            current_proc.cond.release()
        current_proc.wait = wait

def shutdown():
    """
    Closing the PYCSP instance

    Every PyCSP application will create a server thread, to serve incoming communications
    on channels. For this reason, it is required to always end the PyCSP application with
    a call to shutdown()

    Usage:
      >>> shutdown()

    Performs a stable shutdown of hosted channels, waiting for local and remote
    processes to disconnect from the hosted channels.
    """
    global init_procs
    try:
        # compatible with Python 2.6+
        current_proc = threading.current_thread()
    except AttributeError:
        # compatible with Python 2.5- 
        current_proc = threading.currentThread()

    try:
        if current_proc.maintained:
            raise InfoException("pycsp.shutdown must not be called in PyCSP processes wrapped in a PyCSP.Process structure. PyCSP.Process processes have their own shutdown mechanism.")
    except AttributeError:
        pass

    try:
        dispatch = SocketDispatcher().getThread()

        for p in current_proc.spawned:
            p.join()

        # Initiate clean up and waiting for channels to finish outstanding operations.
        for channel in current_proc.activeChanList:
            channel._CM.leave(channel, current_proc)

        # Wait for channels        
        current_proc.cond.acquire()
        X = len(current_proc.activeChanList)
        while len(current_proc.closedChanList) < X:
            current_proc.cond.wait()
        current_proc.cond.release()

        dispatch.deregisterProcess(current_proc.id)

        # Deregister channel references
        for chan in current_proc.registeredChanConnectList:
            chan._deregister()        
        for chan in current_proc.registeredChanHomeList:
            chan._deregister()        
            
        # Wait for channelhomethreads to terminate
        for chan in current_proc.registeredChanHomeList:
            chan._threadjoin()

        # Cleaning structures
        current_proc.spawned = []
        current_proc.registeredChanHomeList = []
        current_proc.registeredChanConnectList = []
        current_proc.activeChanList = []
        current_proc.closedChanList = []

        # Reset current_proc id, to force a new init(), if required
        del current_proc.id


    except AttributeError:
        pass
