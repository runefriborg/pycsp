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
import inspect, sys
import types
import threading
import time, random
from channel import ChannelPoisonException, ChannelRetireException, ChannelFailstopException, ChannelRetireLikeFailstopException, ChannelRollBackException, Channel
from channelend import ChannelEndRead, ChannelEndWrite
from pycsp.common.const import *

# Decorators
def process(func=None, **options):
    """
    @process decorator for creating process functions

    >>> @process
    ... def P():
    ...     pass

    >>> isinstance(P(), Process)
    True

    Processes can have a fail_type.
    This is checked when failing.

    >>> @process(fail_type=FAILSTOP)
    ... def P():
    ...     1/0
    """
    if func != None:
        def _call(*args, **kwargs):
            return Process(func, options, *args, **kwargs)            
        return _call
    else:
        def _func(func):
            return process(func, **options)
        return _func

def io(func):
    """
    @io decorator for blocking io operations.
    In PyCSP threading it has no effect, other than compatibility

    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)

    >>> sleep(0.01)
    """
    return func

def load_variables(*pargs):
    stack = inspect.stack()
        
    try:
        process_ = stack[3][0].f_locals
    finally:
        del stack
    
    loaded_vars = process_['self'].vars
    
    var = []
    for __x in pargs:
        if __x[0] in loaded_vars: 
            var.append(loaded_vars[__x[0]])
        else:
            var.append(__x[1])
    
    if len(var) == 1:
        return var[0]
    else:
        return var

def load(**kwargs):
    if len(kwargs) > 1:
        raise AttributeError

    for __x, __v in kwargs.iteritems():
        return load_variables((__x, __v))

# Classes
class Process(threading.Thread):
    """ Process(func, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances
    """
    def __init__(self, fn, options, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        
        self.fail_type = None
        if options is not None and 'fail_type' in options:
            self.fail_type = options['fail_type']
        
        self.args = args
        self.kwargs = kwargs
        
        # Create unique id
        self.id = str(random.random())+str(time.time())

        self.options = options
        self.vars = {}

        self.print_error = False
        if options is not None and 'print_error' in options:
            self.print_error = options['print_error']

        self.max_retries = CHECKPOINT_RETRIES
        if options is not None and 'retries' in options:
            self.max_retries = options['retries']

        self.retries = 0

        self.fail_type_after_retries = self.__check_retirelike
        if options is not None and 'fail_type_after_retries' in options:
            if options['fail_type_after_retries'] == FAILSTOP:
                self.fail_type_after_retries = self.__check_failstop

    def run(self):
        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
            # The process is done
            # It should auto retire all of its channels
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())
        except ChannelPoisonException:
            # look for channels and channel ends
            self.__check_poison(self.args)
            self.__check_poison(self.kwargs.values())
        except ChannelRetireException:
            # look for channel ends
            self.__check_retire(self.args)
            self.__check_retire(self.kwargs.values())
        except ChannelFailstopException:
            self.__check_failstop(self.args)
            self.__check_failstop(self.kwargs.values())
        except ChannelRetireLikeFailstopException:
            self.__check_retirelike(self.args)
            self.__check_retirelike(self.kwargs.values())
        except ChannelRollBackException:
            # Another process sharing a channel with this one
            # has rolled back, so we must as well.
            self.run()
        except Exception as e:
            if self.print_error:
                print e
            
            fail_type_fn = None
            rerun = False
            
            if self.fail_type == FAILSTOP:
                fail_type_fn = self.__check_failstop
            elif self.fail_type == RETIRELIKE:
                fail_type_fn = self.__check_retirelike
            elif self.fail_type == CHECKPOINT:
                if self.max_retries != -1 and self.retries >= self.max_retries:
                    fail_type_fn = self.fail_type_after_retries
                else:
                    rerun = True
                    fail_type_fn = self.__check_checkpointing

            if fail_type_fn is not None:
                fail_type_fn(self.args)
                fail_type_fn(self.kwargs.values())

            if rerun:
                self.retries += 1
                self.run()      

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
                    except ChannelRetireLikeFailstopException:
                        pass
            except AttributeError:
                pass

    def __check_failstop(self, args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_failstop(arg)
                elif types.DictType == type(arg):
                    self.__check_failstop(arg.keys())
                    self.__check_failstop(arg.values())
                elif type(arg.failstop) == types.UnboundMethodType:
                    arg.failstop()
            except AttributeError:
                pass

    def __check_retirelike(self, args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_retirelike(arg)
                elif types.DictType == type(arg):
                    self.__check_retirelike(arg.keys())
                    self.__check_retirelike(arg.values())
                elif type(arg.retirelike) == types.UnboundMethodType:
                    # Ignore if try to retire an already retired channel end.
                    try:
                        arg.retirelike()
                    except ChannelRetireLikeFailstopException:
                        pass
                    except ChannelRetireException:
                        pass
            except AttributeError:
                pass

    def __check_checkpointing(self, args):
        for arg in args:
            try:
                if types.ListType == type(arg) or types.TupleType == type(arg):
                    self.__check_checkpointing(arg)
                elif types.DictType == type(arg):
                    self.__check_checkpointing(arg.keys())
                    self.__check_checkpointing(arg.values())
                elif type(arg.rollback) == types.UnboundMethodType:
                    # Our argument is a channel
                    arg.rollback()
            except AttributeError:
                pass

    # syntactic sugar:  Process() * 2 == [Process<1>,Process<2>]
    def __mul__(self, multiplier):
        return [self] + [Process(self.fn, self.options, *self.__mul_channel_ends(self.args), **self.__mul_channel_ends(self.kwargs)) for i in range(multiplier - 1)]

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
    >>> Cin = [chan.reader() for chan in C]
    >>> Cout = [chan.writer() for chan in C]
    
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
    >>> Spawn([P1(C.writer(), i) for i in range(10)])
    
    >>> L = []
    >>> cin = C.reader()
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
    >>> Spawn(P1(C.writer()))
    
    >>> L = []
    >>> cin = C.reader()
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
            return '__main__'
    return t.id

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
