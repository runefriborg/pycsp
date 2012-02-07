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
from channel import ChannelReq, ReqStatus
from const import *

# Classes
class Guard:
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
    SkipGuard will try to accept a read or a write, the moment it is posted.
    
    >>> from __init__ import *

    >>> C = Channel()
    >>> Cin = C.reader()
    >>> (g, msg) = AltSelect(InputGuard(Cin),  SkipGuard() )

    >>> isinstance(g, Skip) and msg == None
    True
    """
    def __init__(self, action=None):
        self.g = (self, action)

    # Offer instantly
    def post_read(self, reader):
        ChannelReq(ReqStatus(), msg=None).offer(reader)
        
    # Offer instantly
    def post_write(self, writer):
        writer.offer(ChannelReq(ReqStatus()))


class TimeoutGuard(Guard):
    """
    TimeoutGuard spawns a timer thread, when posted. If removed
    before timeout, then the timer thread is cancelled.
    
    >>> from __init__ import *
    >>> import time

    >>> C = Channel()
    >>> Cin = C.reader()

    >>> time_start = time.time()
    >>> (g, msg) = AltSelect( InputGuard(Cin), TimeoutGuard(seconds=0.5) )
    >>> time_passed = time.time() - time_start

    >>> time_passed >= 0.5
    True
    
    >>> time_passed < 0.6
    True
    
    >>> isinstance(g, Timeout) and msg == None
    True
    """
    def __init__(self, seconds, action=None):
        self.seconds = seconds
        self.posted = (None, None)
        self.g = (self, action)

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

# Backwards compatibility
Skip = SkipGuard
Timeout = TimeoutGuard

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
