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
    from py.magic import greenlet

import threading
import time
import uuid
import os

from communicator import Communicator
from pycsp.common.const import *

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
    >>> time_start = time.time()
    >>> Sequence([P1() for i in range(10)])
    >>> diff = time.time() - time_start
    >>> diff >= 0.5 and diff < 0.6
    True

    In parallel, it should be close to 0.05 seconds.
    >>> time_start = time.time()
    >>> Parallel([P1() for i in range(10)])
    >>> diff = time.time() - time_start
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

        # Check for exception propagation.
        if io_thread.exception:
            raise io_thread.exception

        # Return value from function, set by Io class.
        return io_thread.retval
    return _call_io


# Classes
class Io(threading.Thread):
    """ Io(fn, *args, **kwargs)
    It is recommended to use the @io decorator, to create Io instances.
    See io.__doc__
    """
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.retval = None
        self.exception = None

        self.s = Scheduler()
        self.p = self.s.current

    def run(self):
        try:
            self.retval = self.fn(*self.args, **self.kwargs)
        except Exception, e:
            # Save exception for greenlet.
            self.exception = e

        self.s.io_unblock(self.p)


class MainProcess():
    """
    A special process implementation for the __main__ namespace.
    
    This allows __main__ to communicate with greenlets processes using channels.
    """

    def __init__(self, main_greenlet, scheduler):
        # Create unique id
        self.id = '__main__'

        # Greenlet specific
        self.greenlet = main_greenlet
        
        # Synchronization specific
        self.state = None
        self.s = scheduler

    def setstate(self, new_state):
        self.state = new_state

    # Reschedule, without putting this process on either the next[] or the blocking[] list.
    def wait(self):
        self.s.blocking_on_wait += 1
        while self.state == ACTIVE:
            self.s.getNext().greenlet.switch()
        self.s.blocking_on_wait -= 1

    # Notify, by activating and setting state.    
    def notify(self, new_state, force=False):
        self.state = new_state

        # Only activate, if we are activating someone other than ourselves
        # or we force an activation, which happens when an Io thread finishes, while
        # the calling process is still current process.
        if self.s.current != self or force:
            self.s.activate(self)


class Scheduler(object):
    """
    Scheduler is a singleton class.
    
    It is optimized for fast switching and is not fair.
   
    >>> A = Scheduler()
    >>> B = Scheduler()
    >>> A == B
    True
    """

    __instance = None  # the unique instance

    def __new__(cls, *args, **kargs):
        return cls.getInstance(cls, *args, **kargs)

    def __init__(self):
        pass
    
    def getInstance(cls, *args, **kargs):
        '''Static method to have a reference to **THE UNIQUE** instance'''
        if cls.__instance is None:
            # (Some exception may be thrown...)
            # Initialize **the unique** instance
            cls.__instance = object.__new__(cls)

            # Initialize members for scheduler
            cls.__instance.new = []
            cls.__instance.next = []
            cls.__instance.main_process = MainProcess(greenlet.getcurrent(), cls.__instance)
            cls.__instance.current = cls.__instance.main_process

            # Timer specific  value = (activation time, process)
            # On update we do a sort based on the activation time
            cls.__instance.timers = []
            
            # Event wait set list, that contains processes waiting for events from event threads.
            cls.__instance.event_wait_set = {}

            # Updated with new events from the event threads. Checked by the scheduler on every
            # reschedule cyclus.
            cls.__instance.new_events = []

            # Needed to know, when to quit.
            cls.__instance.blocking_on_wait = 0

            # Register communicator, to ensure that we listen on PYCSP_PORT            
            if os.environ.has_key('PYCSP_PORT'):
                cls.__instance.pycsp_port = int(os.environ['PYCSP_PORT'])
                cls.__instance.communicator = Communicator(cls.__instance)                
            else:
                cls.__instance.pycsp_port = None
                cls.__instance.communicator = None
                
            # Io specific
            cls.__instance.blocking_on_io = 0


            # Condition value to ensure that we can wait for io or events, without risking a deadlock.
            # The Scheduler will go into a wait condition, when the next list is empty. As long as the next list
            # is not empty, the io / events can be handled without going into a wait condition.
            cls.__instance.cond = threading.Condition()

            # Start scheduler greenlet
            cls.__instance.greenlet = greenlet(cls.__instance.main)

        return cls.__instance
    getInstance = classmethod(getInstance)

    # Called by MainThread
    def timer_wait(self, p, seconds):
        new_time = seconds + time.time()

        inserted = False
        for i in xrange(len(self.timers)):
            if new_time < self.timers[i][0]:
                self.timers.insert(i,(new_time, p))
                inserted = True
                break
        
        if not inserted:
            self.timers.append((new_time, p))

    # Called by MainThread
    def timer_cancel(self, p):
        for i in xrange(len(self.timers)):
            if self.timers[i][1] == p:
                self.timers.pop(i)
                break

    # Called by threading.Timer()
    def timer_notify(self):
        self.cond.acquire()
        self.cond.notify()
        self.cond.release()

    # Called from scheduler
    def check_event(self):
        if self.new_events:
            id, package = self.new_events[0]
            p = self.event_wait_set.pop(id, None)
            if p != None:                
                self.new_events.pop(0)
                p.event = package
                p.notify(DONE, force=True)

    # Called from event thread
    def new_event(self, id, package):
        self.cond.acquire()
        self.new_events.append((id, package))
        self.cond.notify()
        self.cond.release()
        print self.new_events

    # Called from greenlet
    def event_wait(self):
        p = self.current
        self.event_wait_set[p.id] = p
        p.event = None
        p.setstate(ACTIVE)
        p.wait()

    # Called from MainThread
    def io_block_prepare(self, p):
        self.cond.acquire()
        self.blocking_on_io += 1
        p.setstate(ACTIVE)
        self.cond.release()
        
    # Called from MainThread
    def io_block_wait(self, p):
        p.wait()

    # Called from io thread
    def io_unblock(self, p):
        self.cond.acquire()
        p.notify(DONE, force=True)
        self.blocking_on_io -= 1
        self.cond.notify()
        self.cond.release()
        
    # Add a list of processes onto the new list.
    def addBulk(self, processes):

        # We reverse the list of added processes, if the total amount of new processes exceeds 1000.
        if len(self.new) + len(processes) > 1000:
            processes.reverse()
            
        self.new.extend(processes)

    # Main loop
    # When all queues are empty all greenlets have been executed.
    # Queues are new, next, timers and "blocking io counter"
    # Greenlets that are either executing, blocking on a channel or blocking on io is not in any lists.
    def main(self):
        while True:
            if self.timers and self.timers[0][0] < time.time():
                _,self.current = self.timers.pop(0)
                self.current.greenlet.switch()
            elif self.new:
                if len(self.new) > 1000:
                    # Pop from end, if the new list might be large.
                    self.current = self.new.pop(-1)
                else:
                    # Pop from beginning to be more fair
                    self.current = self.new.pop(0)
                self.current.greenlet.switch()
            elif self.next:
                # Pop from the beginning
                self.current = self.next.pop(0)
                self.current.greenlet.switch()

            # We enter a critical region, since timer threads or blocking io threads,
            # might try to update the internal queues.
            self.cond.acquire()
            if not (self.next or self.new):
                # Waiting on blocking processes or all processes have finished!
                if self.timers:
                    # Set timer to lowest activation time
                    seconds = self.timers[0][0] - time.time()
                    if seconds > 0:
                        t = threading.Timer(seconds, self.timer_notify)

                        # We don't worry about cancelling, since it makes no difference if timer_notify
                        # is called one more time.
                        t.start()

                        # Now go to sleep
                        self.cond.wait()
                elif self.pycsp_port and self.blocking_on_wait > 0:
                    # Now go to sleep
                    self.cond.wait()
                    self.check_event()
                elif self.blocking_on_io > 0:
                    # Now go to sleep
                    self.cond.wait()
                else:
                    # Execution finished!
                    self.cond.release()
                    self.done = True

                    # Switch to main process and leave the greenlet scheduler
                    # running for continued usage of PyCSP greenlets.
                    self.main_process.greenlet.switch()

                    # If any processes are still blocked, there is a deadlock.
                    if self.blocking_on_wait > 0:
                        raise Exception('Deadlock')

            self.cond.release()
                

    # Join is called from _parallel and will block the greenlet until
    # greenlet processes has been executed.
    def join(self, processes):
        save_current = self.current
        self.done = False

        for p in processes:
            while not p.executed:

                # __main__ check for deadlock
                if self.done:
                    raise Exception('Deadlock')

                # p, not executed yet, switch to any waiting greenlet                    
                self.getNext().greenlet.switch()

        # Restore current
        self.current = save_current

    # Get next greenlet available for scheduling
    def getNext(self):

        # Check for new event
        if self.pycsp_port:
            self.check_event()

        if self.new:
            # Returning scheduler, to avoid exceeding the recursion limit.
            # All new greenlets must be started from the scheduler, to have the
            # scheduler as parent greenlet.
            # Switch to main loop
            return self
        elif self.next:
            # Quick choice
            self.current = self.next.pop(0)
            return self.current
        else:
            # Some processes are blocking or all have been executed.
            # Switch to main loop.
            return self


    def activate(self, process):
        self.next.append(process)

def current_process_id():
    s = Scheduler()
    g = s.current
    return g.id


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
