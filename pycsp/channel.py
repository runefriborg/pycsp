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
import random, time
import osprocess
from channelend import ChannelEndRead, ChannelEndWrite 
import protocol
from pycsp.common.const import *

# Classes
class Channel(object):
    def __init__(self, name=None, buffer=0, connect=None):
        
        self.ispoisoned=False
        self.isretired=False

        
        # Check args
        if name == None and connect != None:
            raise Exception("Must provide name when connecting to remote channel")

        # Set name
        if name == None:
            # Create unique name
            self.name = str(random.random())+str(time.time())
        else:
            self.name=name

        # Set channel home
        if connect == None:
            # Get local channel home
            # These should handle multiple channels in the future
            self.channelhomethread = protocol.ChannelHomeThread()
            self.channelhomethread.start()
            self.channelhome = self.channelhomethread.address
        else:
            self.channelhome = connect

    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()

    def _read(self):
        p = osprocess.getProc()
        self.check_termination()
        p.state = READY
        
        protocol.post_read(self, p)
        p.wait()

        protocol.remove_read(self, p)
        
        if p.state == SUCCESS:
            print "GOT %s" % (str(p.result_msg))
            return p.result_msg                
        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self.check_termination()

        print 'We should not get here in read!!!', p.state
        return None

    
    def _write(self, msg):
        p = osprocess.getProc()
        self.check_termination()
        p.state = READY
        
        protocol.post_write(self, p, msg)
        p.wait()

        protocol.remove_write(self, p)
        
        if p.state == SUCCESS:
            return               
        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self.check_termination()

        print 'We should not get here in read!!!', p.state
        return None

    # syntactic sugar: cin = +chan
    def __pos__(self):
        return self.reader()
    
    # syntactic sugar: cout = -chan
    def __neg__(self):
        return self.writer()

    # syntactic sugar: Channel() * N
    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1)))
        return new

    # syntactic sugar: N * Channel()
    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)
    
    def reader(self):
        """
        Join as reader
        
        >>> C = Channel()
        >>> cin = C.reader()
        >>> isinstance(cin, ChannelEndRead)
        True
        """
        self.join_reader()
        return ChannelEndRead(self)

    def writer(self):
        """
        Join as writer
        
        >>> C = Channel()
        >>> cout = C.writer()
        >>> isinstance(cout, ChannelEndWrite)
        True
        """
        self.join_writer()
        return ChannelEndWrite(self)

    def join_reader(self):
        protocol.join_reader(self)

    def join_writer(self):
        protocol.join_writer(self)

    def leave_reader(self):
        if not self.isretired:
            retired = protocol.leave_reader(self)
            if retired:
                self.isretired = True

    def leave_writer(self):
        if not self.isretired:
            retired = protocol.leave_writer(self)
            if retired:
                self.isretired = True

    def poison(self):
        if not self.ispoisoned:
            self.ispoisoned = True
            protocol.poison(self)
