"""
Channelend module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""

# Functions
def IN(channel):
    """ Join as reader
    >>> from __init__ import *
    >>> C = Channel()
    >>> isinstance(IN(C), ChannelEndRead)
    True
    """
    channel.join_reader()
    return ChannelEndRead(channel)

def OUT(channel):
    """ Join as writer
    >>> from __init__ import *
    >>> C = Channel()
    >>> isinstance(OUT(C), ChannelEndWrite)
    True
    """
    channel.join_writer()
    return ChannelEndWrite(channel)

def retire(*list_of_channelEnds):
    """ Retire reader or writer, to do auto-poisoning
    When all readers or writer of a channel have retired. The channel is poisoned.
    
    >>> from __init__ import *
    >>> C = Channel()
    >>> cout1, cout2 = OUT(C), OUT(C)
    >>> retire(cout1)

    >>> Spawn(Process(cout2, 'ok'))

    >>> try:
    ...     cout1('fail')
    ... except ChannelEndException:
    ...     True
    True

    >>> retire(cout2)    
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
    >>> Spawn(P1(IN(C1), OUT(C2)))
    >>> cout = OUT(C1)
    >>> cout('Test')

    >>> poison(cout)
    
    >>> cin = IN(C2)
    >>> cin()
    42
    """
    for channelEnd in list_of_channelEnds:
        channelEnd.poison()

# Exceptions
class ChannelEndException(Exception):
    def __init__(self, msg):
        Exception.__init__(self, msg)

# Classes
class ChannelEndWrite():
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False

        self.__call__ = self.channel._write
        self.post_write = self.channel.post_write

        self.remove_write = self.channel.remove_write
        self.poison = self.channel.poison

    def _retire(self, msg):
        raise ChannelEndException('Not allowed to write to retired channelend!')

    def retire(self):
        if self.isretired:
            raise ChannelEndException('Cannot retire twice!')
        self.channel.leave_writer()
        self.__call__ = self._retire
        self.post_write = self._retire
        self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndWrite wrapping %s>" % self.channel
        else:
            return "<ChannelEndWrite wrapping %s named %s>" % (self.channel, self.channel.name)


class ChannelEndRead():
    def __init__(self, channel):
        self.channel = channel
        self.isretired = False

        self.__call__ = self.channel._read
        self.post_read = self.channel.post_read

        self.remove_read = self.channel.remove_read
        self.poison = self.channel.poison

    def _retire(self):
        raise ChannelEndException('Not allowed to read from retired channelend!')

    def retire(self):
        if self.isretired:
            raise ChannelEndException('Cannot retire twice!')
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
