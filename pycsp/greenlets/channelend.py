"""
Channelend module

Copyright (c) 2009 John Markus Bjoerndalen <jmb@cs.uit.no>,
      Brian Vinter <vinter@nbi.dk>, Rune M. Friborg <rune.m.friborg@gmail.com>.
See LICENSE.txt for licensing details (MIT License). 
"""

from pycsp.greenlets.exceptions import *
from pycsp.common.const import *

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
class ChannelEndWrite(object):
    def __init__(self, channel):
        self.channel = channel
        self._op = WRITE        

        # Prevention against multiple retires
        self.isretired = False

        self._post_write = self.channel._post_write
        self._remove_write = self.channel._remove_write
        self.poison = self.channel.poison

    def __lt__(self, other):
        # Needed for sorting in FairSelect
        return self

    def __call__(self, *args, **kwargs):
        return self.channel._write(*args, **kwargs)

    def _retire(self, *ignore):
        raise ChannelRetireException()

    def retire(self):
        if not self.isretired:
            self.channel.leave_writer()
            self.__call__ = self._retire
            self._post_write = self._retire
            self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndWrite wrapping %s>" % self.channel
        else:
            return "<ChannelEndWrite wrapping %s named %s>" % (self.channel, self.channel.name)

    def isWriter(self):
        return True

    def isReader(self):
        return False

class ChannelEndRead(object):
    def __init__(self, channel):
        self.channel = channel
        self._op = READ

        # Prevention against multiple retires
        self.isretired = False

        self._post_read = self.channel._post_read
        self._remove_read = self.channel._remove_read
        self.poison = self.channel.poison

    def __lt__(self, other):
        # Needed for sorting in FairSelect
        return self

    def __call__(self, *args, **kwargs):
        return self.channel._read(*args, **kwargs)

    def _retire(self, *ignore):
        raise ChannelRetireException()

    def retire(self):
        if not self.isretired:
            self.channel.leave_reader()
            self.__call__ = self._retire
            self._post_read = self._retire
            self.isretired = True

    def __repr__(self):
        if self.channel.name == None:
            return "<ChannelEndRead wrapping %s>" % self.channel
        else:
            return "<ChannelEndRead wrapping %s named %s>" % (self.channel, self.channel.name)

    def isWriter(self):
        return False

    def isReader(self):
        return True



