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
from channelend import ChannelRetireException
from const import *

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

# Classes
class ReqStatus:
    def __init__(self, state=ACTIVE):
        self.state=state
        self.cond = threading.Condition()

class ChannelReq:
    def __init__(self,  status, msg=None, signal=None, name=None):
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



class RealChannel():
    """
    RealChannel is the Channel object that handles synchronization
    at the channel server daemon.
    """
    def __init__(self, name=None):
        self.readqueue=[]
        self.writequeue=[]
        self.ispoisoned=False
        self.isretired=False
        self.readers=0
        self.writers=0

        if name == None:
            # Create name based on host ID and current time
            import uuid
            self.name = str(uuid.uuid1())
        else:
            self.name=name

        # This lock is used to ensure atomic updates of the channelend
        # reference counting
        self.lock = threading.RLock()

        # We can avoid protecting the queue operations with this lock
        # , because of the Global Interpreter Lock preventing us from
        # updating Python lists simultaneously from multiple threads.
    
    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()
        
    def _read(self):
        self.check_termination()
        req=ChannelReq(ReqStatus(), name=self.name)
        self.post_read(req)
        req.wait()
        self.remove_read(req)
        if req.result==SUCCESS:
            return req.msg
        self.check_termination()

        print 'We should not get here in read!!!', req.status.state
        return None #Here we should handle that a read was cancled...

    
    def _write(self, msg):
        self.check_termination()
        req=ChannelReq(ReqStatus(), msg)
        self.post_write(req)
        req.wait()
        self.remove_write(req)
        if req.result==SUCCESS:
            return req.msg
        self.check_termination()

        print 'We should not get here in write!!!', req.status
        return None #Here we should handle that a read was cancled...

    def post_read(self, req):
        self.check_termination()
        self.readqueue.append(req) # ATOMIC
        self.match()

    def remove_read(self, req):
        self.readqueue.remove(req) # ATOMIC

        
    def post_write(self, req):
        self.check_termination()
        self.writequeue.append(req) # ATOMIC
        self.match()

    def remove_write(self, req):
        self.writequeue.remove(req) # ATOMIC

    def match(self):
        for w in self.writequeue[:]: # ATOMIC copy
            for r in self.readqueue[:]: # ATOMIC copy
                w.offer(r)

    def poison(self):
        self.ispoisoned=True
        for p in self.readqueue[:]: # ATOMIC copy
            p.poison()
        for p in self.writequeue[:]: # ATOMIC copy
            p.poison()

    def join_reader(self):
        self.lock.acquire()
        self.readers+=1
        self.lock.release()

    def join_writer(self):
        self.lock.acquire()
        self.writers+=1
        self.lock.release()

    def leave_reader(self):
        self.lock.acquire()
        if not self.isretired:
            self.readers-=1
            if self.readers==0:
                # Set channel retired
                self.isretired = True
                for p in self.writequeue[:]: # ATOMIC copy
                    p.retire()
        self.lock.release()

    def leave_writer(self):
        self.lock.acquire()
        if not self.isretired:
            self.writers-=1
            if self.writers==0:
                # Set channel retired
                self.isretired = True
                for p in self.readqueue[:]: # ATOMIC copy
                    p.retire()
        self.lock.release()
    

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
