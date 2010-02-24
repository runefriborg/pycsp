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
from channel import *
from const import *

# Classes
class Guard():
    """
    The standard interface of a guard.
    """

    def offer_write(self, reader_id):
        manager = ShmManager()
        req_id = manager.ChannelReqDataPool.new()
        req_status_id = manager.ReqStatusDataPool.new()
        manager.ReqStatus_reset(req_status_id)
        manager.ChannelReq_reset(req_id, req_status_id, msg=None, write=True)
        manager.ChannelReq_offer(req_id, reader_id)
    
    def offer_read(self, writer_id):
        manager = ShmManager()
        req_id = manager.ChannelReqDataPool.new()
        req_status_id = manager.ReqStatusDataPool.new()
        manager.ReqStatus_reset(req_status_id)
        manager.ChannelReq_reset(req_id, req_status_id, msg=None)
        manager.ChannelReq_offer(writer_id, req_id)

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

    # Offer instantly
    def post_read(self, reader_id):
        self.offer_write(reader_id)

    # Offer instantly
    def post_write(self, writer_id):
        self.offer_read(writer_id)


class TimeoutGuard(Guard):
    """
    Timeout spawns a timer thread, when posted. If removed
    before timeout, then the timer thread is cancelled.
    """
    def __init__(self, seconds, action=None):
        self.seconds = seconds
        self.posted = (None, None)
        self.g = (self, action)

    # Timer expired, offer an active Channel Request
    def expire(self):
        op, req = self.posted
        if op == READ:
            self.offer_write(req)
        elif op == WRITE:
            self.offer_read(req)

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

# Backwards compatibility
Skip = SkipGuard
Timeout = TimeoutGuard

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
