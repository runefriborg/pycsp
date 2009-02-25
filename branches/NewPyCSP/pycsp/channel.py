import threading
import time
import random

ACTIVE, CANCEL, DONE, POISON = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

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
        self.status.state=POISON
        self.result=POISON
        self.status.cond.notifyAll()
        self.status.cond.release()

    def wait(self):
        self.status.cond.acquire()
        while self.status.state==ACTIVE:
            self.status.cond.wait()
        self.status.cond.release()


    def offer(self, recipient):
        self.status.cond.acquire()
        recipient.status.cond.acquire()
        if self.status.state==ACTIVE and recipient.status.state==ACTIVE:
            recipient.msg=self.msg
            self.status.state=DONE
            self.result=SUCCESS
            recipient.status.state=DONE
            recipient.result=SUCCESS
            self.status.cond.notifyAll()
            recipient.status.cond.notifyAll()
        recipient.status.cond.release()
        self.status.cond.release()

        
class Channel:
    def __init__(self, name=None):
        self.readqueue=[]
        self.writequeue=[]
        self.cond=threading.Condition()
        self.name=name
        self.ispoisoned=False
        self.readers=0
        self.writers=0

    def check_poison(self):
        self.cond.acquire()
        if self.ispoisoned:
            self.cond.release()
            raise ChannelPoisonException()
        self.cond.release()
        
    def read(self):
        done=False
        while not done:
            req=ChannelReq(ReqStatus(), name=self.name)
            self.post_read(req)
            self.check_poison()            
            req.wait()
            self.remove_read(req)
            if req.result==SUCCESS:
                done=True
                return req.msg
            self.check_poison()
        print 'We should not get here in read!!!', req.status.state
        return None #Here we should handle that a read was cancled...

    
    def write(self, msg):
        self.check_poison()
        done=False
        while not done:
            req=ChannelReq(ReqStatus(), msg)
            self.post_write(req)
            req.wait()
            self.remove_write(req)
            if req.result==SUCCESS:
                done=True
                return req.msg
            self.check_poison()
        print 'We should not get here in write!!!', req.status
        return None #Here we should handle that a read was cancled...

    def post_read(self, req):
        if self.ispoisoned:
            raise ChannelPoisonException()
        self.cond.acquire()
        self.readqueue.append(req)
        self.cond.release()
        self.match()

    def remove_read(self, req):
        self.cond.acquire()
        self.readqueue.remove(req)
        self.cond.release()
        
    def post_write(self, req):
        if self.ispoisoned:
            raise ChannelPoisonException()
        self.cond.acquire()
        self.writequeue.append(req)
        self.cond.release()
        self.match()

    def remove_write(self, req):
        self.cond.acquire()
        self.writequeue.remove(req)
        self.cond.release()

    def match(self):
        self.cond.acquire()
        if self.readqueue and self.writequeue:
            for w in self.writequeue:
                for r in self.readqueue:
                    w.offer(r)
        self.cond.release()

    def poison(self):
        self.cond.acquire()
        self.ispoisoned=True
        for p in self.readqueue:
            p.poison()
        for p in self.writequeue:
            p.poison()
        self.cond.release()

    def join(self, reader=True, writer=True):
        r=None
        w=None
        if reader:
            r=self.read
            self.readers+=1
        if writer:
            w=self.write
            self.writers+=1
        return (r,w)

    def leave(self, reader=True, writer=True):
        if reader:
            self.readers-=1
        if writer:
            self.writers-=1
        if self.readers==0 or self.writers==0:
            self.poison()
    
    def status(self):
        print 'Reads:',len(self.readqueue), 'Writes:',len(self.writequeue)

