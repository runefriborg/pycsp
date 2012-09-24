"""
Multiprocess

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

import multiprocessing

from dispatch import SocketDispatcher
from protocol import RemoteLock
from channel import ChannelPoisonException, Channel
from channelend import ChannelRetireException, ChannelEndRead, ChannelEndWrite
from pycsp.common.const import *
from configuration import *
        
conf = Configuration()

# Decorators
def multiprocess2(port=None):
    """
    @process decorator for creating process functions

    >>> @multiprocess(port=8080)
    ... def P():
    ...     pass

    >>> isinstance(P(), MultiProcess)
    True
    """
    def wrap_process(func):
        def _call(*args, **kwargs):
            return MultiProcess(func, port, *args, **kwargs)
        _call.func_name = func.func_name
        return _call
    return wrap_process

# Decorators
def multiprocess(func):
    """
    @process decorator for creating process functions

    >>> @multiprocess(port=8080)
    ... def P():
    ...     pass

    >>> isinstance(P(), MultiProcess)
    True
    """
    def _call(*args, **kwargs):
        port = None
        return MultiProcess(func, port, *args, **kwargs)
    _call.func_name = func.func_name
    return _call


# Classes
class MultiProcess(multiprocessing.Process):
    """ Process(func, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    """
    def __init__(self, fn, port, *args, **kwargs):
        multiprocessing.Process.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        # Create 16 byte unique id based on network address, sequence number and time sample.
        self.id = uuid.uuid1().hex
        

        # Channel request state
        self.state = FAIL
        self.result_ch_idx = None
        self.result_msg = None
        
        # Used to ensure the validity of the remote answers
        self.sequence_number = 1L

        # Port address will be set for the SocketDispatcher (one per interpreter/multiprocess)
        if port:
            conf.set(PYCSP_PORT, port)

    def wait(self):
        self.cond.acquire()
        if self.state == READY:
            self.cond.wait()
        self.cond.release()

    def run(self):
        
        # Multiprocessing inherits global objects like singletons. Thus we must reset!
        # Reset SocketDispatcher Singleton object to force the creation of a new
        # SocketDispatcher
        
        SocketDispatcher(reset=True)

        # Create remote lock
        self.cond = threading.Condition()        
        dispatch = SocketDispatcher().getThread()
        self.addr = dispatch.server_addr
        dispatch.registerProcess(self.id, RemoteLock(self))

        try:
            # Do not store the returned value from the process
            # TODO: Consider, whether process should return values
            self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(self.kwargs.values())
        except ChannelRetireException, e:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())

        # Initiate clean up and waiting for channels to finish outstanding operations.
        #print("Deregister %s %s\n" % (self.id, self.fn))
        dispatch.deregisterProcess(self.id)

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
        return [self] + [MultiProcess(self.fn, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

    # syntactic sugar:  2 * Process() == [Process<1>,Process<2>]
    def __rmul__(self, multiplier):
        return [self] + [MultiProcess(self.fn, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

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
                
