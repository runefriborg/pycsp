import threading
from channel import ChannelReq, ReqStatus

ACTIVE, DONE, POISON = range(3)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

# The empty interface of a guard.
class Guard():
    def post_read(self, req):
        pass

    def post_write(self, req):
        pass

    def remove_read(self, req):
        pass

    def remove_write(self, req):
        pass

    def poison(self):
        pass

# Skip will try to accept a read or a write, the moment it is posted.
class Skip(Guard):
    # Offer instantly
    def post_read(self, reader):
        ChannelReq(ReqStatus(), msg=None).offer(reader)
        
    # Offer instantly
    def post_write(self, writer):
        writer.offer(ChannelReq(ReqStatus()))
    
# Timeout spawns a timer thread, when posted. If removed or poisoned
# before expired the timer thread is cancelled.
class Timeout(Guard):
    def __init__(self, seconds):
        self.seconds = seconds
        self.posted = (None, None)

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

    def poison(self):
        self.timer.cancel()
