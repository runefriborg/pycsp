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
import uuid

#from channel import ChannelReq, ReqStatus
from process import Process
from pycsp.common.const import *
from protocol import AddrID, ChannelReq, LockMessenger
from dispatch import SocketDispatcher
from exceptions import *

# Classes
class Guard:
    """
    The empty interface of a guard.
    """
    def __init__(self, action=None):
        self.g = (self, action)

        # Id similar to channel name, to correctly select the chosen guard among the guard set.
        self.id = uuid.uuid1().bytes

        # Necessary to allow for correct locking
        dispatch = SocketDispatcher().getThread()
        dispatch.registerChannel(self.id)
        self.LM = LockMessenger(self.id)

    def offer(self, req):
        try:
            # Acquire lock
            conn, state, seq = self.LM.remote_acquire_and_get_state(req.process)
            
            # Check sequence number
            if seq != req.seq_check:
                state = FAIL

            # Success?
            if (state == READY):
                self.LM.remote_notify(conn, req.process, req.ch_id, None)
                
            # Release lock
            self.LM.remote_release(conn, req.process)
        except AddrUnavailableException as e:
            # Unable to reach process during offer
            # The primary reason is probably because a request were part of an alting and the process have exited.
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP unable to reach process during Guard.offer(%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP unable to reach process during Guard.offer(%s)\n" % str(self.process))

        return
    
    def cancel(self):
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
        Guard.__init__(self, action)

    # Offer instantly
    def post_read(self, process):
        self.offer(ChannelReq(self.LM, AddrID(process.addr, process.id),
                                       process.sequence_number,
                                       self.id))

    def post_write(self, process, msg):
        raise InfoException("Can not use SkipGuard with msg")
        

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
        Guard.__init__(self, action)
        self.seconds = seconds
        self.posted_req = None

    # Timer expired, offer an active Channel Request
    def expire(self):
        self.offer(self.posted_req)
        
    def post_read(self, process):
        self.posted_req = ChannelReq(self.LM, AddrID(process.addr, process.id),
                                     process.sequence_number,
                                     self.id)
        self.timer = threading.Timer(self.seconds, self.expire)
        self.timer.start()
  
    def cancel(self):
        self.timer.cancel()

# Backwards compatibility
Skip = SkipGuard
Timeout = TimeoutGuard

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
