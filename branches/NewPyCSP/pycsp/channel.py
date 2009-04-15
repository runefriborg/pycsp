import threading

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
        if self.result != SUCCESS or self.status.state != DONE:
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
        # Eliminate unnecessary locking, by adding an extra test
        if self.status.state == recipient.status.state == ACTIVE:
            self.status.cond.acquire()
            recipient.status.cond.acquire()
            if self.status.state == recipient.status.state == ACTIVE:
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
        self.name=name
        self.ispoisoned=False
        self.readers=0
        self.writers=0

        # We can remove the condition from Channel, because all operations
        # on the queues can be done atomic, because of the Global Interpreter Lock
        # preventing us from accessing Python lists simultaneously from multiple threads.
        # self.cond=threading.Condition()
        #
        # But what about match(). We can now have interleaving processes calling match
        # meaning, that several might be offering messages. Offering is protected. Is that enough?.
        # If it is, then this might be a very clean method to ensure a correct locking.

    
    def check_poison(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        
    def _read(self):
        self.check_poison()
        req=ChannelReq(ReqStatus(), name=self.name)
        self.post_read(req)
        req.wait()
        self.remove_read(req)
        if req.result==SUCCESS:
            return req.msg
        self.check_poison()

        print 'We should not get here in read!!!', req.status.state
        return None #Here we should handle that a read was cancled...

    
    def _write(self, msg):
        self.check_poison()
        req=ChannelReq(ReqStatus(), msg)
        self.post_write(req)
        req.wait()
        self.remove_write(req)
        if req.result==SUCCESS:
            return req.msg
        self.check_poison()

        print 'We should not get here in write!!!', req.status
        return None #Here we should handle that a read was cancled...

    def post_read(self, req):
        if self.ispoisoned:
            raise ChannelPoisonException()
        self.readqueue.append(req) # ATOMIC
        self.match()

    def remove_read(self, req):
        self.readqueue.remove(req) # ATOMIC

        
    def post_write(self, req):
        if self.ispoisoned:
            raise ChannelPoisonException()
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
        self.readers+=1

    def join_writer(self):
        self.writers+=1

    def leave_reader(self):
        self.readers-=1
        if self.readers==0:
            self.poison()
            return

    def leave_writer(self):
        self.writers-=1
        if self.writers==0:
            self.poison()
            return
    
    def status(self):
        print 'Reads:',len(self.readqueue), 'Writes:',len(self.writequeue)

