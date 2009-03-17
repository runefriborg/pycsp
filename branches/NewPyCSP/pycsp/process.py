import threading

from channel import ChannelPoisonException, Channel
from channelend import ChannelEndRead, ChannelEndWrite

ACTIVE, CANCEL, DONE, POISON = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)


def process(func):
    "Decorator for creating process functions"
    def _call(*args, **kwargs):
        return Process(func, *args, **kwargs)
    return _call


class Process(threading.Thread):
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    def run(self):
        self.retval = None
        try:
            # Store the returned value from the process
            self.retval = self.fn(*self.args, **self.kwargs)
        except ChannelPoisonException, e:
            # look for channel ends
            for ch in [x for x in self.args if isinstance(x, ChannelEndRead) or isinstance(x, ChannelEndWrite) or isinstance(x, Channel)]:
                ch.poison()

def Parallel(*plist):
    _parallel(plist, True)

def Spawn(*plist):
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

        # return a list of the return values from the processes
        return [p.retval for p in processes]

    return
    
def Sequence(*processes):
    """Sequence construct. Takes a list of processes (Python threads) which are started.
    The Sequence construct returns when all given processes exit."""
    for p in processes:
        # Call Run directly instead of start() and join() 
        p.run()
    # return a list of the return values from the processes
    return [p.retval for p in processes]
