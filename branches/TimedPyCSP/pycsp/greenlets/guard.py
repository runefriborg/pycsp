"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import threading
from scheduling import Scheduler
from channel import ChannelReq
from process import Process

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# Classes
class Guard():
    """
    The empty interface of a guard.
    """
    def post_read(self, req):
        pass

    def post_write(self, req):
        pass

    def remove_read(self, req):
        pass

    def remove_write(self, req):
        pass


class Skip(Guard):
    """
    Skip will try to accept a read or a write, the moment it is posted.
    
    >>> from __init__ import *

    >>> @process 
    ... def P():
    ...     C = Channel()
    ...     Cin = IN(C)
    ...     (g, msg) = Alternation([{Skip():None}, {Cin:None}]).select()
    ...     print isinstance(g, Skip) and msg == None

    >>> Parallel(P())
    True
    """

    def empty(self):
        pass

    # Start process
    def process(self):
        p = Process(self.empty)
        p.start()
        p.setstate(ACTIVE)
        return p
        
    # Offer instantly
    def post_read(self, reader):
        ChannelReq(self.process(), msg=None).offer(reader)
        
    # Offer instantly
    def post_write(self, writer):
        writer.offer(ChannelReq(self.process()))


class Timeout(Guard):
    """
    Timeout spawns a timer thread, when posted. If removed
    before timeout, then the timer thread is cancelled.
    
    >>> from __init__ import *
    >>> import time

    >>> @process 
    ... def P():
    ...     C = Channel()
    ...     Cin = IN(C)
    ...     time_start = time.time()
    ...     (g, msg) = Alternation([{Timeout(seconds=0.5):None}, {Cin:None}]).select()
    ...     time_passed = time.time() - time_start
    ...     print time_passed >= 0.5
    ...     print time_passed < 0.6
    ...     print isinstance(g, Timeout) and msg == None
    
    >>> Parallel(P())
    True
    True
    True
    """

    def __init__(self, seconds):
        self.seconds = seconds
        self.posted = (None, None)
        self.s = Scheduler()
        self.p = None

    # Timer expired, offer an active Channel Request
    def expire(self):
        op, req = self.posted
        if op == READ:
            ChannelReq(self.p, msg=None).offer(req)
        elif op == WRITE:
            req.offer(ChannelReq(self.p))

    def post_read(self, reader):
        self.posted = (READ, reader)

        # Start process
        self.p = Process(self.expire)
        self.p.start()
        self.p.setstate(ACTIVE)

        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)

    def post_write(self, writer):
        self.posted = (WRITE, writer)

        # Start process
        self.p = Process(self.expire)
        self.p.start()
        self.p.setstate(ACTIVE)

        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)
  
    def remove_read(self, req):
        self.s.timer_cancel(self.p)

    def remove_write(self, req):
        self.s.timer_cancel(self.p)


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
