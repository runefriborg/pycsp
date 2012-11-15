"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
# Imports
import uuid
import cPickle as pickle
import protocol
from exceptions import *
from const import *


# Classes
class Channel(object):
    """
    This is the frontend class to the ChannelControl object.
    It's function is to handle the automatic termination of the
    channel home by updating the reference count.
    """
    def __init__(self, name=None, buffer=0, connect=None):

        try:
            self.control = ChannelControl(name, buffer, connect)

            # Set channel address
            self.address = self.control.channelhome
            
            # Set channel name
            self.name = self.control.name

        except SocketBindException, e:
            self.control = None
            raise ChannelSocketException("PyCSP (create channel) unable to bind channel (%s) to address (%s)" % (e.addr))
        
        # public methods available to the user
        self.writer = self.control.writer
        self.reader = self.control.reader
        self.retire = self.control.retire
        self.poison = self.control.poison

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
            new.append(Channel())
        return new

    # syntactic sugar: N * Channel()
    def __rmul__(self, multiplier):
        return self.__mul__(multiplier)

        
        
class ChannelControl(object):
    def __init__(self, name=None, buffer=0, connect=None):
        
        self.ispoisoned=False
        self.isretired=False
        
        # Check args
        if name == None and connect != None:
            raise Exception("Must provide name when connecting to remote channel")

        # Set name
        if name == None:
            # Create 32 byte unique name based on network address, sequence number and time sample.
            self.name = uuid.uuid1().hex
        else:
            if len(name) > 32:
                raise Exception("Channel names are limited to 32 characters")

            self.name=name

        # Check that the channel name is not already registers at this channel. If this is the
        # case, then throw exception.
        p,_ = getThreadAndName()
        for c in p.registeredChanList:
            if self.name == c.name:
                raise FatalException("Reusing channel name in same process namespace")
                break

        self.CM = protocol.ChannelMessenger()

        # Set channel home
        self.channelhomethread = None

        if connect == None:
            # Get local channel home
            self.channelhomethread = protocol.ChannelHomeThread(self.name, buffer)
            self.channelhomethread.start()
            self.channelhome = self.channelhomethread.addr
        else:
            self.channelhome = connect


        # Register this channel control reference at the channel home thread
        # and at the current process. The current process will call deregister,
        # upon exit.
        self._register()
        p,_ = getThreadAndName()
        
        p.registeredChanList.append(self)


    def _register(self):
        self.CM.register(self)

    def _deregister(self):
        self.CM.deregister(self)
        
    def _threadjoin(self):
        if self.channelhomethread:
            self.channelhomethread.join()

    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()

    def _read(self):
        self.check_termination()

        p,_ = getThreadAndName()
        p.state = READY
        p.sequence_number += 1

        self.CM.post_read(self, p)

        if p.state == READY:
            p.wait()

        if p.state == SUCCESS:
            # unpickle msg if necessary
            msg = p.result_msg
            if type(msg) == list:
                return msg[0]
            else:
                return pickle.loads(msg)[0]

        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self.check_termination()

        print 'We should not get here in read!!!', p.state
        return None

    
    def _write(self, msg):
        self.check_termination()

        p,_ = getThreadAndName()
        p.state = READY
        p.sequence_number += 1

        self.CM.post_write(self, p, msg)

        if p.state == READY:
            p.wait()
        
        if p.state == SUCCESS:
            return               
        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self.check_termination()

        print 'We should not get here in write!!!', p.state, msg
        return None
    
    def reader(self):
        """
        Join as reader
        
        >>> C = Channel()
        >>> cin = C.reader()
        >>> isinstance(cin, ChannelEndRead)
        True
        """
        self.join(direction=READ)
        return ChannelEndRead(self)

    def writer(self):
        """
        Join as writer
        
        >>> C = Channel()
        >>> cout = C.writer()
        >>> isinstance(cout, ChannelEndWrite)
        True
        """
        self.join(direction=WRITE)
        return ChannelEndWrite(self)

    def join(self, direction):
        self.CM.join(self, direction)

    def retire(self, direction):
        if not self.isretired:
            self.CM.retire(self, direction)

    def poison(self, direction):
        if not self.ispoisoned:
            self.ispoisoned = True        
            self.CM.poison(self, direction)



##### Channel end  ####

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
        if isinstance(channelEnd, Channel):
            raise InfoException("Tried to retire a channel object. Only channel end objects may be retired.")
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
        if isinstance(channelEnd, Channel):
            raise InfoException("Tried to poison a channel object. Only channel end objects may be poisoned.")
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

        # Clear channelcontrol
        del odict['channel']

        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)

        # restore ChannelControl immediately, as the receiving end must register a new channel control, before
        # execution is given back to the calling process
        try:
            self.channel = ChannelControl(name=self.restore_info[1], connect=self.restore_info[0])
        except SocketBindException, e:
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


    def remove_write(self, req):
        """
        Including for compatibility with trace and greenlets
        """
        pass

    def __repr__(self):
        return "<ChannelEndWrite on channel named %s>" % self.channel.name


class ChannelEndRead(ChannelEnd):
    def __init__(self, channel):
        ChannelEnd.__init__(self, channel)
        self.op = READ

    def __call__(self):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")
        return self.channel._read()

    def post_read(self, process):
        self.channel.CM.post_read(self.channel, process)

    def remove_read(self, req):
        """
        Including for compatibility with trace and greenlets
        """
        pass

    def __repr__(self):
        return "<ChannelEndRead on channel named %s>" % self.channel.name
