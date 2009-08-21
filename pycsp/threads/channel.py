"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Imports
import threading
from channelend import ChannelRetireException, ChannelEndRead, ChannelEndWrite 

# Constants
ACTIVE, DONE, POISON, RETIRE = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

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


        
class Channel:
    """ Channel class. Blocking communication
    
    >>> from __init__ import *

    >>> @process
    ... def P1(cout):
    ...     while True:
    ...         cout('Hello World')

    >>> C = Channel()
    >>> Spawn(P1(OUT(C)))
    
    >>> cin = IN(C)
    >>> cin()
    'Hello World'

    >>> retire(cin)
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

        # We can avoid protecting the Channel using a lock, because all operations
        # on the queues can be done atomic, because of the Global Interpreter Lock
        # preventing us from accessing Python lists simultaneously from multiple threads.

    
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
            return
        self.check_termination()

        print 'We should not get here in write!!!', req.status
        return #Here we should handle that a read was cancled...

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

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def reader(self):
        self.join_reader()
        return ChannelEndRead(self)

    def writer(self):
        self.join_writer()
        return ChannelEndWrite(self)

    def join_reader(self):
        self.readers+=1        

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        if not self.isretired:
            self.readers-=1
            if self.readers==0:
                # Set channel retired
                self.isretired = True
                for p in self.writequeue[:]: # ATOMIC copy
                    p.retire()

    def leave_writer(self):
        if not self.isretired:
            self.writers-=1
            if self.writers==0:
                # Set channel retired
                self.isretired = True
                for p in self.readqueue[:]: # ATOMIC copy
                    p.retire()
        
    def status(self):
        print 'Reads:',len(self.readqueue), 'Writes:',len(self.writequeue)


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
