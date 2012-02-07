"""
Adds Skip and Timeout guards

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
import threading
from scheduling import Scheduler
from channel import ChannelReq
from process import Process
from const import *

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
    def post_read(self, reader):
        ChannelReq(self.process(), msg=None).offer(reader)
        
    # Offer instantly
    def post_write(self, writer):
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

# Backwards compatibility
Skip = SkipGuard
Timeout = TimeoutGuard

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
