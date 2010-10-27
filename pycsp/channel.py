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
try: from greenlet import greenlet
except ImportError, e:
    from py.magic import greenlet
    
from scheduling import Scheduler, current_process_id
from channelend import ChannelEndRead, ChannelEndWrite, ChannelRetireException
from pycsp.common.const import *

import time, random

# Exceptions
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass

# Classes
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


class ChannelOne2One(object):
    """
    Always put the writer on the scheduler's next queue and continue with the reader.
    """
    
    def __init__(self):
        pass

    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()

    def _read(self):
        self._read1()
        return self._read2()

    def _read1(self):
        self.check_termination()

        p = self.s.current
        
        if self.internal['writer'] == None:
            self.internal['reader'] = p        
            p.setstate(ACTIVE)
            self._read_wait(p)
            self.internal['reader'] = None


    def _read_wait(self, p):        
        while p.state == ACTIVE:
            p.wait()
            #if self.upgrade_now:
            #    print 'UPGRADE'
                

    def _read2(self):
        #print self.upgrade_now
        #print '_read2_ChannelOne2One'

        p = self.s.current

        if self.internal['writer'] != None:
            self.internal['writer'].notify(DONE)
            self.internal['writer'] = None
            p.state = DONE

        if p.state==DONE:
            return self.internal['msg']
        
        self.check_termination()

        print 'We should not get here in read!!!'
        return None #Here we should handle that a read was cancled...
        

    def _write(self, msg):
        self.check_termination()

        p = self.s.current
        
        self.internal['msg'] = msg

        if self.internal['reader'] == None:
            self.internal['writer'] = p
            p.setstate(ACTIVE)
            p.wait()
        else:
            self.s.next.append(p)
            self.s.current = self.internal['reader']
            self.internal['reader'].state = DONE
            self.internal['reader'].greenlet.switch()                    
            #self.internal['reader'].notify(DONE)
            p.state = DONE

        if p.state==DONE:
            return True
    
        self.check_termination()

        print 'We should not get here in write!!!'
        return None #Here we should handle that a read was cancled...

    def poison(self):
        if not self.ispoisoned:
            self.ispoisoned = True
            self.internal['result'] = POISON
            if self.internal['reader'] != None:
                self.internal['reader'].notify(POISON)
            if self.internal['writer'] != None:
                self.internal['writer'].notify(POISON)

    def post_read(self, req):
        pass
        
    def remove_read(self, req):
        pass

    def post_write(self, req):
        pass

    def remove_write(self, req):
        pass

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1)))
        return new

    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

    def reader(self):
        end = ChannelEndRead(current_process_id(), self)
        self.join_reader(end)
        return end

    def writer(self):
        end = ChannelEndWrite(current_process_id(), self)
        self.join_writer(end)
        return end

    def upgrade(self):
        self.__class__ = Channel
        self.upgrade_now = True

        if self.internal['reader'] != None:
            req = ChannelReq(self.internal['reader'])
            self.readqueue.append(req)
        elif self.internal['writer'] != None:
            req = ChannelReq(self.internal['writer'], self.internal['msg'])
            self.writequeue.append(req)
        
    
    def join_reader(self, end):
        if len(self.readers) == 1:
            self.upgrade()
        self.readers.append(end)

    def join_writer(self, end):
        if len(self.writers) == 1:
            self.upgrade()            
        self.writers.append(end)

    def leave_reader(self, end):
        if not self.isretired:
            self.readers.remove(end)
            if len(self.readers)==0:
                # Set channel retired
                self.isretired = True
                self.internal['result'] = RETIRE
                if self.internal['reader'] != None:
                    self.internal['reader'].notify(RETIRE)
                if self.internal['writer'] != None:
                    self.internal['writer'].notify(RETIRE)

    def leave_writer(self, end):
        if not self.isretired:
            self.writers.remove(end)
            if len(self.writers)==0:
                # Set channel retired
                self.isretired = True
                self.internal['result'] = RETIRE
                if self.internal['reader'] != None:
                    self.internal['reader'].notify(RETIRE)
                if self.internal['writer'] != None:
                    self.internal['writer'].notify(RETIRE)

    

class Channel(object):
    """ Channel class. Blocking communication
    """

    def __new__(cls, *args, **kargs):
        if kargs.has_key('buffer') and kargs['buffer'] > 0:
            import buffer                      
            chan = buffer.BufferedChannel(*args, **kargs)
            return chan
        else:
            return object.__new__(cls)

    def __init__(self, name=None, buffer=0):

        self.upgrade_now = False
        self.internal = {
            'msg':None,
            'writer':None,
            'reader':None
            }

        if name == None:
            # Create unique name
            self.name = str(random.random())+str(time.time())
        else:
            self.name=name

        self.readqueue = []
        self.writequeue = []
        
        # Count, makes sure that all processes knows how many channel ends have retired
        self.readers = []
        self.writers = []

        self.ispoisoned = False
        self.isretired = False

        self.s = Scheduler()

        self.__class__ = ChannelOne2One
        
        
    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()


    def _read(self):
        state = self._read1()
        return self._read2(state)
        
    def _read1(self):
        print '_read1_Channel'
        self.check_termination()

        p = self.s.current
        
        # If anyone is on the writequeue and ACTIVE, then we can do the match right away
        # This hack provides a 150% performance improvement and can be removed
        # without breaking anything.
        for w in self.writequeue:
            if w.process.state == ACTIVE:
                msg = w.msg
                w.result = SUCCESS
                w.process.state = DONE
                if p != w.process:
                    self.s.next.append(w.process)
                return msg        

        p.setstate(ACTIVE)
        req = ChannelReq(p)
        self.post_read(req)
        self._read_wait(p)
        self.internal['read_req']
        return req


    def _read2(self, req):
        print '_read2_Channel'
        self.remove_read(req)

        if req.result==SUCCESS:
            return req.msg
        
        self.check_termination()
            
        print 'We should not get here in read!!!'
        return None #Here we should handle that a read was cancled...

    def _read_wait(self, p):
        while p.state == ACTIVE:
            p.wait()
    
    def _write(self, msg):
        self.check_termination()

        p = self.s.current
        
        # If anyone is on the readqueue and ACTIVE, then we can do the match right away
        # This hack provides a 150% performance improvement and can be removed
        # without breaking anything.
        for r in self.readqueue:
            if r.process.state == ACTIVE:
                r.msg = msg
                r.result = SUCCESS
                r.process.state = DONE
                if p != r.process:
                    self.s.next.append(r.process)
                return True

        p.setstate(ACTIVE)
        req = ChannelReq(p,msg=msg)
        self.post_write(req)
        req.process.wait()
        self.remove_write(req)

        if req.result==SUCCESS:
            return True
    
        self.check_termination()

        print 'We should not get here in write!!!'
        return None #Here we should handle that a read was cancled...

    def post_read(self, req):
        self.check_termination()
        self.readqueue.append(req)
        self.match()

    def remove_read(self, req):
        self.readqueue.remove(req)
        
    def post_write(self, req):
        self.check_termination()
        self.writequeue.append(req)
        self.match()

    def remove_write(self, req):
        self.writequeue.remove(req)

    def match(self):
        if self.readqueue and self.writequeue:
            for w in self.writequeue:
                for r in self.readqueue:
                    if w.offer(r):
                        # Did an offer
                        # We can guarantee, that there will always be someone to call offer,
                        # since everything is run in a single thread. Thus we break the loop.
                        return

    def poison(self):
        if not self.ispoisoned:
            self.ispoisoned = True
            map(ChannelReq.poison, self.readqueue)
            map(ChannelReq.poison, self.writequeue)

    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1)))
        return new

    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

    def reader(self):
        end = ChannelEndRead(current_process_id(), self)
        self.join_reader(end)
        return end

    def writer(self):
        end = ChannelEndWrite(current_process_id(), self)
        self.join_writer(end)
        return end

    def join_reader(self, end):
        self.readers.append(end)

    def join_writer(self, end):
        self.writers.append(end)

    def leave_reader(self, end):
        if not self.isretired:
            self.readers.remove(end)
            if len(self.readers)==0:
                # Set channel retired
                self.isretired = True
                for p in self.writequeue[:]:
                    p.retire()

    def leave_writer(self, end):
        if not self.isretired:
            self.writers.remove(end)
            if len(self.writers)==0:
                # Set channel retired
                self.isretired = True
                for p in self.readqueue[:]: # ATOMIC copy
                    p.retire()


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
