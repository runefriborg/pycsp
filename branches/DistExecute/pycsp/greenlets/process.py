"""
Processes and execution

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
"Permission is hereby granted, free of charge, to any person obtaining
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
from greenlet import greenlet
import types
from scheduling import Scheduler
from channel import ChannelPoisonException, ChannelRetireException, Channel
from channelend import ChannelEndRead, ChannelEndWrite
from const import *

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
    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call

# Classes
class Process():
    """ Process(fn, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    See process.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

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
        try:
            # Store the returned value from the process
            self.executed = False
            self.fn(*self.args, **self.kwargs)
            self.executed = True
        except ChannelPoisonException, e:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(self.kwargs.values())
        except ChannelRetireException, e:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())

    def __check_poison(self, args):
        for arg in args:
            if isinstance(arg, ChannelEndRead) or isinstance(arg, ChannelEndWrite) or isinstance(arg, Channel):
                arg.poison()
            elif types.ListType == type(arg):
                self.__check_poison(arg)
            elif types.DictType == type(arg):
                self.__check_poison(arg.keys())
                self.__check_poison(arg.values())

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
                self.__check_retire(arg.keys())
                self.__check_retire(arg.values())

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
                elif item == types.ListType or item == types.DictType or item == types.TupleType:
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
                elif args[key] == types.ListType or args[key] == types.DictType or args[key] == types.TupleType:
                    R[key] = self.__mul_channel_ends(args[key])
            return R
        return args


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
    
    >>> C = [Channel(str(i)) for i in range(10)]
    >>> Cin = map(IN, C)
    >>> Cout = map(OUT, C)
    
    >>> Parallel([P1(Cout[i], i) for i in range(10)],[P2(Cin[i]) for i in range(10)])
    """
    _parallel(plist, True)

def Spawn(*plist):
    """ Spawn(P1, [P2, .. ,PN])
    >>> from __init__ import *
    
    >>> @process
    ... def WrapP():
    ...     @process
    ...     def P1(cout, id):
    ...         for i in range(10):
    ...             cout(id)
    ...     
    ...     C = Channel()
    ...     Spawn([P1(OUT(C), i) for i in range(10)])
    ...     
    ...     L = []
    ...     cin = IN(C)
    ...     for i in range(100):
    ...        L.append(cin())
    ...     
    ...     print len(L)

    >>> Parallel(WrapP())
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

    s = Scheduler()
    s.addBulk(processes)

    if block:
        s.join(processes)

       
def Sequence(*plist):
    """ Sequence(P1, [P2, .. ,PN])
    The Sequence construct returns when all given processes exit.
    >>> from __init__ import *

    >>> @process
    ... def WrapP():
    ...     @process
    ...     def P1(cout):
    ...         Sequence([Process(cout,i) for i in range(10)])
    ...     
    ...     C = Channel()
    ...     Spawn(P1(OUT(C)))
    ...     
    ...     L = []
    ...     cin = IN(C)
    ...     for i in range(10):
    ...        L.append(cin())
    ...     
    ...     print L
    
    >>> Parallel(WrapP())
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
    
