"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
# Imports
import uuid

try:
    import cPickle as pickle
except ImportError:
    import pickle

from pycsp.parallel import protocol
from pycsp.parallel.exceptions import *
from pycsp.parallel.const import *

# Classes
class Channel(object):
    """
pycsp.parallel.Channel(name=None, buffer=0, connect=None)

name is the name of the channel, which must be used by remote processes connecting to the same process. 
    
Create a PyCSP channel for synchronous communication.
    """
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


        self._CM = protocol.ChannelMessenger()

        # Set channel home
        self._channelhomethread = None


        try:
            if connect == None:

                # Check that the channel name is not already registered at this channel. If this is the
                # case, then throw exception.
                p,_ = getThreadAndName()

                for c in p.registeredChanHomeList:
                    if self.name == c.name:
                        raise InfoException("Reusing channel name in same process namespace")

                # Get local channel home
                self._channelhomethread = protocol.ChannelHomeThread(self.name, buffer)
                self._channelhomethread.start()
                self.address = self._channelhomethread.addr

            else:
                self.address = connect

            # Register channel reference at channelhomethread
            self._registered = False            
            self._register()

        except SocketBindException as e:
            raise ChannelSocketException("PyCSP (create channel) unable to bind channel (%s) to address (%s)" % (e.addr))

    def _register(self):
        # Register this channel reference at the channel home thread
        # and at the current process. The current process will call deregister,
        # upon exit.
        self._CM.register(self)

        p,_ = getThreadAndName()
        if self._channelhomethread:
            p.registeredChanHomeList.append(self)
        else:
            p.registeredChanConnectList.append(self)

        self._registered = True

    def _deregister(self):
        self._CM.deregister(self)

    def _check_registration(self):
        if not self._registered:
            self._register()
        
    def _threadjoin(self):
        if self._channelhomethread:
            self._channelhomethread.join()

    def _check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()
    

    def _read(self):
        self._check_termination()
        self._check_registration()

        p,_ = getThreadAndName()
        p.state = READY
        p.sequence_number += 1

        self._CM.post_read(self, p)

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

        self._check_termination()

        print('We should not get here in read!!!' + str(p.state))
        return None

    
    def _write(self, msg):
        self._check_termination()
        self._check_registration()

        p,_ = getThreadAndName()
        p.state = READY
        p.sequence_number += 1

        self._CM.post_write(self, p, msg)

        if p.state == READY:
            p.wait()
        
        if p.state == SUCCESS:
            return               
        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self._check_termination()

        print('We should not get here in write!!! ' + str(p.state) + ' ' + str(msg))
        return None
    
    def reader(self):
        """
        Join as reader
        
        >>> C = Channel()
        >>> cin = C.reader()
        >>> isinstance(cin, ChannelEndRead)
        True
        """
        self._check_registration()
        self._CM.join(self, direction=READ)
        return ChannelEndRead(self)

    def writer(self):
        """
        Join as writer
        
        >>> C = Channel()
        >>> cout = C.writer()
        >>> isinstance(cout, ChannelEndWrite)
        True
        """
        self._check_registration()
        self._CM.join(self, direction=WRITE)
        return ChannelEndWrite(self)

    def _retire(self, direction):
        if not self.isretired:
            self._check_registration()
            self._CM.retire(self, direction)

    def _poison(self, direction):
        if not self.ispoisoned:
            self._check_registration()
            self.ispoisoned = True        
            self._CM.poison(self, direction)

    def disconnect(self):
        """
        Explicit close is only relevant for channel references
        connected to remote channels

        It can be used to make an early close, to allow another interpreter
        hosting the channel home, to quit. This is especially useful when
        used in a server - client setting, where the client has provied a 
        reply channel and desires to disconnect after having received the reply.

        The channel reference will automatically open and reconnect if it is used after a close.
        """
        p,_ = getThreadAndName()
        if self in p.registeredChanConnectList:
            self._deregister()
            p.registeredChanConnectList.remove(self)


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
    # to the channel, before pickling. This is then restored when
    # the channelend is depickled using the necessary saved info in restore_info.
    # Also, the total number of namespace_references should be kept constant after
    # a __getstate__ and a _restore
    def __getstate__(self):
        odict = self.__dict__
        
        odict['restore_info'] = (self.channel.address, self.channel.name)

        # Clear channel object
        del odict['channel']

        return odict

    def __setstate__(self, dict):
        self.__dict__.update(dict)

        # restore Channel immediately, as the receiving end must register a new channel reference, before
        # execution is given back to the calling process
        try:
            self.channel = Channel(name=self.restore_info[1], connect=self.restore_info[0])
        except SocketBindException as e:
            raise ChannelSocketException("PyCSP (reconnect to channel) unable to connect to address (%s)" % (e.addr))
        
    def _poison(self, *ignore):
        raise ChannelPoisonException()

    def poison(self):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")

        if not self.ispoisoned:
            self.channel._poison(direction=self.op)
            self.__call__ = self._poison
            self.ispoisoned = True

    def _retire(self, *ignore):
        raise ChannelRetireException()

    def retire(self):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")

        if not self.isretired:
            self.channel._retire(direction=self.op)
            self.__call__ = self._retire
            self.isretired = True

    def __repr__(self):
        return "<ChannelEndWrite on channel named %s>" % self.channel.name

    def isWriter(self):
        return self.op == WRITE

    def isReader(self):
        return self.op == READ

    def disconnect(self):
        """
        Explicit close is only relevant for closing mobile channel ends in a 
        process.

        Mobile channel ends are automatically closed when a process terminates
        """
        p,_ = getThreadAndName()

        # Initiate clean up and wait for channel to finish outstanding operations.
        if self.channel in p.activeChanList:
            self.channel._CM.leave(self.channel, p)
            
            # Wait for channel        
            p.cond.acquire()
            if not self.channel.name in p.closedChanList:
                p.cond.wait()
            p.cond.release()


            p.closedChanList.remove(self.channel.name)
            p.activeChanList.remove(self.channel)

        # Tell channel to disconnect
        self.channel.disconnect()

    
class ChannelEndWrite(ChannelEnd):
    def __init__(self, channel):
        ChannelEnd.__init__(self, channel)
        self.op = WRITE

    def __call__(self, msg):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")
        return self.channel._write(msg)

    def post_write(self, process, msg):
        self.channel._CM.post_write(self.channel, process, msg)


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
        self.channel._CM.post_read(self.channel, process)

    def remove_read(self, req):
        """
        Including for compatibility with trace and greenlets
        """
        pass

    def __repr__(self):
        return "<ChannelEndRead on channel named %s>" % self.channel.name
