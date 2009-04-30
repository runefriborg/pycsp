"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import threading
from channel import ChannelReq, ReqStatus

# Constants
ACTIVE, DONE, POISON = range(3)
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

    def poison(self):
        pass


class Skip(Guard):
    """
    Skip will try to accept a read or a write, the moment it is posted.
    
    >>> from __init__ import *

    >>> C = Channel()
    >>> Cin = IN(C)
    >>> (g, msg) = Alternation([{Skip():None}, {Cin:None}]).select()

    >>> isinstance(g, Skip) and msg == None
    True
    """

    # Offer instantly
    def post_read(self, reader):
        ChannelReq(ReqStatus(), msg=None).offer(reader)
        
    # Offer instantly
    def post_write(self, writer):
        writer.offer(ChannelReq(ReqStatus()))


class Timeout(Guard):
    """
    Timeout spawns a timer thread, when posted. If removed or poisoned
    before timeout, then the timer thread is cancelled.
    
    >>> from __init__ import *
    >>> import time

    >>> C = Channel()
    >>> Cin = IN(C)

    >>> time_start = time.time()
    >>> (g, msg) = Alternation([{Timeout(seconds=0.5):None}, {Cin:None}]).select()
    >>> time_passed = time.time() - time_start
    >>> time_passed > 0.5 and time_passed < 0.6
    True

    >>> isinstance(g, Timeout) and msg == None
    True
    """

    def __init__(self, seconds):
        self.seconds = seconds
        self.posted = (None, None)

    # Timer expired, offer an active Channel Request
    def expire(self):
        op, req = self.posted
        if op == READ:
            ChannelReq(ReqStatus(), msg=None).offer(req)
        elif op == WRITE:
            req.offer(ChannelReq(ReqStatus()))

    def post_read(self, reader):
        self.posted = (READ, reader)
        self.timer = threading.Timer(self.seconds, self.expire)
        self.timer.start()

    def post_write(self, writer):
        self.posted = (WRITE, writer)
        self.timer = threading.Timer(self.seconds, self.expire)
        self.timer.start()
  
    def remove_read(self, req):
        self.timer.cancel()

    def remove_write(self, req):
        self.timer.cancel()

    def poison(self):
        self.timer.cancel()


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
