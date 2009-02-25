import threading
import time
import random
from channel import *

ACTIVE, CANCEL, DONE, POISON = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

def choice(func):
    def _call(*args, **kwargs):
        return Choice(func, *args, **kwargs)
    return _call

class Choice(threading.Thread):
    def __init__(self, fn, *args, **kwargs):
        threading.Thread.__init__(self)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
    def run(self, ChannelInput=None):
        self.retval = None
        # Store the returned value from the process
        self.kwargs['ChannelInput']=ChannelInput
        self.retval = self.fn(*self.args, **self.kwargs)

class Alternation:
    def __init__(self, guards):
        self.guards=guards
        pass

    def choose(self):
        req_status=ReqStatus()
        reqs={}
        done = False
        try:
            for choice in self.guards.keys():
                if not done:
                    if type(choice)==tuple: 
                        c, msg = choice
                        req=ChannelReq(req_status,msg=msg)
                        c.post_write(req)
                        op=WRITE
                    else:
                        req=ChannelReq(req_status)
                        c=choice
                        c.post_read(req)
                        op=READ
                    reqs[choice]=(c, req, op)
        except ChannelPoisonException:
            for r in reqs.keys():
                c, req, op = reqs[r]
                if op==READ:
                    c.remove_read(req)
                else:
                    c.remove_write(req)
            raise ChannelPoisonException()
        req_status.cond.acquire()
        if req.status.state==ACTIVE:
            req_status.cond.wait()
        req_status.cond.release()
        act=None
        poison=False
        for k in reqs.keys():
            c, req, op = reqs[k]
            if op==READ:
                c.remove_read(req)
            else:
                c.remove_write(req)
            if req.result==SUCCESS:
                act=k
            if req.result==POISON:
                poison=True
        if poison:
            raise ChannelPoisonException()
        c, req, op = reqs[act]

        return (act, c, req, op)

    def execute(self):
        act, c, req, op = self.choose()
        if self.guards[act]:
            if op==WRITE:
                self.guards[act].run()
            else:
                self.guards[act].run(ChannelInput=req.msg)

    def select(self):
        act, c, req, op = self.choose()
        return (c, req.msg)



