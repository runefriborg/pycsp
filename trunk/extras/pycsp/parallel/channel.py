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
    Any-2-any channel for communication between both local and remote processes.
    
    To communicate on this channel, channel ends must be requested using the .reader/.writer methods.

    Usage:
      >>> A = Channel("A")
      >>> cout = A.writer()
      >>> cout("Hello World")

    A channel is registered at the Python interpreter level and hosted in the interpreter where it
    was created.

    Retrieving the address and name of a channel:
    >>> print(A.address)
    ('10.11.105.254', 33703)
    >>> print(A.name)
    A

    Channel(name=None, buffer=0, connect=None):
    name
      is a string used for identifying the Channel and must be unique for every Channel instance.
      The name is limited to maximum 32 characters.
    buffer
      The channel may be buffered by configuring a buffer of size <buffer>.
      buffer=3 will create a channel which can contain three elements, before blocking send.
    connect
      If provided with (host, port), the channel will not create a host, but instead try to connect
      to (host, port) and register at the channel here.
      A name must be provided when connect is set.

    Public variables:
      Channel.address    (host, port) where the channel is hosted
      Channel.name       name to identify the hosted channel
    """

    # Constructor
    def __init__(self, name=None, buffer=0, connect=None):

        self._ispoisoned=False
        self._isretired=False
        
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
        if self._ispoisoned:
            raise ChannelPoisonException()
        if self._isretired:
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
            self._ispoisoned = True
        elif p.state == RETIRE:
            self._isretired = True

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
            self._ispoisoned = True
        elif p.state == RETIRE:
            self._isretired = True

        self._check_termination()

        print('We should not get here in write!!! ' + str(p.state) + ' ' + str(msg))
        return None
    
    def reader(self):
        """
        Create and return a receiving end of the channel

        Returns:
          ChannelEndRead object

        Usage:
          >>> C = Channel()
          >>> cin = C.reader()
          >>> print( cin() ) # Read
        """
        self._check_registration()
        self._CM.join(self, direction=READ)
        return ChannelEndRead(self)

    def writer(self):
        """
        Create and return a writing end of the channel

        Returns:
          ChannelEndWrite object

        Usage:
          >>> C = Channel()
          >>> cout = C.writer()
          >>> cout("Hello reader")
        """
        self._check_registration()
        self._CM.join(self, direction=WRITE)
        return ChannelEndWrite(self)

    def _retire(self, direction):
        if not self._isretired:
            self._check_registration()
            self._CM.retire(self, direction)

    def _poison(self, direction):
        if not self._ispoisoned:
            self._check_registration()
            self._ispoisoned = True        
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
    """ Retire channel ends

    When a channel end is retired, the channel is signaled that a channel end
    has now left the channel. When the set of all reading or writing channel ends is set
    to none, then the channel enters a retired state whereafter
    all actions on the channel will invoke a ChannelRetireException which
    is propagated through the PyCSP network to nicely shutdown all processes unless
    caugth by the user with a try/except clause.

    Retiring is an improved version of poisoning, which avoids the race condition issue
    when terminating multiple concurrent processes.

    Usage:
    >>> retire(cin0)
    >>> retire(cin0, cin1, cout0)
    >>> retire(*cinList)
    """
    for channelEnd in list_of_channelEnds:
        if isinstance(channelEnd, Channel):
            raise InfoException("Tried to retire a channel object. Only channel end objects may be retired.")
        channelEnd.retire()

def poison(*list_of_channelEnds):
    """ Poison channel ends
    
    When a channel end is poisoned, the channel is set into a poisoned state where
    after all actions on the channel will invoke a ChannelPoisonException which
    is propagated through the PyCSP network to shutdown all processes unless
    caugth by the user with a try/except clause.

    Notice that poisoning may cause race conditions, when terminating multiple concurrent processes.
    See retire for an improved shutdown method.

    Usage:
    >>> poison(cin0)
    >>> poison(cin0, cin1, cout0)
    >>> poison(*cinList)
    """
    for channelEnd in list_of_channelEnds:
        if isinstance(channelEnd, Channel):
            raise InfoException("Tried to poison a channel object. Only channel end objects may be poisoned.")
        channelEnd.poison()

# Classes
class ChannelEnd:
    def __init__(self, channel):


        self.channel = channel
        self._op = WRITE

        # Prevention against multiple retires / poisons
        self._isretired = False
        self._ispoisoned = False

        self._restore_info = None


    def __getstate__(self):
        """
        Enables channel end mobility
        """

        # To be able to support the pickle module, we erase the reference
        # to the channel, before pickling. This is then restored when
        # the channelend is depickled using the necessary saved info in restore_info.
        # Also, the total number of namespace_references should be kept constant after
        # a __getstate__ and a _restore

        odict = self.__dict__
        
        odict['_restore_info'] = (self.channel.address, self.channel.name)

        # Clear channel object
        del odict['channel']

        return odict

    def __setstate__(self, dict):
        """
        Enables channel end mobility
        """        

        self.__dict__.update(dict)

        # restore Channel immediately, as the receiving end must register a new channel reference, before
        # execution is given back to the calling process
        try:
            self.channel = Channel(name=self._restore_info[1], connect=self._restore_info[0])
        except SocketBindException as e:
            raise ChannelSocketException("PyCSP (reconnect to channel) unable to connect to address (%s)" % (e.addr))
        
    def _poison(self, *ignore):
        raise ChannelPoisonException()

    def poison(self):
        """ Poison channel end
    
        When a channel end is poisoned, the channel is set into a poisoned state where
        after all actions on the channel will invoke a ChannelPoisonException which
        is propagated through the PyCSP network to shutdown all processes unless
        caugth by the user with a try/except clause.

        Notice that poisoning may cause race conditions, when terminating multiple concurrent processes.
        See retire for an improved shutdown method.
        """

        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")

        if not self._ispoisoned:
            self.channel._poison(direction=self._op)
            self.__call__ = self._poison
            self._ispoisoned = True

    def _retire(self, *ignore):
        raise ChannelRetireException()

    def retire(self):
        """ Retire channel end

        When a channel end is retired, the channel is signaled that a channel end
        has now left the channel. When the set of all reading or writing channel ends is set
        to none, then the channel enters a retired state whereafter
        all actions on the channel will invoke a ChannelRetireException which
        is propagated through the PyCSP network to nicely shutdown all processes unless
        caugth by the user with a try/except clause.

        Retiring is an improved version of poisoning, which avoids the race condition issue
        when terminating multiple concurrent processes.
        """

        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")

        if not self._isretired:
            self.channel._retire(direction=self._op)
            self.__call__ = self._retire
            self._isretired = True

    def __repr__(self):
        return "<ChannelEndWrite on channel named %s>" % self.channel.name

    def isWriter(self):
        """
        Returns True for ChannelEndWrite object
        """
        return self._op == WRITE

    def isReader(self):
        """
        Returns True for ChannelEndRead object
        """
        return self._op == READ

    def disconnect(self):
        """
        Explicit close is only relevant for mobile channel ends to invoke an
        early close.

        The reason for an early close is to allow another interpreter
        hosting the channel home, to quit. This is especially useful when
        used in a server/client setting, where the client has provided a 
        reply channel and desires to disconnect after having received the reply.

        The mobile channel end reference will automatically open and reconnect if
        it is used after a close.
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
        self._op = WRITE

    def __call__(self, msg):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")
        return self.channel._write(msg)

    def _post_write(self, process, msg):
        self.channel._CM.post_write(self.channel, process, msg)


    def _remove_write(self, req):
        """
        Including for compatibility with trace and greenlets
        """
        pass

    def __repr__(self):
        return "<ChannelEndWrite on channel named %s>" % self.channel.name


class ChannelEndRead(ChannelEnd):
    """
    The reading end of a channel. 
    
    Usage:
      >>> val = reading_end()

    Throws:
      ChannelPoisonException()
      ChannelRetireException()

    If the poison and retire exceptions are not caught explicitly they will automatically be
    propagated to all other known channelends provided to the process in the argument list.
    """

    def __init__(self, channel):
        ChannelEnd.__init__(self, channel)
        self._op = READ

    def __call__(self):
        if not self.channel:
            raise FatalException("The user have tried to communicate on a channel end which have been moved to another process")
        return self.channel._read()

    def _post_read(self, process):
        self.channel._CM.post_read(self.channel, process)

    def _remove_read(self, req):
        """
        Including for compatibility with trace and greenlets
        """
        pass

    def __repr__(self):
        return "<ChannelEndRead on channel named %s>" % self.channel.name
