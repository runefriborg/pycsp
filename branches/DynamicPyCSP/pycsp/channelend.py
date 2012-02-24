"""
Channelend module

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

# Functions
def IN(channel):
    """ Join as reader
    """
    return channel.reader()

def OUT(channel):
    """ Join as writer
    """
    return channel.writer()

def retire(*list_of_channelEnds):
    """ Retire reader or writer, to do auto-poisoning
    When all readers or writer of a channel have retired. The channel is retired.
    """    
    for channelEnd in list_of_channelEnds:
        channelEnd.retire()

def poison(*list_of_channelEnds):
    """ Poison channel
    """
    for channelEnd in list_of_channelEnds:
        channelEnd.poison()

# Classes
class ChannelEndWrite():
    def __init__(self, process, channel):
        self.channel = channel
        self.sync = channel.sync
        self.process = process # Unused..
        self.op = WRITE

        # Prevention against multiple retires
        self.isretired = False

    def __call__(self, msg):
        self.sync.write(msg)
    

    def poison(self):
        self.sync.poison()

    def post_write(self, req):
        #Alert, participating in an external choice.
        self.sync.provide_alt_support()
        self.sync.post_write(req)
        
    def remove_write(self, req):
        #Alert, participating in an external choice.
        self.sync.remove_write(req)
        self.sync.no_alt_support()

        
    def _retire(self, msg):
        raise ChannelRetireException()

    def retire(self):
        if not self.channel.isretired:
            self.channel.leave_writer(self)
            self.__call__ = self._retire
            self.post_write = self._retire
            self.isretired = True

    def reconnect(self):
        pass

    def __repr__(self):
        return "<ChannelEndWrite wrapping %s>" % self.channel

    def isWriter(self):
        return True

    def isReader(self):
        return False

class ChannelEndRead():
    def __init__(self, process, channel):
        self.channel = channel
        self.process = process # Unused..
        self.sync = channel.sync
        self.op = READ


        # Prevention against multiple retires
        self.isretired = False


    def __call__(self):
        return self.sync.read()

    def poison(self):
        self.sync.poison()

    def post_read(self, req):
        #Alert, participating in an external choice.
        self.sync.provide_alt_support()
        self.sync.post_read(req)
        
    def remove_read(self, req):
        #Alert, participating in an external choice.
        self.sync.remove_read(req)
        self.sync.no_alt_support()
    

    def _retire(self):
        raise ChannelRetireException()

    def retire(self):
        if not self.isretired:
            self.channel.leave_reader(self)
            self.__call__ = self._retire
            self.post_read = self._retire
            self.isretired = True

    def reconnect(self):
        pass

    def __repr__(self):
        return "<ChannelEndRead wrapping %s>" % self.channel

    def isWriter(self):
        return False

    def isReader(self):
        return True

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()

