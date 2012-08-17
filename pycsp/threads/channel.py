"""
Channel module

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
import inspect
import time, random
from channelend import ChannelRetireException, ChannelRetireLikeFailstopException, ChannelEndRead, ChannelEndWrite 
from pycsp.common.const import *

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

class ChannelFailstopException(Exception):
    def __init__(self):
        pass

class ChannelRollBackException(Exception):
    def __init__(self):
        pass

# Classes
class ReqStatus:
    def __init__(self, state=ACTIVE):
        self.state=state
        self.cond = threading.Condition()

class ChannelReq:
    def __init__(self, status, msg=None, signal=None, name=None):
        self.status=status
        self.msg=msg
        self.signal=signal
        self.result=FAIL
        self.name=name
        
    def cancel(self):
        self.status.cond.acquire()
        self.status.state=CANCEL
        self.status.cond.notifyAll()
        self.status.cond.release()

    def poison(self):
        self.status.cond.acquire()
        if self.result == FAIL and self.status.state == ACTIVE:
            self.status.state=POISON
            self.result=POISON
            self.status.cond.notifyAll()
        self.status.cond.release()

    def retire(self):
        self.status.cond.acquire()
        if self.result == FAIL and self.status.state == ACTIVE:
            self.status.state=RETIRE
            self.result=RETIRE
            self.status.cond.notifyAll()
        self.status.cond.release()        

    def failstop(self):
        self.status.cond.acquire()
        if self.result == FAIL and self.status.state == ACTIVE:
            self.status.state=FAILSTOP
            self.result=FAILSTOP
            self.status.cond.notifyAll()
        self.status.cond.release()

    def retirelike(self):
        self.status.cond.acquire()
        if self.result == FAIL and self.status.state == ACTIVE:
            self.status.state=RETIRELIKE
            self.result=RETIRELIKE
            self.status.cond.notifyAll()
        self.status.cond.release()

    def wait(self):
        self.status.cond.acquire()
        while self.status.state==ACTIVE:
            self.status.cond.wait()
        self.status.cond.release()

    def offer(self, recipient):
        # Eliminate unnecessary locking, by adding an extra test
        if self.status.state == recipient.status.state == ACTIVE:

            s_cond = self.status.cond
            r_cond = recipient.status.cond

            # Ensuring to lock in the correct order.
            if s_cond < r_cond:
                s_cond.acquire()
                r_cond.acquire()
            else:
                r_cond.acquire()
                s_cond.acquire()

            if self.status.state == recipient.status.state == ACTIVE:
                recipient.msg=self.msg
                self.status.state=DONE
                self.result=SUCCESS
                recipient.status.state=DONE
                recipient.result=SUCCESS
                s_cond.notifyAll()
                r_cond.notifyAll()

            # Ensuring that we also release in the correct order. ( done in the opposite order of locking )
            if s_cond < r_cond:
                r_cond.release()
                s_cond.release()
            else:
                s_cond.release()
                r_cond.release()


        
class Channel(object):
    """ Channel class. Blocking communication
    
    >>> from __init__ import *

    >>> @process
    ... def P1(cout):
    ...     while True:
    ...         cout('Hello World')

    >>> C = Channel()
    >>> Spawn(P1(C.writer()))
    
    >>> cin = C.reader()
    >>> cin()
    'Hello World'

    >>> retire(cin)
    """
    def __new__(cls, *args, **kargs):
        if kargs.has_key('buffer') and kargs['buffer'] > 0:
            import buffer                      
            chan = buffer.BufferedChannel(*args, **kargs)
            return chan
        else:
            return object.__new__(cls)

    def __init__(self, name=None, buffer=0):
        self.readqueue  = []
        self.writequeue = []
        
        self.status = NONE
        self.old_status = NONE

        self.readers = 0
        self.writers = 0

        if name == None:
            # Create unique name
            self.name = str(random.random())+str(time.time())
        else:
            self.name=name

        # This lock is used to ensure atomic updates of the channelend
        # reference counting and to protect the read/write queue operations. 
        self.lock = threading.RLock()

    def save_variables(self):
        stack = inspect.stack()
        
        try:
            locals_ = stack[2][0].f_locals
            process_ = stack[3][0].f_locals
        finally:
            del stack
        
        process_['self'].vars = locals_

    def check_termination(self):
        if self.status == POISON:
            raise ChannelPoisonException()
        elif self.status == RETIRE:
            raise ChannelRetireException()
        elif self.status == FAILSTOP:
            raise ChannelFailstopException()
        elif self.status == RETIRELIKE:
            raise ChannelRetireLikeFailstopException()
        elif self.status == CHECKPOINT:
            self.status = self.old_status
            raise ChannelRollBackException()

    def _read(self):
        self.check_termination()
        req=ChannelReq(ReqStatus(), name=self.name)
        self.post_read(req)
        req.wait()
        self.remove_read(req)
        if req.result==SUCCESS:
            self.save_variables()
            return req.msg
        self.check_termination()

        print 'We should not get here in read!!!', req.status.state
        return None
    
    def _write(self, msg):
        self.check_termination()
        req=ChannelReq(ReqStatus(), msg)
        self.post_write(req)
        req.wait()
        self.remove_write(req)
        if req.result==SUCCESS:
            self.save_variables()
            return
        self.check_termination()

        print 'We should not get here in write!!!', req.status
        return

    def post_read(self, req):
        self.check_termination()

        success = True
        self.lock.acquire()
        if self.status != NONE:
            success = False
        else:
            self.readqueue.append(req)
        self.lock.release()

        if success:
            self.match()
        else:
            self.check_termination()
        
    def remove_read(self, req):
        self.lock.acquire()
        self.readqueue.remove(req)
        self.lock.release()

    def post_write(self, req):
        self.check_termination()

        success = True
        self.lock.acquire()
        if self.status != NONE:
            success = False
        else:
            self.writequeue.append(req)
        self.lock.release()

        if success:
            self.match()
        else:
            self.check_termination()

    def remove_write(self, req):
        self.lock.acquire()
        self.writequeue.remove(req)
        self.lock.release()

    def match(self):
        self.lock.acquire()
        for w in self.writequeue:
            for r in self.readqueue:
                w.offer(r)
        self.lock.release()

    def poison(self):
        self.lock.acquire()
        self.status=POISON
        for p in self.readqueue:
            p.poison()
        for p in self.writequeue:
            p.poison()
        self.lock.release()

    def failstop(self):
        self.lock.acquire()
        self.status=FAILSTOP
        for p in self.readqueue:
            p.failstop()
        for p in self.writequeue:
            p.failstop()
        self.lock.release()

    def rollback(self):
        self.lock.acquire()
        
        if self.status != CHECKPOINT:
            self.old_status = self.status
            self.status = CHECKPOINT

        self.lock.release()

    # syntactic sugar: cin = +chan
    def __pos__(self):
        return self.reader()
    
    # syntactic sugar: cout = -chan
    def __neg__(self):
        return self.writer()

    # syntactic sugar: Channel() * N
    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1)))
        return new

    # syntactic sugar: N * Channel()
    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)
    
    def reader(self):
        """
        Join as reader
        
        >>> C = Channel()
        >>> cin = C.reader()
        >>> isinstance(cin, ChannelEndRead)
        True
        """
        self.join_reader()
        return ChannelEndRead(self)

    def writer(self):
        """
        Join as writer
        
        >>> C = Channel()
        >>> cout = C.writer()
        >>> isinstance(cout, ChannelEndWrite)
        True
        """

        self.join_writer()
        return ChannelEndWrite(self)

    def join_reader(self):
        self.lock.acquire()
        self.readers+=1
        self.lock.release()

    def join_writer(self):
        self.lock.acquire()
        self.writers+=1
        self.lock.release()

    def leave_reader(self, status=RETIRE):
        self.lock.acquire()
        if self.status != RETIRE or self.status != RETIRELIKE:
            self.readers-=1
            if self.readers==0:
                # Set channel retired
                self.status = status
                for p in self.writequeue:
                    if status == RETIRELIKE:
                        p.retirelike()
                    else:
                        p.retire()
        self.lock.release()

    def leave_writer(self, status=RETIRE):
        self.lock.acquire()
        if self.status != RETIRE or self.status != RETIRELIKE:
            self.writers-=1
            if self.writers==0:
                # Set channel retired
                self.status = status
                for p in self.readqueue:
                    if status == RETIRELIKE:
                        p.retirelike()
                    else:
                        p.retire()
        self.lock.release()   

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
