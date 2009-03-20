#!/usr/bin/env python
# -*- coding: latin-1 -*-
"""
CSP Channels. 
Copyright (c) 2007 John Markus Bjørndalen, jmb@cs.uit.no.
See LICENSE.txt for licensing details (MIT License). 
"""
from __future__ import with_statement
import threading
from Guards import Guard

# ------------------------------------------------------------
# Some helper decorators, functions and classes.
#
def synchronized(func):
    "Decorator for creating java-like monitor functions"
    def _call(self, *args, **kwargs):
        with self._cond:
            return func(self, *args, **kwargs)
    return _call

def chan_poisoncheck(func):
    "Decorator for making sure that poisoned channels raise exceptions"
    def _call(self, *args, **kwargs):
        if self.poisoned:
            raise ChannelPoisonException()
        try:
            return func(self, *args, **kwargs)
        finally:
            if self.poisoned:
                raise ChannelPoisonException()
    return _call

def poisonChannel(ch):
    "Poisons a channel or a channel end"
    ch.poison()
    
class ChannelPoisonException(Exception): 
    def __init__(self):
        pass
    
# ------------------------------------------------------------
# Channel Ends
#

class ChannelEnd(object):
    """The channel ends are objects that replace the Channel read()
    and write() methods, and adds methods for forwarding poison()
    and pending() calls. 

    NB: read() and write() are not forwarded! That could allow the
    channel ends to be confused with proper channels, which would
    defeat the purpose of the channel ends.
    
    Also, ALT is not supported by default (no enable() or disable()).
    You need the Guard version of the ChannelEnd to do that (see
    ChannelInputEndGuard)."""
    def __init__(self, chan):
        self._chan = chan
    def channel(self):
        "Returns the channel that this channel end belongs to."
        return self._chan
    # simply pass on most calls to the channel by default
    def poison(self):
        return self._chan.poison()
    def pending(self):
        return self._chan.pending()

class ChannelOutputEnd(ChannelEnd):
    def __init__(self, chan):
        ChannelEnd.__init__(self, chan)
    def __call__(self, val):
        return self._chan._write(val)
    def __repr__(self):
        return "<ChannelOutputEnd wrapping %s>" % self._chan

class ChannelInputEnd(ChannelEnd):
    def __init__(self, chan):
        ChannelEnd.__init__(self, chan)
    def __call__(self):
        return self._chan._read()
    def __repr__(self):
        return "<ChannelInputEnd wrapping %s>" % self._chan

class ChannelInputEndGuard(ChannelInputEnd, Guard):
    '''This Channel input end is used for channels that can be used as
    input guards.  The "enable" and "disable" calls will be passed on
    to the channel.

    The channel end inherits from "Guard", which is necessary for
    "Alternate" to accept it (TODO: type checking in alternate).
    Inheriting from "Guard" also means that it is clearer that this is
    how a channel can be used as a guard.

    This guard calls the input enable/disable methods in the channel
    (_ienable, _idisable).  It does NOT support the X2Any channels.
    '''
    def __init__(self, chan):
        ChannelInputEnd.__init__(self, chan)
    def __repr__(self):
        return "<ChannelInputEndWGuard wrapping %s>" % self._chan
    def enable(self, guard):
        return self._chan._ienable(guard)
    def disable(self):
        return self._chan._idisable()


# TODO: we could support ChannelOutput guards with the following semantics:
# - the guard is true if a reader has committed to a read() (and is blocked waiting)
# - only one end of the channel can be a guard (safely)
#   (if both ends should be used as guards, we might need to oracle process to resolve multiple Alt/guard offers)

# ------------------------------------------------------------
# Channels
#

class Channel(object):
    def __init__(self, name):
        self.name = name
        self.poisoned = False
        self.write = ChannelOutputEnd(self)
        self.read  = ChannelInputEnd(self)
    def _write(self, val):
        raise "default method"
    def _read(self):
        raise "default method"
    def poison(self):
        self.poisoned = True

class BlackHoleChannel(Channel):
    def __init__(self, name=None):
        Channel.__init__(self, name)
    @chan_poisoncheck
    def _write(self, obj=None):
        pass
    @chan_poisoncheck
    def _read(self):
        raise "BlackHoleChannels are not readable"

class One2OneChannel(Channel):
    # Based on implementation of one-to-one channel: One2OneChannelImpl.java
    """
    NB:
    - the reading end of this channel may ALT on this channel
    - the writing end is committed (can not use ALT)
    """
    def __init__(self, name=None):
        Channel.__init__(self, name)
        self.read  = ChannelInputEndGuard(self)   # read can be used as an input guard.
        self.rwMonitor = threading.Condition()
        self._cond = self.rwMonitor  # TODO: cleaner sync
        self._pending = False        # For synhronization. True if a reader or writer has committed and waits for the other
        self.hold = None             # object transmitted through channel
        self._ialt = None            # to keep a reference back to the Alternative construct the channel is "enabled" in

    # A couple of points to be aware of with regards to read() and write():
    # - there are never more than one reader and one writer (since it's a one2one channel)
    #   so there is no third process that can enter and cause problems.
    #   (otherwise, somebody else could have entered the channel after, for instance
    #   the reader has signaled the writer and blocked on wait(), but before the
    #   writer has had the chance to wake up and re-aquire the lock/condition)
    # - since the _read and _write operations are synchronized, we generally have two cases:
    #   a) reader enters first, or b) writer enters first.
    # - Note to students: try to identify phases of _read() and _write() that can be labeled
    #   entry and exit protocol. 
    @synchronized
    @chan_poisoncheck
    def _write(self, obj = None):
        self.hold = obj
        if self._pending:
            # reader entered first and is waiting for us.
            # start the exit protocol (set pending to False and notify the other end)
            self._pending = False
            self.rwMonitor.notify()
        else:
            # we entered first, tell reader that we are waiting
            self._pending = True
            if self._ialt != None:
                # The channel is enabled as an input guard, so do the wake-up-call.
                # 
                # NB: we release the condition/lock to avoid a
                # deadlock situation that might occur if an ALT tries
                # to run disable() on this guard while we try to run
                # schedule(). In that case, the ALT has already
                # grabbed its lock, and we keep this lock, which could
                # cause a deadlock when both try to grab the other
                # lock.
                #
                # The code below looks like a potential race
                # condition: if this writer calls schedule and gets
                # blocked, another writer can enter and set _pending to
                # False and send a notify() to a non-existing reader
                # while the alt will eventually be awoken by the
                # schedule() and never find this channel in the
                # disable() phase (since _pending is False).
                #
                # The reason why this is still safe is that this is a
                # One2OneChannel, which has a single writer. The
                # Any2One channels use an extra lock, so multiple
                # writers can never enter _write() at the same time
                # even if we release this lock.
                # 
                self._cond.release()
                self._ialt.schedule()
                self._cond.acquire()
        self.rwMonitor.wait()

    @synchronized
    @chan_poisoncheck
    def _read(self):
        if self._pending:
            # writer entered first and is waiting for us
            # start the exit protocol (set pending to False and notify the other end)
            self._pending = False
        else:
            # we entered first, tell writer that we are waiting
            self._pending = True    
            self.rwMonitor.wait()
        hold = self.hold            # grab a copy before waking up writer 
        self.rwMonitor.notify()
        return hold

    @synchronized
    def poison(self):
        if self.poisoned:
            return
        self.poisoned = True
        self.rwMonitor.notifyAll()
        if self._ialt:
            # also wake up any input guards.
            self._ialt.schedule()   

    # ALT support
    @synchronized
    @chan_poisoncheck
    def _ienable(self, alt):
        """Turns on ALT selection for the channel. Returns true if the channel has a committed writer."""
        # NB: Alts will overwrite each other if both ends use ALT !!!
        if self._pending:
            # got a committed writer, tell the ALT construct
            return True
        self._ialt = alt
        return False

    @synchronized
    @chan_poisoncheck
    def _idisable(self):
        """Turns off ALT selection for the channel. Returns true if the channel has a committed writer."""
        self._ialt = None
        return self._pending

    @synchronized
    @chan_poisoncheck
    def pending(self):
        """Returns whether there is data pending on the channel (NB: strictly speaking,
        whether a reader or writer has committed)."""
        return self._pending

class Any2OneChannel(One2OneChannel):
    """Allows more than one writer to send to one reader. Supports ALT on the reader end."""
    def __init__(self, name=None):
        One2OneChannel.__init__(self, name)
        self.writerLock = threading.RLock()
    def _write(self, obj = None):
        with self.writerLock:  # ensure that only one writer attempts to write at any time
            return super(Any2OneChannel, self)._write(obj)
    
class One2AnyChannel(One2OneChannel):
    """Allows one writer to write to multiple readers. It does, however, not support ALT."""
    def __init__(self, name=None):
        One2OneChannel.__init__(self, name)
        self.read  = ChannelInputEnd(self)  # make sure ALT is not supported 
        self.readerLock = threading.RLock()
    def _read(self):
        with self.readerLock:  # ensure that only one reader attempts to read at any time
            return super(One2AnyChannel, self)._read()

class Any2AnyChannel(One2AnyChannel):
    def __init__(self, name=None):
        One2AnyChannel.__init__(self, name)
        self.writerLock = threading.RLock()
    def _write(self, obj = None):
        with self.writerLock:  # ensure that only one writer attempts to write at any time
            return super(Any2AnyChannel, self)._write(obj)

# TODO: Robert
# TODO: could use Queue as well, but that's another level of threading locks. 
class FifoBuffer(object):
    """NB: This class is not thread-safe. It should be protected by the user."""
    def __init__(self, maxlen=10):
        self.maxlen = maxlen
        self.q = []

    def empty(self):
        return len(self.q) == 0

    def full(self):
        return len(self.q) == self.maxlen

    def put(self, obj):
        assert not self.full()
        self.q.append(obj)

    def get(self):
        assert not self.empty()
        return self.q.pop(0)

# NB/TODO:
# - The naming is different from JCSP, where a buffered channel is, for instance
#   One2OneChannelX.java

# TODO: Robert
class BufferedOne2OneChannel(Channel):
    def __init__(self, name=None, buffer=None, bufsize=10):
        Channel.__init__(self, name)
        if bufsize < 1:
            raise "Buffered Channels can not have a buffer with a size less than 1!"
        self.read  = ChannelInputEndGuard(self)   # allow ALT
        self.rwMonitor = threading.Condition()
        self._cond = self.rwMonitor               
        self._ialt = None
        if buffer is None:
            self.buffer = FifoBuffer(bufsize)
        else:
            self.buffer = buffer

    @synchronized
    @chan_poisoncheck
    def _write(self, obj = None):
        # there will always be some space here since we block _after_ making the channel full,
        # forcing write to wait until a reader has removed at least one slot. 
        # write will not exit until there is at least one empty slot. 
        # (TODO: slightly confusing for people used to reader/writer problems in other systems?)
        self.buffer.put(obj)
        if self._ialt:
            self._ialt.schedule()
        else:
            self.rwMonitor.notify()
        if self.buffer.full():
            # wait until the buffer is non-full
            while self.buffer.full():
                self.rwMonitor.wait()

    @synchronized
    @chan_poisoncheck
    def _read(self):
        if self.buffer.empty():
            while self.buffer.empty():
                if self.poisoned:
                    raise ChannelPoisonException(self)
                self.rwMonitor.wait()
        # poisoning by the writer will also cause 
        # this end to wakeup, so check for poison again
        if self.poisoned:
            raise ChannelPoisonException(self)
        self.rwMonitor.notify()
        return self.buffer.get()

    @synchronized
    def poison(self):
        if self.poisoned:
            return # 
        self.poisoned = True
        self.rwMonitor.notifyAll()
        if self._ialt:
            # also wake up any input guards... (see notes in one2onechannel)
            self._ialt.schedule()

    @synchronized
    def _ienable(self, alt):
        """Turns on ALT selection for the channel. Returns true if the channel has 
        data that can be read, or if the channel has been poisoned."""
        if self.poisoned:
            return True
        if self.buffer.empty():
            self._ialt = alt
            return False
        return True

    # TODO: do a chan_poisoncheck instead? 
    @synchronized
    def _idisable(self):
        """Turns off ALT selection for the channel. Returns true if the channel 
        contains data that can be read, or if the channel has been poisoned."""
        self._ialt = None
        return self.poisoned or not self.buffer.empty()

    @synchronized
    @chan_poisoncheck
    def pending(self):
        return self.buffer.empty()

class BufferedAny2OneChannel(BufferedOne2OneChannel):
    """Allows more than one writer to send to one reader. Supports ALT on the reader end."""
    def __init__(self, name=None, buffer=None):
        BufferedOne2OneChannel.__init__(self, buffer)
        self.writerLock = threading.RLock()
    def _write(self, obj = None):
        with self.writerLock:  # ensure that only one writer attempts to write at any time
            return super(BufferedAny2OneChannel, self)._write(obj)

class BufferedOne2AnyChannel(BufferedOne2OneChannel):
    """Allows one writer to write to multiple readers. It does, however, not support ALT."""
    def __init__(self, name=None, buffer=None):
        BufferedOne2OneChannel.__init__(self, buffer)
        self.readerLock = threading.RLock()
        self.read  = ChannelInputEnd(self)  # make sure ALT is NOT supported 
    def _read(self):
        with self.readerLock:  # ensure that only one reader attempts to read at any time
            return super(BufferedOne2AnyChannel, self)._read()
    
class BufferedAny2AnyChannel(BufferedOne2AnyChannel):
    def __init__(self, name=None, buffer=None):
        BufferedOne2AnyChannel.__init__(self, buffer)
        self.writerLock = threading.RLock()
    def _write(self, obj = None):
        with self.writerLock:  # ensure that only one writer attempts to write at any time
            return super(BufferedAny2AnyChannel, self)._write(obj)
