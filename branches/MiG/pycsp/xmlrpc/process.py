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
import xmlrpclib
import types
import threading
import time, random, sys
from channel import ChannelPoisonException, ChannelRetireException
from net import Channel
from channelend import ChannelEndRead, ChannelEndWrite
from pycsp.common.const import *

import socket
HOSTNAME = socket.gethostname().replace('-','').replace('.','')

# Decorators
def process(func):
    """
    @process decorator for creating process functions
    """
    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call

def io(func):
    """
    @io decorator for blocking io operations.
    In PyCSP threading it has no effect, other than compatibility
    """
    return func


# Classes
class Process(threading.Thread):
    """ Process(...)
    It is recommended to use the @process decorator, to create Process instances
    """
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        # Create unique id
        self.id = str(random.random())+str(time.time())

    def run(self):
        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
        except xmlrpclib.Fault, e:
            if not (e.faultString.find("ChannelPoisonException") == -1):
                # look for channels and channel ends
                self.__check_poison(self.args)
                self.__check_poison(self.kwargs.values())
            elif not (e.faultString.find("ChannelRetireException") == -1):
                # look for channel ends
                self.__check_retire(self.args)
                self.__check_retire(self.kwargs.values())


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
    """
    _parallel(plist, True)

def Spawn(*plist):
    """ Spawn(P1, [P2, .. ,PN])
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

    
def Sequence(*plist):
    """ Sequence(P1, [P2, .. ,PN])
    """
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    # For every process we simulate a new process_id. When executing
    # in Main thread/process we set the new id in a global variable.
    try:
        # compatible with Python 2.6+
        t = threading.current_thread()
        name = t.name
    except AttributeError:
        # compatible with Python 2.5- 
        t = threading.currentThread()
        name = t.getName()

    if name == 'MainThread':
        global MAINTHREAD_ID
        for p in processes:
            MAINTHREAD_ID = p.id

            # Call Run directly instead of start() and join() 
            p.run()
        del MAINTHREAD_ID
    else:
        t_original_id = t.id
        for p in processes:
            t.id = p.id

            # Call Run directly instead of start() and join() 
            p.run()
        t.id = t_original_id

def current_process_id():
    try:
        # compatible with Python 2.6+
        t = threading.current_thread()
        name = t.name
    except AttributeError:
        # compatible with Python 2.5- 
        t = threading.currentThread()
        name = t.getName()

    if name == 'MainThread':
        try:
            return MAINTHREAD_ID        
        except NameError:            
            return HOSTNAME+'__main__'
    return t.id


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
