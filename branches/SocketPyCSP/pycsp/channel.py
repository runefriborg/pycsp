"""
Channel module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@diku.dk>, Rune M. Friborg <runef@diku.dk>.
See LICENSE.txt for licensing details (MIT License). 
"""
# Imports
import uuid
import osprocess
from channelend import ChannelEndRead, ChannelEndWrite 
import protocol
from exceptions import *
from pycsp.common.const import *


def close(*channels):
    """
    Executes cleanup and shuts down channel home threads nicely
    """

    # First deregister all channels
    for x in channels:
        x.control._deregister()

    # Then wait for threads to finish, thus avoiding deadlocks from
    # conflicting threads
    for x in channels:
        x.control._threadjoin()

# Classes
class Channel(object):
    """
    This is the frontend class to the ChannelControl object.
    It's function is to handle the automatic termination of the
    channel home.
    """
    def __init__(self, name=None, buffer=0, connect=None, server=None):

        try:
            self.control = ChannelControl(name, buffer, connect, server)
        except SocketBindException:
            self.control = None
            raise SocketBindException()

        # public methods available to the user
        self.writer = self.control.writer
        self.reader = self.control.reader
        self.retire_reader = self.control.retire_reader
        self.retire_writer = self.control.retire_writer
        self.poison = self.control.poison
        
        # Register this channel reference at the channel home thread
        self.control._register()

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


    def __del__(self):
        """
        Destructor
        
        Deregisters the channel reference from the channel homes and thus allows
        the channel home thread to shutdown when all channel references have
        terminated
        """
        if self.control:
            self.control._deregister()

    def close(self):
        if self.control:
            self.control._deregister()
            self.control._threadjoin()
        
        
class ChannelControl(object):
    def __init__(self, name=None, buffer=0, connect=None, server=None):
        
        self.ispoisoned=False
        self.isretired=False

        
        # Check args
        if server != None and connect != None:
            raise Exception("Either connect or server may be set")
        if name == None and connect != None:
            raise Exception("Must provide name when connecting to remote channel")

        # Set name
        if name == None:
            # Create 16 byte unique name based on network address, sequence number and time sample.
            self.name = uuid.uuid1().bytes
        else:
            if len(name) > 16:
                raise Exception("Channel names are limited to 16 characters")

            self.name=name


        # Set channel home
        self.channelhomethread = None
        self.registered = False
        if connect == None:
            # Get local channel home
            # These should handle multiple channels in the future
            if server == None:
                self.channelhomethread = protocol.ChannelHomeThread(self.name, buffer)
            else:
                self.channelhomethread = protocol.ChannelHomeThread(self.name, buffer, server)
            self.channelhomethread.start()
            self.channelhome = self.channelhomethread.address
        else:
            self.channelhome = connect

    def _threadjoin(self):
        if self.channelhomethread != None:
            self.channelhomethread.join()

    def _register(self):
        if not self.registered:
            self.registered = True
            protocol.register(self)

    def _deregister(self):
        if self.registered:
            self.registered = False
            protocol.deregister(self)
    
    def check_termination(self):
        if self.ispoisoned:
            raise ChannelPoisonException()
        if self.isretired:
            raise ChannelRetireException()

    def _read(self):
        self.check_termination()

        p = osprocess.getProc()
        p.state = READY
        p.sequence_number += 1
        
        protocol.post_read(self, p)

        if p.state == READY:
            p.wait()

        if p.state == SUCCESS:
            return p.result_msg                
        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self.check_termination()

        print 'We should not get here in read!!!', p.state
        return None

    
    def _write(self, msg):
        self.check_termination()

        p = osprocess.getProc()
        p.state = READY
        p.sequence_number += 1

        protocol.post_write(self, p, msg)

        if p.state == READY:
            p.wait()
        
        if p.state == SUCCESS:
            return               
        elif p.state == POISON:
            self.ispoisoned = True
        elif p.state == RETIRE:
            self.isretired = True

        self.check_termination()

        print 'We should not get here in read!!!', p.state
        return None
    
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

    def retire_reader(self):
        if not self.isretired:
            retired = protocol.retire_reader(self)
            if retired:
                self.isretired = True

    def retire_writer(self):
        if not self.isretired:
            retired = protocol.retire_writer(self)
            if retired:
                self.isretired = True

    def poison(self):
        if not self.ispoisoned:
            self.ispoisoned = True
            protocol.poison(self)
