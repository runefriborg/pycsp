"""
Adds Skip and Timeout guards

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
from pycsp.greenlets.scheduling import Scheduler
from pycsp.greenlets.channel import ChannelReq
from pycsp.greenlets.process import Process
from pycsp.common.const import *

# Classes
class Guard(object):
    """
    The empty interface of a guard.
    """
    def _post_read(self, req):
        pass

    def _post_write(self, req):
        pass

    def _remove_read(self, req):
        pass

    def _remove_write(self, req):
        pass


class SkipGuard(Guard):
    """
    Skip will try to accept a read or a write, the moment it is posted.
    """
    def __init__(self, action=None):
        self.g = (self, action)

    def empty(self):
        pass

    # Start process
    def process(self):
        p = Process(self.empty)
        p.start()
        p.setstate(ACTIVE)
        return p
        
    # Offer instantly
    def _post_read(self, reader):
        ChannelReq(self.process(), msg=None).offer(reader)
        
    # Offer instantly
    def _post_write(self, writer):
        writer.offer(ChannelReq(self.process()))


class TimeoutGuard(Guard):
    """
    Timeout spawns a timer thread, when posted. If removed
    before timeout, then the timer thread is cancelled.
    """
    def __init__(self, seconds, action=None):
        self.seconds = seconds

        self.posted = (None, None)
        self.s = Scheduler()
        self.p = None

        self.g = (self, action)

    # Timer expired, offer an active Channel Request
    def expire(self):
        op, req = self.posted
        if op == READ:
            ChannelReq(self.p, msg=None).offer(req)
        elif op == WRITE:
            req.offer(ChannelReq(self.p))

    def _post_read(self, reader):
        self.posted = (READ, reader)

        # Start process
        self.p = Process(self.expire)
        self.p.start()
        self.p.setstate(ACTIVE)

        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)

    def _post_write(self, writer):
        self.posted = (WRITE, writer)

        # Start process
        self.p = Process(self.expire)
        self.p.start()
        self.p.setstate(ACTIVE)

        # Put process on the scheduler timer queue
        self.s.timer_wait(self.p, self.seconds)
  
    def _remove_read(self, req):
        self.s.timer_cancel(self.p)

    def _remove_write(self, req):
        self.s.timer_cancel(self.p)

# Backwards compatibility
Skip = SkipGuard
Timeout = TimeoutGuard

