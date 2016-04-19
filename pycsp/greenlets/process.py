"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
try: from greenlet import greenlet
except ImportError as e:
    from py.magic import greenlet

import time, random
import types
from pycsp.greenlets.scheduling import Scheduler
from pycsp.greenlets.channel import ChannelPoisonException, ChannelRetireException
from pycsp.common.const import *

# Decorators
def process(func):
    """
    @process decorator for creating process functions
    """
    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call

# Classes
class Process(object):
    """ Process(fn, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    See process.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.return_value = None

        # Create unique id
        self.id = str(random.random())+str(time.time())

        # Greenlet specific
        self.greenlet = None
        
        # Synchronization specific
        self.state = None
        self.s = Scheduler()
        self.executed = False

    def setstate(self, new_state):
        self.state = new_state

    # Reschedule, without putting this process on either the next[] or the blocking[] list.
    def wait(self):
        while self.state == ACTIVE:
            self.s.getNext().greenlet.switch()

    # Notify, by activating and setting state.    
    def notify(self, new_state, force=False):
        self.state = new_state

        # Only activate, if we are activating someone other than ourselves
        # or we force an activation, which happens when an Io thread finishes, while
        # the calling process is still current process.
        if self.s.current != self or force:
            self.s.activate(self)


    # Init greenlet code
    # It must be called from the main thread.
    # Since we are only allowing that processes may be created in the main
    # thread or in other processes we can be certain that we are running in
    # the main thread.
    def start(self):
        self.greenlet = greenlet(self.run)

    # Main process execution
    def run(self):
        self.executed = False
        try:
            self.return_value = self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(list(self.kwargs.values()))
        except ChannelRetireException:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(list(self.kwargs.values()))
        self.executed = True
            

    def __check_poison(self, args):
        for arg in args:
            try:
                if list == type(arg) or tuple == type(arg):
                    self.__check_poison(arg)
                elif dict == type(arg):
                    self.__check_poison(list(arg.keys()))
                    self.__check_poison(list(arg.values()))
                elif type(arg.poison) == types.MethodType:
                    arg.poison()
            except AttributeError:
                pass

    def __check_retire(self, args):
        for arg in args:
            try:
                if list == type(arg) or tuple == type(arg):
                    self.__check_retire(arg)
                elif dict == type(arg):
                    self.__check_retire(list(arg.keys()))
                    self.__check_retire(list(arg.values()))
                elif type(arg.retire) == types.MethodType:
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
        if list == type(args) or tuple == type(args):
            R = []
            for item in args:
                try:                    
                    if type(item.isReader) == types.MethodType and item.isReader():
                        R.append(item.channel.reader())
                    elif type(item.isWriter) == types.MethodType and item.isWriter():
                        R.append(item.channel.writer())
                except AttributeError:
                    if item == list or item == dict or item == tuple:
                        R.append(self.__mul_channel_ends(item))
                    else:
                        R.append(item)

            if tuple == type(args):
                return tuple(R)
            else:
                return R
            
        elif dict == type(args):
            R = {}
            for key in args:
                try:
                    if type(key.isReader) == types.MethodType and key.isReader():
                        R[key.channel.reader()] = args[key]
                    elif type(key.isWriter) == types.MethodType and key.isWriter():
                        R[key.channel.writer()] = args[key]
                    elif type(args[key].isReader) == types.MethodType and args[key].isReader():
                        R[key] = args[key].channel.reader()
                    elif type(args[key].isWriter) == types.MethodType and args[key].isWriter():
                        R[key] = args[key].channel.writer()
                except AttributeError:
                    if args[key] == list or args[key] == dict or args[key] == tuple:
                        R[key] = self.__mul_channel_ends(args[key])
                    else:
                        R[key] = args[key]
            return R
        return args


def Parallel(*plist):
    """ Parallel(P1, [P2, .. ,PN])

    Returns a list of return values from P1..PN
    """
    return _parallel(plist, True)

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

    s = Scheduler()
    s.addBulk(processes)

    if block:
        s.join(processes)
        return [p.return_value for p in processes]
    
       
def Sequence(*plist):
    """ Sequence(P1, [P2, .. ,PN])

    Returns a list of return values from P1..PN
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

    s = Scheduler()
    _p = s.current
    _p_original_id = _p.id
    return_values = []
    for p in processes:
        _p.id = p.id

        # Call Run directly instead of start() and join() 
        p.run()
        return_values.append(p.return_value)
    _p.id = _p_original_id
    return return_values

def current_process_id():
    s = Scheduler()
    g = s.current
    return g.id
    
