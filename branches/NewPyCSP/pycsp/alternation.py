import threading
import inspect

from channel import *

ACTIVE, CANCEL, DONE, POISON = range(4)
READ, WRITE = range(2)
FAIL, SUCCESS = range(2)

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
            action = self.guards[act]
            if callable(action):
                # Execute callback function
                if op==WRITE:
                    self.guards[act]()
                else:
                    self.guards[act](ChannelInput=req.msg)
            else:
                # Fetch process frame and namespace
                processframe= inspect.currentframe().f_back
                
                # Compile source provided in a string.
                code = compile(action,processframe.f_code.co_filename + ' line ' + str(processframe.f_lineno) + ' in string' ,'exec')
                f_globals = processframe.f_globals
                f_locals = processframe.f_locals
                if not op==WRITE:
                    f_locals.update({'ChannelInput':req.msg})

                # Execute action
                exec(code, f_globals, f_locals)

    def select(self):
        act, c, req, op = self.choose()
        return (c, req.msg)



