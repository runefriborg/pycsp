"""
Channelend module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
from exceptions import *
from pycsp.common.const import *

# Functions
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
class ChannelEnd:
    def __init__(self, channel):
        self.channel = channel
        self.op = WRITE

        # Prevention against multiple retires / poisons
        self.isretired = False
        self.ispoisoned = False

        self.restore_info = None

    # To be able to support the pickle module, we erase the reference
    # to the channel control, before pickling. This is then restored when
    # the channelend is depickled using the necessary saved info in restore_info.
    # Also, the total number of namespace_references should be kept constant after
    # a __getstate__ and a _restore
    def __getstate__(self):
        odict = self.__dict__
        
        odict['restore_info'] = (self.channel.channelhome, self.channel.name)

        # Remove channel reference from process
        p,_ = getThreadAndName()
        p.namespace_references[self.channel.name] -= 1

        # Clear channelcontrol
        del odict['channel']

        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)

        # TODO: A possible optimization, would be to delay the _restore, to __call__ in
        # if not self.channel then self._restore()   manner.
        self._restore()

    def _restore(self):
        # restore ChannelControl
        try:
            self.channel = pycsp.channel.ChannelControl(name=self.restore_info[1], connect=self.restore_info[0])

            # Add channel reference to process
            p,_ = getThreadAndName()
            if p.namespace_references.has_key(self.channel.name):
                p.namespace_references[self.channel.name] += 1
            else:
                p.namespace_references[self.channel.name] = 1 

        except SocketBindException as e:
            raise ChannelSocketException("PyCSP (reconnect to channel) unable to connect to address (%s)" % (e.addr))
        
    def _poison(self, *ignore):
        raise ChannelPoisonException()

    def poison(self):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")

        if not self.ispoisoned:
            self.channel.poison(direction=self.op)
            self.__call__ = self._poison
            self.ispoisoned = True

    def _retire(self, *ignore):
        raise ChannelRetireException()

    def retire(self):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")

        if not self.isretired:
            self.channel.retire(direction=self.op)
            self.__call__ = self._retire
            self.isretired = True

    def __repr__(self):
        return "<ChannelEndWrite on channel named %s>" % self.channel.name

    def isWriter(self):
        return self.op == WRITE

    def isReader(self):
        return self.op == READ

    
class ChannelEndWrite(ChannelEnd):
    def __init__(self, channel):
        ChannelEnd.__init__(self, channel)
        self.op = WRITE

    def __call__(self, msg):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")
        return self.channel._write(msg)

    def post_write(self, process, msg):
        self.channel.CM.post_write(self.channel, process, msg)

    def __repr__(self):
        return "<ChannelEndWrite on channel named %s>" % self.channel.name


class ChannelEndRead(ChannelEnd):
    def __init__(self, channel):
        ChannelEnd.__init__(self, channel)
        self.op = READ

    def __call__(self, msg):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")
        return self.channel._read()

    def post_read(self, process):
        self.channel.CM.post_read(self.channel, process)

    def __repr__(self):
        return "<ChannelEndRead on channel named %s>" % self.channel.name

# Run tests
if __name__ == '__main__':
    import doctest
    doctest.testmod()
