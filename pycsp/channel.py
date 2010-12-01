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
from communicator import *
from home import ChannelHomeManager

import uuid

# Functions
def Channel(name=None, buffer=0, connect=None):
    """
    Creates a new channel.
    """
    if connect == None:
        # Main channel object.
        return ChannelHost(name, buffer)
    else:
        if name == None:
            raise Exception("Error! Need name parameter to connect with channel")

        # Connect to other channel object.
        return ChannelLink(name, connect)


# Classes
class ChannelHost(object):
    """ Channel class.

    This class main responsibility is to connect the channel ends with each other. A ChannelHome
    is passed on to the first reader joins the channel. On creation of the ChannelHome
    , all writers are passed on to the ChannelHome.

    If the channel is local, the ChannelHost simulates a ChannelHome.
    """
    def __init__(self, name, buffer):
        if name == None:
            # Create unique name
            self.name = str(uuid.uuid4())
        else:
            self.name=name

        # Create a channel home
        self.home = ChannelHome(buffer)

        # Register channel home
        ChannelHomeManager().register(name, self.home)

        # Setup methods
        self.join_reader = self.home.join_reader
        self.join_writer = self.home.join_writer
        self.leave_reader = self.home.leave_reader
        self.leave_writer = self.home.leave_writer                       

    def reader(self):
        p = current_process_id()

        end = ChannelEndRead(p, self.home)
        self.join_reader(end)
        return end

    def writer(self):
        p = current_process_id()

        end = ChannelEndWrite(p, self.home)
        self.join_writer(end)
        return end
    
    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1), buffer=self.buffer))
        return new

    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)


class ChannelLink(object):
    """
    The ChannelLink class handles the redirection of channel requests, to the actual Channel home through the channel host.

    """
    def __init__(self, name, connect):
        self.name = name
        self.addr = connect

        self.home_addr = self.__get_channel_home()

        

    def __get_channel_home(self):
        C = Scheduler().communicator
        return C.request_channel_home(self.addr, self.name)

    def reader(self):
        p = current_process_id()

        end = ChannelEndRead(p, self.home)
        self.join_reader(end)
        return end

    def writer(self):
        p = current_process_id()

        end = ChannelEndWrite(p, self.home)
        self.join_writer(end)
        return end
    
    def __pos__(self):
        return self.reader()

    def __neg__(self):
        return self.writer()

    def __mul__(self, multiplier):
        new = [self]
        for i in range(multiplier-1):
            new.append(Channel(name=self.name+str(i+1), buffer=self.buffer))
        return new

    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)


class ChannelHome(object):
    def __init__(self, buffer=0):            
        self.readers = []
        self.writers = []

        self.ispoisoned = False
        self.isretired = False

        #- self.s = Scheduler()    
        self.level = 0
        self.sync = Sync(self.level, self)
        

    def join_reader(self, end):

        # Test sync level
        if len(self.readers) > 0:
            self.sync.provide_any_support()

        self.readers.append(end)

    def join_writer(self, end):

        # Test sync level
        if len(self.writers) > 0:
            self.sync.provide_any_support()

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
