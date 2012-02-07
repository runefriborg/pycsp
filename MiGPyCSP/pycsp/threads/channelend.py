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
    print 'Warning: IN() are deprecated and will be removed'
    return channel.reader()

def OUT(channel):
    """ Join as writer
    """
    print 'Warning: OUT() are deprecated and will be removed'
    return channel.writer()

def retire(*list_of_channelEnds):
    """ Retire reader or writer, to do auto-poisoning
    When all readers or writer of a channel have retired. The channel is retired.
    
    >>> from __init__ import *
    >>> C = Channel()
    >>> cout1, cout2 = C.writer(), C.writer()
    >>> retire(cout1)

    >>> Spawn(Process(cout2, 'ok'))

    >>> try:
    ...     cout1('fail')
    ... except ChannelRetireException:
    ...     True
    True

    >>> cin = C.reader()
    >>> retire(cin)
    """    
    for channelEnd in list_of_channelEnds:
        channelEnd.retire()

def poison(*list_of_channelEnds):
    """ Poison channel
    >>> from __init__ import *

    >>> @process
    ... def P1(cin, done):
    ...     try:
    ...         while True:
    ...             cin()
    ...     except ChannelPoisonException:
    ...         done(42)

    >>> C1, C2 = Channel(), Channel()
    >>> Spawn(P1(C1.reader(), C2.writer()))
    >>> cout = C1.writer()
    >>> cout('Test')

    >>> poison(cout)
    
    >>> cin = C2.reader()
    >>> cin()
    42
    """
    for channelEnd in list_of_channelEnds:
        channelEnd.poison()

# Classes
class ChannelEndWrite:
    def __init__(self, channel):
        self.channel = channel
        self.op = WRITE

        # Prevention against multiple retires
        self.isretired = False

        self.__call__ = self.channel._write
        self.post_write = self.channel.post_write
        self.remove_write = self.channel.remove_write
        self.poison = self.channel.poison

    def _retire(self, msg):
        raise ChannelRetireException()

    def retire(self):
        if not self.isretired:
            self.channel.leave_writer()
            self.__call__ = self._retire
            self.post_write = self._retire
            self.isretired = True


    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndWrite wrapping %s>" % self.channel
        else:
            return "<ChannelEndWrite wrapping %s named %s>" % (self.channel, self.channel.name)


class ChannelEndRead:
    def __init__(self, channel):
        self.channel = channel
        self.op = READ

        # Prevention against multiple retires
        self.isretired = False

        self.__call__ = self.channel._read
        self.post_read = self.channel.post_read
        self.remove_read = self.channel.remove_read
        self.poison = self.channel.poison

    def _retire(self):
        raise ChannelRetireException()

    def retire(self):
        if not self.isretired:
            self.channel.leave_reader()
            self.__call__ = self._retire
            self.post_read = self._retire
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
