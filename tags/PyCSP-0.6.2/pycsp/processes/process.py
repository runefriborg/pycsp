"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import multiprocessing as mp
import types
import cPickle as pickle
import sys

from channel import ChannelPoisonException, ChannelRetireException, Channel, ShmManager
from channelend import ChannelEndRead, ChannelEndWrite

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Decorators
def process(func):
    """
    @process decorator for creating process functions

    >>> @process
    ... def P():
    ...     pass

    >>> isinstance(P(), Process)
    True
    """
    if sys.platform == 'win32':
        raise Exception('The @process decorator is not supported in win32.')

    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call

def io(func):
    """
    @io decorator for blocking io operations.
    In PyCSP.processes it has no effect, other than compatibility

    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)

    >>> sleep(0.01)
    """
    return func

# Classes
class Process(mp.Process):
    """ Process(...)
    """
    def __init__(self, fn, *args, **kwargs):
        mp.Process.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

        # This reference is created to pass the ShmManager by inheritance.
        # It is required for PyCSP.processes to work in win32, since processes are not forked
        # but instead started in new python interpreters. Setting self.manager
        # here ensures, that the multiprocessing module pickles this instance and
        # recreates it in the new python interpreter.
        self.manager = ShmManager(allocate=True)

    def run(self):
        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channels and channel ends
            self.__check_poison(self.args)
        except ChannelRetireException, e:
            # look for channel ends
            self.__check_retire(self.args)

    def __check_poison(self, args):
        for arg in args:
            if isinstance(arg, ChannelEndRead) or isinstance(arg, ChannelEndWrite) or isinstance(arg, Channel):
                arg.poison()
            elif types.ListType == type(arg):
                self.__check_poison(arg)
            elif types.DictType == type(arg):
                self.__check_poison(arg.keys)
                self.__check_poison(arg.values)

    def __check_retire(self, args):
        for arg in args:
            if isinstance(arg, ChannelEndRead) or isinstance(arg, ChannelEndWrite):
                # Ignore if try to retire an already retired channel end.
                try:
                    arg.retire()
                except ChannelRetireException:
                    pass
            elif types.ListType == type(arg):
                self.__check_retire(arg)
            elif types.DictType == type(arg):
                self.__check_retire(arg.keys)
                self.__check_retire(arg.values)

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
                if isinstance(item, ChannelEndRead):
                    R.append(item.channel.reader())
                elif isinstance(item, ChannelEndWrite):
                    R.append(item.channel.writer())
                elif item == types.ListType or item == types.DictType:
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
                if isinstance(key, ChannelEndRead):
                    R[key.channel.reader()] = args[key]
                elif isinstance(key, ChannelEndWrite):
                    R[key.channel.writer()] = args[key]
                elif isinstance(args[key], ChannelEndRead):
                    R[key] = args[key].channel.reader() 
                elif isinstance(args[key], ChannelEndWriter):
                    R[key] = args[key].channel.writer() 
                elif args[key] == types.ListType or args[key] == types.DictType:
                    R[key] = self.__mul_channel_ends(args[key])
            return R
        return args


# Functions
def Parallel(*plist):
    """ Parallel(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)

    >>> @process
    ... def P2(cin):
    ...     for i in range(10):
    ...         cin()
    
    >>> C = [Channel() for i in range(10)]
    >>> Cin = map(IN, C)
    >>> Cout = map(OUT, C)
    
    >>> Parallel([P1(Cout[i], i) for i in range(10)],[P2(Cin[i]) for i in range(10)])
    """
    _parallel(plist, True)

def Spawn(*plist):
    """ Spawn(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout, id):
    ...     for i in range(10):
    ...         cout(id)
    
    >>> C = Channel()
    >>> Spawn([P1(OUT(C), i) for i in range(10)])
    
    >>> L = []
    >>> cin = IN(C)
    >>> for i in range(100):
    ...    L.append(cin())
    
    >>> len(L)
    100
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
    The Sequence construct returns when all given processes exit.
    >>> from __init__ import *
    
    >>> @process
    ... def P1(cout):
    ...     Sequence([Process(cout,i) for i in range(10)])
    
    >>> C = Channel()
    >>> Spawn(P1(OUT(C)))
    
    >>> L = []
    >>> cin = IN(C)
    >>> for i in range(10):
    ...    L.append(cin())
    
    >>> L
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    """
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    for p in processes:
        # Call Run directly instead of start() and join() 
        p.run()


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
