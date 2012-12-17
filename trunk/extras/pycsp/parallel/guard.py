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
from pycsp.parallel.process import Process
from pycsp.parallel.const import *
from pycsp.parallel.protocol import AddrID, ChannelReq, LockMessenger
from pycsp.parallel.dispatch import SocketDispatcher
from pycsp.parallel.exceptions import *

# Classes
class Guard:
    """
    The empty interface of a guard.
    """
    def __init__(self, action=None):
        self.g = (self, action)

        # Id similar to channel name, to correctly select the chosen guard among the guard set.
        self.id = uuid.uuid1().hex

        # Necessary to allow for correct locking
        self.dispatch = SocketDispatcher().getThread()
        self.dispatch.registerGuard(self.id)
        self.LM = LockMessenger(self.id)

    def _offer(self, req):
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

        except AddrUnavailableException:
            # Unable to reach process during offer
            # The primary reason is probably because a request were part of an alting and the process have exited.
            if conf.get(SOCKETS_STRICT_MODE):
                raise FatalException("PyCSP unable to reach process during Guard.offer(%s)" % str(self.process))
            else:
                sys.stderr.write("PyCSP unable to reach process during Guard.offer(%s)\n" % str(self.process))

        self.dispatch.deregisterGuard(self.id)

    def _cancel(self):
        # Invoked from Alternation
        self.dispatch.deregisterGuard(self.id)

    
class SkipGuard(Guard):
    """ SkipGuard(action=None)

    SkipGuard will commit a successful communication the moment it is posted.

    Usage:
      >>> C = Channel()
      >>> Cin = C.reader()
      >>> (g, msg) = AltSelect(InputGuard(Cin),  SkipGuard() )

    SkipGuard(action=None)
    action
      An action may be provided as a string, a callable function object or a Choice object.
      The Choice object is the recommended use of action.
      
      A string:
        >>> action="L.append(channel_input)"
      
        The string passed to the action parameter is evaluted in the current namespace and can 
        read variables, but can only write output by editing the content of existing mutable variables.
        Newly created immutable and mutable variables will only exist in the evalutation of this string.
      
      callable(func):
        >>> def func(channel_input=None)
        ...     L.append(channel_input)
        >>> action=func
        
        The callable function object must accept one parameter for actions on InputGuards and must
        accept zero parameters for actions on OutputGuards.

      Choice:
        >>> @choice
        ... def func(L, channel_input=None)
        ...     L.append(channel_input)
        >>> action=func(gatherList)

        The choice decorator can be used to make a Choice factory, which can generate actions with
        different parameters depending on the use case. See help(pycsp.choice)
    """
    def __init__(self, action=None):
        Guard.__init__(self, action)

    # Offer instantly
    def _post_read(self, process):
        self._offer(ChannelReq(self.LM, AddrID(process.addr, process.id),
                                       process.sequence_number,
                                       self.id))

    def _post_write(self, process, msg):
        raise InfoException("Can not use SkipGuard with msg")
        

class TimeoutGuard(Guard):
    """ TimeoutGuard(seconds, action=None)

    TimeoutGuard spawns a timer thread, when posted. If removed
    before timeout, then the timer thread is cancelled.

    When the timer expires, the timer thread will commit a successful communication.

    Usage:
      >>> C = Channel()
      >>> Cin = C.reader()
      >>> (g, msg) = AltSelect( InputGuard(Cin), TimeoutGuard(seconds=0.5) )

    TimeoutGuard(action=None)
    seconds
      Set the seconds to wait before timeout. eg. 0.5s
    action
      An action may be provided as a string, a callable function object or a Choice object.
      The Choice object is the recommended use of action.
      
      A string:
        >>> action="L.append(channel_input)"
      
        The string passed to the action parameter is evaluted in the current namespace and can 
        read variables, but can only write output by editing the content of existing mutable variables.
        Newly created immutable and mutable variables will only exist in the evalutation of this string.
      
      callable(func):
        >>> def func(channel_input=None)
        ...     L.append(channel_input)
        >>> action=func
        
        The callable function object must accept one parameter for actions on InputGuards and must
        accept zero parameters for actions on OutputGuards.

      Choice:
        >>> @choice
        ... def func(L, channel_input=None)
        ...     L.append(channel_input)
        >>> action=func(gatherList)

        The choice decorator can be used to make a Choice factory, which can generate actions with
        different parameters depending on the use case. See help(pycsp.choice)
    """
    def __init__(self, seconds, action=None):
        Guard.__init__(self, action)
        self.seconds = seconds
        self.posted_req = None

    # Timer expired, offer an active Channel Request
    def _expire(self):
        self._offer(self.posted_req)
        
    def _post_read(self, process):
        self.posted_req = ChannelReq(self.LM, AddrID(process.addr, process.id),
                                     process.sequence_number,
                                     self.id)
        self.timer = threading.Timer(self.seconds, self._expire)
        self.timer.start()
  
    def _cancel(self):
        Guard._cancel(self)
        self.timer.cancel()
        
        
# Backwards compatibility
Skip = SkipGuard
Timeout = TimeoutGuard

# Validate doc examples
if __name__ == '__main__':
    import doctest
    doctest.testmod()
