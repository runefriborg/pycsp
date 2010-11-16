"""
Selection module

This selection module is used by the channelends to leverage to correct synchronization
mechanisms.


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

from pycsp.common.const import *
from scheduling import Scheduler, current_process_id


class ChannelReq:
    def __init__(self, process, msg=None):
        self.msg = msg
        self.result = FAIL
        self.process = process

    def poison(self):
        if self.result != SUCCESS:
            self.result = POISON
            self.process.notify(POISON)

    def retire(self):
        if self.result != SUCCESS:
            self.result = RETIRE
            self.process.notify(RETIRE)

    def offer(self, recipient):
        if self.process.state == recipient.process.state == ACTIVE:
            recipient.msg= self.msg
            self.result=SUCCESS
            recipient.result=SUCCESS
            self.process.notify(DONE)
            recipient.process.notify(DONE)
            return True
        return False


class SyncShared(object):
    def __init__(self, channel):
        self.channel = channel

    def check_termination(self):
        if self.channel.ispoisoned:
            raise ChannelPoisonException()
        if self.channel.isretired:
            raise ChannelRetireException()


class SyncOneOneLocalNoALT(SyncShared):
    def __init__(self, channel):
        SyncShared.__init__(self, channel)
        self.s = Scheduler()

        # Internal structure
        self.waiting_req = None

    def read(self):
        req, msg = self.enter_read()
        if req == None:
            return msg
        else:
            self.wait_read(req)
            self.leave_read(req)
            return req.msg

    def enter_read(self):
        self.check_termination()
        
        p = self.s.current

        # match
        if self.waiting_req != None:
            w = self.waiting_req
            if w.process.state == ACTIVE:
                msg = w.msg
                w.result = SUCCESS
                w.process.state = DONE
                if p != w.process:
                    self.s.next.append(w.process)
                # Fast remove
                self.waiting_req = None
                return (None, msg)

        p.setstate(ACTIVE)
        req = ChannelReq(p)
        return (req, None)
            
    def wait_read(self, req):
        self.waiting_req = req
        req.process.wait()

    def leave_read(self, req):
        if req.result != SUCCESS:
            self.check_termination()
        

    def write(self, msg):
        req = self.enter_write(msg)
        if req == None:
            return
        else:
            self.wait_write(req)
            self.leave_write(req)
            return
    
    def enter_write(self, msg):
        self.check_termination()
        
        p = self.s.current

        # match
        if self.waiting_req != None:
            r = self.waiting_req
            if r.process.state == ACTIVE:
                r.msg = msg
                r.result = SUCCESS
                r.process.state = DONE
                if p != r.process:
                    self.s.next.append(r.process)
                # Fast remove
                self.waiting_req = None
                return None

        p.setstate(ACTIVE)
        req = ChannelReq(p,msg=msg)
        return req

    def wait_write(self, req):
        self.waiting_req = req
        req.process.wait()

    def leave_write(self, req):
        if req.result != SUCCESS:
            self.check_termination()
        

    def poison(self):
        if not self.channel.ispoisoned:
            self.channel.ispoisoned = True
            if self.waiting_req:
                self.waiting_req.poison()


class SyncOneOneLocal(SyncShared):
    def __init__(self, channel):
        SyncShared.__init__(self, channel)
        
    def read(self):
        # Create RequestState
        self.enter_read()
        self.wait_read()
        return self.leave_read()

    def enter_read(self):
        pass

    def wait_read(self):
        pass
    
    def leave_read(self):
        pass


    def write(self, msg):
        # Create RequestState
        
        self.enter_write()
        self.wait_write()
        self.leave_write()
    
    def enter_write(self):
        pass

    def wait_write(self):
        pass

    def leave_write(self):
        pass


LEVEL = {
    0:SyncOneOneLocalNoALT,
    1:SyncOneOneLocal,
#    2:SyncOneOneGlobalNoALT,
#    3:SyncAnyAnyLocal,
#    4:SyncAnyAnyGlobalNoALT,
    }
# LEVEL[0] = SyncOneOne (greenlet only)
# LEVEL[1] = any-any (greenlet only)

def Sync(level, channel):
    return LEVEL[level](channel)

def transcend(obj, level):
    oldLevel = obj.level
    oldClass = obj.__class__
        
    obj.__class__ = LEVEL[level]

