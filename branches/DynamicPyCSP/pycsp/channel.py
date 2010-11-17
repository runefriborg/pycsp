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
from channelend import ChannelEndRead, ChannelEndWrite
from pycsp.common.const import *
from discovery import Discover
from selection import Sync

import time, random
import socket


#HOST_IP = socket.gethostbyname(socket.gethostname())



# Classes


class ChannelHome(object):
    """ Channel Home class.
    Not every channel will have a ChannelHome.
    Only one ChannelHome per unique channel name must exist.
    """
    def __init__(self, name, buffer, level):
        self.name = name
        self.buffer = buffer
        self.level = level

        # Channel request queues
        self.readqueue = []
        self.writequeue = []
        
        # Count, makes sure that all processes knows how many channel ends have retired
        self.readers = []
        self.writers = []



class Channel(object):
    """ Channel class.

    This class main responsibility is to connect the channel ends with eachother, as long
    as no ChannelHome is created. This means, that as long as we only have one reader and one
    writer, this class will handle everything.
    """

    def __init__(self, name=None, buffer=0):

        if name == None:
            # Create unique name
            self.name = str(random.random())+str(time.time())
        else:
            self.name=name
        
        # Check if a ChannelHome exists? (yes, later when going distributed)
        
        self.readqueue = []
        self.writequeue = []

        self.readers = []
        self.writers = []

        self.ispoisoned = False
        self.isretired = False

        #- self.s = Scheduler()        
        self.level = 0
        self.sync = Sync(self.level, self)


    def _read(self):
        self.check_termination()

        p = self.s.current        
        p.setstate(ACTIVE)
        req = ChannelReq(p)
        self.post_read(req)
        req.process.wait()
        self.remove_read(req)

        if req.result==SUCCESS:
            return req.msg
        
        self.check_termination()
            
        print 'We should not get here in read!!!'
        return None #Here we should handle that a read was cancled...

    
    def _write(self, msg):
        self.check_termination()

        p = self.s.current
        
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
                self.sync.retire()

    def leave_writer(self, end):
        if not self.isretired:
            self.writers.remove(end)
            if len(self.writers)==0:
                # Set channel retired
                self.isretired = True
                self.sync.retire()


# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
