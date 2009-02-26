#!/usr/bin/env python
# 
# Network support for PyCSP.
#
# Network support is provided using Pyro (Python Remote Objects),
# which provides most of the functionality we need out of the box.
#
# The bits we need to handle here are:
# - registration and access to remote channels (provided by 
#   registerNamedChannel() and  getNamedChannel()). 
# - Proper channel class and channel end classes shown to the user of
#   a remote channel. This is done by using a RemoteChannelAdapter,
#   which provides proper channel ends.
# - Alternative support across network links. 
# 
# The tricky bit here is to handle input guards across network
# channels since we can't pass the alt object directly across
# to the other side (the side hosting the channel would then
# have a separate copy of the alt object).
#
# The solution to this is to use an Adaptor class in each end.
# In the remote (reader) end, the adaptor intercepts the _ienable()
# method, registers the alt object with Pyro, and passes the URI over
# to the other side.
# In the Local (hosting) end, the LocalChannelAdaptor intercepts the
# _ienable again, uses the URI to get a Proxy object for the alt object,
# and passes the proxy on to the actual channels _ienable method.
# This allows the channel to call schedule() on the correct alt object. 
#
# _idisable is modified to clean up after _ienable by removing the
# necessary proxy objects (and deregistering the Alt object from
# Pyro).
#
# NOTE/TIP: 
# Performancewise, it's probably much better to host a channel in the
# OS process that needs the read() end, if you want to use 
# ALT on network channels. There will be far fewer interactions between
# the processes (only a write operation compared to several calls and
# extra objects registered with Pyro). 
#
#
import pyrocomm
import pycsp.Channels
from pycsp.Channels import Channel, ChannelOutputEnd, ChannelInputEnd, ChannelInputEndGuard

class _forwardMixin(object):
    # Used to provide common "forward-to-next" functionality in the channel adapters
    def __init__(self, chan):
        self._chan = chan
    def _write(self, obj=None):
        # NB: Can't use the remote.write from RemoteChannelAdapter (pyro complaints about not being able to pickle
        # threading locks). TODO: investigate why. 
        self._chan._write(obj)
    def _read(self):
        return self._chan._read()
    def poison(self):
        self._chan.poison()

class RemoteChannelAdapter(_forwardMixin, pycsp.Channels.Channel):
    """This is a proxy for remote channels.
    Handles input guards if the remote channel can work as an input guard. 
    """
    def __init__(self, remoteChan):
        _forwardMixin.__init__(self, remoteChan)
        self.write = ChannelOutputEnd(self)
        if self._chan.isInputGuard():
            self.read  = ChannelInputEndGuard(self)   # This channel can be an input guard. 
        else:
            self.read  = ChannelInputEnd(self)        # This channel can NOT be an input guard. 

    # Guard management
    def _ienable(self, alt):
        # Create a proxy for the alt object, and register with Pyro. 
        # Then pass the URI over to the remote side.
        self._altURI, self._altProxy = pyrocomm.provide_object(alt)
        return self._chan._ienable(self._altURI)
    def _idisable(self):
        ret = self._chan._idisable()
        pyrocomm.disconnect_object(self._altProxy)
        # drop proxy and URI
        self._altURI = None
        self._altProxy = None
        return ret

class LocalChannelAdapter(_forwardMixin, pycsp.Channels.Channel):
    """This class is used to wrap around local channels that are provided
    to remote processes. The main purpose of this adapter is to manage
    the alt objects.
    """
    def __init__(self, chan):
        _forwardMixin.__init__(self, chan)
    def isInputGuard(self):
        "True if the channels read method is an input guard"
        return isinstance(self._chan.read, pycsp.Guard)

    # Guard management
    def _ienable(self, altURI):
        # gets a proxy object for the provided Alt URI
        self._iAltURI = altURI
        self._ialt = pyrocomm.get_robject(altURI, with_attrs = True)
        # use the proxy to call the channels _ienable method
        return self._chan._ienable(self._ialt)

    def _idisable(self):
        # drop the URI and the proxy
        self.iAltURI = None
        self._ialt = None
        # now do a proper disable on the channel itself
        return self._chan._idisable()

def registerNamedChannel(chan, name):
    pyrocomm.provide_object(LocalChannelAdapter(chan), "chans/" + name)

def getNamedChannel(name):
    #return pyrocomm.get_robject("chans/" + name, with_attrs = True)
    return RemoteChannelAdapter(pyrocomm.get_robject("chans/" + name, with_attrs = True))
