"""
Scheduler and Io module

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
try: from greenlet import greenlet
except ImportError, e:
    try: from py.magic import greenlet
    except ImportError, e: 
        sys.stderr.write("PyCSP.greenlets requires the greenlet module, recommended version is 0.2 and is\navailable from http://pypi.python.org/pypi/greenlet/.\n\n")
        raise ImportError(e)
import threading
import time
import heapq
import pycsp.greenlets.scheduling
from pycsp.greenlets.const import *

def Now():
  return time.time() 

def Wait(seconds):
    """Wrapper function for timer_wait. Will schedule the process for later activation and then switch active process. """
    logging.debug("%s calling Wait()"%RT_Scheduler().current)
    RT_Scheduler().timer_wait(RT_Scheduler().current, seconds)
    t = Now()+seconds
    p = RT_Scheduler().getNext() 
    p.greenlet.switch()
    while Now()<t:
      p = RT_Scheduler().getNext() 
      logging.warning("Wait did not wait correct.Now:%d, should wait until: %d ,swicthing from %s to %s"%(Now(),t,Simulation().current, p))
      p.greenlet.switch()

# Decorators
def io(func):
    """
    @io decorator for blocking io operations.
    Execution is moved to seperate threads and the current greenlet is yielded.

    >>> from __init__ import *

    >>> @io
    ... def sleep(n):
    ...     import time
    ...     time.sleep(n)

    >>> @process
    ... def P1():
    ...     sleep(0.05)

    Sleeping for 10 times 0.05 seconds, which equals roughly half a second
    in the sequential case.
    >>> import time
    >>> time_start = time.time()
    >>> Sequence([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> logging.debug("diff:0.5 <=  %f < 0.6"%diff)
    >>> diff >= 0.5 and diff < 0.6
    True

    In parallel, it should be close to 0.05 seconds.
    >>> time_start = time.time()
    >>> Parallel([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> #logging.warning("diff:0.05 <=  %f < 0.6"%diff)
    >>> diff >= 0.05 and diff < 0.1
    True
    """
    def _call_io(*args, **kwargs):
        io_thread = Io(func, *args, **kwargs)

        if io_thread.p == None:
          # We are not executed from a greenlet
            # Run io code and quit
            return func(*args, **kwargs)
        
        io_thread.s.io_block_prepare(io_thread.p)
        io_thread.start()
        io_thread.s.io_block_wait(io_thread.p)

        # Return value from function, set by Io class.
        return io_thread.retval
    return _call_io


# Classes
class Io(pycsp.greenlets.Io):
    """ Io(fn, *args, **kwargs)
    It is recommended to use the @io decorator, to create Io instances.
    See io.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
        pycsp.greenlets.Io.__init__(self,fn,*args,**kwargs)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.retval = None

        self.s = RT_Scheduler()
        self.p = self.s.current
        logging.debug("init Io, current: %s,\nself: %s"%(self.s.current,self.s))

class RT_Scheduler(pycsp.greenlets.scheduling.Scheduler):
    """
    Scheduler is a singleton class.
    
    It is optimized for fast switching and is not fair.
   
    >>> A = RT_Scheduler()
    >>> B = RT_Scheduler()
    >>> A == B
    True
    """

    __instance = None  # the unique instance

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pycsp.greenlets.scheduling.Scheduler.__init__(self)
        pass

    def decompose(self):
        pycsp.greenlets.scheduling.Scheduler.decompose(self)
        RT_Scheduler.__Scheduler__instance = None

    def __str__(self):
        return "%r\ncurrent:%r, n# blocking:%d \nqueues. \n\tnew:\t%s\n\ttimers:\t%s\n\tnext:\t%s "%(self,self.current, self.blocking,self.new,self.timers,self.next)
    def decompose(self):
      self.__Scheduler__instance = None

    def getInstance(cls, *args, **kargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # (Some exception may be thrown...)
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)

            # Initialize members for scheduler
            cls.__instance.new = []
            cls.__instance.next = []
            cls.__instance.current = None
            cls.__instance.greenlet = greenlet.getcurrent()

            # Timer specific  value = (activation time, process)
            # On update we do a sort based on the activation time
            cls.__instance.timers = []

            # Io specific
            cls.__instance.cond = threading.Condition()
            cls.__instance.blocking = 0

        return cls.__instance
    getInstance = classmethod(getInstance)


    # Main loop
    # When all queues are empty all greenlets have been executed.
    # Queues are new, next, timers and "blocking io counter"
    # Greenlets that are either executing, blocking on a channel or blocking on io is not in any lists.
    def main(self):
        logging.debug("entering main, current:%s"%self.current)
        while True:
            if self.timers and self.timers[0][0] < time.time():
                _,process = heapq.heappop(self.timers)
                self.activate(process)
            elif self.new:
                if len(self.new) > 1000:
                    # Pop from end, if the new list might be large.
                    self.current = self.new.pop(-1)
                else:
                    # Pop from beginning to be more fair
                    self.current = self.new.pop(0)
                logging.debug("main:switching to new %s"%self.current)
                self.current.greenlet.switch()
            elif self.next:
                # Pop from the beginning
                _,self.current = heapq.heappop(self.next)
                logging.debug("main:switching to next %s"%self.current)
                self.current.greenlet.switch()

            # We enter a critical region, since timer threads or blocking io threads,
            # might try to update the internal queues.
            logging.debug("Aquire lock")
            self.cond.acquire()
            logging.debug("Aquired")
            if not (self.next or self.new):
                # Waiting on blocking processes or all processes have finished!
                if self.timers:
                    # Set timer to lowest activation time
                    seconds = self.timers[0][0] - Now()
                    #logging.Debug("will wait for %d seconds",seconds)
                    if seconds > 0:
                        t = threading.Timer(seconds, self.timer_notify)

                        # We don't worry about cancelling, since it makes no difference if timer_notify
                        # is called one more time.
                        t.start()

                        # Now go to sleep
                        self.cond.wait()

                elif self.blocking > 0:
                    logging.debug("blocking processes, will sleep")
                    # Now go to sleep
                    self.cond.wait()
                    logging.debug("done sleeping")
                else:
                    # Execution finished!
                    self.cond.release()
                    return
            self.cond.release()
                

    # Join is called from _parallel and will block the greenlet until
    # greenlet processes has been executed.
    def join(self, processes):
        if self.greenlet == greenlet.getcurrent():
            # Called from main greenlet
            self.main()
            
            for p in processes:
                if not p.executed:
                    raise Exception("Deadlock!!! - Have you correctly closed all procceses?")

        else:
            # Called from child greenlet
            for p in processes:
                while not p.executed:
                    # p, not executed yet, switch to any waiting greenlet
                    self.getNext().greenlet.switch()



    # Get next greenlet available for scheduling
    def getNext(self):
        if self.new:
            # Returning scheduler, to avoid exceeding the recursion limit.
            # All new greenlets must be started from the scheduler, to have the
            # scheduler as parent greenlet.
            # Switch to main loop
            logging.debug("getNext returns scheduler")
            return self
        elif self.next:
            # Quick choice
            #print "choosing a next",self.next
            logging.debug("getNext returns from next")
            _,self.current = heapq.heappop(self.next)
            return self.current
        else:
            # Some processes are blocking, are in timers or all have been executed.
            # Switch to main loop.
            logging.debug("getNext returns scheduler because some is blocking or are in timers sched:%s",self)
            return self


    def activate(self, process):
      logging.debug("activate: %s"%process)
      heapq.heappush(self.next,(process.internal_priority,process))
      #self.next.append(process)


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
