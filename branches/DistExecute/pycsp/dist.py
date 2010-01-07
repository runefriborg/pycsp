
import daemonNet
from pycsp.net import *

import inspect
import types
import sys
import cPickle as pickle

def Init(secretKey):
    Setup(secretKey=secretKey)
    if 'run_from_daemon' in sys.argv:
        func_name = sys.argv[-1]
        stdindata = ''.join(sys.stdin.readlines())
        args, kwargs = pickle.loads(stdindata)

        # Fetch main namespace and execution function
        g = inspect.currentframe().f_back.f_globals
        if g.has_key(func_name):
            # we need to use run, to execute here
            g[func_name](*args, **kwargs).run()
        sys.exit(0)


spawn_doc = Spawn.__doc__
def Spawn(*plist):
    processes=[]
    for p in plist:
        if type(p)==list:
            for q in p:
                processes.append(q)
        else:
            processes.append(p)

    for p in processes:
        p.start(use_join_chan = False)
Spawn.__doc__ = spawn_doc



class Process():
    """ Process(func, *args, **kwargs)
    It is recommended to use the @process decorator, to create Process instances

    Currently we only send processes to daemons when they are started using Parallel() and Spawn().
    Sequential() will execute processes locally.
    """
    def __init__(self, fn, *args, **kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    
    def start(self, use_join_chan = True):
        # Send process to pycsp-daemon
        if use_join_chan:
            join_chan = daemonNet.Channel()
            self.wait_for_term = join_chan.reader()
            reply = join_chan.writer()
        else:
            reply = None

        Setup().send((self.fn.func_name, inspect.getsourcefile(self.fn), pickle.dumps((self.args, self.kwargs), protocol=pickle.HIGHEST_PROTOCOL), reply))

    def join(self):
        stdoutdata, stderrdata = self.wait_for_term()
        if stdoutdata: sys.stdout.write(stdoutdata)
        if stderrdata: sys.stderr.write(stderrdata)

        # lacking garbage collection of join_chan

        # process joined
        return

    def run(self):
        #self.fn(*self.args, **self.kwargs)
        #return

        try:
            # Store the returned value from the process
            self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channels and channel ends
            for ch in [x for x in self.args if isinstance(x, ChannelEndRead) or isinstance(x, ChannelEndWrite) or isinstance(x, Channel)]:
                ch.poison()
        except ChannelRetireException, e:
            # look for channel ends
            for ch_end in [x for x in self.args if isinstance(x, ChannelEndRead) or isinstance(x, ChannelEndWrite)]:
                # Ignore if try to retire an already retired channel end.
                try:
                    ch_end.retire()
                except ChannelRetireException:
                    pass


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
    _call.func_name = func.func_name    
    return _call


class Setup(object):
    """
    Setup is a singleton class.
    """
    __instance = None  # the unique instance
    __conf = {}

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self, *args, **kargs):
        pass
    
    def getInstance(cls, *args, **kargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)

            daemonNet.Configuration().set(daemonNet.NET_SERVER_ID, 'daemonNet')
            
            if kargs.has_key('secretKey'):
                cls.__instance.secretKey = kargs['secretKey']
                cls.__instance.sendToAnyNode = daemonNet.OUT(daemonNet.Channel('AnyDaemon'))
            else:
                raise Exception('Setup class lacks configuration, please set secretKey')
        return cls.__instance
    getInstance = classmethod(getInstance)

    def send(self, o):
        self.sendToAnyNode((self.secretKey, o))
        
        

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
    
