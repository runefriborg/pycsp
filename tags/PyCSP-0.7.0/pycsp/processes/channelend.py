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

from const import *

# Exceptions
class ChannelRetireException(Exception): 
    def __init__(self):
        pass

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
class ChannelEnd:
    def __init__(self):
        self.channel = None
        self.isretired = False

    def post_write(self, req):
        if self.isretired:
            raise ChannelRetireException()
        self.channel.post_write(req)

    def post_read(self, req):
        if self.isretired:
            raise ChannelRetireException()
        self.channel.post_read(req)

    def remove_write(self, req):
        self.channel.remove_write(req)

    def remove_read(self, req):
        self.channel.remove_read(req)

    def poison(self):
        self.channel.poison()

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEnd wrapping %s>" % self.channel
        else:
            return "<ChannelEnd wrapping %s named %s>" % (self.channel, self.channel.name)

    # To be able to support the pickle module, we erase all references to
    # shared memory, before pickling. References are then restored when
    # the channelend is depickled.
    def __getstate__(self):
        _dict = self.__dict__.copy()

        # This erases the references for both the original and the copy.
        # If we could limit it to only the copy, then we would not need to
        # call Channel.restore() in all Channel methods.

        _dict['channel'].lock = None
        _dict['channel'].manager = None
        _dict['channel'].syncData = None
        return _dict

    def __setstate__(self, dict):
        self.__dict__ = dict
        self.channel.restore()

        # To record the amount of channel copies, a counter is incremented.
        # This counter is checked in Channel.__del__, to ensure that the 
        # shared data segment is not retired unless no more copies are left.
        self.channel.lock.acquire()
        self.channel.syncData.copies += 1
        self.channel.lock.release()


class ChannelEndWrite(ChannelEnd):
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False
        self.op = WRITE

    def __call__(self, val):
        if self.isretired:
            raise ChannelRetireException()
        self.channel._write(val)

    def retire(self):
        if not self.isretired:
            self.channel.leave_writer()
            self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndWrite wrapping %s>" % self.channel
        else:
            return "<ChannelEndWrite wrapping %s named %s>" % (self.channel, self.channel.name)


class ChannelEndRead(ChannelEnd):
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False
        self.op = READ

    def __call__(self):
        if self.isretired:
            raise ChannelRetireException()
        return self.channel._read()

    def retire(self):
        if not self.isretired:
            self.channel.leave_reader()
            self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndRead wrapping %s>" % self.channel
        else:
            return "<ChannelEndRead wrapping %s named %s>" % (self.channel, self.channel.name)

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()


